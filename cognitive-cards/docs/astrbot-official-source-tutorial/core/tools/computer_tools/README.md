# 目录教程：core/tools/computer_tools

## 目录定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\tools\computer_tools`
- 相对根目录：`core/tools/computer_tools`
- 直接子目录数：`1`
- 直接文件数：`5`
- 直接 Python 文件数：`5`

## 目录作用

阅读这个目录时，建议先看它的 `README.md`（若有）、`__init__.py`、`main.py` 或带有 `manager` / `adapter` / `event` / `routes` 命名的文件。

## 直接子目录

- `shipyard_neo`：查看 [shipyard_neo](shipyard_neo/README.md)

## 直接文件

- `__init__.py`：查看 [__init__.py](__init__.py.md)：from
- `fs.py`：查看 [fs.py](fs.py.md)：Filesystem tool audit
- `python.py`：查看 [python.py](python.py.md)：这个文件主要定义了 PythonTool、LocalPythonTool 等顶层类。
- `shell.py`：查看 [shell.py](shell.py.md)：这个文件主要定义了 ExecuteShellTool 等顶层类。
- `util.py`：查看 [util.py](util.py.md)：这个文件主要提供了 normalize_umo_for_workspace、workspace_root、is_local_runtime、check_admin_permission 等顶层函数。

## 文件类型分布

- `.py`：5 个

## 建议阅读顺序

- `__init__.py`

## 维护提示

- 这份目录教程基于当前官方源码快照自动生成。
- 如果你要继续深入，建议从本目录下带有入口含义的文件开始，再跟踪它引用的子模块。