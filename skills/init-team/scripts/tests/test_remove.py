"""Tests for the remove subcommand."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from init_team import cmd_remove


def _write_agent(dest, filename, name, description):
    """Helper: write a minimal agent .md file with frontmatter."""
    content = f"---\nname: {name}\ndescription: {description}\n---\n\n# {name}\n"
    (dest / filename).write_text(content, encoding="utf-8")


def _write_team_md(path, agents):
    """Helper: write TEAM.md with agent entries."""
    lines = ["# Project Team\n", "The following agents are active in this project:\n"]
    for name, desc in agents:
        lines.append(f"- **{name}**: {desc}")
    lines.append("\n> If you add agents manually to `.claude/agents/`, add them to this file too.\n")
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_claude_md_with_team(path):
    """Helper: write CLAUDE.md with an Agents and Rules section."""
    content = (
        "# Project\n\nSome content.\n\n"
        "## Agents and Rules\n\n"
        "See [TEAM.md](TEAM.md) for the list of agents configured for this project.\n"
    )
    path.write_text(content, encoding="utf-8")


def test_remove_deletes_agent_file(tmp_path, capsys):
    dest = tmp_path / "agents"
    dest.mkdir()
    _write_agent(dest, "python-pro.md", "python-pro", "Python expert")
    cmd_remove("python-pro.md", str(dest), str(tmp_path / "TEAM.md"), str(tmp_path / "CLAUDE.md"))
    assert not (dest / "python-pro.md").exists()
    assert "[OK]" in capsys.readouterr().out


def test_remove_updates_team_md(tmp_path):
    dest = tmp_path / "agents"
    dest.mkdir()
    _write_agent(dest, "python-pro.md", "python-pro", "Python expert")
    team_md = tmp_path / "TEAM.md"
    _write_team_md(team_md, [("python-pro", "Python expert"), ("debugger", "Debug things")])
    cmd_remove("python-pro.md", str(dest), str(team_md), str(tmp_path / "CLAUDE.md"))
    content = team_md.read_text(encoding="utf-8")
    assert "python-pro" not in content
    assert "debugger" in content


def test_remove_team_md_keeps_other_agents(tmp_path):
    dest = tmp_path / "agents"
    dest.mkdir()
    _write_agent(dest, "python-pro.md", "python-pro", "Python expert")
    _write_agent(dest, "debugger.md", "debugger", "Debug things")
    team_md = tmp_path / "TEAM.md"
    _write_team_md(team_md, [("python-pro", "Python expert"), ("debugger", "Debug things")])
    cmd_remove("python-pro.md", str(dest), str(team_md), str(tmp_path / "CLAUDE.md"))
    content = team_md.read_text(encoding="utf-8")
    assert "- **debugger**:" in content


def test_remove_error_if_agent_not_found(tmp_path):
    dest = tmp_path / "agents"
    dest.mkdir()
    with pytest.raises(SystemExit) as exc_info:
        cmd_remove("nonexistent.md", str(dest), str(tmp_path / "TEAM.md"), str(tmp_path / "CLAUDE.md"))
    assert exc_info.value.code == 1


def test_remove_handles_missing_team_md(tmp_path, capsys):
    """If TEAM.md does not exist, still remove the agent file."""
    dest = tmp_path / "agents"
    dest.mkdir()
    _write_agent(dest, "python-pro.md", "python-pro", "Python expert")
    cmd_remove("python-pro.md", str(dest), str(tmp_path / "TEAM.md"), str(tmp_path / "CLAUDE.md"))
    assert not (dest / "python-pro.md").exists()


def test_remove_cleans_claude_md_when_no_agents_remain(tmp_path):
    dest = tmp_path / "agents"
    dest.mkdir()
    _write_agent(dest, "python-pro.md", "python-pro", "Python expert")
    team_md = tmp_path / "TEAM.md"
    _write_team_md(team_md, [("python-pro", "Python expert")])
    claude_md = tmp_path / "CLAUDE.md"
    _write_claude_md_with_team(claude_md)
    cmd_remove("python-pro.md", str(dest), str(team_md), str(claude_md))
    content = claude_md.read_text(encoding="utf-8")
    assert "## Agents and Rules" not in content


def test_remove_preserves_claude_md_when_agents_remain(tmp_path):
    dest = tmp_path / "agents"
    dest.mkdir()
    _write_agent(dest, "python-pro.md", "python-pro", "Python expert")
    _write_agent(dest, "debugger.md", "debugger", "Debug things")
    team_md = tmp_path / "TEAM.md"
    _write_team_md(team_md, [("python-pro", "Python expert"), ("debugger", "Debug things")])
    claude_md = tmp_path / "CLAUDE.md"
    _write_claude_md_with_team(claude_md)
    cmd_remove("python-pro.md", str(dest), str(team_md), str(claude_md))
    content = claude_md.read_text(encoding="utf-8")
    assert "## Agents and Rules" in content
