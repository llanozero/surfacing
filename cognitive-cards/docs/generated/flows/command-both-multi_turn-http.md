# 插件功能规格草案

## 1. 功能摘要

- 功能定位：指令触发 + 私聊发起 + 群内执行 + 多轮交互 + HTTP 集成
- 说明：从触发、会话、回复、AI 与外部集成五个维度反推应该读哪些 AstrBot 源码。

## 2. 需求拼装结果

- 触发方式：指令
- 会话范围：私聊 + 群聊
- 回复节奏：多轮回复
- 外部集成：HTTP 请求

## 3. 关键依赖链

### 指令识别链

- 主链路：`Plugin handler -> command filter -> 参数转换 -> 进入业务函数`
- 解读：当你需要 `/命令 参数` 时，先掌握 filter 层怎样把字符串转成 Python 参数。

### 私聊发起 + 群内执行链

- 主链路：`私聊命令发起 -> 保存目标群上下文 -> 群内授权/执行 -> 主动回推结果`
- 解读：这正是你当前投票规格最需要的组合链路。

### 多轮交互链

- 主链路：`插件注册 waiter -> USER_SESSIONS/FILTERS -> session_controller 转发后续消息 -> waiter trigger`
- 解读：多轮交互不是轮询，而是依赖 SessionWaiter 体系。

### HTTP 集成链

- 主链路：`Plugin service -> HTTP client -> 外部服务 -> 返回结果 -> AstrBot reply`
- 解读：建议抽服务层，不要把请求细节直接塞进 handler。

## 4. 应优先阅读的官方源码

### core/star/context.py

- 作用：插件上下文桥梁
- 为什么看它：插件几乎都通过 Context 触达平台、Provider、会话与主动发送能力。
- 本地路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\star\context.py`

### core/platform/astr_message_event.py

- 作用：事件对象与回复接口
- 为什么看它：看清 `plain_result`、`image_result`、`send`、`unified_msg_origin` 的定义。
- 本地路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\platform\astr_message_event.py`

### core/message/message_event_result.py

- 作用：消息结果结构
- 为什么看它：所有 yield/发送结果最终都会落到 MessageChain 与 MessageEventResult。
- 本地路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\message\message_event_result.py`

### core/platform/message_type.py

- 作用：消息类型枚举
- 为什么看它：私聊、群聊、其他消息类型的权威枚举定义在这里。
- 本地路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\platform\message_type.py`

### core/star/filter/command.py

- 作用：命令过滤器
- 为什么看它：定义指令命中、参数切分、类型转换、GreedyStr 行为。
- 本地路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\star\filter\command.py`

### core/platform/message_session.py

- 作用：会话标识
- 为什么看它：发起端和执行端会话不同，必须靠统一会话标识串起来。
- 本地路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\platform\message_session.py`

### core/utils/session_waiter.py

- 作用：会话等待器
- 为什么看它：多轮交互的底层状态机、过滤器和超时都在这里。
- 本地路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\utils\session_waiter.py`

### builtin_stars/session_controller/main.py

- 作用：系统会话控制插件
- 为什么看它：它负责把后续消息真正转给活动 waiter。
- 本地路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\builtin_stars\session_controller\main.py`

### plugins/astrbot_plugin_proxy_agent/web_client.py

- 作用：当前插件 Web 代理参考
- 为什么看它：你自己的插件已经有 `backend_mode=web` 参考实现。
- 本地路径：`plugins/astrbot_plugin_proxy_agent/web_client.py`

## 5. 当前插件建议落点

- 抽到 `p00_shared/` 或独立 service 模块：如果会被多个命令复用，或者未来要切 `local/web` 双实现，先做服务边界。
- 单独 manager 模块：多轮流程、状态机、超时和权限最好收口到 manager，而不是继续堆在 `main.py`。
- 优先归到 `p05_afternoon_collab/`：代理、投票、群协作、选择器都属于当前插件的协作主线。

## 6. 当前插件中最接近的现有模块

### main.py

- 角色：插件总协调入口
- 为什么接近：负责注册命令、实例化 manager、维护会话状态，以及统一发送辅助方法。
- 适合承接：普通命令入口；会话状态管理
- 本地路径：`C:\Users\llano\.astrbot\data\plugins\astrbot_plugin_proxy_agent\main.py`

### p05_afternoon_collab/vote_manager.py

- 角色：群协作与跨会话流程中心
- 为什么接近：已经实现私聊发起、群内授权、成员参与、结果收口的复杂状态流。
- 适合承接：私聊发起 + 群内执行；授权与投票状态机
- 本地路径：`C:\Users\llano\.astrbot\data\plugins\astrbot_plugin_proxy_agent\p05_afternoon_collab\vote_manager.py`

### p05_afternoon_collab/interactive_selector.py

- 角色：多轮选择器样板
- 为什么接近：当前插件里最直接的 SessionWaiter 多轮交互模板。
- 适合承接：多轮问答；分页选择目标用户/群/成员
- 本地路径：`C:\Users\llano\.astrbot\data\plugins\astrbot_plugin_proxy_agent\p05_afternoon_collab\interactive_selector.py`

### p06_evening_invest/story_manager.py

- 角色：结构化多轮内容流
- 为什么接近：适合参考多轮互动内容浏览和生成式扩展。
- 适合承接：剧情式多轮流程；结构化内容树
- 本地路径：`C:\Users\llano\.astrbot\data\plugins\astrbot_plugin_proxy_agent\p06_evening_invest\story_manager.py`

### p06_evening_invest/multi_role_manager.py

- 角色：LLM 驱动对话 manager
- 为什么接近：当前插件中最接近 LLM 上下文组装、角色切换和 AI 回复生成的现有模块。
- 适合承接：文本 LLM；角色式回复
- 本地路径：`C:\Users\llano\.astrbot\data\plugins\astrbot_plugin_proxy_agent\p06_evening_invest\multi_role_manager.py`

### web_client.py

- 角色：Web 代理层
- 为什么接近：演示本地实现和 HTTP 后端之间如何做一层客户端代理。
- 适合承接：HTTP 集成；local/web 双实现切换
- 本地路径：`C:\Users\llano\.astrbot\data\plugins\astrbot_plugin_proxy_agent\web_client.py`

### p05_afternoon_collab/session_registry.py

- 角色：本地持久化服务样板
- 为什么接近：展示了当前插件里简单数据持久化服务的边界。
- 适合承接：本地 JSON 存储；用户关系或频次统计
- 本地路径：`C:\Users\llano\.astrbot\data\plugins\astrbot_plugin_proxy_agent\p05_afternoon_collab\session_registry.py`

## 7. 推荐改动步骤

### 第 1 步：对齐触发与会话入口

- 先看官方：`core/star/context.py`
- 优先落到：`main.py`
- 要做什么：先把命令、正则或监听入口跑通，顺手确认私聊/群聊/跨会话标识怎样进入业务层。
- 为什么现在做：入口和会话一旦判断错，后面的多轮、主动回复、HTTP 集成都容易返工。

### 第 2 步：收口业务状态与模块边界

- 先看官方：`core/platform/astr_message_event.py`
- 优先落到：`p05_afternoon_collab/vote_manager.py`
- 要做什么：把状态机、服务层或 manager 放进最合适的现有模块，同时遵循 抽到 `p00_shared/` 或独立 service 模块。
- 为什么现在做：这一步决定代码是继续堆在入口里，还是沉到可复用模块。

### 第 3 步：补齐回复链与回推链

- 先看官方：`core/platform/astr_message_event.py`
- 优先落到：`main.py`
- 要做什么：实现当前回复、主动回推、延时结束或多轮等待的具体发送动作，并补超时、取消、结束提示。
- 为什么现在做：回复链通常跨越事件返回、主动发送和状态清理三层，单独梳理最稳。

### 第 4 步：收口外部接口与部署边界

- 先看官方：`plugins/astrbot_plugin_proxy_agent/web_client.py`
- 优先落到：`web_client.py`
- 要做什么：把本地实现与远端实现整理成同形接口，再决定是否走 Web 后端或复用官方 OpenAPI。
- 为什么现在做：把集成边界放到最后，能减少前期为了部署方式反复改业务层。

## 8. 实现前检查

- 确定命令名和别名是否唯一。
- 先决定参数签名，再决定文案。
- 把私聊发起状态与群内执行状态拆开保存。
- 在规格里明确谁能授权、谁能投票、谁能采纳。
- 设计每一步提示、取消词和超时文案。
- 把多轮状态收口到单独 manager，不要散在 main.py。
- 先画清本地实现和 HTTP 代理的同形接口。
- 为失败、超时和重试留统一错误层。

## 9. 风险与规格提醒

- 这是跨会话功能，规格里要单独写清发起端、执行端、通知端三种身份。
- 多轮状态如果放远端，要先定义超时同步和取消语义。

## 10. 开发顺序建议

- 按右侧源码清单逐个打开权威文件，先验证你对触发链和回复链的假设。
- 把需求拆成 `trigger / session / reply / intelligence / integration` 五栏，避免一开始就写大而全模块。
- 先用最小 handler 跑通链路，再把状态机和服务层外提。
- 先画出每一轮提示、等待条件、超时出口，再开始写 SessionWaiter。
- 单独画一条“私聊发起 -> 群内授权 -> 主动回推”时序图，最容易提前发现规格冲突。
- 给本地实现和 HTTP 代理设计同形接口，后续切换部署方式才不会牵动命令层。

## 11. 建议写入正式规格的句子

- 本功能采用“指令触发 + 私聊发起 + 群内执行 + 多轮交互 + HTTP 集成”的组合实现方式。
- 规格必须明确触发端、执行端、通知端是否属于同一会话。
- 规格必须明确需要依赖的官方源码入口和插件内落点。