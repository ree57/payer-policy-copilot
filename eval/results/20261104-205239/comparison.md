# Comparison: 20261104-203338 -> 20261104-205239

Main setup: section_ctx, filter on, k=8.

## Retrieval, all answerable questions

| run | hit@3 | hit@5 | hit@8 | recall@3 | recall@5 | recall@8 | MRR |
|---|---|---|---|---|---|---|---|
| before | 0.62 | 0.76 | 0.95 | 0.57 | 0.68 | 0.90 | 0.61 |
| after | 0.62 | 0.76 | 0.95 | 0.60 | 0.71 | 0.90 | 0.61 |

## Retrieval, comparison questions

| run | hit@3 | hit@5 | hit@8 | recall@3 | recall@5 | recall@8 | MRR |
|---|---|---|---|---|---|---|---|
| before | 0.67 | 0.67 | 0.67 | 0.33 | 0.33 | 0.50 | 0.67 |
| after | 0.67 | 0.67 | 0.67 | 0.50 | 0.50 | 0.50 | 0.67 |

Questions whose hit@8 / recall@8 changed: none

## Answer grades

| grade | before | after |
|---|---|---|
| correct | 16 | 17 |
| partly | 4 | 2 |
| wrong | 0 | 1 |
| correctly_refused | 4 | 4 |
| wrongly_refused | 1 | 1 |
| **correct + correctly_refused** | **20** | **21** |

## Questions whose grade changed

| id | before | after | cause | judge's reason now |
|---|---|---|---|---|
| q02 | partly | correct | expected facts | The answer correctly states the 12-month initial authorization from S1 and invents nothing; the added reauthorization detail is supported by S2. |
| q15 | partly | wrong | generation | The answer opens with 'Yes' and says Praluent 'is on the formulary', which reverses the main point: Praluent is listed as NF (non-formulary), not covered unless an exception is granted, even though the answer cites that tier and the Repatha comparison correctly. |
