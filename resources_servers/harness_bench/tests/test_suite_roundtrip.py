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
"""Smoke test: generate the core suite, roundtrip every row through
load_task_from_row, and check that grader names survive and all declared
capabilities are known Capability enum values.
"""

from __future__ import annotations

import importlib
import json
import sys
import tempfile
from pathlib import Path


# Allow running from either the Gym repo root or the server root.
_HERE = Path(__file__).resolve().parent
_GYM_ROOT = _HERE.parent.parent.parent
if str(_GYM_ROOT) not in sys.path:
    sys.path.insert(0, str(_GYM_ROOT))

from resources_servers.harness_bench.capabilities import Capability
from resources_servers.harness_bench.task import load_task_from_row


VALID_CAPS = {c.value for c in Capability}


CATEGORY_MODULES = [
    "resources_servers.harness_bench.tasks.adversarial_hallucination",
    "resources_servers.harness_bench.tasks.terminal_calc",
    "resources_servers.harness_bench.tasks.python_data",
    "resources_servers.harness_bench.tasks.terminal_file",
    "resources_servers.harness_bench.tasks.multi_tool_chain",
    "resources_servers.harness_bench.tasks.skill_invoke",
    "resources_servers.harness_bench.tasks.todo_plan",
    "resources_servers.harness_bench.tasks.bugfix_mini",
]


def run():
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "suite.jsonl"
        with out.open("w") as fo:
            for mod_name in CATEGORY_MODULES:
                mod = importlib.import_module(mod_name)
                for d in (1, 2, 3):
                    for s in (0, 1):
                        task = mod.generate(seed=s, difficulty=d)
                        fo.write(json.dumps(task.to_jsonl_row()) + "\n")

        n = 0
        with out.open() as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                orig_grader_name = row["grader"]["name"]
                for c in row.get("required_capabilities", []):
                    assert c in VALID_CAPS, f"unknown capability {c!r} in row {row['task_id']}"
                task = load_task_from_row(row)
                assert task.grader.to_json()["name"] == orig_grader_name, (
                    f"grader name mismatch for {row['task_id']}: "
                    f"{orig_grader_name} vs {task.grader.to_json()['name']}"
                )
                n += 1

        assert n > 0, "no rows generated"
        print(f"OK: roundtripped {n} rows")


if __name__ == "__main__":
    run()
