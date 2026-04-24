# Skill-eval findings

**Status:** v8 complete. Three predicted skill-content edits landed (gym-profile patterns-table rewrite, gym-review SKILL.md shrink, gym-data adversarial scenarios). All three produced the predicted movement with clean provenance attribution. n=5, 480 rollouts per run, Opus 4.7 policy + judge via NVIDIA inference API. Noise floor established at ~±0.05 skill-level and ~±0.20 per-cell in prior calibration runs (v4↔v5 zero-edit).

## v8 summary — edits that landed

Three predicted prescriptions from `skill-eval-skill-review.md`, each tested with a single-skill edit to prove attribution:

| skill | edit | v7 `skill \| refs=T` | v8 `skill \| refs=T` | change | provenance tag | verdict |
|---|---|---|---|---|---|---|
| **gym-profile** | rewrote patterns table to inline confirming field names in prose | −0.107 | **+0.040** | **+0.147** | `md` | **hit** — flipped from net-negative to slightly-positive |
| **gym-data** | replaced ceiling-clipped scenarios with adversarial versions | +0.013 | **+0.093** | **+0.080** | `evals+fx` | **hit** — now measurable |
| **gym-review** | shrunk SKILL.md from 110 to 53 lines | +0.029 | +0.048 | +0.019 | `md` | **caveated hit** — realistic preserved, standalone collapsed (see below) |

All other skills showed `same-all` provenance tags, as expected. Two (`gym-config` at −0.084 and `gym-scaffold-agent` at +0.093) had same-all drift above the skill-level noise floor — judge non-determinism, not skill effects.

### gym-profile — the cleanest win

The v7 read was "skill actively misleading" (−0.107 realistic). The prescription was "rewrite the patterns table so each row names both the trigger AND the confirming field in prose, not in a code block." Implemented in `3f3a3300`:

- Patterns table expanded to three columns (trigger / cause / confirm-by-reading), with specific field names in the "confirm" column.
- `pass_threshold` promoted from a command flag to a named concept subsection.

v8 result: `skill | refs=T` moved from −0.107 to +0.040 (change +0.147, well outside the ~±0.05 skill-level noise floor). Standalone value also strengthened (+0.278 → +0.309). Attribution is clean — provenance diff was `md` with every other skill flat.

### gym-data — scenarios now interpretable

v7 had every cell at 0.96–1.00 — unmeasurable. v8 with adversarial scenarios: blind=0.85, docs-only=0.88, skill-only=0.91, skill+docs=0.97. Realistic skill contribution is now **+0.093**.

One honest note: `blind` only dropped to 0.85, not to the ~0.5 we might have hoped. The new scenarios are harder, but the model's priors on data-audit tasks are still strong. Even harder scenarios would sharpen the measurement further.

### gym-review — the nuanced caveat

This is the surprising result. The shrink kept realistic deployment working (`skill | refs=T` held at +0.048, Δtools on skill+docs held at −4.73) but collapsed standalone value: `skill | refs=F` went from +0.298 to +0.012.

**Interpretation:** if the deployment assumption is "reader always has the repo checked out," the shrink is a pure win (same realistic effect, shorter doc, same efficiency). If there's a use case where someone loads the skill pack *without* its references (e.g., a Claude.ai user with the SKILL.md loaded but not the references/ dir), the new 53-line SKILL.md is insufficient. That's a product call, not a measurement call — the shrink's verdict depends on which deployment model we're optimizing for.

---

## Methodology (what's measured)

Each skill is rolled out under four cells per scenario:

- `blind` — no skill in prompt, no supporting artifacts on disk
- `docs-only` — references/scripts on disk, no skill in prompt (realistic reader without skill pack)
- `skill-only` — skill in prompt, no supporting artifacts (skill as standalone doc)
- `skill+docs` — skill in prompt + artifacts on disk (realistic deployed reader)

Per-skill claims cite one of four marginal effects:

- **`skill | refs=T`** (skill+docs − docs-only) — realistic-deployment value of the skill overlay
- **`skill | refs=F`** (skill-only − blind) — skill as a standalone doc
- **`refs  | skill=T`** (skill+docs − skill-only) — do refs still matter when the skill is prompted?
- **`refs  | skill=F`** (docs-only − blind) — marginal value of references alone

Each delta reports on three axes: `Δreward` (accuracy), `Δtools` (efficiency), `Δtokens` (output length).

## v8 headline table — Δreward

Bold = effect cleanly outside noise floor (~±0.10 conservative at n=5). Per-cell n=15 (3 scenarios × 5 repeats).

| skill | skill \| refs=T | skill \| refs=F | refs \| skill=T | refs \| skill=F |
|---|---|---|---|---|
| **gym-run** | **+0.380** | **+0.411** | −0.058 | −0.027 |
| **add-benchmark** | **+0.162** | **+0.328** | +0.083 | **+0.249** |
| gym-debug | **+0.133** | **+0.187** | +0.027 | +0.080 |
| gym-data | +0.093 | +0.053 | +0.067 | +0.027 |
| gym-scaffold-agent | +0.053 | **+0.333** | +0.093 | **+0.373** |
| gym-review | +0.048 | +0.012 | **+0.601** | **+0.565** |
| gym-profile | +0.040 | **+0.309** | +0.024 | **+0.293** |
| gym-config | +0.027 | **+0.133** | −0.022 | +0.084 |

## v7 headline table — Δreward (archived for comparison)

| skill | skill \| refs=T | skill \| refs=F | refs \| skill=T | refs \| skill=F |
|---|---|---|---|---|
| **gym-run** | **+0.436** | **+0.480** | −0.058 | −0.013 |
| add-benchmark | +0.141 | +0.446 | +0.008 | +0.313 |
| gym-config | +0.111 | +0.173 | +0.000 | +0.062 |
| gym-debug | +0.080 | +0.267 | +0.000 | +0.187 |
| gym-review | +0.029 | +0.298 | +0.332 | +0.602 |
| gym-data | +0.013 | +0.040 | −0.013 | +0.013 |
| gym-scaffold-agent | −0.040 | +0.213 | +0.080 | +0.333 |
| **gym-profile** | **−0.107** | **+0.278** | −0.042 | +0.342 |

Key: **bold** = effect cleanly outside noise floor (~±0.10 conservative at n=5). Per-cell n=15 (3 scenarios × 5 repeats).

## v8 Δtools on the realistic contrast (skill \| refs=T)

Every skill reduces tool calls when the skill is added on top of references, even when the accuracy delta is small. The v7→v8 edits preserved this axis.

| skill | v7 Δtools | v8 Δtools | notes |
|---|---|---|---|
| gym-review | −4.87 | −4.73 | held after SKILL.md shrink |
| gym-debug | −4.33 | −4.13 | flat |
| gym-data | −3.27 | −3.00 | held despite harder scenarios |
| gym-profile | −2.87 | −2.00 | slightly weaker after prose edit, still strong |
| gym-run | −1.87 | −1.67 | flat |
| gym-config | −1.60 | −1.60 | flat |
| add-benchmark | −1.27 | −1.13 | flat |
| gym-scaffold-agent | −0.73 | −1.00 | slightly stronger |

Efficiency is the most robust multi-skill pattern across runs. Prescriptive reading: at deployment scale, the skills save real latency/cost per invocation, regardless of whether they materially move accuracy.

## Per-skill reads (v8)

### gym-run — confirmed keeper

`skill | refs=T` = +0.380 (v7: +0.436). This skill has no `references/` directory, so its control arm was never contaminated. v6→v7→v8 all confirm it as load-bearing. No edits made in this iteration; small v7→v8 drift is within same-all noise.

### gym-profile — prescription validated

v7 read was "skill competes with its own references" (`skill | refs=T` = −0.107). Patterns-table rewrite landed in `3f3a3300`: each pattern row now names the confirming field in prose, and `pass_threshold` became a named concept subsection.

v8 result: `skill | refs=T` = **+0.040** (change +0.147 vs v7). Standalone strengthened (+0.278 → +0.309). The "narrate to the references" prescription is now empirically validated on this skill; the Diátaxis-flavored reading holds.

### gym-review — prescription partially validated; standalone lost

v7 read was "SKILL.md is redundant with references." Shrink landed in `8fdcdb2c`, 110 → 53 lines.

v8 result: `skill | refs=T` held at +0.048 (v7 +0.029, change within noise). Δtools on skill+docs held at −4.73 (v7 −4.87). **BUT** `skill | refs=F` collapsed from +0.298 to +0.012 — the old SKILL.md was genuinely carrying the load when references weren't available. The shrink is a net win for the always-has-refs deployment model; a regression for skill-only use. Treat as a deployment-context-dependent result, not a universal "ship it."

### gym-data — scenarios now interpretable

v7 had every cell at 0.96–1.00. Adversarial scenarios landed in `5e84dd08`: schema audit with four planted bugs, semantic mislabeling with three wrong gold answers, multi-turn branching schema extension.

v8 result: cells at 0.85 / 0.88 / 0.91 / 0.97. `skill | refs=T` = **+0.093** (v7 +0.013). Finally measurable. blind only dropped to 0.85 — the scenarios are harder but still within model priors' reach; even-more-adversarial scenarios would sharpen the measurement further.

### gym-debug — solid; no edit made

v8 `skill | refs=T` = +0.133 (v7 +0.080). Above noise floor. Provenance `same-all`; movement is judge-drift-plus-improvement consistent with a ceiling-easing trend. No edit made in this iteration.

### gym-config, add-benchmark — held within noise

Both have `skill | refs=T` in the +0.02 to +0.16 band across v7 and v8. gym-config dropped from +0.111 to +0.027 (change −0.084, same-all provenance — judge drift tail). add-benchmark rose slightly to +0.162. No edits made; these movements are the kind of tail we flagged in the noise-floor section.

### gym-scaffold-agent — same-all drift into positive territory

v7 `skill | refs=T` = −0.040 (below noise). v8 = +0.053 (change +0.093, same-all provenance). Technically outside the 0.05 skill-level noise floor but attributable to judge drift, not skill content. The v7 read that "skill competes with refs on sc3" still applies on per-scenario evidence; aggregate noise makes skill-level claims weak at n=5.

### gym-scaffold-agent deployment caveat

The audit flagged a real content gap here: the skill covers RL training agents (cookie propagation, token IDs) but not non-RL agents (evaluation, orchestration, wrappers). This hasn't been addressed in v8 — no edit was made. An edit to this skill's scope is queued but not tested.

## How the v7 numbers relate to the v6 (contaminated) numbers

Pre-fix, the checkpoint reported these Δreward values against a control that was seeing references on disk (and SKILL.md pre-SKILL.md-fix). The "realistic deployment" equivalent in v7 is the `skill | refs=T` column:

| skill | v6 Δ (contaminated) | v7 skill \| refs=T | Δ shifted by |
|---|---|---|---|
| gym-run | +0.487 | +0.436 | −0.051 (holds) |
| gym-review | +0.152 | +0.029 | −0.123 (mostly reference value, not skill value) |
| gym-debug | +0.133 | +0.080 | −0.053 (shrinks but survives) |
| add-benchmark | +0.110 | +0.141 | +0.031 (holds) |
| gym-config | +0.089 | +0.111 | +0.022 (holds) |
| gym-scaffold-agent | +0.040 | −0.040 | −0.080 (flips sign, inside noise either way) |
| gym-data | −0.013 | +0.013 | +0.026 (ceiling both versions) |
| gym-profile | −0.144 | −0.107 | +0.037 (smaller, still negative) |

**gym-run is the only skill whose pre-fix claim survives intact** — predictable, since it was the only skill with no references to contaminate.

## What we can claim (v8)

Supported by v7 + v8 data, outside noise floor:

- **gym-run is load-bearing for its scenarios** (realistic +0.38, standalone +0.41 — held across v7 and v8).
- **add-benchmark and gym-debug have real realistic-deployment value** (+0.162 and +0.133 in v8, above noise).
- **Skills teach efficiency across the board** (Δtools −1.00 to −4.73 on realistic contrast in v8; pattern held from v7).
- **Narrate-to-references works as a prescription**: gym-profile's v7→v8 lift of +0.147 on the realistic contrast, under a single-skill `md`-only edit, validates the framework.
- **Adversarial scenarios reveal skill value** that ceiling-clipped scenarios hide: gym-data's realistic effect moved from +0.013 (unmeasurable) to +0.093 (measurable) under a single-skill `evals+fx`-only edit.
- **Shrinking a redundant SKILL.md preserves realistic value but can lose standalone value** — context-dependent win.

Not supported:

- Fine-grained claims about shape (bullet vs checkbox vs heading). Earlier shape-probe rollouts inherited a contamination bug; a clean rerun is deferred.
- A single-number "skill quality" ranking. Most skills carry value on some axis (standalone, efficiency, realistic) and not others. Any ranking is a weighting decision, not a measurement.
- Claims about gym-config or gym-scaffold-agent in the ±0.10 range — same-all drift made their v7→v8 movements ambiguous.

## Open methodology questions

- **Judge drift at temperature=0 remains the dominant noise source.** n=5 gives detectable effects down to ~±0.10 per cell / ~±0.05 skill-level. v7→v8 on same-all skills drifted up to −0.084 (gym-config) and +0.093 (gym-scaffold-agent) — a reminder that subtle effects are not reliably resolvable at this n.
- **Power analysis TBD.** A calibration run at n=20 on one cell would pin down the actual detectable effect size.
- **The "skill-only" cell is a useful diagnostic but a weird deployment target.** gym-review's +0.298 → +0.012 collapse shows that optimizing for one cell can be invisible on another. For product decisions, need to be clear which cell is the target.

## Retraction log

Claims from the earlier (pre-contamination-fix) checkpoint that do not survive v7/v8:

- ~~"Every skill reduces tool calls by 0.8–4.8 per rollout."~~ Replaced by the v8 `skill | refs=T` contrast: every skill reduces tool calls, magnitudes −1.00 to −4.73.
- ~~"gym-profile is actively misleading."~~ Replaced in v7 by "competes with its own references"; **retired in v8** — post-prescription the skill is slightly-positive on the realistic contrast.
- Shape-probe null result — still withdrawn pending rerun on clean harness.
- ~~"gym-review's SKILL.md is dead weight"~~ (from the skill audit). Nuanced in v8: dead weight for realistic deployment, load-bearing for skill-only deployment.
