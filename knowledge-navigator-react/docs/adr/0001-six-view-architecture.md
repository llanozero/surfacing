# 从 4 视图扩展到 6 视图架构

原始 spec 定义了 4 个视图（search/nav/browse/tree），但在开发过程中发现路线规划（plan）和分支探索（free-browse）是独立的交互模式，无法被合并到已有的 4 个视图中。因此决定将视图扩展为 6 个：search → nav → plan → browse → tree → free-browse，每个视图有对应的独立 Zustand store 和责任边界。
