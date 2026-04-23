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
"""Generate a harness_bench suite as a JSONL file.

    python -m resources_servers.harness_bench.generate --out suite.jsonl --seeds 0:20
"""

from __future__ import annotations

import argparse
import importlib
import json
import pathlib


CATEGORY_CONFIGS = [
    # (module_name, difficulty_range)
    ("resources_servers.harness_bench.tasks.adversarial_hallucination", range(1, 4)),
    ("resources_servers.harness_bench.tasks.terminal_calc",             range(1, 6)),
    ("resources_servers.harness_bench.tasks.python_data",               range(1, 4)),
    ("resources_servers.harness_bench.tasks.terminal_file",             range(1, 6)),
    ("resources_servers.harness_bench.tasks.multi_tool_chain",          range(1, 6)),
    ("resources_servers.harness_bench.tasks.skill_invoke",              range(1, 4)),
    ("resources_servers.harness_bench.tasks.todo_plan",                 range(1, 4)),
    ("resources_servers.harness_bench.tasks.bugfix_mini",               range(1, 4)),
]


def _parse_seeds(spec: str) -> list[int]:
    if ":" in spec:
        lo, hi = spec.split(":")
        return list(range(int(lo), int(hi)))
    return [int(x) for x in spec.split(",")]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=pathlib.Path, required=True)
    p.add_argument("--seeds", default="0:20", help="range 'a:b' or comma list")
    p.add_argument("--difficulties", default=None, help="comma-list override (applied to every category)")
    args = p.parse_args()

    seeds = _parse_seeds(args.seeds)
    diff_override = [int(x) for x in args.difficulties.split(",")] if args.difficulties else None

    args.out.parent.mkdir(parents=True, exist_ok=True)

    written = 0
    per_cat: dict[str, int] = {}
    with args.out.open("w") as fo:
        for mod_name, default_diffs in CATEGORY_CONFIGS:
            mod = importlib.import_module(mod_name)
            diffs = diff_override if diff_override is not None else list(default_diffs)
            for d in diffs:
                for s in seeds:
                    task = mod.generate(seed=s, difficulty=d)
                    fo.write(json.dumps(task.to_jsonl_row()) + "\n")
                    per_cat[task.category] = per_cat.get(task.category, 0) + 1
                    written += 1

    print(f"Wrote {written} tasks to {args.out}")
    for cat, n in sorted(per_cat.items()):
        print(f"  {cat}: {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
