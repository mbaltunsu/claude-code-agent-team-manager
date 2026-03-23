# Claude Code Agent Team Manager

A Claude Code skill + plugin that manages your project's agent team. Bootstrap, add, remove, list, and update agents from a central library. Scans the library, recommends agents using AI and full project context, copies approved agents to `.claude/agents/`, and tracks them in `TEAM.md`. Supports capability-based matching and self-update. Can auto-download agents from GitHub for users without a local library.

---

## Repository Structure

```
claude-code-agent-team-manager/
├── .claude-plugin/
│   ├── marketplace.json     ← plugin marketplace manifest (plugin name: "team")
│   └── plugin.json          ← plugin identity and metadata
├── .gitignore
├── hooks/
│   └── hooks.json           ← SessionStart (auto-update) + SubagentStop (auto-push worktree branches)
├── scripts/
│   └── push-worktree-branch.sh  ← auto-push worktree branches to remote on SubagentStop
├── skills/
│   ├── init-team/
│   │   ├── SKILL.md          ← team:init-team skill (full agent roster setup)
│   │   └── scripts/
│   │       ├── init_team.py         ← Python CLI: scan, copy, add, remove, list, update, download, init-project, update-docs, import, source-list, source-add, source-remove, stats
│   │       ├── conftest.py          ← pytest path and encoding setup
│   │       └── tests/
│   │           ├── test_path_resolution.py
│   │           ├── test_scan.py
│   │           ├── test_copy.py
│   │           ├── test_add.py
│   │           ├── test_remove.py
│   │           ├── test_list.py
│   │           ├── test_update.py
│   │           ├── test_download.py
│   │           ├── test_init_project.py
│   │           ├── test_sources.py
│   │           ├── test_import.py
│   │           └── test_stats.py
│   ├── add-agent/
│   │   └── SKILL.md          ← team:add-agent skill (add single agent by name or capability)
│   └── init-project/
│       └── SKILL.md          ← team:init-project skill (bootstrap .claude/rules and CLAUDE.md)
├── starter_template/
│   ├── CLAUDE_STARTER.md    ← workflow guide; copied to user project's CLAUDE.md by init-project
│   ├── GIT_RULES.md         ← git rules; copied to .claude/rules/git-rules.md by init-project
│   └── FRONTEND_RULES.md   ← frontend rules; available for frontend projects
├── docs/
│   └── superpowers/
│       ├── specs/           ← design specs (one per feature)
│       └── plans/           ← implementation plans
├── README.md
├── CLAUDE.md                ← this file
└── .env.example
```

---

## How It Works

Two components work together:

Three skills work together under the `team:` namespace:

1. **`team:init-team`** — Full agent roster setup: scans library → gathers project context → recommends agents → copies approved agents → updates `TEAM.md` and `## Agents and Rules` in `CLAUDE.md`.
2. **`team:add-agent`** — Add a single agent by filename or capability description. Updates `TEAM.md` and `CLAUDE.md`.
3. **`team:init-project`** — Bootstrap a new project: creates `.claude/rules/` and `.claude/agents/`, copies `CLAUDE_STARTER.md` to `CLAUDE.md` (with explicit permission), and generates rule files from AI plan context.

All three invoke **`init_team.py`** (Python CLI) for filesystem operations. Nine subcommands:
   - `scan --path <library>` — walks `categories/` in the agent library, reads frontmatter, returns JSON
   - `copy --agents <paths> --path <library> --dest <dir> --claude-md <file> --team-md <file>` — copies approved agents, skips existing ones, writes `TEAM.md`, updates `CLAUDE.md`
   - `add --agent <file> --path <library> --dest <dir>` — add a single agent by filename, updates TEAM.md and CLAUDE.md
   - `remove --agent <file> --dest <dir>` — remove an agent, updates TEAM.md and CLAUDE.md
   - `list --dest <dir>` — list installed agents as JSON
   - `update [--repo <url>]` — self-update plugin from GitHub, compares versions
   - `download [--dest <dir>] [--repo <url>]` — downloads agents from GitHub using git sparse-checkout, merge-safe (never overwrites)
   - `init-project --rules-dest <dir> --agents-dest <dir> --git-rules-src <file>` — create dirs, copy git-rules.md, output JSON
   - `update-docs --claude-md <file> --team-md <file> --agents-dest <dir> --rules-dest <dir>` — refresh `## Agents and Rules` section in CLAUDE.md
   - `import --path <library> [--dest <dir>]` — copy local agent library into central store (`~/.claude/team-management/agents/`), merge-safe
   - `source-list` — print JSON of all registered sources
   - `source-add --repo <url> --name <name> [--author] [--homepage] [--description]` — register a new agent source
   - `source-remove --id <id>` — remove a source from the registry

---

## Development

### Requirements

- Python 3.8+
- pytest (`pip install pytest`)

### Running Tests

```bash
cd skills/init-team/scripts
pytest tests/ -v
```

All tests use `tmp_path` fixtures — no real agent library or project needed.

### Conventions

- **TDD**: write the failing test first, implement minimally, confirm green, commit
- **stdlib only**: `init_team.py` must not import anything outside the Python standard library
- **Python 3.8+**: use `Optional[str]` from `typing`, not `str | None`
- **Cross-platform**: use `Path` for all filesystem operations; `[OK]`/`[SKIP]` markers instead of Unicode symbols
- **One concern per test file**: `test_path_resolution.py`, `test_scan.py`, `test_copy.py`, `test_download.py`
- **UTF-8 everywhere**: all file reads and writes use `encoding="utf-8"`

### Commit style

```
feat: short description of what was added
fix: short description of what was corrected
docs: documentation-only changes
chore: scaffolding, tooling, config
```

---

## Plugin Installation (for users)

In Claude Code, run:

```
/plugin marketplace add https://github.com/mbaltunsu/claude-code-agent-team-manager.git
/plugin install init-team@agent-team-manager
```

Then run `/init-team` in any Claude Code project.

---

## Manual Installation (alternative)

Copy the skill folder into a project or globally:

```bash
# Per-project
cp -r skills/init-team/ /your/project/.claude/skills/

# Global
cp -r skills/init-team/ ~/.claude/skills/
```

---

## Agent Library Format

The skill expects an agent library with this structure:

```
<AGENTS_LIBRARY_PATH>/
└── categories/
    ├── 01-core-development/
    │   ├── backend-developer.md
    │   └── frontend-developer.md
    ├── 02-language-specialists/
    │   └── python-expert.md
    └── <any-category-folder>/
        └── <any-agent>.md
```

Each agent file needs YAML frontmatter with `name` and `description`.

Set `AGENTS_LIBRARY_PATH` in a `.env` file at the project root. See `.env.example`.

If you don't have a local library, the skill can auto-download from [VoltAgent/awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents).

---

## Docs

- `docs/superpowers/specs/` — design decisions and feature specs
- `docs/superpowers/plans/` — step-by-step implementation plans

## Agents and Rules

See [TEAM.md](TEAM.md) for the full agent roster.

- Use `.claude/rules/x.md` files for project-specific rules (architecture, tech stack, git, context).
- Add project-specific details to these files. Run `/team:init-project` to bootstrap them.

### Installed Rules

- [git-rules.md](.claude/rules/git-rules.md) — version control discipline, branching strategy, and parallel subagent workflows
- [architecture.md](.claude/rules/architecture.md) — plugin architecture, component responsibilities, and design constraints
- [tech-stack.md](.claude/rules/tech-stack.md) — language, stdlib-only policy, tooling, and coding conventions
- [project-context.md](.claude/rules/project-context.md) — project purpose, audience, current state, and hard constraints

### Team Collaboration Guidelines

- Always try to use TEAM agents for different tasks — distribute work efficiently
- Use subagents mode for parallelizable work (e.g., tests + implementation in parallel)
- Use worktrees and different branches for better teamwork — avoid conflicts
- Every agent should utilize git: commit frequently, use descriptive branch names
- Use design/architecture agents early in development before implementation agents
- When a new agent or rule is added manually, update TEAM.md and this section
- Run `/team:init-project` to bootstrap rules for a new project
- Run `/team:add-agent` to add a single agent by name or capability
- Run `/team:init-team` to set up a full agent roster

---

## Workflow and Behavior Rules

### 1. Plan Mode Default

- Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions)
- If something goes sideways, STOP and re-plan immediately
- Use plan mode for verification steps, not just building
- Write detailed specs upfront to reduce ambiguity

### 2. Subagent Strategy

- Use subagents liberally to keep main context window clean
- Offload research, exploration, and parallel analysis to subagents
- For complex problems, throw more compute at it via subagents
- One task per subagent for focused execution

### 3. Self-Improvement Loop

- After ANY correction from the user: update `tasks/lessons.md` with the pattern
- Write rules for yourself that prevent the same mistake
- Ruthlessly iterate on these lessons until mistake rate drops
- Review lessons at session start for relevant project

### 4. Verification Before Done

- Never mark a task complete without proving it works
- Diff behavior between main and your changes when relevant
- Ask yourself: "Would a staff engineer approve this?"
- Run tests, check logs, demonstrate correctness

### 5. Demand Elegance (Balanced)

- For non-trivial changes: pause and ask "Is there a more elegant way?"
- If a fix feels hacky: "Knowing everything I know now, implement the elegant solution"
- Skip this for simple, obvious fixes — don't over-engineer
- Challenge your own work before presenting it

### 6. Autonomous Bug Fixing

- When given a bug report: just fix it. Don't ask for hand-holding
- Point at logs, errors, failing tests — then resolve them
- Zero context switching required from the user
- Go fix failing CI tests without being told how

---

## Task Management

1. **Plan First:** Write plan to `tasks/todo.md` with checkable items
2. **Verify Plan:** Check in before starting implementation
3. **Track Progress:** Mark items complete as you go
4. **Explain Changes:** High-level summary at each step
5. **Document Results:** Add review section to `tasks/todo.md`
6. **Capture Lessons:** Update `tasks/lessons.md` after corrections

---

## Core Principles

- **Simplicity First:** Make every change as simple as possible. Impact minimal code.
- **No Laziness:** Find root causes. No temporary fixes. Senior developer standards.
- **Minimal Impact:** Only touch what's necessary. No side effects with new bugs.

## Code Change Rules

When modifying code:

- Never rewrite entire files unless necessary
- Prefer minimal diff changes
- Preserve existing architecture patterns
- Do not introduce new dependencies without reason
- Do not change naming conventions

Before changing:

1. Understand existing pattern
2. Follow same style
3. Keep changes minimal

## Debugging Protocol

When debugging:

Step 1 — Reproduce issue
Step 2 — Check logs
Step 3 — Check recent changes
Step 4 — Identify root cause
Step 5 — Fix cause not symptom
Step 6 — Verify no regressions

Never:

- Guess fixes
- Apply blind patches
- Change multiple systems at once

## Response Format Rules

When implementing features:

Always provide:

1. Plan
2. Files affected
3. Changes
4. Risks
5. Verification steps

For bug fixes provide:

1. Root cause
2. Fix
3. Why it happened
4. Prevention

## Performance Rules

Prefer:

- O(1) lookups
- Indexed queries
- Batch operations

Avoid:

- N+1 queries
- Unbounded loops on DB

Always:

- Cache expensive reads
- Use pagination

## AI Behavior Rules

Do not:

- Invent APIs
- Assume library behavior

If unsure:

- State uncertainty
- Suggest verification

Prefer:

- Existing project patterns
- Simple solutions
- Deterministic logic
