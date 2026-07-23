# 目录教程：core/platform/sources/discord

## 目录定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\platform\sources\discord`
- 相对根目录：`core/platform/sources/discord`
- 直接子目录数：`0`
- 直接文件数：`4`
- 直接 Python 文件数：`4`

## 目录作用

阅读这个目录时，建议先看它的 `README.md`（若有）、`__init__.py`、`main.py` 或带有 `manager` / `adapter` / `event` / `routes` 命名的文件。

## 直接子目录

- 无

## 直接文件

- `client.py`：查看 [client.py](client.py.md)：这个文件主要定义了 DiscordBotClient 等顶层类。
- `components.py`：查看 [components.py](components.py.md)：这个文件主要定义了 DiscordEmbed、DiscordButton、DiscordReference 等顶层类。
- `discord_platform_adapter.py`：查看 [discord_platform_adapter.py](discord_platform_adapter.py.md)：这个文件主要定义了 DiscordPlatformAdapter 等顶层类。
- `discord_platform_event.py`：查看 [discord_platform_event.py](discord_platform_event.py.md)：这个文件主要定义了 DiscordViewComponent、DiscordPlatformEvent 等顶层类。

## 文件类型分布

- `.py`：4 个

## 建议阅读顺序

- `discord_platform_adapter.py`
- `discord_platform_event.py`

## 维护提示

- 这份目录教程基于当前官方源码快照自动生成。
- 如果你要继续深入，建议从本目录下带有入口含义的文件开始，再跟踪它引用的子模块。