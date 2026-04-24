(skill-eval-scoreboard)=

# Evaluating Agent Skills, Part 2: Running the Scoreboard

Part 1 ({ref}`skill-eval-harness`) built the infrastructure. This part covers what you do with it: write scenarios, generate JSONL, run the scoreboard, and read the result with the right amount of skepticism.

By the end, you will:

- Understand **with-skill vs without-skill delta** — what it measures and why it beats absolute scoring.
- Write a good `evals.json` and know how assertions fail you.
- Generate input JSONL, run the full scoreboard, and compute per-skill deltas.
- Know when to trust a delta and when to ignore it.

:::{button-ref} index
:color: secondary
:outline:
:ref-type: doc

< Back to Building Environments
:::

---

## Prerequisites

- {ref}`skill-eval-harness` — Part 1, the infrastructure this part runs on
- `ng_run` is up and `ng_status` shows all four servers healthy

---

## The methodology: with-vs-without delta

Absolute reward scores lie. If a skill scores 0.90 across 3 scenarios, is it good? Depends entirely on what the model does *without* the skill. A 0.90 skill on top of a 0.90 baseline is noise; a 0.90 skill on top of a 0.40 baseline is +0.50 of real lift.

The harness runs every scenario **twice** — once with `SKILL.md` prepended to the system prompt, once without. Same prompt, same seed workspace, same model, same tools. The only difference is whether the skill's guidance is in context.

$$\text{delta} = \text{mean\_reward}(\text{with\_skill}) - \text{mean\_reward}(\text{without\_skill})$$

Positive delta = the skill is teaching the model something it didn't already know. Zero delta = either redundant or ceiling-clipped (more on that below). Negative delta = diagnostic signal worth chasing, not noise.

---

## Step 1: Write `evals.json`

Each skill has a `.claude/skills/<skill-name>/evals/evals.json` with 3–5 scenarios:

```json
{
  "evals": [
    {
      "id": 1,
      "prompt": "Review the benchmark at evals/files/sample_benchmark/ and produce a merge-readiness report.",
      "files": ["evals/files/sample_benchmark/configs/foo.yaml",
                "evals/files/sample_benchmark/app.py"],
      "assertions": [
        "The agent runs scripts/review.py against the files",
        "verified-true WARN is reported for the YAML config",
        "The report mentions that verified should be false for new unbaselined servers"
      ],
      "expected_output": null
    }
  ]
}
```

### What a good assertion looks like

- **Specific** — "verified-true WARN is reported" > "the agent mentions verified status".
- **Testable from the transcript** — the judge sees the model's output + tool calls, nothing else. Don't assert on filesystem state.
- **Function-oriented, not phrasing-oriented.** Assertions that require a literal string are fragile.

### Cautionary tale

One of our assertions read *"Handoff to gym-profile mentioned for analyzing results after rollout collection"*. The model correctly recommended `ng_reward_profile` — the right *function* — but didn't name the skill `gym-profile` verbatim. The judge correctly flagged it as unsatisfied. The grade was right; the assertion was over-literal.

**Rewrite before running**: *"Mentions using ng_reward_profile (or a handoff to the gym-profile skill) to analyze rollout results"*.

### What about `expected_output`?

Optional. If you have a gold-standard answer, put it here and the judge will see it. For most skills, leave it `null` — the assertions are the spec.

---

## Step 2: Generate the input JSONL

`scripts/build_skill_eval_jsonl.py` walks `.claude/skills/*/evals/evals.json` and emits two records per scenario (one `with_skill=True`, one `with_skill=False`):

```bash
python scripts/build_skill_eval_jsonl.py \
    --skills-dir .claude/skills \
    --output responses_api_agents/skill_eval_agent/data/example.jsonl
```

Each record:

```json
{
  "responses_create_params": {
    "input": [{"role": "user", "content": "<scenario prompt>"}]
  },
  "verifier_metadata": {
    "skill_path": "/abs/path/to/skill",
    "skill_name": "my-skill",
    "scenario_id": 1,
    "files": ["evals/files/..."],
    "with_skill": true,
    "skill_md": "<contents of SKILL.md>",
    "assertions": [...],
    "expected_output": null
  }
}
```

`with_skill=True` means the agent will prepend `SKILL.md` as a system message before the rollout. `with_skill=False` is the control.

---

## Step 3: Run the scoreboard

Start with `num_repeats=1` to sanity-check end-to-end; then bump to 5 for a scoreboard you can interpret.

```bash
ng_collect_rollouts \
    +agent_name=skill_eval_agent \
    +input_jsonl_fpath=responses_api_agents/skill_eval_agent/data/example.jsonl \
    +output_jsonl_fpath=results/scoreboard.jsonl \
    +num_repeats=5 \
    +num_samples_in_parallel=6 \
    "+responses_create_params={max_output_tokens: 8192}"
```

`num_samples_in_parallel` is bounded by your endpoint's rate limit more than your local machine. 6-way parallel on the NVIDIA inference-api produced zero flakes in our runs.

The output JSONL contains one line per rollout with `reward`, per-assertion `grades[]`, and the full `verifier_metadata` preserved.

---

## Step 4: Read the deltas

`ng_collect_rollouts` prints a single `mean/reward` across everything — that number mixes with-skill and without-skill rollouts and is **not** what you want. Bucket by skill and by the `with_skill` flag:

```python
import json
from collections import defaultdict

by_skill = defaultdict(lambda: {"with": [], "without": []})
for line in open("results/scoreboard.jsonl"):
    r = json.loads(line)
    md = r.get("verifier_metadata", {})
    bucket = "with" if md.get("with_skill") else "without"
    by_skill[md["skill_name"]][bucket].append(r["reward"])

print(f"{'skill':20s}  {'with':>8s}  {'without':>8s}  {'delta':>8s}")
print("-" * 60)
for skill in sorted(by_skill):
    w  = sum(by_skill[skill]["with"])    / len(by_skill[skill]["with"])
    wo = sum(by_skill[skill]["without"]) / len(by_skill[skill]["without"])
    print(f"{skill:20s}  {w:8.3f}  {wo:8.3f}  {w - wo:+8.3f}")
```

A real scoreboard from our run (n=5 per bucket, 240 rollouts total):

| skill | with | without | delta |
|---|---|---|---|
| gym-scaffold-agent | 0.867±0.025 | 0.733±0.080 | **+0.133** |
| add-benchmark | 0.877±0.037 | 0.808±0.047 | +0.069 |
| gym-profile | 0.909±0.026 | 0.871±0.046 | +0.038 |
| gym-review | 1.000±0.000 | 0.990±0.010 | +0.010 |
| gym-data | 0.987±0.013 | 0.987±0.013 | +0.000 |
| gym-debug | 0.947±0.024 | 0.973±0.018 | −0.027 |
| gym-config | 0.808±0.060 | 0.920±0.043 | **−0.112** |
| gym-run | 0.778±0.085 | 0.927±0.042 | **−0.149** |

The table does more for you than any scalar. Three clusters to read off:

- **Helpful skills**: `gym-scaffold-agent`, `add-benchmark`, `gym-profile` — real positive lift, delta larger than combined standard error.
- **Ceiling-clipped**: `gym-review`, `gym-data` — `without_skill` is already ~0.99, so there's no room for the skill to help; we can't conclude anything from +0.010 / +0.000.
- **Net-negative (actionable)**: `gym-config −0.112` and `gym-run −0.149` — the skill is making the model measurably *worse* on these scenarios. Chase these: read the failing rollouts' `tool_calls` and `grades[].evidence` and find out which guidance misleads the model.

### Read by column, not by row

The delta column is a summary, not an explanation. Every row in this table is actually two independent measurements that share a prompt:

| column | moves when… | ignore when iterating on… |
|---|---|---|
| `with_skill` | SKILL.md changes; rollout behavior changes (e.g. model stops thrashing on a missing tool) | only the scenario/assertion prose changed |
| `without_skill` | fixtures change; sandbox / harness code changes; judge behavior drifts | only SKILL.md changed |
| `delta` | any of the above | — |

If you want to know whether a skill *edit* landed, read `with_skill`. If you want to know whether your *harness* is doing something to everyone uniformly, read `without_skill` across the whole column — correlated movement there is a stack side-effect, not a skill effect. We will return to this framing in Step 7 when we diff two runs.

---

## Pitfalls — receipts from our own runs

### Pitfall 1: Ceiling effects

Three skills above scored 1.000/1.000. That is **not** "this skill has no effect" — it's "this scenario is solvable without the skill, so we can't measure." Do not shrug at +0.000; go write harder scenarios.

**Rule of thumb:** if `without_skill ≥ 0.95`, treat the delta as *inconclusive*. Add one adversarial scenario and rerun.

### Pitfall 2: Low-n noise

At n=1 per bucket, a single wrong grade moves the delta by `1/num_assertions` (often 0.15–0.25). That's bigger than most real deltas.

**Rule of thumb:** n=1 gives you rank ordering. n=3 gives you direction. n=5 gives you magnitude. Don't claim a skill "improved by 8%" at n≤3.

We ran the same scoreboard at n=1 and n=5. Three things moved between them:

| skill | n=1 delta | n=5 delta | change |
|---|---|---|---|
| add-benchmark | +0.237 | +0.069 | over-stated by 3× |
| gym-scaffold-agent | +0.067 | +0.133 | doubled, now strongest |
| gym-config | +0.000 | −0.112 | flipped sign — masked by noise |

The n=1 run got the *top-three* right as a group. It got the *order within* that group wrong, and it completely missed `gym-config` becoming a net-negative. This is the rank-vs-magnitude distinction in action.

### Pitfall 3: Negative deltas are diagnostic

`gym-run −0.200` is not noise to average away. Either the skill's guidance is misleading, it conflicts with the model's priors, or the scenarios are badly designed. Chase it — read the `tool_calls` and `grades[].evidence` for the failing rollouts and find out which.

### Pitfall 4: Over-literal assertions

See the `gym-profile` example in Step 1. If an assertion-level grade looks wrong, check the assertion *before* blaming the judge. Our spot-check found 6/7 judge decisions defensible; the one "miss" was assertion phrasing.

---

## Step 5: Break out by scenario

Skill-level means average across all scenarios for that skill, which hides exactly the information you need when chasing a delta. A skill with three scenarios and deltas `[+0.20, +0.00, −0.20]` scores 0.00 at the skill level — indistinguishable from a boringly flat skill. When you inspect it, you'll find one great scenario, one ceiling-clipped scenario, and one adversarial scenario where the skill actively misleads the model.

Bucket by `(skill, scenario_id, with_skill)`:

```python
import json
from collections import defaultdict

by_cell = defaultdict(list)
for line in open("results/scoreboard.jsonl"):
    r = json.loads(line)
    md = r.get("verifier_metadata", {})
    key = (md["skill_name"], md["scenario_id"], "with" if md.get("with_skill") else "without")
    by_cell[key].append(r["reward"])

for key in sorted(by_cell):
    rewards = by_cell[key]
    skill, sid, arm = key
    print(f"{skill:22s} sc{sid} {arm:7s}  mean={sum(rewards)/len(rewards):.2f}  n={len(rewards)}")
```

This is also what turns a puzzling skill-level delta into a debugging lead. When `gym-profile` moved from Δ = +0.038 (v2) to Δ = −0.053 (v3) — a change of −0.091 on the *same* SKILL.md — the skill-level number was a dead end. Breaking out by scenario pointed straight at scenario 2's `with_skill` arm: 0.84 in v2, 0.56 in v3. Every other cell in the breakdown was flat. That alone narrowed the root cause to one rollout, which we then opened and found spinning on `python: command not found` — a harness-level side effect we fix in Step 7.

**Rule of thumb:** if the delta-of-deltas between two runs is larger than the noise floor, go straight to the scenario breakdown before doing anything else. The skill-level number is a pointer; the scenario breakdown is the address.

---

## Step 6: Spot-check the judge

Before trusting the scoreboard, verify the judge is actually measuring what you think. Sample a few partial-credit rollouts and read the evidence:

```python
import json, random

random.seed(7)
rows = [json.loads(l) for l in open("results/scoreboard.jsonl")]
partial = [r for r in rows if 0 < r["reward"] < 1.0]
for r in random.sample(partial, k=min(5, len(partial))):
    md = r["verifier_metadata"]
    print(f"\n{md['skill_name']} sc{md['scenario_id']} with={md['with_skill']} r={r['reward']:.2f}")
    for a, g in zip(md["assertions"], r["grades"]):
        mark = "✓" if g["satisfied"] else "✗"
        print(f"  {mark} {a}")
        print(f"     → {g['evidence'][:150]}")
```

What you're looking for:

- **Evidence strings cite real text** from the response or tool calls — not fabricated.
- **Consistent grading on duplicate scenarios** (`with_skill=True` and `=False` should grade the same assertion the same way when the response is substantively similar).
- **Misses should be visibly absent** in the transcript, not judge hallucinations.

Our 7-sample audit: 6/7 clean, 1/7 was assertion phrasing, not judge error. Once you see that pattern, you can trust the deltas.

---

## Step 7: Iterate — version the inputs, rerun, diff

One scoreboard tells you *where* a skill is hurting. It does not tell you whether an edit *fixed* anything. For that you need two runs side-by-side with an unambiguous answer to "is what I ran in v2 actually different from v1 — and different in *which* way?"

### What provenance covers (and what it still doesn't)

`scripts/build_skill_eval_jsonl.py` embeds five content hashes in every record's `verifier_metadata`. They ride through the full pipeline — build → agent → judge → output JSONL — so every scoreboard tells you exactly which inputs it was measuring:

| field | hashes | changes when… | attribution note |
|---|---|---|---|
| `skill_md_sha` | `SKILL.md` | skill prose edited | the only field a *skill* change moves |
| `evals_sha` | `evals/evals.json` | scenarios or assertions edited | assertion-phrasing debt shows up here |
| `fixtures_sha` | listed fixtures for this scenario | a fixture is added/renamed/edited | scenario-scoped, not skill-scoped |
| `judge_prompt_sha` | `skill_judge/prompt_templates/skill_judge.txt` | judge prompt template edited | a stack-wide change; moves every skill |
| `harness_version` | concatenated bytes of `skill_workspace/app.py` + `skill_judge/app.py` + `skill_eval_agent/app.py` | any server code edited | same: stack-wide, moves every skill |

No version bumps to maintain, no drift: if you edit a file that matters, its hash changes; if you don't, it doesn't.

What's still *not* hashed: the policy model version, the judge model version, model temperature, and anything those endpoints do non-deterministically (Opus at `temperature=0` is not bitwise-deterministic on our inference API). When every hash matches and deltas still move, that is your noise floor plus judge drift — both real, neither your fault.

### The diff tool

`scripts/diff_skill_scoreboards.py` runs in two modes:

```bash
# single-file: per-skill scoreboard with all 5 provenance columns
python scripts/diff_skill_scoreboards.py results/v1/rollouts.jsonl

# two-file: v1 vs v2 delta-of-deltas, with per-field provenance diff
python scripts/diff_skill_scoreboards.py \
    results/v1/rollouts.jsonl --v2 results/v2/rollouts.jsonl
```

The `provenance diff` column in two-file mode tells you which inputs actually changed:

| tag | meaning |
|---|---|
| `—` + `same-all` | every hash matches. Any movement is noise / judge drift. |
| `—` + `partial(N/5)` | only N of 5 fields known. Can't distinguish "unchanged" from "untracked". |
| `md` | only SKILL.md changed. Read `with_skill` to see effect. |
| `evals` | only scenarios/assertions changed. `with_skill` AND `without_skill` can both move — same prompt, different judge target. |
| `harness` or `judge` | stack-wide change. Expect correlated movement across every skill's `without_skill` column. |
| `md+evals` | skill body AND scenarios edited in the same run. **Stop.** You cannot attribute the delta cleanly — rerun with one edit at a time. |

**Attribution rule:** a delta-of-delta is only attributable to what the provenance diff points at. `same-all` plus a big delta change is a noise or drift finding, not a "the skill got worse" finding. Don't report it as the latter.

### A real v1 → v2 diff

Between v1 and v2 we made three targeted edits: rewrote `gym-config/SKILL.md` (hash change expected), reworded two over-literal assertions in `gym-run/evals.json` (same SHA expected), and stripped the host's `.venv` from the workspace sandbox PATH (a stack-level change — affects every skill). Here is what the diff tool reported:

| skill | v1 delta | v2 delta | change | note |
|---|---|---|---|---|
| gym-config | −0.112 | +0.033 | **+0.146** | SHA changed |
| gym-run | −0.149 | −0.084 | +0.064 | same-sha |
| gym-debug | −0.027 | −0.013 | +0.013 | same-sha |
| gym-review | +0.010 | +0.010 | +0.000 | same-sha |
| gym-data | +0.000 | −0.013 | −0.013 | same-sha |
| add-benchmark | +0.069 | +0.022 | −0.047 | same-sha |
| gym-scaffold-agent | +0.133 | +0.053 | −0.080 | same-sha |
| gym-profile | +0.038 | −0.053 | −0.091 | same-sha |

Three things to read off:

1. **The skill edit moved the skill.** `gym-config` flipped from net-negative to mildly positive (+0.146 delta-of-deltas), the SHA changed, and the sign flip is well above our n=5 noise floor (~±0.05–0.08). Assertion-level grade inspection on the partial-credit rollouts showed the "Before you answer" checklist pushing the model to read the referenced files before citing them — which is exactly what we wrote it to do.
2. **The assertion rewrite captured half the gap.** `gym-run` moved +0.064 on the *same* SHA. The assertions changed; the skill body did not. So the +0.064 is assertion-phrasing debt we were paying in v1, not a behavior change. That leaves a real −0.084 residual to chase.
3. **Stack changes contaminate "same-sha".** Look at the `without_skill` column in the raw tables: gym-config went 0.920 → 0.956, gym-run 0.927 → 0.956, add-benchmark 0.808 → 0.849. The sandbox PATH strip (see `_build_sandbox_env` in `resources_servers/skill_workspace/app.py`) ironically *helped* the baseline by removing distractions — the model can no longer "find" `ng_*` binaries in the sandbox and wander off investigating them. Same-sha deltas moved as a side effect.

**Takeaway:** interpret diffs by column, not by row. The `with_skill` column moves with skill edits; the `without_skill` column moves with stack edits; the delta moves with both. If you want to isolate the effect of a skill edit, keep the stack frozen and vice versa.

### A real v3 → v4 diff (and its honest failure mode)

Later we added the four additional provenance fields (`evals_sha`, `fixtures_sha`, `judge_prompt_sha`, `harness_version`) and reran with zero input changes as a noise calibration. The tool's response to asymmetric provenance is exactly what we hoped:

```
skill                    v3 delta  v4 delta   change  provenance diff
add-benchmark             +0.108    +0.097   -0.011   evals?+fx?+judge?+harness?
gym-config                -0.011    -0.022   -0.011   evals?+fx?+judge?+harness?
gym-data                  +0.013    +0.013   -0.000   evals?+fx?+judge?+harness?
gym-debug                 -0.027    +0.027   +0.053   evals?+fx?+judge?+harness?
gym-profile               +0.011    +0.071   +0.060   evals?+fx?+judge?+harness?
gym-review                +0.000    -0.010   -0.010   evals?+fx?+judge?+harness?
gym-run                   -0.011    +0.020   +0.031   evals?+fx?+judge?+harness?
gym-scaffold-agent        +0.080    -0.013   -0.093   evals?+fx?+judge?+harness?
```

The `?` suffix says: "v3 didn't carry this hash, so I can't prove those fields matched — they *might* have changed between runs." This is the tool refusing to lie. We know from git that only the harness changed (python symlink), but the JSONL can't prove it, so the diff says so.

This run produced one signal that is essential to record honestly: **the observed noise floor at n=5 is wider than we initially estimated, because the judge itself drifts.** At the scenario-cell level:

- `gym-scaffold-agent sc3 without_skill`: v3 = 0.60, v4 = **0.80** (+0.20, same prompt, same assertions)
- `gym-scaffold-agent sc1 without_skill`: v3 = 0.88, v4 = **1.00** (+0.12, same prompt, same assertions)

These cells drive the skill's delta-of-delta change of −0.093 — but the skill body, assertions, fixtures, and judge prompt are bit-identical across the two runs. The only moving part is the judge's own temperature-0 stochasticity at the inference API. We verified this manually by pulling both runs' rollouts for sc3-without: the model's reviews were substantively similar critical reviews; the *judge* graded the "What's correct" sections more generously in v4.

**The practical implication:** `same-all` rows with |change| < ~0.10 should be read as noise, not as real deltas. If you need to detect a smaller effect reliably, bump `num_repeats` — every doubling of n roughly halves the per-cell stderr. We've been claiming ±0.05–0.08 at n=5; the receipts say ~±0.10 on a bad cell.

This finding also makes it clear what provenance *can't* hash: the model and judge endpoints' internal non-determinism. `same-all` is necessary for attribution but not sufficient — it's a cache-hit check, not a p-value.

### The iteration loop

```
1. Pick the worst (or most interesting) skill from the scoreboard.
2. Break it out by scenario (Step 5) to localize which cell moved.
3. Read the partial-credit rollouts' grades[].evidence to find the failure mode.
4. Edit ONE input — SKILL.md, evals.json, a fixture, or harness code.
5. Regenerate the input JSONL (every relevant hash updates automatically).
6. Rerun ng_collect_rollouts into a fresh output path.
7. Diff v2 vs v1 with diff_skill_scoreboards.py.
8. If the provenance diff points at the thing you changed AND the delta
   change is larger than the noise floor, ship it.
```

The "one input at a time" rule is load-bearing. We once edited both a SKILL.md and the sandbox harness in one run, and had to burn a third run to tell them apart.

---

## What's next

Two common follow-on investments:

- **Harder scenarios for ceiling-saturated skills** — until `without_skill` drops below ~0.90, you can't measure improvement.
- **Assertion audit** — sweep existing assertions for over-literal phrasing that punishes the model for paraphrasing. The `gym-run` assertion rewrite above was worth +0.064 on its own.

:::{button-ref} skill-eval-harness
:color: secondary
:outline:
:ref-type: doc

← Back to Part 1: Build the Harness
:::
