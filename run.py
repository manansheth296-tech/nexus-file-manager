#!/usr/bin/env python3
"""Convenience launcher for Nexus File Manager."""

from __future__ import annotations
import os
import sys
from pathlib import Path

# If frozen inside PyInstaller bundle, ensure internal bundle directories are on sys.path
if getattr(sys, "frozen", False):
    bundle_dir = Path(getattr(sys, "_MEIPASS", sys.executable)).parent
    for p in (bundle_dir, bundle_dir / "_internal", bundle_dir / "_internal" / "nexus_file_manager"):
        p_str = str(p)
        if p.exists() and p_str not in sys.path:
            sys.path.insert(0, p_str)

# Ensure root workspace and nexus_file_manager package directories are on sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
NEXUS_DIR = SCRIPT_DIR / "nexus_file_manager"
CWD = Path.cwd()

for candidate in (SCRIPT_DIR, NEXUS_DIR, CWD, CWD / "nexus_file_manager"):
    p_str = str(candidate.resolve())
    if candidate.exists() and p_str not in sys.path:
        sys.path.insert(0, p_str)

# Explicit import of the main entry point
try:
    from nexus_file_manager.main import main
except (ImportError, ModuleNotFoundError):
    try:
        from main import main
    except (ImportError, ModuleNotFoundError):
        import importlib.util
        target = NEXUS_DIR / "main.py"
        if not target.exists():
            target = SCRIPT_DIR / "main.py"
        if not target.exists():
            target = CWD / "nexus_file_manager" / "main.py"
        spec = importlib.util.spec_from_file_location("nexus_main", str(target))
        _mod = importlib.util.module_from_spec(spec)
        sys.modules["main"] = _mod
        spec.loader.exec_module(_mod)
        main = _mod.main

if __name__ == "__main__":
    sys.exit(main())
