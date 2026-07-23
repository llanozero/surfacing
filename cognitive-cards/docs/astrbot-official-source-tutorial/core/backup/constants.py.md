# 文件教程：core/backup/constants.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\backup\constants.py`
- 文件类型：`.py`
- 文件大小：`2533` 字节
- 所属目录教程：[core/backup](README.md)

## 它是做什么的

AstrBot 备份模块共享常量

## 角色判断

这个文件位于核心实现层，通常承载底层机制、抽象或运行时行为。

## 模块文档字符串

AstrBot 备份模块共享常量

此文件定义了导出器和导入器共享的常量，确保两端配置一致。

## 顶层导入

- `from sqlmodel import SQLModel`
- `from astrbot.core.db.po import Attachment, ChatUIProject, CommandConfig, CommandConflict, ConversationV2, Persona`
- `from astrbot.core.knowledge_base.models import KBDocument, KBMedia, KnowledgeBase`
- `from astrbot.core.utils.astrbot_path import get_astrbot_config_path, get_astrbot_plugin_data_path, get_astrbot_plugin_path, get_astrbot_t2i_templates_path, get_astrbot_temp_path, get_astrbot_webchat_path`

## 顶层类

- 无顶层类定义。

## 顶层函数

- `get_backup_directories`：获取需要备份的目录列表

## 阅读建议

- 建议从模块文档字符串、顶层类和顶层函数出发，再搜索这些名字的调用位置。

## 同目录相关文件

- [__init__.py](__init__.py.md)
- [exporter.py](exporter.py.md)
- [importer.py](importer.py.md)

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。