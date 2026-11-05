# 비타민 D 생활 안내 v1.2.0

2026-11-05. 음식 질문 없이 가벼운 생활 4문항으로 수정함.

1. 출퇴근·통학 방식
2. 점심시간 외출
3. 운동 시간·장소
4. 쉬는 날 낮 외출

횟수·분 단위 계산, 식품 종류·섭취량 질문은 없음. 모든 문항은 선택이며 건너뛰기 가능함. 점수·합계·3단계 결과·계절/나이 보정·비타민 D 부족 예측은 생성하지 않음.

생활 특징 → 상황에 맞는 안내 → 선택할 행동 순서로 안내하며 제품 정보는 응답과 관계없이 사용자가 버튼을 눌렀을 때만 펼침. 식품 정보는 공통 교육 내용으로만 남겼으며 식품 응답 수집·재사용은 하지 않음.

기존 개인 영양예측 24개 모형의 가중치·입력·등급·선정 정책은 변경하지 않음. 이 ZIP은 비타민 D 추가 모듈 교체본이며, 기존 모델/제품 데이터와 원격 웹 반영은 포함하지 않음.

## 파일

- config/survey.ko.json: 한국어 4문항과 값 정의
- src/vitaminDInfo.mjs: 브라우저/Node용 순수 함수
- examples/: 요청·실제 실행 결과·실행 스크립트
- HANDOFF.md: 웹 연결과 v1.0.0 이전 안내
- DISPLAY_POLICY.md: 응답별 표시 정책
- SOURCES.md: 일반 정보 근거
- tests/, VALIDATION.md: 입력·분기 검증

## 실행

Node.js 18 이상. 외부 패키지 설치 불필요.

```sh
node --test tests/*.test.mjs
node examples/run.mjs
```

```js
import {buildVitaminDInfo} from './src/vitaminDInfo.mjs';
const info=buildVitaminDInfo({
  commute:'transit',lunch_outing:'rarely',
  exercise_setting:'indoor',day_off_outing:'sometimes'
});
```

실제 화면은 웹 담당자가 명세를 따라 렌더링함.

## v1.2.0 화면 변경

4문항과 입력 필드는 v1.1.0과 동일함. 새 guidance를 결과의 중심으로 사용하고 개별 summaryCards는 선택 상세 영역에 배치함. 제한 설명은 짧은 보조 문구로 결과 가까이에 표시함. 야외활동 장면이 확인되면 야외활동 정보를, 점심·휴일 외출이 드물고 실내 운동/운동 없음이면 식품 정보를 먼저 제시함. 이 구분은 안내 구성용이며 비타민 D 상태 등급이 아님. 제품 접근 조건과 순서는 동일함.
