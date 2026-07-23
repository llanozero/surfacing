# 目录教程：core/utils/quoted_message

## 目录定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\utils\quoted_message`
- 相对根目录：`core/utils/quoted_message`
- 直接子目录数：`0`
- 直接文件数：`7`
- 直接 Python 文件数：`7`

## 目录作用

阅读这个目录时，建议先看它的 `README.md`（若有）、`__init__.py`、`main.py` 或带有 `manager` / `adapter` / `event` / `routes` 命名的文件。

## 直接子目录

- 无

## 直接文件

- `__init__.py`：查看 [__init__.py](__init__.py.md)：这是一个包初始化文件，通常用于暴露子模块、注册默认导入或定义包级常量。
- `chain_parser.py`：查看 [chain_parser.py](chain_parser.py.md)：这个文件主要定义了 ParsedOneBotPayload、ReplyChainParser、OneBotPayloadParser 等顶层类。
- `extractor.py`：查看 [extractor.py](extractor.py.md)：这个文件主要定义了 QuotedMessageContent、QuotedMessageExtractor 等顶层类。
- `image_refs.py`：查看 [image_refs.py](image_refs.py.md)：这个文件主要提供了 normalize_file_like_url、looks_like_image_file_name、convert_data_image_to_base64_ref、get_existing_local_path 等顶层函数。
- `image_resolver.py`：查看 [image_resolver.py](image_resolver.py.md)：这个文件主要定义了 ImageResolver 等顶层类。
- `onebot_client.py`：查看 [onebot_client.py](onebot_client.py.md)：这个文件主要定义了 CallAction、OneBotClient 等顶层类。
- `settings.py`：查看 [settings.py](settings.py.md)：这个文件主要定义了 QuotedMessageParserSettings 等顶层类。

## 文件类型分布

- `.py`：7 个

## 建议阅读顺序

- `__init__.py`

## 维护提示

- 这份目录教程基于当前官方源码快照自动生成。
- 如果你要继续深入，建议从本目录下带有入口含义的文件开始，再跟踪它引用的子模块。