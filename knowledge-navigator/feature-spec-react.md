# React 版认知导航 — 功能规范

## 版本

| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|----------|
| 1.0 | 2026-07-25 | — | React 迁移版初始功能规范 |
| 1.1 | 2026-07-25 | — | 搜索视图替代全览视图；导航视图合并 DAG+力导向；支持多途径点路线规划 |

---

## 一、概述

### 1.1 目标

将现有 `index.html` 单文件 SPA 迁移为 React 18 + TypeScript 工程化项目，在保持全部现有功能的前提下，实现组件复用、类型安全、HMR 热更新和可维护的代码架构。

同时重构视图架构：将原全览视图（GlobalView）替换为**搜索视图**（SearchView），原 GlobalView 的 D3 力导向图与 NavView 的 DAG 流合并进统一的**导航视图**（NavView），实现"文本搜索 → 卡片匹配 → 导航节点绑定查询 → 多途径点路线规划"的完整认知导航工作流。

### 1.2 对照关系

| 维度 | 原版 | React 版 |
|------|------|----------|
| 文件结构 | 单文件 index.html (~1300 行) | 按 component/hook/store 分层 |
| 模板 | 硬编码 HTML 字符串 + innerHTML | JSX 声明式渲染 |
| 状态 | 闭包内全局对象 state + ddState | Zustand store（6 个切片） |
| 样式 | `<style>` 内联 + CSS Variables | CSS Modules + 共享 Variables |
| 类型 | 无 | TypeScript 全量类型定义 |
| D3 集成 | initGlobalView / initNavView 两个独立函数 | useNavCanvas 统一 Hook（力导向 + DAG 合并） |
| 热更新 | 无（Python http.server） | Vite HMR 即时热更新 |
| 视图架构 | 全览(力导向) + 导航(DAG) 分离 | 搜索(卡片) → 导航(统一画布 + 多途径点) |

### 1.3 视图架构变更

```
原版                           React 版
┌────────────┐                ┌────────────┐
│ GlobalView │  力导向图       │ SearchView │  文本搜索 → 匹配卡片 → 查询绑定导航节点
│ (全览)    │  D3 force       │ (搜索)     │  类比: 地图搜索输入 → 出现多个地点选点
├────────────┤                ├────────────┤
│ NavView    │  DAG 流         │ NavView    │  力导向图(全览) + DAG 流(逐站导航)
│ (导航)     │  逐站选择       │ (导航)     │  + 下拉面板 + 多途径点序列规划
└────────────┘                └────────────┘
```

---

## 二、完整导航工作流

### 2.1 流程总览

```
SearchView                               NavView
─────────                                ───────
输入文本 "监督学习"
    ↓
匹配认知卡片列表（title/description/corpus 模糊匹配）
    ├─ 机器学习         (root/1)
    ├─ 监督学习         (root/1/1)   ← 高亮最相关
    └─ 无监督学习       (root/1/2)
    ↓
用户选中「监督学习」卡片
    ↓
查询该卡片的 bound_nodes 字段 → 找到绑定该卡片的所有导航节点
    ├─ node-supervised        ← 绑定
    ├─ node-ml-foundation     ← 绑定
    └─ node-deep-learning     ← 未绑定 (灰显或不展示)
    ↓
用户选中单个导航节点 → 点击「进入导航」
    ↓                                     ↓
                                  ┌──────────────────────┐
                                  │ 进入 NavView          │
                                  │ 当前节点 = node-supervised │
                                  │ 展示力导向全览图      │
                                  │ → 下拉面板: 节点详情   │
                                  │ → 点击"下一站"选择下一个途经点 │
                                  └──────────┬───────────┘
                                             │
                                  ┌──────────▼───────────┐
                                  │ 多途径点序列:         │
                                  │ [监督学习] → [神经网络] → [深度学习] │
                                  │ 用户可添加/删除/重排途径点 │
                                  └──────────┬───────────┘
                                             │
                                  ┌──────────▼───────────┐
                                  │ 点击「开始浏览」       │
                                  │ → switchView('browse')│
                                  │ 按途径点顺序加载其绑定卡片 │
                                  └──────────────────────┘
```

### 2.2 类比：地图导航

| 认知导航 | 地图导航类比 |
|----------|-------------|
| 输入文本搜索 | 在搜索框输入"咖啡馆" |
| 匹配认知卡片列表 | 搜索结果列表（星巴克、瑞幸、Manner...） |
| 选中卡片 → 查询绑定的导航节点 | 选中某个地点 → 查看地图上匹配的 pin 点 |
| 选中单个导航节点 → 进入导航 | 选一个 pin 作为起点/终点 |
| 多途径点序列规划 | 添加"途经点"（经停 A → 经停 B → 目的地 C） |
| 开始浏览 | 开始导航，按途经顺序推进 |

---

## 三、视图与组件树

### 3.1 根组件 App

```
<App>
  <StatusBar />                    {/* 顶部时间/信号栏 */}
  <main>                           {/* 视图容器，根据 activeView 条件渲染 */}
    {activeView === 'search'  && <SearchView />}
    {activeView === 'nav'     && <NavView />}
    {activeView === 'browse'  && <BrowseView />}
    {activeView === 'tree'    && <TreeView />}
  </main>
  <DropDownPanel />                {/* 全局下拉面板，覆盖在 nav view 画布上方 */}
  <TabBar />                       {/* 底部 4-tab 标签栏 */}
  <Toast />                        {/* 全局 Toast Portal */}
</App>
```

### 3.2 Tab 栏变更

| 序号 | 原版名称 | React 版名称 | 图标 |
|------|----------|-------------|------|
| 1 | 全览 | **搜索** | search |
| 2 | 导航 | **导航** | route |
| 3 | 浏览 | **浏览** | play |
| 4 | 管理 | **管理** | folder-tree |

### 3.3 SearchView 子组件

```
<SearchView>
  <PageHeader title="搜索导航" subtitle="输入关键词，匹配认知卡片并定位导航节点" />
  <SearchBar placeholder="搜索认知卡片..." onSearch={fn} autoFocus />

  {/* 搜索结果区: 卡片匹配列表 */}
  <section className="search-results">
    <SectionHeader>匹配的认知卡片</SectionHeader>
    <CardMatchList>                           {/* 可滚动列表 */}
      {matchedCards.map(card => (
        <CardMatchItem                         {/* 单行: icon + 标题 + 描述片段 + 匹配度 */}
          key={card.id}
          card={card}
          isSelected={card.id === selectedCardId}
          highlight={query}                    {/* 高亮匹配文本 */}
          onClick={() => selectCard(card.id)}
        />
      ))}
    </CardMatchList>
    {matchedCards.length === 0 && <EmptyState>未找到匹配的认知卡片</EmptyState>}
  </section>

  {/* 导航节点绑定区: 选中卡片后出现 */}
  {selectedCard && (
    <section className="bound-nodes">
      <SectionHeader>
        绑定「{selectedCard.title}」的导航节点 ({boundNodes.length})
      </SectionHeader>
      <BoundNodeList>
        {boundNodes.map(node => (
          <BoundNodeItem                        {/* 导航节点行: 圆点 + label + desc + 选中态 */}
            key={node.id}
            node={node}
            isSelected={node.id === selectedNodeId}
            onClick={() => selectNode(node.id)}
          />
        ))}
      </BoundNodeList>
      {boundNodes.length === 0 && <EmptyState>此卡片暂未绑定任何导航节点</EmptyState>}
    </section>
  )}

  {/* 底部操作区 */}
  {selectedNode && (
    <BottomAction>
      <p>已选择导航节点: {selectedNode.label}</p>
      <Button variant="primary" onClick={enterNav}>
        进入导航
      </Button>
    </BottomAction>
  )}
</SearchView>
```

### 3.4 NavView 子组件（合并 D3 力导向 + DAG 流）

```
<NavView>
  <PageHeader title="认知导航" subtitle={currentNode.label} />

  {/* 导航模式切换 */}
  <NavModeToggle>
    <Tab active={mode === 'overview'} onClick={setMode('overview')}>
      全览
    </Tab>
    <Tab active={mode === 'station'} onClick={setMode('station')}>
      逐站
    </Tab>
  </NavModeToggle>

  <div className="canvas-wrap">
    {/* 全览模式: 力导向图 — 展示所有导航节点及其连接 */}
    {mode === 'overview' && (
      <ForceGraph
        data={allNavNodes}
        selectedNodes={routePlan.waypoints}
        onNodeClick={handleNodeClick}
      />
    )}

    {/* 逐站模式: DAG 流 — 当前节点 + 前置 + 可跳转下一站 */}
    {mode === 'station' && (
      <DagFlow
        currentNode={currentNode}
        prevNodes={prevNodes}
        nextNodes={sortedNextNodes}
        onSelectNext={addWaypoint}
      />
    )}

    <ZoomControls onIn={fn} onOut={fn} onReset={fn} />
  </div>

  {/* 途径点序列 (Waypoints Bar) */}
  <WaypointsBar>
    {routePlan.waypoints.length === 0 && (
      <Hint>点击画布中的节点选择途径点</Hint>
    )}
    {routePlan.waypoints.map((wp, i) => (
      <WaypointChip
        key={wp.id}
        index={i}
        node={wp}
        isLast={i === routePlan.waypoints.length - 1}
        onRemove={() => removeWaypoint(i)}
      />
    ))}
    <WaypointChip type="add" onClick={openNodePicker} />
  </WaypointsBar>

  {/* 底部操作 */}
  <BottomBar>
    <Button variant="outline" onClick={clearWaypoints}>清空途径点</Button>
    <Button variant="primary" onClick={startBrowse} disabled={routePlan.waypoints.length === 0}>
      开始浏览 ({routePlan.waypoints.length} 站)
    </Button>
  </BottomBar>
</NavView>
```

### 3.5 BrowseView 子组件

```
<BrowseView>
  <TopBar>
    <Button variant="ghost" onClick={backToNav}>← 返回</Button>
    <Progress>第 {wpIndex + 1}/{routePlan.waypoints.length} 站 · {index + 1}/{total}</Progress>
    <WaypointLabel>{currentWaypoint.label}</WaypointLabel>
  </TopBar>

  <CardStack>
    {visibleCards.map(card => (
      <BrowseCard key={card.title} data={card} />
    ))}
    <CorpusToggle />
    <RelatedNodes />
  </CardStack>

  <SwipeHint direction="up" />
  <SwipeHint direction="down" />

  <BottomBar>
    <Button variant="primary">查看详情</Button>
    <Button variant="ghost">收藏</Button>
    {/* 切换到下一途径点的绑定卡片 */}
    {wpIndex < routePlan.waypoints.length - 1 && (
      <Button variant="outline" onClick={nextWaypoint}>
        下一站: {routePlan.waypoints[wpIndex + 1].label}
      </Button>
    )}
  </BottomBar>
</BrowseView>
```

### 3.6 TreeView 子组件

```
<TreeView>
  <PageHeader title="认知卡片管理" stats={totalCount} />
  <BreadcrumbNav items={pathSegments} onSelect={fn} />
  <SearchBar placeholder="搜索认知卡片..." onSearch={fn} />
  <TreeList>
    {flatData
      .filter(n => parent(n) === currentRoot)
      .map(node => (
        <TreeNode
          key={node.id}
          node={node}
          level={0}
          expanded={expandedIds.has(node.id)}
          selected={selectedId === node.id}
          onToggle={toggleNode}
          onSelect={selectNode}
        />
      ))
    }
  </TreeList>
  <FAB onClick={addCard}>+</FAB>
</TreeView>
```

---

## 四、下拉面板（DropDownPanel）

> DropDownPanel 仅在 **NavView** 中渲染（不再是全局浮层），点击画布中的导航节点时触发。

### 4.1 组件结构

```
<DropDownPanel>
  <div className={panelClass} style={{ transform: `translateY(${offset}%)` }}>
    {position === 'collapsed' ? (
      <PanelCollapsed>
        <NodeLabel />
        <ActionButton>添加为途径点</ActionButton>
      </PanelCollapsed>
    ) : (
      <PanelContent>
        <PanelHeader title={node.label} description={node.description} />
        <PanelStats boundCards={n} nextNodes={n} />
        {position === 'full' && (
          <PanelExpanded>
            <BoundCardList items={node.boundCards} />
            <NextNodeList items={node.nextNodes} />
          </PanelExpanded>
        )}
        <ActionButton onClick={addWaypoint}>添加为途径点</ActionButton>
      </PanelContent>
    )}
    <PanelHandle onDrag={handleDrag} />
  </div>
</DropDownPanel>
```

### 4.2 拖拽交互规范

| 属性 | 值 |
|------|-----|
| 触发区域 | `<PanelHandle />` 及其上下 20px 扩展区域 |
| 拖拽方向 | 垂直（Y 轴） |
| 敏感度 | 手指位移 / 3 映射到面板位移 |
| 停靠位 | `-85%`(收起)、`-50%`(半屏)、`0`(全屏) |
| 吸附逻辑 | 松手时计算距 3 个停靠位的 Y 距离，取最近 |
| 动画 | `transform .3s cubic-bezier(.32,.72,0,1)` |
| 阻止条件 | `node === null` 时禁止拖拽 |

### 4.3 面板生命周期

```
┌─────────┐  click nav node    ┌─────────┐
│ 隐藏     │ ────────────────→  │ 半屏     │
│ (无node) │                    │ (默认)   │
└─────────┘                    └────┬─────┘
     ↑                              │
     │ switchView(browse/tree)      ├── 拖拽展开 → 全屏
     │                              ├── 拖拽收起 → 收起态
     │                              ├── 点击其他节点 → 切换内容 (保持位置)
     │                              └── 点击「添加为途径点」→ 加入 waypoints + 收起面板
     │
     └────── 返回 NavView (若有 node 则恢复) ──────┘
```

---

## 五、交互功能清单

### 5.1 全局交互

| ID | 功能 | 触发方式 | 预期行为 |
|----|------|----------|----------|
| G-01 | 视图切换 | 底部 Tab 点击 / 键盘 1-4 | 条件渲染目标视图，同步面板可见性 |
| G-02 | Toast 提示 | 操作反馈 | Portal 渲染，2s 自动消失 |
| G-03 | 键盘快捷键 | 1/2/3/4 键 | 切换视图；浏览视图中 ↑↓ 切换卡片 |

### 5.2 搜索视图（SearchView）

| ID | 功能 | 触发方式 | 预期行为 |
|----|------|----------|----------|
| SR-01 | 文本搜索匹配 | 输入框输入（debounce 300ms） | 在 title / description / corpus 中模糊匹配，返回匹配卡片列表 |
| SR-02 | 搜索结果展示 | 匹配结果返回 | 列表渲染，每项显示 icon + title + 截断描述 + 匹配度 |
| SR-03 | 匹配文本高亮 | 渲染卡片项 | 与 query 匹配的文本片段高亮（`<mark>`） |
| SR-04 | 选中卡片 | 点击卡片行 | 高亮选中行 → 查询 card.bound_nodes → 渲染绑定导航节点列表 |
| SR-05 | 绑定节点展示 | selectedCard 变更 | 渲染 bound_nodes 列表，每项: 圆点 + label + description |
| SR-06 | 选中导航节点 | 点击节点行 | 高亮选中行 → 底部操作区显示(selectedNode.label + "进入导航"按钮) |
| SR-07 | 进入导航 | 点击"进入导航" | switchView('nav') + navStore.init(selectedNode.id, mode='overview') |
| SR-08 | 空状态 | 无搜索结果 | "未找到匹配的认知卡片"提示 |
| SR-09 | 无绑定节点 | 卡片无 bound_nodes | "此卡片暂未绑定任何导航节点"提示 |

### 5.3 导航视图（NavView）

| ID | 功能 | 触发方式 | 预期行为 |
|----|------|----------|----------|
| NV-01 | 全览模式渲染 | mode='overview' / 组件挂载 | D3 力导向图，渲染全部导航节点及连接边 |
| NV-02 | 逐站模式渲染 | mode='station' | D3 DAG 流，3 层布局（前驱 / 当前 / 后继） |
| NV-03 | 模式切换 | 点击全览/逐站 Tab | 切换画布渲染内容，保持途径点序列不变 |
| NV-04 | 节点点击（全览） | 点击导航节点圆 | 脉冲动画 → dropdown panel 半屏 → 显示"添加为途径点" |
| NV-05 | 节点点击（逐站） | 点击 next 节点 | 高亮 + 脉冲 → dropdown panel 半屏 → "添加为途径点" |
| NV-06 | 添加途径点 | 面板中点击"添加为途径点" | waypoints 数组 push → WaypointsBar 更新 → 面板收起 |
| NV-07 | 途径点 Chip | 渲染 waypoints[] | 横向滚动条，每项: 序号 + label + 删除按钮 |
| NV-08 | 删除途径点 | 点击 Chip 上的 X | waypoints 数组 splice → 重渲染 |
| NV-09 | 清空途径点 | 点击"清空"按钮 | waypoints = []，toast "已清空途径点" |
| NV-10 | 开始浏览 | 点击"开始浏览" | switchView('browse') + browseStore.initFromWaypoints(waypoints) |
| NV-11 | 画布缩放 | 双指/滚轮/按钮 | scaleExtent [0.4, 3] |
| NV-12 | 窗口自适应 | resize | debounce 200ms 重绘 D3 |
| NV-13 | 全览模式高亮途径点 | waypoints 变更 | 已添加为途径点的节点描边加粗 / 填充变化 |

### 5.4 浏览视图

| ID | 功能 | 触发方式 | 预期行为 |
|----|------|----------|----------|
| BR-01 | 卡片切换 | 上下滑动 / 滚轮 / 点击区域 / 键盘 | currentIndex ±1，progress 更新 |
| BR-02 | 卡片边界 | index 到达首/尾 | 首部无法上翻，尾部无法下翻 |
| BR-03 | 语料库展开 | 点击展开按钮 | toggle 显示/隐藏 corpus 列表 |
| BR-04 | 关联展示 | 渲染 related[] | 前置/后置标签区分颜色 |
| BR-05 | 滑动提示 | 空闲 3s 后 | opacity 动画指示上下滑动方向 |
| BR-06 | 返回导航 | 点击返回按钮 | switchView('nav') |
| BR-07 | 收藏 | 点击收藏按钮 | toast "已收藏" |
| BR-08 | 下一途径点 | 点击"下一站" | wpIndex +1，加载下一途径点绑定的认知卡片 |
| BR-09 | 途径点进度 | TopBar 渲染 | 显示"第 X/Y 站"，附带当前途径点 label |

### 5.5 树形管理

| ID | 功能 | 触发方式 | 预期行为 |
|----|------|----------|----------|
| TR-01 | 递归渲染 | 组件挂载 | 扁平 data → parent/children 推导 → 嵌套渲染 |
| TR-02 | 展开/折叠 | 点击 toggle 按钮 | expandedIds Set add/delete，子节点条件渲染 |
| TR-03 | 行选中 | 点击行（排除 toggle/more） | selectedId 更新，背景高亮 |
| TR-04 | 面包屑导航 | 点击面包屑项 | 滚动到目标行 + 展开所有父级 |
| TR-05 | 搜索过滤 | 输入关键字 | 不匹配行 display:none；匹配行的父级自动展开 |
| TR-06 | 添加卡片 | 点击 FAB / header + 按钮 | toast "功能开发中" |

---

## 六、数据流

### 6.1 Store 职责与消费组件

```
viewStore
  ├─ StatusBar, TabBar     ← activeView 决定激活标签
  ├─ App                   ← 条件渲染对应视图
  └─ DropDownPanel         ← switchView 时同步可见性

searchStore
  ├─ SearchView            ← 搜索匹配 + 卡片选中 + 节点选中
  └─ NavView               ← enterNav 时 navStore.init(selectedNodeId)

panelStore
  ├─ NavView               ← 画布节点点击时 setNode()
  ├─ DropDownPanel         ← 拖拽时 setPosition()，渲染时读取 node/position
  └─ App                   ← switchView 时调用 syncVisibility()

navStore
  ├─ ForceGraph / DagFlow  ← 读取 allNavNodes / currentNode + nextNodes 渲染
  ├─ WaypointsBar          ← waypoints[] 增删改
  ├─ DropDownPanel         ← "添加为途径点" → addWaypoint()
  └─ BrowseView            ← startBrowse → browseStore.initFromWaypoints(waypoints)

browseStore
  ├─ CardStack             ← 读取 cards/currentIndex；滑动时 next()/prev()
  └─ TopBar                ← wpIndex + waypoint label 显示

treeStore
  ├─ TreeList              ← 读取 flatData；搜索时 setSearch()
  └─ TreeNode              ← selectedId 决定高亮
```

### 6.2 跨视图数据流

```
SearchView                         NavView                       BrowseView
    │                                  │                              │
    │ 搜索"监督学习"                    │                              │
    │ → 匹配卡片列表                    │                              │
    │ → 选中 root/1/1                  │                              │
    │ → 查询 bound_nodes               │                              │
    │ → 选中 node-supervised            │                              │
    │                                  │                              │
    │ [进入导航] ─────────────────→     │                              │
    │   navStore.init('node-supervised')│                              │
    │   mode='overview'                │                              │
    │                                  │                              │
    │                           全览图高亮当前节点                     │
    │                           点击其他节点 → panel                  │
    │                           "添加为途径点"                        │
    │                           waypoints = [A, B, C]                │
    │                                  │                              │
    │                           [开始浏览] ─────────────→             │
    │                             browseStore.initFromWaypoints()     │
    │                                                         途径点 0: A 的 boundCards
    │                                                         [下一站] ←
    │                                                         途径点 1: B 的 boundCards
    │                                                         ...
    │                                  │ [返回] ←────────────────────┘
```

---

## 七、响应式与多端适配

### 7.1 移动端（基准）

- `#app` max-width: 480px，居中
- `height: 100dvh`（支持 iOS Safari 动态视口）
- 底部 TabBar 含 `env(safe-area-inset-bottom)`
- 拖拽/滑动基于 `touchstart/touchmove/touchend` + 兼容 mouse 事件
- 画布缩放支持双指 pinch

### 7.2 桌面端

- 键盘快捷键（1-4 切换视图，↑↓ 浏览切换）
- 鼠标滚轮缩放画布 / 滚动卡片
- `cursor: ns-resize` 拖拽手柄
- 最小宽度 320px

### 7.3 断点策略

| 断点 | 布局 |
|------|------|
| < 480px | 全宽，无 max-width 限制 |
| 480px ~ 768px | max-width: 480px 居中，模拟手机 |
| > 768px | 同上（产品定位为移动端工具，桌面端不做宽屏适配） |

---

## 八、性能要求

| 指标 | 目标 |
|------|------|
| D3 force 初始化 | ≤ 300 tick 预热（约 300ms） |
| D3 force restart | α 0.1 不中断 |
| 视图切换 | 条件渲染，≤ 16ms（单帧） |
| 面板拖拽 | 无 jank，≥ 60fps |
| 搜索卡片匹配 | debounce 300ms，即时结果 |
| 树展开/折叠 | CSS transition max-height/opacity |
| 卡片滑动 | 即时 DOM 更新 |

---

## 九、状态管理契约

### 9.1 viewStore

```typescript
interface ViewStore {
  activeView: 'search' | 'nav' | 'browse' | 'tree';
  switchView: (name: ViewStore['activeView']) => void;
}
```

约束：`switchView` 调用时自动触发 `panelStore.syncVisibility(name)`。

### 9.2 searchStore

```typescript
interface SearchStore {
  query: string;
  matchedCards: CognitiveCard[];        // 模糊匹配结果
  selectedCardId: string | null;
  selectedCard: CognitiveCard | null;   // 派生
  boundNodes: NavNode[];                // selectedCard.bound_nodes 查询结果
  selectedNodeId: string | null;
  selectedNode: NavNode | null;         // 派生
  setQuery: (q: string) => void;
  selectCard: (id: string) => void;     // 副作用: 查询 boundNodes
  selectNode: (id: string) => void;
  enterNav: () => NavNode | null;       // 返回 selectedNode 供 navStore 消费
}
```

约束：
- `setQuery` debounce 300ms 后执行匹配，更新 `matchedCards`
- `selectCard` 时自动查询该卡片 `bound_nodes` 对应的导航节点列表
- 切换卡片时清空 `selectedNodeId`

### 9.3 panelStore

```typescript
interface PanelStore {
  node: NavNode | null;
  position: 'collapsed' | 'half' | 'full';
  setNode: (node: NavNode) => void;
  clearNode: () => void;
  setPosition: (pos: PanelStore['position']) => void;
  syncVisibility: (viewName: string) => void;
}
```

约束：
- `setNode` 时若 panel 已 open → 切换内容，保持 position
- `setNode` 时若 panel 未 open → position 设为 `'half'`
- `syncVisibility('search' | 'browse' | 'tree')` → 隐藏 DOM
- `syncVisibility('nav')` → 若有 node 则恢复显示

### 9.4 navStore

```typescript
interface NavStore {
  mode: 'overview' | 'station';         // 全览 / 逐站
  currentNodeId: string;
  currentNode: NavNode | null;           // 派生
  allNavNodes: NavNode[];                // 全部导航节点（力导向图用）
  allEdges: GraphEdge[];                 // 全部连接边
  waypoints: NavNode[];                  // 途径点序列
  init: (nodeId: string, mode?: 'overview' | 'station') => void;
  setMode: (m: 'overview' | 'station') => void;
  addWaypoint: (node: NavNode) => void;
  removeWaypoint: (index: number) => void;
  clearWaypoints: () => void;
  getNextNodes: (nodeId: string) => NavNode[];  // 按权重排序的后继节点
  getPrevNodes: (nodeId: string) => NavNode[];
}
```

约束：
- `init` 来自 SearchView 的 `enterNav` 或 BrowseView 的返回
- `waypoints` 非空时"开始浏览"按钮可用
- `addWaypoint` 允许重复（同一节点多次经过）
- 全览模式下已添加的途径点在力导向图中高亮

### 9.5 browseStore

```typescript
interface BrowseStore {
  waypoints: NavNode[];                 // 从 navStore 复制
  wpIndex: number;                       // 当前途径点索引
  cards: BrowseCard[];                   // 当前途径点绑定的认知卡片
  currentIndex: number;                  // 当前卡片在 cards 中的索引
  initFromWaypoints: (waypoints: NavNode[]) => void;
  nextCard: () => void;
  prevCard: () => void;
  nextWaypoint: () => void;
}
```

约束：
- `initFromWaypoints` 复制 waypoints，wpIndex 置 0，加载第一站卡片
- `nextWaypoint` wpIndex +1，加载下一站卡片，currentIndex 重置 0
- `nextCard` / `prevCard` 边界无操作
- BrowseView 返回时不清空，下次进入恢复

### 9.6 treeStore

```typescript
interface TreeStore {
  flatData: TreeNodeData[];
  selectedId: string | null;
  expandedIds: Set<string>;
  searchQuery: string;
  selectNode: (id: string) => void;
  toggleNode: (id: string) => void;
  expandAncestors: (id: string) => void;
  setSearch: (q: string) => void;
}
```

---

## 十、D3 Hook 接口

### 10.1 useNavCanvas（合并 ForceGraph + DagFlow）

```typescript
function useNavCanvas(
  containerRef: RefObject<HTMLDivElement>,
  mode: 'overview' | 'station',
  data: {
    // 全览模式
    allNodes?: NavNode[];
    allEdges?: GraphEdge[];
    // 逐站模式
    currentNode?: NavNode;
    prevNodes?: NavNode[];
    nextNodes?: NavNode[];
    // 通用
    waypointIds?: Set<string>;          // 已添加途径点，全览模式高亮用
  },
  options: {
    onNodeClick?: (node: NavNode) => void;
    onSelectNext?: (node: NavNode) => void;
  }
): {
  zoomIn: () => void;
  zoomOut: () => void;
  zoomReset: () => void;
}
```

实现要点：
- 内部维护两个独立的 D3 渲染实例（forceSimulation + DAG layout）
- `mode` 切换时切换可见 SVG group，不销毁另一个
- 首次进入 `overview` 模式时初始化 forceSimulation
- `waypointIds` 变化时更新全览图节点样式
- 组件卸载时同时清理两个实例

---

## 十一、组件接口（Props）

### 11.1 共享组件

```typescript
// Button
interface ButtonProps {
  variant: 'primary' | 'outline' | 'ghost';
  size?: 'sm' | 'md';
  disabled?: boolean;
  onClick: () => void;
  children: React.ReactNode;
  className?: string;
}

// SearchBar
interface SearchBarProps {
  placeholder: string;
  value: string;
  onChange: (value: string) => void;
  debounceMs?: number;
  autoFocus?: boolean;
}

// BreadcrumbNav
interface BreadcrumbNavProps {
  items: { path: string; label: string }[];
  onSelect: (path: string) => void;
}

// Toast — 无 props，通过 useToastStore 控制
interface ToastStore {
  message: string | null;
  show: (msg: string, duration?: number) => void;
}

// Icon
interface IconProps {
  name: 'search' | 'route' | 'play' | 'folderTree' | 'plus' | 'chevronRight' | 'x' | 'more' | 'globe';
  size?: number;
  color?: string;
}
```

### 11.2 搜索视图组件

```typescript
// CardMatchItem
interface CardMatchItemProps {
  card: CognitiveCard;
  isSelected: boolean;
  highlight: string;     // 搜索关键词，用于高亮
  onClick: () => void;
}

// BoundNodeItem
interface BoundNodeItemProps {
  node: NavNode;
  isSelected: boolean;
  onClick: () => void;
}
```

### 11.3 导航视图组件

```typescript
// NavModeToggle — 内部组件
interface NavModeToggleProps {
  mode: 'overview' | 'station';
  onChange: (mode: 'overview' | 'station') => void;
}

// WaypointsBar
interface WaypointsBarProps {
  waypoints: NavNode[];
  onRemove: (index: number) => void;
  onAdd: () => void;              // 打开节点选择器
}

// WaypointChip
interface WaypointChipProps {
  index?: number;
  node?: NavNode;
  isLast?: boolean;
  type?: 'node' | 'add';         // 'add' 显示 + 按钮
  onRemove?: () => void;
  onClick?: () => void;
}
```

### 11.4 面板组件

```typescript
// DropDownPanel — 内嵌于 NavView，消费 panelStore + navStore

// PanelHandle
interface PanelHandleProps {
  onDragStart: (e: TouchEvent | MouseEvent) => void;
}
```

### 11.5 树组件

```typescript
interface TreeNodeProps {
  node: TreeNodeData;
  level: number;
  isExpanded: boolean;
  isSelected: boolean;
  childCount: number;
  onToggle: (id: string) => void;
  onSelect: (id: string) => void;
}

interface TreeBadgeProps {
  type: 'branch' | 'hierarchy';
}
```

### 11.6 卡片组件

```typescript
interface CardStackProps {
  cards: BrowseCard[];
  currentIndex: number;
  onPrev: () => void;
  onNext: () => void;
}

interface BrowseCardProps {
  data: BrowseCard;
  isTop: boolean;
  onToggleCorpus: () => void;
}

interface SwipeHintProps {
  direction: 'up' | 'down';
}
```

---

## 十二、目录结构（最终交付物）

```
knowledge-navigator-react/
├── index.html
├── package.json
├── tsconfig.json
├── tsconfig.node.json
├── vite.config.ts
└── src/
    ├── main.tsx
    ├── App.tsx
    ├── App.module.css
    │
    ├── store/
    │   ├── index.ts               # 统一导出
    │   ├── viewStore.ts           # activeView 切换
    │   ├── searchStore.ts         # 搜索匹配 + 卡片/节点选中
    │   ├── panelStore.ts          # 下拉面板状态
    │   ├── navStore.ts            # 导航模式 + 途径点 + D3 数据
    │   ├── browseStore.ts         # 浏览卡片 + 途径点进度
    │   └── treeStore.ts           # 树形管理
    │
    ├── data/
    │   ├── types.ts               # 所有 TS 接口
    │   ├── allNavNodes.ts         # 全部导航节点 + 边数据
    │   ├── cards.ts               # 认知卡片 + 浏览卡片数据
    │   └── treeData.ts            # 扁平树数据
    │
    ├── hooks/
    │   ├── useNavCanvas.ts        # 合并 D3 力导向 + DAG 流（单一 Hook）
    │   ├── useDragPanel.ts        # 面板拖拽
    │   └── useCardSwipe.ts        # 卡片滑动
    │
    ├── components/
    │   ├── layout/
    │   │   ├── StatusBar.tsx + .module.css
    │   │   ├── TabBar.tsx + .module.css
    │   │   └── TabButton.tsx + .module.css
    │   │
    │   ├── shared/
    │   │   ├── SearchBar.tsx + .module.css
    │   │   ├── Toast.tsx + .module.css
    │   │   ├── Button.tsx + .module.css
    │   │   ├── BreadcrumbNav.tsx + .module.css
    │   │   └── Icon.tsx
    │   │
    │   ├── panel/
    │   │   ├── DropDownPanel.tsx + .module.css    {/* 仅 NavView 内嵌 */}
    │   │   ├── PanelHandle.tsx + .module.css
    │   │   ├── PanelCollapsed.tsx
    │   │   ├── PanelContent.tsx
    │   │   └── PanelExpanded.tsx
    │   │
    │   ├── views/
    │   │   ├── SearchView.tsx + .module.css        {/* 搜索视图 */}
    │   │   ├── NavView.tsx + .module.css           {/* 导航视图（含 NavModeToggle） */}
    │   │   ├── BrowseView.tsx + .module.css
    │   │   └── TreeView.tsx + .module.css
    │   │
    │   ├── canvas/
    │   │   ├── NavCanvas.tsx + .module.css         {/* 统一画布组件 */}
    │   │   ├── ZoomControls.tsx + .module.css
    │   │   └── CanvasBackground.tsx
    │   │
    │   ├── search/
    │   │   ├── CardMatchList.tsx + .module.css     {/* 卡片匹配结果列表 */}
    │   │   ├── CardMatchItem.tsx + .module.css     {/* 单行匹配卡片 */}
    │   │   ├── BoundNodeList.tsx + .module.css     {/* 绑定导航节点列表 */}
    │   │   └── BoundNodeItem.tsx + .module.css     {/* 单行绑定节点 */}
    │   │
    │   ├── nav/
    │   │   ├── NavModeToggle.tsx + .module.css     {/* 全览/逐站切换 */}
    │   │   ├── WaypointsBar.tsx + .module.css      {/* 途径点序列条 */}
    │   │   └── WaypointChip.tsx + .module.css      {/* 单个途径点 Chip */}
    │   │
    │   ├── tree/
    │   │   ├── TreeList.tsx + .module.css
    │   │   ├── TreeNode.tsx + .module.css
    │   │   └── TreeBadge.tsx + .module.css
    │   │
    │   └── cards/
    │       ├── CardStack.tsx + .module.css
    │       ├── BrowseCard.tsx + .module.css
    │       └── SwipeHint.tsx + .module.css
    │
    └── utils/
        ├── treeUtils.ts           # deriveParent / getTreeChildren / getTreeNode
        ├── weightUtils.ts         # 权重混合算法
        └── format.ts              # 日期/数字格式化
```

---

## 十三、验收标准

### 基础框架
- [ ] Vite 开发服务器启动，HMR 热更新正常工作
- [ ] 4 个 Tab（搜索/导航/浏览/管理）可切换视图，条件渲染正确
- [ ] 键盘 1-4 切换视图与底部 Tab 同步

### 搜索视图
- [ ] 输入文本后 debounce 300ms 进行模糊匹配
- [ ] 匹配结果显示认知卡片列表（icon + title + 描述片段 + 匹配度）
- [ ] 匹配文本在结果中高亮
- [ ] 选中卡片后，绑定导航节点列表正确展示
- [ ] 选中导航节点后，底部显示"进入导航"按钮
- [ ] 点击"进入导航"切换到 NavView，currentNode 为选中节点
- [ ] 空状态正确显示（无搜索结果 / 无绑定节点）

### 导航视图
- [ ] 进入时默认为"全览"模式，显示力导向图（全部导航节点 + 边）
- [ ] 可切换到"逐站"模式，显示 DAG 流（前驱/当前/后继）
- [ ] 点击节点弹出下拉面板（半屏）
- [ ] 面板中点击"添加为途径点" → 途径点序列更新 → 面板收起
- [ ] 途径点 Chip 横向滚动，显示序号 + 名称 + 删除按钮
- [ ] 全览模式中已添加的途径点节点视觉高亮
- [ ] 清空途径点功能正常
- [ ] 画布缩放（+/-/重置 + 双指/滚轮）
- [ ] "开始浏览"按钮在途径点非空时可用
- [ ] 面板拖拽三段停靠正常

### 下拉面板
- [ ] 三段停靠（收起 -85% / 半屏 -50% / 全屏 0）
- [ ] 拖拽手柄响应 touch 和 mouse 事件
- [ ] 松手自动吸附最近停靠位，动画流畅
- [ ] 切换到其他视图时面板隐藏，回到 NavView 时恢复

### 浏览视图
- [ ] 按途径点顺序加载卡片，显示"第 X/Y 站"
- [ ] 3 层卡片堆叠 + 卡片滑动切换
- [ ] "下一站"按钮切换到下个途径点的绑定卡片
- [ ] 首尾边界无越界
- [ ] 语料库展开/折叠
- [ ] "返回"按钮回到导航视图

### 树形管理
- [ ] 扁平数据拼接为嵌套树
- [ ] 文件夹展开/折叠动画
- [ ] 面包屑导航 + 搜索过滤

### 非功能
- [ ] CSS Variables 统一深色主题
- [ ] TypeScript 编译零错误
- [ ] 移动端触摸交互正常
- [ ] 面板拖拽 ≥ 60fps

---

## 十四、与原版差异说明

| 差异项 | 说明 |
|--------|------|
| 视图架构 | 原 GlobalView(力导向图) → SearchView(卡片搜索+节点匹配)；原分离的 ForceGraph+DagFlow → 统一 NavView(全览/逐站双模式) |
| 工作流 | 新增"文本搜索 → 卡片匹配 → 绑定查询 → 多途径点规划"完整流程，类比地图导航 |
| 途径点 | 新增 WaypointsBar + WaypointChip 组件，支持多节点序列规划 |
| 下拉面板 | 从全局浮层改为 NavView 内嵌，按钮从"进入导航"改为"添加为途径点" |
| D3 Hook | useForceGraph + useDagFlow 合并为单个 useNavCanvas |
| Store | globalStore 移除，新增 searchStore；navStore 扩充 waypoints[] 管理；browseStore 新增 wpIndex/nextWaypoint |
| CSS Modules | 替代原版全局 `<style>` 和 inline style |
| 类型系统 | 全量 TypeScript 接口定义 |
| HMR | Vite 自动热更新，替代手动 Ctrl+Shift+R |
| 组件粒化 | 原 1300 行单文件 → 约 50+ 个独立 .tsx/.css 文件 |
