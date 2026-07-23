# 目录教程：core/agent

## 目录定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\agent`
- 相对根目录：`core/agent`
- 直接子目录数：`2`
- 直接文件数：`10`
- 直接 Python 文件数：`10`

## 目录作用

阅读这个目录时，建议先看它的 `README.md`（若有）、`__init__.py`、`main.py` 或带有 `manager` / `adapter` / `event` / `routes` 命名的文件。

## 直接子目录

- `context`：查看 [context](context/README.md)
- `runners`：查看 [runners](runners/README.md)

## 直接文件

- `agent.py`：查看 [agent.py](agent.py.md)：这个文件主要定义了 Agent 等顶层类。
- `handoff.py`：查看 [handoff.py](handoff.py.md)：这个文件主要定义了 HandoffTool 等顶层类。
- `hooks.py`：查看 [hooks.py](hooks.py.md)：这个文件主要定义了 BaseAgentRunHooks 等顶层类。
- `mcp_client.py`：查看 [mcp_client.py](mcp_client.py.md)：这个文件主要定义了 MCPClient、MCPTool 等顶层类。
- `message.py`：查看 [message.py](message.py.md)：这个文件主要定义了 ContentPart、TextPart、ThinkPart 等顶层类。
- `response.py`：查看 [response.py](response.py.md)：这个文件主要定义了 AgentResponseData、AgentResponse、AgentStats 等顶层类。
- `run_context.py`：查看 [run_context.py](run_context.py.md)：这个文件主要定义了 ContextWrapper 等顶层类。
- `tool.py`：查看 [tool.py](tool.py.md)：这个文件主要定义了 ToolSchema、FunctionTool、ToolSet 等顶层类。
- `tool_executor.py`：查看 [tool_executor.py](tool_executor.py.md)：这个文件主要定义了 BaseFunctionToolExecutor 等顶层类。
- `tool_image_cache.py`：查看 [tool_image_cache.py](tool_image_cache.py.md)：Tool image cache module for storing and retrieving images returned by tools

## 文件类型分布

- `.py`：10 个

## 建议阅读顺序

- 先看直接子文件中的 Python 源文件，再按依赖关系向下追踪。

## 维护提示

- 这份目录教程基于当前官方源码快照自动生成。
- 如果你要继续深入，建议从本目录下带有入口含义的文件开始，再跟踪它引用的子模块。