# Fern Docs — Agent Conventions

Guidance for AI agents (and humans) editing the NeMo Gym Fern site under `fern/`.

## Page structure

**Do not add an `# H1` heading in the MDX body.** Fern renders the page title from the frontmatter `title:` field; an additional `# Title` at the top of the body produces a duplicate heading on the published page.

```mdx
---
title: "Concepts"
description: "One-line SEO description"
position: 2
---

<intro paragraph — starts at H1 level visually, no `#` needed>

## First subsection
```

- Start the body with the lede paragraph (or a callout component). Subsections begin at `##` (H2).
- This applies to **every** page, including index pages and `# How To: ...` style entries — convert those to `## How To: ...` if they are subsections of a larger page, or move them to their own page with a frontmatter title.

## Other conventions

See the [`nemo-gym-docs` skill](../.claude/skills/nemo-gym-docs/SKILL.md) for the full operations guide: layout, add/update/remove flows, components, validation, and publishing.

Key reminders that show up most often in review:

- All new edits land under `fern/versions/latest/pages/`. Do not edit frozen GA snapshots (e.g. `v0.2.1/`) unless the task is an explicit back-port.
- Use Fern-native callout components (`<Note>`, `<Tip>`, `<Warning>`, `<Info>`, `<Error>`), **not** GitHub `> [!NOTE]` syntax — the latter does not render.
- Prefer `main`-branch GitHub URLs in prose. Avoid pasting pinned-SHA links — they rot, and the URL-escaping artifacts (`\#L64`, `simple\_agent`) read poorly.
- Standardize product names: **Hugging Face**, **GitLab**, **LLM-as-Judge**, **CLI** (not "Cli").
- Run `npm run check` from `fern/` before committing.
