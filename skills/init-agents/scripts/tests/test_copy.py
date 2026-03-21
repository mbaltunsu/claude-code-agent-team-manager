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
