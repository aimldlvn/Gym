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
"""multi_tool_chain: tasks that require calling at least 2 distinct tools.

A payload file is staged. The correct answer requires composing two tools
(e.g. read_file + terminal md5sum). Grader: exact answer plus at least 2
distinct tool names in the trajectory.
"""

from __future__ import annotations

import hashlib
import os
import random
from pathlib import Path

from resources_servers.harness_bench.capabilities import Capability
from resources_servers.harness_bench.grader import Grader
from resources_servers.harness_bench.task import Task


_STAGING_DIR = Path(
    os.environ.get("HARNESS_BENCH_STAGE", str(Path.home() / ".harness_bench" / "stage"))
) / "chain"


def _stage_payload(seed: int, difficulty: int) -> tuple[Path, dict]:
    rng = random.Random(seed * 6991 + difficulty * 13)
    n_lines = int(10 * (1.5 ** difficulty))
    lines = [f"row-{i:04d}-val-{rng.randint(0, 1 << 20)}" for i in range(n_lines)]
    text = "\n".join(lines) + "\n"
    _STAGING_DIR.mkdir(parents=True, exist_ok=True)
    p = _STAGING_DIR / f"{seed}_{difficulty}.txt"
    p.write_text(text)
    return p, {
        "n_lines": n_lines,
        "n_bytes": len(text.encode("utf-8")),
        "md5": hashlib.md5(text.encode("utf-8")).hexdigest(),
        "sha256_first8": hashlib.sha256(text.encode("utf-8")).hexdigest()[:8],
    }


def generate(seed: int, difficulty: int) -> Task:
    difficulty = max(1, min(5, int(difficulty)))
    rng = random.Random(seed * 6991 + difficulty)
    variant = rng.choice(["line_count_then_double", "md5_of_file", "byte_count_plus_one"])
    p, info = _stage_payload(seed, difficulty)

    if variant == "line_count_then_double":
        ref = str(info["n_lines"] * 2)
        prompt = (
            f"Use at least two different tools to: (1) determine how many lines are in {p}, "
            "(2) compute that count times 2. Reply with only the integer."
        )
    elif variant == "md5_of_file":
        ref = info["md5"]
        prompt = (
            f"Using at least two different tools, compute the MD5 hex digest of the file {p}. "
            "Reply with only the 32-char lowercase hex string."
        )
    else:
        ref = str(info["n_bytes"] + 1)
        prompt = (
            f"Using at least two different tools, determine the byte length of {p} and add 1. "
            "Reply with only the integer."
        )

    return Task(
        id=f"multi_tool_chain/{variant}/d{difficulty}/s{seed}",
        category="multi_tool_chain",
        prompt=prompt,
        grader=Grader.chain_answer_and_ntools(ref, min_distinct_tools=2),
        difficulty=difficulty,
        seed=seed,
        max_turns=8,
        required_capabilities=[
            Capability.TERMINAL,
            Capability.FILESYSTEM_READ,
            Capability.CODE_EXECUTE,
        ],
        tags=["multi_tool", variant],
        metadata={"file": str(p), "ref_answer": ref, "variant": variant, **info},
    )
