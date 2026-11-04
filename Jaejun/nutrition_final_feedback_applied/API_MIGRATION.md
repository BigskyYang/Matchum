# v1.4 → v1.4.1 원시 설문·표시 규칙 변경

가중치는 v1.4 그대로임. 숫자로 이미 코딩한 18개 특성 입력은 변경하지 않음.

## 원시 설문 함수

`predict_from_survey_web(survey)`는 다음 새 키를 사용함.

- currently_smoking: bool. 평생 100개비·담배 종류 분기 없음.
- cigarettes_per_day: 기존 흡연량 입력. 현재 흡연 시 필요함.
- aerobic_150min: bool. 통합 주150분 기준.
- regular_sleep_schedule: bool.
- 일정한 수면이면 workday_bedtime/workday_waketime/restday_bedtime/restday_waketime 필요.
- 불규칙하면 average_sleep_hours 필요.

기존 smoked_100_cigarettes/current_smoking, moderate_* / vigorous_* 원시 키는 새 계약에서 제거됨. 이 키를 새 원시 함수에 그대로 전달하면 오류가 발생하므로 기존 설문 요청을 교체해야 함.

웹이 자체 encode.js로 18개 숫자를 만드는 경우 `predict_from_features_web(feature_row, mini_ffq_survey=...)`를 사용함. 기존 encode.js가 이미 합의된 방향이면 다시 반전하거나 가중하지 않음.

## 응답

- version: v1.4.1-web-feedback.
- model_version: v1.4-web-retrained.
- nutrition: 기존 두 신호 확률+등급 객체 유지. 원시 확률을 평균하거나 화면에 표시하지 않음.
- display_summary: 숫자 없는 화면 투영. 공통 영양소는 평소 식사 기준 우선, 그 결과가 없으면 생활습관 기준. 두 원시 신호는 nutrition에 보존됨.
- food_guidance: 화면에서 선택한 기준의 High 여부를 따라 음식 정보 강조. 실제 부족량이나 필요한 양을 생성하지 않음.
- lifestyle_cluster: managed_by_web 상태만 유지함. cluster_id를 이 함수에 전달하거나 nbti12.json을 요구하지 않음.

화면 선택은 웹의 기존 최대5개 규칙을 사용함. 이 패키지가 새로운 선정·동점·정렬 알고리즘을 만들지 않으므로 기본 selected_nutrients는 빈 목록이며 selection_status=managed_by_web임.

웹이 고른 목록을 검증하려면:

```python
from src.display_policy import build_display_summary
ui=build_display_summary(
    result['nutrition']['lifestyle_risk'],
    result['nutrition']['habitual_diet_risk'],
    selected_ids=['calcium','vitamin_b2'],
)
```

최대 5개·중복 없음·유효 영양소 ID만 검사하고 웹의 순서를 유지함. 빈 목록을 ‘살펴볼 영양소 없음’으로 자동 해석하지 않으며 selection_status를 확인함.
