"""rag.py - Answer coverage questions from the vector store, with citations.

Usage:
  .venv\\Scripts\\python rag.py "Does Cigna require a statin trial for Repatha?"
      [--k 8] [--collection section_ctx] [--no-filter] [--rerank]

Retrieves chunks with embed.search(), asks Claude to answer only from them,
and checks that every [S#] citation points at a retrieved source.
The API key is read from .env by python-dotenv and never printed.
"""
import argparse
import json
import os
import re
import sys
import time
from collections import defaultdict
from functools import cache
from pathlib import Path

import anthropic
from dotenv import load_dotenv

from embed import COLLECTIONS, search

MODEL = "claude-haiku-5-5"        # small, cheap current model
EFFORT = "low"                    # Haiku 5.5 rejects temperature; low effort = short, steady answers
MAX_TOKENS = 2000
PRICE_PER_MTOK = {"input": 0.10, "output": 0.50}   # USD, claude-haiku-5-5 list price
DEFAULT_K = 8
MIN_FILTERED = 3                  # fewer filtered hits than this -> search unfiltered
RERANK_MODEL = "BAAI/bge-reranker-v2-m3"   # 1 of 389 question+chunk pairs exceeds 1024 tokens
RERANK_MAX_LENGTH = 1024
RERANK_CANDIDATES = 25            # embedding hits per filter that the re-ranker re-orders

# Question words -> metadata filters. A field is filtered only when exactly one
# value matches, so "compare Cigna and Aetna" still searches both.
FILTER_RULES = [
    ("source", "cigna", r"\bcigna\b"),
    ("source", "aetna", r"\baetna\b"),
    ("source", "uhc", r"\b(?:unitedhealthcare|united healthcare|uhc)\b"),
    ("drug", "repatha", r"\b(?:repatha|evolocumab)\b"),
    ("drug", "prolia", r"\b(?:prolia|denosumab)\b"),
    ("drug", "otezla", r"\b(?:otezla|apremilast)\b"),
]
SOURCE_NAMES = {"aetna": "Aetna", "cigna": "Cigna", "uhc": "UnitedHealthcare", "fda": "FDA"}

SYSTEM_PROMPT = """\
You answer questions about US insurer coverage policies for Repatha, Prolia and Otezla, \
using only the numbered sources in the user's message.

Rules:
1. Answer ONLY from the sources. Do not use outside knowledge, even if you believe you know the answer.
2. Cite every claim with its source number in square brackets, e.g. [S2] or [S1][S4].
3. If the sources don't answer the question, say so clearly and do not guess.
4. If the question asks about an insurer, plan or drug that does not appear in any source header, \
say explicitly that you don't have that insurer's or drug's policy, and list which insurers you do \
have for that drug, using the document list below. Do not answer from other insurers' policies as \
a substitute. Base every "I don't have X" statement on the document list, not on which sources \
were retrieved: if the list has a document that is not among the sources, say the provided \
sources don't cover it, not that it doesn't exist.
5. For coverage questions, prefer policy and formulary sources over FDA labels, and say which \
insurer and policy date the answer comes from.
6. If sources disagree (different insurers or dates), say so rather than merging them.
7. Keep answers concise. Keep criteria lists in their original AND/OR structure: never turn \
"all of the following" into "any of the following", or the reverse."""

CITATION = re.compile(r"\[\s*(S\d+(?:\s*[,;]\s*S?\d+)*)\s*\]")
NO_ANSWER = re.compile(r"\b(?:do not|don't) have\b|not (?:in|found in|covered by|available in) "
                       r"the (?:provided )?sources|sources (?:do not|don't)", re.I)


@cache
def system_prompt():
    """SYSTEM_PROMPT plus the list of every document we hold, built from data/chunks.jsonl.

    The list lets the model name the insurers we do have for a drug even when
    retrieval missed their chunks. It is fixed per run, so the prompt stays cacheable.
    """
    with Path(COLLECTIONS["section_ctx"][0]).open(encoding="utf-8") as f:
        docs = {(SOURCE_NAMES.get(c["source"], c["source"]), c["drug"].capitalize(),
                 c["doc_type"], c["version_date"]) for c in map(json.loads, f)}
    lines = [" | ".join(doc) for doc in sorted(docs)]
    return (SYSTEM_PROMPT + "\n\nDocuments in the knowledge base (insurer | drug | type | version "
            "date). This list only says what exists; it is not a source and must not be cited:\n"
            + "\n".join(f"- {line}" for line in lines))


@cache
def raw_texts(collection):
    """chunk_id -> text_raw for a collection's chunk file (the prompt adds its own header)."""
    path = COLLECTIONS[collection][0]
    with Path(path).open(encoding="utf-8") as f:
        return {c["chunk_id"]: c["text_raw"] for c in map(json.loads, f)}


def question_filter(question):
    """Metadata filter from insurer and drug names in the question, e.g. {"source": "cigna"}."""
    matches = defaultdict(set)
    for field, value, pattern in FILTER_RULES:
        if re.search(pattern, question, re.I):
            matches[field].add(value)
    return {field: values.pop() for field, values in matches.items() if len(values) == 1}


def insurers_named(question):
    """Insurer source values named in the question, in FILTER_RULES order."""
    return [value for field, value, pattern in FILTER_RULES
            if field == "source" and re.search(pattern, question, re.I)]


@cache
def load_reranker():
    """The cross-encoder, loaded once (about 2.3 GB on first download)."""
    from sentence_transformers import CrossEncoder
    return CrossEncoder(RERANK_MODEL, max_length=RERANK_MAX_LENGTH)


_rerank_scores = {}  # (question, chunk_id) -> cross-encoder score, so repeated k's don't re-score


def rerank(question, candidates, keep):
    """Re-order candidates by cross-encoder relevance to the question; keep the top `keep`."""
    new = [r for r in candidates if (question, r["chunk_id"]) not in _rerank_scores]
    if new:
        scores = load_reranker().predict([(question, r["text"]) for r in new], batch_size=8)
        for r, score in zip(new, scores):
            _rerank_scores[(question, r["chunk_id"])] = float(score)
    ranked = sorted(candidates, key=lambda r: _rerank_scores[(question, r["chunk_id"])],
                    reverse=True)[:keep]
    for rank, r in enumerate(ranked, start=1):
        r["rank"], r["rerank_score"] = rank, _rerank_scores[(question, r["chunk_id"])]
    return ranked


def ranked_search(question, collection, k, where=None, use_rerank=False):
    """search(), or with use_rerank: RERANK_CANDIDATES candidates re-ranked down to k."""
    if not use_rerank:
        return search(question, collection, k=k, where=where)
    return rerank(question, search(question, collection, k=RERANK_CANDIDATES, where=where), k)


def retrieve_per_insurer(question, collection, k, insurers, use_rerank=False):
    """Comparison questions: one filtered search per insurer with k split evenly, then merged.

    Each insurer gets k // n slots (the first k % n insurers one extra) and keeps any
    drug filter; results stay grouped by insurer and are renumbered 1..k for the prompt.
    With use_rerank, each insurer's candidates are re-ranked within that insurer.
    """
    base = question_filter(question)                 # drops "source" when 2+ insurers match
    merged, seen = [], set()
    for i, insurer in enumerate(insurers):
        share = k // len(insurers) + (i < k % len(insurers))
        for r in ranked_search(question, collection, share, {**base, "source": insurer}, use_rerank):
            if r["chunk_id"] not in seen:
                seen.add(r["chunk_id"])
                merged.append(r)
    for rank, r in enumerate(merged, start=1):
        r["rank"] = rank
    return merged, {**base, "source": insurers}


def retrieve(question, collection, k, use_filter=True, use_rerank=False):
    """Top-k chunks -> (results, filter used, fell back?). Unfiltered if the filter finds < 3.

    A question naming 2+ insurers gets one search per insurer (retrieve_per_insurer),
    so one insurer's chunks can't crowd the other's out of the top k. use_rerank
    re-ranks RERANK_CANDIDATES embedding hits with a cross-encoder before keeping k.
    """
    insurers = insurers_named(question) if use_filter else []
    if len(insurers) >= 2:
        results, where = retrieve_per_insurer(question, collection, k, insurers, use_rerank)
        if len(results) >= MIN_FILTERED:
            return results, where, False
        return ranked_search(question, collection, k, None, use_rerank), {}, True
    where = question_filter(question) if use_filter else {}
    if where:
        results = ranked_search(question, collection, k, where, use_rerank)
        if len(results) >= MIN_FILTERED:
            return results, where, False
    return ranked_search(question, collection, k, None, use_rerank), {}, bool(where)


def build_prompt(question, results, collection):
    """Number the chunks [S1]..[Sk] with a header line each, then ask the question."""
    texts = raw_texts(collection)
    blocks = []
    for r in results:
        m = r["meta"]
        pages = f"pp. {m['page_start']}-{m['page_end']}" if m["page_end"] != m["page_start"] \
            else f"p. {m['page_start']}"
        header = " | ".join([SOURCE_NAMES.get(m["source"], m["source"]), m["drug"].capitalize(),
                             m["doc_type"], pages, m["version_date"], m["section"] or "-"])
        blocks.append(f'<source id="S{r["rank"]}">\n{header}\n{texts[r["chunk_id"]]}\n</source>')
    return "\n\n".join(blocks) + f"\n\nQuestion: {question}"


def generate(user_message):
    """One Claude call -> (answer text, usage). Exits with a clear message on auth errors."""
    # Puts ANTHROPIC_API_KEY into the environment (never printed). utf-8-sig also reads a
    # .env saved with a byte-order mark, which PowerShell 5.1 adds by default.
    load_dotenv(encoding="utf-8-sig")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY not found: .env needs a line ANTHROPIC_API_KEY=<your key>.")
    client = anthropic.Anthropic()
    try:
        response = client.messages.create(
            model=MODEL, max_tokens=MAX_TOKENS, system=system_prompt(),
            output_config={"effort": EFFORT},
            messages=[{"role": "user", "content": user_message}])
    except anthropic.AuthenticationError:
        sys.exit("API key rejected (authentication error): check ANTHROPIC_API_KEY in .env.")
    except anthropic.RateLimitError:
        sys.exit("Rate limited by the API; try again in a minute.")
    except anthropic.APIConnectionError:
        sys.exit("Could not reach the Anthropic API; check the network connection.")
    if response.stop_reason == "refusal":
        return "[The model declined to answer this question.]", response.usage
    answer = "".join(block.text for block in response.content if block.type == "text")
    if response.stop_reason == "max_tokens":
        answer += "\n[Answer cut off at MAX_TOKENS.]"
    return answer.strip(), response.usage


def check_citations(answer, n_sources):
    """-> (cited source numbers, invalid citations, uncited-claims warning or None)."""
    cited, invalid = set(), []
    for group in CITATION.findall(answer):
        for number in map(int, re.findall(r"\d+", group)):
            if 1 <= number <= n_sources:
                cited.add(number)
            else:
                invalid.append(f"S{number}")
    warning = None
    if not cited and not NO_ANSWER.search(answer):
        warning = "answer has no citations and doesn't say the sources lack the answer"
    return cited, invalid, warning


def ask(question, k=DEFAULT_K, collection="section_ctx", use_filter=True, use_rerank=False):
    """Retrieve, generate and check one question. Returns a dict with everything to report."""
    start = time.perf_counter()
    results, where, fell_back = retrieve(question, collection, k, use_filter, use_rerank)
    retrieved = time.perf_counter()
    answer, usage = generate(build_prompt(question, results, collection))
    seconds = {"retrieve": retrieved - start, "answer": time.perf_counter() - retrieved}
    cited, invalid, warning = check_citations(answer, len(results))
    cost = (usage.input_tokens * PRICE_PER_MTOK["input"]
            + usage.output_tokens * PRICE_PER_MTOK["output"]) / 1_000_000
    return {"question": question, "answer": answer, "sources": results, "where": where,
            "fell_back": fell_back, "cited": cited, "invalid_citations": invalid,
            "warning": warning, "input_tokens": usage.input_tokens,
            "output_tokens": usage.output_tokens, "cost_usd": cost, "seconds": seconds}


def print_result(result):
    """Answer, then the sources list, citation check and token cost."""
    print(result["answer"])
    print("\nSources:")
    for r in result["sources"]:
        m = r["meta"]
        mark = "cited" if r["rank"] in result["cited"] else "     "
        print(f"  [S{r['rank']}] {mark}  {r['chunk_id']:<28} pp. {m['page_start']}-{m['page_end']:<4} "
              f"{m['version_date']}")
    filt = result["where"] or "none"
    print(f"\nFilter: {filt}" + ("  (filtered search found < 3, fell back to unfiltered)"
                                 if result["fell_back"] else ""))
    if result["invalid_citations"]:
        print(f"WARNING: citations not in the retrieved set: {result['invalid_citations']}")
    if result["warning"]:
        print(f"WARNING: {result['warning']}")
    print(f"Tokens: {result['input_tokens']} in / {result['output_tokens']} out, "
          f"${result['cost_usd']:.5f}")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Answer a coverage question with citations.")
    parser.add_argument("question")
    parser.add_argument("--k", type=int, default=DEFAULT_K)
    parser.add_argument("--collection", choices=COLLECTIONS, default="section_ctx")
    parser.add_argument("--no-filter", action="store_true", help="skip the insurer/drug filter")
    parser.add_argument("--rerank", action="store_true", help=f"re-rank with {RERANK_MODEL}")
    args = parser.parse_args()
    print_result(ask(args.question, args.k, args.collection, not args.no_filter, args.rerank))


if __name__ == "__main__":
    main()
