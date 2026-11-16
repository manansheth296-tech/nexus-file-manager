"""Real filesystem backend for Nexus File Manager: connects real OS files, drives, and tools."""

from __future__ import annotations

import os
import sys
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from PyQt6.QtCore import QObject, pyqtSignal

from nexus.core.backend import BackendHooks
from nexus.core import mock_data
from nexus.tokens.file_types import file_type_for, EXTENSION_TO_FILE_TYPE


def treemap_category_for(ext: str) -> str:
    """Map file extension to treemap category (video, image, code, archive, document, audio, other)."""
    clean_ext = ext.lstrip(".").lower()
    ftype = EXTENSION_TO_FILE_TYPE.get(clean_ext)
    if ftype in ("word", "excel", "powerpoint", "pdf"):
        return "document"
    if ftype in ("video", "image", "code", "archive", "audio"):
        return ftype
    return "other"


class RealBackend(BackendHooks):
    """Production backend connecting the Nexus UI to real OS files and storage."""

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__()
        if parent:
            self.setParent(parent)

    def get_drives(self) -> list[dict]:
        """Query real mounted system partitions with usage and volume names."""
        import psutil
        drives = []
        try:
            partitions = psutil.disk_partitions(all=False)
            for part in partitions:
                if not part.fstype:
                    continue
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    label = part.mountpoint
                    if sys.platform.startswith("win"):
                        try:
                            import ctypes
                            buf = ctypes.create_unicode_buffer(1024)
                            ctypes.windll.kernel32.GetVolumeInformationW(
                                part.mountpoint, buf, 1024, None, None, None, None, 0
                            )
                            vol = buf.value.strip()
                            letter = part.mountpoint.rstrip("\\")
                            label = f"{vol} ({letter})" if vol else f"Local Disk ({letter})"
                        except Exception:
                            label = part.mountpoint
                    drives.append({
                        "label": label,
                        "path": part.mountpoint,
                        "used": usage.used,
                        "total": usage.total,
                    })
                except (PermissionError, OSError):
                    continue
        except Exception as e:
            print(f"Error querying partitions: {e}", file=sys.stderr)
        return drives or mock_data.DRIVES

    def get_quick_access(self) -> list[tuple[str, str, str | None, str]]:
        """Return real user locations (Home, Desktop, Documents, Downloads, etc.)."""
        home = Path.home()
        candidates = [
            ("Home", "home", home),
            ("Desktop", "monitor", home / "Desktop"),
            ("Documents", "file-text", home / "Documents"),
            ("Downloads", "download", home / "Downloads"),
            ("Pictures", "image", home / "Pictures"),
            ("Videos", "video", home / "Videos"),
            ("Music", "music", home / "Music"),
        ]
        qa = []
        for label, icon, p in candidates:
            if p.exists() and p.is_dir():
                qa.append((label, icon, None, str(p)))
        return qa or mock_data.QUICK_ACCESS

    def list_directory(self, path: str) -> list[dict]:
        """Read real directory contents or fallback to mock data if path doesn't exist."""
        p = Path(path)
        if not p.exists() or not p.is_dir():
            # If path doesn't exist on disk (e.g. mock test path), fallback cleanly to mock data
            return mock_data.MOCK_FILES

        items = []
        try:
            with os.scandir(p) as it:
                for entry in it:
                    try:
                        is_dir = entry.is_dir(follow_symlinks=False)
                        stat = entry.stat(follow_symlinks=False)
                        mtime = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                        
                        if is_dir:
                            kind = "folder"
                            type_str = "Folder"
                            size = None
                        else:
                            kind = file_type_for(entry.name) or "binary"
                            ext = Path(entry.name).suffix.lower()
                            type_str = ext[1:].upper() + " File" if ext else "File"
                            size = stat.st_size

                        items.append({
                            "name": entry.name,
                            "size": size,
                            "type": type_str,
                            "modified": mtime,
                            "kind": kind,
                            "path": entry.path,
                        })
                    except (PermissionError, OSError):
                        continue
        except (PermissionError, OSError) as e:
            print(f"Error reading directory {path}: {e}", file=sys.stderr)
            return []

        # Sort: folders first, then alphabetical
        items.sort(key=lambda x: (0 if x["kind"] == "folder" else 1, x["name"].lower()))
        return items

    def scan_storage_tree(self, root_path: str, max_depth: int = 3) -> dict:
        """Scan real folder and build nested tree for Storage Doctor squarified treemap."""
        p = Path(root_path)
        if not p.exists() or not p.is_dir():
            return mock_data.MOCK_STORAGE_TREE

        def _scan(curr_p: Path, depth: int) -> dict:
            children = []
            total_size = 0
            try:
                with os.scandir(curr_p) as it:
                    for entry in it:
                        try:
                            if entry.is_dir(follow_symlinks=False):
                                if depth < max_depth:
                                    child_tree = _scan(Path(entry.path), depth + 1)
                                    children.append(child_tree)
                                    total_size += child_tree.get("size", 0)
                                else:
                                    # Fast size approximation
                                    folder_sz = sum(
                                        f.stat().st_size
                                        for root, _, files in os.walk(entry.path)
                                        for f in (Path(root) / fn for fn in files)
                                        if f.is_file()
                                    )
                                    children.append({
                                        "name": entry.name,
                                        "size": folder_sz,
                                        "category": "folder",
                                        "children": [],
                                    })
                                    total_size += folder_sz
                            else:
                                sz = entry.stat().st_size
                                ext = Path(entry.name).suffix
                                cat = treemap_category_for(ext)
                                children.append({
                                    "name": entry.name,
                                    "size": sz,
                                    "category": cat,
                                })
                                total_size += sz
                        except (PermissionError, OSError):
                            continue
            except (PermissionError, OSError):
                pass

            children.sort(key=lambda c: c.get("size", 0), reverse=True)
            return {
                "name": curr_p.name or str(curr_p),
                "size": total_size,
                "category": "folder",
                "children": children,
                "path": str(curr_p),
            }

        res = _scan(p, depth=0)
        res["base_path"] = str(p)
        return res

    def open_file(self, file_path: str) -> None:
        """Open file using the host operating system's default handler."""
        p = Path(file_path)
        if not p.exists():
            return
        try:
            if sys.platform.startswith("win"):
                os.startfile(str(p))
            elif sys.platform == "darwin":
                import subprocess
                subprocess.Popen(["open", str(p)])
            else:
                import subprocess
                subprocess.Popen(["xdg-open", str(p)])
        except Exception as e:
            print(f"Failed to open {file_path}: {e}", file=sys.stderr)
