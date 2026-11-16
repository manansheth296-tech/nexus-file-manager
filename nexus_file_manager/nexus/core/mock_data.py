"""Placeholder data for UI development. Replace via core/backend.py hooks."""
from __future__ import annotations

from nexus.tokens.file_types import (FILE_COLOR_AUDIO, FILE_COLOR_IMAGE, FILE_COLOR_POWERPOINT,
                                     FILE_COLOR_VIDEO, FILE_COLOR_WORD)

KB, MB, GB = 1024, 1024 ** 2, 1024 ** 3


def format_size(n: int | float | None) -> str:
    if n is None:
        return "—"
    size = float(n)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{n} B"


def _file(name, size, type_, modified, kind):
    return {"name": name, "size": size, "type": type_, "modified": modified, "kind": kind}


# kind -> key into tokens.file_types ('folder' / 'binary' have no spec accent)
MOCK_FILES: list[dict] = [
    _file("Projects", None, "Folder", "2026-11-10 09:41", "folder"),
    _file("Documents", None, "Folder", "2026-11-09 17:20", "folder"),
    _file("Pictures", None, "Folder", "2026-11-04 12:02", "folder"),
    _file("Downloads", None, "Folder", "2026-11-11 08:15", "folder"),
    _file("Q3 Financial Report.docx", 245_000, "Word Document", "2026-11-09 14:22", "word"),
    _file("Meeting Notes.docx", 58_000, "Word Document", "2026-11-07 10:05", "word"),
    _file("Budget 2026.xlsx", 1_200_000, "Spreadsheet", "2026-11-08 18:05", "excel"),
    _file("expenses.csv", 88_000, "CSV File", "2026-11-01 09:30", "excel"),
    _file("Pitch Deck v4.pptx", 18_400_000, "Presentation", "2026-11-06 11:30", "powerpoint"),
    _file("Syllabus.pdf", 1_200_000, "PDF Document", "2026-10-30 15:44", "pdf"),
    _file("invoice_0042.pdf", 340_000, "PDF Document", "2026-11-05 16:12", "pdf"),
    _file("hero-banner.png", 2_100_000, "PNG Image", "2026-11-03 10:48", "image"),
    _file("team-photo.jpg", 3_400_000, "JPEG Image", "2026-10-27 19:21", "image"),
    _file("logo.svg", 14_000, "SVG Image", "2026-10-12 13:00", "image"),
    _file("main.py", 4_200, "Python Script", "2026-11-02 21:17", "code"),
    _file("app.js", 12_800, "JavaScript", "2026-10-29 22:40", "code"),
    _file("backups.zip", 512_000_000, "ZIP Archive", "2026-10-28 08:00", "archive"),
    _file("assets.tar", 96_000_000, "TAR Archive", "2026-10-18 14:12", "archive"),
    _file("podcast_ep12.mp3", 48_000_000, "MP3 Audio", "2026-10-21 19:33", "audio"),
    _file("voice-memo.wav", 22_000_000, "WAV Audio", "2026-10-09 07:58", "audio"),
    _file("demo_reel.mp4", 1_450_000_000, "MP4 Video", "2026-10-14 13:09", "video"),
    _file("lecture_05.mkv", 880_000_000, "MKV Video", "2026-10-02 11:11", "video"),
    _file("setup.exe", 3_800_000, "Application", "2026-09-30 09:09", "binary"),
    _file("firmware.bin", 131_072, "Binary File", "2026-09-22 16:35", "binary"),
]

START_PATH = "C:\\Users\\User\\Projects"

# (label, icon, badge colour (hex or token name), path)
QUICK_ACCESS = [
    ("Home", "home", "COLOR_ACCENT_PRIMARY", "C:\\Users\\User"),
    ("Desktop", "monitor", "COLOR_ACCENT_SECONDARY", "C:\\Users\\User\\Desktop"),
    ("Downloads", "download", "COLOR_SUCCESS", "C:\\Users\\User\\Downloads"),
    ("Documents", "file-text", FILE_COLOR_WORD, "C:\\Users\\User\\Documents"),
    ("Pictures", "image", FILE_COLOR_POWERPOINT, "C:\\Users\\User\\Pictures"),
    ("Music", "music", FILE_COLOR_AUDIO, "C:\\Users\\User\\Music"),
    ("Videos", "video", FILE_COLOR_VIDEO, "C:\\Users\\User\\Videos"),
]

DRIVES = [
    {"label": "Local Disk (C:)", "path": "C:\\", "used": 412_000_000_000, "total": 500_107_862_016},   # warn
    {"label": "Data (D:)", "path": "D:\\", "used": 320_000_000_000, "total": 1_000_204_886_016},        # ok
    {"label": "Backup (E:)", "path": "E:\\", "used": 241_000_000_000, "total": 256_000_000_000},        # danger
]

# (label, icon, key)
TOOLS = [
    ("Storage Doctor", "pie-chart", "storage_doctor"),
    ("Duplicate Hunter", "copy", "duplicate_hunter"),
    ("AI Organizer", "zap", "ai_organizer"),
    ("Encrypted Vault", "shield", "encrypted_vault"),
]

# ── Inspector previews (Phase 3) ────────────────────────────────────────────
WORD_PREVIEW = {
    "title": "Q3 Financial Report",
    "words": 1284,
    "paragraphs": [
        "Revenue grew 12% quarter over quarter, driven primarily by subscription renewals and a strong September.",
        "Operating expenses held flat as hiring was paused in the second half of the quarter.",
        "Outlook: we expect Q4 growth to moderate to 6–8% as seasonal demand softens.",
    ],
}
SHEET_PREVIEW = {
    "columns": ["A", "B", "C", "D", "E"],
    "rows": [
        ["Region", "Q1", "Q2", "Q3", "Q4"],
        ["North", "124", "131", "148", "162"],
        ["South", "98", "104", "101", "119"],
        ["East", "143", "150", "166", "171"],
        ["West", "87", "92", "99", "108"],
        ["Total", "452", "477", "514", "560"],
        ["Growth", "—", "5.5%", "7.8%", "8.9%"],
    ],
}
IMAGE_PREVIEW = {"width": 1920, "height": 1080}
PDF_PREVIEW = {"pages": 12}
# (depth, name, size) – size None = folder
ARCHIVE_PREVIEW = [
    (0, "backups", None),
    (1, "documents", None),
    (2, "report-q3.docx", 245_000),
    (2, "budget.xlsx", 1_200_000),
    (1, "photos", None),
    (2, "team-photo.jpg", 3_400_000),
    (2, "hero-banner.png", 2_100_000),
    (1, "notes.txt", 4_100),
    (0, "README.md", 1_800),
]
MEDIA_PREVIEW = {
    "audio": [("Duration", "42:18"), ("Codec", "MP3 · 192 kbps"), ("Sample rate", "44.1 kHz"), ("Channels", "Stereo")],
    "video": [("Duration", "03:24"), ("Codec", "H.264 · AAC"), ("Resolution", "1920 × 1080"), ("Frame rate", "30 fps")],
}


def mock_hex_bytes(n: int = 96) -> bytes:
    head = bytes([0x4D, 0x5A, 0x90, 0x00, 0x03, 0x00, 0x00, 0x00, 0x04, 0x00, 0x00, 0x00, 0xFF, 0xFF, 0x00, 0x00,
                  0xB8, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x40, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
    msg = b"This program cannot be run in DOS mode.\r\r\n$"
    return (head + msg + bytes((i * 37 + 11) % 256 for i in range(n)))[:n]


# ── Storage Doctor tree (Phase 4) ───────────────────────────────────────────
def _leaf(name: str, size: float, category: str) -> dict:
    return {"name": name, "size": int(size), "category": category}


def _dir(name: str, *children: dict) -> dict:
    return {"name": name, "children": list(children)}


MOCK_STORAGE_TREE = _dir(
    "User",
    _dir("Videos",
         _leaf("demo_reel.mp4", 14.2 * GB, "video"), _leaf("conference_2026.mkv", 9.8 * GB, "video"),
         _leaf("raw_footage.mov", 6.1 * GB, "video"), _leaf("trailer.mp4", 1.9 * GB, "video"),
         _dir("Lectures", *[_leaf(f"lecture_{i:02d}.mkv", (0.8 + (i * 3 % 5) * 0.15) * GB, "video") for i in range(1, 9)])),
    _dir("Pictures",
         _dir("Camera Roll", *[_leaf(f"IMG_{4100 + i}.cr2", (24 + (i * 7 % 6) * 6) * MB, "image") for i in range(24)]),
         _dir("Screenshots", *[_leaf(f"shot_{i:03d}.png", (2 + i % 4) * MB, "image") for i in range(30)]),
         _leaf("wallpapers.zip", 1.2 * GB, "archive")),
    _dir("Projects",
         _dir("nexus-ui", _leaf("venv", 1.8 * GB, "code"), _leaf("src", 120 * MB, "code"), _leaf("assets", 640 * MB, "image")),
         _dir("game-engine", _leaf("build", 2.6 * GB, "code"), _leaf("src", 310 * MB, "code"), _leaf("textures.pak", 1.4 * GB, "image")),
         _leaf("dataset.csv", 3.4 * GB, "document")),
    _dir("Downloads",
         _leaf("ubuntu-24.04.iso", 5.8 * GB, "archive"), _leaf("installers.zip", 3.1 * GB, "archive"),
         _leaf("backups_2025.tar", 7.4 * GB, "archive"), _leaf("setup.exe", 0.4 * GB, "other")),
    _dir("Documents",
         _leaf("Thesis.pdf", 48 * MB, "document"), _leaf("Budget 2026.xlsx", 1.2 * MB, "document"),
         _dir("Reports", *[_leaf(f"report_{i:02d}.docx", (4 + i % 5) * MB, "document") for i in range(1, 10)]),
         _dir("Scans", *[_leaf(f"scan_{i:03d}.pdf", (18 + i % 7 * 4) * MB, "document") for i in range(1, 16)])),
    _dir("Music", *[_leaf(f"track_{i:02d}.mp3", (6 + i % 5) * MB, "audio") for i in range(1, 40)]),
    _leaf("hiberfil.sys", 6.4 * GB, "other"),
)


# ── Phase 5 mock data ───────────────────────────────────────────────────────
def _dup(name: str, size: float, *copies: tuple[str, str]) -> dict:
    return {"name": name, "size": int(size), "copies": [{"path": p, "modified": m} for p, m in copies]}


MOCK_DUPLICATES = [
    _dup("IMG_4112.cr2", 31.2 * MB,
         ("C:\\Users\\User\\Pictures\\Camera Roll\\IMG_4112.cr2", "2026-09-14 18:22"),
         ("C:\\Users\\User\\Downloads\\IMG_4112.cr2", "2026-10-02 09:10"),
         ("E:\\Backup\\Photos\\2026\\IMG_4112.cr2", "2026-09-15 02:00")),
    _dup("ubuntu-24.04.iso", 5.8 * GB,
         ("C:\\Users\\User\\Downloads\\ubuntu-24.04.iso", "2026-08-21 20:14"),
         ("D:\\ISOs\\ubuntu-24.04.iso", "2026-08-22 08:31")),
    _dup("Thesis_final.pdf", 48 * MB,
         ("C:\\Users\\User\\Documents\\Thesis_final.pdf", "2026-10-30 22:05"),
         ("C:\\Users\\User\\Desktop\\Thesis_final.pdf", "2026-10-30 22:07"),
         ("E:\\Backup\\Documents\\Thesis_final.pdf", "2026-10-31 02:00")),
    _dup("demo_reel.mp4", 1.4 * GB,
         ("C:\\Users\\User\\Videos\\demo_reel.mp4", "2026-10-14 13:09"),
         ("D:\\Exports\\demo_reel.mp4", "2026-10-14 13:41")),
    _dup("podcast_ep12.mp3", 45.8 * MB,
         ("C:\\Users\\User\\Music\\podcast_ep12.mp3", "2026-10-21 19:33"),
         ("C:\\Users\\User\\Downloads\\podcast_ep12 (1).mp3", "2026-10-21 19:40")),
    _dup("budget.xlsx", 1.2 * MB,
         ("C:\\Users\\User\\Documents\\Finance\\budget.xlsx", "2026-11-08 18:05"),
         ("C:\\Users\\User\\Documents\\budget.xlsx", "2026-10-02 11:48"),
         ("C:\\Users\\User\\Desktop\\budget.xlsx", "2026-09-19 16:20"),
         ("E:\\Backup\\Documents\\budget.xlsx", "2026-11-01 02:00")),
]

# (original, proposed, #tag, confidence 0..1, kind)
MOCK_ORGANIZER = [
    ("scan0042.pdf", "Electricity Bill – Oct 2026.pdf", "#finance", 0.96, "pdf"),
    ("final_FINAL_v2.xlsx", "Budget 2026.xlsx", "#finance", 0.94, "excel"),
    ("Untitled document (3).docx", "Thermodynamics Lecture Notes.docx", "#academic", 0.91, "word"),
    ("IMG_20261003_184422.jpg", "2026-10-03 Camera Roll 4422.jpg", "#media", 0.97, "image"),
    ("script_new_copy.py", "backup_scheduler.py", "#code", 0.92, "code"),
    ("download (12).png", "Dashboard Mockup.png", "#media", 0.78, "image"),
    ("WhatsApp Image 2026-10-21.jpeg", "Whiteboard Notes 2026-10-21.jpeg", "#academic", 0.66, "image"),
    ("invoice (1).pdf", "Invoice 0042 – Studio Rental.pdf", "#finance", 0.89, "pdf"),
    ("sem5_syllabus_scan.pdf", "Semester 5 Syllabus.pdf", "#academic", 0.93, "pdf"),
    ("main_old2.py", "dataset_loader.py", "#code", 0.71, "code"),
    ("VID_0098.mp4", "Lab Demo Recording 2026-09-30.mp4", "#media", 0.84, "video"),
    ("new 4.docx", "Project Proposal Draft.docx", "#academic", 0.58, "word"),
]


# name -> (author, downloads, one-line blurb) for the Theme Store
THEME_META = {
    "Midnight Cyber": ("Nexus", "", "The default dark theme"),
    "Daylight Slate (demo)": ("Nexus", "", "Clean light variant"),
    "Nord Frost": ("Arctic Ice Studio", "", "Cool, calm blues"),
    "Forest Night": ("Community", "", "Deep green dark"),
    "Cyberpunk Neon": ("neon_wolf", "12.4k", "Magenta and cyan glow"),
    "macOS Glass": ("glassworks", "28.1k", "Light, airy, rounder corners"),
    "Windows 95 Retro": ("retro_club", "9.7k", "Flat grey, square corners"),
}
