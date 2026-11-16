"""PasswordField (reveal toggle) + StrengthMeter (4 segments + label) for the Safe Locker."""
from __future__ import annotations

from PyQt6.QtCore import QRectF, QSize, Qt
from PyQt6.QtGui import QAction, QFont, QPainter
from PyQt6.QtWidgets import QLineEdit, QWidget

from nexus.assets import icon_loader
from nexus.components.input_field import InputField
from nexus.core.strength import LABELS
from nexus.styles.theme_manager import theme_manager
from nexus.tokens.base import FONT_SIZE_XS, SPACE_SM
from nexus.tokens.color_utils import to_qcolor


class PasswordField(InputField):
    def __init__(self, placeholder: str = "Password", parent: QWidget | None = None):
        super().__init__(placeholder, icon="lock", parent=parent)
        self.setEchoMode(QLineEdit.EchoMode.Password)
        self._reveal = QAction(self)
        self._reveal.setToolTip("Show / hide password")
        self._reveal.triggered.connect(self.toggle_reveal)
        self.addAction(self._reveal, QLineEdit.ActionPosition.TrailingPosition)
        self._refresh_reveal_icon()

    @property
    def revealed(self) -> bool:
        return self.echoMode() == QLineEdit.EchoMode.Normal

    def toggle_reveal(self) -> None:
        self.setEchoMode(QLineEdit.EchoMode.Password if self.revealed else QLineEdit.EchoMode.Normal)
        self._refresh_reveal_icon()

    def _refresh_reveal_icon(self) -> None:
        t = theme_manager().tokens
        self._reveal.setIcon(icon_loader.make_icon("eye-off" if self.revealed else "eye", t.COLOR_TEXT_MUTED))

    def _on_theme_changed(self, tokens) -> None:
        super()._on_theme_changed(tokens)
        self._refresh_reveal_icon()


class StrengthMeter(QWidget):
    GAP, BAR_H = 4, 4

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._level = 0
        self._empty = True
        self.setFixedHeight(16)
        theme_manager().theme_changed.connect(self._on_theme_changed)

    @property
    def level(self) -> int:
        return self._level

    def set_level(self, level: int, empty: bool = False) -> None:
        self._level, self._empty = level, empty
        self.update()

    def _on_theme_changed(self, _t) -> None:
        self.update()

    def sizeHint(self) -> QSize:
        return QSize(240, 16)

    def paintEvent(self, event):
        t = theme_manager().tokens
        colors = [t.COLOR_DANGER, t.COLOR_WARNING, t.COLOR_ACCENT_PRIMARY, t.COLOR_SUCCESS]
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        label_w = 64
        bars_w = self.width() - label_w - SPACE_SM
        seg_w = (bars_w - 3 * self.GAP) / 4
        p.setPen(Qt.PenStyle.NoPen)
        for i in range(4):
            lit = not self._empty and i < max(self._level, 1 if not self._empty else 0)
            color = colors[max(self._level - 1, 0)] if lit else None
            p.setBrush(to_qcolor(color) if color else to_qcolor(t.COLOR_BORDER_STRONG))
            p.drawRoundedRect(QRectF(i * (seg_w + self.GAP), (self.height() - self.BAR_H) / 2, seg_w, self.BAR_H), 2, 2)
        font = QFont(self.font())
        font.setPixelSize(FONT_SIZE_XS)
        font.setWeight(QFont.Weight.DemiBold)
        p.setFont(font)
        p.setPen(to_qcolor(t.COLOR_TEXT_MUTED if self._empty else colors[max(self._level - 1, 0)]))
        p.drawText(QRectF(self.width() - label_w, 0, label_w, self.height()),
                   Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                   "" if self._empty else LABELS[self._level])
        p.end()
