---
name: skill-creator
description: Scaffold new OpenCode skills with correct layout, frontmatter, and validation. Use ONLY when creating, fixing, or reviewing a skill (SKILL.md) under .opencode/skills or global skills dirs. Trigger keywords: new skill, SKILL.md, skill frontmatter.
---

# Skill Creator

You create other skills. A skill is a folder containing exactly one `SKILL.md`
file, discovered on demand via the `skill` tool.

## Where skills live

| Scope   | Path (folder named after the skill)      |
| ------- | ---------------------------------------- |
| Project | `.opencode/skills/<name>/SKILL.md`       |
| Global  | `~/.config/opencode/skills/<name>/SKILL.md` |

Also auto-scanned (Claude-compatible): `.claude/skills/`, `.agents/skills/`,
and their `~/` global counterparts. Prefer `.opencode/skills/` for new work.

## Naming (strict — invalid names never load)

- Directory name and `name:` frontmatter must match exactly.
- Regex: `^[a-z0-9]+(-[a-z0-9]+)*$` (lowercase alnum, single hyphens, 1–64 chars).
- `SKILL.md` is all caps. Names must be unique across all locations.

## Template

```markdown
---
name: my-skill
description: What it does AND when to load it, third person. Front-load literal trigger keywords and filenames. Gate noisy skills with "Use ONLY when...".
---

# My Skill

## What I do
- ...

## When to use me
- ...

## Workflow / reference
- Steps, commands, file paths the consumer needs.
```

- `name` (required), `description` (required, 1–1024 chars). Skills without a
  description are filtered out and never surface.
- Optional: `license`, `compatibility`, `metadata` (string-to-string map).
  Unknown frontmatter fields are ignored.
- Write `description` in third person ("Use when..."), never first person.
- Keep the body task-focused: instructions, examples, paths. No chatty preamble.

## Workflow for a new skill

1. Confirm the trigger: what user request or file pattern should load this skill?
   If you cannot state it in one sentence, the skill is too broad — split it.
2. Pick a valid `name`, `mkdir -p .opencode/skills/<name>`.
3. Write `SKILL.md` from the template above.
4. Validate: name == directory, `SKILL.md` caps, description present and gated,
   no unknown frontmatter relied upon.
5. Permissions (only if needed) go in `opencode.json` under
   `permission.skill`, e.g. `{ "experimental-*": "ask" }`. Validate shapes
   against `https://opencode.ai/config.json` — opencode hard-fails on bad config.

## Gotchas

- Skills (like all config) load once at startup. After adding or changing one,
  tell the user to quit and restart opencode; the running session will not see it.
- To disable the `skill` tool for an agent: `tools: { skill: false }` (file agent)
  or `"agent": { "<name>": { "tools": { "skill": false } } }` (opencode.json).
- If a skill does not show up: check caps spelling, `name`/`description`
  presence, name uniqueness, and `permission.skill` deny rules.
