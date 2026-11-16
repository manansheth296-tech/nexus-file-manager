"""
Preview cards for the inspector [spec Screen 3] – one per file-type state:
Word, Spreadsheet, Image, PDF, Archive, Audio/Video, Hex dump (+ a generic fallback).
All content is mock; painted widgets draw only from tokens. HOOK: replace mock_data.* with real
extractors (docx text, first PDF page raster, archive listing, ...).
"""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QFontMetricsF, QLinearGradient, QPainter, QPainterPath, QPolygonF
from PyQt6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget

import os
import shutil
import subprocess
import sys

from nexus.assets import icon_loader
from nexus.components import Badge, Button, Card
from nexus.components._util import resolve_color
from nexus.components.icon_tile import IconTile
from nexus.core import mock_data as md
from nexus.styles.theme_manager import theme_manager
from nexus.tokens.base import (FONT_SIZE_XS, PREVIEW_CARD_WIDTH, SPACE_LG, SPACE_MD, SPACE_SM, SPACE_XL)
from nexus.tokens.color_utils import to_qcolor, with_alpha
from nexus.tokens import file_types as ft

W = PREVIEW_CARD_WIDTH


def _frame(p: QPainter, rect: QRectF, t) -> None:
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(to_qcolor(t.COLOR_BORDER))
    p.setBrush(to_qcolor(t.COLOR_BG_CARD))
    p.drawRoundedRect(rect.adjusted(.5, .5, -.5, -.5), t.RADIUS_LG, t.RADIUS_LG)


class _Painted(QWidget):
    def __init__(self, height: int):
        super().__init__()
        self.setFixedSize(W, height)
        theme_manager().theme_changed.connect(self._on_theme)

    def _on_theme(self, _t) -> None:
        self.update()


def _wrapped(text: str, role: str, width: int) -> QLabel:
    """Word-wrapped label with an explicit height. QLabel height-for-width is unreliable inside a
    QScrollArea, so measure once at the known column width instead."""
    lab = QLabel(text)
    lab.setProperty("role", role)
    lab.setWordWrap(True)
    lab.setFixedWidth(width)
    lab.ensurePolished()               # apply QSS font for the role before measuring
    h = lab.fontMetrics().boundingRect(0, 0, width, 100000, int(Qt.TextFlag.TextWordWrap), text).height()
    lab.setFixedHeight(h + 2)
    return lab


class KeyValueList(QWidget):
    def __init__(self, rows: list[tuple[str, str]]):
        super().__init__()
        g = QGridLayout(self)
        g.setContentsMargins(0, 0, 0, 0)
        g.setHorizontalSpacing(SPACE_MD)
        g.setVerticalSpacing(SPACE_SM)
        for r, (k, v) in enumerate(rows):
            kl = QLabel(k)
            kl.setProperty("role", "muted")
            vl = QLabel(v)
            vl.setWordWrap(True)
            vl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
            g.addWidget(kl, r, 0, Qt.AlignmentFlag.AlignTop)
            g.addWidget(vl, r, 1)
        g.setColumnStretch(1, 1)


# ── 1. Word document ───────────────────────────────────────────────────────
class DocPreview(Card):
    def __init__(self, file: dict):
        super().__init__("card")
        self.setMaximumWidth(W)
        d = md.WORD_PREVIEW
        lay = QVBoxLayout(self)
        lay.setContentsMargins(SPACE_LG, SPACE_LG, SPACE_LG, SPACE_LG)
        lay.setSpacing(SPACE_MD)
        top = QHBoxLayout()
        top.setSpacing(SPACE_SM)
        top.addWidget(IconTile("file-text", ft.FILE_COLOR_WORD, 32))
        top.addWidget(Badge("WORD", ft.FILE_COLOR_WORD))
        top.addWidget(Badge(f"{d['words']:,} words", "COLOR_ACCENT_PRIMARY"))
        top.addStretch(1)
        lay.addLayout(top)
        inner = W - 2 * SPACE_LG - 2          # card content width (minus border)
        lay.addWidget(_wrapped(d["title"], "subheading", inner))
        for para in d["paragraphs"]:
            lay.addWidget(_wrapped(para, "secondary", inner))


# ── 2. Spreadsheet ─────────────────────────────────────────────────────────
class SheetPreview(_Painted):
    ROW_H, HEAD_H, ROWNUM_W = 24, 22, 24

    def __init__(self, file: dict):
        super().__init__(self.HEAD_H + self.ROW_H * len(md.SHEET_PREVIEW["rows"]) + 2 * SPACE_SM)

    def paintEvent(self, event):
        t = theme_manager().tokens
        p = QPainter(self)
        _frame(p, QRectF(self.rect()), t)
        d = md.SHEET_PREVIEW
        x0, y0 = SPACE_SM, SPACE_SM
        ncols = len(d["columns"])
        first = 56                                         # label column is wider than the numeric ones
        cw = (W - 2 * SPACE_SM - self.ROWNUM_W - first) / (ncols - 1)
        colx = lambda c: x0 + self.ROWNUM_W + (0 if c == 0 else first + (c - 1) * cw)   # noqa: E731
        colw = lambda c: first if c == 0 else cw                                          # noqa: E731
        small = QFont(self.font())
        small.setPixelSize(FONT_SIZE_XS)
        p.setFont(small)
        # header
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(to_qcolor(t.COLOR_BG_SURFACE))
        p.drawRect(QRectF(x0, y0, W - 2 * SPACE_SM, self.HEAD_H))
        p.setPen(to_qcolor(t.COLOR_TEXT_MUTED))
        for c, name in enumerate(d["columns"]):
            p.drawText(QRectF(colx(c), y0, colw(c), self.HEAD_H), Qt.AlignmentFlag.AlignCenter, name)
        # rows (alternating cells, first row = header row of the data)
        for r, row in enumerate(d["rows"]):
            y = y0 + self.HEAD_H + r * self.ROW_H
            if r % 2:
                p.fillRect(QRectF(x0, y, W - 2 * SPACE_SM, self.ROW_H), to_qcolor(t.COLOR_ROW_ALT))
            p.setPen(to_qcolor(t.COLOR_TEXT_MUTED))
            p.drawText(QRectF(x0, y, self.ROWNUM_W, self.ROW_H), Qt.AlignmentFlag.AlignCenter, str(r + 1))
            for c, cell in enumerate(row):
                strong = r == 0 or r == len(d["rows"]) - 2
                f = QFont(small)
                f.setWeight(QFont.Weight.DemiBold if strong else QFont.Weight.Normal)
                p.setFont(f)
                p.setPen(to_qcolor(t.COLOR_TEXT_PRIMARY if (strong or c == 0) else t.COLOR_TEXT_SECONDARY))
                align = Qt.AlignmentFlag.AlignLeft if c == 0 else Qt.AlignmentFlag.AlignRight
                p.drawText(QRectF(colx(c) + SPACE_SM, y, colw(c) - 2 * SPACE_SM, self.ROW_H),
                           align | Qt.AlignmentFlag.AlignVCenter, cell)
        # hairlines
        p.setPen(to_qcolor(t.COLOR_BORDER))
        total_h = self.HEAD_H + self.ROW_H * len(d["rows"])
        for c in range(ncols + 1):
            xx = colx(c) if c < ncols else x0 + W - 2 * SPACE_SM
            p.drawLine(QPointF(xx, y0), QPointF(xx, y0 + total_h))
        p.drawLine(QPointF(x0, y0 + self.HEAD_H), QPointF(x0 + W - 2 * SPACE_SM, y0 + self.HEAD_H))
        p.end()


# ── 3. Image ───────────────────────────────────────────────────────────────
class _ImageCanvas(_Painted):
    def __init__(self):
        super().__init__(168)

    def paintEvent(self, event):
        t = theme_manager().tokens
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(.5, .5, -.5, -.5)
        clip = QPainterPath()
        clip.addRoundedRect(r, t.RADIUS_LG, t.RADIUS_LG)
        p.setClipPath(clip)
        g = QLinearGradient(r.topLeft(), r.bottomRight())
        g.setColorAt(0, to_qcolor(with_alpha(t.COLOR_ACCENT_SECONDARY, 0.55)))
        g.setColorAt(1, to_qcolor(with_alpha(t.COLOR_ACCENT_PRIMARY, 0.55)))
        p.fillRect(r, g)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(to_qcolor(with_alpha(t.COLOR_TEXT_PRIMARY, 0.55)))
        p.drawEllipse(QPointF(r.right() - 56, r.top() + 44), 18, 18)                 # sun
        for pts, a in (([(0, 168), (70, 84), (130, 168)], 0.30), ([(60, 168), (150, 70), (250, 168)], 0.45),
                       ([(170, 168), (230, 104), (W, 150), (W, 168)], 0.60)):         # hills
            p.setBrush(to_qcolor(with_alpha(t.COLOR_BG_BASE, a)))
            p.drawPolygon(QPolygonF([QPointF(x, y) for x, y in pts]))
        p.setClipping(False)
        p.setPen(to_qcolor(t.COLOR_BORDER_STRONG))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(r, t.RADIUS_LG, t.RADIUS_LG)
        p.end()


class ImagePreview(QWidget):
    def __init__(self, file: dict):
        super().__init__()
        d = md.IMAGE_PREVIEW
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(SPACE_MD)
        lay.addWidget(_ImageCanvas())
        row = QHBoxLayout()
        row.setSpacing(SPACE_SM)
        row.addWidget(Badge(f"{d['width']} × {d['height']} px", "COLOR_ACCENT_PRIMARY"))
        row.addWidget(Badge(f"{d['width'] * d['height'] / 1e6:.1f} MP", "COLOR_SUCCESS"))
        ext = file["name"].rsplit(".", 1)[-1].upper()
        row.addWidget(Badge(ext, ft.FILE_COLOR_IMAGE))
        row.addStretch(1)
        lay.addLayout(row)


# ── 4. PDF ─────────────────────────────────────────────────────────────────
class _PdfPage(_Painted):
    PAGE_W, PAGE_H = 148, 200

    def __init__(self):
        super().__init__(224)

    def paintEvent(self, event):
        t = theme_manager().tokens
        p = QPainter(self)
        _frame(p, QRectF(self.rect()), t)
        page = QRectF((W - self.PAGE_W) / 2, (self.height() - self.PAGE_H) / 2, self.PAGE_W, self.PAGE_H)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(0, 0, 0, 70))                                   # soft drop shadow
        p.drawRoundedRect(page.translated(0, 3), 3, 3)
        p.setBrush(to_qcolor(t.COLOR_PAPER))
        p.drawRoundedRect(page, 3, 3)
        ink = to_qcolor(t.COLOR_PAPER_INK)
        p.setBrush(to_qcolor(ft.FILE_COLOR_PDF))                          # title bar in PDF accent
        p.drawRoundedRect(QRectF(page.x() + 14, page.y() + 16, 70, 8), 2, 2)
        p.setBrush(ink)
        y = page.y() + 38
        for i, frac in enumerate((1, .94, 1, .88, .97, .6, 0, 1, .92, 1, .85, .96, .5)):
            if frac == 0:
                y += 8
                continue
            p.drawRoundedRect(QRectF(page.x() + 14, y, (self.PAGE_W - 28) * frac, 4), 2, 2)
            y += 10
        p.end()


class PdfPreview(QWidget):
    def __init__(self, file: dict):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(SPACE_MD)
        lay.addWidget(_PdfPage())
        row = QHBoxLayout()
        row.setSpacing(SPACE_SM)
        row.addWidget(Badge(f"{md.PDF_PREVIEW['pages']} pages", ft.FILE_COLOR_PDF))
        row.addWidget(Badge("Page 1", "COLOR_ACCENT_PRIMARY"))
        row.addStretch(1)
        lay.addLayout(row)


# ── 5. Archive ─────────────────────────────────────────────────────────────
class _ArchiveList(_Painted):
    ROW = 26

    def __init__(self):
        super().__init__(len(md.ARCHIVE_PREVIEW) * self.ROW + 2 * SPACE_SM)

    def paintEvent(self, event):
        t = theme_manager().tokens
        p = QPainter(self)
        _frame(p, QRectF(self.rect()), t)
        small = QFont(self.font())
        small.setPixelSize(FONT_SIZE_XS)
        for i, (depth, name, size) in enumerate(md.ARCHIVE_PREVIEW):
            y = SPACE_SM + i * self.ROW
            x = SPACE_MD + depth * 16
            kind = "folder" if size is None else (ft.file_type_for(name) or "file")
            color = ft.kind_color(kind)
            pm = icon_loader.render_pixmap(ft.kind_icon(kind), resolve_color(color, t), 16)
            p.drawPixmap(int(x), int(y + (self.ROW - 16) / 2), pm)
            p.setFont(self.font())
            p.setPen(to_qcolor(t.COLOR_TEXT_PRIMARY if size is None else t.COLOR_TEXT_SECONDARY))
            size_w = 62
            tx = x + 16 + SPACE_SM
            fm = QFontMetricsF(self.font())
            p.drawText(QRectF(tx, y, W - tx - size_w - SPACE_MD, self.ROW), Qt.AlignmentFlag.AlignVCenter,
                       fm.elidedText(name, Qt.TextElideMode.ElideRight, W - tx - size_w - SPACE_MD))
            if size is not None:
                p.setFont(small)
                p.setPen(to_qcolor(t.COLOR_TEXT_MUTED))
                p.drawText(QRectF(W - size_w - SPACE_MD, y, size_w, self.ROW),
                           Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, md.format_size(size))
        p.end()


class ArchivePreview(QWidget):
    def __init__(self, file: dict):
        super().__init__()
        entries = md.ARCHIVE_PREVIEW
        files = sum(1 for _, _, s in entries if s is not None)
        folders = len(entries) - files
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(SPACE_MD)
        row = QHBoxLayout()
        row.setSpacing(SPACE_SM)
        row.addWidget(Badge(f"{files} files", ft.FILE_COLOR_ARCHIVE))
        row.addWidget(Badge(f"{folders} folders", "COLOR_ACCENT_SECONDARY"))
        row.addStretch(1)
        lay.addLayout(row)
        lay.addWidget(_ArchiveList())
        note = QLabel("Contents listed without extracting")
        note.setProperty("role", "muted")
        lay.addWidget(note)


def play_media_vlc(file_path: str | None) -> bool:
    """Launch media directly in VLC Media Player, falling back to OS player."""
    if not file_path or not os.path.exists(file_path):
        return False
    vlc_candidates = [
        r"C:\Program Files\VideoLAN\VLC\vlc.exe",
        r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe",
    ]
    vlc_exe = shutil.which("vlc")
    if not vlc_exe:
        for vc in vlc_candidates:
            if os.path.exists(vc):
                vlc_exe = vc
                break
    try:
        if vlc_exe:
            subprocess.Popen([vlc_exe, file_path])
            return True
        elif sys.platform.startswith("win"):
            os.startfile(file_path)
            return True
        elif sys.platform == "darwin":
            subprocess.Popen(["open", file_path])
            return True
        else:
            subprocess.Popen(["xdg-open", file_path])
            return True
    except Exception as e:
        print(f"Error launching media player for {file_path}: {e}", file=sys.stderr)
        return False


# ── 6. Audio / Video ───────────────────────────────────────────────────────
class _MediaCanvas(_Painted):
    clicked = pyqtSignal()

    def __init__(self, video: bool):
        super().__init__(132)
        self._video = video
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Click to play in VLC Media Player" if video else "Audio Preview")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def paintEvent(self, event):
        t = theme_manager().tokens
        accent = ft.FILE_COLOR_VIDEO if self._video else ft.FILE_COLOR_AUDIO
        p = QPainter(self)
        _frame(p, QRectF(self.rect()), t)
        p.setPen(Qt.PenStyle.NoPen)
        if self._video:                                                   # frame placeholder + play disc
            frame = QRectF(self.rect()).adjusted(SPACE_SM, SPACE_SM, -SPACE_SM, -SPACE_SM)
            g = QLinearGradient(frame.topLeft(), frame.bottomRight())
            g.setColorAt(0, to_qcolor(with_alpha(accent, 0.45)))
            g.setColorAt(1, to_qcolor(with_alpha(t.COLOR_BG_BASE, 0.9)))
            p.setBrush(g)
            p.drawRoundedRect(frame, t.RADIUS_MD, t.RADIUS_MD)
            c = frame.center()
            p.setBrush(to_qcolor(with_alpha(t.COLOR_TEXT_PRIMARY, 0.9)))
            p.drawEllipse(c, 22, 22)
            p.setBrush(to_qcolor(t.COLOR_BG_BASE))
            p.drawPolygon(QPolygonF([QPointF(c.x() - 6, c.y() - 10), QPointF(c.x() - 6, c.y() + 10), QPointF(c.x() + 11, c.y())]))
        else:                                                             # waveform with a played portion
            bars, bw, gap = 46, 3.0, 2.0
            x0 = (W - bars * (bw + gap) + gap) / 2
            mid = self.height() / 2
            for i in range(bars):
                h = 10 + 46 * abs(math.sin(i * 0.55) * math.cos(i * 0.21 + 1.3))
                played = i < bars * 0.35
                p.setBrush(to_qcolor(accent if played else with_alpha(accent, 0.30)))
                p.drawRoundedRect(QRectF(x0 + i * (bw + gap), mid - h / 2, bw, h), 1.5, 1.5)
        p.end()


class MediaPreview(QWidget):
    def __init__(self, file: dict):
        super().__init__()
        self.file = file
        video = file.get("kind") == "video"
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(SPACE_MD)

        canvas = _MediaCanvas(video)
        canvas.clicked.connect(self._play)
        lay.addWidget(canvas)

        self.btn_play = Button("Play in VLC" if video else "Play Audio", icon="play", variant="primary")
        self.btn_play.setToolTip(f"Open {file.get('name', 'file')} directly in VLC Media Player")
        self.btn_play.clicked.connect(self._play)
        lay.addWidget(self.btn_play)

        lay.addWidget(KeyValueList(md.MEDIA_PREVIEW["video" if video else "audio"]))

    def _play(self) -> None:
        path = self.file.get("path")
        play_media_vlc(path)


# ── 7. Hex dump ────────────────────────────────────────────────────────────
class HexPreview(_Painted):
    BYTES_PER_LINE, LINES = 8, 12

    def __init__(self, file: dict):
        super().__init__(self.LINES * 18 + 2 * SPACE_MD)
        self._data = md.mock_hex_bytes(self.BYTES_PER_LINE * self.LINES)

    def _mono(self) -> QFont:
        f = QFont("monospace")
        f.setStyleHint(QFont.StyleHint.Monospace)
        mono = theme_manager().property("mono_family")
        if mono:
            f.setFamily(mono)
        for px in range(FONT_SIZE_XS + 1, 7, -1):                       # shrink until 4+2+23+2+8 chars fit
            f.setPixelSize(px)
            if QFontMetricsF(f).horizontalAdvance("0" * 39) <= W - 2 * SPACE_MD:
                break
        return f

    def paintEvent(self, event):
        t = theme_manager().tokens
        p = QPainter(self)
        _frame(p, QRectF(self.rect()), t)
        font = self._mono()
        p.setFont(font)
        cw = QFontMetricsF(font).horizontalAdvance("0")
        n = self.BYTES_PER_LINE
        for line in range(self.LINES):
            chunk = self._data[line * n:(line + 1) * n]
            y = SPACE_MD + line * 18
            rect = lambda col, ncol: QRectF(SPACE_MD + col * cw, y, ncol * cw + 2, 18)  # noqa: E731
            p.setPen(to_qcolor(t.COLOR_TEXT_MUTED))
            p.drawText(rect(0, 4), Qt.AlignmentFlag.AlignVCenter, f"{line * n:04X}")
            p.setPen(to_qcolor(t.COLOR_TEXT_PRIMARY))
            p.drawText(rect(6, 24), Qt.AlignmentFlag.AlignVCenter, " ".join(f"{b:02X}" for b in chunk))
            p.setPen(to_qcolor(t.COLOR_ACCENT_PRIMARY))
            p.drawText(rect(32, 8), Qt.AlignmentFlag.AlignVCenter,
                       "".join(chr(b) if 32 <= b < 127 else "." for b in chunk))
        p.end()


# ── fallback ───────────────────────────────────────────────────────────────
class GenericPreview(Card):
    def __init__(self, file: dict):
        super().__init__("card")
        self.setMaximumWidth(W)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(SPACE_LG, SPACE_XL, SPACE_LG, SPACE_XL)
        lay.setSpacing(SPACE_MD)
        lay.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        lay.addWidget(IconTile(ft.kind_icon(file["kind"]), ft.kind_color(file["kind"]), 48), 0, Qt.AlignmentFlag.AlignHCenter)
        lab = QLabel("Folder" if file["kind"] == "folder" else "No preview available")
        lab.setProperty("role", "muted")
        lab.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(lab)


def make_preview(file: dict) -> QWidget:
    kind = file["kind"]
    ext = file["name"].rsplit(".", 1)[-1].lower() if "." in file["name"] else ""
    if kind == "word":
        return DocPreview(file)
    if kind == "excel":
        return SheetPreview(file)
    if kind == "image":
        return ImagePreview(file)
    if kind == "pdf":
        return PdfPreview(file)
    if kind == "archive":
        return ArchivePreview(file)
    if kind in ("audio", "video"):
        return MediaPreview(file)
    if kind == "binary" or ext in ("exe", "bin", "dll"):
        return HexPreview(file)
    return GenericPreview(file)
