#!/usr/bin/env python3
"""Convenience launcher for Nexus File Manager (Phases 1-4 UI + Real Backend)."""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
NEXUS_DIR = ROOT_DIR / "nexus_file_manager"

sys.path.insert(0, str(NEXUS_DIR))
sys.path.insert(0, str(ROOT_DIR))

# Launch the Phase 1-4 Nexus application
import main

if __name__ == "__main__":
    main.main()
