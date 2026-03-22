"""Tests for the list subcommand."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from init_team import cmd_list, parse_frontmatter


def _write_agent(dest, filename, name, description):
    """Helper: write a minimal agent .md file with frontmatter."""
    content = f"---\nname: {name}\ndescription: {description}\n---\n\n# {name}\n"
    (dest / filename).write_text(content, encoding="utf-8")


def test_list_empty_dest(tmp_path, capsys):
    """Missing dest directory outputs empty JSON array."""
    missing = tmp_path / "nonexistent"
    cmd_list(str(missing))
    out = json.loads(capsys.readouterr().out)
    assert out == []


def test_list_single_agent(tmp_path, capsys):
    """Single valid agent file returns one-element array."""
    _write_agent(tmp_path, "python-pro.md", "python-pro", "Python expert")
    cmd_list(str(tmp_path))
    out = json.loads(capsys.readouterr().out)
    assert len(out) == 1
    assert out[0]["file"] == "python-pro.md"
    assert out[0]["name"] == "python-pro"
    assert out[0]["description"] == "Python expert"


def test_list_multiple_agents_sorted(tmp_path, capsys):
    """Multiple agents returned sorted by filename."""
    _write_agent(tmp_path, "debugger.md", "debugger", "Debug things")
    _write_agent(tmp_path, "api-designer.md", "api-designer", "Design APIs")
    cmd_list(str(tmp_path))
    out = json.loads(capsys.readouterr().out)
    assert len(out) == 2
    assert out[0]["file"] == "api-designer.md"
    assert out[1]["file"] == "debugger.md"


def test_list_skips_readme(tmp_path, capsys):
    """README.md is excluded from the listing."""
    _write_agent(tmp_path, "python-pro.md", "python-pro", "Python expert")
    (tmp_path / "README.md").write_text("# Readme\n", encoding="utf-8")
    cmd_list(str(tmp_path))
    out = json.loads(capsys.readouterr().out)
    assert len(out) == 1
    assert out[0]["file"] == "python-pro.md"


def test_list_handles_invalid_frontmatter(tmp_path, capsys):
    """Agent with invalid frontmatter still appears with empty description."""
    (tmp_path / "broken.md").write_text("no frontmatter here\n", encoding="utf-8")
    cmd_list(str(tmp_path))
    out = json.loads(capsys.readouterr().out)
    assert len(out) == 1
    assert out[0]["file"] == "broken.md"
    assert out[0]["name"] == "broken.md"
    assert out[0]["description"] == ""


def test_list_output_is_valid_json(tmp_path, capsys):
    """Output is parseable JSON with correct keys."""
    _write_agent(tmp_path, "test-agent.md", "test-agent", "A test agent")
    cmd_list(str(tmp_path))
    raw = capsys.readouterr().out
    out = json.loads(raw)  # Should not raise
    assert isinstance(out, list)
    for entry in out:
        assert "file" in entry
        assert "name" in entry
        assert "description" in entry
