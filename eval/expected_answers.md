# Expected answers (written before running rag.py)

## Q1 Does Cigna require a statin trial before approving Repatha?
Yes, for initial therapy (Cigna Repatha PA policy, version 2026-09-09). For each indication
the patient must meet ONE of: (a) tried one maximally tolerated statin for >= 8 continuous
weeks AND LDL-C after that still above the indication's threshold (>= 55 mg/dL for the
established-CVD / MACE indication), OR (b) is statin-intolerant (statin-related
rhabdomyolysis, OR skeletal-related muscle symptoms meeting ALL of (a)(b)(c)).
Key chunks: cigna__repatha__2026#005 (MACE), #008 (HeFH), #011 (HoFH), #014 (hypercholesterolemia).
Correct = says yes, mentions the statin-intolerance alternative (OR), cites Cigna.

## Q2 How long is UnitedHealthcare's initial approval for Otezla in psoriatic arthritis?
12 months (UHC Otezla policy, effective 2026-02-01). Initial criteria: diagnosis of active
PsA AND not combined with another systemic targeted immunomodulator.
Key chunk: uhc__otezla__2026#003. Must NOT give Cigna's duration as UHC's.

## Q3 What tier is Prolia on Aetna's formulary, and what are its requirements?
Tier PSP (Preferred Specialty Drugs); requirements PA (prior authorization) and
QL (quantity limit) 1 syringe per 180 days. Aetna 2026 Advanced Control Plan formulary.
Key chunk: aetna__formulary__2026#002.

## Q4 What are Aetna's coverage criteria for Prolia, not Xgeva?
Aetna denosumab policy (version 2026-08-21), Prolia section. Initial approval for:
A. postmenopausal osteoporosis (fragility fracture history, OR T-score <= -2.5 / osteopenia
   with high FRAX plus one of: very high fracture risk, failed injectable therapy, failed
   oral bisphosphonate ...);
B. osteoporosis in men; C. glucocorticoid-induced osteoporosis (>= 2.5 mg/day prednisone
   for >= 3 months AND ...); D. breast cancer on aromatase inhibitor; E. prostate cancer on
   ADT; F. rheumatoid arthritis bone erosion. Continuation: < 24 months with no significant
   adverse events, OR >= 24 months with clinical benefit AND no adverse effects.
Key chunks: aetna__prolia__2026#003-#007. Must NOT include Xgeva indications (multiple
myeloma, bone metastases, giant cell tumor, hypercalcemia of malignancy, mastocytosis).
Partly correct if it lists the indications without the sub-criteria.

## Q5 What is Humana's policy for Repatha?
Correctly refused: no Humana policy in the sources; Repatha policies available from
Aetna (2025 file) and Cigna; FDA label also present. No UHC Repatha policy exists in our data.
Wrong if it describes Aetna's or Cigna's criteria as Humana's.
