---
name: join-project
description: "Onboard to an existing project. Analyzes CLAUDE.md, rules, agents, codebase, and docs to give you a full project briefing. Helps you understand workflows, update stale config, and add missing agents. Run when joining a project someone else set up."
---

# Join-Project Skill

Onboard a developer to an existing project that already has Claude Code configuration.

Unlike `init-project` (which creates from scratch), this skill **reads** what exists, **explains** it, and **offers updates** where needed.

---

## Prerequisite Check

Before anything else, verify the project has been set up:

- Check if `CLAUDE.md` exists
- Check if `.claude/rules/` directory exists

If **neither** exists, stop and tell the user:
> "This project hasn't been set up with Claude Code yet. Run `/team:init-project` first to bootstrap the configuration."

If only one exists, note it and continue — the project may be partially set up.

---

## Step 1: Detect Python

Try each of the following in order until one succeeds:
```bash
py --version
```
```bash
python --version
```
```bash
python3 --version
```
```bash
py3 --version
```

If none work, stop and tell the user:
> "Python not found. Install from https://www.python.org before running this skill."

Use whichever command worked for all subsequent steps.

---

## Step 2: Deep Project Analysis

Read and analyze **all** of the following sources. Do not skip any that exist.

### 2a. Rule Files

Read every `.md` file in `.claude/rules/`. For each file, extract the key points. Common files:

- `project-context.md` — purpose, audience, current state, goals, constraints
- `architecture.md` — architectural style, key components, patterns, constraints
- `tech-stack.md` — language, frameworks, dependencies, conventions
- `git-rules.md` — branching strategy, commit discipline, parallel workflows
- `frontend-rules.md` — UI/UX rules (if present)
- Any other custom rule files

### 2b. CLAUDE.md

Read `CLAUDE.md`. Note:
- Project description (if at the top)
- `## Agents and Rules` section — what agents and rules are listed
- Any project-specific workflow rules or conventions
- Any `## Do Not` or constraint sections

### 2c. Installed Agents

Run:
```bash
<PYTHON> "${CLAUDE_PLUGIN_ROOT}/skills/init-team/scripts/init_team.py" list --dest .claude/agents
```

Parse the JSON output to get the list of installed agents with their descriptions.

### 2d. TEAM.md

Read `TEAM.md` if it exists — it has the full agent roster with descriptions.

### 2e. Codebase Structure

- List files in the project root to understand the project layout
- Read `README.md` if present
- Check for dependency files: `package.json`, `requirements.txt`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `Gemfile`
- Check for plan/spec docs: glob `docs/superpowers/plans/*.md` and `docs/superpowers/specs/*.md`

### 2f. Git State

- Run `git log --oneline -10` to see recent activity
- Run `git branch -a` to see active branches

---

## Step 3: Present Project Briefing

Display a structured onboarding summary using everything gathered in Step 2. Use only facts found in the files — do not infer or guess.

```
PROJECT BRIEFING
================

## What This Project Does
[From project-context.md: Purpose — 2-3 sentences max]

## Who It's For
[From project-context.md: Users/Audience]

## Current State
[From project-context.md: State + Key Goals]

## Tech Stack
[From tech-stack.md: Language, Frameworks, Key Dependencies]

## Architecture
[From architecture.md: Style, Key Components — brief]

## Git Workflow
[From git-rules.md: Branch naming, commit style, merge rules — brief]

## Your Agent Team
[Table from installed agents list]
| Agent | Description |
|-------|-------------|
| ...   | ...         |

## Active Rules
[List of rule files found in .claude/rules/ with one-line description each]

## Things to Avoid
[From project-context.md "Do Not" section + any constraints from architecture.md]

## Recent Activity
[Last 5 commits from git log — one line each]
```

If any section has no data (e.g., no project-context.md), write: `Not configured — consider updating.`

---

## Step 4: Ask Clarifying Questions

After presenting the briefing, ask the user:

> "Now that you've seen the project setup, I have a few questions:
>
> 1. **Is the project description accurate and up to date?** (purpose, audience, state)
> 2. **Is the tech stack still current?** (any new frameworks, dependencies, or migrations?)
> 3. **Are there any new rules or constraints** that should be added to `.claude/rules/`?
> 4. **What are you working on?** (your current task or area of focus)"

Wait for the user's response.

---

## Step 5: Update Rules (if needed)

Based on the user's answers from Step 4:

- **If the user reported outdated info** in any rule file → open that file, show current content, ask what to change, then edit the file with the corrected content.

- **If the user wants to add a new rule** → create a new `.md` file in `.claude/rules/` with the content they describe. Use the same format as existing rule files (heading + sections).

- **If everything is up to date** → skip this step.

After any rule changes, run:
```bash
<PYTHON> "${CLAUDE_PLUGIN_ROOT}/skills/init-team/scripts/init_team.py" update-docs \
  --claude-md CLAUDE.md \
  --team-md TEAM.md \
  --agents-dest .claude/agents \
  --rules-dest .claude/rules
```

This refreshes the `## Agents and Rules` section in CLAUDE.md to reflect the current state.

---

## Step 6: Review Agents

Based on the user's task/focus area from Step 4 question 4:

Check if the current agent team covers the user's needs. Consider:
- Does the task need a specialist agent that isn't installed?
- Are there installed agents that are no longer relevant?

If agents should be added, tell the user:
> "Based on your focus on [task], you might benefit from adding: [agent suggestion]. Run `/team:add-agent [name]` to add it, or `/team:init-team` to review the full roster."

If agents should be removed:
> "The agent [name] doesn't seem relevant to the current project state. Run `/team:init-team remove [name]` to clean up."

If the team looks good:
> "Your current agent team covers your needs well."

---

## Step 7: Ready to Work

Summarize what was done:
- Briefing presented
- Rules updated (if any)
- Agent recommendations (if any)

Then print:

> "You're onboarded. Here's your quick reference:
>
> - **Start work:** create a branch (`feature/your-task` or `fix/your-task`)
> - **Need an agent:** `/team:add-agent <name or capability>`
> - **Check stats:** `/team:stats`
> - **Update rules:** edit files in `.claude/rules/` then run `/team:init-team update-docs`
> - **Full team review:** `/team:init-team`"
