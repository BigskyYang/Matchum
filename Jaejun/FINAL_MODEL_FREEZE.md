# FINAL MODEL FREEZE v1.2
- Lifestyle service: 2022–2023 train → 2024 holdout, 14 outputs, mean AUC 0.665
- Habitual mini-FFQ: 2012–2015 train → 2016 holdout, 10 outputs, mean AUC 0.877
- Binary threshold: nutrient-specific Youden J selected using TRAINING predictions only
- Low/Mid/High: relative risk bands, not clinical deficiency cutoffs
- 두 모듈 probability는 평균하지 않고 separate signals로 유지
- 본 버전에서 모델 구조와 feature set을 freeze
