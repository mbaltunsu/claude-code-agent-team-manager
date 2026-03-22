"""Tests for the import subcommand (cmd_import)."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from init_team import cmd_import


def _make_library(base: Path) -> Path:
    """Create a minimal library with two agents in different categories."""
    cat1 = base / "categories" / "01-core"
    cat2 = base / "categories" / "02-lang"
    cat1.mkdir(parents=True)
    cat2.mkdir(parents=True)
    (cat1 / "backend-developer.md").write_text(
        "---\nname: backend-developer\ndescription: Backend specialist\n---\nContent",
        encoding="utf-8",
    )
    (cat2 / "python-pro.md").write_text(
        "---\nname: python-pro\ndescription: Python expert\n---\nContent",
        encoding="utf-8",
    )
    return base


def test_import_copies_agents_to_dest(tmp_path):
    lib = _make_library(tmp_path / "lib")
    dest = tmp_path / "central"
    result = json.loads(cmd_import(str(lib), str(dest)))
    assert (dest / "categories" / "01-core" / "backend-developer.md").exists()
    assert (dest / "categories" / "02-lang" / "python-pro.md").exists()
    assert len(result["imported"]) == 2


def test_import_skips_existing_agents(tmp_path):
    lib = _make_library(tmp_path / "lib")
    dest = tmp_path / "central"
    existing_dir = dest / "categories" / "01-core"
    existing_dir.mkdir(parents=True)
    (existing_dir / "backend-developer.md").write_text("custom content", encoding="utf-8")
    result = json.loads(cmd_import(str(lib), str(dest)))
    assert (existing_dir / "backend-developer.md").read_text(encoding="utf-8") == "custom content"
    assert "01-core/backend-developer.md" in result["skipped"]


def test_import_creates_dest_if_missing(tmp_path):
    lib = _make_library(tmp_path / "lib")
    dest = tmp_path / "new_central"
    assert not dest.exists()
    cmd_import(str(lib), str(dest))
    assert dest.is_dir()


def test_import_json_output(tmp_path):
    lib = _make_library(tmp_path / "lib")
    dest = tmp_path / "central"
    raw = cmd_import(str(lib), str(dest))
    data = json.loads(raw)
    assert "imported" in data
    assert "skipped" in data
    assert "dest" in data


def test_import_exits_if_no_categories_dir(tmp_path):
    lib = tmp_path / "bad-lib"
    lib.mkdir()
    dest = tmp_path / "central"
    with pytest.raises(SystemExit) as exc_info:
        cmd_import(str(lib), str(dest))
    assert exc_info.value.code == 1
