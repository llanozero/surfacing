# 文件教程：core/agent/runners/coze/coze_agent_runner.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\agent\runners\coze\coze_agent_runner.py`
- 文件类型：`.py`
- 文件大小：`14213` 字节
- 所属目录教程：[core/agent/runners/coze](README.md)

## 它是做什么的

这个文件主要定义了 CozeAgentRunner 等顶层类。

## 角色判断

这个文件位于核心实现层，通常承载底层机制、抽象或运行时行为。

## 模块文档字符串

这个文件没有显式模块文档字符串，可以重点看顶层类、函数和导入关系。

## 顶层导入

- `base64`
- `json`
- `sys`
- `typing`
- `astrbot.core.message.components`
- `from astrbot import logger`
- `from astrbot.core import sp`
- `from astrbot.core.message.message_event_result import MessageChain`
- `from astrbot.core.provider.entities import LLMResponse, ProviderRequest`
- `from hooks import BaseAgentRunHooks`
- `from response import AgentResponseData`
- `from run_context import ContextWrapper, TContext`
- `from base import AgentResponse, AgentState, BaseAgentRunner`
- `from coze_api_client import CozeAPIClient`

## 顶层类

- `CozeAgentRunner`：Coze Agent Runner

## 顶层函数

- 无顶层函数定义。

## 阅读建议

- 建议从模块文档字符串、顶层类和顶层函数出发，再搜索这些名字的调用位置。

## 同目录相关文件

- [coze_api_client.py](coze_api_client.py.md)

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。