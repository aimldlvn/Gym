# ============================
# for acereason-math
# ============================
# generate a rollout
# ng_collect_rollouts \
#     +agent_name=verifiers_agent \
#     +input_jsonl_fpath=responses_api_agents/verifiers_agent/data/acereason-math-mock.jsonl \
#     +output_jsonl_fpath=output/acereason-math-mock/acereason-math-mock-rollouts.jsonl \
#     +num_repeats=3 \
#     +num_samples_in_parallel=2

# ============================
# for wiki-search
# ============================
# generate a rollout
ng_collect_rollouts \
    +agent_name=verifiers_agent \
    +input_jsonl_fpath=responses_api_agents/verifiers_agent/data/wiki-search-mock.jsonl \
    +output_jsonl_fpath=output/wiki-search-mock/wiki-search-mock-rollouts.jsonl \
    +num_repeats=3 \
    +num_samples_in_parallel=2