# 后端模式命名重构：local/remote → lite/pro

## 版本

| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|----------|
| 1.0 | 2026-07-26 | — | 初始规范：local/remote → lite/pro 重命名方案 |

---

## 一、动机

### 1.1 现有命名问题

当前模式命名 `local` / `remote`（中文：本地模式 / 远程模式）存在语义偏差：

| 当前名 | 字面含义 | 实际含义 |
|--------|----------|----------|
| `local` | 本地运行 | 前端自包含运行，**不依赖后端服务**，全部数据操作在浏览器内存完成 |
| `remote` | 远程连接 | 全量依赖后端服务，所有数据操作通过 HTTP 调用 Python FastAPI 后端 |

`local` 容易让人误以为仅是"运行位置不同"——实际上前端在开发服务器（`localhost:7100`）上始终是本地运行，区别在于**是否依赖独立后端进程**。`remote` 也容易让人误以为必须连接到远程服务器，实际上后端也可以在同一台机器本地启动。

### 1.2 新命名目标

- **语义精确**：以"是否依赖后端服务"为区分维度
- **自解释**：从名字一眼能看出其含义
- **简短**：适合代码中频繁出现

---

## 二、新命名

| 原名 | 新名 | 中文名 | 含义 |
|------|------|--------|------|
| `local` | `lite` | 轻量模式 | 纯前端运行，不依赖后端服务，数据在浏览器内存中操作 |
| `remote` | `pro` | 完整模式 | 依赖后端服务，通过 HTTP API 完成全部数据操作 |

### 2.1 命名层次

```
BackendMode
  ├── lite  ← 原名 local：无后端，前端自包含
  └── pro   ← 原名 remote：全后端，完整驱动
```

---

## 三、变更范围

### 3.1 核心类型与函数（1 文件）

**`src/config/backend.ts`**

| 现有符号 | 新符号 | 备注 |
|----------|--------|------|
| `BackendMode` type `'local' \| 'remote'` | `BackendMode` type `'lite' \| 'pro'` | 类型字面量变更 |
| `isRemoteMode()` | `isProMode()` | 函数名 + 内部 `=== 'pro'` |
| `defaultBackendConfig.mode = 'local'` | `defaultBackendConfig.mode = 'lite'` | 默认值 |
| URL 参数 `backend_mode=local\|remote` | `backend_mode=lite\|pro` | URL 参数值变更 |
| 环境变量 `KN_BACKEND_MODE=local\|remote` | `KN_BACKEND_MODE=lite\|pro` | 环境变量值变更 |
| 注释 "本地模式"/"远程模式" | "轻量模式（lite）"/"完整模式（pro）" | 注释更新 |

### 3.2 调用方（约 30 文件，～100 处引用）

所有调用 `isRemoteMode()` 和使用字面量 `'local'` / `'remote'` 的地方都需要更新：

| 目录 | 文件 | 影响 |
|------|------|------|
| `src/api/` | `index.ts`, `writeThrough.ts`, `syncFromBackend.ts` | ~80 处 `isRemoteMode()` 调用 + 注释 |
| `src/utils/` | `ttsPlayer.ts`, `vectorMatchUtils.ts` | `isRemoteMode()` 调用 |
| `src/store/` | `navNodeStore.ts`, `planStore.ts` | `isRemoteMode()` 调用 + 注释 |
| `src/cli/` | `runner.ts` | 环境变量注释 |
| `src/` | `App.tsx` | 注释 |
| `src/components/settings/` | `TtsSettingsDialog.tsx` | `isRemoteMode()` 调用 |

### 3.3 文档（约 10 个 MD 文件）

| 文件 | 需要更新的内容 |
|------|--------------|
| `README.md` | "本地模式"/"远程模式" 描述 |
| `backend-architecture.md` | 全部模式定义、配置代码示例、功能对照表 |
| `backend-implementation.md` | 开发指引中的模式描述 |
| `backend-cli-api.md` | CLI 模式对照表 |
| `tts-speech-integration.md` | TTS 故障排查中的模式描述 |
| `nav-selection-sync-and-free-browse.md` | 远程模式描述 |
| `ai-assisted-generation.md` | 本地模式降级描述 |
| `dev-startup-scripts.md` | 启动 URL 示例 |
| `cognitive-cards-relation.md` | 向量匹配模式描述 |
| `mind-toolbox-import.md` | 远程模式描述 |

### 3.4 localStorage / URL / ENV 兼容性

新旧模式的存储键值映射：

| 存储位置 | 旧值 | 新值 | 兼容性处理 |
|----------|------|------|-----------|
| `localStorage` key `kn_backend_config.mode` | `"local"` | `"lite"` | 读取时兼容旧值 `"local"` → 转为 `"lite"` |
| `localStorage` key `kn_backend_config.mode` | `"remote"` | `"pro"` | 读取时兼容旧值 `"remote"` → 转为 `"pro"` |
| URL 参数 `?backend_mode=local` | `local` | `lite` | 读取时兼容旧值 |
| URL 参数 `?backend_mode=remote` | `remote` | `pro` | 读取时兼容旧值 |
| 环境变量 `KN_BACKEND_MODE=local` | `local` | `lite` | 读取时兼容旧值 |
| 环境变量 `KN_BACKEND_MODE=remote` | `remote` | `pro` | 读取时兼容旧值 |

---

## 四、代码修改示例

### 4.1 核心配置（`src/config/backend.ts`）

```typescript
/**
 * 后端模式配置（backend-architecture.md §二）。
 * lite 模式（轻量）：纯前端操作，不依赖后端服务；
 * pro 模式（完整）：通过 HTTP 请求调用 Python FastAPI 后端完成全部数据操作。
 * 优先级：URL 参数 > localStorage > 默认值。
 * Node（CLI）环境下无 localStorage / window，自动降级为默认 lite 模式。
 */

export type BackendMode = 'lite' | 'pro'

export interface BackendConfig {
  /** 当前运行模式 */
  mode: BackendMode
  /** 后端的基础 URL（仅 pro 模式需要） */
  baseUrl: string
  /** 请求超时时间（毫秒） */
  timeout: number
  /** 请求重试次数 */
  retryCount: number
}

export const defaultBackendConfig: BackendConfig = {
  mode: 'lite',
  baseUrl: 'http://localhost:8171',
  timeout: 10000,
  retryCount: 1,
}

// 兼容旧值：local → lite, remote → pro
function migrateMode(value: string): BackendMode {
  if (value === 'local') return 'lite'
  if (value === 'remote') return 'pro'
  return value as BackendMode
}

export function isProMode(): boolean {
  return _config.mode === 'pro'
}

// initBackendConfig 中所有 mode 比较改为：
//   migrateMode(modeParam) === 'lite' || migrateMode(modeParam) === 'pro'
//   migrateMode(envMode) === 'lite' || migrateMode(envMode) === 'pro'
```

### 4.2 API 层（`src/api/index.ts`）

```typescript
import { isProMode } from '../config/backend'

// 所有 if (isRemoteMode()) → if (isProMode())
// 注释 "远程模式" → "pro 模式（完整模式）"
// 注释 "本地模式" → "lite 模式（轻量模式）"
```

### 4.3 TTS 工具（`src/utils/ttsPlayer.ts`）

```typescript
import { isProMode, getBackendConfig } from '../config/backend'

function apiUrl(path: string): string {
  if (isProMode()) {
    return `${getBackendConfig().baseUrl}${path}`
  }
  return path
}
```

### 4.4 TTS 设置对话框（`src/components/settings/TtsSettingsDialog.tsx`）

```typescript
import { isProMode, getBackendConfig } from '../../config/backend'

useEffect(() => {
  const voicesUrl = isProMode()
    ? `${getBackendConfig().baseUrl}/api/tts/voices`
    : '/api/tts/voices'
  fetch(voicesUrl)
    // ...
}, [])
```

---

## 五、兼容性策略

为确保用户在升级后无需重新设置，对旧值做静默适配：

1. **读取时迁移**：`initBackendConfig()` 中读取 localStorage / URL 参数 / 环境变量时，遇到 `'local'` 自动转为 `'lite'`，遇到 `'remote'` 自动转为 `'pro'`
2. **写入新值**：用户下次保存设置时自动使用新值，localStorage 中旧值被覆盖
3. **过渡期**：URL 参数 `?backend_mode=local` 和 `?backend_mode=remote` 继续支持至少一个版本周期

---

## 六、实施步骤

| 步骤 | 内容 | 预估改动文件数 |
|------|------|--------------|
| 1 | 修改 `src/config/backend.ts`：类型 + `isProMode()` + 兼容函数 | 1 |
| 2 | 全局替换 `isRemoteMode(` → `isProMode(` | ~30 |
| 3 | 全局替换 `'remote'` / `'local'` 字面量（排除 node_modules） | ~5 |
| 4 | 更新注释中"本地模式"/"远程模式" → "轻量模式"/"完整模式" | ~15 |
| 5 | 更新所有 .md 文档中的模式描述 | ~10 |
| 6 | 编译验证 + 功能回归 | — |

---

## 七、验收标准

- [ ] `BackendMode` type 为 `'lite' | 'pro'`
- [ ] `isProMode()` 替代 `isRemoteMode()`，语义正确
- [ ] 旧值 `'local'` / `'remote'` 读取时自动迁移为新值
- [ ] URL 参数 `?backend_mode=lite` / `?backend_mode=pro` 正常工作
- [ ] 环境变量 `KN_BACKEND_MODE=lite` / `KN_BACKEND_MODE=pro` 正常工作
- [ ] 旧 URL 参数 `?backend_mode=local` / `?backend_mode=remote` 仍被识别（兼容）
- [ ] TypeScript 编译零错误
- [ ] 所有文档中的模式描述已更新

---

## 八、相关文档对照表

| 模式 | TypeScript 类型 | 中文名 | 含义 | 数据流 |
|------|----------------|--------|------|--------|
| `lite` | `'lite'` | 轻量模式 | 无后端 | 浏览器内存 ↔ 静态数据 |
| `pro` | `'pro'` | 完整模式 | 有后端 | 浏览器 ↔ FastAPI ↔ YAML 持久化 |

---

*本文档定义了后端模式的命名重构方案，从 local/remote 迁移到 lite/pro。*
