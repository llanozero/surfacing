# 文件教程：dashboard/utils.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\dashboard\utils.py`
- 文件类型：`.py`
- 文件大小：`5555` 字节
- 所属目录教程：[dashboard](README.md)

## 它是做什么的

这个文件主要提供了 generate_tsne_visualization 等顶层函数。

## 角色判断

这是一个工具文件，通常提供可复用的辅助函数或基础设施能力。

## 模块文档字符串

这个文件没有显式模块文档字符串，可以重点看顶层类、函数和导入关系。

## 顶层导入

- `base64`
- `traceback`
- `from io import BytesIO`
- `from typing import TYPE_CHECKING`
- `from astrbot.api import logger`
- `from astrbot.core.knowledge_base.kb_helper import KBHelper`
- `from astrbot.core.knowledge_base.kb_mgr import KnowledgeBaseManager`

## 顶层类

- 无顶层类定义。

## 顶层函数

- `generate_tsne_visualization`：生成 t-SNE 可视化图片

## 阅读建议

- 建议从模块文档字符串、顶层类和顶层函数出发，再搜索这些名字的调用位置。

## 同目录相关文件

- [server.py](server.py.md)

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。