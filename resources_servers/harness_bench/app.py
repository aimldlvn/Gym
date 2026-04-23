# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""nemo-gym resources_server for harness_bench.

Exposes /run and /verify. /verify rebuilds the grader from the row and scores
the agent's response in [0, 1].
"""

from __future__ import annotations

from typing import Any

from pydantic import ConfigDict

from nemo_gym.base_resources_server import (
    BaseResourcesServerConfig,
    BaseRunRequest,
    BaseVerifyRequest,
    BaseVerifyResponse,
    SimpleResourcesServer,
)

from resources_servers.harness_bench.task import load_task_from_row


class HarnessBenchConfig(BaseResourcesServerConfig):
    pass


class HarnessBenchRunRequest(BaseRunRequest):
    model_config = ConfigDict(extra="allow")
    task_id: str
    category: str
    difficulty: int
    seed: int
    max_turns: int = 6
    required_capabilities: list[str] = []
    tags: list[str] = []
    metadata: dict[str, Any] = {}
    grader: dict[str, Any]


class HarnessBenchVerifyRequest(HarnessBenchRunRequest, BaseVerifyRequest):
    pass


class HarnessBenchVerifyResponse(BaseVerifyResponse):
    task_id: str
    category: str
    difficulty: int
    seed: int
    score: float


class HarnessBenchResourcesServer(SimpleResourcesServer):
    config: HarnessBenchConfig

    async def verify(self, body: HarnessBenchVerifyRequest) -> HarnessBenchVerifyResponse:
        assistant_responses: list[str] = []
        for item in body.response.output:
            if item.type != "message":
                continue
            for cc in item.content:
                if cc.type != "output_text":
                    continue
                assistant_responses.append(cc.text)
        combined = "".join(assistant_responses)

        # Accept either required_capabilities (new) or required_tools (legacy).
        extras = body.model_extra or {}
        legacy_tools = extras.get("required_tools", [])
        caps = body.required_capabilities or legacy_tools

        row = {
            "task_id": body.task_id,
            "category": body.category,
            "difficulty": body.difficulty,
            "seed": body.seed,
            "max_turns": body.max_turns,
            "required_capabilities": caps,
            "tags": body.tags,
            "metadata": body.metadata,
            "grader": body.grader,
            "responses_create_params": body.responses_create_params.model_dump()
                if hasattr(body.responses_create_params, "model_dump") else dict(body.responses_create_params),
        }
        task = load_task_from_row(row)

        # Traj-aware graders (e.g. not_called_tool) need function_call items.
        task_with_traj = {
            **row,
            "__trajectory__": {
                "response": body.response.model_dump() if hasattr(body.response, "model_dump") else dict(body.response),
            },
        }
        score = task.grader.score(task_with_traj, combined)

        return HarnessBenchVerifyResponse(
            responses_create_params=body.responses_create_params,
            response=body.response,
            task_id=body.task_id,
            category=body.category,
            difficulty=body.difficulty,
            seed=body.seed,
            reward=score,
            score=score,
        )


if __name__ == "__main__":
    HarnessBenchResourcesServer.run_webserver()
