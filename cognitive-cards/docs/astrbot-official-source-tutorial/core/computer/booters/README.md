# 目录教程：core/computer/booters

## 目录定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\computer\booters`
- 相对根目录：`core/computer/booters`
- 直接子目录数：`0`
- 直接文件数：`7`
- 直接 Python 文件数：`7`

## 目录作用

阅读这个目录时，建议先看它的 `README.md`（若有）、`__init__.py`、`main.py` 或带有 `manager` / `adapter` / `event` / `routes` 命名的文件。

## 直接子目录

- 无

## 直接文件

- `base.py`：查看 [base.py](base.py.md)：这个文件主要定义了 ComputerBooter 等顶层类。
- `bay_manager.py`：查看 [bay_manager.py](bay_manager.py.md)：Manage Bay container lifecycle for zero-config Shipyard Neo integration
- `boxlite.py`：查看 [boxlite.py](boxlite.py.md)：这个文件主要定义了 MockShipyardSandboxClient、BoxliteBooter 等顶层类。
- `local.py`：查看 [local.py](local.py.md)：这个文件主要定义了 LocalShellComponent、LocalPythonComponent、LocalFileSystemComponent 等顶层类。
- `shipyard.py`：查看 [shipyard.py](shipyard.py.md)：这个文件主要定义了 ShipyardFileSystemWrapper、ShipyardBooter 等顶层类。
- `shipyard_neo.py`：查看 [shipyard_neo.py](shipyard_neo.py.md)：这个文件主要定义了 NeoPythonComponent、NeoShellComponent、NeoFileSystemComponent 等顶层类。
- `shipyard_search_file_util.py`：查看 [shipyard_search_file_util.py](shipyard_search_file_util.py.md)：这个文件主要提供了 _truncate_long_lines、_build_rg_command、_build_grep_command、_quote_command 等顶层函数。

## 文件类型分布

- `.py`：7 个

## 建议阅读顺序

- `bay_manager.py`

## 维护提示

- 这份目录教程基于当前官方源码快照自动生成。
- 如果你要继续深入，建议从本目录下带有入口含义的文件开始，再跟踪它引用的子模块。