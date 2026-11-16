"""PreviewInspector – right sidebar (~300px) [spec Screen 3]: empty / single-file preview / multi-select."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFontMetrics
from PyQt6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QScrollArea, QStackedWidget, QVBoxLayout, QWidget)

from nexus.components import Badge, Divider
from nexus.components.icon_tile import IconTile
from nexus.core.mock_data import format_size
from nexus.tokens.base import INSPECTOR_WIDTH, PREVIEW_CARD_WIDTH, SPACE_LG, SPACE_MD, SPACE_SM, SPACE_XL
from nexus.tokens.file_types import kind_color, kind_icon
from nexus.views.previews import KeyValueList, make_preview


def _clear(layout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        if item.widget():
            w = item.widget()
            w.setParent(None)          # vanish now; deleteLater alone leaves it painted until the next loop pass
            w.deleteLater()
        elif item.layout():
            _clear(item.layout())


class PreviewInspector(QFrame):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setProperty("surface", "surface")
        self.setFixedWidth(INSPECTOR_WIDTH)
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(Divider(vertical=True))
        self.stack = QStackedWidget()
        outer.addWidget(self.stack, 1)

        # 0 – empty
        empty = QWidget()
        el = QVBoxLayout(empty)
        el.setAlignment(Qt.AlignmentFlag.AlignCenter)
        el.setSpacing(SPACE_MD)
        el.addWidget(IconTile("file", "COLOR_TEXT_MUTED", 48), 0, Qt.AlignmentFlag.AlignHCenter)
        title = QLabel("Nothing selected")
        title.setProperty("role", "subheading")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub = QLabel("Select a file to preview it here")
        sub.setProperty("role", "muted")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        el.addWidget(title)
        el.addWidget(sub)
        self.stack.addWidget(empty)

        # 1 – single file (scrollable)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        body = QWidget()
        self._single = QVBoxLayout(body)
        self._single.setContentsMargins(SPACE_LG, SPACE_LG, SPACE_LG, SPACE_XL)
        self._single.setSpacing(SPACE_LG)
        self._single.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(body)
        self.stack.addWidget(scroll)

        # 2 – multiple
        multi = QWidget()
        ml = QVBoxLayout(multi)
        ml.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ml.setSpacing(SPACE_MD)
        ml.addWidget(IconTile("copy", "COLOR_ACCENT_PRIMARY", 48), 0, Qt.AlignmentFlag.AlignHCenter)
        self._multi_title = QLabel()
        self._multi_title.setProperty("role", "subheading")
        self._multi_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._multi_sub = QLabel()
        self._multi_sub.setProperty("role", "muted")
        self._multi_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ml.addWidget(self._multi_title)
        ml.addWidget(self._multi_sub)
        self.stack.addWidget(multi)

    # ── API ───────────────────────────────────────────────────────────────
    def show_files(self, files: list[dict], location: str = "") -> None:
        if not files:
            self.stack.setCurrentIndex(0)
        elif len(files) == 1:
            self._show_single(files[0], location)
            self.stack.setCurrentIndex(1)
        else:
            total = sum(f["size"] or 0 for f in files)
            self._multi_title.setText(f"{len(files)} items selected")
            self._multi_sub.setText(f"Total size {format_size(total)}")
            self.stack.setCurrentIndex(2)

    @property
    def current_preview(self) -> QWidget | None:
        """The preview widget currently shown (for tests / design QA)."""
        return getattr(self, "_preview", None)

    def _show_single(self, f: dict, location: str) -> None:
        _clear(self._single)
        if "path" not in f and location:
            import os
            f = dict(f)
            f["path"] = os.path.join(location, f["name"])
        head = QHBoxLayout()
        head.setSpacing(SPACE_MD)
        head.addWidget(IconTile(kind_icon(f["kind"]), kind_color(f["kind"]), 40), 0, Qt.AlignmentFlag.AlignTop)
        names = QVBoxLayout()
        names.setSpacing(2)
        name = QLabel(QFontMetrics(self.font()).elidedText(f["name"], Qt.TextElideMode.ElideMiddle, 190))
        name.setProperty("role", "subheading")
        name.setToolTip(f["name"])
        typ = QLabel(f["type"])
        typ.setProperty("role", "muted")
        names.addWidget(name)
        names.addWidget(typ)
        head.addLayout(names, 1)
        self._single.addLayout(head)

        self._preview = make_preview(f)
        self._single.addWidget(self._preview)     # no alignment: keeps height-for-width working for wrapped text

        cap = QLabel("DETAILS")
        cap.setProperty("role", "caption")
        self._single.addWidget(cap)
        rows = [("Size", format_size(f["size"]) if f["size"] is not None else "—"),
                ("Type", f["type"]), ("Modified", f["modified"])]
        if location:
            rows.append(("Location", location))
        self._single.addWidget(KeyValueList(rows))
