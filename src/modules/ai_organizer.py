"""AI-powered Smart File Organizer: automates cleaning and categorizing messy folders."""

import re
import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from PyQt6.QtCore import QThread, pyqtSignal, QObject

from src.config import FILE_CATEGORIES


FINANCE_KEYWORDS = {
    "invoice", "receipt", "bill", "payment", "bank", "statement", "tax", "payroll",
    "salary", "transaction", "gst", "order", "purchase", "crypto", "account"
}

ACADEMIC_KEYWORDS = {
    "paper", "thesis", "research", "journal", "assignment", "homework", "lecture",
    "syllabus", "exam", "quiz", "course", "algorithm", "chapter", "study"
}


class OrganizationPlanItem:
    """Represents a proposed file reorganization."""

    def __init__(self, source: Path, destination: Path, category: str, proposed_name: str, confidence: float):
        self.source = source
        self.destination = destination
        self.category = category
        self.proposed_name = proposed_name
        self.confidence = confidence
        self.enabled = True


def extract_quick_text(file_path: Path, max_chars: int = 1500) -> str:
    """Extract snippet of text from PDF or text-based files for classification."""
    ext = file_path.suffix.lower()
    text = ""
    try:
        if ext == ".pdf":
            import pymupdf
            doc = pymupdf.open(file_path)
            if len(doc) > 0:
                text = doc[0].get_text()[:max_chars]
            doc.close()
        elif ext in {".txt", ".md", ".csv", ".json", ".py", ".html", ".log"}:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read(max_chars)
    except Exception:
        pass
    return text.lower()


class AIOrganizerWorker(QThread):
    """Analyzes a folder and produces a structured reorganization plan with dry-run support."""

    progress_updated = pyqtSignal(int, str)
    plan_generated = pyqtSignal(list)  # List[OrganizationPlanItem]

    def __init__(self, target_folder: Path, organize_by_date: bool = False, rename_smart: bool = True, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.target_folder = target_folder
        self.organize_by_date = organize_by_date
        self.rename_smart = rename_smart
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        items: List[OrganizationPlanItem] = []
        try:
            files = [f for f in self.target_folder.iterdir() if f.is_file()]
            total = len(files)

            for i, f in enumerate(files):
                if self._is_cancelled:
                    return

                self.progress_updated.emit(
                    int((i / max(1, total)) * 100), f"Analyzing: {f.name}"
                )

                plan_item = self._analyze_file(f)
                if plan_item:
                    items.append(plan_item)

            self.progress_updated.emit(100, f"Analysis complete. Planned {len(items)} actions.")
            self.plan_generated.emit(items)
        except Exception as e:
            print(f"Error in AI Organizer analysis: {e}")
            self.plan_generated.emit([])

    def _analyze_file(self, file_path: Path) -> Optional[OrganizationPlanItem]:
        ext = file_path.suffix.lower()
        base_name = file_path.stem.lower()
        extracted_text = extract_quick_text(file_path)

        # Detect category
        category = "Other"
        subfolder = "Other"
        confidence = 0.70

        # Check Finance
        if any(kw in base_name for kw in FINANCE_KEYWORDS) or any(kw in extracted_text for kw in FINANCE_KEYWORDS):
            category = "Finance & Receipts"
            subfolder = "Documents/Finance"
            confidence = 0.95
        # Check Academic
        elif any(kw in base_name for kw in ACADEMIC_KEYWORDS) or any(kw in extracted_text for kw in ACADEMIC_KEYWORDS):
            category = "Academic & Research"
            subfolder = "Documents/Academic"
            confidence = 0.90
        # Extensions based classification
        elif ext in FILE_CATEGORIES["images"]:
            category = "Images"
            subfolder = "Media/Images"
            confidence = 0.99
        elif ext in FILE_CATEGORIES["video"]:
            category = "Videos"
            subfolder = "Media/Videos"
            confidence = 0.99
        elif ext in FILE_CATEGORIES["audio"]:
            category = "Audio"
            subfolder = "Media/Audio"
            confidence = 0.99
        elif ext in FILE_CATEGORIES["archives"]:
            category = "Archives & Packages"
            subfolder = "Archives"
            confidence = 0.99
        elif ext in FILE_CATEGORIES["code"]:
            category = "Code & Scripts"
            subfolder = "Development/Code"
            confidence = 0.95
        elif ext in FILE_CATEGORIES["documents"]:
            category = "Documents"
            subfolder = "Documents/General"
            confidence = 0.85
        elif ext in {".exe", ".msi"}:
            category = "Installers"
            subfolder = "Software_Installers"
            confidence = 0.95

        # Check if smart renaming should be suggested
        new_name = file_path.name
        if self.rename_smart:
            cleaned = self._suggest_clean_name(file_path, extracted_text)
            if cleaned:
                new_name = cleaned

        target_dir = self.target_folder / subfolder
        dest_path = target_dir / new_name

        return OrganizationPlanItem(
            source=file_path,
            destination=dest_path,
            category=category,
            proposed_name=new_name,
            confidence=confidence,
        )

    def _suggest_clean_name(self, file_path: Path, extracted_text: str) -> Optional[str]:
        """Generate cleaner, human-friendly names for cryptic downloads."""
        stem = file_path.stem
        ext = file_path.suffix

        # Remove duplicate download markers like 'download (1)' or 'IMG_0123 (2)'
        cleaned_stem = re.sub(r"\s*\(\d+\)$", "", stem)
        cleaned_stem = re.sub(r"[-_]+", " ", cleaned_stem).strip()

        # If it's a generic camera image name like IMG_20261111_1234
        if re.match(r"^(img|photo|dsc|screenshot)[\d_]+$", stem, re.IGNORECASE):
            try:
                mtime = file_path.stat().st_mtime
                date_str = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d_%H%M")
                return f"Photo_{date_str}{ext}"
            except OSError:
                pass

        # If it's an invoice or receipt, capitalize words
        if "invoice" in cleaned_stem or "invoice" in extracted_text:
            cleaned_title = " ".join(word.capitalize() for word in cleaned_stem.split())
            return f"{cleaned_title}{ext}"

        # Capitalize Title Case
        if len(cleaned_stem) > 3 and not cleaned_stem.isupper():
            title_stem = " ".join(word.capitalize() for word in cleaned_stem.split())
            return f"{title_stem}{ext}"

        return None
