# Evaluation run 20261104-203338

25 questions (4 unanswerable). Answers: claude-haiku-5-5 on section_ctx, filter on, k=8. Judge: claude-opus-5-5.

## Retrieval (answerable questions only)

| setup | hit@3 | hit@5 | hit@8 | recall@3 | recall@5 | recall@8 | MRR |
|---|---|---|---|---|---|---|---|
| section_ctx (filter) | 0.62 | 0.76 | 0.95 | 0.57 | 0.68 | 0.90 | 0.61 |
| section_ctx (no filter) | 0.48 | 0.57 | 0.71 | 0.43 | 0.49 | 0.66 | 0.47 |
| section_raw (filter) | 0.67 | 0.76 | 0.90 | 0.61 | 0.71 | 0.87 | 0.55 |
| section_raw (no filter) | 0.48 | 0.52 | 0.52 | 0.42 | 0.47 | 0.48 | 0.38 |
| fixed (filter) | 0.52 | 0.62 | 0.76 | 0.44 | 0.52 | 0.62 | 0.44 |
| fixed (no filter) | 0.29 | 0.43 | 0.52 | 0.21 | 0.33 | 0.40 | 0.28 |

hit@8 / MRR per category:

| category (n) | section_ctx (filter) | section_ctx (no filter) | section_raw (filter) | section_raw (no filter) | fixed (filter) | fixed (no filter) |
|---|---|---|---|---|---|---|
| comparison (3) | 0.67 / 0.67 | 0.67 / 0.67 | 0.67 / 0.67 | 0.67 / 0.67 | 1.00 / 0.44 | 1.00 / 0.44 |
| criteria (8) | 1.00 / 0.50 | 0.50 / 0.23 | 0.88 / 0.40 | 0.25 / 0.19 | 1.00 / 0.48 | 0.50 / 0.15 |
| duration (3) | 1.00 / 0.75 | 1.00 / 0.54 | 1.00 / 0.56 | 0.33 / 0.17 | 0.67 / 0.50 | 0.33 / 0.33 |
| formulary (3) | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 0.83 | 0.00 / 0.00 | 0.00 / 0.00 |
| label (2) | 1.00 / 0.56 | 1.00 / 0.56 | 1.00 / 0.60 | 1.00 / 0.60 | 0.50 / 0.50 | 0.50 / 0.50 |
| tricky (2) | 1.00 / 0.23 | 0.50 / 0.12 | 1.00 / 0.29 | 0.50 / 0.17 | 1.00 / 0.75 | 1.00 / 0.62 |

## Answers (main setup)

| grade | count |
|---|---|
| correct | 16 |
| partly | 4 |
| correctly_refused | 4 |
| wrongly_refused | 1 |

Grades per category:

| category | correct | partly | correctly_refused | wrongly_refused |
|---|---|---|---|---|
| comparison | 1 | 1 | 0 | 1 |
| criteria | 8 | 0 | 0 | 0 |
| duration | 2 | 1 | 0 | 0 |
| formulary | 2 | 1 | 0 | 0 |
| label | 2 | 0 | 0 | 0 |
| tricky | 1 | 1 | 0 | 0 |
| unanswerable | 0 | 0 | 4 | 0 |

Failures (retrieval = some evidence never reached the model; generation = all evidence was retrieved):

| id | grade | failure | evidence recall@8 | judge's reason |
|---|---|---|---|---|
| q02 | partly | generation | 1.00 | The answer correctly gives the 12-month duration but omits the required criteria: a diagnosis of active psoriatic arthritis and no combination use with another systemic targeted immunomodulator for the same indication. |
| q04 | partly | retrieval | 0.33 | The answer correctly gives the Prolia continuation criteria and excludes Xgeva indications, but it omits the initial approval indications (postmenopausal, male, and glucocorticoid-induced osteoporosis; bone loss with aromatase inhibitor or ADT therapy; RA bone erosion), saying they are not in the sources. |
| q15 | partly | generation | 1.00 | The answer correctly states that Praluent is NF (non-formulary) and not covered unless an exception is granted, though its opening 'Yes' is misleading; it omits the expected contrast that Repatha is Preferred Brand with PA and a quantity limit. |
| q17 | wrongly_refused | retrieval | 0.00 | The answer declines the comparison and gives neither expected threshold: Aetna's LDL-C >= 70 mg/dL or Cigna's >= 55 mg/dL after a maximally tolerated statin trial. |
| q19 | partly | retrieval | 0.50 | The answer gives Aetna's continuation criteria correctly but omits UnitedHealthcare's requirements (documented positive clinical response, label dosing, authorization up to 12 months), correctly noting they are not in its excerpt. |

All answers:

| id | category | grade | reason |
|---|---|---|---|
| q01 | criteria | correct | The answer includes every expected fact: the trial of one maximally tolerated statin for at least 8 continuous weeks, LDL-C remaining at or above 55 mg/dL, the statin-intolerance alternative (rhabdomyolysis or muscle symptoms on both atorvastatin and rosuvastatin), and Cigna's 2026-09-09 Repatha policy as the source, with the extra revision-history detail drawn accurately from S1. |
| q02 | duration | partly | The answer correctly gives the 12-month duration but omits the required criteria: a diagnosis of active psoriatic arthritis and no combination use with another systemic targeted immunomodulator for the same indication. |
| q03 | formulary | correct | The answer states tier PSP (Preferred Specialty Drugs), prior authorization, and a quantity limit of 1 syringe per 180 days, all matching the sources, and adds no invented claims. |
| q04 | tricky | partly | The answer correctly gives the Prolia continuation criteria and excludes Xgeva indications, but it omits the initial approval indications (postmenopausal, male, and glucocorticoid-induced osteoporosis; bone loss with aromatase inhibitor or ADT therapy; RA bone erosion), saying they are not in the sources. |
| q05 | unanswerable | correctly_refused | The answer states that no Humana policy is available, correctly lists Aetna and Cigna as the insurers with Repatha documents and mentions the FDA label, and does not present another insurer's criteria as Humana's. |
| q06 | criteria | correct | The answer includes all expected facts: history of ASCVD or a cardiovascular event, current LDL-C of at least 70 mg/dL, maximally tolerated statin therapy or statin intolerance, and 12-month approval; its extra details come from the sources. |
| q07 | criteria | correct | The answer includes all expected facts — one of the three diagnostic criteria, a prior IV or oral bisphosphonate trial (or another listed alternative), and 1-year approval — and its extra details are supported by the sources. |
| q08 | criteria | correct | The answer includes every expected fact (osteoporosis diagnosis, high fracture risk with the listed examples, FDA-labeled dosing, and authorization of no more than 12 months) and contradicts none. |
| q09 | criteria | correct | The answer includes every expected fact: age of at least 6, the under-18 weight thresholds of 20 kg for Otezla and 50 kg for Otezla XR, a rheumatologist or dermatologist prescriber, and 6-month initial approval, with nothing contradicted or invented. |
| q10 | criteria | correct | The answer includes all expected facts: prior biologic/targeted synthetic drug, OR inadequate response/intolerance/contraindication to methotrexate, leflunomide or another conventional synthetic drug, OR enthesitis, with 12-month adult approval, and invents nothing. |
| q11 | criteria | correct | The answer gives all three expected facts: a plaque psoriasis diagnosis, AND no combination with another systemic targeted immunomodulator, with 12-month authorization, and invents nothing. |
| q12 | criteria | correct | The answer gives all three expected criteria joined by OR (vertebral or hip fracture; T-score <= -2.5 or osteopenia with high FRAX; prior bisphosphonate failure or intolerance) and adds nothing unsupported. |
| q13 | duration | correct | The answer states the 12-month authorization for members continuing PCSK9 inhibitor therapy, which covers both expected facts, and it invents nothing. |
| q14 | duration | correct | The answer gives all three expected facts: documentation of positive clinical response, dosing per FDA-approved labeling, and authorization for no more than 12 months, with no contradictions or invented claims. |
| q15 | formulary | partly | The answer correctly states that Praluent is NF (non-formulary) and not covered unless an exception is granted, though its opening 'Yes' is misleading; it omits the expected contrast that Repatha is Preferred Brand with PA and a quantity limit. |
| q16 | formulary | correct | The answer includes the 60 tablets per 30 days quantity limit, the PSP tier, prior authorization and indication-based coverage for psoriasis and psoriatic arthritis, with nothing missing or invented. |
| q17 | comparison | wrongly_refused | The answer declines the comparison and gives neither expected threshold: Aetna's LDL-C >= 70 mg/dL or Cigna's >= 55 mg/dL after a maximally tolerated statin trial. |
| q18 | comparison | correct | The answer states both expected facts, Cigna's 6-month initial approval and UnitedHealthcare's 12-month initial authorization, and includes nothing contradicting or invented. |
| q19 | comparison | partly | The answer gives Aetna's continuation criteria correctly but omits UnitedHealthcare's requirements (documented positive clinical response, label dosing, authorization up to 12 months), correctly noting they are not in its excerpt. |
| q20 | label | correct | The answer gives both expected regimens (140 mg every 2 weeks or 420 mg once monthly), notes subcutaneous administration and cites the FDA label, with no invented claims. |
| q21 | label | correct | The answer includes all expected facts: 60 mg every 6 months, subcutaneous injection in the upper arm, thigh or abdomen given by a healthcare provider, and calcium 1000 mg plus at least 400 IU vitamin D daily, with the extra missed-dose detail supported by the sources. |
| q22 | tricky | correct | The answer names all four preferred products (Bildyos, Enoby, Prolia, Stoboclo) and says members on non-preferred biosimilars must switch unless they meet the Preferred Product Criteria; the extra details, including the noted discrepancy with S4's revision-history entry, are drawn from the sources. |
| q23 | unanswerable | correctly_refused | The answer correctly states there is no Nexletol policy and lists the Cigna policies that are available (Otezla, Prolia, Repatha) without substituting Repatha's criteria or inventing anything. |
| q24 | unanswerable | correctly_refused | The answer correctly says the sources lack Part D information, notes that the policy covers commercial plans and links only Part B criteria, and does not present commercial criteria as Part D coverage; its mention of an unseen Aetna formulary matches the expected note about a formulary and is not offered as an answer. |
| q25 | unanswerable | correctly_refused | The answer correctly says the sources give no copay amount, accurately adds the Preferred Brand tier, PA and quantity limit details from S1, and invents no dollar figure. |

## API cost

| step | model | input tokens | output tokens | USD |
|---|---|---|---|---|
| answer | claude-haiku-5-5 | 138,191 | 16,254 | 0.0219 |
| judge | claude-opus-5-5 | 149,775 | 2,893 | 0.6570 |
| total | | 287,966 | 19,147 | 0.6789 |

## Judge spot-check (5 random answers, seed 7)

### q02 (duration): How long is UnitedHealthcare's initial approval for Otezla in psoriatic arthritis?

**Judge: partly**: The answer correctly gives the 12-month duration but omits the required criteria: a diagnosis of active psoriatic arthritis and no combination use with another systemic targeted immunomodulator for the same indication.

UnitedHealthcare's initial authorization for Otezla in psoriatic arthritis is 12 months. The policy states that "Authorization will be issued for 12 months." [S1]

This comes from UnitedHealthcare's Otezla policy, effective 2026-02-01 [S1][S7].

### q05 (unanswerable): What is Humana's policy for Repatha?

**Judge: correctly_refused**: The answer states that no Humana policy is available, correctly lists Aetna and Cigna as the insurers with Repatha documents and mentions the FDA label, and does not present another insurer's criteria as Humana's.

I don't have a Humana policy for Repatha, and Humana doesn't appear in the knowledge base, so I can't say what its coverage rules are.

The knowledge base has Repatha coverage documents from two insurers:
- **Aetna:** formulary (2026-01-01) and policy (2025-01-01). None of these Aetna documents were included in your sources.
- **Cigna:** policy (2026-09-09). Your sources include excerpts from this policy.

If you want Humana's policy, you'd need to provide that document. I can answer questions about Cigna's Repatha policy from the excerpts you included, or about the FDA label.

### q11 (criteria): What are UnitedHealthcare's rules for starting Otezla in plaque psoriasis?

**Judge: correct**: The answer gives all three expected facts: a plaque psoriasis diagnosis, AND no combination with another systemic targeted immunomodulator, with 12-month authorization, and invents nothing.

For UnitedHealthcare's Otezla policy (effective 2/1/2026), initial authorization for plaque psoriasis requires both of the following criteria [S1]:

1. Diagnosis of plaque psoriasis
-AND-
2. The patient is not receiving Otezla or Otezla XR in combination with another systemic targeted immunomodulator for treatment of the same indication. The policy lists examples including adalimumab, Bimzelx, Cimzia, Cosentyx, Enbrel, Ilumya, Skyrizi, Siliq, Sotyktu, Taltz, Tremfya, and ustekinumab [S1].

Authorization is issued for 12 months [S1]. The policy's effective date is 2/1/2026 [S8].

### q13 (duration): If a patient is already on Repatha, how long does Aetna approve continued use?

**Judge: correct**: The answer states the 12-month authorization for members continuing PCSK9 inhibitor therapy, which covers both expected facts, and it invents nothing.

Under Aetna's Repatha clinical policy (dated 2025-01-01), authorization of **12 months** may be granted for members who are continuing therapy with a PCSK9 inhibitor [S1].

The excerpt does not list any additional continuation criteria, so I can't say what documentation or clinical conditions apply at renewal.

### q21 (label): How often is Prolia given, and how?

**Judge: correct**: The answer includes all expected facts: 60 mg every 6 months, subcutaneous injection in the upper arm, thigh or abdomen given by a healthcare provider, and calcium 1000 mg plus at least 400 IU vitamin D daily, with the extra missed-dose detail supported by the sources.

Prolia is given as a single 60 mg subcutaneous injection once every 6 months. It should be administered by a healthcare provider, in the upper arm, upper thigh, or abdomen [S2][S8]. All patients should also receive calcium 1000 mg daily and at least 400 IU vitamin D daily [S2][S8].

If a dose is missed, the injection should be given as soon as the patient is available, and then injections scheduled every 6 months from the date of the last injection [S2][S1].

Source note: these answers come from the FDA prescribing label (revised 2026-06-01). I don't have an insurer policy or formulary for Prolia in these sources, so this does not describe any insurer's coverage rules.

