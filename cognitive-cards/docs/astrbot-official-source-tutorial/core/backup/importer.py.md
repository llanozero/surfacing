# 文件教程：core/backup/importer.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\backup\importer.py`
- 文件类型：`.py`
- 文件大小：`36553` 字节
- 所属目录教程：[core/backup](README.md)

## 它是做什么的

AstrBot 数据导入器

## 角色判断

这个文件位于核心实现层，通常承载底层机制、抽象或运行时行为。

## 模块文档字符串

AstrBot 数据导入器

负责从 ZIP 备份文件恢复所有数据。
导入时进行版本校验：
- 主版本（前两位）不同时直接拒绝导入
- 小版本（第三位）不同时提示警告，用户可选择强制导入
- 版本匹配时也需要用户确认

## 顶层导入

- `json`
- `os`
- `shutil`
- `zipfile`
- `from dataclasses import dataclass, field`
- `from datetime import datetime, timezone`
- `from pathlib import Path`
- `from typing import TYPE_CHECKING, Any`
- `from sqlalchemy import delete`
- `from astrbot.core import logger`
- `from astrbot.core.config.default import VERSION`
- `from astrbot.core.db import BaseDatabase`
- `from astrbot.core.utils.astrbot_path import get_astrbot_data_path, get_astrbot_knowledge_base_path`
- `from astrbot.core.utils.version_comparator import VersionComparator`
- `from constants import KB_METADATA_MODELS, MAIN_DB_MODELS, get_backup_directories`

## 顶层类

- `_InvalidCountWarnLimiter`：Rate-limit warnings for invalid platform_stats count values
- `ImportPreCheckResult`：导入预检查结果
- `ImportResult`：导入结果
- `DatabaseClearError`：Raised when clearing the main database in replace mode fails
- `AstrBotImporter`：AstrBot 数据导入器

## 顶层函数

- `_get_major_version`：提取版本的主版本部分（前两位）
- `_load_platform_stats_invalid_count_warn_limit`：建议阅读函数签名和调用位置来判断用途。

## 阅读建议

- 建议从模块文档字符串、顶层类和顶层函数出发，再搜索这些名字的调用位置。

## 同目录相关文件

- [__init__.py](__init__.py.md)
- [constants.py](constants.py.md)
- [exporter.py](exporter.py.md)

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。