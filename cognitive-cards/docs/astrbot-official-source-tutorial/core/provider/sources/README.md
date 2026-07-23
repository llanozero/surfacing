# 目录教程：core/provider/sources

## 目录定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\provider\sources`
- 相对根目录：`core/provider/sources`
- 直接子目录数：`0`
- 直接文件数：`35`
- 直接 Python 文件数：`35`

## 目录作用

阅读这个目录时，建议先看它的 `README.md`（若有）、`__init__.py`、`main.py` 或带有 `manager` / `adapter` / `event` / `routes` 命名的文件。

## 直接子目录

- 无

## 直接文件

- `anthropic_source.py`：查看 [anthropic_source.py](anthropic_source.py.md)：这个文件主要定义了 ProviderAnthropic 等顶层类。
- `azure_tts_source.py`：查看 [azure_tts_source.py](azure_tts_source.py.md)：这个文件主要定义了 OTTSProvider、AzureNativeProvider、AzureTTSProvider 等顶层类。
- `bailian_rerank_source.py`：查看 [bailian_rerank_source.py](bailian_rerank_source.py.md)：这个文件主要定义了 BailianRerankError、BailianAPIError、BailianNetworkError 等顶层类。
- `dashscope_tts.py`：查看 [dashscope_tts.py](dashscope_tts.py.md)：这个文件主要定义了 ProviderDashscopeTTSAPI 等顶层类。
- `edge_tts_source.py`：查看 [edge_tts_source.py](edge_tts_source.py.md)：这个文件主要定义了 ProviderEdgeTTS 等顶层类。
- `fishaudio_tts_api_source.py`：查看 [fishaudio_tts_api_source.py](fishaudio_tts_api_source.py.md)：这个文件主要定义了 ServeReferenceAudio、ServeTTSRequest、ProviderFishAudioTTSAPI 等顶层类。
- `gemini_embedding_source.py`：查看 [gemini_embedding_source.py](gemini_embedding_source.py.md)：这个文件主要定义了 GeminiEmbeddingProvider 等顶层类。
- `gemini_source.py`：查看 [gemini_source.py](gemini_source.py.md)：这个文件主要定义了 SuppressNonTextPartsWarning、ProviderGoogleGenAI 等顶层类。
- `gemini_tts_source.py`：查看 [gemini_tts_source.py](gemini_tts_source.py.md)：这个文件主要定义了 ProviderGeminiTTSAPI 等顶层类。
- `genie_tts.py`：查看 [genie_tts.py](genie_tts.py.md)：这个文件主要定义了 GenieTTSProvider 等顶层类。
- `groq_source.py`：查看 [groq_source.py](groq_source.py.md)：这个文件主要定义了 ProviderGroq 等顶层类。
- `gsv_selfhosted_source.py`：查看 [gsv_selfhosted_source.py](gsv_selfhosted_source.py.md)：这个文件主要定义了 ProviderGSVTTS 等顶层类。
- `gsvi_tts_source.py`：查看 [gsvi_tts_source.py](gsvi_tts_source.py.md)：这个文件主要定义了 ProviderGSVITTS 等顶层类。
- `kimi_code_source.py`：查看 [kimi_code_source.py](kimi_code_source.py.md)：这个文件主要定义了 ProviderKimiCode 等顶层类。
- `longcat_source.py`：查看 [longcat_source.py](longcat_source.py.md)：这个文件主要定义了 ProviderLongCat 等顶层类。
- `mimo_api_common.py`：查看 [mimo_api_common.py](mimo_api_common.py.md)：这个文件主要定义了 MiMoAPIError 等顶层类。
- `mimo_stt_api_source.py`：查看 [mimo_stt_api_source.py](mimo_stt_api_source.py.md)：这个文件主要定义了 ProviderMiMoSTTAPI 等顶层类。
- `mimo_tts_api_source.py`：查看 [mimo_tts_api_source.py](mimo_tts_api_source.py.md)：这个文件主要定义了 ProviderMiMoTTSAPI 等顶层类。
- `minimax_token_plan_source.py`：查看 [minimax_token_plan_source.py](minimax_token_plan_source.py.md)：这个文件主要定义了 ProviderMiniMaxTokenPlan 等顶层类。
- `minimax_tts_api_source.py`：查看 [minimax_tts_api_source.py](minimax_tts_api_source.py.md)：这个文件主要定义了 ProviderMiniMaxTTSAPI 等顶层类。
- `nvidia_rerank_source.py`：查看 [nvidia_rerank_source.py](nvidia_rerank_source.py.md)：这个文件主要定义了 NvidiaRerankProvider 等顶层类。
- `oai_aihubmix_source.py`：查看 [oai_aihubmix_source.py](oai_aihubmix_source.py.md)：这个文件主要定义了 ProviderAIHubMix 等顶层类。
- `openai_embedding_source.py`：查看 [openai_embedding_source.py](openai_embedding_source.py.md)：这个文件主要定义了 OpenAIEmbeddingProvider 等顶层类。
- `openai_source.py`：查看 [openai_source.py](openai_source.py.md)：这个文件主要定义了 ProviderOpenAIOfficial 等顶层类。
- `openai_tts_api_source.py`：查看 [openai_tts_api_source.py](openai_tts_api_source.py.md)：这个文件主要定义了 ProviderOpenAITTSAPI 等顶层类。
- `openrouter_source.py`：查看 [openrouter_source.py](openrouter_source.py.md)：这个文件主要定义了 ProviderOpenRouter 等顶层类。
- `sensevoice_selfhosted_source.py`：查看 [sensevoice_selfhosted_source.py](sensevoice_selfhosted_source.py.md)：Author: diudiu62
- `vllm_rerank_source.py`：查看 [vllm_rerank_source.py](vllm_rerank_source.py.md)：这个文件主要定义了 VLLMRerankProvider 等顶层类。
- `volcengine_tts.py`：查看 [volcengine_tts.py](volcengine_tts.py.md)：这个文件主要定义了 ProviderVolcengineTTS 等顶层类。
- `whisper_api_source.py`：查看 [whisper_api_source.py](whisper_api_source.py.md)：这个文件主要定义了 ProviderOpenAIWhisperAPI 等顶层类。
- `whisper_selfhosted_source.py`：查看 [whisper_selfhosted_source.py](whisper_selfhosted_source.py.md)：这个文件主要定义了 ProviderOpenAIWhisperSelfHost 等顶层类。
- `xai_source.py`：查看 [xai_source.py](xai_source.py.md)：这个文件主要定义了 ProviderXAI 等顶层类。
- `xinference_rerank_source.py`：查看 [xinference_rerank_source.py](xinference_rerank_source.py.md)：这个文件主要定义了 XinferenceRerankProvider 等顶层类。
- `xinference_stt_provider.py`：查看 [xinference_stt_provider.py](xinference_stt_provider.py.md)：这个文件主要定义了 ProviderXinferenceSTT 等顶层类。
- `zhipu_source.py`：查看 [zhipu_source.py](zhipu_source.py.md)：这个文件主要定义了 ProviderZhipu 等顶层类。

## 文件类型分布

- `.py`：35 个

## 建议阅读顺序

- `openrouter_source.py`

## 维护提示

- 这份目录教程基于当前官方源码快照自动生成。
- 如果你要继续深入，建议从本目录下带有入口含义的文件开始，再跟踪它引用的子模块。