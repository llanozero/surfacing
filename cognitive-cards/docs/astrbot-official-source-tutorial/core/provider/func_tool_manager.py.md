# 文件教程：core/provider/func_tool_manager.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\provider\func_tool_manager.py`
- 文件类型：`.py`
- 文件大小：`37317` 字节
- 所属目录教程：[core/provider](README.md)

## 它是做什么的

这个文件主要定义了 MCPInitError、MCPInitTimeoutError、MCPAllServicesFailedError 等顶层类。

## 角色判断

这是一个管理器文件，通常持有运行时状态，并负责编排一类业务流程。

## 模块文档字符串

这个文件没有显式模块文档字符串，可以重点看顶层类、函数和导入关系。

## 顶层导入

- `from __future__ import annotations`
- `asyncio`
- `copy`
- `json`
- `os`
- `threading`
- `urllib.parse`
- `from collections.abc import AsyncGenerator, Awaitable, Callable, Mapping`
- `from dataclasses import dataclass`
- `from types import MappingProxyType`
- `from typing import Any`
- `aiohttp`
- `from astrbot import logger`
- `from astrbot.core import sp`
- `from astrbot.core.agent.mcp_client import MCPClient, MCPTool`
- `from astrbot.core.agent.tool import FunctionTool, ToolSet`
- `from astrbot.core.tools.registry import ensure_builtin_tools_loaded, get_builtin_tool_class, get_builtin_tool_name, iter_builtin_tool_classes`
- `from astrbot.core.utils.astrbot_path import get_astrbot_data_path`

## 顶层类

- `MCPInitError`：Base exception for MCP initialization failures
- `MCPInitTimeoutError`：Raised when MCP client initialization exceeds the configured timeout
- `MCPAllServicesFailedError`：Raised when all configured MCP services fail to initialize
- `MCPShutdownTimeoutError`：Raised when MCP shutdown exceeds the configured timeout
- `MCPInitSummary`：建议阅读类定义与方法名来判断职责。
- `_MCPServerRuntime`：建议阅读类定义与方法名来判断职责。
- `_MCPClientDictView`：Read-only view of MCP clients derived from runtime state
- `FunctionToolManager`：建议阅读类定义与方法名来判断职责。

## 顶层函数

- `_resolve_timeout`：Resolve timeout with precedence: explicit argument > env value > default
- `_prepare_config`：准备配置，处理嵌套格式
- `_quick_test_mcp_connection`：快速测试 MCP 服务器可达性

## 阅读建议

- 重点看内部状态字段、生命周期和跨模块调用。
- 建议从模块文档字符串、顶层类和顶层函数出发，再搜索这些名字的调用位置。

## 同目录相关文件

- [__init__.py](__init__.py.md)
- [entites.py](entites.py.md)
- [entities.py](entities.py.md)
- [manager.py](manager.py.md)
- [provider.py](provider.py.md)
- [register.py](register.py.md)

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。