# 文件教程：core/log.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\log.py`
- 文件类型：`.py`
- 文件大小：`14056` 字节
- 所属目录教程：[core](README.md)

## 它是做什么的

日志系统，统一将标准 logging 输出转发到 loguru

## 角色判断

这个文件位于核心实现层，通常承载底层机制、抽象或运行时行为。

## 模块文档字符串

日志系统，统一将标准 logging 输出转发到 loguru。

## 顶层导入

- `asyncio`
- `logging`
- `os`
- `sys`
- `time`
- `from asyncio import Queue`
- `from collections import deque`
- `from typing import TYPE_CHECKING`
- `from loguru import logger`
- `from astrbot.core.config.default import VERSION`
- `from astrbot.core.utils.astrbot_path import get_astrbot_data_path`

## 顶层类

- `_RecordEnricherFilter`：为 logging.LogRecord 注入 AstrBot 日志字段
- `_QueueAnsiColorFilter`：Attach ANSI color prefix for WebUI console rendering
- `_LoguruInterceptHandler`：将 logging 记录转发到 loguru
- `LogBroker`：日志代理类，用于缓存和分发日志消息
- `LogQueueHandler`：日志处理器，用于将日志消息发送到 LogBroker
- `LogManager`：建议阅读类定义与方法名来判断职责。

## 顶层函数

- `_is_plugin_path`：建议阅读函数签名和调用位置来判断用途。
- `_get_short_level_name`：建议阅读函数签名和调用位置来判断用途。
- `_build_source_file`：建议阅读函数签名和调用位置来判断用途。
- `_patch_record`：建议阅读函数签名和调用位置来判断用途。

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
- [conversation_mgr.py](conversation_mgr.py.md)
- [core_lifecycle.py](core_lifecycle.py.md)
- [event_bus.py](event_bus.py.md)
- [exceptions.py](exceptions.py.md)
- [file_token_service.py](file_token_service.py.md)
- [initial_loader.py](initial_loader.py.md)
- [persona_error_reply.py](persona_error_reply.py.md)
- 其余 7 个同目录文件省略

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。