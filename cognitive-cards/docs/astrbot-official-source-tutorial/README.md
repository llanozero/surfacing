# AstrBot 官方源码遍历教程

这套文档按官方源码目录镜像生成，为 `C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot` 下的目录和文件分别生成单独教程。

## 先读这个

- [AstrBot 源码整体解说：模块作用与相互依赖关系](architecture-overview.md)

## 生成范围

- 源码根目录：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot`
- 输出目录：`C:\Users\llano\.astrbot\data\plugins\astrbot_plugin_proxy_agent\docs\astrbot-official-source-tutorial`
- 目录教程数量：`92`
- 文件教程数量：`414`
- 已跳过：`__pycache__`、`.pyc/.pyo` 等缓存产物

## 顶层目录入口

- [api](api/README.md)
- [builtin_stars](builtin_stars/README.md)
- [cli](cli/README.md)
- [core](core/README.md)
- [dashboard](dashboard/README.md)
- [utils](utils/README.md)

## 顶层文件入口

- [__init__.py](__init__.py.md)

## 使用建议

- 想理解大结构：先看各目录下的 `README.md`。
- 想理解单个实现：直接打开对应文件名后缀为 `.md` 的教程。
- 想追踪插件开发相关接口：优先看 `core/platform/astr_message_event.py.md`、`core/message/message_event_result.py.md`、`core/message/components.py.md`、`core/utils/session_waiter.py.md`、`core/star/context.py.md`。
