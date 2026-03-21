---
name: init-agents
description: Bootstrap agents into this project from a central agent library. Recommends and copies the right agents based on project context (CLAUDE.md or spec docs). Run at project start or any time during development.
---

# Init-Agents Skill

You are setting up project-specific agents. Follow these steps exactly in order.

## Step 1: Detect Python

Run:
```bash
python --version
```
If that fails, run `python3 --version`.

If neither works, stop and tell the user:
> "Python not found. Install from https://www.python.org before running this skill."

Use whichever command worked (`python` or `python3`) for all subsequent steps.

## Step 2: Resolve Library Path

Use the Grep tool to search for `^AGENTS_LIBRARY_PATH=` in `.env` in the project root.

If a match is found, extract the value after `=` and store it as `LIBRARY_PATH`.

If no match is found (or `.env` does not exist), ask the user:
> "Enter the path to your agent library:"

Store their answer as `LIBRARY_PATH`. Do not write it to any file. Path validation happens in Step 4 when the script runs.

## Step 3: Verify Script Exists

Use the Glob tool with pattern `skills/init-agents/scripts/init_agents.py` from the project root to check the script is installed.

If not found, stop and tell the user:
> "Script not found at skills/init-agents/scripts/init_agents.py. Is init-agents installed in this project?"

## Step 4: Scan Agent Library

Run:
```bash
python skills/init-agents/scripts/init_agents.py scan --path "<LIBRARY_PATH>"
```

Parse the JSON output. Each entry contains: `category`, `name`, `file`, `path`, `description`.
The `path` field (e.g. `01-core-development/backend-developer.md`) is used in the copy step.

## Step 5: Read Project Context

Look for `CLAUDE.md` in the current project root. Read it if present.

If `CLAUDE.md` is absent, look for files in `docs/superpowers/specs/`:
- Files with a `YYYY-MM-DD` prefix: sort by that date, descending.
- Files without a date prefix: sort by filesystem modification time, descending.
- Dated files take priority over undated files regardless of mtime.
- If multiple files share the same date, use filesystem mtime to break the tie.
- Read the single most recent file found by this ordering.

If neither `CLAUDE.md` nor any spec file exists, tell the user:
> "No project brief found. Recommendations may be generic. Consider creating a CLAUDE.md before running this skill."

Continue regardless — do not stop.

## Step 6: Recommend Agents

Using the project context and the full list of agents from the scan, recommend the most relevant agents.

Output a Markdown table:

| Agent | Category | Reason |
|---|---|---|
| backend-developer.md | 01-core-development | Project uses Node.js API |

Include only agents that clearly fit the project. 5–10 agents is typical; fewer is fine for narrow projects. Do not recommend agents speculatively.

If the scan returned 0 agents, or if no agents clearly fit the project, stop and tell the user:
> "No suitable agents found in the library for this project. Check your library path and try again."

## Step 7: Wait for Approval

Display the recommendation table, then prompt the user:

> "Type YES to copy all recommended agents, enter comma-separated agent names to select a subset (e.g. backend-developer.md, api-designer.md), or NO to cancel:"

Handle the response:

- `YES` (case-insensitive) → use the full recommended list
- Comma-separated filenames → validate each against scan results (match on the `file` field).
  - Unknown names: print `"Unknown agent: <name> — skipped."` and skip them.
  - If all names are unknown: print `"No valid agents. Exiting."` and stop.
- `NO` or empty input → print `"Cancelled. No files copied."` and stop.
- Any other input → print `"Unrecognized input. Please try again:"` and re-prompt **once** using the same rules:
  1. `YES` → proceed with full list
  2. Comma-separated filenames → validate and proceed
  3. Empty input → `"Cancelled. No files copied."` and stop
  4. Any other input → `"Unrecognized input. Exiting."` and stop

## Step 8: Copy Agents and Update CLAUDE.md

Build a comma-separated list of `path` values for the approved agents
(e.g. `01-core-development/backend-developer.md,02-language-specialists/python-expert.md`).

Run:
```bash
python skills/init-agents/scripts/init_agents.py copy \
  --agents "<comma-separated paths>" \
  --path "<LIBRARY_PATH>" \
  --dest .claude/agents \
  --claude-md CLAUDE.md
```

The script will:
1. Copy newly approved agents into `.claude/agents/` (skipping existing ones)
2. Automatically update `CLAUDE.md` with a `## Project Team` section listing every copied agent (name, filename, description)
3. Add a note in that section reminding the team to manually update it if agents are added outside this skill

Report the script output to the user exactly as printed.

If the script exits with an error (non-zero exit code), report the error output verbatim and stop. Do not declare success.
