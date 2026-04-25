# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
"""Prepare MMMLU for NeMo Gym.

Matches NeMo-Skills ``nemo_skills/dataset/mmmlu/prepare.py`` + ``mmmlu_utils.py``.
Adds Gym ``template_metadata.output_regex`` (single regex) for ``mcqa`` verification.
"""

import argparse
import json
import sys
import uuid
from pathlib import Path


_MM_DIR = Path(__file__).resolve().parent
if str(_MM_DIR) not in sys.path:
    sys.path.insert(0, str(_MM_DIR))

import mmmlu_utils as _u  # noqa: E402


BENCHMARK_DIR = Path(__file__).parent
DATA_DIR = BENCHMARK_DIR / "data"
OUTPUT_FPATH = DATA_DIR / "mmmlu_benchmark.jsonl"

LETTER_REGEX = r"\b\(?\s*([A-D]|[أ-د]|[অ]|[ব]|[ড]|[ঢ]|[Ａ]|[Ｂ]|[Ｃ]|[Ｄ])\s*\)?\.?\b"
GREEDY_REGEX = r"[\s\S]*" + LETTER_REGEX


def _mmmlu_output_regex_built() -> str:
    branches = [_u.MULTILINGUAL_ANSWER_PATTERN_TEMPLATE.format(rx) for rx in _u.MULTILINGUAL_ANSWER_REGEXES]
    branches.append(GREEDY_REGEX)
    return "(?:" + ")|(?:".join(branches) + ")"


MMMLU_OUTPUT_REGEX = _mmmlu_output_regex_built()


def format_entry(entry: dict, language: str) -> dict:
    """NeMo-Skills ``mmmlu/prepare.format_entry`` (verbatim)."""
    expected_answer = entry[_u.Schema.ANSWER]
    category = _u.subject2category.get(entry[_u.Schema.SUBJECT], "other")
    regexes = [
        _u.MULTILINGUAL_ANSWER_PATTERN_TEMPLATE.format(answer_regex)
        for answer_regex in _u.MULTILINGUAL_ANSWER_REGEXES
    ]
    regexes.append(GREEDY_REGEX)
    return {
        "expected_answer": expected_answer,
        "extract_from_boxed": False,
        "extract_regex": regexes,
        "subset_for_metrics": language,
        "relaxed": False,
        "category": category,
        **_u.get_mcq_fields(entry),
    }


def _to_gym_row(ne: dict) -> dict:
    """NeMo row -> Gym JSONL (``template_metadata`` for mcqa)."""
    prompt = ne["question"]
    letters = ["A", "B", "C", "D"]
    options = [{letters[i]: ne[letters[i]]} for i in range(4)]
    seed = json.dumps({"q": prompt, "a": ne["expected_answer"], "subset": ne["subset_for_metrics"]}, sort_keys=True)
    row_uuid = str(uuid.uuid5(uuid.NAMESPACE_URL, seed))
    return {
        "question": prompt,
        "options": options,
        "expected_answer": str(ne["expected_answer"]).strip().upper(),
        "template_metadata": {"output_regex": MMMLU_OUTPUT_REGEX},
        "subset_for_metrics": ne["subset_for_metrics"],
        "category": ne["category"],
        "uuid": row_uuid,
    }


def prepare(
    languages: list[str] | None = None,
    include_english: bool = False,
) -> Path:
    if languages is None:
        languages = list(_u.SUPPORTED_LANGUAGES)
    langs = [lang for lang in languages if lang != "EN-US"]
    valid_languages = set(_u.SUPPORTED_LANGUAGES)
    if include_english:
        valid_languages.add("EN-US")
        langs.append("EN-US")
    invalid = set(langs) - valid_languages
    if invalid:
        raise ValueError(f"Unsupported languages: {invalid}")

    datasets = _u.download_mmmlu_datasets(langs)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    count = 0
    with OUTPUT_FPATH.open("w", encoding="utf-8") as fout:
        for language, examples in datasets.items():
            for entry in examples:
                ne = format_entry(entry=entry, language=language)
                fout.write(json.dumps(_to_gym_row(ne), ensure_ascii=False) + "\n")
                count += 1
    print(f"Wrote {count} problems to {OUTPUT_FPATH}")
    return OUTPUT_FPATH


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--languages",
        default=_u.SUPPORTED_LANGUAGES,
        nargs="+",
        help="Languages to process.",
    )
    parser.add_argument(
        "--include_english",
        action="store_true",
        help="Include English split which corresponds to the original MMLU dataset.",
    )
    args = parser.parse_args()
    prepare(languages=args.languages, include_english=args.include_english)
