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
"""Grader: scores (task, response) pairs in [0, 1]."""

from __future__ import annotations

import os
import re
import subprocess
from typing import Any, Callable, Optional


class Grader:
    """Graders consume (task, agent_response_str) and return a float in [0, 1]."""

    def __init__(self, fn: Callable[[dict, str], float], name: str = "custom"):
        self.fn = fn
        self.name = name
        self.meta: dict[str, Any] = {}

    def score(self, task: dict, response: str) -> float:
        try:
            return float(self.fn(task, response))
        except Exception:
            return 0.0

    def to_json(self) -> dict:
        return {"name": self.name, "meta": self.meta}

    @classmethod
    def exact_int(cls, ref: int) -> "Grader":
        def _f(task, response):
            m = re.findall(r"-?\d+", response)
            if not m:
                return 0.0
            return 1.0 if int(m[-1]) == int(ref) else 0.0
        g = cls(_f, name="exact_int")
        g.meta = {"ref": int(ref)}
        return g

    @classmethod
    def exact_str(cls, ref: str, *, case_sensitive: bool = False, strip: bool = True) -> "Grader":
        def _f(task, response):
            r, t = response, ref
            if strip:
                r = r.strip()
                t = t.strip()
            if not case_sensitive:
                r = r.lower()
                t = t.lower()
            return 1.0 if (r == t or r.endswith(t)) else 0.0
        g = cls(_f, name="exact_str")
        g.meta = {"ref": ref, "case_sensitive": case_sensitive, "strip": strip}
        return g

    @classmethod
    def regex(cls, pattern: str, *, flags: int = re.IGNORECASE) -> "Grader":
        rx = re.compile(pattern, flags)
        def _f(task, response):
            return 1.0 if rx.search(response) else 0.0
        g = cls(_f, name="regex")
        g.meta = {"pattern": pattern}
        return g

    @classmethod
    def negative(cls, must_not_contain: list[str]) -> "Grader":
        """Score 1.0 if response contains none of the banned substrings."""
        bans = [b.lower() for b in must_not_contain]
        def _f(task, response):
            r = response.lower()
            return 0.0 if any(b in r for b in bans) else 1.0
        g = cls(_f, name="negative")
        g.meta = {"must_not_contain": list(must_not_contain)}
        return g

    @classmethod
    def not_called_tool(cls, banned_tool_names: list[str]) -> "Grader":
        """Score 1.0 iff none of the banned tool names appear as function_call
        names in the trajectory. Requires `__trajectory__` in the task dict.
        """
        banned = {b.lower() for b in banned_tool_names}
        def _f(task, response):
            traj = task.get("__trajectory__") or {}
            for item in traj.get("response", {}).get("output", []):
                if item.get("type") == "function_call" and item.get("name", "").lower() in banned:
                    return 0.0
            return 1.0
        g = cls(_f, name="not_called_tool")
        g.meta = {"banned_tool_names": list(banned_tool_names)}
        return g

    @classmethod
    def chain_answer_and_ntools(cls, ref_answer: str, min_distinct_tools: int = 2) -> "Grader":
        """Score 1.0 iff the response matches ref_answer and the trajectory
        called at least `min_distinct_tools` distinct tool names.
        """
        want = (ref_answer or "").strip().lower()
        def _f(task, response):
            resp = (response or "").strip().lower()
            ok_ans = bool(want) and (resp == want or resp.endswith(want) or want in resp)
            if not ok_ans:
                return 0.0
            traj = task.get("__trajectory__") or {}
            names = set()
            for item in traj.get("response", {}).get("output", []):
                if item.get("type") == "function_call":
                    nm = (item.get("name") or "").strip().lower()
                    if nm:
                        names.add(nm)
            return 1.0 if len(names) >= min_distinct_tools else 0.0
        g = cls(_f, name="chain_answer_and_ntools")
        g.meta = {"ref_answer": ref_answer, "min_distinct_tools": int(min_distinct_tools)}
        return g

    @classmethod
    def called_any_of(cls, tool_names: list[str], ref_answer: Optional[str] = None) -> "Grader":
        """Score 1.0 iff any of the given tool names appears as a function_call
        (checked against both `name` and substrings in `arguments`). If
        `ref_answer` is supplied, also require the response to match.
        """
        wanted = {t.lower() for t in tool_names}
        want_ans = None if ref_answer is None else (ref_answer or "").strip().lower()
        def _f(task, response):
            traj = task.get("__trajectory__") or {}
            saw = False
            for item in traj.get("response", {}).get("output", []):
                if item.get("type") != "function_call":
                    continue
                nm = (item.get("name") or "").lower()
                if nm in wanted:
                    saw = True
                    break
                args = (item.get("arguments") or "").lower()
                if any(w in args for w in wanted):
                    saw = True
                    break
            if not saw:
                return 0.0
            if want_ans is None:
                return 1.0
            r = (response or "").strip().lower()
            return 1.0 if (r == want_ans or r.endswith(want_ans) or want_ans in r) else 0.0
        g = cls(_f, name="called_any_of")
        g.meta = {"tool_names": list(tool_names), "ref_answer": ref_answer}
        return g

    @classmethod
    def min_tool_calls_and_answer(cls, tool_name: str, min_calls: int, ref_answer: str) -> "Grader":
        """Score 1.0 iff `tool_name` was called at least `min_calls` times and
        the response matches `ref_answer`.
        """
        tn = tool_name.lower()
        want = (ref_answer or "").strip().lower()
        def _f(task, response):
            r = (response or "").strip().lower()
            if not (r == want or r.endswith(want) or want in r):
                return 0.0
            traj = task.get("__trajectory__") or {}
            cnt = sum(
                1 for item in traj.get("response", {}).get("output", [])
                if item.get("type") == "function_call" and (item.get("name") or "").lower() == tn
            )
            return 1.0 if cnt >= min_calls else 0.0
        g = cls(_f, name="min_tool_calls_and_answer")
        g.meta = {"tool_name": tool_name, "min_calls": int(min_calls), "ref_answer": ref_answer}
        return g

    @classmethod
    def subprocess_test(cls, stage_dir: str, solution_file: str, test_file: str, n_tests: int, timeout_s: int = 30) -> "Grader":
        """Run the staged test file after rollout. Score = fraction of `PASS`
        markers emitted by the test script (partial credit).
        """
        def _f(task, response):
            sol = os.path.join(stage_dir, solution_file)
            tst = os.path.join(stage_dir, test_file)
            if not (os.path.isfile(sol) and os.path.isfile(tst)):
                return 0.0
            try:
                proc = subprocess.run(
                    ["python3", tst], cwd=stage_dir, capture_output=True,
                    timeout=timeout_s, text=True,
                )
            except subprocess.TimeoutExpired:
                return 0.0
            out = (proc.stdout or "") + "\n" + (proc.stderr or "")
            passed = out.count("PASS")
            return min(1.0, passed / max(int(n_tests), 1))
        g = cls(_f, name="subprocess_test")
        g.meta = {
            "stage_dir": stage_dir, "solution_file": solution_file,
            "test_file": test_file, "n_tests": int(n_tests), "timeout_s": int(timeout_s),
        }
        return g
