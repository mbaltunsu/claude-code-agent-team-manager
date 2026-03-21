# Plugin Packaging — Design Spec
**Date:** 2026-03-21
**Status:** Approved

---

## Overview

Package the `init-agents` Claude Code skill as a distributable plugin so anyone can install it from the GitHub repository `mbaltunsu/claude-code-agent-team-manager` with a one-time settings entry, then use `/init-agents` as a skill in any project.

No changes to existing skill or script code. Two new JSON files are added to a `.claude-plugin/` directory at the repo root.

---

## How Claude Code Plugins Work

Claude Code's plugin system has two layers:

- **Marketplace** — a registry that lists available plugins. Defined by `marketplace.json` in `.claude-plugin/`. Users add a marketplace by pointing `extraKnownMarketplaces` in their `settings.json` at a GitHub repo.
- **Plugin** — a unit of installable content (skills, MCP servers, etc.). Defined by `plugin.json` in the plugin root. The marketplace's `source: "./"` means the plugin root is the repo root itself.

After a marketplace is registered and the plugin is enabled, Claude Code clones the repo into its local cache and exposes all skills under `skills/` to the user.

> **Key naming note:** The key used in `extraKnownMarketplaces` (e.g. `"agent-team-manager"`) is a local alias — it can be any string the user chooses. It must match exactly what appears after `@` in the `enabledPlugins` entry (e.g. `"init-agents@agent-team-manager"`). It does not need to match the `name` field inside `marketplace.json`. Avoid using keys that shadow existing marketplace names like `"claude-plugins-official"` or `"superpowers-marketplace"`.

---

## Repository Structure (after this change)

```
claude-code-agent-team-manager/
├── .claude-plugin/
│   ├── marketplace.json     ← marketplace manifest (lists plugins)
│   └── plugin.json          ← plugin identity and metadata
├── skills/
│   └── init-agents/
│       ├── init-agents.md   ← Claude Code skill file (unchanged)
│       └── scripts/
│           ├── init_agents.py
│           ├── conftest.py
│           └── tests/
├── docs/
├── CLAUDE.md
├── TEAM.md (generated per-project, not in this repo)
├── README.md
└── .env.example
```

The existing `skills/init-agents/` directory already satisfies the plugin spec. No restructuring needed.

---

## New Files

### `.claude-plugin/marketplace.json`

```json
{
  "name": "agent-team-manager",
  "description": "Marketplace for the Claude Code agent team manager plugin",
  "owner": {
    "name": "mbaltunsu"
  },
  "plugins": [
    {
      "name": "init-agents",
      "description": "Bootstrap agents into your project from a central agent library. Recommends and copies the right agents, tracks them in TEAM.md.",
      "version": "1.0.0",
      "source": "./",
      "author": {
        "name": "mbaltunsu"
      }
    }
  ]
}
```

### `.claude-plugin/plugin.json`

```json
{
  "name": "init-agents",
  "description": "Bootstrap agents into your project from a central agent library. Recommends and copies the right agents, tracks them in TEAM.md.",
  "version": "1.0.0",
  "author": {
    "name": "mbaltunsu"
  },
  "homepage": "https://github.com/mbaltunsu/claude-code-agent-team-manager",
  "repository": "https://github.com/mbaltunsu/claude-code-agent-team-manager",
  "license": "MIT",
  "keywords": ["agents", "init", "bootstrap", "claude-code", "team"]
}
```

---

## User Installation

### Step 1 — Register the marketplace (one-time)

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
    "init-agents@agent-team-manager": true
  }
}
```

### Step 2 — Use the skill

In any Claude Code project:

```
/init-agents
```

Restart Claude Code after editing `settings.json`. Claude Code clones the plugin on startup and serves the skill from its local cache. No per-project installation needed.

---

## Versioning

The `version` field in `marketplace.json` (inside the `plugins` array) is used by Claude Code for display and cache invalidation. The `version` field in `plugin.json` is optional but included for consistency. Keep them in sync — bump both when releasing a significant change, alongside a matching git tag (`v1.0.0`). If they diverge, `marketplace.json` is the authoritative version Claude Code uses when deciding whether to update the cached plugin.

---

## README Update

The README gets a new **Plugin installation** section placed above the existing manual installation section. It contains the ready-to-paste `settings.json` snippet from the User Installation section above, plus a note that `/init-agents` is available after restarting Claude Code.

The existing manual installation section (copying `skills/init-agents/` into `.claude/skills/`) is kept as the alternative for users who prefer not to use the plugin system or want a local-only copy.

---

## Out of Scope

- MCP server registration
- Plugin auto-update configuration (`autoUpdate` field)
- Publishing to any official Claude Code marketplace
- Multiple plugins in one marketplace
- CI/CD for version bumping or tagging
