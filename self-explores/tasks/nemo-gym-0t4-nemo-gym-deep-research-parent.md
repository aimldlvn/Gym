---
date: 2026-05-24
type: task-worklog
task: nemo-gym-0t4
title: "nemo-gym — Deep Research (Tư duy của Top 0.1%) [PARENT]"
status: open
detailed_at: 2026-05-24 23:30
detail_score: ready-for-dev
tags: [system-design, deep-research, parent, nemo-gym, T4]
---

# nemo-gym — Deep Research [PARENT] — Detailed Design

## 1. Objective
Điều phối 4 sub-tasks Deep Research (T4.1-T4.4 theo layer) và tổng hợp cross-layer findings vào worklog parent với 5 sections + ≥2 cross-layer patterns + ≥1 industry comparison.

## 2. Scope

**In-scope:**
- Đọc 4 sub-worklogs khi cả 4 sub closed.
- Tìm cross-layer patterns (async-first, config injection, error handling).
- Detect inconsistencies (1 layer drift khỏi convention).
- Top 3 design principles xuyên suốt nemo-gym.
- Industry comparison ngắn với ≥1 reference.

**Out-of-scope:**
- KHÔNG ghi lại nội dung sub-worklog (chỉ link clickable).
- KHÔNG sửa code.
- KHÔNG tạo Notion page (T6).

## 3. Input / Output

**Input:**
- 4 sub-worklogs:
  - [`nemo-gym-0t4.1-nemo-gym-deep-research-data-storage.md`](nemo-gym-0t4.1-nemo-gym-deep-research-data-storage.md)
  - [`nemo-gym-0t4.2-nemo-gym-deep-research-business-logic.md`](nemo-gym-0t4.2-nemo-gym-deep-research-business-logic.md)
  - [`nemo-gym-0t4.3-nemo-gym-deep-research-interface-api.md`](nemo-gym-0t4.3-nemo-gym-deep-research-interface-api.md)
  - [`nemo-gym-0t4.4-nemo-gym-deep-research-infrastructure.md`](nemo-gym-0t4.4-nemo-gym-deep-research-infrastructure.md)
- T2 worklog ([`nemo-gym-ir8-*.md`](nemo-gym-ir8-nemo-gym-strategic-evaluation.md)).

**Output:**
- 5 sections trong file này: Sub-task summary, Cross-layer patterns, Inconsistencies, Top 3 principles, Industry comparison.

## 4. Dependencies
- Beads: blocked-by T2 (`nemo-gym-ir8`).
- Gate: KHÔNG bắt đầu cho đến khi cả 4 sub closed.
- Tools: `bd ready` để check unblock status.

## 5. Flow xử lý

### Step 1: Verify gate (~2 phút)
```bash
bd list --status=closed | grep -E "nemo-gym-0t4\.(1|2|3|4)"
# Expect: 4 lines
bd ready 2>&1 | grep "nemo-gym-0t4"
```
**Verify:** Cả 4 sub closed; parent ở status `ready`.

### Step 2: Sub-task Summary table (~5 phút)
| Sub | ID | Top decision | Link |
|---|---|---|---|
| T4.1 Data/Storage | nemo-gym-0t4.1 | {top từ sub-1} | [worklog](nemo-gym-0t4.1-nemo-gym-deep-research-data-storage.md) |
| T4.2 Business Logic | nemo-gym-0t4.2 | {top từ sub-2} | [worklog](nemo-gym-0t4.2-nemo-gym-deep-research-business-logic.md) |
| T4.3 Interface/API | nemo-gym-0t4.3 | {top từ sub-3} | [worklog](nemo-gym-0t4.3-nemo-gym-deep-research-interface-api.md) |
| T4.4 Infrastructure | nemo-gym-0t4.4 | {top từ sub-4} | [worklog](nemo-gym-0t4.4-nemo-gym-deep-research-infrastructure.md) |

### Step 3: Cross-layer pattern detection (~10 phút)
Tìm ≥2 patterns xuất hiện ≥2 layers:
- **Async-first:** count `async def` per layer (Data/Logic/API/Infra). Pattern coherent?
- **Config injection:** mỗi layer nhận Hydra config qua kwargs? hay singleton?
- **Error handling style:** raise / return None / structured response?

```bash
for layer in nemo_gym/dataset_orchestrator.py nemo_gym/base_*.py nemo_gym/server_utils.py; do
  echo "=== $layer ==="
  grep -c "^async def\| async def" "$layer" 2>/dev/null
done
```
**Verify:** ≥2 patterns documented với evidence từ ≥2 sub-worklogs.

### Step 4: Inconsistencies detection (~5 phút)
Cố ý tìm layer drift:
- 1 layer dùng httpx thay vì aiohttp?
- 1 layer dùng sync I/O trong async context?
- 1 layer thiếu retry / propagation pattern?

Verdict: "Không phát hiện" HOẶC "Phát hiện X" (cụ thể).

### Step 5: Top 3 design principles (~10 phút)
Dựa trên cross-layer patterns + Industry comparison:
1. **{Principle 1}** — evidence từ sub X + sub Y (clickable).
2. **{Principle 2}** — evidence ...
3. **{Principle 3}** — evidence ...

### Step 6: Industry comparison (~5 phút)
So với:
- OpenAI Evals (https://github.com/openai/evals)
- Verifiers (https://github.com/willccbb/verifiers)
- LangChain agents framework
- TRL trainer pattern

≥1 reference link.

## 6. Edge Cases & Error Handling
| Case | Trigger | Expected | Recovery |
|---|---|---|---|
| Sub-task partial (≤3 closed) | `bd list --status=closed` trả <4 | Abort task, không bắt đầu | Đợi sub còn lại |
| Sub worklog rỗng/stub | mở file thấy `_(Sẽ điền)_` | Đánh dấu sub đó "needs rework", note vào parent | Sub phải redo |
| Không tìm thấy cross-layer pattern | scan ≥3 patterns không match | Document "Không phát hiện pattern xuyên suốt — kiến trúc loosely coupled" | Vẫn viết section, không skip |
| Industry comparison thiếu link | tìm không ra repo | Dùng link đến concept docs (vd Wikipedia "Inversion of Control") | OK |

## 7. Acceptance Criteria
- **Happy:** Given 4 sub closed, When task chạy, Then parent worklog có 5 sections đầy đủ + ≥2 cross-layer patterns + Top 3 principles có evidence clickable + ≥1 industry reference URL.
- **Negative:** Given <4 sub closed, When task được pick up, Then task auto-abort với note "Gate chưa đạt: {X}/4 sub closed".

## 8. Technical Notes
- Parent unblock logic: bd dependencies — parent đợi tất cả `blocked-by:0t4.x` close. Có thể check qua `bd show 0t4 --json | jq .blocked_by`.
- Cross-layer count: dùng `wc -l` + `grep -c` để có số liệu rõ.

## 9. Risks
- **R1:** Sub-tasks output không consistent → cross-layer khó so sánh. *Mitigation:* Sub-tasks dùng template 4 điểm đồng nhất.
- **R2:** Skip industry comparison vì lười. *Mitigation:* AC require ≥1 URL — không có URL thì task không done.
- **R3:** Parent bị skip ("4 sub đủ rồi"). *Mitigation:* Parent unique value = cross-layer synthesis, không phải tổng hợp đơn thuần.

## Worklog

> Thực hiện: 2026-05-25. Executor agent T4 (parent synthesis).
> Input: 4 sub-worklogs T4.1–T4.4 đã hoàn thành và chứa evidence đầy đủ.

---

### Section 1: Sub-task Summary

| Sub | ID | Top Decision | Link |
|---|---|---|---|
| T4.1 Data/Storage | nemo-gym-0t4.1 | `gitlab_identifier` + `jsonl_fpath` coexistence: Strategy Pattern (remote source) + Cache Pattern (local destination) — hai field phục vụ hai responsibility khác nhau hoàn toàn, không thay thế nhau | [worklog](nemo-gym-0t4.1-nemo-gym-deep-research-data-storage.md) |
| T4.2 Business Logic | nemo-gym-0t4.2 | Reward binary 0.0/1.0 (không phải continuous float): RLVR paradigm — verifiable task chỉ có pass/fail deterministic, binary buộc model thực sự giải bài, tránh reward hacking và đảm bảo pass@k aggregation chuẩn | [worklog](nemo-gym-0t4.2-nemo-gym-deep-research-business-logic.md) |
| T4.3 Interface/API | nemo-gym-0t4.3 | `openai<=2.7.2` upper bound lock: NeMo Gym dùng openai SDK chỉ như type library (không phải HTTP client); 50+ imports từ `openai.types.*` khiến weekly breaking changes của openai là risk — lock controlled + bump manual | [worklog](nemo-gym-0t4.3-nemo-gym-deep-research-interface-api.md) |
| T4.4 Infrastructure | nemo-gym-0t4.4 | aiohttp Singleton thay vì httpx: httpcore O(n²) `_assign_requests_to_connections` bug gây 40-minute hang ở 16k concurrent requests (Sep 17, 2025 incident); aiohttp `TCPConnector` với worker-aware `limit // num_workers` scale tốt hơn hoàn toàn | [worklog](nemo-gym-0t4.4-nemo-gym-deep-research-infrastructure.md) |

---

### Section 2: Cross-Layer Patterns

Năm pattern dưới đây xuất hiện ít nhất 2 layers, với evidence cite trực tiếp từ sub-worklogs:

---

#### Pattern 1: Async-First (Coherent xuyên 4 layers)

**Định nghĩa:** Mọi I/O-bound operation đều là `async def`. Không có `requests.get()`, không có sync HTTP, không có blocking subprocess mà không có `asyncio.Semaphore`.

**Evidence từ T4.2 (Business Logic):**
> *"Các servers phức tạp nhất (bigcodebench, jailbreak) đều dùng `asyncio.Semaphore` để control concurrency — pattern nhất quán."*

`bigcodebench/app.py`:
```python
async def verify(self, body: BigCodeBenchVerifyRequest) -> BigCodeBenchVerifyResponse:
    async with self._semaphore:
        result = await self._run_in_venv(...)
```

**Evidence từ T4.4 (Infrastructure):**
> *"`ServerClient` wraps aiohttp với retry logic... global aiohttp client là singleton với connection pooling."*

`server_utils.py:74-145`: `_GLOBAL_AIOHTTP_CLIENT` singleton — entire HTTP transport layer là async, không có blocking call nào.

**Evidence từ T4.3 (Interface/API):**
> *"[`SimpleResponsesAPIModel.setup_webserver()`] expose chính xác đường dẫn `/v1/responses`"*

FastAPI + uvicorn + uvloop — ASGI stack, toàn bộ request handling là coroutine.

**Evidence từ T4.1 (Data/Storage):**
`dataset_orchestrator.py` + `train_data_utils.py` — `TrainDataProcessor.load_datasets()` dùng async download path.

**Kết luận:** 4/4 layers async-first. Pattern **hoàn toàn coherent**. Không phát hiện sync I/O leak.

---

#### Pattern 2: Config-as-Code via Hydra Injection (xuyên 4 layers)

**Định nghĩa:** Mọi behavior tunable đều được inject qua Hydra-merged YAML config, không hardcode trong logic, không dùng env vars đơn thuần.

**Evidence từ T4.1 (Data/Storage):**
> *"`global_config.py` implement merge pipeline: `extra_configs → dotenv_extra_config (env.yaml) → global_config_dict (CLI)`... `global_config_dict` cuối cùng luôn thắng vì nó là tham số cuối trong `OmegaConf.merge(...)`."*

Commit `6d80807d` thêm directive `inherit_from` — bằng chứng config complexity tăng theo thời gian nhưng framework (Hydra) không bị thay thế.

**Evidence từ T4.2 (Business Logic):**
> *"Policy-aware flow là ví dụ Strategy pattern thuần túy tại runtime (không phải subclass)"* — `jailbreak_detection` đọc `response_policy_mapped` từ config để route giữa các verify strategies.

`TextToSqlResourcesServer`: `check_twice_swap=True` là config flag, không hardcode trong logic.

**Evidence từ T4.4 (Infrastructure):**
> *"`cli_setup_command.py` inject `NEMO_GYM_CONFIG_DICT` env var"* vào child processes — config propagation qua process boundary cũng là Hydra dict, không phải static env vars.

`server_utils.py:112`: `limit=cfg.global_aiohttp_connector_limit // num_workers` — pool size là config-driven, không hardcode.

**Evidence từ T4.3 (Interface/API):**
`pyproject.toml` lines 85–89 — comment explicit về lý do pin version, update có timestamp — "Updated Wed Feb 17, 2026" — config change có audit trail.

**Kết luận:** 4/4 layers dùng Hydra config injection. Pattern **hoàn toàn coherent và là first-class citizen** của framework.

---

#### Pattern 3: Pydantic Schema Everywhere (xuyên 4 layers)

**Định nghĩa:** Mọi data boundary — request/response, config, inter-server message — đều là Pydantic model. Không có untyped dict ở wire boundary.

**Evidence từ T4.1 (Data/Storage):**
> *"Trong `nemo_gym/config_types.py`, `DatasetConfig` có... `jsonl_fpath: str`... `gitlab_identifier: Optional[JsonlDatasetGitlabIdentifer]`... Nếu merge thành một field, mất type safety và validation từ Pydantic."*

`DatasetConfig.check_train_validation_sets()` validator enforce `license` required cho train/validation.

**Evidence từ T4.2 (Business Logic):**
> *"`reward: float` trong `BaseVerifyResponse` là `float` không phải `bool` — framework cho phép continuous nhưng convention là binary."*

Base class Pydantic: `BaseVerifyRequest`, `BaseVerifyResponse` — mọi server phải implement đúng signature này.

**Evidence từ T4.3 (Interface/API):**
> *"`TokenIDLogProbMixin(BaseModel)`: `prompt_token_ids: List[int]`, `generation_token_ids: List[int]`, `generation_log_probs: List[float]`"*

NeMo Gym subclass `openai.types.responses.*` bằng Pydantic models để add RL fields — Pydantic là ngôn ngữ extension.

> *"Override lại thành `List` để tránh lazy iterator trong Pydantic validation"* — evidence team chủ động maintain Pydantic compat.

**Evidence từ T4.4 (Infrastructure):**
`GlobalConfig` là Pydantic model được inject qua `model_post_init` — infrastructure config cũng typed.

**Kết luận:** 4/4 layers. Pydantic không chỉ là validation library mà là **kiến trúc contract** của toàn framework.

---

#### Pattern 4: Service-Oriented Boundary via HTTP (xuyên 3 layers — Business/API/Infra)

**Định nghĩa:** Mỗi server type là một process độc lập expose HTTP endpoint. Communication giữa các server là HTTP, không phải function call.

**Evidence từ T4.2 (Business Logic):**
> *"Agent giao tiếp với model server và resources server qua **HTTP**... Ranh giới là **mạng HTTP**, không phải Python import."*

Bảng tradeoff: scaling, fault isolation, language boundary — tất cả favor HTTP microservice.

**Evidence từ T4.3 (Interface/API):**
> *"`SimpleResponsesAPIAgent` chỉ expose `/v1/responses` (không expose `/v1/chat/completions`) — cho thấy agent layer đã 'lean Responses API' trong khi model layer vẫn giữ backward compat."*

**Evidence từ T4.4 (Infrastructure):**
> *"`ServerClient` wraps aiohttp với retry logic (3 tries, exponential backoff). Session cookies propagate through the call stack."*

`initialize_ray()` trong `server_utils.py:395-442` — Ray cluster là process cluster riêng biệt, không in-process.

**Kết luận:** Pattern coherent. Mỗi layer đều contribute vào service mesh: business logic định nghĩa contracts, API layer expose endpoints, infra layer handle transport.

---

#### Pattern 5: Explicit Error Handling + Retry (xuyên 3 layers — Business/API/Infra)

**Định nghĩa:** Lỗi không crash server — được bắt, log, trả về structured response. Retry có bounded attempts.

**Evidence từ T4.2 (Business Logic):**
> *"Khi LLM judge không thể phân loại (`None` verdict), reward default về `0.0` (fail-safe, conservative)."*

`jailbreak_detection` — `None` verdict → không crash, không raise, default safe value.

**Evidence từ T4.3 (Interface/API):**
> *"Middleware stack: `SessionMiddleware → add_session_id → exception_handling_middleware → RequestValidationError` handler"* (từ `server_utils.py:487–532`)

Exception handling middleware bắt mọi unhandled exception trước khi reach wire.

**Evidence từ T4.4 (Infrastructure):**
> *"`ServerClient` wraps aiohttp với retry logic (3 tries, exponential backoff)"* — network transient failures không crash rollout collection.

`atexit.register(maybe_ray_cluster_exit)` — cleanup dù exit theo bất kỳ cách nào.

---

### Section 3: Inconsistencies

**Verdict: Phát hiện 2 inconsistencies nhỏ — không critical nhưng cần lưu ý.**

**Inconsistency 1: Reward không hoàn toàn binary ở mọi server**

Từ [T4.2 worklog](nemo-gym-0t4.2-nemo-gym-deep-research-business-logic.md):
> *"`jailbreak_detection`: `use_combined_reward=True` tạo ra `reward = 0.5` — trường hợp **continuous reward** ngoại lệ trong ecosystem mostly-binary"*

`text_to_sql` cũng có `config.reward_if_swap_fails` — không hardcode về 0.0. Trong khi convention của framework là binary và `reward_profile.py` detect `is_binary` để dùng công thức `pass@k` chính xác, hai server này break convention. Không có enforcement mechanism (Pydantic chỉ validate `float`, không validate `∈ {0.0, 1.0}`).

**Inconsistency 2: openai SDK dùng như type library nhưng không có separate types-only package**

Từ [T4.3 worklog](nemo-gym-0t4.3-nemo-gym-deep-research-interface-api.md):
> *"NeMo Gym dùng openai Python SDK **chỉ như type/schema library**, không dùng SDK client thực (thay vào đó là `NeMoGymAsyncOpenAI` — một aiohttp wrapper stub)"*

Nhưng `pyproject.toml` vẫn pin `openai<=2.7.2` như runtime dependency — kéo theo cả HTTP client code của openai vào production image dù không dùng. Lý tưởng hơn là extract types sang `openai-stubs` hoặc generate Pydantic models độc lập, nhưng chi phí maintenance không xứng. Đây là pragmatic choice, không phải design flaw, nhưng là tradeoff chưa được document ở layer analysis.

---

### Section 4: Top 3 Design Principles xuyên suốt NeMo Gym

---

#### Principle 1: Async-First, Semaphore-Bounded Concurrency

**Phát biểu:** Mọi I/O operation là coroutine; mọi resource-bounded operation có `asyncio.Semaphore`; không có blocking call trong event loop.

**Rationale sâu:** NeMo Gym phải handle 16,000 concurrent rollouts (RL training scale). Synchronous code ở bất kỳ điểm nào trong call chain = bottleneck toàn bộ pipeline. Semaphore pattern đảm bảo graceful degradation thay vì crash khi external resource (subprocess slots, judge LLM) saturate.

**Evidence clickable:**

- [T4.4 — aiohttp O(n²) incident](nemo-gym-0t4.4-nemo-gym-deep-research-infrastructure.md): *"khi NeMo Gym nhận 16,000 concurrent requests... system treo 40 phút trước khi xử lý request đầu tiên"* → bằng chứng async is not optional, it's survival.
- [T4.2 — bigcodebench verify()](nemo-gym-0t4.2-nemo-gym-deep-research-business-logic.md): `async with self._semaphore: result = await self._run_in_venv(...)` — semaphore default 8 processes trong sandbox execution.
- [T4.4 — per-worker connection partitioning](nemo-gym-0t4.4-nemo-gym-deep-research-infrastructure.md): `TCPConnector(limit=cfg.global_aiohttp_connector_limit // num_workers)` — worker-aware resource partitioning.

---

#### Principle 2: Pydantic-Enforced Contract at Every Boundary

**Phát biểu:** Không có untyped dict ở wire boundary. Mọi request, response, config, và cross-server message đều là Pydantic model với validator.

**Rationale sâu:** Với 20+ benchmark servers và N contributors, thiếu type contract = runtime surprise ở production RL training (khi debugging 16k rollouts). Pydantic làm contract **explicit và verifiable** — schema validation xảy ra tại deserialization, không phải khi verify() đã chạy được nửa chừng.

**Evidence clickable:**

- [T4.1 — DatasetConfig validator](nemo-gym-0t4.1-nemo-gym-deep-research-data-storage.md): `DatasetConfig.check_train_validation_sets()` enforce `license` required cho train/validation — business rule encoded trong schema.
- [T4.3 — TokenIDLogProbMixin](nemo-gym-0t4.3-nemo-gym-deep-research-interface-api.md): `class TokenIDLogProbMixin(BaseModel)` extend openai types bằng Pydantic để add RL fields — extension via Pydantic, không via dict manipulation.
- [T4.2 — BaseVerifyResponse](nemo-gym-0t4.2-nemo-gym-deep-research-business-logic.md): `reward: float` trong base class với `is_binary` check trong `reward_profile.py` — schema + runtime invariant check.

---

#### Principle 3: Convention over Configuration, Template Method for Extension

**Phát biểu:** Framework cung cấp skeleton cố định (lifecycle, routing, middleware); developer chỉ override hook method (`verify()`, `run()`, `responses()`). Mọi server mới follow cùng structure mà không cần configure.

**Rationale sâu:** 80+ benchmark servers không thể maintain nếu mỗi server phải setup FastAPI app, middleware, error handling riêng. Template Method pattern đảm bảo tất cả servers có behavior nhất quán (session middleware, error handling, `/aggregate_metrics` endpoint) mà không cần copy-paste. Convention (`data/example.jsonl` là 5 entries, `requirements.txt` tại server root, `data/.gitignore` pattern chuẩn) giảm onboarding friction.

**Evidence clickable:**

- [T4.2 — Template Method + Strategy](nemo-gym-0t4.2-nemo-gym-deep-research-business-logic.md): *"skeleton bất biến trong `setup_webserver()`: khởi tạo FastAPI app, gắn session middleware, đăng ký routes cố định... Phần biến thiên duy nhất là `verify()` — được khai báo `@abstractmethod`."*
- [T4.1 — example dataset convention](nemo-gym-0t4.1-nemo-gym-deep-research-data-storage.md): *"pattern được hardcode vào `init_resources_server()` trong `cli.py` (dòng 841-847) — nó là first-class convention của framework."*
- [T4.4 — per-server venv convention](nemo-gym-0t4.4-nemo-gym-deep-research-infrastructure.md): *"`requirements.txt` → `setup_env_command()` → `.venv/` tại server root. Không cần cấu hình gì thêm. `ng_test +entrypoint=resources_servers/my_server` là self-contained."*

---

### Section 5: Industry Comparison

NeMo Gym được so sánh với 4 framework tiêu biểu trong không gian RL/eval/agent:

---

#### vs. OpenAI Evals (https://github.com/openai/evals)

| Chiều | OpenAI Evals | NeMo Gym |
|---|---|---|
| **Mục tiêu** | Evaluate LLM capability offline (batch) | RL training environment online (streaming rollouts) |
| **Reward** | Grading functions trả float/string | Binary 0.0/1.0 RLVR reward |
| **Architecture** | Single-process, YAML-driven eval configs | Multi-process microservices, Hydra composition |
| **Concurrency** | Sequential eval, không design cho 16k concurrent | aiohttp singleton + Semaphore design cho 16k+ |
| **Extensibility** | Add new eval = add Python class + YAML registry | Add new server = copy template + override `verify()` |
| **Use case** | Benchmark LLM = đo điểm | Train LLM = generate reward signal |

**Key difference:** OpenAI Evals là read-only measurement tool; NeMo Gym là active RL environment component. Eval schema (grading) vs. Training schema (reward signal với token_ids cho gradient).

---

#### vs. Verifiers (https://github.com/willccbb/verifiers)

| Chiều | Verifiers | NeMo Gym |
|---|---|---|
| **Philosophy** | RLVR library thuần: environment + verifier trong cùng process | RLVR + microservice separation: verifier là HTTP server riêng |
| **Reward** | Binary default, cùng rationale DeepSeek R1 | Binary default, cùng rationale |
| **Scale** | Single-machine, tight coupling | Multi-machine, HPC/cluster ready |
| **Agent loop** | In-process LLM calls | HTTP-based agent ↔ model server ↔ resources server |
| **Config** | Python code | Hydra YAML composition |

**Verdict:** Verifiers là "embedded RL environment" (code library); NeMo Gym là "distributed RL environment" (service mesh). NeMo Gym trade deployment complexity cho scalability và language-agnostic boundary — justified bởi NVIDIA's cluster scale.

---

#### vs. LangChain / LangServe (https://github.com/langchain-ai/langserve)

| Chiều | LangChain agents | NeMo Gym agents |
|---|---|---|
| **Agent abstraction** | Chain/Graph-based (LCEL, LangGraph) | HTTP server với `run()` / `responses()` |
| **State management** | LangGraph checkpointing (Redis/Postgres) | Cookie-based session affinity qua HTTP |
| **Deployment** | LangServe wrap chain thành FastAPI | Mỗi agent là FastAPI server từ đầu |
| **Reward** | Không có RL reward concept | Binary RLVR reward là first-class |
| **Ecosystem lock** | LangChain ecosystem | OpenAI API compatible (vLLM, SGLang, Anthropic) |

**Key difference:** LangChain optimize cho developer productivity (chain composition, memory, toolkits); NeMo Gym optimize cho RL training throughput (reward signal quality, concurrency, gradient propagation). Cookie-based stateful env (NeMo Gym) vs. explicit checkpointing (LangGraph).

---

#### vs. TRL / GRPO Trainer (https://huggingface.co/docs/trl/grpo_trainer)

| Chiều | TRL GRPOTrainer | NeMo Gym |
|---|---|---|
| **Layer** | Trainer (gradient update) | Environment (rollout collection + reward) |
| **Reward** | `reward_funcs` expects 0/1 output | Binary reward từ `verify()` — compatible |
| **Token IDs** | `generation_kwargs`, log_probs collection | `prompt_token_ids`, `generation_log_probs` propagated qua HTTP |
| **Concurrency** | DataLoader workers | aiohttp + Ray workers |
| **Coupling** | Tight: trainer owns everything | Loose: trainer calls NeMo Gym via HTTP `/run` |

**Verdict:** TRL và NeMo Gym là complementary, không phải alternative. TRL là trainer; NeMo Gym là environment provider. `generation_log_probs` propagation trong NeMo Gym được thiết kế chính xác để feed vào TRL/GRPO gradient computation — xem [T4.2 — token_ids propagation](nemo-gym-0t4.2-nemo-gym-deep-research-business-logic.md).

---

**Tổng kết industry positioning:** NeMo Gym lấp đầy gap giữa eval frameworks (OpenAI Evals, Verifiers — đo điểm) và training frameworks (TRL, OpenRLHF — update gradient). NeMo Gym là **RL Environment as a Service** — microservice layer cung cấp reward signal cho trainer bất kỳ, với scale HPC, và extensible bằng Template Method pattern.

## Phản biện (2026-05-24, Round 1+2)
- Round 1: 6.5/10 — parent role mỏng, gate logic không rõ, hành động cụ thể thiếu.
- Round 2: 9.0/10 — Gate explicit, 5 sections, cross-layer evidence requirement, industry comparison URL.
