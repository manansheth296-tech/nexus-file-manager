"""
MainWindow – composes TopBar, Sidebar, Explorer / Storage Doctor pages, Preview Inspector, StatusBar,
and launches the modal dialogs (Duplicate Hunter, AI Organizer, Safe Locker, Semantic Search, Theme Store).

Everything backend-facing goes through `BackendHooks` (core/backend.py) or `RealBackend`.
File operations (New Folder, New File, Cut, Copy, Paste, Delete, Rename) interact directly with the OS.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (QDialog, QHBoxLayout, QInputDialog, QMainWindow,
                             QMessageBox, QStackedWidget, QVBoxLayout, QWidget)

from nexus.components import Divider, Scrim
from nexus.core.backend import BackendHooks
from nexus.core.mock_data import START_PATH
from nexus.core.navigation import NavigationHistory, join_path, parent_path, split_path
from nexus.dialogs import (AIOrganizerDialog, DuplicateHunterDialog, SafeLockerDialog, SemanticSearchDialog,
                           ThemeStoreDialog)
from nexus.styles.theme_manager import theme_manager
from nexus.tokens.base import (SHORTCUT_EDIT_PATH, SHORTCUT_FOCUS_SEARCH, WINDOW_DEFAULT_H, WINDOW_DEFAULT_W,
                               WINDOW_MIN_H, WINDOW_MIN_W)
from nexus.views.explorer import ExplorerView
from nexus.views.inspector import PreviewInspector
from nexus.views.sidebar import Sidebar
from nexus.views.status_bar import NexusStatusBar
from nexus.views.storage_doctor import StorageDoctorView
from nexus.views.top_bar import TopBar

MOCK_TRANSFER = True    # DEMO ONLY – animates the status-bar transfer; real data arrives via backend.transfer_progress


class MainWindow(QMainWindow):
    def __init__(self, backend: BackendHooks | None = None, persist: bool = False):
        super().__init__()
        self.setWindowTitle("Nexus File Manager")
        self.resize(WINDOW_DEFAULT_W, WINDOW_DEFAULT_H)
        self.setMinimumSize(WINDOW_MIN_W, WINDOW_MIN_H)
        self._persist = persist
        self.backend = backend or BackendHooks(self)
        is_real = type(self.backend).__name__ == "RealBackend"
        start = str(Path.cwd()) if is_real else START_PATH
        self.history = NavigationHistory(start)
        self._inspector_wanted = True
        self._dialog: QDialog | None = None
        self._clipboard_files: list[str] = []
        self._clipboard_is_cut: bool = False

        self.top = TopBar()
        self.sidebar = Sidebar(backend=self.backend)
        self.explorer = ExplorerView()
        self.storage = StorageDoctorView()
        self.inspector = PreviewInspector()
        self.status = NexusStatusBar()
        self.setStatusBar(self.status)

        self.pages = QStackedWidget()
        self.pages.addWidget(self.explorer)
        self.pages.addWidget(self.storage)

        central = QWidget()
        col = QVBoxLayout(central)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(0)
        col.addWidget(self.top)
        col.addWidget(Divider())
        body = QHBoxLayout()
        body.setSpacing(0)
        body.addWidget(self.sidebar)
        body.addWidget(self.pages, 1)
        body.addWidget(self.inspector)
        col.addLayout(body, 1)
        self.setCentralWidget(central)
        self.scrim = Scrim(self)

        self._wire()
        QShortcut(QKeySequence(SHORTCUT_EDIT_PATH), self, activated=self.top.begin_path_edit)
        QShortcut(QKeySequence(SHORTCUT_FOCUS_SEARCH), self, activated=self.top.focus_filter)
        QShortcut(QKeySequence("Ctrl+Shift+F"), self, activated=self.open_semantic_search)
        QShortcut(QKeySequence("F5"), self, activated=self.refresh)
        QShortcut(QKeySequence("Alt+Left"), self, activated=self.go_back)
        QShortcut(QKeySequence("Alt+Right"), self, activated=self.go_forward)
        QShortcut(QKeySequence("Alt+Up"), self, activated=self.go_up)

        self._load(start)
        self.explorer.setFocus()          # don't let the first toolbar button grab initial focus
        if MOCK_TRANSFER:
            self._start_mock_transfer()

    # ── wiring ────────────────────────────────────────────────────────────
    def _wire(self) -> None:
        t, ex = self.top, self.explorer
        t.backRequested.connect(self.go_back)
        t.forwardRequested.connect(self.go_forward)
        t.upRequested.connect(self.go_up)
        t.refreshRequested.connect(self.refresh)
        t.pathSubmitted.connect(self.navigate)
        t.segmentActivated.connect(lambda i: self.navigate(join_path(t.segments[:i + 1])))
        t.filterChanged.connect(self._on_filter)
        t.viewModeChanged.connect(ex.set_mode)
        t.previewToggled.connect(self._on_preview_toggled)
        t.themePickerRequested.connect(self.open_theme_store)
        t.deepSearchRequested.connect(self.open_semantic_search)
        t.newFolderRequested.connect(self.create_folder)
        t.newFileRequested.connect(self.create_file)

        self.sidebar.locationRequested.connect(self.navigate)
        self.sidebar.toolRequested.connect(self._on_tool)

        ex.selectionChanged.connect(self._on_selection)
        ex.itemActivated.connect(self._on_item_activated)
        ex.newFolderRequested.connect(self.create_folder)
        ex.newFileRequested.connect(self.create_file)
        ex.renameRequested.connect(self.rename_file)
        ex.deleteRequested.connect(self.delete_files)
        ex.copyRequested.connect(self.copy_files)
        ex.pasteRequested.connect(self.paste_files)
        ex.openInTerminalRequested.connect(self.open_in_terminal)
        ex.showInExplorerRequested.connect(self.show_in_explorer)
        ex.lockRequested.connect(lambda f: self.open_safe_locker(mode="lock"))

        self.storage.scanRequested.connect(self._on_storage_scan)
        self.storage.targetRequested.connect(self._scan_storage_path)

    # ── navigation ────────────────────────────────────────────────────────
    def navigate(self, path: str) -> None:
        path = path.strip()
        if not path:
            return
        self.history.push(path)
        self._load(path)

    def go_back(self) -> None:
        if self.history.can_back:
            self._load(self.history.back())

    def go_forward(self) -> None:
        if self.history.can_forward:
            self._load(self.history.forward())

    def go_up(self) -> None:
        self.navigate(parent_path(self.history.current))

    def refresh(self) -> None:
        self._load(self.history.current)

    def _load(self, path: str) -> None:
        segs = split_path(path)
        self.top.set_segments(segs)
        self.backend.directory_requested.emit(path)
        self.explorer.set_files(self.backend.list_directory(path))      # HOOK
        self.top.set_nav_state(self.history.can_back, self.history.can_forward, len(segs) > 1)
        self.sidebar.set_active(self.sidebar.key_for_path(path))
        self._show_page("explorer")
        self._on_selection([])

    def _show_page(self, page: str) -> None:
        self.pages.setCurrentWidget(self.storage if page == "storage" else self.explorer)
        (self.storage.treemap if page == "storage" else self.explorer).setFocus()   # keep focus rings off buttons
        self._sync_inspector()

    def _sync_inspector(self) -> None:
        self.inspector.setVisible(self._inspector_wanted and self.pages.currentWidget() is self.explorer)

    # ── slots ─────────────────────────────────────────────────────────────
    def _on_filter(self, text: str) -> None:
        self.explorer.set_filter(text)
        self._on_selection(self.explorer.selected_files())

    def _on_selection(self, files: list[dict]) -> None:
        self.inspector.show_files(files, self.history.current)
        self.status.set_selection_summary(self.explorer.item_count(), files)

    def _on_item_activated(self, f: dict) -> None:
        if f.get("kind") == "refresh":
            self.refresh()
            return
        if f.get("kind") == "folder":
            self.navigate(join_path(split_path(self.history.current) + [f["name"]]))
        else:
            if hasattr(self.backend, "open_file"):
                target_path = f.get("path") or join_path(split_path(self.history.current) + [f["name"]])
                self.backend.open_file(target_path)
            self.status.flash(f"Opening: {f['name']}")

    def _on_storage_scan(self) -> None:
        self._scan_storage_path(self.history.current)

    def _scan_storage_path(self, path: str) -> None:
        if hasattr(self.backend, "scan_storage_tree") and Path(path).exists():
            self.status.flash(f"Scanning storage for {path}...")
            tree = self.backend.scan_storage_tree(path)
            self.storage.load(tree)
            self.status.flash(f"Storage analysis ready for {path}")
        else:
            self.backend.storage_scan_requested.emit(path)
            self.status.flash(f"Scan requested for {path}")

    def _on_preview_toggled(self, on: bool) -> None:
        self._inspector_wanted = on
        self._sync_inspector()

    def _on_tool(self, key: str) -> None:
        if key == "storage_doctor":
            self.sidebar.set_active("tool:storage_doctor")
            self._show_page("storage")
            if hasattr(self.backend, "get_drives"):
                targets = [(d["label"], d["path"]) for d in self.backend.get_drives()]
                curr = self.history.current
                if Path(curr).exists():
                    targets.append(("Current Folder", curr))
                self.storage.set_targets(targets)
            if hasattr(self.backend, "scan_storage_tree") and Path(self.history.current).exists():
                self._scan_storage_path(self.history.current)
        elif key == "duplicate_hunter":
            self.open_duplicate_hunter()
        elif key == "ai_organizer":
            self.open_ai_organizer()
        elif key == "encrypted_vault":
            self.open_safe_locker()

    # ── CRUD operations ───────────────────────────────────────────────────
    def create_folder(self) -> None:
        name, ok = QInputDialog.getText(self, "New Folder", "Folder Name:", text="New Folder")
        if ok and name.strip():
            p = Path(self.history.current) / name.strip()
            try:
                p.mkdir(parents=True, exist_ok=False)
                self.refresh()
                self.explorer.select_names([p.name])
                self.status.flash(f"Created folder: {p.name}")
            except Exception as e:
                self.status.flash(f"Error creating folder: {e}")

    def create_file(self) -> None:
        name, ok = QInputDialog.getText(self, "New File", "File Name:", text="New Document.txt")
        if ok and name.strip():
            p = Path(self.history.current) / name.strip()
            try:
                p.touch(exist_ok=False)
                self.refresh()
                self.explorer.select_names([p.name])
                self.status.flash(f"Created file: {p.name}")
            except Exception as e:
                self.status.flash(f"Error creating file: {e}")

    def rename_file(self, f: dict) -> None:
        old_name = f["name"]
        new_name, ok = QInputDialog.getText(self, "Rename", "New Name:", text=old_name)
        if ok and new_name.strip() and new_name.strip() != old_name:
            old_p = Path(f.get("path") or (Path(self.history.current) / old_name))
            new_p = old_p.parent / new_name.strip()
            try:
                old_p.rename(new_p)
                self.refresh()
                self.explorer.select_names([new_p.name])
                self.status.flash(f"Renamed: {old_name} -> {new_p.name}")
            except Exception as e:
                self.status.flash(f"Error renaming: {e}")

    def delete_files(self, files: list[dict]) -> None:
        names = ", ".join(f["name"] for f in files[:3])
        if len(files) > 3:
            names += f" and {len(files) - 3} more"
        ret = QMessageBox.question(self, "Recycle Bin", f"Move {names} to Recycle Bin?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if ret == QMessageBox.StandardButton.Yes:
            import send2trash
            trashed = 0
            for f in files:
                p = f.get("path") or str(Path(self.history.current) / f["name"])
                try:
                    send2trash.send2trash(p)
                    trashed += 1
                except Exception as e:
                    print(f"Failed to trash {p}: {e}")
            self.status.flash(f"Moved {trashed} item(s) to Recycle Bin")
            self.refresh()

    def copy_files(self, files: list[dict], is_cut: bool = False) -> None:
        self._clipboard_files = [f.get("path") or str(Path(self.history.current) / f["name"]) for f in files]
        self._clipboard_is_cut = is_cut
        action = "Cut" if is_cut else "Copied"
        self.status.flash(f"{action} {len(files)} item(s) to clipboard")

    def paste_files(self) -> None:
        if not self._clipboard_files:
            self.status.flash("Clipboard is empty")
            return
        cur = Path(self.history.current)
        pasted = 0
        for src_str in self._clipboard_files:
            src = Path(src_str)
            if not src.exists():
                continue
            dest = cur / src.name
            if dest.exists() and dest != src:
                stem, ext = src.stem, src.suffix
                i = 1
                while (cur / f"{stem} ({i}){ext}").exists():
                    i += 1
                dest = cur / f"{stem} ({i}){ext}"
            try:
                if self._clipboard_is_cut:
                    shutil.move(str(src), str(dest))
                else:
                    if src.is_dir():
                        shutil.copytree(str(src), str(dest))
                    else:
                        shutil.copy2(str(src), str(dest))
                pasted += 1
            except Exception as e:
                print(f"Error pasting {src}: {e}")
        if self._clipboard_is_cut:
            self._clipboard_files = []
        self.status.flash(f"Pasted {pasted} item(s)")
        self.refresh()

    def open_in_terminal(self) -> None:
        p = str(Path(self.history.current))
        try:
            if sys.platform.startswith("win"):
                subprocess.Popen(["cmd.exe", "/c", "start", "powershell.exe", "-NoExit", "-Command", f"Set-Location '{p}'"])
            elif sys.platform == "darwin":
                subprocess.Popen(["open", "-a", "Terminal", p])
            else:
                subprocess.Popen(["x-terminal-emulator", "--working-directory", p])
            self.status.flash(f"Opened terminal at {p}")
        except Exception as e:
            self.status.flash(f"Failed to open terminal: {e}")

    def show_in_explorer(self, f: dict) -> None:
        p = f.get("path") or str(Path(self.history.current) / f["name"])
        try:
            if sys.platform.startswith("win"):
                subprocess.Popen(["explorer.exe", f"/select,{p}"])
            elif sys.platform == "darwin":
                subprocess.Popen(["open", "-R", p])
            else:
                subprocess.Popen(["xdg-open", str(Path(p).parent)])
        except Exception as e:
            self.status.flash(f"Failed to show in explorer: {e}")

    # ── dialogs ───────────────────────────────────────────────────────────
    def _open_dialog(self, dlg: QDialog) -> QDialog:
        if self._dialog is not None:
            self._dialog.reject()
        self._dialog = dlg
        self.scrim.cover()
        dlg.finished.connect(lambda _r, d=dlg: self._on_dialog_closed(d))
        dlg.open()
        return dlg

    def _on_dialog_closed(self, dlg: QDialog) -> None:
        if self._dialog is dlg:
            self._dialog = None
            self.scrim.hide()
        dlg.deleteLater()
        self.explorer.setFocus()

    def open_duplicate_hunter(self, animate: bool = True) -> DuplicateHunterDialog:
        d = DuplicateHunterDialog(self, root=self.history.current, animate=animate)
        d.scanRequested.connect(self.backend.duplicate_scan_requested)
        d.trashRequested.connect(self._on_trash_duplicates)
        return self._open_dialog(d)

    def _on_trash_duplicates(self, paths: list[str]) -> None:
        import send2trash
        trashed = 0
        for p in paths:
            try:
                send2trash.send2trash(p)
                trashed += 1
            except Exception as e:
                print(f"Failed to trash {p}: {e}")
        self.status.flash(f"Moved {trashed} duplicate file(s) to Recycle Bin")
        self.refresh()

    def open_ai_organizer(self) -> AIOrganizerDialog:
        d = AIOrganizerDialog(self, root=self.history.current)
        d.executeRequested.connect(self._on_organize_requested)
        return self._open_dialog(d)

    def _on_organize_requested(self, rows: list[dict]) -> None:
        cur_dir = Path(self.history.current)
        executed = 0
        for r in rows:
            orig = cur_dir / r["original"]
            if orig.exists():
                tag_name = r.get("tag", "General").lstrip("#").capitalize()
                cat_dir = cur_dir / tag_name
                cat_dir.mkdir(parents=True, exist_ok=True)
                dest = cat_dir / r["proposed"]
                try:
                    shutil.move(str(orig), str(dest))
                    executed += 1
                except Exception as e:
                    print(f"Failed to move {orig}: {e}")
        self.status.flash(f"Organized {executed} file(s) into category folders")
        self.refresh()

    def open_safe_locker(self, mode: str = "lock") -> SafeLockerDialog:
        files = self.explorer.selected_files()
        file = files[0] if len(files) == 1 and files[0]["kind"] != "folder" else None
        d = SafeLockerDialog(self, file=file, mode=mode)
        d.vaultActionRequested.connect(self._on_vault_action)
        return self._open_dialog(d)

    def _on_vault_action(self, mode: str, name: str, password: str, trash: bool) -> None:
        from src.modules.crypto_vault import encrypt_file, decrypt_file
        import send2trash
        cur_dir = Path(self.history.current)
        if mode == "lock":
            src = cur_dir / name
            dest = src.with_suffix(src.suffix + ".nxv")
            try:
                encrypt_file(src, dest, password)
                if trash and src.exists():
                    send2trash.send2trash(str(src))
                self.status.flash(f"Locked & Encrypted: {dest.name}")
                self.refresh()
            except Exception as e:
                self.status.flash(f"Vault encryption failed: {e}")
        else:
            src = cur_dir / name
            if not src.name.endswith(".nxv"):
                candidate = src.with_suffix(src.suffix + ".nxv")
                if candidate.exists():
                    src = candidate
            try:
                out = decrypt_file(src, cur_dir, password)
                if trash and src.exists():
                    send2trash.send2trash(str(src))
                self.status.flash(f"Unlocked & Decrypted: {out.name}")
                self.refresh()
            except Exception as e:
                self.status.flash(f"Vault decryption failed: {e}")

    def open_semantic_search(self, query: str = "") -> SemanticSearchDialog:
        d = SemanticSearchDialog(self, query=query if isinstance(query, str) else "")
        d.searchRequested.connect(self.backend.semantic_search_requested)
        d.resultActivated.connect(lambda r: self.backend.open_file(r["path"]) if hasattr(self.backend, "open_file") and "path" in r else self.status.flash(f"Result: {r.get('name')}"))
        return self._open_dialog(d)

    def open_theme_store(self, tab: int = 0) -> ThemeStoreDialog:
        return self._open_dialog(ThemeStoreDialog(self, tab=tab if isinstance(tab, int) else 0))

    # ── window ────────────────────────────────────────────────────────────
    def resizeEvent(self, e):
        super().resizeEvent(e)
        if self.scrim.isVisible():
            self.scrim.setGeometry(self.rect())

    def closeEvent(self, e):
        if self._persist:
            theme_manager().settings().setValue("window/geometry", self.saveGeometry())
        super().closeEvent(e)

    # ── demo-only transfer ticker ─────────────────────────────────────────
    def _start_mock_transfer(self) -> None:
        self._pct = 62
        self._tick = QTimer(self)
        self._tick.setInterval(450)
        self._tick.timeout.connect(self._advance_transfer)
        self._tick.start()
        self.status.set_transfer("data.iso", 18.4, self._pct)

    def _advance_transfer(self) -> None:
        self._pct += 2
        if self._pct > 100:
            self._pct = 0
        self.status.set_transfer("data.iso", 18.4 + (self._pct % 7) * 0.1, self._pct)
