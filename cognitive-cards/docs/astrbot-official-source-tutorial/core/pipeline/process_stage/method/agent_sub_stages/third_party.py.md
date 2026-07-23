# 文件教程：core/pipeline/process_stage/method/agent_sub_stages/third_party.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\pipeline\process_stage\method\agent_sub_stages\third_party.py`
- 文件类型：`.py`
- 文件大小：`16506` 字节
- 所属目录教程：[core/pipeline/process_stage/method/agent_sub_stages](README.md)

## 它是做什么的

这个文件主要定义了 _RunnerResultAggregator、ThirdPartyAgentSubStage 等顶层类。

## 角色判断

这个文件位于核心实现层，通常承载底层机制、抽象或运行时行为。

## 模块文档字符串

这个文件没有显式模块文档字符串，可以重点看顶层类、函数和导入关系。

## 顶层导入

- `asyncio`
- `inspect`
- `from collections.abc import AsyncGenerator, Awaitable, Callable`
- `from typing import TYPE_CHECKING`
- `from astrbot.core import astrbot_config, logger`
- `from astrbot.core.agent.runners.coze.coze_agent_runner import CozeAgentRunner`
- `from astrbot.core.agent.runners.dashscope.dashscope_agent_runner import DashscopeAgentRunner`
- `from astrbot.core.agent.runners.deerflow.constants import DEERFLOW_AGENT_RUNNER_PROVIDER_ID_KEY, DEERFLOW_PROVIDER_TYPE`
- `from astrbot.core.agent.runners.deerflow.deerflow_agent_runner import DeerFlowAgentRunner`
- `from astrbot.core.agent.runners.dify.dify_agent_runner import DifyAgentRunner`
- `from astrbot.core.astr_agent_hooks import MAIN_AGENT_HOOKS`
- `from astrbot.core.message.components import Image, Record`
- `from astrbot.core.message.message_event_result import MessageChain, MessageEventResult, ResultContentType`
- `from astrbot.core.persona_error_reply import resolve_event_conversation_persona_id, resolve_persona_custom_error_message, set_persona_custom_error_message_on_event`
- `from astrbot.core.pipeline.stage import Stage`
- `from astrbot.core.platform.astr_message_event import AstrMessageEvent`
- `from astrbot.core.provider.entities import ProviderRequest`
- `from astrbot.core.star.star_handler import EventType`
- `from astrbot.core.utils.config_number import coerce_int_config`
- `from astrbot.core.utils.metrics import Metric`
- 其余 2 条导入省略

## 顶层类

- `_RunnerResultAggregator`：建议阅读类定义与方法名来判断职责。
- `ThirdPartyAgentSubStage`：建议阅读类定义与方法名来判断职责。

## 顶层函数

- `run_third_party_agent`：运行第三方 agent runner 并转换响应格式
- `_start_stream_watchdog`：建议阅读函数签名和调用位置来判断用途。
- `_close_runner_if_supported`：建议阅读函数签名和调用位置来判断用途。

## 阅读建议

- 建议从模块文档字符串、顶层类和顶层函数出发，再搜索这些名字的调用位置。

## 同目录相关文件

- [internal.py](internal.py.md)

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。