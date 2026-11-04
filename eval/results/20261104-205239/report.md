# Evaluation run 20261104-205239

25 questions (4 unanswerable). Answers: claude-haiku-5-5 on section_ctx, filter on, k=8. Judge: claude-opus-5-5.

## Retrieval (answerable questions only)

| setup | hit@3 | hit@5 | hit@8 | recall@3 | recall@5 | recall@8 | MRR |
|---|---|---|---|---|---|---|---|
| section_ctx (filter) | 0.62 | 0.76 | 0.95 | 0.60 | 0.71 | 0.90 | 0.61 |
| section_ctx (no filter) | 0.48 | 0.57 | 0.71 | 0.43 | 0.49 | 0.66 | 0.47 |
| section_raw (filter) | 0.67 | 0.76 | 0.90 | 0.61 | 0.71 | 0.89 | 0.55 |
| section_raw (no filter) | 0.48 | 0.52 | 0.52 | 0.42 | 0.47 | 0.48 | 0.38 |
| fixed (filter) | 0.62 | 0.67 | 0.76 | 0.49 | 0.55 | 0.62 | 0.44 |
| fixed (no filter) | 0.29 | 0.43 | 0.52 | 0.21 | 0.33 | 0.40 | 0.28 |

hit@8 / MRR per category:

| category (n) | section_ctx (filter) | section_ctx (no filter) | section_raw (filter) | section_raw (no filter) | fixed (filter) | fixed (no filter) |
|---|---|---|---|---|---|---|
| comparison (3) | 0.67 / 0.67 | 0.67 / 0.67 | 0.67 / 0.67 | 0.67 / 0.67 | 1.00 / 0.47 | 1.00 / 0.44 |
| criteria (8) | 1.00 / 0.50 | 0.50 / 0.23 | 0.88 / 0.40 | 0.25 / 0.19 | 1.00 / 0.48 | 0.50 / 0.15 |
| duration (3) | 1.00 / 0.75 | 1.00 / 0.54 | 1.00 / 0.56 | 0.33 / 0.17 | 0.67 / 0.50 | 0.33 / 0.33 |
| formulary (3) | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 0.83 | 0.00 / 0.00 | 0.00 / 0.00 |
| label (2) | 1.00 / 0.56 | 1.00 / 0.56 | 1.00 / 0.60 | 1.00 / 0.60 | 0.50 / 0.50 | 0.50 / 0.50 |
| tricky (2) | 1.00 / 0.23 | 0.50 / 0.12 | 1.00 / 0.29 | 0.50 / 0.17 | 1.00 / 0.75 | 1.00 / 0.62 |

## Answers (main setup)

| grade | count |
|---|---|
| correct | 17 |
| partly | 2 |
| wrong | 1 |
| correctly_refused | 4 |
| wrongly_refused | 1 |

Grades per category:

| category | correct | partly | wrong | correctly_refused | wrongly_refused |
|---|---|---|---|---|---|
| comparison | 1 | 1 | 0 | 0 | 1 |
| criteria | 8 | 0 | 0 | 0 | 0 |
| duration | 3 | 0 | 0 | 0 | 0 |
| formulary | 2 | 0 | 1 | 0 | 0 |
| label | 2 | 0 | 0 | 0 | 0 |
| tricky | 1 | 1 | 0 | 0 | 0 |
| unanswerable | 0 | 0 | 0 | 4 | 0 |

Failures (retrieval = some evidence never reached the model; generation = all evidence was retrieved):

| id | grade | failure | evidence recall@8 | judge's reason |
|---|---|---|---|---|
| q04 | partly | retrieval | 0.33 | The answer gives the continuation criteria correctly but omits the initial approval indications (postmenopausal, male and glucocorticoid-induced osteoporosis, bone loss with aromatase-inhibitor or ADT therapy, rheumatoid arthritis bone erosion), saying they are not in the sources even though S6 lists several of them. |
| q15 | wrong | generation | 1.00 | The answer opens with 'Yes' and says Praluent 'is on the formulary', which reverses the main point: Praluent is listed as NF (non-formulary), not covered unless an exception is granted, even though the answer cites that tier and the Repatha comparison correctly. |
| q17 | wrongly_refused | retrieval | 0.00 | The answer says it cannot determine which bar is higher and omits both expected thresholds: Aetna's LDL-C ≥70 mg/dL for ASCVD and Cigna's LDL-C ≥55 mg/dL after a maximally tolerated statin; the extra details it gives are accurate to the sources. |
| q19 | partly | retrieval | 0.50 | The Aetna continuation criteria are given correctly, but the answer omits UnitedHealthcare's requirements (documented positive clinical response, dosing per label, authorization up to 12 months), saying they are not in the sources. |

All answers:

| id | category | grade | reason |
|---|---|---|---|
| q01 | criteria | correct | The answer includes every expected fact: the 8-week maximally tolerated statin trial, LDL-C remaining ≥ 55 mg/dL, both statin-intolerance alternatives, and the 2026-09-09 Cigna policy, with extra details that are all supported by the sources. |
| q02 | duration | correct | The answer correctly states the 12-month initial authorization from S1 and invents nothing; the added reauthorization detail is supported by S2. |
| q03 | formulary | correct | The answer states all three expected facts: Tier PSP (Preferred Specialty Drugs), prior authorization, and a quantity limit of 1 syringe per 180 days, with nothing invented. |
| q04 | tricky | partly | The answer gives the continuation criteria correctly but omits the initial approval indications (postmenopausal, male and glucocorticoid-induced osteoporosis, bone loss with aromatase-inhibitor or ADT therapy, rheumatoid arthritis bone erosion), saying they are not in the sources even though S6 lists several of them. |
| q05 | unanswerable | correctly_refused | The answer states that no Humana policy is available, lists Aetna and Cigna as the insurers that do have Repatha documents, and does not present any other insurer's criteria as Humana's; the version dates it gives presumably come from a knowledge-base listing and are not substantive coverage claims. |
| q06 | criteria | correct | The answer includes all expected facts (ASCVD or cardiovascular event history, LDL-C >= 70 mg/dL, maximally tolerated statin or statin intolerance, 12-month approval), and every extra detail is supported by the sources. |
| q07 | criteria | correct | The answer includes all expected facts: one of the three diagnostic criteria (T-score ≤ -2.5, osteoporotic/fragility fracture, or low bone mass with high fracture risk), the prior-therapy requirement (IV ibandronate/zoledronic acid or oral bisphosphonate with inadequate efficacy or intolerance, among other options), and the 1-year approval, with nothing contradicted or invented. |
| q08 | criteria | correct | The answer lists all expected initial-therapy criteria from S2 (osteoporosis diagnosis, high fracture risk with examples, FDA-labeled dosing, authorization up to 12 months) with nothing missing or invented. |
| q09 | criteria | correct | The answer includes all expected facts: age ≥ 6, the under-18 weight thresholds (≥ 20 kg for Otezla, ≥ 50 kg for Otezla XR), prescription by or with a rheumatologist or dermatologist, and 6-month initial approval, with no contradictions. |
| q10 | criteria | correct | The answer covers every expected fact: prior biologic or targeted synthetic drug, OR inadequate response or intolerance/contraindication to a conventional synthetic drug, OR enthesitis, with 12-month approval for adults, and it adds nothing unsupported. |
| q11 | criteria | correct | The answer includes all three expected facts (plaque psoriasis diagnosis, AND no combination with another systemic targeted immunomodulator for the same indication, 12-month authorization), and its extra detail is accurately drawn from the sources. |
| q12 | criteria | correct | The answer lists all three alternative (ANY-of) criteria: vertebral or hip fracture history, a T-score of -2.5 or lower or osteopenia with high FRAX, and inadequate response to or intolerance of bisphosphonates, with nothing contradicted or invented. |
| q13 | duration | correct | The answer gives the 12-month continuation approval and says it applies to members continuing PCSK9i therapy, matching both expected facts with nothing invented. |
| q14 | duration | correct | The answer includes all three expected facts: documented positive clinical response, dosing per FDA-approved labeling, and authorization for no more than 12 months; its caveat about other indications is cautious but invents nothing. |
| q15 | formulary | wrong | The answer opens with 'Yes' and says Praluent 'is on the formulary', which reverses the main point: Praluent is listed as NF (non-formulary), not covered unless an exception is granted, even though the answer cites that tier and the Repatha comparison correctly. |
| q16 | formulary | correct | The answer gives all the expected facts: 60 tablets per 30 days, PSP tier, prior authorization, and indication-based coverage preferred for psoriasis and psoriatic arthritis; its extra details come from the sources. |
| q17 | comparison | wrongly_refused | The answer says it cannot determine which bar is higher and omits both expected thresholds: Aetna's LDL-C ≥70 mg/dL for ASCVD and Cigna's LDL-C ≥55 mg/dL after a maximally tolerated statin; the extra details it gives are accurate to the sources. |
| q18 | comparison | correct | The answer gives both expected facts, Cigna's 6-month initial approval and UnitedHealthcare's 12-month initial authorization, with no contradictions or invented claims. |
| q19 | comparison | partly | The Aetna continuation criteria are given correctly, but the answer omits UnitedHealthcare's requirements (documented positive clinical response, dosing per label, authorization up to 12 months), saying they are not in the sources. |
| q20 | label | correct | The answer gives both expected regimens (140 mg every 2 weeks or 420 mg once monthly), states they are given subcutaneously, and cites the FDA label, with nothing invented. |
| q21 | label | correct | The answer includes the 60 mg dose every 6 months, subcutaneous injection in the upper arm, thigh or abdomen given by a healthcare provider, and daily calcium 1000 mg plus at least 400 IU vitamin D, with nothing invented. |
| q22 | tricky | correct | The answer gives all expected facts: the preferred products (Bildyos, Enoby, Prolia, Stoboclo), the required switch for members on non-preferred products, and the Preferred Product Criteria exception, and the discrepancy note it adds is accurately drawn from S4. |
| q23 | unanswerable | correctly_refused | The answer correctly states there is no Cigna Nexletol policy, lists the Cigna policies that are available (Otezla, Prolia, Repatha), and does not substitute Repatha's criteria or invent anything. |
| q24 | unanswerable | correctly_refused | The answer states that the sources contain no Medicare Part D information, correctly identifies the policy as covering commercial plans only, and does not present commercial criteria as Part D coverage. |
| q25 | unanswerable | correctly_refused | The answer correctly says the sources give no copay amount, adds the accurate PB tier, PA and quantity-limit details from S1, and invents no dollar figure. |

## API cost

| step | model | input tokens | output tokens | USD |
|---|---|---|---|---|
| answer | claude-haiku-5-5 | 140,043 | 17,359 | 0.0227 |
| judge | claude-opus-5-5 | 150,361 | 2,778 | 0.6570 |
| total | | 290,404 | 20,137 | 0.6797 |

## Judge spot-check (5 random answers, seed 7)

### q02 (duration): How long is UnitedHealthcare's initial approval for Otezla in psoriatic arthritis?

**Judge: correct**: The answer correctly states the 12-month initial authorization from S1 and invents nothing; the added reauthorization detail is supported by S2.

UnitedHealthcare's initial authorization for Otezla in psoriatic arthritis is 12 months. The policy (effective 2026-02-01) states that "Authorization will be issued for 12 months" [S1].

For context, the same policy's reauthorization for psoriatic arthritis also runs 12 months [S2].

### q05 (unanswerable): What is Humana's policy for Repatha?

**Judge: correctly_refused**: The answer states that no Humana policy is available, lists Aetna and Cigna as the insurers that do have Repatha documents, and does not present any other insurer's criteria as Humana's; the version dates it gives presumably come from a knowledge-base listing and are not substantive coverage claims.

I don't have Humana's policy for Repatha. Humana doesn't appear in the knowledge base, so I can't answer from any Humana document.

For Repatha, the knowledge base includes these insurer documents:
- Aetna: formulary (version 2026-01-01) and policy (version 2025-01-01)
- Cigna: policy (version 2026-09-09)

The sources I was given include only Cigna's Repatha policy and FDA labeling, not Aetna's documents, so I can't summarize the Aetna policy here. If you want Humana's coverage rules, you'd need to check Humana's own documentation.

### q11 (criteria): What are UnitedHealthcare's rules for starting Otezla in plaque psoriasis?

**Judge: correct**: The answer includes all three expected facts (plaque psoriasis diagnosis, AND no combination with another systemic targeted immunomodulator for the same indication, 12-month authorization), and its extra detail is accurately drawn from the sources.

Under UnitedHealthcare's Otezla policy (effective 2026-02-01), Otezla or Otezla XR is approved for initial plaque psoriasis treatment based on **both** of the following criteria [S1]:

1. Diagnosis of plaque psoriasis
**-AND-**
2. Patient is not receiving Otezla or Otezla XR in combination with another systemic targeted immunomodulator for treatment of the same indication. The policy's examples include adalimumab, Bimzelx, Cimzia, Cosentyx, Enbrel, Ilumya, Skyrizi, Siliq, Sotyktu, Taltz, Tremfya, and ustekinumab [S1].

Authorization is issued for 12 months [S1].

The policy's change log says that in 11/2025 the plaque psoriasis criteria were updated to remove candidacy for phototherapy or systemic therapy [S5]. The initial criteria in S1 do not include that requirement.

### q13 (duration): If a patient is already on Repatha, how long does Aetna approve continued use?

**Judge: correct**: The answer gives the 12-month continuation approval and says it applies to members continuing PCSK9i therapy, matching both expected facts with nothing invented.

Aetna's Repatha clinical policy bulletin (policy dated 2025-01-01) states that authorization of 12 months may be granted for members who are continuing therapy with a PCSK9i [S1]. The policy's "Continuation of Therapy" section covers PCSK9 inhibitors generally, and the source does not separately name Repatha in that sentence [S1].

The sources do not cover any further conditions for continuation, such as renewal criteria or lab requirements.

### q21 (label): How often is Prolia given, and how?

**Judge: correct**: The answer includes the 60 mg dose every 6 months, subcutaneous injection in the upper arm, thigh or abdomen given by a healthcare provider, and daily calcium 1000 mg plus at least 400 IU vitamin D, with nothing invented.

Prolia is given as a single 60 mg subcutaneous injection once every 6 months, by a healthcare provider [S2][S8]. The FDA label (2026-06-01) is the only source here, so this is not an insurer policy answer.

- **Frequency:** Once every 6 months [S2]. Patients are counseled that they will receive it 1 time every 6 months [S4].
- **Route and site:** Subcutaneous injection in the upper arm, upper thigh, or abdomen [S2][S8].
- **Administration:** It "should be administered by a healthcare provider" [S2][S8].
- **Missed dose:** Give the injection as soon as the patient is available, then schedule injections every 6 months from the date of the last injection [S2].
- **Concurrent supplements:** All patients should receive calcium 1000 mg daily and at least 400 IU vitamin D daily [S2].

