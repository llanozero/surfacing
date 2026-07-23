# 目录教程：core/knowledge_base

## 目录定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\knowledge_base`
- 相对根目录：`core/knowledge_base`
- 直接子目录数：`3`
- 直接文件数：`5`
- 直接 Python 文件数：`5`

## 目录作用

阅读这个目录时，建议先看它的 `README.md`（若有）、`__init__.py`、`main.py` 或带有 `manager` / `adapter` / `event` / `routes` 命名的文件。

## 直接子目录

- `chunking`：查看 [chunking](chunking/README.md)
- `parsers`：查看 [parsers](parsers/README.md)
- `retrieval`：查看 [retrieval](retrieval/README.md)

## 直接文件

- `kb_db_sqlite.py`：查看 [kb_db_sqlite.py](kb_db_sqlite.py.md)：这个文件主要定义了 KBSQLiteDatabase 等顶层类。
- `kb_helper.py`：查看 [kb_helper.py](kb_helper.py.md)：这个文件主要定义了 RateLimiter、KBHelper 等顶层类。
- `kb_mgr.py`：查看 [kb_mgr.py](kb_mgr.py.md)：这个文件主要定义了 KnowledgeBaseManager 等顶层类。
- `models.py`：查看 [models.py](models.py.md)：这个文件主要定义了 BaseKBModel、KnowledgeBase、KBDocument 等顶层类。
- `prompts.py`：查看 [prompts.py](prompts.py.md)：TEXT_REPAIR_SYSTEM_PROMPT = """You are a meticulous digital archivist

## 文件类型分布

- `.py`：5 个

## 建议阅读顺序

- `models.py`

## 维护提示

- 这份目录教程基于当前官方源码快照自动生成。
- 如果你要继续深入，建议从本目录下带有入口含义的文件开始，再跟踪它引用的子模块。