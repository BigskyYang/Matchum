# 영양 유형 검사 웹앱

Vite + React + Tailwind CSS v4 + react-router-dom

```bash
npm install
npm run dev      # 개발 서버 (http://localhost:5173)
npm test         # 응답 변환·유형 판정·결과 계산 + 데이터·설문 일치 점검
npm run build    # dist/ 로 빌드
npm run preview  # 빌드 결과 미리보기
```

## 화면
- `/` 시작 화면 → `/survey` 1단계 설문 → `/result` 유형 결과 → `/survey2` 2단계 설문 → `/result2` 개인 결과
- 설문은 `Jaejun/SURVEY_V3.md`(설문 v3)·`Jaejun/SURVEY_FINAL.md`(최종 설문)를 바탕으로 답하기 쉽게 고쳤다. 차이는 `src/lib/consistency.test.js`에 적어 두었다
- 문항마다 주소가 `/survey?q=문항ID`로 바뀌어 휴대폰 뒤로·앞으로 가기로 문항을 오갈 수 있다. 답하지 않은 문항으로 건너뛸 수는 없다 (`src/lib/surveyFlow.js`)
- 숫자·날짜·시각 입력은 위아래로 드래그하는 무한 반복 휠 선택기(`components/survey/WheelPicker.jsx`). 처음 맞춰질 값은 `questions.js`의 `initial`
- 응답은 브라우저(sessionStorage)에만 임시 저장하고 서버로 보내지 않는다. 유형 판정도 휴대폰 안에서 한다.
- 앱에서 학습은 하지 않는다. 미리 학습한 결과(군집 중심, 유형별 영양소 결과표, 재준님 예측 모델의 트리·계수)로 휴대폰에서 계산만 한다.
- 두 단계로 진행한다 (응답은 두 단계가 함께 쓴다)
  - 1단계 `/survey` → `/result` 유형 결과 (공유용): 유형·비율 → 생활습관 신호등·이번 주 해볼 것 → 부족할 수 있는 영양소 → 짝꿍 유형 → 2단계로
  - 2단계 `/survey2` → `/result2` 개인 결과 (나만 보기): 흡연·음주 신호등 → 나의 영양소 부족 위험(재준님 모델) → 챙겨 먹으면 좋은 음식 → 건강기능식품 정보(재준님 결과 중 제품 분류로 넘기는 영양소만, 제품은 팀 합의 후)
  - 1단계는 유형 분류에 쓰는 생활습관만 묻는다 (생년월일로 만 나이, 운동 1문항(중강도·고강도 구분 없이 주 150분), 취침·기상 시각, 세 끼 한 화면). 보기가 5개 이상이면 2열로 놓아 스크롤하지 않게 한다
  - 2단계는 재준님 최종 설문 기준: 흡연(궐련·전자담배 구분 없이 지금 피우는지)·음주(지금 상태부터 바로), 채소·과일, mini-FFQ 5문항(65세 이상은 생략)
- 법적 소지가 있는 것은 넣지 않는다
  - PHQ-9 우울 점수 해석, 질환별 식사 조언: 진단·처방처럼 보일 소지 (의료법)
  - 질환·임신·약물·지금 먹는 영양제는 묻지 않는다 (건강 정보(민감정보) 최소 수집). 임신·수유·질환·복용약이 있으면 의사·약사와 먼저 상의하라고 안내한다
  - 건강기능식품 정보는 준혁님 분류·필터링 기준 v3의 화면 원칙을 따른다: 음식 안내가 먼저, 제안 톤("이런 제품도 있어요"), 순위·가격·판매처 없음, 식약처 기능성 문구·섭취 시 주의사항 원문 그대로, 고지문
  - 영양소 역할 문구에 질병 예방·치료 효과를 쓰지 않는다 (식품표시광고법 제8조)

## 고칠 곳
| 바꾸고 싶은 것 | 파일 |
|---|---|
| 서비스 이름·소개 문구 | `src/config.js` |
| 설문 문항·보기·분기 (1단계·2단계) | `src/data/questions.js` |
| 응답 → 모델 변수 변환 규칙 | `src/lib/encode.js` |
| 유형 이름·설명 | `src/data/types.js` |
| 유형 화면 영양소 15종 이름·역할·대표 음식 | `src/data/nutrientGuide.js` |
| 결과 화면에 보여 줄 값 계산 (유형 결과 `buildTypeResult`, 개인 결과 `buildPersonalResult`) | `src/lib/result.js` |
| 개인화용 영양소 14종 (재준님 모델)·건강기능식품 원료·AUC | `src/data/nutrients.js` |
| 개인 영양 위험 계산·화면 (살펴볼 영양소 고르는 규칙) | `src/lib/nutritionRisk.js`, `src/lib/result.js`의 `personalNutrition` |
| 개인 응답 기반 미션·추천 음식 | `src/data/tips.js` |
| 건강기능식품 정보의 영양소·대상·고지문 | `src/data/supplementInfo.js` |
| 생활습관 신호등 점수·해시태그·짝꿍 유형 기준 | `src/lib/profile.js` |
| 테마(색상·둥글기·그림자·애니메이션) | `src/index.css`의 `@theme` |

## 데이터 파일 만들기 (`bigskyyang` 폴더에서)

### 군집 모델 `src/data/nbti12.json`
생활습관 12개 유형(대분류 4 × 세부 3, 지연님 k-medoids)을 휴대폰에서 판정하는 데 쓴다 (`src/lib/classify.js`).
`bigskyyang/analysis/output/nbti_12types.json`을 그대로 복사한 파일이다. 군집화를 다시 돌렸다면:

```bash
python analysis/05_jiyeon_improved.py 20
cp analysis/output/nbti_12types.json web/src/data/nbti12.json
python scripts/make_classify_fixtures.py   # 판정 테스트용 예시 응답 다시 만들기
```

- 계산: 응답(ML_*) → 7개 점수(상수 + Σ 계수 × 응답) → PCA 5개 → 가장 가까운 대분류 중심 → 그 대분류의 세부 중심
- 유형 ID: 대분류 `N`(나무늘보)·`A`(갓생러)·`S`(예민보스)·`O`(워커홀릭) + 세부 번호 → `N1`~`O3`. 이름·설명은 `types.js`
- 유형 비율·평균은 조사 가중치(wt_tot/3)를 쓴 값이다. 분석 과정과 검증은 `bigskyyang/analysis/군집화_결론.md`

### 부족할 수 있는 영양소 `src/data/nutrientCells.json`
유형 화면은 생활습관과 '부족할 수 있는 영양소'까지만 보여준다. 개인별 영양 위험 예측과 건강기능식품 정보는 2단계 개인 결과에서 한다.

유환님 (나)안 결과에서 내 유형 × 성별 × 연령대 칸을 찾아 그대로 보여준다. 어떤 영양소를 고를지는 유환님 코드가 정한다.
- 1줄 '대부분의 사람에게 부족해요': 공통 영양소 8개 (비타민 A·C·D·E, 엽산, 칼슘, 칼륨, 식이섬유)
- 2줄 '내 유형에서 살펴볼 것': 공통 외에 부족 비율 ≥ 0.5 또는 (같은 성별·나이 대비 1.2배 이상 그리고 ≥ 0.3)
  - "내 유형 10명 중 N명 / 같은 성별·나이 평균 10명 중 M명" + 문구(이 유형에서 특히 많아요 / 식사량 점검이 먼저예요 / 같은 성별·나이대가 챙겨야 할 영양소예요)
  - 테두리 색: 10명 중 5명 이상 부족(분홍), 그 아래 주의(노랑). 해당 영양소가 없는 칸은 소제목째 숨기고 공통 영양소만 보여 준다 (120칸 중 103칸은 내 유형 영양소가 없음)
- 영양소를 누르면 역할·대표 음식 카드가 나온다 (`src/data/nutrientGuide.js`). 역할 문구에 질병 예방·치료 효과를 쓰지 않는다

유환님 분석이 바뀌면:

```bash
python scripts/build_nutrient_cells.py
```

- 입력: `Yuhwan/영양분석/output/13_유형화면_나안.json` (유환님 v9, (나)안 확정)

### 개인 영양 위험 예측 `src/data/nutritionModels.json`
재준님 v1.4 모델(`Jaejun/nutrition_final_feedback_applied`, 가중치 `v1.4-web-retrained`, 입력·화면 규칙 `v1.4.1-web-feedback`)을 휴대폰에서 계산하도록 모델 값만 옮긴 파일 (약 1.3MB, 압축 약 380KB). 개인 결과 화면에서만 불러온다.
- 생활습관 모델 14개 (HistGradientBoosting 13 + 로지스틱 회귀 1): 입력 18개 = 1·2단계 생활습관 + 채소·과일
- 평소 식사(mini-FFQ) 모델 10개 (로지스틱 회귀): 19~64세가 5문항에 다 답했을 때만
- 재준님 화면 규칙(`config/display_policy.json`): 두 확률은 평균하지 않고, 영양소마다 평소 식사 기준이 있으면 그 등급, 없으면 생활습관 기준 등급을 보여 준다. 확률 숫자는 쓰지 않는다. 등급 경계(낮음·보통·높음)는 재준님 고정 경계 그대로
- 살펴볼 영양소: 대표 등급이 '높은 편'인 것, 최대 5개 (두 기준이 다르면 생활습관 기준 등급을 작게 같이 적는다)
- 입력 변환: `encode.js`의 ML_*는 재준님 계약과 방향이 같다. 채소·과일만 모델 척도로 뒤집는다(9 − 웹 값) (`nutritionRisk.js`)
- 팀 합의(2026-11-04)로 흡연은 궐련·전자담배 구분 없이, 유산소는 합친 시간 주 150분 여부, 수면은 취침·기상 시각만, 나이는 만 나이. 재준님 예시 응답(`examples/`)을 웹 보기로 답했을 때 입력 18개와 결과가 같은지 `nutritionRisk.test.js`에서 확인한다

재준님 모델이 바뀌면 (scikit-learn **1.8.0** 환경에서, 모델 파일이 1.8.0으로 저장됨):

```bash
python -m pip install scikit-learn==1.8.0 pandas joblib
python scripts/export_nutrition_models.py
```

- 웹 계산 = 파이썬 `predict_proba`인지 예시 60명으로 확인한다 (`src/lib/nutritionModels.fixtures.json`, 차이 1e-8 미만)
- 재준님 `examples/example_raw_survey_response.json`을 웹 설문으로 답한 경우도 재준님 파이프라인과 같은 입력·결과인지 확인한다 (`src/lib/nutritionRisk.test.js`)

### 건강기능식품 정보
**지금 화면:** 제품 추천 방식이 팀에서 아직 합의되지 않아 제품은 보여 주지 않는다. 재준님 모델의 '살펴볼 영양소'(대표 등급 높은 편) 중
준혁님 제품 분류 11종에 있는 영양소, 곧 준혁님 5단계가 받는 값만 보여 주고 "제품 정보는 준비하고 있어요"로 안내한다 (`supplementTargets`, `src/lib/supplements.js`).
비타민 B1·B2는 비타민 B군 하나로, 단백질·칼륨·인은 음식으로 챙기는 영양소로, 나트륨·비타민 A는 뺀다.

**제품을 다시 붙일 때:** 아래 제품 목록 `src/data/supplementProducts.json`과 `supplementInfo`를 쓴다. 화면 코드(제품 카드·펼치기 전 확인)는 커밋 `f8d25a9`의 `src/components/result/SupplementInfo.jsx`에 있다. 지금은 영양소 상세 창(`NutritionRisk.jsx`) 안에 '정보 준비 중'만 보여 준다.
준혁님 분류·필터링 기준 v3(`junhyeok/영양제_분류_필터링_기준(피드백).pdf`)으로 고르고 점수 순으로 정렬한 표를 받아 만든다.
원본·전체 목록은 구글 드라이브에 두고 저장소에 올리지 않는다.

```bash
python scripts/build_supplement_products.py 경로/영양제_웹표시목록.xlsx
```

- 입력 열: 영양소, 제품명, 업체명, 품목제조신고번호, 대상, 1일 섭취량, 1일 함량, 기준치 대비(%), 기능성, 섭취 시 주의사항 (자세한 것은 스크립트 맨 위)
- 영양소: 비타민 B군·C·D, 칼슘, 마그네슘, 아연, 철, 엽산, 식이섬유 + 종합비타민(균형형·피로회복형). 오메가3·유산균·루테인·밀크씨슬은 부족 위험으로 정하지 않아 쓰지 않는다
- 대상: 일반·남성·여성·시니어만 (어린이·임산부·수유부 대상은 뺀다). 가격·판매처·점수 열은 옮기지 않는다
- 어떤 영양소의 제품을 보여 줄지: 개인 영양 위험의 '살펴볼 영양소'만 (`src/lib/result.js`)
- 단백질·칼륨·인은 음식으로만 안내, 비타민 A·E는 제품 정보를 보여 주지 않는다

## 데이터·설문이 바뀌었을 때 점검 (`npm test`의 `src/lib/consistency.test.js`)
다음이 어긋나면 테스트가 실패하고 무엇이 다른지 보여준다.
- 군집 모델의 유형 ↔ `types.js`의 유형 이름·설명 ↔ 유형별 마스코트 그림
- `src/data/nutrients.js`의 영양소 14종 ↔ `Jaejun/config/targets.json`
- 부족할 수 있는 영양소 결과표의 유형·칸·영양소·공통 영양소
- 웹 설문 문항 ↔ `Jaejun/config/survey_schema_v3.json` (문항이 추가되거나 보기 개수가 바뀌면 실패)
- 제품 목록의 영양소 키·대상·필수 칸, 가격·순위 같은 칸이 없는지 (`src/lib/supplements.test.js`)
- 설문 보기 값 ↔ 재준님 v1.4 입력 계약(`encoding_contract.json`): 끼니·외식·음주·채소·과일·mini-FFQ 코드 방향

## 이미지 (`bigskyyang` 폴더에서)
- 마스코트 원본: `public/mascot/` (start.png, thinking.png, happy.png, default.png, hello.gif)
- 유형별 마스코트: `public/mascot/type_N1.png` ~ `type_O3.png` (500px, 결과 화면 맨 위)
- 휴대폰에서 빨리 뜨도록 WebP를 먼저 쓴다 (원본 대비 약 90% 작음). 마스코트를 새로 넣거나 바꿨으면:
  ```bash
  python scripts/optimize_mascots.py
  ```
  움직이는 이미지는 배경을 투명하게 바꿔 화면 배경과 경계가 보이지 않는다. WebP가 없으면 원본, 원본도 없으면 💊 placeholder로 표시
- 링크 공유 미리보기 이미지 `public/og.png` (1200×630). 서비스 이름이나 마스코트가 바뀌면:
  ```bash
  python scripts/make_share_image.py
  ```

## 배포 (Vercel)
1. vercel.com에 GitHub 계정으로 로그인 → **Add New… → Project** → `BigskyYang/Matchum` 저장소 **Import**
2. **Root Directory**를 `bigskyyang/web`으로 지정 (Framework Preset은 Vite로 자동 인식)
3. **Deploy**. 이후 `main`에 push할 때마다 자동으로 다시 배포된다
- SPA 새로고침(`/survey`, `/result` 직접 접속)은 `vercel.json`이 처리
- 공유 미리보기 이미지 주소는 Vercel 배포 주소로 자동으로 채워진다. 도메인을 따로 붙였다면 환경변수 `SITE_URL`(예: `https://nbti.example.com`)을 넣는다
