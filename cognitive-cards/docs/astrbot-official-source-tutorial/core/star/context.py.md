# 文件教程：core/star/context.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\star\context.py`
- 文件类型：`.py`
- 文件大小：`27001` 字节
- 所属目录教程：[core/star](README.md)

## 它是做什么的

这个文件主要定义了 PlatformManagerProtocol、Context 等顶层类。

## 角色判断

这个文件位于核心实现层，通常承载底层机制、抽象或运行时行为。

## 模块文档字符串

这个文件没有显式模块文档字符串，可以重点看顶层类、函数和导入关系。

## 顶层导入

- `from __future__ import annotations`
- `logging`
- `from asyncio import Queue`
- `from collections.abc import Awaitable, Callable`
- `from typing import TYPE_CHECKING, Any, Protocol`
- `from deprecated import deprecated`
- `from astrbot.core.agent.hooks import BaseAgentRunHooks`
- `from astrbot.core.agent.message import Message`
- `from astrbot.core.agent.runners.tool_loop_agent_runner import ToolLoopAgentRunner`
- `from astrbot.core.agent.tool import ToolSet`
- `from astrbot.core.astrbot_config_mgr import AstrBotConfigManager`
- `from astrbot.core.config.astrbot_config import AstrBotConfig`
- `from astrbot.core.conversation_mgr import ConversationManager`
- `from astrbot.core.db import BaseDatabase`
- `from astrbot.core.knowledge_base.kb_mgr import KnowledgeBaseManager`
- `from astrbot.core.message.message_event_result import MessageChain`
- `from astrbot.core.persona_mgr import PersonaManager`
- `from astrbot.core.platform import Platform`
- `from astrbot.core.platform.astr_message_event import AstrMessageEvent, MessageSesion`
- `from astrbot.core.platform_message_history_mgr import PlatformMessageHistoryManager`
- 其余 12 条导入省略

## 顶层类

- `PlatformManagerProtocol`：建议阅读类定义与方法名来判断职责。
- `Context`：暴露给插件的接口上下文

## 顶层函数

- 无顶层函数定义。

## 阅读建议

- 建议从模块文档字符串、顶层类和顶层函数出发，再搜索这些名字的调用位置。

## 同目录相关文件

- [__init__.py](__init__.py.md)
- [base.py](base.py.md)
- [command_management.py](command_management.py.md)
- [config.py](config.py.md)
- [error_messages.py](error_messages.py.md)
- [README.md](README.md.md)
- [session_llm_manager.py](session_llm_manager.py.md)
- [session_plugin_manager.py](session_plugin_manager.py.md)
- [star.py](star.py.md)
- [star_handler.py](star_handler.py.md)
- [star_manager.py](star_manager.py.md)
- [star_tools.py](star_tools.py.md)
- [updator.py](updator.py.md)

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。