# 文件教程：core/star/filter/command.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\star\filter\command.py`
- 文件类型：`.py`
- 文件大小：`9151` 字节
- 所属目录教程：[core/star/filter](README.md)

## 它是做什么的

这个文件主要定义了 GreedyStr、CommandFilter 等顶层类。

## 角色判断

这个文件位于核心实现层，通常承载底层机制、抽象或运行时行为。

## 模块文档字符串

这个文件没有显式模块文档字符串，可以重点看顶层类、函数和导入关系。

## 顶层导入

- `inspect`
- `re`
- `types`
- `typing`
- `from typing import Any`
- `from astrbot.core.config import AstrBotConfig`
- `from astrbot.core.platform.astr_message_event import AstrMessageEvent`
- `from star_handler import StarHandlerMetadata`
- `from  import HandlerFilter`
- `from custom_filter import CustomFilter`

## 顶层类

- `GreedyStr`：标记指令完成其他参数接收后的所有剩余文本
- `CommandFilter`：标准指令过滤器

## 顶层函数

- `unwrap_optional`：去掉 Optional[T] / Union[T, None] / T|None，返回 T

## 阅读建议

- 建议从模块文档字符串、顶层类和顶层函数出发，再搜索这些名字的调用位置。

## 同目录相关文件

- [__init__.py](__init__.py.md)
- [command_group.py](command_group.py.md)
- [custom_filter.py](custom_filter.py.md)
- [event_message_type.py](event_message_type.py.md)
- [permission.py](permission.py.md)
- [platform_adapter_type.py](platform_adapter_type.py.md)
- [regex.py](regex.py.md)

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。