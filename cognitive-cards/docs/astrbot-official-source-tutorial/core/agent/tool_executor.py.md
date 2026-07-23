# 文件教程：core/agent/tool_executor.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\agent\tool_executor.py`
- 文件类型：`.py`
- 文件大小：`455` 字节
- 所属目录教程：[core/agent](README.md)

## 它是做什么的

这个文件主要定义了 BaseFunctionToolExecutor 等顶层类。

## 角色判断

这个文件位于核心实现层，通常承载底层机制、抽象或运行时行为。

## 模块文档字符串

这个文件没有显式模块文档字符串，可以重点看顶层类、函数和导入关系。

## 顶层导入

- `from collections.abc import AsyncGenerator`
- `from typing import Any, Generic`
- `mcp`
- `from run_context import ContextWrapper, TContext`
- `from tool import FunctionTool`

## 顶层类

- `BaseFunctionToolExecutor`：建议阅读类定义与方法名来判断职责。

## 顶层函数

- 无顶层函数定义。

## 阅读建议

- 建议从模块文档字符串、顶层类和顶层函数出发，再搜索这些名字的调用位置。

## 同目录相关文件

- [agent.py](agent.py.md)
- [handoff.py](handoff.py.md)
- [hooks.py](hooks.py.md)
- [mcp_client.py](mcp_client.py.md)
- [message.py](message.py.md)
- [response.py](response.py.md)
- [run_context.py](run_context.py.md)
- [tool.py](tool.py.md)
- [tool_image_cache.py](tool_image_cache.py.md)

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。