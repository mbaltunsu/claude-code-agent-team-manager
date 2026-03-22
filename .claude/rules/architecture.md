# Architecture

## Overview

This is a Claude Code plugin that provides a team management system for AI agents. The plugin is distributed as a skill package under the `team:` namespace and follows the Claude Code plugin architecture.

## Key Components

### SKILL.md files (Claude orchestration layer)
Three skills, each a markdown file Claude reads when the command is invoked:
- `skills/init-team/SKILL.md` — full agent roster setup (8-step workflow with project context gathering)
- `skills/add-agent/SKILL.md` — focused single-agent add by filename or capability description
- `skills/init-project/SKILL.md` — project bootstrap (rules + CLAUDE.md from starter template)

Skills contain no logic — they are pure instructions for Claude to follow. All filesystem work is delegated to `init_team.py`.

### init_team.py (Python CLI layer)
Single-file Python CLI at `skills/init-team/scripts/init_team.py`. All three skills call this script for every filesystem operation. No third-party dependencies — stdlib only.

Subcommands: `scan`, `copy`, `add`, `remove`, `list`, `update`, `download`, `init-project`, `update-docs`, `import`, `source-list`, `source-add`, `source-remove`

### Central agents store
`~/.claude/team-management/agents/` — single location for all agents across projects. Structure mirrors the library: `categories/<category>/<agent>.md`.

### Sources registry
`~/.claude/team-management/sources.json` — tracks named agent sources (git repos). Pre-loaded with the official VoltAgent source. Supports custom sources.

### Plugin manifests
`.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` — Claude Code plugin identity and marketplace registration.

## Patterns

- **Separation of concerns**: SKILL.md files orchestrate, `init_team.py` executes — no logic in markdown
- **Merge-safe operations**: download and import never overwrite existing files
- **Lazy init**: sources registry and central store are created on first use, not on install
- **JSON-first CLI output**: all subcommands that produce data output JSON for skill parsing
- **Force flag pattern**: `update_project_files(force=True)` refreshes CLAUDE.md even with no new agents (used by `update-docs` and `init-project`)

## Constraints

- `init_team.py` must only use Python standard library — no pip installs
- Python 3.8+ compatibility — use `Optional[str]` from `typing`, not `str | None`
- All file I/O must use `encoding="utf-8"` explicitly
- Use `[OK]` / `[SKIP]` ASCII markers — never Unicode symbols (cross-platform)
- All path operations must use `pathlib.Path` — never string concatenation
- Tests use `tmp_path` only — never touch real agent library or home directory (use `patch`)
