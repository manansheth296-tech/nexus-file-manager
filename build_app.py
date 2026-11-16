"""
Build and package Nexus File Manager into standalone executables (.exe):
1. onedir distribution: dist/NexusFileManager/ (for installer packaging)
2. onefile standalone: dist/Nexus.exe (single portable .exe to send directly to friends)
"""

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


def build_app(onefile: bool = False, app_name: str | None = None):
    target_name = app_name or ("Nexus" if onefile else "NexusFileManager")
    mode_str = "Single-File Portable Executable" if onefile else "Directory Distribution"

    print("=" * 65)
    print(f"[*] Packaging Nexus File Manager: {mode_str} ({target_name}.exe)")
    print("=" * 65)

    # Ensure icon exists
    if not ICON_PATH.exists():
        from create_icon import create_nexus_icon
        create_nexus_icon()

    nexus_dir = ROOT_DIR / "nexus_file_manager"
    icons_dir = nexus_dir / "nexus" / "assets" / "icons"

    # PyInstaller arguments
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        f"--name={target_name}",
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
        "--hidden-import=win32api",
        str(ROOT_DIR / "run.py"),
    ]

    if onefile:
        cmd.append("--onefile")
    else:
        cmd.append("--onedir")

    print("[*] Running PyInstaller...")
    result = subprocess.run(cmd)

    if result.returncode == 0:
        print("\n" + "=" * 65)
        print("[+] Build Completed Successfully!")
        if onefile:
            exe_path = DIST_DIR / f"{target_name}.exe"
            print(f"[+] Portable Single-File Executable: {exe_path}")
        else:
            exe_path = DIST_DIR / target_name / f"{target_name}.exe"
            print(f"[+] Application Directory: {DIST_DIR / target_name}")
            print(f"[+] Executable: {exe_path}")
        print("=" * 65)
        return exe_path
    else:
        print(f"\n[-] Build Failed with exit code {result.returncode}")
        sys.exit(result.returncode)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build Nexus File Manager")
    parser.add_argument("--onefile", action="store_true", help="Build single standalone portable .exe")
    parser.add_argument("--both", action="store_true", help="Build both onedir and portable onefile")
    args = parser.parse_args()

    if args.both:
        build_app(onefile=False)
        build_app(onefile=True)
    else:
        build_app(onefile=args.onefile)
