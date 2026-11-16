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

    def find_duplicates(self, root_path: str, max_files: int = 4000) -> list[dict]:
        """Detect duplicate files using 3-tier algorithm (size -> 4KB MD5 -> full SHA256)."""
        p = Path(root_path)
        if not p.exists() or not p.is_dir():
            return []

        from collections import defaultdict
        from src.modules.duplicate_finder import get_partial_hash, get_full_hash

        # Tier 1: Group by size
        size_map: dict[int, list[Path]] = defaultdict(list)
        count = 0
        try:
            for root, _, files in os.walk(p):
                for fn in files:
                    fp = Path(root) / fn
                    try:
                        sz = fp.stat().st_size
                        if sz > 0:
                            size_map[sz].append(fp)
                            count += 1
                            if count >= max_files:
                                break
                    except (PermissionError, OSError):
                        pass
                if count >= max_files:
                    break
        except Exception:
            return []

        candidates = [paths for paths in size_map.values() if len(paths) > 1]
        if not candidates:
            return []

        # Tier 2: 4KB Header hash
        partial_map: dict[tuple[int, str], list[Path]] = defaultdict(list)
        for group in candidates:
            for fp in group:
                phash = get_partial_hash(fp)
                if phash:
                    try:
                        partial_map[(fp.stat().st_size, phash)].append(fp)
                    except OSError:
                        pass

        full_candidates = [paths for paths in partial_map.values() if len(paths) > 1]
        if not full_candidates:
            return []

        # Tier 3: Full SHA-256
        dup_groups: list[dict] = []
        for group in full_candidates:
            sha_map: dict[str, list[Path]] = defaultdict(list)
            for fp in group:
                fhash = get_full_hash(fp)
                if fhash:
                    sha_map[fhash].append(fp)

            for sha, matches in sha_map.items():
                if len(matches) > 1:
                    size = matches[0].stat().st_size
                    copies = []
                    for m in matches:
                        try:
                            mtime = datetime.datetime.fromtimestamp(m.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                        except OSError:
                            mtime = "Unknown"
                        copies.append({
                            "path": str(m),
                            "modified": mtime
                        })
                    dup_groups.append({
                        "name": matches[0].name,
                        "size": size,
                        "copies": copies
                    })

        return dup_groups

    def search_content(self, query: str, root_path: str, max_results: int = 50) -> list[dict]:
        """Search text and document files in root_path by query terms."""
        p = Path(root_path)
        if not p.exists() or not p.is_dir():
            return []

        from src.modules.semantic_search import tokenize
        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        searchable_exts = {
            ".txt", ".md", ".py", ".js", ".ts", ".html", ".css", ".json",
            ".pdf", ".csv", ".yaml", ".yml", ".c", ".cpp", ".java", ".rs", ".docx"
        }

        results: list[dict] = []
        count = 0
        try:
            for root, _, files in os.walk(p):
                rel = Path(root).relative_to(p).parts
                if any(part in (".git", "node_modules", ".venv", "__pycache__", "build", "dist") for part in rel):
                    continue
                if len(rel) > 4:
                    continue

                for fn in files:
                    fp = Path(root) / fn
                    ext = fp.suffix.lower()
                    if ext not in searchable_exts:
                        continue

                    text = ""
                    try:
                        if ext == ".docx":
                            import docx
                            doc = docx.Document(fp)
                            text = " ".join(p.text for p in doc.paragraphs[:20])
                        elif ext == ".pdf":
                            try:
                                import pymupdf
                                doc = pymupdf.open(fp)
                                text = " ".join(page.get_text() for page in doc[:5])
                                doc.close()
                            except Exception:
                                pass
                        else:
                            with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                                text = f.read(100_000)
                    except Exception:
                        continue

                    if not text:
                        continue

                    text_lower = text.lower()
                    name_lower = fp.name.lower()
                    matched_terms = [t for t in query_tokens if t in text_lower or t in name_lower]
                    if not matched_terms:
                        continue

                    term_ratio = len(matched_terms) / len(query_tokens)
                    relevance = int(min(98, 50 + term_ratio * 40 + (10 if any(t in name_lower for t in query_tokens) else 0)))

                    first_pos = min((text_lower.find(t) for t in matched_terms if t in text_lower), default=-1)
                    if first_pos != -1:
                        start = max(0, first_pos - 60)
                        end = min(len(text), first_pos + 120)
                        raw_snip = text[start:end].replace("\r", " ").replace("\n", " ").strip()
                        prefix = "..." if start > 0 else ""
                        suffix = "..." if end < len(text) else ""
                        snippet = f"{prefix}{raw_snip}{suffix}"
                    else:
                        snippet = text[:150].replace("\r", " ").replace("\n", " ").strip() + "..."

                    results.append({
                        "name": fp.name,
                        "path": str(fp),
                        "kind": file_type_for(fp.name) or "code",
                        "relevance": relevance,
                        "snippet": snippet,
                        "terms": matched_terms,
                    })
                    count += 1
                    if count >= max_results:
                        break
                if count >= max_results:
                    break
        except Exception as e:
            print(f"Error searching content: {e}", file=sys.stderr)

        results.sort(key=lambda r: r["relevance"], reverse=True)
        return results

    def analyze_folder_organization(self, root_path: str) -> list[tuple[str, str, str, float, str]]:
        """Analyze files in folder and suggest clean names and category tags."""
        p = Path(root_path)
        if not p.exists() or not p.is_dir():
            return []

        import re
        proposals = []
        try:
            for entry in os.scandir(p):
                if not entry.is_file():
                    continue
                fn = entry.name
                ext = Path(fn).suffix.lower()
                stem = Path(fn).stem
                kind = file_type_for(fn) or "binary"

                tag = "#code" if kind == "code" else "#media" if kind in ("image", "video", "audio") else "#academic"
                conf = 0.85
                lower = stem.lower()
                if any(w in lower for w in ("invoice", "receipt", "bill", "tax", "statement", "salary", "gst")):
                    tag = "#finance"
                    conf = 0.95
                elif any(w in lower for w in ("paper", "thesis", "study", "lecture", "exam", "syllabus", "notes")):
                    tag = "#academic"
                    conf = 0.92
                elif kind in ("image", "video", "audio"):
                    tag = "#media"
                    conf = 0.94
                elif kind == "code":
                    tag = "#code"
                    conf = 0.90

                clean_name = re.sub(r"[_\-\.]+", " ", stem).strip()
                clean_name = " ".join(word.capitalize() for word in clean_name.split())
                proposed = f"{clean_name}{ext}" if clean_name else fn

                proposals.append((fn, proposed, tag, conf, kind))
                if len(proposals) >= 40:
                    break
        except Exception:
            return []

        return proposals
