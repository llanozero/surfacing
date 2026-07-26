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
      // 后端 API（FastAPI 8171），包括 TTS 等所有 /api/* 请求
      '/api': {
        target: 'http://localhost:8171',
        changeOrigin: true,
      },
    },
  },
})
