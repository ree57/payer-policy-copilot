"""embed.py - Embed the chunks into a local, persistent Chroma vector store.

Builds three collections in chroma_db/ so Day 2 can compare them:
  section_ctx  chunks.jsonl, embedding `text` (with the context line)
  section_raw  chunks.jsonl, embedding `text_raw` (no context line)
  fixed        chunks_fixed.jsonl, embedding `text`
then runs a few test searches against section_ctx.
"""
import json
import time
from functools import cache
from pathlib import Path

import chromadb
from chromadb.errors import NotFoundError
from sentence_transformers import SentenceTransformer

DB_PATH = "chroma_db"
# Chosen with measure_tokens.py: 43% of section_ctx chunks are over bge-small's
# 512-token limit and would be silently truncated; none are over nomic's 8192.
MODEL_NAME = "nomic-ai/nomic-embed-text-v1.5"
DOC_PREFIX = "search_document: "     # nomic needs a task prefix on every input
QUERY_PREFIX = "search_query: "
BATCH_SIZE = 16

COLLECTIONS = {  # name: (chunk file, field to embed)
    "section_ctx": ("data/chunks.jsonl", "text"),
    "section_raw": ("data/chunks.jsonl", "text_raw"),
    "fixed": ("data/chunks_fixed.jsonl", "text"),
}
METADATA_FIELDS = ["source", "drug", "doc_type", "page_start", "page_end", "section",
                   "version_date"]

TEST_QUESTIONS = [
    "Does Cigna require a statin trial before approving Repatha?",
    "How long is UnitedHealthcare's initial approval for Otezla in psoriatic arthritis?",
    "What tier is Prolia on Aetna's formulary?",
    "Which denosumab biosimilars does Cigna cover?",
]


@cache
def load_model(name):
    """Load an embedding model once per run (nomic ships its own model code)."""
    return SentenceTransformer(name, trust_remote_code=True)


@cache
def get_client():
    """The persistent Chroma client for chroma_db/."""
    return chromadb.PersistentClient(path=DB_PATH)


def build_collection(name, path, field):
    """(Re)build one collection: delete it if present, embed the chunks, add them.

    The model name and prefixes go into the collection's metadata, so search()
    always queries it with the model it was built with.
    """
    client = get_client()
    try:
        client.delete_collection(name)               # rerun-safe: rebuild, never duplicate
    except NotFoundError:
        pass
    collection = client.create_collection(
        name,
        configuration={"hnsw": {"space": "cosine"}},
        metadata={"embedding_model": MODEL_NAME, "doc_prefix": DOC_PREFIX,
                  "query_prefix": QUERY_PREFIX, "embedded_field": field, "source_file": path},
        embedding_function=None)                     # we always pass our own vectors

    chunks = [json.loads(line) for line in Path(path).open(encoding="utf-8")]
    texts = [c[field] for c in chunks]
    start = time.perf_counter()
    vectors = load_model(MODEL_NAME).encode([DOC_PREFIX + t for t in texts],
                                            batch_size=BATCH_SIZE, normalize_embeddings=True,
                                            show_progress_bar=True)
    seconds = time.perf_counter() - start
    collection.add(
        ids=[c["chunk_id"] for c in chunks],
        documents=texts,
        embeddings=vectors.tolist(),
        metadatas=[{k: c[k] if c[k] is not None else "" for k in METADATA_FIELDS}
                   for c in chunks])                 # Chroma rejects None values
    print(f"{name}: {collection.count()} chunks embedded in {seconds:.0f}s "
          f"({seconds / len(chunks):.2f}s per chunk)")


def search(question, collection, k=5, where=None):
    """Top-k chunks for a question: dicts with rank, score, chunk_id, section, text, meta.

    `where` is a metadata filter like {"source": "cigna", "doc_type": "policy"};
    several keys are combined with AND. Score is cosine similarity (1 = same direction).
    """
    coll = get_client().get_collection(collection)
    model = load_model(coll.metadata["embedding_model"])
    query = model.encode([coll.metadata["query_prefix"] + question], normalize_embeddings=True)
    if where and len(where) > 1:
        where = {"$and": [{key: value} for key, value in where.items()]}
    result = coll.query(query_embeddings=query.tolist(), n_results=k, where=where,
                        include=["documents", "metadatas", "distances"])
    return [{"rank": rank, "score": 1 - distance, "chunk_id": chunk_id,
             "section": meta["section"], "text": doc, "meta": meta}
            for rank, (chunk_id, doc, meta, distance) in enumerate(
                zip(result["ids"][0], result["documents"][0], result["metadatas"][0],
                    result["distances"][0]), start=1)]


def print_results(question, results):
    """Print one question's hits: rank, score, chunk_id, section, first 150 characters."""
    print(f"\nQ: {question}")
    for r in results:
        snippet = " ".join(r["text"].split())[:150]
        print(f"  {r['rank']}. {r['score']:.3f}  {r['chunk_id']:<28} {r['section'][:60]}")
        print(f"       {snippet}")


def main():
    """Build all collections, then run the test questions against section_ctx."""
    model = load_model(MODEL_NAME)
    print(f"Model {MODEL_NAME}: max_seq_length={model.max_seq_length}, "
          f"dim={model.get_embedding_dimension()}")
    for name, (path, field) in COLLECTIONS.items():
        build_collection(name, path, field)

    for question in TEST_QUESTIONS:
        print_results(question, search(question, "section_ctx"))
    where = {"source": "cigna", "doc_type": "policy"}
    print(f"\n--- Same first question, filtered with where={where} ---")
    print_results(TEST_QUESTIONS[0], search(TEST_QUESTIONS[0], "section_ctx", where=where))


if __name__ == "__main__":
    main()
