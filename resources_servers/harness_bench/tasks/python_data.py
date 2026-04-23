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
"""python_data: tabular analytics over a pre-staged CSV.

Stage a deterministic CSV at `$HARNESS_BENCH_STAGE/python_data/{seed}_{diff}.csv`
and ask a question whose answer is computed at stage time.
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
) / "python_data"


def _stage_csv(seed: int, difficulty: int) -> tuple[Path, dict]:
    _STAGING_DIR.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed * 9973 + difficulty)
    n = int(50 * (2 ** difficulty))
    cities = ["Seattle", "Portland", "Boston", "Austin", "Denver", "Miami", "Tampa", "Salem"]
    rows = []
    for _ in range(n):
        city = rng.choice(cities)
        year = rng.choice([2023, 2024, 2025])
        revenue = round(rng.lognormvariate(10, 0.5), 2)
        rows.append((city, year, revenue))

    path = _STAGING_DIR / f"{seed}_{difficulty}.csv"
    with path.open("w") as f:
        f.write("city,year,revenue\n")
        for city, year, rev in rows:
            f.write(f"{city},{year},{rev}\n")

    return path, {"rows": rows}


def _answer_for_variant(variant: str, rows: list[tuple]) -> str:
    if variant == "top_city_2024":
        totals: dict[str, float] = {}
        for city, year, rev in rows:
            if year == 2024:
                totals[city] = totals.get(city, 0.0) + rev
        if not totals:
            return "None"
        return max(totals, key=totals.get)
    if variant == "count_s_cities":
        return str(sum(1 for c, _, _ in rows if c.startswith("S")))
    if variant == "mean_rev_2025":
        vals = [rev for _, y, rev in rows if y == 2025]
        if not vals:
            return "0.00"
        return f"{sum(vals) / len(vals):.2f}"
    raise ValueError(variant)


def generate(seed: int, difficulty: int) -> Task:
    difficulty = max(1, min(3, int(difficulty)))
    rng = random.Random(seed * 9973 + difficulty + 7)
    variant = rng.choice(["top_city_2024", "count_s_cities", "mean_rev_2025"])
    path, info = _stage_csv(seed, difficulty)
    answer = _answer_for_variant(variant, info["rows"])

    if variant == "top_city_2024":
        question = "Which city had the highest total revenue in 2024? Reply with just the city name."
        grader = Grader.exact_str(answer)
    elif variant == "count_s_cities":
        question = "How many rows are for cities whose name starts with the letter 'S'? Reply with only the integer."
        grader = Grader.exact_int(int(answer))
    else:
        question = "What is the mean revenue (to 2 decimal places) of all rows from 2025? Reply with only the number."
        grader = Grader.regex(rf"\b{answer}\b")

    prompt = (
        f"A CSV is staged at {path}. Columns: city, year, revenue.\n"
        f"{question}"
    )

    return Task(
        id=f"python_data/{variant}/d{difficulty}/s{seed}",
        category="python_data",
        prompt=prompt,
        grader=grader,
        difficulty=difficulty,
        seed=seed,
        max_turns=6,
        required_capabilities=[Capability.TERMINAL, Capability.CODE_EXECUTE, Capability.FILESYSTEM_READ],
        tags=["tabular", variant],
        metadata={
            "csv_path": str(path),
            "ref_answer": answer,
            "variant": variant,
            "n_rows": len(info["rows"]),
        },
    )
