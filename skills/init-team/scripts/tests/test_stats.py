"""Tests for the stats subcommand."""
import json
from pathlib import Path
from unittest.mock import patch

import init_team


def _write_session_meta(meta_dir, session_id, project_path, **overrides):
    """Helper: write a fake session-meta JSON file."""
    data = {
        "session_id": session_id,
        "project_path": project_path,
        "start_time": "2026-03-20T10:00:00.000Z",
        "duration_minutes": 5,
        "user_message_count": 3,
        "assistant_message_count": 10,
        "tool_counts": {"Bash": 2, "Edit": 1},
        "input_tokens": 1000,
        "output_tokens": 500,
        "uses_task_agent": False,
        "lines_added": 10,
        "lines_removed": 2,
        "files_modified": 3,
        "git_commits": 1,
        "git_pushes": 0,
        "tool_errors": 0,
    }
    data.update(overrides)
    f = meta_dir / f"{session_id}.json"
    f.write_text(json.dumps(data), encoding="utf-8")
    return f


def test_stats_reads_session_meta_files(tmp_path, capsys):
    meta_dir = tmp_path / "session-meta"
    meta_dir.mkdir()
    _write_session_meta(meta_dir, "aaa", "/proj", input_tokens=1000, output_tokens=500)
    _write_session_meta(meta_dir, "bbb", "/proj", input_tokens=2000, output_tokens=800)

    with patch("init_team.USAGE_DATA_DIR", tmp_path):
        init_team.cmd_stats(project_path=None, last_n=10)

    out = json.loads(capsys.readouterr().out)
    assert out["sessions"] == 2
    assert out["total_tokens"]["input"] == 3000
    assert out["total_tokens"]["output"] == 1300


def test_stats_filters_by_project(tmp_path, capsys):
    meta_dir = tmp_path / "session-meta"
    meta_dir.mkdir()
    _write_session_meta(meta_dir, "aaa", "/proj-a", input_tokens=1000, output_tokens=500)
    _write_session_meta(meta_dir, "bbb", "/proj-b", input_tokens=2000, output_tokens=800)
    _write_session_meta(meta_dir, "ccc", "/proj-a", input_tokens=3000, output_tokens=100)

    with patch("init_team.USAGE_DATA_DIR", tmp_path):
        init_team.cmd_stats(project_path="/proj-a", last_n=10)

    out = json.loads(capsys.readouterr().out)
    assert out["sessions"] == 2
    assert out["total_tokens"]["input"] == 4000


def test_stats_handles_empty_dir(tmp_path, capsys):
    meta_dir = tmp_path / "session-meta"
    meta_dir.mkdir()

    with patch("init_team.USAGE_DATA_DIR", tmp_path):
        init_team.cmd_stats(project_path=None, last_n=10)

    out = json.loads(capsys.readouterr().out)
    assert out["sessions"] == 0
    assert out["total_tokens"]["input"] == 0
    assert out["total_tokens"]["output"] == 0


def test_stats_limits_to_last_n(tmp_path, capsys):
    meta_dir = tmp_path / "session-meta"
    meta_dir.mkdir()
    for i in range(20):
        _write_session_meta(
            meta_dir,
            f"s{i:03d}",
            "/proj",
            start_time=f"2026-03-{i + 1:02d}T10:00:00.000Z",
            input_tokens=100,
            output_tokens=50,
        )

    with patch("init_team.USAGE_DATA_DIR", tmp_path):
        init_team.cmd_stats(project_path=None, last_n=5)

    out = json.loads(capsys.readouterr().out)
    assert out["sessions"] == 5
    assert out["total_tokens"]["input"] == 500


def test_stats_handles_missing_dir(tmp_path, capsys):
    """If session-meta dir doesn't exist, return empty stats."""
    with patch("init_team.USAGE_DATA_DIR", tmp_path):
        init_team.cmd_stats(project_path=None, last_n=10)

    out = json.loads(capsys.readouterr().out)
    assert out["sessions"] == 0


def test_stats_aggregates_tool_counts(tmp_path, capsys):
    meta_dir = tmp_path / "session-meta"
    meta_dir.mkdir()
    _write_session_meta(meta_dir, "aaa", "/proj", tool_counts={"Agent": 3, "Bash": 2})
    _write_session_meta(meta_dir, "bbb", "/proj", tool_counts={"Agent": 1, "Edit": 5})

    with patch("init_team.USAGE_DATA_DIR", tmp_path):
        init_team.cmd_stats(project_path=None, last_n=10)

    out = json.loads(capsys.readouterr().out)
    assert out["tool_usage"]["Agent"] == 4
    assert out["tool_usage"]["Bash"] == 2
    assert out["tool_usage"]["Edit"] == 5


def test_stats_counts_agent_sessions(tmp_path, capsys):
    meta_dir = tmp_path / "session-meta"
    meta_dir.mkdir()
    _write_session_meta(meta_dir, "aaa", "/proj", uses_task_agent=True)
    _write_session_meta(meta_dir, "bbb", "/proj", uses_task_agent=False)
    _write_session_meta(meta_dir, "ccc", "/proj", uses_task_agent=True)

    with patch("init_team.USAGE_DATA_DIR", tmp_path):
        init_team.cmd_stats(project_path=None, last_n=10)

    out = json.loads(capsys.readouterr().out)
    assert out["agent_sessions"] == 2
