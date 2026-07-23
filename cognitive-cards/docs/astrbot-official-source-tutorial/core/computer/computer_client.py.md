# 文件教程：core/computer/computer_client.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\computer\computer_client.py`
- 文件类型：`.py`
- 文件大小：`18361` 字节
- 所属目录教程：[core/computer](README.md)

## 它是做什么的

这个文件主要提供了 _list_local_skill_dirs、_discover_bay_credentials、_build_python_exec_command、_build_apply_sync_command 等顶层函数。

## 角色判断

这个文件位于核心实现层，通常承载底层机制、抽象或运行时行为。

## 模块文档字符串

这个文件没有显式模块文档字符串，可以重点看顶层类、函数和导入关系。

## 顶层导入

- `json`
- `os`
- `shutil`
- `uuid`
- `from pathlib import Path`
- `from astrbot.api import logger`
- `from astrbot.core.skills.skill_manager import SANDBOX_SKILLS_ROOT, SkillManager`
- `from astrbot.core.star.context import Context`
- `from astrbot.core.utils.astrbot_path import get_astrbot_skills_path, get_astrbot_temp_path`
- `from booters.base import ComputerBooter`
- `from booters.local import LocalBooter`

## 顶层类

- 无顶层类定义。

## 顶层函数

- `_list_local_skill_dirs`：建议阅读函数签名和调用位置来判断用途。
- `_discover_bay_credentials`：Try to auto-discover Bay API key from credentials
- `_build_python_exec_command`：建议阅读函数签名和调用位置来判断用途。
- `_build_apply_sync_command`：Build shell command for sync stage only
- `_build_scan_command`：Build shell command for scan stage only
- `_build_sync_and_scan_command`：Legacy combined command kept for backward compatibility
- `_shell_exec_succeeded`：建议阅读函数签名和调用位置来判断用途。
- `_format_exec_error_detail`：Format shell execution details for better observability
- `_decode_sync_payload`：建议阅读函数签名和调用位置来判断用途。
- `_update_sandbox_skills_cache`：建议阅读函数签名和调用位置来判断用途。
- `_apply_skills_to_sandbox`：Apply local skill bundle to sandbox filesystem only
- `_scan_sandbox_skills`：Scan sandbox skills and return normalized payload for cache update
- `_sync_skills_to_sandbox`：Sync local skills to sandbox and refresh cache
- `get_booter`：建议阅读函数签名和调用位置来判断用途。
- `sync_skills_to_active_sandboxes`：Best-effort skills synchronization for all active sandbox sessions
- `get_local_booter`：建议阅读函数签名和调用位置来判断用途。

## 阅读建议

- 建议从模块文档字符串、顶层类和顶层函数出发，再搜索这些名字的调用位置。

## 同目录相关文件

- [file_read_utils.py](file_read_utils.py.md)

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。