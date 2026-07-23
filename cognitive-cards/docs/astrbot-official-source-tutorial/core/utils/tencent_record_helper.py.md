# 文件教程：core/utils/tencent_record_helper.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\utils\tencent_record_helper.py`
- 文件类型：`.py`
- 文件大小：`5262` 字节
- 所属目录教程：[core/utils](README.md)

## 它是做什么的

这个文件主要提供了 tencent_silk_to_wav、wav_to_tencent_silk、convert_to_pcm_wav、audio_to_tencent_silk_base64 等顶层函数。

## 角色判断

这是一个工具文件，通常提供可复用的辅助函数或基础设施能力。

## 模块文档字符串

这个文件没有显式模块文档字符串，可以重点看顶层类、函数和导入关系。

## 顶层导入

- `asyncio`
- `base64`
- `os`
- `subprocess`
- `tempfile`
- `wave`
- `from io import BytesIO`
- `from astrbot.core import logger`
- `from astrbot.core.utils.astrbot_path import get_astrbot_temp_path`

## 顶层类

- 无顶层类定义。

## 顶层函数

- `tencent_silk_to_wav`：建议阅读函数签名和调用位置来判断用途。
- `wav_to_tencent_silk`：返回 duration
- `convert_to_pcm_wav`：将 MP3 或其他音频格式转换为 PCM 16bit WAV，采样率24000Hz，单声道
- `audio_to_tencent_silk_base64`：将 MP3/WAV 文件转为 Tencent Silk 并返回 base64 编码与时长（秒）

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