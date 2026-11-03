# KNHANES Nutrition Service v1.2 FINAL FROZEN

## Final architecture

### 1. Lifestyle Risk Model
- Data: KNHANES 2022–2024
- Train: 2022–2023
- Independent holdout: 2024
- Inputs: service-only survey variables
- HEI_PROTF / HEI_DAIRY excluded
- Mean ROC-AUC: **0.665**
- Mean PR-AUC: **0.620**
- Mean Brier score: **0.191**
- Mean ECE: **0.023**
- 14 nutrient-risk outputs
- Role: 생활습관 기반의 보조적인 개인 영양위험 signal

### 2. Habitual Mini-FFQ Model
- Data: KNHANES 2012–2016 FFQ
- Train: 2012–2015
- Independent holdout: 2016
- Validated age: **19–64**
- Inputs:
  - sex
  - age
  - meat frequency
  - fish/seafood frequency
  - egg frequency
  - legumes/tofu/soy frequency
  - milk/dairy frequency
- Mean ROC-AUC: **0.877**
- Mean PR-AUC: **0.750**
- Mean Brier score: **0.106**
- Mean ECE: **0.025**
- Mean Accuracy: **0.780**
- Mean Sensitivity: **0.832**
- Mean Specificity: **0.761**
- Mean Precision: **0.623**
- Mean F1-score: **0.665**
- 10 nutrient-risk outputs
- Role: habitual dietary pattern 기반의 핵심 dietary risk signal

> Important: `Rich lifestyle + 5Q mean AUC ≈ 0.881`은 historical incremental analysis 결과이며,
> 실제 배포되는 mini-FFQ 모델의 성능값이 아님.
> 배포 mini-FFQ 모델은 `sex + age + 5Q`이며, independent 2016 holdout mean ROC-AUC는 **0.877**임.

### 3. Two-model operation policy
The two models are operated in parallel.

- Lifestyle Risk Model → 14 nutrient-risk outputs
- Habitual Mini-FFQ Model → 10 nutrient-risk outputs
- The two probabilities are **NOT averaged**
- They are displayed and interpreted as separate evidence sources

Example:

```text
Calcium
- Lifestyle Risk: Mid
- Habitual Diet Risk: High
```

The final service interprets agreement/disagreement between the two signals rather than producing a single averaged probability.

### 4. Target nutrients

#### Lifestyle Risk Model: 14 outputs
1. Protein
2. Calcium
3. Magnesium
4. Iron
5. Zinc
6. Phosphorus
7. Vitamin A
8. Vitamin B1
9. Vitamin B2
10. Folate
11. Vitamin C
12. Fiber
13. Potassium
14. Sodium excess

#### Habitual Mini-FFQ Model: 10 outputs
1. Protein
2. Calcium
3. Iron
4. Phosphorus
5. Vitamin B1
6. Vitamin B2
7. Vitamin C
8. Fiber
9. Potassium
10. Sodium excess

For the 10 overlapping nutrients, both Lifestyle and Habitual Diet signals can be shown.

For:
- Magnesium
- Zinc
- Vitamin A
- Folate

only the Lifestyle Risk signal is available.

### 5. Mini-FFQ 5 questions
- meat
- fish/seafood
- egg
- legumes/tofu/soy
- milk/dairy

Common response scale:

- 거의 먹지 않음
- 월 1–3회
- 주 1–2회
- 주 3–4회
- 주 5–6회
- 하루 1회
- 하루 2회
- 하루 3회 이상

### 6. Age fallback
- **19–64:** Lifestyle + Habitual Diet signals
- **65+:** Lifestyle only

The Habitual Mini-FFQ model is not applied to age 65+ because it was not validated in that age range.

### 7. Risk bands: Low / Mid / High

Each nutrient receives an individual model probability and is displayed as:

- **Low**: relatively low model-predicted risk
- **Mid**: intermediate model-predicted risk
- **High**: relatively high model-predicted risk

For mini-FFQ, Low/Mid/High thresholds are derived from nutrient-specific prediction distributions in the 2016 holdout cohort.

Important:
- Low/Mid/High are **relative model-risk bands**
- They are **not clinical deficiency cutoffs**
- Each nutrient can have a different probability cutoff
- Do not apply one universal `0.33 / 0.66` probability threshold to every nutrient

For sodium:
- `High` means **high risk of excessive sodium intake**
- For most other nutrients, `High` means **high risk of insufficient intake**

### 8. Binary validation threshold

Sensitivity, Specificity, Accuracy, Precision and F1 require a binary threshold.

For the final audit:
- each nutrient has its own threshold
- threshold was selected from the **training data**
- Youden J was used to choose the threshold
- the selected threshold was then applied to the independent holdout set

This binary validation threshold is separate from the service Low/Mid/High risk bands.

### 9. Final validation summary

| Model | ROC-AUC | PR-AUC | Brier | Accuracy | Sensitivity | Specificity | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Lifestyle Risk | 0.665 | 0.620 | 0.191 | 0.641 | 0.607 | 0.630 | 0.588 |
| Habitual Mini-FFQ | 0.877 | 0.750 | 0.106 | 0.780 | 0.832 | 0.761 | 0.665 |

### 10. Habitual Mini-FFQ nutrient-level ROC-AUC

| Nutrient | ROC-AUC |
|---|---:|
| Iron | 0.928 |
| Phosphorus | 0.923 |
| Protein | 0.908 |
| Calcium | 0.900 |
| Vitamin B1 | 0.900 |
| Vitamin B2 | 0.897 |
| Sodium excess | 0.870 |
| Potassium | 0.845 |
| Fiber | 0.834 |
| Vitamin C | 0.762 |

### 11. Subgroup robustness

Habitual Mini-FFQ mean ROC-AUC:

#### Sex
- Male: **0.888**
- Female: **0.864**

#### Age
- 19–29: **0.892**
- 30–39: **0.873**
- 40–49: **0.880**
- 50–64: **0.864**

No major performance collapse was observed across the tested sex and age subgroups.

### 12. Calibration
Calibration is evaluated using:
- Brier score
- ECE
- calibration intercept
- calibration slope

Habitual Mini-FFQ:
- Mean Brier score: **0.106**
- Mean ECE: **0.025**
- Mean calibration slope: approximately **1.08**

Lifestyle Risk:
- Mean Brier score: **0.191**
- Mean ECE: **0.023**
- Mean calibration slope: approximately **0.86**

### 13. Safety layers
- PHQ-9 is separate from nutrition prediction
- metabolic disease status is interpretive context
- supplement recommendation safety gate:
  - current supplements
  - pregnancy/breastfeeding
  - anticoagulant/aspirin
  - kidney disease/stones

These variables are not used as nutrient-risk predictors unless explicitly defined in the model feature set.

### 14. Cluster / NBTI
Cluster/NBTI is an independent explanatory layer.

- Cluster explains lifestyle/persona type
- Nutrition models predict individual nutrient risk
- Nutrition prediction does **not** depend on the cluster label
- Cluster probabilities or cluster IDs are not added to the nutrition-risk model

Recommended service structure:

```text
User survey
├─ Cluster / NBTI
│  └─ lifestyle-type explanation
│
├─ Lifestyle Risk Model
│  └─ 14 nutrient-risk signals
│
└─ Habitual Mini-FFQ Model
   └─ 10 nutrient-risk signals
```

### 15. Individual output
For one user, the service can return nutrient-specific Low / Mid / High results.

Example:

```text
Protein              Lifestyle: Low    Habitual: Low
Calcium              Lifestyle: Mid    Habitual: High
Iron                 Lifestyle: Mid    Habitual: Mid
Phosphorus           Lifestyle: Low    Habitual: Low
Vitamin B1           Lifestyle: Mid    Habitual: Low
Vitamin B2           Lifestyle: Low    Habitual: Mid
Vitamin C            Lifestyle: High   Habitual: High
Fiber                Lifestyle: High   Habitual: High
Potassium            Lifestyle: Mid    Habitual: High
Sodium excess        Lifestyle: High   Habitual: Mid

Magnesium            Lifestyle: Mid
Zinc                 Lifestyle: Low
Vitamin A            Lifestyle: Mid
Folate               Lifestyle: High
```

The service should prioritize nutrients with consistent high-risk signals, but should not describe the result as a clinical diagnosis.

## Final model freeze

Version: **v1.2 FINAL FROZEN**

Frozen items:
- model architecture
- predictor feature sets
- target nutrients
- age fallback policy
- separate-signal operation
- Low/Mid/High interpretation policy
- validation framework

The nutrition model should not be modified further unless:
1. the project scope changes,
2. new validated data are added,
3. the survey questions materially change, or
4. a clearly defined model-retraining decision is made.

## Files
- `src/pipeline_v1_2_final.py`
- `config/service_features.json`
- `config/service_manifest.json`
- `config/mini_ffq_risk_thresholds.json`
- `config/supplement_safety_rules.json`
- `config/api_response_schema.json`
- `config/final_freeze_manifest.json`
- `FINAL_MODEL_FREEZE.md`
- `FINAL_VALIDATION_REPORT.md`
- `SURVEY_FINAL.md`
- `TEAM_RESPONSE_JAEJUN.md`
- `reports/final_audit/FINAL_module_summary.csv`
- `reports/final_audit/FINAL_per_nutrient_metrics.csv`
- `reports/final_audit/FINAL_subgroup_summary.csv`
- `reports/final_audit/FINAL_calibration_deciles.csv`

## Interpretation rule
Use:
- `섭취 부족 위험`
- `영양위험`
- `영양취약 가능성`

Do not describe model output as:
- clinical nutrient deficiency
- confirmed deficiency
- medical diagnosis
