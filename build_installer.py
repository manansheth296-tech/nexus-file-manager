"""
Build script to package the Nexus Setup Wizard into a standalone Windows installer executable (NexusSetup.exe).
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
DIST_DIR = ROOT_DIR / "dist"
APP_DIST_DIR = DIST_DIR / "NexusFileManager"
ICON_PATH = ROOT_DIR / "assets" / "icon.ico"
INSTALLER_SCRIPT = ROOT_DIR / "installer" / "setup_wizard.py"


def build_installer(rebuild_app: bool = True):
    print("=" * 70)
    print("[*] Building Nexus File Manager Windows Setup Installer (NexusSetup.exe)")
    print("=" * 70)

    # 1. Build fresh application binary if requested or if missing
    if rebuild_app or not (APP_DIST_DIR / "NexusFileManager.exe").exists():
        print("[*] Building fresh Nexus File Manager executable distribution...")
        from build_app import build_app
        build_app(onefile=False)

    if not APP_DIST_DIR.exists():
        print(f"[-] Error: App distribution directory {APP_DIST_DIR} not found.")
        sys.exit(1)

    # 2. PyInstaller command to build the single-file setup wizard
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--name=NexusSetup",
        "--onefile",
        "--windowed",
        "--clean",
        "--noconfirm",
        f"--icon={ICON_PATH}",
        f"--add-data={APP_DIST_DIR};app",
        "--hidden-import=win32com",
        "--hidden-import=win32com.client",
        str(INSTALLER_SCRIPT),
    ]

    print("[*] Running PyInstaller for Setup Wizard...")
    res = subprocess.run(cmd)

    if res.returncode == 0:
        setup_exe = DIST_DIR / "NexusSetup.exe"
        print("\n" + "=" * 70)
        print("[+] Setup Installer Built Successfully!")
        print(f"[+] Windows Installer Executable: {setup_exe}")
        print("=" * 70)
    else:
        print(f"[-] Setup Installer build failed with exit code {res.returncode}")
        sys.exit(res.returncode)


if __name__ == "__main__":
    build_installer()
