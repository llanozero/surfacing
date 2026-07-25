import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import { initBackendConfig } from './config/backend'
import './App.css'

// 初始化后端模式配置（localStorage 恢复 → URL 参数覆盖），需在首次渲染前完成
initBackendConfig()

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
