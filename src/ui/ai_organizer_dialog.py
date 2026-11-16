"""AI-powered Smart Organizer Dialog: automated folder cleanup with dry-run verification."""

import shutil
from pathlib import Path
from typing import List, Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QProgressBar, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QCheckBox
)
from PyQt6.QtCore import Qt
import qtawesome as qta

from src.modules.ai_organizer import AIOrganizerWorker, OrganizationPlanItem


class AIOrganizerDialog(QDialog):
    """Interactive dry-run preview dialog for AI autonomous folder organization."""

    def __init__(self, target_folder: Path, parent: Optional[QDialog] = None):
        super().__init__(parent)
        self.target_folder = target_folder
        self.worker: Optional[AIOrganizerWorker] = None
        self.plan_items: List[OrganizationPlanItem] = []

        self.setWindowTitle("AI Smart Organizer & Cleaner")
        self.resize(920, 580)
        self._init_ui()
        self.start_analysis()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Header
        header = QHBoxLayout()
        icon_lbl = QLabel(self)
        icon_lbl.setPixmap(qta.icon("fa5s.magic", color="#38bdf8").pixmap(30, 30))
        header.addWidget(icon_lbl)

        title_box = QVBoxLayout()
        title = QLabel(f"Organizing: {self.target_folder.name}", self)
        title.setStyleSheet("font-size: 16px; font-weight: 600; color: #FFFFFF;")
        subtitle = QLabel("Content-aware classification & smart renaming with dry-run approval", self)
        subtitle.setStyleSheet("color: #94A3B8; font-size: 12px;")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)
        header.addStretch()

        layout.addLayout(header)

        # Status & Progress
        self.lbl_status = QLabel("Inspecting files and document text...", self)
        layout.addWidget(self.lbl_status)
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setFixedHeight(8)
        layout.addWidget(self.progress_bar)

        # Plan Table
        self.table = QTableWidget(self)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Select", "Original Name", "Proposed Clean Name", "Target Category", "Confidence"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setShowGrid(False)
        layout.addWidget(self.table, stretch=1)

        # Toolbar
        tools_layout = QHBoxLayout()
        self.btn_select_all = QPushButton("Select All", self)
        self.btn_select_all.clicked.connect(self._select_all)
        self.btn_deselect_all = QPushButton("Deselect All", self)
        self.btn_deselect_all.clicked.connect(self._deselect_all)

        tools_layout.addWidget(self.btn_select_all)
        tools_layout.addWidget(self.btn_deselect_all)
        tools_layout.addStretch()
        layout.addLayout(tools_layout)

        # Bottom Bar
        bottom = QHBoxLayout()
        self.lbl_summary = QLabel("0 actions proposed.", self)
        bottom.addWidget(self.lbl_summary)
        bottom.addStretch()

        self.btn_execute = QPushButton("Execute Reorganization", self)
        self.btn_execute.setIcon(qta.icon("fa5s.check", color="#22c55e"))
        self.btn_execute.setStyleSheet("font-weight: 600; padding: 6px 16px;")
        self.btn_execute.clicked.connect(self._execute_plan)
        bottom.addWidget(self.btn_execute)

        self.btn_cancel = QPushButton("Cancel", self)
        self.btn_cancel.clicked.connect(self.reject)
        bottom.addWidget(self.btn_cancel)

        layout.addLayout(bottom)

    def start_analysis(self):
        self.progress_bar.setValue(0)
        self.table.setRowCount(0)
        self.btn_execute.setEnabled(False)

        self.worker = AIOrganizerWorker(self.target_folder, rename_smart=True)
        self.worker.progress_updated.connect(self._on_progress)
        self.worker.plan_generated.connect(self._on_plan_ready)
        self.worker.start()

    def _on_progress(self, pct: int, msg: str):
        self.progress_bar.setValue(pct)
        self.lbl_status.setText(msg)

    def _on_plan_ready(self, items: List[OrganizationPlanItem]):
        self.plan_items = items
        self.table.setRowCount(len(items))

        for row, item in enumerate(items):
            # Checkbox Item
            chk_item = QTableWidgetItem()
            chk_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            chk_item.setCheckState(Qt.CheckState.Checked)
            self.table.setItem(row, 0, chk_item)

            # Original
            orig_item = QTableWidgetItem(item.source.name)
            self.table.setItem(row, 1, orig_item)

            # Proposed
            prop_item = QTableWidgetItem(item.proposed_name)
            self.table.setItem(row, 2, prop_item)

            # Category
            cat_item = QTableWidgetItem(item.category)
            self.table.setItem(row, 3, cat_item)

            # Confidence
            conf_str = f"{int(item.confidence * 100)}%"
            conf_item = QTableWidgetItem(conf_str)
            conf_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 4, conf_item)

        self.lbl_summary.setText(f"{len(items)} items ready to be organized.")
        self.btn_execute.setEnabled(len(items) > 0)

    def _select_all(self):
        for r in range(self.table.rowCount()):
            self.table.item(r, 0).setCheckState(Qt.CheckState.Checked)

    def _deselect_all(self):
        for r in range(self.table.rowCount()):
            self.table.item(r, 0).setCheckState(Qt.CheckState.Unchecked)

    def _execute_plan(self):
        selected_indices = [
            r for r in range(self.table.rowCount())
            if self.table.item(r, 0).checkState() == Qt.CheckState.Checked
        ]

        if not selected_indices:
            QMessageBox.information(self, "No Selection", "Please check at least one file to organize.")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Reorganization",
            f"Are you ready to organize {len(selected_indices)} file(s) into category folders?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        moved_count = 0
        for r in selected_indices:
            item = self.plan_items[r]
            try:
                item.destination.parent.mkdir(parents=True, exist_ok=True)
                dest = item.destination
                counter = 1
                while dest.exists():
                    dest = item.destination.parent / f"{item.destination.stem} ({counter}){item.destination.suffix}"
                    counter += 1
                shutil.move(item.source, dest)
                moved_count += 1
            except Exception as e:
                print(f"Error moving {item.source}: {e}")

        QMessageBox.information(
            self, "Done", f"Successfully organized {moved_count} file(s)!"
        )
        self.accept()
