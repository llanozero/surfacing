# 文件教程：core/pipeline/process_stage/follow_up.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\pipeline\process_stage\follow_up.py`
- 文件类型：`.py`
- 文件大小：`7692` 字节
- 所属目录教程：[core/pipeline/process_stage](README.md)

## 它是做什么的

这个文件主要定义了 FollowUpCapture 等顶层类。

## 角色判断

这个文件位于核心实现层，通常承载底层机制、抽象或运行时行为。

## 模块文档字符串

这个文件没有显式模块文档字符串，可以重点看顶层类、函数和导入关系。

## 顶层导入

- `from __future__ import annotations`
- `asyncio`
- `from dataclasses import dataclass`
- `from astrbot import logger`
- `from astrbot.core.agent.runners.tool_loop_agent_runner import FollowUpTicket`
- `from astrbot.core.astr_agent_run_util import AgentRunner`
- `from astrbot.core.platform.astr_message_event import AstrMessageEvent`

## 顶层类

- `FollowUpCapture`：建议阅读类定义与方法名来判断职责。

## 顶层函数

- `_event_follow_up_text`：建议阅读函数签名和调用位置来判断用途。
- `register_active_runner`：建议阅读函数签名和调用位置来判断用途。
- `unregister_active_runner`：建议阅读函数签名和调用位置来判断用途。
- `_get_follow_up_order_state`：建议阅读函数签名和调用位置来判断用途。
- `_advance_follow_up_turn_locked`：建议阅读函数签名和调用位置来判断用途。
- `_allocate_follow_up_order`：建议阅读函数签名和调用位置来判断用途。
- `_mark_follow_up_consumed`：建议阅读函数签名和调用位置来判断用途。
- `_activate_and_wait_follow_up_turn`：建议阅读函数签名和调用位置来判断用途。
- `_finish_follow_up_turn`：建议阅读函数签名和调用位置来判断用途。
- `_monitor_follow_up_ticket`：Advance consumed slots immediately on resolution to avoid wake-order drift
- `try_capture_follow_up`：建议阅读函数签名和调用位置来判断用途。
- `prepare_follow_up_capture`：Return `(consumed_marked, activated)` for internal stage branch handling
- `finalize_follow_up_capture`：建议阅读函数签名和调用位置来判断用途。

## 阅读建议

- 建议从模块文档字符串、顶层类和顶层函数出发，再搜索这些名字的调用位置。

## 同目录相关文件

- [stage.py](stage.py.md)

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。