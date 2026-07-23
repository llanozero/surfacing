# 文件教程：core/tools/computer_tools/util.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\tools\computer_tools\util.py`
- 文件类型：`.py`
- 文件大小：`1829` 字节
- 所属目录教程：[core/tools/computer_tools](README.md)

## 它是做什么的

这个文件主要提供了 normalize_umo_for_workspace、workspace_root、is_local_runtime、check_admin_permission 等顶层函数。

## 角色判断

这是一个工具文件，通常提供可复用的辅助函数或基础设施能力。

## 模块文档字符串

这个文件没有显式模块文档字符串，可以重点看顶层类、函数和导入关系。

## 顶层导入

- `re`
- `from pathlib import Path`
- `from astrbot.core.agent.run_context import ContextWrapper`
- `from astrbot.core.astr_agent_context import AstrAgentContext`
- `from astrbot.core.utils.astrbot_path import get_astrbot_workspaces_path`

## 顶层类

- 无顶层类定义。

## 顶层函数

- `normalize_umo_for_workspace`：建议阅读函数签名和调用位置来判断用途。
- `workspace_root`：Root directory for relative paths in local runtime
- `is_local_runtime`：建议阅读函数签名和调用位置来判断用途。
- `check_admin_permission`：建议阅读函数签名和调用位置来判断用途。

## 阅读建议

- 建议从模块文档字符串、顶层类和顶层函数出发，再搜索这些名字的调用位置。

## 同目录相关文件

- [__init__.py](__init__.py.md)
- [fs.py](fs.py.md)
- [python.py](python.py.md)
- [shell.py](shell.py.md)

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。