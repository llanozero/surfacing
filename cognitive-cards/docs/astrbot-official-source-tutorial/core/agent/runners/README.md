# 目录教程：core/agent/runners

## 目录定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\agent\runners`
- 相对根目录：`core/agent/runners`
- 直接子目录数：`4`
- 直接文件数：`3`
- 直接 Python 文件数：`3`

## 目录作用

阅读这个目录时，建议先看它的 `README.md`（若有）、`__init__.py`、`main.py` 或带有 `manager` / `adapter` / `event` / `routes` 命名的文件。

## 直接子目录

- `coze`：查看 [coze](coze/README.md)
- `dashscope`：查看 [dashscope](dashscope/README.md)
- `deerflow`：查看 [deerflow](deerflow/README.md)
- `dify`：查看 [dify](dify/README.md)

## 直接文件

- `__init__.py`：查看 [__init__.py](__init__.py.md)：from
- `base.py`：查看 [base.py](base.py.md)：这个文件主要定义了 AgentState、BaseAgentRunner 等顶层类。
- `tool_loop_agent_runner.py`：查看 [tool_loop_agent_runner.py](tool_loop_agent_runner.py.md)：这个文件主要定义了 _HandleFunctionToolsResult、FollowUpTicket、_ToolExecutionInterrupted 等顶层类。

## 文件类型分布

- `.py`：3 个

## 建议阅读顺序

- `__init__.py`

## 维护提示

- 这份目录教程基于当前官方源码快照自动生成。
- 如果你要继续深入，建议从本目录下带有入口含义的文件开始，再跟踪它引用的子模块。