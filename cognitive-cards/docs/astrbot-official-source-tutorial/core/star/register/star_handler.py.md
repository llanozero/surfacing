# 文件教程：core/star/register/star_handler.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\star\register\star_handler.py`
- 文件类型：`.py`
- 文件大小：`23339` 字节
- 所属目录教程：[core/star/register](README.md)

## 它是做什么的

这个文件主要定义了 RegisteringCommandable、RegisteringAgent 等顶层类。

## 角色判断

这个文件位于核心实现层，通常承载底层机制、抽象或运行时行为。

## 模块文档字符串

这个文件没有显式模块文档字符串，可以重点看顶层类、函数和导入关系。

## 顶层导入

- `from __future__ import annotations`
- `re`
- `from collections.abc import AsyncGenerator, Awaitable, Callable`
- `from typing import Any`
- `docstring_parser`
- `from astrbot.core import logger`
- `from astrbot.core.agent.agent import Agent`
- `from astrbot.core.agent.handoff import HandoffTool`
- `from astrbot.core.agent.hooks import BaseAgentRunHooks`
- `from astrbot.core.agent.tool import FunctionTool`
- `from astrbot.core.message.message_event_result import MessageEventResult`
- `from astrbot.core.provider.func_tool_manager import PY_TO_JSON_TYPE, SUPPORTED_TYPES`
- `from astrbot.core.provider.register import llm_tools`
- `from filter.command import CommandFilter`
- `from filter.command_group import CommandGroupFilter`
- `from filter.custom_filter import CustomFilterAnd, CustomFilterOr`
- `from filter.event_message_type import EventMessageType, EventMessageTypeFilter`
- `from filter.permission import PermissionType, PermissionTypeFilter`
- `from filter.platform_adapter_type import PlatformAdapterType, PlatformAdapterTypeFilter`
- `from filter.regex import RegexFilter`
- 其余 1 条导入省略

## 顶层类

- `RegisteringCommandable`：用于指令组级联注册
- `RegisteringAgent`：用于 Agent 注册

## 顶层函数

- `get_handler_full_name`：获取 Handler 的全名
- `get_handler_or_create`：获取 Handler 或者创建一个新的 Handler
- `register_command`：注册一个 Command
- `register_custom_filter`：注册一个自定义的 CustomFilter
- `register_command_group`：注册一个 CommandGroup
- `register_event_message_type`：注册一个 EventMessageType
- `register_platform_adapter_type`：注册一个 PlatformAdapterType
- `register_regex`：注册一个 Regex
- `register_permission_type`：注册一个 PermissionType
- `register_on_astrbot_loaded`：当 AstrBot 加载完成时
- `register_on_platform_loaded`：当平台加载完成时
- `register_on_plugin_error`：当插件处理消息异常时触发
- `register_on_plugin_loaded`：当有插件加载完成时
- `register_on_plugin_unloaded`：当有插件卸载完成时
- `register_on_waiting_llm_request`：当等待调用 LLM 时的通知事件（在获取锁之前）
- `register_on_llm_request`：当有 LLM 请求时的事件
- `register_on_llm_response`：当有 LLM 请求后的事件
- `register_on_agent_begin`：当 Agent 开始运行时的事件
- `register_on_agent_done`：当 Agent 运行完成后的事件
- `register_on_using_llm_tool`：当调用函数工具前的事件
- `register_on_llm_tool_respond`：当调用函数工具后的事件
- `register_llm_tool`：为函数调用（function-calling / tools-use）添加工具
- `register_agent`：注册一个 Agent
- `register_on_decorating_result`：在发送消息前的事件
- `register_after_message_sent`：在消息发送后的事件

## 阅读建议

- 建议从模块文档字符串、顶层类和顶层函数出发，再搜索这些名字的调用位置。

## 同目录相关文件

- [__init__.py](__init__.py.md)
- [star.py](star.py.md)

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。