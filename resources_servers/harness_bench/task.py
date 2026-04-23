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
"""Task dataclass and JSONL (de)serialization."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from resources_servers.harness_bench.capabilities import Capability
from resources_servers.harness_bench.grader import Grader


@dataclass
class Task:
    """One concrete task instance produced by a task module's generate()."""

    id: str
    category: str
    prompt: str
    grader: Grader
    difficulty: int
    seed: int
    max_turns: int = 6
    required_capabilities: list[Capability] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_jsonl_row(self) -> dict:
        """Serialize to a harness-agnostic JSONL row."""
        return {
            "task_id": self.id,
            "category": self.category,
            "difficulty": self.difficulty,
            "seed": self.seed,
            "max_turns": self.max_turns,
            "required_capabilities": [c.value for c in self.required_capabilities],
            "tags": self.tags,
            "metadata": self.metadata,
            "grader": self.grader.to_json(),
            "responses_create_params": {
                "input": [
                    {"role": "user", "content": self.prompt},
                ],
            },
        }


def load_task_from_row(row: dict) -> Task:
    """Rebuild a Task from its JSONL row. Reconstructs the grader from its
    {name, meta} shape. Accepts either `required_capabilities` (new) or
    `required_tools` (legacy). Raises ValueError on unknown grader names or
    unknown capability strings.
    """
    g_info = row["grader"]
    name = g_info["name"]
    meta = g_info.get("meta", {})
    if name == "exact_int":
        grader = Grader.exact_int(meta["ref"])
    elif name == "exact_str":
        grader = Grader.exact_str(
            meta["ref"],
            case_sensitive=meta.get("case_sensitive", False),
            strip=meta.get("strip", True),
        )
    elif name == "regex":
        grader = Grader.regex(meta["pattern"])
    elif name == "negative":
        grader = Grader.negative(meta["must_not_contain"])
    elif name == "not_called_tool":
        grader = Grader.not_called_tool(meta["banned_tool_names"])
    elif name == "chain_answer_and_ntools":
        grader = Grader.chain_answer_and_ntools(
            meta["ref_answer"], int(meta.get("min_distinct_tools", 2))
        )
    elif name == "called_any_of":
        grader = Grader.called_any_of(list(meta["tool_names"]), ref_answer=meta.get("ref_answer"))
    elif name == "min_tool_calls_and_answer":
        grader = Grader.min_tool_calls_and_answer(
            meta["tool_name"], int(meta["min_calls"]), meta["ref_answer"]
        )
    elif name == "subprocess_test":
        grader = Grader.subprocess_test(
            meta["stage_dir"], meta["solution_file"], meta["test_file"],
            int(meta["n_tests"]), timeout_s=int(meta.get("timeout_s", 30)),
        )
    else:
        raise ValueError(f"Unknown grader name: {name!r}")

    caps_raw = row.get("required_capabilities")
    if caps_raw is None:
        caps_raw = row.get("required_tools", [])
    caps: list[Capability] = []
    for c in caps_raw:
        try:
            caps.append(Capability(c))
        except ValueError as e:
            raise ValueError(f"Unknown capability: {c!r}") from e

    return Task(
        id=row["task_id"],
        category=row["category"],
        prompt=row["responses_create_params"]["input"][-1]["content"],
        grader=grader,
        difficulty=int(row["difficulty"]),
        seed=int(row["seed"]),
        max_turns=int(row.get("max_turns", 6)),
        required_capabilities=caps,
        tags=row.get("tags", []),
        metadata=row.get("metadata", {}),
    )
