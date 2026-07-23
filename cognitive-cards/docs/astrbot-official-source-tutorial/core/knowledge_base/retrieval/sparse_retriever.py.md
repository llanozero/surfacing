# 文件教程：core/knowledge_base/retrieval/sparse_retriever.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\knowledge_base\retrieval\sparse_retriever.py`
- 文件类型：`.py`
- 文件大小：`5383` 字节
- 所属目录教程：[core/knowledge_base/retrieval](README.md)

## 它是做什么的

稀疏检索器

## 角色判断

这个文件位于核心实现层，通常承载底层机制、抽象或运行时行为。

## 模块文档字符串

稀疏检索器

使用 BM25 算法进行基于关键词的文档检索

## 顶层导入

- `json`
- `os`
- `from dataclasses import dataclass`
- `from typing import TYPE_CHECKING`
- `from rank_bm25 import BM25Okapi`
- `from astrbot.core.knowledge_base.kb_db_sqlite import KBSQLiteDatabase`
- `from astrbot.core.knowledge_base.retrieval.tokenizer import load_stopwords, tokenize_text`

## 顶层类

- `SparseResult`：稀疏检索结果
- `SparseRetriever`：BM25 稀疏检索器

## 顶层函数

- 无顶层函数定义。

## 阅读建议

- 建议从模块文档字符串、顶层类和顶层函数出发，再搜索这些名字的调用位置。

## 同目录相关文件

- [__init__.py](__init__.py.md)
- [hit_stopwords.txt](hit_stopwords.txt.md)
- [manager.py](manager.py.md)
- [rank_fusion.py](rank_fusion.py.md)
- [tokenizer.py](tokenizer.py.md)

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。