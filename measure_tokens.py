"""measure_tokens.py - Count chunk lengths with each candidate model's tokenizer.

Embedding models silently truncate input past their max sequence length, so
this checks how many chunks would lose their tail before choosing a model.
Counts include the document prefix each model expects.
"""
import json
from pathlib import Path
from statistics import median

from transformers import AutoTokenizer

CANDIDATES = {
    # model name: (document prefix, max sequence length)
    "BAAI/bge-small-en-v1.5": ("", 512),
    "nomic-ai/nomic-embed-text-v1.5": ("search_document: ", 8192),
}
INPUTS = [  # (label, file, field), matching the three planned collections
    ("section_ctx", "data/chunks.jsonl", "text"),
    ("section_raw", "data/chunks.jsonl", "text_raw"),
    ("fixed", "data/chunks_fixed.jsonl", "text"),
]


def main():
    """Print token stats and over-limit counts per model and collection."""
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
