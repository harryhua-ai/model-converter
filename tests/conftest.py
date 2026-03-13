# tests/conftest.py
import sys
import os
from pathlib import Path

# Add .claude to Python path
project_root = Path(__file__).parent.parent
claude_path = project_root / ".claude"
sys.path.insert(0, str(claude_path))
