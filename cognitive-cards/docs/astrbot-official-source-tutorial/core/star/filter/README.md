# 目录教程：core/star/filter

## 目录定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\star\filter`
- 相对根目录：`core/star/filter`
- 直接子目录数：`0`
- 直接文件数：`8`
- 直接 Python 文件数：`8`

## 目录作用

阅读这个目录时，建议先看它的 `README.md`（若有）、`__init__.py`、`main.py` 或带有 `manager` / `adapter` / `event` / `routes` 命名的文件。

## 直接子目录

- 无

## 直接文件

- `__init__.py`：查看 [__init__.py](__init__.py.md)：这个文件主要定义了 HandlerFilter 等顶层类。
- `command.py`：查看 [command.py](command.py.md)：这个文件主要定义了 GreedyStr、CommandFilter 等顶层类。
- `command_group.py`：查看 [command_group.py](command_group.py.md)：这个文件主要定义了 CommandGroupFilter 等顶层类。
- `custom_filter.py`：查看 [custom_filter.py](custom_filter.py.md)：这个文件主要定义了 CustomFilterMeta、CustomFilter、CustomFilterOr 等顶层类。
- `event_message_type.py`：查看 [event_message_type.py](event_message_type.py.md)：这个文件主要定义了 EventMessageType、EventMessageTypeFilter 等顶层类。
- `permission.py`：查看 [permission.py](permission.py.md)：这个文件主要定义了 PermissionType、PermissionTypeFilter 等顶层类。
- `platform_adapter_type.py`：查看 [platform_adapter_type.py](platform_adapter_type.py.md)：这个文件主要定义了 PlatformAdapterType、PlatformAdapterTypeFilter 等顶层类。
- `regex.py`：查看 [regex.py](regex.py.md)：这个文件主要定义了 RegexFilter 等顶层类。

## 文件类型分布

- `.py`：8 个

## 建议阅读顺序

- `__init__.py`
- `event_message_type.py`
- `platform_adapter_type.py`

## 维护提示

- 这份目录教程基于当前官方源码快照自动生成。
- 如果你要继续深入，建议从本目录下带有入口含义的文件开始，再跟踪它引用的子模块。