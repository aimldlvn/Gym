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
"""terminal_calc: deterministic arithmetic problems best solved via terminal
or code execution rather than by pure chain-of-thought.
"""

from __future__ import annotations

import math
import random

from resources_servers.harness_bench.capabilities import Capability
from resources_servers.harness_bench.grader import Grader
from resources_servers.harness_bench.task import Task


def _nth_prime(n: int) -> int:
    if n < 1:
        raise ValueError(n)
    limit = max(30, int(n * (math.log(n) + math.log(math.log(n) + 1))) + 10)
    sieve = bytearray([1]) * (limit + 1)
    sieve[0] = sieve[1] = 0
    for i in range(2, int(limit**0.5) + 1):
        if sieve[i]:
            for j in range(i * i, limit + 1, i):
                sieve[j] = 0
    count = 0
    for i, flag in enumerate(sieve):
        if flag:
            count += 1
            if count == n:
                return i
    raise RuntimeError(f"sieve limit too small for n={n}")


def generate(seed: int, difficulty: int) -> Task:
    difficulty = max(1, min(5, int(difficulty)))
    rng = random.Random(seed * 1009 + difficulty * 31)
    variant = rng.choice(["prime", "factorial_digits", "perfect_square_count"])

    if variant == "prime":
        n = int(50 * (1.8 ** difficulty))
        prompt = f"What is the {n}-th prime number? Reply with only the integer."
        ref = _nth_prime(n)
    elif variant == "factorial_digits":
        n = int(20 * (1.5 ** difficulty))
        prompt = f"How many digits does {n}! have? Reply with only the integer."
        lg = sum(math.log10(k) for k in range(2, n + 1))
        ref = 1 + int(lg)
    else:
        hi = int(1000 * (2 ** difficulty))
        prompt = (
            f"How many perfect squares are there between 1 and {hi} inclusive? "
            "Reply with only the integer."
        )
        ref = int(math.isqrt(hi))

    return Task(
        id=f"terminal_calc/{variant}/d{difficulty}/s{seed}",
        category="terminal_calc",
        prompt=prompt,
        grader=Grader.exact_int(ref),
        difficulty=difficulty,
        seed=seed,
        max_turns=6,
        required_capabilities=[Capability.TERMINAL, Capability.CODE_EXECUTE],
        tags=["arithmetic", variant],
        metadata={"variant": variant, "ref_answer": str(ref)},
    )
