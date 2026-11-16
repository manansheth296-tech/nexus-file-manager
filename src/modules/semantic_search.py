"""Content & Semantic Search Engine: searches document contents (PDF, Code, Text, Markdown) using TF-IDF."""

import math
import os
import re
from pathlib import Path
from collections import Counter, defaultdict
from typing import List, Dict, Tuple, Optional
from PyQt6.QtCore import QThread, pyqtSignal, QObject


class SearchResult:
    """Represents a matched document with relevance score and text snippet."""

    def __init__(self, file_path: Path, score: float, snippet: str, match_count: int):
        self.file_path = file_path
        self.score = score
        self.snippet = snippet
        self.match_count = match_count


def tokenize(text: str) -> List[str]:
    """Tokenize and normalize text into clean words."""
    return re.findall(r"\b[a-zA-Z0-9_]{2,}\b", text.lower())


class ContentSearchWorker(QThread):
    """Background worker that indexes and performs TF-IDF search across documents in a directory."""

    progress_updated = pyqtSignal(int, str)
    search_completed = pyqtSignal(list)  # List[SearchResult]

    def __init__(self, directory: Path, query: str, max_depth: int = 3, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.directory = directory
        self.query = query
        self.max_depth = max_depth
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            query_tokens = tokenize(self.query)
            if not query_tokens:
                self.search_completed.emit([])
                return

            self.progress_updated.emit(10, "Discovering searchable documents...")
            searchable_exts = {
                ".txt", ".md", ".py", ".js", ".ts", ".html", ".css", ".json",
                ".pdf", ".csv", ".yaml", ".yml", ".c", ".cpp", ".java", ".rs"
            }

            candidate_files: List[Path] = []
            for root, _, files in os.walk(self.directory):
                if self._is_cancelled:
                    return
                # Check depth
                rel_parts = Path(root).relative_to(self.directory).parts
                if len(rel_parts) > self.max_depth:
                    continue
                for f in files:
                    p = Path(root) / f
                    if p.suffix.lower() in searchable_exts:
                        candidate_files.append(p)

            total_docs = len(candidate_files)
            if total_docs == 0:
                self.search_completed.emit([])
                return

            self.progress_updated.emit(25, f"Indexing {total_docs} files for query '{self.query}'...")

            doc_tokens: Dict[Path, List[str]] = {}
            doc_raw_text: Dict[Path, str] = {}
            df: Dict[str, int] = defaultdict(int)

            for i, p in enumerate(candidate_files):
                if self._is_cancelled:
                    return
                raw_text = self._extract_text(p)
                if raw_text:
                    tokens = tokenize(raw_text)
                    if tokens:
                        doc_tokens[p] = tokens
                        doc_raw_text[p] = raw_text
                        unique_tokens = set(tokens)
                        for t in unique_tokens:
                            if t in query_tokens:
                                df[t] += 1

                if i % 15 == 0:
                    pct = 25 + int((i / total_docs) * 50)
                    self.progress_updated.emit(pct, f"Indexing: {p.name}")

            # Calculate TF-IDF scoring for each document
            self.progress_updated.emit(80, "Scoring and ranking documents...")
            results: List[SearchResult] = []

            for p, tokens in doc_tokens.items():
                if self._is_cancelled:
                    return
                doc_len = len(tokens)
                tf = Counter(tokens)
                score = 0.0
                matches = 0

                for qt in query_tokens:
                    if qt in tf:
                        matches += tf[qt]
                        # Term frequency normalized by doc length
                        tf_val = tf[qt] / doc_len
                        # Inverse document frequency
                        idf = math.log((total_docs + 1) / (df[qt] + 1)) + 1.0
                        score += tf_val * idf

                # Filename bonus
                p_name_lower = p.name.lower()
                for qt in query_tokens:
                    if qt in p_name_lower:
                        score += 0.5
                        matches += 1

                if matches > 0:
                    snippet = self._generate_snippet(doc_raw_text[p], query_tokens)
                    results.append(SearchResult(p, score, snippet, matches))

            # Sort by score descending
            results.sort(key=lambda r: r.score, reverse=True)
            self.progress_updated.emit(100, f"Found {len(results)} matching documents.")
            self.search_completed.emit(results)
        except Exception as e:
            print(f"Error in ContentSearchWorker: {e}")
            self.search_completed.emit([])

    def _extract_text(self, path: Path, max_bytes: int = 500_000) -> str:
        ext = path.suffix.lower()
        try:
            if ext == ".pdf":
                import pymupdf
                doc = pymupdf.open(path)
                text_parts = []
                for page in doc[:10]:  # Index up to first 10 pages for speed
                    text_parts.append(page.get_text())
                doc.close()
                return "\n".join(text_parts)
            else:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    return f.read(max_bytes)
        except Exception:
            return ""

    def _generate_snippet(self, full_text: str, query_tokens: List[str], window: int = 120) -> str:
        """Find the occurrence of query words and return an excerpt with surrounding context."""
        lower_text = full_text.lower()
        first_idx = -1
        for qt in query_tokens:
            pos = lower_text.find(qt)
            if pos != -1 and (first_idx == -1 or pos < first_idx):
                first_idx = pos

        if first_idx == -1:
            return full_text[:window * 2].replace("\n", " ").strip() + "..."

        start = max(0, first_idx - window // 2)
        end = min(len(full_text), first_idx + window)
        snippet = full_text[start:end].replace("\n", " ").strip()

        prefix = "..." if start > 0 else ""
        suffix = "..." if end < len(full_text) else ""
        return f"{prefix}{snippet}{suffix}"
