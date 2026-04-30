# Copyright (c) 2026, NVIDIA CORPORATION.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import json
import logging
import traceback
from typing import Any

import verifiers as vf
from fastapi import Body, Request, Response
from openai import AsyncOpenAI
from pydantic import ConfigDict, Field
from verifiers.clients import NeMoRLChatCompletionsClient

from nemo_gym.base_resources_server import BaseRunRequest, BaseVerifyResponse
from nemo_gym.base_responses_api_agent import BaseResponsesAPIAgentConfig, SimpleResponsesAPIAgent
from nemo_gym.config_types import ModelServerRef
from nemo_gym.global_config import get_first_server_config_dict
from nemo_gym.openai_utils import (
    NeMoGymEasyInputMessage,
    NeMoGymFunctionCallOutput,
    NeMoGymResponse,
    NeMoGymResponseCreateParamsNonStreaming,
    NeMoGymResponseFunctionToolCall,
    NeMoGymResponseFunctionToolCallForTraining,
    NeMoGymResponseOutputMessage,
    NeMoGymResponseOutputMessageForTraining,
    NeMoGymResponseOutputText,
)


logger = logging.getLogger(__name__)


class VerifiersNeMoGymResponse(NeMoGymResponse):
    env_id: str
    group_id: str
    output: list[dict[str, Any]]
    reward: float
    metrics: dict[str, Any] = Field(default_factory=dict)
    parallel_tool_calls: bool = True
    tool_choice: str = "auto"
    tools: list = Field(default_factory=list)


class VerifiersAgentVerifyResponse(BaseVerifyResponse):
    model_config = ConfigDict(extra="allow")
    response: VerifiersNeMoGymResponse
    reward: float


class VerifiersAgentConfig(BaseResponsesAPIAgentConfig):
    model_server: ModelServerRef
    model_name: str = Field(default="", description="Model name")

    vf_env_id: str = Field(default="", description="Verifiers environment ID")
    vf_env_args: dict = Field(default_factory=dict, description="Verifiers environment arguments")

    max_tokens: int = Field(default=8192, description="Max tokens for generation")

    # nemo rl generation_config overrides these
    temperature: float = Field(default=1.0)
    top_p: float = Field(default=1.0)


class VerifiersAgentRunRequest(BaseRunRequest):
    model_config = ConfigDict(extra="allow")

    task_idx: int
    vf_env_id: str | None = Field(default=None, description="Verifiers environment ID")
    responses_create_params: NeMoGymResponseCreateParamsNonStreaming = Field(
        default_factory=lambda: NeMoGymResponseCreateParamsNonStreaming(input=[])
    )
    answer: str = Field(default="", description="Expected answer from dataset")
    task: str = Field(default="default", description="Task type from dataset")
    example_id: int | str = Field(default=0, description="Example ID from dataset")
    info: dict = Field(default_factory=dict, description="Extra info from dataset")


class VerifiersAgent(SimpleResponsesAPIAgent):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    config: VerifiersAgentConfig

    envs_cache: dict[str, Any] = Field(default_factory=dict)
    client_cache: dict[str, NeMoRLChatCompletionsClient] = Field(default_factory=dict)

    def _get_env(self, vf_env_id: str) -> vf.Environment:
        if vf_env_id not in self.envs_cache:
            self.envs_cache[vf_env_id] = vf.load_environment(vf_env_id, **self.config.vf_env_args)
        return self.envs_cache[vf_env_id]

    def _get_client(self) -> NeMoRLChatCompletionsClient:
        cache_key = self.config.model_server.name
        if cache_key not in self.client_cache:
            server_config_dict = get_first_server_config_dict(
                self.server_client.global_config_dict,
                self.config.model_server.name,
            )
            model_server_url = f"http://{server_config_dict.host}:{server_config_dict.port}"

            if not model_server_url.endswith("/v1"):
                model_server_url = model_server_url.rstrip("/") + "/v1"

            openai_client = AsyncOpenAI(
                base_url=model_server_url,
                api_key="EMPTY",  # pragma: allowlist secret
            )
            self.client_cache[cache_key] = NeMoRLChatCompletionsClient(openai_client)

        return self.client_cache[cache_key]

    @staticmethod
    def _get_msg_value(obj: Any, key: str, default: Any = None) -> Any:
        if hasattr(obj, "get"):
            return obj.get(key, default)
        return getattr(obj, key, default)

    @staticmethod
    def _normalize_tool_call(tool_call: Any) -> Any:
        if isinstance(tool_call, str):
            try:
                return json.loads(tool_call)
            except json.JSONDecodeError:
                return {"arguments": tool_call}
        return tool_call

    @staticmethod
    def _content_to_text(content: Any) -> str:
        if content is None:
            return ""
        if isinstance(content, str):
            return content
        try:
            return json.dumps(content, default=str)
        except TypeError:
            return str(content)

    def _function_tool_call_to_output(self, tool_call: Any, tokens: dict | None = None) -> dict[str, Any]:
        tool_call = self._normalize_tool_call(tool_call)
        call_id = (
            self._get_msg_value(tool_call, "id", None)
            or self._get_msg_value(tool_call, "call_id", None)
            or f"call_{id(tool_call)}"
        )
        name = self._get_msg_value(tool_call, "name", "")
        arguments = self._get_msg_value(tool_call, "arguments", "{}")
        arguments = self._content_to_text(arguments)

        kwargs = {
            "arguments": arguments,
            "call_id": call_id,
            "name": name,
            "id": call_id,
            "status": "completed",
        }
        if tokens:
            return NeMoGymResponseFunctionToolCallForTraining(
                **kwargs,
                prompt_token_ids=tokens.get("prompt_ids", []),
                generation_token_ids=tokens.get("completion_ids", []),
                generation_log_probs=tokens.get("completion_logprobs", []),
            ).model_dump()
        return NeMoGymResponseFunctionToolCall(**kwargs).model_dump()

    def _assistant_content_to_output(self, msg: Any, content: Any, tokens: dict | None = None) -> dict[str, Any]:
        kwargs = {
            "id": f"msg_{id(msg)}",
            "content": [NeMoGymResponseOutputText(text=self._content_to_text(content), annotations=[])],
        }
        if tokens:
            return NeMoGymResponseOutputMessageForTraining(
                **kwargs,
                prompt_token_ids=tokens.get("prompt_ids", []),
                generation_token_ids=tokens.get("completion_ids", []),
                generation_log_probs=tokens.get("completion_logprobs", []),
            ).model_dump()
        return NeMoGymResponseOutputMessage(**kwargs).model_dump()

    def _assistant_message_to_output_items(self, msg: Any, tokens: dict | None = None) -> list[dict[str, Any]]:
        output: list[dict[str, Any]] = []
        content = self._get_msg_value(msg, "content", "")
        tool_calls = self._get_msg_value(msg, "tool_calls", None) or []

        content_text = self._content_to_text(content)
        if content_text:
            output.append(self._assistant_content_to_output(msg, content_text, None if tool_calls else tokens))

        for idx, tool_call in enumerate(tool_calls):
            # Mirror the vLLM converter: attach token information to the final
            # assistant output item for the completion.
            tool_tokens = tokens if idx == len(tool_calls) - 1 else None
            output.append(self._function_tool_call_to_output(tool_call, tool_tokens))

        if not content_text and not tool_calls:
            output.append(self._assistant_content_to_output(msg, "", tokens))

        return output

    def _convert_message_sequence_to_output(
        self,
        messages: list[Any],
        assistant_tokens: list[dict | None] | None = None,
    ) -> list[dict[str, Any]]:
        output: list[dict[str, Any]] = []
        token_idx = 0

        for msg in messages or []:
            # Handle both plain dicts (serialized RolloutOutput) and Pydantic
            # CustomBaseModel messages (which support .get()).
            if not (hasattr(msg, "get") or hasattr(msg, "role")):
                continue

            role = self._get_msg_value(msg, "role", "user")
            content = self._get_msg_value(msg, "content", "")

            if role == "tool":
                call_id = (
                    self._get_msg_value(msg, "tool_call_id", None)
                    or self._get_msg_value(msg, "call_id", None)
                    or f"call_{id(msg)}"
                )
                output.append(
                    NeMoGymFunctionCallOutput(
                        call_id=call_id,
                        id=call_id,
                        output=self._content_to_text(content),
                        status="completed",
                    ).model_dump()
                )
                continue

            if role == "assistant":
                tokens = None
                if assistant_tokens is not None and token_idx < len(assistant_tokens):
                    tokens = assistant_tokens[token_idx]
                token_idx += 1
                output.extend(self._assistant_message_to_output_items(msg, tokens))
                continue

            if content is None:
                content = ""
            output.append(NeMoGymEasyInputMessage(role=role, content=content).model_dump())

        return output

    def _trajectory_assistant_tokens(self, trajectory: list[Any]) -> list[dict | None]:
        assistant_tokens: list[dict | None] = []
        for step in trajectory or []:
            step_tokens = step.get("tokens") if hasattr(step, "get") else None
            for msg in (step.get("completion", []) if hasattr(step, "get") else []) or []:
                if not (hasattr(msg, "get") or hasattr(msg, "role")):
                    continue
                if self._get_msg_value(msg, "role", None) != "assistant":
                    continue
                tokens = step_tokens
                if tokens is None:
                    tokens = self._get_msg_value(msg, "tokens", None)
                assistant_tokens.append(tokens)
        return assistant_tokens

    def _convert_trajectory_to_output(self, rollout_output: dict) -> list:
        # Verifiers renders top-level completion as the full conversation after
        # the original prompt. This matches the simple_agent `new_outputs`
        # convention and avoids duplicating trajectory prompts at every turn.
        completion = rollout_output.get("completion")
        if completion is not None:
            return self._convert_message_sequence_to_output(
                completion,
                assistant_tokens=self._trajectory_assistant_tokens(rollout_output.get("trajectory", [])),
            )

        output = []
        seen_tool_outputs: set[tuple[str, str]] = set()
        for step in rollout_output.get("trajectory", []) or []:
            for msg in step.get("prompt", []) or []:
                if not (hasattr(msg, "get") or hasattr(msg, "role")):
                    continue
                if self._get_msg_value(msg, "role", None) != "tool":
                    continue
                call_id = (
                    self._get_msg_value(msg, "tool_call_id", None)
                    or self._get_msg_value(msg, "call_id", None)
                    or f"call_{id(msg)}"
                )
                content_text = self._content_to_text(self._get_msg_value(msg, "content", ""))
                key = (call_id, content_text)
                if key in seen_tool_outputs:
                    continue
                seen_tool_outputs.add(key)
                output.append(
                    NeMoGymFunctionCallOutput(
                        call_id=call_id,
                        id=call_id,
                        output=content_text,
                        status="completed",
                    ).model_dump()
                )

            step_tokens = step.get("tokens") if hasattr(step, "get") else None
            for msg in step.get("completion", []) or []:
                if not (hasattr(msg, "get") or hasattr(msg, "role")):
                    continue
                if self._get_msg_value(msg, "role", None) == "assistant":
                    tokens = step_tokens or self._get_msg_value(msg, "tokens", None)
                    output.extend(self._assistant_message_to_output_items(msg, tokens))
                else:
                    output.extend(self._convert_message_sequence_to_output([msg]))

        return output

    async def responses(
        self,
        request: Request,
        response: Response,
        body: VerifiersAgentRunRequest = Body(),
    ) -> VerifiersNeMoGymResponse:
        try:
            vf_env_id = body.vf_env_id or self.config.vf_env_id
            vf_env = self._get_env(vf_env_id)
            task_idx = body.task_idx

            prompt_messages = []
            for item in body.responses_create_params.input or []:
                if hasattr(item, "role") and hasattr(item, "content"):
                    prompt_messages.append({"role": item.role, "content": item.content})
                elif isinstance(item, dict):
                    prompt_messages.append({"role": item.get("role", "user"), "content": item.get("content", "")})

            rollout_input = vf.RolloutInput(
                prompt=prompt_messages,
                answer=body.answer,
                task=body.task,
                info=body.info,
                example_id=body.example_id,
            )

            client = self._get_client()

            # prefer NeMo RL generation config set in responses_create_params
            # https://github.com/NVIDIA-NeMo/RL/blob/main/nemo_rl/experience/rollouts.py#L1045-L1046
            sampling_args = {
                "max_tokens": self.config.max_tokens,
                "temperature": getattr(body.responses_create_params, "temperature", None) or self.config.temperature,
                "top_p": getattr(body.responses_create_params, "top_p", None) or self.config.top_p,
            }
            outputs = await vf_env.run_group(
                group_inputs=[rollout_input],
                client=client,
                model=self.config.model_name,
                sampling_args=sampling_args,
                state_columns=["trajectory"],
            )

            rollout_output = outputs[0]
            reward = rollout_output.get("reward", 0.0) or 0.0
            metrics = rollout_output.get("metrics", {}) or {}

            output = self._convert_trajectory_to_output(rollout_output)

            return VerifiersNeMoGymResponse(
                id=f"verifiers-{vf_env_id}-{task_idx}",
                created_at=0,
                model=self.config.model_name,
                object="response",
                output=output,
                env_id=vf_env_id,
                group_id=str(task_idx),
                reward=reward,
                metrics=metrics,
            )
        except Exception as e:
            logger.error(f"Exception in responses(): {type(e).__name__}: {e}")
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            raise

    async def run(
        self,
        request: Request,
        response: Response,
        body: VerifiersAgentRunRequest = Body(),
    ) -> VerifiersAgentVerifyResponse:
        resp = await self.responses(request, response, body)

        return VerifiersAgentVerifyResponse(
            responses_create_params=body.responses_create_params,
            response=resp,
            reward=resp.reward,
        )


if __name__ == "__main__":
    VerifiersAgent.run_webserver()
