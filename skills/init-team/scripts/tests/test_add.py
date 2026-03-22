"""Tests for the add subcommand."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from init_team import cmd_add


def _make_library(tmp_path):
    """Create a minimal agent library with two agents in different categories."""
    lib = tmp_path / "library"
    cat1 = lib / "categories" / "01-core"
    cat2 = lib / "categories" / "02-lang"
    cat1.mkdir(parents=True)
    cat2.mkdir(parents=True)
    (cat1 / "backend-developer.md").write_text(
        "---\nname: backend-developer\ndescription: Build backend systems\n---\n",
        encoding="utf-8",
    )
    (cat2 / "python-pro.md").write_text(
        "---\nname: python-pro\ndescription: Python expert\n---\n",
        encoding="utf-8",
    )
    return str(lib)


def test_add_copies_agent_from_library(tmp_path):
    lib = _make_library(tmp_path)
    dest = tmp_path / "agents"
    cmd_add(lib, "python-pro.md", str(dest), str(tmp_path / "CLAUDE.md"), str(tmp_path / "TEAM.md"))
    assert (dest / "python-pro.md").exists()


def test_add_creates_dest_if_missing(tmp_path):
    lib = _make_library(tmp_path)
    dest = tmp_path / "deep" / "nested" / "agents"
    cmd_add(lib, "python-pro.md", str(dest), str(tmp_path / "CLAUDE.md"), str(tmp_path / "TEAM.md"))
    assert (dest / "python-pro.md").exists()


def test_add_skips_existing_agent(tmp_path, capsys):
    lib = _make_library(tmp_path)
    dest = tmp_path / "agents"
    dest.mkdir()
    (dest / "python-pro.md").write_text("existing content", encoding="utf-8")
    cmd_add(lib, "python-pro.md", str(dest), str(tmp_path / "CLAUDE.md"), str(tmp_path / "TEAM.md"))
    assert (dest / "python-pro.md").read_text(encoding="utf-8") == "existing content"
    assert "[SKIP]" in capsys.readouterr().out


def test_add_exits_with_error_if_not_found(tmp_path):
    lib = _make_library(tmp_path)
    dest = tmp_path / "agents"
    with pytest.raises(SystemExit) as exc_info:
        cmd_add(lib, "nonexistent.md", str(dest), str(tmp_path / "CLAUDE.md"), str(tmp_path / "TEAM.md"))
    assert exc_info.value.code == 1


def test_add_updates_team_md(tmp_path):
    lib = _make_library(tmp_path)
    dest = tmp_path / "agents"
    team_md = tmp_path / "TEAM.md"
    cmd_add(lib, "python-pro.md", str(dest), str(tmp_path / "CLAUDE.md"), str(team_md))
    content = team_md.read_text(encoding="utf-8")
    assert "python-pro" in content


def test_add_updates_claude_md(tmp_path):
    lib = _make_library(tmp_path)
    dest = tmp_path / "agents"
    claude_md = tmp_path / "CLAUDE.md"
    claude_md.write_text("# Project\n\nSome content.\n", encoding="utf-8")
    cmd_add(lib, "python-pro.md", str(dest), str(claude_md), str(tmp_path / "TEAM.md"))
    content = claude_md.read_text(encoding="utf-8")
    assert "## Agents and Rules" in content


def test_add_finds_agent_in_nested_category(tmp_path):
    """Agent in 02-lang/python-pro.md found by just 'python-pro.md'."""
    lib = _make_library(tmp_path)
    dest = tmp_path / "agents"
    cmd_add(lib, "backend-developer.md", str(dest), str(tmp_path / "CLAUDE.md"), str(tmp_path / "TEAM.md"))
    assert (dest / "backend-developer.md").exists()
