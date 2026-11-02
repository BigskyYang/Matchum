# KNHANES Nutrition Risk Service Prototype v1

## 1. 프로젝트 목적

짧은 생활습관·식습관 설문으로 **영양소 섭취 부족/과잉 위험을 사전 스크리닝**하고,
생활유형·정신건강·대사건강 정보를 별도 해석 레이어로 함께 제공하는 프로토타입.

진단 모델이 아님.

---

## 2. 가장 중요한 수정사항

초기 Prototype은 `HEI_PROTF`, `HEI_DAIRY`를 사용했으나,
이 두 변수는 KNHANES 24시간 회상자료와 같은 날의 실제 식품섭취 정보에서 계산됨.

영양소 부족 target 역시 같은 날 24시간 회상 섭취량에서 만들어지므로,
웹 설문에서 기대할 수 있는 정보보다 강한 정보가 입력에 포함되어 있었음.

따라서 v1부터 모델을 두 가지로 분리함.

### A. Service survey-only model — 공식 서비스 모델
- 실제 웹 설문에서 직접 받을 수 있는 변수만 사용
- `HEI_PROTF`, `HEI_DAIRY` 제외
- 2022-2023 train / 2024 holdout
- 평균 AUC: **0.665**
- 평균 PR-AUC: **0.620**
- 평균 Brier: **0.191**

### B. Research full-information model — 연구용 benchmark
- `HEI_PROTF`, `HEI_DAIRY` 포함
- 평균 AUC: **0.792**
- 웹 서비스 성능으로 해석하지 않음
- full-information upper bound 비교용

---

## 3. 서비스 모델 입력

총 18개:
- 성별, 연령
- 흡연 여부/양
- 음주 여부/빈도/양
- 유산소 충족 여부
- 근력운동 일수
- 좌식시간
- 평균 수면시간
- 스트레스
- 아침/점심/저녁 빈도
- 외식 빈도
- 과일 빈도
- 채소 빈도

Q25 고기·생선·달걀·콩류 및 Q26 우유·유제품은 설문에는 유지하지만
현재 service model predictor에는 넣지 않음.

---

## 4. 출력 구조

```text
사용자 설문
   ├─ Nutrition ML (survey-only)
   │    └─ 14개 영양소 상대위험 Low/Mid/High
   │
   ├─ Lifestyle cluster / NBTI
   │    └─ 최종 군집모델 확정 후 연결
   │
   ├─ Mental health profile
   │    └─ PHQ-9
   │
   └─ Metabolic context
        └─ 고혈압 / 당뇨 / 이상지질혈증
```

각 레이어는 역할을 분리함.
정신건강·대사건강·군집 결과가 nutrition model의 예측확률을 임의로 변경하지 않음.

---

## 5. Risk band 수정

기존 full-information 모델의 2024 tertile cutoff는 사용하지 않음.

`Low / Mid / High`는 **새 survey-only 모델이 2024 holdout에서 만든 예측확률 분포**를 기준으로
영양소별 tertile을 새로 계산함.

따라서 service model과 risk band가 동일한 정보공간에서 정의됨.

---

## 6. 파일 구조

```text
src/
  preprocess_survey.py
  predict.py
  pipeline.py
  mental_health.py
  metabolic_context.py
  profile_layer.py

models/
  service/           <- 실제 서비스용 모델
  research_full/     <- 연구 benchmark

config/
  service_features.json
  service_risk_thresholds.json
  research_full_features.json
  ...

reports/
  service_2024_holdout_metrics.csv
  research_full_2024_holdout_metrics.csv
  service_vs_research_full.csv

research/
  README_FULL_INFORMATION.md
```

---

## 7. 현재 모델을 어떻게 설명할 것인가

권장:

> KNHANES 생활습관·식습관 설문정보만 사용한 서비스용 영양위험 모델을 구축하였으며,
> 2022-2023 학습, 2024 독립 검증에서 평균 AUC 약 0.66를 보였다.
> 같은 날 24시간 식품섭취 정보까지 활용한 연구용 full-information 모델의 성능은
> 약 0.79였으나, 이는 서비스 성능으로 사용하지 않는다.

금지:

> 웹 설문만으로 평균 AUC 0.79

---

## 8. 향후 개선 방향

큰 서비스 구조는 변경하지 않음.

1. Q25/Q26 habitual food-frequency 문항은 유지
2. 과거 KNHANES FFQ 등 외부 자료로 habitual frequency ↔ nutrient risk 관계 검증
3. 최소 추가 식품문항으로 service AUC가 얼마나 개선되는지 평가
4. 최종 lifestyle cluster/NBTI assignment 코드 연결
5. 필요 시 nutrient domain score 병행

현재 Git의 기본 inference path는 **survey-only service model**임.
