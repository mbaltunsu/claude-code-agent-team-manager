# Init-Agents Skill

A Claude Code skill that bootstraps agent files into projects from a central agent library.

## Structure

- `skills/init-agents/init-agents.md` — Claude Code skill file
- `skills/init-agents/scripts/init_agents.py` — Python CLI script (stdlib only)
- `skills/init-agents/scripts/tests/` — pytest tests (one file per concern)

## Running Tests

```bash
cd skills/init-agents/scripts
pytest tests/ -v
```

## Installation

Copy `skills/init-agents/` into `.claude/skills/` of any project, or `~/.claude/skills/` for global use.
