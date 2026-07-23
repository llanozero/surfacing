# 文件教程：core/agent/context/compressor.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\agent\context\compressor.py`
- 文件类型：`.py`
- 文件大小：`8594` 字节
- 所属目录教程：[core/agent/context](README.md)

## 它是做什么的

这个文件主要定义了 ContextCompressor、TruncateByTurnsCompressor、LLMSummaryCompressor 等顶层类。

## 角色判断

这个文件位于核心实现层，通常承载底层机制、抽象或运行时行为。

## 模块文档字符串

这个文件没有显式模块文档字符串，可以重点看顶层类、函数和导入关系。

## 顶层导入

- `from typing import TYPE_CHECKING, Protocol, runtime_checkable`
- `from message import Message`
- `from context.truncator import ContextTruncator`

## 顶层类

- `ContextCompressor`：Protocol for context compressors
- `TruncateByTurnsCompressor`：Truncate by turns compressor implementation
- `LLMSummaryCompressor`：LLM-based summary compressor

## 顶层函数

- `split_history`：Split the message list into system messages, messages to summarize, and recent messages

## 阅读建议

- 建议从模块文档字符串、顶层类和顶层函数出发，再搜索这些名字的调用位置。

## 同目录相关文件

- [config.py](config.py.md)
- [manager.py](manager.py.md)
- [token_counter.py](token_counter.py.md)
- [truncator.py](truncator.py.md)

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。