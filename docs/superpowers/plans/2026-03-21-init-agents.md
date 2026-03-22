# Init-Agents Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Claude Code skill that scans a central agent library, recommends agents for the current project using AI, and copies approved agents into `.claude/agents/` without overwriting customized ones.

**Architecture:** Two-component design — a Python script (`init_agents.py`) handles all filesystem operations (scan, copy, path resolution) via CLI subcommands; a Claude Code skill file (`init-agents.md`) orchestrates the workflow and uses Claude's reasoning for recommendation and user interaction. Zero external Python dependencies (stdlib only).

**Tech Stack:** Python 3.8+ (stdlib: `re`, `json`, `argparse`, `shutil`, `sys`, `pathlib`), Markdown (skill file), pytest (tests)

---

## File Map

| File | Role |
|---|---|
| `skills/init-agents/init-agents.md` | Claude Code skill file — orchestrates the full workflow |
| `skills/init-agents/scripts/init_agents.py` | Python CLI: `scan` and `copy` subcommands |
| `skills/init-agents/scripts/conftest.py` | pytest path + encoding setup |
| `skills/init-agents/scripts/tests/__init__.py` | Makes tests a package |
| `skills/init-agents/scripts/tests/test_path_resolution.py` | Tests for `load_env` and `resolve_library_path` |
| `skills/init-agents/scripts/tests/test_scan.py` | Tests for `parse_frontmatter` and `cmd_scan` |
| `skills/init-agents/scripts/tests/test_copy.py` | Tests for `cmd_copy` and `update_claude_md` |
| `.env.example` | Documents `AGENTS_LIBRARY_PATH` |
| `CLAUDE.md` | Project instructions for this repo |
| `README.md` | Usage and installation guide |

---

### Task 1: Project Scaffold

**Files:**
- Create: `skills/init-agents/scripts/tests/__init__.py`
- Create: `skills/init-agents/scripts/conftest.py`
- Create: `CLAUDE.md`
- Create: `.env.example`

- [ ] **Step 1: Create directory structure** (run from project root)

```bash
mkdir -p skills/init-agents/scripts/tests
touch skills/init-agents/scripts/tests/__init__.py
```

- [ ] **Step 2: Create `conftest.py` so pytest can import the script**

Create `skills/init-agents/scripts/conftest.py`:

```python
import sys
from pathlib import Path

# Allow tests to import init_agents from the parent scripts/ directory
sys.path.insert(0, str(Path(__file__).parent))

# Force UTF-8 stdout for tests on Windows
sys.stdout.reconfigure(encoding="utf-8")
```

- [ ] **Step 3: Create `CLAUDE.md`** (in project root)

```markdown
# Init-Agents Skill

A Claude Code skill that bootstraps agent files into projects from a central agent library.

## Structure

- `skills/init-agents/init-agents.md` — Claude Code skill file
- `skills/init-agents/scripts/init_agents.py` — Python CLI script (stdlib only)
- `skills/init-agents/scripts/tests/` — pytest tests (one file per concern)

## Running Tests

```bash
cd skills/init-agents/scripts
pytest tests/ -v
```

## Installation

Copy `skills/init-agents/` into `.claude/skills/` of any project, or `~/.claude/skills/` for global use.
```

- [ ] **Step 4: Create `.env.example`** (in project root)

```
# Path to your central agent library (e.g. awesome-claude-code-subagents)
AGENTS_LIBRARY_PATH=D:\CLAUDE_AGENTS\awesome-claude-code-subagents
```

- [ ] **Step 5: Initialize git and commit scaffold** (run from project root)

```bash
git init
git add skills/ CLAUDE.md .env.example
git commit -m "chore: project scaffold"
```

---

### Task 2: Python Script — Skeleton + Path Resolution

**Files:**
- Create: `skills/init-agents/scripts/init_agents.py`
- Create: `skills/init-agents/scripts/tests/test_path_resolution.py`

- [ ] **Step 1: Write failing tests for path resolution**

Create `skills/init-agents/scripts/tests/test_path_resolution.py`:

```python
import pytest
from pathlib import Path
from init_agents import load_env, resolve_library_path


# --- load_env ---

def test_load_env_reads_key_value(tmp_path):
    (tmp_path / ".env").write_text("AGENTS_LIBRARY_PATH=/some/path\n", encoding="utf-8")
    result = load_env(tmp_path)
    assert result["AGENTS_LIBRARY_PATH"] == "/some/path"


def test_load_env_ignores_comments(tmp_path):
    (tmp_path / ".env").write_text("# comment\nKEY=value\n", encoding="utf-8")
    result = load_env(tmp_path)
    assert "# comment" not in result
    assert result["KEY"] == "value"


def test_load_env_returns_empty_when_no_file(tmp_path):
    result = load_env(tmp_path)
    assert result == {}


# --- resolve_library_path ---

def test_resolve_uses_cli_arg(tmp_path):
    (tmp_path / "categories").mkdir()
    result = resolve_library_path(cli_path=str(tmp_path), env_path=None)
    assert result == str(tmp_path)


def test_resolve_uses_env_when_no_cli(tmp_path):
    (tmp_path / "categories").mkdir()
    result = resolve_library_path(cli_path=None, env_path=str(tmp_path))
    assert result == str(tmp_path)


def test_resolve_cli_wins_over_env(tmp_path):
    cli_lib = tmp_path / "cli_lib"
    cli_lib.mkdir()
    (cli_lib / "categories").mkdir()
    env_lib = tmp_path / "env_lib"
    env_lib.mkdir()
    (env_lib / "categories").mkdir()
    result = resolve_library_path(cli_path=str(cli_lib), env_path=str(env_lib))
    assert result == str(cli_lib)


def test_resolve_errors_when_neither():
    with pytest.raises(SystemExit):
        resolve_library_path(cli_path=None, env_path=None)


def test_resolve_errors_when_path_not_exist(tmp_path):
    with pytest.raises(SystemExit):
        resolve_library_path(cli_path=str(tmp_path / "nonexistent"), env_path=None)


def test_resolve_errors_when_no_categories(tmp_path):
    with pytest.raises(SystemExit):
        resolve_library_path(cli_path=str(tmp_path), env_path=None)
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd skills/init-agents/scripts
pytest tests/test_path_resolution.py -v
```

Expected: `ImportError` or `ModuleNotFoundError` (script doesn't exist yet)

- [ ] **Step 3: Create script skeleton**

Create `skills/init-agents/scripts/init_agents.py`:

```python
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


def cmd_copy(library_path: str, agents_arg: str, dest: str):
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

    args = parser.parse_args()
    env = load_env(Path.cwd())
    library_path = resolve_library_path(
        cli_path=args.path,
        env_path=env.get("AGENTS_LIBRARY_PATH"),
    )

    if args.command == "scan":
        cmd_scan(library_path)
    elif args.command == "copy":
        cmd_copy(library_path, args.agents, args.dest)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run path resolution tests**

```bash
cd skills/init-agents/scripts
pytest tests/test_path_resolution.py -v
```

Expected: all 8 tests pass

- [ ] **Step 5: Commit** (run from project root)

```bash
git add skills/init-agents/scripts/
git commit -m "feat: script skeleton with path resolution"
```

---

### Task 3: Python Script — Scan Subcommand

**Files:**
- Modify: `skills/init-agents/scripts/init_agents.py` — implement `parse_frontmatter`, `cmd_scan`
- Create: `skills/init-agents/scripts/tests/test_scan.py`

- [ ] **Step 1: Write failing tests for scan**

Create `skills/init-agents/scripts/tests/test_scan.py`:

```python
import json
import pytest
from pathlib import Path
from init_agents import parse_frontmatter, cmd_scan


# --- parse_frontmatter ---

def test_parse_frontmatter_valid():
    content = "---\nname: test-agent\ndescription: A test agent\n---\nBody"
    result = parse_frontmatter(content)
    assert result["name"] == "test-agent"
    assert result["description"] == "A test agent"


def test_parse_frontmatter_missing_description():
    content = "---\nname: test-agent\n---\nBody"
    result = parse_frontmatter(content)
    assert result is None


def test_parse_frontmatter_no_frontmatter():
    content = "Just body text"
    result = parse_frontmatter(content)
    assert result is None


def test_parse_frontmatter_empty_description():
    content = "---\nname: agent\ndescription: \n---\nBody"
    result = parse_frontmatter(content)
    assert result is None


def test_parse_frontmatter_crlf_line_endings():
    content = "---\r\nname: agent\r\ndescription: An agent\r\n---\r\nBody"
    result = parse_frontmatter(content)
    assert result is not None
    assert result["name"] == "agent"
    assert result["description"] == "An agent"


# --- cmd_scan ---

def make_agent_file(directory: Path, filename: str, name: str, description: str):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / filename).write_text(
        f"---\nname: {name}\ndescription: {description}\n---\nContent",
        encoding="utf-8",
    )


def test_scan_returns_agents(tmp_path, capsys):
    cat_dir = tmp_path / "categories" / "01-core-development"
    make_agent_file(cat_dir, "backend-developer.md", "backend-developer", "Backend specialist")
    cmd_scan(str(tmp_path))
    captured = capsys.readouterr()
    agents = json.loads(captured.out)
    assert len(agents) == 1
    assert agents[0]["name"] == "backend-developer"
    assert agents[0]["category"] == "01-core-development"
    assert agents[0]["file"] == "backend-developer.md"
    assert agents[0]["path"] == "01-core-development/backend-developer.md"
    assert agents[0]["description"] == "Backend specialist"


def test_scan_skips_invalid_frontmatter_and_warns(tmp_path, capsys):
    cat_dir = tmp_path / "categories" / "01-core-development"
    cat_dir.mkdir(parents=True)
    (cat_dir / "bad-agent.md").write_text("No frontmatter here", encoding="utf-8")
    cmd_scan(str(tmp_path))
    captured = capsys.readouterr()
    agents = json.loads(captured.out)
    assert len(agents) == 0
    assert "Warning" in captured.err


def test_scan_skips_readme_silently(tmp_path, capsys):
    cat_dir = tmp_path / "categories" / "01-core-development"
    cat_dir.mkdir(parents=True)
    (cat_dir / "README.md").write_text("# README", encoding="utf-8")
    cmd_scan(str(tmp_path))
    captured = capsys.readouterr()
    agents = json.loads(captured.out)
    assert len(agents) == 0
    assert captured.err == ""  # README is skipped silently, no warning


def test_scan_multiple_categories(tmp_path, capsys):
    make_agent_file(tmp_path / "categories" / "01-core", "backend.md", "backend", "Backend")
    make_agent_file(tmp_path / "categories" / "02-lang", "python.md", "python-expert", "Python")
    cmd_scan(str(tmp_path))
    captured = capsys.readouterr()
    agents = json.loads(captured.out)
    assert len(agents) == 2
    categories = {a["category"] for a in agents}
    assert "01-core" in categories
    assert "02-lang" in categories
```

- [ ] **Step 2: Run to confirm failures**

```bash
cd skills/init-agents/scripts
pytest tests/test_scan.py -v
```

Expected: all fail (functions return `None` / `pass`)

- [ ] **Step 3: Implement `parse_frontmatter` and `cmd_scan`**

Replace the `parse_frontmatter` and `cmd_scan` stubs in `init_agents.py`:

```python
def parse_frontmatter(content: str) -> dict | None:
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
```

- [ ] **Step 4: Run scan tests**

```bash
cd skills/init-agents/scripts
pytest tests/test_scan.py -v
```

Expected: all 7 tests pass

- [ ] **Step 5: Run all tests so far to confirm nothing broken**

```bash
cd skills/init-agents/scripts
pytest tests/ -v
```

Expected: all tests pass

- [ ] **Step 6: Commit** (run from project root)

```bash
git add skills/init-agents/scripts/init_agents.py skills/init-agents/scripts/tests/test_scan.py
git commit -m "feat: implement scan subcommand"
```

---

### Task 4: Python Script — Copy Subcommand

**Files:**
- Modify: `skills/init-agents/scripts/init_agents.py` — implement `cmd_copy`
- Create: `skills/init-agents/scripts/tests/test_copy.py`

- [ ] **Step 1: Write failing tests for copy and `update_claude_md`**

Create `skills/init-agents/scripts/tests/test_copy.py`:

```python
import pytest
from pathlib import Path
from init_agents import cmd_copy, update_claude_md


def make_library(base: Path) -> Path:
    """Create a minimal library with one agent."""
    cat_dir = base / "categories" / "01-core-development"
    cat_dir.mkdir(parents=True)
    (cat_dir / "backend-developer.md").write_text(
        "---\nname: backend-developer\ndescription: Backend specialist\n---\nContent",
        encoding="utf-8",
    )
    return base


# --- cmd_copy ---

def test_copy_copies_agent(tmp_path, capsys):
    lib = make_library(tmp_path / "lib")
    dest = tmp_path / "dest"
    cmd_copy(str(lib), "01-core-development/backend-developer.md", str(dest), str(tmp_path / "CLAUDE.md"))
    assert (dest / "backend-developer.md").exists()
    captured = capsys.readouterr()
    assert "[OK] backend-developer.md copied" in captured.out


def test_copy_creates_dest_if_missing(tmp_path):
    lib = make_library(tmp_path / "lib")
    dest = tmp_path / "new_dest"
    assert not dest.exists()
    cmd_copy(str(lib), "01-core-development/backend-developer.md", str(dest), str(tmp_path / "CLAUDE.md"))
    assert dest.exists()


def test_copy_skips_existing_and_preserves_content(tmp_path, capsys):
    lib = make_library(tmp_path / "lib")
    dest = tmp_path / "dest"
    dest.mkdir()
    (dest / "backend-developer.md").write_text("custom content", encoding="utf-8")
    cmd_copy(str(lib), "01-core-development/backend-developer.md", str(dest), str(tmp_path / "CLAUDE.md"))
    assert (dest / "backend-developer.md").read_text(encoding="utf-8") == "custom content"
    captured = capsys.readouterr()
    assert "[SKIP]" in captured.out


def test_copy_summary_counts_correctly(tmp_path, capsys):
    lib = make_library(tmp_path / "lib")
    dest = tmp_path / "dest"
    dest.mkdir()
    (dest / "backend-developer.md").write_text("custom", encoding="utf-8")
    cmd_copy(str(lib), "01-core-development/backend-developer.md", str(dest), str(tmp_path / "CLAUDE.md"))
    captured = capsys.readouterr()
    assert "0 agent(s) copied, 1 skipped" in captured.out


def test_copy_lists_skipped_names_in_summary(tmp_path, capsys):
    lib = make_library(tmp_path / "lib")
    dest = tmp_path / "dest"
    dest.mkdir()
    (dest / "backend-developer.md").write_text("custom", encoding="utf-8")
    cmd_copy(str(lib), "01-core-development/backend-developer.md", str(dest), str(tmp_path / "CLAUDE.md"))
    captured = capsys.readouterr()
    assert "Skipped: backend-developer.md" in captured.out


def test_copy_zero_agents_prints_message(tmp_path, capsys):
    lib = make_library(tmp_path / "lib")
    dest = tmp_path / "dest"
    cmd_copy(str(lib), "   ", str(dest), str(tmp_path / "CLAUDE.md"))
    captured = capsys.readouterr()
    assert "No agents to copy" in captured.out


def test_copy_zero_agents_empty_string(tmp_path, capsys):
    lib = make_library(tmp_path / "lib")
    dest = tmp_path / "dest"
    cmd_copy(str(lib), "", str(dest), str(tmp_path / "CLAUDE.md"))
    captured = capsys.readouterr()
    assert "No agents to copy" in captured.out


# --- update_claude_md ---

def make_agent_in_dest(dest: Path, filename: str, name: str, description: str):
    dest.mkdir(parents=True, exist_ok=True)
    (dest / filename).write_text(
        f"---\nname: {name}\ndescription: {description}\n---\nContent",
        encoding="utf-8",
    )


def test_update_claude_md_creates_section_when_missing(tmp_path):
    dest = tmp_path / "agents"
    make_agent_in_dest(dest, "backend-developer.md", "backend-developer", "Backend specialist")
    claude_md = tmp_path / "CLAUDE.md"
    claude_md.write_text("# My Project\n\nSome content.\n", encoding="utf-8")
    update_claude_md(claude_md, ["backend-developer.md"], dest)
    content = claude_md.read_text(encoding="utf-8")
    assert "## Project Team" in content
    assert "backend-developer" in content
    assert "Backend specialist" in content


def test_update_claude_md_adds_note_about_manual_agents(tmp_path):
    dest = tmp_path / "agents"
    make_agent_in_dest(dest, "backend-developer.md", "backend-developer", "Backend")
    claude_md = tmp_path / "CLAUDE.md"
    update_claude_md(claude_md, ["backend-developer.md"], dest)
    content = claude_md.read_text(encoding="utf-8")
    assert "manually" in content.lower()


def test_update_claude_md_creates_claude_md_if_missing(tmp_path):
    dest = tmp_path / "agents"
    make_agent_in_dest(dest, "backend-developer.md", "backend-developer", "Backend")
    claude_md = tmp_path / "CLAUDE.md"
    assert not claude_md.exists()
    update_claude_md(claude_md, ["backend-developer.md"], dest)
    assert claude_md.exists()
    assert "## Project Team" in claude_md.read_text(encoding="utf-8")


def test_update_claude_md_merges_without_duplicates(tmp_path):
    dest = tmp_path / "agents"
    make_agent_in_dest(dest, "backend-developer.md", "backend-developer", "Backend")
    make_agent_in_dest(dest, "api-designer.md", "api-designer", "API Designer")
    claude_md = tmp_path / "CLAUDE.md"
    # First call — adds backend-developer
    update_claude_md(claude_md, ["backend-developer.md"], dest)
    # Second call — adds api-designer, must not duplicate backend-developer
    update_claude_md(claude_md, ["api-designer.md"], dest)
    content = claude_md.read_text(encoding="utf-8")
    assert content.count("backend-developer") == 1
    assert content.count("api-designer") == 1


def test_update_claude_md_skips_agents_with_invalid_frontmatter(tmp_path):
    dest = tmp_path / "agents"
    dest.mkdir()
    (dest / "bad-agent.md").write_text("No frontmatter", encoding="utf-8")
    claude_md = tmp_path / "CLAUDE.md"
    update_claude_md(claude_md, ["bad-agent.md"], dest)
    # CLAUDE.md should not be created or should not contain Project Team
    # (no valid agents to add)
    if claude_md.exists():
        content = claude_md.read_text(encoding="utf-8")
        assert "## Project Team" not in content
```

- [ ] **Step 2: Run to confirm failures**

```bash
cd skills/init-agents/scripts
pytest tests/test_copy.py -v
```

Expected: all fail (function is a stub)

- [ ] **Step 3: Implement `update_claude_md` and updated `cmd_copy`**

Replace the `cmd_copy` stub and add `update_claude_md` in `init_agents.py`:

```python
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
    section_pattern = re.compile(r"## Project Team\n(.*?)(?=\n## |\Z)", re.DOTALL)
    match = section_pattern.search(claude_content)
    if match:
        for line in match.group(1).splitlines():
            m = re.match(r"^- \*\*(.+?)\*\* \(`(.+?)`\)", line)
            if m:
                existing_entries[m.group(2)] = line  # keyed by filename

    # Merge: existing + new (new overwrites existing on same filename)
    for filename, fm in new_agents.items():
        existing_entries[filename] = (
            f"- **{fm['name']}** (`{filename}`) — {fm['description']}"
        )

    agent_lines = "\n".join(
        existing_entries[k] for k in sorted(existing_entries)
    )
    new_section = (
        f"{section_header}\n\n"
        f"The following agents are active in this project:\n\n"
        f"{agent_lines}\n\n"
        f"{note}\n"
    )

    if match:
        claude_content = section_pattern.sub(new_section, claude_content)
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
```

> **Note:** `[OK]` and `[SKIP]` are used instead of `✓` and `⚠` for cross-platform compatibility. `cmd_copy` now accepts a `claude_md` parameter (defaults to `"CLAUDE.md"` in CWD) and calls `update_claude_md` only when at least one agent was newly copied.

Also update `main()` to pass `--claude-md` arg to `cmd_copy`:

```python
    copy_p.add_argument("--claude-md", default="CLAUDE.md", help="Path to project CLAUDE.md")
```

And in the `elif args.command == "copy":` branch:

```python
    elif args.command == "copy":
        cmd_copy(library_path, args.agents, args.dest, args.claude_md)
```

- [ ] **Step 4: Run all tests**

```bash
cd skills/init-agents/scripts
pytest tests/ -v
```

Expected: all tests pass

- [ ] **Step 5: Commit** (run from project root)

```bash
git add skills/init-agents/scripts/init_agents.py skills/init-agents/scripts/tests/test_copy.py
git commit -m "feat: implement copy subcommand"
```

---

### Task 5: Skill File

**Files:**
- Create: `skills/init-agents/init-agents.md`

- [ ] **Step 1: Create the skill file**

Create `skills/init-agents/init-agents.md`:

```markdown
---
name: init-agents
description: Bootstrap agents into this project from a central agent library. Recommends and copies the right agents based on project context (CLAUDE.md or spec docs). Run at project start or any time during development.
---

# Init-Agents Skill

You are setting up project-specific agents. Follow these steps exactly in order.

## Step 1: Detect Python

Run:
```bash
python --version
```
If that fails, run `python3 --version`.

If neither works, stop and tell the user:
> "Python not found. Install from https://www.python.org before running this skill."

Use whichever command worked (`python` or `python3`) for all subsequent steps.

## Step 2: Resolve Library Path

Read the `.env` file in the current project root. Look for `AGENTS_LIBRARY_PATH`.

If found, store the value as `LIBRARY_PATH` for use in later steps.

If not found, ask the user:
> "Enter the path to your agent library:"

Store their answer as `LIBRARY_PATH`. Do not write it to any file. Path validation happens in Step 4 when the script runs.

## Step 3: Verify Script Exists

Check that `skills/init-agents/scripts/init_agents.py` exists relative to CWD.

If not found, stop and tell the user:
> "Script not found at skills/init-agents/scripts/init_agents.py. Is init-agents installed in this project?"

## Step 4: Scan Agent Library

Run:
```bash
python skills/init-agents/scripts/init_agents.py scan --path <LIBRARY_PATH>
```

Parse the JSON output. Each entry contains: `category`, `name`, `file`, `path`, `description`.
The `path` field (e.g. `01-core-development/backend-developer.md`) is used in the copy step.

## Step 5: Read Project Context

Look for `CLAUDE.md` in the current project root. Read it if present.

If `CLAUDE.md` is absent, look for files in `docs/superpowers/specs/`:
- Files with a `YYYY-MM-DD` prefix: sort by that date, descending.
- Files without a date prefix: sort by filesystem modification time, descending.
- Dated files take priority over undated files regardless of mtime.
- If multiple files share the same date, use filesystem mtime to break the tie.
- Read the single most recent file found by this ordering.

If neither `CLAUDE.md` nor any spec file exists, tell the user:
> "No project brief found. Recommendations may be generic. Consider creating a CLAUDE.md before running this skill."

Continue regardless — do not stop.

## Step 6: Recommend Agents

Using the project context and the full list of agents from the scan, recommend the most relevant agents.

Output a Markdown table:

| Agent | Category | Reason |
|---|---|---|
| backend-developer.md | 01-core-development | Project uses Node.js API |

Include only agents that clearly fit the project. 5–10 agents is typical; fewer is fine for narrow projects. Do not recommend agents speculatively.

## Step 7: Wait for Approval

Display the recommendation table, then prompt the user:

> "Type YES to copy all recommended agents, enter comma-separated agent names to select a subset (e.g. backend-developer.md, api-designer.md), or NO to cancel:"

Handle the response:

- `YES` (case-insensitive) → use the full recommended list
- Comma-separated filenames → validate each against scan results (match on the `file` field).
  - Unknown names: print `"Unknown agent: <name> — skipped."` and skip them.
  - If all names are unknown: print `"No valid agents. Exiting."` and stop.
- `NO` or empty input → print `"Cancelled. No files copied."` and stop.
- Any other input → print `"Unrecognized input. Please try again:"` and re-prompt once.
  - On the second attempt: empty = cancel (`"Cancelled. No files copied."`). Any other unrecognized input → `"Unrecognized input. Exiting."` and stop.

## Step 8: Copy Agents and Update CLAUDE.md

Build a comma-separated list of `path` values for the approved agents
(e.g. `01-core-development/backend-developer.md,02-language-specialists/python-expert.md`).

Run:
```bash
python skills/init-agents/scripts/init_agents.py copy \
  --agents "<comma-separated paths>" \
  --path <LIBRARY_PATH> \
  --dest .claude/agents \
  --claude-md CLAUDE.md
```

The script will:
1. Copy newly approved agents into `.claude/agents/` (skipping existing ones)
2. Automatically update `CLAUDE.md` with a `## Project Team` section listing every copied agent (name, filename, description)
3. Add a note in that section reminding the team to manually update it if agents are added outside this skill

Report the script output to the user exactly as printed.
```

- [ ] **Step 2: Verify the skill file**

Read `skills/init-agents/init-agents.md` and confirm each of the following:
- All 8 steps are present in order
- Step 3 checks for the script before Step 4 runs it
- Step 2 notes that path validation happens via the script in Step 4
- Approval handling in Step 7 covers: YES, subset, NO/empty, unrecognized (re-prompt once)
- Step 8 uses `path` field (not `file`) in the `--agents` argument

- [ ] **Step 3: Commit** (run from project root)

```bash
git add skills/init-agents/init-agents.md
git commit -m "feat: add init-agents skill file"
```

---

### Task 6: README and Final Verification

**Files:**
- Create: `README.md`

- [ ] **Step 1: Create `README.md`** (in project root)

```markdown
# init-agents

A Claude Code skill that bootstraps the right agent files into your project from a central agent library.

## What it does

1. Scans your agent library for all available agents
2. Reads your project brief (`CLAUDE.md` or `docs/superpowers/specs/*.md`)
3. Recommends agents that fit your project
4. Copies approved agents into `.claude/agents/` (never overwrites existing ones)

## Installation

Copy the `skills/init-agents/` folder into your project:

```bash
# Per-project
cp -r skills/init-agents/ /your/project/.claude/skills/

# Global (all projects)
cp -r skills/init-agents/ ~/.claude/skills/
```

## Setup

Create a `.env` file in your project root:

```
AGENTS_LIBRARY_PATH=/path/to/your/agent/library
```

See `.env.example` for reference. The path must point to the root of your agent library — the folder that contains a `categories/` subdirectory.

## Usage

In Claude Code, run:

```
/init-agents
```

## Requirements

- Python 3.8+
- A local agent library with a `categories/` folder structure
  (e.g. [awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents))

## Running tests

```bash
cd skills/init-agents/scripts
pytest tests/ -v
```
```

- [ ] **Step 2: Run the full test suite one final time** (from scripts directory)

```bash
cd skills/init-agents/scripts
pytest tests/ -v
```

Expected: all tests pass, zero errors, zero warnings

- [ ] **Step 3: Final commit** (run from project root)

```bash
git add README.md
git commit -m "docs: add README"
```
