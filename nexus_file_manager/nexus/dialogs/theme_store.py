"""
Theme & Customization Store [spec Screen 9]. Tab 1 Installed (preset themes with circular palette swatches + accent
customisation), Tab 2 Marketplace (card shelf: Cyberpunk Neon, macOS Glass, Windows 95 Retro).
Size is not in the spec → 960 × 620 [assumed].

Apply re-skins the whole running app live. Install is a simulated download. HOOK: `installRequested(name)`.
"""
from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QScrollArea, QStackedWidget, QVBoxLayout, QWidget

from nexus.components import Badge, Button, Card, Divider, NexusDialog, SegmentedTabs
from nexus.components.theme_widgets import AccentChip, PaletteSwatch, ThemeThumbnail
from nexus.core.mock_data import THEME_META
from nexus.styles.theme_manager import theme_manager
from nexus.tokens import ACCENT_PRESETS, MARKETPLACE_THEMES
from nexus.tokens.base import DIALOG_THEME_STORE, SPACE_LG, SPACE_MD, SPACE_SM, SPACE_XL
from nexus.tokens.themes import ThemeTokens

COLUMNS = 4
CARD_W = 214


class ThemeCard(Card):
    applyRequested = pyqtSignal(str)
    installRequested = pyqtSignal(str)

    def __init__(self, tokens: ThemeTokens, state: str):
        """state: 'active' | 'installed' | 'market' | 'installing'"""
        super().__init__("card")
        self.tokens = tokens
        self.state = state
        self.setFixedWidth(CARD_W)
        author, downloads, blurb = THEME_META.get(tokens.name, ("Community", "", ""))
        col = QVBoxLayout(self)
        col.setContentsMargins(SPACE_MD, SPACE_MD, SPACE_MD, SPACE_MD)
        col.setSpacing(SPACE_SM)
        col.addWidget(ThemeThumbnail(tokens, (CARD_W - 2 * SPACE_MD - 2, 104)), 0, Qt.AlignmentFlag.AlignHCenter)
        title = QHBoxLayout()
        name = QLabel(tokens.name.replace(" (demo)", ""))
        name.setProperty("role", "subheading")
        title.addWidget(name, 1)
        if state == "active":
            title.addWidget(Badge("ACTIVE", "COLOR_SUCCESS"))
        elif state in ("installed",) and not downloads:
            title.addWidget(Badge("INSTALLED", "COLOR_ACCENT_SECONDARY"))
        col.addLayout(title)
        meta = QLabel(f"{author}" + (f" · {downloads} downloads" if downloads else "") + (f"\n{blurb}" if blurb else ""))
        meta.setProperty("role", "muted")
        col.addWidget(meta)
        foot = QHBoxLayout()
        foot.setSpacing(SPACE_SM)
        foot.addWidget(PaletteSwatch(tokens, 26))
        foot.addStretch(1)
        self.button = self._make_button()
        foot.addWidget(self.button)
        col.addLayout(foot)

    def _make_button(self) -> Button:
        if self.state == "active":
            b = Button("Applied", icon="check")
            b.setEnabled(False)
        elif self.state == "installed":
            b = Button("Apply", variant="primary")
            b.clicked.connect(lambda: self.applyRequested.emit(self.tokens.name))
        elif self.state == "installing":
            b = Button("Installing…", icon="download")
            b.setEnabled(False)
        else:
            b = Button("Install", icon="download")
            b.clicked.connect(lambda: self.installRequested.emit(self.tokens.name))
        return b

    def mark_installing(self) -> None:
        self.state = "installing"
        self.button.setText("Installing…")
        self.button.setEnabled(False)


class ThemeStoreDialog(NexusDialog):
    installRequested = pyqtSignal(str)       # HOOK: real marketplace download

    def __init__(self, parent: QWidget | None = None, tab: int = 0):
        super().__init__("Theme & Customization", "Themes are token sets — applying one re-skins the entire app instantly",
                         "droplet", "COLOR_ACCENT_SECONDARY", DIALOG_THEME_STORE, parent)
        self._cards: dict[str, ThemeCard] = {}
        col = QVBoxLayout(self.body)
        col.setContentsMargins(SPACE_XL, SPACE_LG, SPACE_XL, 0)
        col.setSpacing(SPACE_MD)
        self.tabs = SegmentedTabs(["Installed Themes", "Marketplace"], ["grid", "download"])
        self.tabs.setFixedWidth(340)
        self.tabs.currentChanged.connect(lambda i: self.pages.setCurrentIndex(i))
        col.addWidget(self.tabs)

        self.pages = QStackedWidget()
        self.installed_page, self.installed_col = self._scroll_page()
        self.market_page, self.market_col = self._scroll_page()
        self.pages.addWidget(self.installed_page)
        self.pages.addWidget(self.market_page)
        col.addWidget(self.pages, 1)

        col.addWidget(Divider())
        foot = QHBoxLayout()
        foot.setContentsMargins(0, 0, 0, SPACE_MD)
        note = QLabel("Radius, colour and state tokens all come from the theme — even the square Windows 95 corners.")
        note.setProperty("role", "muted")
        foot.addWidget(note, 1)
        close = Button("Done", variant="primary")
        close.clicked.connect(self.accept)
        foot.addWidget(close)
        col.addLayout(foot)

        tm = theme_manager()
        tm.theme_changed.connect(self._schedule_rebuild)
        tm.installedChanged.connect(self._schedule_rebuild)
        self._rebuild()
        if tab:
            self.tabs.set_current(tab)
            self.pages.setCurrentIndex(tab)

    def _scroll_page(self) -> tuple[QScrollArea, QVBoxLayout]:
        sc = QScrollArea()
        sc.setWidgetResizable(True)
        sc.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        host = QWidget()
        lay = QVBoxLayout(host)
        lay.setContentsMargins(0, SPACE_SM, SPACE_SM, SPACE_LG)
        lay.setSpacing(SPACE_MD)
        lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        sc.setWidget(host)
        return sc, lay

    def _schedule_rebuild(self, *_a) -> None:
        QTimer.singleShot(0, self._rebuild)          # deferred: the click that triggered it lives inside a card we are about to replace

    @staticmethod
    def _clear(layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()
            elif item.layout():
                ThemeStoreDialog._clear(item.layout())

    def _grid(self, themes: list[tuple[ThemeTokens, str]]) -> QGridLayout:
        grid = QGridLayout()
        grid.setSpacing(SPACE_LG)
        grid.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        for i, (tokens, state) in enumerate(themes):
            card = ThemeCard(tokens, state)
            card.applyRequested.connect(lambda name: theme_manager().apply(next(t for t in theme_manager().installed if t.name == name)))
            card.installRequested.connect(self._on_install)
            self._cards[tokens.name] = card
            grid.addWidget(card, i // COLUMNS, i % COLUMNS)
        return grid

    def _rebuild(self) -> None:
        tm = theme_manager()
        self._cards.clear()
        self._clear(self.installed_col)
        self._clear(self.market_col)

        self.installed_col.addLayout(self._grid([(t, "active" if t.name == tm.tokens.name else "installed") for t in tm.installed]))
        cap = QLabel("CUSTOMIZE ACCENT")
        cap.setProperty("role", "caption")
        self.installed_col.addWidget(cap)
        chips = QHBoxLayout()
        chips.setSpacing(SPACE_SM)
        self.chips: list[AccentChip] = []
        for name, hex_ in ACCENT_PRESETS:
            chip = AccentChip(name, hex_)
            chip.setChecked(tm.tokens.COLOR_ACCENT_PRIMARY.lower() == hex_.lower())
            chip.clicked.connect(lambda _=False, h=hex_: tm.apply_accent(h))
            self.chips.append(chip)
            chips.addWidget(chip)
        reset = Button("Reset", variant="ghost")
        reset.clicked.connect(tm.reset_accent)
        chips.addWidget(reset)
        hint = QLabel("Overrides the active theme's accent; focus rings follow it.")
        hint.setProperty("role", "muted")
        chips.addWidget(hint)
        chips.addStretch(1)
        self.installed_col.addLayout(chips)

        cap2 = QLabel("COMMUNITY THEMES")
        cap2.setProperty("role", "caption")
        self.market_col.addWidget(cap2)
        self.market_col.addLayout(self._grid(
            [(t, "installed" if tm.is_installed(t.name) else "market") for t in MARKETPLACE_THEMES]))

    def _on_install(self, name: str) -> None:
        tokens = next(t for t in MARKETPLACE_THEMES if t.name == name)
        self.installRequested.emit(name)
        card = self._cards.get(name)
        if card:
            card.mark_installing()
        QTimer.singleShot(900, lambda: theme_manager().install(tokens))   # simulated download
