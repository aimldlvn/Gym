# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
"""Prepare MMLU-Redux 2.0 for NeMo Gym.

Logic matches NeMo-Skills ``nemo_skills/dataset/mmlu-redux/prepare.py`` (including
``format_entry`` / ``get_mcq_fields``). Rows are then mapped to Gym ``mcqa`` JSONL
(``question``, ``options_text``, ``options``, ``uuid``).
"""

import argparse
import json
import uuid
from pathlib import Path

from datasets import load_dataset
from tqdm.auto import tqdm


# mmlu subcategories from https://github.com/hendrycks/test/blob/master/categories.py
# (same as NeMo-Skills ``mmlu-redux/prepare.py``).
subcategories = {
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


def get_mcq_fields(question: str, choices: list) -> dict:
    """Same as NeMo-Skills ``nemo_skills/dataset/utils.get_mcq_fields``."""
    options_dict = {chr(ord("A") + i): option for i, option in enumerate(choices)}
    options_text = "\n".join(f"{letter}) {option}" for letter, option in options_dict.items())
    question = question.strip("\n")
    return {
        "problem": f"{question}\n\n{options_text}",
        "options": options_text,
        **options_dict,
    }


# dataset preparing strategy adapted from ZeroEval (NeMo-Skills ``format_entry``).
def format_entry(entry: dict, category: str) -> dict | None:
    if entry["error_type"] == "ok":
        final_answer = chr(65 + int(entry["answer"]))
    elif entry["error_type"] == "wrong_groundtruth" and entry["correct_answer"] in list("ABCD"):
        final_answer = "correct_answer"
    else:
        return None
    return {
        "expected_answer": final_answer,
        "subset_for_metrics": subcategories[category][0],
        "subcategory": category,
        "source": entry["source"],
        **get_mcq_fields(entry["question"], entry["choices"]),
    }


def _to_gym_row(entry: dict, category: str, ne: dict) -> dict:
    """NeMo jsonl row -> Gym ``mcqa`` row (prompt uses stem + options_text)."""
    letters = ["A", "B", "C", "D"]
    choices = entry["choices"]
    mcq = get_mcq_fields(entry["question"], entry["choices"])
    stem = entry["question"].strip()
    options = [{letters[i]: str(choices[i])} for i in range(4)]
    seed = json.dumps({"category": category, "question": stem, "answer": ne["expected_answer"]}, sort_keys=True)
    row_uuid = str(uuid.uuid5(uuid.NAMESPACE_URL, seed))
    return {
        "question": stem,
        "options_text": mcq["options"],
        "options": options,
        "expected_answer": ne["expected_answer"],
        "subset_for_metrics": ne["subset_for_metrics"],
        "subcategory": ne["subcategory"],
        "source": ne["source"],
        "uuid": row_uuid,
    }


BENCHMARK_DIR = Path(__file__).parent
DATA_DIR = BENCHMARK_DIR / "data"
OUTPUT_FPATH = DATA_DIR / "mmlu-redux_benchmark.jsonl"


def prepare(split: str = "test") -> Path:
    if split != "test":
        raise ValueError("Gym benchmark config only supports split=test (NeMo-Skills only exposes test).")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    count = 0
    with OUTPUT_FPATH.open("w", encoding="utf-8") as fout:
        for category in tqdm(subcategories, desc="MMLU-Redux categories"):
            dataset = load_dataset("edinburgh-dawg/mmlu-redux-2.0", name=category, split="test")
            for entry in dataset:
                ne = format_entry(entry, category)
                if ne is None:
                    continue
                gym = _to_gym_row(entry, category, ne)
                fout.write(json.dumps(gym, ensure_ascii=False) + "\n")
                count += 1
    print(f"Wrote {count} problems to {OUTPUT_FPATH}")
    return OUTPUT_FPATH


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", default="test", choices=["test"], help="Dataset split (NeMo-Skills: test only).")
    args = parser.parse_args()
    prepare(split=args.split)
