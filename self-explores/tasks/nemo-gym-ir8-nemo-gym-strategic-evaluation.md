---
date: 2026-05-24
type: task-worklog
task: nemo-gym-ir8
title: "nemo-gym — Strategic Evaluation (Phản biện hệ thống)"
status: open
detailed_at: 2026-05-24 23:30
detail_score: ready-for-dev
tags: [system-design, architecture, strategic-eval, nemo-gym, T2]
---

# nemo-gym — Strategic Evaluation — Detailed Design

## 1. Objective
Đánh giá nemo-gym theo 3 trục chiến lược (Core Components / Leverage / Extensibility & Scale) với ≥6 findings, mỗi finding có file:line clickable + evidence (code quote ≤5 dòng hoặc reason ≥1 câu).

## 2. Scope

**In-scope:**
- Verify ≥2 Core Components candidates: HeadServer, ServerClient (aiohttp retry), Hydra config composition, BaseServer/SimpleServer hierarchy.
- Verify ≥2 Leverage points: aiohttp singleton, FastAPI middleware stack, cookies/token_ids propagation, ServerClient retry policy.
- Phân tích Extensibility (YAML composition) + Scale bottleneck (4k-65k concurrent).
- Fallback "Critical Path" nếu thấy flat structure.

**Out-of-scope:**
- KHÔNG đề xuất refactor (chỉ phân tích hiện trạng).
- KHÔNG so sánh với competitor framework (việc T4).
- KHÔNG đi sâu code internal (việc T3).

## 3. Input / Output

**Input:**
- Worklog T1 ([`nemo-gym-5py-nemo-gym-contextual-awareness.md`](nemo-gym-5py-nemo-gym-contextual-awareness.md)) — diagrams làm seed.
- Code files:
  - [`nemo_gym/cli.py`](../../nemo_gym/cli.py)
  - [`nemo_gym/global_config.py`](../../nemo_gym/global_config.py)
  - [`nemo_gym/server_utils.py`](../../nemo_gym/server_utils.py)
  - [`nemo_gym/base_resources_server.py`](../../nemo_gym/base_resources_server.py)
  - [`nemo_gym/base_responses_api_model.py`](../../nemo_gym/base_responses_api_model.py)
  - [`nemo_gym/base_responses_api_agent.py`](../../nemo_gym/base_responses_api_agent.py)
  - [`resources_servers/example_single_tool_call/configs/`](../../resources_servers/example_single_tool_call/configs/)
  - [`responses_api_models/vllm_model/configs/`](../../responses_api_models/vllm_model/configs/)

**Output:**
- Section "Core Components" với ≥2 entries.
- Section "Leverage" với ≥2 entries.
- Section "Extensibility & Scale" với ≥2 entries.
- Section "Summary" — 1 câu kết luận/trục.

## 4. Dependencies
- Beads: blocked-by T1 (`nemo-gym-5py`).
- Tools: `grep`, `wc`, `find`.

## 5. Flow xử lý

### Step 1: Đọc worklog T1 (~5 phút)
```bash
cat self-explores/tasks/nemo-gym-5py-*.md | head -200
```
**Verify:** Có diagram seed + flow table.

### Step 2: Core Components ─ Verify candidates (~10 phút)
```bash
grep -n "class HeadServer\|class ServerClient\|class BaseServer\|class SimpleServer" nemo_gym/*.py
wc -l nemo_gym/global_config.py nemo_gym/server_utils.py nemo_gym/base_*.py
```
Cho mỗi candidate: trả lời "nếu xóa thì hệ thống fail vì..."
**Verify:** ≥2 entries với file:line + lý do.

### Step 3: Leverage points (~10 phút)
```bash
grep -n "aiohttp\|ClientSession\|retry\|backoff" nemo_gym/server_utils.py nemo_gym/openai_utils.py
grep -n "middleware\|app.add_middleware" nemo_gym/base_*.py
grep -n "cookies\|token_ids\|prompt_token_ids" nemo_gym/base_*.py responses_api_agents/*/app.py | head -20
```
Đo: thay 1 dòng X → tác động bao nhiêu %?
**Verify:** ≥2 entries với LOC count + impact estimate.

### Step 4: Extensibility & Scale (~10 phút)
```bash
ls resources_servers/example_single_tool_call/configs/
ls responses_api_models/vllm_model/configs/
grep -rn "ng_init_resources_server\|init_resources_server" nemo_gym/ scripts/
grep -n "asyncio.Semaphore\|max_concurrent" nemo_gym/*.py | head -10
```
**Verify:** Có YAML example + Semaphore usage + 1 câu "tại sao contributor dễ thêm".

### Step 5: Format output (~10 phút)
Cho mỗi trục viết:
```markdown
## {Trục}
### {Finding name}
- File: [`path:line`](../../path#L...)
- {Evidence: quote ≤5 dòng hoặc reason ≥1 câu}
- {Impact / Tại sao quan trọng}
```

## 6. Edge Cases & Error Handling
| Case | Trigger | Expected | Recovery |
|---|---|---|---|
| Class HeadServer không tồn tại (renamed) | grep trả 0 hit | Tìm class coordinator khác | grep `lifecycle\|coordinator` trong `nemo_gym/cli.py` |
| Flat architecture, không có Leverage rõ | scan ≤200 LOC files không tìm thấy | Fallback "Critical Path" | Phân tích luồng dài nhất, identify fail-one-fail-all |
| asyncio.Semaphore không có | grep trả 0 hit | Tìm cơ chế khác (ThreadPool / queue) | Document concurrency model phát hiện được |

## 7. Acceptance Criteria
- **Happy 1:** Given T1 đã closed, When task chạy, Then 3 sections (Core/Leverage/Ext) đều có ≥2 findings với file:line clickable.
- **Happy 2:** Given flat architecture, When task chạy, Then trục Leverage được thay bằng "Critical Path" + lý do giải thích.
- **Negative:** Given file path trong evidence không tồn tại, When task chạy, Then findings đó bị thay thế hoặc skip + lý do log.

## 8. Technical Notes
- LOC count: `wc -l {file}` ra tổng dòng.
- Pattern "200-500 LOC chi phối toàn bộ": tìm class size moderate (không quá lớn không quá nhỏ) nhưng được import/call từ nhiều nơi (`grep -rl "ClassName" .` ≥5 files).
- Concurrent claim 4k-65k từ [`CLAUDE.md`](../../CLAUDE.md) — verify trong `nemo_gym/server_utils.py` (max_concurrent_requests).

## 9. Risks
- **R1:** Findings quá generic (vd "FastAPI là Core"). *Mitigation:* Phải có file:line cụ thể, không phải mức framework.
- **R2:** Confirmation bias — chỉ confirm hypothesis từ CLAUDE.md. *Mitigation:* Cố tình tìm counter-example (vd "Core nhưng có replacement easy" → để hiểu degree of Core-ness).
- **R3:** Tốn thời gian deep code thay vì strategic. *Mitigation:* Mỗi finding tối đa 5 phút research.

## Worklog

### Axis 1: Core Components

#### Core 1: HeadServer — Service Registry & Config Distributor
- File: [`nemo_gym/server_utils.py:694-733`](../../nemo_gym/server_utils.py#L694)
- Evidence:
  ```python
  class HeadServer(BaseServer):
      def setup_webserver(self) -> FastAPI:
          app = FastAPI()
          app.get("/global_config_dict_yaml")(self.global_config_dict_yaml)
          app.get("/server_instances")(self.get_server_instances)
          return app
  ```
- Tại sao không thể thay thế: HeadServer là điểm duy nhất expose `/global_config_dict_yaml` — mọi child server (agent, model, resources) khởi động bằng cách đọc env var `NEMO_GYM_CONFIG_DICT` được inject từ đây (`cli.py:173`). Nếu xóa HeadServer, không có cơ chế nào để child servers biết địa chỉ IP:port của nhau, toàn bộ inter-server routing sụp đổ. `RunHelper.start()` hardcode `HeadServer.run_webserver()` trước khi spawn bất kỳ subprocess nào (`cli.py:135`).

#### Core 2: GlobalConfigDictParser — Single Source of Truth cho Config
- File: [`nemo_gym/global_config.py:596-634`](../../nemo_gym/global_config.py#L596)
- Evidence:
  ```python
  def get_global_config_dict(...) -> DictConfig:
      global _GLOBAL_CONFIG_DICT
      if _GLOBAL_CONFIG_DICT is not None:
          return _GLOBAL_CONFIG_DICT
      nemo_gym_config_dict_str_from_env = getenv(NEMO_GYM_CONFIG_DICT_ENV_VAR_NAME)
      if nemo_gym_config_dict_str_from_env:
          global_config_dict = OmegaConf.create(nemo_gym_config_dict_str_from_env)
  ```
- Tại sao không thể thay thế: Đây là cơ chế duy nhất giải quyết vòng đời config: (1) main proc → parse từ CLI + YAML files + env.yaml, (2) child proc → deserialize từ `NEMO_GYM_CONFIG_DICT` env var. Nó còn tự động assign host/port cho từng server (`validate_and_populate_defaults`, line ~241), detect "almost-server" misconfig, inject `ray_head_node_address`, và constrain package versions (`ray==`, `openai==`). Xóa đi thì mọi config validation và port allocation đều mất.

#### Core 3: SimpleServer.setup_webserver() + run_webserver() — FastAPI Lifecycle
- File: [`nemo_gym/server_utils.py:475-691`](../../nemo_gym/server_utils.py#L475)
- Evidence:
  ```python
  class SimpleServer(BaseServer):
      @abstractmethod
      def setup_webserver(self) -> FastAPI:
          pass
      @classmethod
      def run_webserver(cls) -> Optional[FastAPI]:
          ...
          app = server.setup_webserver()
          server.set_ulimit()
          server.prefix_server_logs()
          server.setup_exception_middleware(app)
  ```
- Tại sao không thể thay thế: `run_webserver()` là template method duy nhất orchestrate toàn bộ FastAPI startup: ulimit raise lên 65535 (critical cho 65k concurrent), middleware injection, uvicorn launch với multi-worker support. Ba base classes (`SimpleResourcesServer`, `SimpleResponsesAPIAgent`, model) đều inherit và chỉ cần override `setup_webserver()`. Xóa thì không có server nào khởi động được.

---

### Axis 2: Leverage Points

#### Leverage 1: Global aiohttp ClientSession Singleton
- File: [`nemo_gym/server_utils.py:74-145`](../../nemo_gym/server_utils.py#L74)
- LOC: ~70 dòng (singleton management + config)
- Evidence:
  ```python
  _GLOBAL_AIOHTTP_CLIENT: Union[None, ClientSession] = None

  def set_global_aiohttp_client(cfg) -> ClientSession:
      client_session = ClientSession(
          connector=TCPConnector(
              limit=cfg.global_aiohttp_connector_limit // num_workers,   # default 100*1024 total
              limit_per_host=cfg.global_aiohttp_connector_limit_per_host // num_workers,  # 1024/worker
          ),
          timeout=ClientTimeout(),
          cookie_jar=DummyCookieJar(),
      )
  ```
- Impact estimate: thay 1 dòng `limit=100*1024` → thay đổi 100% connection pool capacity cho toàn bộ requests trong hệ thống. Thay `DummyCookieJar()` bằng `CookieJar()` → session state bị corrupt (cookies sẽ bị merge across requests thay vì pass-through riêng lẻ). Đây là lý do trực tiếp tại sao không dùng httpx: httpcore O(n²) pool đã gây 40-phút hang tại 16k concurrent (Sep 2025 incident, documented tại `docs/infrastructure/engineering-notes/aiohttp-vs-httpx.md`).

#### Leverage 2: Cookie Propagation Chain trong simple_agent
- File: [`responses_api_agents/simple_agent/app.py:80-169`](../../responses_api_agents/simple_agent/app.py#L80)
- LOC: ~90 dòng (toàn bộ `responses()` method)
- Evidence:
  ```python
  model_server_cookies = None
  resources_server_cookies = request.cookies  # carry incoming session
  ...
  model_server_cookies = model_response.cookies
  resources_server_cookies = api_response.cookies
  # Propogate any extra cookies necessary for downstream verification
  for k, v in (*resources_server_cookies.items(), *model_server_cookies.items()):
      response.set_cookie(k, v)
  ```
- Impact estimate: Xóa 1 dòng `cookies=resources_server_cookies` trong POST đến resources server → stateful environments (e.g. multi-turn tool call environments dùng session state) mất tracking context, reward tính sai 100% với stateful benchmarks. Thêm `cookies=None` vào model server POST → model server không nhận session_id cookie, mỗi turn trở thành independent request.

#### Leverage 3: MAX_NUM_TRIES + request() retry loop
- File: [`nemo_gym/server_utils.py:149-219`](../../nemo_gym/server_utils.py#L149)
- LOC: ~55 dòng
- Evidence:
  ```python
  MAX_NUM_TRIES = 3  # "not intended to be changed"
  async def request(method, url, _internal=False, **kwargs):
      while True:
          try:
              return await client.request(...)
          except ServerDisconnectedError:
              await asyncio.sleep(0.5)
          except ClientOSError:
              await asyncio.sleep(0.5)
          except Exception as e:
              if num_tries >= MAX_NUM_TRIES:
                  raise e
  ```
- Impact estimate: thay `MAX_NUM_TRIES = 3` → `1` là 100% requests không retry khi server tạm overload (vd GPU inference timeout). `ServerDisconnectedError` và `ClientOSError` retry vô hạn (không bị giới hạn bởi `MAX_NUM_TRIES`) → nếu bỏ `await asyncio.sleep(0.5)` trong các case này thì CPU spin 100% trên socket errors.

---

### Axis 3: Extensibility & Scale

#### Ext 1: YAML Composition + ng_init_resources_server Template Generation
- File: [`nemo_gym/cli.py:724-848`](../../nemo_gym/cli.py#L724) (init_resources_server function) + [`resources_servers/example_single_tool_call/configs/example_single_tool_call.yaml`](../../resources_servers/example_single_tool_call/configs/example_single_tool_call.yaml)
- Evidence (YAML pattern):
  ```yaml
  example_single_tool_call:
    resources_servers:
      example_single_tool_call:
        entrypoint: app.py
        domain: agent
        verified: false
  example_single_tool_call_simple_agent:
    responses_api_agents:
      simple_agent:
        entrypoint: app.py
        resources_server: {type: resources_servers, name: example_single_tool_call}
  ```
- Tại sao là extensibility: `ng_init_resources_server` sinh ra toàn bộ scaffold (app.py từ template, test file, configs, requirements.txt, data/.gitignore) chỉ từ 1 CLI lệnh. Contributor chỉ cần implement `verify()` abstract method — mọi thứ khác (FastAPI setup, session middleware, port allocation, uvicorn launch) đã được base class handle. `_inherit_from` / `_copy` OmegaConf directives cho phép compose configs giữa nhiều server instances mà không duplicate YAML.

#### Ext 2: asyncio.Semaphore cho Concurrency Control tại Rollout Collection
- File: [`nemo_gym/rollout_collection.py:397-399`](../../nemo_gym/rollout_collection.py#L397)
- LOC: ~3 dòng pattern, áp dụng across toàn bộ rollout pipeline
- Evidence:
  ```python
  semaphore = Semaphore(config.num_samples_in_parallel)
  # "Querying with {config.num_samples_in_parallel} concurrent requests"
  ```
- Scale analysis: Theo CLAUDE.md, hệ thống phải handle 4k-65k concurrent requests. `global_aiohttp_connector_limit = 100 * 1024 = 102400` connections được phân chia per-worker (`// num_workers`). `set_ulimit(65535)` trong `SimpleServer.run_webserver()` nâng file descriptor limit tự động (`server_utils.py:556`). Resources servers có thể dùng thêm `asyncio.Semaphore` riêng để cap subprocess/external-tool concurrency (ví dụ `bird_sql/app.py:124`, `text_to_sql/app.py:214`). Pattern 3-layer: Semaphore (rollout client) → aiohttp pool (transport) → ulimit (OS FD) tạo backpressure hierarchy không làm crash server.

#### Ext 3: Isolated venv per Server — Zero-Dependency-Conflict Extensibility
- File: [`nemo_gym/cli.py:168-177`](../../nemo_gym/cli.py#L168)
- Evidence:
  ```python
  _cwd_path = Path.cwd() / _server_rel_path
  _cwd_is_server = (_cwd_path / "requirements.txt").exists() or (_cwd_path / "pyproject.toml").exists()
  dir_path = _cwd_path if _cwd_is_server else PARENT_DIR / _server_rel_path
  command = f"""{setup_env_command(dir_path, global_config_dict, top_level_path)} \
  && {NEMO_GYM_CONFIG_DICT_ENV_VAR_NAME}={escaped_config_dict_yaml_str} \
  python {str(entrypoint_fpath)}"""
  ```
- Tại sao là extensibility: Mỗi resources server / agent / model server chạy trong subprocess riêng với `.venv` riêng (managed by `uv`). Contributor có thể thêm bất kỳ Python dependency nào vào `requirements.txt` mà không conflict với core Gym hay server khác. `ng_test` tạo isolated venv per server, chạy `pytest` độc lập. Đây là lý do benchmark authors có thể integrate arbitrary 3rd-party libraries (compiler runtimes, SQL engines, etc) mà không lo dependency hell.

---

### Summary
- **Core:** Ba thành phần không thể thay thế là HeadServer (service registry), `get_global_config_dict()` (config lifecycle + port allocation), và `SimpleServer.run_webserver()` (FastAPI lifecycle template) — xóa bất kỳ một trong ba thì hệ thống không thể khởi động.
- **Leverage:** Singleton aiohttp ClientSession (quyết định toàn bộ connection capacity), cookie propagation chain trong simple_agent (state carrier duy nhất giữa stateful turns), và `request()` retry loop (resilience layer) — ba điểm này chiếm ~215 LOC nhưng chi phối 100% inter-server communication behavior.
- **Extensibility:** YAML + template generation (`ng_init`) hạ barrier-to-entry cho benchmark authors xuống mức chỉ implement `verify()`; isolated venv per server cho phép arbitrary dependencies; Semaphore + aiohttp pool + ulimit tạo backpressure hierarchy đủ mạnh cho 4k-65k concurrent requests.

## Phản biện (2026-05-24, Round 1+2)
- Round 1: 7.5/10 — 3 trục clear nhưng candidates verify thiếu, AC không quantify.
- Round 2: 9.3/10 — ≥2 entries per trục enforced, file paths verified, Summary section bắt buộc.
