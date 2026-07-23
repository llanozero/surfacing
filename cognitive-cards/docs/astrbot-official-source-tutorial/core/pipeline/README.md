# 目录教程：core/pipeline

## 目录定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\pipeline`
- 相对根目录：`core/pipeline`
- 直接子目录数：`9`
- 直接文件数：`7`
- 直接 Python 文件数：`7`

## 目录作用

阅读这个目录时，建议先看它的 `README.md`（若有）、`__init__.py`、`main.py` 或带有 `manager` / `adapter` / `event` / `routes` 命名的文件。

## 直接子目录

- `content_safety_check`：查看 [content_safety_check](content_safety_check/README.md)
- `preprocess_stage`：查看 [preprocess_stage](preprocess_stage/README.md)
- `process_stage`：查看 [process_stage](process_stage/README.md)
- `rate_limit_check`：查看 [rate_limit_check](rate_limit_check/README.md)
- `respond`：查看 [respond](respond/README.md)
- `result_decorate`：查看 [result_decorate](result_decorate/README.md)
- `session_status_check`：查看 [session_status_check](session_status_check/README.md)
- `waking_check`：查看 [waking_check](waking_check/README.md)
- `whitelist_check`：查看 [whitelist_check](whitelist_check/README.md)

## 直接文件

- `__init__.py`：查看 [__init__.py](__init__.py.md)：Pipeline package exports
- `bootstrap.py`：查看 [bootstrap.py](bootstrap.py.md)：Pipeline bootstrap utilities
- `context.py`：查看 [context.py](context.py.md)：这个文件主要定义了 PipelineContext 等顶层类。
- `context_utils.py`：查看 [context_utils.py](context_utils.py.md)：这个文件主要提供了 call_handler、call_event_hook 等顶层函数。
- `scheduler.py`：查看 [scheduler.py](scheduler.py.md)：这个文件主要定义了 PipelineScheduler 等顶层类。
- `stage.py`：查看 [stage.py](stage.py.md)：这个文件主要定义了 Stage 等顶层类。
- `stage_order.py`：查看 [stage_order.py](stage_order.py.md)：Pipeline stage execution order

## 文件类型分布

- `.py`：7 个

## 建议阅读顺序

- `__init__.py`

## 维护提示

- 这份目录教程基于当前官方源码快照自动生成。
- 如果你要继续深入，建议从本目录下带有入口含义的文件开始，再跟踪它引用的子模块。