# 统一设置面板：三 Tab 合并设计

## 目标

将当前三个独立的设置入口——**TTS 语音设置弹窗**、**后端设置弹窗**、**导航视图同步按钮**——合并到同一个设置面板中，以 **Tab 切换** 的方式组织，减少 UI 碎片，提供一致的用户体验。

## 现状分析

| 入口 | 组件 | 触发位置 | 说明 |
|---|---|---|---|
| TTS 语音设置 | `TtsSettingsDialog` | StatusBar 齿轮按钮 | 音色/语速/音调/预热开关/试听 |
| 后端设置 | `BackendSettingsDialog` | 未知（独立弹窗） | lite/pro 模式切换、后端地址、连接测试 |
| 同步按钮 | 内嵌于 `NavView.tsx` header | 导航视图右上角 🔄 同步 | 调用 `saveAllDraftsToBackend` + 后端 `sync-all` |

## 设计方案

### 新组件：`SettingsDialog`

一个弹窗，内部以 Tab 形式组织三个子面板。

```
┌─────────────────────────────────────┐
│  ⚙ 设置                       [✕]  │
├─────────────────────────────────────┤
│  [后端]  [TTS]  [同步]              │
├─────────────────────────────────────┤
│                                     │
│      （当前 Tab 的内容）             │
│                                     │
├─────────────────────────────────────┤
│                 [关闭]              │
└─────────────────────────────────────┘
```

### Tab 1: 后端设置

直接从现有的 `BackendSettingsDialog` 移植，内容不变：
- 模式选择：lite（轻量）/ pro（完整）
- 后端地址输入框 + 测试连接按钮
- URL 参数提示

### Tab 2: TTS 设置

直接从现有的 `TtsSettingsDialog` 移植，内容不变：
- 音色选择（Voice）
- 语速滑块（Rate）
- 音调滑块（Pitch）
- 后台预热开关
- 试听按钮

### Tab 3: 同步管理

新面板，包含：
- **同步状态展示**：显示上次同步时间、同步状态
- **手动同步按钮**：点击触发 `saveAllDraftsToBackend` + 后端 `sync-all`
- **同步结果提示**：成功/失败信息，同步的节点数和图数
- **清理缓存按钮**（可选）：清空本地草稿变更

### 触发入口

1. **StatusBar**：齿轮按钮 `⚙` → 打开 `SettingsDialog`，默认显示第一个 Tab（后端）
2. **导航视图**：原来的 🔄 同步按钮可保留作为快捷操作，或者移除仅通过设置面板操作。建议保留在 NavView header 作为快捷同步，同时设置面板中也有同步 Tab 提供更多信息

### 文件变更清单

| 文件 | 操作 | 说明 |
|---|---|---|
| `src/components/settings/SettingsDialog.tsx` | 新建 | 统一设置面板，三 Tab |
| `src/components/settings/SettingsDialog.module.css` | 新建 | 面板样式 |
| `src/components/layout/StatusBar.tsx` | 修改 | 齿轮按钮改为打开 SettingsDialog |
| `src/components/views/NavView.tsx` | 修改 | 同步按钮保留快捷操作或移除 |
| `src/components/settings/TtsSettingsDialog.tsx` | 保留/删除 | 可删除，内容移入 SettingsDialog |
| `src/components/settings/BackendSettingsDialog.tsx` | 保留/删除 | 可删除，内容移入 SettingsDialog |

### 状态管理

- 无需新增全局状态，`SettingsDialog` 内部管理当前 Tab 索引和子面板的临时表单状态
- 保存时各自调用对应的 config 写入函数（`setTtsConfig`、`setBackendConfig`、同步接口）

### 关键实现细节

1. **Tab 切换**：使用 CSS 控制 Tab 标签页的 `display`，一次只显示一个 Tab 的内容
2. **数据隔离**：三个 Tab 的表单状态相互独立，切换 Tab 不丢失临时编辑内容
3. **同步 Tab 的响应式**：同步完成后显示结果反馈，同步中禁用按钮
4. **弹窗层级**：与现有弹窗一致，使用 `createPortal` 渲染到 `document.body`，z-index 2000
