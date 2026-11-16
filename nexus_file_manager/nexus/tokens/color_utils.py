"""Colour helpers. Tokens are stored as CSS-style strings ('#38BDF8' or
'rgba(255, 255, 255, 0.04)') exactly as written in the spec."""
from __future__ import annotations

import re

from PyQt6.QtGui import QColor

_RGBA = re.compile(
    r"rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*(?:,\s*([\d.]+)\s*)?\)", re.I
)


def parse_color(value: str) -> tuple[int, int, int, float]:
    """-> (r, g, b, alpha 0..1)"""
    v = value.strip()
    if v.startswith("#"):
        h = v[1:]
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
        a = int(h[6:8], 16) / 255 if len(h) == 8 else 1.0
        return r, g, b, a
    m = _RGBA.fullmatch(v)
    if not m:
        raise ValueError(f"Unsupported colour format: {value!r}")
    r, g, b = (round(float(m.group(i))) for i in (1, 2, 3))
    a = float(m.group(4)) if m.group(4) is not None else 1.0
    return r, g, b, a


def to_qcolor(value: str) -> QColor:
    r, g, b, a = parse_color(value)
    return QColor(r, g, b, round(a * 255))


def to_hex(value: str) -> str:
    """Opaque #rrggbb (alpha dropped) – used for SVG tinting."""
    r, g, b, _ = parse_color(value)
    return f"#{r:02x}{g:02x}{b:02x}"


def to_qss(value: str) -> str:
    """QSS wants alpha as 0-255, not 0-1 – convert here, once."""
    r, g, b, a = parse_color(value)
    if a >= 1:
        return f"#{r:02x}{g:02x}{b:02x}"
    return f"rgba({r}, {g}, {b}, {round(a * 255)})"


def with_alpha(value: str, alpha: float) -> str:
    r, g, b, _ = parse_color(value)
    return f"rgba({r}, {g}, {b}, {alpha:g})"


def _mix(value: str, target: int, amount: float) -> str:
    r, g, b, a = parse_color(value)
    mix = lambda c: round(c + (target - c) * amount)  # noqa: E731
    out = f"#{mix(r):02x}{mix(g):02x}{mix(b):02x}"
    return out if a >= 1 else with_alpha(out, a)


def lighten(value: str, amount: float) -> str:
    return _mix(value, 255, amount)


def darken(value: str, amount: float) -> str:
    return _mix(value, 0, amount)


def lerp_qcolor(a: QColor, b: QColor, t: float) -> QColor:
    t = max(0.0, min(1.0, t))
    return QColor(
        round(a.red() + (b.red() - a.red()) * t),
        round(a.green() + (b.green() - a.green()) * t),
        round(a.blue() + (b.blue() - a.blue()) * t),
        round(a.alpha() + (b.alpha() - a.alpha()) * t),
    )


def composite(fg: str, bg: str) -> str:
    """Opaque #rrggbb of `fg` (with its alpha) laid over an opaque `bg`."""
    fr, fg_, fb, fa = parse_color(fg)
    br, bg_, bb, _ = parse_color(bg)
    mix = lambda f, b: round(f * fa + b * (1 - fa))  # noqa: E731
    return f"#{mix(fr, br):02x}{mix(fg_, bg_):02x}{mix(fb, bb):02x}"


def _channel(c: int) -> float:
    c /= 255
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def luminance(value: str) -> float:
    r, g, b, _ = parse_color(value)
    return 0.2126 * _channel(r) + 0.7152 * _channel(g) + 0.0722 * _channel(b)


def contrast_ratio(fg: str, bg: str) -> float:
    """WCAG 2.x contrast ratio; a translucent `fg` is composited over `bg` first."""
    lf, lb = luminance(composite(fg, bg)), luminance(bg)
    hi, lo = max(lf, lb), min(lf, lb)
    return (hi + 0.05) / (lo + 0.05)
