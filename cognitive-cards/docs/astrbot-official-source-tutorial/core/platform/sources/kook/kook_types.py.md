# 文件教程：core/platform/sources/kook/kook_types.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\platform\sources\kook\kook_types.py`
- 文件类型：`.py`
- 文件大小：`22893` 字节
- 所属目录教程：[core/platform/sources/kook](README.md)

## 它是做什么的

这个文件主要定义了 KookApiPaths、KookMentionTagName、KookMessageType 等顶层类。

## 角色判断

这个文件位于核心实现层，通常承载底层机制、抽象或运行时行为。

## 模块文档字符串

这个文件没有显式模块文档字符串，可以重点看顶层类、函数和导入关系。

## 顶层导入

- `json`
- `from enum import Enum, IntEnum`
- `from typing import Annotated, Any, Literal`
- `from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator`

## 顶层类

- `KookApiPaths`：Kook Api 路径
- `KookMentionTagName`：用来匹配 `(tagName)value(tagName)` 格式里的tagName , 例如: `(met)all(met)`
- `KookMessageType`：定义参见kook事件结构文档: https://developer
- `KookModuleType`：建议阅读类定义与方法名来判断职责。
- `KookRoleExtraType`：定义参见kook事件结构文档: https://developer
- `KookBaseReceiveDataClass`：接收数据基类,`to_dict`/`to_json`默认保证尽量json原样输出
- `KookBaseSendDataClass`：发送数据基类,`to_dict`/`to_json`保证默认输出内容格式包含接口格式所需最简格式内容
- `KookCardModelBase`：卡片模块基类
- `PlainTextElement`：建议阅读类定义与方法名来判断职责。
- `KmarkdownElement`：建议阅读类定义与方法名来判断职责。
- `ImageElement`：建议阅读类定义与方法名来判断职责。
- `ButtonElement`：建议阅读类定义与方法名来判断职责。
- `ParagraphStructure`：建议阅读类定义与方法名来判断职责。
- `HeaderModule`：建议阅读类定义与方法名来判断职责。
- `SectionModule`：建议阅读类定义与方法名来判断职责。
- `ImageGroupModule`：1 到多张图片的组合
- `ContainerModule`：1 到多张图片的组合，与图片组模块(ImageGroupModule)不同，图片并不会裁切为正方形
- `ActionGroupModule`：用来放按钮的模块
- `ContextModule`：建议阅读类定义与方法名来判断职责。
- `DividerModule`：展示分割线用的
- `FileModule`：建议阅读类定义与方法名来判断职责。
- `CountdownModule`：startTime 和 endTime 为毫秒时间戳，startTime 和 endTime 不能小于服务器当前时间戳
- `InviteModule`：建议阅读类定义与方法名来判断职责。
- `KookCardMessage`：卡片定义文档详见 : https://developer
- `KookCardMessageContainer`：卡片消息容器(列表),可放入多个卡片消息(KookCardMessage)
- `OrderMessage`：建议阅读类定义与方法名来判断职责。
- `KookMessageSignal`：KOOK WebSocket 信令类型
- `KookChannelType`：建议阅读类定义与方法名来判断职责。
- `KookAuthor`：建议阅读类定义与方法名来判断职责。
- `KookMarkdownMentionPart`：文档参考: https://developer
- `KookMarkdownMentionRolePart`：文档参考: https://developer
- `KookKMarkdown`：建议阅读类定义与方法名来判断职责。
- `KookRole`：服务器角色对象数据结构
- `KookRoleEventBody`：服务器角色相关事件 (added_role, updated_role, deleted_role) 的 Body 部分
- `KookExtra`：事件结构定义
- `KookMessageEventData`：建议阅读类定义与方法名来判断职责。
- `KookHelloEventData`：建议阅读类定义与方法名来判断职责。
- `KookPingEventData`：建议阅读类定义与方法名来判断职责。
- `KookPongEventData`：建议阅读类定义与方法名来判断职责。
- `KookResumeEventData`：建议阅读类定义与方法名来判断职责。
- `KookReconnectEventData`：建议阅读类定义与方法名来判断职责。
- `KookResumeAckEventData`：建议阅读类定义与方法名来判断职责。
- `KookWebsocketEvent`：KOOK WebSocket 原始推送结构
- `KookUserTag`：建议阅读类定义与方法名来判断职责。
- `KookApiResponseBase`：建议阅读类定义与方法名来判断职责。
- `KookUserMeData`：USER_ME 接口返回的 'data' 字段主体
- `KookUserMeResponse`：USER_ME 完整响应结构
- `KookUserMeViewData`：USER_ME 接口返回的 'data' 字段主体
- `KookUserViewResponse`：USER_VIEW 完整响应结构
- `KookGatewayIndexData`：建议阅读类定义与方法名来判断职责。
- `KookGatewayIndexResponse`：USER_ME 完整响应结构

## 顶层函数

- 无顶层函数定义。

## 阅读建议

- 建议从模块文档字符串、顶层类和顶层函数出发，再搜索这些名字的调用位置。

## 同目录相关文件

- [kook_adapter.py](kook_adapter.py.md)
- [kook_client.py](kook_client.py.md)
- [kook_config.py](kook_config.py.md)
- [kook_event.py](kook_event.py.md)
- [kook_roles_record.py](kook_roles_record.py.md)

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。