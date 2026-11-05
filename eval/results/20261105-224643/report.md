# Evaluation run 20261105-224643

27 questions (4 unanswerable). Answers: claude-haiku-5-5 on section_ctx, filter on, k=8. Judge: claude-opus-5-5.

## Retrieval (answerable questions only)

| setup | hit@3 | hit@5 | hit@8 | recall@3 | recall@5 | recall@8 | MRR |
|---|---|---|---|---|---|---|---|
| section_ctx (filter) | 0.57 | 0.70 | 0.91 | 0.54 | 0.64 | 0.83 | 0.56 |
| section_ctx (no filter) | 0.43 | 0.52 | 0.70 | 0.39 | 0.45 | 0.62 | 0.43 |
| section_raw (filter) | 0.61 | 0.70 | 0.83 | 0.56 | 0.64 | 0.81 | 0.51 |
| section_raw (no filter) | 0.43 | 0.48 | 0.48 | 0.38 | 0.43 | 0.44 | 0.35 |
| fixed (filter) | 0.57 | 0.61 | 0.70 | 0.45 | 0.50 | 0.57 | 0.40 |
| fixed (no filter) | 0.26 | 0.39 | 0.48 | 0.19 | 0.30 | 0.37 | 0.25 |

hit@8 / MRR per category:

| category (n) | section_ctx (filter) | section_ctx (no filter) | section_raw (filter) | section_raw (no filter) | fixed (filter) | fixed (no filter) |
|---|---|---|---|---|---|---|
| comparison (3) | 0.67 / 0.67 | 0.67 / 0.67 | 0.67 / 0.67 | 0.67 / 0.67 | 1.00 / 0.47 | 1.00 / 0.44 |
| criteria (8) | 1.00 / 0.50 | 0.50 / 0.23 | 0.88 / 0.40 | 0.25 / 0.19 | 1.00 / 0.48 | 0.50 / 0.15 |
| drug_comparison (2) | 0.50 / 0.07 | 0.50 / 0.06 | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.00 |
| duration (3) | 1.00 / 0.75 | 1.00 / 0.54 | 1.00 / 0.56 | 0.33 / 0.17 | 0.67 / 0.50 | 0.33 / 0.33 |
| formulary (3) | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 0.83 | 0.00 / 0.00 | 0.00 / 0.00 |
| label (2) | 1.00 / 0.56 | 1.00 / 0.56 | 1.00 / 0.60 | 1.00 / 0.60 | 0.50 / 0.50 | 0.50 / 0.50 |
| tricky (2) | 1.00 / 0.23 | 0.50 / 0.12 | 1.00 / 0.29 | 0.50 / 0.17 | 1.00 / 0.75 | 1.00 / 0.62 |

## Answers (main setup)

| grade | count |
|---|---|
| correct | 17 |
| partly | 4 |
| wrong | 1 |
| correctly_refused | 4 |
| wrongly_refused | 1 |

Grades per category:

| category | correct | partly | wrong | correctly_refused | wrongly_refused |
|---|---|---|---|---|---|
| comparison | 1 | 1 | 0 | 0 | 1 |
| criteria | 8 | 0 | 0 | 0 | 0 |
| drug_comparison | 0 | 2 | 0 | 0 | 0 |
| duration | 3 | 0 | 0 | 0 | 0 |
| formulary | 2 | 0 | 1 | 0 | 0 |
| label | 2 | 0 | 0 | 0 | 0 |
| tricky | 1 | 1 | 0 | 0 | 0 |
| unanswerable | 0 | 0 | 0 | 4 | 0 |

Failures (retrieval = some evidence never reached the model; generation = all evidence was retrieved):

| id | grade | failure | evidence recall@8 | judge's reason |
|---|---|---|---|---|
| q04 | partly | retrieval | 0.33 | The answer gives the continuation criteria correctly but states that the initial-approval criteria are not in the sources, so it omits the Prolia indications (postmenopausal osteoporosis, male osteoporosis, glucocorticoid-induced osteoporosis, AI/ADT bone loss, RA bone erosion). |
| q15 | wrong | generation | 1.00 | The answer opens with "Yes," implying Praluent is on the formulary, which reverses the main point: Praluent is non-formulary (NF) and not covered unless an exception is granted, even though the answer later states the NF tier and the Repatha comparison correctly. |
| q17 | wrongly_refused | retrieval | 0.00 | The question is answerable, but the answer says the sources don't allow a comparison and gives none of the expected facts: Aetna's LDL-C ≥70 mg/dL for ASCVD, Cigna's ≥55 mg/dL after a statin trial, or that Aetna's bar is higher. |
| q19 | partly | retrieval | 0.50 | The answer gives Aetna's continuation criteria correctly but omits UnitedHealthcare's requirements (documented positive clinical response, dosing per label, authorization up to 12 months), saying these were not in the retrieved sources; nothing it states is false. |
| q26 | partly | retrieval | 0.00 | The answer correctly gives Repatha's CV-risk indication, Prolia's osteoporosis use and its 6-month schedule, but it omits the mechanisms (PCSK9 inhibitor/LDL-C lowering; RANKL inhibitor), Repatha's 140 mg every 2 weeks or 420 mg monthly schedule, and Prolia's 60 mg dose. |
| q27 | partly | retrieval | 0.33 | The answer correctly reports that Cigna removed Repatha's specialist-prescriber requirement and that the Prolia excerpts state no such requirement, but it omits the expected fact that Otezla requires a rheumatologist and/or dermatologist prescriber, saying instead that the sources don't address it. |

All answers:

| id | category | grade | reason |
|---|---|---|---|
| q01 | criteria | correct | The answer includes every expected fact: a trial of one maximally tolerated statin for at least 8 continuous weeks, LDL-C still >= 55 mg/dL afterward, the statin-intolerance alternative (rhabdomyolysis or muscle symptoms on both atorvastatin and rosuvastatin), and the Cigna 2026-09-09 policy as source; its added caveats about other indications are accurate and drawn from the sources. |
| q02 | duration | correct | The answer states the 12-month initial authorization for psoriatic arthritis, matching the expected fact with nothing invented. |
| q03 | formulary | correct | The answer gives all three expected facts: tier PSP (Preferred Specialty Drugs), prior authorization, and a quantity limit of 1 syringe per 180 days, and the extra precertification detail is supported by S2. |
| q04 | tricky | partly | The answer gives the continuation criteria correctly but states that the initial-approval criteria are not in the sources, so it omits the Prolia indications (postmenopausal osteoporosis, male osteoporosis, glucocorticoid-induced osteoporosis, AI/ADT bone loss, RA bone erosion). |
| q05 | unanswerable | correctly_refused | The answer correctly says no Humana Repatha policy is available, lists Aetna, Cigna and the FDA label as the available documents, and does not present another insurer's criteria as Humana's. |
| q06 | criteria | correct | The answer includes all expected facts (ASCVD history or cardiovascular event, LDL-C >= 70 mg/dL, maximally tolerated statin or statin intolerance, 12-month approval), and the extra formulary and continuation details are supported by the sources. |
| q07 | criteria | correct | The answer gives all three expected facts: one of the T-score, fracture or low-bone-mass-with-high-risk criteria, a prior IV or oral bisphosphonate trial with inadequate efficacy or intolerance among other options, and 1-year approval, with all extra details supported by the sources. |
| q08 | criteria | correct | The answer includes all expected facts: an osteoporosis diagnosis, high fracture risk with the listed examples, dosing per FDA labeling, and authorization for no more than 12 months. |
| q09 | criteria | correct | The answer includes every expected fact (age ≥6, the under-18 weight thresholds for Otezla and Otezla XR, a rheumatologist or dermatologist prescriber, and 6-month initial approval) with nothing false or invented. |
| q10 | criteria | correct | The answer gives all expected facts: prior biologic or targeted synthetic drug, or inadequate response, intolerance or contraindication to conventional synthetic drugs, or enthesitis, with 12-month authorization; the extra details all come from the sources. |
| q11 | criteria | correct | The answer gives all three expected facts — a plaque psoriasis diagnosis, AND no use with another systemic targeted immunomodulator for the same indication, and a 12-month authorization — with nothing invented. |
| q12 | criteria | correct | The answer gives all three expected criteria with the correct ANY logic: a vertebral or hip fracture, a T-score of -2.5 or lower or osteopenia with high FRAX, and an inadequate response or intolerance to bisphosphonates, and it invents nothing. |
| q13 | duration | correct | The answer states the 12-month authorization for members continuing PCSK9i therapy, covering both expected facts, and its extra details (outpatient place of service, formulary PA and quantity limit) are drawn from the sources. |
| q14 | duration | correct | The answer includes all three expected facts (positive clinical response, FDA-labeled dosing, and authorization for no more than 12 months) with correct AND logic and invents nothing. |
| q15 | formulary | wrong | The answer opens with "Yes," implying Praluent is on the formulary, which reverses the main point: Praluent is non-formulary (NF) and not covered unless an exception is granted, even though the answer later states the NF tier and the Repatha comparison correctly. |
| q16 | formulary | correct | The answer gives every expected fact: the limit of 60 tablets per 30 days, the PSP tier, the PA requirement and indication-based coverage as the preferred agent for psoriasis and psoriatic arthritis, all matching S1. |
| q17 | comparison | wrongly_refused | The question is answerable, but the answer says the sources don't allow a comparison and gives none of the expected facts: Aetna's LDL-C ≥70 mg/dL for ASCVD, Cigna's ≥55 mg/dL after a statin trial, or that Aetna's bar is higher. |
| q18 | comparison | correct | The answer states both expected facts, Cigna's 6-month initial approval and UnitedHealthcare's 12-month initial authorization, with no contradictions or invented claims. |
| q19 | comparison | partly | The answer gives Aetna's continuation criteria correctly but omits UnitedHealthcare's requirements (documented positive clinical response, dosing per label, authorization up to 12 months), saying these were not in the retrieved sources; nothing it states is false. |
| q20 | label | correct | The answer gives both dosing options (140 mg every 2 weeks or 420 mg once monthly), states they are given subcutaneously, and cites the FDA label, with nothing invented. |
| q21 | label | correct | The answer includes every expected fact: 60 mg every 6 months, a subcutaneous injection in the upper arm, thigh or abdomen given by a healthcare provider, and daily calcium 1000 mg plus at least 400 IU vitamin D, with nothing false or invented. |
| q22 | tricky | correct | The answer names Bildyos, Enoby, Prolia and Stoboclo as preferred and says members on non-preferred products must switch unless they meet the Preferred Product Criteria, with all extra details supported by the sources. |
| q23 | unanswerable | correctly_refused | The answer correctly states there is no Cigna Nexletol policy, lists the available Cigna policies (Repatha, Prolia, Otezla) with dates matching the sources, and does not substitute Repatha's criteria. |
| q24 | unanswerable | correctly_refused | The answer correctly states the sources contain no Medicare Part D information for Prolia, notes the policy covers only commercial plans and references Part B rather than Part D, and does not present commercial criteria as Part D coverage. |
| q25 | unanswerable | correctly_refused | The answer correctly states that the sources give no copay amount and accurately adds the PB tier, PA and quantity limits from S1 without inventing any dollar figure. |
| q26 | drug_comparison | partly | The answer correctly gives Repatha's CV-risk indication, Prolia's osteoporosis use and its 6-month schedule, but it omits the mechanisms (PCSK9 inhibitor/LDL-C lowering; RANKL inhibitor), Repatha's 140 mg every 2 weeks or 420 mg monthly schedule, and Prolia's 60 mg dose. |
| q27 | drug_comparison | partly | The answer correctly reports that Cigna removed Repatha's specialist-prescriber requirement and that the Prolia excerpts state no such requirement, but it omits the expected fact that Otezla requires a rheumatologist and/or dermatologist prescriber, saying instead that the sources don't address it. |

## API cost

| step | model | input tokens | output tokens | USD |
|---|---|---|---|---|
| answer | claude-haiku-5-5 | 155,679 | 20,024 | 0.0256 |
| judge | claude-opus-5-5 | 167,519 | 3,376 | 0.7376 |
| total | | 323,198 | 23,400 | 0.7632 |

## Judge spot-check (5 random answers, seed 7)

### q02 (duration): How long is UnitedHealthcare's initial approval for Otezla in psoriatic arthritis?

**Judge: correct**: The answer states the 12-month initial authorization for psoriatic arthritis, matching the expected fact with nothing invented.

UnitedHealthcare's initial authorization for Otezla in psoriatic arthritis is for 12 months. [S1] This is from UnitedHealthcare's Otezla policy, effective 2026-02-01. [S1][S7]

### q05 (unanswerable): What is Humana's policy for Repatha?

**Judge: correctly_refused**: The answer correctly says no Humana Repatha policy is available, lists Aetna, Cigna and the FDA label as the available documents, and does not present another insurer's criteria as Humana's.

I don't have a policy for Humana for Repatha, so I can't say what Humana's coverage rules are.

The Repatha documents I have are from:
- **Aetna**: formulary (2026-01-01) and policy (2025-01-01)
- **Cigna**: policy (2026-09-09)
- **FDA**: label (2026-10-01)

The FDA label is not an insurer policy. If you need Humana's Repatha coverage, you would need Humana's own policy or formulary document.

### q11 (criteria): What are UnitedHealthcare's rules for starting Otezla in plaque psoriasis?

**Judge: correct**: The answer gives all three expected facts — a plaque psoriasis diagnosis, AND no use with another systemic targeted immunomodulator for the same indication, and a 12-month authorization — with nothing invented.

For UnitedHealthcare's Otezla policy (effective 2/1/2026), initial authorization for plaque psoriasis requires both of the following [S1][S8]:

1. Diagnosis of plaque psoriasis
-AND-
2. The patient is not receiving Otezla or Otezla XR in combination with another systemic targeted immunomodulator for treatment of the same indication. The policy's examples include adalimumab, Bimzelx, Cimzia, Cosentyx, Enbrel, Ilumya, Skyrizi, Siliq, Sotyktu, Taltz, Tremfya, and ustekinumab [S1].

If approved, authorization is issued for 12 months [S1].

### q13 (duration): If a patient is already on Repatha, how long does Aetna approve continued use?

**Judge: correct**: The answer states the 12-month authorization for members continuing PCSK9i therapy, covering both expected facts, and its extra details (outpatient place of service, formulary PA and quantity limit) are drawn from the sources.

Under Aetna's Repatha clinical policy (version dated 2025-01-01), continued use is approved for 12 months. The policy states: "Authorization of 12 months may be granted for members who are continuing therapy with a PCSK9i." [S1] The approval is discretionary ("may be granted"), and the place of service is outpatient. [S1]

The retrieved sources don't list the specific criteria a member must meet to qualify for continuation, so I can't say what those are. The Aetna 2026 formulary entries for Repatha show prior authorization and a quantity limit of 3 syringes or pens per 28 days, but they don't state an approval duration. [S5]

### q21 (label): How often is Prolia given, and how?

**Judge: correct**: The answer includes every expected fact: 60 mg every 6 months, a subcutaneous injection in the upper arm, thigh or abdomen given by a healthcare provider, and daily calcium 1000 mg plus at least 400 IU vitamin D, with nothing false or invented.

Prolia is given as a **60 mg single subcutaneous injection once every 6 months** [S2][S8]. It must be administered by a healthcare provider [S2][S8], in the upper arm, upper thigh, or abdomen [S2][S8].

If a dose is missed, give it as soon as the patient is available, then schedule injections every 6 months from the date of the last injection [S2]. Patients should also receive calcium 1000 mg daily and at least 400 IU of vitamin D daily [S2].

These details come from the FDA label (revised 6/2026) [S2][S8]. The retrieved sources did not include any insurer coverage policy for Prolia, so I can't say how any insurer's coverage criteria apply to this dosing.

