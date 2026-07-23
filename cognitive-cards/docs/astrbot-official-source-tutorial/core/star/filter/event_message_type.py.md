# 文件教程：core/star/filter/event_message_type.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\star\filter\event_message_type.py`
- 文件类型：`.py`
- 文件大小：`1205` 字节
- 所属目录教程：[core/star/filter](README.md)

## 它是做什么的

这个文件主要定义了 EventMessageType、EventMessageTypeFilter 等顶层类。

## 角色判断

这是一个事件相关文件，通常定义事件对象、事件行为或平台事件处理逻辑。

## 模块文档字符串

这个文件没有显式模块文档字符串，可以重点看顶层类、函数和导入关系。

## 顶层导入

- `enum`
- `from astrbot.core.config import AstrBotConfig`
- `from astrbot.core.platform.astr_message_event import AstrMessageEvent`
- `from astrbot.core.platform.message_type import MessageType`
- `from  import HandlerFilter`

## 顶层类

- `EventMessageType`：建议阅读类定义与方法名来判断职责。
- `EventMessageTypeFilter`：建议阅读类定义与方法名来判断职责。

## 顶层函数

- 无顶层函数定义。

## 阅读建议

- 重点关注事件对象字段、事件流转和发送行为。
- 建议从模块文档字符串、顶层类和顶层函数出发，再搜索这些名字的调用位置。

## 同目录相关文件

- [__init__.py](__init__.py.md)
- [command.py](command.py.md)
- [command_group.py](command_group.py.md)
- [custom_filter.py](custom_filter.py.md)
- [permission.py](permission.py.md)
- [platform_adapter_type.py](platform_adapter_type.py.md)
- [regex.py](regex.py.md)

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。