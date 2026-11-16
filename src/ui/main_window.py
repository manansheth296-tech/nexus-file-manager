"""Main Application Window for Nexus File Manager."""

import os
import sys
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Any
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QListWidget, QListWidgetItem, QToolBar, QStatusBar, QLabel,
    QProgressBar, QMessageBox, QInputDialog, QLineEdit, QStackedWidget,
    QFrame, QPushButton, QSizePolicy, QApplication
)
from PyQt6.QtCore import Qt, QSize, pyqtSlot, QTimer
from PyQt6.QtGui import QAction, QKeySequence, QIcon
import qtawesome as qta

from src.config import (
    APP_NAME, APP_VERSION, load_config, save_config, format_size
)
from src.themes import generate_stylesheet
from src.core.drive_detector import get_system_drives
from src.core.fs_operations import (
    FileOperationWorker, create_new_folder, create_new_file, rename_item
)
from src.core.fs_watcher import FilesystemWatcher
from src.ui.breadcrumb_bar import BreadcrumbBar
from src.ui.file_view import FileViewWidget
from src.ui.preview_panel import PreviewPanel
from src.ui.treemap_widget import StorageAnalyzerWidget
from src.ui.duplicates_dialog import DuplicatesDialog
from src.ui.ai_organizer_dialog import AIOrganizerDialog
from src.ui.vault_dialog import VaultDialog
from src.ui.semantic_search_dialog import SemanticSearchDialog
from src.ui.theme_dialog import ThemeDialog


class MainWindow(QMainWindow):
    """Primary window coordinating navigation, views, sidebar tools, and background tasks."""

    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.current_path = Path(self.config.get("last_path", str(Path.home()))).resolve()
        if not self.current_path.exists():
            self.current_path = Path.home()

        self.history: List[Path] = [self.current_path]
        self.history_index: int = 0
        self.clipboard_paths: List[Path] = []
        self.clipboard_operation: Optional[str] = None  # 'copy' or 'cut'

        self.worker: Optional[FileOperationWorker] = None
        self.watcher = FilesystemWatcher(self)
        self.watcher.directory_changed.connect(self._on_fs_change_detected)

        # Debounce timer for filesystem watcher to prevent UI event loops
        self.fs_debounce_timer = QTimer(self)
        self.fs_debounce_timer.setSingleShot(True)
        self.fs_debounce_timer.setInterval(350)
        self.fs_debounce_timer.timeout.connect(self.refresh_view)

        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.resize(1320, 820)

        self._init_ui()
        self.apply_theme(self.config.get("theme", "midnight_cyber"))
        self.navigate_to(self.current_path, add_to_history=False)

    def apply_theme(self, theme_key: str):
        """Apply stylesheet across the application and persist preference."""
        self.config["theme"] = theme_key
        save_config(self.config)
        stylesheet = generate_stylesheet(theme_key)
        app = QApplication.instance()
        if app:
            app.setStyleSheet(stylesheet)
        else:
            self.setStyleSheet(stylesheet)

    def _init_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        # 1. Top Navigation & Action Toolbar
        self._setup_top_toolbar(main_layout)

        # 2. Main Horizontal Splitter (Sidebar | Content | Preview)
        self.splitter = QSplitter(Qt.Orientation.Horizontal, self)

        # Left Sidebar (Bookmarks, Drives, Tools)
        self._setup_sidebar()

        # Center Work Area (Stacked Widget: File View vs Treemap)
        self.center_stack = QStackedWidget(self)

        self.file_view = FileViewWidget(self)
        self.file_view.file_selected.connect(self._on_file_selected)
        self.file_view.file_activated.connect(self._on_file_activated)
        self.file_view.selection_changed.connect(self._on_selection_changed)
        self.file_view.request_copy.connect(self._copy_selection)
        self.file_view.request_cut.connect(self._cut_selection)
        self.file_view.request_paste.connect(self._paste_clipboard)
        self.file_view.request_delete.connect(self._delete_items)
        self.file_view.request_rename.connect(self._rename_item_dialog)
        self.file_view.request_vault_lock.connect(self._open_vault_for_files)
        self.center_stack.addWidget(self.file_view)

        # Storage Analyzer Widget (page 1)
        self.treemap_view = StorageAnalyzerWidget(self.current_path, self)
        self.treemap_view.navigate_to_path.connect(self._on_treemap_navigate)
        self.center_stack.addWidget(self.treemap_view)

        self.splitter.addWidget(self.center_stack)

        # Right Inspector / Preview Panel
        self.preview_panel = PreviewPanel(self)
        self.splitter.addWidget(self.preview_panel)

        # Splitter sizing ratio: Sidebar (210), Center (800), Preview (310)
        self.splitter.setSizes([220, 800, 300])
        main_layout.addWidget(self.splitter, stretch=1)

        # 3. Status Bar
        self._setup_status_bar()

    def _setup_top_toolbar(self, parent_layout: QVBoxLayout):
        nav_bar = QHBoxLayout()
        nav_bar.setSpacing(8)

        # Breadcrumbs bar
        self.breadcrumbs = BreadcrumbBar(self.current_path, self)
        self.breadcrumbs.path_changed.connect(self.navigate_to)
        self.breadcrumbs.navigate_back.connect(self.navigate_back)
        self.breadcrumbs.navigate_forward.connect(self.navigate_forward)
        self.breadcrumbs.navigate_up.connect(self.navigate_up)
        self.breadcrumbs.refresh_requested.connect(self.refresh_view)
        nav_bar.addWidget(self.breadcrumbs, stretch=1)

        # Live Filename Filter Search
        self.filter_edit = QLineEdit(self)
        self.filter_edit.setPlaceholderText("Filter files (Ctrl+F)...")
        self.filter_edit.setFixedWidth(170)
        self.filter_edit.textChanged.connect(self._on_filter_text_changed)
        nav_bar.addWidget(self.filter_edit)

        # Deep Content Search Button
        btn_deep_search = QPushButton("Deep Search", self)
        btn_deep_search.setIcon(qta.icon("fa5s.search-plus", color="#38BDF8"))
        btn_deep_search.setToolTip("Search inside PDFs, Docs, Text, Spreadsheets & Code")
        btn_deep_search.clicked.connect(self._open_semantic_search)
        nav_bar.addWidget(btn_deep_search)

        # View Mode Toggle Buttons
        self.btn_view_details = QPushButton(self)
        self.btn_view_details.setIcon(qta.icon("fa5s.list"))
        self.btn_view_details.setToolTip("Details Table View")
        self.btn_view_details.clicked.connect(lambda: self._set_view_mode("details"))
        nav_bar.addWidget(self.btn_view_details)

        self.btn_view_grid = QPushButton(self)
        self.btn_view_grid.setIcon(qta.icon("fa5s.th-large"))
        self.btn_view_grid.setToolTip("Icon Grid View")
        self.btn_view_grid.clicked.connect(lambda: self._set_view_mode("grid"))
        nav_bar.addWidget(self.btn_view_grid)

        # Actions: New Folder & New File
        btn_new_folder = QPushButton(self)
        btn_new_folder.setIcon(qta.icon("fa5s.folder-plus", color="#EAB308"))
        btn_new_folder.setToolTip("New Folder (Ctrl+Shift+N)")
        btn_new_folder.clicked.connect(self._create_folder)
        nav_bar.addWidget(btn_new_folder)

        btn_new_file = QPushButton(self)
        btn_new_file.setIcon(qta.icon("fa5s.file-medical", color="#38BDF8"))
        btn_new_file.setToolTip("New File")
        btn_new_file.clicked.connect(self._create_file)
        nav_bar.addWidget(btn_new_file)

        # Theme Switcher Button
        btn_theme = QPushButton(self)
        btn_theme.setIcon(qta.icon("fa5s.palette", color="#A855F7"))
        btn_theme.setToolTip("Change Theme & Visual Styles")
        btn_theme.clicked.connect(self._open_theme_dialog)
        nav_bar.addWidget(btn_theme)

        # Toggle Preview Panel
        self.btn_toggle_preview = QPushButton(self)
        self.btn_toggle_preview.setIcon(qta.icon("fa5s.columns"))
        self.btn_toggle_preview.setToolTip("Toggle Preview Panel")
        self.btn_toggle_preview.clicked.connect(self._toggle_preview_panel)
        nav_bar.addWidget(self.btn_toggle_preview)

        parent_layout.addLayout(nav_bar)

    def _setup_sidebar(self):
        sidebar_frame = QFrame(self)
        sidebar_frame.setFrameShape(QFrame.Shape.NoFrame)
        sidebar_layout = QVBoxLayout(sidebar_frame)
        sidebar_layout.setContentsMargins(0, 0, 4, 0)
        sidebar_layout.setSpacing(6)

        self.sidebar_list = QListWidget(sidebar_frame)
        self.sidebar_list.itemClicked.connect(self._on_sidebar_item_clicked)

        # 1. Quick Access Header
        self._add_sidebar_section("QUICK ACCESS")
        for b in self.config.get("bookmarks", []):
            item = QListWidgetItem(qta.icon(b.get("icon", "fa5s.folder"), color="#EAB308"), b["name"])
            item.setData(Qt.ItemDataRole.UserRole, {"type": "path", "path": b["path"]})
            self.sidebar_list.addItem(item)

        # 2. System Drives Header
        self._add_sidebar_section("DRIVES")
        drives = get_system_drives()
        for d in drives:
            free_str = format_size(d["free"])
            item = QListWidgetItem(
                qta.icon(d.get("icon", "fa5s.hdd"), color="#38BDF8"),
                f"{d['name']} ({free_str} free)",
            )
            item.setData(Qt.ItemDataRole.UserRole, {"type": "path", "path": d["mountpoint"]})
            self.sidebar_list.addItem(item)

        # 3. Smart Tools Header
        self._add_sidebar_section("SPECIALIZED TOOLS")
        tool_items = [
            ("Storage Doctor (Treemap)", "fa5s.chart-pie", "#A855F7", "treemap"),
            ("Duplicate Hunter", "fa5s.clone", "#38BDF8", "duplicates"),
            ("AI Smart Organizer", "fa5s.magic", "#22C55E", "organizer"),
            ("Encrypted Vault", "fa5s.shield-alt", "#EAB308", "vault"),
        ]

        for name, icon_name, color, tool_id in tool_items:
            item = QListWidgetItem(qta.icon(icon_name, color=color), name)
            item.setData(Qt.ItemDataRole.UserRole, {"type": "tool", "id": tool_id})
            self.sidebar_list.addItem(item)

        sidebar_layout.addWidget(self.sidebar_list)
        self.splitter.addWidget(sidebar_frame)

    def _add_sidebar_section(self, title: str):
        header = QListWidgetItem(title)
        header.setFlags(Qt.ItemFlag.NoItemFlags)
        header.setData(Qt.ItemDataRole.UserRole, {"type": "header"})
        self.sidebar_list.addItem(header)

    def _setup_status_bar(self):
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)

        self.lbl_status_items = QLabel("0 items", self)
        self.status_bar.addWidget(self.lbl_status_items, stretch=1)

        self.lbl_worker_status = QLabel("", self)
        self.lbl_worker_status.setStyleSheet("color: #38BDF8;")
        self.status_bar.addPermanentWidget(self.lbl_worker_status)

        self.task_progress = QProgressBar(self)
        self.task_progress.setRange(0, 100)
        self.task_progress.setFixedWidth(160)
        self.task_progress.setFixedHeight(12)
        self.task_progress.hide()
        self.status_bar.addPermanentWidget(self.task_progress)

    def navigate_to(self, path: Path, add_to_history: bool = True):
        """Navigate to directory path, updating view and history."""
        target = path.resolve()
        if not target.exists() or not target.is_dir():
            QMessageBox.warning(self, "Path Not Found", f"Directory does not exist:\n{target}")
            return

        self.current_path = target
        self.center_stack.setCurrentIndex(0)  # Switch back to file view

        if add_to_history:
            if self.history_index < len(self.history) - 1:
                self.history = self.history[:self.history_index + 1]
            self.history.append(self.current_path)
            self.history_index = len(self.history) - 1

        self.breadcrumbs.set_path(self.current_path)
        self.breadcrumbs.update_history_state(
            can_back=(self.history_index > 0),
            can_forward=(self.history_index < len(self.history) - 1),
        )

        self.refresh_view()
        self.watcher.watch_directory(self.current_path)

        self.config["last_path"] = str(self.current_path)
        save_config(self.config)

    def refresh_view(self):
        """Reload file list in active folder."""
        query = self.filter_edit.text().strip()
        self.file_view.populate(
            self.current_path,
            show_hidden=self.config.get("show_hidden", False),
            filter_query=query,
        )
        self._update_status_item_count()

    def navigate_back(self):
        if self.history_index > 0:
            self.history_index -= 1
            self.navigate_to(self.history[self.history_index], add_to_history=False)

    def navigate_forward(self):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.navigate_to(self.history[self.history_index], add_to_history=False)

    def navigate_up(self):
        parent = self.current_path.parent
        if parent != self.current_path and parent.exists():
            self.navigate_to(parent)

    def _on_filter_text_changed(self, text: str):
        self.refresh_view()

    def _set_view_mode(self, mode: str):
        self.file_view.set_view_mode(mode)
        self.config["default_view"] = mode
        save_config(self.config)

    def _toggle_preview_panel(self):
        is_visible = self.preview_panel.isVisible()
        self.preview_panel.setVisible(not is_visible)

    def _on_file_selected(self, path: Optional[Path]):
        self.preview_panel.set_file(path)

    def _on_file_activated(self, path: Path):
        if path.is_dir():
            self.navigate_to(path)
        else:
            try:
                if sys.platform.startswith("win"):
                    os.startfile(str(path))
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", str(path)])
                else:
                    subprocess.Popen(["xdg-open", str(path)])
            except Exception as e:
                QMessageBox.warning(self, "Cannot Open File", f"Error opening file: {e}")

    def _on_selection_changed(self, paths: List[Path]):
        if not paths:
            self._update_status_item_count()
            return
        total_size = sum(p.stat().st_size for p in paths if p.is_file())
        count_str = f"{len(paths)} item{'s' if len(paths) != 1 else ''} selected"
        size_str = f" ({format_size(total_size)})" if total_size > 0 else ""
        self.lbl_status_items.setText(f"{count_str}{size_str}")

    def _update_status_item_count(self):
        total = len(self.file_view.items)
        self.lbl_status_items.setText(f"{total} item{'s' if total != 1 else ''}")

    def _on_sidebar_item_clicked(self, item: QListWidgetItem):
        data = item.data(Qt.ItemDataRole.UserRole)
        if not data:
            return
        itype = data.get("type")
        if itype == "path":
            self.navigate_to(Path(data["path"]))
        elif itype == "tool":
            tool_id = data.get("id")
            if tool_id == "treemap":
                self._open_treemap_view()
            elif tool_id == "duplicates":
                self._open_duplicates_dialog()
            elif tool_id == "organizer":
                self._open_ai_organizer()
            elif tool_id == "vault":
                self._open_vault_for_files([])

    def _open_treemap_view(self):
        self.treemap_view.start_scan(self.current_path)
        self.center_stack.setCurrentIndex(1)

    def _on_treemap_navigate(self, path: Path):
        self.navigate_to(path)

    def _open_duplicates_dialog(self):
        dlg = DuplicatesDialog(self.current_path, self)
        dlg.exec()
        self.refresh_view()

    def _open_ai_organizer(self):
        dlg = AIOrganizerDialog(self.current_path, self)
        dlg.exec()
        self.refresh_view()

    def _open_vault_for_files(self, paths: List[Path]):
        dlg = VaultDialog(paths, self.current_path, self)
        dlg.exec()
        self.refresh_view()

    def _open_semantic_search(self):
        dlg = SemanticSearchDialog(self.current_path, self)
        dlg.file_activated.connect(self._on_file_activated)
        dlg.exec()

    def _open_theme_dialog(self):
        dlg = ThemeDialog(
            current_theme=self.config.get("theme", "midnight_cyber"),
            on_theme_changed=self.apply_theme,
            parent=self,
        )
        dlg.exec()

    # File Operations
    def _create_folder(self):
        name, ok = QInputDialog.getText(self, "New Folder", "Folder Name:", text="New Folder")
        if ok and name.strip():
            create_new_folder(self.current_path, name.strip())
            self.refresh_view()

    def _create_file(self):
        name, ok = QInputDialog.getText(self, "New File", "File Name:", text="New Document.txt")
        if ok and name.strip():
            create_new_file(self.current_path, name.strip())
            self.refresh_view()

    def _rename_item_dialog(self, path: Path):
        name, ok = QInputDialog.getText(self, "Rename", "New Name:", text=path.name)
        if ok and name.strip() and name.strip() != path.name:
            try:
                rename_item(path, name.strip())
                self.refresh_view()
            except Exception as e:
                QMessageBox.warning(self, "Rename Error", str(e))

    def _copy_selection(self, paths: List[Path]):
        self.clipboard_paths = paths
        self.clipboard_operation = "copy"
        self.status_bar.showMessage(f"Copied {len(paths)} item(s) to clipboard.", 3000)

    def _cut_selection(self, paths: List[Path]):
        self.clipboard_paths = paths
        self.clipboard_operation = "cut"
        self.status_bar.showMessage(f"Cut {len(paths)} item(s) to clipboard.", 3000)

    def _paste_clipboard(self):
        if not self.clipboard_paths or not self.clipboard_operation:
            return

        op = "move" if self.clipboard_operation == "cut" else "copy"
        self.task_progress.show()
        self.task_progress.setValue(0)
        self.lbl_worker_status.setText(f"Starting {op}...")

        self.worker = FileOperationWorker(
            operation=op,
            sources=self.clipboard_paths,
            destination=self.current_path,
            overwrite=False,
        )
        self.worker.progress_updated.connect(self._on_worker_progress)
        self.worker.operation_completed.connect(self._on_worker_completed)
        self.worker.start()

        if self.clipboard_operation == "cut":
            self.clipboard_paths = []
            self.clipboard_operation = None

    def _delete_items(self, paths: List[Path], permanent: bool):
        msg = f"Permanently delete {len(paths)} item(s)?" if permanent else f"Send {len(paths)} item(s) to the Recycle Bin?"
        reply = QMessageBox.question(
            self, "Confirm Delete", msg, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            op = "delete_permanent" if permanent else "delete_trash"
            self.worker = FileOperationWorker(operation=op, sources=paths)
            self.worker.operation_completed.connect(self._on_worker_completed)
            self.worker.start()

    def _on_worker_progress(self, pct: int, filename: str, speed: str):
        self.task_progress.setValue(pct)
        self.lbl_worker_status.setText(f"{filename} ({speed})")

    def _on_worker_completed(self, success: bool, message: str):
        self.task_progress.hide()
        self.lbl_worker_status.setText("")
        self.status_bar.showMessage(message, 4000)
        self.refresh_view()

    def _on_fs_change_detected(self, changed_path: str):
        self.fs_debounce_timer.start()

    def closeEvent(self, event):
        self.watcher.stop()
        super().closeEvent(event)
