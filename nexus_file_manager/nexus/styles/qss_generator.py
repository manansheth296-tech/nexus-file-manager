"""
QSS generator – the single place where tokens become stylesheet text.

The template below contains no literal colours or pixel sizes: every value is a
`${TOKEN_NAME}` placeholder that mirrors the spec's token names. `Template.substitute`
raises KeyError on any missing token, so typos fail loudly instead of silently
rendering wrong.

State selectors come in pairs (`:pressed` + `[forceState="pressed"]`). The second
form lets the component gallery / design QA render a state statically.
"""
from __future__ import annotations

from string import Template

from nexus.assets import icon_loader
from nexus.tokens import base
from nexus.tokens.color_utils import to_qss
from nexus.tokens.themes import ThemeTokens

QSS_TEMPLATE = Template(r'''
/* ═══ Global ═══════════════════════════════════════════════════════════ */
QWidget {
    background: transparent;
    color: ${COLOR_TEXT_PRIMARY};
    font-family: "${FONT_FAMILY}";
    font-size: ${FONT_SIZE_MD}px;
}
QMainWindow, QDialog { background: ${COLOR_BG_BASE}; }
QDialog[nexusDialog="true"] { background: transparent; }     /* frameless, rounded, translucent window */

QToolTip {
    background: ${COLOR_BG_RAISED};
    color: ${COLOR_TEXT_PRIMARY};
    border: 1px solid ${COLOR_BORDER_STRONG};
    border-radius: ${RADIUS_MD}px;
    padding: ${SPACE_XS}px ${SPACE_SM}px;
    font-size: ${FONT_SIZE_SM}px;
}

/* ═══ Surfaces (Card / Panel / Divider) ═════════════════════════════════ */
QFrame[surface="base"]     { background: ${COLOR_BG_BASE};    border: none; }
QFrame[surface="surface"]  { background: ${COLOR_BG_SURFACE}; border: none; }
QFrame[surface="card"] {
    background: ${COLOR_BG_CARD};
    border: 1px solid ${COLOR_BORDER};
    border-radius: ${RADIUS_LG}px;
}
QFrame[surface="dialog"] {
    background: ${COLOR_BG_RAISED};
    border: 1px solid ${COLOR_BORDER_STRONG};
    border-radius: ${RADIUS_XL}px;
}
QFrame[divider="h"] { background: ${COLOR_BORDER}; border: none; min-height: 1px; max-height: 1px; }
QFrame[divider="v"] { background: ${COLOR_BORDER}; border: none; min-width: 1px;  max-width: 1px; }

/* ═══ Labels (typographic roles) ════════════════════════════════════════ */
QLabel[role="title"]     { font-size: ${FONT_SIZE_2XL}px; font-weight: 700; }
QLabel[role="heading"]   { font-size: ${FONT_SIZE_XL}px;  font-weight: 600; }
QLabel[role="subheading"]{ font-size: ${FONT_SIZE_LG}px;  font-weight: 600; }
QLabel[role="secondary"] { color: ${COLOR_TEXT_SECONDARY}; }
QLabel[role="muted"]     { color: ${COLOR_TEXT_MUTED}; font-size: ${FONT_SIZE_SM}px; }
QLabel[role="caption"]   { color: ${COLOR_TEXT_MUTED}; font-size: ${FONT_SIZE_XS}px; font-weight: 600; }
QLabel[role="mono"]      { font-family: "${FONT_FAMILY_MONO}"; font-size: ${FONT_SIZE_SM}px; color: ${COLOR_TEXT_SECONDARY}; }

/* ═══ Buttons ═══════════════════════════════════════════════════════════
   variant: secondary (default) | primary | ghost | danger
   Hover is a painted, animated overlay (QSS has no transitions) – see components/button.py */
QPushButton {
    background: ${COLOR_BG_CARD};
    color: ${COLOR_TEXT_PRIMARY};
    border: 1px solid ${COLOR_BORDER};
    border-radius: ${RADIUS_MD}px;
    padding: 0 ${SPACE_LG}px;
    min-height: ${CONTROL_INNER_HEIGHT}px;
    font-weight: 500;
}
QPushButton[iconOnly="true"] { padding: 0; min-width: ${CONTROL_INNER_HEIGHT}px; }
QPushButton:pressed, QPushButton[forceState="pressed"] { background: ${COLOR_PRESSED_BG}; }
QPushButton:disabled { background: ${COLOR_DISABLED_BG}; color: ${COLOR_TEXT_MUTED}; border-color: ${COLOR_BORDER}; }

QPushButton[variant="primary"] {
    background: ${COLOR_ACCENT_PRIMARY}; color: ${COLOR_TEXT_ON_ACCENT};
    border: 1px solid ${COLOR_ACCENT_PRIMARY}; font-weight: 600;
}
QPushButton[variant="primary"]:pressed, QPushButton[variant="primary"][forceState="pressed"] {
    background: ${COLOR_ACCENT_PRESSED}; border-color: ${COLOR_ACCENT_PRESSED};
}
QPushButton[variant="primary"]:disabled {
    background: ${COLOR_DISABLED_BG}; color: ${COLOR_TEXT_MUTED}; border-color: ${COLOR_BORDER};
}

QPushButton[variant="ghost"] { background: transparent; border: 1px solid transparent; color: ${COLOR_TEXT_SECONDARY}; }
QPushButton[variant="ghost"]:pressed, QPushButton[variant="ghost"][forceState="pressed"] { background: ${COLOR_PRESSED_BG}; color: ${COLOR_TEXT_PRIMARY}; }
QPushButton[variant="ghost"]:disabled { background: transparent; color: ${COLOR_TEXT_MUTED}; border-color: transparent; }
QPushButton[variant="ghost"]:checked { background: ${COLOR_SELECTED_BG}; color: ${COLOR_ACCENT_PRIMARY}; }

QPushButton[variant="danger"] {
    background: ${COLOR_DANGER}; color: ${COLOR_TEXT_ON_DANGER};
    border: 1px solid ${COLOR_DANGER}; font-weight: 600;
}
QPushButton[variant="danger"]:pressed, QPushButton[variant="danger"][forceState="pressed"] {
    background: ${COLOR_DANGER_PRESSED}; border-color: ${COLOR_DANGER_PRESSED};
}
QPushButton[variant="danger"]:disabled {
    background: ${COLOR_DISABLED_BG}; color: ${COLOR_TEXT_MUTED}; border-color: ${COLOR_BORDER};
}

/* ═══ Input field ═══════════════════════════════════════════════════════ */
QLineEdit {
    background: ${COLOR_BG_CARD};
    color: ${COLOR_TEXT_PRIMARY};
    border: 1px solid ${COLOR_BORDER};
    border-radius: ${RADIUS_MD}px;
    padding: 0 ${SPACE_MD}px;
    min-height: ${CONTROL_INNER_HEIGHT}px;
    selection-background-color: ${COLOR_SELECTED_BG};
    selection-color: ${COLOR_TEXT_PRIMARY};
}
QLineEdit[size="lg"] {
    min-height: ${CONTROL_LG_INNER}px; font-size: ${FONT_SIZE_LG}px;
    border-radius: ${RADIUS_LG}px; padding: 0 ${SPACE_LG}px;
}
QLineEdit:hover, QLineEdit[forceState="hover"] { border-color: ${COLOR_BORDER_STRONG}; background: ${COLOR_PRESSED_BG}; }
QLineEdit:focus, QLineEdit[forceState="focus"] { border: 1px solid ${COLOR_BORDER_FOCUS}; background: ${COLOR_BG_SURFACE}; }
QLineEdit[error="true"],
QLineEdit[error="true"]:hover,
QLineEdit[error="true"]:focus,
QLineEdit[error="true"][forceState="focus"] { border: 1px solid ${COLOR_DANGER}; }
QLineEdit:disabled { background: ${COLOR_DISABLED_BG}; color: ${COLOR_TEXT_MUTED}; border-color: ${COLOR_BORDER}; }

/* ═══ Table / tree views ════════════════════════════════════════════════
   Row backgrounds (normal/alt/hover/selected/multi) are painted by NexusRowDelegate
   from tokens, so QSS only neutralises Qt's own selection painting. */
QTableView, QTreeView, QListView {
    background: transparent;
    border: none;
    outline: 0;
    gridline-color: transparent;
    selection-background-color: transparent;
    alternate-background-color: transparent;
}
QTableView::item, QTreeView::item { padding: 0 ${SPACE_MD}px; border: none; background: transparent; }
QTableView::item:selected, QTreeView::item:selected { background: transparent; }

QHeaderView { background: transparent; border: none; }
QHeaderView::section {
    background: ${COLOR_BG_SURFACE};
    color: ${COLOR_TEXT_SECONDARY};
    border: none;
    border-bottom: 1px solid ${COLOR_BORDER};
    padding: 0 ${SPACE_MD}px;
    font-size: ${FONT_SIZE_XS}px;
    font-weight: 700;
    text-align: left;
}
QHeaderView::section:hover { color: ${COLOR_TEXT_PRIMARY}; }
QHeaderView::up-arrow   { image: url("${ICON_SORT_UP}");   width: ${ICON_SIZE_SM}px; height: ${ICON_SIZE_SM}px; }
QHeaderView::down-arrow { image: url("${ICON_SORT_DOWN}"); width: ${ICON_SIZE_SM}px; height: ${ICON_SIZE_SM}px; }

/* ═══ Scrollbars (thin, floating) ═══════════════════════════════════════ */
QScrollBar:vertical   { background: transparent; width: 10px;  margin: 2px; }
QScrollBar:horizontal { background: transparent; height: 10px; margin: 2px; }
QScrollBar::handle:vertical   { background: ${COLOR_SCROLL_HANDLE}; border-radius: 3px; min-height: ${SPACE_2XL}px; margin: 0 2px; }
QScrollBar::handle:horizontal { background: ${COLOR_SCROLL_HANDLE}; border-radius: 3px; min-width:  ${SPACE_2XL}px; margin: 2px 0; }
QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover { background: ${COLOR_SCROLL_HANDLE_HOVER}; }
QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; border: none; background: none; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }

/* ═══ Progress (drive usage, transfers) ═════════════════════════════════ */
QProgressBar { background: ${COLOR_BORDER_STRONG}; border: none; border-radius: ${RADIUS_SM}px; min-height: ${SPACE_XS}px; max-height: ${SPACE_XS}px; text-align: center; }
QProgressBar::chunk { background: ${COLOR_ACCENT_PRIMARY}; border-radius: ${RADIUS_SM}px; }
QProgressBar[level="warn"]::chunk   { background: ${COLOR_WARNING}; }
QProgressBar[level="danger"]::chunk { background: ${COLOR_DANGER}; }

/* ═══ Window chrome ═════════════════════════════════════════════════════ */
QStatusBar { background: ${COLOR_BG_SURFACE}; border-top: 1px solid ${COLOR_BORDER}; color: ${COLOR_TEXT_SECONDARY}; font-size: ${FONT_SIZE_SM}px; }
QStatusBar::item { border: none; }
QSplitter::handle { background: ${COLOR_BORDER}; }
QSplitter::handle:horizontal { width: 1px; }
QSplitter::handle:vertical { height: 1px; }
QScrollArea { border: none; background: transparent; }

QMenu {
    background: ${COLOR_BG_RAISED};
    border: 1px solid ${COLOR_BORDER_STRONG};
    border-radius: ${RADIUS_LG}px;
    padding: ${SPACE_XS}px;
}
QMenu::item { padding: ${SPACE_SM}px ${SPACE_XL}px ${SPACE_SM}px ${SPACE_MD}px; border-radius: ${RADIUS_MD}px; }
QMenu::item:selected { background: ${COLOR_SELECTED_BG}; }
QMenu::item:disabled { color: ${COLOR_TEXT_MUTED}; }
QMenu::separator { height: 1px; background: ${COLOR_BORDER}; margin: ${SPACE_XS}px ${SPACE_SM}px; }
''')


def build_mapping(tokens: ThemeTokens, font_family: str, mono_family: str) -> dict[str, object]:
    """Merge theme-independent base constants, theme tokens and runtime values."""
    mapping: dict[str, object] = {
        k: v for k, v in vars(base).items()
        if k.isupper() and isinstance(v, (int, float)) and not isinstance(v, bool)
    }
    for key, value in tokens.as_mapping().items():
        mapping[key] = to_qss(value) if key.startswith("COLOR_") else value
    mapping["FONT_FAMILY"] = font_family
    mapping["FONT_FAMILY_MONO"] = mono_family
    mapping["ICON_SORT_UP"] = icon_loader.tinted_svg_path("chevron-up", tokens.COLOR_TEXT_SECONDARY)
    mapping["ICON_SORT_DOWN"] = icon_loader.tinted_svg_path("chevron-down", tokens.COLOR_TEXT_SECONDARY)
    return mapping


def generate_qss(tokens: ThemeTokens, font_family: str = "sans-serif",
                 mono_family: str = "monospace") -> str:
    return QSS_TEMPLATE.substitute(build_mapping(tokens, font_family, mono_family))
