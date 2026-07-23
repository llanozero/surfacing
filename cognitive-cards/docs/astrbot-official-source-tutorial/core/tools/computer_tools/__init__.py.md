# 文件教程：core/tools/computer_tools/__init__.py

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\tools\computer_tools\__init__.py`
- 文件类型：`.py`
- 文件大小：`1438` 字节
- 所属目录教程：[core/tools/computer_tools](README.md)

## 它是做什么的

from

## 角色判断

这是一个包初始化文件，通常用于暴露子模块、注册默认导入或定义包级常量。

## 模块文档字符串

这个文件没有显式模块文档字符串，可以重点看顶层类、函数和导入关系。

## 顶层导入

- `from fs import FileDownloadTool, FileEditTool, FileReadTool, FileUploadTool, FileWriteTool, GrepTool`
- `from python import LocalPythonTool, PythonTool`
- `from shell import ExecuteShellTool`
- `from shipyard_neo import AnnotateExecutionTool, BrowserBatchExecTool, BrowserExecTool, CreateSkillCandidateTool, CreateSkillPayloadTool, EvaluateSkillCandidateTool`
- `from util import check_admin_permission, normalize_umo_for_workspace`

## 顶层类

- 无顶层类定义。

## 顶层函数

- 无顶层函数定义。

## 阅读建议

- 先确认这个包是否在这里暴露公共接口，或是否只做最小初始化。
- 建议从模块文档字符串、顶层类和顶层函数出发，再搜索这些名字的调用位置。

## 同目录相关文件

- [fs.py](fs.py.md)
- [python.py](python.py.md)
- [shell.py](shell.py.md)
- [util.py](util.py.md)

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。