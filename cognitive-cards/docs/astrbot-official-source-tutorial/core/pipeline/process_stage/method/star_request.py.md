# 文件教程：core/pipeline/process_stage/method/star_request.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\pipeline\process_stage\method\star_request.py`
- 文件类型：`.py`
- 文件大小：`2868` 字节
- 所属目录教程：[core/pipeline/process_stage/method](README.md)

## 它是做什么的

本地 Agent 模式的 AstrBot 插件调用 Stage

## 角色判断

这个文件位于核心实现层，通常承载底层机制、抽象或运行时行为。

## 模块文档字符串

本地 Agent 模式的 AstrBot 插件调用 Stage

## 顶层导入

- `traceback`
- `from collections.abc import AsyncGenerator`
- `from typing import Any`
- `from astrbot.core import logger`
- `from astrbot.core.message.message_event_result import MessageEventResult`
- `from astrbot.core.platform.astr_message_event import AstrMessageEvent`
- `from astrbot.core.star.star import star_map`
- `from astrbot.core.star.star_handler import EventType, StarHandlerMetadata`
- `from context import PipelineContext, call_event_hook, call_handler`
- `from stage import Stage`

## 顶层类

- `StarRequestSubStage`：建议阅读类定义与方法名来判断职责。

## 顶层函数

- 无顶层函数定义。

## 阅读建议

- 建议从模块文档字符串、顶层类和顶层函数出发，再搜索这些名字的调用位置。

## 同目录相关文件

- [agent_request.py](agent_request.py.md)

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。