# 目录教程：core/utils/t2i

## 目录定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\utils\t2i`
- 相对根目录：`core/utils/t2i`
- 直接子目录数：`1`
- 直接文件数：`5`
- 直接 Python 文件数：`5`

## 目录作用

阅读这个目录时，建议先看它的 `README.md`（若有）、`__init__.py`、`main.py` 或带有 `manager` / `adapter` / `event` / `routes` 命名的文件。

## 直接子目录

- `template`：查看 [template](template/README.md)

## 直接文件

- `__init__.py`：查看 [__init__.py](__init__.py.md)：这个文件主要定义了 RenderStrategy 等顶层类。
- `local_strategy.py`：查看 [local_strategy.py](local_strategy.py.md)：这个文件主要定义了 FontManager、TextMeasurer、MarkdownElement 等顶层类。
- `network_strategy.py`：查看 [network_strategy.py](network_strategy.py.md)：这个文件主要定义了 NetworkRenderStrategy 等顶层类。
- `renderer.py`：查看 [renderer.py](renderer.py.md)：这个文件主要定义了 HtmlRenderer 等顶层类。
- `template_manager.py`：查看 [template_manager.py](template_manager.py.md)：这个文件主要定义了 TemplateManager 等顶层类。

## 文件类型分布

- `.py`：5 个

## 建议阅读顺序

- `__init__.py`
- `template_manager.py`

## 维护提示

- 这份目录教程基于当前官方源码快照自动生成。
- 如果你要继续深入，建议从本目录下带有入口含义的文件开始，再跟踪它引用的子模块。