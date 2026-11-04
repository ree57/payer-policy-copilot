"""compare.py - Compare two eval/results runs and write comparison.md into the newer one.

Usage: .venv\\Scripts\\python eval\\compare.py eval/results/<baseline> eval/results/<new>

Each changed grade is attributed from the data, not by hand:
  expected facts  - the question record has a changed_after_baseline note
  retrieval       - the 8 sources given to the answering model changed
  generation      - same sources, same expectations: the answer itself changed
                    (prompt edit, or run-to-run variation of the model)
"""
import json
import sys
from collections import Counter
from pathlib import Path

from eval import GRADES, KS, MAIN_SETUP, QUESTIONS_PATH, mean

METRICS = [f"hit@{k}" for k in KS] + [f"recall@{k}" for k in KS] + ["rr"]
GOOD = {"correct", "correctly_refused"}


def load(run, name):
    """Rows of a run's JSONL file, keyed by question id (retrieval: main setup only)."""
    rows = [json.loads(line) for line in (Path(run) / name).open(encoding="utf-8")]
    if name == "retrieval.jsonl":
        rows = [r for r in rows if (r["collection"], r["filter"]) == MAIN_SETUP]
    return {r["id"]: r for r in rows}


def metric_row(label, rows):
    """One markdown table row of the mean of each metric."""
    return f"| {label} | " + " | ".join(f"{mean([r[m] for r in rows]):.2f}" for m in METRICS) + " |"


def main():
    """Write the before/after comparison for the main setup."""
    base, new = sys.argv[1], sys.argv[2]
    rb, rn = load(base, "retrieval.jsonl"), load(new, "retrieval.jsonl")
    ab, an = load(base, "answers.jsonl"), load(new, "answers.jsonl")
    questions = {q["id"]: q for q in map(json.loads, QUESTIONS_PATH.open(encoding="utf-8"))}

    head = "| run | " + " | ".join(m.replace("rr", "MRR") for m in METRICS) + " |"
    lines = [f"# Comparison: {Path(base).name} -> {Path(new).name}", "",
             f"Main setup: {MAIN_SETUP[0]}, filter on, k={max(KS)}.", "",
             "## Retrieval, all answerable questions", "", head, "|---" * (len(METRICS) + 1) + "|",
             metric_row("before", rb.values()), metric_row("after", rn.values())]
    for cat in sorted({r["category"] for r in rn.values()}):
        if cat == "comparison":
            lines += ["", f"## Retrieval, {cat} questions", "", head, "|---" * (len(METRICS) + 1) + "|",
                      metric_row("before", [r for r in rb.values() if r["category"] == cat]),
                      metric_row("after", [r for r in rn.values() if r["category"] == cat])]
    moved = [i for i in rn if (rb[i]["hit@8"], rb[i]["recall@8"]) != (rn[i]["hit@8"], rn[i]["recall@8"])]
    lines += ["", "Questions whose hit@8 / recall@8 changed: " +
              (", ".join(f"{i} ({rb[i]['recall@8']:.2f} -> {rn[i]['recall@8']:.2f})" for i in moved) or "none")]

    gb, gn = Counter(r["grade"] for r in ab.values()), Counter(r["grade"] for r in an.values())
    lines += ["", "## Answer grades", "", "| grade | before | after |", "|---|---|---|"]
    lines += [f"| {g} | {gb[g]} | {gn[g]} |" for g in GRADES + ["judge_refused"] if gb[g] or gn[g]]
    good_b, good_n = sum(gb[g] for g in GOOD), sum(gn[g] for g in GOOD)
    lines += [f"| **correct + correctly_refused** | **{good_b}** | **{good_n}** |"]

    lines += ["", "## Questions whose grade changed", "",
              "| id | before | after | cause | judge's reason now |", "|---|---|---|---|---|"]
    for i in an:
        if ab[i]["grade"] == an[i]["grade"]:
            continue
        if "changed_after_baseline" in questions[i]:
            cause = "expected facts"
        elif ab[i]["sources"] != an[i]["sources"]:
            cause = "retrieval"
        else:
            cause = "generation"
        lines.append(f"| {i} | {ab[i]['grade']} | {an[i]['grade']} | {cause} | {an[i]['reason']} |")
    out = Path(new) / "comparison.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
