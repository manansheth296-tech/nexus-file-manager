"""Configuration and helper utilities for Nexus File Manager."""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple

APP_NAME = "Nexus File Manager"
APP_VERSION = "1.1.0"

# Application storage directory in user profile
APP_DIR = Path.home() / ".nexus_file_manager"
APP_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_FILE = APP_DIR / "config.json"
VAULT_INDEX_FILE = APP_DIR / "vaults.json"

DEFAULT_CONFIG: Dict[str, Any] = {
    "theme": "midnight_cyber",
    "show_hidden": False,
    "last_path": str(Path.home()),
    "bookmarks": [
        {"name": "Home", "path": str(Path.home()), "icon": "fa5s.home"},
        {"name": "Desktop", "path": str(Path.home() / "Desktop"), "icon": "fa5s.desktop"},
        {"name": "Downloads", "path": str(Path.home() / "Downloads"), "icon": "fa5s.download"},
        {"name": "Documents", "path": str(Path.home() / "Documents"), "icon": "fa5s.file-alt"},
        {"name": "Pictures", "path": str(Path.home() / "Pictures"), "icon": "fa5s.images"},
        {"name": "Music", "path": str(Path.home() / "Music"), "icon": "fa5s.music"},
        {"name": "Videos", "path": str(Path.home() / "Videos"), "icon": "fa5s.video"},
    ],
    "default_view": "details",  # 'details' or 'grid'
    "preview_panel_visible": True,
}

# Comprehensive file extension categories
FILE_CATEGORIES = {
    "word": {".doc", ".docx", ".dotx", ".odt", ".rtf"},
    "excel": {".xls", ".xlsx", ".xlsm", ".csv", ".tsv", ".ods"},
    "powerpoint": {".ppt", ".pptx", ".ppsx", ".odp"},
    "pdf": {".pdf"},
    "images": {
        ".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp", ".ico", ".tiff",
        ".tif", ".svg", ".psd", ".ai", ".eps", ".raw", ".cr2", ".nef"
    },
    "documents": {".txt", ".md", ".rtf", ".log", ".tex", ".nfo", ".ini", ".cfg", ".conf", ".env"},
    "code": {
        ".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".htm", ".css", ".scss",
        ".sass", ".less", ".json", ".xml", ".yaml", ".yml", ".c", ".cpp", ".cc",
        ".cxx", ".h", ".hpp", ".hxx", ".rs", ".go", ".java", ".kt", ".cs", ".php",
        ".rb", ".sh", ".bash", ".zsh", ".bat", ".cmd", ".ps1", ".sql", ".dart",
        ".swift", ".lua", ".r", ".asm"
    },
    "archives": {".zip", ".tar", ".gz", ".bz2", ".xz", ".7z", ".rar", ".iso", ".dmg", ".cab"},
    "audio": {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".wma", ".mid", ".midi", ".opus"},
    "video": {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".webm", ".flv", ".m4v", ".3gp", ".ts"},
    "binaries": {".exe", ".msi", ".dll", ".sys", ".bin", ".dat", ".apk", ".deb", ".rpm"},
}


def load_config() -> Dict[str, Any]:
    """Load configuration from disk, falling back to defaults."""
    if not CONFIG_FILE.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            for k, v in DEFAULT_CONFIG.items():
                if k not in data:
                    data[k] = v
            return data
    except Exception:
        return DEFAULT_CONFIG.copy()


def save_config(config: Dict[str, Any]) -> None:
    """Save configuration to disk."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"Error saving config: {e}", file=sys.stderr)


def format_size(size_bytes: int) -> str:
    """Convert bytes to a human-readable string (e.g. 14.2 MB)."""
    if size_bytes < 0:
        return "0 B"
    for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
        if size_bytes < 1024.0 or unit == "PB":
            if unit == "B":
                return f"{int(size_bytes)} B"
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def get_file_icon_info(path: Path) -> Tuple[str, str]:
    """Return (icon_name, hex_color) for any file or folder."""
    if path.is_dir():
        return ("fa5s.folder", "#EAB308")  # Warm Amber

    ext = path.suffix.lower()

    # Microsoft Office / Docs
    if ext in FILE_CATEGORIES["word"]:
        return ("fa5s.file-word", "#2B579A")  # Word Blue
    if ext in FILE_CATEGORIES["excel"]:
        return ("fa5s.file-excel", "#217346")  # Excel Green
    if ext in FILE_CATEGORIES["powerpoint"]:
        return ("fa5s.file-powerpoint", "#D24726")  # PPT Orange-Red
    if ext in FILE_CATEGORIES["pdf"]:
        return ("fa5s.file-pdf", "#EF4444")  # PDF Red

    # Media
    if ext in FILE_CATEGORIES["images"]:
        if ext in {".psd", ".ai", ".eps"}:
            return ("fa5s.paint-brush", "#06B6D4")  # Paint Cyan
        return ("fa5s.file-image", "#10B981")  # Emerald Green
    if ext in FILE_CATEGORIES["audio"]:
        return ("fa5s.file-audio", "#8B5CF6")  # Violet
    if ext in FILE_CATEGORIES["video"]:
        return ("fa5s.file-video", "#A855F7")  # Purple

    # Code & Tech
    if ext in FILE_CATEGORIES["code"]:
        return ("fa5s.file-code", "#38BDF8")  # Electric Sky Blue
    if ext in FILE_CATEGORIES["archives"]:
        return ("fa5s.file-archive", "#F59E0B")  # Amber
    if ext in FILE_CATEGORIES["binaries"]:
        return ("fa5s.cogs", "#94A3B8")  # Slate

    # Text / Docs
    if ext in FILE_CATEGORIES["documents"]:
        return ("fa5s.file-alt", "#CBD5E1")

    # Vault
    if ext == ".vault":
        return ("fa5s.shield-alt", "#EAB308")

    return ("fa5s.file", "#94A3B8")


def get_file_icon_name(path: Path) -> str:
    """Backward compatibility helper."""
    return get_file_icon_info(path)[0]
