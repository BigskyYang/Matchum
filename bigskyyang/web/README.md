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
- `/` 시작 화면 → `/survey` 설문 → `/result` 결과
- 설문은 `Jaejun/SURVEY_V3.md`(설문 v3) 기준. 만 나이만 생년월일로 받는다.
  - 핵심 문항(생활습관·식습관) 23~27개 → 선택 문항을 더 할지 고름 → (선택) PHQ-9 9개 + 대사건강 3개
  - 선택 문항은 유형 판정에 쓰지 않고, 결과 화면의 마음 건강·대사 건강 안내에만 쓴다
- 문항마다 주소가 `/survey?q=문항ID`로 바뀌어 휴대폰 뒤로·앞으로 가기로 문항을 오갈 수 있다. 답하지 않은 문항으로 건너뛸 수는 없다 (`src/lib/surveyFlow.js`)
- 숫자·날짜·시각 입력은 위아래로 드래그하는 무한 반복 휠 선택기(`components/survey/WheelPicker.jsx`). 처음 맞춰질 값은 `questions.js`의 `initial`
- 응답은 브라우저(sessionStorage)에만 임시 저장하고 서버로 보내지 않는다. 유형 판정도 휴대폰 안에서 한다.
- 앱에서 머신러닝을 돌리지 않는다. 미리 만든 결과(군집 중심, 유형별 영양소 결과표)를 찾아 보여줄 뿐이다.
- 두 단계로 진행한다 (응답은 두 단계가 함께 쓴다)
  - 1단계 `/survey` → `/result` 유형 결과 (공유용): 유형·비율 → 생활습관 신호등·이번 주 해볼 것 → 부족할 수 있는 영양소 → 짝꿍 유형 → 2단계로
  - 2단계 `/survey2` → `/result2` 개인 결과 (나만 보기): 흡연·음주 신호등 → 챙겨 먹으면 좋은 음식 → 개인 영양 위험(준비 중) → 마음·대사 건강
  - 1단계는 유형 분류에 쓰는 생활습관만 묻는다 (출생연도, 운동 1문항, 수면이 들쭉날쭉하면 평균 시간, 세 끼 한 화면). 보기가 5개 이상이면 2열로 놓아 스크롤하지 않게 한다
  - 2단계는 재준님 최종 설문(`Jaejun/SURVEY_FINAL.md`) 기준: 흡연·음주(지금 상태부터 바로), 채소·과일, mini-FFQ 5문항(65세 이상은 생략), 건강 상태(안전 문항 + 대사질환, 여러 개 고르기), 지금 먹는 영양제, 선택 문항 PHQ-9

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
| 개인 응답 기반 미션·추천 음식 | `src/data/tips.js` |
| 생활습관 신호등 점수·해시태그·짝꿍 유형 기준 | `src/lib/profile.js` |
| 마음 건강(PHQ-9)·대사 건강 안내 문구 | `src/components/result/MindCard.jsx`, `MetabolicCard.jsx` |
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
유형 화면은 생활습관과 '부족할 수 있는 영양소'까지만 보여준다. 개인별 영양 위험 예측과 건강기능식품 안내는 개인화('더 알아보기', 준비 중)에서 한다.

유환님 (나)안 결과에서 내 유형 × 성별 × 연령대 칸을 찾아 그대로 보여준다. 어떤 영양소를 고를지는 유환님 코드가 정한다.
- 1줄 '대부분의 사람에게 부족해요': 공통 영양소 8개 (비타민 A·C·D·E, 엽산, 칼슘, 칼륨, 식이섬유)
- 2줄 '내 유형에서 살펴볼 것': 공통 외에 부족 비율 ≥ 0.5 또는 (같은 성별·나이 대비 1.2배 이상 그리고 ≥ 0.3)
  - "내 유형 10명 중 N명 / 같은 성별·나이 평균 10명 중 M명" + 문구(이 유형에서 특히 많아요 / 식사량 점검이 먼저예요 / 같은 성별·나이대에서 흔해요)
  - 테두리 색: 10명 중 5명 이상 부족(분홍), 그 아래 주의(노랑). 없으면 "공통 영양소 외에 특히 더 부족한 영양소는 없어요"
- 영양소를 누르면 역할·대표 음식 카드가 나온다 (`src/data/nutrientGuide.js`). 역할 문구에 질병 예방·치료 효과를 쓰지 않는다

유환님 분석이 바뀌면:

```bash
python scripts/build_nutrient_cells.py
```

- 입력: `Yuhwan/영양분석/output/13_유형화면_나안.json` (유환님 v9, (나)안 확정)

## 데이터·설문이 바뀌었을 때 점검 (`npm test`의 `src/lib/consistency.test.js`)
다음이 어긋나면 테스트가 실패하고 무엇이 다른지 보여준다.
- 군집 모델의 유형 ↔ `types.js`의 유형 이름·설명 ↔ 유형별 마스코트 그림
- `src/data/nutrients.js`의 영양소 14종 ↔ `Jaejun/config/targets.json`
- 부족할 수 있는 영양소 결과표의 유형·칸·영양소·공통 영양소
- 웹 설문 문항 ↔ `Jaejun/config/survey_schema_v3.json` (문항이 추가되거나 보기 개수가 바뀌면 실패)

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
