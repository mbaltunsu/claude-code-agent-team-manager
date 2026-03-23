---
name: stats
description: "Show session usage statistics: tokens, cost, duration, tool usage, and agent vs non-agent comparison. Use to understand how agents impact your workflow and token usage."
---

# Stats Skill

Show usage statistics for Claude Code sessions in this project.

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

## Step 2: Run Stats Command

**Project-scoped stats (default):**
```bash
<PYTHON> "${CLAUDE_PLUGIN_ROOT}/skills/init-team/scripts/init_team.py" stats --project "<CWD>" --last 20
```

**Global stats** (if user says "all", "global", or "all projects"):
```bash
<PYTHON> "${CLAUDE_PLUGIN_ROOT}/skills/init-team/scripts/init_team.py" stats --last 50
```

Parse the JSON output.

---

## Step 3: Display Results

Format the output as a readable summary:

```
Session Statistics (last N sessions)
=====================================

| Metric                    | Value         |
|---------------------------|---------------|
| Sessions                  | 20            |
| Total tokens (in / out)   | 50,000 / 12,000 |
| Total duration            | 45 min        |
| Lines changed (+/-)       | +320 / -80    |
| Files modified            | 25            |
| Commits                   | 8             |
| Agent sessions            | 12 of 20      |

Agent Impact
------------
| Metric                        | With Agents | Without Agents |
|-------------------------------|-------------|----------------|
| Avg tokens per session        | 4,200       | 2,800          |
| Avg duration (min)            | 8           | 3              |
| Estimated overhead per session| +1,400 tokens (~50% more) |

Top Tools: Agent: 15, Bash: 40, Edit: 30, Read: 25
```

Use commas for large numbers. Round percentages to nearest integer.

If `non_agent_sessions` is 0, skip the "Agent Impact" comparison and note:
> "All sessions used agents — no baseline comparison available yet."

If `agent_sessions` is 0, skip it and note:
> "No agent sessions found — run `/team:init-team` to set up your agent team."

---

## Step 4: Interpretation

After the table, add a brief one-line interpretation:

- If agent overhead is < 30%: "Agent overhead is minimal — good efficiency."
- If agent overhead is 30-100%: "Agents add moderate overhead but enable parallel work and specialization."
- If agent overhead is > 100%: "High agent overhead — consider using agents only for complex, parallelizable tasks."
- If not enough data: "Not enough sessions to draw conclusions yet."
