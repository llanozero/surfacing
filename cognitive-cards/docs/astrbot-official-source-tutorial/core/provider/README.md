# 目录教程：core/provider

## 目录定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\provider`
- 相对根目录：`core/provider`
- 直接子目录数：`1`
- 直接文件数：`7`
- 直接 Python 文件数：`7`

## 目录作用

阅读这个目录时，建议先看它的 `README.md`（若有）、`__init__.py`、`main.py` 或带有 `manager` / `adapter` / `event` / `routes` 命名的文件。

## 直接子目录

- `sources`：查看 [sources](sources/README.md)

## 直接文件

- `__init__.py`：查看 [__init__.py](__init__.py.md)：from
- `entites.py`：查看 [entites.py](entites.py.md)：这个文件位于核心实现层，通常承载底层机制、抽象或运行时行为。
- `entities.py`：查看 [entities.py](entities.py.md)：这个文件主要定义了 ProviderType、ProviderMeta、ProviderMetaData 等顶层类。
- `func_tool_manager.py`：查看 [func_tool_manager.py](func_tool_manager.py.md)：这个文件主要定义了 MCPInitError、MCPInitTimeoutError、MCPAllServicesFailedError 等顶层类。
- `manager.py`：查看 [manager.py](manager.py.md)：这个文件主要定义了 HasInitialize、ProviderManager 等顶层类。
- `provider.py`：查看 [provider.py](provider.py.md)：这个文件主要定义了 AbstractProvider、Provider、STTProvider 等顶层类。
- `register.py`：查看 [register.py](register.py.md)：这个文件主要提供了 register_provider_adapter 等顶层函数。

## 文件类型分布

- `.py`：7 个

## 建议阅读顺序

- `__init__.py`
- `func_tool_manager.py`
- `manager.py`

## 维护提示

- 这份目录教程基于当前官方源码快照自动生成。
- 如果你要继续深入，建议从本目录下带有入口含义的文件开始，再跟踪它引用的子模块。