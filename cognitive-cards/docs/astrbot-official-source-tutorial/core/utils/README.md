# 目录教程：core/utils

## 目录定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\utils`
- 相对根目录：`core/utils`
- 直接子目录数：`2`
- 直接文件数：`34`
- 直接 Python 文件数：`34`

## 目录作用

阅读这个目录时，建议先看它的 `README.md`（若有）、`__init__.py`、`main.py` 或带有 `manager` / `adapter` / `event` / `routes` 命名的文件。

## 直接子目录

- `quoted_message`：查看 [quoted_message](quoted_message/README.md)
- `t2i`：查看 [t2i](t2i/README.md)

## 直接文件

- `active_event_registry.py`：查看 [active_event_registry.py](active_event_registry.py.md)：这个文件主要定义了 ActiveEventRegistry 等顶层类。
- `astrbot_path.py`：查看 [astrbot_path.py](astrbot_path.py.md)：Centralized AstrBot path helpers
- `command_parser.py`：查看 [command_parser.py](command_parser.py.md)：这个文件主要定义了 CommandTokens、CommandParserMixin 等顶层类。
- `config_number.py`：查看 [config_number.py](config_number.py.md)：这个文件主要提供了 coerce_int_config 等顶层函数。
- `core_constraints.py`：查看 [core_constraints.py](core_constraints.py.md)：这个文件主要定义了 CoreConstraintsProvider 等顶层类。
- `datetime_utils.py`：查看 [datetime_utils.py](datetime_utils.py.md)：这个文件主要提供了 normalize_datetime_utc、to_utc_isoformat、to_utc_timestamp 等顶层函数。
- `error_redaction.py`：查看 [error_redaction.py](error_redaction.py.md)：这个文件主要提供了 _redact_json_field、_redact_auth_json_field、_redact_prefixed_value、_redact_bearer_token 等顶层函数。
- `file_extract.py`：查看 [file_extract.py](file_extract.py.md)：这个文件主要提供了 extract_file_moonshotai 等顶层函数。
- `history_saver.py`：查看 [history_saver.py](history_saver.py.md)：这个文件主要提供了 persist_agent_history 等顶层函数。
- `http_ssl.py`：查看 [http_ssl.py](http_ssl.py.md)：这个文件主要提供了 build_ssl_context_with_certifi、build_tls_connector 等顶层函数。
- `image_ref_utils.py`：查看 [image_ref_utils.py](image_ref_utils.py.md)：这个文件主要提供了 resolve_file_url_path、_is_path_within_roots、is_supported_image_ref 等顶层函数。
- `io.py`：查看 [io.py](io.py.md)：这个文件主要提供了 on_error、remove_dir、port_checker、save_temp_img 等顶层函数。
- `llm_metadata.py`：查看 [llm_metadata.py](llm_metadata.py.md)：这个文件主要定义了 LLMModalities、LLMLimit、LLMMetadata 等顶层类。
- `log_pipe.py`：查看 [log_pipe.py](log_pipe.py.md)：这个文件主要定义了 LogPipe 等顶层类。
- `media_utils.py`：查看 [media_utils.py](media_utils.py.md)：媒体文件处理工具
- `metrics.py`：查看 [metrics.py](metrics.py.md)：这个文件主要定义了 Metric 等顶层类。
- `migra_helper.py`：查看 [migra_helper.py](migra_helper.py.md)：这个文件主要提供了 _migra_agent_runner_configs、_migra_provider_to_source_structure、migra 等顶层函数。
- `network_utils.py`：查看 [network_utils.py](network_utils.py.md)：Network error handling utilities for providers
- `path_util.py`：查看 [path_util.py](path_util.py.md)：这个文件主要提供了 path_Mapping 等顶层函数。
- `pip_installer.py`：查看 [pip_installer.py](pip_installer.py.md)：这个文件主要定义了 DependencyConflictError、PipInstallError、PipConflictContext 等顶层类。
- `plugin_kv_store.py`：查看 [plugin_kv_store.py](plugin_kv_store.py.md)：这个文件主要定义了 PluginKVStoreMixin 等顶层类。
- `quoted_message_parser.py`：查看 [quoted_message_parser.py](quoted_message_parser.py.md)：这个文件位于核心实现层，通常承载底层机制、抽象或运行时行为。
- `requirements_utils.py`：查看 [requirements_utils.py](requirements_utils.py.md)：这个文件主要定义了 RequirementsPrecheckFailed、ParsedPackageInput、MissingRequirementsAnalysis 等顶层类。
- `runtime_env.py`：查看 [runtime_env.py](runtime_env.py.md)：这个文件主要提供了 is_frozen_runtime、is_packaged_desktop_runtime 等顶层函数。
- `session_lock.py`：查看 [session_lock.py](session_lock.py.md)：这个文件主要定义了 _PerLoopSessionLockManager、SessionLockManager 等顶层类。
- `session_waiter.py`：查看 [session_waiter.py](session_waiter.py.md)：会话控制
- `shared_preferences.py`：查看 [shared_preferences.py](shared_preferences.py.md)：这个文件主要定义了 SharedPreferences 等顶层类。
- `storage_cleaner.py`：查看 [storage_cleaner.py](storage_cleaner.py.md)：这个文件主要定义了 LogFileConfig、StorageCleaner 等顶层类。
- `string_utils.py`：查看 [string_utils.py](string_utils.py.md)：这个文件主要提供了 normalize_and_dedupe_strings 等顶层函数。
- `temp_dir_cleaner.py`：查看 [temp_dir_cleaner.py](temp_dir_cleaner.py.md)：这个文件主要定义了 TempFileInfo、TempDirCleaner 等顶层类。
- `tencent_record_helper.py`：查看 [tencent_record_helper.py](tencent_record_helper.py.md)：这个文件主要提供了 tencent_silk_to_wav、wav_to_tencent_silk、convert_to_pcm_wav、audio_to_tencent_silk_base64 等顶层函数。
- `trace.py`：查看 [trace.py](trace.py.md)：这个文件主要定义了 TraceSpan 等顶层类。
- `version_comparator.py`：查看 [version_comparator.py](version_comparator.py.md)：这个文件主要定义了 VersionComparator 等顶层类。
- `webhook_utils.py`：查看 [webhook_utils.py](webhook_utils.py.md)：这个文件主要提供了 _get_callback_api_base、_get_dashboard_port、_is_dashboard_ssl_enabled、log_webhook_info 等顶层函数。

## 文件类型分布

- `.py`：34 个

## 建议阅读顺序

- `active_event_registry.py`

## 维护提示

- 这份目录教程基于当前官方源码快照自动生成。
- 如果你要继续深入，建议从本目录下带有入口含义的文件开始，再跟踪它引用的子模块。