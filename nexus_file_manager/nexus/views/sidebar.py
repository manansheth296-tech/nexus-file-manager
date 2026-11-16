"""Sidebar (~220px): QUICK ACCESS, DRIVES (usage bars), SPECIALIZED TOOLS [spec Screen 1]."""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget

from nexus.components import Divider
from nexus.components.drive_item import DriveItem
from nexus.components.sidebar_item import SidebarItem
from nexus.core.backend import BackendHooks
from nexus.core.mock_data import DRIVES, QUICK_ACCESS, TOOLS
from nexus.tokens.base import SIDEBAR_WIDTH, SPACE_LG, SPACE_MD, SPACE_SM, SPACE_XS


class Sidebar(QFrame):
    locationRequested = pyqtSignal(str)   # a quick-access folder or drive path
    toolRequested = pyqtSignal(str)       # 'storage_doctor' | 'duplicate_hunter' | 'ai_organizer' | 'encrypted_vault'

    def __init__(self, backend: BackendHooks | None = None, parent: QWidget | None = None):
        if isinstance(backend, QWidget) and parent is None:
            parent, backend = backend, None
        super().__init__(parent)
        self.setProperty("surface", "surface")
        self.setFixedWidth(SIDEBAR_WIDTH)
        self._items: dict[str, SidebarItem] = {}
        self.backend = backend

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        body = QWidget()
        col = QVBoxLayout(body)
        col.setContentsMargins(SPACE_SM, SPACE_SM, SPACE_SM, SPACE_MD)
        col.setSpacing(2)
        scroll.setWidget(body)
        outer.addWidget(scroll, 1)
        outer.addWidget(Divider(vertical=True))

        qa_items = backend.get_quick_access() if backend else QUICK_ACCESS
        col.addWidget(self._header("Quick access", first=True))
        for label, icon, badge, path in qa_items:
            item = SidebarItem(label, icon, badge, key=f"path:{path}")
            item.clicked.connect(lambda _=False, p=path: self.locationRequested.emit(p))
            self._add(col, item)

        drive_items = backend.get_drives() if backend else DRIVES
        col.addWidget(self._header("Drives"))
        for d in drive_items:
            item = DriveItem(d["label"], d["used"], d["total"], key=f"path:{d['path']}")
            item.clicked.connect(lambda _=False, p=d["path"]: self.locationRequested.emit(p))
            self._add(col, item)

        col.addWidget(self._header("Specialized tools"))
        for label, icon, key in TOOLS:
            item = SidebarItem(label, icon, None, key=f"tool:{key}")
            item.clicked.connect(lambda _=False, k=key: self.toolRequested.emit(k))
            self._add(col, item)
        col.addStretch(1)

    def _add(self, col: QVBoxLayout, item: SidebarItem) -> None:
        self._items[item.key] = item
        col.addWidget(item)

    @staticmethod
    def _header(text: str, first: bool = False) -> QLabel:
        lab = QLabel(text.upper())
        lab.setProperty("role", "caption")
        lab.setContentsMargins(SPACE_MD, SPACE_XS if first else SPACE_LG, 0, SPACE_XS)
        return lab

    # ── API ───────────────────────────────────────────────────────────────
    def key_for_path(self, path: str) -> str | None:
        key = f"path:{path}"
        return key if key in self._items else None

    def set_active(self, key: str | None) -> None:
        for k, item in self._items.items():
            item.set_active(k == key)
