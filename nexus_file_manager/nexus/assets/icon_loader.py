"""
SVG icon loading + runtime tinting.

Icons in assets/icons/*.svg use `stroke="currentColor"`; we swap in a token colour
at load time, so one SVG set serves every theme. Kept free of widget imports so
the QSS generator can use it without circular dependencies.
"""
from __future__ import annotations

import tempfile
from functools import lru_cache
from pathlib import Path

from PyQt6.QtCore import QByteArray, QRectF, Qt
from PyQt6.QtGui import QGuiApplication, QIcon, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer

from nexus.tokens.base import ICON_SIZE_MD
from nexus.tokens.color_utils import to_hex

ICON_DIR = Path(__file__).resolve().parent / "icons"
_tmp_dir: Path | None = None


@lru_cache(maxsize=None)
def svg_source(name: str) -> str:
    path = ICON_DIR / f"{name}.svg"
    if not path.exists():
        raise FileNotFoundError(f"Icon '{name}' not found in {ICON_DIR}")
    return path.read_text(encoding="utf-8")


def _dpr() -> float:
    screen = QGuiApplication.primaryScreen()
    return max(2.0, screen.devicePixelRatio() if screen else 1.0)  # always crisp on HiDPI


@lru_cache(maxsize=1024)
def _render(name: str, hex_color: str, size: int, dpr: float) -> QPixmap:
    svg = svg_source(name).replace("currentColor", hex_color)
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    px = int(size * dpr)
    pm = QPixmap(px, px)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(p, QRectF(0, 0, px, px))
    p.end()
    pm.setDevicePixelRatio(dpr)
    return pm


def render_pixmap(name: str, color: str, size: int = ICON_SIZE_MD) -> QPixmap:
    """Tinted pixmap; `color` is any token string (hex or rgba)."""
    return _render(name, to_hex(color), size, _dpr())


def make_icon(name: str, color: str, disabled_color: str | None = None,
              size: int = ICON_SIZE_MD) -> QIcon:
    icon = QIcon()
    icon.addPixmap(render_pixmap(name, color, size), QIcon.Mode.Normal)
    icon.addPixmap(render_pixmap(name, disabled_color or color, size), QIcon.Mode.Disabled)
    return icon


def tinted_svg_path(name: str, color: str) -> str:
    """Write a tinted copy to a temp dir and return a QSS-safe `url()` path.
    QSS can only reference images by file path, so this feeds header sort arrows etc."""
    global _tmp_dir
    if _tmp_dir is None:
        _tmp_dir = Path(tempfile.mkdtemp(prefix="nexus_icons_"))
    hex_color = to_hex(color)
    out = _tmp_dir / f"{name}_{hex_color[1:]}.svg"
    if not out.exists():
        out.write_text(svg_source(name).replace("currentColor", hex_color), encoding="utf-8")
    return out.as_posix()
