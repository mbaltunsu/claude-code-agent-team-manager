---
name: init-project
description: "Bootstrap Claude Code project configuration from scratch. Creates .claude/rules/ and .claude/agents/, copies CLAUDE_STARTER.md to CLAUDE.md (with explicit permission), and generates rule files from project context. Run once per new project."
---

# Init-Project Skill

Bootstrap a new project's Claude Code configuration from scratch.

---

## Step 0: Gather Project Context via Q&A

Before making any changes, ask the user the following questions in a single message. Do **not** infer or guess from files, folder names, or project structure — use only what the user tells you.

> 1. **What does this project do?** (purpose and goal — one or two sentences)
> 2. **Who uses it?** (audience: internal tool, external users, library consumers, CLI users, etc.)
> 3. **What tech stack?** (language, runtime, frameworks, key libraries)
> 4. **What is the current state?** (greenfield, MVP, active development, production, being refactored, etc.)
> 5. **Any hard rules or constraints?** (things Claude should never do, dependencies to avoid, architectural limits)

Wait for the user's response. Use their answers verbatim to fill in the rule files in Steps 3–5.

If the user skips a question or says "skip" / "I don't know", mark that section with `TODO: fill in` in the generated file.

---

## Step 1: Create Base Directories

Run:
```bash
py "${CLAUDE_PLUGIN_ROOT}/skills/init-team/scripts/init_team.py" init-project \
  --rules-dest .claude/rules \
  --agents-dest .claude/agents \
  --git-rules-src "${CLAUDE_PLUGIN_ROOT}/starter_template/GIT_RULES.md"
```

Parse the JSON output and report the result to the user:
- For each entry in `dirs_created`: `[OK] <dir> created`
- For each entry in `files_copied`: `[OK] <file> created`
- For each entry in `files_skipped`: `[SKIP] <file> already exists`

If the script exits with a non-zero code, report the error and stop.

---

## Step 2: Permission for CLAUDE.md

⚠️ Ask the user BEFORE touching CLAUDE.md.

Check if `CLAUDE.md` exists:

- **If it exists:** Display the first 15 lines, then ask:
  > "⚠️ **CLAUDE.md already exists and will be COMPLETELY OVERWRITTEN.** Your current content will be lost permanently.
  >
  > [show first 15 lines of current CLAUDE.md]
  >
  > Type **YES** to overwrite with the starter template, or **NO** to skip:"

- **If it does not exist:** Ask:
  > "CLAUDE.md does not exist. Type **YES** to create it from the starter template, or **NO** to skip:"

Handle response:
- `YES` (case-insensitive) → read `${CLAUDE_PLUGIN_ROOT}/starter_template/CLAUDE_STARTER.md`, write its content to `CLAUDE.md`; print `[OK] CLAUDE.md written`
- `NO` → print `[SKIP] CLAUDE.md not modified.` — **do NOT stop**, continue to Step 3

---

## Step 3: Create `.claude/rules/architecture.md`

Check if `.claude/rules/architecture.md` already exists. If it does, ask:
> "`.claude/rules/architecture.md` already exists. Overwrite? (YES/NO):"

If `NO`, skip this file and continue to Step 4.

Write `.claude/rules/architecture.md` using only the user's answers from Step 0. Do not infer or add anything the user did not say. For any skipped section, write `TODO: fill in`:

```markdown
# Architecture

## Overview
[1-3 sentences on architectural style: monolith, microservices, serverless, CLI tool, library, etc.]

## Key Components
[Main modules/services/layers identified from project exploration]

## Patterns
[Key design patterns: MVC, repository pattern, event-driven, etc.]

## Constraints
[Architectural rules to follow: e.g., "No direct DB calls from UI layer"]
```

---

## Step 4: Create `.claude/rules/tech-stack.md`

Same overwrite permission flow as Step 3. Write using only the tech stack the user described in Step 0. Do not detect or infer from project files:

```markdown
# Tech Stack

## Runtime / Language
[e.g., Python 3.12, Node.js 20, Go 1.22, TypeScript 5]

## Frameworks
[e.g., FastAPI, React 18, Express, Next.js]

## Key Dependencies
[Top 5-10 from package.json / requirements.txt]

## Dev Tools
[e.g., pytest, vitest, eslint, docker, make]

## Conventions
[Project-specific coding conventions: e.g., "All models use Pydantic", "camelCase in API responses"]
```

---

## Step 5: Create `.claude/rules/project-context.md`

Same overwrite permission flow. Write using only what the user told you in Step 0. Do not infer or add anything not explicitly stated. For any skipped question, write `TODO: fill in`:

```markdown
# Project Context

## Purpose
[What this project does and why it exists]

## Users / Audience
[Who uses this: internal tool, B2C, library, CLI, API, etc.]

## Current State
[Greenfield, mature, in active development, being refactored, etc.]

## Key Goals
[Top 3 current priorities]

## Do Not
[Things to avoid: e.g., "Do not add analytics without approval", "No jQuery"]
```

---

## Step 6: Update `## Agents and Rules` Section in CLAUDE.md

Run:
```bash
py "${CLAUDE_PLUGIN_ROOT}/skills/init-team/scripts/init_team.py" update-docs \
  --claude-md CLAUDE.md \
  --team-md TEAM.md \
  --agents-dest .claude/agents \
  --rules-dest .claude/rules
```

Report the output. The `## Agents and Rules` section in CLAUDE.md now lists all agents and rules.

---

## Completion

Summarize what was created:
- Directories created/skipped
- CLAUDE.md status (written / skipped)
- Rule files created/skipped: `git-rules.md`, `architecture.md`, `tech-stack.md`, `project-context.md`
- Whether the `## Agents and Rules` section was updated

Tell the user:
> "Project bootstrapped. Run `/team:add-agent` to add agents, or `/team:init-team` for a full agent roster."
