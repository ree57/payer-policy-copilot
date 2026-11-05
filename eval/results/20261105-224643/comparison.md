# Comparison: 20261104-205239 -> 20261105-224643

Answering setup (collection, filter, rerank): before ('section_ctx', True, False), after ('section_ctx', True, False); k=8.

## Retrieval, all answerable questions

| run | hit@3 | hit@5 | hit@8 | recall@3 | recall@5 | recall@8 | MRR |
|---|---|---|---|---|---|---|---|
| before | 0.62 | 0.76 | 0.95 | 0.60 | 0.71 | 0.90 | 0.61 |
| after | 0.62 | 0.76 | 0.95 | 0.60 | 0.71 | 0.90 | 0.61 |

## Retrieval, comparison questions

| run | hit@3 | hit@5 | hit@8 | recall@3 | recall@5 | recall@8 | MRR |
|---|---|---|---|---|---|---|---|
| before | 0.67 | 0.67 | 0.67 | 0.50 | 0.50 | 0.50 | 0.67 |
| after | 0.67 | 0.67 | 0.67 | 0.50 | 0.50 | 0.50 | 0.67 |

Questions whose hit@8 / recall@8 changed: none

## Answer grades

| grade | before | after |
|---|---|---|
| correct | 17 | 17 |
| partly | 2 | 2 |
| wrong | 1 | 1 |
| correctly_refused | 4 | 4 |
| wrongly_refused | 1 | 1 |
| **correct + correctly_refused** | **21** | **21** |

## Questions whose grade changed

| id | before | after | cause | judge's reason now |
|---|---|---|---|---|

## Questions added since the earlier run

| id | grade | evidence recall@8 | judge's reason |
|---|---|---|---|
| q26 | partly | 0.00 | The answer correctly gives Repatha's CV-risk indication, Prolia's osteoporosis use and its 6-month schedule, but it omits the mechanisms (PCSK9 inhibitor/LDL-C lowering; RANKL inhibitor), Repatha's 140 mg every 2 weeks or 420 mg monthly schedule, and Prolia's 60 mg dose. |
| q27 | partly | 0.33 | The answer correctly reports that Cigna removed Repatha's specialist-prescriber requirement and that the Prolia excerpts state no such requirement, but it omits the expected fact that Otezla requires a rheumatologist and/or dermatologist prescriber, saying instead that the sources don't address it. |
