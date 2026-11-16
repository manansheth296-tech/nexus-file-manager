"""
Encrypted Safe Locker (520 × 380) [spec Screen 7]: Lock / Unlock segmented tabs, password with reveal toggle and
strength meter, the "Move original … to Recycle Bin after locking" safety checkbox, shield branding.

UI-only. HOOK: `vaultActionRequested(mode, path, password, trash_original)`. The password is never stored or logged here.
"""
from __future__ import annotations

from PyQt6.QtCore import QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QPainter
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from nexus.assets import icon_loader
from nexus.components import (Button, Card, Checkbox, ElidedLabel, IconTile, NexusDialog, PasswordField,
                              SegmentedTabs, StrengthMeter)
from nexus.core.mock_data import MOCK_FILES, format_size
from nexus.core.strength import password_strength
from nexus.styles.theme_manager import theme_manager
from nexus.tokens.base import DIALOG_SAFE_LOCKER, SPACE_LG, SPACE_MD, SPACE_SM, SPACE_XL
from nexus.tokens.color_utils import to_qcolor, with_alpha
from nexus.tokens.file_types import kind_color, kind_icon


class _Body(QWidget):
    """Body with a large, faint shield watermark (branding)."""

    def paintEvent(self, event):
        t = theme_manager().tokens
        size = 170
        pm = icon_loader.render_pixmap("shield", t.COLOR_ACCENT_PRIMARY, size)
        p = QPainter(self)
        p.setOpacity(0.07)
        p.drawPixmap(self.width() - size - SPACE_XL + 24, self.height() - size - 20, pm)
        p.end()


class SafeLockerDialog(NexusDialog):
    vaultActionRequested = pyqtSignal(str, str, str, bool)   # HOOK: mode, path, password, trash_original

    def __init__(self, parent: QWidget | None = None, file: dict | None = None, mode: str = "lock"):
        super().__init__("Encrypted Safe Locker", "Zero-knowledge · your password never leaves this device",
                         "shield", "COLOR_ACCENT_PRIMARY", DIALOG_SAFE_LOCKER, parent)
        self.file = file or next(f for f in MOCK_FILES if f["name"].startswith("Q3 Financial"))
        # replace the plain body with the branded one
        self.body.setParent(None)
        self.body = _Body()
        self.panel.layout().addWidget(self.body, 1)

        col = QVBoxLayout(self.body)
        col.setContentsMargins(SPACE_XL, SPACE_LG, SPACE_XL, 20)
        col.setSpacing(0)
        self.tabs = SegmentedTabs(["Lock (Encrypt)", "Unlock (Decrypt)"], ["lock", "shield"])
        self.tabs.currentChanged.connect(self._on_mode)
        col.addWidget(self.tabs)
        col.addSpacing(14)

        target = Card("card")
        tl = QHBoxLayout(target)
        tl.setContentsMargins(SPACE_MD, 6, SPACE_SM, 6)
        tl.setSpacing(SPACE_MD)
        self.target_icon = IconTile(kind_icon(self.file["kind"]), kind_color(self.file["kind"]), 28)
        tl.addWidget(self.target_icon)
        self.target_name = ElidedLabel(self.file["name"])
        tl.addWidget(self.target_name, 1)
        self.target_size = QLabel(format_size(self.file["size"]))
        self.target_size.setProperty("role", "muted")
        tl.addWidget(self.target_size)
        self.btn_change = Button("Change…", variant="ghost")
        self.btn_change.setFixedHeight(28)
        self.btn_change.clicked.connect(self._choose_file)
        tl.addWidget(self.btn_change)
        col.addWidget(target)
        col.addSpacing(SPACE_MD)

        self.password = PasswordField("Password")
        self.password.textChanged.connect(self._validate)
        col.addWidget(self.password)
        col.addSpacing(4)
        self.meter = StrengthMeter()
        col.addWidget(self.meter)
        col.addSpacing(SPACE_SM)
        self.confirm = PasswordField("Confirm password")
        self.confirm.textChanged.connect(self._validate)
        col.addWidget(self.confirm)
        self.unlock_hint = QLabel("Enter the password used to lock this file. There is no recovery if it is lost.")
        self.unlock_hint.setProperty("role", "muted")
        self.unlock_hint.setWordWrap(True)
        col.addWidget(self.unlock_hint)
        col.addSpacing(SPACE_MD)
        self.safety = Checkbox("Move original unencrypted file to Recycle Bin after locking")
        self.safety.setChecked(True)
        col.addWidget(self.safety)
        col.addStretch(1)

        foot = QHBoxLayout()
        foot.setSpacing(SPACE_SM)
        foot.addStretch(1)
        self.btn_cancel = Button("Cancel", variant="ghost")
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_go = Button("Lock File", icon="lock", variant="primary")
        self.btn_go.clicked.connect(self._on_go)
        foot.addWidget(self.btn_cancel)
        foot.addWidget(self.btn_go)
        col.addLayout(foot)

        if mode == "unlock":
            self.tabs.set_current(1)
        self._on_mode(self.tabs.current)

    @property
    def mode(self) -> str:
        return "lock" if self.tabs.current == 0 else "unlock"

    def _on_mode(self, _i: int) -> None:
        lock = self.mode == "lock"
        for w in (self.meter, self.confirm, self.safety):
            w.setVisible(lock)
        self.unlock_hint.setVisible(not lock)
        self.target_name.setText(self.file["name"] if lock else self.file["name"] + ".nxv")
        self.btn_go.setText("Lock File" if lock else "Unlock File")
        self.btn_go._icon_name = "lock" if lock else "shield"
        self.btn_go._refresh_icon()
        self.password.setPlaceholderText("Choose a password" if lock else "Password")
        self._validate()

    def _validate(self) -> None:
        pw, cf = self.password.text(), self.confirm.text()
        if self.mode == "lock":
            self.meter.set_level(password_strength(pw), empty=not pw)
            mismatch = bool(cf) and cf != pw
            self.confirm.set_error(mismatch)
            self.confirm.setToolTip("Passwords don't match" if mismatch else "")
            self.btn_go.setEnabled(password_strength(pw) >= 1 and cf == pw)
        else:
            self.confirm.set_error(False)
            self.btn_go.setEnabled(bool(pw))

    def _choose_file(self) -> None:
        from pathlib import Path
        from PyQt6.QtWidgets import QFileDialog
        filter_str = "All Files (*.*)" if self.mode == "lock" else "Encrypted Vaults (*.nxv);;All Files (*.*)"
        path, _ = QFileDialog.getOpenFileName(self, "Select File for Safe Locker", "", filter_str)
        if path:
            p = Path(path)
            from nexus.tokens.file_types import file_type_for
            self.file = {
                "name": p.name,
                "path": str(p),
                "size": p.stat().st_size if p.exists() else 0,
                "kind": file_type_for(p.name) or "binary"
            }
            lock = self.mode == "lock"
            self.target_name.setText(self.file["name"] if lock else self.file["name"] + ".nxv")
            self.target_icon.set_icon(kind_icon(self.file["kind"]), kind_color(self.file["kind"]))
            self.target_size.setText(format_size(self.file["size"]))
            self._validate()

    def _on_go(self) -> None:
        self.vaultActionRequested.emit(self.mode, self.file["name"], self.password.text(),
                                       self.safety.isChecked() and self.mode == "lock")
        self.password.clear()
        self.confirm.clear()
        self.accept()
