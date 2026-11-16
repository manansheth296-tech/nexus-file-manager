"""Small helpers shared by components."""
from __future__ import annotations

from PyQt6.QtWidgets import QWidget

from nexus.styles.theme_manager import theme_manager
from nexus.tokens.themes import ThemeTokens


def repolish(w: QWidget) -> None:
    """Re-evaluate QSS after a dynamic property changed."""
    w.style().unpolish(w)
    w.style().polish(w)
    w.update()


def set_prop(w: QWidget, name: str, value) -> None:
    if w.property(name) == value:
        return
    w.setProperty(name, value)
    repolish(w)


def force_state(w: QWidget, state: str | None) -> None:
    """Pin a visual state ('hover'|'pressed'|'focus'|None) – used by the gallery / design QA."""
    set_prop(w, "forceState", state or "")


def resolve_color(value: str, tokens: ThemeTokens | None = None) -> str:
    """Accept either a token name ('COLOR_SUCCESS') or a raw colour string."""
    tokens = tokens or theme_manager().tokens
    return getattr(tokens, value) if value.startswith("COLOR_") and hasattr(tokens, value) else value
