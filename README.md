# init-agents

A Claude Code skill that bootstraps the right agent files into your project from a central agent library.

## What it does

1. Scans your agent library for all available agents
2. Reads your project brief (`CLAUDE.md` or `docs/superpowers/specs/*.md`)
3. Recommends agents that fit your project
4. Copies approved agents into `.claude/agents/` (never overwrites existing ones)
5. Updates `CLAUDE.md` with a `## Project Team` section listing every agent added

## Installation

Copy the `skills/init-agents/` folder into your project:

```bash
# Per-project
cp -r skills/init-agents/ /your/project/.claude/skills/

# Global (all projects)
cp -r skills/init-agents/ ~/.claude/skills/
```

## Setup

Create a `.env` file in your project root:

```
AGENTS_LIBRARY_PATH=/path/to/your/agent/library
```

See `.env.example` for reference. The path must point to the root of your agent library — the folder that contains a `categories/` subdirectory.

## Usage

In Claude Code, run:

```
/init-agents
```

## Requirements

- Python 3.8+
- A local agent library with a `categories/` folder structure
  (e.g. [awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents))

## Running tests

```bash
cd skills/init-agents/scripts
pytest tests/ -v
```
