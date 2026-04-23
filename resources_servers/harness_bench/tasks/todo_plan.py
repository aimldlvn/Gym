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
"""todo_plan: require the agent to track multi-step work with a todo tool.

A 3-step arithmetic problem; the prompt instructs the model to record each
step as a todo. Grader requires at least `min_calls` todo invocations and a
matching final answer.
"""

from __future__ import annotations

import random

from resources_servers.harness_bench.capabilities import Capability
from resources_servers.harness_bench.grader import Grader
from resources_servers.harness_bench.task import Task


def _three_step_problem(rng: random.Random) -> tuple[str, int]:
    a = rng.randint(10, 99)
    b = rng.randint(10, 99)
    c = rng.randint(2, 9)
    ans = ((a + b) * c) - max(a, b)
    prompt = (
        "Solve this 3-step problem. Use your todo tool to track each of the "
        "three sub-steps as separate todo items (create at least 3). Then "
        "give the final numeric answer on the last line.\n\n"
        f"Step 1: Compute X = {a} + {b}.\n"
        f"Step 2: Multiply X by {c} to get Y.\n"
        f"Step 3: Subtract max({a}, {b}) from Y to get the final answer.\n\n"
        "Respond with the final integer on the last line, nothing else after it."
    )
    return prompt, ans


def generate(seed: int, difficulty: int) -> Task:
    difficulty = max(1, min(3, int(difficulty)))
    rng = random.Random(seed * 8837 + difficulty)
    prompt, ans = _three_step_problem(rng)
    min_calls = 3 if difficulty >= 2 else 2

    return Task(
        id=f"todo_plan/3step/d{difficulty}/s{seed}",
        category="todo_plan",
        prompt=prompt,
        grader=Grader.min_tool_calls_and_answer("todo", min_calls=min_calls, ref_answer=str(ans)),
        difficulty=difficulty,
        seed=seed,
        max_turns=6,
        required_capabilities=[Capability.TODO_TRACK],
        tags=["planning", "todo"],
        metadata={"ref_answer": str(ans), "min_todo_calls": min_calls},
    )
