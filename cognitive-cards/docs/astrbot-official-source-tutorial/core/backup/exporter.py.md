# 文件教程：core/backup/exporter.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\backup\exporter.py`
- 文件类型：`.py`
- 文件大小：`19543` 字节
- 所属目录教程：[core/backup](README.md)

## 它是做什么的

AstrBot 数据导出器

## 角色判断

这个文件位于核心实现层，通常承载底层机制、抽象或运行时行为。

## 模块文档字符串

AstrBot 数据导出器

负责将所有数据导出为 ZIP 备份文件。
导出格式为 JSON，这是数据库无关的方案，支持未来向 MySQL/PostgreSQL 迁移。

## 顶层导入

- `hashlib`
- `json`
- `os`
- `zipfile`
- `from datetime import datetime, timezone`
- `from pathlib import Path`
- `from typing import TYPE_CHECKING, Any`
- `from sqlalchemy import select`
- `from astrbot.core import logger`
- `from astrbot.core.config.default import VERSION`
- `from astrbot.core.db import BaseDatabase`
- `from astrbot.core.utils.astrbot_path import get_astrbot_backups_path, get_astrbot_data_path`
- `from constants import BACKUP_MANIFEST_VERSION, KB_METADATA_MODELS, MAIN_DB_MODELS, get_backup_directories`

## 顶层类

- `AstrBotExporter`：AstrBot 数据导出器

## 顶层函数

- 无顶层函数定义。

## 阅读建议

- 建议从模块文档字符串、顶层类和顶层函数出发，再搜索这些名字的调用位置。

## 同目录相关文件

- [__init__.py](__init__.py.md)
- [constants.py](constants.py.md)
- [importer.py](importer.py.md)

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。