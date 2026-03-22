"""Tests for source registry management (_load_sources, _save_sources, cmd_source_*)."""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from init_team import (
    DEFAULT_SOURCE_ENTRY,
    _load_sources,
    _save_sources,
    cmd_source_add,
    cmd_source_list,
    cmd_source_remove,
)


# ── _load_sources ────────────────────────────────────────────────────────────

def test_load_sources_returns_default_when_no_file(tmp_path):
    registry = tmp_path / "sources.json"
    with patch("init_team.SOURCES_REGISTRY", registry):
        sources = _load_sources()
    assert len(sources) == 1
    assert sources[0]["id"] == "voltagent"
    assert sources[0]["is_default"] is True


def test_load_sources_reads_existing_file(tmp_path):
    registry = tmp_path / "sources.json"
    data = {"sources": [{"id": "custom", "name": "my-agents", "repo": "https://example.com/repo.git"}]}
    registry.write_text(json.dumps(data), encoding="utf-8")
    with patch("init_team.SOURCES_REGISTRY", registry):
        sources = _load_sources()
    assert len(sources) == 1
    assert sources[0]["id"] == "custom"


def test_load_sources_returns_empty_list_on_parse_error(tmp_path, capsys):
    registry = tmp_path / "sources.json"
    registry.write_text("not valid json", encoding="utf-8")
    with patch("init_team.SOURCES_REGISTRY", registry):
        sources = _load_sources()
    assert sources == []
    assert "Warning" in capsys.readouterr().err


# ── _save_sources ────────────────────────────────────────────────────────────

def test_save_sources_creates_dir_if_missing(tmp_path):
    registry = tmp_path / "subdir" / "sources.json"
    with patch("init_team.SOURCES_REGISTRY", registry), \
         patch("init_team.TEAM_MANAGEMENT_DIR", registry.parent):
        _save_sources([DEFAULT_SOURCE_ENTRY])
    assert registry.exists()


def test_save_sources_writes_valid_json(tmp_path):
    registry = tmp_path / "sources.json"
    with patch("init_team.SOURCES_REGISTRY", registry), \
         patch("init_team.TEAM_MANAGEMENT_DIR", tmp_path):
        _save_sources([DEFAULT_SOURCE_ENTRY])
    data = json.loads(registry.read_text(encoding="utf-8"))
    assert "sources" in data
    assert data["sources"][0]["id"] == "voltagent"


# ── cmd_source_list ───────────────────────────────────────────────────────────

def test_source_list_prints_json(tmp_path, capsys):
    registry = tmp_path / "sources.json"
    with patch("init_team.SOURCES_REGISTRY", registry):
        cmd_source_list()
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert isinstance(data, list)
    assert data[0]["id"] == "voltagent"


# ── cmd_source_add ────────────────────────────────────────────────────────────

def test_source_add_adds_entry(tmp_path, capsys):
    registry = tmp_path / "sources.json"
    with patch("init_team.SOURCES_REGISTRY", registry), \
         patch("init_team.TEAM_MANAGEMENT_DIR", tmp_path):
        cmd_source_add(
            repo="https://github.com/user/my-agents.git",
            name="my-agents",
            author="user",
            homepage="",
            description="",
        )
    with patch("init_team.SOURCES_REGISTRY", registry):
        sources = _load_sources()
    ids = [s["id"] for s in sources]
    assert "my-agents" in ids
    assert "[OK]" in capsys.readouterr().out


def test_source_add_rejects_duplicate_id(tmp_path, capsys):
    registry = tmp_path / "sources.json"
    with patch("init_team.SOURCES_REGISTRY", registry), \
         patch("init_team.TEAM_MANAGEMENT_DIR", tmp_path):
        cmd_source_add(repo="https://x.git", name="my-agents", author="", homepage="", description="")
        # second add with same generated id
        cmd_source_add(repo="https://y.git", name="my-agents", author="", homepage="", description="")
    with patch("init_team.SOURCES_REGISTRY", registry):
        sources = _load_sources()
    assert sum(1 for s in sources if s["id"] == "my-agents") == 1
    assert "already exists" in capsys.readouterr().err


# ── cmd_source_remove ─────────────────────────────────────────────────────────

def test_source_remove_removes_entry(tmp_path, capsys):
    registry = tmp_path / "sources.json"
    # Pre-populate with voltagent + custom
    initial = [DEFAULT_SOURCE_ENTRY, {"id": "custom", "name": "custom", "repo": "https://x.git"}]
    with patch("init_team.SOURCES_REGISTRY", registry), \
         patch("init_team.TEAM_MANAGEMENT_DIR", tmp_path):
        _save_sources(initial)
        cmd_source_remove("custom")
    with patch("init_team.SOURCES_REGISTRY", registry):
        sources = _load_sources()
    assert all(s["id"] != "custom" for s in sources)
    assert "[OK]" in capsys.readouterr().out


def test_source_remove_exits_if_not_found(tmp_path):
    registry = tmp_path / "sources.json"
    with patch("init_team.SOURCES_REGISTRY", registry), \
         patch("init_team.TEAM_MANAGEMENT_DIR", tmp_path):
        with pytest.raises(SystemExit) as exc_info:
            cmd_source_remove("nonexistent-id")
    assert exc_info.value.code == 1
