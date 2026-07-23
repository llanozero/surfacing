# 文件教程：core/tools/computer_tools/shipyard_neo/neo_skills.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\tools\computer_tools\shipyard_neo\neo_skills.py`
- 文件类型：`.py`
- 文件大小：`19175` 字节
- 所属目录教程：[core/tools/computer_tools/shipyard_neo](README.md)

## 它是做什么的

这个文件主要定义了 NeoSkillToolBase、GetExecutionHistoryTool、AnnotateExecutionTool 等顶层类。

## 角色判断

这个文件位于核心实现层，通常承载底层机制、抽象或运行时行为。

## 模块文档字符串

这个文件没有显式模块文档字符串，可以重点看顶层类、函数和导入关系。

## 顶层导入

- `json`
- `from collections.abc import Awaitable, Callable`
- `from dataclasses import dataclass, field`
- `from typing import Any`
- `from astrbot.api import FunctionTool`
- `from astrbot.core.agent.run_context import ContextWrapper`
- `from astrbot.core.agent.tool import ToolExecResult`
- `from astrbot.core.astr_agent_context import AstrAgentContext`
- `from astrbot.core.computer.computer_client import get_booter`
- `from astrbot.core.skills.neo_skill_sync import NeoSkillSyncManager`
- `from astrbot.core.tools.computer_tools.util import check_admin_permission`
- `from astrbot.core.tools.registry import builtin_tool`

## 顶层类

- `NeoSkillToolBase`：建议阅读类定义与方法名来判断职责。
- `GetExecutionHistoryTool`：建议阅读类定义与方法名来判断职责。
- `AnnotateExecutionTool`：建议阅读类定义与方法名来判断职责。
- `CreateSkillPayloadTool`：建议阅读类定义与方法名来判断职责。
- `GetSkillPayloadTool`：建议阅读类定义与方法名来判断职责。
- `CreateSkillCandidateTool`：建议阅读类定义与方法名来判断职责。
- `ListSkillCandidatesTool`：建议阅读类定义与方法名来判断职责。
- `EvaluateSkillCandidateTool`：建议阅读类定义与方法名来判断职责。
- `PromoteSkillCandidateTool`：建议阅读类定义与方法名来判断职责。
- `ListSkillReleasesTool`：建议阅读类定义与方法名来判断职责。
- `RollbackSkillReleaseTool`：建议阅读类定义与方法名来判断职责。
- `SyncSkillReleaseTool`：建议阅读类定义与方法名来判断职责。

## 顶层函数

- `_to_jsonable`：建议阅读函数签名和调用位置来判断用途。
- `_to_json_text`：建议阅读函数签名和调用位置来判断用途。
- `_get_neo_context`：建议阅读函数签名和调用位置来判断用途。
- `_sync_release_to_dict`：建议阅读函数签名和调用位置来判断用途。

## 阅读建议

- 建议从模块文档字符串、顶层类和顶层函数出发，再搜索这些名字的调用位置。

## 同目录相关文件

- [__init__.py](__init__.py.md)
- [browser.py](browser.py.md)

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。