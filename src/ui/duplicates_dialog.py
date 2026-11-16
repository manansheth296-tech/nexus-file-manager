"""Duplicate File Cleaner dialog: 3-tier SHA-256 deduplication and safe recycling."""

from pathlib import Path
from typing import Dict, List, Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QProgressBar, QTreeWidget, QTreeWidgetItem, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
import qtawesome as qta
import send2trash

from src.config import format_size
from src.modules.duplicate_finder import DuplicateFinderWorker


class DuplicatesDialog(QDialog):
    """Interactive modal to search and clean duplicate files."""

    def __init__(self, target_dir: Path, parent: Optional[QDialog] = None):
        super().__init__(parent)
        self.target_dir = target_dir
        self.worker: Optional[DuplicateFinderWorker] = None
        self.duplicate_groups: Dict[str, List[Path]] = {}

        self.setWindowTitle("Smart Duplicate File Finder")
        self.resize(850, 560)
        self._init_ui()
        self.start_scan()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Header Section
        header = QHBoxLayout()
        icon_lbl = QLabel(self)
        icon_lbl.setPixmap(qta.icon("fa5s.clone", color="#38bdf8").pixmap(28, 28))
        header.addWidget(icon_lbl)

        title_box = QVBoxLayout()
        title = QLabel(f"Duplicate Hunter: {self.target_dir.name}", self)
        title.setStyleSheet("font-size: 15px; font-weight: 600; color: #FFFFFF;")
        subtitle = QLabel("Multi-stage hash comparison (Size → 4KB Header → SHA-256)", self)
        subtitle.setStyleSheet("color: #94A3B8; font-size: 12px;")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)
        header.addStretch()

        layout.addLayout(header)

        # Progress Section
        self.lbl_status = QLabel("Preparing scan...", self)
        layout.addWidget(self.lbl_status)
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setFixedHeight(8)
        layout.addWidget(self.progress_bar)

        # Duplicate Tree
        self.tree = QTreeWidget(self)
        self.tree.setHeaderLabels(["File / Group", "Size", "Modified Date"])
        self.tree.setColumnWidth(0, 480)
        self.tree.setColumnWidth(1, 100)
        layout.addWidget(self.tree, stretch=1)

        # Selection Helpers Toolbar
        tools_layout = QHBoxLayout()
        self.btn_keep_newest = QPushButton("Keep Newest Only", self)
        self.btn_keep_newest.setIcon(qta.icon("fa5s.clock"))
        self.btn_keep_newest.clicked.connect(self._select_keep_newest)

        self.btn_keep_oldest = QPushButton("Keep Oldest Only", self)
        self.btn_keep_oldest.setIcon(qta.icon("fa5s.history"))
        self.btn_keep_oldest.clicked.connect(self._select_keep_oldest)

        self.btn_select_none = QPushButton("Deselect All", self)
        self.btn_select_none.clicked.connect(self._deselect_all)

        tools_layout.addWidget(self.btn_keep_newest)
        tools_layout.addWidget(self.btn_keep_oldest)
        tools_layout.addWidget(self.btn_select_none)
        tools_layout.addStretch()

        layout.addLayout(tools_layout)

        # Bottom Actions
        bottom_bar = QHBoxLayout()
        self.lbl_summary = QLabel("0 duplicate groups found.", self)
        bottom_bar.addWidget(self.lbl_summary)
        bottom_bar.addStretch()

        self.btn_delete = QPushButton("Move Selected to Recycle Bin", self)
        self.btn_delete.setIcon(qta.icon("fa5s.trash-alt", color="#ef4444"))
        self.btn_delete.setStyleSheet("QPushButton { font-weight: 600; padding: 6px 14px; }")
        self.btn_delete.clicked.connect(self._delete_selected)
        bottom_bar.addWidget(self.btn_delete)

        self.btn_close = QPushButton("Close", self)
        self.btn_close.clicked.connect(self.accept)
        bottom_bar.addWidget(self.btn_close)

        layout.addLayout(bottom_bar)

    def start_scan(self):
        self.progress_bar.setValue(0)
        self.tree.clear()
        self.btn_delete.setEnabled(False)

        self.worker = DuplicateFinderWorker(self.target_dir)
        self.worker.progress_updated.connect(self._on_progress)
        self.worker.duplicates_found.connect(self._on_duplicates_found)
        self.worker.start()

    def _on_progress(self, percent: int, msg: str):
        self.progress_bar.setValue(percent)
        self.lbl_status.setText(msg)

    def _on_duplicates_found(self, results: Dict[str, List[Path]]):
        self.duplicate_groups = results
        self.tree.clear()

        total_dups = 0
        total_wasted_bytes = 0

        for h, paths in results.items():
            if not paths:
                continue
            first_path = paths[0]
            try:
                sz = first_path.stat().st_size
            except OSError:
                sz = 0

            # Wasted space = (count - 1) * file_size
            total_wasted_bytes += (len(paths) - 1) * sz
            total_dups += len(paths) - 1

            group_item = QTreeWidgetItem(self.tree)
            group_item.setText(0, f"Group: {first_path.name} ({len(paths)} copies)")
            group_item.setText(1, format_size(sz))
            group_item.setIcon(0, qta.icon("fa5s.copy", color="#eab308"))
            group_item.setExpanded(True)

            for p in paths:
                child = QTreeWidgetItem(group_item)
                child.setText(0, str(p))
                child.setFlags(child.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                child.setCheckState(0, Qt.CheckState.Unchecked)
                child.setData(0, Qt.ItemDataRole.UserRole, str(p))
                try:
                    import datetime
                    mtime = datetime.datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                    child.setText(2, mtime)
                except OSError:
                    pass

        self.lbl_summary.setText(
            f"Found {len(results)} groups ({total_dups} duplicate files). Potential savings: {format_size(total_wasted_bytes)}"
        )
        self.btn_delete.setEnabled(total_dups > 0)
        if total_dups > 0:
            self._select_keep_newest()

    def _select_keep_newest(self):
        """Check all duplicate files except the newest one in each group."""
        for i in range(self.tree.topLevelItemCount()):
            group = self.tree.topLevelItem(i)
            children = [group.child(c) for c in range(group.childCount())]
            # Sort by mtime descending
            def get_mtime(item):
                p = Path(item.data(0, Qt.ItemDataRole.UserRole))
                try:
                    return p.stat().st_mtime
                except OSError:
                    return 0

            children.sort(key=get_mtime, reverse=True)
            # Keep index 0 unchecked, check the rest
            for idx, c in enumerate(children):
                c.setCheckState(0, Qt.CheckState.Unchecked if idx == 0 else Qt.CheckState.Checked)

    def _select_keep_oldest(self):
        """Check all duplicate files except the oldest one in each group."""
        for i in range(self.tree.topLevelItemCount()):
            group = self.tree.topLevelItem(i)
            children = [group.child(c) for c in range(group.childCount())]
            def get_mtime(item):
                p = Path(item.data(0, Qt.ItemDataRole.UserRole))
                try:
                    return p.stat().st_mtime
                except OSError:
                    return 0

            children.sort(key=get_mtime)
            for idx, c in enumerate(children):
                c.setCheckState(0, Qt.CheckState.Unchecked if idx == 0 else Qt.CheckState.Checked)

    def _deselect_all(self):
        for i in range(self.tree.topLevelItemCount()):
            group = self.tree.topLevelItem(i)
            for c in range(group.childCount()):
                group.child(c).setCheckState(0, Qt.CheckState.Unchecked)

    def _delete_selected(self):
        selected_paths: List[Path] = []
        for i in range(self.tree.topLevelItemCount()):
            group = self.tree.topLevelItem(i)
            for c in range(group.childCount()):
                child = group.child(c)
                if child.checkState(0) == Qt.CheckState.Checked:
                    selected_paths.append(Path(child.data(0, Qt.ItemDataRole.UserRole)))

        if not selected_paths:
            QMessageBox.information(self, "No Selection", "Please check at least one duplicate file to remove.")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Safe Deletion",
            f"Are you sure you want to move {len(selected_paths)} duplicate file(s) to the Recycle Bin?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            success = 0
            for p in selected_paths:
                try:
                    send2trash.send2trash(str(p))
                    success += 1
                except Exception as e:
                    print(f"Error trashing duplicate {p}: {e}")

            QMessageBox.information(
                self, "Duplicates Cleaned", f"Successfully moved {success} duplicate files to Recycle Bin."
            )
            self.start_scan()
