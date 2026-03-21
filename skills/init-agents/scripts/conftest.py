import sys
from pathlib import Path

# Allow tests to import init_agents from the parent scripts/ directory
sys.path.insert(0, str(Path(__file__).parent))

# Force UTF-8 stdout for tests on Windows
sys.stdout.reconfigure(encoding="utf-8")
