# Claude Code Agent Team Manager

A Claude Code skill + plugin that bootstraps the right agent files into a project from a central agent library. Scans the library, recommends agents using AI, copies approved agents to `.claude/agents/`, and tracks them in `TEAM.md`. Can auto-download agents from GitHub for users without a local library.

---

## Repository Structure

```
claude-code-agent-team-manager/
├── .claude-plugin/
│   ├── marketplace.json     ← plugin marketplace manifest
│   └── plugin.json          ← plugin identity and metadata
├── .gitignore
├── skills/
│   └── init-team/
│       ├── SKILL.md          ← Claude Code skill (orchestrates the 8-step workflow)
│       └── scripts/
│           ├── init_team.py         ← Python CLI: scan, copy, download subcommands
│           ├── conftest.py          ← pytest path and encoding setup
│           └── tests/
│               ├── test_path_resolution.py
│               ├── test_scan.py
│               ├── test_copy.py
│               └── test_download.py
├── docs/
│   └── superpowers/
│       ├── specs/           ← design specs (one per feature)
│       └── plans/           ← implementation plans
├── README.md
├── CLAUDE.md                ← this file
└── .env.example
```

---

## How It Works

Two components work together:

1. **`SKILL.md`** (skill file) — Claude reads this when `/init-team` is invoked. It orchestrates the 8-step workflow: detect Python → resolve library path (or download) → verify script → scan → read project context → recommend → wait for approval → copy and update docs.

2. **`init_team.py`** (Python CLI) — handles all filesystem operations. Three subcommands:
   - `scan --path <library>` — walks `categories/` in the agent library, reads frontmatter, returns JSON
   - `copy --agents <paths> --path <library> --dest <dir> --claude-md <file> --team-md <file>` — copies approved agents, skips existing ones, writes `TEAM.md`, adds a pointer in `CLAUDE.md`
   - `download [--dest <dir>] [--repo <url>]` — downloads agents from GitHub using git sparse-checkout, merge-safe (never overwrites)

---

## Development

### Requirements

- Python 3.8+
- pytest (`pip install pytest`)

### Running Tests

```bash
cd skills/init-team/scripts
pytest tests/ -v
```

All tests use `tmp_path` fixtures — no real agent library or project needed.

### Conventions

- **TDD**: write the failing test first, implement minimally, confirm green, commit
- **stdlib only**: `init_team.py` must not import anything outside the Python standard library
- **Python 3.8+**: use `Optional[str]` from `typing`, not `str | None`
- **Cross-platform**: use `Path` for all filesystem operations; `[OK]`/`[SKIP]` markers instead of Unicode symbols
- **One concern per test file**: `test_path_resolution.py`, `test_scan.py`, `test_copy.py`, `test_download.py`
- **UTF-8 everywhere**: all file reads and writes use `encoding="utf-8"`

### Commit style

```
feat: short description of what was added
fix: short description of what was corrected
docs: documentation-only changes
chore: scaffolding, tooling, config
```

---

## Plugin Installation (for users)

Add to `~/.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "agent-team-manager": {
      "source": {
        "source": "github",
        "repo": "mbaltunsu/claude-code-agent-team-manager"
      }
    }
  },
  "enabledPlugins": {
    "init-team@agent-team-manager": true
  }
}
```

Then run `/init-team` in any Claude Code project.

---

## Manual Installation (alternative)

Copy the skill folder into a project or globally:

```bash
# Per-project
cp -r skills/init-team/ /your/project/.claude/skills/

# Global
cp -r skills/init-team/ ~/.claude/skills/
```

---

## Agent Library Format

The skill expects an agent library with this structure:

```
<AGENTS_LIBRARY_PATH>/
└── categories/
    ├── 01-core-development/
    │   ├── backend-developer.md
    │   └── frontend-developer.md
    ├── 02-language-specialists/
    │   └── python-expert.md
    └── <any-category-folder>/
        └── <any-agent>.md
```

Each agent file needs YAML frontmatter with `name` and `description`.

Set `AGENTS_LIBRARY_PATH` in a `.env` file at the project root. See `.env.example`.

If you don't have a local library, the skill can auto-download from [VoltAgent/awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents).

---

## Docs

- `docs/superpowers/specs/` — design decisions and feature specs
- `docs/superpowers/plans/` — step-by-step implementation plans
