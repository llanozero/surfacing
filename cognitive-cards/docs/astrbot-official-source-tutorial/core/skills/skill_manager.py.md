# 文件教程：core/skills/skill_manager.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\skills\skill_manager.py`
- 文件类型：`.py`
- 文件大小：`27660` 字节
- 所属目录教程：[core/skills](README.md)

## 它是做什么的

这个文件主要定义了 SkillInfo、SkillManager 等顶层类。

## 角色判断

这是一个管理器文件，通常持有运行时状态，并负责编排一类业务流程。

## 模块文档字符串

这个文件没有显式模块文档字符串，可以重点看顶层类、函数和导入关系。

## 顶层导入

- `from __future__ import annotations`
- `json`
- `os`
- `re`
- `shlex`
- `shutil`
- `tempfile`
- `uuid`
- `zipfile`
- `from dataclasses import dataclass`
- `from datetime import datetime, timezone`
- `from pathlib import Path, PurePosixPath`
- `yaml`
- `from astrbot.core.utils.astrbot_path import get_astrbot_data_path, get_astrbot_skills_path, get_astrbot_temp_path`

## 顶层类

- `SkillInfo`：建议阅读类定义与方法名来判断职责。
- `SkillManager`：建议阅读类定义与方法名来判断职责。

## 顶层函数

- `_normalize_skill_name`：建议阅读函数签名和调用位置来判断用途。
- `_default_sandbox_skill_path`：建议阅读函数签名和调用位置来判断用途。
- `_normalize_cached_sandbox_skill_path`：建议阅读函数签名和调用位置来判断用途。
- `_is_ignored_zip_entry`：建议阅读函数签名和调用位置来判断用途。
- `_normalize_skill_markdown_path`：Return the canonical `SKILL
- `_parse_frontmatter_description`：Extract the ``description`` value from YAML frontmatter
- `_is_windows_prompt_path`：建议阅读函数签名和调用位置来判断用途。
- `_sanitize_prompt_path_for_prompt`：建议阅读函数签名和调用位置来判断用途。
- `_sanitize_prompt_description`：建议阅读函数签名和调用位置来判断用途。
- `_sanitize_skill_display_name`：建议阅读函数签名和调用位置来判断用途。
- `_build_skill_read_command_example`：建议阅读函数签名和调用位置来判断用途。
- `build_skills_prompt`：Build the skills section of the system prompt

## 阅读建议

- 重点看内部状态字段、生命周期和跨模块调用。
- 建议从模块文档字符串、顶层类和顶层函数出发，再搜索这些名字的调用位置。

## 同目录相关文件

- [__init__.py](__init__.py.md)
- [neo_skill_sync.py](neo_skill_sync.py.md)

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。