"""eval.py - Score retrieval and answers against eval/questions.jsonl.

Run from the project root:
  .venv\\Scripts\\python eval\\eval.py                    # retrieval (free) + answers (API)
  .venv\\Scripts\\python eval\\eval.py --retrieval-only   # no API calls
  .venv\\Scripts\\python eval\\eval.py --limit 2          # quick smoke test
Writes eval/results/<timestamp>/ with retrieval.jsonl, answers.jsonl and report.md.
"""
import argparse
import json
import random
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # project root: rag, embed

import anthropic
from dotenv import load_dotenv

import rag
from check_evidence import normalize
from embed import COLLECTIONS, search

QUESTIONS_PATH = Path("eval/questions.jsonl")
RESULTS_DIR = Path("eval/results")
KS = (3, 5, 8)
MAIN_SETUP = ("section_ctx", True)            # collection, filter on: what the chatbot uses
SETUPS = [(c, f, False) for c in COLLECTIONS for f in (True, False)]   # (collection, filter, rerank)
RERANK_SETUP = ("section_ctx", True, True)    # added with --rerank

JUDGE_MODEL = "claude-opus-5-5"               # stronger than the answering model (rag.MODEL)
JUDGE_EFFORT = "medium"
JUDGE_PRICE_PER_MTOK = {"input": 4.00, "output": 20.00}
GRADES = ["correct", "partly", "wrong", "correctly_refused", "wrongly_refused", "hallucinated"]
FAILURES = {"partly", "wrong", "wrongly_refused", "hallucinated"}

JUDGE_RUBRIC = """\
You grade answers from a chatbot that answers questions about US insurers' drug coverage \
policies from retrieved document excerpts.

You get the question, whether our documents can answer it, the facts a correct answer must \
contain, the sources the chatbot was given, and its answer. Pick one grade:
- correct: answerable; contains every expected fact (wording may differ) and contradicts none.
- partly: answerable; contains some expected facts, nothing false. This includes answers that \
give some facts and say the rest is not in the sources.
- wrong: answerable; contradicts an expected fact or gets the main point wrong (wrong insurer, \
wrong number or duration, AND/OR logic reversed).
- correctly_refused: not answerable; says the information isn't available and invents nothing.
- wrongly_refused: answerable; says the sources don't answer it and gives no expected fact.
- hallucinated: states a specific claim found in neither the sources nor the expected facts, or, \
for an unanswerable question, presents other information as the answer. This overrides the \
other grades.
Extra correct detail drawn from the sources does not lower a grade. Judge substance, not style.
reason: one sentence naming the missing, wrong or invented fact, if any."""

GRADE_SCHEMA = {
    "type": "object",
    "properties": {"grade": {"type": "string", "enum": GRADES}, "reason": {"type": "string"}},
    "required": ["grade", "reason"],
    "additionalProperties": False,
}


def load_questions(limit=None):
    """The test set, optionally cut to the first `limit` questions."""
    questions = [json.loads(line) for line in QUESTIONS_PATH.open(encoding="utf-8")]
    return questions[:limit] if limit else questions


def evidence_ranks(results, evidence):
    """For each evidence phrase, the rank of the first retrieved chunk containing it (None if none)."""
    texts = [normalize(r["text"]) for r in results]
    return [next((rank for rank, text in enumerate(texts, 1) if normalize(e["phrase"]) in text), None)
            for e in evidence]


def score_retrieval(questions, setups):
    """Every answerable question x setup (collection, filter, rerank) -> ranks and metrics.

    Each k gets its own retrieval rather than the first k of a k=8 list: per-insurer
    retrieval splits k between insurers, so the top 3 of a k=8 list is not what k=3 returns.
    MRR and the stored ranks come from the k=8 run.
    """
    rows = []
    for q in (q for q in questions if q["answerable"]):
        for collection, use_filter, use_rerank in setups:
            metrics = {}
            for k in KS:
                if use_filter:
                    results, where, fell_back = rag.retrieve(q["question"], collection, k,
                                                             use_rerank=use_rerank)
                else:
                    results, where, fell_back = search(q["question"], collection, k=k), {}, False
                ranks = evidence_ranks(results, q["evidence"])
                found = [r for r in ranks if r is not None]
                metrics[f"hit@{k}"] = float(bool(found))
                metrics[f"recall@{k}"] = len(found) / len(ranks)
            metrics["rr"] = 1 / min(found) if found else 0.0   # k = max(KS), the last run
            rows.append({"id": q["id"], "category": q["category"], "collection": collection,
                         "filter": use_filter, "rerank": use_rerank, "where": where,
                         "fell_back": fell_back, "ranks": ranks, **metrics})
    return rows


def judge(client, q, result):
    """Ask the judge model for {grade, reason}; also returns its token usage."""
    sources = rag.build_prompt(q["question"], result["sources"], MAIN_SETUP[0])
    message = (f"QUESTION: {q['question']}\n"
               f"ANSWERABLE FROM OUR DOCUMENTS: {'yes' if q['answerable'] else 'no'}\n"
               "EXPECTED FACTS:\n" + "\n".join(f"- {f}" for f in q["expected_facts"]) +
               f"\n\nSOURCES THE CHATBOT WAS GIVEN:\n{sources}\n\nCHATBOT ANSWER:\n{result['answer']}")
    response = client.beta.messages.create(
        model=JUDGE_MODEL, max_tokens=4000, system=JUDGE_RUBRIC,
        betas=["server-side-fallback-2026-07-01"], fallbacks="default",   # reroute if the judge declines
        output_config={"effort": JUDGE_EFFORT,
                       "format": {"type": "json_schema", "schema": GRADE_SCHEMA}},
        messages=[{"role": "user", "content": message}])
    if response.stop_reason == "refusal":
        verdict = {"grade": "judge_refused", "reason": "the judge model declined to grade"}
    else:
        verdict = json.loads(next(b.text for b in response.content if b.type == "text"))
    return verdict, response.usage


def score_answers(questions, use_rerank=False):
    """Answer every question with rag.ask() (main setup), judge it, and label failures."""
    load_dotenv(encoding="utf-8-sig")             # ANTHROPIC_API_KEY; never printed
    client = anthropic.Anthropic()
    rows = []
    for q in questions:
        try:
            result = rag.ask(q["question"], k=max(KS), collection=MAIN_SETUP[0],
                             use_filter=MAIN_SETUP[1], use_rerank=use_rerank)
        except rag.AnswerError as e:
            sys.exit(str(e))
        try:
            verdict, usage = judge(client, q, result)
        except anthropic.AuthenticationError:
            sys.exit("API key rejected (authentication error): check ANTHROPIC_API_KEY in .env.")
        ranks = evidence_ranks(result["sources"], q["evidence"]) if q["answerable"] else []
        recall = sum(r is not None for r in ranks) / len(ranks) if ranks else None
        failure = None
        if verdict["grade"] in FAILURES:
            # all evidence reached the model -> it's the answer step's fault
            failure = "generation" if not q["answerable"] or recall == 1 else "retrieval"
        judge_cost = (usage.input_tokens * JUDGE_PRICE_PER_MTOK["input"]
                      + usage.output_tokens * JUDGE_PRICE_PER_MTOK["output"]) / 1_000_000
        rows.append({"id": q["id"], "category": q["category"], "question": q["question"],
                     "answerable": q["answerable"], "answer": result["answer"],
                     "sources": [r["chunk_id"] for r in result["sources"]],
                     "where": result["where"], "cited": sorted(result["cited"]),
                     "invalid_citations": result["invalid_citations"],
                     "evidence_ranks": ranks, "evidence_recall@8": recall,
                     "grade": verdict["grade"], "reason": verdict["reason"], "failure": failure,
                     "answer_tokens": [result["input_tokens"], result["output_tokens"]],
                     "answer_cost_usd": result["cost_usd"],
                     "judge_tokens": [usage.input_tokens, usage.output_tokens],
                     "judge_cost_usd": judge_cost, "rerank": use_rerank,
                     "seconds": result["seconds"]})
        print(f"  {q['id']} {verdict['grade']:<18} {failure or '':<10} {verdict['reason'][:70]}")
    return rows


def mean(values):
    """Average of a non-empty list."""
    return sum(values) / len(values)


def retrieval_tables(rows):
    """Markdown: overall metrics per setup, then hit@8 / MRR per category per setup."""
    setup_of = lambda r: (r["collection"], r["filter"], r.get("rerank", False))
    setups = list(dict.fromkeys(setup_of(r) for r in rows))          # in run order
    name = lambda c, f, rr: f"{c} ({'filter' if f else 'no filter'}{' + rerank' if rr else ''})"
    cols = [f"hit@{k}" for k in KS] + [f"recall@{k}" for k in KS] + ["MRR"]
    lines = ["| setup | " + " | ".join(cols) + " |", "|---" * (len(cols) + 1) + "|"]
    for s in setups:
        sel = [r for r in rows if setup_of(r) == s]
        vals = [mean([r[m] for r in sel]) for m in cols[:-1]] + [mean([r["rr"] for r in sel])]
        lines.append(f"| {name(*s)} | " + " | ".join(f"{v:.2f}" for v in vals) + " |")
    cats = sorted({r["category"] for r in rows})
    lines += ["", "hit@8 / MRR per category:", "",
              "| category (n) | " + " | ".join(name(*s) for s in setups) + " |",
              "|---" * (len(setups) + 1) + "|"]
    for cat in cats:
        cells = []
        for s in setups:
            sel = [r for r in rows if setup_of(r) == s and r["category"] == cat]
            cells.append(f"{mean([r['hit@8'] for r in sel]):.2f} / {mean([r['rr'] for r in sel]):.2f}")
        n = len({r["id"] for r in rows if r["category"] == cat})
        lines.append(f"| {cat} ({n}) | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def answer_tables(rows):
    """Markdown: grade counts overall and per category, failures, and per-question grades."""
    grades = [g for g in GRADES + ["judge_refused"] if any(r["grade"] == g for r in rows)]
    total = Counter(r["grade"] for r in rows)
    lines = ["| grade | count |", "|---|---|"] + [f"| {g} | {total[g]} |" for g in grades]
    lines += ["", "Grades per category:", "", "| category | " + " | ".join(grades) + " |",
              "|---" * (len(grades) + 1) + "|"]
    by_cat = defaultdict(Counter)
    for r in rows:
        by_cat[r["category"]][r["grade"]] += 1
    for cat in sorted(by_cat):
        lines.append(f"| {cat} | " + " | ".join(str(by_cat[cat][g]) for g in grades) + " |")
    lines += ["", "Failures (retrieval = some evidence never reached the model; "
                  "generation = all evidence was retrieved):", "",
              "| id | grade | failure | evidence recall@8 | judge's reason |", "|---|---|---|---|---|"]
    for r in rows:
        if r["failure"]:
            recall = "n/a" if r["evidence_recall@8"] is None else f"{r['evidence_recall@8']:.2f}"
            lines.append(f"| {r['id']} | {r['grade']} | {r['failure']} | {recall} | {r['reason']} |")
    lines += ["", "All answers:", "", "| id | category | grade | reason |", "|---|---|---|---|"]
    lines += [f"| {r['id']} | {r['category']} | {r['grade']} | {r['reason']} |" for r in rows]
    return "\n".join(lines)


def cost_table(rows):
    """Markdown: tokens and USD for the answering model and the judge."""
    ans_in, ans_out = (sum(r["answer_tokens"][i] for r in rows) for i in (0, 1))
    j_in, j_out = (sum(r["judge_tokens"][i] for r in rows) for i in (0, 1))
    ans_cost, j_cost = sum(r["answer_cost_usd"] for r in rows), sum(r["judge_cost_usd"] for r in rows)
    return "\n".join(["| step | model | input tokens | output tokens | USD |", "|---|---|---|---|---|",
                      f"| answer | {rag.MODEL} | {ans_in:,} | {ans_out:,} | {ans_cost:.4f} |",
                      f"| judge | {JUDGE_MODEL} | {j_in:,} | {j_out:,} | {j_cost:.4f} |",
                      f"| total | | {ans_in + j_in:,} | {ans_out + j_out:,} | {ans_cost + j_cost:.4f} |"])


def spot_check(rows, n, seed):
    """n randomly chosen judged answers (fixed seed), for a human to check the judge."""
    picks = random.Random(seed).sample(rows, min(n, len(rows)))
    parts = []
    for r in sorted(picks, key=lambda r: r["id"]):
        parts.append(f"### {r['id']} ({r['category']}): {r['question']}\n\n"
                     f"**Judge: {r['grade']}**: {r['reason']}\n\n{r['answer']}\n")
    return "\n".join(parts)


def main():
    """Run the evaluation and write the results folder."""
    parser = argparse.ArgumentParser(description="Score retrieval and answers.")
    parser.add_argument("--retrieval-only", action="store_true", help="skip API calls")
    parser.add_argument("--limit", type=int, help="only the first N questions")
    parser.add_argument("--seed", type=int, default=7, help="seed for the judge spot-check")
    parser.add_argument("--rerank", action="store_true",
                        help=f"add a re-ranked retrieval setup and answer with re-ranking ({rag.RERANK_MODEL})")
    args = parser.parse_args()

    questions = load_questions(args.limit)
    out = RESULTS_DIR / datetime.now().strftime("%Y%m%d-%H%M%S")
    out.mkdir(parents=True)
    print(f"Scoring retrieval for {sum(q['answerable'] for q in questions)} answerable questions...")
    retrieval = score_retrieval(questions, SETUPS + ([RERANK_SETUP] if args.rerank else []))
    write_jsonl(out / "retrieval.jsonl", retrieval)
    rerank_note = f" + {rag.RERANK_MODEL} re-ranking of {rag.RERANK_CANDIDATES}" if args.rerank else ""
    report = [f"# Evaluation run {out.name}", "",
              f"{len(questions)} questions ({sum(not q['answerable'] for q in questions)} unanswerable). "
              f"Answers: {rag.MODEL} on {MAIN_SETUP[0]}, filter on{rerank_note}, k={max(KS)}. "
              f"Judge: {JUDGE_MODEL}.",
              "", "## Retrieval (answerable questions only)", "", retrieval_tables(retrieval)]
    if not args.retrieval_only:
        print(f"Answering and judging {len(questions)} questions...")
        answers = score_answers(questions, use_rerank=args.rerank)
        write_jsonl(out / "answers.jsonl", answers)
        report += ["", "## Answers (main setup)", "", answer_tables(answers),
                   "", "## API cost", "", cost_table(answers),
                   "", f"## Judge spot-check (5 random answers, seed {args.seed})", "",
                   spot_check(answers, 5, args.seed)]
    (out / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"\nWrote {out}/report.md")


def write_jsonl(path, rows):
    """One JSON object per line."""
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
