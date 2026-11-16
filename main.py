#!/usr/bin/env python3
"""
Nexus File Manager – Root Entry Point.
Launches the full desktop application from either `python main.py` or `python run.py`.
"""
import sys
import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
NEXUS_DIR = ROOT_DIR / "nexus_file_manager"

for p in (str(NEXUS_DIR), str(ROOT_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

# Import main from package or local module
try:
    from nexus_file_manager.main import main as app_main
except ImportError:
    try:
        import main as _m
        app_main = _m.main
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
