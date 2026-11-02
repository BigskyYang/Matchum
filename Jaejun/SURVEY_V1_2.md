# 사용자 설문 v1.2

기존 생활습관 설문 구조를 유지하면서 habitual diet mini-FFQ 5문항을 정식 추가함.

## Mini-FFQ 5문항

### F1. 육류
평소 육류(소고기, 돼지고기, 닭고기 등)를 얼마나 자주 드십니까?

### F2. 생선·해산물
평소 생선 및 해산물을 얼마나 자주 드십니까?

### F3. 달걀
평소 달걀을 얼마나 자주 드십니까?

### F4. 콩·두부·콩제품
평소 콩, 두부 및 콩제품을 얼마나 자주 드십니까?

### F5. 우유·유제품
평소 우유 및 유제품을 얼마나 자주 드십니까?

공통 보기:
- 거의 먹지 않음
- 월 1~3회
- 주 1~2회
- 주 3~4회
- 주 5~6회
- 하루 1회
- 하루 2회
- 하루 3회 이상

## 결과 구조

- Lifestyle risk: 2022–2024 survey-only model
- Habitual diet risk: 2012–2016 mini-FFQ model
- Lifestyle subtype/NBTI: cluster model
- Mental health: PHQ-9
- Metabolic health: disease context
- Supplement safety: 별도 safety gate 예정

두 영양위험 모듈의 probability는 직접 평균하지 않음.
