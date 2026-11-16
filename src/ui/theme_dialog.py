"""Theme selector and Customization Store dialog."""

from typing import Optional, Callable
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QFrame, QTabWidget, QWidget
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QPixmap, QPainter, QBrush, QPen
import qtawesome as qta

from src.themes import THEMES


class ThemeDialog(QDialog):
    """Modern Theme and Customization store preview modal."""

    def __init__(self, current_theme: str, on_theme_changed: Callable[[str], None], parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.current_theme = current_theme
        self.on_theme_changed = on_theme_changed

        self.setWindowTitle("Appearance & Theme Store")
        self.resize(600, 440)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        icon = QLabel(self)
        icon.setPixmap(qta.icon("fa5s.palette", color="#38BDF8").pixmap(28, 28))
        header.addWidget(icon)

        title_box = QVBoxLayout()
        title = QLabel("Themes & Visual Customization", self)
        title.setStyleSheet("font-size: 15px; font-weight: 700; color: #FFFFFF;")
        subtitle = QLabel("Personalize colors, card styling, and explore upcoming community themes", self)
        subtitle.setStyleSheet("color: #94A3B8; font-size: 11px;")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)
        header.addStretch()
        layout.addLayout(header)

        # Tabbed interface: Built-in Themes vs Theme & Icon Store
        tabs = QTabWidget(self)

        # Tab 1: Installed Themes
        tab_themes = QWidget()
        themes_layout = QVBoxLayout(tab_themes)

        self.theme_list = QListWidget(tab_themes)
        self.theme_list.setIconSize(QSize(36, 36))
        self.theme_list.setSpacing(6)

        for key, info in THEMES.items():
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, key)
            item.setText(info["name"])

            # Create color swatch icon
            pixmap = QPixmap(36, 36)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            # Base background
            painter.setBrush(QBrush(QColor(info["bg_base"])))
            painter.setPen(QPen(QColor(info["border"]), 1))
            painter.drawRoundedRect(1, 1, 34, 34, 6, 6)
            # Accent circle
            painter.setBrush(QBrush(QColor(info["accent"])))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(18, 18, 14, 14)
            painter.end()

            item.setIcon(qta.icon("fa5s.circle", color=info["accent"]))
            item.setIcon(qta.icon("fa5s.paint-brush", color=info["accent"]))
            item.setData(Qt.ItemDataRole.DecorationRole, pixmap)
            self.theme_list.addItem(item)

            if key == self.current_theme:
                self.theme_list.setCurrentItem(item)

        self.theme_list.itemClicked.connect(self._on_theme_selected)
        themes_layout.addWidget(self.theme_list)
        tabs.addTab(tab_themes, "Installed Themes")

        # Tab 2: Theme & Icon Store (Future / Extension Shelf)
        tab_store = QWidget()
        store_layout = QVBoxLayout(tab_store)
        store_layout.setSpacing(8)

        store_banner = QFrame(tab_store)
        store_banner.setStyleSheet("background: rgba(56, 189, 248, 0.08); border-radius: 8px; padding: 10px;")
        banner_layout = QVBoxLayout(store_banner)
        lbl_store_title = QLabel("🛒 Community Theme & Icon Marketplace")
        lbl_store_title.setStyleSheet("font-weight: 700; color: #38BDF8; font-size: 13px;")
        lbl_store_desc = QLabel(
            "Download community-crafted QSS styling bundles, Lucide/Material/Phosphor icon sets, and custom folder badges."
        )
        lbl_store_desc.setWordWrap(True)
        lbl_store_desc.setStyleSheet("color: #94A3B8; font-size: 11px;")
        banner_layout.addWidget(lbl_store_title)
        banner_layout.addWidget(lbl_store_desc)
        store_layout.addWidget(store_banner)

        store_list = QListWidget(tab_store)
        store_items = [
            ("Cyberpunk Neon 2077 Pack", "High-contrast neon pink/yellow with holographic folder glyphs", "fa5s.rocket", "#FF007F"),
            ("macOS Sonoma Glass Theme", "Frosted acrylic glass backgrounds with Cupertino rounded icons", "fa5s.apple", "#38BDF8"),
            ("Retro Windows 95 Nostalgia", "Classic 3D beveled silver borders and vintage pixel icons", "fa5s.window-restore", "#EAB308"),
            ("Solarized Dark Engineering", "Low-glare color palette optimized for high-intensity night coding", "fa5s.sun", "#F97316"),
        ]
        for name, desc, icon_name, color in store_items:
            item = QListWidgetItem(qta.icon(icon_name, color=color), f"{name}\n{desc}")
            item.setSizeHint(QSize(0, 50))
            store_list.addItem(item)

        store_layout.addWidget(store_list)
        tabs.addTab(tab_store, "Theme & Icon Store (Marketplace)")

        layout.addWidget(tabs)

        # Bottom Close button
        btn_close = QPushButton("Done", self)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignRight)

    def _on_theme_selected(self, item: QListWidgetItem):
        theme_key = item.data(Qt.ItemDataRole.UserRole)
        if theme_key:
            self.current_theme = theme_key
            self.on_theme_changed(theme_key)
