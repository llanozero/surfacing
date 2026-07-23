# 文件教程：core/tools/computer_tools/fs.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\tools\computer_tools\fs.py`
- 文件类型：`.py`
- 文件大小：`28385` 字节
- 所属目录教程：[core/tools/computer_tools](README.md)

## 它是做什么的

Filesystem tool audit

## 角色判断

这个文件位于核心实现层，通常承载底层机制、抽象或运行时行为。

## 模块文档字符串

Filesystem tool audit.

Tool exposure from the main agent:
- Local runtime exposes `astrbot_read_file_tool`, `astrbot_file_write_tool`,
  `astrbot_file_edit_tool`, and `astrbot_grep_tool`.
- Sandbox runtime exposes `astrbot_upload_file`, `astrbot_download_file`,
  `astrbot_read_file_tool`, `astrbot_file_write_tool`,
  `astrbot_file_edit_tool`, and `astrbot_grep_tool`.

Behavior when `provider_settings.computer_use_require_admin=True`:
- Admin + local: read/write/edit/grep are not path-restricted by this module;
  access depends on the local runtime implementation and host OS permissions.
  Upload and download tools are defined here, but `LocalBooter` does not
  implement them and the main agent does not expose them in local mode.
- Member + local: read/write/edit/grep are restricted to `data/skills`,
  `data/workspaces/{normalized_umo}`, and `/tmp/.astrbot`. Upload/download are
  denied by `check_admin_permission` if invoked.
- Admin + sandbox: read/write/edit/grep are not path-restricted by this
  module;
  sandbox filesystem boundaries are enforced by the sandbox runtime. Upload and
  download are allowed.
- Member + sandbox: read/write/edit/grep are also not path-restricted by this
  module. Upload/download are denied by `check_admin_permission` if invoked.

When `computer_use_require_admin=False`, member behavior in this module matches
admin behavior.

Local path resolution rule:
- In local runtime, relative paths are resolved under
  `data/workspaces/{normalized_umo}`.
- In sandbox runtime, relative paths are passed through unchanged.

## 顶层导入

- `os`
- `uuid`
- `from dataclasses import dataclass, field`
- `from pathlib import Path`
- `from astrbot.api import FunctionTool, logger`
- `from astrbot.api.event import MessageChain`
- `from astrbot.core.agent.run_context import ContextWrapper`
- `from astrbot.core.agent.tool import ToolExecResult`
- `from astrbot.core.astr_agent_context import AstrAgentContext`
- `from astrbot.core.computer.computer_client import get_booter`
- `from astrbot.core.computer.file_read_utils import read_file_tool_result`
- `from astrbot.core.message.components import File`
- `from astrbot.core.utils.astrbot_path import get_astrbot_skills_path, get_astrbot_system_tmp_path, get_astrbot_temp_path`
- `from registry import builtin_tool`
- `from  import util`
- `from util import check_admin_permission, is_local_runtime, normalize_umo_for_workspace`

## 顶层类

- `FileReadTool`：建议阅读类定义与方法名来判断职责。
- `FileWriteTool`：建议阅读类定义与方法名来判断职责。
- `FileEditTool`：建议阅读类定义与方法名来判断职责。
- `GrepTool`：建议阅读类定义与方法名来判断职责。
- `FileUploadTool`：建议阅读类定义与方法名来判断职责。
- `FileDownloadTool`：建议阅读类定义与方法名来判断职责。

## 顶层函数

- `_restricted_env_path_labels`：Labels for the allowed directories in a local(not sandbox) and restricted(not admin) environment
- `get_astrbot_workspaces_path`：Compatibility wrapper for tests and older module-level monkeypatches
- `_workspace_root`：Workspace root that follows both util-level and fs-level getter monkeypatches
- `_read_allowed_roots`：Non-admin users can only read files within these directories (and their subdirectories)
- `_is_restricted_env`：建议阅读函数签名和调用位置来判断用途。
- `_resolve_tool_path`：建议阅读函数签名和调用位置来判断用途。
- `_resolve_user_path`：建议阅读函数签名和调用位置来判断用途。
- `_is_path_within_allowed_roots`：建议阅读函数签名和调用位置来判断用途。
- `_normalize_rw_path`：建议阅读函数签名和调用位置来判断用途。
- `_decode_escaped_text`：Decode common escaped control sequences used in tool arguments

## 阅读建议

- 建议从模块文档字符串、顶层类和顶层函数出发，再搜索这些名字的调用位置。

## 同目录相关文件

- [__init__.py](__init__.py.md)
- [python.py](python.py.md)
- [shell.py](shell.py.md)
- [util.py](util.py.md)

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。