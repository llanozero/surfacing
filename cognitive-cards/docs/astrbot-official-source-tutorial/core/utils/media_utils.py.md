# 文件教程：core/utils/media_utils.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\utils\media_utils.py`
- 文件类型：`.py`
- 文件大小：`15503` 字节
- 所属目录教程：[core/utils](README.md)

## 它是做什么的

媒体文件处理工具

## 角色判断

这是一个工具文件，通常提供可复用的辅助函数或基础设施能力。

## 模块文档字符串

媒体文件处理工具

提供音视频格式转换、时长获取等功能。

## 顶层导入

- `asyncio`
- `base64`
- `io`
- `os`
- `subprocess`
- `uuid`
- `from pathlib import Path`
- `from PIL import Image`
- `from astrbot import logger`
- `from astrbot.core.utils.astrbot_path import get_astrbot_temp_path`

## 顶层类

- 无顶层类定义。

## 顶层函数

- `get_media_duration`：使用ffprobe获取媒体文件时长
- `convert_audio_to_opus`：使用ffmpeg将音频转换为opus格式
- `convert_video_format`：使用ffmpeg转换视频格式
- `convert_audio_format`：使用ffmpeg将音频转换为指定格式
- `convert_audio_to_amr`：将音频转换为amr格式
- `convert_audio_to_wav`：将音频转换为wav格式
- `ensure_wav`：Ensure the audio path points to wav format by extension/guess and convert when needed
- `_get_audio_magic_type`：Detect common audio formats from magic bytes
- `extract_video_cover`：从视频中提取封面图(JPG)
- `_compress_image_sync`：Run image compression synchronously via ``asyncio
- `compress_image`：Compress large user-uploaded images

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
- [metrics.py](metrics.py.md)
- 其余 18 个同目录文件省略

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。