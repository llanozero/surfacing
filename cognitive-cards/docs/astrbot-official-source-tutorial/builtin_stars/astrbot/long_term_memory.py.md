# 文件教程：builtin_stars/astrbot/long_term_memory.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\builtin_stars\astrbot\long_term_memory.py`
- 文件类型：`.py`
- 文件大小：`7910` 字节
- 所属目录教程：[builtin_stars/astrbot](README.md)

## 它是做什么的

这个文件主要定义了 LongTermMemory 等顶层类。

## 角色判断

这是一个 Python 源文件，建议结合顶部文档字符串、顶层类和函数一起阅读其职责。

## 模块文档字符串

这个文件没有显式模块文档字符串，可以重点看顶层类、函数和导入关系。

## 顶层导入

- `datetime`
- `random`
- `uuid`
- `from collections import defaultdict`
- `from astrbot import logger`
- `from astrbot.api import star`
- `from astrbot.api.event import AstrMessageEvent`
- `from astrbot.api.message_components import At, Image, Plain`
- `from astrbot.api.platform import MessageType`
- `from astrbot.api.provider import LLMResponse, Provider, ProviderRequest`
- `from astrbot.core.astrbot_config_mgr import AstrBotConfigManager`

## 顶层类

- `LongTermMemory`：建议阅读类定义与方法名来判断职责。

## 顶层函数

- 无顶层函数定义。

## 阅读建议

- 建议从模块文档字符串、顶层类和顶层函数出发，再搜索这些名字的调用位置。

## 同目录相关文件

- [main.py](main.py.md)
- [metadata.yaml](metadata.yaml.md)

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。