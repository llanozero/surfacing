# astrbot_plugin_proxy_agent 开发者模块手册

## 1. 文档目的

这份文档面向继续维护 `plugins/astrbot_plugin_proxy_agent/` 的开发者。

目标有三件事：

1. 说明 `@ecc` 在当前 Codex 会话里如何使用。
2. 以 AstrBot 官方源码为权威依据，梳理当前插件依赖的关键 API。
3. 按模块拆解当前插件的职责、入口、调用链和后续扩展点。

如果你现在想按官方源码树逐个目录、逐个文件查阅，请直接看：

- [AstrBot 官方源码遍历教程](/c:/Users/llano/.astrbot/data/plugins/astrbot_plugin_proxy_agent/docs/astrbot-official-source-tutorial/README.md)

---

## 2. `@ecc` 在当前会话里怎么用

`[@ecc](plugin://ecc@openai-curated)` 指的是当前会话启用的 `Everything Claude Code` 插件能力集合。

它不是你项目目录里的 Python 依赖，也不是 AstrBot 插件代码的一部分，而是 Codex 在当前开发会话里可调用的一组增强能力。

当前可用能力包括：

- `context7`：查官方库文档
- `exa`：网页搜索与抓取
- `github`：GitHub 仓库/PR/Issue 操作
- `playwright`：浏览器自动化
- `memory`：知识图谱式记忆
- `sequential-thinking`：结构化推理

在实际协作里，可以直接用自然语言触发，比如：

- “用 `@ecc` 查一下某个库最新官方文档”
- “用 `@ecc` 搜索 AstrBot 某个接口的公开示例”
- “用 `@ecc` 帮我审查这个 PR”

如果任务本身是“继续开发当前插件”，`@ecc` 更适合作为辅助研究与校验工具，而不是项目运行时依赖。

---

## 3. AstrBot 官方权威定义

下面这些定义都来自你提供的官方源码目录：

`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot`

### 3.1 事件返回与主动发送

权威来源：

- `core/platform/astr_message_event.py`
- `core/message/message_event_result.py`
- `core/star/context.py`

关键结论：

- `event.plain_result(text)` 返回的是 `MessageEventResult().message(text)`。
- `event.image_result(url_or_path)` 会根据 `http` 或本地路径构造图片结果。
- `event.send(message_chain)` 用于把一条 `MessageChain` 发回当前事件上下文。
- `context.send_message(session, message_chain)` 用于主动向指定 `session/unified_msg_origin` 发送消息。

这直接对应当前插件中的三种发送路径：

1. `yield event.plain_result(...)`
2. `await event.send(MessageChain(...))`
3. `await self.context.send_message(umo, chain)`

开发建议：

- 回复当前指令上下文，优先用 `yield event.plain_result(...)` 或 `_send_auto(...)`。
- 在非生成器上下文里临时给当前会话发消息，用 `await event.send(...)`。
- 跨会话、跨用户、跨群主动推送，用 `context.send_message(...)`。

### 3.2 MessageChain 与消息组件

权威来源：

- `core/message/message_event_result.py`
- `core/message/components.py`

关键结论：

- `MessageChain` 本质上是有序的组件列表。
- 可链式调用 `.message()`、`.at()`、`.url_image()`、`.file_image()`、`.base64_image()`。
- `Plain`、`At`、`Image` 都是基础消息组件。
- `Image.fromBase64(...)` 支持 `base64://...` 形式的图片消息。

这解释了当前插件里的实现方式：

- `_send_auto()` 里用 `event.make_result().base64_image(...)`
- `_forward_to_group_target()` 里手动拼 `Comp.At` + `Comp.Plain`
- `_send_to_user()` 里用 `MessageChain().message(content)`

### 3.3 SessionWaiter 机制

权威来源：

- `core/utils/session_waiter.py`

关键结论：

- `USER_SESSIONS` 保存活动中的 `SessionWaiter`
- `FILTERS` 保存 `SessionFilter`
- `DefaultSessionFilter.filter(event)` 默认返回 `event.unified_msg_origin`
- `SessionWaiter.register_wait()` 的核心是 `keep(timeout, reset_timeout=True)`

当前插件没有完全走装饰器式 `@session_waiter(...)` 用法，而是直接操作：

- `USER_SESSIONS`
- `FILTERS`
- `SessionWaiter`
- `DefaultSessionFilter`

这是 `InteractiveSelector`、`StoryManager`、`MultiRoleManager`、`VoteManager` 多轮交互都能稳定工作的底层原因。

### 3.4 插件元数据

权威来源：

- `core/star/star.py`

关键结论：

- AstrBot 插件元数据包含 `name`、`author`、`desc`、`version`、`repo`
- `support_platforms` 是声明支持的平台适配器 ID 列表
- `astrbot_version` 使用类似 `>=4.16` 的版本范围

因此本插件的 `metadata.yaml` 应尽量与 `@register(...)` 和真实平台能力保持一致。

---

## 4. 项目总览

当前插件目录：

```text
plugins/astrbot_plugin_proxy_agent/
├── main.py
├── _conf_schema.json
├── metadata.yaml
├── README.md
├── web_client.py
├── data/
├── docs/
├── p00_shared/
├── p01_night_rest/
├── p02_morning_plan/
├── p03_morning_focus/
├── p04_noon_repair/
├── p05_afternoon_collab/
└── p06_evening_invest/
```

当前真正已有实现的核心在：

- `main.py`
- `p00_shared/`
- `p02_morning_plan/`
- `p05_afternoon_collab/`
- `p06_evening_invest/`
- `web_client.py`

`p01`、`p03`、`p04` 目前更接近预留阶段目录。

---

## 5. 主入口：`main.py`

文件：

- `plugins/astrbot_plugin_proxy_agent/main.py`

### 5.1 它负责什么

`ProxyAgentPlugin` 是总协调器，负责：

- 读取配置
- 条件实例化模块
- 注册所有指令
- 管理运行中会话
- 统一消息发送辅助方法

### 5.2 主要运行时状态

关键字段：

- `self.sessions`：当前活跃/已关闭但尚未清理的代理会话
- `self.user_sessions`：用户到会话 ID 的映射
- `self.user_platform_id`：用户到平台 ID 的映射
- `self.registry`：历史频次统计
- `self.selector`：交互式代理选择器
- `self.vote_manager`：投票管理器
- `self.todo_manager`：代办服务
- `self.story_manager`：剧情管理器
- `self.multi_role_manager`：多角色管理器

### 5.3 指令入口分布

基础代理：

- `/代理`
- `/关闭代理`
- `/代理状态`
- `/代理选择`

管理员会话管理：

- `/admin_list`
- `/admin_reply`
- `/admin_close`
- `/admin_broadcast`

投票：

- 私聊 `/发起投票`
- 群内 `/授权` `/提议` `/投票` `/投票结果` `/结束投票` `/采纳`

扩展模块：

- `/代办`
- `/剧情`
- `/角色对话`
- `/扮演`
- `/回应`

### 5.4 开发时优先看哪些辅助方法

- `_record_platform()`：主动消息能否发出去，关键依赖它缓存 platform ID
- `_send_auto()`：所有“插件主动回复”建议走这里
- `_send_to_user()`：主动私聊发送
- `_forward_to_group_target()`：群聊代理发消息
- `_close_session()`：会话清理和通知

---

## 6. 共享层：`p00_shared`

### 6.1 `paginator.py`

职责：

- 为列表型交互提供统一分页能力

典型使用场景：

- `/代理选择` 的好友列表
- `/代理选择` 的群聊列表
- `/代理选择` 的群成员列表

核心接口：

- `render_page()`
- `next_page()`
- `prev_page()`
- `goto_page(n)`
- `get_item(item_index)`

适合继续扩展的方向：

- 支持自定义页脚提示
- 支持不同 `PAGE_SIZE`
- 支持页头标题

### 6.2 `long_message_renderer.py`

职责：

- 把长文本渲染成 PNG

当前接入方式：

- 不直接暴露命令
- 由 `main.py` 中 `_send_auto()` 在文本过长时自动调用

开发注意：

- 这是“插件主动回复”的渲染层，不应该用于转发用户原始消息
- 如果你后续单独实现 `admin_list` 的强制图片模式，可以继续复用这个思路

---

## 7. 协作主线：`p05_afternoon_collab`

这是当前插件最成熟、最接近主业务的模块组。

### 7.1 `models.py`

职责：

- 定义 `ProxySession`
- 定义 `VoteOption`
- 定义 `VoteSession`

你改业务规则时，先看这里：

- 会话状态字段是否够用
- 投票权限和采纳结果是否需要扩展

### 7.2 `session_registry.py`

职责：

- 把 `user_a:user_b -> count` 持久化到 `data/session_frequency.json`

当前用途：

- `/admin_list` 个性化排序
- 会话创建时统计历史频次

何时改它：

- 想增加时间衰减
- 想记录最后活跃时间
- 想导出关系图谱

### 7.3 `admin_list_renderer.py`

职责：

- 渲染 `/admin_list`

当前有两种内容模式：

- `standard`
- `personalized`

注意：

- 这个模块负责“内容组织”
- 当前文本/图片发送形式不由它决定，而是由 `main.py` 的 `_send_auto()` 接管

所以如果你想彻底理顺列表渲染，最好把“排序/字段”和“输出媒介”继续拆开。

### 7.4 `aiocqhttp_adapter.py`

职责：

- 包装 aiocqhttp 平台 API
- 提供好友列表、群列表、群成员列表获取

它是交互式选择器与平台之间的适配层。

何时优先改它：

- 平台 API 行为变动
- 需要更严格的平台探测逻辑
- 需要缓存群成员列表

### 7.5 `interactive_selector.py`

职责：

- 实现 `/代理选择`

当前结构：

1. 检查用户是否已有会话
2. 检查当前平台是否支持
3. 进入模式选择
4. 进入好友/群/成员分页选择
5. 最终调用插件的 `_create_proxy_session(...)`

开发重点：

- 它通过 `SessionWaiter + asyncio.Queue` 接收下一条消息
- 用 `_raw_wait()` 统一处理超时与取消
- 用 `_pager_loop()` 统一处理翻页和选项输入

这部分已经是一个很好的可复用交互模板，后续如果你要加新的多轮选择功能，建议直接仿照它。

### 7.6 `vote_manager.py`

职责：

- 负责整个投票生命周期

当前口径：

1. 管理员私聊 `/发起投票`
2. 交互收集问题、选项、目标群、模式
3. 在群里发布公告
4. 管理员用 `/授权` 给成员加权限
5. 成员 `/提议`、`/投票`
6. 管理员 `/结束投票`、`/采纳`

开发重点：

- 它本质上是“群级投票管理器”，不是 ProxySession 的从属对象
- 定时结束和自动采纳都在这里
- 投票历史落到 `data/vote_history.json`

后续如果你要继续增强投票，优先考虑加这些点：

- 更清晰的投票状态机
- 按群隔离的唯一活跃投票约束
- 采纳后自动生成可发送草稿

---

## 8. 清晨模块：`p02_morning_plan`

### 8.1 `todo_manager.py`

职责：

- 管理 `data/todo_list.json`
- 实现代办的增删改查与文本渲染

当前暴露入口：

- `/代办`
- `/代办 帮助`
- `/代办 新增`
- `/代办 删除`
- `/代办 切换`
- `/代办 状态`

特点：

- 目前是最独立、最容易继续开发的模块之一
- 业务边界清晰，和代理主线耦合低

适合优先追加的能力：

- 优先级
- 截止日期
- 标签
- 搜索和筛选

---

## 9. 晚间模块：`p06_evening_invest`

### 9.1 `story_manager.py`

职责：

- 实现 `/剧情`
- 读取 `story_trees/*.yaml`
- 支持互动式剧情浏览和 AI 生成新分支

它适合被看作“结构化内容浏览器 + 分支生成器”。

如果你继续开发：

- 优先考虑把剧情树数据结构文档化
- 再考虑把 AI 生成流程单独下沉到服务层

### 9.2 `multi_role_manager.py`

职责：

- 实现 `/角色对话`
- 选择对话组、历史记录并分页展示
- 支持在上下文中执行 `/扮演` 和 `/回应`

与主插件的配合关系：

- `main.py` 负责注册命令
- `MultiRoleManager` 负责选择、加载和维护当前活跃历史记录
- `/回应` 最终通过 `self.context.llm_generate(...)` 调模型

开发建议：

- 这是当前最依赖 LLM Provider 的子模块
- 如果后续要增强模型切换、提示词模板、上下文裁剪，优先改这块

---

## 10. Web 同步层：`web_client.py`

职责：

- 在 `backend_mode=web` 时，提供 HTTP 代理

当前已代理的能力：

- 代办：`TodoClientProxy`
- 会话频次：`SessionRegistryProxy`

当前还没有全面代理的能力：

- 代理会话本身
- 投票会话
- 剧情/多角色数据

所以目前的 `web` 模式更准确地说是“局部同步模式”，不是完整后端化。

如果你要继续推进 Web 化，建议按下面顺序：

1. 统一服务接口抽象
2. 把本地实现和 Web 代理做成同形 service
3. 再逐步把投票和会话迁走

---

## 11. 数据目录：`data/`

当前已见到的持久化文件：

- `session_frequency.json`
- `vote_history.json`
- `todo_list.json`

这三类数据目前都是单机本地文件模式，适合快速开发，但后续要注意：

- 并发写入
- 损坏恢复
- 历史清理
- 迁移到 Web/数据库时的兼容策略

---

## 12. 开发时最常见的判断题

### 12.1 什么时候 `yield event.plain_result(...)`

当你在命令 handler 里，想回复当前这条指令时。

### 12.2 什么时候 `await event.send(...)`

当你不在 `yield` 返回链路里，但仍想向“当前事件对应的会话”发一条消息时。

### 12.3 什么时候 `context.send_message(...)`

当你想主动向别的用户/群/管理员发消息时。

### 12.4 什么时候自己维护 `SessionWaiter`

当你要做多轮交互，并且需要：

- 自定义超时
- 接管取消逻辑
- 控制每一步重注册 waiter

这正是当前 `InteractiveSelector`、`VoteManager`、`StoryManager`、`MultiRoleManager` 的做法。

### 12.5 什么时候新增独立模块，而不是继续往 `main.py` 塞

满足下面任一条就该拆模块：

- 有独立状态和数据文件
- 有单独的多轮交互流程
- 有稳定的输入输出接口
- 后续可能切换为 Web 后端

---

## 13. 推荐的继续开发顺序

如果目标是“继续推进插件开发”，建议按这个顺序做：

1. 收口 `p05_afternoon_collab`
   - 先把代理、列表、投票主链路打磨稳定
2. 收口服务边界
   - 明确哪些模块支持 `local/web` 双实现
3. 为多轮交互提取共用基类或工具
   - 减少 `SessionWaiter + Queue` 重复代码
4. 给 `p02` 和 `p06` 增加文档与测试
   - 它们已经能用，但维护信息还不够集中
5. 再考虑推进 `p01/p03/p04`

---

## 14. 附：建议优先阅读的源码文件

AstrBot 官方：

- `C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\platform\astr_message_event.py`
- `C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\message\message_event_result.py`
- `C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\message\components.py`
- `C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\utils\session_waiter.py`
- `C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\star\context.py`
- `C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\star\star.py`

当前插件：

- `plugins/astrbot_plugin_proxy_agent/main.py`
- `plugins/astrbot_plugin_proxy_agent/p00_shared/paginator.py`
- `plugins/astrbot_plugin_proxy_agent/p00_shared/long_message_renderer.py`
- `plugins/astrbot_plugin_proxy_agent/p05_afternoon_collab/interactive_selector.py`
- `plugins/astrbot_plugin_proxy_agent/p05_afternoon_collab/vote_manager.py`
- `plugins/astrbot_plugin_proxy_agent/p05_afternoon_collab/admin_list_renderer.py`
- `plugins/astrbot_plugin_proxy_agent/p02_morning_plan/todo_manager.py`
- `plugins/astrbot_plugin_proxy_agent/p06_evening_invest/story_manager.py`
- `plugins/astrbot_plugin_proxy_agent/p06_evening_invest/multi_role_manager.py`
- `plugins/astrbot_plugin_proxy_agent/web_client.py`

---

## 15. 这份文档的使用方式

建议把它当成三个入口文档来用：

- 想查“某条能力从哪个命令进入”时，看第 5 节。
- 想查“某个模块内部该怎么改”时，看第 6 到第 10 节。
- 想查“AstrBot 官方到底怎么定义发送和等待”时，看第 3 节。

如果后续你新增了 `p01/p03/p04` 的真实实现，建议直接续写到本文件，而不是另起零散说明。
