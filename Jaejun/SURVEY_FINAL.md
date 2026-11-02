# 사용자 설문 v1.2 FINAL

## 기본정보
- 성별
- 연령

## 생활습관
기존 survey-only v1 문항 구조 유지
- 흡연
- 음주
- 운동
- 좌식시간
- 수면
- 스트레스
- 식사빈도
- 외식빈도
- 과일
- 채소

## Habitual mini-FFQ 5문항
공통 응답:
거의 먹지 않음 / 월 1~3회 / 주 1~2회 / 주 3~4회 / 주 5~6회 / 하루 1회 / 하루 2회 / 하루 3회 이상

1. 육류
2. 생선·해산물
3. 달걀
4. 콩·두부·콩제품
5. 우유·유제품

## 정신건강
PHQ-9 9문항
- nutrition predictor에는 사용하지 않음
- item 9 > 0이면 safety response 필요

## 대사건강
- 고혈압 진단 여부
- 당뇨병 진단 여부
- 이상지질혈증 진단 여부
nutrition probability를 직접 변경하지 않고 결과 해석 context로 사용

## 제품추천 안전문항
1. 현재 복용 중인 영양제
2. 임신·수유 여부
3. 항응고제·아스피린 등 주의 약물 복용 여부
4. 신장질환·신장결석 여부

## 연령 규칙
- 19–64세: lifestyle risk + habitual mini-FFQ risk 제공
- 65세 이상: lifestyle risk만 제공, mini-FFQ는 미검증으로 비활성화

## 결과 원칙
- Lifestyle risk와 Habitual diet risk는 서로 다른 signal로 표시
- 두 probability를 단순 평균하지 않음
- Low/Mid/High는 각 모델 내부 기준으로만 표시
