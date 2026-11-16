"""NexusStatusBar – left: item/selection count + size; right: async transfer progress [spec Screen 1]."""
from __future__ import annotations

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QProgressBar, QStatusBar, QWidget

from nexus.core.mock_data import format_size
from nexus.tokens.base import SPACE_LG, SPACE_MD, STATUSBAR_HEIGHT


class NexusStatusBar(QStatusBar):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setSizeGripEnabled(False)
        self.setFixedHeight(STATUSBAR_HEIGHT)
        self.left = QLabel()
        self.left.setContentsMargins(SPACE_LG, 0, 0, 0)
        self.addWidget(self.left, 1)

        self._right = QWidget()
        r = QHBoxLayout(self._right)
        r.setContentsMargins(0, 0, SPACE_LG, 0)
        r.setSpacing(SPACE_MD)
        self.transfer_label = QLabel()
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setFixedWidth(160)
        r.addWidget(self.transfer_label)
        r.addWidget(self.progress)
        self.addPermanentWidget(self._right)
        self._right.hide()
        self._summary = ""

    def set_selection_summary(self, total_items: int, selected: list[dict]) -> None:
        if selected:
            size = sum(f["size"] or 0 for f in selected)
            self._summary = f"{len(selected)} of {total_items} selected · {format_size(size)}"
        else:
            self._summary = f"{total_items} items"
        self.left.setText(self._summary)

    def flash(self, text: str, ms: int = 2500) -> None:
        """Transient message (used to mark unwired hook points in the UI-only build)."""
        self.left.setText(text)
        QTimer.singleShot(ms, lambda: self.left.setText(self._summary))

    def set_transfer(self, name: str, mbps: float, percent: int) -> None:
        self.transfer_label.setText(f"Copying: {name} ({mbps:.1f} MB/s)")
        self.progress.setValue(percent)
        self._right.show()

    def clear_transfer(self) -> None:
        self._right.hide()
