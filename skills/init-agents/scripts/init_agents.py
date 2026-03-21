#!/usr/bin/env python3
"""init_agents.py — CLI script for the Claude Code init-agents skill."""

import argparse
import json
import re
import shutil
import sys
from pathlib import Path


def _ensure_utf8_stdout():
    """Force UTF-8 stdout on Windows to handle unicode characters."""
    try:
        if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
            sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass  # Python < 3.7


def load_env(cwd: Path) -> dict:
    """Parse .env file in cwd, return key=value pairs. Ignores comments."""
    env_file = cwd / ".env"
    result = {}
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                result[key.strip()] = value.strip()
    return result


def resolve_library_path(cli_path: str | None, env_path: str | None) -> str:
    """Resolve library path: CLI arg > env var > error."""
    path_str = cli_path or env_path
    if not path_str:
        print(
            "Error: No library path provided. "
            "Set AGENTS_LIBRARY_PATH in .env or pass --path.",
            file=sys.stderr,
        )
        sys.exit(1)
    path = Path(path_str)
    if not path.exists():
        print(f"Error: Path does not exist: {path_str}", file=sys.stderr)
        sys.exit(1)
    if not (path / "categories").is_dir():
        print(
            f"Error: Expected a 'categories/' subdirectory in {path_str}. "
            "Is this the correct library path?",
            file=sys.stderr,
        )
        sys.exit(1)
    return str(path)


def parse_frontmatter(content: str) -> dict | None:
    pass  # TODO Task 3


def cmd_scan(library_path: str):
    pass  # TODO Task 3


def update_claude_md(claude_md_path: Path, copied_files: list, dest_dir: Path):
    pass  # TODO Task 4


def cmd_copy(library_path: str, agents_arg: str, dest: str, claude_md: str = "CLAUDE.md"):
    pass  # TODO Task 4


def main():
    _ensure_utf8_stdout()
    parser = argparse.ArgumentParser(description="init-agents script")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_p = subparsers.add_parser("scan")
    scan_p.add_argument("--path", help="Path to agent library")

    copy_p = subparsers.add_parser("copy")
    copy_p.add_argument("--path", help="Path to agent library")
    copy_p.add_argument("--agents", required=True, help="Comma-separated category/file paths")
    copy_p.add_argument("--dest", default=".claude/agents", help="Destination directory")
    copy_p.add_argument("--claude-md", default="CLAUDE.md", help="Path to project CLAUDE.md")

    args = parser.parse_args()
    env = load_env(Path.cwd())
    library_path = resolve_library_path(
        cli_path=args.path,
        env_path=env.get("AGENTS_LIBRARY_PATH"),
    )

    if args.command == "scan":
        cmd_scan(library_path)
    elif args.command == "copy":
        cmd_copy(library_path, args.agents, args.dest, args.claude_md)


if __name__ == "__main__":
    main()
