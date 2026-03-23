import pytest
from pathlib import Path
from unittest.mock import patch
from init_team import load_env, resolve_library_path, DEFAULT_AGENTS_DIR


# --- load_env ---

def test_load_env_reads_key_value(tmp_path):
    (tmp_path / ".env").write_text("AGENTS_LIBRARY_PATH=/some/path\n", encoding="utf-8")
    result = load_env(tmp_path)
    assert result["AGENTS_LIBRARY_PATH"] == "/some/path"


def test_load_env_ignores_comments(tmp_path):
    (tmp_path / ".env").write_text("# comment\nKEY=value\n", encoding="utf-8")
    result = load_env(tmp_path)
    assert "# comment" not in result
    assert result["KEY"] == "value"


def test_load_env_returns_empty_when_no_file(tmp_path):
    result = load_env(tmp_path)
    assert result == {}


# --- resolve_library_path ---

def test_resolve_uses_cli_arg(tmp_path):
    (tmp_path / "categories").mkdir()
    result = resolve_library_path(cli_path=str(tmp_path), env_path=None)
    assert result == str(tmp_path)


def test_resolve_uses_env_when_no_cli(tmp_path):
    (tmp_path / "categories").mkdir()
    result = resolve_library_path(cli_path=None, env_path=str(tmp_path))
    assert result == str(tmp_path)


def test_resolve_cli_wins_over_env(tmp_path):
    cli_lib = tmp_path / "cli_lib"
    cli_lib.mkdir()
    (cli_lib / "categories").mkdir()
    env_lib = tmp_path / "env_lib"
    env_lib.mkdir()
    (env_lib / "categories").mkdir()
    result = resolve_library_path(cli_path=str(cli_lib), env_path=str(env_lib))
    assert result == str(cli_lib)


def test_resolve_errors_when_neither(tmp_path):
    fake_central = tmp_path / "no-agents"
    with patch("init_team.DEFAULT_AGENTS_DIR", fake_central):
        with pytest.raises(SystemExit):
            resolve_library_path(cli_path=None, env_path=None)


def test_resolve_errors_when_path_not_exist(tmp_path):
    with pytest.raises(SystemExit):
        resolve_library_path(cli_path=str(tmp_path / "nonexistent"), env_path=None)


def test_resolve_errors_when_no_categories(tmp_path):
    with pytest.raises(SystemExit):
        resolve_library_path(cli_path=str(tmp_path), env_path=None)


def test_resolve_falls_back_to_central_agents_dir(tmp_path):
    """When no cli/env path given but central dir has categories/, use it."""
    central = tmp_path / "central"
    (central / "categories").mkdir(parents=True)
    with patch("init_team.DEFAULT_AGENTS_DIR", central):
        result = resolve_library_path(cli_path=None, env_path=None)
    assert result == str(central)
