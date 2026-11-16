"""Fast, asynchronous preview extraction engine with LRU memory caching and thread-safe QImage."""

import csv
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, Dict, Any, List
from PyQt6.QtCore import QThread, pyqtSignal, QObject
from PyQt6.QtGui import QImage
from PIL import Image

from src.config import FILE_CATEGORIES, format_size

MAX_CACHE_ENTRIES = 200
_PREVIEW_CACHE: Dict[str, "PreviewData"] = {}


class PreviewData:
    """Encapsulates extracted preview visuals and metadata."""

    def __init__(
        self,
        file_path: Path,
        preview_type: str,
        qimage: Optional[QImage] = None,
        text_content: Optional[str] = None,
        table_data: Optional[List[List[str]]] = None,
        archive_items: Optional[List[Dict[str, str]]] = None,
        extra_meta: Optional[Dict[str, str]] = None,
    ):
        self.file_path = file_path
        self.preview_type = preview_type  # 'image', 'pdf', 'word', 'table', 'text', 'archive', 'hex', 'audio', 'video', 'icon'
        self.qimage = qimage
        self.text_content = text_content
        self.table_data = table_data
        self.archive_items = archive_items
        self.extra_meta = extra_meta or {}


class AsyncPreviewWorker(QThread):
    """Background worker that extracts file previews using thread-safe memory buffers."""

    preview_ready = pyqtSignal(int, object)  # (request_id, PreviewData)

    def __init__(self, file_path: Path, request_id: int, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.file_path = file_path
        self.request_id = request_id
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            cache_key = f"{self.file_path}_{self.file_path.stat().st_mtime}"
            if cache_key in _PREVIEW_CACHE:
                self.preview_ready.emit(self.request_id, _PREVIEW_CACHE[cache_key])
                return

            if self._is_cancelled or not self.file_path.exists():
                return

            data = self._generate_preview()
            if data and not self._is_cancelled:
                if len(_PREVIEW_CACHE) >= MAX_CACHE_ENTRIES:
                    _PREVIEW_CACHE.pop(next(iter(_PREVIEW_CACHE)))
                _PREVIEW_CACHE[cache_key] = data
                self.preview_ready.emit(self.request_id, data)
        except Exception as e:
            empty_data = PreviewData(self.file_path, "error", text_content=f"Preview unavailable: {e}")
            self.preview_ready.emit(self.request_id, empty_data)

    def _generate_preview(self) -> PreviewData:
        ext = self.file_path.suffix.lower()

        if ext in FILE_CATEGORIES["images"]:
            return self._preview_image()
        if ext in FILE_CATEGORIES["pdf"]:
            return self._preview_pdf()
        if ext in FILE_CATEGORIES["word"]:
            return self._preview_word()
        if ext in FILE_CATEGORIES["excel"]:
            return self._preview_spreadsheet()
        if ext in FILE_CATEGORIES["powerpoint"]:
            return self._preview_powerpoint()
        if ext in FILE_CATEGORIES["archives"]:
            return self._preview_archive()
        if ext in FILE_CATEGORIES["code"] or ext in FILE_CATEGORIES["documents"]:
            return self._preview_text()
        if ext in FILE_CATEGORIES["audio"]:
            return self._preview_audio()
        if ext in FILE_CATEGORIES["video"]:
            return self._preview_video()
        if ext in FILE_CATEGORIES["binaries"]:
            return self._preview_hex_dump()

        return self._preview_hex_dump()

    def _preview_image(self) -> PreviewData:
        try:
            with Image.open(self.file_path) as img:
                w, h = img.size
                mode = img.mode
                fmt = img.format or "Image"

                img_copy = img.copy()
                img_copy.thumbnail((320, 240), Image.Resampling.LANCZOS)

                if img_copy.mode != "RGBA":
                    img_copy = img_copy.convert("RGBA")

                raw_data = img_copy.tobytes("raw", "RGBA")
                # QImage is completely thread-safe in worker threads
                qimage = QImage(
                    raw_data, img_copy.width, img_copy.height,
                    img_copy.width * 4, QImage.Format.Format_RGBA8888
                ).copy()  # detached copy

                return PreviewData(
                    self.file_path,
                    "image",
                    qimage=qimage,
                    extra_meta={
                        "Resolution": f"{w} × {h} px",
                        "Format": fmt,
                        "Color Mode": mode,
                        "Megapixels": f"{(w * h) / 1_000_000:.2f} MP",
                    },
                )
        except Exception:
            return PreviewData(self.file_path, "icon", extra_meta={"Format": "Image"})

    def _preview_pdf(self) -> PreviewData:
        try:
            import pymupdf
            doc = pymupdf.open(self.file_path)
            total_pages = len(doc)
            qimage = None
            if total_pages > 0:
                page = doc[0]
                pix = page.get_pixmap(dpi=110)
                qimage = QImage(
                    pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888
                ).copy()
            doc.close()

            return PreviewData(
                self.file_path,
                "pdf",
                qimage=qimage,
                extra_meta={"Total Pages": str(total_pages), "Format": "PDF Document"},
            )
        except Exception:
            return PreviewData(self.file_path, "icon", extra_meta={"Format": "PDF Document"})

    def _preview_word(self) -> PreviewData:
        ext = self.file_path.suffix.lower()
        if ext == ".docx":
            try:
                import docx
                doc = docx.Document(self.file_path)
                paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
                preview_text = "\n\n".join(paragraphs[:30])
                total_words = sum(len(p.split()) for p in paragraphs)

                return PreviewData(
                    self.file_path,
                    "word",
                    text_content=preview_text if preview_text else "[Empty Document]",
                    extra_meta={
                        "Format": "Microsoft Word Document",
                        "Paragraphs": str(len(paragraphs)),
                        "Estimated Words": f"~{total_words:,}",
                    },
                )
            except Exception:
                pass
        return PreviewData(self.file_path, "icon", extra_meta={"Format": "Word Document"})

    def _preview_spreadsheet(self) -> PreviewData:
        ext = self.file_path.suffix.lower()
        rows_data: List[List[str]] = []

        try:
            if ext in {".csv", ".tsv"}:
                delimiter = "\t" if ext == ".tsv" else ","
                with open(self.file_path, "r", encoding="utf-8", errors="ignore") as f:
                    reader = csv.reader(f, delimiter=delimiter)
                    for i, row in enumerate(reader):
                        if i >= 20:
                            break
                        rows_data.append(row[:8])
            elif ext == ".xlsx":
                import openpyxl
                wb = openpyxl.load_workbook(self.file_path, read_only=True, data_only=True)
                ws = wb.active
                if ws:
                    for i, row in enumerate(ws.iter_rows(values_only=True)):
                        if i >= 20:
                            break
                        rows_data.append([str(v) if v is not None else "" for v in row[:8]])
                wb.close()

            if rows_data:
                return PreviewData(
                    self.file_path,
                    "table",
                    table_data=rows_data,
                    extra_meta={"Format": "Spreadsheet", "Preview Rows": str(len(rows_data))},
                )
        except Exception:
            pass

        return PreviewData(self.file_path, "icon", extra_meta={"Format": "Spreadsheet"})

    def _preview_powerpoint(self) -> PreviewData:
        try:
            with zipfile.ZipFile(self.file_path, "r") as z:
                slides = [name for name in z.namelist() if name.startswith("ppt/slides/slide") and name.endswith(".xml")]
                return PreviewData(
                    self.file_path,
                    "icon",
                    extra_meta={
                        "Format": "PowerPoint Presentation",
                        "Total Slides": str(len(slides)),
                    },
                )
        except Exception:
            return PreviewData(self.file_path, "icon", extra_meta={"Format": "PowerPoint"})

    def _preview_archive(self) -> PreviewData:
        ext = self.file_path.suffix.lower()
        items: List[Dict[str, str]] = []
        try:
            if ext == ".zip":
                with zipfile.ZipFile(self.file_path, "r") as z:
                    infolist = z.infolist()
                    total_uncompressed = sum(info.file_size for info in infolist)
                    for info in infolist[:30]:
                        items.append({
                            "name": info.filename,
                            "size": format_size(info.file_size),
                            "is_dir": str(info.is_dir()),
                        })
                    return PreviewData(
                        self.file_path,
                        "archive",
                        archive_items=items,
                        extra_meta={
                            "Archive Type": "ZIP Archive",
                            "Total Files": f"{len(infolist):,}",
                            "Uncompressed Size": format_size(total_uncompressed),
                        },
                    )
        except Exception:
            pass
        return PreviewData(self.file_path, "icon", extra_meta={"Format": "Archive"})

    def _preview_text(self) -> PreviewData:
        try:
            with open(self.file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(8000)

            line_count = content.count("\n") + 1
            word_count = len(content.split())

            return PreviewData(
                self.file_path,
                "text",
                text_content=content,
                extra_meta={
                    "Lines": f"{line_count:,}",
                    "Words": f"{word_count:,}",
                    "Characters": f"{len(content):,}",
                },
            )
        except Exception:
            return PreviewData(self.file_path, "icon", extra_meta={"Format": "Text Document"})

    def _preview_audio(self) -> PreviewData:
        return PreviewData(
            self.file_path,
            "audio",
            extra_meta={
                "Format": self.file_path.suffix.upper()[1:] + " Audio",
                "File Size": format_size(self.file_path.stat().st_size),
            },
        )

    def _preview_video(self) -> PreviewData:
        return PreviewData(
            self.file_path,
            "video",
            extra_meta={
                "Format": self.file_path.suffix.upper()[1:] + " Video",
                "File Size": format_size(self.file_path.stat().st_size),
            },
        )

    def _preview_hex_dump(self) -> PreviewData:
        try:
            with open(self.file_path, "rb") as f:
                raw_bytes = f.read(192)

            lines = []
            for i in range(0, len(raw_bytes), 16):
                chunk = raw_bytes[i:i + 16]
                hex_part = " ".join(f"{b:02X}" for b in chunk)
                hex_part = f"{hex_part:<48}"
                ascii_part = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
                lines.append(f"{i:08X}: {hex_part} | {ascii_part}")

            return PreviewData(
                self.file_path,
                "hex",
                text_content="\n".join(lines),
                extra_meta={"Format": "Binary File", "View": "Hex Dump (first 192 bytes)"},
            )
        except Exception:
            return PreviewData(self.file_path, "icon", extra_meta={"Format": "Binary"})
