# 文件教程：core/utils/astrbot_path.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\utils\astrbot_path.py`
- 文件类型：`.py`
- 文件大小：`3442` 字节
- 所属目录教程：[core/utils](README.md)

## 它是做什么的

Centralized AstrBot path helpers

## 角色判断

这个文件位于核心实现层，通常承载底层机制、抽象或运行时行为。

## 模块文档字符串

Centralized AstrBot path helpers.

Project path:
- Fixed to the source tree location.

Root path:
- Defaults to the current working directory.
- Can be overridden with the ``ASTRBOT_ROOT`` environment variable.

Data subdirectories:
- Most runtime data lives under ``<root>/data``.
- A few tool-runtime files intentionally live under the system temporary
  directory as ``.astrbot``.

## 顶层导入

- `os`
- `tempfile`
- `from astrbot.core.utils.runtime_env import is_packaged_desktop_runtime`

## 顶层类

- 无顶层类定义。

## 顶层函数

- `get_astrbot_path`：Return the AstrBot project source path
- `get_astrbot_root`：Return the AstrBot root directory
- `get_astrbot_data_path`：Return the AstrBot data directory path
- `get_astrbot_config_path`：Return the AstrBot config directory path
- `get_astrbot_plugin_path`：Return the AstrBot plugin directory path
- `get_astrbot_plugin_data_path`：Return the AstrBot plugin data directory path
- `get_astrbot_t2i_templates_path`：Return the AstrBot T2I templates directory path
- `get_astrbot_webchat_path`：Return the AstrBot WebChat data directory path
- `get_astrbot_temp_path`：Return the AstrBot temporary data directory path
- `get_astrbot_skills_path`：Return the AstrBot skills directory path
- `get_astrbot_workspaces_path`：Return the AstrBot workspaces directory path
- `get_astrbot_system_tmp_path`：Return the shared system temporary directory used by local tools
- `get_astrbot_site_packages_path`：Return the AstrBot third-party site-packages directory path
- `get_astrbot_knowledge_base_path`：Return the AstrBot knowledge base root path
- `get_astrbot_backups_path`：Return the AstrBot backups directory path

## 阅读建议

- 建议从模块文档字符串、顶层类和顶层函数出发，再搜索这些名字的调用位置。

## 同目录相关文件

- [active_event_registry.py](active_event_registry.py.md)
- [command_parser.py](command_parser.py.md)
- [config_number.py](config_number.py.md)
- [core_constraints.py](core_constraints.py.md)
- [datetime_utils.py](datetime_utils.py.md)
- [error_redaction.py](error_redaction.py.md)
- [file_extract.py](file_extract.py.md)
- [history_saver.py](history_saver.py.md)
- [http_ssl.py](http_ssl.py.md)
- [image_ref_utils.py](image_ref_utils.py.md)
- [io.py](io.py.md)
- [llm_metadata.py](llm_metadata.py.md)
- [log_pipe.py](log_pipe.py.md)
- [media_utils.py](media_utils.py.md)
- [metrics.py](metrics.py.md)
- 其余 18 个同目录文件省略

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。