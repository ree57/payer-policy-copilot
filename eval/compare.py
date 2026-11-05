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


def run_setup(run):
    """(collection, filter, rerank) the run's answers used; older runs had no re-ranking."""
    with (Path(run) / "answers.jsonl").open(encoding="utf-8") as f:
        return (*MAIN_SETUP, json.loads(f.readline()).get("rerank", False))


def load(run, name):
    """Rows of a run's JSONL file, keyed by question id (retrieval: the answering setup only)."""
    rows = [json.loads(line) for line in (Path(run) / name).open(encoding="utf-8")]
    if name == "retrieval.jsonl":
        rows = [r for r in rows if (r["collection"], r["filter"], r.get("rerank", False)) == run_setup(run)]
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
    # Before/after numbers cover only the questions both runs answered; added ones are listed apart.
    added = [i for i in an if i not in ab]
    rn = {i: r for i, r in rn.items() if i in rb}
    an_all, an = an, {i: r for i, r in an.items() if i in ab}

    head = "| run | " + " | ".join(m.replace("rr", "MRR") for m in METRICS) + " |"
    lines = [f"# Comparison: {Path(base).name} -> {Path(new).name}", "",
             f"Answering setup (collection, filter, rerank): before {run_setup(base)}, "
             f"after {run_setup(new)}; k={max(KS)}.", "",
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
        if Path(base).name in questions[i].get("changed_after_baseline", ""):
            cause = "expected facts"       # the note names this baseline run
        elif ab[i]["sources"] != an[i]["sources"]:
            cause = "retrieval"
        else:
            cause = "generation"
        lines.append(f"| {i} | {ab[i]['grade']} | {an[i]['grade']} | {cause} | {an[i]['reason']} |")
    if added:
        lines += ["", "## Questions added since the earlier run", "",
                  "| id | grade | evidence recall@8 | judge's reason |", "|---|---|---|---|"]
        for i in added:
            recall = an_all[i]["evidence_recall@8"]
            lines.append(f"| {i} | {an_all[i]['grade']} | "
                         f"{'n/a' if recall is None else f'{recall:.2f}'} | {an_all[i]['reason']} |")
    out = Path(new) / "comparison.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
