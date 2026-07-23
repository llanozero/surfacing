# 文件教程：core/provider/sources/openai_embedding_source.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\provider\sources\openai_embedding_source.py`
- 文件类型：`.py`
- 文件大小：`3583` 字节
- 所属目录教程：[core/provider/sources](README.md)

## 它是做什么的

这个文件主要定义了 OpenAIEmbeddingProvider 等顶层类。

## 角色判断

这个文件位于核心实现层，通常承载底层机制、抽象或运行时行为。

## 模块文档字符串

这个文件没有显式模块文档字符串，可以重点看顶层类、函数和导入关系。

## 顶层导入

- `httpx`
- `from openai import AsyncOpenAI`
- `from astrbot import logger`
- `from entities import ProviderType`
- `from provider import EmbeddingProvider`
- `from register import register_provider_adapter`

## 顶层类

- `OpenAIEmbeddingProvider`：建议阅读类定义与方法名来判断职责。

## 顶层函数

- 无顶层函数定义。

## 阅读建议

- 建议从模块文档字符串、顶层类和顶层函数出发，再搜索这些名字的调用位置。

## 同目录相关文件

- [anthropic_source.py](anthropic_source.py.md)
- [azure_tts_source.py](azure_tts_source.py.md)
- [bailian_rerank_source.py](bailian_rerank_source.py.md)
- [dashscope_tts.py](dashscope_tts.py.md)
- [edge_tts_source.py](edge_tts_source.py.md)
- [fishaudio_tts_api_source.py](fishaudio_tts_api_source.py.md)
- [gemini_embedding_source.py](gemini_embedding_source.py.md)
- [gemini_source.py](gemini_source.py.md)
- [gemini_tts_source.py](gemini_tts_source.py.md)
- [genie_tts.py](genie_tts.py.md)
- [groq_source.py](groq_source.py.md)
- [gsv_selfhosted_source.py](gsv_selfhosted_source.py.md)
- [gsvi_tts_source.py](gsvi_tts_source.py.md)
- [kimi_code_source.py](kimi_code_source.py.md)
- [longcat_source.py](longcat_source.py.md)
- 其余 19 个同目录文件省略

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。