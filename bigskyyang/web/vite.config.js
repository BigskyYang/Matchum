import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import { SERVICE_NAME, SERVICE_TAGLINE } from './src/config.js'

// index.html의 %SERVICE_NAME%, %SERVICE_TAGLINE% 자리에 config.js 값을 넣는다.
const serviceNameHtml = {
  name: 'service-name-html',
  transformIndexHtml: (html) =>
    html.replaceAll('%SERVICE_NAME%', SERVICE_NAME).replaceAll('%SERVICE_TAGLINE%', SERVICE_TAGLINE),
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss(), serviceNameHtml],
})
