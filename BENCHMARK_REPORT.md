# Benchmark & Observability Report — Day 14

> Copy file này thành `BENCHMARK_REPORT.md` trong repo của bạn và điền đầy đủ.
> Mọi con số phải lấy từ report JSON / CSV / screenshot thật, không ước lượng.

**Họ tên:** Nguyễn Trọng Phương Bách (2A202603716)
**Ngày chạy:** 2026-11-25 (CP7, local)
**Môi trường:** Linux, Python 3.12.3, agent chạy trực tiếp bằng `python app.py` (mock LLM)

---

## 1. SLO của agent

| SLI | SLO | Lý do chọn ngưỡng này |
|---|---|---|
| p95 latency `/ask` | < 500 ms | Request bình thường ~190 ms; 500 ms cho dư ~2.5x, vẫn nhanh với người dùng. Bắt được tail do request chậm (+1500 ms). |
| Error rate `/ask` | < 2 % | Mock lỗi mặc định 1%; 2% là mức bắt đầu bất thường. |
| Accuracy trên golden dataset | ≥ 85 % | Khớp job CI; v2 gốc đạt 91.3%, sau sửa KB 100%. |

---

## 2. Benchmark hiệu năng (develop, `load_test.py`)

### 2.1 Concurrency vs latency (agent v2)

| Concurrency | RPS | p50 (ms) | p95 (ms) | p99 (ms) | Error rate | SLO |
|---|---|---|---|---|---|---|
| 1 | 4.5 | 187.1 | 218.6 | 1679.6 | 0.67% | PASS |
| 10 | 35.95 | 191.2 | 220.4 | 1700.7 | 0.33% | PASS |
| 50 | 117.16 | 196.5 | 248.0 | 1663.2 | 0.67% | PASS |
| 100 | 67.02 | 344.7 | 2826.9 | 3152.8 | 0.33% | **FAIL** (p95) |

**Nhận xét:** RPS tăng gần tuyến tính từ 1 → 10 (4.5 → 36, ~8x) vì mỗi request chỉ chờ I/O ~190 ms. Từ 10 → 50 chỉ tăng 3.3x (117 RPS), và ở 100 RPS **giảm** còn 67 trong khi p95 vọt lên 2.8 s: một process Python/uvicorn đơn đã bão hoà, request xếp hàng chờ event loop. Giới hạn nằm ở 1 instance, nên cần scale ngang (CP8). Mỗi mức chỉ chạy 300 request nên số liệu có nhiễu; p99 ở c1–c50 (~1.7 s) hầu hết là các request "slow" ngẫu nhiên.

### 2.2 Tail latency

| `MOCK_SLOW_RATE` | avg (ms) | p95 (ms) | p99 (ms) |
|---|---|---|---|
| 0 | 189.7 | 217.1 | 223.0 |
| 0.03 (mặc định) | 261.3 | 237.5 | 1708.3 |
| 0.1 | 368.5 | 1701.9 | 1714.8 |

**Nhận xét:** (concurrency 20, 300 request mỗi lần). Từ 0 → 0.03, avg chỉ tăng ~38% (190 → 261 ms) nhưng p99 tăng gấp ~8 lần (223 → 1708 ms); p95 chỉ nhảy khi tỉ lệ slow vượt 5% (0.1 → 1702 ms). Vậy p99 nhạy nhất với đuôi chậm. Trung bình trộn lẫn 97% request nhanh với 3% request rất chậm nên che mất trải nghiệm xấu của nhóm này; SLO theo p95/p99 phản ánh đúng người dùng tệ nhất. Lưu ý: ở 0.03, p95 (237 ms) vẫn đẹp vì chỉ ~3% request chậm, nên p99 mới là chỉ số bắt được nó.

---

## 3. Benchmark chất lượng (develop, `eval/run_eval.py`)

| Chỉ số | Agent v1 | Agent v2 | Agent v2 (sau khi sửa KB) |
|---|---|---|---|
| Accuracy | 4.3% (1/23) | 91.3% (21/23) | 100% (23/23) |
| Avg tokens / câu | 56.7 | 109.0 | 113.7 |
| Tổng cost (USD) | 0.000399 | 0.000759 | 0.000790 |
| Cost / câu đúng (USD) | 0.00039855 | 0.00003616 | 0.00003436 |
| Quality gate | FAIL | PASS (≥80%) | PASS (≥100%, 0 regression) |

**Những câu v2 trả lời sai ban đầu và cách bạn sửa:**

| ID | Keyword bị thiếu | Bạn đã sửa gì |
|---|---|---|
| security-02 | token, hết hạn, chữ ký | Thêm doc `["jwt"]` vào `KNOWLEDGE_BASE` giải thích JWT vs API key |
| scaling-03 | cpu, memory, custom metrics | Thêm doc `["hpa","kubernetes","autoscal"]` về Kubernetes HPA |

**Nhận xét về trade-off chất lượng / chi phí / latency giữa v1 và v2:** v2 tốn gấp ~1.9x token (109 vs 57) và tổng cost gấp ~1.9x, p95 chậm hơn ~26 ms do bước retrieval, nhưng accuracy tăng từ 4.3% lên 91.3%. Tính theo cost / câu đúng thì v2 rẻ hơn ~11x (0.0000362 vs 0.000399 USD), vì v1 trả tiền cho câu trả lời sai. Đó là lý do so sánh theo "cost / câu đúng" công bằng hơn "cost / câu". Sau khi sửa KB, accuracy 100%, 0 regression, cost +0.000031.

---

## 4. Observability stack (production)

### 4.1 Screenshot

- [x] Dashboard Grafana khi đang có tải (thấy rõ Golden Signals)
- [x] Một trace chậm trong Jaeger (thấy span nào chiếm thời gian)
- [x] Một trace lỗi trong Jaeger (có event `exception`)
- [x] Trang Alerts của Prometheus với ít nhất 2 alert đang **firing**

### 4.2 Thí nghiệm "phá hệ thống"

| # | Thay đổi | Alert nào firing | Thời gian từ lúc đổi → firing | Panel nào phản ánh rõ nhất |
|---|---|---|---|---|
| A | `MOCK_ERROR_RATE=0.2` | `AgentHighErrorRate` | 98 s (pending ở 33 s, `for: 1m`) | Error rate (503) |
| B | `MOCK_SLOW_RATE=0.3` | `AgentHighLatencyP95` | 142 s (pending ở 21 s, `for: 2m`) | p95/p99 latency |
| C | `LLM_MODEL=mock-llm-large` | không làm (chỉ yêu cầu ≥ 2) | - | - |
| D | `docker pause` 1 instance | `AgentInstanceDown` | 45 s (pending ở 15 s, `for: 30s`) | Instances up: 2 → 1 |
| E | `AGENT_VERSION=v1` | không làm (theo README: không alert nào) | - | - |

**Thí nghiệm E không làm alert nào firing. Bạn sẽ phát hiện loại sự cố này trong production bằng cách nào?**

Metric hạ tầng (error rate, latency) vẫn xanh nên không alert nào bắt được. Phải chạy eval trên golden dataset định kỳ (cron/CI) và alert khi accuracy tụt dưới SLO 85%; thêm feedback của người dùng (thumbs up/down) và metric như retrieval hit ratio.

Ảnh `screenshots/prometheus-alert-firing.png` chụp ở một lần chạy trước, khi lỗi và độ trễ cùng bật nên hai alert cùng firing trên một trang; thời gian firing trong bảng là từ các lần chạy riêng. Mỗi thí nghiệm A, B, D chạy riêng trên stack mới (`docker compose down -v` rồi `up`), tải Locust 30 user, baseline không có alert nào firing; thời gian đo bằng polling Prometheus mỗi 5 s từ lúc đổi cấu hình.

Thí nghiệm D: pause 1 trong 2 instance, `AgentInstanceDown` (`up == 0`) firing sau 45 s trong khi alert error rate của agent vẫn không firing. Lần chạy này 30 request qua Nginx đều trả 200 (Nginx có `proxy_next_upstream` nên thử lại instance còn sống). Ở một lần chạy trước (baseline chưa sạch) mình thấy 1/20 request trả 504 từ Nginx: lỗi 504 sinh ra ở Nginx, request chưa được agent xử lý xong nên metric của agent không đếm. Vì vậy cần giám sát ở tầng load balancer hoặc synthetic check bên ngoài, chứ không chỉ metric của agent.

(Lưu ý: `LLMCostBurnRateHigh` cũng firing trong lúc chạy A/B, do tải Locust 100 user chạy trước đó trong lần chạy đầu, không phải do thí nghiệm C. Ở các lần chạy riêng từng thí nghiệm, baseline không có alert nào.)

### 4.3 Debug bằng trace

Chọn 1 trace chậm nhất bạn tìm được:

- `trace_id`: `532a78a475a53752340e42033dd921e2`
- Tổng thời gian: 1722 ms (`POST /ask`)
- Span chiếm nhiều thời gian nhất: `chat mock-llm-small` (1694 ms, ~98%); `agent.retrieve_context` chỉ 25 ms
- Dòng log tương ứng (grep theo `trace_id`):

```json
{"ts": "2026-11-25T02:10:21.017482+00:00", "level": "INFO", "service": "observable-agent", "instance": "48fd20f3b59f", "event": "llm_call", "trace_id": "532a78a475a53752340e42033dd921e2", "request_id": "269cec012cee", "model": "mock-llm-small", "agent_version": "v2", "input_tokens": 74, "output_tokens": 37, "cost_usd": 3.3e-05, "llm_ms": 1694.1}
{"ts": "2026-11-25T02:10:21.018114+00:00", "level": "INFO", "service": "observable-agent", "instance": "48fd20f3b59f", "event": "http_request", "trace_id": "532a78a475a53752340e42033dd921e2", "request_id": "269cec012cee", "method": "POST", "route": "/ask", "status": 200, "ms": 1721.5}
```

Trace lỗi: `trace_id` `12bae23c20fa0e22471bf265622dcf56`: span `chat mock-llm-small` (96 ms) có event `exception` `LLMError: Upstream LLM error: 503 Service Unavailable (mock)`; log `llm_error` cùng `trace_id`.

---

## 5. Benchmark scaling (production, Locust headless, 100 users, 2 phút)

| Số instance | RPS | p50 (ms) | p95 (ms) | p99 (ms) | Failures |
|---|---|---|---|---|---|
| 1 | 59.3 | 190 | 240 | 1700 | 68 / 7069 (0.96%) |
| 3 | 60.0 | 190 | 230 | 1700 | 70 / 7156 (0.98%) |

**Giải thích kết quả:** Số liệu là dòng `/ask` trong `scale_*_stats.csv`. Scale 1 → 3 instance gần như không đổi RPS (59.3 → 60.0) và p95 (240 → 230 ms). Nguyên nhân: 100 user Locust có thời gian nghỉ giữa các request nên tải bị giới hạn bởi load generator, không phải bởi agent; 1 instance chưa bão hoà ở mức này. Độ trễ cũng do LLM mock (~190 ms, và ~1700 ms ở 3% request chậm) chứ không do CPU agent, nên thêm instance không giúp p95/p99. Failures ~1% là lỗi 503 mock (`MOCK_ERROR_RATE=0.01`).

---

## 6. Kết luận

- 3 điều bạn học được về benchmark & observability:
  1. p95/p99 mới lộ ra đuôi chậm; trung bình che mất nó (avg 261 ms vs p99 1708 ms).
  2. Trace + log chung `trace_id` chỉ ra ngay span nào chậm/lỗi (LLM chiếm 98% thời gian).
  3. Scale ngang chỉ giúp khi nút thắt là CPU của agent; ở đây không phải. Và alert hạ tầng không bắt được lỗi chất lượng (thí nghiệm E), cần eval định kỳ.
- Nếu đưa agent này lên production thật, bạn sẽ thêm metric / alert nào nữa?

Alert accuracy từ eval định kỳ, alert/synthetic check ở tầng Nginx (504 không hiện ở metric agent), alert tỉ lệ request bị rate-limit và ngân sách chi phí theo ngày.
