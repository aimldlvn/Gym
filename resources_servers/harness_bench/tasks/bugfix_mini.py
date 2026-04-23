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
"""bugfix_mini: procedural single-file Python bugfix tasks with partial credit.

Stages a buggy.py and a test_solution.py under
`$HARNESS_BENCH_STAGE/bugfix/{name}_{seed}_{difficulty}/`. The agent edits the
buggy module and runs the tests. Grader runs `python3 test_solution.py` after
rollout and scores = fraction of `PASS` markers printed.
"""

from __future__ import annotations

import os
import random
import textwrap
from pathlib import Path

from resources_servers.harness_bench.capabilities import Capability
from resources_servers.harness_bench.grader import Grader
from resources_servers.harness_bench.task import Task


_STAGING_DIR = Path(
    os.environ.get("HARNESS_BENCH_STAGE", str(Path.home() / ".harness_bench" / "stage"))
) / "bugfix"


_TEMPLATES = [
    (
        "factorial",
        textwrap.dedent("""
            def factorial(n):
                if n == 0:
                    return 1
                return n * factorial(n - 1)
        """).strip(),
        [
            ("off-by-one recursion", textwrap.dedent("""
                def factorial(n):
                    if n == 0:
                        return 1
                    return n * factorial(n - 2)
            """).strip()),
            ("wrong base case", textwrap.dedent("""
                def factorial(n):
                    if n == 1:
                        return 1
                    return n * factorial(n - 1)
            """).strip()),
        ],
        textwrap.dedent("""
            from buggy import factorial
            cases = [(0, 1), (1, 1), (3, 6), (5, 120), (6, 720)]
            for n, want in cases:
                try:
                    got = factorial(n)
                    if got == want:
                        print(f"PASS factorial({n})=={want}")
                    else:
                        print(f"FAIL factorial({n}) got {got} want {want}")
                except Exception as e:
                    print(f"FAIL factorial({n}): {e}")
        """).strip(),
    ),
    (
        "is_palindrome",
        textwrap.dedent("""
            def is_palindrome(s):
                s = s.lower()
                return s == s[::-1]
        """).strip(),
        [
            ("forgot lower()", textwrap.dedent("""
                def is_palindrome(s):
                    return s == s[::-1]
            """).strip()),
            ("wrong slice", textwrap.dedent("""
                def is_palindrome(s):
                    s = s.lower()
                    return s == s[::1]
            """).strip()),
        ],
        textwrap.dedent("""
            from buggy import is_palindrome
            cases = [("racecar", True), ("RaceCar", True), ("hello", False), ("noon", True), ("abba", True)]
            for s, want in cases:
                try:
                    got = is_palindrome(s)
                    if got == want:
                        print(f"PASS is_palindrome({s!r})=={want}")
                    else:
                        print(f"FAIL is_palindrome({s!r}) got {got} want {want}")
                except Exception as e:
                    print(f"FAIL is_palindrome({s!r}): {e}")
        """).strip(),
    ),
    (
        "fib",
        textwrap.dedent("""
            def fib(n):
                if n < 2:
                    return n
                a, b = 0, 1
                for _ in range(n - 1):
                    a, b = b, a + b
                return b
        """).strip(),
        [
            ("wrong init", textwrap.dedent("""
                def fib(n):
                    if n < 2:
                        return n
                    a, b = 1, 1
                    for _ in range(n - 1):
                        a, b = b, a + b
                    return b
            """).strip()),
            ("off by one", textwrap.dedent("""
                def fib(n):
                    if n < 2:
                        return n
                    a, b = 0, 1
                    for _ in range(n):
                        a, b = b, a + b
                    return b
            """).strip()),
        ],
        textwrap.dedent("""
            from buggy import fib
            cases = [(0, 0), (1, 1), (2, 1), (5, 5), (7, 13), (10, 55)]
            for n, want in cases:
                try:
                    got = fib(n)
                    if got == want:
                        print(f"PASS fib({n})=={want}")
                    else:
                        print(f"FAIL fib({n}) got {got} want {want}")
                except Exception as e:
                    print(f"FAIL fib({n}): {e}")
        """).strip(),
    ),
    (
        "binary_search",
        textwrap.dedent("""
            def binary_search(arr, target):
                lo, hi = 0, len(arr) - 1
                while lo <= hi:
                    mid = (lo + hi) // 2
                    if arr[mid] == target:
                        return mid
                    if arr[mid] < target:
                        lo = mid + 1
                    else:
                        hi = mid - 1
                return -1
        """).strip(),
        [
            ("wrong loop bound", textwrap.dedent("""
                def binary_search(arr, target):
                    lo, hi = 0, len(arr) - 1
                    while lo < hi:
                        mid = (lo + hi) // 2
                        if arr[mid] == target:
                            return mid
                        if arr[mid] < target:
                            lo = mid + 1
                        else:
                            hi = mid - 1
                    return -1
            """).strip()),
            ("swapped compare", textwrap.dedent("""
                def binary_search(arr, target):
                    lo, hi = 0, len(arr) - 1
                    while lo <= hi:
                        mid = (lo + hi) // 2
                        if arr[mid] == target:
                            return mid
                        if arr[mid] > target:
                            lo = mid + 1
                        else:
                            hi = mid - 1
                    return -1
            """).strip()),
        ],
        textwrap.dedent("""
            from buggy import binary_search
            arr = [1, 3, 5, 7, 9, 11, 13, 15]
            cases = [(1, 0), (5, 2), (15, 7), (7, 3), (9, 4), (2, -1)]
            for target, want in cases:
                try:
                    got = binary_search(arr, target)
                    if got == want:
                        print(f"PASS binary_search({target})=={want}")
                    else:
                        print(f"FAIL binary_search({target}) got {got} want {want}")
                except Exception as e:
                    print(f"FAIL binary_search({target}): {e}")
        """).strip(),
    ),
]


def _stage_task(seed: int, difficulty: int, template_idx: int) -> tuple[Path, dict]:
    name, _canonical, bugs, test_src = _TEMPLATES[template_idx]
    rng = random.Random(seed * 4003 + difficulty + template_idx)
    bug_idx = rng.randrange(len(bugs))
    _bug_desc, buggy_src = bugs[bug_idx]

    d = _STAGING_DIR / f"{name}_{seed}_{difficulty}"
    d.mkdir(parents=True, exist_ok=True)
    (d / "buggy.py").write_text(buggy_src + "\n")
    (d / "test_solution.py").write_text(test_src + "\n")
    n_tests = test_src.count("PASS ")
    if n_tests == 0:
        n_tests = test_src.count("cases")
    return d, {"n_tests": max(n_tests, 1), "bug_idx": bug_idx, "template": name}


def generate(seed: int, difficulty: int) -> Task:
    difficulty = max(1, min(3, int(difficulty)))
    rng = random.Random(seed * 4003 + difficulty)
    template_idx = rng.randrange(len(_TEMPLATES))
    path, info = _stage_task(seed, difficulty, template_idx)
    name = info["template"]
    n_tests = info["n_tests"]

    prompt = (
        f"A Python module `{path}/buggy.py` has a bug. The test file at "
        f"`{path}/test_solution.py` contains {n_tests} assertions (one per test case). "
        "Read the buggy module, identify the bug, fix it in place, then run the tests "
        "using your terminal to verify. Each passing test prints `PASS ...`. Aim for "
        "all tests to pass.\n\n"
        "When you are done, reply with a one-line summary."
    )

    return Task(
        id=f"bugfix_mini/{name}/d{difficulty}/s{seed}",
        category="bugfix_mini",
        prompt=prompt,
        grader=Grader.subprocess_test(
            stage_dir=str(path), solution_file="buggy.py",
            test_file="test_solution.py", n_tests=n_tests, timeout_s=20,
        ),
        difficulty=difficulty,
        seed=seed,
        max_turns=10,
        required_capabilities=[
            Capability.FILESYSTEM_READ,
            Capability.FILESYSTEM_WRITE,
            Capability.TERMINAL,
        ],
        tags=["swe-mini", name],
        metadata={"stage_dir": str(path), "template": name, "n_tests": n_tests},
    )
