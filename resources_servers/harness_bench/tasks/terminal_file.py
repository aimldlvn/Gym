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
"""terminal_file: deterministic filesystem queries over a pre-staged directory.

Difficulty knob = number of files (more files = more red herrings). The agent
is expected to use terminal utilities (ls, grep, wc) or a file-read tool.
"""

from __future__ import annotations

import os
import random
from pathlib import Path

from resources_servers.harness_bench.capabilities import Capability
from resources_servers.harness_bench.grader import Grader
from resources_servers.harness_bench.task import Task


_STAGING_DIR = Path(
    os.environ.get("HARNESS_BENCH_STAGE", str(Path.home() / ".harness_bench" / "stage"))
) / "term_file"


def _stage_dir(seed: int, difficulty: int) -> tuple[Path, dict]:
    rng = random.Random(seed * 7919 + difficulty)
    n_files = int(20 * (1.6 ** difficulty))
    d = _STAGING_DIR / f"{seed}_{difficulty}"
    d.mkdir(parents=True, exist_ok=True)
    for p in d.iterdir():
        try:
            p.unlink()
        except OSError:
            pass
    n_magic = 0
    exts = [".py", ".txt", ".log"]
    total_lines = 0
    for i in range(n_files):
        ext = rng.choice(exts)
        lines = rng.randint(3, 20)
        has_magic = rng.random() < 0.25
        content_lines = []
        for _ in range(lines):
            if has_magic and rng.random() < 0.3:
                content_lines.append("# MAGIC42 marker")
            else:
                content_lines.append(f"# random-line-{rng.randint(0, 1 << 16)}")
        (d / f"f{i:04d}{ext}").write_text("\n".join(content_lines) + "\n")
        if any("MAGIC42" in ln for ln in content_lines):
            n_magic += 1
        total_lines += lines
    return d, {"n_files": n_files, "n_magic": n_magic, "total_lines": total_lines}


def generate(seed: int, difficulty: int) -> Task:
    difficulty = max(1, min(5, int(difficulty)))
    rng = random.Random(seed * 7919 + difficulty + 3)
    variant = rng.choice(["count_magic", "count_py", "sum_lines"])
    path, info = _stage_dir(seed, difficulty)

    if variant == "count_magic":
        prompt = (
            f"Directory {path} contains several files. How many files in it "
            "contain the exact substring 'MAGIC42'? Reply with only the integer."
        )
        ref = info["n_magic"]
    elif variant == "count_py":
        n_py = sum(1 for p in path.iterdir() if p.suffix == ".py")
        prompt = (
            f"Directory {path} contains several files. How many of them end "
            "in '.py'? Reply with only the integer."
        )
        ref = n_py
    else:
        prompt = (
            f"Directory {path} contains several files. What is the total number "
            "of lines across ALL files in that directory (count every line)? "
            "Reply with only the integer."
        )
        ref = info["total_lines"]

    return Task(
        id=f"terminal_file/{variant}/d{difficulty}/s{seed}",
        category="terminal_file",
        prompt=prompt,
        grader=Grader.exact_int(ref),
        difficulty=difficulty,
        seed=seed,
        max_turns=6,
        required_capabilities=[Capability.TERMINAL, Capability.FILESYSTEM_READ],
        tags=["filesystem", variant],
        metadata={"dir": str(path), "ref_answer": str(ref), "variant": variant, **info},
    )
