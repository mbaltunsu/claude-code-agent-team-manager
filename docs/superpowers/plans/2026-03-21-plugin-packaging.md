# Plugin Packaging Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `.claude-plugin/marketplace.json` and `.claude-plugin/plugin.json` to make the init-agents skill installable as a Claude Code plugin from `mbaltunsu/claude-code-agent-team-manager`, and update the README with plugin install instructions.

**Architecture:** Two static JSON files in a new `.claude-plugin/` directory at the repo root tell Claude Code what this repo publishes and where to find the plugin content. The existing `skills/init-agents/` directory is already structured correctly — no code changes needed. The README gets a new section above the current Installation section with a ready-to-paste settings snippet.

**Tech Stack:** JSON, Markdown

**Out of scope:** MCP server registration, `autoUpdate` configuration, publishing to the official Claude Code marketplace, multiple plugins in one marketplace, CI/CD for version bumping.

---

## File Map

| File | Action | Role |
|---|---|---|
| `.claude-plugin/marketplace.json` | Create | Marketplace manifest — declares the `init-agents` plugin |
| `.claude-plugin/plugin.json` | Create | Plugin metadata — name, version, author, links |
| `README.md` | Modify | Add Plugin installation section above existing Installation |

---

### Task 1: Plugin Manifest Files

**Files:**
- Create: `.claude-plugin/marketplace.json`
- Create: `.claude-plugin/plugin.json`

- [ ] **Step 1: Create the `.claude-plugin/` directory**

```bash
mkdir .claude-plugin
```

- [ ] **Step 2: Create `.claude-plugin/marketplace.json`**

Write this exact content:

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

- [ ] **Step 3: Validate `marketplace.json` syntax**

Run from project root:

```bash
python -c "import json; json.load(open('.claude-plugin/marketplace.json'))" && echo "OK"
```

Expected output: `OK`

- [ ] **Step 4: Create `.claude-plugin/plugin.json`**

Write this exact content:

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

- [ ] **Step 5: Validate `plugin.json` syntax**

```bash
python -c "import json; json.load(open('.claude-plugin/plugin.json'))" && echo "OK"
```

Expected output: `OK`

- [ ] **Step 6: Verify `name` and `version` are consistent**

Confirm manually:
- `marketplace.json` → `plugins[0].name` = `"init-agents"`, `plugins[0].version` = `"1.0.0"`
- `plugin.json` → `name` = `"init-agents"`, `version` = `"1.0.0"`

- [ ] **Step 7: Commit**

```bash
git add .claude-plugin/marketplace.json .claude-plugin/plugin.json
git commit -m "feat: add .claude-plugin manifests for plugin distribution"
```

- [ ] **Step 8: Create release tag**

```bash
git tag v1.0.0
```

> Note: Push the tag alongside the branch when publishing to GitHub: `git push origin main --tags`

---

### Task 2: README — Plugin Installation Section

**Files:**
- Modify: `README.md`

The current README structure is:

```
# init-agents
## What it does
## Installation
## Setup
## Usage
## Requirements
## Running tests
```

After this task it must be:

```
# init-agents
## What it does
## Plugin installation (recommended)
## Installation (manual alternative)
## Setup
## Usage
## Requirements
## Running tests
```

- [ ] **Step 1: Rename the existing `## Installation` heading**

In `README.md`, change line 13 from:

```
## Installation
```

to:

```
## Installation (manual alternative)
```

- [ ] **Step 2: Insert `## Plugin installation (recommended)` section**

Insert the following block immediately after the `## What it does` section (after line 11, before the now-renamed `## Installation (manual alternative)` heading). The content to insert — write it exactly as shown below, with the JSON as an indented code block:

---

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
    "init-agents@agent-team-manager": true
  }
}
```

Restart Claude Code. `/init-agents` is now available in every project — no per-project setup needed.

> **Note:** `agent-team-manager` is a local alias you choose. It must match exactly what appears after `@` in `enabledPlugins`. Avoid names that conflict with existing marketplace keys in your settings (e.g. `claude-plugins-official`, `superpowers-marketplace`).

---

- [ ] **Step 3: Verify final README heading order**

Read `README.md` and confirm headings appear in this order:
1. `# init-agents`
2. `## What it does`
3. `## Plugin installation (recommended)`
4. `## Installation (manual alternative)`
5. `## Setup`
6. `## Usage`
7. `## Requirements`
8. `## Running tests`

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: add plugin installation section to README"
```
