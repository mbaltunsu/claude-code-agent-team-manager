"""Tests for the update subcommand."""

import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from init_team import cmd_update, _compare_versions


class TestCompareVersions:
    def test_newer(self):
        assert _compare_versions("1.0.0", "1.1.0") == -1

    def test_same(self):
        assert _compare_versions("1.0.0", "1.0.0") == 0

    def test_older(self):
        assert _compare_versions("2.0.0", "1.0.0") == 1

    def test_patch_difference(self):
        assert _compare_versions("1.0.0", "1.0.1") == -1

    def test_major_difference(self):
        assert _compare_versions("1.9.9", "2.0.0") == -1


class TestCmdUpdate:
    @patch("init_team.shutil.which", return_value=None)
    def test_git_not_found(self, mock_which):
        result = json.loads(cmd_update())
        assert "error" in result
        assert "git" in result["error"].lower()

    @patch("init_team.shutil.which", return_value="/usr/bin/git")
    @patch("init_team.subprocess.run")
    @patch("init_team.shutil.rmtree")
    def test_no_update_when_same_version(self, mock_rmtree, mock_run, mock_which, tmp_path):
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        with patch("init_team.tempfile.mkdtemp", return_value=str(tmp_path / "tmp")):
            tmp_dir = tmp_path / "tmp"
            tmp_dir.mkdir()
            plugin_dir = tmp_dir / ".claude-plugin"
            plugin_dir.mkdir()
            (plugin_dir / "plugin.json").write_text(
                json.dumps({"version": "1.0.0"}), encoding="utf-8"
            )

            with patch("init_team._get_local_plugin_json") as mock_local:
                mock_local.return_value = {"version": "1.0.0"}
                result = json.loads(cmd_update())

        assert result["updated"] is False
        assert result["current_version"] == "1.0.0"

    @patch("init_team.shutil.which", return_value="/usr/bin/git")
    @patch("init_team.subprocess.run")
    @patch("init_team.shutil.rmtree")
    def test_update_when_newer(self, mock_rmtree, mock_run, mock_which, tmp_path):
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        with patch("init_team.tempfile.mkdtemp", return_value=str(tmp_path / "tmp")):
            tmp_dir = tmp_path / "tmp"
            tmp_dir.mkdir()
            plugin_dir = tmp_dir / ".claude-plugin"
            plugin_dir.mkdir()
            (plugin_dir / "plugin.json").write_text(
                json.dumps({"version": "2.0.0"}), encoding="utf-8"
            )
            skill_dir = tmp_dir / "skills" / "init-team" / "scripts"
            skill_dir.mkdir(parents=True)
            (skill_dir / "init_team.py").write_text("# new version", encoding="utf-8")

            with patch("init_team._get_local_plugin_json") as mock_local:
                mock_local.return_value = {"version": "1.0.0"}
                with patch("init_team._get_local_plugin_root") as mock_root:
                    mock_root.return_value = tmp_path / "local"
                    (tmp_path / "local").mkdir()
                    result = json.loads(cmd_update())

        assert result["updated"] is True
        assert result["old_version"] == "1.0.0"
        assert result["new_version"] == "2.0.0"

    @patch("init_team.shutil.which", return_value="/usr/bin/git")
    @patch("init_team.subprocess.run")
    def test_network_failure(self, mock_run, mock_which, tmp_path):
        mock_run.return_value = MagicMock(returncode=1, stderr="fatal: Could not resolve host")

        with patch("init_team.tempfile.mkdtemp", return_value=str(tmp_path / "tmp")):
            (tmp_path / "tmp").mkdir()
            with patch("init_team.shutil.rmtree"):
                result = json.loads(cmd_update())

        assert "error" in result

    @patch("init_team.shutil.which", return_value="/usr/bin/git")
    @patch("init_team.subprocess.run")
    def test_cleans_temp_dir(self, mock_run, mock_which, tmp_path):
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        with patch("init_team.tempfile.mkdtemp", return_value=str(tmp_path / "tmp")):
            tmp_dir = tmp_path / "tmp"
            tmp_dir.mkdir()
            plugin_dir = tmp_dir / ".claude-plugin"
            plugin_dir.mkdir()
            (plugin_dir / "plugin.json").write_text(
                json.dumps({"version": "1.0.0"}), encoding="utf-8"
            )

            with patch("init_team._get_local_plugin_json") as mock_local:
                mock_local.return_value = {"version": "1.0.0"}
                with patch("init_team.shutil.rmtree") as mock_rmtree:
                    cmd_update()
                    mock_rmtree.assert_called_once_with(str(tmp_dir))
