# 文件教程：core/computer/booters/shipyard_neo.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\computer\booters\shipyard_neo.py`
- 文件类型：`.py`
- 文件大小：`20467` 字节
- 所属目录教程：[core/computer/booters](README.md)

## 它是做什么的

这个文件主要定义了 NeoPythonComponent、NeoShellComponent、NeoFileSystemComponent 等顶层类。

## 角色判断

这个文件位于核心实现层，通常承载底层机制、抽象或运行时行为。

## 模块文档字符串

这个文件没有显式模块文档字符串，可以重点看顶层类、函数和导入关系。

## 顶层导入

- `from __future__ import annotations`
- `os`
- `shlex`
- `from typing import Any, cast`
- `from astrbot.api import logger`
- `from olayer import BrowserComponent, FileSystemComponent, PythonComponent, ShellComponent`
- `from base import ComputerBooter`
- `from shipyard_search_file_util import search_files_via_shell`

## 顶层类

- `NeoPythonComponent`：建议阅读类定义与方法名来判断职责。
- `NeoShellComponent`：建议阅读类定义与方法名来判断职责。
- `NeoFileSystemComponent`：建议阅读类定义与方法名来判断职责。
- `NeoBrowserComponent`：建议阅读类定义与方法名来判断职责。
- `ShipyardNeoBooter`：Booter backed by Shipyard Neo (Bay)

## 顶层函数

- `_maybe_model_dump`：建议阅读函数签名和调用位置来判断用途。
- `_slice_content_by_lines`：建议阅读函数签名和调用位置来判断用途。

## 阅读建议

- 建议从模块文档字符串、顶层类和顶层函数出发，再搜索这些名字的调用位置。

## 同目录相关文件

- [base.py](base.py.md)
- [bay_manager.py](bay_manager.py.md)
- [boxlite.py](boxlite.py.md)
- [local.py](local.py.md)
- [shipyard.py](shipyard.py.md)
- [shipyard_search_file_util.py](shipyard_search_file_util.py.md)

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。