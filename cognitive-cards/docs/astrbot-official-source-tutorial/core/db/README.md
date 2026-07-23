# 目录教程：core/db

## 目录定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\db`
- 相对根目录：`core/db`
- 直接子目录数：`2`
- 直接文件数：`3`
- 直接 Python 文件数：`3`

## 目录作用

阅读这个目录时，建议先看它的 `README.md`（若有）、`__init__.py`、`main.py` 或带有 `manager` / `adapter` / `event` / `routes` 命名的文件。

## 直接子目录

- `migration`：查看 [migration](migration/README.md)
- `vec_db`：查看 [vec_db](vec_db/README.md)

## 直接文件

- `__init__.py`：查看 [__init__.py](__init__.py.md)：这个文件主要定义了 BaseDatabase 等顶层类。
- `po.py`：查看 [po.py](po.py.md)：这个文件主要定义了 TimestampMixin、PlatformStat、ProviderStat 等顶层类。
- `sqlite.py`：查看 [sqlite.py](sqlite.py.md)：这个文件主要定义了 SQLiteDatabase 等顶层类。

## 文件类型分布

- `.py`：3 个

## 建议阅读顺序

- `__init__.py`

## 维护提示

- 这份目录教程基于当前官方源码快照自动生成。
- 如果你要继续深入，建议从本目录下带有入口含义的文件开始，再跟踪它引用的子模块。