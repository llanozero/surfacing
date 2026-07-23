# 目录教程：core/db/migration

## 目录定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\db\migration`
- 相对根目录：`core/db/migration`
- 直接子目录数：`0`
- 直接文件数：`7`
- 直接 Python 文件数：`7`

## 目录作用

阅读这个目录时，建议先看它的 `README.md`（若有）、`__init__.py`、`main.py` 或带有 `manager` / `adapter` / `event` / `routes` 命名的文件。

## 直接子目录

- 无

## 直接文件

- `helper.py`：查看 [helper.py](helper.py.md)：这个文件主要提供了 check_migration_needed_v4、do_migration_v4 等顶层函数。
- `migra_3_to_4.py`：查看 [migra_3_to_4.py](migra_3_to_4.py.md)：这个文件主要提供了 get_platform_id、get_platform_type、migration_conversation_table、migration_platform_table 等顶层函数。
- `migra_45_to_46.py`：查看 [migra_45_to_46.py](migra_45_to_46.py.md)：这个文件主要提供了 migrate_45_to_46 等顶层函数。
- `migra_token_usage.py`：查看 [migra_token_usage.py](migra_token_usage.py.md)：Migration script to add token_usage column to conversations table
- `migra_webchat_session.py`：查看 [migra_webchat_session.py](migra_webchat_session.py.md)：Migration script for WebChat sessions
- `shared_preferences_v3.py`：查看 [shared_preferences_v3.py](shared_preferences_v3.py.md)：这个文件主要定义了 SharedPreferences 等顶层类。
- `sqlite_v3.py`：查看 [sqlite_v3.py](sqlite_v3.py.md)：这个文件主要定义了 Conversation、SQLiteDatabase 等顶层类。

## 文件类型分布

- `.py`：7 个

## 建议阅读顺序

- 先看直接子文件中的 Python 源文件，再按依赖关系向下追踪。

## 维护提示

- 这份目录教程基于当前官方源码快照自动生成。
- 如果你要继续深入，建议从本目录下带有入口含义的文件开始，再跟踪它引用的子模块。