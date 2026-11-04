"""check_evidence.py - Validate the evidence phrases in eval/questions.jsonl.

Retrieval is scored by whether a retrieved chunk contains a question's evidence
phrases, so every phrase must, in BOTH chunk files (section and fixed):
  - appear in at least one chunk (after normalizing whitespace and case),
  - appear only in chunks from its expected file,
  - appear in at most MAX_CHUNKS chunks; a phrase found everywhere is too
    generic and would make retrieval look better than it is.
Unanswerable questions list absent_terms, which must appear in no chunk at all.

Usage: .venv\\Scripts\\python eval\\check_evidence.py   (exit code 1 if anything fails)
"""
import json
import sys
from pathlib import Path

QUESTIONS_PATH = Path("eval/questions.jsonl")
CHUNK_FILES = {"section": Path("data/chunks.jsonl"), "fixed": Path("data/chunks_fixed.jsonl")}
MAX_CHUNKS = 3


def normalize(text):
    """Lowercase and collapse all whitespace (line breaks included) to single spaces."""
    return " ".join(text.lower().split())


def load_chunks():
    """{"section": [(file, normalized text_raw), ...], "fixed": [...]}."""
    return {name: [(c["file"], normalize(c["text_raw"]))
                   for c in map(json.loads, path.open(encoding="utf-8"))]
            for name, path in CHUNK_FILES.items()}


def check_phrase(phrase, expected_file, chunks):
    """-> (problems, {collection: match count}) for one evidence phrase."""
    phrase, problems, counts = normalize(phrase), [], {}
    for name, items in chunks.items():
        files = [f for f, text in items if phrase in text]
        counts[name] = len(files)
        if not files:
            problems.append(f"not found in {name}")
        elif set(files) != {expected_file}:
            problems.append(f"{name} matches other files: {sorted(set(files) - {expected_file})}")
        elif len(files) > MAX_CHUNKS:
            problems.append(f"too generic in {name} ({len(files)} chunks)")
    return problems, counts


def main():
    """Check every question; print one line per phrase or absent term."""
    chunks = load_chunks()
    questions = [json.loads(line) for line in QUESTIONS_PATH.open(encoding="utf-8")]
    failures = 0
    print(f"{'id':<5} {'section':>7} {'fixed':>5}  status  phrase")
    for q in questions:
        for ev in q["evidence"]:
            problems, counts = check_phrase(ev["phrase"], ev["file"], chunks)
            failures += bool(problems)
            status = "ok" if not problems else "FAIL: " + "; ".join(problems)
            print(f"{q['id']:<5} {counts['section']:>7} {counts['fixed']:>5}  {status:<6}  {ev['phrase'][:70]}")
        for term in q.get("absent_terms", []):
            found = sum(normalize(term) in text for items in chunks.values() for _, text in items)
            failures += bool(found)
            print(f"{q['id']:<5} {'':>13}  {'ok' if not found else f'FAIL: found in {found} chunks'}"
                  f"  absent: {term!r}")
    print(f"\n{len(questions)} questions, {failures} problem(s)")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
