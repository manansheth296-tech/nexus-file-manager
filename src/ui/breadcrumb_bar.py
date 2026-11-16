"""Interactive breadcrumb navigation bar with path editing and history controls."""

from pathlib import Path
from typing import List, Optional
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLineEdit, QStackedWidget,
    QFrame, QSizePolicy, QToolButton
)
from PyQt6.QtCore import pyqtSignal, Qt
import qtawesome as qta


class BreadcrumbBar(QWidget):
    """Modern breadcrumb navigation bar supporting clickable segments and direct typing."""

    path_changed = pyqtSignal(Path)
    navigate_back = pyqtSignal()
    navigate_forward = pyqtSignal()
    navigate_up = pyqtSignal()
    refresh_requested = pyqtSignal()

    def __init__(self, initial_path: Path, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.current_path = initial_path.resolve()

        self._init_ui()
        self.set_path(self.current_path)

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Navigation Action Buttons
        self.btn_back = QToolButton(self)
        self.btn_back.setIcon(qta.icon("fa5s.arrow-left", color="#9E9E9E"))
        self.btn_back.setToolTip("Back (Alt+Left)")
        self.btn_back.clicked.connect(self.navigate_back.emit)
        self.btn_back.setEnabled(False)
        layout.addWidget(self.btn_back)

        self.btn_forward = QToolButton(self)
        self.btn_forward.setIcon(qta.icon("fa5s.arrow-right", color="#9E9E9E"))
        self.btn_forward.setToolTip("Forward (Alt+Right)")
        self.btn_forward.clicked.connect(self.navigate_forward.emit)
        self.btn_forward.setEnabled(False)
        layout.addWidget(self.btn_forward)

        self.btn_up = QToolButton(self)
        self.btn_up.setIcon(qta.icon("fa5s.arrow-up", color="#CCCCCC"))
        self.btn_up.setToolTip("Up to parent (Alt+Up)")
        self.btn_up.clicked.connect(self.navigate_up.emit)
        layout.addWidget(self.btn_up)

        self.btn_refresh = QToolButton(self)
        self.btn_refresh.setIcon(qta.icon("fa5s.sync-alt", color="#CCCCCC"))
        self.btn_refresh.setToolTip("Refresh (F5)")
        self.btn_refresh.clicked.connect(self.refresh_requested.emit)
        layout.addWidget(self.btn_refresh)

        # Central Switcher: Breadcrumb View vs Direct Text Edit
        self.stack = QStackedWidget(self)
        self.stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        # Page 0: Interactive clickable breadcrumbs container
        self.crumb_container = QFrame(self)
        self.crumb_layout = QHBoxLayout(self.crumb_container)
        self.crumb_layout.setContentsMargins(4, 2, 4, 2)
        self.crumb_layout.setSpacing(2)
        self.crumb_container.setFrameShape(QFrame.Shape.StyledPanel)
        self.crumb_container.setStyleSheet(
            "QFrame { background-color: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 6px; }"
        )
        self.crumb_container.mousePressEvent = self._on_crumb_container_clicked
        self.stack.addWidget(self.crumb_container)

        # Page 1: Direct text edit
        self.path_edit = QLineEdit(self)
        self.path_edit.returnPressed.connect(self._on_path_entered)
        self.path_edit.editingFinished.connect(self._on_edit_finished)
        self.stack.addWidget(self.path_edit)

        layout.addWidget(self.stack)

    def set_path(self, path: Path):
        """Update breadcrumbs display with the given path."""
        self.current_path = path.resolve()
        self.path_edit.setText(str(self.current_path))
        self._rebuild_breadcrumbs()

    def update_history_state(self, can_back: bool, can_forward: bool):
        """Update navigation button enabled status."""
        self.btn_back.setEnabled(can_back)
        self.btn_back.setIcon(
            qta.icon("fa5s.arrow-left", color="#CCCCCC" if can_back else "#555555")
        )
        self.btn_forward.setEnabled(can_forward)
        self.btn_forward.setIcon(
            qta.icon("fa5s.arrow-right", color="#CCCCCC" if can_forward else "#555555")
        )

    def _rebuild_breadcrumbs(self):
        # Clear existing buttons
        while self.crumb_layout.count():
            item = self.crumb_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # Build path segments from root to current
        parts = list(self.current_path.parts)
        if not parts:
            return

        accumulated = Path(parts[0])
        for i, part in enumerate(parts):
            if i > 0:
                accumulated = accumulated / part

            # Segment button
            btn = QPushButton(part if part != "\\" else "Root", self.crumb_container)
            btn.setStyleSheet(
                "QPushButton { background: transparent; border: none; padding: 3px 6px; font-weight: 500; font-size: 13px; border-radius: 4px; }"
                "QPushButton:hover { background-color: rgba(255, 255, 255, 0.12); color: #38bdf8; }"
            )
            # Capture path by default argument
            btn.clicked.connect(lambda checked, p=accumulated: self.path_changed.emit(p))
            self.crumb_layout.addWidget(btn)

            # Chevron separator (except after the last segment)
            if i < len(parts) - 1:
                sep = QPushButton(self.crumb_container)
                sep.setIcon(qta.icon("fa5s.chevron-right", color="#777777", scale=0.6))
                sep.setFixedSize(16, 20)
                sep.setStyleSheet("QPushButton { background: transparent; border: none; }")
                self.crumb_layout.addWidget(sep)

        self.crumb_layout.addStretch()

    def _on_crumb_container_clicked(self, event):
        """Switch to direct text edit mode when clicking empty space."""
        self.stack.setCurrentIndex(1)
        self.path_edit.setFocus()
        self.path_edit.selectAll()

    def _on_path_entered(self):
        text = self.path_edit.text().strip()
        candidate = Path(text)
        if candidate.exists() and candidate.is_dir():
            self.set_path(candidate)
            self.path_changed.emit(self.current_path)
            self.stack.setCurrentIndex(0)
        else:
            self.path_edit.setStyleSheet("border: 1px solid #ef4444;")

    def _on_edit_finished(self):
        self.path_edit.setStyleSheet("")
        self.stack.setCurrentIndex(0)
