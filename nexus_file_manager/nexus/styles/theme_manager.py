"""
ThemeManager – owns the active ThemeTokens, the installed-theme list, and (optionally) persists both.

    from nexus.styles.theme_manager import theme_manager
    theme_manager().apply(MIDNIGHT_CYBER)
    theme_manager().theme_changed.connect(my_widget.on_theme)      # painted widgets listen

Painted components read `theme_manager().tokens` at paint time, so they re-skin instantly on theme_changed.
Persistence (QSettings) is opt-in via enable_persistence() so tests and screenshot runs never touch user settings.
"""
from __future__ import annotations

import dataclasses

from PyQt6.QtCore import QObject, QSettings, pyqtSignal
from PyQt6.QtGui import QColor, QFontDatabase, QPalette
from PyQt6.QtWidgets import QApplication

from nexus.styles.qss_generator import generate_qss
from nexus.tokens import base
from nexus.tokens.color_utils import to_qcolor
from nexus.tokens.themes import INSTALLED_DEFAULT, MIDNIGHT_CYBER, THEMES, ThemeTokens


def _first_installed(stack: tuple[str, ...], fallback: str) -> str:
    available = set(QFontDatabase.families())
    return next((f for f in stack if f in available), fallback)


class ThemeManager(QObject):
    theme_changed = pyqtSignal(object)   # emits the new ThemeTokens
    installedChanged = pyqtSignal()

    ORG, APP = "NexusFileManager", "Nexus"

    def __init__(self) -> None:
        super().__init__()
        self._tokens: ThemeTokens = MIDNIGHT_CYBER
        self._installed: list[ThemeTokens] = list(INSTALLED_DEFAULT)
        self._persist = False
        self._settings_file: str | None = None

    # ── state ─────────────────────────────────────────────────────────────
    @property
    def tokens(self) -> ThemeTokens:
        return self._tokens

    @property
    def installed(self) -> list[ThemeTokens]:
        return list(self._installed)

    def is_installed(self, name: str) -> bool:
        return any(t.name == name for t in self._installed)

    def install(self, tokens: ThemeTokens) -> None:
        """HOOK: the real marketplace download/verify step goes before this call."""
        if not self.is_installed(tokens.name):
            self._installed.append(tokens)
            self._save()
            self.installedChanged.emit()

    def apply_accent(self, hex_color: str) -> None:
        """Re-skin the active theme with a custom accent (focus border follows the accent)."""
        self.apply(dataclasses.replace(self._tokens, COLOR_ACCENT_PRIMARY=hex_color, COLOR_BORDER_FOCUS=hex_color))

    def reset_accent(self) -> None:
        self.apply(THEMES.get(self._tokens.name, self._tokens))

    # ── apply ─────────────────────────────────────────────────────────────
    def apply(self, tokens: ThemeTokens, app: QApplication | None = None) -> None:
        app = app or QApplication.instance()
        self._tokens = tokens
        ui_font = _first_installed(base.FONT_STACK_UI, app.font().family())
        mono_font = _first_installed(base.FONT_STACK_MONO, "monospace")
        self.setProperty("mono_family", mono_font)     # painted monospace widgets (hex dump) read this
        app.setStyleSheet(generate_qss(tokens, ui_font, mono_font))
        app.setPalette(self._build_palette(tokens))
        self._save()
        self.theme_changed.emit(tokens)

    @staticmethod
    def _build_palette(t: ThemeTokens) -> QPalette:
        """Palette covers what QSS doesn't (native dialogs, disabled text, selection)."""
        pal = QPalette()
        c = to_qcolor
        for role, value in (
            (QPalette.ColorRole.Window, t.COLOR_BG_BASE),
            (QPalette.ColorRole.Base, t.COLOR_BG_RAISED),
            (QPalette.ColorRole.AlternateBase, t.COLOR_ROW_ALT),
            (QPalette.ColorRole.Text, t.COLOR_TEXT_PRIMARY),
            (QPalette.ColorRole.WindowText, t.COLOR_TEXT_PRIMARY),
            (QPalette.ColorRole.ButtonText, t.COLOR_TEXT_PRIMARY),
            (QPalette.ColorRole.Button, t.COLOR_BG_RAISED),
            (QPalette.ColorRole.ToolTipBase, t.COLOR_BG_RAISED),
            (QPalette.ColorRole.ToolTipText, t.COLOR_TEXT_PRIMARY),
            (QPalette.ColorRole.Highlight, t.COLOR_ACCENT_PRIMARY),
            (QPalette.ColorRole.HighlightedText, t.COLOR_TEXT_ON_ACCENT),
            (QPalette.ColorRole.PlaceholderText, t.COLOR_TEXT_MUTED),
        ):
            pal.setColor(role, c(value))
        for role in (QPalette.ColorRole.Text, QPalette.ColorRole.WindowText, QPalette.ColorRole.ButtonText):
            pal.setColor(QPalette.ColorGroup.Disabled, role, QColor(c(t.COLOR_TEXT_MUTED)))
        return pal

    # ── persistence (opt-in) ──────────────────────────────────────────────
    def enable_persistence(self) -> None:
        self._persist = True

    def set_settings_file(self, path: str | None) -> None:
        """Store settings in an explicit INI file instead of the platform location (tests, portable installs)."""
        self._settings_file = path

    def settings(self) -> QSettings:
        """The one QSettings used for theme AND window state, so an override applies to both."""
        if self._settings_file:
            return QSettings(self._settings_file, QSettings.Format.IniFormat)
        return QSettings(self.ORG, self.APP)

    _settings = settings   # backwards-compatible alias

    def _save(self) -> None:
        if not self._persist:
            return
        s = self._settings()
        s.setValue("theme/active", self._tokens.name)
        catalogue = THEMES.get(self._tokens.name)
        custom = catalogue is not None and catalogue.COLOR_ACCENT_PRIMARY != self._tokens.COLOR_ACCENT_PRIMARY
        s.setValue("theme/accent", self._tokens.COLOR_ACCENT_PRIMARY if custom else "")
        s.setValue("theme/installed", [t.name for t in self._installed])

    def restore(self, app: QApplication | None = None) -> bool:
        """Re-apply the saved theme / accent / installed list. Returns False if nothing valid was saved."""
        s = self._settings()
        names = s.value("theme/installed", [], type=list) or []
        for n in names:
            if n in THEMES and not self.is_installed(n):
                self._installed.append(THEMES[n])
        active = s.value("theme/active", "", type=str)
        if active not in THEMES:
            return False
        tokens = THEMES[active]
        accent = s.value("theme/accent", "", type=str)
        if accent:
            tokens = dataclasses.replace(tokens, COLOR_ACCENT_PRIMARY=accent, COLOR_BORDER_FOCUS=accent)
        self.apply(tokens, app)
        return True


_instance: ThemeManager | None = None


def theme_manager() -> ThemeManager:
    global _instance
    if _instance is None:
        _instance = ThemeManager()
    return _instance
