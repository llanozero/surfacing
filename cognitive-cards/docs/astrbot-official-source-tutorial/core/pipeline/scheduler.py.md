# 文件教程：core/pipeline/scheduler.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\pipeline\scheduler.py`
- 文件类型：`.py`
- 文件大小：`3979` 字节
- 所属目录教程：[core/pipeline](README.md)

## 它是做什么的

这个文件主要定义了 PipelineScheduler 等顶层类。

## 角色判断

这个文件位于核心实现层，通常承载底层机制、抽象或运行时行为。

## 模块文档字符串

这个文件没有显式模块文档字符串，可以重点看顶层类、函数和导入关系。

## 顶层导入

- `from collections.abc import AsyncGenerator`
- `from astrbot.core import logger`
- `from astrbot.core.platform import AstrMessageEvent`
- `from astrbot.core.platform.sources.webchat.webchat_event import WebChatMessageEvent`
- `from astrbot.core.platform.sources.wecom_ai_bot.wecomai_event import WecomAIBotMessageEvent`
- `from astrbot.core.utils.active_event_registry import active_event_registry`
- `from bootstrap import ensure_builtin_stages_registered`
- `from context import PipelineContext`
- `from stage import registered_stages`
- `from stage_order import STAGES_ORDER`

## 顶层类

- `PipelineScheduler`：管道调度器，负责调度各个阶段的执行

## 顶层函数

- 无顶层函数定义。

## 阅读建议

- 建议从模块文档字符串、顶层类和顶层函数出发，再搜索这些名字的调用位置。

## 同目录相关文件

- [__init__.py](__init__.py.md)
- [bootstrap.py](bootstrap.py.md)
- [context.py](context.py.md)
- [context_utils.py](context_utils.py.md)
- [stage.py](stage.py.md)
- [stage_order.py](stage_order.py.md)

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。