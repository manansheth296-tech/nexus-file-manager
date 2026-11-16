"""
NexusDialog – frameless, rounded (radius-xl), drop-shadowed modal shell shared by all dialogs.

The window is the spec's dialog size plus a transparent DIALOG_SHADOW_MARGIN on every side (room for the
shadow). Header = icon tile + title/subtitle + close; drag the header to move. Esc closes. Subclasses fill
`self.body` (a plain QWidget under the header divider).
"""
from __future__ import annotations

from PyQt6.QtCore import QPoint, Qt, QTimer
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (QDialog, QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel, QVBoxLayout, QWidget)

from nexus.components.button import Button
from nexus.components.icon_tile import IconTile
from nexus.components.surface import Divider
from nexus.styles.theme_manager import theme_manager
from nexus.tokens.base import DIALOG_HEADER_HEIGHT, DIALOG_SHADOW_MARGIN, SPACE_LG, SPACE_MD, SPACE_XL
from nexus.tokens.color_utils import to_qcolor


class NexusDialog(QDialog):
    def __init__(self, title: str, subtitle: str, icon: str, icon_color: str, size: tuple[int, int],
                 parent: QWidget | None = None):
        super().__init__(parent, Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setProperty("nexusDialog", True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.content_size = size
        m = DIALOG_SHADOW_MARGIN
        self.setFixedSize(size[0] + 2 * m, size[1] + 2 * m)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(m, m, m, m)
        self.panel = QFrame()
        self.panel.setProperty("surface", "dialog")
        outer.addWidget(self.panel)
        self._shadow = QGraphicsDropShadowEffect(self.panel)
        self._shadow.setBlurRadius(48)
        self._shadow.setOffset(0, 12)
        self.panel.setGraphicsEffect(self._shadow)
        theme_manager().theme_changed.connect(self._on_theme_changed)
        self._on_theme_changed(None)

        col = QVBoxLayout(self.panel)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(0)
        self.header = QWidget()
        self.header.setFixedHeight(DIALOG_HEADER_HEIGHT)
        hl = QHBoxLayout(self.header)
        hl.setContentsMargins(SPACE_XL, 0, SPACE_LG, 0)
        hl.setSpacing(SPACE_MD)
        self.icon_tile = IconTile(icon, icon_color, 40)
        hl.addWidget(self.icon_tile)
        titles = QVBoxLayout()
        titles.setSpacing(0)
        self.title_label = QLabel(title)
        self.title_label.setProperty("role", "subheading")
        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setProperty("role", "muted")
        titles.addStretch(1)
        titles.addWidget(self.title_label)
        titles.addWidget(self.subtitle_label)
        titles.addStretch(1)
        hl.addLayout(titles, 1)
        self.btn_close = Button(icon="x", variant="ghost")
        self.btn_close.setToolTip("Close (Esc)")
        self.btn_close.clicked.connect(self.reject)
        hl.addWidget(self.btn_close)
        col.addWidget(self.header)
        col.addWidget(Divider())
        self.body = QWidget()
        col.addWidget(self.body, 1)
        self._drag: QPoint | None = None

    def set_subtitle(self, text: str) -> None:
        self.subtitle_label.setText(text)

    def _on_theme_changed(self, _tokens) -> None:
        c = to_qcolor(theme_manager().tokens.COLOR_SHADOW)
        self._shadow.setColor(QColor(c))

    def footer_divider(self) -> Divider:
        return Divider()

    # centre over the parent window, and drag by the header
    def showEvent(self, e):
        parent = self.parentWidget()
        if parent is not None:
            g = parent.window().frameGeometry()
            self.move(g.center() - self.rect().center())
        super().showEvent(e)
        QTimer.singleShot(0, self._settle_focus)

    def _settle_focus(self) -> None:
        """Qt hands initial focus to the first button (the close icon) and paints a ring on it; park focus on the
        dialog itself unless a subclass already focused something meaningful (search / password field)."""
        fw = self.focusWidget()
        if fw is None or fw is self.btn_close:
            self.setFocus()

    def mousePressEvent(self, e):
        top = DIALOG_SHADOW_MARGIN
        if e.button() == Qt.MouseButton.LeftButton and top <= e.position().y() <= top + DIALOG_HEADER_HEIGHT:
            self._drag = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self._drag is not None:
            self.move(e.globalPosition().toPoint() - self._drag)
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        self._drag = None
        super().mouseReleaseEvent(e)
