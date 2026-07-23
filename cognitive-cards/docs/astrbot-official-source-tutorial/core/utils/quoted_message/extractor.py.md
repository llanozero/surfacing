# 文件教程：core/utils/quoted_message/extractor.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\utils\quoted_message\extractor.py`
- 文件类型：`.py`
- 文件大小：`7240` 字节
- 所属目录教程：[core/utils/quoted_message](README.md)

## 它是做什么的

这个文件主要定义了 QuotedMessageContent、QuotedMessageExtractor 等顶层类。

## 角色判断

这个文件位于核心实现层，通常承载底层机制、抽象或运行时行为。

## 模块文档字符串

这个文件没有显式模块文档字符串，可以重点看顶层类、函数和导入关系。

## 顶层导入

- `from __future__ import annotations`
- `from dataclasses import dataclass`
- `from astrbot import logger`
- `from astrbot.core.message.components import Reply`
- `from astrbot.core.platform.astr_message_event import AstrMessageEvent`
- `from astrbot.core.utils.string_utils import normalize_and_dedupe_strings`
- `from chain_parser import OneBotPayloadParser, ReplyChainParser`
- `from image_resolver import ImageResolver`
- `from onebot_client import OneBotClient`
- `from settings import SETTINGS, QuotedMessageParserSettings`

## 顶层类

- `QuotedMessageContent`：建议阅读类定义与方法名来判断职责。
- `QuotedMessageExtractor`：建议阅读类定义与方法名来判断职责。

## 顶层函数

- `_collect_text_and_images_from_forward_ids`：建议阅读函数签名和调用位置来判断用途。
- `extract_quoted_message_text`：建议阅读函数签名和调用位置来判断用途。
- `extract_quoted_message_images`：建议阅读函数签名和调用位置来判断用途。

## 阅读建议

- 建议从模块文档字符串、顶层类和顶层函数出发，再搜索这些名字的调用位置。

## 同目录相关文件

- [__init__.py](__init__.py.md)
- [chain_parser.py](chain_parser.py.md)
- [image_refs.py](image_refs.py.md)
- [image_resolver.py](image_resolver.py.md)
- [onebot_client.py](onebot_client.py.md)
- [settings.py](settings.py.md)

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。