"""parse.py - Extract and clean page text from the coverage PDFs.

Reads every PDF in data/pdfs/, strips running headers/footers and Cigna's
legal disclaimer, and writes one JSON record per page to data/pages.jsonl.
"""
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import pymupdf

PDF_DIR = Path("data/pdfs")
OUT_PATH = Path("data/pages.jsonl")
MIN_CHARS = 50          # pages shorter than this after cleaning are skipped
EDGE_LINES = 5          # top/bottom zone size; headers and footers counted apart
REPEAT_SHARE = 0.6      # a zone line on >= 60% of pages counts as boilerplate
MIN_DOC_PAGES = 5       # shorter docs skip the rule: their criteria repeat too

# Lines frequency counting can't catch: short docs (< MIN_DOC_PAGES) or lines
# that appear once per document. Applied to every line of every document.
KNOWN_BOILERPLATE = [
    # Print button text saved with the Aetna web policies (first/last page only)
    re.compile(r"^print this page$", re.I),
    # UHC footer; sits under a 4-line header, and UHC Otezla is too short to count
    re.compile(r"^proprietary information of unitedhealthcare", re.I),
    # UHC copyright line on every page of the 4-page Otezla policy
    re.compile(r"^©\s*\d{4} unitedhealthcare", re.I),
    # Page counters, including on documents too short for frequency counting
    re.compile(r"^page \d+ of \d+$", re.I),
    # Aetna formulary footer; explicit so it goes even if it drifts out of the zone
    re.compile(r"^2026 pharmacy drug guide.*advanced control plan", re.I),
]

# Bare page numbers are removed only from the top/bottom zone, and only when
# they equal the page number (plus a per-document offset). FDA labels have no
# printed page numbers, but do have bare numbers: doses, table cells, steps.
BARE_NUMBER = re.compile(r"^\d{1,3}$")

DATE = r"(\d{1,2}/\d{1,2}/\d{4}|[A-Z][a-z]+ \d{1,2}, \d{4})"   # 9/1/2026, October 1, 2026

# "Effective 10/01/2026", "Effective Date ..... 9/1/2026", "Effective Date: October 1, 2026"
EFFECTIVE_DATE = re.compile(r"Effective(?:\s+Date)?[\s.:]*" + DATE)

# Any label that dates a version of the document; the latest match wins.
VERSION_LABELS = ["Effective", "Review Date", "Last Review", "Revised",
                  "Policy History", "P&T Approval Date"]
VERSION_DATE = re.compile(
    "(" + "|".join(label.replace(" ", r"\s+") for label in VERSION_LABELS) + ")"
    + r"(?:\s+Date)?[\s.:|]*" + DATE, re.I)
FDA_REVISED = re.compile(r"Revised:\s*(\d{1,2})/(\d{4})\b")   # "Revised: 10/2025"

DISCLAIMER_START = re.compile(r"INSTRUCTIONS FOR USE", re.IGNORECASE)
DISCLAIMER_END = re.compile(r"other\s+coverage\s+determinations\.", re.IGNORECASE)


def parse_filename(path):
    """Return (source, drug, doc_type, year) from 'cigna__repatha__2026.pdf'.

    `year` is the third name part: a year string, or "label" for FDA labels.
    """
    parts = path.stem.split("__")
    if len(parts) != 3:
        raise ValueError(f"Unexpected file name: {path.name}")
    source, drug, year = parts
    if source == "fda":
        doc_type = "label"
    elif drug == "formulary":
        doc_type = "formulary"
    else:
        doc_type = "policy"
    return source, drug, doc_type, year


def normalize(line):
    """Comparison key for a line: lowercase, numbers -> '#', single spaces."""
    line = re.sub(r"\d+", "#", line.lower())
    return re.sub(r"\s+", " ", line).strip()


def to_iso(date_text):
    """'9/1/2026' or 'October 1, 2026' -> '2026-09-01'; None if it isn't a real date."""
    for fmt in ("%m/%d/%Y", "%B %d, %Y"):
        try:
            return datetime.strptime(date_text, fmt).date().isoformat()
        except ValueError:
            pass
    return None


def find_effective_date(text):
    """First 'Effective (Date): <date>' in the document as YYYY-MM-DD, or None."""
    match = EFFECTIVE_DATE.search(text)
    return to_iso(match.group(1)) if match else None


def find_version_date(text, doc_type, year):
    """Most recent labelled date in the document -> (YYYY-MM-DD, source label).

    FDA labels also use their 'Revised: MM/YYYY' line. With no labelled date,
    falls back to the file name's year as (YYYY-01-01, "filename").
    """
    canonical = {label.lower(): label for label in VERSION_LABELS}
    found = []
    for match in VERSION_DATE.finditer(text):
        if date := to_iso(match.group(2)):
            found.append((date, canonical[re.sub(r"\s+", " ", match.group(1)).lower()]))
    if doc_type == "label":
        found += [(f"{y}-{int(m):02d}-01", "Revised") for m, y in FDA_REVISED.findall(text)]
    if found:
        return max(found)
    if year.isdigit():
        return f"{year}-01-01", "filename"
    return None, None


def page_number_offset(pages):
    """Constant (printed number - page index) shared by most pages, else 0.

    Handles PDFs whose printed numbering doesn't start at 1, e.g. an extract
    whose first page is printed as "20".
    """
    diffs = Counter()
    for page_num, lines in enumerate(pages, start=1):
        top, bottom = zones(lines)
        diffs.update({int(lines[i]) - page_num for i in top + bottom
                      if BARE_NUMBER.match(lines[i].strip())})
    if diffs:
        offset, n = diffs.most_common(1)[0]
        if n >= REPEAT_SHARE * len(pages):
            return offset
    return 0


def zones(lines):
    """Index lists for one page: top zone (top down) and bottom zone (bottom up)."""
    n = len(lines)
    return list(range(min(EDGE_LINES, n))), list(reversed(range(max(0, n - EDGE_LINES), n)))


def find_running_lines(pages):
    """Return (header keys, footer keys): zone lines repeated on most pages."""
    if len(pages) < MIN_DOC_PAGES:
        return set(), set()
    tops, bottoms = Counter(), Counter()
    for lines in pages:
        top, bottom = zones(lines)
        tops.update({normalize(lines[i]) for i in top})
        bottoms.update({normalize(lines[i]) for i in bottom})
    needed = REPEAT_SHARE * len(pages)
    return ({k for k, n in tops.items() if n >= needed},
            {k for k, n in bottoms.items() if n >= needed})


def remove_boilerplate(pages):
    """Strip running headers/footers, page numbers and KNOWN_BOILERPLATE lines.

    `pages` is a list of pages, each a list of non-empty lines. A header is
    removed only from the top zone and a footer only from the bottom zone,
    at most once per page. Returns the cleaned pages plus a Counter of
    (reason, normalized line) -> times removed.
    """
    headers, footers = find_running_lines(pages)
    offset = page_number_offset(pages)
    removed, cleaned = Counter(), []
    for page_num, lines in enumerate(pages, start=1):
        top, bottom = zones(lines)
        drop = {}                                    # line index -> (reason, key)
        for zone, keys, reason in ((top, headers, "header"), (bottom, footers, "footer")):
            seen = set()
            for i in zone:
                key = normalize(lines[i])
                if key in keys and key not in seen and i not in drop:
                    drop[i] = (reason, key)
                    seen.add(key)
        for i in top + bottom:
            line = lines[i].strip()
            if (i not in drop and BARE_NUMBER.match(line)
                    and int(line) in (page_num, page_num + offset)):
                drop[i] = ("pageno", line)
        for i, line in enumerate(lines):
            if i not in drop and any(p.search(line.strip()) for p in KNOWN_BOILERPLATE):
                drop[i] = ("known", normalize(line))
        removed.update(drop.values())
        cleaned.append([line for i, line in enumerate(lines) if i not in drop])
    return cleaned, removed


def remove_disclaimer(texts):
    """Cut Cigna's 'INSTRUCTIONS FOR USE' block, which may spill onto the next page.

    Safety net: if the end phrase is not found by the following page, that
    page is kept untouched instead of deleting the rest of the document.
    """
    out, inside = [], False
    for text in texts:
        kept = text
        if inside:                         # continuation page
            end = DISCLAIMER_END.search(text)
            kept = text[end.end():] if end else text
            if not end:
                print("WARNING: disclaimer end not found; kept the page as-is")
            inside = False
        elif start := DISCLAIMER_START.search(text):
            end = DISCLAIMER_END.search(text, start.end())
            kept = text[:start.start()] + (text[end.end():] if end else "")
            inside = end is None
        out.append(kept)
    return out


def clean_text(text):
    """Fix stray glyphs and collapse extra spaces and blank lines."""
    text = text.replace("�", " ")                # unmappable glyph from PDF fonts
    text = re.sub(r"^([•o▪])\s*\n", r"\1 ", text, flags=re.M)  # join lone bullets
    text = re.sub(r"[ \t\xa0]+", " ", text)           # runs of spaces -> one space
    text = "\n".join(line.strip() for line in text.splitlines())
    text = re.sub(r"\n{3,}", "\n\n", text)            # 3+ newlines -> one blank line
    return text.strip()


def parse_pdf(path):
    """Return (page records, skipped count, removed boilerplate) for one PDF."""
    source, drug, doc_type, year = parse_filename(path)
    with pymupdf.open(path) as doc:
        raw_pages = [page.get_text("text") for page in doc]

    raw_text = "\n".join(raw_pages)                  # dates are read before stripping
    effective_date = find_effective_date(raw_text)
    version_date, version_source = find_version_date(raw_text, doc_type, year)
    pages = [[l for l in text.splitlines() if l.strip()] for text in raw_pages]
    pages, removed = remove_boilerplate(pages)
    texts = ["\n".join(lines) for lines in pages]
    if source == "cigna":                 # FDA labels have a real "Instructions for Use"
        texts = remove_disclaimer(texts)

    records, skipped = [], 0
    for page_num, text in enumerate(texts, start=1):
        text = clean_text(text)
        if len(text) < MIN_CHARS:
            print(f"WARNING: skipping {path.name} page {page_num} ({len(text)} chars)")
            skipped += 1
            continue
        records.append({"source": source, "drug": drug, "doc_type": doc_type,
                        "effective_date": effective_date, "version_date": version_date,
                        "version_date_source": version_source,
                        "file": path.name, "page": page_num,
                        "text": text, "char_count": len(text)})
    return records, skipped, removed


def print_summary(rows):
    """Print per-file counts and totals by doc_type."""
    print(f"\n{'file':<30} {'type':<10} {'kept':>5} {'skip':>5} {'chars':>9}")
    print("-" * 63)
    totals = defaultdict(lambda: [0, 0, 0])
    for name, doc_type, kept, skipped, chars in rows:
        print(f"{name:<30} {doc_type:<10} {kept:>5} {skipped:>5} {chars:>9,}")
        for i, value in enumerate((kept, skipped, chars)):
            totals[doc_type][i] += value
    print("-" * 63)
    for doc_type, (kept, skipped, chars) in sorted(totals.items()):
        print(f"{'TOTAL ' + doc_type:<41} {kept:>5} {skipped:>5} {chars:>9,}")


def print_removed(removed_by_file):
    """List the boilerplate lines removed from each file, for manual review."""
    print("\nRemoved as boilerplate (times removed, reason, normalized line):")
    for name, removed in removed_by_file.items():
        print(f"\n{name}")
        if not removed:
            print("  (none)")
        for (reason, line), n in sorted(removed.items()):
            print(f"  {n:>3}x  {reason:<6}  {line}")


def main():
    """Parse every PDF and write data/pages.jsonl."""
    rows, removed_by_file = [], {}
    with OUT_PATH.open("w", encoding="utf-8") as out:
        for path in sorted(PDF_DIR.glob("*.pdf")):
            records, skipped, removed = parse_pdf(path)
            for record in records:
                out.write(json.dumps(record, ensure_ascii=False) + "\n")
            chars = sum(r["char_count"] for r in records)
            rows.append((path.name, parse_filename(path)[2], len(records), skipped, chars))
            removed_by_file[path.name] = removed
    print_summary(rows)
    print_removed(removed_by_file)
    print(f"\nWrote {sum(r[2] for r in rows)} pages to {OUT_PATH}")


if __name__ == "__main__":
    main()
