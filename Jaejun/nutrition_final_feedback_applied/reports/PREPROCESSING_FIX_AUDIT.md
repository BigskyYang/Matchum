> v1.3 단계의 역사적 검증 기록임. 현재 v1.4 생활습관 가중치는 재학습되었으므로 현재 성능·가중치는 retraining/RETRAIN_COMPARISON.md 참조.

# 전처리 수정 검증

원시자료와 기존 전처리 표를 ID·연도로 연결한 자료에서 비교함. 개인 ID는 보고서에 포함하지 않음.

| 특성 | 비교 인원 | 불일치 |
| --- | --- | --- |
| ML_breakfast_freq_ord | 16586 | 0 |
| ML_lunch_freq_ord | 16586 | 0 |
| ML_dinner_freq_ord | 16586 | 0 |
| ML_eatingout_freq_ord | 16586 | 0 |
| ML_drink_month | 16310 | 0 |

## 변환 전후 가상 사례

35세 여성, 비흡연, 비음주, 세 끼 주 5~7회, 외식 주 1~2회. 나머지 값은 examples의 설문과 동일함. 피드백에 제시된 사용자의 전체 응답이 없으므로 동일 개인 결과의 재현이라고 주장하지 않음. 가중치를 그대로 두고 끼니·외식 코드만 비교함.

| 영양소 | 기존 확률 | 기존 등급 | 수정 확률 | 수정 등급 |
| --- | --- | --- | --- | --- |
| calcium | 0.677440 | Low | 0.658477 | Low |
| fiber | 0.809907 | High | 0.602214 | Mid |
| folate | 0.734965 | High | 0.711409 | High |
| iron | 0.649013 | High | 0.333740 | High |
| magnesium | 0.796218 | High | 0.500420 | Mid |
| phosphorus | 0.233721 | High | 0.081031 | Mid |
| potassium | 0.962879 | High | 0.901714 | High |
| protein | 0.302759 | High | 0.187119 | Mid |
| sodium_excess | 0.573322 | Low | 0.643355 | Mid |
| vitamin_a | 0.838245 | High | 0.704506 | Low |
| vitamin_b1 | 0.703576 | High | 0.467569 | Mid |
| vitamin_b2 | 0.417231 | High | 0.221739 | Low |
| vitamin_c | 0.857931 | High | 0.774872 | High |
| zinc | 0.517533 | High | 0.301676 | Mid |

이 가상 사례에서 등급 변경 9개. 이는 전처리 영향 확인이며 신규 성능평가가 아님.

## 가중치 보존

24개 모형과 두 등급 JSON의 SHA-256이 원본 v1.2와 동일함. 자세한 값은 같은 이름의 JSON 보고서에 포함함.
