# 文件教程：core/utils/t2i/template_manager.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\utils\t2i\template_manager.py`
- 文件类型：`.py`
- 文件大小：`4748` 字节
- 所属目录教程：[core/utils/t2i](README.md)

## 它是做什么的

这个文件主要定义了 TemplateManager 等顶层类。

## 角色判断

这是一个管理器文件，通常持有运行时状态，并负责编排一类业务流程。

## 模块文档字符串

这个文件没有显式模块文档字符串，可以重点看顶层类、函数和导入关系。

## 顶层导入

- `os`
- `shutil`
- `from astrbot.core.utils.astrbot_path import get_astrbot_data_path, get_astrbot_path`

## 顶层类

- `TemplateManager`：负责管理 t2i HTML 模板的 CRUD 和重置操作

## 顶层函数

- 无顶层函数定义。

## 阅读建议

- 重点看内部状态字段、生命周期和跨模块调用。
- 建议从模块文档字符串、顶层类和顶层函数出发，再搜索这些名字的调用位置。

## 同目录相关文件

- [__init__.py](__init__.py.md)
- [local_strategy.py](local_strategy.py.md)
- [network_strategy.py](network_strategy.py.md)
- [renderer.py](renderer.py.md)

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。