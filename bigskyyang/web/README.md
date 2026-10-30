# 영양 유형 검사 웹앱

Vite + React + Tailwind CSS v4 + react-router-dom

```bash
npm install
npm run dev      # 개발 서버 (http://localhost:5173)
npm run build    # dist/ 로 빌드
npm run preview  # 빌드 결과 미리보기
```

- 서비스 이름·문항 수: `src/config.js`
- 테마(색상·둥글기·그림자·애니메이션): `src/index.css`의 `@theme`
- 마스코트 이미지: `public/mascot/` (start.png, thinking.png, happy.png, default.png). 없으면 💊 placeholder로 표시
- Vercel 배포 시 Root Directory를 `bigskyyang/web`으로 지정. SPA 새로고침은 `vercel.json`이 처리
