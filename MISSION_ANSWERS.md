# Mission Answers — Day 14

## Part 1: Localhost vs Production

### Exercise 1.1 — Anti-patterns in `01-localhost-vs-production/develop/app.py`

1. **Hardcoded secrets** (lines 17-18): `OPENAI_API_KEY = "sk-..."` and a `DATABASE_URL` with a password. Pushing this to a public repo leaks them.
2. **No config management** (lines 21-22): `DEBUG = True` and `MAX_TOKENS = 500` are fixed in code, so changing them means editing code.
3. **`print()` instead of logging** (lines 33, 36, 38): unstructured output that log tools can't parse.
4. **Secret written to logs** (line 34): `print(f"[DEBUG] Using key: {OPENAI_API_KEY}")`.
5. **No health check endpoint**: the platform can't tell if the agent crashed, so it can't restart it. I confirmed `GET /health` returns 404.
6. **Fixed port** (line 53): `port=8000` ignores the `PORT` env var that Railway and Render inject.
7. **`host="localhost"`** (line 51): only accepts connections from the same machine, so it is unreachable from outside a container.
8. **`reload=True`** (line 53): the debug auto-reloader is on.
9. **No graceful shutdown**: there is no SIGTERM handling or lifespan, so in-flight requests get cut off.

### Exercise 1.2 — Running the develop version

```
$ curl -X POST "localhost:8000/ask?question=Hello"
{"answer":"Tôi là AI agent được deploy lên cloud. Câu hỏi của bạn đã được nhận."}

$ curl localhost:8000/health
404

$ curl -X POST localhost:8000/ask -H 'Content-Type: application/json' -d '{"question":"Hello"}'
{"detail":[{"type":"missing","loc":["query","question"],"msg":"Field required",...}]}   # 422
```

It works, but it is not production-ready: no `/health`, secrets in code, and it can only be reached from localhost.

### Exercise 1.3 — Develop vs production

Production version run locally:

```
$ curl localhost:8000/health
{"status":"ok","uptime_seconds":3.7,"version":"1.0.0","environment":"development",...}
$ curl localhost:8000/ready
{"ready":true}
$ curl -X POST localhost:8000/ask -H 'Content-Type: application/json' -d '{"question":"Hello"}'
{"question":"Hello","answer":"Agent đang hoạt động tốt! (mock response)...","model":"gpt-4o-mini"}
```

| Feature | Develop | Production | Why it matters |
|---------|---------|------------|----------------|
| Config | Hardcoded constants (`app.py` 17-22) | Env vars via `config.py` `Settings` (`os.getenv`) | The same code runs in dev, staging and prod. No secrets in git. |
| Secrets | `"sk-hardcoded..."` in code | `AGENT_API_KEY`, `OPENAI_API_KEY` from env; `validate()` raises if the key is missing in production | A leaked repo doesn't leak keys. Missing config fails at startup. |
| Port / host | `localhost:8000` fixed | `HOST=0.0.0.0`, `PORT` from env (`config.py` 17-18) | Containers and PaaS inject the port and need to reach the app from outside. |
| Health check | None (404) | `GET /health` (liveness) and `GET /ready` (readiness, 503 until startup finishes) | The platform restarts a dead container and only routes traffic to a ready one. |
| Logging | `print()`, leaks the API key | JSON logs, no secrets (`app.py` 111-122) | Log aggregators can parse them, and secrets don't end up in logs. |
| Shutdown | Abrupt | `lifespan` shutdown plus a SIGTERM handler (`app.py` 39-67, 180-189) | A deploy or scale-down doesn't drop requests that are in flight. |
| Reload | `reload=True` always | `reload=settings.debug` (off by default) | The reloader is a dev tool and wastes resources in prod. |

### Self-check: one anti-pattern fixed

Develop has `OPENAI_API_KEY = "sk-hardcoded-fake-key-never-do-this"` at `develop/app.py:17`. Production replaces it with `openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))` at `production/config.py:27`.

### Discussion

- **Why hardcoding secrets is dangerous:** anyone who can read the repo or its history gets the key, and bots scan public GitHub within minutes. Deleting the file doesn't help, because git history keeps it. The key has to be revoked.
- **Why health check and graceful shutdown:** `/health` lets the platform detect a dead process and restart it. `/ready` keeps traffic away until the app is ready. Graceful shutdown lets in-flight requests finish when the platform sends SIGTERM during a deploy or scale-down.

## Part 2: Docker

### Exercise 2.1 — `02-docker/develop/Dockerfile`

1. **Base image:** `python:3.11` (full distribution, not slim).
2. **Working directory:** `/app`.
3. **Why `COPY requirements.txt` first:** Docker caches each layer. If only `app.py` changes, the `pip install` layer is reused instead of reinstalling every dependency. `COPY . .` before it would invalidate the cache on every code edit.
4. **CMD vs ENTRYPOINT:** `CMD` is the default command and is replaced by anything after `docker run image ...`. `ENTRYPOINT` is the fixed executable, and `docker run` arguments are appended to it. This Dockerfile uses `CMD ["python", "app.py"]`.

### Exercise 2.2 — Build and run develop

```
$ docker build -f 02-docker/develop/Dockerfile -t my-agent:develop .
$ docker run -p 8000:8000 my-agent:develop
$ curl -X POST "localhost:8000/ask?question=What+is+Docker%3F"
{"answer":"Container là cách đóng gói app để chạy ở mọi nơi. Build once, run anywhere!"}
$ curl -s -o /dev/null -w '%{http_code}\n' localhost:8000/health
200
```

`/ask` here takes `question` as a query parameter. Sending a JSON body, as `CODE_LAB.md` shows, returns 422.

### Exercise 2.3 — Multi-stage build

- **Stage 1 (`builder`):** `python:3.11-slim` plus `gcc` and `libpq-dev`; runs `pip install --user` into `/root/.local`.
- **Stage 2 (`runtime`):** a fresh `python:3.11-slim`. It copies only `/root/.local` and `main.py`, then runs as a non-root `appuser` with a `HEALTHCHECK`.
- **Why smaller:** gcc, apt caches and pip build leftovers stay in the builder stage and are not shipped. The base is also `slim` instead of the full image.

Measured with `docker images`:

| Image | Size |
|-------|------|
| `my-agent:develop` | 1.67 GB |
| `my-agent:advanced` | 240 MB |

The production image is about **86% smaller** ((1670 − 240) / 1670).

### Exercise 2.4 — Docker Compose stack

```
Client ──:80──> nginx ──> agent:8000 ──(depends_on, healthy)──> redis:6379
                                   └───(depends_on, healthy)──> qdrant:6333
         (all four on the private `internal` bridge network; only nginx publishes ports)
```

`docker compose up` started `nginx`, `agent`, `redis` and `qdrant`, all healthy. The agent starts only after redis and qdrant pass their health checks. Services reach each other by service name on the `internal` network. Nginx is the only entry point and also adds security headers and rate limiting.

`docker-compose.yml` needs a `.env.local` (gitignored) because of `env_file`. I created an empty one for the test.

Test through Nginx:

```
$ curl -i localhost/health
HTTP/1.1 200 OK
Server: nginx
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
{"status":"ok","uptime_seconds":26.3,"version":"2.0.0",...}

$ curl localhost/ask -X POST -H "Content-Type: application/json" -d '{"question": "Explain microservices"}'
{"answer":"Tôi là AI agent được deploy lên cloud. Câu hỏi của bạn đã được nhận."}
```

`main.py` doesn't actually import redis or qdrant, so in this stack they are started but unused.

### Self-check

Sizes above come from my own `docker images` run. Debug commands: `docker logs <container>`, `docker exec -it <container> sh`.

## Part 4: API Security

### Exercise 4.1 — API key (`04-api-gateway/develop/app.py`)

- **Where it is checked:** `verify_api_key` (lines 39-52) is a FastAPI dependency. `/ask` uses it through `Depends(verify_api_key)` (line 70). The key comes from the `AGENT_API_KEY` env var (line 35).
- **Wrong key:** no header gives 401, a wrong key gives 403.
- **Rotating the key:** change `AGENT_API_KEY` and restart. The key is not in the code, so there is no code change or redeploy of new code.

```
$ AGENT_API_KEY=secret-key-123 python app.py
$ curl -i localhost:8000/ask -X POST -H 'Content-Type: application/json' -d '{"question":"Hello"}'
HTTP/1.1 401 Unauthorized
{"detail":"Missing API key. Include header: X-API-Key: <your-key>"}

$ curl -i ... -H 'X-API-Key: wrong'
HTTP/1.1 403 Forbidden
{"detail":"Invalid API key."}

$ curl -i ... -H 'X-API-Key: secret-key-123'
HTTP/1.1 200 OK
{"question":"Hello","answer":"Đây là câu trả lời từ AI agent (mock). ..."}
```

### Exercise 4.2 — JWT (`04-api-gateway/production`)

Flow: `POST /auth/token` checks username/password (`authenticate_user`) and returns a signed JWT (`create_token`, HS256, expires in 60 minutes). On `/ask`, `verify_token` decodes it with `JWT_SECRET` and gets the username and role, so no database lookup is needed per request.

```
$ curl -i localhost:8000/ask -X POST -H 'Content-Type: application/json' -d '{"question":"Hello"}'
HTTP/1.1 401 Unauthorized
{"detail":"Authentication required. Include: Authorization: Bearer <token>"}

$ curl -s localhost:8000/auth/token -X POST -H 'Content-Type: application/json' -d '{"username":"student","password":"demo123"}'
{"access_token":"eyJhbGciOi...<redacted>","token_type":"bearer","expires_in_minutes":60,...}

$ curl -i localhost:8000/ask -X POST -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -d '{"question":"Explain JWT"}'
HTTP/1.1 200 OK
```

### Exercise 4.3 — Rate limiting (`rate_limiter.py`)

- **Algorithm:** sliding window. Each user has a deque of request timestamps. Entries older than 60 s are dropped, and if the deque already holds `max_requests` entries the request gets 429.
- **Limit:** user 10 requests/minute (`rate_limiter_user`), admin 100 requests/minute (`rate_limiter_admin`).
- **Admin bypass:** not a full bypass. `app.py` line 141 picks `rate_limiter_admin` when the JWT role is `admin`, which gives a higher limit.

12 calls in a row with the `student` token:

```
1-10: HTTP/1.1 200 OK
11:   HTTP/1.1 429 Too Many Requests
12:   HTTP/1.1 429 Too Many Requests

$ curl -i ... (11th+ call)
HTTP/1.1 429 Too Many Requests
x-ratelimit-limit: 10
x-ratelimit-remaining: 0
x-ratelimit-reset: 1795570957
retry-after: 59
{"detail":{"error":"Rate limit exceeded","limit":10,"window_seconds":60,"retry_after_seconds":59}}
```

### Exercise 4.4 — Cost guard (`cost_guard.py`)

`CostGuard` was already implemented in `production/cost_guard.py` (in memory, per day, not per month and not in Redis as the `CODE_LAB.md` sketch suggests). How it works:

1. Before calling the LLM, `check_budget(user)` raises **402** if the user's spend today is at or above `daily_budget_usd` ($1), and **503** if the global spend is at or above $10/day. It logs a warning at 80%.
2. After the call, `record_usage` adds the input/output tokens and the cost (GPT-4o-mini prices) to the user's record and to the global total.
3. A new date key resets the record each day.

`/ask` calls `check_budget` first, then the LLM, then `record_usage` (app.py 145-153). `GET /me/usage` shows the current numbers: after my 10 requests, `cost_usd` was 0.000191 of the $1 budget.

Quick test with a tiny budget (`CostGuard(daily_budget_usd=0.0005)`): request 1 and 2 pass, request 3 is rejected with 402 `Daily budget exceeded`.

Limit: the state is in RAM, so with several instances or a restart each one has its own count. Production would keep it in Redis (done in Part 6).

**Why both rate limit and cost guard:** the rate limit caps speed (requests per minute), so a flood can't overload the service. It does not cap total spend, since a slow user can still use long prompts all day. The cost guard caps money, but would not stop a burst before the budget is used up. Each covers what the other misses.

## Part 5: Scaling & Reliability

### Exercise 5.1 — Health checks (`05-scaling-reliability/develop/app.py`)

Both endpoints were already implemented. I ran the app and called them:

```
$ curl localhost:8000/health
{"status":"ok","uptime_seconds":2.7,"version":"1.0.0",...,"checks":{"memory":{"status":"ok","used_percent":23.2}}}
$ curl -w ' [%{http_code}]' localhost:8000/ready
{"ready":true,"in_flight_requests":1} [200]
```

- **`/health` (liveness):** is the process alive? If it fails, the platform restarts the container.
- **`/ready` (readiness):** can it take traffic now? It returns 503 while starting, while shutting down, or (in the production app) when Redis is unreachable. A failing `/ready` removes the instance from the load balancer but does **not** restart it.

### Exercise 5.2 — Graceful shutdown

The develop app counts in-flight requests in a middleware. On SIGTERM, uvicorn runs the `lifespan` shutdown: it sets `_is_ready = False`, waits up to 30 s for `_in_flight_requests` to reach 0, then exits (`timeout_graceful_shutdown=30`). Test: I sent a request and `kill -TERM`'d the server right after.

```
{"answer":"Agent đang hoạt động tốt! (mock response) ..."} [http 200]     <- request finished
INFO: Shutting down
🔄 Graceful shutdown initiated...
✅ Shutdown complete
Received signal 15 — uvicorn will handle graceful shutdown
```

The in-flight request returned 200 and the process exited cleanly instead of cutting it off.

### Exercise 5.3 — Stateless design (`production/app.py`)

Session history lives in Redis, not in a Python dict: `save_session` does `setex("session:<id>", 3600, json)` and `load_session` reads it back (lines 59-73). Every instance reads and writes the same Redis, so any instance can serve any request. A module-level dict would give each instance its own copy, and a request routed to another instance would not find the conversation. (If `REDIS_URL` is unreachable the app falls back to an in-memory store, which is only for local use.)

### Exercise 5.4 — Load balancing

`docker compose up -d --build --scale agent=3` (after `touch .env.local`) started 3 agents, Redis and Nginx on port 8080, all healthy. Nginx round-robins across the `agent` DNS name and adds an `X-Served-By` header. Six `POST /chat` calls were served by `instance-1c8549`, `99c23a`, `ac51db`, `1c8549`, `99c23a`, `ac51db`, which is an even rotation.

### Exercise 5.5 — `test_stateless.py`

Result: 5 requests in one session were served by 3 different instances (`instance-1c8549`, `99c23a`, `ac51db`), and the history afterwards had all **10 messages** (5 user + 5 assistant). It works because the history is in Redis, not in the memory of whichever instance answered.

I also tested failure myself (the script does not kill anything): I started a session, ran `docker stop production-agent-1`, and sent 2 more messages with the same `session_id`. Both were answered by the remaining instances (turns 3 and 4), and the history still had all 6 messages. `proxy_next_upstream error timeout http_503` in `nginx.conf` retries on another instance. I then ran `docker compose down`.

## Part 6: Final Project

Filled every `TODO` in `06-lab-complete/` (config, auth, Redis client, rate limiter, cost guard, JSON logs, `/health` and `/ready`, multi-stage Dockerfile, compose with Redis, `.dockerignore`, `.env.example`, `railway.toml`, `render.yaml`). `/health` never touches Redis, so it stays 200 when Redis is down; `/ready` pings Redis and returns 503 when it fails. Rate limit and daily cost are Redis keys, so they are shared by workers and survive a restart. Shutdown relies on uvicorn's own SIGTERM handling (finish in-flight requests, exit 0) plus a `lifespan` cleanup.

Output of `python check_production_ready.py` (full run, with Docker):

```text
Checklist Deliverable
   [x] Dockerfile (multi-stage, < 500 MB)
   [x] docker-compose.yml (agent + redis)
   [x] .dockerignore
   [x] Health check endpoint (GET /health)
   [x] Readiness endpoint (GET /ready)
   [x] API Key authentication
   [x] Rate limiting
   [x] Cost guard
   [x] Config from environment variables
   [x] Structured logging
   [x] Graceful shutdown
   [x] Public URL ready (Railway / Render config)
Result: 12/12 criteria passed, 43/43 checks passed
PASS 12/12 - PRODUCTION READY!
```

## AI log

- Part 1: asked Claude Code to read the Day 14 docs, run both Part 1 apps, and draft this section. I checked the line numbers and curl outputs against the files and my own runs.
- Part 2: asked Claude Code to build both images, run the develop container and the compose stack, and draft this section. Sizes and curl outputs are from those runs.
- Part 4: asked Claude Code to run the develop and production gateways and draft this section. The curl outputs are from those runs; I checked the line numbers in the code.
- Part 5: asked Claude Code to run the develop app (health, ready, SIGTERM test) and the 3-instance compose stack with `test_stateless.py` and an instance-stop test, and draft this section. All outputs are from those runs.
- Part 6: asked Claude Code to fill the `TODO`s in `06-lab-complete/` and run `check_production_ready.py`. I read each file and the script output; the result above is from that run.
- Part 3: asked Claude Code to walk me through the Render Blueprint deploy and to add a root `render.yaml`, then run the 4 curl checks against the public URL. I did the deploy and took the screenshots myself; the status codes are from those runs.
- Part 7: asked Claude Code to run the load tests, evals, the Docker observability stack, the Locust scale runs and the two alert experiments, to find the traces in Jaeger and to fix the `production/Dockerfile` (it crashed with `No module named uvicorn`), and to fill `BENCHMARK_REPORT.md`. All numbers come from the JSON/CSV files and my screenshots. I took the screenshots myself. Alert times in 4.2 were measured by polling Prometheus every 5 s.

## Part 3: Cloud Deployment

### Exercise 3.2: Render deployment (agent from `06-lab-complete/`)
- URL: https://agent-n0nl.onrender.com
- Screenshot: [dashboard](screenshots/dashboard.png), [test](screenshots/test.png)

## Part 7: Benchmark & Observability (Bước 1, local)

Số liệu đầy đủ: [BENCHMARK_REPORT.md](BENCHMARK_REPORT.md); file thô: `06-lab-complete/benchmark-observability/develop/reports/`.

### Exercise 7.1 — Metrics
1. Counter: `http_requests_total`, `llm_tokens_total` (chỉ tăng). Gauge: `agent_in_flight_requests`, `agent_info` (lên xuống). Histogram: `http_request_duration_seconds_bucket`, `llm_request_duration_seconds_bucket`, `agent_question_length_chars_bucket`.
2. Dùng `request.url.path` thì mỗi URL lạ (`/wp-admin`, `/.env`, `/a1b2c3`…) tạo một series label mới → cardinality bùng nổ, Prometheus tốn RAM/disk và truy vấn chậm. `route.path` (hoặc `unmatched`) giữ số series cố định.
3. Đã thêm Histogram `agent_question_length_chars` trong `develop/app.py` (observe `len(body.question)` trong `ask()`); kiểm tra bằng `curl /metrics`: `_count 1.0`, `_sum 40.0` sau 1 câu hỏi 40 ký tự.

### Exercise 7.2 — Load test & SLO
Bảng concurrency 1/10/50/100 và so sánh `MOCK_SLOW_RATE` 0/0.03/0.1 nằm ở mục 2 của `BENCHMARK_REPORT.md`. avg chỉ tăng nhẹ vì ~97% request vẫn nhanh, còn p99 nằm đúng ở nhóm 3% request chậm +1500 ms. SLO đặt theo p95/p99 (và error rate), không theo avg.

### Exercise 7.3 — Eval & quality gate
- v1 4.3%, v2 91.3%, v2 sau sửa KB 100% (0 regression, `Quality gate ✅ PASS`). Hai câu sai ban đầu (`security-02`, `scaling-03`) và cách sửa: mục 3 của `BENCHMARK_REPORT.md`; sửa trong `develop/utils/mock_llm.py`.
- CI: [.github/workflows/eval.yml](.github/workflows/eval.yml) chạy agent v2 rồi `run_eval.py --min-accuracy 0.85`. Script thoát exit code 1 khi accuracy dưới ngưỡng hoặc có regression, nên job fail và PR bị chặn merge (khi bật branch protection yêu cầu check này).

### Exercise 7.4 — Observability stack
Số liệu đọc từ `screenshots/grafana-dashboard.png` (lúc chạy thí nghiệm B, `MOCK_SLOW_RATE=0.3`, 30 user).
1. p95 ≈ 1.9 s, p50 ≈ 0.2 s, avg ≈ 0.7–0.9 s (đọc ước từ đồ thị). avg cách xa p95 nghĩa là phân bố lệch: đa số request nhanh, một nhóm nhỏ rất chậm kéo đuôi. Avg che nhóm này, p95/p99 thì lộ ra.
2. Chưa chụp panel "Requests/s theo instance" nên không có số đo. Theo cấu hình, `nginx.conf` dùng upstream `agent_cluster` mặc định (round-robin, không `least_conn`) và `server agent:8000 resolve`, nên về lý thuyết chia đều cho các instance.
3. Mỗi lần gọi LLM, input gồm câu hỏi và đoạn context lấy từ knowledge base, còn output chỉ là câu trả lời ngắn. Log `llm_call` của mình: `input_tokens: 74`, `output_tokens: 37`.
4. `curl http://localhost:8080/metrics` trả **404**: `nginx.conf` có `location = /metrics { return 404; }` để không lộ metric ra ngoài. Prometheus scrape thẳng từng agent trong mạng nội bộ.

### Exercise 7.5 — Tracing
Trace chậm `532a78a475a53752340e42033dd921e2`: 1722 ms, span `chat mock-llm-small` chiếm 1694 ms (~98%), `agent.retrieve_context` chỉ 25 ms. Trace lỗi `12bae23c20fa0e22471bf265622dcf56`: span LLM có event `exception` (`Upstream LLM error: 503`). Cả hai có dòng log JSON cùng `trace_id` (chi tiết ở mục 4.3 của `BENCHMARK_REPORT.md`).

### Exercise 7.6 — Alerts
Đã chạy `promtool test rules` (SUCCESS) và 2 thí nghiệm: Mỗi thí nghiệm chạy riêng trên stack mới, baseline không có alert nào, đo bằng polling Prometheus mỗi 5 s từ lúc đổi cấu hình: A (`MOCK_ERROR_RATE=0.2`) → `AgentHighErrorRate` firing sau 98 s; B (`MOCK_SLOW_RATE=0.3`) → `AgentHighLatencyP95` firing sau 142 s; D (`docker pause` 1 instance) → `AgentInstanceDown` firing sau 45 s. Alert chờ `for: 1m` / `2m` / `30s` nên không firing ngay. Lỗi 504 do Nginx (thấy ở một lần chạy trước) không hiện trong metric của agent.
Với `AGENT_VERSION=v1` không alert nào firing vì lỗi/latency vẫn bình thường, chỉ câu trả lời sai. Loại sự cố này cần eval định kỳ trên golden dataset (CI hoặc cron) và feedback người dùng.
