"""
Pytest configuration for the databy backend.

This file ensures that pytest can find the app module correctly
by adding the project root to sys.path.
"""
import sys
from pathlib import Path

# Add the project root to sys.path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
