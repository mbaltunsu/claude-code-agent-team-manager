---
name: init-team
description: "Manage project agent teams: bootstrap, add, remove, list, and update agents from a central library. Recommends agents based on project context. Supports capability-based matching (\"I need an agent for testing\"). Run at project start or any time during development."
---

# Init-Team Skill

You manage project-specific agents. Detect the user's intent and route to the correct flow:

- **Full setup** (no arguments, first run) → Steps 1–8
- **"add <name>"** or **"I need an agent that can do X"** → Tell the user: "Use `/team:add-agent` to add a single agent by name or capability." Then stop.
- **"remove <name>"** → Quick Action: Remove
- **"list"** → Quick Action: List
- **"update"** → Quick Action: Update

---

## Full Setup Flow (Steps 1–8)

### Step 1: Detect Python

Run:
```bash
python --version
```
If that fails, run `python3 --version`.

If neither works, stop and tell the user:
> "Python not found. Install from https://www.python.org before running this skill."

Use whichever command worked (`python` or `python3`) for all subsequent steps.

### Step 2: Resolve Library Path

Check whether the central agents directory already has content:

```bash
python skills/init-team/scripts/init_team.py list --dest ~/.claude/team-management/agents
```

- **If agents are found** → set `LIBRARY_PATH` to `~/.claude/team-management/agents` and continue to Step 3.

- **If empty or missing** → ask the user:
  > "No agents found in the central store (`~/.claude/team-management/agents`). Choose:
  >
  > 1. Download from official source (VoltAgent/awesome-claude-code-subagents)
  > 2. Import from a local library path
  > 3. Add a custom source (git repo URL)"

  Handle each option:

  **Option 1 — Download from official source:**
  ```bash
  python skills/init-team/scripts/init_team.py download --source voltagent
  ```
  Parse JSON output. On success set `LIBRARY_PATH` to the `dest` value.

  **Option 2 — Import from local path:**
  ```bash
  python skills/init-team/scripts/init_team.py import --path "<USER_PATH>"
  ```
  Parse JSON output. On success set `LIBRARY_PATH` to `~/.claude/team-management/agents`.

  **Option 3 — Add custom source then download:**
  ```bash
  python skills/init-team/scripts/init_team.py source-add --repo "<URL>" --name "<name>"
  python skills/init-team/scripts/init_team.py download --source "<generated-id>"
  ```

  If any command fails (JSON `error` key), report the error and stop.

### Step 3: Verify Script Exists

Use the Glob tool with pattern `skills/init-team/scripts/init_team.py` from the project root to check the script is installed.

If not found, stop and tell the user:
> "Script not found at skills/init-team/scripts/init_team.py. Is init-team installed in this project?"

### Step 4: Scan Agent Library

Run:
```bash
python skills/init-team/scripts/init_team.py scan --path "<LIBRARY_PATH>"
```

Parse the JSON output. Each entry contains: `category`, `name`, `file`, `path`, `description`.
The `path` field (e.g. `01-core-development/backend-developer.md`) is used in the copy step.

### Step 5: Gather Project Context

Collect context from **all available sources** to inform agent recommendations. Read each source that exists:

1. **CLAUDE.md** — read if present in project root
2. **Plan docs** — use Glob for `docs/superpowers/plans/*.md`. Sort by `YYYY-MM-DD` prefix descending (dated files first, then undated by mtime). Read the 2 most recent.
3. **Spec docs** — use Glob for `docs/superpowers/specs/*.md`. Same sorting. Read the 2 most recent.
4. **Architecture docs** — check for and read any of: `ARCHITECTURE.md`, files matching `docs/architecture*`, files in `docs/adr/`
5. **Tech stack detection** — check for these files and read their dependency sections:
   - `package.json` → Node.js (read `dependencies` and `devDependencies`)
   - `requirements.txt` or `pyproject.toml` → Python
   - `Cargo.toml` → Rust
   - `go.mod` → Go
   - `pom.xml` or `build.gradle` → Java/Kotlin
   - `Gemfile` → Ruby
6. **Already installed agents** — run:
   ```bash
   python skills/init-team/scripts/init_team.py list --dest .claude/agents
   ```
   Parse JSON output. Do not recommend agents that are already installed.
7. **User's prompt/request** — use whatever the user said when invoking the skill as primary context for recommendations.

If no context sources exist at all, tell the user:
> "No project brief found. Recommendations may be generic. Consider creating a CLAUDE.md before running this skill."

Continue regardless — do not stop.

### Step 6: Recommend Agents

Using **all gathered context** and the full list of agents from the scan, recommend the most relevant agents.

Output a Markdown table:

| Agent | Category | Reason |
|---|---|---|
| backend-developer.md | 01-core-development | Project uses Node.js API |

Include only agents that clearly fit the project. 5–10 agents is typical; fewer is fine for narrow projects. Do not recommend agents speculatively. Exclude any agents already installed (from Step 5.6).

If the scan returned 0 agents, or if no agents clearly fit the project, stop and tell the user:
> "No suitable agents found in the library for this project. Check your library path and try again."

### Step 7: Wait for Approval

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

### Step 8: Copy Agents and Update CLAUDE.md

Build a comma-separated list of `path` values for the approved agents
(e.g. `01-core-development/backend-developer.md,02-language-specialists/python-expert.md`).

Run:
```bash
python skills/init-team/scripts/init_team.py copy \
  --agents "<comma-separated paths>" \
  --path "<LIBRARY_PATH>" \
  --dest .claude/agents \
  --claude-md CLAUDE.md \
  --team-md TEAM.md
```

The script will:
1. Copy newly approved agents into `.claude/agents/` (skipping existing ones)
2. Create/update `TEAM.md` listing every copied agent (name and description)
3. Add/update the `## Agents and Rules` section in `CLAUDE.md` with team collaboration guidelines and a pointer to `TEAM.md`

Report the script output to the user exactly as printed.

If the script exits with an error (non-zero exit code), report the error output verbatim and stop. Do not declare success.

After the copy succeeds, run:
```bash
python skills/init-team/scripts/init_team.py update-docs \
  --claude-md CLAUDE.md \
  --team-md TEAM.md \
  --agents-dest .claude/agents \
  --rules-dest .claude/rules
```

This refreshes the `## Agents and Rules` section to list all installed agents and rules.

---

## Quick Actions

These alternative flows handle single-agent operations. They still require Steps 1–3 (detect Python, resolve library path, verify script) before running.

### Quick Action: Remove

Triggered when the user says "remove <agent-name>".

Run Step 1 (detect Python), then:
```bash
python skills/init-team/scripts/init_team.py remove \
  --agent "<filename>" \
  --dest .claude/agents \
  --team-md TEAM.md \
  --claude-md CLAUDE.md
```

Report the output to the user. The script removes the agent file and updates TEAM.md and CLAUDE.md.

### Quick Action: List

Triggered when the user says "list" or "show agents".

Run Step 1 (detect Python), then:
```bash
python skills/init-team/scripts/init_team.py list --dest .claude/agents
```

Parse the JSON output and display a formatted table:

| Agent | Description |
|---|---|
| python-pro.md | Python expert |

### Quick Action: Update

Triggered when the user says "update" or "check for updates".

Run Step 1 (detect Python), then:
```bash
python skills/init-team/scripts/init_team.py update
```

Parse the JSON output:
- If `"updated": true` → report the old and new versions and list of updated files
- If `"updated": false` → tell the user they are on the latest version
- If `"error"` key present → report the error

### Quick Action: Source List

Triggered when the user says "source list" or "show sources".

Run Step 1 (detect Python), then:
```bash
python skills/init-team/scripts/init_team.py source-list
```

Parse the JSON output and display a formatted table:

| ID | Name | Author | Repo |
|---|---|---|---|
| voltagent | awesome-claude-code-subagents | VoltAgent | https://github.com/VoltAgent/... |

### Quick Action: Source Add

Triggered when the user says "source add <url>" or "add source".

Run Step 1 (detect Python), then:
```bash
python skills/init-team/scripts/init_team.py source-add \
  --repo "<URL>" \
  --name "<name>" \
  [--author "<author>"] \
  [--homepage "<url>"]
```

Report the output.

### Quick Action: Import

Triggered when the user says "import <path>" or "import local library".

Run Step 1 (detect Python), then:
```bash
python skills/init-team/scripts/init_team.py import --path "<PATH>"
```

Parse the JSON output and report how many agents were imported vs skipped.
