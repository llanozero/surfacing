# 目录教程：core/agent/context

## 目录定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\agent\context`
- 相对根目录：`core/agent/context`
- 直接子目录数：`0`
- 直接文件数：`5`
- 直接 Python 文件数：`5`

## 目录作用

阅读这个目录时，建议先看它的 `README.md`（若有）、`__init__.py`、`main.py` 或带有 `manager` / `adapter` / `event` / `routes` 命名的文件。

## 直接子目录

- 无

## 直接文件

- `compressor.py`：查看 [compressor.py](compressor.py.md)：这个文件主要定义了 ContextCompressor、TruncateByTurnsCompressor、LLMSummaryCompressor 等顶层类。
- `config.py`：查看 [config.py](config.py.md)：这个文件主要定义了 ContextConfig 等顶层类。
- `manager.py`：查看 [manager.py](manager.py.md)：这个文件主要定义了 ContextManager 等顶层类。
- `token_counter.py`：查看 [token_counter.py](token_counter.py.md)：这个文件主要定义了 TokenCounter、EstimateTokenCounter 等顶层类。
- `truncator.py`：查看 [truncator.py](truncator.py.md)：这个文件主要定义了 ContextTruncator 等顶层类。

## 文件类型分布

- `.py`：5 个

## 建议阅读顺序

- `manager.py`

## 维护提示

- 这份目录教程基于当前官方源码快照自动生成。
- 如果你要继续深入，建议从本目录下带有入口含义的文件开始，再跟踪它引用的子模块。