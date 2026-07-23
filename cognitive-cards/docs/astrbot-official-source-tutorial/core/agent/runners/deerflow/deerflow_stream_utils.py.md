# 文件教程：core/agent/runners/deerflow/deerflow_stream_utils.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\agent\runners\deerflow\deerflow_stream_utils.py`
- 文件类型：`.py`
- 文件大小：`6882` 字节
- 所属目录教程：[core/agent/runners/deerflow](README.md)

## 它是做什么的

这个文件主要提供了 extract_text、extract_messages_from_values_data、is_ai_message、extract_latest_ai_text 等顶层函数。

## 角色判断

这是一个工具文件，通常提供可复用的辅助函数或基础设施能力。

## 模块文档字符串

这个文件没有显式模块文档字符串，可以重点看顶层类、函数和导入关系。

## 顶层导入

- `typing`
- `from collections.abc import Iterable`

## 顶层类

- 无顶层类定义。

## 顶层函数

- `extract_text`：建议阅读函数签名和调用位置来判断用途。
- `extract_messages_from_values_data`：Extract messages list from possible values event payload shapes
- `is_ai_message`：建议阅读函数签名和调用位置来判断用途。
- `extract_latest_ai_text`：建议阅读函数签名和调用位置来判断用途。
- `extract_latest_ai_message`：建议阅读函数签名和调用位置来判断用途。
- `is_clarification_tool_message`：建议阅读函数签名和调用位置来判断用途。
- `extract_latest_clarification_text`：建议阅读函数签名和调用位置来判断用途。
- `get_message_id`：建议阅读函数签名和调用位置来判断用途。
- `extract_event_message_obj`：建议阅读函数签名和调用位置来判断用途。
- `extract_ai_delta_from_event_data`：建议阅读函数签名和调用位置来判断用途。
- `extract_clarification_from_event_data`：建议阅读函数签名和调用位置来判断用途。
- `_iter_custom_event_items`：建议阅读函数签名和调用位置来判断用途。
- `extract_task_failures_from_custom_event`：建议阅读函数签名和调用位置来判断用途。
- `build_task_failure_summary`：建议阅读函数签名和调用位置来判断用途。

## 阅读建议

- 建议从模块文档字符串、顶层类和顶层函数出发，再搜索这些名字的调用位置。

## 同目录相关文件

- [constants.py](constants.py.md)
- [deerflow_agent_runner.py](deerflow_agent_runner.py.md)
- [deerflow_api_client.py](deerflow_api_client.py.md)
- [deerflow_content_mapper.py](deerflow_content_mapper.py.md)

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。