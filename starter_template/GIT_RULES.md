## Version Control and Parallel Workflows

### Git Workflow Rules

- Always use git for any non-trivial change.
- Create .gitignore template if does not exist.
- Never work directly on `main` or `stage`.
- Always create a dedicated branch before starting work.
- Use branch prefixes consistently:
  - `feature/...` for new features
  - `fix/...` for bug fixes
  - `refactor/...` for internal code improvements
  - `chore/...` for maintenance tasks
  - `docs/...` for documentation only
  - `test/...` for test-related work

Examples:

- `feature/wallet-merge-session-detection`
- `fix/polygon-deposit-confirmation`
- `refactor/blockchain-event-processor`

### Commit Discipline

- Create small, clean, logically separated commits.
- Each commit should represent one meaningful unit of change.
- Do not mix unrelated changes in the same commit.
- Commit messages must be clear and descriptive.

Preferred commit message style:

- `feat: add TON wallet session merge handling`
- `fix: prevent duplicate polygon deposit processing`
- `refactor: extract balance update logic into service`
- `docs: update deposit verification workflow`
- `test: add coverage for wallet linking flow`

Commit rules:

- Commit early when a unit of work is complete.
- Commit before risky refactors.
- Commit after tests pass for the changed unit.
- Avoid large “everything changed” commits.
- Do not include formatting-only noise unless intentional and isolated.

### Staging Rules

- Stage only the files relevant to the current change.
- Review staged diff before every commit.
- Do not commit unrelated edits, temporary debugging code, or commented-out code.
- Keep generated files, secrets, and local environment changes out of commits unless explicitly required.

Before committing:

1. Review `git diff`
2. Review `git diff --staged`
3. Confirm scope is clean and isolated
4. Confirm no secrets or accidental files are included

### Branching Rules

- Branch from the correct base branch:
  - branch from `main` for normal feature/fix work unless team workflow requires otherwise
  - use `stage` only when the workflow explicitly requires integration against staging
- Keep branches focused on a single task.
- Rebase or sync regularly to reduce merge conflicts.
- Do not leave long-lived branches drifting far from base.

### Parallel Work with Subagents

- When multiple subagents or parallel efforts are used, each one must work in its own branch or git worktree.
- Never let multiple subagents edit the same working tree simultaneously.
- Prefer separate worktrees for parallel implementation, investigation, or refactoring streams.
- One task, one branch, one worktree.

Examples:

- `feature/deposit-indexer`
- `fix/ton-confirmation-race`
- `refactor/webhook-idempotency`

Parallel workflow rules:

- Isolate each parallel task completely
- Merge only after reviewing conflicts and behavior
- Do not combine unrelated subagent outputs blindly
- Re-verify integration after merging parallel work

### Merge Rules

- Merge feature/fix branches into `main` or `stage` only after:
  - implementation is complete
  - tests pass
  - diff is reviewed
  - scope is clean
  - no debug artifacts remain
- Prefer clean history.
- Squash merge when the branch contains noisy intermediate commits.
- Preserve separate commits when they are already clean and meaningful.

### Main and Stage Protection

- `main` must remain stable and production-quality.
- `stage` must remain integration-ready and reasonably stable.
- Never push experimental or half-finished work directly to `main` or `stage`.
- All work should flow through feature/fix/refactor branches first, then merge into `stage` or `main` according to release workflow.

### Sync and Safety Rules

- Sync with the base branch before opening or finalizing a merge.
- Resolve conflicts carefully, not mechanically.
- After syncing or merging:
  - rerun relevant tests
  - verify changed flows
  - confirm no regressions
- If parallel work overlaps, explicitly review integration boundaries.

### Definition of Good Git Hygiene

- Branch names are consistent
- Commits are small and purposeful
- Commit messages explain intent
- History is readable
- Diffs are easy to review
- Parallel work is isolated
- `main` and `stage` stay clean

## Non-Negotiables

- Do not work directly on `main` or `stage`
- Do not make large mixed-purpose commits
- Do not combine unrelated changes in one branch
- Do not let parallel subagents share the same worktree
- Do not merge without reviewing diff and verifying behavior
