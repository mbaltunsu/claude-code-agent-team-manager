import json
import os
import shutil
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from init_team import cmd_download


DEFAULT_REPO = "https://github.com/VoltAgent/awesome-claude-code-subagents.git"


# --- dest directory creation ---

def test_download_creates_dest_dir(tmp_path):
    dest = tmp_path / "new_library"
    assert not dest.exists()

    # Mock git to simulate a successful clone with no files
    with patch("init_team.shutil.which", return_value="/usr/bin/git"), \
         patch("init_team.subprocess.run") as mock_run, \
         patch("init_team.tempfile.mkdtemp", return_value=str(tmp_path / "tmpclone")):
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        # Create empty categories dir in the "clone"
        (tmp_path / "tmpclone" / "categories").mkdir(parents=True)

        result = cmd_download(dest=str(dest))

    assert dest.exists()


def test_download_creates_nested_dest(tmp_path):
    dest = tmp_path / "a" / "b" / "c" / "library"
    assert not dest.exists()

    with patch("init_team.shutil.which", return_value="/usr/bin/git"), \
         patch("init_team.subprocess.run") as mock_run, \
         patch("init_team.tempfile.mkdtemp", return_value=str(tmp_path / "tmpclone")):
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        (tmp_path / "tmpclone" / "categories").mkdir(parents=True)

        result = cmd_download(dest=str(dest))

    assert dest.exists()
    assert (dest / "categories").exists()


# --- git commands ---

def test_download_calls_git_sparse_checkout(tmp_path):
    dest = tmp_path / "lib"
    clone_dir = tmp_path / "tmpclone"

    with patch("init_team.shutil.which", return_value="/usr/bin/git"), \
         patch("init_team.subprocess.run") as mock_run, \
         patch("init_team.tempfile.mkdtemp", return_value=str(clone_dir)):
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        (clone_dir / "categories").mkdir(parents=True)

        cmd_download(dest=str(dest))

    calls = mock_run.call_args_list
    # Should have at least: clone, sparse-checkout init, sparse-checkout set, checkout
    assert len(calls) >= 4
    clone_call = calls[0]
    assert "clone" in clone_call[0][0]
    assert "--depth=1" in clone_call[0][0]


def test_download_custom_repo_url(tmp_path):
    dest = tmp_path / "lib"
    custom_repo = "https://github.com/custom/agents.git"

    with patch("init_team.shutil.which", return_value="/usr/bin/git"), \
         patch("init_team.subprocess.run") as mock_run, \
         patch("init_team.tempfile.mkdtemp", return_value=str(tmp_path / "tmpclone")):
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        (tmp_path / "tmpclone" / "categories").mkdir(parents=True)

        cmd_download(dest=str(dest), repo=custom_repo)

    clone_call = mock_run.call_args_list[0]
    assert custom_repo in clone_call[0][0]


# --- merge mode ---

def test_download_merge_skips_existing(tmp_path, capsys):
    dest = tmp_path / "lib"
    clone_dir = tmp_path / "tmpclone"

    # Pre-existing agent at destination
    (dest / "categories" / "01-core").mkdir(parents=True)
    (dest / "categories" / "01-core" / "existing.md").write_text("custom content", encoding="utf-8")

    # Downloaded agent (same path + a new one)
    (clone_dir / "categories" / "01-core").mkdir(parents=True)
    (clone_dir / "categories" / "01-core" / "existing.md").write_text("new content", encoding="utf-8")
    (clone_dir / "categories" / "01-core" / "new-agent.md").write_text("new agent", encoding="utf-8")

    with patch("init_team.shutil.which", return_value="/usr/bin/git"), \
         patch("init_team.subprocess.run") as mock_run, \
         patch("init_team.tempfile.mkdtemp", return_value=str(clone_dir)):
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        result = cmd_download(dest=str(dest))

    # Existing file should NOT be overwritten
    assert (dest / "categories" / "01-core" / "existing.md").read_text(encoding="utf-8") == "custom content"
    # New file should be copied
    assert (dest / "categories" / "01-core" / "new-agent.md").exists()

    output = json.loads(result)
    assert "01-core/existing.md" in output["skipped"]
    assert "01-core/new-agent.md" in output["downloaded"]


# --- error handling ---

def test_download_git_not_found(capsys):
    with patch("init_team.shutil.which", return_value=None):
        result = cmd_download(dest="/tmp/test")

    output = json.loads(result)
    assert "error" in output
    assert "git" in output["error"].lower()


def test_download_network_failure(tmp_path):
    dest = tmp_path / "lib"

    with patch("init_team.shutil.which", return_value="/usr/bin/git"), \
         patch("init_team.subprocess.run") as mock_run, \
         patch("init_team.tempfile.mkdtemp", return_value=str(tmp_path / "tmpclone")):
        mock_run.return_value = MagicMock(returncode=128, stderr="fatal: repository not found")

        result = cmd_download(dest=str(dest))

    output = json.loads(result)
    assert "error" in output
    assert "repository" in output["error"].lower() or "clone" in output["error"].lower()


# --- JSON output ---

def test_download_json_output(tmp_path):
    dest = tmp_path / "lib"
    clone_dir = tmp_path / "tmpclone"

    (clone_dir / "categories" / "01-core").mkdir(parents=True)
    (clone_dir / "categories" / "01-core" / "agent.md").write_text("content", encoding="utf-8")

    with patch("init_team.shutil.which", return_value="/usr/bin/git"), \
         patch("init_team.subprocess.run") as mock_run, \
         patch("init_team.tempfile.mkdtemp", return_value=str(clone_dir)):
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        result = cmd_download(dest=str(dest))

    output = json.loads(result)
    assert "downloaded" in output
    assert "skipped" in output
    assert "dest" in output
    assert output["dest"] == str(dest)


# --- cleanup ---

def test_download_cleans_temp_dir(tmp_path):
    dest = tmp_path / "lib"
    clone_dir = tmp_path / "tmpclone"
    clone_dir.mkdir()
    (clone_dir / "categories").mkdir()

    with patch("init_team.shutil.which", return_value="/usr/bin/git"), \
         patch("init_team.subprocess.run") as mock_run, \
         patch("init_team.tempfile.mkdtemp", return_value=str(clone_dir)):
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        cmd_download(dest=str(dest))

    assert not clone_dir.exists()


def test_download_cleanup_failure_warns(tmp_path):
    dest = tmp_path / "lib"
    clone_dir = tmp_path / "tmpclone"
    clone_dir.mkdir()
    (clone_dir / "categories").mkdir()

    with patch("init_team.shutil.which", return_value="/usr/bin/git"), \
         patch("init_team.subprocess.run") as mock_run, \
         patch("init_team.tempfile.mkdtemp", return_value=str(clone_dir)), \
         patch("init_team.shutil.rmtree", side_effect=PermissionError("locked")):
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        result = cmd_download(dest=str(dest))

    output = json.loads(result)
    assert "warning" in output
    assert "cleanup" in output["warning"].lower() or "temp" in output["warning"].lower()
