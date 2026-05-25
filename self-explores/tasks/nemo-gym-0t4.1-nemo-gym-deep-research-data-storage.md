---
date: 2026-05-24
type: task-worklog
task: nemo-gym-0t4.1
parent: nemo-gym-0t4
title: "nemo-gym — T4.1 Deep Research: Data/Storage Layer"
status: open
detailed_at: 2026-05-24 23:30
detail_score: ready-for-dev
tags: [system-design, deep-research, data-storage, nemo-gym]
---

# nemo-gym — T4.1 Deep Research: Data/Storage Layer — Detailed Design

## 1. Objective
Phân tích "Tại sao họ thiết kế như vậy?" cho Data/Storage/Config layer của nemo-gym, ≥3 design decisions full 4 điểm (Principle/Rationale/Historical/Industry).

## 2. Scope

**In-scope (modules):**
- [`nemo_gym/cli.py`](../../nemo_gym/cli.py) — Hydra entrypoints (ng_run, ng_test, ng_collect_rollouts, ng_prepare_data)
- [`nemo_gym/config_types.py`](../../nemo_gym/config_types.py) — Pydantic schemas
- [`nemo_gym/global_config.py`](../../nemo_gym/global_config.py) — singleton config holder
- [`nemo_gym/dataset_orchestrator.py`](../../nemo_gym/dataset_orchestrator.py)
- [`nemo_gym/gitlab_utils.py`](../../nemo_gym/gitlab_utils.py)
- [`nemo_gym/hf_utils.py`](../../nemo_gym/hf_utils.py)
- [`nemo_gym/train_data_utils.py`](../../nemo_gym/train_data_utils.py)
- `env.yaml` (root)
- Resources YAML configs: [`resources_servers/*/configs/*.yaml`](../../resources_servers/)

**Out-of-scope:**
- KHÔNG đụng business logic verify()/run() (T4.2).
- KHÔNG đụng FastAPI endpoint shape (T4.3).
- KHÔNG đụng Ray/aiohttp infra (T4.4).

## 3. Input / Output

**Input:** Hot-zone files (Scope), git log của các files đó.

**Output:** ≥3 decisions, mỗi cái 4 điểm:
```
### Decision: {tên}
1. Nguyên lý: ...
2. Tại sao KHÔNG đơn giản hơn: ...
3. Historical context: ...
4. Industry reference: [link/repo URL]
```

## 4. Dependencies
- Beads: blocked-by T2 (`nemo-gym-ir8`).
- Parent: `nemo-gym-0t4`.
- Tools: `git log -- {file}`, `grep`.

## 5. Flow xử lý

### Step 1: Verify modules (~3 phút)
```bash
for f in nemo_gym/cli.py nemo_gym/config_types.py nemo_gym/global_config.py nemo_gym/dataset_orchestrator.py nemo_gym/gitlab_utils.py nemo_gym/hf_utils.py; do
  [ -f "$f" ] && wc -l "$f" || echo "MISSING: $f"
done
ls env.yaml 2>&1 || echo "env.yaml missing (expected for new clone)"
```

### Step 2: Decision 1 — Hydra composition (~10 phút)
**Câu hỏi sắc bén:** Sao Hydra+OmegaConf thay vì argparse / pydantic-settings / env vars?
```bash
grep -n "@hydra\|compose\|OmegaConf\|HydraConfig" nemo_gym/cli.py | head -10
git log --oneline -5 -- nemo_gym/cli.py
```
- **Principle:** Composition over inheritance, Config-as-Code.
- **Rationale:** YAML cascading allows benchmark/model/agent reusable + override at CLI.
- **Historical:** {commit hash từ git log}
- **Industry:** [Hydra@Meta](https://hydra.cc/), [PyTorch Lightning configs](https://lightning.ai/docs/pytorch/stable/cli/lightning_cli.html), [Kedro](https://kedro.readthedocs.io/).

### Step 3: Decision 2 — gitlab_identifier + jsonl_fpath coexistence (~10 phút)
**Câu hỏi sắc bén:** Tại sao 2 field cùng tồn tại (không thay thế)?
```bash
grep -n "gitlab_identifier\|jsonl_fpath" nemo_gym/dataset_orchestrator.py nemo_gym/config_types.py
```
- **Principle:** Strategy pattern (resolve dataset từ gitlab/hf/local) + Local cache pattern.
- **Rationale:** `gitlab_identifier` = source, `jsonl_fpath` = local cache destination → tách concerns fetch vs read.
- **Historical:** {commit khi tách field, nếu có}
- **Industry:** [DVC](https://dvc.org/) cache, [MLflow artifacts](https://mlflow.org/docs/latest/tracking.html), [HuggingFace datasets cache](https://huggingface.co/docs/datasets/cache).

### Step 4: Decision 3 — example vs train/validation dataset split (~10 phút)
**Câu hỏi sắc bén:** Tại sao `example` commit vào git, `train/validation` chỉ ở registry?
```bash
grep -n "example_validation\|train_preparation\|*train.jsonl" nemo_gym/ scripts/ -r 2>/dev/null | head
cat resources_servers/example_single_tool_call/data/.gitignore 2>&1
```
- **Principle:** Test fixtures in-repo vs data lake out-of-repo.
- **Rationale:** Example dùng cho CI smoke test (5 entries đủ), train/val lớn → registry.
- **Historical:** `.gitignore` pattern `*train.jsonl` xuất hiện khi nào.
- **Industry:** [pytest fixtures](https://docs.pytest.org/en/stable/explanation/fixtures.html), [LFS pointers](https://git-lfs.com/) (chọn registry thay vì LFS — tại sao?).

### Step 5: (Optional) Decision 4 — verifier_metadata opaque schema (~10 phút)
**Câu hỏi sắc bén:** Tradeoff flexibility vs validation?
- **Principle:** Schema-less envelope / open-content pattern.
- **Rationale:** Per-benchmark fields khác nhau (test cases, expected answers, task IDs) → schema strict sẽ break extensibility.

## 6. Edge Cases & Error Handling
| Case | Trigger | Expected | Recovery |
|---|---|---|---|
| `env.yaml` missing trong dev environment | `ls env.yaml` fail | Document là expected; user phải tạo từ `env.example.yaml` | Note trong worklog |
| `git log` ngắn (squashed history) | `--oneline` trả ≤2 commits | Historical = "Insufficient history (squashed)" + skip điểm 3 cho decision đó | Bỏ điểm 3 cho 1 decision tối đa |
| Industry reference link 404 | curl trả 404 | Tìm alternative (web archive, alternative repo) | Note "Archived: {wayback URL}" |

## 7. Acceptance Criteria
- **Happy:** Given T2 closed, When task chạy, Then ≥3 decisions với đủ 4 điểm + mỗi decision có industry reference URL + ≥1 historical context dùng git log evidence.
- **Negative:** Given file `nemo_gym/cli.py` không có Hydra usage (renamed), When scan, Then decision Hydra được thay thế bằng decision khác (vd argparse, click) + reason ghi rõ.

## 8. Technical Notes
- Hydra version: check `pyproject.toml` hoặc `requirements.txt` cho `hydra-core>=X.Y`.
- GitLab MLflow URI format: `https://<host>/api/v4/projects/<ID>/ml/mlflow` (CLAUDE.md).
- Example smoke test count: 5 entries (CLAUDE.md confirm).

## 9. Risks
- **R1:** Industry reference quá broad (vd "configuration management"). *Mitigation:* Phải link tới repo/docs cụ thể, không Wikipedia general.
- **R2:** Decision overlap với T4.2 (vd verifier_metadata cũng là business logic). *Mitigation:* Focus DATA flow, không touch verify() logic.

## Worklog

### Decision 1: Hydra Composition over argparse/pydantic-settings

**1. Nguyên lý gốc:** Composition over Inheritance (GoF) + Config-as-Code.

Hydra xây dựng config dict bằng cách **merge** nhiều YAML file theo thứ tự ưu tiên rõ ràng (YAML file → env.yaml → CLI override), thay vì định nghĩa schema cứng bằng argparse. Trong `nemo_gym/global_config.py` (hàm `GlobalConfigDictParser.parse()`), pipeline merge là:

```
extra_configs (từ config_paths) → dotenv_extra_config (env.yaml) → global_config_dict (CLI)
```

`global_config_dict` cuối cùng luôn thắng vì nó là tham số cuối trong `OmegaConf.merge(...)`. Đây là **Decorator pattern ứng dụng vào config**: mỗi layer là một "decorator" bổ sung lên base config.

**2. Tại sao KHÔNG đơn giản hơn (argparse / pydantic-settings / env vars):**

| Phương án đơn giản hơn | Tại sao bị loại |
|---|---|
| `argparse` thuần | Không hỗ trợ hierarchical YAML merge. Thêm 1 server = thêm N CLI flags. 50 benchmarks = 50 × (3–5 flags) = 150-250 flags không quản lý được. |
| `pydantic-settings` | Flat env var model: `MY_SERVER_HOST=...` không thể biểu diễn cấu trúc `{server_name: {server_type: {inner_name: {...}}}}`. |
| Hard-coded env vars | Không composable, không override tại CLI, không diff/review config như code. |

NeMo Gym cần run nhiều loại server cùng lúc với config riêng cho từng server trong một lần chạy duy nhất — đây là use case Hydra được thiết kế chính xác cho.

Ngoài ra, `global_config.py` còn implement custom directives `inherit_from` và `copy` (xem `_recursively_swap_keys_helper()`) — tính năng không có trong argparse/pydantic-settings, cho phép reuse config giữa các server instances.

**3. Historical context:**

```
git log --oneline -- nemo_gym/cli.py | head -5
e2931bfa fix: pypi  (#1056)
b1be550b feat: AALCR and Ruler benchmarks; Misc infra (#966)
74a527be fix: RMtree ignores errors (#964)
f1399809 benchmark: LiveCodeBench v5 and v6 (#933)
6d80807d feat: Benchmark infra refactors (#906)
```

Commit `6d80807d` (2026-03-19, "Benchmark infra refactors") thêm directive `inherit_from` (đổi tên từ `swap_key`) — bằng chứng config complexity tăng dần buộc team mở rộng Hydra thay vì switch sang giải pháp đơn giản hơn. Commit message ghi rõ: *"Rename `swap_key` directive to `inherit_from` per suggestion"*.

Commit `c45ee6aa` (2026-02-25, "Rollout infra upgrades") thêm 42 dòng vào `global_config.py` mà không thay đổi parsing framework — cho thấy Hydra đủ linh hoạt để mở rộng.

**4. Industry reference:**
- [Hydra — Composable Configuration Framework (Meta/Facebook AI)](https://hydra.cc/docs/intro/) — framework được tạo ra chính xác cho ML experiment configuration.
- [PyTorch Lightning CLI — Hydra integration pattern](https://lightning.ai/docs/pytorch/stable/cli/lightning_cli.html) — cùng kiến trúc compose YAML cho training runs.
- [OmegaConf structured configs](https://omegaconf.readthedocs.io/en/2.3_branch/structured_config.html) — base layer mà Hydra builds on.

---

### Decision 2: `gitlab_identifier` + `jsonl_fpath` Coexistence (Strategy + Local Cache)

**1. Nguyên lý gốc:** Strategy Pattern (GoF) cho dataset source + Cache pattern (POSA) cho local path.

Trong `nemo_gym/config_types.py`, `DatasetConfig` có đồng thời:
- `jsonl_fpath: str` — local filesystem path (luôn bắt buộc)
- `gitlab_identifier: Optional[JsonlDatasetGitlabIdentifer]` — remote registry pointer
- `huggingface_identifier: Optional[JsonlDatasetHuggingFaceIdentifer]` — HF registry pointer

Hai field này không thay thế nhau — chúng thực hiện **hai responsibility hoàn toàn khác nhau**:
- `*_identifier` = "tìm dataset ở đâu trên remote" (source strategy)
- `jsonl_fpath` = "đọc dataset từ đâu trên local" (cache destination)

Trong `train_data_utils.py` (`TrainDataProcessor.load_datasets()`), logic quyết định backend:
```python
if d.gitlab_identifier and d.huggingface_identifier:
    backend = config.data_source  # user chọn
elif not d.gitlab_identifier:
    backend = "huggingface"
elif not d.huggingface_identifier:
    backend = "gitlab"
```
Đây là **Strategy selector** dựa trên config — không cần if/else trong business logic.

Sau khi download, file được lưu vào `jsonl_fpath` — đây là **Cache materialization**: lần sau nếu file đã tồn tại, `load_datasets()` skip download hoàn toàn (`if jsonl_fpath.exists(): local_datasets_found[c.name].append(d)`).

**2. Tại sao KHÔNG đơn giản hơn:**

Phương án đơn giản: chỉ dùng `remote_url: str` và download on-the-fly mỗi lần run.

Vấn đề:
- **Repeatability bị phá vỡ**: training run không thể dùng dataset đã được validated và fixed tại một version cụ thể.
- **HPC environment**: Lustre filesystem trên cluster không có internet. Download phải được thực hiện trên login node trước, sau đó dùng file local trong job.
- **Data versioning**: `gitlab_identifier.version = "0.0.1"` pinned — rollback về dataset version cũ không cần thay đổi code, chỉ đổi YAML.
- Nếu merge thành một field (vd `source: "gitlab://dataset_name/0.0.1/train.jsonl"`), mất type safety và validation từ Pydantic.

**3. Historical context:**

```
git log --oneline -- nemo_gym/gitlab_utils.py | head -3
4a19206f Huggingface dataset integration (#101)
b77546bc Update header for OSRB and license (#287)
c93c0e87 Update GitHub with Gitlab main (#3)
```

Commit `4a19206f` (2025-11-10, "Huggingface dataset integration") là milestone quan trọng nhất: PR này **thêm `huggingface_identifier`** vào `DatasetConfig` song song với `gitlab_identifier` đã tồn tại, thay vì replace GitLab bằng HF. Commit message: *"adds support for Huggingface dataset management (upload/download/delete Gitlab artifact(s))"* — xác nhận quyết định giữ cả hai registry song song.

**4. Industry reference:**
- [DVC (Data Version Control) — remote + cache pattern](https://dvc.org/doc/user-guide/data-management/remote-storage) — cùng kiến trúc: `dvc remote` = remote pointer, `.dvc` file = local cache manifest.
- [MLflow Model Registry — versioned artifacts](https://mlflow.org/docs/latest/model-registry.html) — GitLab MLflow backend được dùng trong `gitlab_utils.py` (`MlflowClient`).
- [HuggingFace Datasets cache](https://huggingface.co/docs/datasets/en/cache) — HF backend trong `hf_utils.py` dùng cùng pattern cache-first.

---

### Decision 3: Example Dataset In-Git, Train/Validation In Registry

**1. Nguyên lý gốc:** Test Fixtures In-Repo (XP/TDD principle) + Data Lake out-of-repo (Data Engineering best practice).

Ba loại dataset có lifecycle và kích thước hoàn toàn khác:

| Type | Size | Location | Mục đích |
|---|---|---|---|
| `example` | 5 entries | Git (committed) | CI smoke test, PR validation |
| `train` | ~10k–100k+ entries | GitLab/HF registry | RL training job |
| `validation` | ~1k–10k entries | GitLab/HF registry | Eval during training |

`DatasetConfig.check_train_validation_sets()` validator trong `config_types.py` enforce điều này:
```python
if self.type in ["train", "validation"]:
    assert self.license is not None, f"A license is required for {self.name}"
```
Chỉ `train`/`validation` mới bắt buộc có `license` — vì chúng là artifacts có thể distributed; `example` không cần.

`data/.gitignore` trong mỗi resources server gitignore chính xác `*train.jsonl`, `*validation.jsonl` nhưng KHÔNG gitignore `example.jsonl`:
```
*train.jsonl
*validation.jsonl
*train_prepare.jsonl
*validation_prepare.jsonl
*example_prepare.jsonl
```
Note: `example.jsonl` (không có `_prepare`) KHÔNG bị gitignore — đây là deliberate design.

Trong `cli.py` (`_validate_data_single()`), CI validation kiểm tra `data/example.jsonl` tồn tại và có đúng 5 entries — nếu thiếu, PR fail ngay:
```python
assert count == 5, f"Expected 5 examples at {example_fpath} but got {count}."
```

**2. Tại sao KHÔNG đơn giản hơn:**

Phương án đơn giản hơn:
- (A) Tất cả trong git: Train/validation dataset lớn (GB-TB) sẽ bloat git repo, clone chậm, CI timeout.
- (B) Tất cả trong registry: CI không thể chạy smoke test mà không download — thêm dependency vào GitLab/HF credentials trong CI, fragile.
- (C) Git LFS: Vẫn phải pull LFS objects, bandwidth tốn kém, không phân biệt được version semantic của dataset (không có `dataset_name + version` concept).

Quyết định in-git chỉ 5 examples là **minimum viable fixture**: đủ để test format JSONL hợp lệ, schema đúng, server có thể parse, nhưng không đủ để làm chậm CI hay tạo data leakage risk.

**3. Historical context:**

```
git log --oneline --all --diff-filter=A -- "resources_servers/*/data/.gitignore" | head -5
9f14ff86 feat: GRL Sokoban Gymnasium Environment (#1330)
ab1f44b5 feat: GRL Tetris Gymnasium Environment (#1331)
25808bf4 Rename examples simple_weather and stateful_counter (#479)
```

Mỗi lần thêm resources server mới (ví dụ `9f14ff86` — GRL Sokoban, `ab1f44b5` — GRL Tetris) đều tạo `data/.gitignore` mới với cùng pattern — pattern này được hardcode vào `init_resources_server()` trong `cli.py` (dòng 841-847), tức là **nó là first-class convention** của framework, không phải ad-hoc.

**4. Industry reference:**
- [pytest fixtures — test data in-repo pattern](https://docs.pytest.org/en/stable/explanation/fixtures.html) — canonical reference cho "5 examples là fixture, không phải data".
- [The Twelve-Factor App — Config/Data separation](https://12factor.net/config) — backing services (registries) cho large data, filesystem cho small config/fixtures.
- [Git LFS vs Dataset Registries (Hugging Face blog)](https://huggingface.co/docs/hub/en/repositories-getting-started#what-files-should-i-store-with-git-lfs) — HF khuyến nghị dùng dataset hosting thay LFS cho file >10MB, cùng rationale với NeMo Gym.

---

### Decision 4 (Bonus): `verifier_metadata` Opaque Schema — Flexibility over Strict Validation

**1. Nguyên lý gốc:** Open Content Pattern / Schema-less Envelope — "be conservative in what you send, liberal in what you accept" (Postel's Law ứng dụng vào data schema).

Trong `nemo_gym/base_resources_server.py` (được import từ `train_data_utils.py`), `BaseRunRequest` có `verifier_metadata` là `Dict[str, Any]` — hoàn toàn opaque với framework. Framework không validate nội dung bên trong, chỉ pass-through từ JSONL input tới resources server `verify()`.

Từ `config_types.py`, `DatasetConfig` không có field nào cho schema của `verifier_metadata` — mỗi benchmark tự define structure riêng.

**2. Tại sao KHÔNG đơn giản hơn (strict schema):**

Nếu framework enforce strict schema cho `verifier_metadata`:
- Math benchmark cần: `{"expected_answer": "42", "difficulty": "hard"}`
- Code benchmark cần: `{"test_cases": [...], "timeout_seconds": 5, "language": "python"}`
- Tool-calling benchmark cần: `{"expected_tool_calls": [...], "allowed_tools": [...]}`

Không thể unify thành một Pydantic model mà không dùng Union với 50+ discriminated types — một per benchmark. Mỗi lần thêm benchmark mới cần sửa core framework schema.

Tradeoff được chấp nhận: lỗi schema trong `verifier_metadata` chỉ bị phát hiện khi resources server gọi `verify()` (runtime), không phải khi parse JSONL (load time). Đây là acceptable vì: (1) `ng_prepare_data` chạy trước training, (2) 5-entry example validation catch lỗi format sớm.

**3. Historical context:**

```
git log --oneline -- nemo_gym/train_data_utils.py | head -3
6d80807d feat: Benchmark infra refactors (#906)
c45ee6aa feat: Rollout infra upgrades (#761)
f1d19a88 fix: ng prepare data metrics conflict (#738)
```

Commit `6d80807d` ("Benchmark infra refactors") refactor infrastructure để support multiple benchmarks chạy cùng lúc — nếu `verifier_metadata` có strict schema, PR này sẽ phải thêm Union types cho từng benchmark được thêm vào. Thực tế PR chỉ sửa config structure, không thay đổi `verifier_metadata` — bằng chứng quyết định opaque được giữ nguyên qua nhiều evolution.

**4. Industry reference:**
- [Protocol Buffers — `Any` type for opaque payloads](https://protobuf.dev/programming-guides/proto3/#any) — Google's pattern cho opaque extension points trong distributed systems.
- [OpenAI API — `metadata` field pattern](https://platform.openai.com/docs/api-reference/runs/object#runs/object-metadata) — `Dict[str, str]` opaque metadata trên mọi object, cùng rationale.
- [JSON Schema — `additionalProperties: true` open content](https://json-schema.org/understanding-json-schema/reference/object.html#additional-properties) — canonical reference cho schema extensibility tradeoff.

## Phản biện (2026-05-24, Round 1+2)
- Round 1: 8.0/10 — modules concrete, 4 điểm framework rõ.
- Round 2: 9.2/10 — Industry URL bắt buộc, git log evidence requirement.
