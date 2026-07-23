# 文件教程：core/star/star_manager.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\star\star_manager.py`
- 文件类型：`.py`
- 文件大小：`74421` 字节
- 所属目录教程：[core/star](README.md)

## 它是做什么的

插件的重载、启停、安装、卸载等操作

## 角色判断

这是一个管理器文件，通常持有运行时状态，并负责编排一类业务流程。

## 模块文档字符串

插件的重载、启停、安装、卸载等操作。

## 顶层导入

- `asyncio`
- `contextlib`
- `functools`
- `inspect`
- `json`
- `keyword`
- `logging`
- `os`
- `sys`
- `tempfile`
- `traceback`
- `from dataclasses import dataclass`
- `from enum import Enum, auto`
- `from types import ModuleType`
- `yaml`
- `from packaging.specifiers import InvalidSpecifier, SpecifierSet`
- `from packaging.version import InvalidVersion, Version`
- `from astrbot.core import DependencyConflictError, logger, pip_installer, sp`
- `from astrbot.core.agent.handoff import FunctionTool, HandoffTool`
- `from astrbot.core.config.astrbot_config import AstrBotConfig`
- 其余 15 条导入省略

## 顶层类

- `PluginVersionIncompatibleError`：Raised when plugin astrbot_version is incompatible with current AstrBot
- `PluginDependencyInstallError`：Raised when plugin dependency installation fails
- `ImportDependencyRecoveryMode`：建议阅读类定义与方法名来判断职责。
- `ImportDependencyRecoveryState`：建议阅读类定义与方法名来判断职责。
- `PluginManager`：建议阅读类定义与方法名来判断职责。

## 顶层函数

- `_temporary_filtered_requirements_file`：建议阅读函数签名和调用位置来判断用途。
- `_install_requirements_with_precheck`：建议阅读函数签名和调用位置来判断用途。

## 阅读建议

- 重点看内部状态字段、生命周期和跨模块调用。
- 建议从模块文档字符串、顶层类和顶层函数出发，再搜索这些名字的调用位置。

## 同目录相关文件

- [__init__.py](__init__.py.md)
- [base.py](base.py.md)
- [command_management.py](command_management.py.md)
- [config.py](config.py.md)
- [context.py](context.py.md)
- [error_messages.py](error_messages.py.md)
- [README.md](README.md.md)
- [session_llm_manager.py](session_llm_manager.py.md)
- [session_plugin_manager.py](session_plugin_manager.py.md)
- [star.py](star.py.md)
- [star_handler.py](star_handler.py.md)
- [star_tools.py](star_tools.py.md)
- [updator.py](updator.py.md)

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。