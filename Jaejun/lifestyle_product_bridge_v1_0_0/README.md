# 생활기능 제품 연결 모듈 v1.0.0

장 건강·눈 건강·혈행/중성지질·간 건강을 사용자가 선택하면, 전달받은 최종 제품 목록으로 연결합니다. 기존 영양 예측 모델, 등급 경계, 최대 5개 선택 규칙은 수정하지 않습니다. 이번 항목은 예측 영양소 카드 수에 합산하지 않으며, 같은 결과 화면의 관심 정보 영역에서 사용합니다.

## 확정 구현 규칙

- 입력은 사용자가 직접 선택한 관심 항목입니다. 선택하지 않으면 추가 제품 카드는 없습니다.
- 기존 생활습관 응답은 생활 안내에만 사용합니다. 음주 → 밀크씨슬, 좌식시간 → 오메가3처럼 필요도를 추정하거나 자동으로 관심 항목을 선택하지 않습니다.
- `gut` → 유산균, `eye` → 루테인, `circulation` → 혈행·중성지질 기능이 표시된 오메가3, `liver` → 밀크씨슬.
- 눈 건강에서 건조한 눈 개선 기능이 표시된 오메가3도 볼 수 있는 옵션은 기본 꺼짐입니다. 일반적인 눈 건강 문구만으로 연결하지 않습니다. 제품 표시문구 문자열에 따른 탐색 규칙이며 원료별 기능성의 자동 검증은 아닙니다.
- 관심 선택은 복수 가능. 제품명·제조업체·신고번호 검색, 제형/단일·목적형/하루 개수 필터, 페이지당 12·16·20개를 제공합니다.
- 점수·효능·가격 순위는 만들지 않습니다. 기본 제품명순, 동률은 신고번호순입니다. 엄밀히 동일한 다국어 환경 정렬이 필요하면 `sort:'id'`를 사용합니다.
- 2,188개는 원본 '남은 제품' 시트와 동일합니다. 기존 필터링을 재평가하거나 기준을 강화하지 않았습니다. '빠진 제품'은 포함하지 않습니다.
- `source='user_interest'`, `probability=null`, `grade=null`. 기존 모델의 확률·등급 배열에 혼합하지 마세요.

## 파일 구성

- `data/products.json`: 최종 제품 배열. 유산균 964 / 오메가3 523 / 루테인 394 / 밀크씨슬 307.
- `data/metadata.json`: 원본 SHA-256, 행 수, 제품군별 개수.
- `src/bridge.js`: 프레임워크에 의존하지 않는 선택·필터·페이지 나누기 함수.
- `examples/LifestyleProducts.jsx`: 기존 React 웹에 붙이는 예제. React는 호스트 웹의 의존성을 사용합니다.
- `scripts/export_products.py`: 원본 Excel을 다시 JSON으로 변환하는 스크립트. openpyxl 필요.
- `tests/bridge.test.mjs`: 실제 제품 데이터 기반 연결·검색·페이지 나누기 검증.

## React 연결

```jsx
import products from './lifestyle-products/data/products.json';
import LifestyleProducts from './lifestyle-products/examples/LifestyleProducts.jsx';

// 기존 제품 확인/상담 절차의 결과를 연결합니다.
<LifestyleProducts
  products={products}
  allowProductBrowsing={existingSafetyFlowAllowsBrowsing}
  onOpenExistingSafetyFlow={() => openExistingSafetyFlow()}
/>
```

`existingSafetyFlowAllowsBrowsing`과 `openExistingSafetyFlow`는 기존 웹에 맞춰 연결할 변수/함수입니다. 예제 자체는 완성된 기존 웹이나 독립 실행 앱이 아닙니다. 기본값은 제품 노출 차단이며, 기존 확인 절차를 생략해 무조건 true로 설정하지 마세요. 기존 영양소 관련 제품 영역 다음에 관심 정보 컴포넌트를 배치하면 됩니다. 체크박스 선택은 컴포넌트 상태에만 저장하며 서버 전송은 없습니다.

## 기존 생활 안내에 연결

```js
import { buildLifestyleNotes } from './src/bridge.js';
const notes = buildLifestyleNotes({
  monthlyDrinking: surveyFeatures.ML_drink_month === 1,
  prolongedSitting: existingLifestyleFlags.prolongedSitting,
  irregularMeals: existingLifestyleFlags.irregularMeals,
});
```

위 플래그는 기존 웹의 판정값입니다. 새 좌식시간/식사 컷오프를 도입하지 않았습니다. 호출하지 않아도 관심 선택·제품 탐색은 동작합니다. 생활 안내와 제품 관심 선택은 독립적으로 처리합니다.

## 함량·주의사항 표시

제품 기능성과 주의사항은 원문을 텍스트로 표시합니다. `dailyIntakeText`는 사용자에게 표시할 섭취방법입니다. 원본에는 주성분 하루 함량의 **단위 컬럼이 없으므로**, `dailyMainAmountRaw`를 임의로 mg/g/CFU로 해석하지 않았습니다. `dailyMainAmountUnit=null`이며 예제는 이 수치를 노출하지 않습니다. 단위와 원료별 함량 정의를 확인한 후에만 라벨을 추가하세요.

함께 든 성분은 이름만 있고 전체 성분별 수치가 없습니다. 이 데이터만으로 상한섭취량 합계를 계산하거나 '함께 먹어도 안전'이라고 표시하지 않습니다. 기존 합산 계산에 넣으려면 기존 성분별 수치 데이터와 신고번호로 결합해야 하며, 정보가 없으면 계산 불가로 처리합니다.

제품의 적합성 판정, 의약품 상호작용 판정, 복용 지시를 추가하지 않았습니다. 이 모듈은 선택한 관심 항목에 맞는 제품 표시 정보의 탐색 기능입니다.

## 실행 및 재생성

```sh
node --test tests/bridge.test.mjs
python scripts/export_products.py /path/to/생활기능_분류.xlsx
```

Node.js 18 이상에서 코어 함수·테스트를 실행할 수 있습니다. 웹 빌드/실제 화면 검증은 통합 대상 저장소에서 별도로 진행합니다. 새 원본으로 갱신해 개수가 바뀌면 테스트의 원본 고정 개수도 확인 후 갱신하세요.
