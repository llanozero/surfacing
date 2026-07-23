# 目录教程：core/tools

## 目录定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\tools`
- 相对根目录：`core/tools`
- 直接子目录数：`1`
- 直接文件数：`5`
- 直接 Python 文件数：`5`

## 目录作用

阅读这个目录时，建议先看它的 `README.md`（若有）、`__init__.py`、`main.py` 或带有 `manager` / `adapter` / `event` / `routes` 命名的文件。

## 直接子目录

- `computer_tools`：查看 [computer_tools](computer_tools/README.md)

## 直接文件

- `cron_tools.py`：查看 [cron_tools.py](cron_tools.py.md)：这个文件主要定义了 FutureTaskTool 等顶层类。
- `knowledge_base_tools.py`：查看 [knowledge_base_tools.py](knowledge_base_tools.py.md)：这个文件主要定义了 KnowledgeBaseQueryTool 等顶层类。
- `message_tools.py`：查看 [message_tools.py](message_tools.py.md)：这个文件主要定义了 SendMessageToUserTool 等顶层类。
- `registry.py`：查看 [registry.py](registry.py.md)：这个文件主要定义了 BuiltinToolConfigCondition、BuiltinToolConfigRule 等顶层类。
- `web_search_tools.py`：查看 [web_search_tools.py](web_search_tools.py.md)：这个文件主要定义了 SearchResult、_KeyRotator、TavilyWebSearchTool 等顶层类。

## 文件类型分布

- `.py`：5 个

## 建议阅读顺序

- 先看直接子文件中的 Python 源文件，再按依赖关系向下追踪。

## 维护提示

- 这份目录教程基于当前官方源码快照自动生成。
- 如果你要继续深入，建议从本目录下带有入口含义的文件开始，再跟踪它引用的子模块。