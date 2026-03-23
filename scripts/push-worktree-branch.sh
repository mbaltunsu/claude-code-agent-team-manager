#!/bin/bash
# SubagentStop hook: auto-push worktree branches to remote.
# Reads JSON from stdin (hook payload with cwd field).
# Only pushes if cwd is inside a git worktree (not the main working tree)
# and the branch is not main/master.

INPUT=$(cat)

# Extract cwd from JSON — try py first (Windows), then python3
CWD=$(echo "$INPUT" | py -c "import sys,json; print(json.load(sys.stdin).get('cwd',''))" 2>/dev/null)
if [ -z "$CWD" ]; then
  CWD=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('cwd',''))" 2>/dev/null)
fi
if [ -z "$CWD" ]; then
  CWD=$(echo "$INPUT" | python -c "import sys,json; print(json.load(sys.stdin).get('cwd',''))" 2>/dev/null)
fi

if [ -z "$CWD" ] || [ ! -d "$CWD" ]; then
  exit 0
fi

cd "$CWD" || exit 0

# Only proceed if inside a git repo
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  exit 0
fi

# Check if this is a worktree (not the main working tree)
MAIN_WORKTREE=$(git worktree list --porcelain 2>/dev/null | head -1 | sed 's/worktree //')
CURRENT=$(pwd -P)

# Normalize paths for comparison (handle Windows path differences)
MAIN_WORKTREE=$(echo "$MAIN_WORKTREE" | sed 's|\\|/|g' | sed 's|/$||')
CURRENT=$(echo "$CURRENT" | sed 's|\\|/|g' | sed 's|/$||')

if [ "$CURRENT" = "$MAIN_WORKTREE" ]; then
  # Not a worktree — do not push from main working tree
  exit 0
fi

BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)

if [ -z "$BRANCH" ] || [ "$BRANCH" = "HEAD" ] || [ "$BRANCH" = "main" ] || [ "$BRANCH" = "master" ]; then
  exit 0
fi

# Push the branch to remote (silently fail if no remote or auth issues)
git push -u origin "$BRANCH" 2>/dev/null || true
