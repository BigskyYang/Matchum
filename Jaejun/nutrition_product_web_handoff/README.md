# 영양 모델–제품 목록 웹 연결 인계

2026-11-04 · 연결 모듈 1.0.0 · 기존 모델 가중치 및 등급 경계 변경 없음

사용자가 최종본으로 확정한 9단계 CSV를 제품 목록으로 변환함. 원래 파일명에는 시험용이라는 글자가 있지만, 사용자의 확정을 기준으로 이 인계 자료를 구성함. 필터링·배점·등급·선정 순서를 다시 계산하지 않음.

## 포함 자료

| 파일 | 사용처 |
|---|---|
| data/nutritionProducts.json | 제품 2,786개와 영양소·대상별 연결 3,534행 |
| src/productBridge.mjs | 기존 웹의 선정 영양소 ID를 제품 목록으로 연결하는 순수 JS 함수 |
| data/catalog_summary.json | 제품 수·원본 해시·영양소 및 대상별 개수 |
| examples/*.json | 화면·연결 확인용 응답 예시 |
| tests/productBridge.test.mjs | 전체 목록 페이지 탐색·순서 보존 등 검증 |
| source/stage9_final.csv | 확정된 원본의 바이트 그대로 보존한 파일. 점수는 이 원본에만 있음 |
| HANDOFF.md | 화면 구현 및 담당 범위 |

## 웹 사용 예

웹에서 JSON을 한 번 읽고 연결 모듈에 전달함. 기존 빌드 방식에 맞춰 경로를 조정함. 별도 학습 패키지나 scikit-learn 설치 없이 웹에서 실행할 수 있음.

```js
import { buildProductResult, fromModelResponse } from './src/productBridge.mjs';
// catalog = 기존 웹 방식으로 data/nutritionProducts.json을 import/fetch한 값
const result = buildProductResult(catalog, {
  selectedNutrientIds: selectedIdsFromExistingWeb,
  target: '일반',
  pageSize: 20,
  pages: { calcium: 1, magnesium: 1 },
});

// 모델 패키지 응답에 selected_nutrients가 들어 있을 때:
const linked = fromModelResponse(catalog, modelResponse, { target: '일반' });

// 제형 필터를 바꿀 때 페이지를 1로 되돌림:
const tablets = buildProductResult(catalog, {
  selectedNutrientIds: ['calcium'],
  filters: { calcium: { forms: ['정'] } },
  pages: { calcium: 1 },
});
```

입력 `selectedNutrientIds`는 기존 웹이 이미 선택한 영양소 목록임. 이 모듈은 확률·위험등급을 다시 비교하거나, 높은 편인 영양소를 자동으로 고르지 않음. 모델 기본 응답의 `display_summary.selected_nutrients`는 빈 배열일 수 있으며, 이때 웹이 선정한 ID 배열을 명시적으로 넘겨야 함. 빈 배열은 그대로 빈 목록을 반환함.

## 모델 출력 ID 연결

| 모델 영양소 ID | 제품 목록 ID |
|---|---|
| magnesium | magnesium |
| vitamin_b1, vitamin_b2 | vitamin_b 한 목록으로 통합 |
| vitamin_c | vitamin_c |
| fiber | fiber |
| zinc | zinc |
| folate | folate |
| iron | iron |
| calcium | calcium |
| protein, phosphorus, potassium, vitamin_a, sodium_excess | 제품 목록 없이 기존 식품 안내 유지 |

비타민 D(`vitamin_d`)·종합비타민 균형형(`multi_balance`)·피로회복형(`multi_energy`)은 모델 출력에서 자동 연결하지 않음. 웹·제품 담당자가 해당 일반 정보/대안 영역을 표시하기로 한 경우에만 `informationCategoryIds`에 명시함. 종합비타민 두 유형은 종합비타민 탭의 하위 유형으로 표시 가능함.

```js
buildProductResult(catalog, {
  selectedNutrientIds: selectedIdsFromExistingWeb,
  informationCategoryIds: ['vitamin_d'], // 별도 일반 정보 영역을 구현할 때만 지정
});
```

## 대상과 정렬

- 전체 순서: 마그네슘 → B군 → C → D → 식이섬유 → 아연 → 엽산 → 종합비타민(균형형·피로회복형) → 철 → 칼슘.
- 각 영양소·대상 안에서는 원본 CSV의 `순서`만 사용함. 점수·동점 규칙을 웹에서 재계산하지 않음.
- `target`은 원본 분류값 일반/남성/여성/시니어 중 하나임. 기본값은 일반. 나이·성별로 대상 분류를 새로 추론하지 않음.
- 일반과 여성 등 여러 풀을 화면에 함께 제공할 경우 이 함수를 대상별로 호출하고 섹션으로 구분함. 서로 다른 대상의 `순서`는 동일 순위 척도로 합치지 않음. 대상별 적용 방식은 기존 웹/제품 담당 정책을 유지함.
- 없는 대상 풀을 일반으로 자동 채우거나, 수량을 맞추기 위해 제품을 생성하지 않음.
- 원본의 영양소 ID는 제품 태그이며, 실제 품질·효능 순위나 개인 복용 우선순위를 의미하지 않음.

## 페이지와 중복

- 기본 20개, `pageSize`는 정수 12~20 범위로 지정 가능. 페이지는 1부터 시작함.
- 후보 전체를 유지하며, 상위 3개로 자르지 않음. 제형 필터 적용 후에도 원본 순서는 유지함.
- 후보가 없으면 `total_count: 0, page_count: 0, items: []`로 반환함. 범위를 벗어난 페이지도 빈 배열로 반환하므로 필터 변경 시 페이지를 1로 초기화함.
- 신고번호는 문자열임. 제품 딕셔너리에 한 번 저장하며 여러 영양소 링크는 유지함. 탭마다 같은 제품이 등장할 수 있고, 전체 제품 수/선택 제품 비교에서는 신고번호로 중복 제거함.
- B1·B2는 한 B군 탭으로 합치며 연결 이유의 ID 둘은 보존함.

## 화면 표시

- 목록 제목: `칼슘 함유 제품 살펴보기`와 `total_count`.
- 카드: 제품명, 표시된 1일 섭취방법, 제형, 해당 목록의 1일 함량·단위, 분류.
- 상세 펼치기: 기능성 원문, 섭취 시 주의사항, 업체명.
- 점수·상중 등급·모델 확률은 카드 응답에 포함하지 않음.
- 비어 있는 함량은 그대로 null로 보존함. 화면에서는 항목을 생략하거나 확인된 정보만 표시함. 0으로 바꾸지 않음.
- 기능성 전문은 일반 텍스트로 표시함. 문자열을 HTML로 직접 삽입하지 않음.
- 성분 관련 추가 설명은 전달된 기능성 정보 범위에서 표시함. 이 모듈은 새 성분 효능·개인 복용량·동시 복용 가능 여부를 생성하지 않음.

## 검증 실행

```sh
node --test tests/productBridge.test.mjs
```

원격 웹 저장소 반영·실제 웹 화면 검증은 웹 담당자의 작업임. 기존 nutritionModels.json이나 모델 학습 가중치를 교체할 필요는 없음.
