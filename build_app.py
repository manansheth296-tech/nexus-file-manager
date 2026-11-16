"""Build and package Nexus File Manager into a standalone desktop application (.exe)."""

import sys
import subprocess
import shutil
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
DIST_DIR = ROOT_DIR / "dist"
BUILD_DIR = ROOT_DIR / "build"
SPEC_FILE = ROOT_DIR / "NexusFileManager.spec"
ICON_PATH = ROOT_DIR / "assets" / "icon.ico"


def build_app(onefile: bool = False):
    print("=" * 60)
    print("[*] Packaging Nexus File Manager as Standalone Executable")
    print("=" * 60)

    # Ensure icon exists
    if not ICON_PATH.exists():
        from create_icon import create_app_icon
        create_app_icon()

    # PyInstaller arguments
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--name=NexusFileManager",
        "--windowed",                 # No console window popup
        "--clean",
        "--noconfirm",
        f"--icon={ICON_PATH}",
        f"--add-data={ROOT_DIR / 'assets'};assets",
        "--collect-all=qtawesome",
        "--collect-all=pymupdf",
        "--collect-all=docx",
        "--collect-all=openpyxl",
        "--hidden-import=qtawesome",
        "--hidden-import=pymupdf",
        "--hidden-import=PIL",
        "--hidden-import=cryptography",
        "--hidden-import=send2trash",
        "--hidden-import=watchdog",
        "--hidden-import=openpyxl",
        "--hidden-import=docx",
        str(ROOT_DIR / "src" / "main.py"),
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


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Build Nexus File Manager")
    parser.add_argument("--onefile", action="store_true", help="Build single standalone .exe")
    args = parser.parse_args()
    build_app(onefile=args.onefile)
