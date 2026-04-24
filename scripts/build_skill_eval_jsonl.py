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
"""Generate an ng_collect_rollouts-compatible JSONL from agent skills.

For every skill under --skills-dir that has an evals.json, emit 2 lines per
scenario — one with_skill=True and one with_skill=False. The skill_eval_agent
uses verifier_metadata.with_skill to decide whether to prepend SKILL.md.

Every record carries a provenance block so downstream tooling can attribute
changes between runs to a specific input:
- skill_md_sha: sha256(SKILL.md)[:12]
- evals_sha:    sha256(evals/evals.json bytes)[:12]
- fixtures_sha: sha256 over sorted (relpath, bytes) pairs for this scenario's fixtures
- judge_prompt_sha: sha256 of the judge prompt template bytes (if provided)
- harness_version: sha256 over the concatenated bytes of the harness source files
                   (workspace + judge + agent app.py by default); changes whenever
                   any of those files change.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

_DEFAULT_JUDGE_PROMPT = Path("resources_servers/skill_judge/prompt_templates/skill_judge.txt")
_DEFAULT_HARNESS_PATHS = (
    Path("resources_servers/skill_workspace/app.py"),
    Path("resources_servers/skill_judge/app.py"),
    Path("responses_api_agents/skill_eval_agent/app.py"),
)


def _sha12(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:12]


def _file_sha12(path: Path) -> str:
    return _sha12(path.read_bytes()) if path.is_file() else ""


def _concat_file_sha12(paths: list[Path]) -> str:
    h = hashlib.sha256()
    for p in paths:
        if not p.is_file():
            continue
        h.update(p.as_posix().encode("utf-8"))
        h.update(b"\0")
        h.update(p.read_bytes())
        h.update(b"\0")
    return h.hexdigest()[:12]


def _fixtures_sha12(skill_dir: Path, files: list[str]) -> str:
    """Hash (relpath, bytes) for each fixture listed by the scenario, sorted for
    determinism. Missing fixtures contribute their name only — the sha still
    changes if a fixture is added, removed, renamed, or edited."""
    h = hashlib.sha256()
    for rel in sorted(files):
        fpath = skill_dir / rel
        h.update(rel.encode("utf-8"))
        h.update(b"\0")
        if fpath.is_file():
            h.update(fpath.read_bytes())
        h.update(b"\0")
    return h.hexdigest()[:12]


def _load_skill(skill_dir: Path) -> tuple[str, bytes, list[dict]] | None:
    evals_path = skill_dir / "evals" / "evals.json"
    if not evals_path.is_file():
        return None
    evals_bytes = evals_path.read_bytes()
    data = json.loads(evals_bytes.decode("utf-8"))
    evals = data.get("evals") or []
    if not evals:
        return None
    skill_md_path = skill_dir / "SKILL.md"
    skill_md = skill_md_path.read_text(encoding="utf-8") if skill_md_path.is_file() else ""
    return skill_md, evals_bytes, evals


def build_jsonl(
    skills_dir: Path,
    output: Path,
    judge_prompt: Path = _DEFAULT_JUDGE_PROMPT,
    harness_paths: list[Path] | None = None,
) -> int:
    skills_dir = skills_dir.resolve()
    judge_prompt_sha = _file_sha12(judge_prompt)
    harness_version = _concat_file_sha12(list(harness_paths or _DEFAULT_HARNESS_PATHS))

    lines: list[str] = []
    for skill_dir in sorted(p for p in skills_dir.iterdir() if p.is_dir()):
        loaded = _load_skill(skill_dir)
        if loaded is None:
            continue
        skill_md, evals_bytes, evals = loaded
        skill_md_sha = _sha12(skill_md.encode("utf-8"))
        evals_sha = _sha12(evals_bytes)

        for scenario in evals:
            sid = scenario.get("id")
            prompt = scenario.get("prompt") or ""
            assertions = scenario.get("assertions") or []
            files = scenario.get("files") or []
            expected_output = scenario.get("expected_output")
            if sid is None or not assertions or not prompt:
                continue
            fixtures_sha = _fixtures_sha12(skill_dir, files)

            for with_skill in (True, False):
                record = {
                    "responses_create_params": {
                        "input": [{"role": "user", "content": prompt}],
                    },
                    "verifier_metadata": {
                        "skill_path": str(skill_dir),
                        "skill_name": skill_dir.name,
                        "skill_md_sha": skill_md_sha,
                        "evals_sha": evals_sha,
                        "fixtures_sha": fixtures_sha,
                        "judge_prompt_sha": judge_prompt_sha,
                        "harness_version": harness_version,
                        "scenario_id": int(sid),
                        "files": files,
                        "with_skill": with_skill,
                        "skill_md": skill_md if with_skill else "",
                        "assertions": assertions,
                        "expected_output": expected_output,
                    },
                }
                lines.append(json.dumps(record, ensure_ascii=False))

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return len(lines)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--skills-dir", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument(
        "--judge-prompt",
        type=Path,
        default=_DEFAULT_JUDGE_PROMPT,
        help="Path to the judge prompt template. Hashed into verifier_metadata.judge_prompt_sha.",
    )
    p.add_argument(
        "--harness-path",
        type=Path,
        action="append",
        default=None,
        help=(
            "Harness source file(s) whose bytes are hashed into verifier_metadata.harness_version. "
            "Repeat to include multiple files; defaults to the three skill-eval server app.py files."
        ),
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    n = build_jsonl(
        args.skills_dir,
        args.output,
        judge_prompt=args.judge_prompt,
        harness_paths=args.harness_path,
    )
    print(f"wrote {n} lines → {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
