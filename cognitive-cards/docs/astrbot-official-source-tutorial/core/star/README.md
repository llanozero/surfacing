# 目录教程：core/star

## 目录定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\star`
- 相对根目录：`core/star`
- 直接子目录数：`2`
- 直接文件数：`14`
- 直接 Python 文件数：`13`

## 目录作用

阅读这个目录时，建议先看它的 `README.md`（若有）、`__init__.py`、`main.py` 或带有 `manager` / `adapter` / `event` / `routes` 命名的文件。

## 直接子目录

- `filter`：查看 [filter](filter/README.md)
- `register`：查看 [register](register/README.md)

## 直接文件

- `__init__.py`：查看 [__init__.py](__init__.py.md)：# 兼容导出: Provider 从 provider 模块重新导出
- `base.py`：查看 [base.py](base.py.md)：这个文件主要定义了 Star 等顶层类。
- `command_management.py`：查看 [command_management.py](command_management.py.md)：这个文件主要定义了 CommandDescriptor 等顶层类。
- `config.py`：查看 [config.py](config.py.md)：此功能已过时，参考 https://astrbot
- `context.py`：查看 [context.py](context.py.md)：这个文件主要定义了 PlatformManagerProtocol、Context 等顶层类。
- `error_messages.py`：查看 [error_messages.py](error_messages.py.md)：Shared plugin error message templates for star manager flows
- `README.md`：查看 [README.md](README.md.md)：# AstrBot Star
- `session_llm_manager.py`：查看 [session_llm_manager.py](session_llm_manager.py.md)：会话服务管理器 - 负责管理每个会话的LLM、TTS等服务的启停状态
- `session_plugin_manager.py`：查看 [session_plugin_manager.py](session_plugin_manager.py.md)：会话插件管理器 - 负责管理每个会话的插件启停状态
- `star.py`：查看 [star.py](star.py.md)：这个文件主要定义了 StarMetadata 等顶层类。
- `star_handler.py`：查看 [star_handler.py](star_handler.py.md)：这个文件主要定义了 StarHandlerRegistry、EventType、StarHandlerMetadata 等顶层类。
- `star_manager.py`：查看 [star_manager.py](star_manager.py.md)：插件的重载、启停、安装、卸载等操作
- `star_tools.py`：查看 [star_tools.py](star_tools.py.md)：插件开发工具集
- `updator.py`：查看 [updator.py](updator.py.md)：这个文件主要定义了 PluginUpdator 等顶层类。

## 文件类型分布

- `.md`：1 个
- `.py`：13 个

## 建议阅读顺序

- `__init__.py`
- `session_llm_manager.py`
- `session_plugin_manager.py`
- `star_manager.py`

## 维护提示

- 这份目录教程基于当前官方源码快照自动生成。
- 如果你要继续深入，建议从本目录下带有入口含义的文件开始，再跟踪它引用的子模块。