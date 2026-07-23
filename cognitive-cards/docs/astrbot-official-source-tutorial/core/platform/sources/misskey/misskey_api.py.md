# 文件教程：core/platform/sources/misskey/misskey_api.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\platform\sources\misskey\misskey_api.py`
- 文件类型：`.py`
- 文件大小：`36875` 字节
- 所属目录教程：[core/platform/sources/misskey](README.md)

## 它是做什么的

这个文件主要定义了 APIError、APIConnectionError、APIRateLimitError 等顶层类。

## 角色判断

这个文件位于核心实现层，通常承载底层机制、抽象或运行时行为。

## 模块文档字符串

这个文件没有显式模块文档字符串，可以重点看顶层类、函数和导入关系。

## 顶层导入

- `asyncio`
- `json`
- `random`
- `uuid`
- `from collections.abc import Awaitable, Callable`
- `from typing import Any, NoReturn`
- `from astrbot.api import logger`
- `from misskey_utils import FileIDExtractor`

## 顶层类

- `APIError`：Misskey API 基础异常
- `APIConnectionError`：网络连接异常
- `APIRateLimitError`：API 频率限制异常
- `AuthenticationError`：认证失败异常
- `WebSocketError`：WebSocket 连接异常
- `StreamingClient`：建议阅读类定义与方法名来判断职责。
- `MisskeyAPI`：建议阅读类定义与方法名来判断职责。

## 顶层函数

- `retry_async`：智能异步重试装饰器

## 阅读建议

- 建议从模块文档字符串、顶层类和顶层函数出发，再搜索这些名字的调用位置。

## 同目录相关文件

- [misskey_adapter.py](misskey_adapter.py.md)
- [misskey_event.py](misskey_event.py.md)
- [misskey_utils.py](misskey_utils.py.md)

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。