#!/usr/bin/env python3
"""init_team.py — CLI script for the Claude Code init-team skill."""

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

DEFAULT_REPO = "https://github.com/VoltAgent/awesome-claude-code-subagents.git"
DEFAULT_PLUGIN_REPO = "https://github.com/mbaltunsu/claude-code-agent-team-manager.git"

TEAM_MANAGEMENT_DIR = Path.home() / ".claude" / "team-management"
DEFAULT_AGENTS_DIR = TEAM_MANAGEMENT_DIR / "agents"
SOURCES_REGISTRY = TEAM_MANAGEMENT_DIR / "sources.json"
DEFAULT_DEST = str(DEFAULT_AGENTS_DIR)

DEFAULT_SOURCE_ENTRY = {
    "id": "voltagent",
    "name": "awesome-claude-code-subagents",
    "repo": DEFAULT_REPO,
    "homepage": "https://github.com/VoltAgent/awesome-claude-code-subagents",
    "author": "VoltAgent",
    "description": "Community-curated collection of Claude Code subagents",
    "is_default": True,
}


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
    """Resolve library path: CLI arg > env var > central agents dir > error."""
    path_str = cli_path or env_path
    if not path_str:
        # Fall back to central agents directory
        if (DEFAULT_AGENTS_DIR / "categories").is_dir():
            return str(DEFAULT_AGENTS_DIR)
        print(
            "Error: No library path provided. "
            "Set AGENTS_LIBRARY_PATH in .env, pass --path, or run 'download' / 'import' first.",
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


def _load_sources() -> list:
    """Load sources registry. Returns default (VoltAgent) if file missing, [] on parse error."""
    if not SOURCES_REGISTRY.exists():
        return [DEFAULT_SOURCE_ENTRY]
    try:
        data = json.loads(SOURCES_REGISTRY.read_text(encoding="utf-8"))
        return data.get("sources", [])
    except (json.JSONDecodeError, Exception) as e:
        print(f"Warning: Could not parse sources registry: {e}", file=sys.stderr)
        return []


def _save_sources(sources: list):
    """Persist sources list to SOURCES_REGISTRY, creating parent dirs as needed."""
    TEAM_MANAGEMENT_DIR.mkdir(parents=True, exist_ok=True)
    SOURCES_REGISTRY.write_text(json.dumps({"sources": sources}, indent=2), encoding="utf-8")


def cmd_source_list():
    """Print JSON array of all registered sources."""
    sources = _load_sources()
    print(json.dumps(sources, indent=2))


def cmd_source_add(repo: str, name: str, author: str, homepage: str, description: str):
    """Add a new source to the registry."""
    source_id = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    sources = _load_sources()
    if any(s["id"] == source_id for s in sources):
        print(f"Error: Source '{source_id}' already exists.", file=sys.stderr)
        return
    sources.append({
        "id": source_id,
        "name": name,
        "repo": repo,
        "homepage": homepage,
        "author": author,
        "description": description,
        "is_default": False,
    })
    _save_sources(sources)
    print(f"[OK] Source '{source_id}' added.")


def cmd_source_remove(source_id: str):
    """Remove a source from the registry by id."""
    sources = _load_sources()
    matching = [s for s in sources if s["id"] == source_id]
    if not matching:
        print(f"Error: Source '{source_id}' not found.", file=sys.stderr)
        sys.exit(1)
    if matching[0].get("is_default"):
        print(f"Warning: Removing default source '{source_id}'.", file=sys.stderr)
    updated = [s for s in sources if s["id"] != source_id]
    _save_sources(updated)
    print(f"[OK] Source '{source_id}' removed.")


def cmd_import(library_path: str, dest: Optional[str] = None) -> str:
    """Copy agents from a local library into the central agents dir (merge-safe)."""
    dest_str = dest or str(DEFAULT_AGENTS_DIR)
    categories_dir = Path(library_path) / "categories"
    if not categories_dir.is_dir():
        print(f"Error: No 'categories/' directory found in {library_path}.", file=sys.stderr)
        sys.exit(1)

    dest_path = Path(dest_str)
    result = {"imported": [], "skipped": [], "dest": dest_str}

    for category_dir in sorted(categories_dir.iterdir()):
        if not category_dir.is_dir():
            continue
        for agent_file in sorted(category_dir.glob("*.md")):
            if agent_file.name.lower() == "readme.md":
                continue
            rel = f"{category_dir.name}/{agent_file.name}"
            destination = dest_path / "categories" / category_dir.name / agent_file.name
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists():
                print(f"[SKIP] {rel}")
                result["skipped"].append(rel)
            else:
                shutil.copy2(agent_file, destination)
                print(f"[OK] {rel} imported")
                result["imported"].append(rel)

    print(f"\n{len(result['imported'])} agent(s) imported, {len(result['skipped'])} skipped.")
    return json.dumps(result)


def _scan_rules(rules_dir: Optional[Path]) -> list:
    """Return sorted list of rule filenames from rules_dir. Returns [] if dir missing."""
    if rules_dir is None or not rules_dir.is_dir():
        return []
    return sorted(f.name for f in rules_dir.glob("*.md"))


def update_project_files(
    claude_md_path: Path,
    team_md_path: Path,
    copied_files: list,
    dest_dir: Path,
    rules_dir: Optional[Path] = None,
    force: bool = False,
):
    """Write agent info to TEAM.md and update ## Agents and Rules section in CLAUDE.md."""
    new_agents = {}
    for filename in copied_files:
        agent_file = dest_dir / filename
        if not agent_file.exists():
            continue
        content = agent_file.read_text(encoding="utf-8")
        fm = parse_frontmatter(content)
        if fm:
            new_agents[filename] = fm

    if not new_agents and not force:
        return

    note = (
        "> If you add agents manually to `.claude/agents/`, "
        "add them to this file too."
    )

    existing_entries = {}
    if team_md_path.exists():
        team_content = team_md_path.read_text(encoding="utf-8").replace("\r\n", "\n")
        for line in team_content.splitlines():
            m = re.match(r"^- \*\*(.+?)\*\*: (.+)$", line)
            if m:
                existing_entries[m.group(1)] = line

    for filename, fm in new_agents.items():
        agent_name = fm["name"]
        if agent_name in existing_entries:
            print(
                f"Warning: Agent name '{agent_name}' from {filename} conflicts with an existing entry — overwriting.",
                file=sys.stderr,
            )
        existing_entries[agent_name] = f"- **{fm['name']}**: {fm['description']}"

    if existing_entries or new_agents:
        agent_lines = "\n".join(existing_entries[k] for k in sorted(existing_entries))
        team_content = (
            "# Project Team\n\n"
            "The following agents are active in this project:\n\n"
            f"{agent_lines}\n\n"
            f"{note}\n"
        )
        team_md_path.write_text(team_content, encoding="utf-8")
        print(f"Updated TEAM.md — {len(existing_entries)} agent(s) listed.")

    # Build dynamic installed agents list from dest_dir
    installed_agents = []
    if dest_dir.is_dir():
        for agent_file in sorted(dest_dir.glob("*.md")):
            if agent_file.name.lower() == "readme.md":
                continue
            fm = parse_frontmatter(agent_file.read_text(encoding="utf-8"))
            desc = fm["description"] if fm else ""
            installed_agents.append((agent_file.name, desc))

    agents_block = ""
    if installed_agents:
        lines = "\n".join(f"- {name} — {desc}" if desc else f"- {name}" for name, desc in installed_agents)
        agents_block = f"\n**Agents** (`.claude/agents/`):\n{lines}\n"

    # Build dynamic rules list
    rule_files = _scan_rules(rules_dir)
    rules_block = ""
    if rule_files:
        lines = "\n".join(f"- {f}" for f in rule_files)
        rules_block = f"\n**Rules** (`.claude/rules/`):\n{lines}\n"

    installed_section = ""
    if agents_block or rules_block:
        installed_section = f"\n### Installed Agents and Rules\n{agents_block}{rules_block}"

    pointer_section = (
        "## Agents and Rules\n\n"
        f"See [{team_md_path.name}]({team_md_path.name}) for the full agent roster.\n\n"
        "- Use `.claude/rules/x.md` files for project-specific rules (architecture, tech stack, git, context).\n"
        "- Add project-specific details to these files. Run `/team:init-project` to bootstrap them.\n"
        f"{installed_section}\n"
        "### Team Collaboration Guidelines\n\n"
        "- Always try to use TEAM agents for different tasks — distribute work efficiently\n"
        "- Use subagents mode for parallelizable work (e.g., tests + implementation in parallel)\n"
        "- Use worktrees and different branches for better teamwork — avoid conflicts\n"
        "- Every agent should utilize git: commit frequently, use descriptive branch names\n"
        "- Use design/architecture agents early in development before implementation agents\n"
        "- When a new agent or rule is added manually, update TEAM.md and this section\n"
        "- Run `/team:init-project` to bootstrap rules for a new project\n"
        "- Run `/team:add-agent` to add a single agent by name or capability\n"
        "- Run `/team:init-team` to set up a full agent roster\n"
    )
    section_pattern = re.compile(r"^## Agents and Rules\n(.*?)(?=^## |\Z)", re.DOTALL | re.MULTILINE)

    if claude_md_path.exists():
        claude_content = claude_md_path.read_text(encoding="utf-8").replace("\r\n", "\n")
    else:
        claude_content = ""

    match = section_pattern.search(claude_content)
    if match:
        claude_content = section_pattern.sub(lambda _: pointer_section, claude_content)
    else:
        claude_content = claude_content.rstrip("\n") + "\n\n" + pointer_section + "\n"

    claude_md_path.write_text(claude_content, encoding="utf-8")
    print(f"Updated CLAUDE.md — Agents and Rules section updated.")


def remove_from_team_md(team_md_path: Path, agent_name: str) -> int:
    """Remove an agent entry from TEAM.md. Returns count of remaining agents."""
    if not team_md_path.exists():
        return 0
    content = team_md_path.read_text(encoding="utf-8").replace("\r\n", "\n")
    remaining = []
    for line in content.splitlines():
        m = re.match(r"^- \*\*(.+?)\*\*: (.+)$", line)
        if m and m.group(1) == agent_name:
            continue
        remaining.append(line)
    team_md_path.write_text("\n".join(remaining) + "\n", encoding="utf-8")
    count = sum(1 for l in remaining if re.match(r"^- \*\*(.+?)\*\*:", l))
    return count


def remove_from_claude_md(claude_md_path: Path):
    """Remove the ## Agents and Rules section from CLAUDE.md."""
    if not claude_md_path.exists():
        return
    content = claude_md_path.read_text(encoding="utf-8").replace("\r\n", "\n")
    section_pattern = re.compile(r"\n*^## Agents and Rules\n(.*?)(?=^## |\Z)", re.DOTALL | re.MULTILINE)
    new_content = section_pattern.sub("", content).rstrip("\n") + "\n"
    claude_md_path.write_text(new_content, encoding="utf-8")


def cmd_remove(agent_filename: str, dest: str, team_md: str = "TEAM.md", claude_md: str = "CLAUDE.md"):
    """Remove an agent from the project."""
    agent_path = Path(dest) / agent_filename
    if not agent_path.exists():
        print(f"Error: Agent '{agent_filename}' not found in {dest}.", file=sys.stderr)
        sys.exit(1)

    content = agent_path.read_text(encoding="utf-8")
    fm = parse_frontmatter(content)
    agent_name = fm["name"] if fm else agent_filename.replace(".md", "")

    agent_path.unlink()
    print(f"[OK] {agent_filename} removed")

    team_md_path = Path(team_md)
    remaining = remove_from_team_md(team_md_path, agent_name)

    if remaining == 0:
        remove_from_claude_md(Path(claude_md))


def cmd_add(library_path: str, agent_filename: str, dest: str, claude_md: str = "CLAUDE.md", team_md: str = "TEAM.md"):
    """Add a single agent from the library to the project."""
    categories_dir = Path(library_path) / "categories"
    source = None
    for category_dir in sorted(categories_dir.iterdir()):
        if not category_dir.is_dir():
            continue
        candidate = category_dir / agent_filename
        if candidate.exists():
            source = candidate
            break

    if source is None:
        print(f"Error: Agent '{agent_filename}' not found in library.", file=sys.stderr)
        sys.exit(1)

    dest_dir = Path(dest)
    dest_dir.mkdir(parents=True, exist_ok=True)
    destination = dest_dir / agent_filename

    if destination.exists():
        print(f"[SKIP] {agent_filename} already exists")
        return

    shutil.copy2(source, destination)
    print(f"[OK] {agent_filename} copied")
    update_project_files(Path(claude_md), Path(team_md), [agent_filename], dest_dir, rules_dir=Path(".claude/rules"))


def cmd_list(dest: str):
    """List installed agents in dest directory, print JSON array to stdout."""
    dest_dir = Path(dest)
    agents = []
    if dest_dir.is_dir():
        for agent_file in sorted(dest_dir.glob("*.md")):
            if agent_file.name.lower() == "readme.md":
                continue
            content = agent_file.read_text(encoding="utf-8")
            fm = parse_frontmatter(content)
            if fm:
                agents.append({
                    "file": agent_file.name,
                    "name": fm["name"],
                    "description": fm["description"],
                })
            else:
                agents.append({
                    "file": agent_file.name,
                    "name": agent_file.name,
                    "description": "",
                })
    print(json.dumps(agents, indent=2))


def cmd_copy(library_path: str, agents_arg: str, dest: str, claude_md: str = "CLAUDE.md", team_md: str = "TEAM.md"):
    """Copy approved agents to dest directory. Skips existing. Updates TEAM.md and CLAUDE.md."""
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
        update_project_files(Path(claude_md), Path(team_md), copied, dest_dir, rules_dir=Path(".claude/rules"))


def _compare_versions(a: str, b: str) -> int:
    """Compare two semver strings. Returns -1 if a < b, 0 if equal, 1 if a > b."""
    parts_a = [int(x) for x in a.split(".")]
    parts_b = [int(x) for x in b.split(".")]
    for va, vb in zip(parts_a, parts_b):
        if va < vb:
            return -1
        if va > vb:
            return 1
    return 0


def _get_local_plugin_root() -> Path:
    """Resolve the plugin root directory from this script's location."""
    return Path(__file__).resolve().parent.parent.parent.parent


def _get_local_plugin_json() -> dict:
    """Read the local plugin.json."""
    plugin_json = _get_local_plugin_root() / ".claude-plugin" / "plugin.json"
    if not plugin_json.exists():
        return {}
    return json.loads(plugin_json.read_text(encoding="utf-8"))


def cmd_update(repo: Optional[str] = None) -> str:
    """Check for plugin updates and apply if newer version available.

    Returns JSON string with results.
    """
    repo = repo or DEFAULT_PLUGIN_REPO

    if shutil.which("git") is None:
        return json.dumps({"error": "git is required but not found on PATH"})

    tmp_dir = tempfile.mkdtemp()

    try:
        clone_result = subprocess.run(
            ["git", "clone", "--filter=blob:none", "--no-checkout", "--depth=1", repo, tmp_dir],
            capture_output=True,
            text=True,
        )
        if clone_result.returncode != 0:
            return json.dumps({"error": f"Failed to clone repository: {clone_result.stderr.strip()}"})

        subprocess.run(
            ["git", "-C", tmp_dir, "sparse-checkout", "init", "--cone"],
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "-C", tmp_dir, "sparse-checkout", "set", "skills/init-team", ".claude-plugin"],
            capture_output=True,
            text=True,
        )
        checkout_result = subprocess.run(
            ["git", "-C", tmp_dir, "checkout"],
            capture_output=True,
            text=True,
        )
        if checkout_result.returncode != 0:
            return json.dumps({"error": f"Failed to checkout: {checkout_result.stderr.strip()}"})

        remote_plugin_json = Path(tmp_dir) / ".claude-plugin" / "plugin.json"
        if not remote_plugin_json.exists():
            return json.dumps({"error": "Remote plugin.json not found"})

        remote_meta = json.loads(remote_plugin_json.read_text(encoding="utf-8"))
        remote_version = remote_meta.get("version", "0.0.0")

        local_meta = _get_local_plugin_json()
        local_version = local_meta.get("version", "0.0.0")

        if _compare_versions(local_version, remote_version) >= 0:
            return json.dumps({
                "updated": False,
                "current_version": local_version,
                "latest_version": remote_version,
            })

        local_root = _get_local_plugin_root()
        files_updated = []

        for src_file in Path(tmp_dir).rglob("*"):
            if not src_file.is_file():
                continue
            if ".git" in src_file.parts:
                continue
            rel = src_file.relative_to(tmp_dir)
            dest_file = local_root / rel
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dest_file)
            files_updated.append(str(rel))

        return json.dumps({
            "updated": True,
            "old_version": local_version,
            "new_version": remote_version,
            "files_updated": files_updated,
        })

    except Exception as e:
        return json.dumps({"error": f"Update failed: {str(e)}"})

    finally:
        try:
            shutil.rmtree(tmp_dir)
        except Exception:
            pass


def cmd_download(dest: Optional[str] = None, repo: Optional[str] = None, source_id: Optional[str] = None) -> str:
    """Download agents from a GitHub repo using git sparse-checkout.

    Returns JSON string with results. Uses subprocess to call git CLI
    (stdlib only — no third-party dependencies).
    """
    dest = dest or DEFAULT_DEST
    dest_path = Path(dest)

    # Resolve repo: --source takes precedence over --repo
    if source_id is not None:
        sources = _load_sources()
        match = next((s for s in sources if s["id"] == source_id), None)
        if match is None:
            return json.dumps({"error": f"Source '{source_id}' not found in registry."})
        repo = match["repo"]
    else:
        repo = repo or DEFAULT_REPO

    if shutil.which("git") is None:
        return json.dumps({"error": "git is required but not found on PATH"})

    tmp_dir = tempfile.mkdtemp()
    warning = None

    try:
        clone_result = subprocess.run(
            ["git", "clone", "--filter=blob:none", "--no-checkout", "--depth=1", repo, tmp_dir],
            capture_output=True,
            text=True,
        )
        if clone_result.returncode != 0:
            return json.dumps({"error": f"Failed to clone repository: {clone_result.stderr.strip()}"})

        subprocess.run(
            ["git", "-C", tmp_dir, "sparse-checkout", "init", "--cone"],
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "-C", tmp_dir, "sparse-checkout", "set", "categories"],
            capture_output=True,
            text=True,
        )
        checkout_result = subprocess.run(
            ["git", "-C", tmp_dir, "checkout"],
            capture_output=True,
            text=True,
        )
        if checkout_result.returncode != 0:
            return json.dumps({"error": f"Failed to checkout: {checkout_result.stderr.strip()}"})

        src_categories = Path(tmp_dir) / "categories"
        dest_categories = dest_path / "categories"
        dest_categories.mkdir(parents=True, exist_ok=True)

        downloaded = []
        skipped = []

        if src_categories.is_dir():
            for category_dir in sorted(src_categories.iterdir()):
                if not category_dir.is_dir():
                    continue
                dest_cat = dest_categories / category_dir.name
                dest_cat.mkdir(parents=True, exist_ok=True)

                for agent_file in sorted(category_dir.glob("*.md")):
                    rel_path = f"{category_dir.name}/{agent_file.name}"
                    dest_file = dest_cat / agent_file.name

                    if dest_file.exists():
                        skipped.append(rel_path)
                    else:
                        shutil.copy2(agent_file, dest_file)
                        downloaded.append(rel_path)

        result = {
            "downloaded": downloaded,
            "skipped": skipped,
            "dest": str(dest_path),
        }

    except Exception as e:
        return json.dumps({"error": f"Download failed: {str(e)}"})

    finally:
        try:
            shutil.rmtree(tmp_dir)
        except Exception:
            warning = f"Could not clean up temporary directory: {tmp_dir}"

    if warning:
        result["warning"] = warning

    return json.dumps(result)


def cmd_init_project(rules_dest: str, agents_dest: str, git_rules_src: str) -> str:
    """Create .claude/rules and .claude/agents dirs; copy git-rules.md if not present."""
    result = {"dirs_created": [], "files_copied": [], "files_skipped": []}

    agents_path = Path(agents_dest)
    if not agents_path.exists():
        agents_path.mkdir(parents=True, exist_ok=True)
        result["dirs_created"].append(str(agents_path))
        print(f"[OK] {agents_dest} created")
    else:
        print(f"[SKIP] {agents_dest} already exists")

    rules_path = Path(rules_dest)
    if not rules_path.exists():
        rules_path.mkdir(parents=True, exist_ok=True)
        result["dirs_created"].append(str(rules_path))
        print(f"[OK] {rules_dest} created")
    else:
        print(f"[SKIP] {rules_dest} already exists")

    git_rules_dest = rules_path / "git-rules.md"
    git_rules_source = Path(git_rules_src)

    if not git_rules_source.exists():
        print(f"Warning: git-rules source not found: {git_rules_src}", file=sys.stderr)
    elif git_rules_dest.exists():
        print(f"[SKIP] git-rules.md already exists")
        result["files_skipped"].append("git-rules.md")
    else:
        shutil.copy2(git_rules_source, git_rules_dest)
        print(f"[OK] git-rules.md created")
        result["files_copied"].append("git-rules.md")

    print(json.dumps(result))
    return json.dumps(result)


def cmd_update_docs(claude_md: str, team_md: str, agents_dest: str, rules_dest: str):
    """Refresh the ## Agents and Rules section in CLAUDE.md."""
    update_project_files(
        Path(claude_md),
        Path(team_md),
        [],
        Path(agents_dest),
        rules_dir=Path(rules_dest),
        force=True,
    )


def main():
    _ensure_utf8_stdout()
    parser = argparse.ArgumentParser(description="init-team script")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_p = subparsers.add_parser("scan")
    scan_p.add_argument("--path", help="Path to agent library")

    copy_p = subparsers.add_parser("copy")
    copy_p.add_argument("--path", help="Path to agent library")
    copy_p.add_argument("--agents", required=True, help="Comma-separated category/file paths")
    copy_p.add_argument("--dest", default=".claude/agents", help="Destination directory")
    copy_p.add_argument("--claude-md", default="CLAUDE.md", help="Path to project CLAUDE.md")
    copy_p.add_argument("--team-md", default="TEAM.md", help="Path to project TEAM.md")

    update_p = subparsers.add_parser("update")
    update_p.add_argument("--repo", default=DEFAULT_PLUGIN_REPO, help="Plugin repository URL")

    remove_p = subparsers.add_parser("remove")
    remove_p.add_argument("--agent", required=True, help="Agent filename to remove")
    remove_p.add_argument("--dest", default=".claude/agents", help="Directory containing installed agents")
    remove_p.add_argument("--team-md", default="TEAM.md", help="Path to project TEAM.md")
    remove_p.add_argument("--claude-md", default="CLAUDE.md", help="Path to project CLAUDE.md")

    add_p = subparsers.add_parser("add")
    add_p.add_argument("--agent", required=True, help="Agent filename to add")
    add_p.add_argument("--path", help="Path to agent library")
    add_p.add_argument("--dest", default=".claude/agents", help="Destination directory")
    add_p.add_argument("--claude-md", default="CLAUDE.md", help="Path to project CLAUDE.md")
    add_p.add_argument("--team-md", default="TEAM.md", help="Path to project TEAM.md")

    list_p = subparsers.add_parser("list")
    list_p.add_argument("--dest", default=".claude/agents", help="Directory containing installed agents")

    download_p = subparsers.add_parser("download")
    download_p.add_argument("--dest", default=DEFAULT_DEST, help="Destination directory for downloaded agents")
    download_p.add_argument("--repo", default=None, help="Git repository URL to download from")
    download_p.add_argument("--source", default=None, dest="source_id", help="Source ID from registry")

    source_list_p = subparsers.add_parser("source-list")  # noqa: F841

    source_add_p = subparsers.add_parser("source-add")
    source_add_p.add_argument("--repo", required=True)
    source_add_p.add_argument("--name", required=True)
    source_add_p.add_argument("--author", default="")
    source_add_p.add_argument("--homepage", default="")
    source_add_p.add_argument("--description", default="")

    source_remove_p = subparsers.add_parser("source-remove")
    source_remove_p.add_argument("--id", required=True, dest="source_id")

    import_p = subparsers.add_parser("import")
    import_p.add_argument("--path", required=True, help="Local library path to import from")
    import_p.add_argument("--dest", default=str(DEFAULT_AGENTS_DIR))

    init_project_p = subparsers.add_parser("init-project")
    init_project_p.add_argument("--rules-dest", default=".claude/rules")
    init_project_p.add_argument("--agents-dest", default=".claude/agents")
    init_project_p.add_argument("--git-rules-src", required=True)

    update_docs_p = subparsers.add_parser("update-docs")
    update_docs_p.add_argument("--claude-md", default="CLAUDE.md")
    update_docs_p.add_argument("--team-md", default="TEAM.md")
    update_docs_p.add_argument("--agents-dest", default=".claude/agents")
    update_docs_p.add_argument("--rules-dest", default=".claude/rules")

    args = parser.parse_args()

    if args.command == "init-project":
        cmd_init_project(args.rules_dest, args.agents_dest, args.git_rules_src)
        return

    if args.command == "update-docs":
        cmd_update_docs(args.claude_md, args.team_md, args.agents_dest, args.rules_dest)
        return

    if args.command == "list":
        cmd_list(dest=args.dest)
        return

    if args.command == "remove":
        cmd_remove(args.agent, args.dest, args.team_md, args.claude_md)
        return

    if args.command == "update":
        result = cmd_update(repo=args.repo)
        print(result)
        output = json.loads(result)
        if "error" in output:
            sys.exit(1)
        return

    if args.command == "source-list":
        cmd_source_list()
        return

    if args.command == "source-add":
        cmd_source_add(args.repo, args.name, args.author, args.homepage, args.description)
        return

    if args.command == "source-remove":
        cmd_source_remove(args.source_id)
        return

    if args.command == "import":
        result = cmd_import(args.path, args.dest)
        print(result)
        output = json.loads(result)
        if "error" in output:
            sys.exit(1)
        return

    if args.command == "download":
        result = cmd_download(dest=args.dest, repo=args.repo, source_id=args.source_id)
        print(result)
        output = json.loads(result)
        if "error" in output:
            sys.exit(1)
        return

    env = load_env(Path.cwd())
    library_path = resolve_library_path(
        cli_path=args.path,
        env_path=env.get("AGENTS_LIBRARY_PATH"),
    )

    if args.command == "scan":
        cmd_scan(library_path)
    elif args.command == "copy":
        cmd_copy(library_path, args.agents, args.dest, args.claude_md, args.team_md)
    elif args.command == "add":
        cmd_add(library_path, args.agent, args.dest, args.claude_md, args.team_md)


if __name__ == "__main__":
    main()
