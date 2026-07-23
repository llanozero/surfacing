# 文件教程：core/agent/runners/tool_loop_agent_runner.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\agent\runners\tool_loop_agent_runner.py`
- 文件类型：`.py`
- 文件大小：`58250` 字节
- 所属目录教程：[core/agent/runners](README.md)

## 它是做什么的

这个文件主要定义了 _HandleFunctionToolsResult、FollowUpTicket、_ToolExecutionInterrupted 等顶层类。

## 角色判断

这个文件位于核心实现层，通常承载底层机制、抽象或运行时行为。

## 模块文档字符串

这个文件没有显式模块文档字符串，可以重点看顶层类、函数和导入关系。

## 顶层导入

- `asyncio`
- `copy`
- `sys`
- `time`
- `traceback`
- `typing`
- `uuid`
- `from collections.abc import AsyncIterator`
- `from contextlib import suppress`
- `from dataclasses import dataclass, field`
- `from pathlib import Path`
- `from mcp.types import BlobResourceContents, CallToolResult, EmbeddedResource, ImageContent, TextContent, TextResourceContents`
- `from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential`
- `from astrbot import logger`
- `from astrbot.core.agent.message import ImageURLPart, TextPart, ThinkPart`
- `from astrbot.core.agent.tool import FunctionTool, ToolSet`
- `from astrbot.core.agent.tool_image_cache import tool_image_cache`
- `from astrbot.core.exceptions import EmptyModelOutputError`
- `from astrbot.core.message.components import Json`
- `from astrbot.core.message.message_event_result import MessageChain`
- 其余 13 条导入省略

## 顶层类

- `_HandleFunctionToolsResult`：建议阅读类定义与方法名来判断职责。
- `FollowUpTicket`：建议阅读类定义与方法名来判断职责。
- `_ToolExecutionInterrupted`：Raised when a running tool call is interrupted by a stop request
- `ToolLoopAgentRunner`：建议阅读类定义与方法名来判断职责。

## 顶层函数

- 无顶层函数定义。

## 阅读建议

- 建议从模块文档字符串、顶层类和顶层函数出发，再搜索这些名字的调用位置。

## 同目录相关文件

- [__init__.py](__init__.py.md)
- [base.py](base.py.md)

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。