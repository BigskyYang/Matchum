# 비타민 D 생활·식사 안내 v1.0.0

2026-11-05 기준. 웹 개발자에게 전달하는 별도 추가 모듈임.

## 반영 내용

- 야외활동 빈도·시간 2문항과 식품 종류 1문항을 제공함.
- 응답을 직접 요약하고 식품·일반 제품 정보로 연결함.
- 점수, 3단계, 나이·계절에 따른 등급 보정, 부족 예측, 복용량 계산은 제공하지 않음.
- 제품 정보는 모든 사용자에게 같은 조건으로 제공하되, 사용자가 버튼을 눌렀을 때만 펼침.
- 기존 개인 예측의 24개 가중치·입력·등급·최대 5개 정책을 변경하지 않음.

이 ZIP에는 기존 모델/제품 데이터가 중복 포함되어 있지 않음. 기존 프로젝트에 추가하여 쓰는 독립 모듈이며, 기존 패키지 전체의 교체본이 아님. 원격 저장소·웹 반영은 수행하지 않음.

## 파일

- config/survey.ko.json: 설문 및 조건부 노출 명세
- src/vitaminDInfo.mjs: 외부 의존성이 없는 순수 JavaScript 함수
- examples/answers.json, result.json: 요청·응답 예시
- examples/run.mjs: 예시 실행
- HANDOFF.md: 웹 연결과 문항 재사용 규칙
- DISPLAY_POLICY.md: 응답별 표시와 제품 연결 정책
- SOURCES.md: 정보 문구의 근거와 검증 범위
- tests/: 입력·분기·출력 계약 검사
- VALIDATION.md: 로컬 검증 기록

## 실행

Node.js 18 이상 환경에서 설치 없이 실행 가능함.

```sh
node --test tests/*.test.mjs
node examples/run.mjs
```

브라우저에서는 아래처럼 호출함. 실제 설문·카드·버튼 렌더링은 웹 담당자가 구현함.

```js
import {buildVitaminDInfo} from './src/vitaminDInfo.mjs';
const info = buildVitaminDInfo({
  outdoor_days: 'days_1_2',
  outdoor_duration: 'min15_30',
  vitamin_d_foods: ['fish', 'egg_yolk']
});
```
