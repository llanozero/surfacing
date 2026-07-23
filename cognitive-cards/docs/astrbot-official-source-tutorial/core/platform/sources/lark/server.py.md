# 文件教程：core/platform/sources/lark/server.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\platform\sources\lark\server.py`
- 文件类型：`.py`
- 文件大小：`6615` 字节
- 所属目录教程：[core/platform/sources/lark](README.md)

## 它是做什么的

飞书(Lark) Webhook 服务器实现

## 角色判断

这个文件位于核心实现层，通常承载底层机制、抽象或运行时行为。

## 模块文档字符串

飞书(Lark) Webhook 服务器实现

实现飞书事件订阅的 Webhook 模式，支持:
1. 请求 URL 验证 (challenge 验证)
2. 事件加密/解密 (AES-256-CBC)
3. 签名校验 (SHA256)
4. 事件接收和处理

## 顶层导入

- `asyncio`
- `base64`
- `hashlib`
- `json`
- `from collections.abc import Awaitable, Callable`
- `from Crypto.Cipher import AES`
- `from astrbot.api import logger`

## 顶层类

- `AESCipher`：AES 加密/解密工具类
- `LarkWebhookServer`：飞书 Webhook 服务器

## 顶层函数

- 无顶层函数定义。

## 阅读建议

- 建议从模块文档字符串、顶层类和顶层函数出发，再搜索这些名字的调用位置。

## 同目录相关文件

- [lark_adapter.py](lark_adapter.py.md)
- [lark_event.py](lark_event.py.md)

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。