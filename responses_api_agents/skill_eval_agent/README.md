# skill_eval_agent

Agent that orchestrates [agentskills.io](https://agentskills.io/specification)
skill evaluations on real NeMo Gym infrastructure. Produces a `reward` per
rollout that equals the fraction of behavioral assertions satisfied, so
`ng_collect_rollouts` + `ng_reward_profile` yield the same delta
(with-skill − without-skill) that the Sprint 4 `scripts/eval_skills.py` harness
computes by hand.

## Stack

Three servers are wired together:

| Role | Server | What it does |
|---|---|---|
| Tool sandbox | `resources_servers/skill_workspace` | Seeds a scoped tmpdir with `SKILL.md`, `scripts/`, `references/`, and fixtures. Exposes `/run_bash` and `/read_file`. |
| Grader | `resources_servers/skill_judge` | LLM-as-judge that returns per-assertion binary grades; aggregate reward = fraction satisfied. |
| Policy | any `responses_api_models/*` | The model under evaluation. |

## /run flow

1. `POST /seed_session` → `skill_workspace` with `{skill_path, scenario_id, files}` returning `env_id`.
2. If `verifier_metadata.with_skill`, prepend a system message containing the SKILL.md body. Inject `run_bash`/`read_file` tool schemas when the incoming request has no tools.
3. Model ↔ tool loop (bounded by `max_steps`). Every tool call is dispatched to `skill_workspace` with the `env_id` and captured into a `ToolCallLogEntry`.
4. `POST /verify` → `skill_judge`, forwarding the captured `tool_calls` + `assertions` + model response via `verifier_metadata`.
5. `POST /close` → `skill_workspace` runs in a `finally` block so the workspace is cleaned up even on error.

## Input JSONL shape

```json
{
  "responses_create_params": {"input": [{"role": "user", "content": "<task prompt>"}]},
  "verifier_metadata": {
    "skill_path": "/abs/path/to/.claude/skills/gym-review",
    "skill_name": "gym-review",
    "skill_md_sha": "851931cb5698",
    "scenario_id": 1,
    "files": ["evals/scenario_1/broken_agent.py"],
    "with_skill": true,
    "skill_md": "<contents of SKILL.md>",
    "assertions": ["response identifies httpx usage", "response recommends aiohttp"]
  }
}
```

`skill_md_sha` is `sha256(SKILL.md)[:12]`, populated on every record (both
`with_skill=True` and `False`) so downstream tooling can tell which SKILL.md
body a scoreboard measured. Use `scripts/build_skill_eval_jsonl.py` to
generate one line per (scenario × {with, without}) pair from a skills
directory and `scripts/diff_skill_scoreboards.py` to compute per-skill deltas
and diff two scoreboards with a `same-sha` marker.

## Config

See `configs/skill_eval_agent.yaml`. Tunables:

- `max_steps` (default 8) — caps the model↔tool loop length.
- `inject_tools` (default true) — auto-injects `run_bash`/`read_file` schemas if the JSONL carries no tools.
