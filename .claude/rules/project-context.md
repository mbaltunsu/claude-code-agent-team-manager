# Project Context

## Purpose

A Claude Code plugin that manages AI agent teams for software projects. It solves the problem of manually setting up Claude Code subagents by automating discovery, recommendation, installation, and documentation of agents from a curated library.

## Users / Audience

Claude Code users (developers) who want to:
- Use multiple specialized agents (backend dev, test automator, code reviewer, etc.) on their projects
- Bootstrap Claude Code configuration quickly on new projects
- Maintain a consistent team of agents across a project lifecycle

## Current State

Active development — v4.0.0. Core functionality complete and test-covered (101 tests). Three skills fully operational under the `team:` namespace. Central agents store and sources registry introduced in v4.0.

## Key Goals

1. **Zero-friction setup** — run one command, get a working agent team configured for your specific project
2. **Central agent store** — agents live in `~/.claude/team-management/agents/`, shared across all projects, never need per-project library setup
3. **Official + custom sources** — VoltAgent community library pre-wired; users can add their own repos

## Do Not

- Do not add third-party dependencies to `init_team.py` — stdlib only
- Do not write to the real home directory in tests — always mock `SOURCES_REGISTRY`, `DEFAULT_AGENTS_DIR`, and `TEAM_MANAGEMENT_DIR`
- Do not break Python 3.8 compatibility — no walrus operator, no `str | None` union syntax, no `match` statements
- Do not silently overwrite existing agent files — every copy/import operation must respect the merge-safe contract
- Do not add logic to SKILL.md files — they are instructions for Claude, not code; keep all logic in `init_team.py`
- Do not commit to `main` directly — all work goes through a feature/fix branch and PR
