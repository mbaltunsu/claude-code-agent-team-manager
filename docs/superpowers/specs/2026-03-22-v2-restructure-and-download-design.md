# V2: Restructure, Download Mode & Plugin Install

**Date:** 2026-03-22
**Status:** Draft

---

## Overview

Three tightly coupled changes to bring the plugin to industry standards:

1. **Rename skill file** `init-agents.md` → `SKILL.md`
2. **Add download subcommand** for users without a local agent library
3. **Rewrite README/docs** with clear folder structure and plugin install instructions

All delivered as a single unified refactor.

---

## 1. Repository Restructure

### File Changes

| Current Path | New Path | Action |
|---|---|---|
| `skills/init-agents/init-agents.md` | `skills/init-agents/SKILL.md` | Rename |
| `skills/init-agents/scripts/init_agents.py` | *(unchanged)* | Update internal paths |
| `.claude-plugin/marketplace.json` | *(unchanged)* | No changes needed |
| `.claude-plugin/plugin.json` | *(unchanged)* | No changes needed |
| `CLAUDE.md` | *(unchanged)* | Update references |
| `README.md` | *(unchanged)* | Full rewrite |
| *(new)* | `.gitignore` | Create |

### .gitignore

```
# Documentation (generated specs/plans)
docs/superpowers/

# Python
__pycache__/
*.pyc
*.pyo

# Environment
.env
```

### Final Repo Layout

```
claude-code-agent-team-manager/
├── .claude-plugin/
│   ├── marketplace.json
│   └── plugin.json
├── .gitignore
├── skills/
│   └── init-agents/
│       ├── SKILL.md                  ← renamed from init-agents.md
│       └── scripts/
│           ├── init_agents.py
│           ├── conftest.py
│           └── tests/
│               ├── test_path_resolution.py
│               ├── test_scan.py
│               ├── test_copy.py
│               └── test_download.py  ← new
├── docs/
│   └── superpowers/
│       ├── specs/
│       └── plans/
├── CLAUDE.md
├── README.md
└── .env.example
```

---

## 2. Download Subcommand

### Interface

```
python scripts/init_agents.py download [--dest <path>] [--repo <url>]
```

| Flag | Default | Description |
|---|---|---|
| `--dest` | `~/.claude/agent-library/` | Where to store downloaded agents |
| `--repo` | `https://github.com/VoltAgent/awesome-claude-code-subagents.git` | Source repo |

### Behavior

1. **Check git is available** on PATH. Exit with clear error if not.
2. **Create dest directory** if it doesn't exist.
3. **Git sparse-checkout** to fetch only `categories/` from the repo:
   - Clone with `--filter=blob:none --no-checkout --depth=1`
   - Configure sparse-checkout for `categories/`
   - Checkout
4. **Merge mode**: If dest already has a `categories/` folder:
   - Walk the downloaded `categories/`
   - Copy only files that don't already exist at the destination
   - Skip existing files (never overwrite)
5. **Clean up** the temporary git clone directory.
6. **Output JSON** result to stdout:
   ```json
   {
     "downloaded": ["categories/01-core/backend-developer.md", ...],
     "skipped": ["categories/01-core/frontend-developer.md", ...],
     "dest": "/home/user/.claude/agent-library"
   }
   ```

### Error Cases

- `git` not found → `{"error": "git is required but not found on PATH"}`
- Network failure → `{"error": "Failed to clone repository: <details>"}`
- Invalid repo URL → `{"error": "Repository not found: <url>"}`
- Permission denied on dest → `{"error": "Cannot write to <dest>: permission denied"}`

---

## 3. SKILL.md Workflow Update

The renamed SKILL.md will update **Step 2** (library path resolution):

### Current Step 2
1. Look for `AGENTS_LIBRARY_PATH` in `.env`
2. If not found → prompt user for path

### New Step 2
1. Look for `AGENTS_LIBRARY_PATH` in `.env`
2. If not found → ask user: **"Do you have a local agent library?"**
   - **Yes** → prompt for path, save to `.env`
   - **No** → run `download` subcommand with defaults → set `AGENTS_LIBRARY_PATH=~/.claude/agent-library/` in `.env`
3. Continue with scan as before

All other steps remain the same, with path references updated from `skills/init-agents/scripts/init_agents.py` to the correct relative path.

---

## 4. README Rewrite

### Key Sections

**Installation:**
```
/plugin install https://github.com/mbaltunsu/claude-code-agent-team-manager
```

**Agent Library Format** (clear, explicit):
```
your-agent-library/
└── categories/
    ├── 01-core-development/
    │   ├── backend-developer.md
    │   └── frontend-developer.md
    ├── 02-language-specialists/
    │   └── python-expert.md
    └── <any-category-folder>/
        └── <any-agent>.md
```

Each `.md` file requires YAML frontmatter:
```yaml
---
name: Backend Developer
description: Specializes in server-side development...
---
```

**No Agent Library?** section:
- Explains auto-download from VoltAgent's awesome-claude-code-subagents
- Default destination: `~/.claude/agent-library/`
- Merge-safe: never overwrites existing agents

---

## 5. CLAUDE.md Updates

- Update file path references (`init-agents.md` → `SKILL.md`)
- Update repo structure diagram
- No changes to conventions, commit style, or development workflow

---

## Testing

### New Tests (`test_download.py`)

- `test_download_creates_dest_dir` — dest is created if missing
- `test_download_calls_git_sparse_checkout` — correct git commands issued
- `test_download_merge_skips_existing` — existing files not overwritten
- `test_download_git_not_found` — clear error when git missing
- `test_download_network_failure` — graceful error on clone failure
- `test_download_custom_repo_url` — `--repo` flag works
- `test_download_json_output` — output contains downloaded/skipped/dest

### Existing Tests

All existing tests (`test_scan.py`, `test_copy.py`, `test_path_resolution.py`) should continue passing — internal logic unchanged, only file locations and skill filename change.

---

## Out of Scope

- Agent library versioning or update checking
- Authentication for private repos
- Non-git download methods (HTTP/zip fallback)
- Auto-updating already-downloaded agents
- MCP server functionality
