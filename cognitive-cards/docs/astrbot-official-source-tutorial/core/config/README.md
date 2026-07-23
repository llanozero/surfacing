# 目录教程：core/config

## 目录定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\config`
- 相对根目录：`core/config`
- 直接子目录数：`0`
- 直接文件数：`4`
- 直接 Python 文件数：`4`

## 目录作用

阅读这个目录时，建议先看它的 `README.md`（若有）、`__init__.py`、`main.py` 或带有 `manager` / `adapter` / `event` / `routes` 命名的文件。

## 直接子目录

- 无

## 直接文件

- `__init__.py`：查看 [__init__.py](__init__.py.md)：from
- `astrbot_config.py`：查看 [astrbot_config.py](astrbot_config.py.md)：这个文件主要定义了 RateLimitStrategy、AstrBotConfig 等顶层类。
- `default.py`：查看 [default.py](default.py.md)：如需修改配置，请在 `data/cmd_config.json` 中修改或者在管理面板中可视化修改
- `i18n_utils.py`：查看 [i18n_utils.py](i18n_utils.py.md)：配置元数据国际化工具

## 文件类型分布

- `.py`：4 个

## 建议阅读顺序

- `__init__.py`

## 维护提示

- 这份目录教程基于当前官方源码快照自动生成。
- 如果你要继续深入，建议从本目录下带有入口含义的文件开始，再跟踪它引用的子模块。