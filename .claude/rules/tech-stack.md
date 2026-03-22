# Tech Stack

## Runtime / Language

Python 3.8+ (target: 3.8 minimum for broad compatibility, tested on 3.12)

## Frameworks

None — `init_team.py` uses Python standard library only. No external packages in production code.

## Key Dependencies

**Runtime (stdlib only):**
- `argparse` — CLI argument parsing
- `pathlib` — all filesystem path operations
- `json` — JSON serialization for all CLI outputs
- `shutil` — file copying, temp dir cleanup
- `subprocess` — git CLI calls (download, update, import)
- `tempfile` — temporary clone directories
- `re` — YAML frontmatter parsing, section pattern matching
- `typing` — `Optional` for Python 3.8 compatibility

**Development only:**
- `pytest` — test runner (`pip install pytest`)
- `unittest.mock` — `patch`, `MagicMock` for mocking git subprocess calls and filesystem globals

## Dev Tools

- `pytest` with `tmp_path` fixture — all tests are isolated, no real filesystem state
- `conftest.py` — adds script dir to `sys.path`, sets UTF-8 encoding for Windows
- No linter configured (follow existing code style by hand)

## Conventions

- **No third-party imports** in `init_team.py` — if you need it, check if stdlib covers it first
- **All outputs are JSON** for subcommands that return data (`scan`, `list`, `download`, `import`, `update`, `source-list`, `init-project`)
- **`[OK]` / `[SKIP]` prefixes** for per-file progress lines to stdout
- **`sys.exit(1)`** on errors — never raise exceptions that bubble to the user
- **`encoding="utf-8"`** on every `read_text()` and `write_text()` call
- **`Optional[str]`** not `str | None` — Python 3.8 compatibility
- **Test file naming**: one concern per file — `test_scan.py`, `test_copy.py`, `test_sources.py`, etc.
- **Mock global constants** in tests: patch `init_team.SOURCES_REGISTRY`, `init_team.DEFAULT_AGENTS_DIR`, `init_team.TEAM_MANAGEMENT_DIR` — never let tests write to real home directory
