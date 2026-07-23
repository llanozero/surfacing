# 目录教程：core

## 目录定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core`
- 相对根目录：`core`
- 直接子目录数：`15`
- 直接文件数：`23`
- 直接 Python 文件数：`23`

## 目录作用

阅读这个目录时，建议先看它的 `README.md`（若有）、`__init__.py`、`main.py` 或带有 `manager` / `adapter` / `event` / `routes` 命名的文件。

## 直接子目录

- `agent`：查看 [agent](agent/README.md)
- `backup`：查看 [backup](backup/README.md)
- `computer`：查看 [computer](computer/README.md)
- `config`：查看 [config](config/README.md)
- `cron`：查看 [cron](cron/README.md)
- `db`：查看 [db](db/README.md)
- `knowledge_base`：查看 [knowledge_base](knowledge_base/README.md)
- `message`：查看 [message](message/README.md)
- `pipeline`：查看 [pipeline](pipeline/README.md)
- `platform`：查看 [platform](platform/README.md)
- `provider`：查看 [provider](provider/README.md)
- `skills`：查看 [skills](skills/README.md)
- `star`：查看 [star](star/README.md)
- `tools`：查看 [tools](tools/README.md)
- `utils`：查看 [utils](utils/README.md)

## 直接文件

- `__init__.py`：查看 [__init__.py](__init__.py.md)：这是一个包初始化文件，通常用于暴露子模块、注册默认导入或定义包级常量。
- `astr_agent_context.py`：查看 [astr_agent_context.py](astr_agent_context.py.md)：这个文件主要定义了 AstrAgentContext 等顶层类。
- `astr_agent_hooks.py`：查看 [astr_agent_hooks.py](astr_agent_hooks.py.md)：这个文件主要定义了 MainAgentHooks、EmptyAgentHooks 等顶层类。
- `astr_agent_run_util.py`：查看 [astr_agent_run_util.py](astr_agent_run_util.py.md)：这个文件主要提供了 _should_stop_agent、_truncate_tool_result、_extract_chain_json_data、_record_tool_call_name 等顶层函数。
- `astr_agent_tool_exec.py`：查看 [astr_agent_tool_exec.py](astr_agent_tool_exec.py.md)：这个文件主要定义了 FunctionToolExecutor 等顶层类。
- `astr_main_agent.py`：查看 [astr_main_agent.py](astr_main_agent.py.md)：这个文件主要定义了 MainAgentBuildConfig、MainAgentBuildResult 等顶层类。
- `astr_main_agent_resources.py`：查看 [astr_main_agent_resources.py](astr_main_agent_resources.py.md)：这个文件位于核心实现层，通常承载底层机制、抽象或运行时行为。
- `astrbot_config_mgr.py`：查看 [astrbot_config_mgr.py](astrbot_config_mgr.py.md)：这个文件主要定义了 ConfInfo、AstrBotConfigManager 等顶层类。
- `conversation_mgr.py`：查看 [conversation_mgr.py](conversation_mgr.py.md)：AstrBot 会话-对话管理器, 维护两个本地存储, 其中一个是 json 格式的shared_preferences, 另外一个是数据库
- `core_lifecycle.py`：查看 [core_lifecycle.py](core_lifecycle.py.md)：Astrbot 核心生命周期管理类, 负责管理 AstrBot 的启动、停止、重启等操作
- `event_bus.py`：查看 [event_bus.py](event_bus.py.md)：事件总线, 用于处理事件的分发和处理
- `exceptions.py`：查看 [exceptions.py](exceptions.py.md)：这个文件主要定义了 AstrBotError、ProviderNotFoundError、EmptyModelOutputError 等顶层类。
- `file_token_service.py`：查看 [file_token_service.py](file_token_service.py.md)：这个文件主要定义了 FileTokenService 等顶层类。
- `initial_loader.py`：查看 [initial_loader.py](initial_loader.py.md)：AstrBot 启动器，负责初始化和启动核心组件和仪表板服务器
- `log.py`：查看 [log.py](log.py.md)：日志系统，统一将标准 logging 输出转发到 loguru
- `persona_error_reply.py`：查看 [persona_error_reply.py](persona_error_reply.py.md)：这个文件主要提供了 normalize_persona_custom_error_message、extract_persona_custom_error_message_from_persona、extract_persona_custom_error_message_from_event、set_persona_custom_error_message_on_event 等顶层函数。
- `persona_mgr.py`：查看 [persona_mgr.py](persona_mgr.py.md)：这个文件主要定义了 PersonaManager 等顶层类。
- `platform_message_history_mgr.py`：查看 [platform_message_history_mgr.py](platform_message_history_mgr.py.md)：这个文件主要定义了 PlatformMessageHistoryManager 等顶层类。
- `sentinels.py`：查看 [sentinels.py](sentinels.py.md)：NOT_GIVEN = object()
- `subagent_orchestrator.py`：查看 [subagent_orchestrator.py](subagent_orchestrator.py.md)：这个文件主要定义了 SubAgentOrchestrator 等顶层类。
- `umop_config_router.py`：查看 [umop_config_router.py](umop_config_router.py.md)：这个文件主要定义了 UmopConfigRouter 等顶层类。
- `updator.py`：查看 [updator.py](updator.py.md)：这个文件主要定义了 AstrBotUpdator 等顶层类。
- `zip_updator.py`：查看 [zip_updator.py](zip_updator.py.md)：这个文件主要定义了 ReleaseInfo、RepoZipUpdator 等顶层类。

## 文件类型分布

- `.py`：23 个

## 建议阅读顺序

- `__init__.py`
- `event_bus.py`
- `umop_config_router.py`

## 维护提示

- 这份目录教程基于当前官方源码快照自动生成。
- 如果你要继续深入，建议从本目录下带有入口含义的文件开始，再跟踪它引用的子模块。