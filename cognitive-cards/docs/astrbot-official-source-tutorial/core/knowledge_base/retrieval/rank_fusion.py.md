# 文件教程：core/knowledge_base/retrieval/rank_fusion.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\knowledge_base\retrieval\rank_fusion.py`
- 文件类型：`.py`
- 文件大小：`4591` 字节
- 所属目录教程：[core/knowledge_base/retrieval](README.md)

## 它是做什么的

检索结果融合器

## 角色判断

这个文件位于核心实现层，通常承载底层机制、抽象或运行时行为。

## 模块文档字符串

检索结果融合器

使用 Reciprocal Rank Fusion (RRF) 算法融合稠密检索和稀疏检索的结果

## 顶层导入

- `json`
- `from dataclasses import dataclass`
- `from astrbot.core.db.vec_db.base import Result`
- `from astrbot.core.knowledge_base.kb_db_sqlite import KBSQLiteDatabase`
- `from astrbot.core.knowledge_base.retrieval.sparse_retriever import SparseResult`

## 顶层类

- `FusedResult`：融合后的检索结果
- `RankFusion`：检索结果融合器

## 顶层函数

- 无顶层函数定义。

## 阅读建议

- 建议从模块文档字符串、顶层类和顶层函数出发，再搜索这些名字的调用位置。

## 同目录相关文件

- [__init__.py](__init__.py.md)
- [hit_stopwords.txt](hit_stopwords.txt.md)
- [manager.py](manager.py.md)
- [sparse_retriever.py](sparse_retriever.py.md)
- [tokenizer.py](tokenizer.py.md)

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。