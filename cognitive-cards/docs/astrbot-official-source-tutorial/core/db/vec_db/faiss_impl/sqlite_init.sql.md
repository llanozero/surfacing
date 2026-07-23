# 文件教程：core/db/vec_db/faiss_impl/sqlite_init.sql

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\db\vec_db\faiss_impl\sqlite_init.sql`
- 文件类型：`.sql`
- 文件大小：`697` 字节
- 所属目录教程：[core/db/vec_db/faiss_impl](README.md)

## 它是做什么的

-- 创建文档存储表，包含 faiss 中文档的 id，文档文本，create_at，updated_at

## 角色判断

这个文件位于核心实现层，通常承载底层机制、抽象或运行时行为。

## 文件内容摘要

以下是文件前 30 行的截断预览，便于快速判断内容：

```text
-- 创建文档存储表，包含 faiss 中文档的 id，文档文本，create_at，updated_at
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id TEXT NOT NULL,
    text TEXT NOT NULL,
    metadata TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE documents
ADD COLUMN group_id TEXT GENERATED ALWAYS AS (json_extract(metadata, '$.group_id')) STORED;
ALTER TABLE documents
ADD COLUMN user_id TEXT GENERATED ALWAYS AS (json_extract(metadata, '$.user_id')) STORED;

CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_documents_group_id ON documents(group_id);
```

## 阅读建议

- 建议结合同目录 Python 文件一起看，确认这个文件在运行时如何被加载。

## 同目录相关文件

- [__init__.py](__init__.py.md)
- [document_storage.py](document_storage.py.md)
- [embedding_storage.py](embedding_storage.py.md)
- [vec_db.py](vec_db.py.md)

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。