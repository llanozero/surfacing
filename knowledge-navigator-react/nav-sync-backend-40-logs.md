# 同步按钮后端 40+ 条报错日志分析

## 测试说明

手动启动后端（`python backend\run.py`，端口 8171）和前端（`npm run dev`，端口 7100），打开浏览器点击同步按钮后，后端控制台输出约 40+ 条错误日志，总计约 509KB。

## 后端日志全貌

### 启动阶段（4 条）

```
INFO:     Started server process [37624]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8171 (Press CTRL+C to quit)
```

### 页面加载阶段（12 条，正常 200）

```
GET /api/graphs    → 200 OK  (4 次)
GET /api/cards     → 200 OK  (4 次)
GET /api/nodes     → 200 OK  (4 次)
```

### 点击同步按钮后（核心错误区域）

**同步流程拆解：**

```
用户点击 🔄 同步
    │
    ├─ 第 1 步: saveAllDraftsToBackend()
    │    └─ 遍历 40+ 节点，逐个发送 PUT /api/nodes/{id}
    │         ├─ OPTIONS（预检，CORS 中间件处理）→ 200 OK ← ✅ CORS 无问题
    │         └─ PUT（实际写入）→ 500 Internal Server Error ← ❌ 真正问题
    │
    └─ 第 2 步: POST /api/graphs/sync-all → 200 OK ← ✅ sync-all 本身正常
```

**OPTIONS 预检请求全部成功（200 OK）**，说明 **CORS 不是问题**。

**PUT 请求全部返回 500**，错误信息完全一致：

```
INFO:     127.0.0.1:64501 - "PUT /api/nodes/node-ai-intro HTTP/1.1" 500 Internal Server Error
ERROR:    Exception in ASGI application
...
  File "backend\app\routers\nodes.py", line 82, in update_node
    node = _require_node(node_id)
  File "backend\app\routers\nodes.py", line 28, in _require_node
    node = store.get_node(node_id)
AttributeError: 'DataStore' object has no attribute 'get_node'
```

## 根因分析

### 错误定位

**文件：** [nodes.py](file:///c:/Users/llano/Desktop/龙虾/surfacing/knowledge-navigator-react/backend/app/routers/nodes.py) 第 28 行

```python
def _require_node(node_id: str) -> dict[str, Any]:
    node = store.get_node(node_id)  # ← 这里报错
    if node is None:
        raise HTTPException(status_code=404, detail=f"节点 {node_id} 不存在")
    return node
```

**`store` 是 `DataStore` 的实例（第 12 行 `from ..store import store`），但 `get_node` 方法定义在 `Graph` 类上，不在 `DataStore` 类上。**

### 代码结构

**`Graph` 类**（[store.py:25-113](file:///c:/Users/llano/Desktop/龙虾/surfacing/knowledge-navigator-react/backend/app/store.py#L25)）：
```python
class Graph:
    """单个导航图的内存表示。"""
    def __init__(self, graph_id, label, description):
        self.graph_id = graph_id
        self.cards = []
        self.nodes = []
    
    def get_node(self, node_id) -> dict | None:    # ← get_node 在这里
        for n in self.nodes:
            if n.get("id") == node_id:
                return n
        return None
    
    def get_card(self, card_id) -> dict | None:   # ← get_card 也在这里
        ...
```

**`DataStore` 类**（[store.py:116+](file:///c:/Users/llano/Desktop/龙虾/surfacing/knowledge-navigator-react/backend/app/store.py#L116)）：
```python
class DataStore:
    """多图数据存储，管理多个 Graph 实例。"""
    def __init__(self):
        self.graphs: dict[str, Graph] = {}
        ...
    
    def all_nodes(self, graph_id=None) -> list:    # ← DataStore 只有 all_nodes，没有 get_node
        ...
    
    def all_cards(self, graph_id=None) -> list:    # ← DataStore 只有 all_cards，没有 get_card
        ...
    
    # ❌ 缺少 get_node() 和 get_card() 方法
```

### 为什么旧版正常，新版报错？

之前的架构只有一个 YAML 文件，`store` 直接操作 `store.nodes` 列表。多图重构后，`DataStore` 通过 `self.graphs` 管理多个 `Graph` 实例，但 `nodes.py` 中的 `_require_node` 没有被更新，仍然调用 `store.get_node()`。

## 错误日志统计

### 全部 500 错误的 PUT 请求列表（42 条）

| # | 节点 ID | 状态 |
|---|---------|------|
| 1 | `node-ai-intro` | 500 |
| 2 | `node-math-subgraph` | 500 |
| 3 | `node-math-foundation` | 500 |
| 4 | `node-probability` | 500 |
| 5 | `node-linear-algebra` | 500 |
| 6 | `node-supervised` | 500 |
| 7 | `node-reinforcement` | 500 |
| 8 | `node-unsupervised` | 500 |
| 9 | `node-nn-foundation` | 500 |
| 10 | `node-deep-learning` | 500 |
| 11 | `node-attention` | 500 |
| 12 | `node-transformer` | 500 |
| 13 | `node-nlp` | 500 |
| 14 | `node-word-embedding` | 500 |
| 15 | `node-cv` | 500 |
| 16 | `node-kit-a` | 500 |
| 17 | `node-kit-b` | 500 |
| 18 | `node-kit-c` | 500 |
| 19 | `node-kit-d` | 500 |
| 20 | `node-kit-e` | 500 |
| 21 | `node-kit-f` | 500 |
| 22 | `node-kit-g` | 500 |
| 23 | `node-kit-h` | 500 |
| 24 | `node-probability-theory` | 500 |
| 25 | `node-bayes-theorem` | 500 |
| 26 | `node-la-foundation` | 500 |
| 27 | `node-matrix` | 500 |
| 28 | `node-eigen` | 500 |
| 29 | `node-calc-foundation` | 500 |
| 30 | `node-derivative` | 500 |
| 31 | `node-cog-psy-subgraph` | 500 |
| 32 | `node-cog-psy-foundation` | 500 |
| 33 | `node-working-memory` | 500 |
| 34 | `node-ltm` | 500 |
| 35 | `node-decision` | 500 |
| 36 | `node-cog-load` | 500 |
| 37 | `node-mental-model` | 500 |
| 38 | `node-ml-foundation` | 500 |
| 39 | `node-cnn` | 500 |
| 40 | `node-rnn` | 500 |
| 41~42 |（部分节点因重试有第 2 轮）| 500 |

### 成功的请求

| 请求 | 方法 | 状态 |
|------|------|------|
| `/api/graphs/sync-all` | POST | 200 OK |
| 全部 OPTIONS 预检 | OPTIONS | 200 OK |
| `/api/nodes` `GET` | GET | 200 OK |
| `/api/cards` `GET` | GET | 200 OK |
| `/api/graphs` `GET` | GET | 200 OK |

## 修复方向

### 方案 1：在 DataStore 上添加 `get_node` 方法（推荐）

在 [store.py](file:///c:/Users/llano/Desktop/龙虾/surfacing/knowledge-navigator-react/backend/app/store.py) 的 `DataStore` 类中添加全局搜索方法：

```python
class DataStore:
    # ... 现有代码 ...
    
    def get_node(self, node_id: str) -> dict | None:
        """跨所有图搜索节点。"""
        for g in self.graphs.values():
            node = g.get_node(node_id)
            if node:
                return node
        return None
    
    def get_card(self, card_id: str) -> dict | None:
        """跨所有图搜索卡片。"""
        for g in self.graphs.values():
            card = g.get_card(card_id)
            if card:
                return card
        return None
```

### 方案 2：让 _require_node 搜索所有图

修改 [nodes.py](file:///c:/Users/llano/Desktop/龙虾/surfacing/knowledge-navigator-react/backend/app/routers/nodes.py) 中的 `_require_node`：

```python
def _require_node(node_id: str) -> dict[str, Any]:
    for g in store.graphs.values():
        node = g.get_node(node_id)
        if node:
            return node
    raise HTTPException(status_code=404, detail=f"节点 {node_id} 不存在")
```

**方案 1 更优**，因为它也修复了 `cards.py` 中可能存在的类似问题（`store.get_card()` 同样不存在）。

## 涉及文件

| 文件 | 说明 |
|------|------|
| [nodes.py](file:///c:/Users/llano/Desktop/龙虾/surfacing/knowledge-navigator-react/backend/app/routers/nodes.py) | 第 28 行 `store.get_node()` 导致 AttributeError |
| [cards.py](file:///c:/Users/llano/Desktop/龙虾/surfacing/knowledge-navigator-react/backend/app/routers/cards.py) | 可能也存在类似的 `store.get_card()` 问题 |
| [store.py](file:///c:/Users/llano/Desktop/龙虾/surfacing/knowledge-navigator-react/backend/app/store.py) | `DataStore` 类缺少 `get_node` 和 `get_card` 方法，`Graph` 类有这些方法 |
| [writeThrough.ts](file:///c:/Users/llano/Desktop/龙虾/surfacing/knowledge-navigator-react/src/api/writeThrough.ts) | `wtUpdateNode` fire-and-forget 模式吞掉错误 |
| [navNodeStore.ts](file:///c:/Users/llano/Desktop/龙虾/surfacing/knowledge-navigator-react/src/store/navNodeStore.ts) | `saveAllDraftsToBackend` 调用链 |

## 过去的错误排查记录更新

之前的 [nav-sync-405-and-cors-error.md](file:///c:/Users/llano/Desktop/龙虾/surfacing/knowledge-navigator-react/nav-sync-405-and-cors-error.md) 报告提到 CORS 问题需要修正：

**新发现：CORS 不是问题，OPTIONS 预检全部成功（200 OK）。**

真正的根因是 **`DataStore` 类缺少 `get_node` 方法**，导致所有 PUT 请求返回 500。前端看到的 405 错误实际是后端返回的 500（后端 `AttributeError` 返回 HTTP 500），前端 `BackendAdapter` 抛出 `ApiError(500)`。
