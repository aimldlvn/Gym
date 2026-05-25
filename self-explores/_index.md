---
created: 2026-05-24
updated: 2026-05-24
project: nemo-gym
---

# Project Context Index

Folder này lưu trữ learnings, decisions, và context quan trọng của dự án NeMo-Gym.
Claude sessions sau sẽ đọc folder này để hiểu bối cảnh.

## Cấu trúc

- `decisions/` — Quyết định quan trọng (architecture, library choice, trade-offs)
- `learnings/` — Kiến thức học được (debug fixes, gotchas, patterns)
- `context/` — Bối cảnh dự án (domain knowledge, constraints, stakeholders)
- `daily/` — Nhật ký hàng ngày (review reports)
- `tasks/` — Context cho từng task (auto-captured outputs)
- `leverage/` — Phân tích đòn bẩy bất đối xứng
- `history/` — JSONL log cho mỗi lệnh `/viec`

## Cách sử dụng

- `/viec ghi` — Ghi chép mới (learning / decision / context)
- `/viec doc` — Đọc lại context
- `/viec xong` — Tự động hỏi learnings khi hoàn thành task
- `/viec review` — Tổng hợp vào daily log
- `/viec donbay` — Phân tích đòn bẩy

## Liên kết

- Task tracker: `bd list`, `bd ready`
- Backup: `.beads/backup/` (JSONL, auto mỗi 15 phút)
- Project docs: [[../CLAUDE.md]]
