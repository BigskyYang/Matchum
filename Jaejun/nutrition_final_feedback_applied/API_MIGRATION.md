# v1.2 → v1.4-web-retrained API 변경

## 권장 원시 설문 경로

```python
from src.pipeline_web import predict_from_survey_web
result=predict_from_survey_web(survey)
```

문자열 보기의 원시 설문을 받음. 기존 제거 문항이 포함되면 ValueError로 거부하여 웹 수집 범위를 명확히 함. 잘못된 요청은 서버에서 HTTP 400 등으로 변환하여 표시하면 됨. API 서버·CORS·인증·배포 자체는 이 Python 패키지에 포함되지 않음.

## 숫자로 이미 변환한 웹 입력 경로

```python
from src.pipeline_web import predict_from_features_web
result=predict_from_features_web(
    feature_row,
    mini_ffq_survey=mini_ffq_answers_with_sex_and_age,
)
```

`feature_row`는 `config/service_features.json`의 18개 키와 `encoding_contract.json`의 방향을 사용함. mini-FFQ에는 sex·age와 5개 응답을 전달함. 웹에서 이미 숫자로 변환한 끼니·외식 값을 다시 역코딩하지 않음. 기존 encode.js의 실제 소스는 이번 작업에서 확인하지 못했으므로 제공한 계약·예시와 비교해야 함.

## 응답

- 생활습관: `nutrition.lifestyle_risk.calcium.probability`, `.risk_band`.
- 식품빈도: `nutrition.habitual_diet_risk.calcium.probability`, `.risk_band`.
- v1.2의 식품빈도 별도 `habitual_diet_risk_band` 딕셔너리는 제거됨. 해당 모듈도 확률+등급 객체로 통일됨.
- 식품빈도가 없으면 딕셔너리 자체가 null임. `habitual_diet_available`과 `habitual_diet_fallback_reason`으로 분기함.
- `food_guidance`는 영양소 공급 식품 예시·나트륨 점검 정보만 제공함. 질환별 식사·제품·용량 안내 없음.
- `profile_summary`, `dietary_context`, `supplement_safety`는 제거됨.
- `model_data_quality`는 개발·검수용 상태 정보임. 사용자 결과 화면에 그대로 표시할 구현 지침은 아님.
- 두 확률을 평균하지 않으며 미제공을 Low로 대체하지 않음.

기존 `pipeline.py`, `pipeline_v1_2.py`, `pipeline_v1_2_final.py`의 함수 이름은 가져오기 호환 별칭으로 남겼으나 반환값은 모두 v1.4-web-retrained임. 응답 형식은 호환되지 않으므로 프런트 경로 수정이 필요함.

## NBTI 연결

```python
result=predict_from_survey_web(
    survey,
    cluster_id='N1',
    nbti12_path='/actual/path/to/web/src/data/nbti12.json',
)
```

실제 JSON에 그 ID가 있어야 연결됨. N1은 호출 형태를 보여주는 예시이며 기존 G0 세부군집과 대응시킨 값이 아님. 훅은 ID를 검증해 첨부하며 군집을 계산하거나 N1~O3 이름·분류를 새로 만들지 않음. 원본 JSON에 ID/code 열 대신 다른 구조가 있으면 해당 파일을 받은 후 추출기를 맞춰야 함.

웹의 군집 결과는 영양확률을 변경하지 않음.
