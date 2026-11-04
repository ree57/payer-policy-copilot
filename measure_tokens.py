"""measure_tokens.py - Count chunk lengths with each candidate model's tokenizer.

Embedding models silently truncate input past their max sequence length, so
this checks how many chunks would lose their tail before choosing a model.
Counts include the document prefix each model expects.
"""
import json
import sys
from pathlib import Path
from statistics import median

from transformers import AutoTokenizer

CANDIDATES = {
    # model name: (document prefix, max sequence length)
    "BAAI/bge-small-en-v1.5": ("", 512),
    "nomic-ai/nomic-embed-text-v1.5": ("search_document: ", 8192),
}
RERANKERS = {  # cross-encoder candidates: max input length of the (question, chunk) pair
    "BAAI/bge-reranker-base": 512,
    "BAAI/bge-reranker-v2-m3": 8192,
}
INPUTS = [  # (label, file, field), matching the three planned collections
    ("section_ctx", "data/chunks.jsonl", "text"),
    ("section_raw", "data/chunks.jsonl", "text_raw"),
    ("fixed", "data/chunks_fixed.jsonl", "text"),
]


def measure_rerankers():
    """Token counts of (longest test question, chunk text) pairs, as a cross-encoder reads them."""
    questions = [json.loads(line)["question"] for line in Path("eval/questions.jsonl").open(encoding="utf-8")]
    question = max(questions, key=len)
    chunks = [json.loads(line) for line in Path("data/chunks.jsonl").open(encoding="utf-8")]
    print(f"Pairs of the longest test question ({len(question)} chars) with each section_ctx chunk `text`")
    for model, max_len in RERANKERS.items():
        tokenizer = AutoTokenizer.from_pretrained(model)
        counts = [len(ids) for ids in tokenizer([question] * len(chunks),
                                                [c["text"] for c in chunks])["input_ids"]]
        over = [n for n in counts if n > max_len]
        over_512 = [n for n in counts if n > 512]
        print(f"\n{model}  (max {max_len})")
        print(f"  pairs {len(counts)}  min {min(counts)}  median {median(counts):.0f}  max {max(counts)}  "
              f"over max: {len(over)} ({len(over) / len(counts):.0%})  over 512: {len(over_512)} "
              f"({len(over_512) / len(counts):.0%})")


def main():
    """Print token stats and over-limit counts per model and collection."""
    if "--rerankers" in sys.argv:
        measure_rerankers()
        return
    for model, (prefix, max_len) in CANDIDATES.items():
        tokenizer = AutoTokenizer.from_pretrained(model)
        print(f"\n{model}  (max {max_len} tokens, prefix {prefix!r})")
        print(f"  {'collection':<12} {'chunks':>6} {'min':>5} {'median':>6} {'max':>5} "
              f"{'over max':>9} {'chars/token':>11}")
        for label, path, field in INPUTS:
            chunks = [json.loads(line) for line in Path(path).open(encoding="utf-8")]
            texts = [prefix + c[field] for c in chunks]
            counts = [len(ids) for ids in tokenizer(texts)["input_ids"]]   # includes [CLS]/[SEP]
            over = [(n, c["chunk_id"]) for n, c in zip(counts, chunks) if n > max_len]
            ratio = sum(map(len, texts)) / sum(counts)
            print(f"  {label:<12} {len(chunks):>6} {min(counts):>5} {median(counts):>6.0f} "
                  f"{max(counts):>5} {len(over):>4} ({len(over) / len(chunks):4.0%}) {ratio:>11.2f}")
            for n, chunk_id in sorted(over, reverse=True)[:3]:
                print(f"      longest over: {chunk_id} = {n} tokens")


if __name__ == "__main__":
    main()
