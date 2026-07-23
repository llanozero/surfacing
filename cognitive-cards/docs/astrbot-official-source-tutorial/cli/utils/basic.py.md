# 文件教程：cli/utils/basic.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\cli\utils\basic.py`
- 文件类型：`.py`
- 文件大小：`3171` 字节
- 所属目录教程：[cli/utils](README.md)

## 它是做什么的

这个文件主要提供了 check_astrbot_root、get_astrbot_root、check_dashboard 等顶层函数。

## 角色判断

这是一个 Python 源文件，建议结合顶部文档字符串、顶层类和函数一起阅读其职责。

## 模块文档字符串

这个文件没有显式模块文档字符串，可以重点看顶层类、函数和导入关系。

## 顶层导入

- `from pathlib import Path`
- `click`

## 顶层类

- 无顶层类定义。

## 顶层函数

- `check_astrbot_root`：Check if the path is an AstrBot root directory
- `get_astrbot_root`：Get the AstrBot root directory path
- `check_dashboard`：Check if the dashboard is installed

## 阅读建议

- 建议从模块文档字符串、顶层类和顶层函数出发，再搜索这些名字的调用位置。

## 同目录相关文件

- [__init__.py](__init__.py.md)
- [plugin.py](plugin.py.md)
- [version_comparator.py](version_comparator.py.md)

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。