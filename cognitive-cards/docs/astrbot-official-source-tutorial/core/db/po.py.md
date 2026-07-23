# 文件教程：core/db/po.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\db\po.py`
- 文件类型：`.py`
- 文件大小：`17991` 字节
- 所属目录教程：[core/db](README.md)

## 它是做什么的

这个文件主要定义了 TimestampMixin、PlatformStat、ProviderStat 等顶层类。

## 角色判断

这个文件位于核心实现层，通常承载底层机制、抽象或运行时行为。

## 模块文档字符串

这个文件没有显式模块文档字符串，可以重点看顶层类、函数和导入关系。

## 顶层导入

- `uuid`
- `from dataclasses import dataclass, field`
- `from datetime import datetime, timezone`
- `from typing import TypedDict`
- `from sqlmodel import JSON, Field, SQLModel, Text, UniqueConstraint`

## 顶层类

- `TimestampMixin`：建议阅读类定义与方法名来判断职责。
- `PlatformStat`：This class represents the statistics of bot usage across different platforms
- `ProviderStat`：Per-response provider stats for internal agent runs
- `ConversationV2`：建议阅读类定义与方法名来判断职责。
- `PersonaFolder`：Persona 文件夹，支持递归层级结构
- `Persona`：Persona is a set of instructions for LLMs to follow
- `CronJob`：Cron job definition for scheduler and WebUI management
- `Preference`：This class represents preferences for bots
- `PlatformMessageHistory`：This class represents the message history for a specific platform
- `PlatformSession`：Platform session table for managing user sessions across different platforms
- `Attachment`：This class represents attachments for messages in AstrBot
- `ApiKey`：API keys used by external developers to access Open APIs
- `ChatUIProject`：This class represents projects for organizing ChatUI conversations
- `SessionProjectRelation`：This class represents the relationship between platform sessions and ChatUI projects
- `CommandConfig`：Per-command configuration overrides for dashboard management
- `CommandConflict`：Conflict tracking for duplicated command names
- `Conversation`：LLM 对话类
- `Personality`：LLM 人格类
- `Platform`：平台使用统计数据
- `Stats`：建议阅读类定义与方法名来判断职责。

## 顶层函数

- 无顶层函数定义。

## 阅读建议

- 建议从模块文档字符串、顶层类和顶层函数出发，再搜索这些名字的调用位置。

## 同目录相关文件

- [__init__.py](__init__.py.md)
- [sqlite.py](sqlite.py.md)

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。