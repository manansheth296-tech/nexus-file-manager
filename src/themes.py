"""Theme and Styling Engine for Nexus File Manager: presets, custom QSS, and theme switching."""

from typing import Dict, Any, List

THEMES: Dict[str, Dict[str, str]] = {
    "midnight_cyber": {
        "name": "Midnight Cyber (Default)",
        "mode": "dark",
        "bg_base": "#0B0F19",
        "bg_surface": "#111827",
        "bg_card": "rgba(255, 255, 255, 0.04)",
        "bg_hover": "rgba(56, 189, 248, 0.12)",
        "bg_selected": "rgba(56, 189, 248, 0.22)",
        "border": "rgba(255, 255, 255, 0.08)",
        "border_focus": "#38BDF8",
        "accent": "#38BDF8",
        "accent_secondary": "#818CF8",
        "text_primary": "#F8FAFC",
        "text_secondary": "#94A3B8",
        "text_muted": "#64748B",
    },
    "dracula_velvet": {
        "name": "Dracula Velvet",
        "mode": "dark",
        "bg_base": "#1E1F29",
        "bg_surface": "#282A36",
        "bg_card": "rgba(255, 255, 255, 0.05)",
        "bg_hover": "rgba(189, 147, 249, 0.15)",
        "bg_selected": "rgba(189, 147, 249, 0.25)",
        "border": "rgba(255, 255, 255, 0.1)",
        "border_focus": "#FF79C6",
        "accent": "#BD93F9",
        "accent_secondary": "#FF79C6",
        "text_primary": "#F8F8F2",
        "text_secondary": "#BFBFBF",
        "text_muted": "#6272A4",
    },
    "catppuccin_mocha": {
        "name": "Catppuccin Mocha",
        "mode": "dark",
        "bg_base": "#181825",
        "bg_surface": "#1E1E2E",
        "bg_card": "rgba(255, 255, 255, 0.04)",
        "bg_hover": "rgba(137, 180, 250, 0.12)",
        "bg_selected": "rgba(137, 180, 250, 0.22)",
        "border": "#313244",
        "border_focus": "#89B4FA",
        "accent": "#89B4FA",
        "accent_secondary": "#F5C2E7",
        "text_primary": "#CDD6F4",
        "text_secondary": "#A6ADC8",
        "text_muted": "#6C7086",
    },
    "nord_frost": {
        "name": "Nord Frost",
        "mode": "dark",
        "bg_base": "#242933",
        "bg_surface": "#2E3440",
        "bg_card": "rgba(255, 255, 255, 0.04)",
        "bg_hover": "rgba(136, 192, 208, 0.14)",
        "bg_selected": "rgba(136, 192, 208, 0.24)",
        "border": "#3B4252",
        "border_focus": "#88C0D0",
        "accent": "#88C0D0",
        "accent_secondary": "#81A1C1",
        "text_primary": "#ECEFF4",
        "text_secondary": "#D8DEE9",
        "text_muted": "#4C566A",
    },
    "oled_pure_black": {
        "name": "OLED Pure Black",
        "mode": "dark",
        "bg_base": "#000000",
        "bg_surface": "#0A0A0A",
        "bg_card": "#121212",
        "bg_hover": "#1E1E1E",
        "bg_selected": "#282828",
        "border": "#222222",
        "border_focus": "#00E5FF",
        "accent": "#00E5FF",
        "accent_secondary": "#7C4DFF",
        "text_primary": "#FFFFFF",
        "text_secondary": "#AAAAAA",
        "text_muted": "#555555",
    },
    "modern_light": {
        "name": "Modern Light",
        "mode": "light",
        "bg_base": "#F1F5F9",
        "bg_surface": "#FFFFFF",
        "bg_card": "#F8FAFC",
        "bg_hover": "rgba(14, 165, 233, 0.1)",
        "bg_selected": "rgba(14, 165, 233, 0.18)",
        "border": "#E2E8F0",
        "border_focus": "#0284C7",
        "accent": "#0284C7",
        "accent_secondary": "#4F46E5",
        "text_primary": "#0F172A",
        "text_secondary": "#475569",
        "text_muted": "#94A3B8",
    },
}


def generate_stylesheet(theme_key: str = "midnight_cyber") -> str:
    """Generate high-fidelity modern Qt StyleSheet for the application."""
    t = THEMES.get(theme_key, THEMES["midnight_cyber"])

    return f"""
    /* Global Application Reset */
    QWidget {{
        background-color: {t["bg_base"]};
        color: {t["text_primary"]};
        font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, 'Roboto', sans-serif;
        font-size: 13px;
        selection-background-color: {t["accent"]};
        selection-color: #000000;
    }}

    /* Main Window & Central Containers */
    QMainWindow, QDialog {{
        background-color: {t["bg_base"]};
    }}

    QSplitter::handle {{
        background-color: {t["border"]};
        width: 1px;
    }}
    QSplitter::handle:hover {{
        background-color: {t["accent"]};
    }}

    /* Modern Rounded Push Buttons */
    QPushButton {{
        background-color: {t["bg_surface"]};
        color: {t["text_primary"]};
        border: 1px solid {t["border"]};
        border-radius: 6px;
        padding: 5px 12px;
        font-weight: 500;
    }}
    QPushButton:hover {{
        background-color: {t["bg_hover"]};
        border-color: {t["accent"]};
        color: {t["accent"]};
    }}
    QPushButton:pressed {{
        background-color: {t["bg_selected"]};
    }}
    QPushButton:disabled {{
        background-color: {t["bg_card"]};
        color: {t["text_muted"]};
        border-color: transparent;
    }}

    /* Tool Buttons */
    QToolButton {{
        background-color: transparent;
        border: 1px solid transparent;
        border-radius: 6px;
        padding: 4px;
        color: {t["text_secondary"]};
    }}
    QToolButton:hover {{
        background-color: {t["bg_hover"]};
        border-color: {t["border"]};
        color: {t["accent"]};
    }}
    QToolButton:pressed {{
        background-color: {t["bg_selected"]};
    }}

    /* Pill-style Text & Search Input */
    QLineEdit {{
        background-color: {t["bg_surface"]};
        color: {t["text_primary"]};
        border: 1px solid {t["border"]};
        border-radius: 6px;
        padding: 5px 10px;
        font-size: 12px;
    }}
    QLineEdit:focus {{
        border: 1px solid {t["border_focus"]};
        background-color: {t["bg_base"]};
    }}

    /* Modern Table Widget */
    QTableWidget {{
        background-color: {t["bg_surface"]};
        border: 1px solid {t["border"]};
        border-radius: 8px;
        gridline-color: transparent;
        outline: none;
    }}
    QTableWidget::item {{
        padding: 6px 8px;
        border-bottom: 1px solid {t["border"]};
    }}
    QTableWidget::item:hover {{
        background-color: {t["bg_hover"]};
    }}
    QTableWidget::item:selected {{
        background-color: {t["bg_selected"]};
        color: {t["accent"]};
        font-weight: 600;
    }}

    /* Header View */
    QHeaderView::section {{
        background-color: {t["bg_base"]};
        color: {t["text_secondary"]};
        padding: 6px 8px;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        border: none;
        border-bottom: 1px solid {t["border"]};
    }}
    QHeaderView::section:hover {{
        color: {t["accent"]};
    }}

    /* List Widgets (Sidebar / Grid) */
    QListWidget {{
        background-color: {t["bg_surface"]};
        border: 1px solid {t["border"]};
        border-radius: 8px;
        outline: none;
    }}
    QListWidget::item {{
        padding: 6px 8px;
        border-radius: 6px;
        margin: 1px 2px;
    }}
    QListWidget::item:hover {{
        background-color: {t["bg_hover"]};
        color: {t["accent"]};
    }}
    QListWidget::item:selected {{
        background-color: {t["bg_selected"]};
        color: {t["accent"]};
        font-weight: 600;
    }}

    /* Tree Widget */
    QTreeWidget {{
        background-color: {t["bg_surface"]};
        border: 1px solid {t["border"]};
        border-radius: 8px;
        outline: none;
    }}
    QTreeWidget::item {{
        padding: 5px;
    }}
    QTreeWidget::item:hover {{
        background-color: {t["bg_hover"]};
    }}
    QTreeWidget::item:selected {{
        background-color: {t["bg_selected"]};
        color: {t["accent"]};
    }}

    /* Modern Tabs */
    QTabWidget::pane {{
        border: 1px solid {t["border"]};
        border-radius: 8px;
        background-color: {t["bg_surface"]};
        top: -1px;
    }}
    QTabBar::tab {{
        background-color: {t["bg_base"]};
        color: {t["text_secondary"]};
        border: 1px solid {t["border"]};
        border-bottom: none;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
        padding: 7px 16px;
        font-weight: 500;
        margin-right: 2px;
    }}
    QTabBar::tab:selected {{
        background-color: {t["bg_surface"]};
        color: {t["accent"]};
        font-weight: 600;
        border-bottom: 2px solid {t["accent"]};
    }}
    QTabBar::tab:hover:!selected {{
        background-color: {t["bg_hover"]};
        color: {t["text_primary"]};
    }}

    /* Modern Thin Scrollbars */
    QScrollBar:vertical {{
        background: transparent;
        width: 8px;
        margin: 0px;
    }}
    QScrollBar::handle:vertical {{
        background: {t["border"]};
        min-height: 24px;
        border-radius: 4px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {t["accent"]};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QScrollBar:horizontal {{
        background: transparent;
        height: 8px;
        margin: 0px;
    }}
    QScrollBar::handle:horizontal {{
        background: {t["border"]};
        min-width: 24px;
        border-radius: 4px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {t["accent"]};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        height: 0px;
    }}

    /* Context Menus */
    QMenu {{
        background-color: {t["bg_surface"]};
        color: {t["text_primary"]};
        border: 1px solid {t["border"]};
        border-radius: 8px;
        padding: 6px;
    }}
    QMenu::item {{
        padding: 6px 24px 6px 12px;
        border-radius: 4px;
    }}
    QMenu::item:selected {{
        background-color: {t["bg_hover"]};
        color: {t["accent"]};
    }}
    QMenu::separator {{
        height: 1px;
        background-color: {t["border"]};
        margin: 4px 6px;
    }}

    /* Progress Bar */
    QProgressBar {{
        background-color: {t["bg_card"]};
        border: 1px solid {t["border"]};
        border-radius: 4px;
        text-align: center;
        font-size: 10px;
        color: {t["text_secondary"]};
    }}
    QProgressBar::chunk {{
        background-color: {t["accent"]};
        border-radius: 3px;
    }}

    /* Status Bar */
    QStatusBar {{
        background-color: {t["bg_base"]};
        color: {t["text_secondary"]};
        border-top: 1px solid {t["border"]};
        font-size: 11px;
        padding: 2px 6px;
    }}

    /* Tooltips */
    QToolTip {{
        background-color: {t["bg_surface"]};
        color: {t["text_primary"]};
        border: 1px solid {t["border"]};
        border-radius: 6px;
        padding: 6px 8px;
        font-size: 12px;
    }}
    """
