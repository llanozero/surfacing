# 文件教程：core/tools/knowledge_base_tools.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\tools\knowledge_base_tools.py`
- 文件类型：`.py`
- 文件大小：`4621` 字节
- 所属目录教程：[core/tools](README.md)

## 它是做什么的

这个文件主要定义了 KnowledgeBaseQueryTool 等顶层类。

## 角色判断

这个文件位于核心实现层，通常承载底层机制、抽象或运行时行为。

## 模块文档字符串

这个文件没有显式模块文档字符串，可以重点看顶层类、函数和导入关系。

## 顶层导入

- `from pydantic import Field`
- `from pydantic.dataclasses import dataclass`
- `from astrbot.api import logger, sp`
- `from astrbot.core.agent.run_context import ContextWrapper`
- `from astrbot.core.agent.tool import FunctionTool, ToolExecResult`
- `from astrbot.core.astr_agent_context import AstrAgentContext`
- `from astrbot.core.knowledge_base.kb_helper import KBHelper`
- `from astrbot.core.star.context import Context`
- `from astrbot.core.tools.registry import builtin_tool`

## 顶层类

- `KnowledgeBaseQueryTool`：建议阅读类定义与方法名来判断职责。

## 顶层函数

- `check_all_kb`：检查是否所有的知识库都为空
- `retrieve_knowledge_base`：Retrieve knowledge base context for the given query

## 阅读建议

- 建议从模块文档字符串、顶层类和顶层函数出发，再搜索这些名字的调用位置。

## 同目录相关文件

- [cron_tools.py](cron_tools.py.md)
- [message_tools.py](message_tools.py.md)
- [registry.py](registry.py.md)
- [web_search_tools.py](web_search_tools.py.md)

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。