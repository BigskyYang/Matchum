# KNHANES Nutrition Service v1.2 FINAL

## Final architecture

### 1. Lifestyle risk
- Data: KNHANES 2022–2024
- Service-only survey variables
- HEI_PROTF / HEI_DAIRY excluded
- Mean AUC: ~0.665
- 14 nutrient-risk outputs

### 2. Habitual diet risk
- Data: KNHANES 2012–2016 ALL + FFQ
- Train: 2012–2015
- Independent validation: 2016
- Age: 19–64
- Inputs: 5 habitual food-frequency questions
- Rich lifestyle + 5Q mean AUC: ~0.881
- 10 nutrient-risk outputs

### 3. Output policy
The two probabilities are NOT averaged.
They are displayed as separate evidence sources.

### 4. Mini-FFQ 5 questions
- meat
- fish/seafood
- egg
- legumes/tofu/soy
- milk/dairy

### 5. Age fallback
- 19–64: lifestyle + habitual-diet signals
- 65+: lifestyle only

### 6. Safety layers
- PHQ-9 is separate from nutrition prediction
- metabolic disease status is interpretive context
- supplement recommendation safety gate:
  - current supplements
  - pregnancy/breastfeeding
  - anticoagulant/aspirin
  - kidney disease/stones

### 7. Risk bands
Mini-FFQ Low/Mid/High thresholds are derived from 2016 holdout prediction tertiles.
They are relative model-risk bands, not clinical deficiency cutoffs.

### 8. Cluster/NBTI
Cluster assignment is intentionally left as a hook until the team freezes:
- final `Micro_Cluster`
- final cluster names
- final preprocessing / model mapping

The nutrition service must not depend on the cluster label.

## Validation summary

| Model | Mean AUC |
|---|---:|
| Rich lifestyle only | 0.664 |
| Rich lifestyle + 3Q | 0.856 |
| Rich lifestyle + 5Q | 0.881 |

## Files
- `src/pipeline_v1_2_final.py`
- `config/mini_ffq_risk_thresholds.json`
- `config/supplement_safety_rules.json`
- `config/api_response_schema.json`
- `SURVEY_FINAL.md`
- `TEAM_RESPONSE_JAEJUN.md`
- validation reports under `reports/`

## Interpretation rule
Use “섭취 부족 위험” or “영양취약 가능성”.
Do not describe model output as a clinical nutrient deficiency diagnosis.
