"""Build and package Nexus File Manager into a standalone desktop application (.exe)."""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
DIST_DIR = ROOT_DIR / "dist"
BUILD_DIR = ROOT_DIR / "build"
ICON_PATH = ROOT_DIR / "assets" / "icon.ico"


def build_app(onefile: bool = False):
    print("=" * 60)
    print("[*] Packaging Nexus File Manager as Standalone Executable")
    print("=" * 60)

    # Ensure icon exists
    if not ICON_PATH.exists():
        from create_icon import create_app_icon
        create_app_icon()

    nexus_dir = ROOT_DIR / "nexus_file_manager"
    icons_dir = nexus_dir / "nexus" / "assets" / "icons"

    # PyInstaller arguments
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--name=NexusFileManager",
        "--windowed",                 # No console window popup
        "--clean",
        "--noconfirm",
        f"--icon={ICON_PATH}",
        f"--paths={ROOT_DIR}",
        f"--paths={nexus_dir}",
        f"--add-data={ROOT_DIR / 'assets'};assets",
        f"--add-data={icons_dir};nexus/assets/icons",
        f"--add-data={nexus_dir / 'nexus'};nexus",
        f"--add-data={nexus_dir};nexus_file_manager",
        f"--add-data={ROOT_DIR / 'src'};src",
        "--collect-all=nexus",
        "--collect-all=nexus_file_manager",
        "--collect-all=docx",
        "--collect-all=openpyxl",
        "--hidden-import=nexus",
        "--hidden-import=nexus_file_manager",
        "--hidden-import=nexus_file_manager.main",
        "--hidden-import=nexus.components.splash_screen",
        "--hidden-import=nexus.core",
        "--hidden-import=nexus.styles",
        "--hidden-import=nexus.tokens",
        "--hidden-import=nexus.views",
        "--hidden-import=nexus.dialogs",
        "--hidden-import=psutil",
        "--hidden-import=cryptography",
        "--hidden-import=send2trash",
        "--hidden-import=docx",
        "--hidden-import=openpyxl",
        "--hidden-import=win32com",
        "--hidden-import=win32com.client",
        str(ROOT_DIR / "run.py"),
    ]

    if onefile:
        cmd.append("--onefile")
    else:
        cmd.append("--onedir")

    print("[*] Running PyInstaller...")
    result = subprocess.run(cmd)

    if result.returncode == 0:
        print("\n" + "=" * 60)
        print("[+] Build Completed Successfully!")
        if onefile:
            exe_path = DIST_DIR / "NexusFileManager.exe"
            print(f"[+] Standalone Executable: {exe_path}")
        else:
            exe_path = DIST_DIR / "NexusFileManager" / "NexusFileManager.exe"
            print(f"[+] Application Directory: {DIST_DIR / 'NexusFileManager'}")
            print(f"[+] Executable: {exe_path}")
        print("=" * 60)
    else:
        print(f"\n[-] Build Failed with exit code {result.returncode}")
        sys.exit(result.returncode)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build Nexus File Manager")
    parser.add_argument("--onefile", action="store_true", help="Build single standalone .exe")
    args = parser.parse_args()
    build_app(onefile=args.onefile)
