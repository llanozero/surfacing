# 插件功能规格草案

## 1. 功能摘要

- 功能定位：指令触发
- 说明：从触发、会话、回复、AI 与外部集成五个维度反推应该读哪些 AstrBot 源码。

## 2. 需求拼装结果

- 触发方式：指令

## 3. 关键依赖链

### 指令识别链

- 主链路：`Plugin handler -> command filter -> 参数转换 -> 进入业务函数`
- 解读：当你需要 `/命令 参数` 时，先掌握 filter 层怎样把字符串转成 Python 参数。

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

## 5. 当前插件建议落点

- 放在 `main.py` + 轻量 helper：如果只是单次指令、无复杂状态，直接在命令入口附近实现最省维护成本。

## 6. 当前插件中最接近的现有模块

### main.py

- 角色：插件总协调入口
- 为什么接近：负责注册命令、实例化 manager、维护会话状态，以及统一发送辅助方法。
- 适合承接：普通命令入口；会话状态管理
- 本地路径：`C:\Users\llano\.astrbot\data\plugins\astrbot_plugin_proxy_agent\main.py`

## 7. 实现前检查

- 确定命令名和别名是否唯一。
- 先决定参数签名，再决定文案。

## 8. 风险与规格提醒

- 当前组合暂无额外结构性风险提示。

## 9. 开发顺序建议

- 按右侧源码清单逐个打开权威文件，先验证你对触发链和回复链的假设。
- 把需求拆成 `trigger / session / reply / intelligence / integration` 五栏，避免一开始就写大而全模块。
- 先用最小 handler 跑通链路，再把状态机和服务层外提。

## 10. 建议写入正式规格的句子

- 本功能采用“指令触发”的组合实现方式。
- 规格必须明确触发端、执行端、通知端是否属于同一会话。
- 规格必须明确需要依赖的官方源码入口和插件内落点。