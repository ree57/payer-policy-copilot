"""timing.py - End-to-end seconds per question and peak memory, with re-ranking on or off.

Run once per mode, in separate processes so peak memory isn't shared:
  .venv\\Scripts\\python eval\\timing.py
  .venv\\Scripts\\python eval\\timing.py --rerank
Uses rag.ask() for every test question (answering model only, no judge: about $0.02 a run).
A warm-up question first loads the models; that cold start is reported separately.
Writes eval/results/timing/rerank-on.json or rerank-off.json.
"""
import argparse
import json
import sys
import time
from pathlib import Path
from statistics import median, quantiles

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # project root: rag, embed

import psutil

import rag

QUESTIONS_PATH = Path("eval/questions.jsonl")
OUT_DIR = Path("eval/results/timing")
WARM_UP = "Warm-up: which documents cover Repatha?"   # not a test question, so no cached scores


def peak_memory_mb():
    """Peak memory of this process so far: peak working set on Windows, else current RSS."""
    info = psutil.Process().memory_info()
    return getattr(info, "peak_wset", info.rss) / 2**20


def summary(values):
    """median / p90 / max of a list of seconds."""
    return {"median": median(values), "p90": quantiles(values, n=10)[-1], "max": max(values)}


def main():
    """Time every question and write the JSON summary."""
    parser = argparse.ArgumentParser(description="Time rag.ask() with re-ranking on or off.")
    parser.add_argument("--rerank", action="store_true")
    use_rerank = parser.parse_args().rerank
    questions = [json.loads(line)["question"] for line in QUESTIONS_PATH.open(encoding="utf-8")]

    start = time.perf_counter()
    rag.retrieve(WARM_UP, "section_ctx", rag.DEFAULT_K, use_rerank=use_rerank)   # loads the models
    cold_start = time.perf_counter() - start

    rows = []
    for question in questions:
        start = time.perf_counter()
        result = rag.ask(question, use_rerank=use_rerank)
        total = time.perf_counter() - start
        rows.append({**result["seconds"], "total": total})
        print(f"  {total:5.1f}s  (retrieve {result['seconds']['retrieve']:4.1f}s)  {question[:60]}")

    report = {"rerank": use_rerank, "questions": len(rows),
              "cold_start_seconds": cold_start, "peak_memory_mb": peak_memory_mb(),
              **{step: summary([r[step] for r in rows]) for step in ("retrieve", "answer", "total")}}
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"rerank-{'on' if use_rerank else 'off'}.json"
    out.write_text(json.dumps(report, indent=1), encoding="utf-8")
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
