# 영양 유형 검사 웹앱

Vite + React + Tailwind CSS v4 + react-router-dom

```bash
npm install
npm run dev      # 개발 서버 (http://localhost:5173)
npm test         # 응답 변환·유형 판정 테스트
npm run build    # dist/ 로 빌드
npm run preview  # 빌드 결과 미리보기
```

## 화면
- `/` 시작 화면 → `/survey` 설문(한 화면에 한 문항, 분기 포함 22~26문항) → `/result` 결과
- 숫자·날짜·시각 입력은 휴대폰에서 위아래로 드래그하는 휠 선택기(`components/survey/WheelPicker.jsx`). 처음 맞춰질 값은 `questions.js`의 `initial`
- 응답은 브라우저(sessionStorage)에만 임시 저장하고 서버로 보내지 않는다. 판정도 휴대폰 안에서 한다.

## 고칠 곳
| 바꾸고 싶은 것 | 파일 |
|---|---|
| 서비스 이름·소개 문구 | `src/config.js` |
| 설문 문항·보기·분기 | `src/data/questions.js` |
| 응답 → 모델 변수 변환 규칙 | `src/lib/encode.js` |
| 유형 이름·설명·영양소·추천 원료 | `src/data/types.js` |
| 개인 응답 기반 미션·추천 음식 | `src/data/tips.js` |
| 생활습관 신호등 점수·해시태그·짝꿍 유형 기준 | `src/lib/profile.js` |
| 테마(색상·둥글기·그림자·애니메이션) | `src/index.css`의 `@theme` |

## 군집 모델 갱신
`src/data/model.json`은 군집화 결과 엑셀에서 자동으로 만든다. 군집화를 다시 돌렸다면 `bigskyyang` 폴더에서:

```bash
python scripts/export_model.py
```

- 기본 입력: `Jiyeon/KMeans_Final_MicroClustered.xlsx` (다른 파일이면 경로를 인자로 넘긴다)
- 단계별 스케일러와 군집 중심을 다시 계산하고, 학습 데이터 전체를 다시 분류해 엑셀 라벨과의 일치율을 출력한다
- 세부 유형 이름이 바뀌면 `src/data/types.js`도 함께 맞춘다

## 기타
- 마스코트 이미지: `public/mascot/` (start.png, thinking.png, happy.png, default.png, hello.gif). 없으면 💊 placeholder로 표시
- Vercel 배포 시 Root Directory를 `bigskyyang/web`으로 지정. SPA 새로고침은 `vercel.json`이 처리
