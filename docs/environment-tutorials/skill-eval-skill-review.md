# Skill-by-skill audit — v7 results

Per-skill verdicts, root-cause hypotheses, and prescriptive file-level changes based on the v7 4-cell rollout (n=5, 480 rollouts, post-contamination-fix baseline). Each entry cites the four v7 Δreward effects, the per-scenario breakdown, and specific source files to inspect or edit.

The four effects (see `skill-eval-scoreboard.md` for definitions):

- **`skill | refs=T`** (realistic deployment)
- **`skill | refs=F`** (standalone value)
- **`refs | skill=F`** (marginal value of references alone)
- **`Δtools (skill | refs=T)`** (efficiency axis)

Bold = effect outside noise floor (~±0.10 at n=5 per-cell).

---

## `gym-run` — load-bearing, keep as-is

| `skill | refs=T` | `skill | refs=F` | `refs | skill=F` | Δtools |
|---|---|---|---|
| **+0.436** | **+0.480** | −0.013 | −1.87 |

Per-scenario (`skill | refs=T`): sc1 **+0.97**, sc2 **+0.24**, sc3 +0.10.

**Verdict:** the one unambiguous keeper. Large positive on both realistic and standalone contrasts, no references directory to contaminate, sc1 is literally "the model cannot do this task without the skill" (blind=0.00, docs=0.00).

**Why it works:** `gym-run`'s scenarios test specific `ng_run` / `ng_status` / `ng_collect_rollouts` workflow knowledge that the model has no priors for. The SKILL.md walks through env.yaml setup, server health checks, and smoke-test diagnostics — concrete operational knowledge, not explainable from first principles.

**Source:**
- `.claude/skills/gym-run/SKILL.md` (205 lines) — no changes needed.
- No `references/` directory. Consider adding one only if scenarios expand.

**Gaps:** none identified. If anything, this skill is a template for what "skill-only" value looks like when the content is a genuine operational procedure.

---

## `add-benchmark` — keep; scenario 3 is ceiling-clipped

| `skill | refs=T` | `skill | refs=F` | `refs | skill=F` | Δtools |
|---|---|---|---|
| **+0.141** | **+0.446** | **+0.313** | −1.27 |

Per-scenario (`skill | refs=T`): sc1 **+0.14**, sc2 **+0.28**, sc3 +0.00.

**Verdict:** skill and references both carry real signal; the skill adds genuine value on top of a strong reference doc. sc3 (httpx wrapper) is effectively solved by references alone (docs=1.00, blind=0.03) — a clean example of content that migrated entirely into the reference.

**Why it works:** the skill covers the full workflow (data prep → server scaffold → config → baseline), and the references in `patterns.md` go deep on wrapper patterns. They're complementary, not competing.

**Source:**
- `.claude/skills/add-benchmark/SKILL.md` (257 lines) — no changes needed.
- `.claude/skills/add-benchmark/references/patterns.md` (2,541 words — largest in the tree) — clearly doing real work.

**Gaps:**
- sc3 is ceiling-clipped by references. Either write a harder wrapper scenario (e.g. library that uses a httpx transport *and* has its own scoring library *and* emits non-binary rewards) to recover discriminating power, or accept that this scenario just validates the reference content.
- Consider an sc4 testing the "convert from a source repo's format" workflow — that's operational knowledge neither the SKILL.md nor current scenarios exercise.

---

## `gym-config` — holds; 2/3 scenarios are too easy

| `skill | refs=T` | `skill | refs=F` | `refs | skill=F` | Δtools |
|---|---|---|---|
| **+0.111** | **+0.173** | +0.062 | −1.60 |

Per-scenario (`skill | refs=T`): sc1 −0.07, sc2 **+0.40**, sc3 +0.00.

**Verdict:** meaningful value but driven almost entirely by sc2. sc1 and sc3 are ceiling-clipped with refs (docs=1.00), masking any signal.

**Why sc2 works:** validating a combined-reward config requires naming specific fields (`reward_if_quality_low` etc.) in prose. The SKILL.md's validation checklist pushes the model toward reading the file and citing exact fields. Reference content alone (config-patterns.md) doesn't prompt this behavior as reliably.

**Source:**
- `.claude/skills/gym-config/SKILL.md` (219 lines) — no changes needed; the "Before you answer" checklist is doing real work.
- `.claude/skills/gym-config/references/config-patterns.md` (818 words) — likely appropriate coverage for sc1/sc3's simpler validations.

**Gaps:**
- **`.claude/skills/gym-config/evals/evals.json` sc1 and sc3 are too easy.** Add more adversarial scenarios: bad interpolation, circular references, `${oc.env:...}` misuse, duplicate instance names across composed configs. This is where the skill-content quality can't be measured, not where the skill is bad.
- The `fixtures_sha` between different gym-config scenarios would tell us whether the fixture files themselves are the bottleneck. They likely are — probably simple YAMLs with one obvious issue.

---

## `gym-debug` — holds; references carry most of the load

| `skill | refs=T` | `skill | refs=F` | `refs | skill=F` | Δtools |
|---|---|---|---|
| +0.080 | **+0.267** | **+0.187** | **−4.33** |

Per-scenario (`skill | refs=T`): sc1 **+0.24**, sc2 +0.00, sc3 +0.00.

**Verdict:** sc1 is where the skill adds realistic value; sc2/sc3 are ceiling-clipped with refs (docs=1.00). Tool-call reduction is the strongest in the tree — the skill teaches the model to skip exploratory commands.

**Why sc1 works but sc2/sc3 don't:** sc1 is about `check_twice_swap` + positional-bias diagnosis, which requires recalling *multiple interacting concepts* — the skill's structured walk-through primes the model for that. sc2 (think-block interference) and sc3 (combined reward) are "identify the diagnostic field from the rollout JSON" tasks, which the references handle directly.

**Source:**
- `.claude/skills/gym-debug/SKILL.md` (123 lines) — keep.
- `.claude/skills/gym-debug/references/diagnostic-fields.md` and `error-patterns.md` (1,481 words combined) — doing strong work on sc2/sc3.

**Gaps:**
- Scenarios are fixture-driven, and the fixtures contain the diagnostic fields the assertions test for. So the model can reason from the fixture even without docs. Consider sc4/sc5 that test diagnosis *without* the specific field being pre-named in the fixture — e.g., "rewards are 0.5 and the rollout is truncated; is this a judge fallback or a model budget issue?" requires integrating multiple signals.

---

## `gym-review` — delete or dramatically shrink SKILL.md

| `skill | refs=T` | `skill | refs=F` | `refs | skill=F` | Δtools |
|---|---|---|---|
| +0.029 | **+0.298** | **+0.602** | **−4.87** |

Per-scenario (`skill | refs=T`): sc1 +0.00, sc2 +0.03, sc3 +0.06.

**Verdict:** **the skill is almost entirely redundant with its references.** `refs | skill=F` = +0.602 is the largest reference-alone signal in the tree; `skill | refs=T` is essentially zero across every scenario.

**Why:** `gym-review` ships a `scripts/review.py` that the model runs, plus two strong reference docs (`anti-patterns.md`, `fix-patterns.md`, 1,291 words combined). The script does most of the work by producing a structured report; references tell the model what each finding means. SKILL.md adds nothing on top.

**Source:**
- `.claude/skills/gym-review/SKILL.md` (110 lines) — **shrink to ~20–30 lines.** Current SKILL.md duplicates content that lives in the references and the script. Keep only: how to invoke `review.py`, how to interpret its output categories, and when to bypass it.
- `.claude/skills/gym-review/references/anti-patterns.md` and `fix-patterns.md` — **keep; these are load-bearing.**
- `.claude/skills/gym-review/scripts/review.py` — doing the heavy lifting.

**Gaps:**
- The measurable skill value is the tool-call efficiency (−4.87 per rollout). That suggests the SKILL.md is teaching the model to *trust the script* and not explore independently. Which is useful! But we're paying for 110 lines of SKILL.md to teach "run the script" — the same thing could be a 5-line paragraph in the references.

---

## `gym-scaffold-agent` — competes with refs on sc3

| `skill | refs=T` | `skill | refs=F` | `refs | skill=F` | Δtools |
|---|---|---|---|
| −0.040 | **+0.213** | **+0.333** | −0.73 |

Per-scenario (`skill | refs=T`): sc1 −0.04, sc2 +0.00, sc3 −0.08.

**Verdict:** within noise on the realistic contrast. Standalone value is real (+0.213), but the refs do more alone (+0.333), and adding the skill on top slightly hurts on sc3.

**Why sc3 is slightly negative:** sc3 is the "clean code, should be approved" scenario. In v7, with skill prompted + refs on disk, the model tends to flag non-issues — the skill's pattern-catalog structure biases it toward finding problems even when none exist. Without the skill (docs-only), the model is more willing to say "looks fine."

**Source:**
- `.claude/skills/gym-scaffold-agent/SKILL.md` (179 lines) — needs trimming. The RL-centric content (cookie propagation, token accumulation, httpx→aiohttp) is correct but over-dominant in the narrative.
- `.claude/skills/gym-scaffold-agent/references/agent-patterns.md` (776 words) — carries most of the value.

**Gaps:**
- **SKILL.md lacks an "when the code is clean, say so" framing.** The pattern-catalog structure teaches the model to search for issues. Add an explicit "Approval heuristic" section that tells the model how to recognize correct code and how to write a clean-bill-of-health review.
- **Not enough coverage of non-RL agent patterns.** The skill is scoped tightly to RL training agents (cookie propagation, token IDs for RLVR). But many agent-server use cases are non-RL (evaluation, orchestration) and the skill has nothing to say. This is real content gap — the author of this sprint's `skill_eval_agent` got no value from the skill.

---

## `gym-profile` — rewrite SKILL.md to narrate to references

| `skill | refs=T` | `skill | refs=F` | `refs | skill=F` | Δtools |
|---|---|---|---|
| **−0.107** | **+0.278** | **+0.342** | −2.87 |

Per-scenario (`skill | refs=T`): sc1 +0.00, sc2 **−0.16**, sc3 **−0.16**.

**Verdict:** **the clearest "skill competes with references" pattern in the sprint.** Useful standalone, but adding it on top of refs consistently costs ~0.16 on non-ceiling scenarios.

**Why:** the SKILL.md is structured as a how-to (Steps 1–5, commands with flags). The references (`metrics-guide.md`) are structured as explanation (named sections per concept: `pass_threshold`, variance, suspicious patterns). For sc2/sc3 assertions that test *conceptual noun recall* (e.g. "mentions `pass_threshold`", "recommends checking `extracted_model_code`"), the without-skill model reasons from first principles + references and surfaces the noun correctly. The with-skill model follows the SKILL.md's recipe structure and never reaches the point of naming the specific noun — it cites the pattern and shows a generic code snippet.

**Source:**
- `.claude/skills/gym-profile/SKILL.md` (148 lines) — **needs targeted rewrite.** Specifically:
  - Line ~67 (patterns table): inline the confirming field names into the narrative. Current: `"reasoning_format_violation_rate may be high — check if thinking tags are being stripped"`. Should be: `"reasoning_format_violation_rate is high → read extracted_model_code to confirm <think> tokens leaked into extraction"`.
  - Elevate `pass_threshold` from a command flag (line ~37) into its own explained subsection.
  - Every pattern → cause chain needs a specific field-name handoff in prose, not via a code snippet.
- `.claude/skills/gym-profile/references/metrics-guide.md` (716 words) — **keep; this is the better doc for these JTBDs.**

**Gaps:**
- This is a Diátaxis-mode mismatch: how-to (SKILL.md) doing explanation's job (conceptual noun recall). The references are explanation-mode and do this correctly. Rewriting SKILL.md to cross-reference `metrics-guide.md` at each decision point — rather than duplicating content in recipe form — should flip `skill | refs=T` to positive.

---

## `gym-data` — ceiling-clipped; scenarios need rewriting

| `skill | refs=T` | `skill | refs=F` | `refs | skill=F` | Δtools |
|---|---|---|---|
| +0.013 | +0.040 | +0.013 | **−3.27** |

Per-scenario (`skill | refs=T`): all near-ceiling (blind=0.88–1.00, docs/skill/both all at 0.96–1.00).

**Verdict:** cannot be measured. Every cell of every scenario is ≥ 0.96. Tool-call reduction suggests the skill teaches something (−3.27 calls per rollout), but the accuracy dimension is invisible.

**Why:** scenarios are "validate this dataset" tasks where the problems are obvious on inspection (sc1: well-formed tool-calling data; sc2: bad data; sc3: schema extension). Modern frontier models solve these from first principles.

**Source:**
- `.claude/skills/gym-data/SKILL.md` (200 lines) — can't evaluate without harder scenarios.
- `.claude/skills/gym-data/references/schema.md` (743 words) — can't evaluate.
- `.claude/skills/gym-data/evals/evals.json` — **this is the file that needs work.**

**Gaps:**
- **Rewrite all three scenarios to be adversarial.** Examples:
  - sc1 replacement: a dataset where tool-calling messages have subtly malformed `function.arguments` (quoted JSON string that should be an object), where the right answer requires knowing the OpenAI schema edge case.
  - sc2 replacement: a dataset where the labels look correct but are semantically wrong (e.g., labeled "safe" but content is clearly unsafe) — tests whether the model applies judgment, not just format validation.
  - sc3 replacement: generate examples for a benchmark with a non-obvious schema (multi-turn with branching tool calls; verifier_metadata with nested expected-answer structures).
- Until scenarios move, this skill is in a measurement dead zone regardless of whether its content is good.

---

## Cross-cutting patterns and prescriptions

**Where SKILL.md is redundant with references (shrink SKILL.md):**
- `gym-review` (most severe)

**Where SKILL.md competes with references (rewrite SKILL.md to narrate to refs):**
- `gym-profile` (clearest case)
- `gym-scaffold-agent` (milder)

**Where scenarios are ceiling-clipped (rewrite evals.json):**
- `gym-data` (all three)
- `gym-config` (sc1, sc3)
- `gym-debug` (sc2, sc3)
- `add-benchmark` (sc3 is actually fine — solved by refs — but consider a new scenario that needs unique skill knowledge)

**Where the skill has real content gaps (add new material):**
- `gym-scaffold-agent` — missing non-RL agent patterns (evaluation, orchestration)
- `gym-scaffold-agent` — missing "how to recognize correct code" heuristic

**Where the skill is load-bearing as-written:**
- `gym-run` (keep)
- `add-benchmark` (keep)
- `gym-config` (keep, but write harder scenarios)

**Skills that would benefit most from a post-edit remeasurement:**
1. `gym-profile` — rewrite SKILL.md patterns table, expect `skill | refs=T` to go from −0.107 to near-zero or positive. Cleanest test of the narrate-to-references prescription.
2. `gym-review` — shrink SKILL.md; expect `skill | refs=T` to stay near zero (it's the floor), but also expect no loss. That proves the skill body was dead weight.
3. `gym-data` — write harder scenarios, expect `docs-only` to drop below 0.95, opening measurable headroom for the skill to be evaluated.

## Prerequisites for trusting these recommendations

All of the above rests on v7 (n=5, 480 rollouts) as a single measurement. Before shipping any large skill rewrites:

1. **Calibration run at n=20** on one cell (e.g., `gym-profile sc2 skill+docs`) to confirm effect sizes are outside noise.
2. **One edit at a time.** Rewriting gym-profile's patterns table AND gym-review's SKILL.md in the same run confounds attribution.
3. **Post-edit diff must show the right provenance tag.** If the prescription is "rewrite SKILL.md for gym-profile," the diff should flag `md` as the change for exactly that skill and `—` (same-all) for every other skill. Anything else is a confound.
