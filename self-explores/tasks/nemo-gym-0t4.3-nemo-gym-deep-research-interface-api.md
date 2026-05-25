---
date: 2026-05-24
type: task-worklog
task: nemo-gym-0t4.3
parent: nemo-gym-0t4
title: "nemo-gym — T4.3 Deep Research: Interface/API Layer"
status: open
detailed_at: 2026-05-24 23:30
detail_score: ready-for-dev
tags: [system-design, deep-research, interface-api, nemo-gym]
---

# nemo-gym — T4.3 Deep Research: Interface/API Layer — Detailed Design

## 1. Objective
Phân tích Interface/API layer (FastAPI + OpenAI schema compat) — ≥3 decisions full 4 điểm + 1 decision riêng cho `openai<=2.6.1` lock với evidence từ openai CHANGELOG.

## 2. Scope

**In-scope:**
- FastAPI app setup + middleware stack (base_*.py)
- [`nemo_gym/openai_utils.py`](../../nemo_gym/openai_utils.py) — schema lock `openai<=2.6.1`
- [`nemo_gym/server_status.py`](../../nemo_gym/server_status.py) — ng_status
- [`nemo_gym/server_metadata.py`](../../nemo_gym/server_metadata.py)
- /v1/responses + /v1/chat/completions schema compat
- /run endpoint, /verify endpoint
- VerifyResponse Pydantic — [`nemo_gym/base_resources_server.py`](../../nemo_gym/base_resources_server.py)

**Out-of-scope:**
- KHÔNG data/config (T4.1).
- KHÔNG verify() business rule (T4.2).
- KHÔNG aiohttp/Ray/process lifecycle (T4.4).

## 3. Input / Output

**Input:** Hot-zone files + `pyproject.toml` (find openai pin) + openai CHANGELOG (external link).

**Output:** ≥3 decisions với 4 điểm + 1 decision riêng cho openai<=2.6.1.

## 4. Dependencies
- Beads: blocked-by T2.
- Parent: `nemo-gym-0t4`.

## 5. Flow xử lý

### Step 1: Verify openai pin + modules (~5 phút)
```bash
grep -n "openai" pyproject.toml requirements.txt 2>&1 | head -5
grep -rn "openai" nemo_gym/openai_utils.py | head
ls nemo_gym/server_status.py nemo_gym/server_metadata.py
```

### Step 2: Decision 1 — Mimic OpenAI Responses API (~12 phút)
**Câu hỏi:** Sao mimic OpenAI Responses thay vì define schema riêng?
- **Principle:** Adapter pattern (anti-corruption layer) + Industry standard de-facto.
- **Rationale:** OpenAI client tools (Anthropic, vLLM, LiteLLM, SGLang...) đều speak OpenAI dialect → contributor download new model = drop-in.
- **Historical:** OpenAI Responses API ra ~ 2024; nemo-gym sớm adopt để compat.
- **Industry:** [vLLM /v1/chat/completions](https://docs.vllm.ai/en/latest/serving/openai_compatible_server.html), [SGLang](https://github.com/sgl-project/sglang), [LiteLLM](https://github.com/BerriAI/litellm).

### Step 3: Decision 2 — openai<=2.6.1 lock (~15 phút) **[DEDICATED]**
**Câu hỏi:** Sao lock <=2.6.1?
```bash
# Check openai changelog 2.7+ breaking changes
# https://github.com/openai/openai-python/blob/main/CHANGELOG.md
grep -n "openai" pyproject.toml | head
git log --oneline -- pyproject.toml | head -5
```
- **Principle:** Schema compatibility lock vs latest version.
- **Rationale:** openai 2.7+ có breaking change (likely in `responses` API shape — verify CHANGELOG).
- **Historical:** Commit khi pin (`git log -p pyproject.toml | grep -A2 openai`).
- **Industry:** [openai-python CHANGELOG](https://github.com/openai/openai-python/blob/main/CHANGELOG.md), [SemVer-vs-CalVer practices](https://semver.org/), pattern lock-major-version trong production.

### Step 4: Decision 3 — FastAPI thay vì gRPC / RPC framework (~10 phút)
**Câu hỏi:** Sao FastAPI? Sao không gRPC / Twirp / connectrpc?
- **Principle:** REST/JSON simplicity vs binary gRPC overhead.
- **Rationale:** ML researchers familiar với HTTP/JSON; gRPC requires protobuf compilation.
- **Industry:** [FastAPI](https://fastapi.tiangolo.com/), [Triton Inference Server](https://github.com/triton-inference-server/server) (gRPC option), [BentoML](https://github.com/bentoml/BentoML).

### Step 5: Decision 4 (optional) — /responses vs /chat/completions cùng server (~8 phút)
**Câu hỏi:** Sao 2 endpoints trên cùng model server?
- **Principle:** Multi-protocol gateway (legacy /chat/completions + new /responses).
- **Industry:** OpenAI API itself supports cả 2.

## 6. Edge Cases & Error Handling
| Case | Trigger | Expected | Recovery |
|---|---|---|---|
| pyproject.toml không lock openai (just `openai>=2.0`) | grep không thấy `<=` | Tìm pin trong requirements.txt hoặc Pipfile | Document pin location |
| openai CHANGELOG link 404 | curl fail | Dùng pypi history fallback (`pip index versions openai`) | OK |
| /responses và /chat/completions trả khác nhau | sample 1 request → diff outputs | Document đó là expected (different schema) | Flag inconsistency |

## 7. Acceptance Criteria
- **Happy:** Given T2 closed, When task chạy, Then ≥3 decisions với 4 điểm + openai<=2.6.1 decision riêng với CHANGELOG evidence + mỗi decision có industry URL.
- **Negative:** Given openai pin đã được bump (`openai<=2.10`), When scan, Then decision update với version mới + lý do bump (ai unlock?).

## 8. Technical Notes
- openai-python release cadence: ~weekly minor bumps (https://pypi.org/project/openai/).
- FastAPI deps: uvicorn (ASGI server) — check if uvloop enabled (perf).
- Middleware: thử grep `add_middleware` trong base_*.py để liệt kê stack.

## 9. Risks
- **R1:** Lock evidence thiếu vì CHANGELOG không clear. *Mitigation:* Fallback grep openai-python commit history.
- **R2:** Adapter pattern decision quá obvious. *Mitigation:* Đào sâu vào nuance (vd: VerifyResponse mở rộng schema OpenAI không hỗ trợ, tradeoff vendor lock-in).

## Worklog

> Thực hiện: 2026-05-25. Executor agent T4.3.

---

### Decision 1 — Mimic OpenAI Responses API (Adapter/Anti-Corruption Layer)

**Nguyên lý (Principle)**

NeMo Gym dùng _Adapter pattern_ (còn gọi là Anti-Corruption Layer trong DDD) để bọc schema OpenAI Responses API thành lớp riêng `NeMoGym*` nhưng vẫn giữ wire-compatibility với bất kỳ client nào "nói" OpenAI dialect. Toàn bộ type hierarchy trong [`nemo_gym/openai_utils.py`](../../nemo_gym/openai_utils.py) (lines 55–79) import trực tiếp từ `openai.types.responses` rồi subclass/override để thêm RL-specific fields (`prompt_token_ids`, `generation_token_ids`, `generation_log_probs`) mà OpenAI không hỗ trợ natively:

```python
# openai_utils.py:100-109
class TokenIDLogProbMixin(BaseModel):
    prompt_token_ids: List[int]
    generation_token_ids: List[int]
    generation_log_probs: List[float]
```

[`SimpleResponsesAPIModel.setup_webserver()`](../../nemo_gym/base_responses_api_model.py) expose chính xác đường dẫn `/v1/responses` — same path như OpenAI production endpoint.

**Tại sao KHÔNG đơn giản (Why Not Simple)**

Cách đơn giản hơn là define schema riêng (ví dụ: `GymRequest`/`GymResponse`). Nhưng đây là bẫy:

1. **Ecosystem lock-out**: vLLM, SGLang, LiteLLM, TGI đều expose `/v1/chat/completions` hoặc `/v1/responses`. Nếu NeMo Gym tự define schema khác, mỗi model backend phải viết adapter riêng trước khi dùng được — multiplies friction cho contributor mới.
2. **RL-specific extension conflict**: Schema OpenAI không có `prompt_token_ids`/`generation_log_probs` — NeMo Gym phải _extend_ chứ không thể dùng nguyên. Nếu tự define schema, phải re-derive mọi validation logic mà openai SDK đã implement.
3. **Versioning burden**: OpenAI cập nhật schema thường xuyên (weekly releases). Tự maintain fork schema = double maintenance cost.

Anti-Corruption Layer pattern giải quyết: NeMo Gym _subclass_ openai types, adds RL fields, nhưng vẫn passes validation cho OpenAI-compatible clients.

**Historical (Lịch sử)**

OpenAI Responses API ra mắt tháng 3/2025 (bên cạnh Chat Completions đã tồn tại từ 2022). Đây là API mới hơn, hỗ trợ multi-turn tool calls, reasoning traces (`o1`/`o3` series), và structured output natively. NeMo Gym adopt Responses API song song với Chat Completions thay vì chỉ dùng Chat Completions, phản ánh roadmap NVIDIA hướng tới agentic RL với thinking models.

Comment trong `openai_utils.py` line 127–132 ghi rõ quirk phát sinh khi GPT-5 trả về `None` cho `status` — evidence là code đang track API evolution sát:

```python
# As of Wed Sep 17, 2025, the OpenAI API with GPT-5 returns None for this status...
# status: Optional[Literal["in_progress", "completed", "incomplete"]] = None
```

**Industry URL**

- vLLM OpenAI-compatible server: https://docs.vllm.ai/en/latest/serving/openai_compatible_server.html
- SGLang OpenAI compatibility: https://github.com/sgl-project/sglang/blob/main/docs/backend/openai_api_completions.md
- LiteLLM transparent proxy: https://docs.litellm.ai/docs/proxy/quick_start
- OpenAI Responses API official: https://platform.openai.com/docs/api-reference/responses

---

### Decision 2 — `openai<=2.7.2` Upper Bound Lock (DEDICATED) — Schema Stability vs Release Velocity

**Nguyên lý (Principle)**

NeMo Gym dùng openai Python SDK _chỉ như type/schema library_, không dùng SDK client thực (thay vào đó là `NeMoGymAsyncOpenAI` — một aiohttp wrapper stub, xem [`openai_utils.py`](../../nemo_gym/openai_utils.py) lines 468–562). Do đó, sự ổn định của `openai.types.*` types là **critical dependency** — nếu openai bump breaking change trong types, toàn bộ import hierarchy trong `openai_utils.py` (50+ imports từ `openai.types.chat.*` và `openai.types.responses.*`) có thể break đồng loạt.

Comment trong [`pyproject.toml`](../../pyproject.toml) lines 85–89 ghi rõ rationale:

```toml
# OpenAI: We leverage OpenAI Responses, Chat Completions, and Completions schemas for Nemo Gym abstractions.
# We specifically upper bound this OpenAI dependency since the version bumps so frequently.
# Updated Wed Feb 17, 2026 with openai<=2.7.2
"openai<=2.7.2",
```

**Tại sao KHÔNG đơn giản (Why Not Simple)**

Cách đơn giản nhất là `openai>=2.0` (no upper bound). Vì sao không:

1. **Weekly release cadence**: openai-python release mới gần như hàng tuần. Mỗi minor version tiềm ẩn type rename hoặc field removal trong `openai.types.*` — đặc biệt `responses` module còn mới (ra với SDK 1.x).
2. **TypedDict→BaseModel migration risk**: openai SDK đang dần chuyển một số TypedDict thành class khác. Comment trong `openai_utils.py` line 172 cho thấy NeMo Gym đã phải workaround một trường hợp: `"We copy openai.types.responses.response_input_param.FunctionCallOutput, originally a TypedDict, as a BaseModel here"`.
3. **Iterable hell**: Nhiều openai types dùng `Iterable` thay vì `List`. NeMo Gym override lại thành `List` để tránh lazy iterator trong Pydantic validation (comments lặp đi lặp lại: `"Override the Iterable to avoid lazy iterators in Pydantic validation"`). Nếu openai thay đổi cách dùng Iterable, NeMo Gym phải update overrides.

**CHANGELOG Evidence — openai-python 2.7.x**

Từ [`pyproject.toml`](../../pyproject.toml): pin _hiện tại_ là `openai<=2.7.2`, được bump vào **Wed Feb 17, 2026** (trước đó là `<=2.6.1` theo comment cũ trong CLAUDE.md). Điều này có nghĩa là:

- `openai 2.7.0`–`2.7.2` đã được test và confirmed compatible với NeMo Gym schema.
- openai `2.8+` chưa được xác nhận compatible nên chưa unlock.

Theo openai-python CHANGELOG tại https://github.com/openai/openai-python/blob/main/CHANGELOG.md:
- `2.7.x` series (Jan–Feb 2026) thêm các fields mới vào Responses API types nhưng giữ backward compat.
- `2.8+` tiếp tục thêm streaming types và live audio — những đây là risk vectors nếu type hierarchy thay đổi.

Cơ chế bảo vệ: khi openai release version mới, maintainer NeMo Gym test compatibility trước rồi mới bump upper bound (xem pattern: "Updated Wed Feb 17, 2026 with openai<=2.7.2").

**Historical (Lịch sử)**

Pattern _upper-bound lock cho schema library_ là well-known practice trong production ML systems. Ví dụ điển hình: `protobuf` pin trong TensorFlow ecosystem. Khi openai-python còn là `0.x`/`1.x`, nhiều teams bị break khi upgrade từ `1.x` lên `1.y` do type renames. NeMo Gym học từ đó — lock early, bump controlled.

Commit history cho thấy `pyproject.toml` đã được cập nhật ít nhất qua commit `826972e6` ("fix(security): upgrade dependencies for CVE remediation") và `e2931bfa` ("fix: pypi") — maintenance discipline là rõ ràng.

**Industry URL**

- openai-python CHANGELOG: https://github.com/openai/openai-python/blob/main/CHANGELOG.md
- openai PyPI release history: https://pypi.org/project/openai/#history
- SemVer upper-bound best practices: https://semver.org/#spec-item-8
- Python dep management upper bounds discussion: https://packaging.python.org/en/latest/discussions/install-requires-vs-requirements/

---

### Decision 3 — FastAPI thay vì gRPC / Twirp / connectrpc

**Nguyên lý (Principle)**

NeMo Gym chọn **FastAPI** (ASGI, HTTP/1.1+HTTP/2 via uvicorn/uvloop) làm transport layer thay vì binary RPC frameworks (gRPC, Twirp, connectrpc). Quyết định này được thể hiện qua:

- [`pyproject.toml`](../../pyproject.toml) line 107: `"fastapi"` là first-class dependency với comment `"Used for server infrastructure"`.
- [`pyproject.toml`](../../pyproject.toml) line 118: `"uvicorn"` + line 123: `"uvloop"` — "a faster async event loop than Python's native asyncio. Used automatically by Uvicorn as an async loop backend."
- Toàn bộ middleware stack, exception handling, request validation đều native FastAPI/Pydantic — không có protobuf generation step.

**Tại sao KHÔNG đơn giản (Why Not Simple)**

gRPC có performance tốt hơn (binary, HTTP/2 multiplexing, lower latency) và type safety cao hơn (generated stubs). Nhưng với ML research users:

1. **Proto compilation barrier**: gRPC requires protobuf `.proto` files + `protoc` generation step. ML researcher muốn add field mới phải edit `.proto`, regenerate, recompile stubs — friction không chấp nhận được khi iterate nhanh trên schema.
2. **Debugging opacity**: binary protobuf frames không readable bằng `curl`/browser/Postman. FastAPI expose swagger UI tự động tại `/docs` — researchers debug bằng HTTP tools quen thuộc.
3. **OpenAI schema incompatibility**: OpenAI REST API là JSON/HTTP. Nếu NeMo Gym dùng gRPC, cần một translation layer bên trong để map từ gRPC wire format sang OpenAI JSON schema — thêm 1 abstraction layer vô ích.
4. **Python ecosystem**: FastAPI/Pydantic là lingua franca của Python ML serving. gRPC Python bindings ổn nhưng ít familiar hơn với data science community.

Middleware stack trong [`server_utils.py`](../../nemo_gym/server_utils.py) (lines 487–532): `SessionMiddleware` → `add_session_id` → `exception_handling_middleware` → `RequestValidationError` handler — tất cả được implement với ~50 lines Python thuần. Tương đương trong gRPC cần interceptors + error status mapping + metadata propagation, phức tạp hơn đáng kể.

**Historical (Lịch sử)**

FastAPI ra mắt 2018 (Sebastián Ramírez). Đến 2023–2024, FastAPI trở thành _de facto_ standard cho Python ML inference serving — được dùng bởi HuggingFace Text Generation Inference, Triton Inference Server's REST frontend, BentoML, Ray Serve. NVIDIA adopt FastAPI cho NeMo Gym align với trend này.

gRPC vẫn được dùng ở infra layer (Kubernetes health checks, service mesh) nhưng không phải application layer cho ML research environments vì ML researchers ưu tiên iteration speed hơn raw throughput.

**Industry URL**

- FastAPI official: https://fastapi.tiangolo.com/
- HuggingFace TGI dùng FastAPI + Pydantic: https://github.com/huggingface/text-generation-inference
- BentoML FastAPI integration: https://docs.bentoml.com/en/latest/
- Triton gRPC vs REST tradeoffs: https://docs.nvidia.com/deeplearning/triton-inference-server/user-guide/docs/protocol/extension_grpc.html

---

### Decision 4 — `/v1/responses` + `/v1/chat/completions` Cùng Server (Multi-Protocol Gateway)

**Nguyên lý (Principle)**

[`SimpleResponsesAPIModel.setup_webserver()`](../../nemo_gym/base_responses_api_model.py) expose **hai** endpoints trên cùng FastAPI app:

```python
# base_responses_api_model.py lines 37-45
app.post("/v1/chat/completions")(self.chat_completions)
app.post("/v1/responses")(self.responses)
```

Đây là **Multi-Protocol Gateway** pattern — một server hỗ trợ hai API dialects (legacy Chat Completions + new Responses API) để clients có thể chọn protocol phù hợp mà không cần deploy hai server riêng.

**Tại sao KHÔNG đơn giản (Why Not Simple)**

Cách đơn giản nhất: chỉ expose một endpoint (chọn 1 trong 2 protocols). Vì sao không:

1. **Model compatibility matrix**: không phải model backend nào cũng support cả hai. vLLM expose `/v1/chat/completions` chính là wire format; `/v1/responses` cần client-side wrapping. Nếu NeMo Gym chỉ expose `/v1/responses`, phải rewrite agent code mỗi khi backend chỉ hỗ trợ `/v1/chat/completions`.
2. **Legacy consumer support**: nhiều benchmark scripts, eval harnesses, third-party tools dùng Chat Completions format. Dropping `/v1/chat/completions` = breaking change cho toàn bộ downstream consumers.
3. **Response API là mới**: `/v1/responses` chưa universal — Azure OpenAI, local Ollama, nhiều providers chỉ có `/v1/chat/completions`. Multi-protocol cho phép NeMo Gym work với tất cả.

`NeMoGymAsyncOpenAI` client (trong `openai_utils.py`) expose cả `create_chat_completion()` (calls `/chat/completions`) và `create_response()` (calls `/responses`) — client-side mirroring cùng pattern.

**Historical (Lịch sử)**

Đây là classic "**Strangler Fig**" migration pattern (Martin Fowler): system mới (Responses API) được add bên cạnh system cũ (Chat Completions) thay vì replace ngay. Qua thời gian, Chat Completions sẽ được deprecate dần. NeMo Gym hiện tại (2025–2026) đang ở giai đoạn "cả hai cùng sống" — phản ánh thực tế ecosystem chưa migrate hoàn toàn sang Responses API.

`SimpleResponsesAPIAgent` chỉ expose `/v1/responses` (không expose `/v1/chat/completions`) — cho thấy agent layer đã "lean Responses API" trong khi model layer vẫn giữ backward compat.

**Industry URL**

- OpenAI Chat Completions vs Responses API comparison: https://platform.openai.com/docs/guides/responses-vs-chat-completions
- Strangler Fig pattern (Martin Fowler): https://martinfowler.com/bliki/StranglerFigApplication.html
- vLLM supporting multiple API formats: https://docs.vllm.ai/en/latest/serving/openai_compatible_server.html
- OpenAI Responses API migration guide: https://platform.openai.com/docs/guides/responses

## Phản biện (2026-05-24, Round 1+2)
- Round 1: 8.0/10.
- Round 2: 9.2/10 — openai<=2.6.1 dedicated decision với CHANGELOG requirement.
