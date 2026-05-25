---
date: 2026-05-24
type: task-worklog
task: nemo-gym-0t4.2
parent: nemo-gym-0t4
title: "nemo-gym — T4.2 Deep Research: Business Logic Layer"
status: open
detailed_at: 2026-05-24 23:30
detail_score: ready-for-dev
tags: [system-design, deep-research, business-logic, nemo-gym]
---

# nemo-gym — T4.2 Deep Research: Business Logic Layer — Detailed Design

## 1. Objective
Phân tích Business Logic layer (verify + run loops + reward) — ≥3 design decisions full 4 điểm, sample ≥3 resources_servers different domains.

## 2. Scope

**In-scope:**
- [`nemo_gym/base_resources_server.py`](../../nemo_gym/base_resources_server.py) — abstract verify() + VerifyResponse
- [`nemo_gym/base_responses_api_agent.py`](../../nemo_gym/base_responses_api_agent.py) — run() / responses() lifecycle
- [`nemo_gym/base_responses_api_model.py`](../../nemo_gym/base_responses_api_model.py)
- [`nemo_gym/reward_profile.py`](../../nemo_gym/reward_profile.py)
- [`nemo_gym/rollout_collection.py`](../../nemo_gym/rollout_collection.py)
- [`responses_api_agents/simple_agent/app.py`](../../responses_api_agents/simple_agent/app.py)
- Multi-turn agents: proof_refinement_agent, hermes_agent, langgraph_agent
- 3-5 resources_servers/*/app.py different domains (vd: example_single_tool_call, bigcodebench, browsecomp_advanced_harness)

**Out-of-scope:**
- KHÔNG đụng data/config (T4.1).
- KHÔNG đụng FastAPI endpoint definitions (T4.3).
- KHÔNG đụng aiohttp/Ray (T4.4).

## 3. Input / Output

**Input:** Hot-zone files + ≥3 sample resources_servers/*/app.py.

**Output:** ≥3 decisions với 4 điểm + 1 decision riêng cho reward binary choice.

## 4. Dependencies
- Beads: blocked-by T2 (`nemo-gym-ir8`).
- Parent: `nemo-gym-0t4`.

## 5. Flow xử lý

### Step 1: Verify modules (~3 phút)
```bash
ls nemo_gym/base_*.py nemo_gym/reward_profile.py nemo_gym/rollout_collection.py
ls responses_api_agents/{simple_agent,proof_refinement_agent,hermes_agent,langgraph_agent}/app.py 2>&1
ls resources_servers/{example_single_tool_call,bigcodebench,browsecomp_advanced_harness}/app.py 2>&1
```

### Step 2: Decision 1 — Template Method + Strategy (~12 phút)
**Câu hỏi:** Sao base_*.py là Template Method (skeleton fixed) + Strategy (verify() per-server)?
```bash
grep -n "abstractmethod\|def verify\|class.*Resources\|class.*Agent\|class.*Model" nemo_gym/base_*.py | head
```
- **Principle:** Template Method + Strategy.
- **Rationale:** Mọi resources_server cần lifecycle giống nhau (init → route → verify → response), chỉ verify() khác → tách.
- **Historical:** `git log -p nemo_gym/base_resources_server.py | head -200` tìm initial commit.
- **Industry:** [Django REST GenericAPIView](https://www.django-rest-framework.org/api-guide/generic-views/), [FastAPI APIRouter pattern](https://fastapi.tiangolo.com/tutorial/bigger-applications/).

### Step 3: Decision 2 — Agent as HTTP server (~12 phút)
**Câu hỏi:** Sao agent là HTTP server riêng thay vì in-process Python class?
```bash
ls responses_api_agents/  # confirm 1 dir = 1 deployable
grep -n "FastAPI\|app = FastAPI\|@app.post" responses_api_agents/simple_agent/app.py | head
```
- **Principle:** Service-Oriented (microservice) + Language-agnostic boundary.
- **Rationale:** Tradeoff: deployment cost vs isolation + scaling + multi-tenancy.
- **Historical:** When mono → multi-service?
- **Industry:** [OpenAI Agents SDK](https://github.com/openai/openai-agents-python), [LangChain LangServe](https://github.com/langchain-ai/langserve), [TGI](https://github.com/huggingface/text-generation-inference).

### Step 4: Decision 3 — Reward binary 0.0/1.0 (~12 phút)
**Câu hỏi:** Sao reward binary thay vì float [0,1] continuous?
```bash
grep -n "reward\|0\.0\|1\.0\|VerifyResponse" nemo_gym/base_resources_server.py nemo_gym/reward_profile.py | head -20
```
- **Principle:** RLVR (RL with Verifiable Rewards) design — verifiable means deterministic pass/fail.
- **Rationale:** Binary signal mạnh, dễ aggregate (pass@k = avg). Continuous reward dễ bị reward hacking.
- **Historical:** OpenAI o1-preview launch (2024-09) → wave of RLVR adoption.
- **Industry:** [Verifiers framework](https://github.com/willccbb/verifiers), [TRL GRPO](https://huggingface.co/docs/trl/grpo_trainer), [DeepSeek R1 paper](https://arxiv.org/abs/2501.12948).

### Step 5: Decision 4 (optional) — Cookies + token_ids propagation (~10 phút)
**Câu hỏi:** Sao cookies/session ID + token_ids forward agent → model → resources?
```bash
grep -n "cookies\|token_ids\|prompt_token_ids\|generation_token_ids" responses_api_agents/proof_refinement_agent/app.py | head
```
- **Principle:** Stateful env via session affinity + RL gradient feed (token-level log_probs).
- **Industry:** [TRL token-level logging](https://github.com/huggingface/trl), [OpenRLHF](https://github.com/OpenLLMAI/OpenRLHF).

### Step 6: Sample ≥3 resources_servers verify() spectrum (~15 phút)
- `example_single_tool_call`: simplest baseline.
- `bigcodebench`: code execution + subprocess.
- `browsecomp_advanced_harness`: multi-turn web browsing.
Compare verify() signature + return shape.

## 6. Edge Cases & Error Handling
| Case | Trigger | Expected | Recovery |
|---|---|---|---|
| Resources_server không subclass BaseResourcesServer | scan thấy ad-hoc app.py | Note "Out-of-band server (legacy)" | Skip from sample |
| Reward float [0,1] phát hiện trong 1 server | grep `reward.*0\.[0-9]` ngoài 0.0/1.0 | Note exception | Document "Edge: continuous reward in {server}" |
| Multi-turn agent state lost giữa turn | log analysis | Document cookie/session affinity required | Reference proof_refinement_agent |

## 7. Acceptance Criteria
- **Happy:** Given T2 closed, When task chạy, Then ≥3 decisions với 4 điểm + reward binary có 1 decision riêng + sample ≥3 resources_servers + mỗi decision có industry URL.
- **Negative:** Given ít hơn 3 resources_servers có app.py runnable, When scan, Then expand scope tới 5 servers để đủ spectrum.

## 8. Technical Notes
- VerifyResponse Pydantic — base class, mỗi server có thể extend (subclass override).
- Cookies vs Authorization header: cookies dùng cho cross-server session (stateful env), header cho auth.
- token_ids = list[int] (Pydantic), match openai 2.x format.

## 9. Risks
- **R1:** "verify() spectrum" quá rộng → tốn thời gian sample. *Mitigation:* Strict 3 servers, không deep-dive.
- **R2:** Decision reward binary overlap với T4.1 (data schema). *Mitigation:* T4.1 = how data flows, T4.2 = why reward shape this way.

## Worklog

### Decision 1: Template Method + Strategy trong base classes

**File:** [`nemo_gym/base_resources_server.py`](../../nemo_gym/base_resources_server.py) · [`nemo_gym/base_responses_api_agent.py`](../../nemo_gym/base_responses_api_agent.py) · [`nemo_gym/base_responses_api_model.py`](../../nemo_gym/base_responses_api_model.py)

**1. Nguyên lý — Template Method + Strategy:**
Ba base class (`SimpleResourcesServer`, `SimpleResponsesAPIAgent`, `SimpleResponsesAPIModel`) định nghĩa một **skeleton bất biến** trong `setup_webserver()`: khởi tạo FastAPI app, gắn session middleware, đăng ký routes cố định (`/seed_session`, `/verify`, `/aggregate_metrics`). Phần biến thiên duy nhất là `verify()` (resources server) và `responses()` / `run()` (agent) — được khai báo `@abstractmethod`. Đây chính xác là **Template Method** (GOF): lớp cha kiểm soát flow, lớp con chỉ override hook.

Song song đó, mỗi resources server có thể inject **Strategy** riêng vào `verify()`: `BigCodeBenchResourcesServer` dùng subprocess + semaphore để chạy code; `TextToSqlResourcesServer` dùng LLM-as-judge; `JailbreakDetectionResourcesServer` dùng multi-verifier policy-aware flow; `example_single_tool_call` trả `reward=1.0` cứng. Cùng một interface `BaseVerifyRequest → BaseVerifyResponse`, logic hoàn toàn khác nhau.

**2. Tại sao KHÔNG đơn giản hơn (e.g., monkey-patching hoặc plain function)?**
- Nếu dùng **plain FastAPI function**: mỗi server phải tự lặp lại boilerplate `app = FastAPI()`, session middleware setup, error handling — ~30 dòng mỗi server × 80+ servers = ~2400 dòng duplicate.
- Nếu dùng **mixin/composition không có base class**: mất enforce contract — không ai đảm bảo mỗi server thực sự có `/verify` với signature đúng. Pydantic validation ở base class bị mất.
- Nếu dùng **monkey-patching hoặc decorator**: mất static type checking, IDE navigation, và khó test riêng từng server.
- Kết luận: Template Method là giải pháp tối thiểu đảm bảo **contract** (abstractmethod force implement) + **DRY** (lifecycle một lần) mà không over-engineer.

**3. Historical context:**
Template Method pattern được mô tả trong GOF (1994). Python hiện thực hóa nó qua `abc.abstractmethod` (PEP 3119, Python 3.0). Framework Django dùng chính xác pattern này từ version 1.x qua `View.as_view()` → `dispatch()` → `get()`/`post()`. DRF (Django REST Framework) kế thừa và mở rộng qua `GenericAPIView.perform_create()` / `perform_update()`. NeMo Gym đi theo cùng genealogy: skeleton cứng ở tầng base, extension point ở method leaf.

**4. Industry URL:**
- [Django REST Framework — GenericAPIView](https://www.django-rest-framework.org/api-guide/generic-views/) — `perform_create()`, `get_queryset()` là hook đúng Template Method style
- [FastAPI — Bigger Applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/) — Router pattern tương đương ở tầng framework
- [GOF Template Method (refactoring.guru)](https://refactoring.guru/design-patterns/template-method) — canonical description
- [Python abc module docs](https://docs.python.org/3/library/abc.html) — cơ chế `@abstractmethod` enforce contract

---

### Decision 2: Agent là HTTP server độc lập thay vì in-process class

**File:** [`responses_api_agents/simple_agent/app.py`](../../responses_api_agents/simple_agent/app.py) · [`responses_api_agents/proof_refinement_agent/app.py`](../../responses_api_agents/proof_refinement_agent/app.py)

**1. Nguyên lý — Service-Oriented Architecture (SOA / microservice boundary):**
Mỗi agent là một **process độc lập** chạy FastAPI server riêng với port riêng, được HeadServer quản lý lifecycle. Agent giao tiếp với model server và resources server qua **HTTP** (không phải function call trong cùng process). `SimpleAgent.responses()` POST tới `model_server.name + /v1/responses`; `SimpleAgent.run()` POST tới `resources_server.name + /verify`. Ranh giới là **mạng HTTP**, không phải Python import.

**2. Tại sao KHÔNG in-process (import trực tiếp)?**

| Tradeoff | In-process | HTTP microservice |
|---|---|---|
| **Scaling** | Không scale agent riêng | Scale agent × N, model × M độc lập |
| **Language boundary** | Phải cùng Python process | Agent có thể viết bất kỳ ngôn ngữ nào |
| **Fault isolation** | Crash agent → crash toàn bộ | Agent crash → resources server vẫn sống |
| **Versioning** | Deploy toàn bộ khi update 1 agent | Rolling deploy từng service |
| **Concurrency** | Shared GIL (Python) | Mỗi service có event loop riêng |
| **Testing** | Mock khó (deep dependency) | Mock bằng HTTP stub, contract testing |

Quan trọng nhất với NeMo Gym: **RL training cần chạy song song nhiều rollout**. Nếu in-process, 16k concurrent requests sẽ đụng GIL và shared state. HTTP boundary + aiohttp (connection pool) giải quyết vấn đề này — mỗi agent instance là stateless process có thể replicate.

**3. Historical context:**
SOA nổi lên từ Amazon (~2002, Jeff Bezos "API mandate"). Microservice pattern được Martin Fowler & James Lewis formalize (2014). Xu hướng ML serving: TGI (HuggingFace, 2022) dùng HTTP server cho inference; OpenAI Assistants API (2023) expose agent-like server qua REST; LangServe (2023) wrap LangChain chains thành FastAPI server. NeMo Gym hội tụ tất cả: dùng FastAPI + aiohttp để build ML agent microservices.

**4. Industry URL:**
- [OpenAI Agents SDK](https://github.com/openai/openai-agents-python) — agent-as-service concept, tool server pattern
- [LangChain LangServe](https://github.com/langchain-ai/langserve) — wrap LangChain Runnable thành FastAPI endpoint, đúng cùng pattern
- [HuggingFace TGI Architecture](https://huggingface.co/docs/text-generation-inference/architecture) — tách inference server khỏi orchestration
- [Martin Fowler — Microservices](https://martinfowler.com/articles/microservices.html) — bài viết gốc define microservice tradeoffs

---

### Decision 3 [DEDICATED]: Reward binary 0.0/1.0 thay vì continuous float [0,1]

**File:** [`nemo_gym/base_resources_server.py`](../../nemo_gym/base_resources_server.py) (line 46: `reward: float` trong `BaseVerifyResponse`) · [`nemo_gym/reward_profile.py`](../../nemo_gym/reward_profile.py) (line 379-386: `is_binary` branch trong `compute_pass_majority_metrics`)

**1. Nguyên lý — RLVR (RL with Verifiable Rewards):**
RLVR là paradigm trong đó reward signal đến từ **deterministic verifier** (compiler, unit test, SQL executor, math checker) thay vì reward model. Khi verifier là deterministic, kết quả chỉ có hai trạng thái: **pass (1.0)** hoặc **fail (0.0)**. Đây là property intrinsic của verifiable tasks — không phải tuỳ chọn thiết kế mà là hệ quả của việc chọn "verifiable" làm tiêu chí benchmark. Code pass test suite → `reward=1.0`; code compile lỗi → `reward=0.0`. Không có "gần đúng".

Bằng chứng trong codebase:
- `BigCodeBenchResourcesServer.verify()` line 122: `reward=1.0 if status == "pass" else 0.0`
- `PythonExecutorResourcesServer.verify()` (math_with_code) line 247: `reward = 1.0 if accuracy else 0.0`
- `JailbreakDetectionResourcesServer`: `reward_if_safe: float = 1.0`, `reward_if_unsafe: float = 0.0`
- `example_single_tool_call`: `reward=1.0` hardcoded

`reward_profile.py` line 379-386 ghi nhận binary explicitly:
```python
is_binary = all(v in (0, 1, 0.0, 1.0) for v in vals)
if is_binary:
    # dùng công thức pass@k combinatorial
else:
    pass_values.append(max(vals[:k]))  # continuous fallback
```
Framework biết binary là default, continuous là exception.

**2. Tại sao KHÔNG continuous float [0,1]?**

**Vấn đề 1 — Reward hacking:** Với continuous reward (e.g., partial credit dựa trên output similarity), model học tối ưu proxy thay vì bài toán thật. Ví dụ: model học viết code trông giống đúng nhưng không pass test, hay học copy một phần expected SQL để tăng similarity score. Binary buộc model phải thực sự giải bài.

**Vấn đề 2 — Aggregation complexity:** Binary reward → `pass@k` có công thức combinatorial chính xác: `1 - C(n_incorrect, k) / C(n_total, k)`. Continuous reward không có định nghĩa `pass@k` chuẩn — phải dùng `max(vals[:k])` (như NeMo Gym làm ở fallback), vốn dĩ thiên vị và không so sánh được across benchmarks.

**Vấn đề 3 — RL gradient stability:** GRPO/PPO với binary reward cho gradient rõ ràng — rollout đúng được reinforce, sai không. Continuous reward cần cẩn thận về scale, variance, normalization (reward whitening). Ở quy mô 16k concurrent rollouts, sự đơn giản của binary rất có giá trị.

**Vấn đề 4 — Benchmark comparability:** Pass@k với binary reward là metric được cộng đồng chấp nhận rộng rãi (HumanEval, MBPP, MATH, AIME). Continuous score proprietary không so sánh được với baseline.

**3. Historical context:**
- **2021:** OpenAI Codex paper (Chen et al.) introduce `pass@k` metric cho code generation với binary reward — được cite hơn 3000 lần.
- **2023:** DeepMind AlphaCode, Meta Code Llama đều dùng binary pass/fail.
- **2024-09:** OpenAI o1-preview launch reveal RLVR methodology — verifiable math/code rewards là core của o1 training. Làn sóng RLVR adoption bắt đầu.
- **2025-01:** DeepSeek R1 paper công khai GRPO + binary reward cho math và code — benchmark đạt SOTA mà không cần outcome reward model. Confirm rằng binary RLVR scale tốt hơn continuous reward model.
- **2025:** Verifiers framework, TRL GRPO trainer, OpenRLHF đều default binary reward cho verifiable benchmarks.

**4. Industry URL:**
- [DeepSeek R1 paper (arXiv 2501.12948)](https://arxiv.org/abs/2501.12948) — Section 3.1 mô tả binary reward cho math/code, GRPO training với `r ∈ {0, 1}`
- [Verifiers framework (willccbb)](https://github.com/willccbb/verifiers) — RLVR library, binary reward là default, defines "verifiable = deterministic check"
- [TRL GRPO Trainer docs](https://huggingface.co/docs/trl/grpo_trainer) — `reward_funcs` expects 0/1 return, `process_reward_fn` normalizes
- [OpenAI Codex paper — pass@k](https://arxiv.org/abs/2107.03374) — original `pass@k` definition với binary per-sample correctness
- [OpenRLHF](https://github.com/OpenLLMAI/OpenRLHF) — binary reward verifier pattern trong `examples/train_ppo_ray.sh`

---

### Decision 4: Cookie + token_ids propagation cho stateful environment affinity

**File:** [`responses_api_agents/simple_agent/app.py`](../../responses_api_agents/simple_agent/app.py) (lines 80-97, 155-170) · [`responses_api_agents/proof_refinement_agent/app.py`](../../responses_api_agents/proof_refinement_agent/app.py) (lines 158-175)

**1. Nguyên lý — Session affinity + RL gradient feed:**

**Cookie propagation** giải quyết hai vấn đề:
1. **Stateful environments:** `math_with_code` (`PythonExecutorResourcesServer`) dùng `session_id` cookie để map HTTP request → long-lived subprocess (`_SessionHandle`) lưu Python globals giữa các lần `execute_python()`. Không có cookie propagation, mỗi tool call tạo process mới → mất state.
2. **Cross-service session continuity:** Trong `SimpleAgent.responses()`, `resources_server_cookies` được update sau mỗi tool call và truyền vào call tiếp theo: `cookies=resources_server_cookies`. Cuối cùng tất cả cookies được set vào response trả về, để caller (`run()`) forward vào `/verify`.

**Token_ids propagation** phục vụ RL training: `prompt_token_ids`, `generation_token_ids`, `generation_log_probs` được truyền qua response để trainer tính policy gradient mà không cần re-tokenize. Đây là optimization critical cho GRPO (Generalized Reward Policy Optimization) — cần log_probs của generation cũ để tính KL divergence.

**2. Tại sao KHÔNG dùng Authorization header hoặc shared DB?**

- **Auth header:** Chỉ phù hợp cho identity, không phải session state. Header không persist qua response/request cycle — phải client tự lưu lại.
- **Shared Redis/DB:** Tạo external dependency, tăng latency (~1ms/lookup), single point of failure. Với 16k concurrent rollouts, Redis sẽ là bottleneck. Cookie-based session sidecar trên HTTP layer zero-cost về infra.
- **In-memory dict trên agent:** Vỡ khi scale horizontally (multiple agent instances). Cookie là stateless transport — session state ở resources server, agent chỉ forward.

**3. Historical context:**
HTTP cookie (RFC 6265) ban đầu dùng cho web session auth (Netscape, 1994). Dùng cookie cho microservice session routing là pattern chuẩn trong service mesh (Istio session affinity, 2018). Trong ML serving, OpenAI API dùng cookies cho streaming SSE; vLLM dùng session ID cho prefix caching. Token-level log_probs propagation pattern từ TRL và OpenRLHF — cần token IDs để avoid re-compute trong PPO/GRPO.

**4. Industry URL:**
- [TRL — token-level logging và GRPO](https://github.com/huggingface/trl/blob/main/trl/trainer/grpo_trainer.py) — xem `generation_kwargs`, log_probs collection
- [OpenRLHF — token IDs trong rollout](https://github.com/OpenLLMAI/OpenRLHF/blob/main/openrlhf/trainer/ray/ppo_actor.py) — `prompt_ids`, `response_ids` propagation
- [RFC 6265 — HTTP State Management Mechanism](https://datatracker.ietf.org/doc/html/rfc6265) — cookie spec
- [Istio session affinity](https://istio.io/latest/docs/concepts/traffic-management/#sticky-sessions) — microservice-level cookie-based routing

---

### Sampling: 5 resources_servers verify() spectrum

#### Server 1: `example_single_tool_call` — Trivial baseline (tool testing domain)
**File:** [`resources_servers/example_single_tool_call/app.py`](../../resources_servers/example_single_tool_call/app.py)

```python
async def verify(self, body: BaseVerifyRequest) -> BaseVerifyResponse:
    return BaseVerifyResponse(**body.model_dump(), reward=1.0)
```

- **Domain:** Smoke test / tool call validation
- **Verify strategy:** Hardcoded `reward=1.0` — không check gì cả. Dùng để test infrastructure, không đánh giá chất lượng output.
- **Complexity:** Minimal — 1 dòng logic
- **Extra endpoints:** `/get_weather` (tool endpoint) — resources server kiêm tool server
- **Lesson:** Base class enforces `verify()` phải tồn tại, nhưng không enforce nội dung. Đây là valid implementation cho smoke test.

#### Server 2: `bigcodebench` — Code execution (coding domain)
**File:** [`resources_servers/bigcodebench/app.py`](../../resources_servers/bigcodebench/app.py)

```python
async def verify(self, body: BigCodeBenchVerifyRequest) -> BigCodeBenchVerifyResponse:
    # 1. Extract code from model output
    extracted = preprocess_code_completion(model_out)
    # 2. Run in isolated venv subprocess với semaphore
    async with self._semaphore:
        result = await self._run_in_venv(code=calibrated, test_code=..., entry_point=...)
    # 3. Binary reward
    reward=1.0 if status == "pass" else 0.0
```

- **Domain:** Code generation (BigCodeBench benchmark)
- **Verify strategy:** Subprocess execution trong isolated venv với timeout, resource limits (AS/data/stack), semaphore concurrency control (default 8 processes)
- **Complexity:** Cao — auto-install venv (`ensure_bcb_venv`), code extraction, sandboxed execution
- **Extra fields:** `extracted_model_code`, `status`, `details`, `task_id`
- **Lesson:** Verify() có thể spawn external processes. `asyncio.Semaphore` là pattern chuẩn cho concurrency control.

#### Server 3: `math_with_code` — Stateful REPL (math domain)
**File:** [`resources_servers/math_with_code/app.py`](../../resources_servers/math_with_code/app.py)

```python
async def verify(self, body: PythonMathVerifyRequest) -> PythonMathVerifyResponse:
    # Extract \boxed{} answer từ assistant output hoặc tool stdout
    actual = _extract_boxed_answer(text_content)
    accuracy = _answers_match(actual, expected)
    reward = 1.0 if accuracy else 0.0
```

- **Domain:** Mathematical reasoning with code execution tool
- **Verify strategy:** Parse `\boxed{...}` LaTeX answer với brace-depth tracking + numeric fuzzy match (`|fa - fe| < 1e-6 × max(1, |fe|)`)
- **Extra endpoints:** `/execute_python`, `/end_session` — stateful REPL với `_SessionHandle` (subprocess per session_id, giữ Python globals)
- **Complexity:** Medium — answer extraction + numeric normalization + session management
- **Lesson:** Resources server vừa là tool server (execute_python) vừa là verifier. Session state dùng cookie-mapped `_SessionHandle`.

#### Server 4: `text_to_sql` — LLM-as-judge (database domain)
**File:** [`resources_servers/text_to_sql/app.py`](../../resources_servers/text_to_sql/app.py)

```python
async def verify(self, body: TextToSqlVerifyRequest) -> TextToSqlVerifyResponse:
    extracted_sql = extract_sql_from_response(generated)
    first_equal, first_eval = await self._generate_judge_evaluation(...)
    if first_equal and self.config.check_twice_swap:
        # Swap check để detect positional bias
        second_equal, second_eval = await self._generate_judge_evaluation(
            expected_sql=extracted_sql, generated_sql=expected_sql  # SWAPPED
        )
        reward = 1.0 if second_equal else config.reward_if_swap_fails
```

- **Domain:** Text-to-SQL (database query generation)
- **Verify strategy:** LLM judge với double-check swap (reverse A/B order để detect judge positional bias). Config `check_twice_swap=True` là default.
- **Complexity:** Cao — SQL extraction (multi-fallback regex), async judge call với Semaphore(64), swap validation
- **Extra fields:** `extracted_sql`, `judge_passed`, `failure_reason` (enum), `judge_evaluations` (list)
- **Lesson:** LLM-as-judge có thể bị positional bias → swap check. `reward: float = 0.0` hoặc `config.reward_if_swap_fails` — không hoàn toàn binary ở config level nhưng default là binary.

#### Server 5: `jailbreak_detection` — Safety evaluation (safety domain)
**File:** [`resources_servers/jailbreak_detection/app.py`](../../resources_servers/jailbreak_detection/app.py)

```python
async def verify(self, body: JailbreakDetectionVerifyRequest) -> JailbreakDetectionVerifyResponse:
    # Policy-aware routing
    policy = body.model_extra.get("response_policy_mapped")
    if policy and policy in self._policy_verifier_map:
        return await self._verify_policy_aware(...)  # multi-verifier, product/average combination
    return await self._verify_legacy(...)  # standard safety × quality flow

# Legacy flow:
reward = reward_safety  # 1.0 (safe) / 0.0 (unsafe)
# Combined mode: reward = reward_safety * reward_quality (0.5 quality partial credit)
```

- **Domain:** AI safety / jailbreak detection
- **Verify strategy:** LLM judge với 3 modes: (1) custom label template, (2) Nemotron-Content-Safety-Reasoning-4B format, (3) policy-aware multi-verifier (parallel asyncio.gather, product/average reward combination)
- **Complexity:** Rất cao — dual-mode judge, policy routing, YAML-loaded verifier templates, `asyncio.gather` cho parallel verifiers
- **Edge case:** `use_combined_reward=True` tạo ra `reward = 0.5` — trường hợp **continuous reward** ngoại lệ trong ecosystem mostly-binary
- **Lesson:** Một server duy nhất có thể support nhiều verify strategies qua config. Policy-aware flow là ví dụ Strategy pattern thuần túy tại runtime (không phải subclass).

---

### Tổng hợp verify() spectrum

| Server | Domain | Strategy | Binary? | Extra tools? | Complexity |
|---|---|---|---|---|---|
| example_single_tool_call | Tool testing | Hardcoded 1.0 | Trivially yes | `/get_weather` | 1/5 |
| bigcodebench | Code execution | Subprocess + venv | Yes | - | 4/5 |
| math_with_code | Math reasoning | Boxed answer parse + numeric match | Yes | `/execute_python` (stateful REPL) | 3/5 |
| text_to_sql | Database/SQL | LLM judge + swap check | Yes (default) | - | 4/5 |
| jailbreak_detection | AI safety | Multi-LLM judge, policy routing | Mostly yes | - | 5/5 |

**Quan sát chính:**
1. `reward: float` trong `BaseVerifyResponse` là `float` không phải `bool` — framework cho phép continuous nhưng convention là binary.
2. Khi LLM judge không thể phân loại (`None` verdict), reward default về `0.0` (fail-safe, conservative).
3. Các servers phức tạp nhất (bigcodebench, jailbreak) đều dùng `asyncio.Semaphore` để control concurrency — pattern nhất quán.
4. Proof-refinement loop (agent level) có thể chạy nhiều verify() calls tuần tự, mỗi lần nhận `correction_prompt` từ resources server — stateless resources server + stateful agent là sự phân tách rõ ràng.

## Phản biện (2026-05-24, Round 1+2)
- Round 1: 8.0/10.
- Round 2: 9.2/10 — Reward binary decision dedicated, ≥3 servers sampling enforced.
