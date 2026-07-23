# 目录教程：core/computer

## 目录定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\computer`
- 相对根目录：`core/computer`
- 直接子目录数：`3`
- 直接文件数：`2`
- 直接 Python 文件数：`2`

## 目录作用

阅读这个目录时，建议先看它的 `README.md`（若有）、`__init__.py`、`main.py` 或带有 `manager` / `adapter` / `event` / `routes` 命名的文件。

## 直接子目录

- `booters`：查看 [booters](booters/README.md)
- `olayer`：查看 [olayer](olayer/README.md)
- `tools`：查看 [tools](tools/README.md)

## 直接文件

- `computer_client.py`：查看 [computer_client.py](computer_client.py.md)：这个文件主要提供了 _list_local_skill_dirs、_discover_bay_credentials、_build_python_exec_command、_build_apply_sync_command 等顶层函数。
- `file_read_utils.py`：查看 [file_read_utils.py](file_read_utils.py.md)：这个文件主要定义了 FileProbe、ParsedDocument 等顶层类。

## 文件类型分布

- `.py`：2 个

## 建议阅读顺序

- 先看直接子文件中的 Python 源文件，再按依赖关系向下追踪。

## 维护提示

- 这份目录教程基于当前官方源码快照自动生成。
- 如果你要继续深入，建议从本目录下带有入口含义的文件开始，再跟踪它引用的子模块。