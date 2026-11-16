"""File view widget supporting sortable Details Table View and Grid View with rich icons."""

import datetime
import os
import sys
import subprocess
from pathlib import Path
from typing import List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QMenu, QAbstractItemView, QStackedWidget, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import pyqtSignal, Qt, QSize
from PyQt6.QtGui import QAction, QKeySequence, QIcon, QKeyEvent
import qtawesome as qta

from src.config import format_size, get_file_icon_info, FILE_CATEGORIES


class FileViewWidget(QWidget):
    """Unified file view with toggleable Table (Details) and Grid (Icon) modes."""

    file_selected = pyqtSignal(object)       # Optional[Path]
    file_activated = pyqtSignal(Path)        # Path (double click or Enter)
    selection_changed = pyqtSignal(list)     # List[Path]
    request_copy = pyqtSignal(list)          # List[Path]
    request_cut = pyqtSignal(list)           # List[Path]
    request_paste = pyqtSignal()
    request_delete = pyqtSignal(list, bool)  # (List[Path], permanent_bool)
    request_rename = pyqtSignal(Path)
    request_vault_lock = pyqtSignal(list)    # List[Path]

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.current_path: Optional[Path] = None
        self.items: List[Path] = []
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget(self)

        # 0: Details Table View
        self.table = QTableWidget(self)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Name", "Size", "Type", "Date Modified"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.table.itemSelectionChanged.connect(self._on_table_selection_changed)
        self.table.itemDoubleClicked.connect(self._on_table_double_clicked)
        self.table.setIconSize(QSize(20, 20))
        self.stack.addWidget(self.table)

        # 1: Grid (Icon) View
        self.grid = QListWidget(self)
        self.grid.setViewMode(QListWidget.ViewMode.IconMode)
        self.grid.setIconSize(QSize(60, 60))
        self.grid.setGridSize(QSize(105, 95))
        self.grid.setSpacing(10)
        self.grid.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.grid.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.grid.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.grid.customContextMenuRequested.connect(self._show_context_menu)
        self.grid.itemSelectionChanged.connect(self._on_grid_selection_changed)
        self.grid.itemDoubleClicked.connect(self._on_grid_double_clicked)
        self.stack.addWidget(self.grid)

        layout.addWidget(self.stack)

    def set_view_mode(self, mode: str):
        """Switch between 'details' and 'grid'."""
        if mode == "grid":
            self.stack.setCurrentIndex(1)
        else:
            self.stack.setCurrentIndex(0)

    def populate(self, directory: Path, show_hidden: bool = False, filter_query: str = ""):
        """Populate items from the directory into the views."""
        self.current_path = directory
        self.items = []
        self.table.setRowCount(0)
        self.grid.clear()

        if not directory.exists() or not directory.is_dir():
            return

        try:
            entries = list(directory.iterdir())
        except (PermissionError, OSError) as e:
            print(f"Error reading {directory}: {e}")
            return

        # Sort: Folders first, then alphabetically
        folders = []
        files = []
        for e in entries:
            if not show_hidden and e.name.startswith("."):
                continue
            if filter_query and filter_query.lower() not in e.name.lower():
                continue
            if e.is_dir():
                folders.append(e)
            else:
                files.append(e)

        folders.sort(key=lambda p: p.name.lower())
        files.sort(key=lambda p: p.name.lower())
        self.items = folders + files

        self.table.setRowCount(len(self.items))

        for row, path in enumerate(self.items):
            is_dir = path.is_dir()
            icon_name, color = get_file_icon_info(path)
            icon = qta.icon(icon_name, color=color)

            # 1. Name Item
            name_item = QTableWidgetItem(icon, path.name)
            name_item.setData(Qt.ItemDataRole.UserRole, str(path))
            self.table.setItem(row, 0, name_item)

            # Metadata
            try:
                stat = path.stat()
                size_str = "" if is_dir else format_size(stat.st_size)
                ext = path.suffix.lower()
                type_str = "Folder" if is_dir else (ext.upper()[1:] + " File" if ext else "File")
                date_str = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
            except OSError:
                size_str, type_str, date_str = "", "Unknown", ""

            # 2. Size Item
            size_item = QTableWidgetItem(size_str)
            size_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 1, size_item)

            # 3. Type Item
            type_item = QTableWidgetItem(type_str)
            self.table.setItem(row, 2, type_item)

            # 4. Modified Item
            date_item = QTableWidgetItem(date_str)
            self.table.setItem(row, 3, date_item)

            # Add to Grid View
            grid_item = QListWidgetItem(icon, path.name)
            grid_item.setData(Qt.ItemDataRole.UserRole, str(path))
            grid_item.setSizeHint(QSize(95, 88))
            grid_item.setTextAlignment(Qt.AlignmentFlag.AlignHCenter)
            self.grid.addItem(grid_item)

    def get_selected_paths(self) -> List[Path]:
        """Return list of currently selected paths."""
        if self.stack.currentIndex() == 0:
            selected_rows = set(index.row() for index in self.table.selectedIndexes())
            return [self.items[r] for r in selected_rows if r < len(self.items)]
        else:
            return [Path(item.data(Qt.ItemDataRole.UserRole)) for item in self.grid.selectedItems()]

    def _on_table_selection_changed(self):
        paths = self.get_selected_paths()
        self.selection_changed.emit(paths)
        self.file_selected.emit(paths[0] if paths else None)

    def _on_grid_selection_changed(self):
        paths = self.get_selected_paths()
        self.selection_changed.emit(paths)
        self.file_selected.emit(paths[0] if paths else None)

    def _on_table_double_clicked(self, item: QTableWidgetItem):
        row = item.row()
        if row < len(self.items):
            self.file_activated.emit(self.items[row])

    def _on_grid_double_clicked(self, item: QListWidgetItem):
        p_str = item.data(Qt.ItemDataRole.UserRole)
        if p_str:
            self.file_activated.emit(Path(p_str))

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        paths = self.get_selected_paths()

        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if paths:
                self.file_activated.emit(paths[0])
            return
        elif key == Qt.Key.Key_F2:
            if len(paths) == 1:
                self.request_rename.emit(paths[0])
            return
        elif key == Qt.Key.Key_Delete:
            if paths:
                permanent = bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
                self.request_delete.emit(paths, permanent)
            return

        super().keyPressEvent(event)

    def _show_context_menu(self, pos):
        paths = self.get_selected_paths()
        menu = QMenu(self)

        if paths:
            first = paths[0]
            act_open = menu.addAction(qta.icon("fa5s.folder-open"), "Open")
            act_open.triggered.connect(lambda: self.file_activated.emit(first))
            menu.addSeparator()

            act_cut = menu.addAction(qta.icon("fa5s.cut"), "Cut (Ctrl+X)")
            act_cut.triggered.connect(lambda: self.request_cut.emit(paths))
            act_copy = menu.addAction(qta.icon("fa5s.copy"), "Copy (Ctrl+C)")
            act_copy.triggered.connect(lambda: self.request_copy.emit(paths))

        act_paste = menu.addAction(qta.icon("fa5s.paste"), "Paste (Ctrl+V)")
        act_paste.triggered.connect(self.request_paste.emit)

        if paths:
            menu.addSeparator()
            if len(paths) == 1:
                act_rename = menu.addAction(qta.icon("fa5s.edit"), "Rename (F2)")
                act_rename.triggered.connect(lambda: self.request_rename.emit(paths[0]))

            act_trash = menu.addAction(qta.icon("fa5s.trash-alt", color="#EF4444"), "Move to Recycle Bin (Del)")
            act_trash.triggered.connect(lambda: self.request_delete.emit(paths, False))

            act_perm_del = menu.addAction(qta.icon("fa5s.times", color="#EF4444"), "Permanently Delete (Shift+Del)")
            act_perm_del.triggered.connect(lambda: self.request_delete.emit(paths, True))

            menu.addSeparator()
            act_vault = menu.addAction(qta.icon("fa5s.lock", color="#EAB308"), "Lock in Encrypted Vault")
            act_vault.triggered.connect(lambda: self.request_vault_lock.emit(paths))

            act_copy_path = menu.addAction(qta.icon("fa5s.link"), "Copy Path")
            act_copy_path.triggered.connect(lambda: self._copy_path_to_clipboard(paths[0]))

        menu.addSeparator()
        act_term = menu.addAction(qta.icon("fa5s.terminal"), "Open in Terminal")
        act_term.triggered.connect(self._open_terminal)

        target_widget = self.table if self.stack.currentIndex() == 0 else self.grid
        menu.exec(target_widget.mapToGlobal(pos))

    def _copy_path_to_clipboard(self, path: Path):
        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setText(str(path))

    def _open_terminal(self):
        folder = self.current_path or Path.home()
        if sys.platform.startswith("win"):
            subprocess.Popen(["cmd.exe", "/K", f"cd /d {folder}"], creationflags=subprocess.CREATE_NEW_CONSOLE)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", "-a", "Terminal", str(folder)])
        else:
            subprocess.Popen(["x-terminal-emulator", f"--working-directory={folder}"])
