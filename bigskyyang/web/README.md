# 영양 유형 검사 웹앱

Vite + React + Tailwind CSS v4 + react-router-dom

```bash
npm install
npm run dev      # 개발 서버 (http://localhost:5173)
npm test         # 응답 변환·유형 판정·결과 계산 테스트
npm run build    # dist/ 로 빌드
npm run preview  # 빌드 결과 미리보기
```

## 화면
- `/` 시작 화면 → `/survey` 설문 → `/result` 결과
- 설문은 `Jaejun/SURVEY_V3.md`(설문 v3) 기준. 만 나이만 생년월일로 받는다.
  - 핵심 문항(생활습관·식습관) 23~27개 → 선택 문항을 더 할지 고름 → (선택) PHQ-9 9개 + 대사건강 3개
  - 선택 문항은 유형 판정에 쓰지 않고, 결과 화면의 마음 건강·대사 건강 안내에만 쓴다
- 숫자·날짜·시각 입력은 위아래로 드래그하는 무한 반복 휠 선택기(`components/survey/WheelPicker.jsx`). 처음 맞춰질 값은 `questions.js`의 `initial`
- 응답은 브라우저(sessionStorage)에만 임시 저장하고 서버로 보내지 않는다. 유형 판정도 휴대폰 안에서 한다.
- 앱에서 머신러닝을 돌리지 않는다. 미리 만든 결과(군집 중심, 유형별 영양소 결과표)를 찾아 보여줄 뿐이다.

## 고칠 곳
| 바꾸고 싶은 것 | 파일 |
|---|---|
| 서비스 이름·소개 문구 | `src/config.js` |
| 설문 문항·보기·분기 | `src/data/questions.js` |
| 응답 → 모델 변수 변환 규칙 | `src/lib/encode.js` |
| 유형 이름·설명 | `src/data/types.js` |
| 영양소 14종 이름·대표 음식·건강기능식품 원료·AUC | `src/data/nutrients.js` |
| 개인 응답 기반 미션·추천 음식 | `src/data/tips.js` |
| 생활습관 신호등 점수·해시태그·짝꿍 유형 기준 | `src/lib/profile.js` |
| 마음 건강(PHQ-9)·대사 건강 안내 문구 | `src/components/result/MindCard.jsx`, `MetabolicCard.jsx` |
| 테마(색상·둥글기·그림자·애니메이션) | `src/index.css`의 `@theme` |

## 데이터 파일 만들기 (`bigskyyang` 폴더에서)

### 군집 모델 `src/data/model.json`
군집화를 다시 돌렸다면:

```bash
python scripts/export_model.py
```

- 기본 입력: `Jiyeon/KMeans_Final_MicroClustered.xlsx` (다른 파일이면 경로를 인자로 넘긴다)
- 단계별 스케일러와 군집 중심을 다시 계산하고, 학습 데이터 전체를 다시 분류해 엑셀 라벨과의 일치율을 출력한다
- 세부 유형 이름이 바뀌면 `src/data/types.js`도 함께 맞춘다

### 유형별 영양소 결과표 `src/data/nutrientProfiles.json`
결과 화면의 '내 유형이 챙겨야 할 영양소'와 '건강기능식품 원료'는 이 표에서 내 유형의 값을 찾아 보여준다.
표가 비어 있으면 "결과가 준비되면 표시돼요"가 나온다.

```bash
python scripts/build_nutrient_profiles.py --nutrients <개인별 영양소 CSV>
```

- 입력 CSV: `ID`, `year` + 영양소별 열 (`<영양소키>_prob` 예측확률, 또는 `Jaejun/config/targets.json`의 실제 부족 여부 0/1)
- 군집 결과(`Jiyeon/...xlsx`)와 `ID`·`year`로 합쳐 유형(대분류 4개 + 세부 20개)별 평균을 내고, `Jaejun/config/risk_thresholds.json` 기준으로 Low/Mid/High를 붙인다
- 가중치를 적용하지 않은 표본 평균이다. 세부 유형 값이 없으면 대분류 값을 쓴다

## 기타
- 마스코트 이미지: `public/mascot/` (start.png, thinking.png, happy.png, default.png, hello.gif). 없으면 💊 placeholder로 표시
- Vercel 배포 시 Root Directory를 `bigskyyang/web`으로 지정. SPA 새로고침은 `vercel.json`이 처리
