# 文件教程：core/star/star_tools.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\star\star_tools.py`
- 文件类型：`.py`
- 文件大小：`11169` 字节
- 所属目录教程：[core/star](README.md)

## 它是做什么的

插件开发工具集

## 角色判断

这个文件位于核心实现层，通常承载底层机制、抽象或运行时行为。

## 模块文档字符串

插件开发工具集
封装了许多常用的操作，方便插件开发者使用

说明:

主动发送消息: send_message(session, message_chain)
    根据 session (unified_msg_origin) 主动发送消息, 前提是需要提前获得或构造 session

根据id直接主动发送消息: send_message_by_id(type, id, message_chain, platform="aiocqhttp")
    根据 id (例如 qq 号, 群号等) 直接, 主动地发送消息

以上两种方式需要构造消息链, 也就是消息组件的列表

构造事件:

首先需要构造一个 AstrBotMessage 对象, 使用 create_message 方法
然后使用 create_event 方法提交事件到指定平台

## 顶层导入

- `inspect`
- `os`
- `uuid`
- `from collections.abc import Awaitable, Callable`
- `from pathlib import Path`
- `from typing import Any, ClassVar`
- `from astrbot.api.platform import AstrBotMessage, MessageMember, MessageType`
- `from astrbot.core.message.components import BaseMessageComponent`
- `from astrbot.core.message.message_event_result import MessageChain`
- `from astrbot.core.platform.astr_message_event import MessageSesion`
- `from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent`
- `from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_platform_adapter import AiocqhttpAdapter`
- `from astrbot.core.star.context import Context`
- `from astrbot.core.star.star import star_map`
- `from astrbot.core.utils.astrbot_path import get_astrbot_data_path`

## 顶层类

- `StarTools`：提供给插件使用的便捷工具函数集合

## 顶层函数

- 无顶层函数定义。

## 阅读建议

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
- [star_manager.py](star_manager.py.md)
- [updator.py](updator.py.md)

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。