"""
BACKEND HOOK POINTS  ─  UI-only project: nothing here touches the filesystem.

Every feature that will need real logic gets one signal (UI -> backend request)
and one stub method (backend -> UI result). Views connect to these; when the real
backend arrives, subclass `BackendHooks` and override the `# HOOK:` methods –
no view code changes.
"""
from __future__ import annotations

from PyQt6.QtCore import QObject, pyqtSignal

from nexus.core import mock_data


class BackendHooks(QObject):
    # ── UI -> backend requests ────────────────────────────────────────────
    directory_requested = pyqtSignal(str)            # path
    duplicate_scan_requested = pyqtSignal(str)       # root path        (Phase 5)
    organizer_dry_run_requested = pyqtSignal(str)    # root path        (Phase 5)
    vault_action_requested = pyqtSignal(str, str, str, bool)  # mode, path, password, trash_original (Phase 5)
    semantic_search_requested = pyqtSignal(str)      # query            (Phase 5)
    storage_scan_requested = pyqtSignal(str)         # root path        (Phase 4)

    # ── backend -> UI results ─────────────────────────────────────────────
    directory_loaded = pyqtSignal(str, list)         # path, rows
    transfer_progress = pyqtSignal(str, float)       # label, MB/s      (status bar)

    # HOOK: replace with real directory listing
    def list_directory(self, path: str) -> list[dict]:
        return mock_data.MOCK_FILES

    # HOOK: replace with real drive listing
    def get_drives(self) -> list[dict]:
        return mock_data.DRIVES

    # HOOK: replace with real quick-access locations
    def get_quick_access(self) -> list[tuple[str, str, str | None, str]]:
        return mock_data.QUICK_ACCESS

    # HOOK: replace with real hashing pipeline (size -> 4KB header -> SHA-256)
    def scan_duplicates(self, root: str) -> list[dict]:
        raise NotImplementedError("Phase 5 – duplicate hunter backend")

    # HOOK: replace with real encryption (zero-knowledge)
    def vault_apply(self, mode: str, path: str, password: str, trash_original: bool) -> None:
        raise NotImplementedError("Phase 5 – vault backend")
