# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Copied from NeMo-Skills ``nemo_skills/dataset/mmmlu/mmmlu_utils.py`` with:
# - CSV loading uses stdlib ``csv`` (equivalent to ``pandas.read_csv(..., index_col=0)``)
# - downloads go under ``benchmarks/mmmlu/data/`` next to this file

import csv
import os
import urllib.request
from io import StringIO
from pathlib import Path


_DATA_DIR = Path(__file__).resolve().parent / "data"

SUPPORTED_LANGUAGES = [
    "AR-XY",
    "BN-BD",
    "DE-DE",
    "ES-LA",
    "FR-FR",
    "HI-IN",
    "ID-ID",
    "IT-IT",
    "JA-JP",
    "KO-KR",
    "PT-BR",
    "ZH-CN",
    "SW-KE",
    "YO-NG",
]

subject2category = {
    "abstract_algebra": "stem",
    "anatomy": "other",
    "astronomy": "stem",
    "business_ethics": "other",
    "clinical_knowledge": "other",
    "college_biology": "stem",
    "college_chemistry": "stem",
    "college_computer_science": "stem",
    "college_mathematics": "stem",
    "college_medicine": "other",
    "college_physics": "stem",
    "computer_security": "stem",
    "conceptual_physics": "stem",
    "econometrics": "social_sciences",
    "electrical_engineering": "stem",
    "elementary_mathematics": "stem",
    "formal_logic": "humanities",
    "global_facts": "other",
    "high_school_biology": "stem",
    "high_school_chemistry": "stem",
    "high_school_computer_science": "stem",
    "high_school_european_history": "humanities",
    "high_school_geography": "social_sciences",
    "high_school_government_and_politics": "social_sciences",
    "high_school_macroeconomics": "social_sciences",
    "high_school_mathematics": "stem",
    "high_school_microeconomics": "social_sciences",
    "high_school_physics": "stem",
    "high_school_psychology": "social_sciences",
    "high_school_statistics": "stem",
    "high_school_us_history": "humanities",
    "high_school_world_history": "humanities",
    "human_aging": "other",
    "human_sexuality": "social_sciences",
    "international_law": "humanities",
    "jurisprudence": "humanities",
    "logical_fallacies": "humanities",
    "machine_learning": "stem",
    "management": "other",
    "marketing": "other",
    "medical_genetics": "other",
    "miscellaneous": "other",
    "moral_disputes": "humanities",
    "moral_scenarios": "humanities",
    "nutrition": "other",
    "philosophy": "humanities",
    "prehistory": "humanities",
    "professional_accounting": "other",
    "professional_law": "humanities",
    "professional_medicine": "other",
    "professional_psychology": "social_sciences",
    "public_relations": "social_sciences",
    "security_studies": "social_sciences",
    "sociology": "social_sciences",
    "us_foreign_policy": "social_sciences",
    "virology": "other",
    "world_religions": "humanities",
}

QUERY_TEMPLATE_MULTICHOICE = """
Answer the following multiple choice question. The last line of your response should be of the following format: 'Answer: $LETTER' (without quotes) where LETTER is one of ABCD. Think step by step before answering.

{Question}

A) {A}
B) {B}
C) {C}
D) {D}
""".strip()

MULTILINGUAL_ANSWER_PATTERN_TEMPLATE = "(?i){}[ \t]*([A-D]|[أ-د]|[অ]|[ব]|[ড]|[ঢ]|[Ａ]|[Ｂ]|[Ｃ]|[Ｄ])"

MULTILINGUAL_ANSWER_REGEXES = [
    r"Answer\s*:",
    r"Answer\s*:​​​​​​",
    r"উত্তর\s*:",
    r"उत्तर\s*:",
    r"উত্তরঃ",
    r"উত্তর\s*:",
    r"Antwort\s*:",
    r"답변\s*:",
    r"정답\s*:",
    r"답\s*:",
    r"答案\s*：",
    r"答案\s*:",
    r"答\s*：",
    r"答\s*:",
    r"答复\s*：",
    r"答曰\s*：",
    r"الإجابة:",
    r"الجواب:",
    r"إجابة:",
    r"الإجابة النهائية:",
    r"الإجابة الصحيحة:",
    r"الإجابة الصحيحة هي:",
    r"الإجابة هي:",
    r"الجواب النهائي:",
    r"Respuesta\s*:",
    r"Risposta\s*:",
    r"答え\s*:",
    r"答え\s*：",
    r"回答\s*:",
    r"回答\s*：",
    r"解答\s*:",
    r"Jawaban\s*:",
    r"Réponse\s*:",
    r"Resposta\s*:",
    r"Jibu\s*:",
    r"Idahun\s*:",
    r"Ìdáhùn\s*:",
    r"Idáhùn\s*:",
    r"Àmọ̀nà\s*:",
    r"Àdáhùn\s*:",
    r"Ànúgọ\s*:",
    r"Àṣàyàn\s*:",
]


class Schema:
    ANSWER: str = "Answer"
    QUESTION: str = "Question"
    SUBJECT: str = "Subject"
    OPTIONS: list[str] = ["A", "B", "C", "D"]


def _read_mmmlu_csv(download_dst_path: Path) -> list[dict]:
    """Match ``pandas.read_csv(path, index_col=0)`` row dicts (first column dropped from fields)."""
    required = {Schema.QUESTION, "A", "B", "C", "D", Schema.SUBJECT, Schema.ANSWER}
    text = download_dst_path.read_text(encoding="utf-8")
    reader = csv.reader(StringIO(text))
    header = next(reader)
    if not header:
        return []
    if required.issubset(set(header)):
        keys = header
        strip_first = False
    elif len(header) > 1 and required.issubset(set(header[1:])):
        keys = header[1:]
        strip_first = True
    else:
        raise ValueError(f"Unexpected MMMLU CSV header: {header!r}")

    rows: list[dict] = []
    for parts in reader:
        if not parts:
            continue
        if strip_first and len(parts) > len(keys):
            parts = parts[1:]
        if len(parts) != len(keys):
            continue
        rows.append(dict(zip(keys, parts, strict=True)))
    return rows


def download_mmmlu_datasets(languages: list[str]) -> dict[str, list[dict]]:
    OPENAI_PUBLIC_URL = "https://openaipublic.blob.core.windows.net/simple-evals/{}"
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    mmmlu_datasets: dict[str, list[dict]] = {}
    for language in languages:
        suffix = "mmlu.csv" if language == "EN-US" else f"mmlu_{language}.csv"
        download_dst_path = _DATA_DIR / suffix
        if os.path.exists(download_dst_path):
            print(f"Skipping download of {suffix} because it already exists")
        else:
            url = OPENAI_PUBLIC_URL.format(suffix)
            urllib.request.urlretrieve(url, download_dst_path)
            if not os.path.exists(download_dst_path):
                raise RuntimeError(f"Failed to download {suffix}")

        examples = _read_mmmlu_csv(download_dst_path)
        mmmlu_datasets[language] = examples
    return mmmlu_datasets


def format_multichoice_question(row: dict) -> str:
    return QUERY_TEMPLATE_MULTICHOICE.format(**row)


def get_mcq_fields(entry: dict) -> dict:
    options_dict = {letter: entry[letter] for letter in Schema.OPTIONS}
    options_text = "\n".join(f"{letter}) {option}" for letter, option in options_dict.items())
    prompt = format_multichoice_question(entry)
    return {"question": prompt, "options": options_text, **options_dict}
