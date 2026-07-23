# 目录教程：cli/commands

## 目录定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\cli\commands`
- 相对根目录：`cli/commands`
- 直接子目录数：`0`
- 直接文件数：`5`
- 直接 Python 文件数：`5`

## 目录作用

阅读这个目录时，建议先看它的 `README.md`（若有）、`__init__.py`、`main.py` 或带有 `manager` / `adapter` / `event` / `routes` 命名的文件。

## 直接子目录

- 无

## 直接文件

- `__init__.py`：查看 [__init__.py](__init__.py.md)：from
- `cmd_conf.py`：查看 [cmd_conf.py](cmd_conf.py.md)：这个文件主要提供了 _validate_log_level、_validate_dashboard_port、_validate_dashboard_username、_validate_dashboard_password 等顶层函数。
- `cmd_init.py`：查看 [cmd_init.py](cmd_init.py.md)：这个文件主要提供了 initialize_astrbot、init 等顶层函数。
- `cmd_plug.py`：查看 [cmd_plug.py](cmd_plug.py.md)：这个文件主要提供了 plug、_get_data_path、display_plugins、new 等顶层函数。
- `cmd_run.py`：查看 [cmd_run.py](cmd_run.py.md)：这个文件主要提供了 run_astrbot、run 等顶层函数。

## 文件类型分布

- `.py`：5 个

## 建议阅读顺序

- `__init__.py`

## 维护提示

- 这份目录教程基于当前官方源码快照自动生成。
- 如果你要继续深入，建议从本目录下带有入口含义的文件开始，再跟踪它引用的子模块。