# KNHANES Nutrition Risk Prototype v1

KNHANES 2022-2024 기반 영양소 섭취 부족/과잉 위험 예측 연구 프로토타입.

## 현재 설계

- Train: 2022-2023
- Holdout test: 2024
- BMI: 최종 영양예측 predictor에서 제외
- PHQ-9: 영양예측 predictor에서 제외, 정신건강 프로파일용
- 고혈압/당뇨/이상지질혈증: 영양예측 predictor에서 제외, 결과 해석/subgroup용
- Outputs: 14 nutrient-risk models
- Vitamin C: Logistic Regression
- Others: HistGradientBoostingClassifier
- Risk bands: 2024 holdout 예측확률 tertile 기반 Low / Mid / High

## 중요 제한

현재 연구 모델의 식품군 predictor는 KNHANES의 `HEI_PROTF`, `HEI_DAIRY`입니다.
웹 설문에서는 사용성을 위해 `주당 섭취횟수 -> servings/day` 형태를 사용하기로 했지만,
이 값은 `HEI_PROTF/HEI_DAIRY`와 동일 변수가 아닙니다.

따라서 **웹 설문 serving 값을 모델에 직접 대입하면 안 됩니다.**
최종 배포 전 별도의 survey-to-training calibration/bridge validation이 필요합니다.

## 폴더

- `src/train.py`: prepared table에서 모델 재학습
- `src/predict.py`: 연구용 feature row 예측
- `src/survey_adapter.py`: 직접 변환 가능한 설문 파생변수 helper
- `config/features.json`: 최종 nutrition model input
- `config/targets.json`: 영양소 target mapping
- `config/risk_thresholds.json`: Low/Mid/High cutoff
- `config/survey_schema_v3.json`: 최종 설문 구조
- `models/`: 학습된 모델
- `reports/holdout_2024_metrics.csv`: BMI 제외 최종 모델 2024 holdout 성능

## 평균 holdout 성능

- Mean AUC: 0.7915
- Mean PR-AUC: 0.7785
- Mean Brier: 0.1574

## 해석 범위

이 모델은 영양결핍이나 질환 진단 모델이 아닙니다.
KNHANES 24시간 회상자료 기반의 **영양소 섭취 부족/과잉 위험 스크리닝 모델**입니다.
Low/Mid/High 역시 임상적 cutoff가 아니라 2024 예측확률 분포 기반 상대 위험군입니다.

## Git 시작 예시

```bash
git init
git add .
git commit -m "Add KNHANES nutrition risk prototype v1"
```
