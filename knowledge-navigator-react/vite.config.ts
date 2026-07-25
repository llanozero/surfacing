import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 7100,
    proxy: {
      // LM Studio 本地服务（OpenAI 兼容接口），规避浏览器 CORS
      '/api/lm': {
        target: 'http://localhost:1234',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/lm/, ''),
      },
    },
  },
})
