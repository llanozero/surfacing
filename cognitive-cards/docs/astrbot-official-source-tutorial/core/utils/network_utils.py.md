# 文件教程：core/utils/network_utils.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\utils\network_utils.py`
- 文件类型：`.py`
- 文件大小：`3172` 字节
- 所属目录教程：[core/utils](README.md)

## 它是做什么的

Network error handling utilities for providers

## 角色判断

这是一个工具文件，通常提供可复用的辅助函数或基础设施能力。

## 模块文档字符串

Network error handling utilities for providers.

## 顶层导入

- `httpx`
- `from astrbot import logger`

## 顶层类

- 无顶层类定义。

## 顶层函数

- `is_connection_error`：Check if an exception is a connection/network related error
- `log_connection_failure`：Log a connection failure with proxy information
- `create_proxy_client`：Create an httpx AsyncClient with proxy configuration if provided

## 阅读建议

- 建议从模块文档字符串、顶层类和顶层函数出发，再搜索这些名字的调用位置。

## 同目录相关文件

- [active_event_registry.py](active_event_registry.py.md)
- [astrbot_path.py](astrbot_path.py.md)
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
- 其余 18 个同目录文件省略

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。