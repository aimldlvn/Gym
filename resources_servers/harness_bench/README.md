# harness_bench

A small procedural benchmark for LLM agents running inside tool-using
harnesses (Hermes, Claude Code, etc.). Tasks declare the abstract
**capabilities** they need (e.g. `filesystem_read`, `terminal`,
`code_execute`), not concrete tool names. A harness **adapter** is the shim
that maps capabilities to whatever tools the target harness actually exposes.

## Core task suite

| category | capabilities | grader |
|---|---|---|
| `adversarial_hallucination` | none | `not_called_tool` |
| `terminal_calc` | terminal, code_execute | `exact_int` |
| `python_data` | terminal, code_execute, filesystem_read | `exact_str` / `exact_int` / `regex` |
| `terminal_file` | terminal, filesystem_read | `exact_int` |
| `multi_tool_chain` | terminal, filesystem_read, code_execute | `chain_answer_and_ntools` |
| `skill_invoke` | skill_invoke | `called_any_of` |
| `todo_plan` | todo_track | `min_tool_calls_and_answer` |
| `bugfix_mini` | filesystem_read, filesystem_write, terminal | `subprocess_test` (partial credit) |

`adversarial_hallucination` probes whether the agent refuses to emit
function_calls for tools that do not exist.

## Staged files

Tasks that stage payloads (`python_data`, `terminal_file`, `multi_tool_chain`,
`bugfix_mini`) write under `$HARNESS_BENCH_STAGE` if set, otherwise under
`$HOME/.harness_bench/stage`. The stage is created lazily by `generate()`.

## Generate the suite

From the Gym repo root:

```bash
python -m resources_servers.harness_bench.generate \
    --out resources_servers/harness_bench/data/suite_v1.jsonl \
    --seeds 0:20
```

`--seeds a:b` is a half-open range; `--difficulties 1,2,3` overrides the
per-category default ranges. Each row is a JSON dict with
`task_id, category, difficulty, seed, required_capabilities, grader, ...`
and an OpenAI-style `responses_create_params` block with the user turn.

## Row schema

The loader accepts both `required_capabilities` (new) and `required_tools`
(legacy) so existing production JSONLs still grade.

## Validation

From the server root (`resources_servers/harness_bench/`):

```bash
python3 tests/test_suite_roundtrip.py
```

## Config

See `configs/harness_bench_hermes_agent.yaml` for the Hermes agent wiring.

## Writing a harness adapter

See `PROGRAM.md`. The Hermes adapter in `adapters/hermes.py` is the reference.
