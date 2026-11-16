#!/usr/bin/env python3
"""
Nexus File Manager – Root Entry Point.
Launches the full desktop application from either `python main.py` or `python run.py`.
"""
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

ROOT_DIR = Path(__file__).resolve().parent
NEXUS_DIR = ROOT_DIR / "nexus_file_manager"

for p in (NEXUS_DIR, ROOT_DIR):
    p_str = str(p)
    if p.exists() and p_str not in sys.path:
        sys.path.insert(0, p_str)

# Import main from package or local module
try:
    from nexus_file_manager.main import main as app_main
except ImportError:
    try:
        from main import main as app_main
    except ImportError:
        import importlib.util
        target = NEXUS_DIR / "main.py"
        spec = importlib.util.spec_from_file_location("main", str(target))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        app_main = mod.main


def main(argv=None):
    return app_main(argv)


if __name__ == "__main__":
    sys.exit(main())
