# Rubric — Day 14: Deployment, Benchmark & Observability

> Bài **cá nhân**. Bảng điểm khớp [INSTRUCTOR_GUIDE.md](INSTRUCTOR_GUIDE.md) và [DAY14_DELIVERY_CHECKLIST.md](DAY14_DELIVERY_CHECKLIST.md).
> **Tổng thô 120**, quy về thang 100: `Điểm = Tổng thô × 100 / 120` (làm tròn 0,5). **Đạt:** 70/100 (tương đương 84/120).
> **Cách chấm:** mở link repo nộp trên LMS, chấm commit cuối trước deadline. Bước đầu tiên là chạy `python check_production_ready.py` trong `06-lab-complete/` trên máy có Docker.

## Điểm chính

| Hạng mục | Điểm | Checkpoint | Bằng chứng |
| --- | ---: | --- | --- |
| Part 1 — Localhost vs Production | 8 | CP1 | `MISSION_ANSWERS.md` mục Part 1 |
| Part 2 — Docker | 8 | CP2 | `MISSION_ANSWERS.md` mục Part 2, có số MB đo được |
| Part 3 — Cloud Deployment | 8 | CP6 | `MISSION_ANSWERS.md` mục Part 3, URL public trả lời được |
| Part 4 — API Security | 8 | CP3 | `MISSION_ANSWERS.md` mục Part 4, có output 401 / 200 / 429 |
| Part 5 — Scaling & Reliability | 8 | CP4 | `MISSION_ANSWERS.md` mục Part 5 |
| **Part 6 — Final Project** | **60** | CP5, CP6 | `06-lab-complete/` báo `PASS 12/12`; `DEPLOYMENT.md` có URL chạy được; ảnh trong `screenshots/` |
| Part 7 — Load test & SLO | 4 | CP7 | Bảng 4 mức concurrency (RPS, p50/p95/p99, error rate); so sánh `MOCK_SLOW_RATE` |
| Part 7 — Eval & quality gate | 5 | CP7 | v1 vs v2; v2 đạt 23/23 không regression; cách dùng exit code để chặn merge |
| Part 7 — Observability stack | 4 | CP8 | Ảnh Grafana có tải; trả lời Exercise 7.4 |
| Part 7 — Tracing | 3 | CP8 | Ảnh trace chậm (span chậm nhất + số ms); `trace_id` khớp một dòng log JSON |
| Part 7 — Alerts & chaos | 4 | CP8 | Ảnh ≥ 2 alert firing + thời gian tới lúc firing; phân tích thí nghiệm |
| **Tổng thô** | **120** | | |

Chi tiết chấm từng mục (tiêu chí con, đáp án mong đợi) nằm trong [INSTRUCTOR_GUIDE.md](INSTRUCTOR_GUIDE.md).

## Part 6 và script chấm

- Mục nào `check_production_ready.py` báo ❌ thì bị trừ điểm phần tương ứng. Mục ⚠️ (không kiểm tra được, ví dụ thiếu Docker) cũng tính là chưa đạt.
- Sửa `check_production_ready.py` để lấy `PASS`: Part 6 bị 0 điểm.

## Bonus

Lab này không có bonus. Các mục "Mở rộng" ở Part 6 (lưu history trong Redis, streaming, Nginx + 3 instance) không tính điểm.

## Trừ điểm và điều kiện không chấm

| Tình huống | Xử lý |
| --- | --- |
| Commit `.env`, API key hoặc token deploy (kể cả trong lịch sử commit) | −10 điểm; phải thu hồi (revoke) và tạo key mới. Xoá file thôi không đủ |
| Số liệu trong `BENCHMARK_REPORT.md` không khớp file JSON/CSV đã nộp | Mục Part 7 tương ứng 0 điểm |
| Sai tên repo hoặc sai chỗ file (xem [SUBMISSION.md](SUBMISSION.md)) | −5 điểm nếu vẫn tìm được bài; không chấm nếu không tìm được |
| Repo private, Lab Coach không mở được | Không chấm |
| Nộp muộn, sửa sau deadline, sao chép, dùng AI không khai báo | Theo [RULES.md](RULES.md) |
