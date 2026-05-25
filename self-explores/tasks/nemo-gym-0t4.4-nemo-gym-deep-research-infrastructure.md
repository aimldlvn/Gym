---
date: 2026-05-24
type: task-worklog
task: nemo-gym-0t4.4
parent: nemo-gym-0t4
title: "nemo-gym — T4.4 Deep Research: Infrastructure Layer"
status: open
detailed_at: 2026-05-24 23:30
detail_score: ready-for-dev
tags: [system-design, deep-research, infrastructure, nemo-gym]
---

# nemo-gym — T4.4 Deep Research: Infrastructure Layer — Detailed Design

## 1. Objective
Phân tích Infrastructure layer (aiohttp + Ray + lifecycle) — ≥3 decisions full 4 điểm + 1 dedicated decision cho aiohttp vs httpx + 1 dedicated cho Ray RAY_TMPDIR gotcha.

## 2. Scope

**In-scope:**
- [`nemo_gym/server_utils.py`](../../nemo_gym/server_utils.py) — aiohttp singleton + ServerClient
- [`nemo_gym/openai_utils.py`](../../nemo_gym/openai_utils.py)
- [`docs/infrastructure/engineering-notes/aiohttp-vs-httpx.md`](../../docs/infrastructure/engineering-notes/aiohttp-vs-httpx.md) — **BẮT BUỘC ĐỌC ĐẦU**
- [`resources_servers/tavily_search/app.py`](../../resources_servers/tavily_search/app.py) — TavilySearchAIOHTTPClient adapter
- [`nemo_gym/cli.py`](../../nemo_gym/cli.py) — Ray cluster init
- [`nemo_gym/global_config.py`](../../nemo_gym/global_config.py) — singleton lifecycle
- External tool auto-install: `setup_<tool>.py` modules
- `pytest_configure` hooks trong conftest.py files

**Out-of-scope:**
- KHÔNG data/config (T4.1).
- KHÔNG verify() (T4.2).
- KHÔNG FastAPI endpoint shape (T4.3).

## 3. Input / Output

**Input:** Hot-zone files + engineering note.

**Output:** ≥3 decisions với 4 điểm; 1 aiohttp-vs-httpx dedicated; 1 Ray RAY_TMPDIR dedicated.

## 4. Dependencies
- Beads: blocked-by T2.
- Parent: `nemo-gym-0t4`.

## 5. Flow xử lý

### Step 1: Đọc engineering note (~10 phút) **[BẮT BUỘC ĐẦU TIÊN]**
```bash
cat docs/infrastructure/engineering-notes/aiohttp-vs-httpx.md
```
**Verify:** Hiểu O(n²) connection pool bug + httpx hangs at 16k+ requests + adapter pattern.

### Step 2: Decision 1 — aiohttp singleton + Connection Pool (~12 phút) **[DEDICATED]**
**Câu hỏi:** Sao aiohttp thay vì httpx?
```bash
grep -n "ClientSession\|TCPConnector\|aiohttp" nemo_gym/server_utils.py | head
grep -rn "httpx" nemo_gym/ resources_servers/ 2>/dev/null | head  # phải hầu như 0 hit, chỉ trong adapter pattern
```
- **Principle:** Singleton + Connection Pool + Bulkhead (Semaphore).
- **Rationale:** httpx có O(n²) connection pool lookup bug at high concurrency (engineering note evidence). aiohttp ClientSession đơn giản và scale tốt 16k+.
- **Historical:** Commit refactor httpx → aiohttp (`git log --oneline -- nemo_gym/server_utils.py | head -10`).
- **Industry:** [aiohttp docs - Client](https://docs.aiohttp.org/en/stable/client.html), [httpx issue tracker](https://github.com/encode/httpx/issues) (search "connection pool slow"), [TavilySearchAIOHTTPClient adapter](../../resources_servers/tavily_search/app.py).

### Step 3: Decision 2 — Ray cluster init + RAY_TMPDIR gotcha (~12 phút) **[DEDICATED]**
**Câu hỏi:** Sao RAY_TMPDIR=/tmp required?
```bash
grep -rn "ray.init\|RAY_TMPDIR" nemo_gym/ scripts/ 2>/dev/null | head
```
- **Principle:** Process supervision + Inter-process communication (AF_UNIX).
- **Rationale:** Ray dùng AF_UNIX socket — Linux socket path max 107 bytes. Lustre/Network FS có path dài → exceed limit. Force `/tmp` để bypass.
- **Historical:** Khi nào gotcha document trong CLAUDE.md (git log -- CLAUDE.md | grep -i ray).
- **Industry:** [Ray Documentation - Configuring Logging](https://docs.ray.io/en/latest/ray-observability/user-guides/configure-logging.html), [Linux UNIX(7) socket man page](https://man7.org/linux/man-pages/man7/unix.7.html), [POSIX socket path limits](https://stackoverflow.com/questions/34829600).

### Step 4: Decision 3 — venv isolation per resources_server (~10 phút)
**Câu hỏi:** Sao venv per-server thay vì single venv với tox/nox?
```bash
grep -rn "ng_test\|venv\|virtualenv" nemo_gym/*.py | head
ls resources_servers/example_single_tool_call/requirements.txt
```
- **Principle:** Process isolation + Dependency conflict prevention.
- **Rationale:** Mỗi benchmark có dep stack riêng (vd: bigcodebench cần subprocess + 100+ pkgs, browsing cần playwright). Single venv = dependency hell.
- **Industry:** [tox docs](https://tox.wiki/), [Nix-style isolation](https://nixos.org/), [Docker per-service pattern](https://docs.docker.com/get-started/overview/).

### Step 5: Decision 4 (optional) — Auto-install hooks (~8 phút)
**Câu hỏi:** Sao external tool auto-install qua `model_post_init` thay vì doc requirement?
- **Principle:** Convention over Configuration + Self-bootstrapping.
- **Industry:** [Kubernetes init containers](https://kubernetes.io/docs/concepts/workloads/pods/init-containers/), [Docker multi-stage builds](https://docs.docker.com/build/building/multi-stage/).

## 6. Edge Cases & Error Handling
| Case | Trigger | Expected | Recovery |
|---|---|---|---|
| Engineering note thiếu (file removed) | ls fail | Abort task, escalate (note quan trọng quá) | Find via `git log --all -- aiohttp-vs-httpx.md` |
| httpx vẫn còn dùng ở đâu đó | grep hit | Document "Edge: httpx used in {file} (legacy)" | Mention trong worklog |
| Ray version mismatch (ray.init API changed) | API call fail | Note version từ requirements | Adapt example |
| RAY_TMPDIR đã set ở env | echo $RAY_TMPDIR non-empty | Document đó là pre-condition | OK |

## 7. Acceptance Criteria
- **Happy:** Given engineering note đã đọc, When task chạy, Then ≥3 decisions với 4 điểm + aiohttp-vs-httpx decision riêng + RAY_TMPDIR decision riêng + mỗi decision có industry URL.
- **Negative:** Given httpx import found > 5 places, When scan, Then decision aiohttp được reframe thành "migration in progress" + count tracking.

## 8. Technical Notes
- aiohttp ClientSession lifecycle: closed → broken; phải reuse single instance.
- Ray socket path: `/tmp/ray_session_*/sockets/raylet`. Path < 107 bytes mới fit.
- venv per resources_server: `ng_test` creates if not exists. Speed up bằng `skip_venv_if_present`.
- Linux 107-byte limit: `sys/un.h` SUN_LEN macro.

## 9. Risks
- **R1:** Engineering note quá ngắn để extract industry context. *Mitigation:* Đào thêm git history + author commits.
- **R2:** Ray gotcha documentation thiếu, chỉ có CLAUDE.md mention. *Mitigation:* Reproduce qua thử nghiệm: create dir tên dài + ray.init() để confirm.

## Worklog

**Trạng thái:** completed  
**Ngày thực hiện:** 2026-05-25  
**Files đã đọc:** `docs/infrastructure/engineering-notes/aiohttp-vs-httpx.md`, `nemo_gym/server_utils.py`, `nemo_gym/cli.py`, `nemo_gym/global_config.py`, `resources_servers/tavily_search/app.py`, `resources_servers/gdpval/setup_libreoffice.py`

---

## Decision 1 (DEDICATED): aiohttp Singleton + Connection Pool thay vì httpx

**File tham chiếu:**
- [`nemo_gym/server_utils.py:74-145`](../../nemo_gym/server_utils.py) — `_GLOBAL_AIOHTTP_CLIENT` singleton + `set_global_aiohttp_client()`
- [`docs/infrastructure/engineering-notes/aiohttp-vs-httpx.md`](../../docs/infrastructure/engineering-notes/aiohttp-vs-httpx.md) — **engineering note gốc** (Sep 17, 2025 incident)
- [`resources_servers/tavily_search/app.py:133-188`](../../resources_servers/tavily_search/app.py) — `TavilySearchAIOHTTPClient` adapter pattern

### 1.1 Nguyên lý (Principle)

Ba nguyên lý phối hợp:

**Singleton Session** — `ClientSession` của aiohttp phải được tạo 1 lần và tái dùng suốt lifetime của process. Mỗi session là một object quản lý connection pool + cookie jar + SSL context; tạo lại mỗi request gây thêm overhead O(1) khởi tạo nhân với số lượng request.

**Connection Pooling (Bulkhead Pattern)** — `TCPConnector(limit=100*1024, limit_per_host=1024)` phân vùng tài nguyên socket. Bulkhead pattern (từ Michael Nygard, *Release It!* 2007) cô lập failure domain: nếu một downstream endpoint bị chậm, nó chỉ tiêu thụ `limit_per_host=1024` connections thay vì toàn bộ pool.

**Adaptive Pool per Worker** — khi Uvicorn chạy multi-worker (`num_workers > 1`), pool được chia đều: `limit // num_workers`. Code: `server_utils.py:112` — `TCPConnector(limit=cfg.global_aiohttp_connector_limit // num_workers, ...)`. Đây là **worker-aware resource partitioning** để tránh oversubscription ở tầng OS.

### 1.2 Tại sao KHÔNG đơn giản (Why Not Simple)

**Không thể dùng httpx vì O(n²) bug trong httpcore `_assign_requests_to_connections`:**

Engineering note ghi lại chi tiết call stack:
```
OpenAI client → httpx._client:1014 → httpx._transports.default:250
→ httpcore._async.connection_pool:228 _assign_requests_to_connections()
  → loop connections (L284)
    → loop queued_requests (L303)  ← O(n²) total
```

Khi NeMo Gym nhận 16,000 concurrent requests (Sep 17, 2025, inspired by DeepSeek R1 Nature paper, 16 off-policy steps × 1,000 rollouts), **system treo 40 phút** trước khi xử lý request đầu tiên. httpcore duyệt từng request để gán vào connection — với n=16,000 thì O(n²) = 256,000,000 iteration trong event loop, block toàn bộ asyncio.

Giải pháp đơn giản nhất (giữ httpx, thêm semaphore) KHÔNG đủ vì bottleneck là trong connection pool management, không phải ở concurrency cap. Semaphore chỉ giới hạn in-flight requests, không fix O(n²) iteration.

**Không thể tạo ClientSession per-request:** aiohttp document cảnh báo `ClientSession` phải được đóng, và việc tạo TCP connector mới mỗi request gây port exhaustion và TIME_WAIT storm ở OS networking stack.

### 1.3 Historical Context

- **Commit `6409cc3b`** (`Fix aiohttp connection limit under FastAPI/Uvicorn workers > 1`): phát hiện rằng khi workers > 1, mỗi worker fork tạo 1 session riêng nhưng limit không được scale down → oversubscription. Fix: divide limit by `num_workers`.
- **Commit `d8dd34e0`** (`feat: Misc infra`): migration ban đầu từ httpx sang aiohttp.
- **Incident Sep 17, 2025**: DeepSeek R1 Nature paper release → 16k concurrent requests → 40-minute hang. Xem engineering note đầy đủ tại [`docs/infrastructure/engineering-notes/aiohttp-vs-httpx.md`](../../docs/infrastructure/engineering-notes/aiohttp-vs-httpx.md).

### 1.4 Industry URL

- **Engineering note gốc:** [`docs/infrastructure/engineering-notes/aiohttp-vs-httpx.md`](../../docs/infrastructure/engineering-notes/aiohttp-vs-httpx.md)
- **httpcore issue:** https://github.com/encode/httpx/issues/3215#issuecomment-2220795088 — community validation của O(n²) problem
- **openai-python issue #1596:** https://github.com/openai/openai-python/issues/1596 — người dùng báo AsyncOpenAI hang ở concurrency > 32
- **aiohttp TCPConnector docs:** https://docs.aiohttp.org/en/stable/client_reference.html#tcpconnector — `limit` và `limit_per_host` parameters
- **Adapter pattern (TavilySearch):** [`resources_servers/tavily_search/app.py:133`](../../resources_servers/tavily_search/app.py) — `TavilySearchAIOHTTPClient.from_httpx_AsyncClient()` wraps httpx interface bằng aiohttp transport

---

## Decision 2 (DEDICATED): Ray Cluster Init + RAY_TMPDIR=/tmp Gotcha

**File tham chiếu:**
- [`nemo_gym/server_utils.py:395-442`](../../nemo_gym/server_utils.py) — `initialize_ray()` + `maybe_ray_cluster_exit()`
- [`nemo_gym/cli.py:124-133`](../../nemo_gym/cli.py) — `RunHelper.start()` calls `initialize_ray()` trước khi spawn worker processes

### 2.1 Nguyên lý (Principle)

**Inter-Process Communication via AF_UNIX Sockets** — Ray dùng Unix Domain Sockets (UDS) để các components giao tiếp trong cùng host: Raylet daemon, GCS (Global Control Store), worker processes. UDS có path như `/tmp/ray/session_20250917_123456_789012_1234/sockets/raylet`.

**Single Cluster per Run** — `initialize_ray()` có flag `_NEMO_GYM_STARTED_RAY_CLUSTER: bool` để đảm bảo chỉ main process khởi động cluster; child workers (Uvicorn forks) connect đến địa chỉ đã có qua `ray_head_node_address` trong global config. Đây là **ownership tracking**: process nào start thì process đó shutdown (`atexit.register(maybe_ray_cluster_exit)`).

### 2.2 Tại sao KHÔNG đơn giản (Why Not Simple)

**Root cause: Linux AF_UNIX socket pathname limit = 107 bytes (108 bytes - null terminator)**

Từ Linux `sys/un.h`:
```c
struct sockaddr_un {
    sa_family_t sun_family;    /* AF_UNIX */
    char        sun_path[108]; /* pathname */
};
```

`sun_path` là 108 bytes — 1 byte null terminator = **107 bytes usable**. Đây là hard limit từ kernel, không thể cấu hình.

Khi Ray tạo session directory mặc định dựa trên `os.getcwd()` hoặc `$HOME`, trên HPC clusters với Lustre filesystem, CWD có dạng:
```
/lustre/fsw/portfolios/llmservice/projects/llmservice_nemo_llm/users/username/experiments/2025/09/17/nemo-gym-experiments/run-001
```

Path đến socket:
```
{cwd}/ray_session_20250917_XXXXXX/sockets/raylet
```

Tổng có thể vượt 107 bytes → `OSError: [Errno 91] Protocol not available` hoặc silent failure trong Ray startup.

**Fix:** Set `RAY_TMPDIR=/tmp` trước khi chạy → Ray dùng `/tmp/ray/session_...` thay vì `{cwd}/ray_...` → path ngắn hơn nhiều, luôn fit trong 107 bytes.

Lưu ý thêm từ CLAUDE.md: `ng_test` tạo isolated venvs, `os.environ` changes trong Python không propagate sang subprocess — phải set `RAY_TMPDIR=/tmp` externally: `RAY_TMPDIR=/tmp ng_test +entrypoint=...`

### 2.3 Historical Context

- Gotcha được document trong `CLAUDE.md` phần "Cluster / HPC Gotchas": *"On systems with long working directory paths (e.g. Lustre mounts), Ray's AF_UNIX socket paths can exceed the 107-byte Linux limit."*
- `initialize_ray()` trong `server_utils.py:398-442` lưu `ray_head_node_address` vào global config dict sau khi start cluster, để child processes dùng `ray.init(address=...)` thay vì start cluster mới.
- `atexit.register(maybe_ray_cluster_exit)` pattern đảm bảo Ray cluster cleanup dù process exit theo bất kỳ cách nào (normal, exception, signal).

### 2.4 Industry URL

- **Linux unix(7) man page:** https://man7.org/linux/man-pages/man7/unix.7.html — *"sun_path: a pathname... limited to 108 bytes (including the terminating null byte)"*
- **POSIX socket path limits (Stack Overflow):** https://stackoverflow.com/questions/34829600/why-is-the-maximum-path-length-allowed-for-unix-sockets-on-linux-108-bytes — lý giải lịch sử 108-byte limit từ BSD 4.2
- **Ray: Configuring Logging / Temp Dir:** https://docs.ray.io/en/latest/ray-observability/user-guides/configure-logging.html#logging-directory-structure — cách Ray xây dựng session directory path
- **Ray: Environment Variables:** https://docs.ray.io/en/latest/ray-core/configure.html — `RAY_TMPDIR` configuration

---

## Decision 3: Per-Server venv Isolation thay vì Single venv với tox/nox

**File tham chiếu:**
- [`nemo_gym/cli.py:555-571`](../../nemo_gym/cli.py) — `_test_single()` gọi `setup_env_command(dir_path, ...)` trước `pytest`
- [`nemo_gym/cli.py:605-657`](../../nemo_gym/cli.py) — `test_all()` tạo `.venv` per server, có `delete_venvs_after_each_test` flag
- [`resources_servers/gdpval/setup_libreoffice.py`](../../resources_servers/gdpval/setup_libreoffice.py) — example: server cần libreoffice + Java JRE
- `resources_servers/bigcodebench/setup_bcb_venv.py`, `resources_servers/bird_sql/setup_bird_sql.py` — evidence về complexity per-server

### 3.1 Nguyên lý (Principle)

**Process Isolation via Virtual Environment per Server** — mỗi resources server có thể có `requirements.txt` với conflicting dependency versions. venv isolation đảm bảo không có version conflict giữa `bigcodebench` (cần `transformers==4.x`) và `tavily_search` (cần `httpx` version khác).

**Convention over Configuration** — tất cả servers đều có cùng structure: `requirements.txt` → `setup_env_command()` → `.venv/` tại server root. Không cần cấu hình gì thêm. `ng_test +entrypoint=resources_servers/my_server` là self-contained.

### 3.2 Tại sao KHÔNG đơn giản (Why Not Simple)

**Không dùng tox/nox vì:**

1. **Dependency conflict hell ở scale:** `test_all()` trong `cli.py:605` iterate qua `resources_servers/*`, `responses_api_agents/*`, `responses_api_models/*`. Với 20+ servers mỗi server có dep riêng (numpy versions, torch versions, special compilers), single venv = constant conflict resolution. tox matrix sẽ tốn nhiều config.

2. **External tool install side effects:** `setup_libreoffice.py` chạy `apt-get install libreoffice` vào host OS — không thể wrap trong tox. Tương tự, `setup_bcb_venv.py` cho BigCodeBench install Docker images. Những side effects này không phải Python package, cần isolation ở mức process/container.

3. **DRY_RUN serial install optimization:** `cli.py:183` — `if global_config_dict[DRY_RUN_KEY_NAME]: process.communicate()` install venvs serially để tránh UV cache bloat lên 10-20GB (comment trong code). tox/nox không có concept này.

4. **`skip_venv_if_present` performance optimization** (`SKIP_VENV_IF_PRESENT_KEY_NAME` trong `global_config.py:59`): developer có thể đặt `.venv/` sẵn để skip venv creation. tox không support pattern này dễ dàng.

### 3.3 Historical Context

- `cli_setup_command.py` (referenced từ `cli.py:46`) xử lý `setup_env_command()` — command phức tạp: `uv venv`, `uv pip install -r requirements.txt`, inject `NEMO_GYM_CONFIG_DICT` env var, set `NEMO_GYM_CONFIG_PATH`.
- **Comment trong `cli.py:183`:** *"In dry run mode, wait for each setup command to finish before starting the next. This installs uv virtual environments serially, which significantly reduces uv cache size. For Nemotron's set of environments, parallel installation can produce a cache 10-20GB larger than serial installation."* — evidence rằng team đã profiled và tối ưu pattern này.

### 3.4 Industry URL

- **uv docs — workspaces vs standalone:** https://docs.astral.sh/uv/concepts/projects/workspaces/ — lý do uv workspace có thể gây conflict; per-project venv là cách uv khuyến nghị cho independent projects
- **Docker Compose per-service pattern:** https://docs.docker.com/compose/how-tos/multiple-compose-files/ — analogous pattern ở container level
- **tox vs per-env isolation tradeoffs:** https://tox.wiki/en/latest/config.html#env — tox envs cũng là per-venv nhưng centralised config → không fit pattern "each server owns its own requirements"

---

## Decision 4 (Bonus): External Tool Auto-Install qua `model_post_init` + `pytest_configure` Hook

**File tham chiếu:**
- [`resources_servers/gdpval/setup_libreoffice.py`](../../resources_servers/gdpval/setup_libreoffice.py) — `ensure_libreoffice()` với 4-version history
- `resources_servers/bird_sql/setup_bird_sql.py`, `resources_servers/newton_bench/setup_newton_bench.py` — other auto-install examples

### 4.1 Nguyên lý (Principle)

**Self-Bootstrapping Server** — server tự đảm bảo dependencies khi start (`model_post_init`), không yêu cầu manual host setup. Đây là **Convention over Documentation** — thay vì docs nói "install libreoffice trước khi chạy", code tự install.

**Idempotent Install** — mỗi `ensure_*()` function phải idempotent: skip nếu đã installed. Tuy nhiên, `setup_libreoffice.py` v4 dạy lesson quan trọng: đôi khi **always-run là đúng hơn early-exit**, vì `which()` check không đủ (binary tồn tại nhưng broken — case JRE/javaldx trong libreoffice).

### 4.2 Tại sao KHÔNG đơn giản (Why Not Simple)

**`skipif(shutil.which("tool") is None)` trong pytest evaluates at import time**, trước khi fixture chạy. Nếu `ensure_tool()` chỉ được gọi trong fixture → tool chưa install lúc `skipif` evaluate → test bị skip dù tool có thể install được.

**Fix pattern** (`conftest.py` `pytest_configure` hook): gọi `ensure_tool()` trước collection phase → `skipif` thấy tool đã on PATH → test không bị skip.

**4 versions của `setup_libreoffice.py`** (documented in source) chứng minh complexity:
- v1: `which("libreoffice")` → fail (image bake without JRE)
- v2: `which("libreoffice") and which("java")` → fail (broken java binary)
- v3: `which("libreoffice") and _java_runs()` → fail (javaldx can't find JRE via JNI)
- v4: **always run apt-install** (idempotent, few seconds if already installed) → correct

### 4.3 Historical Context

Từ CLAUDE.md: *"If a benchmark auto-installs its tool dependency, add a `pytest_configure` hook in `conftest.py` to run the install before test collection — `skipif` markers evaluate at import time, before fixtures run."*

Pattern chuẩn hóa qua 7 servers: `bird_sql`, `bigcodebench`, `ifbench`, `newton_bench`, `gdpval`, `spider2_lite`, `ether0`.

### 4.4 Industry URL

- **Kubernetes init containers:** https://kubernetes.io/docs/concepts/workloads/pods/init-containers/ — analogous: container chạy setup task trước main container (giống `model_post_init`)
- **pytest `pytest_configure` hook docs:** https://docs.pytest.org/en/stable/reference/reference.html#pytest.hookspec.pytest_configure — hook chạy trước collection, đúng place để gọi auto-install
- **Ansible idempotency principle:** https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_intro.html#idempotency — "operations that are safe to run multiple times without changing the result beyond the initial application"

---

## Tóm tắt các file infrastructure hot-zones

| File | Role | Key Pattern |
|---|---|---|
| [`nemo_gym/server_utils.py`](../../nemo_gym/server_utils.py) | aiohttp singleton + ServerClient + Ray init | `_GLOBAL_AIOHTTP_CLIENT`, `initialize_ray()`, `atexit` cleanup |
| [`nemo_gym/global_config.py`](../../nemo_gym/global_config.py) | Hydra config singleton + port allocation | `_GLOBAL_CONFIG_DICT`, child proc env var injection |
| [`nemo_gym/cli.py`](../../nemo_gym/cli.py) | Server lifecycle + per-server venv | `RunHelper`, `setup_env_command`, `DRY_RUN` serial install |
| [`resources_servers/tavily_search/app.py`](../../resources_servers/tavily_search/app.py) | httpx→aiohttp adapter | `TavilySearchAIOHTTPClient.from_httpx_AsyncClient()` |
| [`resources_servers/gdpval/setup_libreoffice.py`](../../resources_servers/gdpval/setup_libreoffice.py) | Auto-install pattern | `ensure_libreoffice()` v4 always-run pattern |
| [`docs/infrastructure/engineering-notes/aiohttp-vs-httpx.md`](../../docs/infrastructure/engineering-notes/aiohttp-vs-httpx.md) | Root cause analysis | O(n²) httpcore bug, Sep 2025 40-min hang incident |

## Phản biện (2026-05-24, Round 1+2)
- Round 1: 8.0/10.
- Round 2: 9.3/10 — aiohttp-vs-httpx + Ray RAY_TMPDIR dedicated, engineering note mandatory đọc đầu.
