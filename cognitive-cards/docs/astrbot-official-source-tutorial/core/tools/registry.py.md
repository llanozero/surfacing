# 文件教程：core/tools/registry.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\tools\registry.py`
- 文件类型：`.py`
- 文件大小：`10736` 字节
- 所属目录教程：[core/tools](README.md)

## 它是做什么的

这个文件主要定义了 BuiltinToolConfigCondition、BuiltinToolConfigRule 等顶层类。

## 角色判断

这个文件位于核心实现层，通常承载底层机制、抽象或运行时行为。

## 模块文档字符串

这个文件没有显式模块文档字符串，可以重点看顶层类、函数和导入关系。

## 顶层导入

- `from __future__ import annotations`
- `from collections.abc import Callable`
- `from dataclasses import dataclass`
- `from importlib import import_module`
- `from typing import Any, TypeVar`
- `from astrbot.core.agent.tool import FunctionTool`

## 顶层类

- `BuiltinToolConfigCondition`：建议阅读类定义与方法名来判断职责。
- `BuiltinToolConfigRule`：建议阅读类定义与方法名来判断职责。

## 顶层函数

- `_get_config_value`：建议阅读函数签名和调用位置来判断用途。
- `_json_safe`：建议阅读函数签名和调用位置来判断用途。
- `_equals`：建议阅读函数签名和调用位置来判断用途。
- `_in`：建议阅读函数签名和调用位置来判断用途。
- `_custom_condition`：建议阅读函数签名和调用位置来判断用途。
- `_build_rule_from_config_map`：建议阅读函数签名和调用位置来判断用途。
- `_evaluate_send_message_tool`：建议阅读函数签名和调用位置来判断用途。
- `_register_builtin_tool_config_rule`：建议阅读函数签名和调用位置来判断用途。
- `_resolve_builtin_tool_name`：建议阅读函数签名和调用位置来判断用途。
- `builtin_tool`：建议阅读函数签名和调用位置来判断用途。
- `ensure_builtin_tools_loaded`：建议阅读函数签名和调用位置来判断用途。
- `get_builtin_tool_class`：建议阅读函数签名和调用位置来判断用途。
- `get_builtin_tool_name`：建议阅读函数签名和调用位置来判断用途。
- `iter_builtin_tool_classes`：建议阅读函数签名和调用位置来判断用途。
- `get_builtin_tool_config_rule`：建议阅读函数签名和调用位置来判断用途。
- `get_builtin_tool_config_statuses`：建议阅读函数签名和调用位置来判断用途。
- `get_builtin_tool_config_tags`：建议阅读函数签名和调用位置来判断用途。

## 阅读建议

- 建议从模块文档字符串、顶层类和顶层函数出发，再搜索这些名字的调用位置。

## 同目录相关文件

- [cron_tools.py](cron_tools.py.md)
- [knowledge_base_tools.py](knowledge_base_tools.py.md)
- [message_tools.py](message_tools.py.md)
- [web_search_tools.py](web_search_tools.py.md)

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。