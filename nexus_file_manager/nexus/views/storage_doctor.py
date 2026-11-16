"""StorageDoctorView – treemap page [spec Screen 4]: drill-down breadcrumb, colour legend, hover tooltips."""
from __future__ import annotations

from PyQt6.QtCore import QRectF, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QPainter
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from pathlib import Path

from nexus.components import Button, Card
from nexus.components._util import resolve_color
from nexus.components.breadcrumb import BreadcrumbBar
from nexus.components.treemap import TreemapWidget
from nexus.core.mock_data import MOCK_STORAGE_TREE, format_size
from nexus.styles.theme_manager import theme_manager
from nexus.tokens.base import SPACE_LG, SPACE_MD, SPACE_SM, SPACE_XL
from nexus.tokens.color_utils import to_qcolor
from nexus.tokens.file_types import TREEMAP_CATEGORY_COLORS, TREEMAP_CATEGORY_LABELS


class _LegendItem(QWidget):
    def __init__(self, category: str):
        super().__init__()
        self._cat = category
        self._label = TREEMAP_CATEGORY_LABELS[category]
        self.setFixedSize(self.fontMetrics().horizontalAdvance(self._label) + 26, 20)
        theme_manager().theme_changed.connect(self._on_theme_changed)

    def _on_theme_changed(self, _tokens) -> None:
        self.update()

    def paintEvent(self, event):
        t = theme_manager().tokens
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(to_qcolor(resolve_color(TREEMAP_CATEGORY_COLORS[self._cat], t)))
        p.drawRoundedRect(QRectF(0, 5, 10, 10), t.RADIUS_SM, t.RADIUS_SM)
        p.setPen(to_qcolor(t.COLOR_TEXT_SECONDARY))
        p.drawText(QRectF(18, 0, self.width() - 18, 20), Qt.AlignmentFlag.AlignVCenter, self._label)
        p.end()


class StorageDoctorView(QWidget):
    scanRequested = pyqtSignal()        # HOOK: backend.storage_scan_requested
    targetRequested = pyqtSignal(str)   # explicit drive or folder path to scan

    BASE_SEGMENTS = ["C:", "Users"]     # drive/location prefix shown before the tree root (spec default)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.base_segments = list(self.BASE_SEGMENTS)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(SPACE_XL, SPACE_LG, SPACE_XL, SPACE_XL)
        lay.setSpacing(SPACE_MD)

        head = QHBoxLayout()
        titles = QVBoxLayout()
        titles.setSpacing(2)
        title = QLabel("Storage Doctor")
        title.setProperty("role", "heading")
        self.subtitle = QLabel()
        self.subtitle.setProperty("role", "muted")
        titles.addWidget(title)
        titles.addWidget(self.subtitle)
        head.addLayout(titles, 1)

        self._target_bar = QHBoxLayout()
        self._target_bar.setSpacing(SPACE_SM)
        head.addLayout(self._target_bar)

        self.btn_scan = Button("Rescan", icon="refresh")
        self.btn_scan.clicked.connect(lambda: self.scanRequested.emit())
        head.addWidget(self.btn_scan, 0, Qt.AlignmentFlag.AlignTop)
        lay.addLayout(head)

        self.breadcrumb = BreadcrumbBar(editable=False)
        self.breadcrumb.segmentActivated.connect(self._on_crumb)
        lay.addWidget(self.breadcrumb)

        legend = QHBoxLayout()
        legend.setSpacing(SPACE_MD)
        for cat in TREEMAP_CATEGORY_LABELS:
            legend.addWidget(_LegendItem(cat))
        legend.addStretch(1)
        self.hint = QLabel("Click a folder to drill in · hover for details")
        self.hint.setProperty("role", "muted")
        legend.addWidget(self.hint)
        lay.addLayout(legend)

        card = Card("card")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(SPACE_SM, SPACE_SM, SPACE_SM, SPACE_SM)
        self.treemap = TreemapWidget()
        cl.addWidget(self.treemap)
        lay.addWidget(card, 1)

        self.treemap.pathChanged.connect(self._on_path)
        self.load(MOCK_STORAGE_TREE)

    def set_targets(self, targets: list[tuple[str, str]]) -> None:
        """Populate quick-target drive/folder buttons in the header."""
        while self._target_bar.count():
            item = self._target_bar.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for label, path in targets:
            btn = Button(label, icon="hard-drive", variant="ghost")
            btn.clicked.connect(lambda _=False, p=path: self.targetRequested.emit(p))
            self._target_bar.addWidget(btn)

    def load(self, root: dict, base_segments: list[str] | None = None) -> None:
        if base_segments is not None:
            self.base_segments = list(base_segments)
        elif "base_path" in root:
            p = Path(root["base_path"])
            parts = [part.rstrip("\\") for part in p.parts if part]
            if parts and parts[-1] == root.get("name"):
                self.base_segments = parts[:-1]
            else:
                self.base_segments = parts
        else:
            self.base_segments = list(self.BASE_SEGMENTS)
        self.treemap.set_root(root)

    def _on_path(self, names: list[str]) -> None:
        # names[0] is the tree root
        self.breadcrumb.set_segments(self.base_segments + names)
        cur = self.treemap.current
        total = self.treemap._size(cur)
        self.subtitle.setText(f"{cur['name']} · {format_size(total)} across {len(cur.get('children', []))} items")

    def _on_crumb(self, idx: int) -> None:
        self.treemap.navigate_to(max(0, idx - len(self.base_segments)))
