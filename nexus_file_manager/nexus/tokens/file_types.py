"""File-type accent colours [spec §3 'File Type Accent Colors'] + icon/extension maps."""
from __future__ import annotations

FILE_COLOR_WORD = "#2563EB"
FILE_COLOR_EXCEL = "#16A34A"
FILE_COLOR_POWERPOINT = "#EA580C"
FILE_COLOR_PDF = "#EF4444"
FILE_COLOR_IMAGE = "#10B981"
FILE_COLOR_CODE = "#38BDF8"
FILE_COLOR_ARCHIVE = "#F59E0B"
FILE_COLOR_AUDIO = "#8B5CF6"
FILE_COLOR_VIDEO = "#A855F7"

FILE_TYPE_COLORS: dict[str, str] = {
    "word": FILE_COLOR_WORD, "excel": FILE_COLOR_EXCEL, "powerpoint": FILE_COLOR_POWERPOINT,
    "pdf": FILE_COLOR_PDF, "image": FILE_COLOR_IMAGE, "code": FILE_COLOR_CODE,
    "archive": FILE_COLOR_ARCHIVE, "audio": FILE_COLOR_AUDIO, "video": FILE_COLOR_VIDEO,
}

# Which SVG in assets/icons represents each type [assumed]
FILE_TYPE_ICONS: dict[str, str] = {
    "word": "file-text", "excel": "table", "powerpoint": "layout", "pdf": "file-text",
    "image": "image", "code": "code", "archive": "archive", "audio": "music",
    "video": "video",
}

EXTENSION_TO_FILE_TYPE: dict[str, str] = {
    **dict.fromkeys(("docx", "doc", "odt", "rtf"), "word"),
    **dict.fromkeys(("xlsx", "xls", "csv", "ods"), "excel"),
    **dict.fromkeys(("pptx", "ppt", "odp", "key"), "powerpoint"),
    "pdf": "pdf",
    **dict.fromkeys(("png", "jpg", "jpeg", "gif", "webp", "svg", "psd", "bmp"), "image"),
    **dict.fromkeys(("py", "js", "ts", "html", "css", "json", "cpp", "c", "rs", "go", "sh", "java"), "code"),
    **dict.fromkeys(("zip", "tar", "gz", "7z", "rar"), "archive"),
    **dict.fromkeys(("mp3", "wav", "flac", "ogg", "m4a"), "audio"),
    **dict.fromkeys(("mp4", "mkv", "mov", "avi", "webm"), "video"),
}


def file_type_for(filename: str) -> str | None:
    """-> 'word' | 'excel' | ... | None (unknown / generic)."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return EXTENSION_TO_FILE_TYPE.get(ext)


# ── Treemap categories [spec Screen 4] ──────────────────────────────────────
# Spec: Video=Purple, Images=Green, Code=Blue, Archives=Amber, Documents=Yellow.
# 'Documents = Yellow' has no counterpart in the file-type table, so this one is [assumed].
FILE_COLOR_DOCUMENT_YELLOW = "#EAB308"

TREEMAP_CATEGORY_COLORS: dict[str, str] = {
    "video": FILE_COLOR_VIDEO,
    "image": FILE_COLOR_IMAGE,
    "code": FILE_COLOR_CODE,
    "archive": FILE_COLOR_ARCHIVE,
    "document": FILE_COLOR_DOCUMENT_YELLOW,
    "audio": FILE_COLOR_AUDIO,          # [assumed] not listed in the spec's treemap legend
    "other": "COLOR_TEXT_MUTED",        # token name – resolved per theme
}
TREEMAP_CATEGORY_LABELS: dict[str, str] = {
    "video": "Video", "image": "Images", "code": "Code", "archive": "Archives",
    "document": "Documents", "audio": "Audio", "other": "Other",
}
KIND_TO_TREEMAP_CATEGORY: dict[str, str] = {
    "word": "document", "excel": "document", "powerpoint": "document", "pdf": "document",
    "image": "image", "code": "code", "archive": "archive", "audio": "audio", "video": "video",
}


def kind_color(kind: str) -> str:
    """Accent for a file kind: a hex, or a theme token name (resolve with resolve_color)."""
    return FILE_TYPE_COLORS.get(kind) or {"folder": "COLOR_ACCENT_SECONDARY"}.get(kind, "COLOR_TEXT_SECONDARY")


def kind_icon(kind: str) -> str:
    return FILE_TYPE_ICONS.get(kind) or ("folder" if kind == "folder" else "file")


# Category tags used by the AI Organizer [assumed mapping; spec names the four tags, not their colours]
CATEGORY_TAG_COLORS: dict[str, str] = {
    "#finance": "COLOR_SUCCESS", "#academic": "COLOR_ACCENT_SECONDARY",
    "#media": "COLOR_WARNING", "#code": "COLOR_ACCENT_PRIMARY",
}
