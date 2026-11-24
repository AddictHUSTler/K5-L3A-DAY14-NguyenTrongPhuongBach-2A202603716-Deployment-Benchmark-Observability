# Day 14 — Deployment, Benchmark & Observability

> Đưa agent lên cloud, đo xem nó nhanh và đúng tới đâu, rồi giám sát nó khi chạy thật.

> **AICB-P1 · VinUniversity 2026**  
> Repository thực hành đi kèm bài giảng Day 14.  
> Mỗi phần có ví dụ **cơ bản** (hiểu concept) và **chuyên sâu** (production-ready).

> **Hình thức: CÁ NHÂN** · **Thời lượng:** 4 giờ tại lớp · **Deadline:** 23h59 (GMT+7) ngày lab, trừ khi Lab Coach thông báo khác
> **Đọc theo thứ tự:** README → [RULES](RULES.md) → [CHECKPOINTS](CHECKPOINTS.md) → [SUBMISSION](SUBMISSION.md) → [RUBRIC](RUBRIC.md)
> **Bài nộp:** repo `K5-<L3A|L3B>-DAY14-HoVaTen-MSSV-Deployment-Benchmark-Observability`, nộp **link repo** trên LMS (chi tiết: [SUBMISSION.md](SUBMISSION.md)).

---

## Cấu Trúc Project

```
K5-L3-Day14-Deployment-Agent-Benchmark-Observability/
├── 01-localhost-vs-production/     # Section 1: Dev ≠ Production
│   ├── develop/                      #   Agent "đúng kiểu localhost"
│   └── production/                   #   12-Factor compliant agent
│
├── 02-docker/                      # Section 2: Containerization
│   ├── develop/                      #   Dockerfile đơn giản
│   └── production/                   #   Multi-stage + Docker Compose stack
│
├── 03-cloud-deployment/            # Section 3: Cloud Options
│   ├── railway/                    #   Deploy Railway (< 5 phút)
│   ├── render/                     #   Deploy Render + render.yaml
│   └── production-cloud-run/         #   GCP Cloud Run + CI/CD
│
├── 04-api-gateway/                 # Section 4: Security
│   ├── develop/                      #   API Key authentication
│   └── production/                   #   JWT + Rate Limiting + Cost Guard
│
├── 05-scaling-reliability/         # Section 5: Scale & Reliability
│   ├── develop/                      #   Health check + graceful shutdown
│   └── production/                   #   Stateless + Redis + Nginx LB
│
├── 06-lab-complete/                # Lab 14: Production-ready agent
│   ├── (bản khung TODO — sinh viên tự làm, chấm bằng check_production_ready.py)
│   └── benchmark-observability/      #   Part 7: Benchmark & Observability
│       ├── develop/                  #     Metrics + load test + eval (chạy local)
│       └── production/               #     Prometheus + Grafana + Jaeger + Locust
│
├── Dockerfile_examples/            # Ví dụ Dockerfile (Go) + thứ tự layers
│   ├── Dockerfile                    #   Single-stage, COPY . . (chưa tối ưu)
│   ├── Dockerfile.deps-first         #   Dependencies trước, source sau (tối ưu)
│   └── Dockerfile.source-first       #   Source trước, dependencies sau (không tối ưu)
│
└── utils/                          # Mock LLM dùng chung (không cần API key)
```

---

## 🚀 Bắt Đầu Nhanh

**Muốn thử ngay?** → [QUICK_START.md](QUICK_START.md) (5 phút)

**Muốn học kỹ?** → [CODE_LAB.md](CODE_LAB.md) (4-5 giờ)

## Cách Học

| Bước | Làm gì |
|------|--------|
| 0 | **[Khuyến nghị]** Đọc [QUICK_START.md](QUICK_START.md) để thử nhanh |
| 1 | Đọc [CODE_LAB.md](CODE_LAB.md) để hiểu chi tiết |
| 2 | Chạy ví dụ **basic** trước — hiểu concept |
| 3 | So sánh với ví dụ **advanced** — thấy sự khác biệt |
| 4 | Tự làm Lab 06 từ bản khung, chạy `python check_production_ready.py` tới khi `PASS 12/12` |
| 4b | Benchmark và giám sát agent với `06-lab-complete/benchmark-observability`, điền Benchmark Report |
| 5 | Tham khảo [QUICK_REFERENCE.md](QUICK_REFERENCE.md) khi cần |
| 6 | Xem [TROUBLESHOOTING.md](TROUBLESHOOTING.md) khi gặp lỗi |

---

## Yêu Cầu

```bash
python 3.11+
docker & docker compose
```

Mỗi folder có `requirements.txt` riêng. Không cần API key thật — các ví dụ dùng **mock LLM** để chạy offline.

---

## Sections

| # | Folder | Concept chính |
|---|--------|--------------|
| 1 | `01-localhost-vs-production` | Dev/prod gap, 12-factor, secrets |
| 2 | `02-docker` | Dockerfile, multi-stage, docker-compose |
| 3 | `03-cloud-deployment` | Railway, Render, Cloud Run |
| 4 | `04-api-gateway` | Auth, rate limiting, cost protection |
| 5 | `05-scaling-reliability` | Health check, stateless, rolling deploy |
| 6 | `06-lab-complete` | **Final project: tự xây production agent từ bản khung TODO** |
| 7 | `06-lab-complete/benchmark-observability` | Load test, eval, Prometheus, Grafana, OpenTelemetry, alerts |

---

## 📚 Lab Materials

Chúng tôi đã chuẩn bị đầy đủ tài liệu hướng dẫn:

### Cho Sinh Viên

| Tài liệu | Mô tả | Thời gian |
|----------|-------|-----------|
| **[CODE_LAB.md](CODE_LAB.md)** | Hướng dẫn lab chi tiết từng bước | 4-5 giờ |
| **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** | Cheat sheet các lệnh và patterns | Tra cứu |
| **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** | Giải quyết lỗi thường gặp | Khi cần |

### Cho Giảng Viên

| Tài liệu | Mô tả |
|----------|-------|
| **[INSTRUCTOR_GUIDE.md](INSTRUCTOR_GUIDE.md)** | Hướng dẫn chấm điểm và đánh giá |

### Cách Sử Dụng

1. **Trước lab:** Đọc [CODE_LAB.md](CODE_LAB.md) để hiểu tổng quan
2. **Trong lab:** Làm theo từng Part, tham khảo [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
3. **Gặp lỗi:** Xem [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
4. **Sau lab:** Nộp Part 6 Final Project và Part 7 Benchmark Report để chấm điểm (xem [DAY14_DELIVERY_CHECKLIST.md](DAY14_DELIVERY_CHECKLIST.md))
