# 目录教程：core/platform/sources/misskey

## 目录定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\platform\sources\misskey`
- 相对根目录：`core/platform/sources/misskey`
- 直接子目录数：`0`
- 直接文件数：`4`
- 直接 Python 文件数：`4`

## 目录作用

阅读这个目录时，建议先看它的 `README.md`（若有）、`__init__.py`、`main.py` 或带有 `manager` / `adapter` / `event` / `routes` 命名的文件。

## 直接子目录

- 无

## 直接文件

- `misskey_adapter.py`：查看 [misskey_adapter.py](misskey_adapter.py.md)：这个文件主要定义了 MisskeyPlatformAdapter 等顶层类。
- `misskey_api.py`：查看 [misskey_api.py](misskey_api.py.md)：这个文件主要定义了 APIError、APIConnectionError、APIRateLimitError 等顶层类。
- `misskey_event.py`：查看 [misskey_event.py](misskey_event.py.md)：这个文件主要定义了 MisskeyPlatformEvent 等顶层类。
- `misskey_utils.py`：查看 [misskey_utils.py](misskey_utils.py.md)：Misskey 平台适配器通用工具函数

## 文件类型分布

- `.py`：4 个

## 建议阅读顺序

- `misskey_adapter.py`
- `misskey_event.py`

## 维护提示

- 这份目录教程基于当前官方源码快照自动生成。
- 如果你要继续深入，建议从本目录下带有入口含义的文件开始，再跟踪它引用的子模块。