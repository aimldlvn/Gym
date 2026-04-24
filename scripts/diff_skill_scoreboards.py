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
"""Compute per-skill with-vs-without deltas from a rollout JSONL.

Single-file mode: prints a scoreboard (skill, with, without, delta, provenance).
Two-file mode: diff of v1 vs v2 — per-skill delta-of-deltas with provenance
changes highlighted so you can attribute a delta-of-delta to what actually
changed (skill text, evals, fixtures, judge prompt, harness version).

Provenance fields read from `verifier_metadata`: skill_md_sha, evals_sha,
fixtures_sha, judge_prompt_sha, harness_version. Missing fields are treated
as empty — legacy rollouts still work, they just carry less information.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import sys
from dataclasses import dataclass, field
from pathlib import Path


_PROV_FIELDS = ("skill_md_sha", "evals_sha", "fixtures_sha", "judge_prompt_sha", "harness_version")
_PROV_ABBREV = {
    "skill_md_sha": "md",
    "evals_sha": "evals",
    "fixtures_sha": "fx",
    "judge_prompt_sha": "judge",
    "harness_version": "harness",
}


@dataclass
class SkillStats:
    with_scores: list[float] = field(default_factory=list)
    without_scores: list[float] = field(default_factory=list)
    prov: dict[str, str] = field(default_factory=dict)

    @property
    def mean_with(self) -> float:
        return statistics.fmean(self.with_scores) if self.with_scores else float("nan")

    @property
    def mean_without(self) -> float:
        return statistics.fmean(self.without_scores) if self.without_scores else float("nan")

    @property
    def delta(self) -> float:
        return self.mean_with - self.mean_without


def _sha12(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:12]


def _extract_prov(md: dict, with_skill: bool) -> dict[str, str]:
    prov = {f: str(md.get(f) or "") for f in _PROV_FIELDS}
    # Legacy rollouts carried skill_md but not skill_md_sha; back-fill when possible.
    if not prov["skill_md_sha"] and with_skill:
        prov["skill_md_sha"] = _sha12(str(md.get("skill_md") or "").encode("utf-8"))
    return prov


def load_scoreboard(path: Path) -> dict[str, SkillStats]:
    """Bucket rewards by skill + with_skill flag. Returns {skill_name: SkillStats}."""
    buckets: dict[str, SkillStats] = {}
    with path.open() as f:
        for line in f:
            r = json.loads(line)
            md = r.get("verifier_metadata") or {}
            skill_name = md.get("skill_name")
            if not skill_name:
                continue
            reward = r.get("reward")
            if reward is None:
                continue
            with_skill = bool(md.get("with_skill"))
            record_prov = _extract_prov(md, with_skill=with_skill)

            stats = buckets.get(skill_name)
            if stats is None:
                stats = SkillStats()
                buckets[skill_name] = stats
            # Fill in prov fields as we see them; don't overwrite established values.
            for k, v in record_prov.items():
                if v and not stats.prov.get(k):
                    stats.prov[k] = v
            (stats.with_scores if with_skill else stats.without_scores).append(float(reward))
    return buckets


def _fmt_delta(d: float) -> str:
    return f"{d:+.3f}"


def print_scoreboard(board: dict[str, SkillStats], label: str) -> None:
    print(f"\n=== {label} ===")
    print(
        f"{'skill':24s}  {'with':>8s}  {'without':>8s}  {'delta':>8s}  "
        f"{'n_with':>6s}  {'n_wo':>6s}  {'md':>13s}  {'evals':>13s}  {'fx':>13s}  {'judge':>13s}  {'harness':>13s}"
    )
    print("-" * 148)
    for name in sorted(board):
        s = board[name]
        p = s.prov
        print(
            f"{name:24s}  {s.mean_with:8.3f}  {s.mean_without:8.3f}  "
            f"{_fmt_delta(s.delta)}  {len(s.with_scores):6d}  {len(s.without_scores):6d}  "
            f"{p.get('skill_md_sha') or '—':>13s}  {p.get('evals_sha') or '—':>13s}  "
            f"{p.get('fixtures_sha') or '—':>13s}  {p.get('judge_prompt_sha') or '—':>13s}  "
            f"{p.get('harness_version') or '—':>13s}"
        )


def _prov_change_tag(p1: dict[str, str], p2: dict[str, str]) -> tuple[str, str]:
    """Return (diff_tag, note). diff_tag lists which provenance fields changed;
    note indicates attribution confidence — 'same-all' only when every field is
    known on both sides and matches, 'partial' when some fields are unknown,
    'legacy' when neither side has any provenance."""
    changed = []
    both_known = 0
    total_populated = 0
    for f in _PROV_FIELDS:
        a, b = p1.get(f, ""), p2.get(f, "")
        if a and b:
            both_known += 1
            if a != b:
                changed.append(_PROV_ABBREV[f])
        elif a or b:
            # One side has provenance, the other doesn't — definitely a change.
            changed.append(f"{_PROV_ABBREV[f]}?")
        if a or b:
            total_populated += 1

    if total_populated == 0:
        return "—", "legacy"
    if changed:
        return "+".join(changed), ""
    if both_known == len(_PROV_FIELDS):
        return "—", "same-all"
    return "—", f"partial({both_known}/{len(_PROV_FIELDS)})"


def print_diff(v1: dict[str, SkillStats], v2: dict[str, SkillStats]) -> None:
    print(
        f"\n{'skill':24s}  {'v1 delta':>9s}  {'v2 delta':>9s}  {'change':>8s}  "
        f"{'provenance diff':>20s}  {'note':>10s}"
    )
    print("-" * 92)
    for name in sorted(set(v1) | set(v2)):
        s1, s2 = v1.get(name), v2.get(name)
        if s1 is None or s2 is None:
            side = "v2 only" if s1 is None else "v1 only"
            print(
                f"{name:24s}  {'—':>9s}  {'—':>9s}  {'—':>8s}  "
                f"{'—':>20s}  {side:>10s}"
            )
            continue
        change = s2.delta - s1.delta
        prov_diff, note = _prov_change_tag(s1.prov, s2.prov)
        print(
            f"{name:24s}  {_fmt_delta(s1.delta):>9s}  {_fmt_delta(s2.delta):>9s}  "
            f"{_fmt_delta(change):>8s}  {prov_diff:>20s}  {note:>10s}"
        )


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("rollouts", type=Path, help="Rollout JSONL (v1 if --v2 is given, else just scoreboard).")
    p.add_argument("--v2", type=Path, default=None, help="If provided, diff v1 vs v2 per skill.")
    p.add_argument("--v1-label", type=str, default="v1")
    p.add_argument("--v2-label", type=str, default="v2")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv if argv is not None else sys.argv[1:])
    v1 = load_scoreboard(args.rollouts)
    if args.v2 is None:
        print_scoreboard(v1, label=str(args.rollouts))
        return 0
    v2 = load_scoreboard(args.v2)
    print_scoreboard(v1, label=f"{args.v1_label}: {args.rollouts}")
    print_scoreboard(v2, label=f"{args.v2_label}: {args.v2}")
    print_diff(v1, v2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
