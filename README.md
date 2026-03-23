# team — Claude Code Agent Manager

**Assemble a team of AI specialists for your project.** Each agent has a distinct role, works on its own git branch, and hands off clean pull requests — all orchestrated by Claude.

---

## Why agents?

Solo Claude sessions get slow on big tasks. The `team` plugin splits work across specialists:

- A **backend developer** builds the API while a **test automator** writes tests in parallel
- A **code reviewer** checks their work before anything merges
- A **git-workflow manager** keeps branches clean and PRs tidy
- Each agent commits frequently, uses descriptive branches, and never blocks the others

You stay in the driver's seat — agents handle execution.

---

## How it works

```
┌─────────────────────────────────────────────────────────────┐
│                        Your Project                         │
│                                                             │
│   You ──► /team:init-team                                   │
│                  │                                          │
│                  ▼                                          │
│         Claude reads your project,                          │
│         recommends the right agents                         │
│                  │                                          │
│       ┌──────────┼──────────┐                               │
│       ▼          ▼          ▼                               │
│  [backend]  [test-auto]  [reviewer]   ← .claude/agents/     │
│       │          │          │                               │
│       │  branch  │  branch  │  branch                      │
│       ▼          ▼          ▼                               │
│   feat/api   feat/tests  review/api                         │
│       └──────────┴──────────┘                               │
│                  │                                          │
│                  ▼                                          │
│             Pull Requests                                   │
│                  │                                          │
│                  ▼                                          │
│              main branch                                    │
└─────────────────────────────────────────────────────────────┘
```

**Rule files** in `.claude/rules/` keep every agent aligned — architecture decisions, tech stack, git conventions — no agent goes rogue.

---

## Install

Two commands in Claude Code:

```
/plugin marketplace add https://github.com/mbaltunsu/claude-code-agent-team-manager.git
```

```
/plugin install team@agent-team-manager
```

Done. The three `team:` skills are now available in every project.

> **Requires:** Python 3.8+ · `git` (for downloading agents)

---

## Updating

The plugin auto-updates at the start of each Claude Code session — no action needed. You'll see a brief notice in the session output when a new version is applied.

**Manual update:**
```
/team:init-team update
```

**Via Claude Code plugin system** (requires refreshing the marketplace cache first):
```
/plugin marketplace remove agent-team-manager
/plugin marketplace add https://github.com/mbaltunsu/claude-code-agent-team-manager.git
/plugin update team@agent-team-manager
```

---

## Skills

### `/team:init-project` — Start here on a new project

Sets up your project's Claude Code configuration from scratch:

1. Creates `.claude/agents/` and `.claude/rules/` directories
2. Writes a `CLAUDE.md` from a battle-tested starter template (asks permission first)
3. Generates rule files for your specific project — architecture, tech stack, git conventions — based on what it finds in your codebase

Run this **once**, at the beginning of a project.

---

### `/team:join-project` — Join an existing project

Joining a project someone else set up? This gives you the full picture:

```
/team:join-project
```

Claude will:
- Read all rule files, CLAUDE.md, TEAM.md, and your codebase
- Present a structured **project briefing** (purpose, tech stack, architecture, git workflow, active agents)
- Ask if anything is outdated or missing
- Help you update rules and add agents for your specific task

Run this when you're **new to a project** or returning after a long break.

---

### `/team:init-team` — Assemble your team

Scans the agent library, reads your project context, and recommends the best agents for your stack and goals.

```
/team:init-team
```

Claude will:
- Scan available agents from the library
- Read your CLAUDE.md, plans, specs, and tech stack files
- Show a recommendation table with reasons
- Ask for your approval before copying anything

Agents are copied to `.claude/agents/` and tracked in `TEAM.md`. Your `CLAUDE.md` gets an **Agents and Rules** section listing what's installed.

**Quick actions:**
| Command | What it does |
|---|---|
| `/team:init-team list` | Show all installed agents |
| `/team:init-team remove python-pro.md` | Remove an agent |
| `/team:init-team update` | Self-update the plugin |
| `/team:init-team source list` | Show registered agent sources |
| `/team:init-team import <path>` | Import a local library |
| `/team:init-team stats` | Show session usage statistics |

---

### `/team:add-agent` — Add one agent

Add a single agent when you know what you need:

```
/team:add-agent python-pro.md
```

Or describe what you need and let Claude find the best match:

```
/team:add-agent an agent that can write automated tests
```

Claude scans the library, shows you matches, and adds the one you pick.

---

## Agent library

All agents live in one place: `~/.claude/team-management/agents/`

This central store works across all your projects — no per-project setup needed. The plugin comes pre-connected to the official **[VoltAgent/awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents)** collection.

**First run:** if the store is empty, you'll be offered three options:
1. Download from the official VoltAgent source
2. Import from a local folder you already have
3. Add a custom source (your own git repo)

You can manage sources at any time:

| Command | What it does |
|---|---|
| `/team:init-team source list` | See all registered sources |
| `/team:init-team source add <url>` | Add your own agent repo |

---

## Effective agent teamwork

Once your team is set up, here's how to get the most out of it:

**Parallel work with worktrees**

```
# Claude orchestrates — agents run in parallel, each on their own branch
Use subagents for work that can run in parallel.
Use worktrees so agents don't step on each other.
```

Worktree branches are **automatically pushed to remote** when an agent finishes (via a SubagentStop hook), so all agent work is visible for review on GitHub.

**Session statistics**

Track how much work your agents are doing:

```
/team:init-team stats
```

Shows total tokens, duration, lines changed, tool usage, and how many sessions used parallel agents — all from Claude Code's built-in session metadata.

**Git discipline built in**

Every agent is instructed to:
- Create a branch before starting any work
- Commit frequently with descriptive messages
- Open a pull request when done — never push direct to main

**Design first**

The `.claude/rules/architecture.md` file gives every agent the same architectural context before they write a single line.

---

## What gets created

```
your-project/
├── CLAUDE.md              ← team roster + collaboration guidelines
├── TEAM.md                ← full agent list with descriptions
└── .claude/
    ├── agents/
    │   ├── backend-developer.md
    │   ├── python-pro.md
    │   └── test-automator.md
    └── rules/
        ├── git-rules.md
        ├── architecture.md
        ├── tech-stack.md
        └── project-context.md
```

---

## Credits

Agent library by **[VoltAgent/awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents)** — a community-curated collection of Claude Code subagents. If this saves you time, give them a star.
