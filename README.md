# Payer Policy Copilot

A retrieval-augmented chatbot that answers questions about US insurer coverage of three
Amgen drugs (Repatha, Prolia and Otezla) from the insurers' own policy documents, a
formulary extract and the FDA labels. Every answer cites the policy section it came from,
and the bot says so when the documents don't contain the answer. For market access work,
this turns "what does Cigna require before approving Repatha?" from a search through
several long PDFs into a cited answer with the policy date, which can be checked against
the source in one click.

## Live demo

**[payer-policy-copilot on Streamlit Community Cloud](https://payer-policy-copilot-37qjb6etypma8bigmygtbc.streamlit.app/)**
(password available on request).

It runs on free hosting: the first load after a period of inactivity can take 1-3 minutes
while the embedding model and search index load. After that, a typical answer takes a few
seconds.

## Architecture

```mermaid
flowchart LR
    A[12 PDFs] --> B[clean] --> C[parse] --> D[chunk] --> E[embed] --> F[retrieve] --> G[generate with citations]
```

| Step | What it does |
|---|---|
| clean | Removes browser print headers and billing-code tables from the source PDFs (done before this repo's pipeline). |
| parse (`parse.py`) | Extracts text page by page with PyMuPDF, removes repeated headers and footers, records each document's version date. |
| chunk (`chunk.py`) | Splits policies at their own section headings, keeps AND/OR criteria lists together, rebuilds formulary table rows as sentences. |
| embed (`embed.py`) | Embeds chunks with `nomic-ai/nomic-embed-text-v1.5` into a local Chroma index. |
| retrieve (`rag.py`) | Top 8 chunks, filtered by the insurer and drug named in the question; one search per insurer for comparisons. |
| generate (`rag.py`) | Claude Haiku 5.5 answers only from the numbered sources; code checks that every `[S#]` citation was retrieved. |
| app (`app.py`) | Streamlit chat with a sources panel, behind a password gate. |

## Data

| Insurer | Drug | Document | Pages | Version date |
|---|---|---|---|---|
| Aetna | Repatha | Coverage policy | 3 | 2025 (from file name) |
| Aetna | Prolia | Clinical policy bulletin | 61 | 2026-08-21 (policy history) |
| Aetna | Otezla | Coverage policy | 9 | 2024 (from file name) |
| Aetna | all three | 2026 Advanced Control Plan formulary (extract) | 5 | 2026 (from file name) |
| Cigna | Repatha | Prior authorization policy | 13 | 2026-09-09 (latest revision) |
| Cigna | Prolia | Drug coverage policy | 13 | 2026-09-01 (effective) |
| Cigna | Otezla | Prior authorization policy | 8 | 2026-07-01 (effective) |
| UnitedHealthcare | Prolia | Medical benefit drug policy | 7 | 2026-10-01 (effective) |
| UnitedHealthcare | Otezla | Coverage policy | 4 | 2026-02-01 (effective) |
| FDA | Repatha | Prescribing information | 95 | 2026-10 (revised) |
| FDA | Prolia | Prescribing information | 38 | 2026-06 (revised) |
| FDA | Otezla | Prescribing information | 66 | 2026-09 (revised) |

320 pages were kept after parsing (2 near-empty pages skipped), giving 389 section-aware
chunks. There is no UnitedHealthcare Repatha policy in the set.

**What isn't in this repo:** the source PDFs (they are the insurers' and FDA's documents,
so they are not redistributed here) and the search index. The app downloads its index and
chunk file at startup from a private Hugging Face dataset.

## Evaluation

### Test set

25 questions in `eval/questions.jsonl`, written the way an analyst would ask them rather
than in the documents' wording:

| Category | Questions | Example |
|---|---|---|
| Criteria | 8 | "For a postmenopausal woman with osteoporosis, what hoops does Cigna make her jump through before covering Prolia?" |
| Duration / renewal | 3 | "What does UnitedHealthcare need to renew Prolia, and for how long?" |
| Formulary | 3 | "Is Praluent on Aetna's 2026 formulary?" |
| Comparison | 3 | "Cigna versus UnitedHealthcare: how long is the first Otezla approval for psoriatic arthritis?" |
| Label | 2 | "How often is Prolia given, and how?" |
| Tricky | 2 | "What are Aetna's coverage criteria for Prolia, not Xgeva?" |
| Unanswerable | 4 | an insurer, a drug and a plan type we don't have, plus a copay amount that no document gives |

- Each answerable question lists 2-4 expected facts and 1-3 **evidence phrases** copied
  from the source chunks. `eval/check_evidence.py` verifies that every phrase appears in its
  expected document, in both chunking strategies, and in no more than 3 chunks (so generic
  phrases can't inflate retrieval scores).
- The expected answers for three of the hardest questions (two comparisons and the
  biosimilar question: q17, q18, q22) were checked against the source PDFs by hand.
- Answers are graded by an LLM judge (Claude Opus 5.5, stronger than the answering model)
  against the expected facts and the retrieved sources. Five randomly chosen grades (seed 7)
  were reviewed by hand; the one disagreement traced to an over-specified expected answer
  (q02), which was then corrected.

### Retrieval (21 answerable questions)

hit@8 = at least one evidence phrase in the top 8; recall@8 = share of evidence phrases
found; MRR = 1 / rank of the first hit.

| Setup | hit@3 | hit@8 | recall@8 | MRR |
|---|---|---|---|---|
| Section chunks + context line, **filter on (deployed setup)** | 0.62 | **0.95** | **0.90** | **0.61** |
| Section chunks + context line, no filter | 0.48 | 0.71 | 0.66 | 0.47 |
| Section chunks, no context line, no filter | 0.48 | 0.52 | 0.48 | 0.38 |
| Fixed-size chunks (500 tokens), no filter | 0.29 | 0.52 | 0.40 | 0.28 |

Source: `eval/results/20261104-205239/report.md`.

- **Chunking:** section-aware chunks beat fixed-size chunks (hit@8 0.71 vs 0.52, MRR 0.47 vs
  0.28). This comparison uses the **no-filter** rows on purpose: in the fixed-size set, the
  formulary chunks are labelled `drug = formulary` rather than a drug, so a drug filter can
  never reach them, which would penalise fixed-size chunking for a labelling reason.
- **Context line** (a header such as `[Cigna | Repatha | policy | 2026-09-09 | ...]` added to
  each chunk before embedding): hit@8 0.71 vs 0.52 without it.
- **Insurer/drug filter:** the largest single gain, hit@8 0.71 → 0.95.

### Answers (deployed setup)

| Grade | Count |
|---|---|
| Correct | 17 |
| Partly correct | 2 |
| Wrong | 1 |
| Correctly refused (unanswerable) | 4 |
| Wrongly refused | 1 |
| **Hallucinated** | **0** |

- All 4 unanswerable questions were refused without inventing an answer; for the missing
  insurer and drug, the bot listed the documents it does have.
- No answer cited a source that wasn't retrieved (0 invalid citations in both runs).
- 3 of the 4 failures are retrieval failures (the evidence never reached the model; the
  model said so rather than guessing). The fourth (q15) is an ambiguous question
  ("Is Praluent on the formulary?": it is listed, as non-formulary), flagged for rewording.

### Cost and speed

| | Per question |
|---|---|
| Answer (Claude Haiku 5.5) | about $0.0009 ($0.0227 for 25 questions) |
| Judge (Claude Opus 5.5, evaluation only) | about $0.026 ($0.657 for 25 questions) |
| End-to-end time, local CPU | median 3.4 s, p90 6.9 s (retrieval 0.05 s of that) |

## Experiments

| Change | Result | Decision |
|---|---|---|
| **Per-insurer retrieval** for comparison questions (one search per insurer, k split evenly) | Comparison recall@3 0.33 → 0.50; recall@8 unchanged at 0.50; no answer grade changed because of it. The right chunks rank too low *within* each insurer's documents, which splitting k can't fix. | Kept (no downside) |
| **Cross-encoder re-ranker** (`BAAI/bge-reranker-v2-m3`, 25 candidates) on the 3 retrieval failures | q04 evidence 1/3 → 2/3 (Prolia criteria moved from rank 18 to 1); q17 0/2 → 1/2; **q19 1/2 → 0/2**. 42-73 s per query on CPU; peak memory 1,640 → 2,912 MB. | Left off (code behind a flag) |

Details: `eval/results/20261104-205239/comparison.md` and
`eval/results/20261104-212605-rerank-probe/rerank_probe.md`.

## Engineering challenges

- **Boilerplate removal:** running headers and footers are detected by frequency, counting
  the top and bottom of each page separately, rather than hard-coded per insurer. A first
  version of the page-number rule also deleted 61 real numbers from the FDA labels,
  including the "60" in "60 mg/mL". The fix only removes a number that matches the page's
  own page number.
- **AND/OR criteria:** coverage criteria are nested lists ("ALL of i, ii and iii", where iii
  is "ONE of a or b"). The chunker splits at the policies' own headings and only cuts long
  sections between top-level list items, so a criterion stays with its condition.
- **Formulary tables:** plain text extraction put each table cell on its own line. The
  formulary is re-read with PyMuPDF's table detection and each row is rebuilt as one
  sentence, with codes expanded from the document's own legend ("QL (Quantity Limit) 1
  SYRINGE per 180 days").
- **Embedding model chosen by measurement:** with each model's own tokenizer, 43% of chunks
  exceeded bge-small's 512-token limit (text past the limit is silently dropped); none
  exceeded nomic-embed-text-v1.5's 8,192.
- **Deployment fixes:** CPU-only PyTorch via an extra package index (the default Linux wheel
  bundles CUDA), a SQLite shim because Streamlit Community Cloud's Debian 11 base ships
  SQLite 3.34 and Chroma needs 3.35+, and transformers pinned to 4.x because the
  embedding model's code calls an API removed in transformers 5.

## Limitations and next steps

- **Small test set:** 21 answerable questions, so one question is about 5 percentage
  points. A larger, held-out set built from real user questions is the next step.
- **Ranking within long documents:** the remaining failures are relevant chunks ranked
  just outside the top 8 (rank 5-21). A faster re-ranker or hybrid keyword + vector search
  are the next things to test.
- **Document coverage:** the Aetna Otezla policy is from 2024 and the Aetna Repatha policy
  from 2025; there is no UnitedHealthcare Repatha policy.
- **No follow-up memory:** each question is answered on its own.
- **Free hosting:** slow first load and shared CPU; the app sleeps after 12 hours without
  traffic.

## Run it locally

Requires Python 3.12+ and the source PDFs (not included) in `data/pdfs/`, named
`<source>__<drug>__<year or label>.pdf`.

```bash
py -m venv .venv
.venv\Scripts\python -m pip install -r requirements-dev.txt
```

Create a `.env` file (never commit it) with:

```
ANTHROPIC_API_KEY=...
APP_PASSWORD=...
```

Then run the pipeline in order:

```bash
.venv\Scripts\python parse.py                   # data/pages.jsonl
.venv\Scripts\python chunk.py                   # data/chunks.jsonl (section-aware)
.venv\Scripts\python chunk.py --strategy fixed  # data/chunks_fixed.jsonl (baseline)
.venv\Scripts\python embed.py                   # chroma_db/ (about 15 minutes on CPU)
.venv\Scripts\python rag.py "Does Cigna require a statin trial before approving Repatha?"
.venv\Scripts\streamlit run app.py
```

Evaluation: `eval\check_evidence.py` (free), then `eval\eval.py` (about $0.68 per full
run, mostly the judge) and `eval\compare.py <before> <after>`.

## Security

- **Password gate:** nothing renders until the password is entered; it is compared with
  `hmac.compare_digest`. Wrong passwords wait 2 seconds, and a session locks after 5 wrong
  attempts. The app refuses to start if no password is configured.
- **Usage caps:** 20 questions per browser session and 150 per day across all users (the
  daily counter resets when the server restarts).
- **Secrets:** API keys and the password live in the host's secrets settings, never in the
  repo; the git history was checked for keys, tokens, `.env` and data files.
- **Data access:** the search index sits in a private Hugging Face dataset, read with a
  fine-grained token that has read access to that one dataset only.

Not coverage or medical advice: answers reflect the listed documents as of their version
dates.
