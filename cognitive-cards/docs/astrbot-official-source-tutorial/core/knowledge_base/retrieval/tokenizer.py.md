# 文件教程：core/knowledge_base/retrieval/tokenizer.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\knowledge_base\retrieval\tokenizer.py`
- 文件类型：`.py`
- 文件大小：`1126` 字节
- 所属目录教程：[core/knowledge_base/retrieval](README.md)

## 它是做什么的

Tokenization helpers shared by sparse retrieval indexes

## 角色判断

这个文件位于核心实现层，通常承载底层机制、抽象或运行时行为。

## 模块文档字符串

Tokenization helpers shared by sparse retrieval indexes.

## 顶层导入

- `re`
- `from pathlib import Path`
- `from re import Pattern`
- `jieba`

## 顶层类

- 无顶层类定义。

## 顶层函数

- `load_stopwords`：建议阅读函数签名和调用位置来判断用途。
- `tokenize_text`：建议阅读函数签名和调用位置来判断用途。
- `to_fts5_search_text`：建议阅读函数签名和调用位置来判断用途。
- `quote_fts5_token`：建议阅读函数签名和调用位置来判断用途。
- `build_fts5_or_query`：建议阅读函数签名和调用位置来判断用途。

## 阅读建议

- 建议从模块文档字符串、顶层类和顶层函数出发，再搜索这些名字的调用位置。

## 同目录相关文件

- [__init__.py](__init__.py.md)
- [hit_stopwords.txt](hit_stopwords.txt.md)
- [manager.py](manager.py.md)
- [rank_fusion.py](rank_fusion.py.md)
- [sparse_retriever.py](sparse_retriever.py.md)

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。