"""
Button – states: Default, Hover, Pressed, Disabled, Focused (+ Checked for toggles).

variant: 'secondary' (default) | 'primary' | 'ghost' | 'danger'
Default / pressed / disabled / checked come from QSS; hover (animated) and focus ring are painted.
Icon-only buttons (empty text) are square. `set_compact(True)` collapses a labelled button
to icon-only for narrow windows (the label moves into the tooltip).
"""
from __future__ import annotations

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QPainter
from PyQt6.QtWidgets import QPushButton, QWidget

from nexus.assets import icon_loader
from nexus.components._interactive import InteractiveMixin
from nexus.components._util import set_prop
from nexus.styles.theme_manager import theme_manager
from nexus.tokens.base import ICON_SIZE_MD


class Button(InteractiveMixin, QPushButton):
    def __init__(self, text: str = "", icon: str | None = None, variant: str = "secondary",
                 parent: QWidget | None = None):
        super().__init__(text, parent)
        self._icon_name = icon
        self._label = text
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)      # ring shows for keyboard focus only
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setProperty("variant", variant)
        self.setProperty("iconOnly", bool(icon) and not text)
        if text:
            self.setToolTip(text)
        self._init_interactive("RADIUS_MD")
        self.setIconSize(QSize(ICON_SIZE_MD, ICON_SIZE_MD))
        self.toggled.connect(lambda _on: self._refresh_icon())
        self._refresh_icon()

    def set_variant(self, variant: str) -> None:
        set_prop(self, "variant", variant)
        self._refresh_icon()

    def set_compact(self, compact: bool) -> None:
        if not (self._icon_name and self._label):
            return
        self.setText("" if compact else self._label)
        set_prop(self, "iconOnly", compact)
        self.updateGeometry()

    def _refresh_icon(self) -> None:
        if not self._icon_name:
            return
        t = theme_manager().tokens
        variant = self.property("variant")
        normal = {"primary": t.COLOR_TEXT_ON_ACCENT, "danger": t.COLOR_TEXT_ON_DANGER,
                  "ghost": t.COLOR_TEXT_SECONDARY}.get(variant, t.COLOR_TEXT_PRIMARY)
        if variant == "ghost" and self.isChecked():
            normal = t.COLOR_ACCENT_PRIMARY
        self.setIcon(icon_loader.make_icon(self._icon_name, normal, t.COLOR_TEXT_MUTED))

    def _on_theme_changed(self, _tokens) -> None:
        self._refresh_icon()
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)                         # QSS draws bg/border/text/icon
        p = QPainter(self)
        self._paint_interactive_overlay(p)
        p.end()
