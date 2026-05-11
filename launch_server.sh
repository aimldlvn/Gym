# ============================
# for acereason-math
# ============================
# # create output dir
# mkdir -p output/acereason-math-mock
# start server
# ng_run "+config_paths=[responses_api_agents/verifiers_agent/configs/acereason-math.yaml,responses_api_models/vllm_model/configs/vllm_model.yaml]"


# ============================
# for wiki-search
# ============================
# Load project secrets (NVIDIA_API_KEY, HF_TOKEN, ...) — agent server inherits these.
set -a
source ~/Gym/.env
set +a
# create output dir
mkdir -p output/wiki-search-mock
ng_run "+config_paths=[responses_api_agents/verifiers_agent/configs/wiki-search.yaml,responses_api_models/vllm_model/configs/vllm_model.yaml]"
