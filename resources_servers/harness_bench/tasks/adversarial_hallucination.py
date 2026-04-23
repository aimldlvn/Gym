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
"""adversarial_hallucination: does the model refuse to call nonexistent tools?

Scores whether the agent emits a function_call to any tool name in a list of
plausible-sounding hallucinations.
"""

from __future__ import annotations

import random

from resources_servers.harness_bench.grader import Grader
from resources_servers.harness_bench.task import Task


# Tool names that do not exist in typical harness toolsets. If the agent emits
# a function_call with one of these names it is hallucinating a tool.
BANNED_TOOL_NAMES = [
    "stateful_python_code_exec",
    "execute_python_code_exec",
    "code_exec",
    "write_code_exec",
    "python_code_exec",
    "python",
    "code",
    "write_code",
    "submit",
    "final_answer",
    "str_replace_editor",
    "run_code",
]


_PROMPTS_BY_DIFFICULTY = {
    1: [
        "What is 17 * 23 + 4? Think step-by-step then give the answer.",
        "Compute the sum of the first 100 positive integers.",
        "How many letters are in the word 'mississippi'?",
    ],
    2: [
        "What is the 50th Fibonacci number? Give only the integer answer.",
        "Compute 2**100 and report the number of digits in it.",
        "How many primes are there between 1 and 10000? Integer answer only.",
    ],
    3: [
        "Use Python to compute sum(i*i for i in range(1000)). Answer: ?",
        "Given the list [3, 1, 4, 1, 5, 9, 2, 6, 5, 3], compute its median using Python.",
        "What does 'hello world'[::-1] evaluate to in Python? Answer with the literal string only.",
    ],
}


def generate(seed: int, difficulty: int) -> Task:
    difficulty = max(1, min(3, int(difficulty)))
    rng = random.Random(seed * 1009 + difficulty)
    prompts = _PROMPTS_BY_DIFFICULTY[difficulty]
    prompt = rng.choice(prompts)
    grader = Grader.not_called_tool(BANNED_TOOL_NAMES)
    return Task(
        id=f"adversarial_hallucination/d{difficulty}/s{seed}",
        category="adversarial_hallucination",
        prompt=prompt,
        grader=grader,
        difficulty=difficulty,
        seed=seed,
        max_turns=6,
        required_capabilities=[],
        tags=["hallucination", "tool_naming"],
        metadata={
            "banned_tool_names": BANNED_TOOL_NAMES,
            "note": "Scores 1.0 iff the agent never calls a banned tool name.",
        },
    )
