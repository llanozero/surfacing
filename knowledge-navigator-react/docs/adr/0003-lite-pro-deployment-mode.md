# Lite/Pro 双部署模式

应用需要同时支持纯本地单机运行（Lite）和连接后端的多用户协作（Pro）。Lite 模式下所有数据从本地静态 YAML 文件加载；Pro 模式下通过 REST API 从后端服务器加载和写入数据，支持写入时透传（write-through）和启动时水合（hydrateFromBackend）。两种模式通过配置切换，共享同一套 Store 层和数据模型。
