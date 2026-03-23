"""Tests for the init-project subcommand."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from init_team import cmd_init_project


def _make_git_rules_src(tmp_path: Path) -> Path:
    """Create a fake GIT_RULES.md source file."""
    src = tmp_path / "GIT_RULES.md"
    src.write_text("# Git Rules\n\nUse descriptive branch names.\n", encoding="utf-8")
    return src


def test_init_project_creates_both_dirs(tmp_path):
    src = _make_git_rules_src(tmp_path)
    rules_dest = tmp_path / "rules"
    agents_dest = tmp_path / "agents"
    cmd_init_project(str(rules_dest), str(agents_dest), str(src))
    assert rules_dest.is_dir()
    assert agents_dest.is_dir()


def test_init_project_copies_git_rules(tmp_path):
    src = _make_git_rules_src(tmp_path)
    rules_dest = tmp_path / "rules"
    agents_dest = tmp_path / "agents"
    cmd_init_project(str(rules_dest), str(agents_dest), str(src))
    assert (rules_dest / "git-rules.md").exists()
    assert "Git Rules" in (rules_dest / "git-rules.md").read_text(encoding="utf-8")


def test_init_project_skips_existing_dirs(tmp_path):
    src = _make_git_rules_src(tmp_path)
    rules_dest = tmp_path / "rules"
    agents_dest = tmp_path / "agents"
    rules_dest.mkdir()
    agents_dest.mkdir()
    # Should not raise, even though dirs already exist
    cmd_init_project(str(rules_dest), str(agents_dest), str(src))
    assert rules_dest.is_dir()
    assert agents_dest.is_dir()


def test_init_project_skips_existing_git_rules(tmp_path, capsys):
    src = _make_git_rules_src(tmp_path)
    rules_dest = tmp_path / "rules"
    agents_dest = tmp_path / "agents"
    rules_dest.mkdir()
    (rules_dest / "git-rules.md").write_text("existing content", encoding="utf-8")
    cmd_init_project(str(rules_dest), str(agents_dest), str(src))
    assert (rules_dest / "git-rules.md").read_text(encoding="utf-8") == "existing content"
    captured = capsys.readouterr()
    assert "[SKIP] git-rules.md" in captured.out


def test_init_project_handles_missing_git_rules_src(tmp_path, capsys):
    rules_dest = tmp_path / "rules"
    agents_dest = tmp_path / "agents"
    cmd_init_project(str(rules_dest), str(agents_dest), str(tmp_path / "nonexistent.md"))
    # Dirs should still be created
    assert rules_dest.is_dir()
    assert agents_dest.is_dir()
    # Warning should go to stderr
    captured = capsys.readouterr()
    assert "Warning" in captured.err


def test_init_project_json_output(tmp_path, capsys):
    src = _make_git_rules_src(tmp_path)
    rules_dest = tmp_path / "rules"
    agents_dest = tmp_path / "agents"
    cmd_init_project(str(rules_dest), str(agents_dest), str(src))
    captured = capsys.readouterr()
    # Last line should be valid JSON
    json_line = [line for line in captured.out.strip().splitlines() if line.startswith("{")]
    assert json_line, "Expected JSON output line"
    data = json.loads(json_line[-1])
    assert "dirs_created" in data
    assert "files_copied" in data
    assert "files_skipped" in data
    assert "git-rules.md" in data["files_copied"]


def test_init_project_copies_frontend_rules(tmp_path):
    git_src = _make_git_rules_src(tmp_path)
    fe_src = tmp_path / "FRONTEND_RULES.md"
    fe_src.write_text("# Frontend Rules\n\nNo static text selectable.\n", encoding="utf-8")
    rules_dest = tmp_path / "rules"
    agents_dest = tmp_path / "agents"
    cmd_init_project(str(rules_dest), str(agents_dest), str(git_src), frontend_rules_src=str(fe_src))
    assert (rules_dest / "frontend-rules.md").exists()
    assert "Frontend Rules" in (rules_dest / "frontend-rules.md").read_text(encoding="utf-8")


def test_init_project_skips_frontend_rules_when_not_provided(tmp_path):
    git_src = _make_git_rules_src(tmp_path)
    rules_dest = tmp_path / "rules"
    agents_dest = tmp_path / "agents"
    cmd_init_project(str(rules_dest), str(agents_dest), str(git_src))
    assert not (rules_dest / "frontend-rules.md").exists()
