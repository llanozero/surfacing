# 目录教程：core/db/vec_db/faiss_impl

## 目录定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\db\vec_db\faiss_impl`
- 相对根目录：`core/db/vec_db/faiss_impl`
- 直接子目录数：`0`
- 直接文件数：`5`
- 直接 Python 文件数：`4`

## 目录作用

阅读这个目录时，建议先看它的 `README.md`（若有）、`__init__.py`、`main.py` 或带有 `manager` / `adapter` / `event` / `routes` 命名的文件。

## 直接子目录

- 无

## 直接文件

- `__init__.py`：查看 [__init__.py](__init__.py.md)：from
- `document_storage.py`：查看 [document_storage.py](document_storage.py.md)：这个文件主要定义了 BaseDocModel、Document、DocumentStorage 等顶层类。
- `embedding_storage.py`：查看 [embedding_storage.py](embedding_storage.py.md)：这个文件主要定义了 EmbeddingStorage 等顶层类。
- `sqlite_init.sql`：查看 [sqlite_init.sql](sqlite_init.sql.md)：-- 创建文档存储表，包含 faiss 中文档的 id，文档文本，create_at，updated_at
- `vec_db.py`：查看 [vec_db.py](vec_db.py.md)：这个文件主要定义了 FaissVecDB 等顶层类。

## 文件类型分布

- `.py`：4 个
- `.sql`：1 个

## 建议阅读顺序

- `__init__.py`

## 维护提示

- 这份目录教程基于当前官方源码快照自动生成。
- 如果你要继续深入，建议从本目录下带有入口含义的文件开始，再跟踪它引用的子模块。