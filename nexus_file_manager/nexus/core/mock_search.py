"""
Mock 'semantic' search for the Semantic Search dialog (UI-only).
HOOK: replace `search()` with the embedding/index backend; the dialog only needs the dict shape returned here.
Meaning is faked with a tiny synonym table so e.g. 'bill' also finds 'invoice' and 'electricity'.
"""
from __future__ import annotations

import re

CORPUS = [
    {"name": "Electricity Bill – Oct 2026.pdf", "path": "C:\\Users\\User\\Documents\\Finance", "kind": "pdf",
     "text": "Invoice for October. Total amount due 4,820 INR. Electricity consumption was 312 units. Payment is due before 18 November to avoid a late fee."},
    {"name": "Budget 2026.xlsx", "path": "C:\\Users\\User\\Documents\\Finance", "kind": "excel",
     "text": "Annual budget by quarter. Rent and groceries make up most expenses. Savings target is 20 percent of income. Review the budget every month."},
    {"name": "Thermodynamics Lecture Notes.docx", "path": "C:\\Users\\User\\Documents\\Semester 5", "kind": "word",
     "text": "Lecture 7 covers entropy and the second law. The exam will include Carnot cycle problems. Revise the derivation of efficiency before the midterm."},
    {"name": "Semester 5 Syllabus.pdf", "path": "C:\\Users\\User\\Documents\\Semester 5", "kind": "pdf",
     "text": "Course outline and exam schedule. The midterm is in week 8 and the final exam in week 16. Assignments are due every second Friday."},
    {"name": "Project Proposal Draft.docx", "path": "C:\\Users\\User\\Documents\\Projects", "kind": "word",
     "text": "Proposal for an offline file manager with duplicate detection and encryption. Milestones: prototype, user testing, final report. The deadline is 30 November."},
    {"name": "Studio Rental Contract.pdf", "path": "C:\\Users\\User\\Documents\\Legal", "kind": "pdf",
     "text": "Rental agreement for the studio. Monthly payment of 12,000 INR. Either party may terminate with 30 days notice. A security deposit is refundable."},
    {"name": "backup_scheduler.py", "path": "C:\\Users\\User\\Projects\\scripts", "kind": "code",
     "text": "Python script that schedules nightly backups. Reads the config, compresses folders and copies the archive to the external drive. Logs errors to a file."},
    {"name": "Meeting Notes.docx", "path": "C:\\Users\\User\\Documents", "kind": "word",
     "text": "Team meeting notes. Decided to ship the beta next week. Action items: finish the budget review, send the invoice to the client, book the studio."},
    {"name": "Goa Trip Itinerary.pdf", "path": "C:\\Users\\User\\Documents\\Travel", "kind": "pdf",
     "text": "Flights, hotel booking and a day-by-day plan. Payment confirmation attached. Check-in is on 12 December; travel insurance is included."},
]

SYNONYMS = {
    "bill": ["invoice", "electricity", "payment", "amount"], "money": ["budget", "payment", "expenses", "savings", "rent"],
    "exam": ["midterm", "syllabus", "lecture", "assignments"], "test": ["exam", "midterm"],
    "deadline": ["due", "milestones"], "contract": ["agreement", "rental", "terminate"],
    "backup": ["archive", "nightly", "copies"], "trip": ["flights", "hotel", "travel", "itinerary"],
    "rent": ["rental", "studio"], "study": ["lecture", "exam", "syllabus", "notes"],
}


def _terms(query: str) -> list[str]:
    return [w for w in re.findall(r"\w+", query.lower()) if len(w) > 2]


def search(query: str) -> list[dict]:
    terms = _terms(query)
    if not terms:
        return []
    results = []
    for doc in CORPUS:
        hay = f"{doc['name']} {doc['text']}".lower()
        matched: list[str] = []
        hits = 0
        for term in terms:
            variants = {term, *SYNONYMS.get(term, [])}
            found = [v for v in variants if v in hay]
            if found:
                matched.extend(found)
                hits += sum(hay.count(v) for v in found)
        if not matched:
            continue
        distinct = len({t for t in terms if {t, *SYNONYMS.get(t, [])} & set(matched)})
        relevance = min(98, 50 + hits * 7 + distinct * 8)
        text = doc["text"]
        first = min((text.lower().find(m) for m in matched if m in text.lower()), default=0)
        start = max(0, text.rfind(". ", 0, first) + 2 if text.rfind(". ", 0, first) >= 0 else 0)
        snippet = text[start:start + 150].strip()
        results.append({**doc, "relevance": relevance, "snippet": snippet, "terms": sorted(set(matched), key=len, reverse=True)})
    return sorted(results, key=lambda r: -r["relevance"])
