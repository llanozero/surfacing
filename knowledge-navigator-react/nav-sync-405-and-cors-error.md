# 同步按钮 405 错误排查报告

## 问题描述

点击导航视图右上角的 `🔄 同步` 按钮后，前端提示同步失败，浏览器控制台有 CORS 相关报错。经浏览器 Agent 抓包确认：**核心问题是 PUT /api/nodes/{id} 请求因 CORS 跨域被拦截，而非 sync-all 接口本身返回 405**。

## 抓包结果

通过浏览器开发者工具 Network 面板记录：

| # | 请求 URL | 方法 | 状态 | 说明 |
|---|----------|------|------|------|
| 1 | `http://localhost:8171/api/nodes/node-math-subgraph` | PUT | ❌ `FAILED` | `net::ERR_FAILED` (CORS) |
| 2 | `http://localhost:8171/api/nodes/node-cog-psy-subgraph` | PUT | ❌ `FAILED` | `net::ERR_FAILED` (CORS) |
| 3 | **`http://localhost:8171/api/graphs/sync-all`** | **POST** | **✅ 200** | **`{"ok":true,"saved_graphs":3}`** |
| 4~82 | `http://localhost:8171/api/nodes/{node-id}` | PUT | ❌ `FAILED` | 全部 CORS 失败（含重试） |

**关键结论：`POST /api/graphs/sync-all` 实际返回 200 成功，但 `PUT /api/nodes/{id}` 全部因 CORS 失败。**

## 同步流程分析

```
用户点击 🔄 同步
    │
    ├─ 1. saveAllDraftsToBackend()
    │    └─ 遍历 allNavNodes，调用 wtUpdateNode(node)
    │         └─ BackendAdapter.put(`/api/nodes/${id}`, fields)
    │              └─ fetch 到 http://localhost:8171/api/nodes/{id}  ← ❌ CORS 阻塞
    │
    └─ 2. fetch POST ${baseUrl}/api/graphs/sync-all
         └─ http://localhost:8171/api/graphs/sync-all  ← ✅ 200
```

### 为什么 sync-all 成功但 PUT 失败？

**sync-all（成功）：**

```typescript
// NavView.tsx:185  /  SettingsDialog.tsx:156
const resp = await fetch(`${baseUrl}/api/graphs/sync-all`, { method: 'POST' })
```

- 无 body，无 `Content-Type` 头 → **简单请求（simple request）**
- 浏览器不发送 OPTIONS 预检，直接发 POST
- 后端 CORS 中间件在响应中添加 `Access-Control-Allow-Origin: *`
- ✅ 请求成功

**PUT /api/nodes/{id}（失败）：**

```typescript
// BackendAdapter.ts:47-54
const resp = await fetch(url, {
  method: 'PUT',
  headers: {
    Accept: 'application/json',
    'Content-Type': 'application/json',  // ← 非简单请求的 MIME
  },
  body: JSON.stringify(body),
})
```

- `Content-Type: application/json` 不是简单请求允许的 MIME 类型 → **非简单请求**
- 方法为 `PUT`（不是 GET/HEAD/POST）→ 进一步确认非简单
- 浏览器先发出 OPTIONS 预检请求
- OPTIONS 未通过 CORS 策略 → `net::ERR_FAILED`，实际 PUT 请求从未发出

### 第二个问题：wtUpdateNode 的 fire-and-forget 模式

```typescript
// writeThrough.ts:51-57
export function wtUpdateNode(node: NavNode): void {
  if (!isProMode()) return
  const { id, ...fields } = node
  void BackendAdapter.getInstance()           // ← void 表达式，不返回 Promise
    .put(`/api/nodes/${id}`, fields)
    .catch((e) => report(`更新节点 ${id}`, e))  // ← 错误仅 console.warn
}
```

```typescript
// navNodeStore.ts:228-235
export async function saveAllDraftsToBackend(): Promise<number> {
  let count = 0
  for (const node of allNavNodes) {
    await wtUpdateNode(node)  // ← void 的 await 立即返回，不等待实际请求
    count++
  }
  return count
}
```

- `wtUpdateNode` 返回 `void`（不是 Promise），`await void` 立即 resolve
- 实际的 fetch 在微任务中异步执行
- 即使所有 PUT 请求都失败，`saveAllDraftsToBackend()` 也正常返回 `count`
- 错误通过 `.catch()` 被 `console.warn` 吞掉 → **用户 UI 看不到真正的错误原因**

### 第三个问题：前端直接跨域访问后端端口

```
前端（Vite Dev Server）:  http://localhost:7100
后端（FastAPI）:          http://localhost:8171
```

前端使用 `getBackendConfig().baseUrl`（`http://localhost:8171`）直接访问后端，**绕过了 Vite 代理**：

```typescript
// vite.config.ts
proxy: {
  '/api': {
    target: 'http://localhost:8171',
    changeOrigin: true,
  },
}
```

如果改为使用同源路径 `/api`（通过 Vite 代理转发），则不会产生跨域问题。

## 控制台报错详情

```
[error] Access to fetch at 'http://localhost:8171/api/nodes/node-ai-intro'
        from origin 'http://localhost:7100' has been blocked by CORS policy:
        No 'Access-Control-Allow-Origin' header is present on the requested resource.

[warning] [remote-write] 更新节点 node-ai-intro 同步后端失败： TypeError: Failed to fetch
    at BackendAdapter.requestOnce (BackendAdapter.ts:32:26)
    at BackendAdapter.request (BackendAdapter.ts:55:27)
```

后端 Console 无异常（因为实际 PUT 请求没有被浏览器发出，OPTIONS 预检失败）。

## 根因总结

| 问题 | 根因 | 影响范围 |
|------|------|----------|
| PUT 请求 CORS 失败 | `BackendAdapter` 使用 `baseUrl` (`http://localhost:8171`) 直接跨域访问 + `Content-Type: application/json` 触发预检 | 所有通过 BackendAdapter 的 POST/PUT/DELETE 请求 |
| 用户 UI 无真实错误提示 | `wtUpdateNode` 的 fire-and-forget 模式通过 `.catch()` 吃掉了错误，仅 `console.warn` | 用户点击同步后 toast 显示成功，但数据未真正持久化 |
| sync-all 意外成功 | 因其为无 body 的简单 POST 请求，绕过 CORS 预检 | sync-all 执行时所有节点数据尚未写入后端 |

## 修复方向建议

1. **BackendAdapter 改用同源路径**：将 `baseUrl` 设为空字符串 `''` 或 `window.location.origin`，通过 Vite 代理转发到后端
2. **或修复后端 CORS 预检**：确认 FastAPI `CORSMiddleware` 正确处理 OPTIONS 请求（当前配置 `allow_origins=["*"]` 理论应工作）
3. **wtUpdateNode 改为 awaitable**：从 fire-and-forget 改为返回 Promise，让 `saveAllDraftsToBackend` 能感知请求失败并向上层抛出
4. **错误提示机制**：`saveAllDraftsToBackend` 中统计成功/失败数，失败时向用户显示具体原因

## 涉及文件

| 文件 | 说明 |
|------|------|
| [BackendAdapter.ts](file:///c:/Users/llano/Desktop/龙虾/surfacing/knowledge-navigator-react/src/api/BackendAdapter.ts) | 使用 `baseUrl` 直连后端，Content-Type 触发 CORS 预检 |
| [writeThrough.ts](file:///c:/Users/llano/Desktop/龙虾/surfacing/knowledge-navigator-react/src/api/writeThrough.ts) | `wtUpdateNode` 的 fire-and-forget 模式吞掉错误 |
| [navNodeStore.ts](file:///c:/Users/llano/Desktop/龙虾/surfacing/knowledge-navigator-react/src/store/navNodeStore.ts) | `saveAllDraftsToBackend` 遍历调用 `wtUpdateNode` |
| [NavView.tsx](file:///c:/Users/llano/Desktop/龙虾/surfacing/knowledge-navigator-react/src/components/views/NavView.tsx) | 同步按钮触发 `handleSync` |
| [vite.config.ts](file:///c:/Users/llano/Desktop/龙虾/surfacing/knowledge-navigator-react/vite.config.ts) | 已配置 `/api` 代理到 8171，但 BackendAdapter 未使用 |
| [main.py](file:///c:/Users/llano/Desktop/龙虾/surfacing/knowledge-navigator-react/backend/app/main.py) | 后端 CORS 中间件配置 `allow_origins=["*"]` |
| [nodes.py](file:///c:/Users/llano/Desktop/龙虾/surfacing/knowledge-navigator-react/backend/app/routers/nodes.py) | `PUT /api/nodes/{node_id}` 路由已正确定义 |
| [graphs.py](file:///c:/Users/llano/Desktop/龙虾/surfacing/knowledge-navigator-react/backend/app/routers/graphs.py) | `POST /api/graphs/sync-all` 路由返回 200，功能正常 |
