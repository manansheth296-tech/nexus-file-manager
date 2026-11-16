"""Unit tests for the new high-speed multi-format preview loader."""

import os
import sys
import unittest
import tempfile
import shutil
import zipfile
from pathlib import Path
from PIL import Image

# Ensure offscreen Qt
os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PyQt6.QtWidgets import QApplication

from src.modules.preview_loader import AsyncPreviewWorker, PreviewData


class TestPreviewLoader(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication(sys.argv)

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="preview_test_"))

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_text_preview(self):
        txt_file = self.test_dir / "sample.txt"
        txt_file.write_text("Hello World from Nexus File Manager!\nLine 2", encoding="utf-8")

        worker = AsyncPreviewWorker(txt_file, request_id=1)
        data = worker._generate_preview()

        self.assertEqual(data.preview_type, "text")
        self.assertIn("Hello World", data.text_content)
        self.assertEqual(data.extra_meta["Lines"], "2")

    def test_image_preview(self):
        img_file = self.test_dir / "sample.png"
        img = Image.new("RGBA", (100, 80), color="#FF0000")
        img.save(img_file)

        worker = AsyncPreviewWorker(img_file, request_id=2)
        data = worker._generate_preview()

        self.assertEqual(data.preview_type, "image")
        self.assertIsNotNone(data.qimage)
        self.assertIn("100 × 80", data.extra_meta["Resolution"])

    def test_hex_dump_preview(self):
        bin_file = self.test_dir / "sample.bin"
        bin_file.write_bytes(b"\x7fELF\x02\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00")

        worker = AsyncPreviewWorker(bin_file, request_id=3)
        data = worker._generate_preview()

        self.assertEqual(data.preview_type, "hex")
        self.assertIn("7F 45 4C 46", data.text_content)
        self.assertIn("ELF", data.text_content)

    def test_zip_archive_preview(self):
        zip_path = self.test_dir / "bundle.zip"
        with zipfile.ZipFile(zip_path, "w") as z:
            z.writestr("inner_document.txt", "Compressed content")
            z.writestr("subfolder/data.json", '{"key": "value"}')

        worker = AsyncPreviewWorker(zip_path, request_id=4)
        data = worker._generate_preview()

        self.assertEqual(data.preview_type, "archive")
        self.assertEqual(len(data.archive_items), 2)
        self.assertEqual(data.extra_meta["Total Files"], "2")


if __name__ == "__main__":
    unittest.main()
