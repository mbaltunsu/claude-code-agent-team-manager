import json
import pytest
from pathlib import Path
from init_team import parse_frontmatter, cmd_scan


# --- parse_frontmatter ---

def test_parse_frontmatter_valid():
    content = "---\nname: test-agent\ndescription: A test agent\n---\nBody"
    result = parse_frontmatter(content)
    assert result["name"] == "test-agent"
    assert result["description"] == "A test agent"


def test_parse_frontmatter_missing_description():
    content = "---\nname: test-agent\n---\nBody"
    result = parse_frontmatter(content)
    assert result is None


def test_parse_frontmatter_no_frontmatter():
    content = "Just body text"
    result = parse_frontmatter(content)
    assert result is None


def test_parse_frontmatter_empty_description():
    content = "---\nname: agent\ndescription: \n---\nBody"
    result = parse_frontmatter(content)
    assert result is None


def test_parse_frontmatter_crlf_line_endings():
    content = "---\r\nname: agent\r\ndescription: An agent\r\n---\r\nBody"
    result = parse_frontmatter(content)
    assert result is not None
    assert result["name"] == "agent"
    assert result["description"] == "An agent"


# --- cmd_scan ---

def make_agent_file(directory: Path, filename: str, name: str, description: str):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / filename).write_text(
        f"---\nname: {name}\ndescription: {description}\n---\nContent",
        encoding="utf-8",
    )


def test_scan_returns_agents(tmp_path, capsys):
    cat_dir = tmp_path / "categories" / "01-core-development"
    make_agent_file(cat_dir, "backend-developer.md", "backend-developer", "Backend specialist")
    cmd_scan(str(tmp_path))
    captured = capsys.readouterr()
    agents = json.loads(captured.out)
    assert len(agents) == 1
    assert agents[0]["name"] == "backend-developer"
    assert agents[0]["category"] == "01-core-development"
    assert agents[0]["file"] == "backend-developer.md"
    assert agents[0]["path"] == "01-core-development/backend-developer.md"
    assert agents[0]["description"] == "Backend specialist"


def test_scan_skips_invalid_frontmatter_and_warns(tmp_path, capsys):
    cat_dir = tmp_path / "categories" / "01-core-development"
    cat_dir.mkdir(parents=True)
    (cat_dir / "bad-agent.md").write_text("No frontmatter here", encoding="utf-8")
    cmd_scan(str(tmp_path))
    captured = capsys.readouterr()
    agents = json.loads(captured.out)
    assert len(agents) == 0
    assert "Warning" in captured.err


def test_scan_skips_readme_silently(tmp_path, capsys):
    cat_dir = tmp_path / "categories" / "01-core-development"
    cat_dir.mkdir(parents=True)
    (cat_dir / "README.md").write_text("# README", encoding="utf-8")
    cmd_scan(str(tmp_path))
    captured = capsys.readouterr()
    agents = json.loads(captured.out)
    assert len(agents) == 0
    assert captured.err == ""  # README is skipped silently, no warning


def test_scan_multiple_categories(tmp_path, capsys):
    make_agent_file(tmp_path / "categories" / "01-core", "backend.md", "backend", "Backend")
    make_agent_file(tmp_path / "categories" / "02-lang", "python.md", "python-expert", "Python")
    cmd_scan(str(tmp_path))
    captured = capsys.readouterr()
    agents = json.loads(captured.out)
    assert len(agents) == 2
    categories = {a["category"] for a in agents}
    assert "01-core" in categories
    assert "02-lang" in categories
