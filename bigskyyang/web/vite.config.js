import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import { SERVICE_NAME } from './src/config.js'

// index.html의 %SERVICE_NAME% 자리에 config.js의 서비스 이름을 넣는다.
const serviceNameHtml = {
  name: 'service-name-html',
  transformIndexHtml: (html) => html.replaceAll('%SERVICE_NAME%', SERVICE_NAME),
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss(), serviceNameHtml],
})
