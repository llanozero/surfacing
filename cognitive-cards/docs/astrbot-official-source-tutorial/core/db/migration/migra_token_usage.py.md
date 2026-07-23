# 文件教程：core/db/migration/migra_token_usage.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\db\migration\migra_token_usage.py`
- 文件类型：`.py`
- 文件大小：`2141` 字节
- 所属目录教程：[core/db/migration](README.md)

## 它是做什么的

Migration script to add token_usage column to conversations table

## 角色判断

这个文件位于核心实现层，通常承载底层机制、抽象或运行时行为。

## 模块文档字符串

Migration script to add token_usage column to conversations table.

This migration adds the token_usage field to track token consumption for each conversation.

Changes:
- Adds token_usage column to conversations table (default: 0)

## 顶层导入

- `from sqlalchemy import text`
- `from astrbot.api import logger, sp`
- `from astrbot.core.db import BaseDatabase`

## 顶层类

- 无顶层类定义。

## 顶层函数

- `migrate_token_usage`：Add token_usage column to conversations table

## 阅读建议

- 建议从模块文档字符串、顶层类和顶层函数出发，再搜索这些名字的调用位置。

## 同目录相关文件

- [helper.py](helper.py.md)
- [migra_3_to_4.py](migra_3_to_4.py.md)
- [migra_45_to_46.py](migra_45_to_46.py.md)
- [migra_webchat_session.py](migra_webchat_session.py.md)
- [shared_preferences_v3.py](shared_preferences_v3.py.md)
- [sqlite_v3.py](sqlite_v3.py.md)

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。