# init-team

A Claude Code skill that bootstraps the right agent files into your project from a central agent library.

## What it does

1. Scans your agent library for all available agents
2. Reads your project brief (`CLAUDE.md` or `docs/superpowers/specs/*.md`)
3. Recommends agents that fit your project
4. Copies approved agents into `.claude/agents/` (never overwrites existing ones)
5. Creates/updates `TEAM.md` with the full agent roster; adds a pointer in `CLAUDE.md`

**No agent library?** The skill can auto-download agents from [awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents) into `~/.claude/agent-library/` — just say "No" when asked if you have a local library.

## Plugin installation (recommended)

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

Restart Claude Code. `/init-team` is now available in every project — no per-project setup needed.

> **Note:** `agent-team-manager` is a local alias you choose. It must match exactly what appears after `@` in `enabledPlugins`. Avoid names that conflict with existing marketplace keys in your settings (e.g. `claude-plugins-official`, `superpowers-marketplace`).

## Manual installation (alternative)

Copy the `skills/init-team/` folder into your project:

```bash
# Per-project
cp -r skills/init-team/ /your/project/.claude/skills/

# Global (all projects)
cp -r skills/init-team/ ~/.claude/skills/
```

## Setup

Create a `.env` file in your project root:

```
AGENTS_LIBRARY_PATH=/path/to/your/agent/library
```

See `.env.example` for reference. The path must point to the root of your agent library — the folder that contains a `categories/` subdirectory.

If you don't have a local library, skip this step — the skill will offer to download one for you.

## Agent library format

The skill expects an agent library with this folder structure:

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

Each `.md` agent file must have YAML frontmatter with `name` and `description`:

```yaml
---
name: Backend Developer
description: Specializes in server-side architecture, APIs, and database design
---

(agent instructions below)
```

Category folders can use any naming convention (numbered prefixes like `01-`, `02-` are common but not required). Every `.md` file inside a category folder (except `README.md`) is treated as an agent.

## Usage

In Claude Code, run:

```
/init-team
```

The skill will guide you through scanning, recommending, and copying agents.

## Auto-download mode

If you don't have a local agent library, the skill will offer to download agents from [VoltAgent/awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents):

- **Default destination:** `~/.claude/agent-library/`
- **Merge-safe:** never overwrites existing agents — only downloads new ones
- **Requires:** `git` on your PATH

You can also run the download manually:

```bash
python skills/init-team/scripts/init_team.py download
python skills/init-team/scripts/init_team.py download --dest /custom/path
python skills/init-team/scripts/init_team.py download --repo https://github.com/user/repo.git
```

## Requirements

- Python 3.8+
- `git` (for auto-download mode only)

## Running tests

```bash
cd skills/init-team/scripts
pytest tests/ -v
```
