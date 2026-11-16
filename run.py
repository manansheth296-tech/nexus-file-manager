#!/usr/bin/env python3
"""Convenience launcher for Nexus File Manager."""

import os
import sys
from pathlib import Path

# Always ensure the root workspace and nexus_file_manager directories are on sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
NEXUS_DIR = SCRIPT_DIR / "nexus_file_manager"
CWD = Path.cwd()

for candidate in (SCRIPT_DIR, NEXUS_DIR, CWD, CWD / "nexus_file_manager"):
    p_str = str(candidate.resolve())
    if candidate.exists() and p_str not in sys.path:
        sys.path.insert(0, p_str)

# Robust import of main module
try:
    from nexus_file_manager import main
except (ImportError, ModuleNotFoundError):
    try:
        import main
    except (ImportError, ModuleNotFoundError):
        import importlib.util
        target = NEXUS_DIR / "main.py"
        if not target.exists():
            target = SCRIPT_DIR / "main.py"
        if not target.exists():
            target = CWD / "nexus_file_manager" / "main.py"
        spec = importlib.util.spec_from_file_location("nexus_main", str(target))
        main = importlib.util.module_from_spec(spec)
        sys.modules["main"] = main
        spec.loader.exec_module(main)

if __name__ == "__main__":
    if hasattr(main, "main"):
        main.main()
