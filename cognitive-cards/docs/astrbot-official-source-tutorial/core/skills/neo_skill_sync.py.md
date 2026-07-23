# 文件教程：core/skills/neo_skill_sync.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\skills\neo_skill_sync.py`
- 文件类型：`.py`
- 文件大小：`13288` 字节
- 所属目录教程：[core/skills](README.md)

## 它是做什么的

这个文件主要定义了 NeoSkillSyncResult、NeoSkillSyncManager 等顶层类。

## 角色判断

这个文件位于核心实现层，通常承载底层机制、抽象或运行时行为。

## 模块文档字符串

这个文件没有显式模块文档字符串，可以重点看顶层类、函数和导入关系。

## 顶层导入

- `from __future__ import annotations`
- `hashlib`
- `json`
- `os`
- `re`
- `from dataclasses import dataclass`
- `from datetime import datetime, timezone`
- `from pathlib import Path`
- `from typing import Any`
- `from astrbot.core.computer.computer_client import sync_skills_to_active_sandboxes`
- `from astrbot.core.skills.skill_manager import SkillManager`
- `from astrbot.core.utils.astrbot_path import get_astrbot_skills_path`

## 顶层类

- `NeoSkillSyncResult`：建议阅读类定义与方法名来判断职责。
- `NeoSkillSyncManager`：建议阅读类定义与方法名来判断职责。

## 顶层函数

- `_now_iso`：建议阅读函数签名和调用位置来判断用途。
- `_to_jsonable`：建议阅读函数签名和调用位置来判断用途。
- `_parse_frontmatter`：建议阅读函数签名和调用位置来判断用途。
- `_derive_description`：建议阅读函数签名和调用位置来判断用途。
- `_ensure_skill_frontmatter`：建议阅读函数签名和调用位置来判断用途。

## 阅读建议

- 建议从模块文档字符串、顶层类和顶层函数出发，再搜索这些名字的调用位置。

## 同目录相关文件

- [__init__.py](__init__.py.md)
- [skill_manager.py](skill_manager.py.md)

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。