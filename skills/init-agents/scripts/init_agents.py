#!/usr/bin/env python3
"""init_agents.py — CLI script for the Claude Code init-agents skill."""

import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Optional


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


def resolve_library_path(cli_path: Optional[str], env_path: Optional[str]) -> str:
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


def parse_frontmatter(content: str) -> Optional[dict]:
    """Extract name and description from YAML frontmatter. Returns None if invalid."""
    # Normalize line endings for cross-platform compatibility
    content = content.replace("\r\n", "\n")
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n?", content, re.DOTALL)
    if not match:
        return None
    fm_text = match.group(1)
    result = {}
    for line in fm_text.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            result[key.strip()] = value.strip().strip('"').strip("'")
    name = result.get("name", "").strip()
    description = result.get("description", "").strip()
    if not name or not description:
        return None
    return {"name": name, "description": description}


def cmd_scan(library_path: str):
    """Scan agent library, print JSON array to stdout."""
    categories_dir = Path(library_path) / "categories"
    agents = []
    for category_dir in sorted(categories_dir.iterdir()):
        if not category_dir.is_dir():
            continue
        for agent_file in sorted(category_dir.glob("*.md")):
            if agent_file.name.lower() == "readme.md":
                continue
            content = agent_file.read_text(encoding="utf-8")
            fm = parse_frontmatter(content)
            if fm is None:
                print(
                    f"Warning: Skipping {agent_file.name} — invalid or missing frontmatter",
                    file=sys.stderr,
                )
                continue
            agents.append({
                "category": category_dir.name,
                "name": fm["name"],
                "file": agent_file.name,
                "path": f"{category_dir.name}/{agent_file.name}",
                "description": fm["description"],
            })
    print(json.dumps(agents, indent=2))


def update_claude_md(claude_md_path: Path, copied_files: list, dest_dir: Path):
    """Add/update ## Project Team section in CLAUDE.md with newly copied agents."""
    # Read agent info from their installed files
    new_agents = {}
    for filename in copied_files:
        agent_file = dest_dir / filename
        if not agent_file.exists():
            continue
        content = agent_file.read_text(encoding="utf-8")
        fm = parse_frontmatter(content)
        if fm:
            new_agents[filename] = fm

    if not new_agents:
        return

    # Read existing CLAUDE.md or start fresh
    if claude_md_path.exists():
        claude_content = claude_md_path.read_text(encoding="utf-8").replace("\r\n", "\n")
    else:
        claude_content = ""

    section_header = "## Project Team"
    note = (
        "> If you add agents manually to `.claude/agents/`, "
        "add them to this section too."
    )

    # Parse existing agent entries from current Project Team section (if any)
    existing_entries = {}
    section_pattern = re.compile(r"^## Project Team\n(.*?)(?=^## |\Z)", re.DOTALL | re.MULTILINE)
    match = section_pattern.search(claude_content)
    if match:
        for line in match.group(1).splitlines():
            m = re.match(r"^- \*\*(.+?)\*\*: (.+)$", line)
            if m:
                existing_entries[m.group(1)] = line  # keyed by name

    # Merge: existing + new (new overwrites existing on same filename)
    for filename, fm in new_agents.items():
        agent_name = fm["name"]
        if agent_name in existing_entries:
            print(
                f"Warning: Agent name '{agent_name}' from {filename} conflicts with an existing entry — overwriting.",
                file=sys.stderr,
            )
        existing_entries[agent_name] = (
            f"- **{fm['name']}**: {fm['description']}"
        )

    agent_lines = "\n".join(
        existing_entries[k] for k in sorted(existing_entries.keys())
    )
    new_section = (
        f"{section_header}\n\n"
        f"The following agents are active in this project:\n\n"
        f"{agent_lines}\n\n"
        f"{note}\n"
    )

    if match:
        claude_content = section_pattern.sub(lambda _: new_section, claude_content)
    else:
        claude_content = claude_content.rstrip("\n") + "\n\n" + new_section + "\n"

    claude_md_path.write_text(claude_content, encoding="utf-8")
    print(f"Updated CLAUDE.md — Project Team section now has {len(existing_entries)} agent(s).")


def cmd_copy(library_path: str, agents_arg: str, dest: str, claude_md: str = "CLAUDE.md"):
    """Copy approved agents to dest directory. Skips existing. Updates CLAUDE.md."""
    agent_paths = [a.strip() for a in agents_arg.split(",") if a.strip()]
    if not agent_paths:
        print("No agents to copy. Exiting.")
        return

    dest_dir = Path(dest)
    dest_dir.mkdir(parents=True, exist_ok=True)

    copied = []
    skipped = []

    for rel_path in agent_paths:
        source = Path(library_path) / "categories" / rel_path
        filename = Path(rel_path).name
        destination = dest_dir / filename

        if destination.exists():
            print(f"[SKIP] {filename} already exists — skipped")
            skipped.append(filename)
        else:
            shutil.copy2(source, destination)
            print(f"[OK] {filename} copied")
            copied.append(filename)

    print(f"\n{len(copied)} agent(s) copied, {len(skipped)} skipped.")
    if skipped:
        print(f"Skipped: {', '.join(skipped)}")

    if copied:
        update_claude_md(Path(claude_md), copied, dest_dir)


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
