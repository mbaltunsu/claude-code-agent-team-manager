---
name: add-agent
description: "Add a single agent to the project team by filename or by describing a capability. Updates .claude/agents/, TEAM.md, and the Agents and Rules section in CLAUDE.md."
---

# Add-Agent Skill

Add a single agent to this project's team.

---

## Step 1: Detect Python

Run:
```bash
py --version
```

If that fails, try `python --version`, then `python3 --version`.

If none work, stop and tell the user:
> "Python not found. Install from https://www.python.org before running this skill."

Use whichever command worked for all subsequent steps.

---

## Step 2: Resolve Library Path

Check whether the central agents directory already has content:

```bash
py "${CLAUDE_PLUGIN_ROOT}/skills/init-team/scripts/init_team.py" list \
  --dest ~/.claude/team-management/agents
```

- **If agents are found** → set `LIBRARY_PATH` to `~/.claude/team-management/agents` and continue to Step 3.

- **If empty or missing** → ask the user:
  > "No agents in central store. Choose:
  > 1. Download from official source (VoltAgent/awesome-claude-code-subagents)
  > 2. Import from a local library path"

  **Option 1:**
  ```bash
  py "${CLAUDE_PLUGIN_ROOT}/skills/init-team/scripts/init_team.py" download --source voltagent
  ```

  **Option 2:**
  ```bash
  py "${CLAUDE_PLUGIN_ROOT}/skills/init-team/scripts/init_team.py" import --path "<USER_PATH>"
  ```

  On success, set `LIBRARY_PATH` to `~/.claude/team-management/agents`. On error, report and stop.

---

## Step 3: Verify Script Exists

Use the Glob tool with pattern `${CLAUDE_PLUGIN_ROOT}/skills/init-team/scripts/init_team.py` to confirm the script is installed.

If not found, stop and tell the user:
> "Script not found. Is the team plugin installed?"

---

## Step 4: Determine Agent Filename

**If the user provided a filename** (e.g., `/team:add-agent python-pro.md`) → use it directly, skip to Step 5.

**If the user described a capability** (e.g., `/team:add-agent an agent for testing`) → run scan:

```bash
py "${CLAUDE_PLUGIN_ROOT}/skills/init-team/scripts/init_team.py" scan --path "<LIBRARY_PATH>"
```

Parse the JSON output. Use AI reasoning to match the user's description against the `name` and `description` fields of all agents. Present the top 1–3 matches:

| Agent | Category | Why this matches |
|---|---|---|
| test-automator.md | 04-quality-security | Builds test frameworks and CI/CD integration |

Ask the user to confirm which agent to add. If none match well, tell the user and stop.

---

## Step 5: Add the Agent

```bash
py "${CLAUDE_PLUGIN_ROOT}/skills/init-team/scripts/init_team.py" add \
  --agent "<filename>" \
  --path "<LIBRARY_PATH>" \
  --dest .claude/agents \
  --claude-md CLAUDE.md \
  --team-md TEAM.md
```

Report the output. If the script exits with an error, report it verbatim and stop.

---

## Step 6: Refresh `## Agents and Rules` Section

```bash
py "${CLAUDE_PLUGIN_ROOT}/skills/init-team/scripts/init_team.py" update-docs \
  --claude-md CLAUDE.md \
  --team-md TEAM.md \
  --agents-dest .claude/agents \
  --rules-dest .claude/rules
```

Report the output. The `## Agents and Rules` section in CLAUDE.md now reflects the updated agent roster.
