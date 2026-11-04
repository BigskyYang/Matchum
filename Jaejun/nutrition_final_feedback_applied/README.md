# KNHANES Nutrition v1.4 — 웹용 재학습 버전

2026-11-04

**과일·채소 모름 코드 99가 있는 학습 대상 2명을 제외하고 생활습관 모형 14개를 재학습함.** 9,742명 → 9,740명. 동일 2024 평가 대상 5,320명에서 비교함.

| 지표 | 기존 | 정리 후 재학습 |
|---|---:|---:|
| 평균 AUC | 0.664521 | 0.664391 |
| 평균 PR-AUC | 0.620465 | 0.620470 |
| 평균 Brier | 0.190603 | 0.190599 |

성능 향상을 확인한 결과가 아니라 학습 입력의 비정상 코드를 정리한 결과임. 기존 고정 경계에서 영양소별 등급 변경률 평균은 9.302%임. mini-FFQ 10개는 원본 유지함.

## 범위

웹은 영양소·일반 음식 정보만 제공함. PHQ-9·질환·임신·약물·현재 영양제·제품 추천 경로는 포함하지 않음. 제품 분석은 발표 자료 범위임. 군집 유형 산출과 웹 표시는 군집·웹 담당 영역이며 영양모형의 완료 조건으로 요구하지 않음.

## 실행

```bash
python -m pip install -r requirements.txt
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python -m unittest discover -s tests -v
```

```python
import json
from src.pipeline_web import predict_from_survey_web
survey=json.load(open('examples/example_raw_survey_response.json',encoding='utf-8'))
result=predict_from_survey_web(survey)
```

응답 version은 `v1.4-web-retrained`. 원시 설문은 `config/survey_web.json`, 5문항 전용 설문은 `config/mini_ffq_5q.json`을 사용함. 두 모형은 모두 영양소별 확률+등급 객체를 반환하며 확률을 평균하지 않음. 기존 숫자 encode.js 경로는 `API_MIGRATION.md` 참조.

## 결과·재현 파일

- `reports/retraining/RETRAIN_COMPARISON.md`: 기존 vs 재학습 성능·등급 변화.
- `reports/retraining/RETRAIN_COMPARISON.json`: 세부 지표·원본 재현 오차·입력 파일 해시.
- `reports/TRAINING_DATA_QUALITY.md`: 99 정리와 재학습 처리.
- `scripts/retrain_service.py`: 실제 정답표와 기존 학습 설정으로 재현·재학습하는 코드.
- `config/service_binary_thresholds.json`: 학습 자료에서 고른 이진 평가 cutoff.
- `examples/example_response.json`: 재학습 모형으로 실제 계산한 가상 응답 결과.
- `reports/RETRAINING_TEST_RESULTS.md`: 추론·계약·원본 보존 검사.

`reports/final_audit/*.md` 등 v1.2·v1.3 보고서는 역사적 기록임. 현재 생활습관 성능은 retraining/RETRAIN_COMPARISON.md를 사용함. 기존 mini-FFQ 성능은 변경하지 않았음.

개인별 원시 자료·정답표는 패키지에 포함하지 않음. 재학습하려면 원래 자료를 직접 지정해야 함. 공식 영양 기준값의 정확성 및 실제 사용자 결과의 별도 검증은 이번 99 정리 비교 범위 밖임.
