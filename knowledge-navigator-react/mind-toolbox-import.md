# 心智工具箱导入 · cognitive-cards → 知识导航

> 将 `cognitive-cards` 项目的 10 张概念卡片与 8 个「锦囊」导入知识导航后端，
> 锦囊作为导航节点构成「设计者 ↔ 执行者」循环导航图。

## 一、数据源

| 文件 | 内容 | 数量 |
|------|------|------|
| `cognitive-cards/data/cards.json` | 概念卡片（sections: insight / design_directive / product_form） | 10 |
| `cognitive-cards/data/kits.json` | 锦囊（body 段落 + mechanism + next_kits 循环连接） | 8 |

## 二、映射规则

生成器：`scripts/generate-mind-toolbox-yaml.py`（可重复执行，源数据更新后重新生成即可）

| 源 | 目标 | 说明 |
|----|------|------|
| — | 卡片 `root/7`（folder） | 一级文件夹「心智工具箱 · 设计者循环」，绑定全部 8 个锦囊节点 |
| cards.json × 10 | 卡片 `root/7/1` ~ `root/7/10` | title 带原始编号；corpus = insight / design_directive / product_form 三段；tag 取首个标签 |
| kits.json × 8 | 卡片 `root/7/11` ~ `root/7/18` | 「锦囊 X · 名称」；corpus = body 段落 + 机制说明；绑定对应锦囊节点 |
| kits.json × 8 | 节点 `node-kit-a` ~ `node-kit-h` | label =「字母 · 名称」；description = mechanism |
| kits.json next_kits | 节点出向连接 | preset_weight 按顺序 1.0 / 0.9 递减，connection_type = preset |

锦囊循环：A 锚点确立 → B 迷失预警 → C 负向沉沦 → D 自防御后 →（回到 A / E 回归执行者）
→ F 具身认知临战 → G 复盘提取 → A；H 提前复盘警告 → E（拦截路径）。

## 三、导入执行

```bash
# 启动后端
python backend/run.py

# CLI 远程模式：校验 → 预览 → 导入
set KN_BACKEND_MODE=remote
kn-cli yaml validate imports/cognitive-cards-kits.yaml
kn-cli yaml preview  imports/cognitive-cards-kits.yaml
kn-cli yaml import   imports/cognitive-cards-kits.yaml
```

## 四、导入结果（2026-07-26 验证）

- 校验通过：19 张卡片 + 8 个节点；预览：新增 19 / 8，覆盖 0
- 导入后总量：**37 张认知卡片 + 25 个导航节点**（44 条图边，其中 11 条锦囊环路）
- `root/7` 下 18 张子卡片；每个锦囊节点绑定对应锦囊卡片（浏览站点时可翻阅语料）
- 路线规划验证：`plan generate --ids node-kit-a,node-kit-e,node-kit-g`
  → Plan A（推荐，权重 0.95）：G 复盘提取 → A 锚点确立 → E 回归执行者
- 持久化：`backend/data.yaml` 已落盘（35 KB，gitignored），重启后端数据保留

## 五、一键启动

`start-dev.bat`：同时启动 FastAPI 后端（8171）与 Vite 前端开发服务器。

- 远程模式切换：管理界面 ⚙ → 远程模式 → `http://localhost:8171` → 保存
- 或 URL 参数：`http://localhost:5173/?backend_mode=remote`

## 六、后续可选

- 概念卡片 ↔ 锦囊节点的语义绑定（当前概念卡片未绑定节点，可按 tags/keywords 重叠自动关联）
- `kits.json` 的 `path_rules`（from_designer_stuck 等入口规则）可作为预设路线模板导入
