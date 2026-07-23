# 文件教程：dashboard/routes/util.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\dashboard\routes\util.py`
- 文件类型：`.py`
- 文件大小：`2958` 字节
- 所属目录教程：[dashboard/routes](README.md)

## 它是做什么的

Dashboard 路由工具集

## 角色判断

这是一个工具文件，通常提供可复用的辅助函数或基础设施能力。

## 模块文档字符串

Dashboard 路由工具集。

这里放一些 dashboard routes 可复用的小工具函数。

目前主要用于「配置文件上传（file 类型配置项）」功能：
- 清洗/规范化用户可控的文件名与相对路径
- 将配置 key 映射到配置项独立子目录

## 顶层导入

- `os`

## 顶层类

- 无顶层类定义。

## 顶层函数

- `get_schema_item`：按 dot-path 获取 schema 的节点
- `sanitize_filename`：清洗上传文件名，避免路径穿越与非法名称
- `sanitize_path_segment`：清洗目录片段（URL/path 安全，避免穿越）
- `config_key_to_folder`：将 dot-path 的配置 key 转成稳定的文件夹路径
- `normalize_rel_path`：规范化用户传入的相对路径，并阻止路径穿越

## 阅读建议

- 建议从模块文档字符串、顶层类和顶层函数出发，再搜索这些名字的调用位置。

## 同目录相关文件

- [__init__.py](__init__.py.md)
- [api_key.py](api_key.py.md)
- [auth.py](auth.py.md)
- [backup.py](backup.py.md)
- [chat.py](chat.py.md)
- [chatui_project.py](chatui_project.py.md)
- [command.py](command.py.md)
- [config.py](config.py.md)
- [conversation.py](conversation.py.md)
- [cron.py](cron.py.md)
- [file.py](file.py.md)
- [knowledge_base.py](knowledge_base.py.md)
- [live_chat.py](live_chat.py.md)
- [log.py](log.py.md)
- [open_api.py](open_api.py.md)
- 其余 12 个同目录文件省略

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。