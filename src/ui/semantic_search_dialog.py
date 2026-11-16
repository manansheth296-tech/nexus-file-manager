"""Semantic & Content Search Dialog: search inside documents with TF-IDF relevance ranking."""

from pathlib import Path
from typing import List, Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QProgressBar, QFrame,
    QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont
import qtawesome as qta

from src.config import get_file_icon_name
from src.modules.semantic_search import ContentSearchWorker, SearchResult


class SemanticSearchDialog(QDialog):
    """Dialog to search inside file contents (PDFs, Code, Markdown, Docs) by concept/query."""

    file_activated = pyqtSignal(Path)

    def __init__(self, target_dir: Path, parent: Optional[QDialog] = None):
        super().__init__(parent)
        self.target_dir = target_dir
        self.worker: Optional[ContentSearchWorker] = None

        self.setWindowTitle("Content & Semantic Document Search")
        self.resize(780, 520)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Header
        header = QHBoxLayout()
        icon = QLabel(self)
        icon.setPixmap(qta.icon("fa5s.search", color="#38bdf8").pixmap(28, 28))
        header.addWidget(icon)

        title_box = QVBoxLayout()
        title = QLabel(f"Search Inside Files: {self.target_dir.name}", self)
        title.setStyleSheet("font-size: 15px; font-weight: 600; color: #FFFFFF;")
        subtitle = QLabel("Full-text TF-IDF search across PDFs, Markdown, Text, Code, and Docs", self)
        subtitle.setStyleSheet("color: #94A3B8; font-size: 12px;")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)
        header.addStretch()

        layout.addLayout(header)

        # Search Bar
        search_box = QHBoxLayout()
        self.search_edit = QLineEdit(self)
        self.search_edit.setPlaceholderText("Search for keywords, phrases, or topics inside documents...")
        self.search_edit.returnPressed.connect(self._start_search)
        search_box.addWidget(self.search_edit)

        self.btn_search = QPushButton("Search", self)
        self.btn_search.setIcon(qta.icon("fa5s.search"))
        self.btn_search.clicked.connect(self._start_search)
        search_box.addWidget(self.btn_search)
        layout.addLayout(search_box)

        # Progress
        self.lbl_status = QLabel("Enter a query and press Search.", self)
        layout.addWidget(self.lbl_status)
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # Results List
        self.results_list = QListWidget(self)
        self.results_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.results_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.results_list, stretch=1)

        # Bottom
        bottom = QHBoxLayout()
        self.lbl_count = QLabel("0 results.", self)
        bottom.addWidget(self.lbl_count)
        bottom.addStretch()

        self.btn_open = QPushButton("Open File", self)
        self.btn_open.clicked.connect(self._open_selected)
        bottom.addWidget(self.btn_open)

        self.btn_close = QPushButton("Close", self)
        self.btn_close.clicked.connect(self.accept)
        bottom.addWidget(self.btn_close)

        layout.addLayout(bottom)

    def _start_search(self):
        query = self.search_edit.text().strip()
        if not query:
            return

        self.results_list.clear()
        self.progress_bar.show()
        self.progress_bar.setValue(0)
        self.lbl_status.setText(f"Searching for '{query}'...")

        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait()

        self.worker = ContentSearchWorker(self.target_dir, query)
        self.worker.progress_updated.connect(self._on_progress)
        self.worker.search_completed.connect(self._on_results)
        self.worker.start()

    def _on_progress(self, pct: int, msg: str):
        self.progress_bar.setValue(pct)
        self.lbl_status.setText(msg)

    def _on_results(self, results: List[SearchResult]):
        self.progress_bar.hide()
        self.results_list.clear()
        self.lbl_count.setText(f"{len(results)} matching document(s) found.")

        for r in results:
            icon_name = get_file_icon_name(r.file_path)
            item = QListWidgetItem(self.results_list)
            item.setData(Qt.ItemDataRole.UserRole, str(r.file_path))
            item.setSizeHint(QSize(0, 68))

            # Custom result widget
            w = QFrame()
            w_layout = QVBoxLayout(w)
            w_layout.setContentsMargins(8, 6, 8, 6)
            w_layout.setSpacing(2)

            top_row = QHBoxLayout()
            icon_lbl = QLabel()
            icon_lbl.setPixmap(qta.icon(icon_name, color="#38bdf8").pixmap(18, 18))
            top_row.addWidget(icon_lbl)

            name_lbl = QLabel(r.file_path.name)
            name_lbl.setStyleSheet("font-weight: 600; font-size: 13px; color: #FFFFFF;")
            top_row.addWidget(name_lbl)

            score_badge = QLabel(f"Relevance: {int(min(1.0, r.score) * 100)}%")
            score_badge.setStyleSheet(
                "background-color: rgba(56, 189, 248, 0.2); color: #38bdf8; padding: 2px 6px; border-radius: 4px; font-size: 11px;"
            )
            top_row.addWidget(score_badge)
            top_row.addStretch()

            w_layout.addLayout(top_row)

            snippet_lbl = QLabel(r.snippet)
            snippet_lbl.setStyleSheet("color: #94A3B8; font-size: 11px;")
            snippet_lbl.setWordWrap(True)
            w_layout.addWidget(snippet_lbl)

            self.results_list.setItemWidget(item, w)

    def _open_selected(self):
        item = self.results_list.currentItem()
        if item:
            self._on_item_double_clicked(item)

    def _on_item_double_clicked(self, item: QListWidgetItem):
        p_str = item.data(Qt.ItemDataRole.UserRole)
        if p_str:
            self.file_activated.emit(Path(p_str))
            self.accept()
