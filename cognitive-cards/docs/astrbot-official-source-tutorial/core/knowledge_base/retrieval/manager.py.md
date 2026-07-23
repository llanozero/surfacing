# 文件教程：core/knowledge_base/retrieval/manager.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\knowledge_base\retrieval\manager.py`
- 文件类型：`.py`
- 文件大小：`9351` 字节
- 所属目录教程：[core/knowledge_base/retrieval](README.md)

## 它是做什么的

检索管理器

## 角色判断

这是一个管理器文件，通常持有运行时状态，并负责编排一类业务流程。

## 模块文档字符串

检索管理器

协调稠密检索、稀疏检索和 Rerank,提供统一的检索接口

## 顶层导入

- `time`
- `from dataclasses import dataclass`
- `from typing import TYPE_CHECKING`
- `from astrbot import logger`
- `from astrbot.core.db.vec_db.base import Result`
- `from astrbot.core.knowledge_base.kb_db_sqlite import KBSQLiteDatabase`
- `from astrbot.core.knowledge_base.retrieval.rank_fusion import RankFusion`
- `from astrbot.core.knowledge_base.retrieval.sparse_retriever import SparseRetriever`
- `from astrbot.core.provider.provider import RerankProvider`
- `from kb_helper import KBHelper`

## 顶层类

- `RetrievalResult`：检索结果
- `RetrievalManager`：检索管理器

## 顶层函数

- 无顶层函数定义。

## 阅读建议

- 重点看内部状态字段、生命周期和跨模块调用。
- 建议从模块文档字符串、顶层类和顶层函数出发，再搜索这些名字的调用位置。

## 同目录相关文件

- [__init__.py](__init__.py.md)
- [hit_stopwords.txt](hit_stopwords.txt.md)
- [rank_fusion.py](rank_fusion.py.md)
- [sparse_retriever.py](sparse_retriever.py.md)
- [tokenizer.py](tokenizer.py.md)

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。