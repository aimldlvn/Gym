#!/usr/bin/env bash
set -euo pipefail

# acereason-math is a deterministic math env — no judge / embed keys required.
# Run from inside responses_api_agents/verifiers_agent with .venv active.

# Full dataset
# python3 scripts/create_dataset.py \
#     --env-id acereason-math \
#     --output data/acereason-math.jsonl

# Mock training set (1000 examples, fixed seed)
# python3 scripts/create_dataset.py \
#     --env-id acereason-math \
#     --size 1000 \
#     --seed 42 \
#     --output data/acereason-math-mock-train.jsonl

# Mock validation set (100 examples)
# python3 scripts/create_dataset.py \
#     --env-id acereason-math \
#     --size 100 \
#     --seed 123 \
#     --output data/acereason-math-mock-val.jsonl

# Tiny smoke set (3 examples)
python3 scripts/create_dataset.py \
    --env-id acereason-math \
    --size 3 \
    --seed 123 \
    --output data/acereason-math-mock.jsonl
