# Init-Agents Skill — Design Spec
**Date:** 2026-03-21
**Status:** Approved

---

## Overview

A Claude Code skill that bootstraps the right agent files into a project from a central agent library. It reads the project brief, scans the available agents, uses AI to recommend the best fit, and copies approved agents into `.claude/agents/` — without overwriting already-customized agents.

Especially useful at project start and planning phase, but can be run at any point during development.

---

## Repository Structure

```
claude-code-project-and-team-setup/
├── skills/
│   └── init-agents/
│       ├── init-agents.md           ← Claude Code skill file
│       └── scripts/
│           └── init_agents.py       ← cross-platform Python script
├── .env.example                     ← documents AGENTS_LIBRARY_PATH
├── CLAUDE.md
└── README.md
```

The `init-agents/` folder is self-contained. To install: copy it into `.claude/skills/` of any project, or into `~/.claude/skills/` for global use.

---

## Agent Library Format

Expected structure of the central agent library:

```
<AGENTS_LIBRARY_PATH>/
├── categories/
│   ├── 01-core-development/
│   │   ├── backend-developer.md
│   │   ├── frontend-developer.md
│   │   └── ...
│   ├── 02-language-specialists/
│   └── ...
```

Each agent file is a Markdown file with YAML frontmatter containing at minimum `name` and `description`. The `categories/` subdirectory is required.

---

## Flow

```
User invokes /init-agents
        │
        ▼
1. DETECT PYTHON
   Run: python --version (or python3 --version)
   If neither found → print error + install hint (python.org), stop.
        │
        ▼
2. RESOLVE LIBRARY PATH
   Read AGENTS_LIBRARY_PATH from .env in current project root.
   If not found → prompt user: "Enter the path to your agent library:"
   Store as a Python variable for the duration of this run only.
   Do not write back to .env or any file.
        │
        ▼
3. SCAN
   Run: python <script_path> scan --path <library_path>
   Parse JSON output: array of { category, name, file, path }
   where path = "<category>/<file>" (relative to categories/)
        │
        ▼
4. READ PROJECT CONTEXT
   Try: CLAUDE.md in current project root (CWD).
   If absent → try: docs/superpowers/specs/*.md
     - Files matching YYYY-MM-DD prefix are sorted by that date (descending).
     - Files without a YYYY-MM-DD prefix are sorted by filesystem mtime (descending).
     - Dated files are preferred over undated files regardless of mtime.
     - If multiple files share the same date, sort by filesystem mtime (descending).
     - Use the single most recent file.
   If neither CLAUDE.md nor any spec file found → print warning:
     "No project brief found. Recommendations may be generic.
      Consider creating a CLAUDE.md before running this skill."
   Continue in all cases — do not stop.
        │
        ▼
5. RECOMMEND
   Claude reasons over available agents + project context.
   Output: Markdown table — Agent | Category | Reason
        │
        ▼
6. WAIT FOR APPROVAL
   Display recommendations and prompt:
     "Type YES to copy all recommended agents, enter comma-separated agent
      names to select a subset (e.g. backend-developer.md, api-designer.md),
      or NO to cancel:"

   Input handling (first prompt):
   - "YES" (case-insensitive) → copy all recommended agents
   - Comma-separated names → validate each name against scan results;
     unknown names print: "Unknown agent: <name> — skipped."
     Copy only valid names. If all names are unknown → "No valid agents. Exiting."
   - "NO" or empty input → print "Cancelled. No files copied." and stop.
   - Any other input → print "Unrecognized input. Please try again:" and re-prompt once.

   Input handling (re-prompt, second attempt only):
   - Same rules as first prompt.
   - Empty input on re-prompt → treated as NO → "Cancelled. No files copied." and stop.
   - Any other unrecognized input → "Unrecognized input. Exiting." and stop.
        │
        ▼
7. COPY
   Skill passes --path explicitly (the already-resolved library path from step 2).
   Run: python <script_path> copy \
        --agents "<category/file>,<category/file>" \
        --path <library_path> \
        --dest <dest_path>

   Per agent:
   - If not present at dest → copy, print: "✓ <file> copied"
   - If already present → skip, print: "⚠ <file> already exists — skipped"

   If zero valid agents remain → print "No agents to copy. Exiting." and stop.
   Print final summary: "X agent(s) copied, Y skipped."
   If Y > 0 → also print: "Skipped: <file1>, <file2>, ..."
```

---

## Python Script Interface

```bash
# Scan the agent library, print JSON to stdout
python skills/init-agents/scripts/init_agents.py scan --path PATH

# Copy approved agents into destination
python skills/init-agents/scripts/init_agents.py copy \
  --agents "01-core-development/backend-developer.md,02-language-specialists/python-expert.md" \
  --path PATH \
  --dest PATH
```

### Path resolution — applies identically to both `scan` and `copy` subcommands

Each subcommand resolves `--path` independently in this order:
1. `--path` CLI argument (highest priority)
2. `AGENTS_LIBRARY_PATH` from `.env` file in CWD
3. Error: "No library path provided. Set AGENTS_LIBRARY_PATH in .env or pass --path."

The skill always passes `--path` explicitly on both calls (reusing the value resolved in step 2), so the script's own `.env` fallback is a convenience for standalone script use only.

### Script path resolution

The skill instructs Claude to locate the script at:
```
skills/init-agents/scripts/init_agents.py
```
relative to CWD (the project root where the skill is invoked). If the file is not found:
> "Script not found at skills/init-agents/scripts/init_agents.py. Is init-agents installed in this project?"

### `--dest` default

Defaults to `.claude/agents` relative to CWD. Created automatically if it does not exist.

### Scan output format

```json
[
  {
    "category": "01-core-development",
    "name": "backend-developer",
    "file": "backend-developer.md",
    "path": "01-core-development/backend-developer.md",
    "description": "Specialist for server-side development..."
  }
]
```

- `file` — bare filename (e.g. `backend-developer.md`)
- `path` — relative path from `categories/` (e.g. `01-core-development/backend-developer.md`)
- Full source path = `<library_path>/categories/<path>`
- The `path` field is what gets passed to `--agents` in the copy command

### Malformed frontmatter during scan

If an agent file is missing `name` or `description`, has invalid YAML, or has no frontmatter block:
- Print to stderr: `"Warning: Skipping <file> — invalid or missing frontmatter"`
- Skip the file and continue scanning
- Do not stop the scan

### Copy behavior

- Creates `--dest` directory if it does not exist
- Skips agents that already exist at dest — prints warning per skipped file
- Never overwrites existing files
- If zero valid files to copy → print "No agents to copy. Exiting." and exit 0
- Per-file output: `✓ <file> copied` or `⚠ <file> already exists — skipped`
- Final summary: `X agent(s) copied, Y skipped.`
- If Y > 0: also print `Skipped: <file1>, <file2>, ...`

---

## Skill File Responsibilities (`init-agents.md`)

The skill instructs Claude to execute in order:

1. Check for `python` or `python3` — error + hint if missing, stop
2. Resolve library path from `.env` or prompt user; keep in variable for session
3. Run `scan --path <library_path>`, parse JSON output
4. Read `CLAUDE.md` → `docs/superpowers/specs/*.md` (date-sorted) → warn if neither, continue
5. Reason over agents + context, output recommendation table
6. Present recommendations, prompt for approval (YES / names / NO)
7. Validate subset names against scan results before invoking copy
8. Run `copy --path <library_path> --agents <category/file list>`, report per-file results and summary

---

## Environment Variables

| Variable | Description |
|---|---|
| `AGENTS_LIBRARY_PATH` | Absolute path to the root of the agent library |

Documented in `.env.example`:
```
AGENTS_LIBRARY_PATH=D:\CLAUDE_AGENTS\awesome-claude-code-subagents
```

---

## Edge Cases

| Scenario | Behavior |
|---|---|
| Python not found | Error: "Python not found. Install from python.org." Stop. |
| `.env` missing `AGENTS_LIBRARY_PATH` | Prompt user for path interactively |
| Library path does not exist | Error: "Path does not exist: `<path>`" Stop. |
| `categories/` subdirectory missing | Error: "Expected a 'categories/' subdirectory in `<path>`. Is this the correct library path?" Stop. |
| Agent file has missing/invalid frontmatter | Warn to stderr, skip file, continue scan |
| No `CLAUDE.md` or spec doc found | Warn user, continue with generic recommendations |
| User types NO or empty at approval | "Cancelled. No files copied." Stop gracefully. |
| User types unrecognized input | Re-prompt once with same prompt + warning. Empty on re-prompt = NO. Second unrecognized = "Unrecognized input. Exiting." Stop. |
| User enters unknown agent name in subset | Warn per name, skip unknown, copy valid. If all unknown → "No valid agents. Exiting." |
| Zero agents after approval/filtering | "No agents to copy. Exiting." Stop gracefully. |
| Agent already in `.claude/agents/` | Skip + warn per file, list in summary. Never overwrite. |
| `.claude/agents/` does not exist | Create automatically. |
| Script not found at expected path | Error with install hint. Stop. |
| Multiple spec files with same date | Sort by filesystem mtime descending, use most recent. |
| Spec files with no date prefix | Sort by filesystem mtime descending, prefer dated files. |

---

## Out of Scope

- Installing or updating the agent library itself
- Creating or editing agent files
- Auto-running without user approval
- Fetching agents from remote (GitHub API)
- Persisting the user-entered library path across sessions
