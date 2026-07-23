# 目录教程：core/platform

## 目录定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\platform`
- 相对根目录：`core/platform`
- 直接子目录数：`1`
- 直接文件数：`9`
- 直接 Python 文件数：`9`

## 目录作用

阅读这个目录时，建议先看它的 `README.md`（若有）、`__init__.py`、`main.py` 或带有 `manager` / `adapter` / `event` / `routes` 命名的文件。

## 直接子目录

- `sources`：查看 [sources](sources/README.md)

## 直接文件

- `__init__.py`：查看 [__init__.py](__init__.py.md)：from
- `astr_message_event.py`：查看 [astr_message_event.py](astr_message_event.py.md)：这个文件主要定义了 AstrMessageEvent 等顶层类。
- `astrbot_message.py`：查看 [astrbot_message.py](astrbot_message.py.md)：这个文件主要定义了 MessageMember、Group、AstrBotMessage 等顶层类。
- `manager.py`：查看 [manager.py](manager.py.md)：这个文件主要定义了 PlatformTasks、PlatformManager 等顶层类。
- `message_session.py`：查看 [message_session.py](message_session.py.md)：这个文件主要定义了 MessageSession 等顶层类。
- `message_type.py`：查看 [message_type.py](message_type.py.md)：这个文件主要定义了 MessageType 等顶层类。
- `platform.py`：查看 [platform.py](platform.py.md)：这个文件主要定义了 PlatformStatus、PlatformError、Platform 等顶层类。
- `platform_metadata.py`：查看 [platform_metadata.py](platform_metadata.py.md)：这个文件主要定义了 PlatformMetadata 等顶层类。
- `register.py`：查看 [register.py](register.py.md)：这个文件主要提供了 register_platform_adapter、unregister_platform_adapters_by_module 等顶层函数。

## 文件类型分布

- `.py`：9 个

## 建议阅读顺序

- `__init__.py`
- `astr_message_event.py`
- `manager.py`

## 维护提示

- 这份目录教程基于当前官方源码快照自动生成。
- 如果你要继续深入，建议从本目录下带有入口含义的文件开始，再跟踪它引用的子模块。