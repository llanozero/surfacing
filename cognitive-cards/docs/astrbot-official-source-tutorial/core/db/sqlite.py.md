# 文件教程：core/db/sqlite.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\db\sqlite.py`
- 文件类型：`.py`
- 文件大小：`73276` 字节
- 所属目录教程：[core/db](README.md)

## 它是做什么的

这个文件主要定义了 SQLiteDatabase 等顶层类。

## 角色判断

这个文件位于核心实现层，通常承载底层机制、抽象或运行时行为。

## 模块文档字符串

这个文件没有显式模块文档字符串，可以重点看顶层类、函数和导入关系。

## 顶层导入

- `asyncio`
- `threading`
- `typing`
- `from collections.abc import Awaitable, Callable`
- `from datetime import datetime, timedelta, timezone`
- `from sqlalchemy import CursorResult, Row`
- `from sqlalchemy.ext.asyncio import AsyncSession`
- `from sqlmodel import col, delete, desc, func, or_, select`
- `from astrbot.core.db import BaseDatabase`
- `from astrbot.core.db.po import ApiKey, Attachment, ChatUIProject, CommandConfig, CommandConflict, ConversationV2`
- `from astrbot.core.db.po import Platform`
- `from astrbot.core.db.po import Stats`
- `from astrbot.core.sentinels import NOT_GIVEN`

## 顶层类

- `SQLiteDatabase`：建议阅读类定义与方法名来判断职责。

## 顶层函数

- 无顶层函数定义。

## 阅读建议

- 建议从模块文档字符串、顶层类和顶层函数出发，再搜索这些名字的调用位置。

## 同目录相关文件

- [__init__.py](__init__.py.md)
- [po.py](po.py.md)

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。