"""Interactive WinDirStat-style squarified treemap canvas widget with drill-down."""

from pathlib import Path
from typing import List, Optional, Tuple
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QToolTip, QFrame
)
from PyQt6.QtCore import Qt, QRectF, pyqtSignal, QPoint
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPaintEvent, QMouseEvent

from src.config import format_size, FILE_CATEGORIES
from src.modules.storage_analyzer import (
    TreemapNode,
    StorageScanWorker,
    calculate_squarified_treemap,
)
import qtawesome as qta

# Modern harmonious palette for categories
PALETTE = {
    "video": QColor("#a855f7"),      # Purple
    "images": QColor("#10b981"),     # Emerald Green
    "audio": QColor("#8b5cf6"),      # Violet
    "code": QColor("#38bdf8"),       # Electric Sky Blue
    "archives": QColor("#f59e0b"),   # Amber
    "documents": QColor("#cbd5e1"),  # Light Slate
    "word": QColor("#2563eb"),       # Word Blue
    "excel": QColor("#16a34a"),      # Excel Green
    "powerpoint": QColor("#ea580c"), # PPT Orange
    "pdf": QColor("#ef4444"),        # PDF Red
    "binaries": QColor("#64748b"),   # Slate
    "other": QColor("#64748b"),      # Slate
    "folder": QColor("#334155"),     # Dark slate
}


class TreemapCanvas(QWidget):
    """Paints squarified rectangles with mouse hover tooltips and drill-down clicks."""

    node_clicked = pyqtSignal(TreemapNode)
    node_double_clicked = pyqtSignal(TreemapNode)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.root_node: Optional[TreemapNode] = None
        self.hovered_node: Optional[TreemapNode] = None
        self.nodes_to_draw: List[TreemapNode] = []
        self.setMinimumSize(400, 300)

    def set_data(self, root: TreemapNode):
        self.root_node = root
        self.nodes_to_draw = []
        if root and root.children:
            self.nodes_to_draw = root.children
        elif root:
            self.nodes_to_draw = [root]
        self._recompute_layout()
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._recompute_layout()

    def _recompute_layout(self):
        if not self.nodes_to_draw:
            return
        w = max(10.0, float(self.width() - 4))
        h = max(10.0, float(self.height() - 4))
        calculate_squarified_treemap(self.nodes_to_draw, 2.0, 2.0, w, h)

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        # Background
        painter.fillRect(self.rect(), QColor("#111827"))

        if not self.nodes_to_draw:
            painter.setPen(QColor("#9CA3AF"))
            painter.setFont(QFont("Segoe UI", 12))
            painter.drawText(
                self.rect(), Qt.AlignmentFlag.AlignCenter, "No files scanned or folder is empty"
            )
            return

        font_large = QFont("Segoe UI", 9, QFont.Weight.DemiBold)
        font_small = QFont("Segoe UI", 8)

        for node in self.nodes_to_draw:
            x, y, w, h = node.rect
            if w <= 1 or h <= 1:
                continue

            rect = QRectF(x, y, w, h)
            color = self._get_node_color(node)

            if node == self.hovered_node:
                # Highlight hovered rectangle
                painter.setBrush(QBrush(color.lighter(130)))
                painter.setPen(QPen(QColor("#FFFFFF"), 2))
            else:
                painter.setBrush(QBrush(color))
                painter.setPen(QPen(QColor("#1F2937"), 1))

            painter.drawRect(rect)

            # Draw text if rectangle is big enough
            if w > 65 and h > 35:
                painter.setPen(QColor("#FFFFFF"))
                painter.setFont(font_large)
                text_rect = QRectF(x + 4, y + 4, w - 8, 16)
                painter.drawText(
                    text_rect,
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                    node.name,
                )

                painter.setPen(QColor("#E5E7EB"))
                painter.setFont(font_small)
                size_rect = QRectF(x + 4, y + 20, w - 8, 14)
                painter.drawText(
                    size_rect,
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                    format_size(node.size),
                )

    def _get_node_color(self, node: TreemapNode) -> QColor:
        if node.is_dir:
            return PALETTE["folder"]
        ext = node.path.suffix.lower()
        for cat, exts in FILE_CATEGORIES.items():
            if ext in exts:
                return PALETTE.get(cat, PALETTE["other"])
        return PALETTE["other"]

    def mouseMoveEvent(self, event: QMouseEvent):
        pos = event.position()
        found = None
        for node in self.nodes_to_draw:
            x, y, w, h = node.rect
            if x <= pos.x() <= x + w and y <= pos.y() <= y + h:
                found = node
                break

        if found != self.hovered_node:
            self.hovered_node = found
            if found:
                tip = f"{found.name}\nSize: {format_size(found.size)}\nType: {'Folder' if found.is_dir else found.path.suffix.upper() or 'File'}"
                QToolTip.showText(event.globalPosition().toPoint(), tip, self)
            else:
                QToolTip.hideText()
            self.update()

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if self.hovered_node:
            self.node_double_clicked.emit(self.hovered_node)


class StorageAnalyzerWidget(QWidget):
    """Storage Doctor view containing Treemap Canvas, scanner controls, and stats bar."""

    navigate_to_path = pyqtSignal(Path)

    def __init__(self, target_dir: Path, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.target_dir = target_dir
        self.scan_worker: Optional[StorageScanWorker] = None
        self._init_ui()
        self.start_scan(self.target_dir)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Top Bar
        top_bar = QHBoxLayout()
        self.lbl_title = QLabel(f"Storage Treemap: {self.target_dir.name}", self)
        self.lbl_title.setStyleSheet("font-size: 15px; font-weight: 600; color: #38bdf8;")
        top_bar.addWidget(self.lbl_title)
        top_bar.addStretch()

        self.btn_rescan = QPushButton("Rescan", self)
        self.btn_rescan.setIcon(qta.icon("fa5s.sync-alt"))
        self.btn_rescan.clicked.connect(lambda: self.start_scan(self.target_dir))
        top_bar.addWidget(self.btn_rescan)
        layout.addLayout(top_bar)

        # Progress Indicator
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 0)  # indeterminate
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)

        # Treemap Canvas
        self.canvas = TreemapCanvas(self)
        self.canvas.node_double_clicked.connect(self._on_node_double_clicked)
        layout.addWidget(self.canvas, stretch=1)

        # Bottom Stats Bar
        self.stats_bar = QFrame(self)
        self.stats_bar.setStyleSheet("background: rgba(255, 255, 255, 0.04); border-radius: 6px; padding: 4px;")
        stats_layout = QHBoxLayout(self.stats_bar)
        self.lbl_stats = QLabel("Scanning directory...", self.stats_bar)
        stats_layout.addWidget(self.lbl_stats)
        layout.addWidget(self.stats_bar)

    def start_scan(self, path: Path):
        self.target_dir = path
        self.lbl_title.setText(f"Storage Treemap: {self.target_dir}")
        self.progress_bar.show()
        self.lbl_stats.setText("Calculating disk space...")

        if self.scan_worker and self.scan_worker.isRunning():
            self.scan_worker.cancel()
            self.scan_worker.wait()

        self.scan_worker = StorageScanWorker(self.target_dir, max_depth=3)
        self.scan_worker.progress_updated.connect(lambda count, p: self.lbl_stats.setText(f"Scanned {count} items: {p}"))
        self.scan_worker.scan_completed.connect(self._on_scan_completed)
        self.scan_worker.start()

    def _on_scan_completed(self, root_node: TreemapNode, cat_stats: dict):
        self.progress_bar.hide()
        self.canvas.set_data(root_node)
        summary = f"Total Size: {format_size(root_node.size)}  |  Folders/Files: {len(root_node.children)}"
        self.lbl_stats.setText(summary)

    def _on_node_double_clicked(self, node: TreemapNode):
        if node.is_dir:
            self.start_scan(node.path)
            self.navigate_to_path.emit(node.path)
        else:
            self.navigate_to_path.emit(node.path.parent)
