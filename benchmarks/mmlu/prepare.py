# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
"""Prepare MMLU (Hendrycks) benchmark data for NeMo Gym (mcqa).

Ports NeMo-Skills' ``mmlu`` benchmark: loads per-subject test splits from HuggingFace
and writes Gym JSONL rows compatible with ``mcqa`` + ``lenient_answer_colon_md`` grading.
"""

import json
import uuid
from pathlib import Path

from datasets import load_dataset
from tqdm.auto import tqdm


# From https://github.com/hendrycks/test/blob/master/categories.py (NeMo-Skills / Hendrycks MMLU).
MMLU_SUBJECT_TO_CATEGORY: dict[str, list[str]] = {
    "abstract_algebra": ["math"],
    "anatomy": ["health"],
    "astronomy": ["physics"],
    "business_ethics": ["business"],
    "clinical_knowledge": ["health"],
    "college_biology": ["biology"],
    "college_chemistry": ["chemistry"],
    "college_computer_science": ["computer science"],
    "college_mathematics": ["math"],
    "college_medicine": ["health"],
    "college_physics": ["physics"],
    "computer_security": ["computer science"],
    "conceptual_physics": ["physics"],
    "econometrics": ["economics"],
    "electrical_engineering": ["engineering"],
    "elementary_mathematics": ["math"],
    "formal_logic": ["philosophy"],
    "global_facts": ["other"],
    "high_school_biology": ["biology"],
    "high_school_chemistry": ["chemistry"],
    "high_school_computer_science": ["computer science"],
    "high_school_european_history": ["history"],
    "high_school_geography": ["geography"],
    "high_school_government_and_politics": ["politics"],
    "high_school_macroeconomics": ["economics"],
    "high_school_mathematics": ["math"],
    "high_school_microeconomics": ["economics"],
    "high_school_physics": ["physics"],
    "high_school_psychology": ["psychology"],
    "high_school_statistics": ["math"],
    "high_school_us_history": ["history"],
    "high_school_world_history": ["history"],
    "human_aging": ["health"],
    "human_sexuality": ["culture"],
    "international_law": ["law"],
    "jurisprudence": ["law"],
    "logical_fallacies": ["philosophy"],
    "machine_learning": ["computer science"],
    "management": ["business"],
    "marketing": ["business"],
    "medical_genetics": ["health"],
    "miscellaneous": ["other"],
    "moral_disputes": ["philosophy"],
    "moral_scenarios": ["philosophy"],
    "nutrition": ["health"],
    "philosophy": ["philosophy"],
    "prehistory": ["history"],
    "professional_accounting": ["other"],
    "professional_law": ["law"],
    "professional_medicine": ["health"],
    "professional_psychology": ["psychology"],
    "public_relations": ["politics"],
    "security_studies": ["politics"],
    "sociology": ["culture"],
    "us_foreign_policy": ["politics"],
    "virology": ["health"],
    "world_religions": ["philosophy"],
}

MMLU_SUBJECTS: tuple[str, ...] = tuple(MMLU_SUBJECT_TO_CATEGORY.keys())

BENCHMARK_DIR = Path(__file__).parent
DATA_DIR = BENCHMARK_DIR / "data"
OUTPUT_FPATH = DATA_DIR / "mmlu_benchmark.jsonl"

HF_CANDIDATES = ("lukaemon/mmlu", "cais/mmlu")


def _load_dataset_kwargs(repo_id: str) -> dict:
    """``lukaemon/mmlu`` ships a dataset script (Hendrycks tarball) and needs trust_remote_code."""
    if repo_id == "lukaemon/mmlu":
        return {"trust_remote_code": True}
    return {}


def _load_mmlu_subject(repo_id: str, subject: str):
    return load_dataset(repo_id, subject, split="test", **_load_dataset_kwargs(repo_id))


def _find_hf_repo() -> str:
    last_err: Exception | None = None
    for repo in HF_CANDIDATES:
        try:
            _load_mmlu_subject(repo, MMLU_SUBJECTS[0])
            return repo
        except Exception as e:  # noqa: BLE001 — try next mirror
            last_err = e
    raise RuntimeError(f"Could not load MMLU from {HF_CANDIDATES}: {last_err}")


def _normalize_hf_row(ex: dict) -> tuple[str, list[str], str]:
    """Return ``(question_stem, [four choice strings], answer_letter)`` for different HF MMLU layouts.

    - ``lukaemon/mmlu`` (script): ``input``, ``A``..``D``, ``target`` (letter).
    - Other mirrors often use: ``question``, ``choices`` (list), ``answer`` (index or letter).
    """
    if "input" in ex and "target" in ex and all(k in ex for k in ("A", "B", "C", "D")):
        stem = str(ex["input"]).strip()
        choices = [str(ex[k]) for k in ("A", "B", "C", "D")]
        letter = str(ex["target"]).strip().upper()
        if len(letter) != 1 or letter not in "ABCD":
            raise ValueError(f"Unexpected target label: {letter!r}")
        return stem, choices, letter

    if "choices" in ex and "answer" in ex:
        stem = str(ex.get("question") or ex.get("input") or "").strip()
        choices = [str(c) for c in ex["choices"]]
        if len(choices) != 4:
            raise ValueError(f"Expected 4 choices, got {len(choices)}")
        ans = ex["answer"]
        if isinstance(ans, str) and len(ans) == 1 and ans.upper() in "ABCD":
            letter = ans.upper()
        else:
            letter = chr(ord("A") + int(ans))
        return stem, choices, letter

    raise ValueError(f"Unknown MMLU row schema; keys={sorted(ex.keys())}")


def _row_from_parts(subject: str, stem: str, choices: list[str], letter: str) -> dict:
    if len(choices) != 4:
        raise ValueError(f"Expected 4 choices for {subject}, got {len(choices)}")
    letters = ["A", "B", "C", "D"]
    options = [{letters[i]: choices[i]} for i in range(4)]
    options_text = "\n".join(f"{letters[i]}) {choices[i]}" for i in range(4))
    seed = json.dumps({"subject": subject, "question": stem, "answer": letter}, sort_keys=True)
    row_uuid = str(uuid.uuid5(uuid.NAMESPACE_URL, seed))
    subset = MMLU_SUBJECT_TO_CATEGORY[subject][0]
    return {
        "question": stem,
        "options_text": options_text,
        "options": options,
        "expected_answer": letter,
        "subset_for_metrics": subset,
        "subject": subject,
        "uuid": row_uuid,
    }


def prepare() -> Path:
    """Download MMLU test splits and write Gym JSONL."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    repo = _find_hf_repo()
    print(f"Using HuggingFace dataset: {repo}")

    count = 0
    with OUTPUT_FPATH.open("w", encoding="utf-8") as fout:
        for subject in tqdm(MMLU_SUBJECTS, desc="MMLU subjects"):
            ds = _load_mmlu_subject(repo, subject)
            for ex in ds:
                stem, choices, letter = _normalize_hf_row(ex)
                row = _row_from_parts(subject, stem, choices, letter)
                fout.write(json.dumps(row, ensure_ascii=False) + "\n")
                count += 1

    print(f"Wrote {count} problems to {OUTPUT_FPATH}")
    return OUTPUT_FPATH


if __name__ == "__main__":
    prepare()
