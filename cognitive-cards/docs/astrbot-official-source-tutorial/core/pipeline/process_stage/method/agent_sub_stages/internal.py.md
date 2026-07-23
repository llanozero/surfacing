# 文件教程：core/pipeline/process_stage/method/agent_sub_stages/internal.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\pipeline\process_stage\method\agent_sub_stages\internal.py`
- 文件类型：`.py`
- 文件大小：`22088` 字节
- 所属目录教程：[core/pipeline/process_stage/method/agent_sub_stages](README.md)

## 它是做什么的

本地 Agent 模式的 LLM 调用 Stage

## 角色判断

这个文件位于核心实现层，通常承载底层机制、抽象或运行时行为。

## 模块文档字符串

本地 Agent 模式的 LLM 调用 Stage

## 顶层导入

- `asyncio`
- `base64`
- `from collections.abc import AsyncGenerator`
- `from dataclasses import replace`
- `from astrbot.core import db_helper, logger`
- `from astrbot.core.agent.message import Message`
- `from astrbot.core.agent.response import AgentStats`
- `from astrbot.core.astr_main_agent import MainAgentBuildConfig, MainAgentBuildResult, build_main_agent`
- `from astrbot.core.message.components import File, Image, Record, Video`
- `from astrbot.core.message.message_event_result import MessageChain, MessageEventResult, ResultContentType`
- `from astrbot.core.persona_error_reply import extract_persona_custom_error_message_from_event`
- `from astrbot.core.pipeline.stage import Stage`
- `from astrbot.core.platform.astr_message_event import AstrMessageEvent`
- `from astrbot.core.provider.entities import LLMResponse, ProviderRequest`
- `from astrbot.core.star.star_handler import EventType`
- `from astrbot.core.utils.metrics import Metric`
- `from astrbot.core.utils.session_lock import session_lock_manager`
- `from astr_agent_run_util import AgentRunner, run_agent, run_live_agent`
- `from context import PipelineContext, call_event_hook`
- `from follow_up import FollowUpCapture, finalize_follow_up_capture, prepare_follow_up_capture, register_active_runner, try_capture_follow_up, unregister_active_runner`

## 顶层类

- `InternalAgentSubStage`：建议阅读类定义与方法名来判断职责。

## 顶层函数

- `_record_internal_agent_stats`：Persist internal agent stats without affecting the user response flow

## 阅读建议

- 建议从模块文档字符串、顶层类和顶层函数出发，再搜索这些名字的调用位置。

## 同目录相关文件

- [third_party.py](third_party.py.md)

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。