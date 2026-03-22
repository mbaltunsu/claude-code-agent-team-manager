import pytest
from pathlib import Path
from init_team import cmd_copy, update_project_files


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
    cmd_copy(str(lib), "01-core-development/backend-developer.md", str(dest), str(tmp_path / "CLAUDE.md"), str(tmp_path / "TEAM.md"))
    assert (dest / "backend-developer.md").exists()
    captured = capsys.readouterr()
    assert "[OK] backend-developer.md copied" in captured.out


def test_copy_creates_dest_if_missing(tmp_path):
    lib = make_library(tmp_path / "lib")
    dest = tmp_path / "new_dest"
    assert not dest.exists()
    cmd_copy(str(lib), "01-core-development/backend-developer.md", str(dest), str(tmp_path / "CLAUDE.md"), str(tmp_path / "TEAM.md"))
    assert dest.exists()


def test_copy_skips_existing_and_preserves_content(tmp_path, capsys):
    lib = make_library(tmp_path / "lib")
    dest = tmp_path / "dest"
    dest.mkdir()
    (dest / "backend-developer.md").write_text("custom content", encoding="utf-8")
    cmd_copy(str(lib), "01-core-development/backend-developer.md", str(dest), str(tmp_path / "CLAUDE.md"), str(tmp_path / "TEAM.md"))
    assert (dest / "backend-developer.md").read_text(encoding="utf-8") == "custom content"
    captured = capsys.readouterr()
    assert "[SKIP]" in captured.out


def test_copy_summary_counts_correctly(tmp_path, capsys):
    lib = make_library(tmp_path / "lib")
    dest = tmp_path / "dest"
    dest.mkdir()
    (dest / "backend-developer.md").write_text("custom", encoding="utf-8")
    cmd_copy(str(lib), "01-core-development/backend-developer.md", str(dest), str(tmp_path / "CLAUDE.md"), str(tmp_path / "TEAM.md"))
    captured = capsys.readouterr()
    assert "0 agent(s) copied, 1 skipped" in captured.out


def test_copy_lists_skipped_names_in_summary(tmp_path, capsys):
    lib = make_library(tmp_path / "lib")
    dest = tmp_path / "dest"
    dest.mkdir()
    (dest / "backend-developer.md").write_text("custom", encoding="utf-8")
    cmd_copy(str(lib), "01-core-development/backend-developer.md", str(dest), str(tmp_path / "CLAUDE.md"), str(tmp_path / "TEAM.md"))
    captured = capsys.readouterr()
    assert "Skipped: backend-developer.md" in captured.out


def test_copy_zero_agents_prints_message(tmp_path, capsys):
    lib = make_library(tmp_path / "lib")
    dest = tmp_path / "dest"
    cmd_copy(str(lib), "   ", str(dest), str(tmp_path / "CLAUDE.md"), str(tmp_path / "TEAM.md"))
    captured = capsys.readouterr()
    assert "No agents to copy" in captured.out


def test_copy_zero_agents_empty_string(tmp_path, capsys):
    lib = make_library(tmp_path / "lib")
    dest = tmp_path / "dest"
    cmd_copy(str(lib), "", str(dest), str(tmp_path / "CLAUDE.md"), str(tmp_path / "TEAM.md"))
    captured = capsys.readouterr()
    assert "No agents to copy" in captured.out


# --- update_project_files ---

def make_agent_in_dest(dest: Path, filename: str, name: str, description: str):
    dest.mkdir(parents=True, exist_ok=True)
    (dest / filename).write_text(
        f"---\nname: {name}\ndescription: {description}\n---\nContent",
        encoding="utf-8",
    )


def test_update_creates_team_md(tmp_path):
    dest = tmp_path / "agents"
    make_agent_in_dest(dest, "backend-developer.md", "backend-developer", "Backend specialist")
    claude_md = tmp_path / "CLAUDE.md"
    team_md = tmp_path / "TEAM.md"
    update_project_files(claude_md, team_md, ["backend-developer.md"], dest)
    assert team_md.exists()
    content = team_md.read_text(encoding="utf-8")
    assert "# Project Team" in content
    assert "backend-developer" in content
    assert "Backend specialist" in content


def test_update_team_md_has_manual_agent_note(tmp_path):
    dest = tmp_path / "agents"
    make_agent_in_dest(dest, "backend-developer.md", "backend-developer", "Backend")
    team_md = tmp_path / "TEAM.md"
    update_project_files(tmp_path / "CLAUDE.md", team_md, ["backend-developer.md"], dest)
    content = team_md.read_text(encoding="utf-8")
    assert "manually" in content.lower()


def test_update_claude_md_gets_pointer_to_team_md(tmp_path):
    dest = tmp_path / "agents"
    make_agent_in_dest(dest, "backend-developer.md", "backend-developer", "Backend")
    claude_md = tmp_path / "CLAUDE.md"
    claude_md.write_text("# My Project\n\nSome content.\n", encoding="utf-8")
    team_md = tmp_path / "TEAM.md"
    update_project_files(claude_md, team_md, ["backend-developer.md"], dest)
    content = claude_md.read_text(encoding="utf-8")
    assert "## Agents and Rules" in content
    assert "TEAM.md" in content


def test_update_creates_claude_md_if_missing(tmp_path):
    dest = tmp_path / "agents"
    make_agent_in_dest(dest, "backend-developer.md", "backend-developer", "Backend")
    claude_md = tmp_path / "CLAUDE.md"
    team_md = tmp_path / "TEAM.md"
    assert not claude_md.exists()
    update_project_files(claude_md, team_md, ["backend-developer.md"], dest)
    assert claude_md.exists()
    assert "TEAM.md" in claude_md.read_text(encoding="utf-8")


def test_update_merges_team_md_without_duplicates(tmp_path):
    dest = tmp_path / "agents"
    make_agent_in_dest(dest, "backend-developer.md", "backend-developer", "Backend")
    make_agent_in_dest(dest, "api-designer.md", "api-designer", "API Designer")
    claude_md = tmp_path / "CLAUDE.md"
    team_md = tmp_path / "TEAM.md"
    # First call
    update_project_files(claude_md, team_md, ["backend-developer.md"], dest)
    # Second call — must not duplicate backend-developer
    update_project_files(claude_md, team_md, ["api-designer.md"], dest)
    content = team_md.read_text(encoding="utf-8")
    assert content.count("backend-developer") == 1
    assert content.count("api-designer") == 1


def test_update_skips_invalid_frontmatter(tmp_path):
    dest = tmp_path / "agents"
    dest.mkdir()
    (dest / "bad-agent.md").write_text("No frontmatter", encoding="utf-8")
    claude_md = tmp_path / "CLAUDE.md"
    team_md = tmp_path / "TEAM.md"
    update_project_files(claude_md, team_md, ["bad-agent.md"], dest)
    assert not team_md.exists()
    assert not claude_md.exists()


def _setup_update(tmp_path):
    """Helper: set up a valid agent and run update_project_files."""
    dest = tmp_path / "agents"
    dest.mkdir()
    (dest / "python-pro.md").write_text(
        "---\nname: python-pro\ndescription: Python expert\n---\n",
        encoding="utf-8",
    )
    claude_md = tmp_path / "CLAUDE.md"
    team_md = tmp_path / "TEAM.md"
    update_project_files(claude_md, team_md, ["python-pro.md"], dest)
    return claude_md.read_text(encoding="utf-8")


def test_update_claude_md_has_collaboration_guidelines(tmp_path):
    content = _setup_update(tmp_path)
    assert "Team Collaboration Guidelines" in content


def test_update_claude_md_mentions_subagents(tmp_path):
    content = _setup_update(tmp_path)
    assert "subagents" in content


def test_update_claude_md_mentions_worktrees(tmp_path):
    content = _setup_update(tmp_path)
    assert "worktrees" in content


def test_update_collaboration_guidelines_idempotent(tmp_path):
    """Re-running update_project_files should not duplicate guidelines."""
    dest = tmp_path / "agents"
    dest.mkdir()
    (dest / "python-pro.md").write_text(
        "---\nname: python-pro\ndescription: Python expert\n---\n",
        encoding="utf-8",
    )
    claude_md = tmp_path / "CLAUDE.md"
    team_md = tmp_path / "TEAM.md"
    update_project_files(claude_md, team_md, ["python-pro.md"], dest)
    update_project_files(claude_md, team_md, ["python-pro.md"], dest)
    content = claude_md.read_text(encoding="utf-8")
    assert content.count("Team Collaboration Guidelines") == 1
    assert content.count("## Agents and Rules") == 1


def test_update_claude_md_lists_installed_agents(tmp_path):
    dest = tmp_path / "agents"
    make_agent_in_dest(dest, "python-pro.md", "python-pro", "Python expert")
    claude_md = tmp_path / "CLAUDE.md"
    team_md = tmp_path / "TEAM.md"
    update_project_files(claude_md, team_md, ["python-pro.md"], dest)
    content = claude_md.read_text(encoding="utf-8")
    assert "### Installed Agents and Rules" in content
    assert "python-pro.md" in content
    assert "Python expert" in content


def test_update_claude_md_lists_installed_rules(tmp_path):
    dest = tmp_path / "agents"
    make_agent_in_dest(dest, "python-pro.md", "python-pro", "Python expert")
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()
    (rules_dir / "git-rules.md").write_text("# Git Rules\n", encoding="utf-8")
    claude_md = tmp_path / "CLAUDE.md"
    team_md = tmp_path / "TEAM.md"
    update_project_files(claude_md, team_md, ["python-pro.md"], dest, rules_dir=rules_dir)
    content = claude_md.read_text(encoding="utf-8")
    assert "### Installed Agents and Rules" in content
    assert "git-rules.md" in content
