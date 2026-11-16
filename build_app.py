"""
Build and package Nexus File Manager:
1. Fast onedir application distribution: dist/NexusFileManager/ (launches in < 1s)
2. Standalone Windows Setup Installer: dist/NexusSetup.exe (single file to send to friends)
3. Portable ZIP archive: dist/NexusFileManager-Portable.zip (instant-launch zero-install archive)
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


def build_app(onefile: bool = False, app_name: str | None = None) -> Path:
    target_name = app_name or ("Nexus" if onefile else "NexusFileManager")
    mode_str = "Single-File Portable Executable" if onefile else "Directory Distribution"

    print("=" * 70)
    print(f"[*] Packaging Nexus File Manager: {mode_str} ({target_name}.exe)")
    print("=" * 70)

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
        print("\n" + "=" * 70)
        print("[+] Build Completed Successfully!")
        if onefile:
            exe_path = DIST_DIR / f"{target_name}.exe"
            print(f"[+] Portable Single-File Executable: {exe_path}")
        else:
            exe_path = DIST_DIR / target_name / f"{target_name}.exe"
            print(f"[+] Application Directory: {DIST_DIR / target_name}")
            print(f"[+] Executable: {exe_path}")
        print("=" * 70)
        return exe_path
    else:
        print(f"\n[-] Build Failed with exit code {result.returncode}")
        sys.exit(result.returncode)


def build_portable_zip() -> Path:
    app_dir = DIST_DIR / "NexusFileManager"
    if not app_dir.exists():
        print(f"[-] Cannot create zip: {app_dir} does not exist.")
        sys.exit(1)
    zip_path = DIST_DIR / "NexusFileManager-Portable.zip"
    print(f"[*] Packaging portable ZIP archive: {zip_path.name}...")
    shutil.make_archive(str(DIST_DIR / "NexusFileManager-Portable"), "zip", root_dir=str(DIST_DIR), base_dir="NexusFileManager")
    print(f"[+] Portable ZIP Created: {zip_path} ({zip_path.stat().st_size / (1024*1024):.1f} MB)")
    return zip_path


def build_full_release(skip_app: bool = False, make_zip: bool = True):
    print("\n" + "#" * 70)
    print("#  NEXUS FILE MANAGER – OFFICIAL PRODUCTION RELEASE BUILD PIPELINE")
    print("#" * 70 + "\n")

    # Step 1: Build Application Directory (fast < 1s startup)
    if not skip_app or not (DIST_DIR / "NexusFileManager" / "NexusFileManager.exe").exists():
        build_app(onefile=False)

    # Step 2: Build Windows Setup Wizard Installer (single file for users)
    from build_installer import build_installer
    build_installer(rebuild_app=False)

    # Step 3: Package Portable Zero-Install ZIP
    zip_path = None
    if make_zip:
        zip_path = build_portable_zip()

    print("\n" + "=" * 70)
    print("[+] RELEASE BUILD READY FOR DISTRIBUTION!")
    print("=" * 70)
    print(f"  1. [PRIMARY] Windows Installer Wizard:  dist/NexusSetup.exe")
    print(f"     -> Send this single installer to friends/users. Installs in 3s with shortcuts.")
    if zip_path and zip_path.exists():
        print(f"  2. [PORTABLE] Zero-Install Archive:     dist/NexusFileManager-Portable.zip")
        print(f"     -> Unzips and launches instantly with zero install and zero temp decompression lag.")
    print(f"  3. [LOCAL] Application Directory:       dist/NexusFileManager/NexusFileManager.exe")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Nexus File Manager Release Builder")
    parser.add_argument("--installer-only", action="store_true", help="Package NexusSetup.exe using existing app build")
    parser.add_argument("--legacy-onefile", action="store_true", help="Build single-file uncompressing Nexus.exe (slow cold start)")
    parser.add_argument("--no-zip", action="store_true", help="Skip creating portable .zip archive")
    args = parser.parse_args()

    if args.legacy_onefile:
        build_app(onefile=True)
    elif args.installer_only:
        build_full_release(skip_app=True, make_zip=not args.no_zip)
    else:
        build_full_release(skip_app=False, make_zip=not args.no_zip)

