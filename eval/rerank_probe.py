"""rerank_probe.py - Retrieval-only check of cross-encoder re-ranking on the failing questions.

Run from the project root (no API calls):
  .venv\\Scripts\\python eval\\rerank_probe.py [results folder]
For q04, q17 and q19: evidence ranks and recall@8 with re-ranking off and on, the time
each retrieval takes, the re-ranker's load time and the process's peak memory.
Writes rerank_probe.md into the given folder (default: a new timestamped one).
"""
import json
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # project root: rag, embed

import psutil

import rag
from check_evidence import normalize

PROBE_IDS = ("q04", "q17", "q19")      # the retrieval failures in the baseline evaluation


def peak_memory_mb():
    """Peak memory of this process so far: peak working set on Windows, else current RSS."""
    info = psutil.Process().memory_info()
    return getattr(info, "peak_wset", info.rss) / 2**20


def main():
    """Probe the three questions with re-ranking off, then on, and write the table."""
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else \
        Path("eval/results") / f"{datetime.now():%Y%m%d-%H%M%S}-rerank-probe"
    out.mkdir(parents=True, exist_ok=True)
    questions = {q["id"]: q for q in map(json.loads, Path("eval/questions.jsonl").open(encoding="utf-8"))}

    rag.retrieve("warm-up", "section_ctx", rag.DEFAULT_K)        # load the embedding model first
    memory_before = peak_memory_mb()
    start = time.perf_counter()
    rag.load_reranker()
    load_seconds = time.perf_counter() - start

    rows = ["| question | re-rank | seconds | evidence ranks in top 8 | recall@8 |", "|---|---|---|---|---|"]
    for qid in PROBE_IDS:
        q = questions[qid]
        for use_rerank in (False, True):
            start = time.perf_counter()
            results, _, _ = rag.retrieve(q["question"], "section_ctx", rag.DEFAULT_K, use_rerank=use_rerank)
            seconds = time.perf_counter() - start
            texts = [normalize(r["text"]) for r in results]
            ranks = [next((i for i, t in enumerate(texts, 1) if normalize(e["phrase"]) in t), None)
                     for e in q["evidence"]]
            found = sum(r is not None for r in ranks)
            rows.append(f"| {qid} | {'on' if use_rerank else 'off'} | {seconds:.1f} | "
                        f"{', '.join(str(r) if r else '-' for r in ranks)} | {found}/{len(ranks)} |")
            print(rows[-1])

    report = [f"# Re-ranking probe: {rag.RERANK_MODEL}", "",
              f"section_ctx, filters as rag.retrieve, k={rag.DEFAULT_K}, "
              f"{rag.RERANK_CANDIDATES} candidates per filter, max_length {rag.RERANK_MAX_LENGTH}, CPU.", "",
              *rows, "",
              f"- Re-ranker load time: {load_seconds:.0f} s (model already downloaded; "
              "the first-ever run also downloads about 2.3 GB).",
              f"- Peak memory: {memory_before:,.0f} MB with the embedding model only, "
              f"{peak_memory_mb():,.0f} MB after re-ranking.",
              "", "Decision: re-ranking stays off by default (known limitation). It moved q04's Prolia "
              "criteria to rank 1 and q17's Cigna threshold into the top 8, but q19 lost Aetna's "
              "chunk, and re-ranking takes about a minute per question on this CPU."]
    (out / "rerank_probe.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"\nWrote {out / 'rerank_probe.md'}")


if __name__ == "__main__":
    main()
