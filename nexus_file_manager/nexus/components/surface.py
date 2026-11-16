"""Card / Panel / Divider – QFrame wrappers whose look is 100% QSS (`surface` property)."""
from __future__ import annotations

from PyQt6.QtWidgets import QFrame, QWidget


class Card(QFrame):
    """surface: 'card' (bordered, translucent) | 'surface' (sidebar/panel) | 'base'."""

    def __init__(self, surface: str = "card", parent: QWidget | None = None):
        super().__init__(parent)
        self.setProperty("surface", surface)


class Divider(QFrame):
    def __init__(self, vertical: bool = False, parent: QWidget | None = None):
        super().__init__(parent)
        self.setProperty("divider", "v" if vertical else "h")
        self.setFrameShape(QFrame.Shape.NoFrame)
