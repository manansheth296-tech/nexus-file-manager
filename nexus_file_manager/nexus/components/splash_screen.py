"""
NexusSplashScreen – Modern, sleek launcher splash screen displayed during application startup.
"""
from __future__ import annotations

from PyQt6.QtCore import QPointF, QRectF, Qt, QTimer
from PyQt6.QtGui import QFont, QPainter, QPainterPath, QPixmap
from PyQt6.QtWidgets import (QApplication, QHBoxLayout, QLabel,
                             QProgressBar, QSplashScreen, QStyle, QVBoxLayout, QWidget)

from nexus.assets import icon_loader
from nexus.components.badge import Badge
from nexus.styles.theme_manager import theme_manager
from nexus.tokens.base import FONT_SIZE_MD, FONT_SIZE_SM, FONT_SIZE_XS, SPACE_LG, SPACE_MD, SPACE_SM, SPACE_XL
from nexus.tokens.color_utils import to_qcolor, with_alpha


class NexusSplashScreen(QSplashScreen):
    """Frameless modern launcher splash card with startup metrics and progress bar."""

    def __init__(self):
        pixmap = QPixmap(500, 300)
        pixmap.fill(Qt.GlobalColor.transparent)
        super().__init__(pixmap, Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(500, 300)

        # Center on active screen
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.geometry()
            self.setGeometry(
                QStyle.alignedRect(
                    Qt.LayoutDirection.LeftToRight,
                    Qt.AlignmentFlag.AlignCenter,
                    self.size(),
                    geo,
                )
            )

        col = QVBoxLayout(self)
        col.setContentsMargins(SPACE_XL, SPACE_XL, SPACE_XL, SPACE_XL)
        col.setSpacing(SPACE_MD)

        # Header with Logo & Badges
        head = QHBoxLayout()
        head.setSpacing(SPACE_MD)
        self.badge_version = Badge("v1.0.0 PRO", "COLOR_ACCENT_PRIMARY")
        self.badge_status = Badge("SECURE", "COLOR_SUCCESS")
        head.addStretch(1)
        head.addWidget(self.badge_version)
        head.addWidget(self.badge_status)
        col.addLayout(head)

        col.addSpacing(SPACE_SM)

        # Title & Subtitle
        self.title_label = QLabel("NEXUS FILE MANAGER")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font_title = QFont()
        font_title.setPixelSize(22)
        font_title.setWeight(QFont.Weight.Bold)
        self.title_label.setFont(font_title)
        self.title_label.setProperty("role", "heading")
        col.addWidget(self.title_label)

        self.subtitle_label = QLabel("Next-Generation Intelligent Desktop Explorer")
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font_sub = QFont()
        font_sub.setPixelSize(FONT_SIZE_SM)
        self.subtitle_label.setFont(font_sub)
        self.subtitle_label.setProperty("role", "secondary")
        col.addWidget(self.subtitle_label)

        col.addStretch(1)

        # Status text
        self.status_label = QLabel("Initializing storage engine...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        font_status = QFont()
        font_status.setPixelSize(FONT_SIZE_XS)
        self.status_label.setFont(font_status)
        self.status_label.setProperty("role", "muted")
        col.addWidget(self.status_label)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setFixedHeight(6)
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 100)
        self.progress.setValue(10)
        col.addWidget(self.progress)

        # Footer
        foot = QHBoxLayout()
        hint = QLabel("Zero-knowledge · AES-256 · Local-First")
        hint.setProperty("role", "muted")
        font_hint = QFont()
        font_hint.setPixelSize(FONT_SIZE_XS - 1)
        hint.setFont(font_hint)
        foot.addWidget(hint)
        foot.addStretch(1)
        col.addLayout(foot)

    def set_progress(self, percent: int, message: str = "") -> None:
        self.progress.setValue(percent)
        if message:
            self.status_label.setText(message)
        QApplication.processEvents()

    def finish_and_show(self, main_win: QWidget) -> None:
        self.set_progress(100, "Ready")
        def _reveal():
            main_win.show()
            main_win.raise_()
            main_win.activateWindow()
            self.finish(main_win)
        QTimer.singleShot(250, _reveal)

    def paintEvent(self, event):
        t = theme_manager().tokens
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        path = QPainterPath()
        path.addRoundedRect(rect, t.RADIUS_XL, t.RADIUS_XL)

        # Background
        p.fillPath(path, to_qcolor(t.COLOR_BG_BASE))

        # Soft Accent Glow in background
        glow_center = QPointF(rect.center().x(), rect.top() + 60)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(to_qcolor(with_alpha(t.COLOR_ACCENT_PRIMARY, 0.08)))
        p.drawEllipse(glow_center, 120, 70)

        # Border
        p.setPen(to_qcolor(t.COLOR_BORDER_STRONG))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(rect, t.RADIUS_XL, t.RADIUS_XL)

        # App Icon in top-left
        drawn = False
        import sys
        from pathlib import Path
        for c in (
            Path(__file__).resolve().parent.parent / "assets" / "icon.png",
            Path(__file__).resolve().parent.parent.parent.parent / "assets" / "icon.png",
            Path(getattr(sys, "_MEIPASS", "")) / "assets" / "icon.png",
            Path(sys.executable).parent / "assets" / "icon.png",
        ):
            if c and c.exists():
                icon_img = QPixmap(str(c))
                if not icon_img.isNull():
                    scaled = icon_img.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    p.drawPixmap(SPACE_XL, SPACE_XL - 4, scaled)
                    drawn = True
                    break
        if not drawn:
            icon_pm = icon_loader.render_pixmap("folder", t.COLOR_ACCENT_PRIMARY, 28)
            p.drawPixmap(SPACE_XL, SPACE_XL - 2, icon_pm)
        p.end()
