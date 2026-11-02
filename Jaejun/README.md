# KNHANES 기반 영양위험 예측 모델 Prototype v1

## 1. 프로젝트 목적

국민건강영양조사(KNHANES) 2022–2024 데이터를 활용하여  
**사용자의 생활습관과 간단한 식습관 설문만으로 영양소 섭취 부족·과잉 위험을 예측하는 머신러닝 프로토타입**을 구축함.

본 모델은 영양결핍이나 질환을 진단하기 위한 모델이 아니라,  
사용자가 자신의 영양취약 가능성을 빠르게 확인할 수 있도록 하는 **저부담 스크리닝 모델**을 목표로 함.

---

## 2. 데이터 및 학습 구조

- 데이터: KNHANES 2022–2024 성인 자료
- 학습 데이터: 2022–2023
- 독립 검증 데이터: 2024
- 예측 대상: 14개 영양소의 섭취 부족 또는 과잉 위험

### 주요 예측 영양소

- 단백질
- 칼슘
- 마그네슘
- 철
- 아연
- 인
- 비타민 A
- 비타민 B1
- 비타민 B2
- 엽산
- 비타민 C
- 식이섬유
- 칼륨
- 나트륨 과잉

영양소별 위험 기준은 EAR, AI, CDRR 등 한국인 영양소 섭취기준을 기반으로 정의함.

---

## 3. 최종 입력 변수

최종 영양예측 모델에는 다음 생활습관 및 식습관 정보를 사용함.

### 기본정보
- 성별
- 나이

### 생활습관
- 현재 흡연 여부
- 하루 흡연량
- 음주 여부
- 음주 빈도
- 1회 음주량
- 유산소 운동 충족 여부
- 근력운동 일수
- 좌식시간
- 평균 수면시간
- 스트레스 수준

### 식사패턴
- 아침식사 빈도
- 점심식사 빈도
- 저녁식사 빈도
- 외식 빈도

### 식품섭취
- 채소 섭취빈도
- 과일 섭취빈도
- 고기·생선·달걀·콩류 섭취
- 우유·유제품 섭취

### 제외한 변수
- BMI는 ablation 및 feature importance 분석에서 예측 기여도가 매우 낮게 확인되어 최종 nutrition model predictor에서 제외함.
- PHQ-9은 영양예측 성능을 유의하게 개선하지 않아 predictor로 사용하지 않음.
- 고혈압, 당뇨병, 이상지질혈증 여부는 영양예측 predictor가 아니라 결과 해석 및 subgroup 분석용으로 사용함.

---

## 4. 모델 구조

영양소별로 별도의 이진 분류 모델을 구축함.

- 대부분의 영양소: `HistGradientBoostingClassifier`
- 비타민 C: `Logistic Regression`

예측 결과는 각 영양소별 위험 확률로 산출되며,  
2024 holdout 데이터의 예측확률 분포를 기준으로 `Low / Mid / High` 상대위험군을 구분함.

> Low / Mid / High는 임상적 cutoff가 아니라 KNHANES 기반 상대 위험등급임.

---

## 5. 최종 Prototype v1 성능

2022–2023 학습 → 2024 독립 검증 기준

- 평균 AUC: **0.7915**
- 평균 PR-AUC: **0.7785**
- 평균 Brier score: **0.1574**

### 대표 영양소 AUC

| 영양소 | AUC |
|---|---:|
| 인 | 0.920 |
| 단백질 | 0.913 |
| 철 | 0.860 |
| 아연 | 0.859 |
| 비타민 B2 | 0.824 |
| 칼슘 | 0.808 |
| 비타민 B1 | 0.774 |
| 마그네슘 | 0.767 |
| 칼륨 | 0.759 |
| 엽산 | 0.756 |
| 나트륨 과잉 | 0.751 |
| 비타민 A | 0.709 |
| 식이섬유 | 0.707 |
| 비타민 C | 0.672 |

모든 영양소가 동일한 예측력을 보이는 것은 아니므로,  
예측력이 높은 영양소는 개인화 결과에 적극적으로 활용하고 성능이 낮은 항목은 참고정보로 제공하는 방향임.

---

## 6. 현재까지 수행한 검증

### 6.1 독립연도 검증
- 2022–2023 학습
- 2024 독립 테스트
- 연도 기반 일반화 성능 확인

### 6.2 24시간 회상자료 robustness check
- 조사일 식사량이 “평소와 비슷했다”고 응답한 대상자만 별도 분석
- 전체 2024 표본과 비교해 AUC와 Brier가 거의 동일하게 유지됨

### 6.3 Subgroup validation
성별, 연령, BMI 그룹별로 모델 성능을 확인함.

- 성별·연령·BMI에 따라 전체 성능이 크게 무너지는 현상은 확인되지 않음
- 일부 영양소에서 특정 subgroup의 성능 저하가 관찰되어 해석 시 주의 필요

### 6.4 Ablation analysis
- 성별 제거: 성능 소폭 감소
- 나이 제거: 성능 소폭 감소
- BMI 제거: 성능 변화 거의 없음

→ 최종 모델에서는 성별·나이는 유지하고 BMI는 제외함.

### 6.5 Calibration
- 평균 ECE 약 0.019
- 14개 영양소 중 13개는 calibration 양호
- 비타민 A는 상대적으로 관찰이 필요한 수준

### 6.6 Feature importance / SHAP
주요 예측변수의 방향성과 중요도를 확인함.

대표적으로:

- 우유·유제품 → 칼슘 예측에 높은 기여
- 과일 섭취 → 비타민 C 예측에 높은 기여
- 고기·생선·달걀·콩류 → 단백질·철·아연 예측에 높은 기여

BMI보다 실제 식품섭취 정보가 핵심 predictor로 작동함을 확인함.

### 6.7 PHQ-9 추가 실험
2022 → 2024 동일표본에서

- 기존 모델
- 기존 모델 + PHQ-9 총점

을 비교함.

결과적으로 평균 AUC가 개선되지 않아 PHQ-9은 영양예측 predictor에서 제외함.

대신 PHQ-9은 별도의 정신건강 프로파일에 활용할 예정임.

---

## 7. 현재 서비스 설계

최종 사용자 결과는 다음 구조로 구성하는 것을 목표로 함.

```text
생활습관·식습관 설문
        │
        ├── 영양위험 예측 모델
        │      └─ 14개 영양소 Low / Mid / High
        │
        ├── 생활습관 군집화
        │      └─ Lifestyle subtype
        │
        ├── 스트레스 + PHQ-9
        │      └─ Mental health profile
        │
        └── 고혈압 / 당뇨 / 이상지질혈증
               └─ Metabolic health context

                     ↓

            최종 개인화 결과 / NBTI
```

생활습관 군집화와 NBTI는 영양예측 모델과 별도 레이어로 구성함.

---

## 8. 현재 한계 및 주의사항

### 8.1 진단 모델이 아님
본 모델은 실제 영양결핍 또는 질환을 진단하지 않음.

정확한 표현은:

> 생활습관 및 식습관을 기반으로 KNHANES에서 관찰된  
> 영양소 섭취 부족·과잉 위험 패턴을 예측하는 스크리닝 모델

임.

### 8.2 24시간 회상자료 기반
영양소 target은 KNHANES 24시간 회상자료의 1일 섭취량을 기반으로 함.

따라서 개인의 장기적인 habitual intake를 완벽히 대변하지는 않음.

### 8.3 웹 설문 serving과 학습변수 간 calibration 필요
현재 연구 모델에서 주요 식품군 변수는 KNHANES의

- `HEI_PROTF`
- `HEI_DAIRY`

를 사용함.

웹 설문에서는 사용 편의성을 위해

- 주당 고기·생선·달걀·콩류 섭취빈도
- 주당 우유·유제품 섭취빈도

를 받도록 설계함.

이 두 설문값은 `HEI_PROTF / HEI_DAIRY`와 동일한 변수가 아니므로,  
**실제 웹 배포 전 survey-to-training calibration 또는 bridge validation이 필요함.**

현재 Git 버전은 이 부분이 아직 남아 있는 연구용 Prototype v1임.

---

## 9. Repository 구조

```text
.
├─ README.md
├─ SURVEY_V3.md
├─ requirements.txt
├─ config/
│  ├─ features.json
│  ├─ targets.json
│  ├─ risk_thresholds.json
│  ├─ model_manifest.json
│  └─ survey_schema_v3.json
├─ src/
│  ├─ train.py
│  ├─ predict.py
│  └─ survey_adapter.py
├─ models/
│  └─ 영양소별 학습 완료 모델
├─ reports/
│  └─ 2024 holdout 성능 결과
└─ examples/
   └─ 입력 예시
```

### 주요 파일 설명

- `src/train.py`  
  준비된 KNHANES 분석 테이블을 이용한 모델 재학습 코드

- `src/predict.py`  
  전처리된 feature row를 이용한 14개 영양소 위험 예측

- `src/survey_adapter.py`  
  설문 응답에서 직접 계산 가능한 파생변수 처리

- `SURVEY_V3.md`  
  현재 확정된 사용자 설문 문항

- `reports/holdout_2024_metrics.csv`  
  최종 BMI 제외 모델의 2024 독립검증 성능

---

## 10. 현재 진행상황

### 완료
- KNHANES 데이터 전처리
- 영양소별 target 정의
- 최종 입력 변수 선정
- 모델 학습
- 2024 독립검증
- N_DUSUAL robustness check
- 성별·연령·BMI subgroup validation
- ablation analysis
- calibration
- feature importance
- SHAP
- PHQ-9 추가 효과 검증
- 최종 설문 v3 설계

### 추가 예정
- 고혈압·당뇨·이상지질혈증 subgroup 분석
- 웹 설문 serving ↔ KNHANES 학습변수 calibration
- 웹 개발자와 API 및 결과 화면 설계
- 생활습관 군집화 최종안 확정
- NBTI 표현 레이어 개발

---

## 11. 핵심 요약

> KNHANES 2022–2024 데이터를 기반으로  
> 생활습관·식습관 설문만으로 14개 영양소의 섭취 부족·과잉 위험을 예측하는 Prototype v1을 구축함.
>
> 2022–2023 학습, 2024 독립검증에서 평균 AUC 약 0.79를 확인하였고,  
> robustness, subgroup, ablation, calibration, feature importance, SHAP 분석을 통해 모델의 안정성과 해석 가능성을 추가 검증함.
>
> 현재 단계는 연구용 Prototype v1이며,  
> 향후 웹 설문 serving과 KNHANES 학습변수 간 calibration 후 서비스 연결 예정임.
