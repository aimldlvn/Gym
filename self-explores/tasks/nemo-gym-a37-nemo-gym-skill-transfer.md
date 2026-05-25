---
date: 2026-05-24
type: task-worklog
task: nemo-gym-a37
title: "nemo-gym — Skill Transfer (Lối tắt & Thực hành)"
status: open
detailed_at: 2026-05-24 23:30
detail_score: ready-for-dev
tags: [system-design, skill-transfer, nemo-gym, T5]
---

# nemo-gym — Skill Transfer — Detailed Design

## 1. Objective
Chuyển giao kỹ năng từ phân tích nemo-gym: ≥3 mental shortcuts khác góc nhìn + ≥2 exercises (<2h mỗi bài) runnable với verify criteria là runnable command.

## 2. Scope

**In-scope:**
- 3-5 mental shortcuts (config / function / async / failure / data perspectives).
- 2-3 exercises trên branch `practice-*`, mỗi bài có Goal + Setup + Steps + Verify + Estimated + Nguyên lý applied.
- Mỗi exercise link đến ≥1 decision từ T4.{1-4}.

**Out-of-scope:**
- KHÔNG thực hiện bài tập (chỉ thiết kế).
- KHÔNG đụng benchmarks production (chỉ branch `practice-*`).

## 3. Input / Output

**Input:**
- T3 worklog ([code mapping](nemo-gym-mpk-nemo-gym-code-mapping.md))
- T4.1-T4.4 worklogs (deep research per layer)
- T4 parent (cross-layer patterns)

**Output:**
- Section "Mental Shortcuts" với ≥3 entries.
- Section "Exercises" với ≥2 entries.

## 4. Dependencies
- Beads: blocked-by T3 (`nemo-gym-mpk`) + T4 parent (`nemo-gym-0t4`).

## 5. Flow xử lý

### Step 1: Đọc worklogs upstream (~10 phút)
```bash
cat self-explores/tasks/nemo-gym-mpk-*.md | head -300
cat self-explores/tasks/nemo-gym-0t4-*.md | head -200
```

### Step 2: Draft Mental Shortcuts (~10 phút)
Tối thiểu 3 góc nhìn khác nhau:
1. **Config perspective:** "Mỗi YAML top-level key = 1 server instance. Đọc configs/*.yaml trước code."
2. **Function perspective:** "Tìm `verify()` trước; mọi resources_server đều converge về function này."
3. **Async perspective:** "Tìm sync I/O trong nemo_gym/ = code smell."
4. **Failure perspective:** "ServerClient retry config (3 tries, expo backoff) = SLA giả định."
5. **Data perspective:** "`verifier_metadata` opaque = Hydra escape hatch."

### Step 3: Draft Exercise 1 — Build length_check resources_server (~15 phút)
- **Goal:** Tạo resources_server `length_check` với verify reward = (len(output) >= X ? 1.0 : 0.0).
- **Setup:**
  ```bash
  git checkout -b practice-length-check
  uv venv && uv sync --extra dev
  # Verify ng_init CLI exists
  ng_init_resources_server --help 2>&1 | head -5
  ```
- **Steps:**
  1. `ng_init_resources_server +name=length_check` (hoặc copy từ example_single_tool_call).
  2. Edit `resources_servers/length_check/app.py` → override verify() trả reward dựa len(output).
  3. Tạo `data/example.jsonl` 5 entries với varied output lengths.
  4. Add `resources_servers/length_check/configs/length_check.yaml`.
  5. Run `ng_test +entrypoint=resources_servers/length_check`.
- **Verify:** `ng_test` exit code 0; pytest coverage >= 95%.
- **Estimated:** 60-90 phút.
- **Nguyên lý applied:** Template Method (T4.2) + YAML composition (T4.1).

### Step 4: Draft Exercise 2 — aiohttp adapter for fake HTTP lib (~10 phút)
- **Goal:** Wrap fake HTTP library (mock thay vì real) bằng aiohttp adapter pattern (TavilySearchAIOHTTPClient style).
- **Setup:**
  ```bash
  git checkout -b practice-aiohttp-adapter
  mkdir resources_servers/length_check/mock_client
  ```
- **Steps:**
  1. Implement `MockAIOHTTPClient` qua `nemo_gym.server_utils.request()`.
  2. Add stress test fixture: 100 concurrent requests qua `pytest.mark.asyncio`.
  3. Verify no hang + no fd leak.
- **Verify:** `pytest -k stress resources_servers/length_check/tests/ -v` pass; `lsof -p <pid>` không leak fd.
- **Estimated:** 60 phút.
- **Nguyên lý applied:** aiohttp singleton + Connection pool (T4.4 + engineering note).

### Step 5: Draft Exercise 3 (optional) — Mock ResponsesAPIModel (~10 phút)
- **Goal:** Add `responses_api_models/mock_model` trả output cố định (vd "42") cho dev/testing.
- **Setup:**
  ```bash
  git checkout -b practice-mock-model
  cp -r responses_api_models/vllm_model responses_api_models/mock_model
  ```
- **Steps:** Override `chat_completions()` + `responses()` trả constant.
- **Verify:** `simple_agent /run` với mock_model returns reward consistent across 10 calls.
- **Estimated:** 30-45 phút.
- **Nguyên lý applied:** Adapter pattern (T4.3) + Strategy (multiple ResponsesAPIModel variants).

## 6. Edge Cases & Error Handling
| Case | Trigger | Expected | Recovery |
|---|---|---|---|
| `ng_init_resources_server` không tồn tại (renamed) | --help fail | Document path fix; copy template thủ công | Use existing example as template |
| `practice-*` branch chưa clean | git checkout fail | `git stash` rồi checkout | Cảnh báo user |
| Stress test fail vì RAY_TMPDIR | tests hang | Set `RAY_TMPDIR=/tmp` (T4.4 gotcha) | Doc tip ở top of exercise |
| Verify command yêu cầu GPU | RTX 3090 không free | Doc fallback CPU-only verify | Skip GPU-dependent assertion |

## 7. Acceptance Criteria
- **Happy:** Given T3 + T4 closed, When task chạy, Then ≥3 mental shortcuts khác góc nhìn + ≥2 exercises có ĐỦ 6 fields (Goal/Setup/Steps/Verify/Estimated/Nguyên lý) + verify criteria là runnable command + mỗi exercise link đến T4 decision.
- **Negative:** Given exercise verify command không runnable (vd require manual UI inspection), When review, Then exercise đó được thay thế bằng one runnable.

## 8. Technical Notes
- `ng_init_resources_server` từ CLAUDE.md — verify CLI tồn tại trong nemo_gym/cli_setup_command.py.
- Stress test fd count: `ls /proc/$$/fd | wc -l` trước/sau.
- `pytest.mark.asyncio` requires `pytest-asyncio` (đã có trong dev deps).

## 9. Risks
- **R1:** Exercises tốn nhiều hơn 2h. *Mitigation:* Strict timebox + provide "minimum viable" path (skip optional steps).
- **R2:** Mental shortcuts trùng góc nhìn. *Mitigation:* Buộc khác category (config/function/async/failure/data — pick 3 different).
- **R3:** Exercise dùng feature out-of-scope (vd Ray distributed). *Mitigation:* Each exercise must run on single dev box RTX 3090, no cluster.

## Worklog

> Thực hiện: 2026-05-25. Executor agent T5 (skill transfer).
> Input: T3 (code-mapping) + T4 parent (cross-layer) + T4.1–T4.4 (per-layer decisions).

---

## Mental Shortcuts

### Shortcut 1 — Config Perspective: "YAML top-level key = 1 process"

**Phát biểu:** Mỗi top-level key trong merged YAML config là 1 server instance độc lập. Muốn hiểu hệ thống đang chạy gì, đọc config — không cần đọc code.

**Cơ chế:** `GlobalConfigDictParser.parse()` tại [`nemo_gym/global_config.py:385`](../../nemo_gym/global_config.py#L385) gọi `filter_for_server_instance_configs()` để tách riêng các key là server instance, sau đó `validate_and_populate_defaults()` auto-assign host/port cho từng instance từ `port_range_low..port_range_high`. Developer không bao giờ hardcode port — hệ thống tự phân phối.

**Lối tắt thực hành:**
- Gặp config mới → đọc top-level keys trước → biết ngay có bao nhiêu process, loại gì.
- Muốn thêm 1 server → thêm 1 top-level key, không sửa code.
- Debug port conflict → kiểm tra `disallowed_ports` trong merged config (`ng_dump_config`).

**Liên kết:** [T4.1 — Decision: Hydra Composition](nemo-gym-0t4.1-nemo-gym-deep-research-data-storage.md) + [T4 Parent — Principle 3: Convention over Configuration](nemo-gym-0t4-nemo-gym-deep-research-parent.md).

---

### Shortcut 2 — Function Perspective: "verify() là duy nhất bạn cần implement"

**Phát biểu:** Khi thêm benchmark mới, chỉ 1 method bắt buộc: `async def verify(self, body) -> BaseVerifyResponse`. Mọi thứ khác (FastAPI routing, session middleware, error handling, `/aggregate_metrics`) đã có sẵn trong skeleton.

**Cơ chế:** `SimpleResourcesServer` tại [`nemo_gym/base_resources_server.py:57`](../../nemo_gym/base_resources_server.py#L57) dùng Template Method pattern — `setup_webserver()` frozen, `verify()` là `@abstractmethod` duy nhất. Kết quả: 89 LOC định nghĩa toàn bộ extensibility contract cho 80+ benchmarks trong hệ thống.

**Lối tắt thực hành:**
- Đọc codebase server mới → `grep -n "def verify"` → tìm được business logic ngay, bỏ qua boilerplate.
- Khi review PR benchmark mới → chỉ cần xem `verify()` body + `VerifyResponse` fields; middleware/routing không cần đụng.
- Nếu `verify()` gọi external process → tìm `asyncio.Semaphore` ngay bên trên — đây là convention bắt buộc.

**Liên kết:** [T4.2 — Decision: Template Method + Strategy](nemo-gym-0t4.2-nemo-gym-deep-research-business-logic.md) + [T3 Leverage Point: SimpleResourcesServer](nemo-gym-mpk-nemo-gym-code-mapping.md).

---

### Shortcut 3 — Async/Failure Perspective: "Tìm sync I/O = tìm time bomb"

**Phát biểu:** NeMo Gym xử lý 16,000+ concurrent rollouts. Bất kỳ blocking call nào trong event loop = toàn bộ rollout collection đóng băng. Rule: nếu thấy code không có `await`, không có `async with`, không có `asyncio.Semaphore` quanh external call — đó là bug, không phải style.

**Cơ chế — 3 tầng phòng thủ:**
1. **Transport**: `_GLOBAL_AIOHTTP_CLIENT` singleton tại [`nemo_gym/server_utils.py:74`](../../nemo_gym/server_utils.py#L74) — 1 `ClientSession`, 1 `TCPConnector(limit=N//num_workers)`. Không tạo connection mới per-request.
2. **Subprocess**: `async with self._semaphore:` bao quanh `await self._run_in_venv(...)` trong `bigcodebench/app.py` — default 8 slots, không crash khi 1000 requests concurrent.
3. **Adapter**: Nếu thư viện ngoài dùng httpx/requests → wrap bằng `TavilySearchAIOHTTPClient` pattern ([`resources_servers/tavily_search/app.py`](../../resources_servers/tavily_search/app.py)) — thay HTTP transport, giữ nguyên API surface.

**Lối tắt thực hành:**
- Audit server mới: `grep -rn "requests\.\|httpx\.\|\.get(\|\.post(" app.py` → phải ra 0 hit ngoài test file.
- Nếu thấy `subprocess.run(...)` không có `await` và không có `asyncio` wrapper → critical bug, escalate.
- `RAY_TMPDIR=/tmp` luôn set trước khi chạy tests có Ray (socket path > 107 bytes = silent hang).

**Liên kết:** [T4.4 — Decision: aiohttp O(n²) incident](nemo-gym-0t4.4-nemo-gym-deep-research-infrastructure.md) + [T4 Parent — Principle 1: Async-First, Semaphore-Bounded](nemo-gym-0t4-nemo-gym-deep-research-parent.md) + [Engineering note](../../docs/infrastructure/engineering-notes/aiohttp-vs-httpx.md).

---

### Shortcut 4 — Data Perspective: "verifier_metadata là Hydra escape hatch — opaque by design"

**Phát biểu:** `verifier_metadata` trong JSONL input là dict không có schema cố định — framework không parse nó, chỉ pass-through từ data file vào `verify()`. Đây là intentional design: mỗi benchmark tự define schema của mình bên trong.

**Cơ chế:** `BaseVerifyRequest` tại [`nemo_gym/base_resources_server.py`](../../nemo_gym/base_resources_server.py) có `verifier_metadata: dict` kiểu `Any`. Server subclass cast nó về Pydantic model riêng bên trong `verify()`. Tương tự, `gitlab_identifier` + `jsonl_fpath` coexist trong `DatasetConfig` ([`nemo_gym/config_types.py`](../../nemo_gym/config_types.py)) — hai field phục vụ hai responsibility: remote source (Strategy) vs local cache (Cache pattern), không thay thế nhau.

**Lối tắt thực hành:**
- Thiết kế data mới → bỏ task-specific fields vào `verifier_metadata`, không sửa framework schema.
- Debug "verify() nhận sai data" → kiểm tra `verifier_metadata` trong JSONL input trước, không nhìn framework code.
- Khi thêm `gitlab_identifier` vào config → `jsonl_fpath` vẫn bắt buộc (local download target), không xóa được.

**Liên kết:** [T4.1 — Decision: gitlab_identifier + jsonl_fpath coexistence](nemo-gym-0t4.1-nemo-gym-deep-research-data-storage.md) + [T4 Parent — Pattern 3: Pydantic Schema Everywhere](nemo-gym-0t4-nemo-gym-deep-research-parent.md).

---

## Exercises

### Exercise 1: Build `length_check` Resources Server từ Template

**1. Goal**
Tạo resources server `length_check` hoàn chỉnh với `verify()` trả `reward=1.0` khi `len(output_text) >= min_length`, verify bằng `ng_test` exit 0 và coverage >= 95%.

**2. Setup**
```bash
# Tạo branch thực hành
git checkout -b practice-length-check

# Cài dev deps (nếu chưa có)
uv venv && uv sync --extra dev

# Verify template tồn tại
ls /home/admin88/5_poc_experiments/nvidia/Gym/resources_servers/example_single_tool_call/app.py

# Kiểm tra ng_test CLI
ng_test --help 2>&1 | head -5
```

**3. Steps**
1. Copy template và tạo structure:
   ```bash
   cp -r resources_servers/example_single_tool_call resources_servers/length_check
   rm -rf resources_servers/length_check/data/
   mkdir -p resources_servers/length_check/data
   ```

2. Sửa `resources_servers/length_check/app.py` — override `verify()`:
   ```python
   # Trong LengthCheckResourcesServer(SimpleResourcesServer):
   class LengthCheckConfig(BaseResourcesServerConfig):
       min_length: int = 10  # configurable via YAML

   async def verify(self, body: BaseVerifyRequest) -> BaseVerifyResponse:
       output_text = body.response.output_text or ""
       reward = 1.0 if len(output_text) >= self.config.min_length else 0.0
       return BaseVerifyResponse(**body.model_dump(), reward=reward)
   ```

3. Tạo `resources_servers/length_check/configs/length_check.yaml`:
   ```yaml
   length_check_server:
     resources_servers:
       length_check:
         entrypoint: app.py
         domain: general
         min_length: 10
   ```

4. Tạo `resources_servers/length_check/data/example.jsonl` (5 entries — output ngắn + dài):
   ```bash
   # 3 entries có output >= 10 chars (reward 1.0), 2 entries ngắn (reward 0.0)
   printf '{"responses_create_params":{"input":[{"role":"user","content":"Say hello"}]},"verifier_metadata":{}}\n' > resources_servers/length_check/data/example.jsonl
   # (thêm 4 entries tương tự)
   ```

5. Sửa `tests/test_app.py` để test `min_length=5` với output ngắn/dài:
   ```bash
   # Test reward=1.0 khi len >= min_length, reward=0.0 khi len < min_length
   pytest resources_servers/length_check/tests/ -v
   ```

**4. Verify**
```bash
# Primary verify — phải exit 0
RAY_TMPDIR=/tmp ng_test +entrypoint=resources_servers/length_check

# Coverage check
RAY_TMPDIR=/tmp ng_test +entrypoint=resources_servers/length_check 2>&1 | grep -E "PASSED|FAILED|coverage"

# Smoke test build (không cần GPU)
cd resources_servers/length_check && python -c "from app import LengthCheckResourcesServer; print('import OK')"
```

**5. Estimated time**
60–90 phút (copy template 5 phút, override verify() 15 phút, data/config 20 phút, test fix 20 phút, verify pass 10 phút).

**6. Nguyên lý applied**
- [T4.2 — Template Method + Strategy: skeleton frozen, verify() hot spot](nemo-gym-0t4.2-nemo-gym-deep-research-business-logic.md) — đây là bài luyện tập chính của pattern này.
- [T4.1 — Hydra YAML Composition: top-level key = 1 server instance](nemo-gym-0t4.1-nemo-gym-deep-research-data-storage.md) — file `length_check.yaml` minh họa convention.
- [T4 Parent — Principle 3: Convention over Configuration](nemo-gym-0t4-nemo-gym-deep-research-parent.md) — `data/example.jsonl` 5 entries, `requirements.txt`, `data/.gitignore` đều là convention bắt buộc.

---

### Exercise 2: aiohttp Adapter cho Mock HTTP Library

**1. Goal**
Implement `MockAIOHTTPClient` wrap một mock HTTP library (không dùng requests/httpx) theo pattern `TavilySearchAIOHTTPClient`, verify bằng stress test 100 concurrent requests pass và không leak file descriptors.

**2. Setup**
```bash
# Tạo branch thực hành
git checkout -b practice-aiohttp-adapter

# Cài dev deps
uv venv && uv sync --extra dev

# Verify TavilySearchAIOHTTPClient tồn tại (mẫu tham khảo)
grep -n "class TavilySearchAIOHTTPClient\|aiohttp\|ClientSession" \
  resources_servers/tavily_search/app.py | head -20

# Verify pytest-asyncio có sẵn
python -c "import pytest_asyncio; print('pytest-asyncio OK')"
```

**3. Steps**
1. Tạo `resources_servers/length_check/mock_client.py` với `MockAIOHTTPClient`:
   ```python
   # Wrap fake responses qua nemo_gym.server_utils.request() interface
   # Không dùng requests.get() hay httpx.get()
   # Pattern: class MockAIOHTTPClient với async def post(self, url, **kwargs)
   # Dùng aiohttp.ClientSession từ get_global_aiohttp_client()
   ```

2. Tạo `resources_servers/length_check/tests/test_stress.py` với stress fixture:
   ```python
   import asyncio
   import pytest

   @pytest.mark.asyncio
   async def test_stress_100_concurrent(mock_client):
       """100 concurrent requests — không hang, không leak fd."""
       tasks = [mock_client.post("http://fake/api", json={"text": f"x" * 20})
                for _ in range(100)]
       results = await asyncio.gather(*tasks)
       assert all(r.status == 200 for r in results)
   ```

3. Đếm fd trước/sau trong test:
   ```python
   import os, glob
   fd_before = len(glob.glob(f"/proc/{os.getpid()}/fd/*"))
   # ... run 100 requests ...
   fd_after = len(glob.glob(f"/proc/{os.getpid()}/fd/*"))
   assert fd_after - fd_before < 10  # không leak
   ```

4. Chạy stress test lần đầu, fix nếu fail (thường do ClientSession không reuse).

5. Xác nhận không có `httpx` hay `requests` import trong mock_client.py:
   ```bash
   grep -n "import httpx\|import requests" resources_servers/length_check/mock_client.py && echo "FAIL: sync HTTP found" || echo "OK"
   ```

**4. Verify**
```bash
# Primary verify — stress test phải pass, fd leak check phải pass
RAY_TMPDIR=/tmp pytest -k "stress" resources_servers/length_check/tests/ -v

# No sync HTTP import
grep -rn "import httpx\|import requests\|requests\.get\|requests\.post" \
  resources_servers/length_check/mock_client.py \
  && echo "AUDIT_FAIL: sync HTTP found" || echo "AUDIT_PASS"

# fd count verification (in-test assertion covers này, nhưng có thể chạy thêm)
RAY_TMPDIR=/tmp pytest -k "stress" resources_servers/length_check/tests/ -v -s 2>&1 | grep -E "fd_before|fd_after|PASSED|FAILED"
```

**5. Estimated time**
60 phút (đọc TavilySearchAIOHTTPClient 10 phút, implement MockAIOHTTPClient 20 phút, write stress test 15 phút, debug fd leak nếu có 15 phút).

**6. Nguyên lý applied**
- [T4.4 — Decision: aiohttp singleton + O(n²) incident](nemo-gym-0t4.4-nemo-gym-deep-research-infrastructure.md) — bài này là hands-on với pattern chống O(n²) bug, reuse `_GLOBAL_AIOHTTP_CLIENT`.
- [T4 Parent — Principle 1: Async-First, Semaphore-Bounded Concurrency](nemo-gym-0t4-nemo-gym-deep-research-parent.md) — 100 concurrent requests là minimum smoke cho async correctness.
- [T3 — Leverage Point: Global aiohttp Singleton + Retry Bulkhead](nemo-gym-mpk-nemo-gym-code-mapping.md) — đọc `get_global_aiohttp_client()` trước khi implement, không tạo `ClientSession` mới.
- [Engineering note: aiohttp-vs-httpx](../../docs/infrastructure/engineering-notes/aiohttp-vs-httpx.md) — hiểu tại sao mock library phải dùng aiohttp adapter thay vì wrap httpx.

---

### Exercise 3 (optional): Mock ResponsesAPIModel trả output cố định

**1. Goal**
Tạo `responses_api_models/mock_model` trả output cố định (VD: `"42"`) cho mọi request, dùng làm model giả cho dev/testing mà không cần GPU, verify bằng `simple_agent /run` trả reward consistent qua 5 lần gọi.

**2. Setup**
```bash
git checkout -b practice-mock-model

# Copy từ model có structure đơn giản nhất
cp -r responses_api_models/openai_model responses_api_models/mock_model

# Verify structure
ls responses_api_models/mock_model/
```

**3. Steps**
1. Sửa `responses_api_models/mock_model/app.py` — override `chat_completions()` + `responses()`:
   ```python
   async def chat_completions(self, body) -> ChatCompletion:
       # Trả message cố định, không gọi LLM
       return ChatCompletion(choices=[{"message": {"content": "42"}}], ...)

   async def responses(self, body) -> Response:
       return Response(output=[{"text": "42"}], ...)
   ```

2. Tạo `responses_api_models/mock_model/configs/mock_model.yaml`.

3. Chạy `ng_test +entrypoint=responses_api_models/mock_model`.

4. Pair với `length_check` server từ Exercise 1: output `"42"` có len=2 < min_length=10 → reward=0.0 consistent.

5. Verify 5 lần gọi đều ra reward=0.0:
   ```bash
   for i in {1..5}; do
     curl -s -X POST http://localhost:PORT/verify -H "Content-Type: application/json" \
       -d '{"response":{"output_text":"42"},"responses_create_params":{"input":[]},"verifier_metadata":{}}' \
       | python -c "import sys,json; d=json.load(sys.stdin); print(f'run {'"$i"'}: reward={d[\"reward\"]}')"
   done
   ```

**4. Verify**
```bash
# Unit test mock model
RAY_TMPDIR=/tmp ng_test +entrypoint=responses_api_models/mock_model

# Consistency: 5 calls, cùng reward
RAY_TMPDIR=/tmp pytest responses_api_models/mock_model/tests/ -k "consistent" -v
```

**5. Estimated time**
30–45 phút (override 2 methods 10 phút, config 5 phút, test 15 phút, consistency check 10 phút).

**6. Nguyên lý applied**
- [T4.3 — Decision: Mimic OpenAI Responses API + /responses vs /chat/completions](nemo-gym-0t4.3-nemo-gym-deep-research-interface-api.md) — mock model phải expose đúng 2 endpoints này.
- [T4.2 — Decision: Agent as HTTP server (Service-Oriented)](nemo-gym-0t4.2-nemo-gym-deep-research-business-logic.md) — mock model là HTTP server riêng, test isolation sạch.
- [T4 Parent — Principle 2: Pydantic-Enforced Contract at Every Boundary](nemo-gym-0t4-nemo-gym-deep-research-parent.md) — response từ mock phải conform Pydantic schema, không untyped dict.

## Phản biện (2026-05-24, Round 1+2)
- Round 1: 7.0/10 — examples có nhưng verify mơ hồ ("stress test 1k không hang" không runnable).
- Round 2: 9.4/10 — 3 exercises với full 6 fields, runnable commands, link tới T4 decisions.
