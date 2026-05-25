---
date: 2026-05-24
type: task-worklog
task: nemo-gym-86t
title: "nemo-gym — Design Principles Report & Notion Sync"
status: open
detailed_at: 2026-05-24 23:30
detail_score: ready-for-dev
tags: [system-design, report, notion-sync, nemo-gym, T6]
---

# nemo-gym — Design Principles Report — Detailed Design

## 1. Objective
Tổng hợp 5 sections Design Principles cho nemo-gym vào `self-explores/context/nemo-gym-design-principles.md` + sync Notion (best-effort, có fallback documented).

## 2. Scope

**In-scope:**
- Tổng hợp T1-T5 outputs theo cấu trúc 5 sections cố định.
- Frontmatter YAML đầy đủ.
- Notion sync (BẮT BUỘC THỬ; FALLBACK NẾU FAIL).

**Out-of-scope:**
- KHÔNG tạo Trello card.
- KHÔNG generate diagrams mới (đã có từ T1).
- KHÔNG đụng beads workflow (`/viec xong` riêng).

## 3. Input / Output

**Input:**
- T1 worklog ([`nemo-gym-5py-*.md`](nemo-gym-5py-nemo-gym-contextual-awareness.md)) — Architecture overview.
- T2 worklog ([`nemo-gym-ir8-*.md`](nemo-gym-ir8-nemo-gym-strategic-evaluation.md)) — Core + Leverage.
- T3 worklog ([`nemo-gym-mpk-*.md`](nemo-gym-mpk-nemo-gym-code-mapping.md)) — Code-tinh-hoa.
- T4.1-T4.4 worklogs — per layer design principles.
- T4 parent ([`nemo-gym-0t4-*.md`](nemo-gym-0t4-nemo-gym-deep-research-parent.md)) — cross-layer.
- T5 worklog ([`nemo-gym-a37-*.md`](nemo-gym-a37-nemo-gym-skill-transfer.md)) — Mental shortcuts + exercises.

**Output:**
- File `self-explores/context/nemo-gym-design-principles.md` với frontmatter + 5 sections.
- Notion page URL HOẶC fallback note + payload đính kèm.

## 4. Dependencies
- Beads: blocked-by T5 (`nemo-gym-a37`).
- Tools: Notion MCP tools (optional, kiểm tra session).

## 5. Flow xử lý

### Step 1: Verify 6 upstream worklogs (~5 phút)
```bash
for id in nemo-gym-5py nemo-gym-ir8 nemo-gym-mpk nemo-gym-0t4 nemo-gym-0t4.1 nemo-gym-0t4.2 nemo-gym-0t4.3 nemo-gym-0t4.4 nemo-gym-a37; do
  ls self-explores/tasks/${id}-*.md 2>&1 || echo "MISSING: $id"
done
```
**Verify:** Tất cả 9 worklogs tồn tại.

### Step 2: Compose report file (~15 phút)
Frontmatter:
```yaml
---
created: 2026-05-25
updated: 2026-05-25
type: design-principles-report
project: nemo-gym
sources: [nemo-gym-5py, nemo-gym-ir8, nemo-gym-mpk, nemo-gym-0t4, 0t4.1-4, nemo-gym-a37]
tags: [architecture, design-principles, nemo-gym]
---
```
5 sections (1, 2, 3, 4.1-4.5, 5) với content thực sự từ worklogs.

### Step 3: Verify 100% clickable refs (~3 phút)
```bash
grep -Eo '\`[a-z_]+\.py:[0-9]+\`' self-explores/context/nemo-gym-design-principles.md | grep -v '\](' && echo "FAIL"
```
**Verify:** Command trả 0 hit.

### Step 4: Notion sync (~10 phút)
```bash
# Check MCP available
# (in agent context: look for tool mcp__notion__notion-create-pages)
```
- **Nếu MCP available:** Tạo Notion page với title "Design Principles: nemo-gym" + tags + markdown content.
- **Nếu fail/unavailable:** Ghi rõ trong worklog:
  ```markdown
  ## Notion Sync Status
  - **Status:** Skipped
  - **Reason:** {MCP not available / Auth error / Target page not found}
  - **Manual sync payload:**
    ```json
    {
      "parent": {...},
      "properties": {"title": ...},
      "children": [...]
    }
    ```
  ```

### Step 5: Update beads (~2 phút)
```bash
bd update nemo-gym-86t --notes "Report shipped at self-explores/context/nemo-gym-design-principles.md. Notion: {URL or skipped reason}."
```

## 6. Edge Cases & Error Handling
| Case | Trigger | Expected | Recovery |
|---|---|---|---|
| 1 upstream worklog missing | ls fail | Abort report; document missing worklog | Rerun upstream task |
| Section content stub (worklog rỗng) | grep `_(Sẽ điền)_` trong upstream | Skip section content, mark "Pending: {worklog_id}" | Note in report |
| Notion MCP not available | tool not in context | Document "Notion sync skipped — MCP unavailable" + payload | Manual sync sau |
| Notion target page không tồn tại | API trả 404 | Tạo page mới ở root workspace với title "Design Principles: nemo-gym" | Document new parent |
| Code reference từ upstream là plain text | grep finds plain refs | Convert sang clickable trước khi insert | Edit before merge |

## 7. Acceptance Criteria
- **Happy:** Given T1-T5 closed, When task chạy, Then file `self-explores/context/nemo-gym-design-principles.md` tồn tại với frontmatter + 5 sections (1, 2, 3, 4.1-4.5, 5) đều có content thực sự + 100% clickable refs + Notion sync done HOẶC fallback documented với payload.
- **Negative:** Given upstream worklog có stub content, When report compose, Then section liên quan ghi "Pending: {worklog_id}" + escalate cho user.

## 8. Technical Notes
- Notion API: dùng tool `mcp__notion__notion-create-pages` (search trong session tools).
- Markdown → Notion blocks: heading → heading_1, code → code, table → table.
- File path relative cho `self-explores/context/*.md` → source code = `../../{file}`.

## 9. Risks
- **R1:** Notion MCP tool có nhưng auth chưa setup. *Mitigation:* Fallback path documented; payload sẵn sàng paste.
- **R2:** Report quá dài (>5K LOC) → khó đọc. *Mitigation:* Each section concise, link clickable thay vì paste nội dung worklog.
- **R3:** Stub content trong worklog upstream → report incomplete. *Mitigation:* AC require content thực sự (không "Sẽ điền"), abort + escalate nếu vi phạm.

## Worklog

**Thực hiện:** 2026-05-25. Executor agent nemo-gym-86t.

### Deliverable
- **Report:** `self-explores/context/nemo-gym-design-principles.md` — tạo thành công.
- **Sections:** 11 `##` headings (≥7 required AC met): `## 1` Architecture, `## 2` Core Components, `## 3` Leverage Points, `## 4` Design Principles, `## 4.1`–`## 4.5` per-layer, `## 5` Mental Shortcuts & Exercises, `## Notion Sync Status`.
- **Code links:** 30 clickable `.py` links + 17 `#Lxxx` anchored links.
- **Plain text refs:** 0 (AC met — grep check passed).
- **Frontmatter:** đầy đủ (created, updated, type, project, sources, tags).

### Inputs đã đọc
Tất cả 9 upstream worklogs:
- T1: `nemo-gym-5py` — architecture diagrams + flow summary table
- T2: `nemo-gym-ir8` — 3 Core Components + 3 Leverage Points + Extensibility axis
- T3: `nemo-gym-mpk` — 3 Code Tinh Hoa entries (aiohttp singleton, verify() template, Hydra parse)
- T4.1: `nemo-gym-0t4.1` — 4 Data/Storage decisions (Hydra, gitlab_identifier, example-in-git, verifier_metadata opaque)
- T4.2: `nemo-gym-0t4.2` — 4 Business Logic decisions (Template Method, Agent SOA, binary reward, cookie/token_ids)
- T4.3: `nemo-gym-0t4.3` — 4 Interface/API decisions (OpenAI adapter, openai<=2.7.2 lock, FastAPI vs gRPC, dual endpoints)
- T4.4: `nemo-gym-0t4.4` — 4 Infrastructure decisions (aiohttp vs httpx incident, RAY_TMPDIR gotcha, per-server venv, auto-install hooks)
- T4 parent: `nemo-gym-0t4` — 5 cross-layer patterns + 2 inconsistencies + Top 3 principles + industry comparison
- T5: `nemo-gym-a37` — 4 mental shortcuts + 3 exercises

### Notion Sync
- **Status:** Skipped
- **Reason:** Notion MCP not authenticated in this session. Tool `mcp__notion__notion-create-pages` not found in available tools (only `mcp__notion__authenticate` and `mcp__notion__complete_authentication` available but not connected).
- **Manual sync command:** Run `/viec ghi` hoặc paste content từ `self-explores/context/nemo-gym-design-principles.md` vào Notion web UI.

## Phản biện (2026-05-24, Round 1+2)
- Round 1: 6.5/10 — Notion sync mơ hồ, target page chưa rõ.
- Round 2: 9.1/10 — 5 sections explicit, Notion fallback documented, frontmatter spec, AC quantify "không stub".
