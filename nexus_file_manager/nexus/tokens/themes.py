"""
Theme token sets.

A theme is one frozen `ThemeTokens`. Swap the object handed to
`ThemeManager.apply()` and the entire app (QSS, palette, painted components)
re-skins. Spec colours are required fields; hover/selected/overlay colours are
*derived* from them so a new theme only has to supply the 13 spec colours.
"""
from __future__ import annotations

from dataclasses import dataclass, fields

from nexus.tokens import base
from nexus.tokens.color_utils import composite, darken, with_alpha


@dataclass(frozen=True)
class ThemeTokens:
    name: str

    # ── Spec colour tokens [spec §3] ──────────────────────────────────────
    COLOR_BG_BASE: str          # application background
    COLOR_BG_SURFACE: str       # sidebar, cards, headers, panels
    COLOR_BG_CARD: str          # subtle containers, preview frame
    COLOR_BORDER: str           # dividers, card borders
    COLOR_BORDER_FOCUS: str     # active input borders, focused items
    COLOR_ACCENT_PRIMARY: str   # primary buttons, active pills
    COLOR_ACCENT_SECONDARY: str
    COLOR_TEXT_PRIMARY: str
    COLOR_TEXT_SECONDARY: str
    COLOR_TEXT_MUTED: str
    COLOR_DANGER: str
    COLOR_WARNING: str
    COLOR_SUCCESS: str

    # ── Additions [assumed] – legible text on filled accent/danger buttons ─
    COLOR_TEXT_ON_ACCENT: str = "#0B0F19"
    COLOR_TEXT_ON_DANGER: str = "#F8FAFC"
    is_dark: bool = True
    COLOR_PAPER: str = "#F8FAFC"       # [assumed] PDF page / document paper – same in every theme
    COLOR_PAPER_INK: str = "#CBD5E1"   # [assumed] placeholder text lines drawn on paper

    # ── Radii (spec values; a retro theme may override with 0) ────────────
    RADIUS_SM: int = base.RADIUS_SM
    RADIUS_MD: int = base.RADIUS_MD
    RADIUS_LG: int = base.RADIUS_LG
    RADIUS_XL: int = base.RADIUS_XL

    # ── Derived state colours [assumed] ───────────────────────────────────
    _DERIVED = (
        "COLOR_HOVER_OVERLAY", "COLOR_PRESSED_BG", "COLOR_BORDER_STRONG",
        "COLOR_DISABLED_BG", "COLOR_ROW_ALT", "COLOR_SELECTED_BG",
        "COLOR_MULTI_SELECTED_BG", "COLOR_ACCENT_PRESSED", "COLOR_DANGER_PRESSED",
        "COLOR_ACCENT_SOFT", "COLOR_DANGER_SOFT", "COLOR_WARNING_SOFT",
        "COLOR_SUCCESS_SOFT", "COLOR_SCROLL_HANDLE", "COLOR_SCROLL_HANDLE_HOVER",
        "COLOR_SWITCH_OFF", "COLOR_KNOB", "COLOR_BG_RAISED", "COLOR_SHADOW", "COLOR_SCRIM",
    )

    @property
    def COLOR_HOVER_OVERLAY(self) -> str:       # animated hover wash
        return with_alpha(self.COLOR_TEXT_PRIMARY, 0.06)

    @property
    def COLOR_PRESSED_BG(self) -> str:
        return with_alpha(self.COLOR_TEXT_PRIMARY, 0.10)

    @property
    def COLOR_BORDER_STRONG(self) -> str:       # hovered inputs, checkbox outline
        return with_alpha(self.COLOR_TEXT_PRIMARY, 0.16)

    @property
    def COLOR_DISABLED_BG(self) -> str:
        return with_alpha(self.COLOR_TEXT_PRIMARY, 0.04)

    @property
    def COLOR_ROW_ALT(self) -> str:             # alternating row tint
        return with_alpha(self.COLOR_TEXT_PRIMARY, 0.025)

    @property
    def COLOR_SELECTED_BG(self) -> str:
        return with_alpha(self.COLOR_ACCENT_PRIMARY, 0.16)

    @property
    def COLOR_MULTI_SELECTED_BG(self) -> str:
        return with_alpha(self.COLOR_ACCENT_PRIMARY, 0.26)

    @property
    def COLOR_ACCENT_PRESSED(self) -> str:
        return darken(self.COLOR_ACCENT_PRIMARY, 0.15)

    @property
    def COLOR_DANGER_PRESSED(self) -> str:
        return darken(self.COLOR_DANGER, 0.15)

    @property
    def COLOR_ACCENT_SOFT(self) -> str:
        return with_alpha(self.COLOR_ACCENT_PRIMARY, 0.14)

    @property
    def COLOR_DANGER_SOFT(self) -> str:
        return with_alpha(self.COLOR_DANGER, 0.14)

    @property
    def COLOR_WARNING_SOFT(self) -> str:
        return with_alpha(self.COLOR_WARNING, 0.14)

    @property
    def COLOR_SUCCESS_SOFT(self) -> str:
        return with_alpha(self.COLOR_SUCCESS, 0.14)

    @property
    def COLOR_SCROLL_HANDLE(self) -> str:
        return with_alpha(self.COLOR_TEXT_PRIMARY, 0.16)

    @property
    def COLOR_SCROLL_HANDLE_HOVER(self) -> str:
        return with_alpha(self.COLOR_TEXT_PRIMARY, 0.28)

    @property
    def COLOR_SWITCH_OFF(self) -> str:
        return with_alpha(self.COLOR_TEXT_SECONDARY, 0.30)

    @property
    def COLOR_KNOB(self) -> str:
        return self.COLOR_TEXT_PRIMARY if self.is_dark else self.COLOR_BG_SURFACE

    @property
    def COLOR_BG_RAISED(self) -> str:           # surface flattened over base: always opaque (dialogs, menus, tooltips)
        return composite(self.COLOR_BG_SURFACE, self.COLOR_BG_BASE)

    @property
    def COLOR_SHADOW(self) -> str:
        return with_alpha("#000000", 0.5)

    @property
    def COLOR_SCRIM(self) -> str:               # dim layer behind modal dialogs
        return with_alpha("#000000", 0.55)

    def as_mapping(self) -> dict[str, object]:
        """Every COLOR_* / RADIUS_* value (spec + derived) for the QSS generator."""
        out = {f.name: getattr(self, f.name) for f in fields(self)
               if f.name.startswith(("COLOR_", "RADIUS_"))}
        out.update({n: getattr(self, n) for n in self._DERIVED})
        return out


# ── Primary theme: Midnight Cyber [spec §3] – hex codes verbatim ───────────
MIDNIGHT_CYBER = ThemeTokens(
    name="Midnight Cyber",
    COLOR_BG_BASE="#0B0F19",
    COLOR_BG_SURFACE="#111827",
    COLOR_BG_CARD="rgba(255, 255, 255, 0.04)",
    COLOR_BORDER="rgba(255, 255, 255, 0.08)",
    COLOR_BORDER_FOCUS="#38BDF8",
    COLOR_ACCENT_PRIMARY="#38BDF8",
    COLOR_ACCENT_SECONDARY="#818CF8",
    COLOR_TEXT_PRIMARY="#F8FAFC",
    COLOR_TEXT_SECONDARY="#94A3B8",
    COLOR_TEXT_MUTED="#64748B",
    COLOR_DANGER="#EF4444",
    COLOR_WARNING="#F59E0B",
    COLOR_SUCCESS="#10B981",
)

# ── Demo theme: NOT from the spec. Exists only to prove that swapping one
#    token set re-skins everything (the Phase 6 Theme Store will build on it).
DAYLIGHT_SLATE = ThemeTokens(
    name="Daylight Slate (demo)",
    COLOR_BG_BASE="#F1F5F9",
    COLOR_BG_SURFACE="#FFFFFF",
    COLOR_BG_CARD="rgba(15, 23, 42, 0.04)",
    COLOR_BORDER="rgba(15, 23, 42, 0.10)",
    COLOR_BORDER_FOCUS="#0369A1",
    COLOR_ACCENT_PRIMARY="#0369A1",
    COLOR_ACCENT_SECONDARY="#6366F1",
    COLOR_TEXT_PRIMARY="#0F172A",
    COLOR_TEXT_SECONDARY="#475569",
    COLOR_TEXT_MUTED="#64748B",
    COLOR_DANGER="#DC2626",
    COLOR_WARNING="#D97706",
    COLOR_SUCCESS="#059669",
    COLOR_TEXT_ON_ACCENT="#FFFFFF",
    COLOR_TEXT_ON_DANGER="#FFFFFF",
    is_dark=False,
)

# ── Extra themes. NOT in the spec – the Phase 6 Theme Store's catalogue [assumed values]. ──
NORD_FROST = ThemeTokens(
    name="Nord Frost",
    COLOR_BG_BASE="#2E3440", COLOR_BG_SURFACE="#3B4252", COLOR_BG_CARD="rgba(255, 255, 255, 0.05)",
    COLOR_BORDER="rgba(236, 239, 244, 0.10)", COLOR_BORDER_FOCUS="#88C0D0",
    COLOR_ACCENT_PRIMARY="#88C0D0", COLOR_ACCENT_SECONDARY="#B48EAD",
    COLOR_TEXT_PRIMARY="#ECEFF4", COLOR_TEXT_SECONDARY="#D8DEE9", COLOR_TEXT_MUTED="#8F9BB3",
    COLOR_DANGER="#BF616A", COLOR_WARNING="#EBCB8B", COLOR_SUCCESS="#A3BE8C",
    COLOR_TEXT_ON_ACCENT="#2E3440", COLOR_TEXT_ON_DANGER="#FFFFFF",
)
FOREST_NIGHT = ThemeTokens(
    name="Forest Night",
    COLOR_BG_BASE="#0C1511", COLOR_BG_SURFACE="#12201A", COLOR_BG_CARD="rgba(255, 255, 255, 0.04)",
    COLOR_BORDER="rgba(255, 255, 255, 0.08)", COLOR_BORDER_FOCUS="#34D399",
    COLOR_ACCENT_PRIMARY="#34D399", COLOR_ACCENT_SECONDARY="#A3E635",
    COLOR_TEXT_PRIMARY="#ECFDF5", COLOR_TEXT_SECONDARY="#9DB8A9", COLOR_TEXT_MUTED="#6B8577",
    COLOR_DANGER="#F87171", COLOR_WARNING="#FBBF24", COLOR_SUCCESS="#4ADE80",
    COLOR_TEXT_ON_ACCENT="#052E16", COLOR_TEXT_ON_DANGER="#052E16",
)
CYBERPUNK_NEON = ThemeTokens(
    name="Cyberpunk Neon",
    COLOR_BG_BASE="#0A0014", COLOR_BG_SURFACE="#14002B", COLOR_BG_CARD="rgba(255, 255, 255, 0.05)",
    COLOR_BORDER="rgba(255, 43, 214, 0.28)", COLOR_BORDER_FOCUS="#FF2BD6",
    COLOR_ACCENT_PRIMARY="#FF2BD6", COLOR_ACCENT_SECONDARY="#00F0FF",
    COLOR_TEXT_PRIMARY="#F5E9FF", COLOR_TEXT_SECONDARY="#B79CD6", COLOR_TEXT_MUTED="#8D75AE",
    COLOR_DANGER="#FF3B5C", COLOR_WARNING="#FFE600", COLOR_SUCCESS="#00FF9C",
    COLOR_TEXT_ON_ACCENT="#14002B", COLOR_TEXT_ON_DANGER="#14002B",
)
MACOS_GLASS = ThemeTokens(
    name="macOS Glass",
    COLOR_BG_BASE="#E5E7EE", COLOR_BG_SURFACE="rgba(255, 255, 255, 0.78)", COLOR_BG_CARD="rgba(60, 60, 67, 0.05)",
    COLOR_BORDER="rgba(60, 60, 67, 0.14)", COLOR_BORDER_FOCUS="#0A66C2",
    COLOR_ACCENT_PRIMARY="#0A66C2", COLOR_ACCENT_SECONDARY="#AF52DE",
    COLOR_TEXT_PRIMARY="#1C1C1E", COLOR_TEXT_SECONDARY="#48484A", COLOR_TEXT_MUTED="#6E6E73",
    COLOR_DANGER="#D92D20", COLOR_WARNING="#FF9500", COLOR_SUCCESS="#34C759",
    COLOR_TEXT_ON_ACCENT="#FFFFFF", COLOR_TEXT_ON_DANGER="#FFFFFF",
    is_dark=False, RADIUS_SM=6, RADIUS_MD=8, RADIUS_LG=12, RADIUS_XL=16,        # rounder, to show radius tokens swap too
)
WINDOWS_95_RETRO = ThemeTokens(
    name="Windows 95 Retro",
    COLOR_BG_BASE="#C0C0C0", COLOR_BG_SURFACE="#DFDFDF", COLOR_BG_CARD="rgba(0, 0, 0, 0.05)",
    COLOR_BORDER="rgba(0, 0, 0, 0.45)", COLOR_BORDER_FOCUS="#000080",
    COLOR_ACCENT_PRIMARY="#000080", COLOR_ACCENT_SECONDARY="#008080",
    COLOR_TEXT_PRIMARY="#000000", COLOR_TEXT_SECONDARY="#303030", COLOR_TEXT_MUTED="#5A5A5A",
    COLOR_DANGER="#C00000", COLOR_WARNING="#806000", COLOR_SUCCESS="#006400",
    COLOR_TEXT_ON_ACCENT="#FFFFFF", COLOR_TEXT_ON_DANGER="#FFFFFF",
    is_dark=False, RADIUS_SM=0, RADIUS_MD=0, RADIUS_LG=0, RADIUS_XL=0,            # square corners everywhere
)

CONVERGE_DARK = ThemeTokens(
    name="Converge Dark",
    COLOR_BG_BASE="#0D1117",
    COLOR_BG_SURFACE="#161B22",
    COLOR_BG_CARD="rgba(255, 255, 255, 0.035)",
    COLOR_BORDER="rgba(240, 246, 252, 0.07)",
    COLOR_BORDER_FOCUS="#58A6FF",
    COLOR_ACCENT_PRIMARY="#58A6FF",
    COLOR_ACCENT_SECONDARY="#BC8CFF",
    COLOR_TEXT_PRIMARY="#F0F6FC",
    COLOR_TEXT_SECONDARY="#8B949E",
    COLOR_TEXT_MUTED="#6E7681",
    COLOR_DANGER="#EF4444",
    COLOR_WARNING="#D29922",
    COLOR_SUCCESS="#3FB950",
    COLOR_TEXT_ON_ACCENT="#0D1117",
    COLOR_TEXT_ON_DANGER="#F8FAFC",
    is_dark=True,
    RADIUS_SM=6,
    RADIUS_MD=10,
    RADIUS_LG=14,
    RADIUS_XL=18,
)

INSTALLED_DEFAULT = [MIDNIGHT_CYBER, CONVERGE_DARK, DAYLIGHT_SLATE, NORD_FROST, FOREST_NIGHT]
MARKETPLACE_THEMES = [CYBERPUNK_NEON, MACOS_GLASS, WINDOWS_95_RETRO]
THEMES: dict[str, ThemeTokens] = {t.name: t for t in (*INSTALLED_DEFAULT, *MARKETPLACE_THEMES)}

# Accent presets for the store's "Customize accent" row [assumed]
ACCENT_PRESETS = [("Cyan", "#38BDF8"), ("Indigo", "#818CF8"), ("Emerald", "#10B981"),
                  ("Amber", "#F59E0B"), ("Rose", "#FB7185"), ("Violet", "#A78BFA")]
