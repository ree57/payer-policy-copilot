# Re-ranking probe: BAAI/bge-reranker-v2-m3

section_ctx, filters as rag.retrieve, k=8, 25 candidates per filter, max_length 1024, CPU.

| question | re-rank | seconds | evidence ranks in top 8 | recall@8 |
|---|---|---|---|---|
| q04 | off | 0.0 | -, -, 4 | 1/3 |
| q04 | on | 42.1 | 1, -, 6 | 2/3 |
| q17 | off | 0.1 | -, - | 0/2 |
| q17 | on | 55.4 | 5, - | 1/2 |
| q19 | off | 0.1 | 1, - | 1/2 |
| q19 | on | 73.0 | -, - | 0/2 |

- Re-ranker load time: 4 s (model already downloaded; the first-ever run also downloads about 2.3 GB).
- Peak memory: 1,640 MB with the embedding model only, 2,912 MB after re-ranking.

Decision: re-ranking stays off by default (known limitation). It moved q04's Prolia criteria to rank 1 and q17's Cigna threshold into the top 8, but q19 lost Aetna's chunk, and re-ranking takes about a minute per question on this CPU.

## End-to-end time without re-ranking (eval/timing.py, all 25 test questions)

- Per question (retrieval + answer): median 3.4 s, p90 6.9 s, max 7.6 s; retrieval alone median 0.05 s.
- Cold start (loading the embedding model): 8.5 s. Peak memory: 1,638 MB.
- With re-ranking, each question would add the re-rank time above (about 40-75 s) to this,
  and peak memory rises to about 2.9 GB. The full re-rank-on timing pass was not run.
- Raw numbers: timing_rerank_off.json.
