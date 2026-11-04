# Nutrition — Final Feedback Applied

패키지 버전: **v1.4.1-web-feedback**  
학습 가중치 버전: **v1.4-web-retrained**  
반영일: 2026-11-04

## 이번 반영 내용

- 현재 흡연 유무로 `ML_smoker`를 계산함. 평생 100개비 문항이나 담배 종류 분기는 사용하지 않음.
- 유산소는 강도 구분 없이 주 150분 이상 여부를 `ML_aerobic`으로 사용함. 고강도 ×2 계산 없음.
- 수면이 일정하면 평일×5·휴일×2 평균, 불규칙하면 직접 응답한 평균 수면시간을 사용함.
- 나이는 웹이 전달한 숫자를 그대로 사용함. 출생연도·생일 계산은 웹 담당 영역임.
- 두 신호 확률은 평균하지 않고, 화면용 등급은 평소 식사 모형이 있으면 그 결과를 따름.
- 화면은 높은 편/보통/낮은 편만 표시함. 원시 확률은 API에 유지함.
- 살펴볼 영양소는 웹이 기존 규칙으로 고른 최대 5개 ID를 사용함. 영양소 간 확률을 비교하는 새 순위를 만들지 않음.
- 군집은 웹이 별도로 판정함. 사용하지 않는 cluster_hook을 제거함.

## 제품 정보 담당 범위

**영양 모델 패키지에는 제품 추천·제품 정보 경로가 없고, 제품 정보는 준혁 님 파트에서 관리함.** 전체 웹 개인 결과에 준혁 님 파트의 건강기능식품 정보가 별도로 표시되는 구성을 금지하거나 제거하는 지침이 아님. 제품 분석은 발표에도 활용할 수 있음.

PHQ-9·대사건강·질환·임신·약물·현재 영양제 문항은 이 패키지에서 수집·계산하지 않음.

## 기존 웹 모델 export를 다시 해야 하나?

**이번 패치는 24개 joblib과 두 상대등급 JSON을 모두 유지함.** SHA-256 동일성을 확인했으므로 가중치 JSON을 다시 만들 필요는 없음. 웹의 `nutritionModels.json` 모형 내용은 v1.4 그대로 사용 가능함.

바뀐 것은 원시 설문 어댑터·화면용 처리·문서임. 웹이 자체 encode.js로 이미 합의된 숫자 18개를 만든다면 `predict_from_features_web()` 경로와 호환됨. Python 원시 설문 함수를 사용한다면 새 `config/survey_web.json`과 예시 응답을 따라야 함.

웹 담당자가 보고한 60명 오차 1e-8 미만·18개 입력과 예시 확률/등급 일치는 **팀원이 수행한 웹 검증 결과**로 기록함. 웹 소스와 내보내기 파일을 이 작업에서 다시 실행한 결과로 설명하지 않음.

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

응답의 `version`은 어댑터 버전, `model_version`은 가중치 버전임. 모델이 바뀌면 가중치 버전을 갱신해 웹 담당자에게 전달하고, 웹 담당자가 `bigskyyang/scripts/export_nutrition_models.py`로 다시 내보냄.

## 파일 안내

| 파일 | 용도 |
|---|---|
| `TEAM_FEEDBACK_RESPONSE.md` | 이번 피드백별 반영 내역 |
| `NOTION_CONNECTION_TABLE_UPDATE.md` | 노션에 교체할 현재 코딩 방향·표시 규칙 |
| `config/survey_web.json` | 합의된 원시 설문 정의 |
| `config/encoding_contract.json` | 숫자 입력 18개 계약과 변환 정책 |
| `config/display_policy.json` | 화면 라벨·우선 기준·최대 5개 정책 |
| `src/display_policy.py` | 숫자 없는 화면용 결과, 웹 선정 목록 검증 |
| `API_MIGRATION.md` | 새 원시 요청 및 응답 변화 |
| `reports/FEEDBACK_PATCH_TEST_RESULTS.md` | 이번 패치 검사 |
| `reports/retraining/RETRAIN_COMPARISON.md` | 기존 v1.4 재학습 결과; 이번 패치에서 재평가하지 않음 |

## 해석 범위

설문 단순화는 팀이 합의한 웹 입력 규칙임. 기존 학습·검증 수치를 변경된 문항의 동등성·실제 사용자 성능을 새로 검증한 수치라고 설명하지 않음. 흡연량 특성 `ML_cigarettes_day`는 기존 모형 입력이므로 유지하며, 값이 필요한 경우 임의로 0을 넣지 않음.
