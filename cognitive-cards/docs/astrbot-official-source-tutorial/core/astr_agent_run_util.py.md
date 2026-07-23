# 文件教程：core/astr_agent_run_util.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\astr_agent_run_util.py`
- 文件类型：`.py`
- 文件大小：`19885` 字节
- 所属目录教程：[core](README.md)

## 它是做什么的

这个文件主要提供了 _should_stop_agent、_truncate_tool_result、_extract_chain_json_data、_record_tool_call_name 等顶层函数。

## 角色判断

这是一个工具文件，通常提供可复用的辅助函数或基础设施能力。

## 模块文档字符串

这个文件没有显式模块文档字符串，可以重点看顶层类、函数和导入关系。

## 顶层导入

- `asyncio`
- `re`
- `time`
- `traceback`
- `from collections.abc import AsyncGenerator`
- `from astrbot.core import logger`
- `from astrbot.core.agent.message import Message`
- `from astrbot.core.agent.runners.tool_loop_agent_runner import ToolLoopAgentRunner`
- `from astrbot.core.astr_agent_context import AstrAgentContext`
- `from astrbot.core.message.components import BaseMessageComponent, Json, Plain`
- `from astrbot.core.message.message_event_result import MessageChain, MessageEventResult, ResultContentType`
- `from astrbot.core.persona_error_reply import extract_persona_custom_error_message_from_event`
- `from astrbot.core.provider.entities import LLMResponse`
- `from astrbot.core.provider.provider import TTSProvider`

## 顶层类

- 无顶层类定义。

## 顶层函数

- `_should_stop_agent`：建议阅读函数签名和调用位置来判断用途。
- `_truncate_tool_result`：建议阅读函数签名和调用位置来判断用途。
- `_extract_chain_json_data`：建议阅读函数签名和调用位置来判断用途。
- `_record_tool_call_name`：建议阅读函数签名和调用位置来判断用途。
- `_build_tool_call_status_message`：建议阅读函数签名和调用位置来判断用途。
- `_build_tool_result_status_message`：建议阅读函数签名和调用位置来判断用途。
- `run_agent`：建议阅读函数签名和调用位置来判断用途。
- `_watch_agent_stop_signal`：建议阅读函数签名和调用位置来判断用途。
- `run_live_agent`：Live Mode 的 Agent 运行器，支持流式 TTS
- `_run_agent_feeder`：运行 Agent 并将文本输出分句放入队列
- `_safe_tts_stream_wrapper`：包装原生流式 TTS 确保异常处理和队列关闭
- `_simulated_stream_tts`：模拟流式 TTS 分句生成音频

## 阅读建议

- 建议从模块文档字符串、顶层类和顶层函数出发，再搜索这些名字的调用位置。

## 同目录相关文件

- [__init__.py](__init__.py.md)
- [astr_agent_context.py](astr_agent_context.py.md)
- [astr_agent_hooks.py](astr_agent_hooks.py.md)
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
- [log.py](log.py.md)
- [persona_error_reply.py](persona_error_reply.py.md)
- 其余 7 个同目录文件省略

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。