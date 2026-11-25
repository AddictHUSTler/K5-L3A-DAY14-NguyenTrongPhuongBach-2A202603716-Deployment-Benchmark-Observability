# Checkpoints — Day 14

> 👤 **Cá nhân** · **4 giờ tại lớp** · Deadline: xem [SUBMISSION.md](SUBMISSION.md#deadline).
> Nội dung từng bài tập giữ nguyên trong [CODE_LAB.md](CODE_LAB.md). File này chỉ chia giờ để vừa 4 tiếng và nói rõ mỗi mốc phải có gì.

`CODE_LAB.md` ghi tổng 335 phút (Part 1–7). Để vừa 240 phút, lịch dưới đây làm ba việc:

1. Rút ngắn Part 1, 2, 4, 5: chạy ví dụ có sẵn và trả lời câu hỏi vào `MISSION_ANSWERS.md`, không tự viết lại code mẫu.
2. Đưa **Part 3 (deploy) ra sau Part 6** và deploy luôn agent Part 6, thay vì deploy app mẫu trong `03-cloud-deployment/` rồi deploy lại lần nữa. Exercise 3.3 (Cloud Run) là tuỳ chọn, bỏ qua.
3. Làm **Part 7 Bước 1** (chạy local, Exercise 7.1–7.3) tại lớp. **Part 7 Bước 2** (Docker stack Grafana/Jaeger/alerts, Exercise 7.4–7.7) làm sau giờ lab, trước deadline.

| Giờ | Checkpoint | Phần trong `CODE_LAB.md` | Thời gian |
| --- | --- | --- | ---: |
| 0:00 | CP0 · Setup | Fork, đổi tên repo, cài Python + Docker | 10' |
| 0:10 | CP1 · Localhost vs Production | Part 1 (Exercise 1.1–1.3) | 20' |
| 0:30 | CP2 · Docker | Part 2 (Exercise 2.1–2.4) | 30' |
| 1:00 | CP3 · API Security | Part 4 (Exercise 4.1–4.4) | 25' |
| 1:25 | CP4 · Scaling & Reliability | Part 5 (Exercise 5.1–5.5) | 20' |
| 1:45 | Nghỉ | | 5' |
| 1:50 | CP5 · Final Project | Part 6, `06-lab-complete/` → `PASS 12/12` | 60' |
| 2:50 | CP6 · Cloud Deployment | Part 3, deploy agent Part 6 → `DEPLOYMENT.md` | 25' |
| 3:15 | CP7 · Benchmark local | Part 7 Bước 1 (Exercise 7.1–7.3) | 45' |
| Sau lab | CP8 · Observability stack + nộp | Part 7 Bước 2 (Exercise 7.4–7.7), đóng gói | trước deadline |

Kẹt quá 10 phút ở một mốc: gọi Lab Coach, ghi lại lỗi, rồi đi tiếp mốc sau. CP5 là phần nhiều điểm nhất (60/120), không để CP1–CP4 lấn sang giờ của CP5.

## CP0 — Setup (0:00 → 0:10)

- **Mục tiêu:** có repo bài làm đúng tên và máy chạy được Python, Docker.
- **Cần làm:** fork repo, đổi tên theo [SUBMISSION.md](SUBMISSION.md#tên-repository), clone bản fork. Kiểm tra `python --version` (3.11+), `docker compose version`. Đọc mục *Lưu ý khi làm bài* trong [README.md](README.md).
- **Sản phẩm:** repo đã đổi tên, clone về máy.
- **Tự kiểm tra:** `docker run --rm hello-world` chạy được. Không có Docker thì vẫn làm được CP1, CP3, CP7, nhưng CP2, CP5 (phần build image) và CP8 cần Docker: báo Lab Coach ngay.

## CP1 — Localhost vs Production (0:10 → 0:30)

- **Mục tiêu:** chỉ ra được vì sao code chạy trên laptop chưa sẵn sàng cho production.
- **Cần làm:** Part 1, Exercise 1.1–1.3 trong `01-localhost-vs-production/`.
- **Sản phẩm:** mục Part 1 trong `MISSION_ANSWERS.md` (danh sách anti-pattern, bảng so sánh develop/production).
- **Cần hiểu:** vì sao hardcode secret nguy hiểm; vì sao cần health check và graceful shutdown.
- **Tự kiểm tra:** chỉ ra được ít nhất một anti-pattern trong `develop/app.py` mà `production/app.py` đã sửa, kèm dòng code.

## CP2 — Docker (0:30 → 1:00)

- **Mục tiêu:** đóng gói agent thành image nhỏ, chạy giống nhau ở mọi máy.
- **Cần làm:** Part 2, Exercise 2.1–2.4 trong `02-docker/`.
- **Sản phẩm:** mục Part 2 trong `MISSION_ANSWERS.md`, có kích thước image develop và production đo bằng `docker images`.
- **Cần hiểu:** multi-stage giảm dung lượng ở đâu; vì sao `COPY requirements.txt` phải đứng trước `COPY . .`.
- **Tự kiểm tra:** số MB trong bài là số bạn đo được, không chép từ README.

## CP3 — API Security (1:00 → 1:25)

- **Mục tiêu:** chặn được truy cập trái phép, gọi quá nhanh và tiêu quá ngân sách.
- **Cần làm:** Part 4, Exercise 4.1–4.4 trong `04-api-gateway/`. Exercise 4.2 (JWT) đọc hiểu, không bắt buộc chạy.
- **Sản phẩm:** mục Part 4 trong `MISSION_ANSWERS.md`, dán output curl của các trường hợp 401, 200, 429.
- **Cần hiểu:** rate limit bảo vệ tốc độ, cost guard bảo vệ tiền; vì sao cần cả hai.
- **Tự kiểm tra:** thấy được 429 bằng vòng lặp curl của chính mình.

## CP4 — Scaling & Reliability (1:25 → 1:45)

- **Mục tiêu:** chạy được nhiều instance mà không mất state, tắt không cắt ngang request.
- **Cần làm:** Part 5, Exercise 5.1–5.5 trong `05-scaling-reliability/`.
- **Sản phẩm:** mục Part 5 trong `MISSION_ANSWERS.md`.
- **Cần hiểu:** liveness (`/health`) khác readiness (`/ready`) ở đâu; vì sao state trong RAM hỏng khi chạy nhiều instance.
- **Tự kiểm tra:** sau `docker compose up --scale agent=3` (Exercise 5.4), chạy `production/test_stateless.py` và giải thích kết quả.

## CP5 — Final Project (1:50 → 2:50)

- **Mục tiêu:** tự ráp mọi phần trên thành một agent production đạt đủ 12 tiêu chí.
- **Cần làm:** Part 6. Sửa các chỗ `TODO` trong `06-lab-complete/` theo thứ tự gợi ý ở [06-lab-complete/README.md](06-lab-complete/README.md). Làm ngay trong thư mục đó, không chuyển code ra chỗ khác.
- **Sản phẩm:** `python check_production_ready.py` (chạy trong `06-lab-complete/`, có Docker) báo **`PASS 12/12`**. Dán phần "📋 Checklist Deliverable" của output vào `MISSION_ANSWERS.md`.
- **Cần hiểu:** từng tiêu chí trong mục *Script chấm dựa vào những tiêu chí dưới đây* của `06-lab-complete/README.md`, đặc biệt vì sao `/health` phải trả 200 khi Redis chết còn `/ready` phải trả 503.
- **Tự kiểm tra:** chạy `python check_production_ready.py --static-only` sớm và chạy lại sau mỗi bước; chạy bản đầy đủ trước khi sang CP6.

## CP6 — Cloud Deployment (2:50 → 3:15)

- **Mục tiêu:** agent Part 6 chạy trên cloud với URL public, có Redis và API key.
- **Cần làm:** Part 3, Exercise 3.1 (Railway) **hoặc** 3.2 (Render), nhưng deploy thư mục `06-lab-complete/` (dùng `railway.toml` hoặc `render.yaml` bạn viết ở CP5), không deploy app mẫu `03-cloud-deployment/`. Cách làm và phần Redis: mục *Lưu ý khi làm bài* số 2 trong [README.md](README.md). Đặt `AGENT_API_KEY` bằng biến môi trường trên nền tảng, không ghi vào code.
- **Sản phẩm:** `DEPLOYMENT.md` theo mẫu trong [DAY14_DELIVERY_CHECKLIST.md](DAY14_DELIVERY_CHECKLIST.md) mục 3; ảnh trong `screenshots/`; URL điền vào mục Part 3 của `MISSION_ANSWERS.md`.
- **Tự kiểm tra:** từ máy khác (hoặc điện thoại): `GET /health` và `GET /ready` trả 200; `POST /ask` không có `X-API-Key` trả 401, có key trả 200. Đủ các lệnh ở mục Self-Test của [DAY14_DELIVERY_CHECKLIST.md](DAY14_DELIVERY_CHECKLIST.md).

## CP7 — Benchmark local (3:15 → 4:00)

- **Mục tiêu:** đo được agent nhanh tới đâu và đúng tới đâu bằng số của chính mình.
- **Cần làm:** Part 7 Bước 1 trong `06-lab-complete/benchmark-observability/develop/` (Exercise 7.1–7.3): chạy agent v1 và v2, load test 4 mức concurrency, eval v1/v2, sửa `KNOWLEDGE_BASE` cho tới khi v2 đạt 100% không regression.
- **Sản phẩm:** `reports/load_v2_c*.json`, `reports/eval_v1.json`, `reports/eval_v2.json`, `reports/eval_v2_fixed.json`; bắt đầu điền `BENCHMARK_REPORT.md`.
- **Cần hiểu:** vì sao đặt SLO theo p95/p99 chứ không theo trung bình; vì sao "cost / câu đúng" tốt hơn "cost / câu" để so hai phiên bản.
- **Tự kiểm tra:** trong `develop/`, `python eval/run_eval.py --url http://localhost:8002 --min-accuracy 1.0` in `Quality gate ... ✅ PASS`.

## CP8 — Observability stack và nộp bài (sau giờ lab, trước deadline)

- **Mục tiêu:** nhìn được sức khoẻ agent khi chạy (metrics, trace, alert) và nộp đủ bằng chứng.
- **Cần làm:** Part 7 Bước 2 trong `06-lab-complete/benchmark-observability/production/` (Exercise 7.4–7.7): bật stack bằng Docker Compose, tạo tải bằng Locust, chụp Grafana, tìm 1 trace chậm và 1 trace lỗi trong Jaeger, làm cho ít nhất 2 alert firing, benchmark scale 1 và 3. Dọn stack khi xong (`docker compose down -v`).
- **Sản phẩm:** `BENCHMARK_REPORT.md` điền đủ, `benchmark-results/`, 4 ảnh Part 7 trong `screenshots/`. Đóng gói theo [SUBMISSION.md](SUBMISSION.md).
- **Tự kiểm tra:** mọi con số trong `BENCHMARK_REPORT.md` khớp với file JSON/CSV đã nộp.
