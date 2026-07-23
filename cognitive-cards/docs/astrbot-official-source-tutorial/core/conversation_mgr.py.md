# 文件教程：core/conversation_mgr.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\conversation_mgr.py`
- 文件类型：`.py`
- 文件大小：`16637` 字节
- 所属目录教程：[core](README.md)

## 它是做什么的

AstrBot 会话-对话管理器, 维护两个本地存储, 其中一个是 json 格式的shared_preferences, 另外一个是数据库

## 角色判断

这个文件位于核心实现层，通常承载底层机制、抽象或运行时行为。

## 模块文档字符串

AstrBot 会话-对话管理器, 维护两个本地存储, 其中一个是 json 格式的shared_preferences, 另外一个是数据库.

在 AstrBot 中, 会话和对话是独立的, 会话用于标记对话窗口, 例如群聊"123456789"可以建立一个会话,
在一个会话中可以建立多个对话, 并且支持对话的切换和删除

## 顶层导入

- `json`
- `from collections.abc import Awaitable, Callable`
- `from astrbot.core import sp`
- `from astrbot.core.agent.message import AssistantMessageSegment, UserMessageSegment`
- `from astrbot.core.db import BaseDatabase`
- `from astrbot.core.db.po import Conversation, ConversationV2`
- `from astrbot.core.utils.datetime_utils import to_utc_timestamp`

## 顶层类

- `ConversationManager`：负责管理会话与 LLM 的对话，某个会话当前正在用哪个对话

## 顶层函数

- 无顶层函数定义。

## 阅读建议

- 建议从模块文档字符串、顶层类和顶层函数出发，再搜索这些名字的调用位置。

## 同目录相关文件

- [__init__.py](__init__.py.md)
- [astr_agent_context.py](astr_agent_context.py.md)
- [astr_agent_hooks.py](astr_agent_hooks.py.md)
- [astr_agent_run_util.py](astr_agent_run_util.py.md)
- [astr_agent_tool_exec.py](astr_agent_tool_exec.py.md)
- [astr_main_agent.py](astr_main_agent.py.md)
- [astr_main_agent_resources.py](astr_main_agent_resources.py.md)
- [astrbot_config_mgr.py](astrbot_config_mgr.py.md)
- [core_lifecycle.py](core_lifecycle.py.md)
- [event_bus.py](event_bus.py.md)
- [exceptions.py](exceptions.py.md)
- [file_token_service.py](file_token_service.py.md)
- [initial_loader.py](initial_loader.py.md)
- [log.py](log.py.md)
- [persona_error_reply.py](persona_error_reply.py.md)
- 其余 7 个同目录文件省略

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。