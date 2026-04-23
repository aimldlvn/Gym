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
"""skill_invoke: tasks whose natural solution invokes a named skill.

Skill names are abstract strings. A harness adapter maps them to whatever
skill surface the harness exposes. The grader accepts either a direct
function_call whose name matches the skill, or any function_call whose
arguments substring-match the skill name.
"""

from __future__ import annotations

import random

from resources_servers.harness_bench.capabilities import Capability
from resources_servers.harness_bench.grader import Grader
from resources_servers.harness_bench.task import Task


# (skill_name, prompt) pairs. Prompts name the target domain; the model has to
# recognize which skill fits.
_SKILL_TEMPLATES: list[tuple[str, str]] = [
    ("arxiv",
     "I want to quickly pull the abstract and authors of the arXiv paper with ID 2402.03300. "
     "Please use the skill best suited for querying the arXiv API so I don't have to shell out."),
    ("github",
     "Give me a one-line summary of what the open issues look like on the PyTorch GitHub repo "
     "(open count, most-recent label). Use the skill for talking to GitHub."),
    ("nano-pdf",
     "I have a PDF called `/tmp/report.pdf` and want to change the title on page 1 to \"Q2 Revenue\". "
     "Use the skill designed for natural-language PDF editing."),
    ("ocr-and-documents",
     "Extract the text from a scanned receipt at `/tmp/receipt.jpg`. Use the OCR skill."),
    ("google-workspace",
     "I need to append one row to my Google Sheet. Use the skill that talks to Google Workspace."),
    ("linear",
     "Create a Linear issue titled \"API timeout on /users\". Use the Linear skill."),
    ("notion",
     "Create a page in my Notion workspace summarising today's meeting notes. Use the Notion skill."),
    ("polymarket",
     "What's the current yes-price on the top political Polymarket market? Use the Polymarket skill."),
    ("openhue",
     "Turn the living-room Hue lights to 50% warm white. Use the Hue skill."),
    ("arxiv",
     "Find 3 recent arXiv papers about MoE routing. Use the arXiv skill."),
]


def generate(seed: int, difficulty: int) -> Task:
    difficulty = max(1, min(3, int(difficulty)))
    rng = random.Random(seed * 11117 + difficulty)
    skill_name, prompt = rng.choice(_SKILL_TEMPLATES)

    return Task(
        id=f"skill_invoke/{skill_name}/d{difficulty}/s{seed}",
        category="skill_invoke",
        prompt=prompt,
        grader=Grader.called_any_of([skill_name]),
        difficulty=difficulty,
        seed=seed,
        max_turns=4,
        required_capabilities=[Capability.SKILL_INVOKE],
        tags=["skills", skill_name],
        metadata={"target_skill": skill_name},
    )
