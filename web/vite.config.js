import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import { SERVICE_NAME, SERVICE_TAGLINE } from './src/config.js'

// 사이트 주소 (공유 미리보기 이미지는 전체 주소여야 카카오톡 등에서 뜬다).
// Vercel에서는 배포 주소(VERCEL_PROJECT_PRODUCTION_URL)를 자동으로 쓰고, 직접 정하려면 환경변수 SITE_URL을 넣는다.
const SITE_URL = (
  process.env.SITE_URL ||
  (process.env.VERCEL_PROJECT_PRODUCTION_URL ? `https://${process.env.VERCEL_PROJECT_PRODUCTION_URL}` : '')
).replace(/\/$/, '')

// index.html의 %SERVICE_NAME%, %SERVICE_TAGLINE%, %SITE_URL% 자리에 값을 넣는다.
const serviceNameHtml = {
  name: 'service-name-html',
  transformIndexHtml: (html) =>
    html
      .replaceAll('%SERVICE_NAME%', SERVICE_NAME)
      .replaceAll('%SERVICE_TAGLINE%', SERVICE_TAGLINE)
      .replaceAll('%SITE_URL%', SITE_URL),
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss(), serviceNameHtml],
})
