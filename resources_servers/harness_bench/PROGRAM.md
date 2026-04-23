# Extending harness_bench with a new adapter

## Goal

Add support for a new agent harness (e.g. Claude Code, OpenClaw) by writing a
capability-to-tool-name map and, optionally, harness-specific task modules.
The core task suite remains unchanged; only the adapter is new.

## Inputs you need

1. The harness's tool documentation URL.
2. A list of the tool names the harness exposes, with one line each describing
   what the tool does.
3. For any harness-specific feature that does not fit an existing capability,
   a note on why a new task module is warranted.

## Steps

1. Open `capabilities.py`. Confirm every capability your harness supports is
   already listed. If a capability is genuinely missing (not just renamed),
   add it; otherwise do not touch this file.

2. Create `adapters/<harness>.py`. Declare a single module level dict:

   ```python
   from resources_servers.harness_bench.capabilities import Capability

   CAPABILITY_TO_TOOLS: dict[Capability, list[str]] = {
       Capability.FILESYSTEM_READ: ["<harness-tool-name>"],
       ...
   }
   ```

   One short paragraph at the top saying which harness this is and linking the
   tool docs. No runner, no factory, no config loader.

3. If the harness has a feature the core suite does not exercise (e.g. a
   screen reader, a GUI automation tool), add one task module at
   `tasks/<harness>_<feature>.py`. Follow the existing task modules: a
   `generate(seed, difficulty) -> Task` function, a deterministic RNG seeded
   on `seed * prime + difficulty`, and one grader builder from `grader.py`.
   Register the module in `generate.py`'s `CATEGORY_CONFIGS` only if it
   should be part of the default core suite; otherwise leave it opt-in.

4. Update `README.md` only if you added a new task category. Do not add
   adapter listings to the README.

## Style rules

- No em-dashes in any file. Use hyphens, semicolons, or periods.
- Minimal runtime dependencies; stdlib only unless there is a concrete need.
- Prefer deterministic graders (exact_int, exact_str, regex, subprocess_test).
  LLM judges are acceptable only when no deterministic grader is possible;
  if added, the builder must serialize to `{name, meta}` like the existing
  graders and be registered in `load_task_from_row`.
- Keep task modules under ~100 lines each.
- No abstract base classes unless there is more than one subclass today.

## Validation

From the server root:

```bash
python3 tests/test_suite_roundtrip.py
```

It generates a small suite with seeds 0..1, loads every row back, and verifies
grader names and capability strings roundtrip. A green run is the bar for
merging a new adapter.
