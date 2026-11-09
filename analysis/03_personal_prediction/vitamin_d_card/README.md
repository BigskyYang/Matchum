# 비타민 D 기존 영양소 카드 연결 v1.3.0

가벼운 생활 4문항을 종합한 ‘살펴볼 이유’를 기존 영양소 결과 목록에 추가함. 별도의 생활 분석 화면이나 정보 버튼 우선순위 변경 기능이 아님.

## 사용자 결과 흐름

비타민 D → 살펴볼 이유 → 식품 안내 → 관련 제품 목록과 기존 필터.

- 기존 영양소와 같은 카드 컴포넌트/목록을 사용함.
- 안내 출처만 ‘추가 생활문항 기반 안내’로 표시함.
- 학습된 비타민 D 모델은 없음. grade/probability는 null이며 기존 낮음/보통/높음으로 변환하지 않음.
- 식품 질문이나 시간 계산 없이 출퇴근/점심/운동/쉬는 날 4문항 유지.
- 여러 응답을 종합해 평일·휴일 외출의 차이, 운동을 통한 접점, 여러 장면에서 드문 외출 등을 해석함.
- 관련 제품은 기존 카탈로그·정렬·제형 필터·기본 20개 페이지를 재사용함.

## 이번 교체 대상

기존 비타민 D v1.2.0을 대체함. 기존 학습 모델과 제품 전체 패키지를 교체하는 ZIP이 아님. v1.2.0의 buildVitaminDInfo, guidance, actions 기반 별도 영역 렌더링을 제거하고 새 카드 계약으로 연결해야 함. 설문 ID/선택지와 저장 응답은 v1.1.0/v1.2.0과 호환됨.

## 실행

Node.js 18 이상, 외부 패키지 설치 불필요.

```sh
node --test tests/*.test.mjs
node examples/run.mjs
```

## 코드

```js
import {appendVitaminDCard} from './src/vitaminDCard.mjs';
const cards=appendVitaminDCard(existingNutrientCards,vitaminDAnswers);
// 기존 카드 목록에 렌더링. 원격 웹의 실제 필드명은 HANDOFF.md 매핑 참고.
```

제품 연결 예시는 examples/webIntegration.mjs를 참고함. compat/productBridge.v1.0.1.mjs는 기존 제품 연결 함수를 바이트 그대로 복사한 호환 코드이며 새 필터나 점수를 만들지 않음. 실제 제품 카탈로그는 기존 nutritionProducts.json을 전달해야 함.

파일: config/survey.ko.json, src/vitaminDCard.mjs, src/productAdapter.mjs, HANDOFF.md, DISPLAY_RULES.md, examples/, tests/, VALIDATION.md, SOURCES.md.

원격 웹/깃 반영은 수행하지 않았음. 실제 컴포넌트/필드명을 연결하고 브라우저에서 확인하는 작업은 웹 담당자가 수행함.
