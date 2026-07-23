# 文件教程：core/computer/file_read_utils.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\computer\file_read_utils.py`
- 文件类型：`.py`
- 文件大小：`21509` 字节
- 所属目录教程：[core/computer](README.md)

## 它是做什么的

这个文件主要定义了 FileProbe、ParsedDocument 等顶层类。

## 角色判断

这是一个工具文件，通常提供可复用的辅助函数或基础设施能力。

## 模块文档字符串

这个文件没有显式模块文档字符串，可以重点看顶层类、函数和导入关系。

## 顶层导入

- `from __future__ import annotations`
- `base64`
- `hashlib`
- `io`
- `json`
- `zipfile`
- `from asyncio import to_thread`
- `from dataclasses import dataclass`
- `from pathlib import Path`
- `from typing import Literal`
- `mcp`
- `from astrbot.core.agent.context.token_counter import EstimateTokenCounter`
- `from astrbot.core.agent.message import Message`
- `from astrbot.core.agent.tool import ToolExecResult`
- `from astrbot.core.utils.astrbot_path import get_astrbot_temp_path`
- `from astrbot.core.utils.media_utils import IMAGE_COMPRESS_DEFAULT_MAX_SIZE, IMAGE_COMPRESS_DEFAULT_OPTIMIZE, IMAGE_COMPRESS_DEFAULT_QUALITY, _compress_image_sync`
- `from booters.base import ComputerBooter`

## 顶层类

- `FileProbe`：建议阅读类定义与方法名来判断职责。
- `ParsedDocument`：建议阅读类定义与方法名来判断职责。

## 顶层函数

- `_build_probe_script`：建议阅读函数签名和调用位置来判断用途。
- `_build_text_read_script`：建议阅读函数签名和调用位置来判断用途。
- `_build_image_read_script`：建议阅读函数签名和调用位置来判断用途。
- `_looks_like_text`：建议阅读函数签名和调用位置来判断用途。
- `detect_text_encoding`：建议阅读函数签名和调用位置来判断用途。
- `read_local_text_range_sync`：建议阅读函数签名和调用位置来判断用途。
- `read_local_text_range`：建议阅读函数签名和调用位置来判断用途。
- `_exec_python_json`：建议阅读函数签名和调用位置来判断用途。
- `_probe_local_file`：建议阅读函数签名和调用位置来判断用途。
- `_read_local_image_base64`：建议阅读函数签名和调用位置来判断用途。
- `_read_local_file_bytes`：建议阅读函数签名和调用位置来判断用途。
- `_compress_image_bytes_to_base64`：建议阅读函数签名和调用位置来判断用途。
- `_detect_image_mime`：建议阅读函数签名和调用位置来判断用途。
- `_looks_like_known_binary`：建议阅读函数签名和调用位置来判断用途。
- `_looks_like_pdf`：建议阅读函数签名和调用位置来判断用途。
- `_looks_like_zip_container`：建议阅读函数签名和调用位置来判断用途。
- `_is_docx_bytes`：建议阅读函数签名和调用位置来判断用途。
- `_parse_local_docx_text`：建议阅读函数签名和调用位置来判断用途。
- `_parse_local_pdf_text`：建议阅读函数签名和调用位置来判断用途。
- `_parse_local_supported_document`：建议阅读函数签名和调用位置来判断用途。
- `_probe_file`：建议阅读函数签名和调用位置来判断用途。
- `_validate_text_output`：建议阅读函数签名和调用位置来判断用途。
- `_text_exceeds_read_thresholds`：建议阅读函数签名和调用位置来判断用途。
- `_validate_full_text_read_request`：建议阅读函数签名和调用位置来判断用途。
- `_slice_text_by_lines`：建议阅读函数签名和调用位置来判断用途。
- `_store_converted_text_for_workspace`：建议阅读函数签名和调用位置来判断用途。
- `_build_converted_text_notice`：建议阅读函数签名和调用位置来判断用途。
- `_read_local_supported_document_result`：建议阅读函数签名和调用位置来判断用途。
- `read_file_tool_result`：建议阅读函数签名和调用位置来判断用途。

## 阅读建议

- 建议从模块文档字符串、顶层类和顶层函数出发，再搜索这些名字的调用位置。

## 同目录相关文件

- [computer_client.py](computer_client.py.md)

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。