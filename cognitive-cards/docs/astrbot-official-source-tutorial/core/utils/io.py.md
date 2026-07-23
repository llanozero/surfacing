# 文件教程：core/utils/io.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\utils\io.py`
- 文件类型：`.py`
- 文件大小：`11086` 字节
- 所属目录教程：[core/utils](README.md)

## 它是做什么的

这个文件主要提供了 on_error、remove_dir、port_checker、save_temp_img 等顶层函数。

## 角色判断

这个文件位于核心实现层，通常承载底层机制、抽象或运行时行为。

## 模块文档字符串

这个文件没有显式模块文档字符串，可以重点看顶层类、函数和导入关系。

## 顶层导入

- `base64`
- `logging`
- `os`
- `shutil`
- `socket`
- `ssl`
- `time`
- `uuid`
- `zipfile`
- `from pathlib import Path`
- `aiohttp`
- `certifi`
- `psutil`
- `from PIL import Image`
- `from astrbot_path import get_astrbot_data_path, get_astrbot_path, get_astrbot_temp_path`

## 顶层类

- 无顶层类定义。

## 顶层函数

- `on_error`：A callback of the rmtree function
- `remove_dir`：建议阅读函数签名和调用位置来判断用途。
- `port_checker`：建议阅读函数签名和调用位置来判断用途。
- `save_temp_img`：建议阅读函数签名和调用位置来判断用途。
- `download_image_by_url`：下载图片, 返回 path
- `download_file`：从指定 url 下载文件到指定路径 path
- `file_to_base64`：建议阅读函数签名和调用位置来判断用途。
- `get_local_ip_addresses`：建议阅读函数签名和调用位置来判断用途。
- `get_dashboard_version`：建议阅读函数签名和调用位置来判断用途。
- `download_dashboard`：下载管理面板文件

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
- [llm_metadata.py](llm_metadata.py.md)
- [log_pipe.py](log_pipe.py.md)
- [media_utils.py](media_utils.py.md)
- [metrics.py](metrics.py.md)
- 其余 18 个同目录文件省略

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。