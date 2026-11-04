"""chunk.py - Split the parsed pages into retrieval chunks.

Reads data/pages.jsonl (from parse.py) and writes one JSON chunk per line.
  --strategy section (default): section-aware policies, fixed-size labels and
      rebuilt formulary rows -> data/chunks.jsonl
  --strategy fixed: every document fixed-size, no section logic (baseline)
      -> data/chunks_fixed.jsonl
"""
import argparse
import json
import math
import re
from collections import defaultdict
from pathlib import Path
from statistics import median

import pymupdf

PAGES_PATH = Path("data/pages.jsonl")
PDF_DIR = Path("data/pdfs")
OUT_PATHS = {"section": Path("data/chunks.jsonl"), "fixed": Path("data/chunks_fixed.jsonl")}

TARGET_TOKENS = 500     # aim for chunks about this size
MAX_TOKENS = 800        # hard ceiling, context line included
MIN_TOKENS = 80         # smaller policy sections merge into the next one
OVERLAP_TOKENS = 80     # repeated between consecutive pieces of one split
CONTEXT_TOKENS = 50     # room reserved for the "[Source | Drug | ...]" line
MAX_FORMULARY_ROWS = 6  # table rows per formulary chunk

SOURCE_NAMES = {"aetna": "Aetna", "cigna": "Cigna", "uhc": "UHC", "fda": "FDA"}

# --- Policy headings -------------------------------------------------------
# "A. Patient has ..." / "1. The member has ..." are criteria, not headings.
NOT_CRITERION = r"(?!(?i:(?:the\s+)?(?:patient|member)s?\b))"

# (level, pattern), checked in order. A heading clears every heading at its
# level or deeper, so levels build the section path.
HEADING_PATTERNS = [
    # Upper-case Roman numeral: "II. CRITERIA FOR INITIAL APPROVAL"
    (1, re.compile(r"^[IVX]+\.\s+[A-Z]")),
    # Whole line in capitals with a real word: "POLICY STATEMENT" (not "RA, UC")
    (1, re.compile(r"^(?=.*[A-Z]{4})[A-Z][A-Z0-9 ,&/()\-–:]{5,60}$")),
    # Standard section names on a line of their own: "Background", "References"
    (1, re.compile(r"^(?:Background|References|Policy History|Coverage Rationale"
                   r"|Dosing Information|Appendix)$")),
    # Known sub-headings, with or without a marker: "1. Initial Authorization",
    # "A) Initial Therapy". Case-sensitive, so prose ("unproven because") is skipped.
    (4, re.compile(r"^(?:[A-Z0-9]{1,2}[.)]\s+)?(?:Initial (?:Authorization|Approval|Therapy)"
                   r"|Reauthorization|Continuation of Therapy"
                   r"|Patient is Currently Receiving)\b")),
    # "Unproven" lists conditions, so it sits beside them, not under the last one
    (2, re.compile(r"^Unproven$")),
    # Capital letter + condition name: "A. Psoriatic Arthritis (PsA)"
    (2, re.compile(r"^[A-Z][.)]\s+" + NOT_CRITERION + r"[A-Z]")),
    # Number + two Title Case words, or one word and a colon:
    # "2. Heterozygous Familial ...", "1. Background:" (not "1. Dactylitis")
    (3, re.compile(r"^\d{1,2}\.\s+" + NOT_CRITERION + r"[A-Z][\w’'-]*(?:\s+[A-Z(]|:)")),
]

# Never a heading: lines that are only AND / OR (Cigna puts them between
# criteria), lines that end the way a criterion does ("...; AND", "...,"),
# and reference-list entries ("Menter A, Gelfand JM, et al").
NOT_HEADING = re.compile(r"^\(?(?:and|or)\)?[\s.,;:]*$|(?:\b(?:and|or)|[;,])\s*$", re.I)
AUTHOR_LIST = re.compile(r"\b[A-Z][\w'’-]+ [A-Z]{1,3}[,.]|\bet al\b")
GENERIC_IN_PARENS = re.compile(r"\([a-z][a-z\- ]+\)")     # "REPATHA (evolocumab)"

# Headings are tested on a line's opening phrase, so Cigna's
# "1. Behcet's Disease. Approve for the duration..." is read as "1. Behcet's Disease".
LEAD_PHRASE_END = re.compile(r"(?<=[a-z)])\.\*?\s+(?=[A-Z])")
# UHC names each condition in a sentence, not a heading: "Denosumab is proven
# for the treatment of postmenopausal patients with osteoporosis at high risk..."
PROVEN_FOR = re.compile(r"^\w+ is proven (?:and medically necessary )?(?:for|to) "
                        r"(?:the treatment of |treat )?(.+)")

# Safe places to cut inside a long policy section: before a new list item.
# Lower rank = shallower item = better place to cut.
BREAK_RANKS = [
    (1, re.compile(r"^(?:[IVX]+|[A-Z])[.)]\s")),                      # II.  A.  B)
    (2, re.compile(r"^(?:\d{1,2}|[ivx]+)[.)]\s")),                    # 1.  iii.
    (3, re.compile(r"^(?:[a-z][.)]|\(\d{1,2}\)|\([a-z]\)|[•o▪])(?:\s|$)")),  # a)  (1)  (a)  •
]
LONE_MARKER = re.compile(r"^\(?\w{1,4}[.)]$")             # "(1)" alone; its text is on the next line

# --- FDA labels: "1 INDICATIONS AND USAGE", "5.1 Hypersensitivity Reactions" -
LABEL_HEADING = re.compile(r"^(1[0-7]|[1-9])(\.\d{1,2})?\s+([A-Z].*)$")

# --- Formulary ---------------------------------------------------------------
OUR_GENERICS = {"evolocumab": "repatha", "denosumab": "prolia", "apremilast": "otezla"}
KEEP_CLASS = re.compile(r"PCSK9", re.I)
GROUP_NAMES = {"repatha": "PCSK9 inhibitors", "prolia": "Denosumab products",
               "otezla": "Immunology agents"}   # for groups whose class header isn't in the extract
LEGEND_ENTRY = re.compile(r"^([A-Z][A-Za-z0-9 ]{0,12}?)\s*=\s*(.+?)(?=^[A-Z][A-Za-z0-9 ]{0,12}?\s*=|\Z)",
                          re.M | re.S)


def tokens(text):
    """Rough token estimate: about 4 characters per token for English text."""
    return len(text) // 4


def join(lines):
    """Text of a list of (page, text, ...) lines."""
    return "\n".join(line[1] for line in lines)


def path_text(path):
    """{1: 'POLICY STATEMENT', 4: 'Initial Therapy'} -> 'POLICY STATEMENT > Initial Therapy'."""
    return " > ".join(path[level] for level in sorted(path))


# --- Splitting -----------------------------------------------------------------

def split_lines(lines, break_rank, name):
    """Cut lines into pieces of ~TARGET_TOKENS, never over the MAX_TOKENS budget.

    `break_rank(lines, i)` says how good it is to cut before lines[i] (lower is
    better, None means never). Among cuts that leave a reasonably sized piece,
    the shallowest wins, then the one closest to TARGET_TOKENS. Each piece
    after the first starts with about OVERLAP_TOKENS of the previous piece,
    beginning at a safe line.
    """
    limit = MAX_TOKENS - CONTEXT_TOKENS
    total = (len(join(lines)) + 1) / 4
    pieces, start, last_cut = [], 0, 0
    while True:
        end, size, options = start, 0.0, []
        while end < len(lines) and size + (len(lines[end][1]) + 1) / 4 <= limit:
            size += (len(lines[end][1]) + 1) / 4
            end += 1
            done = (len(join(lines[:end])) + 1) / 4  # tokens before this cut
            if end > last_cut and end < len(lines) and \
                    (rank := break_rank(lines, end)) is not None:
                options.append((size >= TARGET_TOKENS / 2 and total - done >= MIN_TOKENS,
                                rank, abs(size - TARGET_TOKENS), end))
        if end == len(lines):                        # the rest fits in one piece
            pieces.append(lines[start:])
            return pieces
        if options:
            # prefer cuts leaving both sides a decent size, then shallow, then near target
            cut = min(options, key=lambda o: (not o[0], o[1], o[2]))[3]
        else:
            cut = max(end, last_cut + 1)
            print(f"WARNING: {name}: no safe break near page {lines[end][0]}; cut at a line")
        pieces.append(lines[start:cut])
        last_cut = cut
        start = overlap_start(lines, start, cut, break_rank)


def overlap_start(lines, start, cut, break_rank):
    """Where the next piece begins: the earliest safe line within OVERLAP_TOKENS of the cut."""
    for i in range(start + 1, cut):
        if break_rank(lines, i) is not None and tokens(join(lines[i:cut])) <= OVERLAP_TOKENS:
            return i
    return cut


def any_break(lines, i):
    """Fixed-size chunking: any line boundary is an acceptable cut."""
    return 1


def policy_break_rank(lines, i):
    """Rank of cutting a policy section before lines[i]; None if it would split a criterion."""
    text, prev = lines[i][1], lines[i - 1][1].strip()
    if text.lower().startswith("note:") or LONE_MARKER.match(prev) or NOT_HEADING.match(text):
        return None                                  # notes and AND/OR stay with their criterion
    for rank, pattern in BREAK_RANKS:
        if pattern.match(text):
            return rank
    if re.search(r"(?:[.;:]|\b(?:AND|OR))$", prev) and text[:1].isupper():
        return 4                                     # a new sentence
    return None


# --- Policies ------------------------------------------------------------------

def detect_heading(text):
    """Return (level, title) if a policy line is a section heading, else None."""
    if proven := PROVEN_FOR.match(text):
        condition = proven.group(1)
        if len(condition) > 60:
            condition = condition[:60].rsplit(" ", 1)[0]
        return 2, condition[:1].upper() + condition[1:]
    lead = LEAD_PHRASE_END.split(text, maxsplit=1)[0]
    if len(lead) > 90 or NOT_HEADING.search(lead) or AUTHOR_LIST.search(lead):
        return None
    if lead != text and re.match(r"^\d{1,2}\.\s+[A-Z][\w’'-]+$", lead):
        return 3, lead.split(maxsplit=1)[1]          # "4. Hypercholesterolemia.* Approve for..."
    if len(lead.split()) < 4 and GENERIC_IN_PARENS.search(lead) \
            and GENERIC_IN_PARENS.sub("", lead).isupper():
        return None                                  # a drug-name line, not a section
    for level, pattern in HEADING_PATTERNS:
        if pattern.match(lead):
            title = re.sub(r"^(?:[IVX]+|[A-Z]|\d{1,2})[.)]\s+", "", lead)
            title = re.split(r"\.\*?\s|:\s|\*\s", title)[0].strip(" .:*")
            return (level, title) if title else None
    return None


def merge_small(sections):
    """Merge sections under MIN_TOKENS into the next one (the last one into the previous)."""
    merged, carry = [], []
    for section, lines in sections:
        lines = carry + lines
        carry = []
        if tokens(join(lines)) < MIN_TOKENS:
            carry = lines
        else:
            merged.append((section, lines))
    if carry and merged:
        merged[-1] = (merged[-1][0], merged[-1][1] + carry)
    elif carry:
        merged.append((sections[-1][0], carry))
    return merged


def chunk_policy(lines, name, headings):
    """Section-aware pieces for one policy: split at headings, merge small, split large."""
    sections, path, current = [], {}, []
    for line in lines:
        if found := detect_heading(line[1]):
            headings.append((found[0], found[1], line[0]))
            if current:
                sections.append((path_text(path) or "Document start", current))
            path = {level: t for level, t in path.items() if level < found[0]}
            path[found[0]] = found[1]
            current = []
        current.append(line)
    if current:
        sections.append((path_text(path) or "Document start", current))

    return [(section, piece, None)
            for section, sec_lines in merge_small(sections)
            for piece in split_lines(sec_lines, policy_break_rank, name)]


# --- FDA labels ----------------------------------------------------------------

def chunk_label(lines, name):
    """Fixed-size pieces; each piece's section is the label heading in effect where it starts."""
    path, tagged = {}, []
    for page, text in lines:
        match = LABEL_HEADING.match(text)
        if match and len(text) <= 80 and (match.group(2) or match.group(3).isupper()):
            level = 2 if match.group(2) else 1
            path = {lvl: t for lvl, t in path.items() if lvl < level}
            path[level] = text
        tagged.append((page, text, path_text(path)))
    return [(piece[0][2] or None, piece, None) for piece in split_lines(tagged, any_break, name)]


# --- Formulary -----------------------------------------------------------------

def formulary_legend(text):
    """Code -> meaning from the legend page, e.g. {'QL': 'Quantity Limit'}."""
    block = text.split("Prescription Drug Name")[0]
    block = re.sub(r"Drug Tier|Coverage Requirements and\s+Limits", "", block)
    return {code.strip(): re.split(r":|\. ", " ".join(meaning.split()))[0].strip(" .")
            for code, meaning in LEGEND_ENTRY.findall(block)}


def formulary_groups(doc):
    """Table rows grouped under their class-header row.

    find_tables() gives the row/column structure; get_textbox() on each cell's
    rectangle gives its text with spaces intact (the table's own cell text
    runs words together). A page's rows before its first class header form
    an unnamed group: the extract skips pages, so their header isn't in it.
    """
    groups = []
    for page in doc:
        current = None
        for table in page.find_tables().tables:
            for row in table.rows:
                drug, tier, reqs = (" ".join(page.get_textbox(c).split()) if c else ""
                                    for c in row.cells)
                if drug == "Prescription Drug Name":
                    continue
                if current is None or not (tier or reqs):
                    current = {"page": page.number + 1, "name": None, "rows": []}
                    groups.append(current)
                if tier or reqs:
                    current["rows"].append((drug, tier, reqs))
                else:
                    current["name"] = drug           # class header row
    return [g for g in groups if g["rows"]]


def expand_codes(reqs, legend):
    """'PA; QL (3 PENS per 28 days)' -> 'PA (Prior Authorization); QL (Quantity Limit) 3 PENS per 28 days'."""
    parts = []
    for part in filter(None, (p.strip() for p in reqs.split(";"))):
        code, _, detail = part.partition(" ")
        detail = detail.strip().removeprefix("(").removesuffix(")")
        meaning = f" ({legend[code]})" if code in legend else ""
        parts.append(code + meaning + (f" {detail}" if detail else ""))
    return "; ".join(parts)


def chunk_formulary(meta):
    """One sentence per table row, only our drug classes, 3-6 related rows per piece."""
    with pymupdf.open(PDF_DIR / meta["file"]) as doc:
        legend = formulary_legend(doc[1].get_text())
        plan = re.search(r"(\w[\w ]*? Plan)\s*-", doc[0].get_text())
        groups = formulary_groups(doc)
    title = " ".join(filter(None, [SOURCE_NAMES[meta["source"]], meta["version_date"][:4],
                                   plan.group(1) if plan else None, "formulary"]))
    pieces = []
    for group in groups:
        contents = " ".join([group["name"] or ""] + [row[0] for row in group["rows"]]).lower()
        drug = next((d for g, d in OUR_GENERICS.items() if g in contents), None)
        if not drug and not KEEP_CLASS.search(group["name"] or ""):
            continue
        sentences = [(group["page"],
                      f"{title}: {name}. Tier: {tier}"
                      + (f" ({legend[tier]})" if tier in legend else "")
                      + f". Requirements: {expand_codes(reqs, legend) or 'none listed'}.")
                     for name, tier, reqs in group["rows"]]
        n_chunks = math.ceil(len(sentences) / MAX_FORMULARY_ROWS)
        size = math.ceil(len(sentences) / n_chunks)  # balanced: 12 rows -> 6 + 6
        section = group["name"] or GROUP_NAMES.get(drug, "Unnamed drug class")
        pieces += [(section, sentences[i:i + size], drug) for i in range(0, len(sentences), size)]
    return pieces


# --- Assembly ------------------------------------------------------------------

def make_chunk(meta, number, section, lines, drug):
    """Build one chunk record, prefixing a context line so it reads on its own."""
    drug = drug or meta["drug"]
    text_raw = join(lines)
    leaf = " > ".join(section.split(" > ")[-2:]) if section else ""
    if len(leaf) > 120:
        leaf = leaf[:119] + "…"
    fields = [SOURCE_NAMES[meta["source"]], drug.capitalize(), meta["doc_type"],
              meta["version_date"]] + ([leaf] if leaf else [])
    text = "[" + " | ".join(fields) + "]\n" + text_raw
    return {"chunk_id": f"{Path(meta['file']).stem}#{number:03d}",
            "source": meta["source"], "drug": drug, "doc_type": meta["doc_type"],
            "file": meta["file"], "page_start": lines[0][0], "page_end": lines[-1][0],
            "section": section, "version_date": meta["version_date"],
            "version_date_source": meta["version_date_source"],
            "text": text, "text_raw": text_raw, "n_tokens": tokens(text)}


def chunk_document(pages, strategy, headings):
    """All chunks for one document (its pages from pages.jsonl, in order)."""
    meta, name = pages[0], pages[0]["file"]
    lines = [(p["page"], line) for p in pages for line in p["text"].splitlines() if line.strip()]
    if strategy == "fixed":
        pieces = [(None, piece, None) for piece in split_lines(lines, any_break, name)]
    elif meta["doc_type"] == "policy":
        pieces = chunk_policy(lines, name, headings)
    elif meta["doc_type"] == "label":
        pieces = chunk_label(lines, name)
    else:
        pieces = chunk_formulary(meta)
    return [make_chunk(meta, n, section, piece, drug)
            for n, (section, piece, drug) in enumerate(pieces, start=1)]


def print_stats(chunks):
    """Per file and per doc_type: chunk count, min/median/max tokens, multi-page chunks."""
    by_file, by_type = defaultdict(list), defaultdict(list)
    for c in chunks:
        by_file[c["file"]].append(c)
        by_type["TOTAL " + c["doc_type"]].append(c)
    print(f"\n{'file':<30} {'chunks':>6} {'min':>5} {'median':>6} {'max':>5} {'multi-page':>10}")
    for groups in (by_file, dict(sorted(by_type.items()))):
        print("-" * 67)
        for name, group in groups.items():
            sizes = [c["n_tokens"] for c in group]
            multi = sum(c["page_end"] > c["page_start"] for c in group)
            print(f"{name:<30} {len(group):>6} {min(sizes):>5} {median(sizes):>6.0f} "
                  f"{max(sizes):>5} {multi:>10}")


def print_headings(headings_by_file):
    """Detected policy headings (level, page, title), for spotting misfires."""
    print("\nDetected policy headings (level, page, title):")
    for name, headings in headings_by_file.items():
        print(f"\n{name} ({len(headings)})")
        for level, title, page in headings:
            print(f"  L{level} p{page:<3} {'  ' * (level - 1)}{title}")


def main():
    """Chunk every document with the chosen strategy and write the JSONL file."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--strategy", choices=OUT_PATHS, default="section")
    strategy = parser.parse_args().strategy

    docs = defaultdict(list)
    with PAGES_PATH.open(encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            docs[record["file"]].append(record)

    chunks, headings_by_file = [], {}
    for name, pages in docs.items():
        headings = []
        chunks += chunk_document(pages, strategy, headings)
        if headings:
            headings_by_file[name] = headings

    with OUT_PATHS[strategy].open("w", encoding="utf-8") as out:
        for chunk in chunks:
            out.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    print_stats(chunks)
    if strategy == "section":
        print_headings(headings_by_file)
    print(f"\nWrote {len(chunks)} chunks to {OUT_PATHS[strategy]}")


if __name__ == "__main__":
    main()
