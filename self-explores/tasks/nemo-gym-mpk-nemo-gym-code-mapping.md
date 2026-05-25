---
date: 2026-05-24
type: task-worklog
task: nemo-gym-mpk
title: "nemo-gym — Code Mapping (Truy vết thực tế)"
status: open
detailed_at: 2026-05-24 23:30
detail_score: ready-for-dev
tags: [system-design, code-mapping, nemo-gym, T3]
---

# nemo-gym — Code Mapping — Detailed Design

## 1. Objective
Map mỗi Core Component / Leverage Point từ T2 → file:line cụ thể (clickable). Trích ≥3 đoạn "code tinh hoa" 50-100 dòng + giải thích nguyên lý + impact estimate. 100% file:line là clickable markdown link.

## 2. Scope

**In-scope (hot zones bắt buộc scan):**
- [`nemo_gym/base_resources_server.py`](../../nemo_gym/base_resources_server.py)
- [`nemo_gym/base_responses_api_agent.py`](../../nemo_gym/base_responses_api_agent.py)
- [`nemo_gym/base_responses_api_model.py`](../../nemo_gym/base_responses_api_model.py)
- [`nemo_gym/server_utils.py`](../../nemo_gym/server_utils.py)
- [`nemo_gym/openai_utils.py`](../../nemo_gym/openai_utils.py)
- [`nemo_gym/dataset_orchestrator.py`](../../nemo_gym/dataset_orchestrator.py) + [`gitlab_utils.py`](../../nemo_gym/gitlab_utils.py) + [`hf_utils.py`](../../nemo_gym/hf_utils.py)
- [`nemo_gym/cli.py`](../../nemo_gym/cli.py)
- [`nemo_gym/config_types.py`](../../nemo_gym/config_types.py)
- [`nemo_gym/global_config.py`](../../nemo_gym/global_config.py)
- [`responses_api_agents/simple_agent/app.py`](../../responses_api_agents/simple_agent/app.py)
- [`resources_servers/example_single_tool_call/app.py`](../../resources_servers/example_single_tool_call/app.py)
- [`docs/infrastructure/engineering-notes/aiohttp-vs-httpx.md`](../../docs/infrastructure/engineering-notes/aiohttp-vs-httpx.md)

**Out-of-scope:**
- KHÔNG re-explain code line-by-line (đó là tutorial).
- KHÔNG phân tích test files (`tests/`).
- KHÔNG đụng `benchmarks/` hoặc `results/`.

## 3. Input / Output

**Input:**
- Findings từ T2 worklog ([`nemo-gym-ir8-*.md`](nemo-gym-ir8-nemo-gym-strategic-evaluation.md)).
- Code files ở hot zones (xem Scope).

**Output:**
- ≥3 "Code Tinh Hoa" entries theo format:
  ```markdown
  ### Leverage Point: {tên}
  - File: [`path:LINE`](../../path#LLINE)
  - LOC: {x}
  - Nguyên lý: {SOLID / GoF / Domain-specific}
  - Code tinh hoa (≤100 dòng): ```python ... ```
  - Tại sao tinh hoa: {TƯ DUY thiết kế}
  - Thay 1 dòng → impact: {ước tính %}
  ```
- ≥1 entry từ aiohttp/server_utils, ≥1 từ base_*.py, ≥1 từ cli.py Hydra.

## 4. Dependencies
- Beads: blocked-by T2 (`nemo-gym-ir8`).
- Tools: `grep`, `sed`, `awk` để trích snippets.

## 5. Flow xử lý

### Step 1: Verify hot zones (~3 phút)
```bash
for f in nemo_gym/base_resources_server.py nemo_gym/server_utils.py nemo_gym/cli.py; do
  [ -f "$f" ] && wc -l "$f" || echo "MISSING: $f"
done
ls docs/infrastructure/engineering-notes/aiohttp-vs-httpx.md
```
**Verify:** Tất cả file tồn tại; ghi LOC.

### Step 2: Đọc engineering note đầu tiên (~5 phút)
Đọc [`aiohttp-vs-httpx.md`](../../docs/infrastructure/engineering-notes/aiohttp-vs-httpx.md) — đây là context cho Leverage Infra.
**Verify:** Hiểu O(n²) connection pool bug + httpx hangs.

### Step 3: Trích "Code Tinh Hoa" #1 — aiohttp singleton (~15 phút)
```bash
grep -n "ClientSession\|get_session\|connector\|TCPConnector" nemo_gym/server_utils.py
sed -n '1,200p' nemo_gym/server_utils.py
```
Trích 50-100 dòng singleton + retry pattern. Giải thích:
- **Nguyên lý:** Singleton + Connection Pool + Bulkhead (Semaphore).
- **Tại sao tinh hoa:** Single global session = 1 DNS cache + 1 TCP pool cho cả app. Stress test 16k+ requests stable (engineering note evidence).
- **Impact:** Thay `ClientSession(connector=...)` → ảnh hưởng 100% HTTP requests.

### Step 4: Trích "Code Tinh Hoa" #2 — verify() abstract (~15 phút)
```bash
grep -n "abstractmethod\|verify\|VerifyResponse" nemo_gym/base_resources_server.py
sed -n '1,150p' nemo_gym/base_resources_server.py
```
Giải thích Template Method + extensibility.

### Step 5: Trích "Code Tinh Hoa" #3 — Hydra cli composition (~15 phút)
```bash
grep -n "hydra\|compose\|@hydra.main\|OmegaConf" nemo_gym/cli.py | head -20
sed -n '1,150p' nemo_gym/cli.py
```
Giải thích Configuration-as-Code + cascading override.

### Step 6: Format + verify clickable (~7 phút)
Mọi `path:line` phải có markdown link wrap.
```bash
grep -E '\`[a-z_/]+\.py:[0-9]+\`' self-explores/tasks/nemo-gym-mpk-*.md | grep -v '\](' && echo "FOUND_PLAIN_TEXT_REFS"
```
**Verify:** Command trên trả 0 hit (không có plain text refs).

## 6. Edge Cases & Error Handling
| Case | Trigger | Expected | Recovery |
|---|---|---|---|
| File >1000 LOC | wc -l > 1000 | Trích range relevant + ghi "(file dài N LOC)" | Skip non-relevant ranges |
| Abstract method body chỉ là `pass` | grep `abstractmethod` rồi sed thấy body rỗng | Trích cả docstring + subclass cụ thể | Tham chiếu `example_single_tool_call` |
| Hydra logic phân tán (decorator vs function) | grep nhiều hit | Trích toàn bộ entry function | Theo call chain |
| Engineering note đã obsolete (httpx fix bug n²) | note có "DEPRECATED" header | Vẫn dùng làm historical context | Note rõ trong section "Historical context" |

## 7. Acceptance Criteria
- **Happy 1:** Given T2 closed với 6 findings, When task chạy, Then ≥3 code-tinh-hoa entries (≥1 mỗi 3 zones) với 100% clickable refs.
- **Happy 2:** Given file `nemo_gym/server_utils.py` chứa aiohttp singleton, When trích, Then snippet 50-100 dòng có decorator + class + method chính.
- **Negative:** Given grep `path:line` text plain trong worklog, When verify command chạy, Then 0 hit (không còn plain text refs).

## 8. Technical Notes
- Markdown link relative: từ `self-explores/tasks/*.md` → `../../nemo_gym/*.py`.
- VSCode: Cmd+Click trên link mở file tại line đúng.
- GitHub render: `#L42-L50` hiển thị block highlighted.
- Engineering note path: [`docs/infrastructure/engineering-notes/aiohttp-vs-httpx.md`](../../docs/infrastructure/engineering-notes/aiohttp-vs-httpx.md).

## 9. Risks
- **R1:** Trích snippet quá dài → fatigue cho reader. *Mitigation:* Strict 50-100 LOC range, dùng ellipsis cho non-relevant lines.
- **R2:** Link broken sau refactor. *Mitigation:* Verify mỗi link bằng `ls path && grep -c '' path | awk '{if ($1 < line) print "LINE_OOB"}'`.
- **R3:** Plain text refs lọt qua (vi phạm AC). *Mitigation:* Grep verify step trước khi mark task done.

## Worklog

### Leverage Point: Global aiohttp Singleton + Retry Bulkhead
- File: [`nemo_gym/server_utils.py:74`](../../nemo_gym/server_utils.py#L74)
- LOC: 760 dòng trong file
- Nguyên lý: Singleton (GoF Creational) + Bulkhead (Resilience Pattern) + Connection Pool
- Code tinh hoa (≤100 dòng):
  ```python
  _GLOBAL_AIOHTTP_CLIENT: Union[None, ClientSession] = None
  _GLOBAL_AIOHTTP_CLIENT_REQUEST_DEBUG: bool = False


  class GlobalAIOHTTPAsyncClientConfig(BaseModel):
      global_aiohttp_connector_limit: int = 100 * 1024
      global_aiohttp_connector_limit_per_host: int = 1024

      global_aiohttp_client_request_debug: bool = False


  def get_global_aiohttp_client(
      global_config_dict_parser_config: Optional[GlobalConfigDictParserConfig] = None,
      global_config_dict_parser_cls: Type[GlobalConfigDictParser] = GlobalConfigDictParser,
  ) -> ClientSession:  # pragma: no cover
      global _GLOBAL_AIOHTTP_CLIENT

      if _GLOBAL_AIOHTTP_CLIENT is not None:
          return _GLOBAL_AIOHTTP_CLIENT

      global_config_dict = get_global_config_dict(
          global_config_dict_parser_config=global_config_dict_parser_config,
          global_config_dict_parser_cls=global_config_dict_parser_cls,
      )
      cfg = GlobalAIOHTTPAsyncClientConfig.model_validate(global_config_dict)

      return set_global_aiohttp_client(cfg)


  def set_global_aiohttp_client(cfg: GlobalAIOHTTPAsyncClientConfig) -> ClientSession:  # pragma: no cover
      assert not is_global_aiohttp_client_setup(), (
          "There is already a global aiohttp client setup. Please refactor your code or call `global_aiohttp_client_exit` if you want to explicitly re-make the client!"
      )

      num_workers = get_nemo_gym_fastapi_num_workers()
      client_session = ClientSession(
          connector=TCPConnector(
              limit=cfg.global_aiohttp_connector_limit // num_workers,
              limit_per_host=cfg.global_aiohttp_connector_limit_per_host // num_workers,
          ),
          timeout=ClientTimeout(),
          cookie_jar=DummyCookieJar(),
      )

      global _GLOBAL_AIOHTTP_CLIENT
      _GLOBAL_AIOHTTP_CLIENT = client_session

      global _GLOBAL_AIOHTTP_CLIENT_REQUEST_DEBUG
      _GLOBAL_AIOHTTP_CLIENT_REQUEST_DEBUG = cfg.global_aiohttp_client_request_debug

      return _GLOBAL_AIOHTTP_CLIENT


  atexit.register(global_aiohttp_client_exit)


  MAX_NUM_TRIES = 3

  async def request(
      method: str, url: str, _internal: bool = False, **kwargs: Unpack[_RequestOptions]
  ) -> ClientResponse:  # pragma: no cover
      if kwargs.get("json"):
          kwargs["data"] = orjson.dumps(kwargs.pop("json"))
          kwargs.setdefault("headers", dict())
          kwargs["headers"]["Content-Type"] = "application/json"

      client = get_global_aiohttp_client()
      num_tries = 1
      retries = 0
      retry_start = time.monotonic()
      while True:
          try:
              return await client.request(method=method, url=url, **kwargs)
          except ServerDisconnectedError:
              global _NUM_SERVER_DISCONNECTED_ERROR
              _NUM_SERVER_DISCONNECTED_ERROR += 1
              retries += 1
              if _NUM_SERVER_DISCONNECTED_ERROR % DISCONNECTED_CLIENT_OS_PRINT_INTERVAL == 0:
                  print(
                      f"[request_retry url={url} error=ServerDisconnectedError retry={retries} elapsed_s={time.monotonic() - retry_start:.1f}] "
                      f"Hit {_NUM_SERVER_DISCONNECTED_ERROR} global `ServerDisconnectedError` while querying {url}.\n{DISCONNECTED_CLIENT_OS_HELP_TEXT}",
                      flush=True,
                  )
              await asyncio.sleep(0.5)
          except Exception as e:
              if not _internal:
                  if num_tries >= MAX_NUM_TRIES:
                      raise e
                  num_tries += 1
              await asyncio.sleep(0.5)
  ```
- Tại sao tinh hoa: Đây là quyết định kiến trúc được đúc kết từ production incident thực tế. Engineering note ghi lại rằng httpx/httpcore có O(n²) connection pool assignment — với 16,000 concurrent requests, hệ thống bị treo 40 phút không xử lý được request nào. Thiết kế này giải quyết vấn đề theo ba tầng: (1) **Singleton** — toàn bộ app chỉ có 1 `ClientSession`, chia sẻ 1 DNS cache + 1 TCP pool, loại bỏ overhead tạo connection mới; (2) **Bulkhead** — `limit // num_workers` phân phối tài nguyên đều giữa các uvicorn worker, tránh 1 worker chiếm hết pool; (3) **atexit cleanup** — `atexit.register(global_aiohttp_client_exit)` đảm bảo graceful shutdown ngay cả khi process bị kill. Pattern `orjson.dumps` thay vì JSON default của aiohttp thể hiện tư duy "every microsecond counts" ở hot path.
- Thay 1 dòng → impact: Thay `TCPConnector(limit=..., limit_per_host=...)` bằng `TCPConnector()` (default limit=100) → **100% requests timeout** khi concurrency > 100, toàn bộ rollout collection tê liệt.

---

### Leverage Point: SimpleResourcesServer — Template Method + Abstract verify()
- File: [`nemo_gym/base_resources_server.py:57`](../../nemo_gym/base_resources_server.py#L57)
- LOC: 89 dòng trong file
- Nguyên lý: Template Method (GoF Behavioral) + Interface Segregation (SOLID ISP) + Open/Closed Principle (SOLID OCP)
- Code tinh hoa (≤100 dòng):
  ```python
  class BaseVerifyRequest(BaseRunRequest):
      response: NeMoGymResponse


  class BaseVerifyResponse(BaseVerifyRequest):
      reward: float


  class BaseSeedSessionRequest(BaseModel):
      pass


  class BaseSeedSessionResponse(BaseModel):
      pass


  class SimpleResourcesServer(BaseResourcesServer, AggregateMetricsMixin, SimpleServer):
      config: BaseResourcesServerConfig

      def setup_webserver(self) -> FastAPI:
          app = FastAPI()

          self.setup_session_middleware(app)

          app.post("/seed_session")(self.seed_session)
          app.post("/verify")(self.verify)
          app.post("/aggregate_metrics")(self.aggregate_metrics)

          return app

      async def seed_session(self, body: BaseSeedSessionRequest) -> BaseSeedSessionResponse:
          return BaseSeedSessionResponse()

      @abstractmethod
      async def verify(self, body: BaseVerifyRequest) -> BaseVerifyResponse:
          pass

      async def aggregate_metrics(self, body: AggregateMetricsRequest) -> AggregateMetrics:
          """Compute aggregate metrics from verify responses.

          RewardProfiler provides baseline stats. Override compute_metrics() and/or
          get_key_metrics() for benchmark-specific customization.
          """
          return compute_aggregate_metrics(
              body.verify_responses,
              compute_metrics_fn=self.compute_metrics,
              get_key_metrics_fn=self.get_key_metrics,
          )
  ```
- Tại sao tinh hoa: File chỉ có 89 LOC nhưng định nghĩa **toàn bộ extensibility contract** cho mọi benchmark trong hệ thống. Tư duy thiết kế ở đây là "frozen skeleton, hot spots". Skeleton (route wiring `/seed_session`, `/verify`, `/aggregate_metrics`, session middleware) hoàn toàn frozen — developer không cần biết FastAPI routing, middleware ordering, hay session management. Hot spot duy nhất là `@abstractmethod verify()` — đây là điểm duy nhất subclass PHẢI implement. `BaseVerifyResponse` kế thừa `BaseVerifyRequest` kế thừa `BaseRunRequest` tạo ra một chuỗi type-safe: response luôn mang theo cả `responses_create_params` lẫn `response` gốc, đảm bảo traceability cho RL training. `seed_session` có default implementation trả về empty response — không bắt buộc override, thể hiện ISP (subclass chỉ implement những gì cần thiết). Multiple inheritance `(BaseResourcesServer, AggregateMetricsMixin, SimpleServer)` dùng Mixin pattern để compose behavior mà không phải copy code.
- Thay 1 dòng → impact: Xóa `self.setup_session_middleware(app)` → **100% stateful environments mất session tracking**, cookies không propagate qua multi-turn agent calls, toàn bộ multi-step benchmarks bị broken.

---

### Leverage Point: GlobalConfigDictParser.parse() — Hydra + OmegaConf Cascading Composition
- File: [`nemo_gym/global_config.py:385`](../../nemo_gym/global_config.py#L385)
- LOC: 797 dòng trong file
- Nguyên lý: Configuration-as-Code + Chain of Responsibility (GoF Behavioral) + Single Source of Truth (DRY)
- Code tinh hoa (≤100 dòng):
  ```python
  def parse(self, parse_config: Optional[GlobalConfigDictParserConfig] = None) -> DictConfig:
      if parse_config is None:
          parse_config = GlobalConfigDictParserConfig()

      global_config_dict = (
          DictConfig(dict()) if parse_config.skip_load_from_cli else self.parse_global_config_dict_from_cli()
      )

      # Command line overrides function input.
      initial_global_config_dict = OmegaConf.create(parse_config.initial_global_config_dict or dict())
      global_config_dict: DictConfig = OmegaConf.merge(initial_global_config_dict, global_config_dict)

      # Load the env.yaml config.
      if parse_config.dotenv_path:
          dotenv_path = parse_config.dotenv_path
      else:
          cwd_env_yaml = Path.cwd() / "env.yaml"
          dotenv_path = cwd_env_yaml if cwd_env_yaml.exists() else PARENT_DIR / "env.yaml"

      dotenv_extra_config = DictConfig({})
      if dotenv_path.exists() and not parse_config.skip_load_from_dotenv:
          dotenv_extra_config = OmegaConf.load(dotenv_path)

      merged_config_for_config_paths = OmegaConf.merge(dotenv_extra_config, global_config_dict)
      ta = TypeAdapter(List[str])
      config_paths = merged_config_for_config_paths.get(CONFIG_PATHS_KEY_NAME) or []
      config_paths = ta.validate_python(config_paths)

      config_paths, extra_configs = self.load_extra_config_paths(config_paths)

      # Dot env overrides previous configs
      extra_configs.append(dotenv_extra_config)

      # global_config_dict is the last config arg here since we want command line args to override everything else.
      global_config_dict = OmegaConf.merge(*extra_configs, global_config_dict)

      # Update the config paths after postprocessing
      if config_paths:
          with open_dict(global_config_dict):
              global_config_dict[CONFIG_PATHS_KEY_NAME] = config_paths

      self._recursively_swap_keys(global_config_dict)

      server_instance_configs = self.filter_for_server_instance_configs(global_config_dict)

      with open_dict(global_config_dict):
          use_absolute_ip = global_config_dict.setdefault(USE_ABSOLUTE_IP, False)
      if use_absolute_ip:
          default_host = gethostbyname(gethostname())
      else:
          default_host = global_config_dict.get(DEFAULT_HOST_KEY_NAME) or "127.0.0.1"

      head_server_config = global_config_dict.get(HEAD_SERVER_KEY_NAME, {})
      head_server_port = head_server_config.get("port", DEFAULT_HEAD_SERVER_PORT)
      initial_disallowed_ports = [head_server_port] if head_server_port is not None else []

      with open_dict(global_config_dict):
          port_range_low = global_config_dict.setdefault(PORT_RANGE_LOW_KEY_NAME, 10_001)
          port_range_high = global_config_dict.setdefault(PORT_RANGE_HIGH_KEY_NAME, 20_000)

      disallowed_ports = self.validate_and_populate_defaults(
          server_instance_configs=server_instance_configs,
          default_host=default_host,
          initial_disallowed_ports=initial_disallowed_ports,
          port_range_low=port_range_low,
          port_range_high=port_range_high,
      )

      with open_dict(global_config_dict):
          if not global_config_dict.get(HEAD_SERVER_KEY_NAME):
              global_config_dict[HEAD_SERVER_KEY_NAME] = {
                  "host": default_host,
                  "port": DEFAULT_HEAD_SERVER_PORT,
              }
          global_config_dict[DISALLOWED_PORTS_KEY_NAME] = disallowed_ports
          global_config_dict[HEAD_SERVER_DEPS_KEY_NAME] = [
              f"ray[default]=={ray_version}",
              f"openai=={openai_version}",
          ]
          global_config_dict[PYTHON_VERSION_KEY_NAME] = python_version()
          global_config_dict.setdefault(SKIP_VENV_IF_PRESENT_KEY_NAME, False)
          global_config_dict.setdefault(DRY_RUN_KEY_NAME, False)

      return global_config_dict
  ```
- Tại sao tinh hoa: Đây là "configuration bootstrap" của toàn bộ hệ thống — được gọi đúng 1 lần duy nhất (Singleton pattern ở `get_global_config_dict`), sau đó cache lại. Tư duy thiết kế là **explicit priority cascade**: `yaml_files < env.yaml < CLI args` — thứ tự merge được encode trực tiếp vào code (`OmegaConf.merge(*extra_configs, global_config_dict)` — CLI dict đứng cuối nên highest priority). `load_extra_config_paths` dùng loop mutation (`for config_path in config_paths: config_paths.append(...)`) để xử lý transitive includes — một YAML có thể include YAML khác, và được expand lazily trong cùng một pass. Sau merge, `_recursively_swap_keys` xử lý `_inherit_from` và `_copy` directives — đây là custom resolution layer nằm trên OmegaConf, cho phép server configs tái sử dụng lẫn nhau mà không cần copy-paste. Cuối cùng, `validate_and_populate_defaults` auto-assign host/port cho mọi server — developer không bao giờ cần hardcode port, hệ thống tự phân phối từ `port_range_low` đến `port_range_high` tránh collision.
- Thay 1 dòng → impact: Đổi `global_config_dict = OmegaConf.merge(*extra_configs, global_config_dict)` thành `global_config_dict = OmegaConf.merge(global_config_dict, *extra_configs)` → **CLI overrides bị env.yaml override ngược lại**, mọi `+key=value` từ command line bị ignore → 100% CLI-driven workflows bị broken, không còn khả năng override config từ terminal.

## Phản biện (2026-05-24, Round 1+2)
- Round 1: 7.5/10 — hot zones liệt kê nhưng format mơ hồ, quantity unclear.
- Round 2: 9.4/10 — Format strict, ≥3 entries enforced, 100% clickable enforce + verify command.
