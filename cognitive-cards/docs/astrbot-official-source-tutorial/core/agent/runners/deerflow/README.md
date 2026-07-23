# 目录教程：core/agent/runners/deerflow

## 目录定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\agent\runners\deerflow`
- 相对根目录：`core/agent/runners/deerflow`
- 直接子目录数：`0`
- 直接文件数：`5`
- 直接 Python 文件数：`5`

## 目录作用

阅读这个目录时，建议先看它的 `README.md`（若有）、`__init__.py`、`main.py` 或带有 `manager` / `adapter` / `event` / `routes` 命名的文件。

## 直接子目录

- 无

## 直接文件

- `constants.py`：查看 [constants.py](constants.py.md)：DEERFLOW_PROVIDER_TYPE = "deerflow
- `deerflow_agent_runner.py`：查看 [deerflow_agent_runner.py](deerflow_agent_runner.py.md)：这个文件主要定义了 DeerFlowAgentRunner 等顶层类。
- `deerflow_api_client.py`：查看 [deerflow_api_client.py](deerflow_api_client.py.md)：这个文件主要定义了 DeerFlowAPIError、DeerFlowAPIClient 等顶层类。
- `deerflow_content_mapper.py`：查看 [deerflow_content_mapper.py](deerflow_content_mapper.py.md)：这个文件主要提供了 is_likely_base64_image、build_user_content、image_component_from_url、append_components_from_content 等顶层函数。
- `deerflow_stream_utils.py`：查看 [deerflow_stream_utils.py](deerflow_stream_utils.py.md)：这个文件主要提供了 extract_text、extract_messages_from_values_data、is_ai_message、extract_latest_ai_text 等顶层函数。

## 文件类型分布

- `.py`：5 个

## 建议阅读顺序

- 先看直接子文件中的 Python 源文件，再按依赖关系向下追踪。

## 维护提示

- 这份目录教程基于当前官方源码快照自动生成。
- 如果你要继续深入，建议从本目录下带有入口含义的文件开始，再跟踪它引用的子模块。