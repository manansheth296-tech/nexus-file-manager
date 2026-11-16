"""Ultra-fast, asynchronous multi-format file preview panel with thread safety."""

import datetime
from pathlib import Path
from typing import Optional, Dict
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTextEdit, QScrollArea, QFrame,
    QHBoxLayout, QStackedWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QListWidget, QListWidgetItem, QSizePolicy
)
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtCore import Qt, QSize
import qtawesome as qta

from src.config import format_size, get_file_icon_info
from src.modules.preview_loader import AsyncPreviewWorker, PreviewData


class PreviewPanel(QWidget):
    """High-speed asynchronous inspector panel supporting images, docs, sheets, archives, and hex."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setMinimumWidth(280)
        self.setMaximumWidth(420)
        self.current_request_id = 0
        self.active_worker: Optional[AsyncPreviewWorker] = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Panel Header
        header = QHBoxLayout()
        icon_lbl = QLabel(self)
        icon_lbl.setPixmap(qta.icon("fa5s.eye", color="#38BDF8").pixmap(18, 18))
        header.addWidget(icon_lbl)

        title = QLabel("Quick Preview", self)
        title.setStyleSheet("font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # Visual Preview Stack
        self.preview_container = QFrame(self)
        self.preview_container.setMinimumHeight(220)
        self.preview_container.setFrameShape(QFrame.Shape.StyledPanel)
        self.preview_container.setStyleSheet(
            "QFrame { background-color: rgba(0, 0, 0, 0.25); border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.08); }"
        )
        container_layout = QVBoxLayout(self.preview_container)
        container_layout.setContentsMargins(4, 4, 4, 4)

        self.stack = QStackedWidget(self.preview_container)

        # Page 0: Image / PDF Pixmap view
        self.image_view = QLabel(self.stack)
        self.image_view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.stack.addWidget(self.image_view)

        # Page 1: Text / Code / Hex / Word view
        self.text_view = QTextEdit(self.stack)
        self.text_view.setReadOnly(True)
        self.text_view.setFont(QFont("Consolas", 10))
        self.text_view.setStyleSheet("QTextEdit { background: transparent; border: none; font-size: 11px; }")
        self.stack.addWidget(self.text_view)

        # Page 2: Spreadsheet Table view
        self.table_view = QTableWidget(self.stack)
        self.table_view.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_view.setShowGrid(True)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table_view.setStyleSheet("QTableWidget { background: transparent; border: none; font-size: 11px; }")
        self.stack.addWidget(self.table_view)

        # Page 3: Archive (Zip) listing view
        self.archive_view = QListWidget(self.stack)
        self.archive_view.setStyleSheet("QListWidget { background: transparent; border: none; font-size: 11px; }")
        self.stack.addWidget(self.archive_view)

        # Page 4: Audio / Media Visualizer Card
        self.media_card = QWidget(self.stack)
        media_layout = QVBoxLayout(self.media_card)
        media_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        media_layout.setSpacing(8)
        self.media_icon = QLabel(self.media_card)
        self.media_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        media_layout.addWidget(self.media_icon)
        self.media_title = QLabel("Audio Track", self.media_card)
        self.media_title.setStyleSheet("font-weight: 600; font-size: 13px; color: #38BDF8;")
        self.media_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        media_layout.addWidget(self.media_title)
        self.stack.addWidget(self.media_card)

        container_layout.addWidget(self.stack)
        layout.addWidget(self.preview_container)

        # Metadata Section
        self.meta_scroll = QScrollArea(self)
        self.meta_scroll.setWidgetResizable(True)
        self.meta_scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.meta_widget = QWidget()
        self.meta_layout = QVBoxLayout(self.meta_widget)
        self.meta_layout.setContentsMargins(2, 4, 2, 4)
        self.meta_layout.setSpacing(6)

        self.lbl_name = QLabel("Select an item to inspect", self.meta_widget)
        self.lbl_name.setWordWrap(True)
        self.lbl_name.setStyleSheet("font-weight: 600; font-size: 13px;")
        self.meta_layout.addWidget(self.lbl_name)

        self.meta_rows_container = QVBoxLayout()
        self.meta_rows_container.setSpacing(4)
        self.meta_layout.addLayout(self.meta_rows_container)

        self.meta_layout.addStretch()
        self.meta_scroll.setWidget(self.meta_widget)
        layout.addWidget(self.meta_scroll)

        self.clear_preview()

    def clear_preview(self):
        """Reset panel to empty state."""
        self.current_request_id += 1
        if self.active_worker:
            try:
                self.active_worker.preview_ready.disconnect()
            except Exception:
                pass
            self.active_worker.cancel()

        self.image_view.clear()
        self.text_view.clear()
        self.table_view.setRowCount(0)
        self.table_view.setColumnCount(0)
        self.archive_view.clear()
        self.lbl_name.setText("No item selected")
        self._clear_meta_rows()

    def _clear_meta_rows(self):
        while self.meta_rows_container.count():
            item = self.meta_rows_container.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def _add_meta_row(self, label: str, value: str):
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        lbl_k = QLabel(label)
        lbl_k.setStyleSheet("color: #94A3B8; font-size: 11px; font-weight: 500;")
        lbl_v = QLabel(value)
        lbl_v.setStyleSheet("color: #F8FAFC; font-size: 11px;")
        lbl_v.setWordWrap(True)
        row.addWidget(lbl_k)
        row.addStretch()
        row.addWidget(lbl_v)
        w = QWidget()
        w.setLayout(row)
        self.meta_rows_container.addWidget(w)

    def set_file(self, path: Optional[Path]):
        """Load and display preview for the given path using fast async worker."""
        if not path or not path.exists():
            self.clear_preview()
            return

        self.current_request_id += 1
        request_id = self.current_request_id

        # Safely disconnect old worker so it doesn't touch the UI when cancelled
        if self.active_worker:
            try:
                self.active_worker.preview_ready.disconnect()
            except Exception:
                pass
            self.active_worker.cancel()

        # 1. Instant metadata display on UI thread (< 1ms)
        self._clear_meta_rows()
        self.lbl_name.setText(path.name)

        try:
            stat = path.stat()
            size_str = format_size(stat.st_size) if not path.is_dir() else "Folder"
            mtime = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%b %d, %Y %H:%M")
            self._add_meta_row("Size", size_str)
            self._add_meta_row("Modified", mtime)
        except OSError:
            pass

        # If it's a directory, handle immediately without worker
        if path.is_dir():
            icon_name, color = get_file_icon_info(path)
            self._show_icon_preview(icon_name, color)
            try:
                count = len(list(path.iterdir()))
                self._add_meta_row("Items", str(count))
            except (PermissionError, OSError):
                pass
            return

        # 2. Spawn Async Preview Worker for heavy lifting
        self.active_worker = AsyncPreviewWorker(path, request_id, parent=self)
        self.active_worker.preview_ready.connect(self._on_preview_ready)
        self.active_worker.start()

    def _on_preview_ready(self, req_id: int, data: PreviewData):
        if req_id != self.current_request_id:
            return

        # Add extra metadata extracted by worker
        for k, v in data.extra_meta.items():
            self._add_meta_row(k, v)

        # Route to appropriate visual page
        # Note: QPixmap.fromImage MUST be called here on the GUI thread for thread safety
        if data.preview_type in ("image", "pdf") and data.qimage:
            pixmap = QPixmap.fromImage(data.qimage)
            scaled = pixmap.scaled(
                280, 210,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.image_view.setPixmap(scaled)
            self.stack.setCurrentIndex(0)

        elif data.preview_type in ("text", "word", "hex") and data.text_content:
            self.text_view.setPlainText(data.text_content)
            self.stack.setCurrentIndex(1)

        elif data.preview_type == "table" and data.table_data:
            rows = data.table_data
            if rows:
                col_count = max(len(r) for r in rows)
                self.table_view.setRowCount(len(rows))
                self.table_view.setColumnCount(col_count)
                for r_idx, row in enumerate(rows):
                    for c_idx in range(col_count):
                        val = row[c_idx] if c_idx < len(row) else ""
                        item = QTableWidgetItem(val)
                        self.table_view.setItem(r_idx, c_idx, item)
            self.stack.setCurrentIndex(2)

        elif data.preview_type == "archive" and data.archive_items:
            self.archive_view.clear()
            for item in data.archive_items:
                is_dir = item.get("is_dir") == "True"
                icon_name = "fa5s.folder" if is_dir else "fa5s.file"
                list_item = QListWidgetItem(
                    qta.icon(icon_name, color="#F59E0B" if is_dir else "#94A3B8"),
                    f"{item['name']} ({item['size']})"
                )
                self.archive_view.addItem(list_item)
            self.stack.setCurrentIndex(3)

        elif data.preview_type in ("audio", "video"):
            icon_name, color = get_file_icon_info(data.file_path)
            self.media_icon.setPixmap(qta.icon(icon_name, color=color).pixmap(56, 56))
            self.media_title.setText(data.file_path.name)
            self.stack.setCurrentIndex(4)

        else:
            icon_name, color = get_file_icon_info(data.file_path)
            self._show_icon_preview(icon_name, color)

    def _show_icon_preview(self, icon_name: str, color: str):
        pixmap = qta.icon(icon_name, color=color).pixmap(96, 96)
        self.image_view.setPixmap(pixmap)
        self.stack.setCurrentIndex(0)
