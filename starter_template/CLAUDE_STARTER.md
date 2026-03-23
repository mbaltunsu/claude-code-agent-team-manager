## Workflow Orchestration

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
- **Recommended Library Versions:** Always try to use latest stable or recommended versions of libraries,frameworks,apis,packages unless another version is absolutely necessary because of a dependency

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
