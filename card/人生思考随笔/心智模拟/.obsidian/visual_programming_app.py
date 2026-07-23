from __future__ import annotations

"""独立的可视化编程测试 UI。

本模块不接入 ASTViewer 主应用壳，而是作为一个单独运行的 Tk 应用，
用最小实现串联：

- scope_index.ScopeIndex：词法作用域与变量绑定
- workflow_adapter.ast_to_workflow：调用/控制流薄视图

并基于一段内联示例代码（与 tests/test_scope_index.py 中 EXAMPLE_CODE 一致）
构建四个 Tab：

1. 导入区：展示示例代码中的 import 语句（当前示例没有 import，会提示为空）。
2. 定义区：展示示例代码中定义的类/函数，以及类内部方法。
3. 调用区：基于 workflow_adapter，展示选定入口函数的 WorkflowGraph 节点与边。
4. 执行区：输入参数，调用示例中的函数（foo 或 A.method），展示返回值。

注意：这是一个原型调试 UI，不修改任何文件，也不与 ASTViewer 主窗口交互。
"""

import ast
import sys
import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Any, Dict

# 添加项目根目录到路径，便于直接运行本脚本时找到 services / workflow_adapter 包
current_dir = Path(__file__).resolve().parent
project_root = current_dir
if current_dir.name != "ast_viewer":
    project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from services.scope_index import ScopeIndex, build_scope_index  # type: ignore[import]
from services.execution_engine import SimpleFunctionExecutor  # type: ignore[import]
from workflow_adapter import ast_to_workflow, WorkflowGraph, WorkflowNode, WorkflowEdge  # type: ignore[import]


# 与 tests/test_scope_index.py 中 EXAMPLE_CODE 相同的示例代码
EXAMPLE_CODE = (
    "X = 1\n\n"
    "class A:\n"
    "    CX = 10\n\n"
    "    def method(self, p1, p2):\n"
    "        local1 = X + self.CX\n"
    "        if p1:\n"
    "            inner = local1 + p2\n"
    "        return inner\n\n\n"
    "def foo(a, b):\n"
    "    y = a + b\n"
    "    z = y * 2\n"
    "    return z\n"
)


@dataclass
class ExampleContext:
    source: str
    tree: ast.Module
    scope_index: ScopeIndex
    functions: List[ast.FunctionDef]
    classes: List[ast.ClassDef]
    module_name: str
    file_path: str


def build_example_context() -> ExampleContext:
    """构建初始示例上下文。

    优先尝试从与本脚本同目录的 demo_exec_source.py 读取源码，
    解析成功则以该文件为默认演示源；若文件不存在或解析失败，
    回退到内联 EXAMPLE_CODE（example.py）。
    """

    base_dir = Path(__file__).resolve().parent
    demo_path = base_dir / "demo_exec_source.py"

    source: str
    tree: ast.Module
    module_name: str
    file_path: str

    if demo_path.exists():
        try:
            source = demo_path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(demo_path))
            module_name = demo_path.stem
            file_path = str(demo_path)
        except Exception:  # noqa: BLE001
            # 任何异常都退回到内联示例
            source = EXAMPLE_CODE
            tree = ast.parse(source, filename="example.py")
            module_name = "example"
            file_path = "example.py"
    else:
        source = EXAMPLE_CODE
        tree = ast.parse(source, filename="example.py")
        module_name = "example"
        file_path = "example.py"

    try:
        index = build_scope_index(tree, module_name=module_name)
    except Exception:  # noqa: BLE001
        # 索引失败时至少保持一个空索引占位，避免后续逻辑崩溃
        index = build_scope_index(tree, module_name=module_name)

    funcs: List[ast.FunctionDef] = []
    classes: List[ast.ClassDef] = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            funcs.append(node)
        elif isinstance(node, ast.ClassDef):
            classes.append(node)

    return ExampleContext(
        source=source,
        tree=tree,
        scope_index=index,
        functions=funcs,
        classes=classes,
        module_name=module_name,
        file_path=file_path,
    )


class ScrollableFrame(ttk.Frame):
    def __init__(self, parent: tk.Misc, *args: Any, **kwargs: Any) -> None:
        super().__init__(parent, *args, **kwargs)

        self._canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        vbar = ttk.Scrollbar(self, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=vbar.set)

        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.inner = ttk.Frame(self._canvas)
        self._window_id = self._canvas.create_window((0, 0), window=self.inner, anchor="nw")

        self.inner.bind(
            "<Configure>",
            lambda _e: self._canvas.configure(scrollregion=self._canvas.bbox("all")),
        )

        # 窗口大小变化时，同步内部 Frame 的宽度，使内容宽度自适应外层
        self._canvas.bind(
            "<Configure>",
            lambda e: self._canvas.itemconfigure(self._window_id, width=e.width),
        )

        self.inner.bind("<Enter>", self._on_enter)
        self.inner.bind("<Leave>", self._on_leave)

    def _on_mousewheel(self, event: tk.Event) -> None:  # type: ignore[type-arg]
        delta = 0
        if hasattr(event, "delta") and event.delta:
            delta = -int(event.delta / 120)
        elif hasattr(event, "num") and event.num in (4, 5):  # X11
            delta = -1 if event.num == 4 else 1
        if delta:
            self._canvas.yview_scroll(delta, "units")

    def _on_enter(self, _event: tk.Event) -> None:  # type: ignore[type-arg]
        self.bind_all("<MouseWheel>", self._on_mousewheel, add="+")

    def _on_leave(self, _event: tk.Event) -> None:  # type: ignore[type-arg]
        self.unbind_all("<MouseWheel>")


class VisualProgrammingApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Visual Programming Demo - ScopeIndex & WorkflowGraph")
        self.geometry("1200x800")

        self.ctx = build_example_context()
        # 执行区当前使用的上下文（可以切换到外部 .py 文件）
        self.exec_ctx: ExampleContext = self.ctx

        # 定义区中“模块定义 JSON 工具”的当前模板（ImportedModuleObject + LocalModuleObject 骨架）
        self.module_defs_template: Dict[str, Any] | None = None
        # 调用区中“执行空间 JSON 工具”的当前模板（ExecutionSpaceObject 骨架）
        self.exec_space_template: Dict[str, Any] | None = None

        # 执行空间编辑 / 执行器模式：
        # - "瀑布流 JSON"：仅基于 ExecutionSpaceObject 瀑布流结构进行编辑与回放；
        # - "瀑布流 + StepAstNode"：在瀑布流基础上结合 StepAstNode 结构驱动执行引擎。
        self.exec_engine_mode: str = "瀑布流 JSON"

        # 条件分支布局模式："below" 表示分支体在分支头下方展开，"right" 表示在分支头右侧展开
        self.branch_layout_mode = "below"
        # 分支快照模式："taken_only" 仅在 JSON 中保留条件为真的分支，"all" 保留所有分支
        self.branch_snapshot_mode = "taken_only"

        # 顶层布局：垂直分割为两部分
        # 上方：全局共享的执行时间线 Canvas（CAV 视图）
        # 下方：源选择条 + Notebook（导入区 / 定义区 / 调用区 / 执行区）
        self.main_pane: ttk.Panedwindow = ttk.Panedwindow(self, orient=tk.VERTICAL)
        self.main_pane.pack(fill=tk.BOTH, expand=True)

        self.exec_timeline_canvas = tk.Canvas(self.main_pane, height=120, bg="#ffffff")
        self.bottom_frame = ttk.Frame(self.main_pane)

        self.main_pane.add(self.exec_timeline_canvas, weight=0)
        self.main_pane.add(self.bottom_frame, weight=1)

        # 下半部分：第 0 行为“当前源 / 选择 .py 文件”工具条，第 1 行为 Notebook + Step 详情并列
        self.bottom_frame.columnconfigure(0, weight=3)
        self.bottom_frame.columnconfigure(1, weight=1)
        self.bottom_frame.rowconfigure(1, weight=1)

        # 初始当前源：使用 exec_ctx.file_path（优先 demo_exec_source.py，否则 example.py）
        self.exec_source_var = tk.StringVar(value=self.exec_ctx.file_path)
        src_frame = ttk.Frame(self.bottom_frame)
        # 让“当前源 + 分支布局 + 分支显示”等控件横跨两列，位于 Notebook 和 Step 详情面板之上
        src_frame.grid(row=0, column=0, columnspan=2, sticky="w", padx=5, pady=(5, 2))
        ttk.Label(src_frame, text="当前源：").pack(side=tk.LEFT)
        ttk.Label(src_frame, textvariable=self.exec_source_var).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(src_frame, text="选择 .py 文件...", command=self._choose_exec_file).pack(side=tk.LEFT)

        # 条件分支视图布局模式切换（仅影响 Canvas 时间线展示）
        ttk.Label(src_frame, text="分支布局：").pack(side=tk.LEFT, padx=(16, 2))
        self.branch_layout_var = tk.StringVar(value="下方展开")
        layout_cb = ttk.Combobox(
            src_frame,
            textvariable=self.branch_layout_var,
            values=["下方展开", "右侧展开"],
            state="readonly",
            width=8,
        )
        layout_cb.pack(side=tk.LEFT)
        layout_cb.bind("<<ComboboxSelected>>", self._on_branch_layout_change)

        # 条件分支显示开关（仅影响 Canvas 时间线是否显示未命中的分支子单元）
        ttk.Label(src_frame, text="分支显示：").pack(side=tk.LEFT, padx=(12, 2))
        self.branch_snapshot_var = tk.StringVar(value="仅执行路径")
        snapshot_cb = ttk.Combobox(
            src_frame,
            textvariable=self.branch_snapshot_var,
            values=["仅执行路径", "全部分支"],
            state="readonly",
            width=8,
        )
        snapshot_cb.pack(side=tk.LEFT)
        snapshot_cb.bind("<<ComboboxSelected>>", self._on_branch_snapshot_change)

        self.notebook: ttk.Notebook = ttk.Notebook(self.bottom_frame)
        self.notebook.grid(row=1, column=0, sticky="nsew")

        self.step_detail_frame = ttk.Frame(self.bottom_frame)
        self.step_detail_frame.grid(row=1, column=1, sticky="nsew")
        ttk.Label(self.step_detail_frame, text="当前 Step 详情").pack(anchor="w", padx=5, pady=(5, 0))
        self.step_detail_text = tk.Text(self.step_detail_frame, wrap="word", font=("Consolas", 9), height=6)
        self.step_detail_text.pack(fill="both", expand=True, padx=5, pady=5)
        self.step_detail_text.configure(state="disabled")

        # Canvas 时间线的 UI 状态：根 execution_space / 选中路径 / 展开路径集合
        # 路径采用 "0-1-3" 形式表示从根 exec_queue 开始的下钻索引序列
        self._timeline_root_space: Dict[str, Any] | None = None
        self._timeline_selected_path: str | None = None
        self._timeline_expanded_paths: set[str] = set()
        self._timeline_hit_regions: list[dict[str, Any]] = []

        # 绑定 Canvas 点击/双击事件
        self.exec_timeline_canvas.bind("<Button-1>", self._on_timeline_click)
        self.exec_timeline_canvas.bind("<Double-Button-1>", self._on_timeline_double_click)

        # 四个 Tab：外层为可滚动容器，内层 Frame 作为实际内容面板
        self.imports_container = ScrollableFrame(self.notebook)
        self.defs_container = ScrollableFrame(self.notebook)
        self.calls_container = ScrollableFrame(self.notebook)
        self.exec_container = ScrollableFrame(self.notebook)

        self.imports_tab = self.imports_container.inner
        self.defs_tab = self.defs_container.inner
        self.calls_tab = self.calls_container.inner
        self.exec_tab = self.exec_container.inner

        self.notebook.add(self.imports_container, text="导入区")
        self.notebook.add(self.defs_container, text="定义区")
        self.notebook.add(self.calls_container, text="调用区")
        self.notebook.add(self.exec_container, text="执行区")

        self._build_imports_tab()
        self._build_defs_tab()
        self._build_calls_tab()
        self._build_exec_tab()

    # -------------------- 导入区 --------------------
    def _build_imports_tab(self) -> None:
        frame = self.imports_tab
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)

        ttk.Label(frame, text="示例代码中的 import 语句：").grid(
            row=0, column=0, sticky="w", padx=5, pady=(5, 2)
        )

        self.imports_text = tk.Text(frame, wrap="none", font=("Consolas", 10))
        self.imports_text.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        self.imports_modules_frame = ttk.Frame(frame)
        self.imports_modules_frame.grid(row=2, column=0, sticky="w", padx=5, pady=(0, 5))
        self.import_module_vars: Dict[str, tk.BooleanVar] = {}
        self.import_module_paths: Dict[str, str] = {}

        self._refresh_imports_content()

    def _refresh_imports_content(self) -> None:
        text = getattr(self, "imports_text", None)
        if text is None:
            return

        text.configure(state="normal")
        text.delete("1.0", tk.END)

        tree = getattr(self.exec_ctx, "tree", None)
        if tree is None:
            text.insert("1.0", "（当前示例代码没有解析成功）")
            text.configure(state="disabled")
            return

        lines: list[str] = []
        modules: Dict[str, str] = {}

        file_path = getattr(self.exec_ctx, "file_path", "")
        try:
            base_dir = Path(file_path).resolve().parent if file_path else current_dir
        except Exception:
            base_dir = current_dir
        search_roots = [base_dir, current_dir, project_root]

        def _resolve_module_path(name: str) -> str | None:
            rel = name.replace(".", "/") + ".py"
            for root in search_roots:
                candidate = (root / rel).resolve()
                if candidate.exists() and candidate.is_file():
                    return str(candidate)
            return None

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    ln = getattr(node, "lineno", None)
                    lines.append(f"Import: {alias.name} (L{ln})")
                    mod_name = alias.name
                    if mod_name not in modules:
                        path = _resolve_module_path(mod_name)
                        if path is not None:
                            modules[mod_name] = path
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                ln = getattr(node, "lineno", None)
                names = ", ".join(a.name for a in node.names)
                lines.append(f"From {module} import {names} (L{ln})")
                if module and module not in modules:
                    path = _resolve_module_path(module)
                    if path is not None:
                        modules[module] = path

        if not lines:
            lines.append("（当前示例代码没有 import 语句）")

        text.insert("1.0", "\n".join(lines))
        text.configure(state="disabled")

        mods_frame = getattr(self, "imports_modules_frame", None)
        if isinstance(mods_frame, ttk.Frame):
            for child in mods_frame.winfo_children():
                child.destroy()

            self.import_module_vars = {}
            self.import_module_paths = modules

            if not modules:
                ttk.Label(mods_frame, text="（没有可解析的本地模块）").pack(side=tk.LEFT)
            else:
                ttk.Label(mods_frame, text="勾选要在定义区展开的模块：").pack(anchor="w")
                for name in sorted(modules.keys()):
                    var = tk.BooleanVar(value=False)
                    self.import_module_vars[name] = var
                    path = modules[name]
                    label_text = f"{name}  ({Path(path).name})"
                    ttk.Checkbutton(
                        mods_frame,
                        text=label_text,
                        variable=var,
                        command=self._on_import_module_toggle,
                    ).pack(anchor="w")

    def _on_import_module_toggle(self) -> None:
        try:
            self._refresh_defs_content()
        except Exception:
            pass

    # -------------------- 定义区 --------------------
    def _build_defs_tab(self) -> None:
        frame = self.defs_tab
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        # 在定义区内部放一个 Notebook：
        #  - 子Tab1：定义树（原来的 defs_tree，作为“工具箱”）
        #  - 子Tab2：模块定义 JSON 工具
        defs_nb = ttk.Notebook(frame)
        defs_nb.grid(row=0, column=0, sticky="nsew")

        # 子Tab1：定义树
        tree_tab = ttk.Frame(defs_nb)
        tree_tab.columnconfigure(0, weight=1)
        tree_tab.rowconfigure(0, weight=1)

        tree = ttk.Treeview(tree_tab, columns=("kind", "lineno"), show="tree headings")
        tree.heading("kind", text="种类")
        tree.heading("lineno", text="行号")
        tree.column("kind", width=120, anchor="w")
        tree.column("lineno", width=60, anchor="e")
        tree.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.defs_tree = tree

        sb = ttk.Scrollbar(tree_tab, orient=tk.VERTICAL, command=tree.yview)
        sb.grid(row=0, column=1, sticky="ns", pady=5)
        tree.configure(yscrollcommand=sb.set)

        self._refresh_defs_content()

        # 子Tab2：模块定义 JSON 工具（从调用区迁移而来）
        mod_tab = ttk.Frame(defs_nb)
        mod_tab.columnconfigure(0, weight=1)
        mod_tab.rowconfigure(2, weight=1)

        tools_frame = ttk.LabelFrame(mod_tab, text="模块定义 JSON 工具")
        tools_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # 第 1 行：模块级操作按钮
        btn_row = ttk.Frame(tools_frame)
        btn_row.grid(row=0, column=0, sticky="w", padx=5, pady=(5, 2))

        ttk.Button(
            btn_row,
            text="新建模块 JSON",
            command=self._on_new_module_json_clicked,
        ).pack(side=tk.LEFT, padx=(0, 8))

        ttk.Button(
            btn_row,
            text="添加模块属性(全局变量)",
            command=self._add_module_attribute_from_defs,
        ).pack(side=tk.LEFT, padx=(0, 8))

        ttk.Button(
            btn_row,
            text="添加模块方法(全局函数)",
            command=self._add_module_method_from_defs,
        ).pack(side=tk.LEFT)

        # 第 2 行：类 / 实例相关操作（新建类、选择当前类、新建属性/方法）
        class_row = ttk.Frame(tools_frame)
        class_row.grid(row=1, column=0, sticky="w", padx=5, pady=(2, 2))

        ttk.Button(
            class_row,
            text="新建类",
            command=self._on_new_class_clicked,
        ).pack(side=tk.LEFT, padx=(0, 8))

        ttk.Label(class_row, text="当前类：").pack(side=tk.LEFT)
        self.local_class_var = tk.StringVar(value="")
        self.local_class_cb = ttk.Combobox(
            class_row,
            textvariable=self.local_class_var,
            values=[],
            state="readonly",
            width=18,
        )
        self.local_class_cb.pack(side=tk.LEFT, padx=(0, 8))

        ttk.Button(
            class_row,
            text="新建属性",
            command=self._on_new_class_attr_clicked,
        ).pack(side=tk.LEFT, padx=(0, 8))

        ttk.Button(
            class_row,
            text="新建方法",
            command=self._on_new_class_method_clicked,
        ).pack(side=tk.LEFT)

        tools_frame.rowconfigure(2, weight=1)
        tools_frame.columnconfigure(0, weight=1)

        self.module_defs_preview = tk.Text(tools_frame, wrap="none", font=("Consolas", 9), height=10)
        self.module_defs_preview.grid(row=2, column=0, sticky="nsew", padx=5, pady=(0, 5))
        self.module_defs_preview.configure(state="disabled")

        # 把两个子页加入 Notebook
        defs_nb.add(tree_tab, text="定义树")
        defs_nb.add(mod_tab, text="模块定义")

    def _refresh_defs_content(self) -> None:
        tree = getattr(self, "defs_tree", None)
        if tree is None:
            return

        # 清空现有内容
        for item in tree.get_children(""):
            tree.delete(item)

        ctx = self.exec_ctx
        def add_module_to_tree(
            mod_name: str,
            classes: List[ast.ClassDef],
            functions: List[ast.FunctionDef],
            globals_nodes: List[ast.AST],
        ) -> None:
            root_id = tree.insert("", "end", text=mod_name, values=("module", ""))

            for cls in classes:
                ln = getattr(cls, "lineno", "")
                cls_id = tree.insert(
                    root_id,
                    "end",
                    text=cls.name,
                    values=("class", ln),
                )
                for stmt in cls.body:
                    if isinstance(stmt, ast.FunctionDef):
                        ln_m = getattr(stmt, "lineno", "")
                        tree.insert(
                            cls_id,
                            "end",
                            text=stmt.name,
                            values=("method", ln_m),
                        )

            for fn in functions:
                ln = getattr(fn, "lineno", "")
                tree.insert(
                    root_id,
                    "end",
                    text=fn.name,
                    values=("function", ln),
                )

            for gv in globals_nodes:
                ln = getattr(gv, "lineno", "")
                if isinstance(gv, ast.Assign):
                    targets = [t.id for t in gv.targets if isinstance(t, ast.Name)]
                    name = ", ".join(targets) if targets else "<assign>"
                elif isinstance(gv, ast.AnnAssign) and isinstance(gv.target, ast.Name):
                    name = gv.target.id
                else:
                    name = "<var>"
                tree.insert(
                    root_id,
                    "end",
                    text=name,
                    values=("global", ln),
                )

            tree.item(root_id, open=True)

        globals_nodes: List[ast.AST] = []
        if isinstance(ctx.tree, ast.Module):
            for node in ctx.tree.body:
                if isinstance(node, (ast.Assign, ast.AnnAssign)):
                    globals_nodes.append(node)

        add_module_to_tree(ctx.module_name, ctx.classes, ctx.functions, globals_nodes)

        module_paths: Dict[str, str] = getattr(self, "import_module_paths", {})
        module_vars: Dict[str, tk.BooleanVar] = getattr(self, "import_module_vars", {})
        for mod_name, var in module_vars.items():
            if not var.get():
                continue

            path = module_paths.get(mod_name)
            if not path:
                continue

            try:
                source = Path(path).read_text(encoding="utf-8")
                mod_tree = ast.parse(source, filename=path)
            except Exception:
                continue

            funcs2: List[ast.FunctionDef] = []
            classes2: List[ast.ClassDef] = []
            globals2: List[ast.AST] = []
            for node in mod_tree.body:
                if isinstance(node, ast.FunctionDef):
                    funcs2.append(node)
                elif isinstance(node, ast.ClassDef):
                    classes2.append(node)
                elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                    globals2.append(node)

            add_module_to_tree(mod_name, classes2, funcs2, globals2)

    # -------------------- 调用区（Workflow） --------------------
    def _build_calls_tab(self) -> None:
        frame = self.calls_tab
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        calls_nb = ttk.Notebook(frame)
        calls_nb.grid(row=0, column=0, sticky="nsew")

        # 子Tab1：节点/边（原有 Workflow 文本视图）
        wf_tab = ttk.Frame(calls_nb)
        wf_tab.columnconfigure(0, weight=1)
        wf_tab.rowconfigure(2, weight=1)

        ttk.Label(wf_tab, text="选择入口函数：").grid(
            row=0, column=0, sticky="w", padx=5, pady=(5, 2)
        )
        self.entry_var = tk.StringVar(value="foo")
        choices: list[str] = []
        for cls in self.exec_ctx.classes:
            for stmt in cls.body:
                if isinstance(stmt, ast.FunctionDef):
                    choices.append(f"{cls.name}.{stmt.name}")
        for fn in self.exec_ctx.functions:
            choices.append(fn.name)

        cb = ttk.Combobox(wf_tab, textvariable=self.entry_var, values=choices, state="readonly")
        cb.grid(row=1, column=0, sticky="w", padx=5, pady=(0, 5))
        cb.bind("<<ComboboxSelected>>", lambda _e: self._refresh_calls_view())
        self.calls_entry_cb = cb

        self.calls_text = tk.Text(wf_tab, wrap="none", font=("Consolas", 10))
        self.calls_text.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)

        calls_nb.add(wf_tab, text="节点/边")

        # 子Tab2：执行空间 JSON 工具（编辑 ExecutionSpaceObject）
        exec_tab = ttk.Frame(calls_nb)
        exec_tab.columnconfigure(0, weight=1)
        exec_tab.rowconfigure(3, weight=1)

        tools_row = ttk.Frame(exec_tab)
        tools_row.grid(row=0, column=0, sticky="w", padx=5, pady=(5, 2))

        ttk.Button(
            tools_row,
            text="新建执行空间 JSON",
            command=self._on_new_exec_space_clicked,
        ).pack(side=tk.LEFT, padx=(0, 8))

        ttk.Button(
            tools_row,
            text="导入全局到 scope_in",
            command=self._on_import_globals_to_scope_in,
        ).pack(side=tk.LEFT, padx=(0, 8))

        # 执行器模式选择：瀑布流 JSON / 瀑布流 + StepAstNode
        ttk.Label(tools_row, text="执行模式：").pack(side=tk.LEFT, padx=(8, 2))
        self.exec_engine_mode_var = tk.StringVar(value=self.exec_engine_mode)
        exec_mode_cb = ttk.Combobox(
            tools_row,
            textvariable=self.exec_engine_mode_var,
            values=["瀑布流 JSON", "瀑布流 + StepAstNode"],
            state="readonly",
            width=18,
        )
        exec_mode_cb.pack(side=tk.LEFT)

        def _on_exec_mode_changed(_event: tk.Event | None = None) -> None:  # type: ignore[type-arg]
            mode = self.exec_engine_mode_var.get()
            if isinstance(mode, str) and mode:
                self.exec_engine_mode = mode

        exec_mode_cb.bind("<<ComboboxSelected>>", _on_exec_mode_changed)

        # Step 类型选择 + 添加 Step
        type_row = ttk.Frame(exec_tab)
        type_row.grid(row=1, column=0, sticky="w", padx=5, pady=(0, 2))

        ttk.Label(type_row, text="步骤类型：").pack(side=tk.LEFT)
        self.exec_step_type_var = tk.StringVar(value="普通步骤")
        type_cb = ttk.Combobox(
            type_row,
            textvariable=self.exec_step_type_var,
            values=["普通步骤", "函数调用", "条件控制"],
            state="readonly",
            width=10,
        )
        type_cb.pack(side=tk.LEFT, padx=(0, 8))

        ttk.Button(
            type_row,
            text="添加 Step",
            command=self._on_add_exec_step_clicked,
        ).pack(side=tk.LEFT)

        # 第 3 行：左侧步骤列表，右侧 JSON 预览
        main_row = ttk.Frame(exec_tab)
        main_row.grid(row=2, column=0, sticky="nsew", padx=5, pady=(2, 5))
        main_row.columnconfigure(0, weight=0)
        main_row.columnconfigure(1, weight=1)
        main_row.rowconfigure(0, weight=1)

        steps_frame = ttk.LabelFrame(main_row, text="步骤列表(exec_queue)")
        steps_frame.grid(row=0, column=0, sticky="ns", padx=(0, 5))

        self.exec_steps_list = tk.Listbox(steps_frame, height=10, width=26)
        self.exec_steps_list.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        steps_sb = ttk.Scrollbar(steps_frame, orient=tk.VERTICAL, command=self.exec_steps_list.yview)
        steps_sb.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        self.exec_steps_list.configure(yscrollcommand=steps_sb.set)

        # 顶层步骤列表选中变化时，刷新下方的分支列表
        self.exec_steps_list.bind("<<ListboxSelect>>", self._on_exec_step_selected)

        preview_frame = ttk.LabelFrame(main_row, text="ExecutionSpaceObject 预览")
        preview_frame.grid(row=0, column=1, sticky="nsew")
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)

        self.exec_space_preview = tk.Text(preview_frame, wrap="none", font=("Consolas", 9))
        self.exec_space_preview.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.exec_space_preview.configure(state="disabled")

        # 当前 if step 的分支列表（用于将子 step 添加到某个分支的 exec_queue 中）
        branches_frame = ttk.LabelFrame(main_row, text="当前 if 分支(branches)")
        branches_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 5), pady=(0, 5))
        main_row.rowconfigure(1, weight=0)

        self.exec_branch_step_label_var = tk.StringVar(value="当前 Step: <未选中>")
        ttk.Label(branches_frame, textvariable=self.exec_branch_step_label_var).pack(
            anchor="w",
            padx=5,
            pady=(5, 0),
        )

        self.exec_branches_list = tk.Listbox(branches_frame, height=4, width=26)
        self.exec_branches_list.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)

        branches_sb = ttk.Scrollbar(branches_frame, orient=tk.VERTICAL, command=self.exec_branches_list.yview)
        branches_sb.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        self.exec_branches_list.configure(yscrollcommand=branches_sb.set)
        self.exec_branches_list.bind("<<ListboxSelect>>", self._on_exec_branch_selected)

        calls_nb.add(exec_tab, text="执行空间")

        self._refresh_calls_view()

    def _resolve_entry_node(self) -> Optional[ast.AST]:
        """根据 entry_var 解析为具体的 AST 节点（方法或函数）。"""

        name = self.entry_var.get()
        if "." in name:
            cls_name, meth_name = name.split(".", 1)
            for cls in self.exec_ctx.classes:
                if cls.name == cls_name:
                    for stmt in cls.body:
                        if isinstance(stmt, ast.FunctionDef) and stmt.name == meth_name:
                            return stmt
            return None
        else:
            for fn in self.exec_ctx.functions:
                if fn.name == name:
                    return fn
            return None

    def _refresh_calls_view(self) -> None:
        if self.calls_text is None:
            return

        self.calls_text.configure(state="normal")
        self.calls_text.delete("1.0", tk.END)

        entry_node = self._resolve_entry_node()
        if entry_node is None:
            self.calls_text.insert("1.0", "未找到入口函数对应的 AST 节点。\n")
            self.calls_text.configure(state="disabled")
            return

        try:
            graph: WorkflowGraph = ast_to_workflow(entry_node)
        except Exception as exc:  # noqa: BLE001
            self.calls_text.insert("1.0", f"ast_to_workflow 失败: {exc}\n")
            self.calls_text.configure(state="disabled")
            return

        lines: list[str] = []
        lines.append(f"Entry: {type(entry_node).__name__} {getattr(entry_node, 'name', '')}")
        lines.append("")
        lines.append("Nodes:")
        for node in graph.nodes:
            ast_type = type(node.ast_node).__name__
            lineno = getattr(node.ast_node, "lineno", None)
            exec_mode = node.metadata.get("exec_mode") if isinstance(node, WorkflowNode) else None
            control_type = node.metadata.get("control_type") if isinstance(node, WorkflowNode) else None

            if isinstance(lineno, int):
                base = f"  {node.id}: {node.component_type} ({ast_type}, L{lineno})"
            else:
                base = f"  {node.id}: {node.component_type} ({ast_type})"

            if exec_mode:
                base += f" [mode={exec_mode}]"
            if control_type:
                base += f" [control={control_type}]"
            lines.append(base)

        lines.append("")
        lines.append("Edges:")
        if graph.edges:
            for edge in graph.edges:
                etype = edge.edge_type if isinstance(edge, WorkflowEdge) else "?"
                lines.append(
                    f"  {edge.id}: {edge.source_port_id} -> {edge.target_port_id} [{etype}]",
                )
        else:
            lines.append("  (无边)")

        self.calls_text.insert("1.0", "\n".join(lines) + "\n")
        self.calls_text.configure(state="disabled")

    # -------------------- 执行空间 JSON 工具：ExecutionSpaceObject 编辑 --------------------

    def _init_exec_space_template(self) -> None:
        """初始化执行空间 JSON 模板。"""

        self.exec_space_template = {
            "scope_level": "module",
            "scope_in": {},
            "scope_out": {},
            "exec_queue": [],  # list[ExecutionStepObject]
        }

    def _refresh_exec_space_preview(self) -> None:
        text = getattr(self, "exec_space_preview", None)
        if text is None:
            return

        text.configure(state="normal")
        text.delete("1.0", tk.END)

        data = getattr(self, "exec_space_template", None)
        if data is None:
            text.insert("1.0", "（尚未创建执行空间 JSON）")
        else:
            try:
                pretty = json.dumps(data, ensure_ascii=False, indent=2)
            except TypeError:
                pretty = str(data)
            text.insert("1.0", pretty)

        text.configure(state="disabled")

    def _refresh_exec_steps_list(self) -> None:
        lst = getattr(self, "exec_steps_list", None)
        if lst is None:
            return

        lst.delete(0, tk.END)

        space = getattr(self, "exec_space_template", None)
        if not isinstance(space, dict):
            return

        steps = space.get("exec_queue") or []
        if not isinstance(steps, list):
            return

        for idx, step in enumerate(steps):
            if not isinstance(step, dict):
                label = f"#{idx} <invalid>"
            else:
                kind = step.get("kind") or "step"
                desc = step.get("desc") or step.get("name") or ""
                if desc:
                    label = f"#{idx} {kind}: {desc}"
                else:
                    label = f"#{idx} {kind}"
            lst.insert(tk.END, label)

        # 步骤列表刷新后，同步刷新当前分支列表
        self._refresh_exec_branches_list()

    def _on_exec_step_selected(self, _event: tk.Event | None = None) -> None:  # type: ignore[type-arg]
        """当顶层步骤列表选中项变化时，记录选中的 step 索引并刷新分支列表。"""

        lst = getattr(self, "exec_steps_list", None)
        if lst is None:
            return

        sel = lst.curselection()
        if not sel:
            self._exec_selected_step_index: int | None = None
        else:
            try:
                self._exec_selected_step_index = int(sel[0])
            except (TypeError, ValueError):
                self._exec_selected_step_index = None

        # 选中新的 step 时，清空分支选中状态
        self._exec_selected_branch_index: int | None = None
        self._refresh_exec_branches_list()

    def _refresh_exec_branches_list(self) -> None:
        """根据当前选中的 step，刷新下方的分支列表。"""

        lst = getattr(self, "exec_branches_list", None)
        label_var = getattr(self, "exec_branch_step_label_var", None)
        if lst is None or label_var is None:
            return

        lst.delete(0, tk.END)

        space = getattr(self, "exec_space_template", None)
        if not isinstance(space, dict):
            label_var.set("当前 Step: <未选中>")
            return

        steps = space.get("exec_queue") or []
        if not isinstance(steps, list) or not steps:
            label_var.set("当前 Step: <无步骤>")
            return

        step_idx: int | None = getattr(self, "_exec_selected_step_index", None)
        if step_idx is None or step_idx < 0 or step_idx >= len(steps):
            label_var.set("当前 Step: <未选中>")
            return

        step = steps[step_idx]
        if not isinstance(step, dict):
            label_var.set(f"当前 Step: #{step_idx} <invalid>")
            return

        kind = step.get("kind") or "step"
        desc = step.get("desc") or step.get("name") or ""
        if desc:
            label_var.set(f"当前 Step: #{step_idx} {kind}: {desc}")
        else:
            label_var.set(f"当前 Step: #{step_idx} {kind}")

        branches = step.get("branches")
        if not isinstance(branches, list) or not branches:
            lst.insert(tk.END, "(当前步骤不是条件控制型，或无 branches)")
            return

        for idx, branch in enumerate(branches):
            if not isinstance(branch, dict):
                lst.insert(tk.END, f"#{idx} <invalid>")
                continue

            label = branch.get("label") or "branch"
            cond = branch.get("condition_expr") or ""
            taken = bool(branch.get("taken"))

            text = label if not cond else f"{label}: {cond}"
            if taken:
                text += " [taken]"
            lst.insert(tk.END, f"#{idx} {text}")

    def _on_exec_branch_selected(self, _event: tk.Event | None = None) -> None:  # type: ignore[type-arg]
        """当分支列表选中项变化时，记录当前选中的 branch 索引。"""

        lst = getattr(self, "exec_branches_list", None)
        if lst is None:
            return

        sel = lst.curselection()
        if not sel:
            self._exec_selected_branch_index = None
        else:
            try:
                self._exec_selected_branch_index = int(sel[0])
            except (TypeError, ValueError):
                self._exec_selected_branch_index = None

    def _on_new_exec_space_clicked(self) -> None:
        """点击“新建执行空间 JSON”时重置 ExecutionSpaceObject。"""

        self._init_exec_space_template()
        self._refresh_exec_steps_list()
        self._refresh_exec_space_preview()

    def _make_scope_binding(self, name: str, value: Any, kind: str | None = None) -> Dict[str, Any]:
        """根据当前文档约定，将一个名字和值包装为 {kind, name, value} 三元组。

        说明：
        - kind 用于粗粒度区分“module/constant/call/…”，默认为基于 value 的简单推断；
        - name 是作用域中的键名；
        - value 是与该绑定相关的具体值或结构（例如 module_ref、func_def_ref，或占位 None）。
        """

        inferred_kind: str
        if kind is not None:
            inferred_kind = kind
        else:
            # 简单默认策略：基础标量视为 constant，其余视为 generic value
            if isinstance(value, (int, float, bool, str)) or value is None:
                inferred_kind = "constant"
            else:
                inferred_kind = "value"

        return {"kind": inferred_kind, "name": name, "value": value}

    def _on_import_globals_to_scope_in(self) -> None:
        """将模块定义 JSON 中的全局变量半自动导入到 scope_in 中。

        当前策略：
        - 若 module_defs_template 尚未创建，先提示用户去定义区创建；
        - 从 local_module.definitions.attributes 中读取键；
        - 对于每个键，若 scope_in 中无同名键，则填充一个占位值 None；
          （后续可以扩展为弹窗让用户为每个变量填写具体初始值）。
        """

        if self.exec_space_template is None:
            self._init_exec_space_template()

        if self.module_defs_template is None:
            messagebox.showinfo("导入全局到 scope_in", "请先在定义区的“模块定义”页中新建模块 JSON，并添加全局变量。")
            return

        local_module = self.module_defs_template.get("local_module") or {}
        defs = local_module.get("definitions") or {}
        attrs = defs.get("attributes")
        if not isinstance(attrs, dict) or not attrs:
            messagebox.showinfo("导入全局到 scope_in", "模块定义中没有可导入的全局变量。")
            return

        scope_in = self.exec_space_template.get("scope_in")
        if not isinstance(scope_in, dict):
            scope_in = {}
            self.exec_space_template["scope_in"] = scope_in

        for name in attrs.keys():
            if name not in scope_in:
                # 使用 {kind, name, value} 三元组形式为 scope_in 填充占位绑定
                scope_in[name] = self._make_scope_binding(name, None, kind="constant")

        self._refresh_exec_space_preview()

    def _on_add_exec_step_clicked(self) -> None:
        """根据当前选择的步骤类型，向适当的 exec_queue 追加一个 ExecutionStepObject。

        规则：
        - 默认情况下，将步骤追加到顶层 ExecutionSpaceObject.exec_queue；
        - 若当前在下方分支列表中选中了某个 if 分支，则将步骤追加到该分支的 exec_queue 中，
          便于构造 "branch.exec_queue" 形式的分支体步骤序列。
        """

        if self.exec_space_template is None:
            self._init_exec_space_template()

        space = self.exec_space_template

        # 默认目标：顶层 exec_queue
        root_steps = space.get("exec_queue")
        if not isinstance(root_steps, list):
            root_steps = []
            space["exec_queue"] = root_steps
        target_steps = root_steps

        # 若当前选中了某个 if step + 其分支，则尝试将步骤追加到该 branch.exec_queue
        step_idx: int | None = getattr(self, "_exec_selected_step_index", None)
        branch_idx: int | None = getattr(self, "_exec_selected_branch_index", None)
        if (
            isinstance(step_idx, int)
            and isinstance(branch_idx, int)
            and 0 <= step_idx < len(root_steps)
        ):
            parent_step = root_steps[step_idx]
            if isinstance(parent_step, dict):
                branches = parent_step.get("branches")
                if isinstance(branches, list) and 0 <= branch_idx < len(branches):
                    branch = branches[branch_idx]
                    if isinstance(branch, dict):
                        branch_steps = branch.get("exec_queue")
                        if not isinstance(branch_steps, list):
                            branch_steps = []
                            branch["exec_queue"] = branch_steps
                        target_steps = branch_steps

        step_type = getattr(self, "exec_step_type_var", None)
        if isinstance(step_type, tk.StringVar):
            tval = step_type.get()
        else:
            tval = "普通步骤"

        if tval == "函数调用":
            # 简单函数调用步骤：kind=method_call，附带占位信息
            desc = simpledialog.askstring("添加 Step", "请输入函数/方法调用描述（如 foo 或 A.method）：", parent=self)
            if not desc:
                return
            func_name = desc.strip()
            target_name = "result"
            step = {
                "kind": "method_call",
                "desc": desc.strip(),
                "scope_level": "function",
                "scope_in": {},
                "scope_out": {},
                "exec_queue": [],
                # 扁平化 StepAstNode：直接在 step 上携带 ast_node_type / fields
                "ast_node_type": "Assign",
                "fields": {
                    "targets": [
                        {
                            "ast_node_type": "Name",
                            "fields": {
                                "id": target_name,
                                "ctx": "Store",
                            },
                        }
                    ],
                    "value": {
                        "ast_node_type": "Call",
                        "fields": {
                            "func": {
                                "ast_node_type": "Name",
                                "fields": {
                                    "id": func_name,
                                    "ctx": "Load",
                                },
                            },
                            "args": [],
                            "keywords": [],
                        },
                    },
                    "type_comment": None,
                },
            }
        elif tval == "条件控制":
            # 条件控制步骤：构造一个真正的 if ExecutionStepObject，并自动生成若干空分支
            cond = simpledialog.askstring("添加 Step", "请输入 if 分支的条件表达式说明：", parent=self)
            if cond is None:
                return
            cond_text = cond.strip()
            step = {
                "kind": "if",
                "desc": cond_text,
                "scope_level": "stmt",
                "scope_in": {},
                "scope_out": {},
                "exec_queue": [],  # 条件控制型 step 自身的线性子执行空间通常留空
                "control_type": "if",
                # 分支对象直接通过 exec_queue 挂载分支体内部的 ExecutionStepObject 列表
                "branches": [
                    {
                        "label": "if",
                        "condition_expr": cond_text or None,
                        "condition_value": None,
                        "taken": False,
                        "exec_queue": [],
                    },
                    {
                        "label": "else",
                        "condition_expr": None,
                        "condition_value": None,
                        "taken": False,
                        "exec_queue": [],
                    },
                ],
                # 扁平化 StepAstNode：If 语句的静态结构占位
                "ast_node_type": "If",
                "fields": {
                    "test": None,
                    "body": [],
                    "orelse": [],
                },
            }
        else:
            # 普通步骤：kind=step，可选描述
            desc = simpledialog.askstring("添加 Step", "请输入步骤描述（可留空）：", parent=self)
            if desc is None:
                return
            step = {
                "kind": "step",
                "desc": desc.strip(),
                "scope_level": "block",
                "scope_in": {},
                "scope_out": {},
                "exec_queue": [],
            }

        target_steps.append(step)
        self._refresh_exec_steps_list()
        self._refresh_exec_space_preview()

    # -------------------- 模块定义 JSON 工具：ImportedModuleObject + LocalModuleObject 骨架 --------------------

    def _init_module_defs_template(self) -> None:
        """根据当前 exec_ctx 和导入区可解析模块，初始化模块定义 JSON 骨架。

        结构对齐 ASTViewer_runtime_object_model.md 中的 ImportedModuleObject / LocalModuleObject：

        {
          "imported_modules": [ImportedModuleObject, ...],
          "local_module": LocalModuleObject,
        }
        """

        imported_modules: list[dict[str, Any]] = []

        # 当前源模块也视为一个 ImportedModuleObject
        mod_name = getattr(self.exec_ctx, "module_name", "<current>")
        file_path = getattr(self.exec_ctx, "file_path", None)
        imported_modules.append(
            {
                "original_module_name": mod_name,
                "file_path": file_path,
                "definitions": {
                    "attributes": {},
                    "methods": {},
                    "inner_classes": {},
                },
            }
        )

        # 导入区中可解析到的本地模块，同样作为 ImportedModuleObject 挂到 imported_modules
        module_paths: Dict[str, str] = getattr(self, "import_module_paths", {})
        for name, path in sorted(module_paths.items()):
            imported_modules.append(
                {
                    "original_module_name": name,
                    "file_path": path,
                    "definitions": {
                        "attributes": {},
                        "methods": {},
                        "inner_classes": {},
                    },
                }
            )

        # 本模块自身：LocalModuleObject
        local_module = {
            "definitions": {
                "attributes": {},
                "methods": {},
                "inner_classes": {},
            }
        }

        self.module_defs_template = {
            "imported_modules": imported_modules,
            "local_module": local_module,
        }

    def _refresh_module_defs_preview(self) -> None:
        text = getattr(self, "module_defs_preview", None)
        if text is None:
            return

        text.configure(state="normal")
        text.delete("1.0", tk.END)

        data = getattr(self, "module_defs_template", None)
        if data is None:
            text.insert("1.0", "（尚未创建模块 JSON）")
        else:
            try:
                pretty = json.dumps(data, ensure_ascii=False, indent=2)
            except TypeError:
                pretty = str(data)
            text.insert("1.0", pretty)

        text.configure(state="disabled")

    def _on_new_module_json_clicked(self) -> None:
        """点击“新建模块 JSON”按钮时，重置模块定义骨架并刷新预览。"""

        self._init_module_defs_template()
        self._refresh_local_class_choices()
        self._refresh_module_defs_preview()

    def _get_defs_tree_selection_kind_name(self) -> tuple[str | None, str | None]:
        """从定义区 Treeview 当前选中项中提取 (kind, name)。

        kind 对应第二列的种类："class" / "method" / "function" / "global" / "module"。
        name 对应节点文本。
        """

        tree = getattr(self, "defs_tree", None)
        if tree is None:
            return None, None

        sel = tree.selection()
        if not sel:
            return None, None

        item_id = sel[0]
        item = tree.item(item_id)
        text = item.get("text") or None
        values = item.get("values") or []
        kind: str | None = None
        if values and isinstance(values, (list, tuple)):
            k = values[0]
            if isinstance(k, str):
                kind = k

        return kind, text

    def _add_module_attribute_from_defs(self) -> None:
        """将定义区当前选中的全局变量，添加为 local_module.definitions.attributes 的一项。"""

        if self.module_defs_template is None:
            self._init_module_defs_template()

        kind, name = self._get_defs_tree_selection_kind_name()
        if kind != "global" or not name:
            return

        local_module = self.module_defs_template.get("local_module") or {}
        defs = local_module.get("definitions") or {}
        attrs = defs.get("attributes")
        if not isinstance(attrs, dict):
            attrs = {}
            defs["attributes"] = attrs

        # 简化版 GlobalVarObject：仅记录名称和来源模块名，后续可由执行引擎扩展为完整对象
        mod_name = getattr(self.exec_ctx, "module_name", "<current>")
        attrs[name] = {
            "name": name,
            "from_module": mod_name,
        }

        local_module["definitions"] = defs
        self.module_defs_template["local_module"] = local_module
        self._refresh_module_defs_preview()

    # -------------------- 模块定义 JSON 工具：类 / 实例相关操作 --------------------

    def _refresh_local_class_choices(self) -> None:
        """根据 local_module.definitions.inner_classes 刷新类下拉列表。"""

        cb = getattr(self, "local_class_cb", None)
        var = getattr(self, "local_class_var", None)
        if cb is None or var is None:
            return

        module_label = "[模块级]"
        classes: list[str] = [module_label]
        if self.module_defs_template is not None:
            local_module = self.module_defs_template.get("local_module") or {}
            defs = local_module.get("definitions") or {}
            inner = defs.get("inner_classes")
            if isinstance(inner, dict):
                classes.extend(sorted(str(name) for name in inner.keys()))

        cb["values"] = classes

        current = var.get() if isinstance(var, tk.StringVar) else ""
        if classes:
            if current not in classes:
                var.set(classes[0])
        else:
            var.set("")

    def _on_new_class_clicked(self) -> None:
        """新建类：弹窗输入类名，在 local_module.definitions.inner_classes 中创建占位结构。"""

        if self.module_defs_template is None:
            self._init_module_defs_template()

        module_label = "[模块级]"

        name = simpledialog.askstring("新建类", "请输入类名：", parent=self)
        if not name:
            return
        name = name.strip()
        if not name:
            return

        if name == module_label:
            messagebox.showwarning("新建类", f"类名 '{module_label}' 为保留名称，请使用其他名称。")
            return

        local_module = self.module_defs_template.get("local_module") or {}
        defs = local_module.get("definitions") or {}
        inner = defs.get("inner_classes")
        if not isinstance(inner, dict):
            inner = {}
            defs["inner_classes"] = inner

        if name in inner:
            messagebox.showwarning("新建类", f"类 '{name}' 已存在。")
            return

        inner[name] = {
            "name": name,
            "kind": "class",
            "attributes": {},
            "methods": {},
        }

        local_module["definitions"] = defs
        self.module_defs_template["local_module"] = local_module

        # 刷新下拉并选中新建的类
        self._refresh_local_class_choices()
        if isinstance(self.local_class_var, tk.StringVar):
            self.local_class_var.set(name)

        self._refresh_module_defs_preview()

    def _on_new_class_attr_clicked(self) -> None:
        """为当前选中类新建属性（类属性或实例属性）。"""

        if self.module_defs_template is None:
            self._init_module_defs_template()

        module_label = "[模块级]"

        current_cls = self.local_class_var.get() if isinstance(self.local_class_var, tk.StringVar) else ""
        if not current_cls:
            messagebox.showinfo("新建属性", "请先选择一个类。")
            return

        is_module_level = current_cls == module_label

        attr_kind: str | None = None
        if not is_module_level:
            # 选择属性类型：类属性 / 实例属性
            kind_raw = simpledialog.askstring("新建属性", "请输入属性类型（类/实例）：", parent=self)
            if not kind_raw:
                return
            kind_raw = kind_raw.strip()
            if kind_raw in ("类", "class", "cls"):
                attr_kind = "class_attr"
            elif kind_raw in ("实例", "instance", "self"):
                attr_kind = "instance_attr"
            else:
                messagebox.showwarning("新建属性", "属性类型仅支持：类 / 实例。")
                return

        attr_name = simpledialog.askstring("新建属性", "请输入属性名：", parent=self)
        if not attr_name:
            return
        attr_name = attr_name.strip()
        if not attr_name:
            return

        init_text = simpledialog.askstring("新建属性", "请输入初始值（可留空，按字符串处理）：", parent=self)
        if init_text is None:
            return

        # 尝试用 JSON 解析基础类型（数字/布尔等），失败则按原始字符串保存
        init_value: Any
        if init_text == "":
            init_value = None
        else:
            try:
                init_value = json.loads(init_text)
            except Exception:
                init_value = init_text

        local_module = self.module_defs_template.get("local_module") or {}
        defs = local_module.get("definitions") or {}

        if is_module_level:
            # 模块级特殊类：将属性视为全局变量，写入 attributes
            attrs = defs.get("attributes")
            if not isinstance(attrs, dict):
                attrs = {}
                defs["attributes"] = attrs

            mod_name = getattr(self.exec_ctx, "module_name", "<current>")
            attrs[attr_name] = {
                "name": attr_name,
                "kind": "global_attr",
                "init_value": init_value,
                "from_module": mod_name,
            }
        else:
            inner = defs.get("inner_classes")
            if not isinstance(inner, dict) or current_cls not in inner:
                messagebox.showwarning("新建属性", "当前类不存在于模块定义中。")
                return

            cls_obj = inner.get(current_cls) or {}
            attrs = cls_obj.get("attributes")
            if not isinstance(attrs, dict):
                attrs = {}
                cls_obj["attributes"] = attrs

            attrs[attr_name] = {
                "name": attr_name,
                "kind": attr_kind,
                "init_value": init_value,
            }

            inner[current_cls] = cls_obj
            defs["inner_classes"] = inner

        local_module["definitions"] = defs
        self.module_defs_template["local_module"] = local_module

        self._refresh_module_defs_preview()

    def _on_new_class_method_clicked(self) -> None:
        """为当前选中类新建方法（类方法或实例方法）。"""

        if self.module_defs_template is None:
            self._init_module_defs_template()

        module_label = "[模块级]"

        current_cls = self.local_class_var.get() if isinstance(self.local_class_var, tk.StringVar) else ""
        if not current_cls:
            messagebox.showinfo("新建方法", "请先选择一个类。")
            return

        is_module_level = current_cls == module_label

        if not is_module_level:
            kind_raw = simpledialog.askstring("新建方法", "请输入方法类型（类/实例）：", parent=self)
            if not kind_raw:
                return
            kind_raw = kind_raw.strip()
            if kind_raw in ("类", "class", "cls"):
                method_kind = "class_method"
                params = ["cls"]
            elif kind_raw in ("实例", "instance", "self"):
                method_kind = "instance_method"
                params = ["self"]
            else:
                messagebox.showwarning("新建方法", "方法类型仅支持：类 / 实例。")
                return

        method_name = simpledialog.askstring("新建方法", "请输入方法名：", parent=self)
        if not method_name:
            return
        method_name = method_name.strip()
        if not method_name:
            return

        local_module = self.module_defs_template.get("local_module") or {}
        defs = local_module.get("definitions") or {}

        if is_module_level:
            # 模块级特殊类：将方法视为全局函数，写入 methods
            methods = defs.get("methods")
            if not isinstance(methods, dict):
                methods = {}
                defs["methods"] = methods

            mod_name = getattr(self.exec_ctx, "module_name", "<current>")
            methods[method_name] = {
                "name": method_name,
                "kind": "function",
                "params": [],
                "body": "pass",
                "from_module": mod_name,
            }
        else:
            inner = defs.get("inner_classes")
            if not isinstance(inner, dict) or current_cls not in inner:
                messagebox.showwarning("新建方法", "当前类不存在于模块定义中。")
                return

            cls_obj = inner.get(current_cls) or {}
            methods = cls_obj.get("methods")
            if not isinstance(methods, dict):
                methods = {}
                cls_obj["methods"] = methods

            methods[method_name] = {
                "name": method_name,
                "kind": method_kind,
                "params": params,
                "body": "pass",
            }

            inner[current_cls] = cls_obj
            defs["inner_classes"] = inner

        local_module["definitions"] = defs
        self.module_defs_template["local_module"] = local_module

        self._refresh_module_defs_preview()

    def _add_module_method_from_defs(self) -> None:
        """将定义区当前选中的全局函数，添加为 local_module.definitions.methods 的一项。"""

        if self.module_defs_template is None:
            self._init_module_defs_template()

        kind, name = self._get_defs_tree_selection_kind_name()
        if kind != "function" or not name:
            return

        local_module = self.module_defs_template.get("local_module") or {}
        defs = local_module.get("definitions") or {}
        methods = defs.get("methods")
        if not isinstance(methods, dict):
            methods = {}
            defs["methods"] = methods

        mod_name = getattr(self.exec_ctx, "module_name", "<current>")
        methods[name] = {
            "name": name,
            "from_module": mod_name,
        }

        local_module["definitions"] = defs
        self.module_defs_template["local_module"] = local_module
        self._refresh_module_defs_preview()

    # -------------------- 执行区 --------------------
    def _build_exec_tab(self) -> None:
        frame = self.exec_tab
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(5, weight=1)

        ttk.Label(frame, text="选择执行入口：").grid(
            row=0, column=0, sticky="w", padx=5, pady=(5, 2)
        )

        self.exec_entry_var = tk.StringVar(value="foo")
        choices: list[str] = []
        for cls in self.exec_ctx.classes:
            for stmt in cls.body:
                if isinstance(stmt, ast.FunctionDef):
                    choices.append(f"{cls.name}.{stmt.name}")
        for fn in self.exec_ctx.functions:
            choices.append(fn.name)

        cb = ttk.Combobox(frame, textvariable=self.exec_entry_var, values=choices, state="readonly")
        cb.grid(row=1, column=0, sticky="w", padx=5, pady=(0, 5))
        cb.bind("<<ComboboxSelected>>", lambda _e: self._refresh_exec_param_form())
        self.exec_entry_cb = cb

        # 执行模式：直接 Python 调用 vs AST 驱动执行
        mode_frame = ttk.Frame(frame)
        mode_frame.grid(row=2, column=0, sticky="w", padx=5, pady=(0, 5))
        ttk.Label(mode_frame, text="执行模式：").pack(side=tk.LEFT)
        self.exec_mode_var = tk.StringVar(value="python")
        ttk.Radiobutton(
            mode_frame,
            text="Python",
            value="python",
            variable=self.exec_mode_var,
        ).pack(side=tk.LEFT, padx=(4, 0))
        ttk.Radiobutton(
            mode_frame,
            text="AST",
            value="ast",
            variable=self.exec_mode_var,
        ).pack(side=tk.LEFT, padx=(4, 0))

        # 参数输入区
        self.params_frame = ttk.Frame(frame)
        self.params_frame.grid(row=3, column=0, sticky="ew", padx=5, pady=5)
        self.params_frame.columnconfigure(1, weight=1)

        # 运行 & JSON 回放 按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=4, column=0, sticky="ew", padx=5, pady=(0, 5))
        btn_frame.columnconfigure(0, weight=1)

        playback_btn = ttk.Button(
            btn_frame,
            text="从 JSON 快照回放...",
            command=self._playback_from_json,
        )
        playback_btn.grid(row=0, column=0, sticky="w")

        run_btn = ttk.Button(btn_frame, text="执行", command=self._run_example)
        run_btn.grid(row=0, column=1, sticky="e")

        # 执行结果输出区（支持滚轮，随 Notebook 面板一起伸缩）
        self.exec_output = tk.Text(frame, wrap="none", font=("Consolas", 10))
        self.exec_output.grid(row=5, column=0, sticky="nsew", padx=5, pady=5)

        self._refresh_exec_param_form()

    def _render_execution_timeline(self, execution_space: Dict[str, Any]) -> None:
        canvas = getattr(self, "exec_timeline_canvas", None)
        if canvas is None or not isinstance(canvas, tk.Canvas):
            return

        # 记录根执行空间，便于交互后重新渲染
        self._timeline_root_space = execution_space
        self._timeline_hit_regions = []

        try:
            canvas.delete("all")
        except tk.TclError:
            return

        steps = execution_space.get("exec_queue") or []
        if not isinstance(steps, list):
            return

        box_width = 140
        box_height = 40
        margin_x = 10
        margin_y = 10
        spacing = 20
        child_offset_y = box_height + 10
        branch_row_spacing = 4

        expanded_paths: set[str] = getattr(self, "_timeline_expanded_paths", set())
        selected_path: str | None = getattr(self, "_timeline_selected_path", None)
        layout_mode: str = getattr(self, "branch_layout_mode", "below")
        snapshot_mode: str = getattr(self, "branch_snapshot_mode", "taken_only")

        def compute_step_width(step: dict[str, Any], path: tuple[int, ...]) -> int:
            """根据当前展开状态递归计算某个 step 子树所需的总宽度。

            规则：
            - 条件控制型 step（存在 branches）时：
              - 仅考虑已展开分支（branch_path 在 expanded_paths 中）的内部执行空间宽度；
              - 每个已展开分支体宽度 = 其 exec_queue 子树宽度的水平累加；
              - 父 step 宽度 = max(box_width, 所有已展开分支体宽度的最大值)。
            - 其它 step：若有线性子执行空间且展开，则为所有子节点子树宽度累加；否则为 box_width。
            """

            path_key = "-".join(str(i) for i in path)

            # 1) 条件控制型：优先考虑 branches
            branches = step.get("branches")
            if isinstance(branches, list) and branches:
                if path_key not in expanded_paths:
                    # 有分支但未展开时，用基础宽度
                    return box_width

                if layout_mode == "below":
                    max_branch_width = box_width
                    for b_idx, branch in enumerate(branches):
                        if not isinstance(branch, dict):
                            continue

                        branch_path = path + (b_idx,)
                        branch_path_key = "-".join(str(i) for i in branch_path)

                        child_steps = branch.get("exec_queue") or []
                        if not isinstance(child_steps, list) or not child_steps:
                            continue

                        # 仅对“将会渲染子单元”的分支体计算宽度
                        if branch_path_key not in expanded_paths:
                            continue

                        if snapshot_mode == "taken_only" and not branch.get("taken"):
                            continue

                        total = 0
                        first = True
                        for c_idx, child in enumerate(child_steps):
                            if not isinstance(child, dict):
                                continue
                            child_path = branch_path + (c_idx,)
                            w = compute_step_width(child, child_path)
                            if not first:
                                total += spacing
                            total += w
                            first = False

                        if total > max_branch_width:
                            max_branch_width = total

                    return max_branch_width

                # right 模式：分支体在分支头右侧展开，每行宽度=分支头宽度+间距+分支体宽度
                max_line_width = box_width
                for b_idx, branch in enumerate(branches):
                    if not isinstance(branch, dict):
                        continue

                    branch_path = path + (b_idx,)
                    branch_path_key = "-".join(str(i) for i in branch_path)

                    child_steps = branch.get("exec_queue") or []
                    if not isinstance(child_steps, list) or not child_steps:
                        continue

                    if branch_path_key not in expanded_paths:
                        continue

                    if snapshot_mode == "taken_only" and not branch.get("taken"):
                        continue

                    body_total = 0
                    first = True
                    for c_idx, child in enumerate(child_steps):
                        if not isinstance(child, dict):
                            continue
                        child_path = branch_path + (c_idx,)
                        w = compute_step_width(child, child_path)
                        if not first:
                            body_total += spacing
                        body_total += w
                        first = False

                    line_width = box_width + (spacing if body_total > 0 else 0) + body_total
                    if line_width > max_line_width:
                        max_line_width = line_width

                return max_line_width

            # 2) 普通线性子执行空间：inner_execution_zone / 自身 exec_queue
            inner_steps: list[dict[str, Any]] = []
            inner_zone = step.get("inner_execution_zone")
            if isinstance(inner_zone, dict):
                tmp = inner_zone.get("exec_queue") or []
                if isinstance(tmp, list):
                    inner_steps = tmp
            elif isinstance(step.get("exec_queue"), list):
                inner_steps = step["exec_queue"]

            if not inner_steps or path_key not in expanded_paths:
                return box_width

            total_width = 0
            first = True
            for idx, child in enumerate(inner_steps):
                if not isinstance(child, dict):
                    continue
                child_path = path + (idx,)
                child_width = compute_step_width(child, child_path)
                if not first:
                    total_width += spacing
                total_width += child_width
                first = False

            if total_width <= 0:
                return box_width
            return max(box_width, total_width)

        def render_level(
            steps_list: list[dict[str, Any]],
            base_x: int,
            base_y: int,
            path_prefix: tuple[int, ...],
        ) -> int:
            """递归渲染一个 exec_queue 层级，返回本层结束后的 x 坐标。"""

            current_x = base_x
            for local_idx, step in enumerate(steps_list):
                if not isinstance(step, dict):
                    continue

                path = path_prefix + (local_idx,)
                path_key = "-".join(str(i) for i in path)

                # 计算该节点在当前展开状态下的整体子树宽度
                width = compute_step_width(step, path)

                # 线性子执行空间（用于调用链等）
                inner_steps: list[dict[str, Any]] = []
                inner_zone = step.get("inner_execution_zone")
                if isinstance(inner_zone, dict):
                    tmp = inner_zone.get("exec_queue") or []
                    if isinstance(tmp, list):
                        inner_steps = tmp
                elif isinstance(step.get("exec_queue"), list):
                    inner_steps = step["exec_queue"]

                # 条件控制型：存在 branches 时，线性子执行空间由每个 branch.execution_space 承担
                branches = step.get("branches")
                has_branches = isinstance(branches, list) and len(branches) > 0
                is_branch_control = has_branches

                has_children = bool(inner_steps) and not is_branch_control
                is_expanded = has_children and (path_key in expanded_paths)

                x0 = current_x
                y0 = base_y
                x1 = x0 + width
                y1 = y0 + box_height

                # 选中态样式
                if selected_path is not None and selected_path == path_key:
                    outline_color = "#0066cc"
                    fill_color = "#cce5ff"
                else:
                    outline_color = "#444444"
                    fill_color = "#e0f0ff"

                try:
                    canvas.create_rectangle(x0, y0, x1, y1, outline=outline_color, fill=fill_color)

                    kind = step.get("kind") or ""
                    code = step.get("code") or ""
                    label = f"{local_idx + 1}: {kind}" if kind else f"{local_idx + 1}"
                    if code:
                        label = f"{label}\n{code}"

                    canvas.create_text(
                        (x0 + x1) / 2,
                        (y0 + y1) / 2,
                        text=label,
                        font=("Consolas", 9),
                    )

                    # 记录当前 step 的点击区域
                    self._timeline_hit_regions.append({
                        "path": path_key,
                        "x0": x0,
                        "y0": y0,
                        "x1": x1,
                        "y1": y1,
                    })

                    # 1) 条件控制型：展开时，根据布局模式在父盒子下方按行绘制各分支头部，
                    #    并在分支头下方或右方展开分支体内部 exec_queue。
                    if is_branch_control and has_branches and (path_key in expanded_paths):
                        assert isinstance(branches, list)

                        if layout_mode == "below":
                            # below 模式：每个分支独占一段垂直空间：
                            # - 收缩时：仅分支头占一行；
                            # - 展开时：分支头 + 子单元占两行；
                            # 分支头宽度统一为已展开分支体中最宽者。

                            # 先扫描一次，计算所有已展开分支体的最大宽度
                            branch_heads_width = box_width
                            for b_idx, branch in enumerate(branches):
                                if not isinstance(branch, dict):
                                    continue

                                branch_path = path + (b_idx,)
                                branch_path_key = "-".join(str(i) for i in branch_path)

                                exec_space = branch.get("execution_space")
                                if not isinstance(exec_space, dict):
                                    continue
                                child_steps = exec_space.get("exec_queue") or []
                                if not isinstance(child_steps, list) or not child_steps:
                                    continue

                                if branch_path_key not in expanded_paths:
                                    continue

                                total = 0
                                first = True
                                for c_idx, child in enumerate(child_steps):
                                    if not isinstance(child, dict):
                                        continue
                                    child_path = branch_path + (c_idx,)
                                    w = compute_step_width(child, child_path)
                                    if not first:
                                        total += spacing
                                    total += w
                                    first = False

                                if total > branch_heads_width:
                                    branch_heads_width = total

                            # 再按顺序逐个分支绘制，并根据展开状态累积纵向偏移，
                            # 保证某个分支展开时会把其后的分支整体向下推。
                            current_branch_y = y0 + box_height + branch_row_spacing

                            for b_idx, branch in enumerate(branches):
                                if not isinstance(branch, dict):
                                    continue

                                branch_path = path + (b_idx,)
                                branch_path_key = "-".join(str(i) for i in branch_path)

                                branch_y0 = current_branch_y
                                branch_x0 = x0
                                branch_x1 = branch_x0 + branch_heads_width
                                branch_y1 = branch_y0 + box_height

                                label = branch.get("label") or "branch"
                                cond = branch.get("condition_expr") or ""
                                taken = bool(branch.get("taken"))

                                text_label = label if not cond else f"{label}: {cond}"
                                if taken:
                                    b_outline = "#006600"
                                    b_fill = "#ddffdd"
                                else:
                                    b_outline = "#888888"
                                    b_fill = "#f5f5f5"

                                canvas.create_rectangle(branch_x0, branch_y0, branch_x1, branch_y1, outline=b_outline, fill=b_fill)
                                canvas.create_text(
                                    (branch_x0 + branch_x1) / 2,
                                    (branch_y0 + branch_y1) / 2,
                                    text=text_label,
                                    font=("Consolas", 8),
                                )

                                # 分支头部点击区域
                                self._timeline_hit_regions.append({
                                    "path": branch_path_key,
                                    "x0": branch_x0,
                                    "y0": branch_y0,
                                    "x1": branch_x1,
                                    "y1": branch_y1,
                                })

                                # 若该分支本身被展开，则在该行下方绘制其 execution_space.exec_queue
                                child_steps: list[dict[str, Any]] = []
                                tmp = branch.get("exec_queue") or []
                                if isinstance(tmp, list):
                                    child_steps = tmp

                                branch_block_height = box_height

                                can_show_children = bool(child_steps) and (branch_path_key in expanded_paths)
                                if snapshot_mode == "taken_only" and not branch.get("taken"):
                                    can_show_children = False

                                if can_show_children:
                                    child_y0 = branch_y0 + child_offset_y
                                    try:
                                        render_level(child_steps, branch_x0, child_y0, branch_path)
                                    except tk.TclError:
                                        break
                                    # 头 + 子单元占两行：高度约为 box_height + child_offset_y
                                    branch_block_height = child_offset_y + box_height

                                # 下一条分支的起始 y：当前分支块底部再加一个间隔
                                current_branch_y = branch_y0 + branch_block_height + branch_row_spacing
                        else:
                            # right 模式：分支体在分支头右侧一行展开，分支头宽度固定为 box_width。
                            for b_idx, branch in enumerate(branches):
                                if not isinstance(branch, dict):
                                    continue

                                branch_path = path + (b_idx,)
                                branch_path_key = "-".join(str(i) for i in branch_path)

                                branch_y0 = y0 + (b_idx + 1) * (box_height + branch_row_spacing)
                                branch_x0 = x0
                                branch_x1 = branch_x0 + box_width
                                branch_y1 = branch_y0 + box_height

                                label = branch.get("label") or "branch"
                                cond = branch.get("condition_expr") or ""
                                taken = bool(branch.get("taken"))

                                text_label = label if not cond else f"{label}: {cond}"
                                if taken:
                                    b_outline = "#006600"
                                    b_fill = "#ddffdd"
                                else:
                                    b_outline = "#888888"
                                    b_fill = "#f5f5f5"

                                canvas.create_rectangle(branch_x0, branch_y0, branch_x1, branch_y1, outline=b_outline, fill=b_fill)
                                canvas.create_text(
                                    (branch_x0 + branch_x1) / 2,
                                    (branch_y0 + branch_y1) / 2,
                                    text=text_label,
                                    font=("Consolas", 8),
                                )

                                # 分支头部点击区域
                                self._timeline_hit_regions.append({
                                    "path": branch_path_key,
                                    "x0": branch_x0,
                                    "y0": branch_y0,
                                    "x1": branch_x1,
                                    "y1": branch_y1,
                                })

                                # 若该分支本身被展开，则在该行右侧绘制其 execution_space.exec_queue
                                child_steps: list[dict[str, Any]] = []
                                tmp = branch.get("exec_queue") or []
                                if isinstance(tmp, list):
                                    child_steps = tmp

                                can_show_children = bool(child_steps) and (branch_path_key in expanded_paths)
                                if snapshot_mode == "taken_only" and not branch.get("taken"):
                                    can_show_children = False

                                if can_show_children:
                                    children_base_x = branch_x0 + box_width + spacing
                                    try:
                                        render_level(child_steps, children_base_x, branch_y0, branch_path)
                                    except tk.TclError:
                                        break

                    # 2) 普通线性子执行空间：在下一行递归绘制子执行单元
                    elif is_expanded and has_children:
                        child_y0 = y0 + child_offset_y
                        try:
                            render_level(inner_steps, x0, child_y0, path)
                        except tk.TclError:
                            break

                except tk.TclError:
                    break

                current_x = x1 + spacing

            return current_x

        try:
            render_level(steps, margin_x, margin_y, tuple())
        except tk.TclError:
            return

    # Canvas 点击：选中执行单元
    def _on_timeline_click(self, event: tk.Event) -> None:  # type: ignore[type-arg]
        if not self._timeline_root_space or not self._timeline_hit_regions:
            return

        x = event.x
        y = event.y
        hit_path: str | None = None
        for region in self._timeline_hit_regions:
            if region["x0"] <= x <= region["x1"] and region["y0"] <= y <= region["y1"]:
                hit_path = str(region.get("path"))
                break

        if hit_path is None:
            return

        self._timeline_selected_path = hit_path
        self._update_step_detail()
        try:
            self._render_execution_timeline(self._timeline_root_space)
        except Exception:
            pass

    # Canvas 双击：展开 / 折叠执行单元
    def _on_timeline_double_click(self, event: tk.Event) -> None:  # type: ignore[type-arg]
        if not self._timeline_root_space or not self._timeline_hit_regions:
            return

        x = event.x
        y = event.y
        hit_path: str | None = None
        for region in self._timeline_hit_regions:
            if region["x0"] <= x <= region["x1"] and region["y0"] <= y <= region["y1"]:
                hit_path = str(region.get("path"))
                break

        if hit_path is None:
            return

        # 通用路径下钻：支持三类节点类型 space/step/branch
        parts = [int(p) for p in hit_path.split("-") if p != ""]
        if not parts:
            return

        root_space = self._timeline_root_space
        if not isinstance(root_space, dict):
            return

        node: dict[str, Any] | dict | None
        node_type: str = "space"  # "space" | "step" | "branch"

        # 获取当前节点的子列表及子节点类型
        def _get_children(cur_node: dict[str, Any] | dict, cur_type: str) -> tuple[list[dict[str, Any]], str]:
            if cur_type == "space":
                steps = cur_node.get("exec_queue") or []  # type: ignore[union-attr]
                return (steps if isinstance(steps, list) else []), "step"

            if cur_type == "step":
                branches = cur_node.get("branches", [])
                if isinstance(branches, list) and branches:
                    return branches, "branch"

                inner_steps: list[dict[str, Any]] = []
                inner_zone = cur_node.get("inner_execution_zone")
                if isinstance(inner_zone, dict):
                    tmp = inner_zone.get("exec_queue") or []
                    if isinstance(tmp, list):
                        inner_steps = tmp
                elif isinstance(cur_node.get("exec_queue"), list):
                    inner_steps = cur_node["exec_queue"]
                return inner_steps, "step"

            if cur_type == "branch":
                steps = cur_node.get("exec_queue") or []
                return (steps if isinstance(steps, list) else []), "step"

            return [], cur_type

        # 初始从根 execution_space 出发
        current_node: dict[str, Any] | dict = root_space
        current_type: str = "space"
        children, child_type = _get_children(current_node, current_type)

        for depth, idx in enumerate(parts):
            if not children or idx < 0 or idx >= len(children):
                return
            current_node = children[idx]
            if not isinstance(current_node, dict):
                return
            current_type = child_type
            if depth < len(parts) - 1:
                children, child_type = _get_children(current_node, current_type)

        # current_node 即为被双击的节点，获取其子节点来决定能否展开
        children, _ = _get_children(current_node, current_type)
        if not children:
            return

        expanded_paths: set[str] = getattr(self, "_timeline_expanded_paths", set())
        if hit_path in expanded_paths:
            expanded_paths.remove(hit_path)
        else:
            expanded_paths.add(hit_path)
        self._timeline_expanded_paths = expanded_paths

        # 双击也更新当前选中路径和详情
        self._timeline_selected_path = hit_path
        self._update_step_detail()

        try:
            self._render_execution_timeline(self._timeline_root_space)
        except Exception:
            pass

    def _update_step_detail(self) -> None:
        """根据 _timeline_selected_path 在侧边栏展示当前 Step 的关键字段。"""

        text = getattr(self, "step_detail_text", None)
        space = self._timeline_root_space
        path_key: str | None = getattr(self, "_timeline_selected_path", None)

        if text is None:
            return

        text.configure(state="normal")
        text.delete("1.0", tk.END)

        if not space or not path_key:
            text.configure(state="disabled")
            return

        # 通用路径下钻：支持 space/step/branch 三种节点类型
        if not isinstance(space, dict):
            text.configure(state="disabled")
            return

        parts = [int(p) for p in path_key.split("-") if p != ""]
        if not parts:
            text.configure(state="disabled")
            return

        node: dict[str, Any] | dict = space
        node_type: str = "space"  # "space" | "step" | "branch"

        def _get_children(cur_node: dict[str, Any] | dict, cur_type: str) -> tuple[list[dict[str, Any]], str]:
            if cur_type == "space":
                steps = cur_node.get("exec_queue") or []  # type: ignore[union-attr]
                return (steps if isinstance(steps, list) else []), "step"

            if cur_type == "step":
                branches = cur_node.get("branches", [])
                if isinstance(branches, list) and branches:
                    return branches, "branch"

                inner_steps: list[dict[str, Any]] = []
                inner_zone = cur_node.get("inner_execution_zone")
                if isinstance(inner_zone, dict):
                    tmp = inner_zone.get("exec_queue") or []
                    if isinstance(tmp, list):
                        inner_steps = tmp
                elif isinstance(cur_node.get("exec_queue"), list):
                    inner_steps = cur_node["exec_queue"]
                return inner_steps, "step"

            if cur_type == "branch":
                steps = cur_node.get("exec_queue") or []
                return (steps if isinstance(steps, list) else []), "step"

            return [], cur_type

        children, child_type = _get_children(node, node_type)
        for depth, idx in enumerate(parts):
            if not children or idx < 0 or idx >= len(children):
                text.configure(state="disabled")
                return
            candidate = children[idx]
            if not isinstance(candidate, dict):
                text.configure(state="disabled")
                return
            node = candidate
            node_type = child_type
            if depth < len(parts) - 1:
                children, child_type = _get_children(node, node_type)

        # 根据最终节点类型决定展示内容
        lines: list[str] = []
        lines.append(f"path: {path_key}")

        if node_type == "branch":
            label = node.get("label")
            cond_expr = node.get("condition_expr")
            cond_value = node.get("condition_value")
            taken = node.get("taken")

            lines.append("type: branch")
            if label is not None:
                lines.append(f"label: {label}")
            if cond_expr is not None:
                lines.append(f"condition_expr: {cond_expr}")
            if cond_value is not None:
                lines.append(f"condition_value: {cond_value}")
            lines.append(f"taken: {bool(taken)}")
            # 分支体内部的执行单元现在直接通过 branch.exec_queue 表达
            child_steps = node.get("exec_queue") or []
            if isinstance(child_steps, list) and child_steps:
                first_scope_in = child_steps[0].get("scope_in") or {}
                last_scope_out = child_steps[-1].get("scope_out") or {}
                lines.append("")
                lines.append(f"branch.exec_queue length: {len(child_steps)}")
                lines.append(f"first_step.scope_in keys: {sorted(first_scope_in.keys())}")
                lines.append(f"last_step.scope_out keys: {sorted(last_scope_out.keys())}")
            else:
                lines.append("")
                lines.append("branch.exec_queue: []")
        else:
            kind = node.get("kind")
            lineno = node.get("lineno")
            code = node.get("code")
            scope_in = node.get("scope_in") or {}
            scope_out = node.get("scope_out") or {}

            if kind is not None:
                lines.append(f"kind: {kind}")
            if lineno is not None:
                lines.append(f"lineno: {lineno}")
            if code is not None:
                lines.append("code:")
                lines.append(str(code))

            lines.append("")
            lines.append(f"scope_in keys: {sorted(scope_in.keys())}")
            lines.append(f"scope_out keys: {sorted(scope_out.keys())}")

        text.insert("1.0", "\n".join(lines))
        text.configure(state="disabled")

    def _playback_from_json(self) -> None:
        """从 runtime_samples 目录选择 JSON 快照并在执行区回放。

        仅基于 JSON 中已有的 execution_space / exec_queue 展示 scope_in/scope_out，
        不做重新执行，作为纯“时间线回放”视图。
        """

        base_dir = Path(__file__).resolve().parent
        default_dir = base_dir / "runtime_samples"

        path = filedialog.askopenfilename(
            title="选择 execution_space JSON 快照",
            initialdir=str(default_dir) if default_dir.exists() else str(base_dir),
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return

        try:
            text = Path(path).read_text(encoding="utf-8")
            data = json.loads(text)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("读取失败", f"无法读取或解析 JSON: {exc}")
            return

        space = data.get("execution_space")
        if not isinstance(space, dict):
            messagebox.showerror("结构错误", "JSON 中未找到 execution_space 字段或类型不正确。")
            return

        module_name = data.get("module_name")
        file_path = data.get("file_path")
        entry_name = data.get("entry")

        # 解析本模块定义信息（attributes / methods / inner_classes）
        defs = (
            data.get("local_module", {})
            .get("definitions", {})
        )
        # 新模型字段优先，兼容旧的 globals/functions/classes 快照
        attributes_defs = defs.get("attributes") or defs.get("globals") or {}
        methods_defs = defs.get("methods") or defs.get("functions") or {}
        inner_classes_defs = defs.get("inner_classes") or defs.get("classes") or {}
        module_def_name = defs.get("name") or module_name
        module_def_kind = defs.get("kind") or "module_class"

        self.exec_output.configure(state="normal")
        self.exec_output.delete("1.0", tk.END)

        def log(msg: str) -> None:
            line = msg.rstrip("\n") + "\n"
            self.exec_output.insert("end", line)

        log(f"[Replay] 文件: {file_path!r} 模块: {module_name!r} 入口: {entry_name!r}")

        # 本文件定义的 attributes / methods / inner_classes（从 JSON local_module.definitions 解析）
        log("[Replay] 本模块定义（from local_module.definitions）：")
        log(f"  module_def.name = {module_def_name!r}, kind = {module_def_kind!r}")

        if attributes_defs:
            log("  attributes:")
            for name, info in attributes_defs.items():
                ln = info.get("lineno")
                log(f"    - {name} (L{ln})")
        else:
            log("  attributes: (无)")

        if methods_defs:
            log("  methods:")
            for name, info in methods_defs.items():
                ln = info.get("lineno")
                log(f"    - {name} (L{ln})")
        else:
            log("  methods: (无)")

        if inner_classes_defs:
            log("  inner_classes:")
            for cls_name, info in inner_classes_defs.items():
                ln = info.get("lineno")
                kind = info.get("kind")
                if kind is not None:
                    log(f"    - {cls_name} (kind={kind!r}, L{ln})")
                else:
                    log(f"    - {cls_name} (L{ln})")

                # 类属性
                class_attrs = info.get("class_attributes") or {}
                if class_attrs:
                    log("      class_attributes:")
                    for a_name, a_info in class_attrs.items():
                        a_ln = a_info.get("lineno")
                        log(f"        · {a_name} (L{a_ln})")

                # 实例属性规范（静态推断）
                inst_attrs = info.get("instance_attributes") or {}
                if inst_attrs:
                    log("      instance_attributes:")
                    for a_name, a_info in inst_attrs.items():
                        a_ln = a_info.get("first_lineno")
                        defined_in = a_info.get("defined_in")
                        log(f"        · {a_name} (defined_in={defined_in!r}, L{a_ln})")

                # 实例方法 / 类方法 / 静态方法（兼容旧字段 methods）
                inst_methods = info.get("instance_methods") or info.get("methods") or {}
                class_methods = info.get("class_methods") or {}
                static_methods = info.get("static_methods") or {}

                if inst_methods:
                    log("      instance_methods:")
                    for m_name, m_info in inst_methods.items():
                        m_ln = m_info.get("lineno")
                        log(f"        · {m_name} (L{m_ln})")

                if class_methods:
                    log("      class_methods:")
                    for m_name, m_info in class_methods.items():
                        m_ln = m_info.get("lineno")
                        log(f"        · {m_name} (L{m_ln})")

                if static_methods:
                    log("      static_methods:")
                    for m_name, m_info in static_methods.items():
                        m_ln = m_info.get("lineno")
                        log(f"        · {m_name} (L{m_ln})")
        else:
            log("  inner_classes: (无)")

        # 实例对象池：instance_pool
        instance_pool = data.get("instance_pool") or {}
        if isinstance(instance_pool, dict) and instance_pool:
            log("")
            log("[Replay] instance_pool：")
            for obj_id, obj_info in instance_pool.items():
                cls_name = obj_info.get("class_name")
                mod_name = obj_info.get("module_name")
                log(f"  - {obj_id}: class={cls_name!r}, module={mod_name!r}")
                attrs = obj_info.get("attrs") or {}
                if attrs:
                    log("      attrs:")
                    for k, v in attrs.items():
                        log(f"        · {k} = {v!r}")

        log("")
        log("[Replay] 顶层 execution_space:")
        log(f"  scope_level: {space.get('scope_level')!r}")
        log(f"  scope_in:  {space.get('scope_in')!r}")
        log(f"  scope_out: {space.get('scope_out')!r}")

        steps = space.get("exec_queue") or []
        if not isinstance(steps, list):
            log("[Replay] exec_queue 不是列表，无法展开步骤。")
        else:
            log("[Replay] ---- exec_queue steps ----")
            for idx, step in enumerate(steps, start=1):
                if not isinstance(step, dict):
                    log(f"[Replay] step {idx}: 非 dict，跳过。")
                    continue
                lineno = step.get("lineno")
                code_repr = step.get("code")
                log(f"[Replay] step {idx}: L{lineno} {code_repr}")
                log(f"           scope_in:  {step.get('scope_in')!r}")
                log(f"           scope_out: {step.get('scope_out')!r}")

        try:
            self._render_execution_timeline(space)
        except Exception:
            pass

        self.exec_output.configure(state="disabled")

    def _resolve_exec_entry_def(
        self,
    ) -> tuple[Optional[ast.FunctionDef], bool, Optional[str], Optional[str]]:
        """根据 exec_entry_var 解析为 AST FunctionDef，并标记是否为方法。"""

        entry_name = self.exec_entry_var.get()
        if not entry_name:
            return None, False, None, None

        if "." in entry_name:
            cls_name, meth_name = entry_name.split(".", 1)
            for cls in self.exec_ctx.classes:
                if cls.name == cls_name:
                    for stmt in cls.body:
                        if isinstance(stmt, ast.FunctionDef) and stmt.name == meth_name:
                            return stmt, True, cls_name, meth_name
            return None, True, cls_name, meth_name

        for fn in self.exec_ctx.functions:
            if fn.name == entry_name:
                return fn, False, None, entry_name
        return None, False, None, entry_name

    # -------------------- 执行结果 JSON 快照 --------------------
    def _save_execution_zone_json(
        self,
        entry_name: str,
        zone: Dict[str, Any],
        return_value: Any,
        *,
        tree: Optional[ast.AST] = None,
        functions: Optional[List[ast.FunctionDef]] = None,
        classes: Optional[List[ast.ClassDef]] = None,
        module_name: Optional[str] = None,
        file_path: Optional[str] = None,
    ) -> None:
        """将一次 AST 执行得到的 execution_zone 快照写入 JSON 文件。

        文件输出目录：与本脚本同级的 runtime_samples 目录。
        文件名格式：execution_<entry_name>_<timestamp>.json
        """

        try:
            base_dir = Path(__file__).resolve().parent
            out_dir = base_dir / "runtime_samples"
            out_dir.mkdir(parents=True, exist_ok=True)

            from datetime import datetime  # 局部导入，避免打断顶部结构

            ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            out_path = out_dir / f"execution_{entry_name}_{ts}.json"

            # 基于给定 AST（默认为当前示例）构建局部的 ModuleDefinitionsObject 视图
            if tree is None:
                tree = self.ctx.tree
            if functions is None:
                functions = self.ctx.functions
            if classes is None:
                classes = self.ctx.classes
            globals_defs: Dict[str, Any] = {}
            functions_defs: Dict[str, Any] = {}
            classes_defs: Dict[str, Any] = {}

            # imported_modules: 基于 Import / ImportFrom 的最小 ImportedModuleObject 视图
            imported_modules: Dict[str, Any] = {}
            try:
                for node in ast.walk(tree):  # type: ignore[arg-type]
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            key = alias.asname or alias.name
                            if key in imported_modules:
                                continue
                            imported_modules[key] = {
                                "original_module_name": alias.name,
                                # 暂不解析真实文件路径，先占位，后续与 project_deps / sys.modules 对齐
                                "file_path": None,
                                "definitions": {
                                    "name": alias.name,
                                    "kind": "module_class",
                                    "attributes": {},
                                    "methods": {},
                                    "inner_classes": {},
                                },
                            }
                    elif isinstance(node, ast.ImportFrom):
                        module_name = node.module or ""
                        for alias in node.names:
                            key = alias.asname or alias.name
                            if key in imported_modules:
                                continue
                            original = f"{module_name}.{alias.name}" if module_name else alias.name
                            imported_modules[key] = {
                                "original_module_name": original,
                                "file_path": None,
                                "definitions": {
                                    "name": original,
                                    "kind": "module_class",
                                    "attributes": {},
                                    "methods": {},
                                    "inner_classes": {},
                                },
                            }
            except Exception:
                # 分析失败时，宁可留空也不要影响主流程
                imported_modules = {}

            # 模块级全局变量（简单处理 Assign 到 Name 的情况）
            for node in getattr(tree, "body", []):  # type: ignore[union-attr]
                if isinstance(node, ast.Assign):
                    for tgt in node.targets:
                        if isinstance(tgt, ast.Name):
                            globals_defs[tgt.id] = {
                                "name": tgt.id,
                                "lineno": getattr(node, "lineno", None),
                            }

            # 顶层函数定义
            for fn in functions or []:
                functions_defs[fn.name] = {
                    "name": fn.name,
                    "lineno": getattr(fn, "lineno", None),
                }

            # 顶层类定义 + 类方法三分类 + 预留实例属性结构
            for cls in classes or []:
                class_attrs: Dict[str, Any] = {}
                instance_attrs: Dict[str, Any] = {}
                instance_methods: Dict[str, Any] = {}
                class_methods: Dict[str, Any] = {}
                static_methods: Dict[str, Any] = {}

                # 简单判断装饰器名称
                def _has_decorator(fn: ast.FunctionDef, name: str) -> bool:
                    for dec in fn.decorator_list:
                        if isinstance(dec, ast.Name) and dec.id == name:
                            return True
                        if isinstance(dec, ast.Attribute) and dec.attr == name:
                            return True
                    return False

                # 第一次扫描：类体中的类属性 + 方法分类
                for stmt in cls.body:
                    # 类属性：class A: k = 1
                    if isinstance(stmt, (ast.Assign, ast.AnnAssign)):
                        targets: list[ast.expr] = []
                        if isinstance(stmt, ast.Assign):
                            targets = stmt.targets
                        elif isinstance(stmt, ast.AnnAssign) and stmt.target is not None:
                            targets = [stmt.target]
                        for tgt in targets:
                            if isinstance(tgt, ast.Name):
                                class_attrs[tgt.id] = {
                                    "name": tgt.id,
                                    "lineno": getattr(stmt, "lineno", None),
                                }
                    # 方法：按装饰器拆分为实例/类/静态方法
                    if isinstance(stmt, ast.FunctionDef):
                        info = {
                            "name": stmt.name,
                            "lineno": getattr(stmt, "lineno", None),
                        }
                        if _has_decorator(stmt, "classmethod"):
                            class_methods[stmt.name] = info
                        elif _has_decorator(stmt, "staticmethod"):
                            static_methods[stmt.name] = info
                        else:
                            instance_methods[stmt.name] = info

                # 第二次扫描：在实例方法里静态提取 self.xxx 作为实例属性规范
                for fn_name in list(instance_methods.keys()):
                    # 找到对应的 ast.FunctionDef
                    fn_node = None
                    for stmt in cls.body:
                        if isinstance(stmt, ast.FunctionDef) and stmt.name == fn_name:
                            fn_node = stmt
                            break
                    if fn_node is None:
                        continue

                    # 推断实例变量名（通常是第一个参数 self）
                    self_name = None
                    if fn_node.args.args:
                        self_name = fn_node.args.args[0].arg
                    if not self_name:
                        continue

                    for sub in ast.walk(fn_node):
                        if isinstance(sub, (ast.Assign, ast.AnnAssign)):
                            targets: list[ast.expr] = []
                            if isinstance(sub, ast.Assign):
                                targets = sub.targets
                            elif isinstance(sub, ast.AnnAssign) and sub.target is not None:
                                targets = [sub.target]
                            for tgt in targets:
                                # 只关心 self.xxx 形式
                                if (
                                    isinstance(tgt, ast.Attribute)
                                    and isinstance(tgt.value, ast.Name)
                                    and tgt.value.id == self_name
                                ):
                                    attr_name = tgt.attr
                                    # 只记录第一次出现的位置
                                    if attr_name not in instance_attrs:
                                        instance_attrs[attr_name] = {
                                            "name": attr_name,
                                            "first_lineno": getattr(sub, "lineno", None),
                                            "defined_in": fn_name,
                                        }

                classes_defs[cls.name] = {
                    "name": cls.name,
                    "kind": "inner_class",
                    "lineno": getattr(cls, "lineno", None),
                    "class_attributes": class_attrs,
                    "instance_attributes": instance_attrs,
                    "instance_methods": instance_methods,
                    "class_methods": class_methods,
                    "static_methods": static_methods,
                }

            mod_name = module_name or getattr(self.exec_ctx, "module_name", "example")
            fpath = file_path or getattr(self.exec_ctx, "file_path", "example.py")

            # ------------------------------------------------------------------
            # 根据 execution_zone 构建 instance_pool，并将其中的实例对象改写为句柄
            # 同时，将各级 scope_in/scope_out 中的绑定统一包装为 {kind, name, value}
            # ------------------------------------------------------------------

            instance_pool: Dict[str, Any] = {}
            pyid_to_oid: Dict[int, str] = {}
            class_counters: Dict[str, int] = {}

            def _wrap_scopes_in_place(obj: Any) -> None:
                """在 execution_zone 结构中，就地将 scope_in/scope_out 的条目包装为三元组。

                - 不改变 scope_in / scope_out 的键集合；
                - 若某个绑定的值已是 {kind, name, value} 形态，则保持不变；
                - 否则使用 _make_scope_binding(name, value) 包装。
                """

                if isinstance(obj, dict):
                    for key in ("scope_in", "scope_out"):
                        scope = obj.get(key)
                        if isinstance(scope, dict):
                            for name, val in list(scope.items()):
                                if (
                                    isinstance(val, dict)
                                    and "kind" in val
                                    and "name" in val
                                    and "value" in val
                                ):
                                    continue
                                scope[name] = self._make_scope_binding(name, val)
                    for val in obj.values():
                        if isinstance(val, (dict, list)):
                            _wrap_scopes_in_place(val)
                elif isinstance(obj, list):
                    for item in obj:
                        if isinstance(item, (dict, list)):
                            _wrap_scopes_in_place(item)

            def _encode_value(v: Any) -> Any:
                """将值编码为可 JSON 序列化形式，并收集实例对象到 instance_pool。

                规则：
                - dict / list 递归处理；
                - 对于有 __dict__ 的普通实例对象，分配 object_id，
                  在 instance_pool 中记录完整 attrs，在 execution_space 中仅保留句柄：
                  {"__object_id__": ..., "__class__": ...}。
                """

                # 容器类型递归
                if isinstance(v, dict):
                    return {k: _encode_value(val) for k, val in v.items()}
                if isinstance(v, list):
                    return [_encode_value(item) for item in v]

                # 跳过类型对象 / AST 节点等
                if isinstance(v, type) or isinstance(v, ast.AST):
                    return str(v)

                # 普通实例对象：通过 __dict__ 粗略判断
                if hasattr(v, "__dict__") and not isinstance(v, (str, bytes, int, float, bool, type(None))):
                    pyid = id(v)
                    if pyid in pyid_to_oid:
                        object_id = pyid_to_oid[pyid]
                    else:
                        cls = v.__class__
                        cls_name = getattr(cls, "__name__", v.__class__.__name__)
                        # 为同名类分配递增编号：A#1, A#2, ...
                        idx = class_counters.get(cls_name, 0) + 1
                        class_counters[cls_name] = idx
                        object_id = f"{cls_name}#{idx}"
                        pyid_to_oid[pyid] = object_id

                        # 收集实例当前属性快照（尽量保持可序列化，复杂值用 repr 占位）
                        attrs: Dict[str, Any] = {}
                        for name, value in getattr(v, "__dict__", {}).items():
                            if isinstance(value, (str, int, float, bool)) or value is None:
                                attrs[name] = value
                            elif isinstance(value, (list, dict)):
                                # 简单递归编码容器
                                attrs[name] = _encode_value(value)
                            else:
                                attrs[name] = repr(value)

                        instance_pool[object_id] = {
                            "object_id": object_id,
                            "class_name": getattr(cls, "__name__", "<unknown>"),
                            "module_name": getattr(cls, "__module__", mod_name),
                            "attrs": attrs,
                            "metadata": {},
                        }

                    return {"__object_id__": object_id, "__class__": v.__class__.__name__}

                # 其余保持原样（数字/字符串等）
                return v

            # 先在原始 execution_zone 上统一包装 scope_in/scope_out，
            # 再进行通用的值编码和 instance_pool 抽取。
            _wrap_scopes_in_place(zone)
            encoded_zone = _encode_value(zone)

            snapshot: Dict[str, Any] = {
                "module_name": mod_name,
                "file_path": fpath,
                "imported_modules": imported_modules,
                "local_module": {
                    "definitions": {
                        "name": mod_name,
                        "kind": "module_class",
                        "attributes": globals_defs,
                        "methods": functions_defs,
                        "inner_classes": classes_defs,
                    },
                },
                "instance_pool": instance_pool,
                "entry": entry_name,
                "execution_space": encoded_zone,
                "return_value": return_value,
            }

            out_path.write_text(
                json.dumps(snapshot, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            print(f"[ExecLog] execution_zone JSON 已写入: {out_path}")
        except Exception as exc:  # noqa: BLE001
            print(f"[ExecLog] 写入 execution_zone JSON 失败: {exc}")

    def _choose_exec_file(self) -> None:
        """选择一个外部 .py 文件作为执行/可视化源，并解析为 AST 上下文。

        解析后会更新：
        - self.exec_ctx: ExampleContext（source/tree/functions/classes）
        - 执行入口下拉框可选项
        - 参数输入表单
        - 源显示标签
        """

        path = filedialog.askopenfilename(
            title="选择 Python 文件",
            filetypes=[("Python files", "*.py"), ("All files", "*.*")],
        )
        if not path:
            return

        try:
            source = Path(path).read_text(encoding="utf-8")
        except OSError as exc:  # noqa: BLE001
            messagebox.showerror("读取失败", f"无法读取文件: {exc}")
            return

        try:
            tree = ast.parse(source, filename=path)
        except SyntaxError as exc:  # noqa: BLE001
            messagebox.showerror("语法错误", f"解析失败: {exc}")
            return

        # 为外部文件构建一个简单的 ExampleContext
        try:
            index = build_scope_index(tree, module_name=Path(path).stem)
        except Exception:  # noqa: BLE001
            index = self.ctx.scope_index

        funcs: List[ast.FunctionDef] = []
        classes: List[ast.ClassDef] = []
        for node in getattr(tree, "body", []):
            if isinstance(node, ast.FunctionDef):
                funcs.append(node)
            elif isinstance(node, ast.ClassDef):
                classes.append(node)

        self.exec_ctx = ExampleContext(
            source=source,
            tree=tree,  # type: ignore[arg-type]
            scope_index=index,
            functions=funcs,
            classes=classes,
            module_name=Path(path).stem,
            file_path=path,
        )

        # 更新源显示
        self.exec_source_var.set(path)

        # 基于新的 exec_ctx 重新构建入口函数列表（类方法 + 顶层函数）
        choices: list[str] = []
        for cls in self.exec_ctx.classes:
            for stmt in cls.body:
                if isinstance(stmt, ast.FunctionDef):
                    choices.append(f"{cls.name}.{stmt.name}")
        for fn in self.exec_ctx.functions:
            choices.append(fn.name)

        # 执行区入口下拉框
        self.exec_entry_cb["values"] = choices
        if choices:
            if self.exec_entry_var.get() not in choices:
                self.exec_entry_var.set(choices[0])
        else:
            self.exec_entry_var.set("")

        self._refresh_exec_param_form()

        # 调用区入口下拉框与视图刷新
        calls_cb = getattr(self, "calls_entry_cb", None)
        if isinstance(calls_cb, ttk.Combobox):
            calls_cb["values"] = choices
        if choices:
            if self.entry_var.get() not in choices:
                self.entry_var.set(choices[0])
        else:
            self.entry_var.set("")

        try:
            self._refresh_calls_view()
        except Exception:
            pass

        # 导入区 / 定义区 随当前源刷新
        try:
            self._refresh_imports_content()
        except Exception:
            pass
        try:
            self._refresh_defs_content()
        except Exception:
            pass

        # 选择新源后，若已有执行时间线，可以根据需要重新渲染
        try:
            if self._timeline_root_space:
                self._render_execution_timeline(self._timeline_root_space)
        except Exception:
            pass

    def _on_branch_snapshot_change(self, _event: tk.Event) -> None:  # type: ignore[type-arg]
        """切换分支快照策略，仅影响 UI 渲染时是否展开未命中分支的子单元。"""

        label = getattr(self, "branch_snapshot_var", None)
        if isinstance(label, tk.StringVar):
            value = label.get()
        else:
            value = "仅执行路径"

        if value == "全部分支":
            self.branch_snapshot_mode = "all"
        else:
            self.branch_snapshot_mode = "taken_only"

        # 切换后，若已有执行时间线，则重新渲染以反映开关效果
        try:
            if self._timeline_root_space:
                self._render_execution_timeline(self._timeline_root_space)
        except Exception:
            pass

    def _on_branch_layout_change(self, _event: tk.Event) -> None:  # type: ignore[type-arg]
        """切换条件分支的布局模式，并尝试重新渲染时间线。"""

        label = getattr(self, "branch_layout_var", None)
        if isinstance(label, tk.StringVar):
            value = label.get()
        else:
            value = "下方展开"

        # 文本 -> 内部模式值的简单映射
        if value == "右侧展开":
            self.branch_layout_mode = "right"
        else:
            self.branch_layout_mode = "below"

        try:
            if self._timeline_root_space:
                self._render_execution_timeline(self._timeline_root_space)
        except Exception:
            pass

    def _refresh_exec_param_form(self) -> None:
        # 清空旧的参数输入控件
        for child in self.params_frame.winfo_children():
            child.destroy()

        entry_name = self.exec_entry_var.get()
        row = 0

        func_def, is_method, _cls_name, _fn_name = self._resolve_exec_entry_def()
        param_entries: Dict[str, ttk.Entry] = {}

        if func_def is None:
            self.params_frame._param_entries = param_entries  # type: ignore[attr-defined]
            return

        for idx, arg in enumerate(func_def.args.args):
            if is_method and idx == 0 and arg.arg in {"self", "cls"}:
                continue

            ttk.Label(self.params_frame, text=f"参数 {arg.arg}：").grid(
                row=row,
                column=0,
                sticky="w",
            )
            entry = ttk.Entry(self.params_frame)
            default = "1" if idx == 0 else "2" if idx == 1 else ""
            if default:
                entry.insert(0, default)
            entry.grid(row=row, column=1, sticky="ew", padx=5, pady=2)
            param_entries[arg.arg] = entry
            row += 1

        self.params_frame._param_entries = param_entries  # type: ignore[attr-defined]

    def _run_example(self) -> None:
        self.exec_output.configure(state="normal")
        self.exec_output.delete("1.0", tk.END)

        entry_name = self.exec_entry_var.get()

        # 简单的日志函数：同时写入执行区和标准输出
        # 加入健壮性判断，避免窗口关闭后继续写入已销毁的 Text 控件
        def log(msg: str) -> None:
            line = msg.rstrip("\n") + "\n"
            try:
                widget = getattr(self, "exec_output", None)
                # 控件仍然存在时才写入 UI
                if widget is not None and widget.winfo_exists():
                    widget.insert("end", line)
                # 无论如何都打印到标准输出
                print(f"[ExecLog] {line.strip()}")
            except tk.TclError:
                # 当 Tk 已经销毁时，只输出到控制台，避免再次抛异常
                print(f"[ExecLog] (no UI) {line.strip()}")

        try:
            mode = getattr(self, "exec_mode_var", None)
            mode_value = mode.get() if isinstance(mode, tk.StringVar) else "python"

            # 当前执行源信息：模块名 / 文件路径 / 入口函数
            mod_name = getattr(self.exec_ctx, "module_name", None)
            file_path = getattr(self.exec_ctx, "file_path", None)

            log(f"开始执行入口: {entry_name} (模式={mode_value})")
            log(f"执行源: module={mod_name!r} file={file_path!r} entry={entry_name!r}")
            log("构建执行环境...")

            func_def, is_method, cls_name, fn_name = self._resolve_exec_entry_def()
            if func_def is None:
                log("未找到入口对应的函数定义。")
                try:
                    widget = getattr(self, "exec_output", None)
                    if widget is not None and widget.winfo_exists():
                        widget.configure(state="disabled")
                except tk.TclError:
                    pass
                return

            # 检测是否存在在函数/方法内部再次定义的嵌套函数或 lambda（闭包场景）。
            # 这类结构当前 SimpleFunctionExecutor 尚未完整支持，先在 AST 模式中友好降级。
            has_inner_def = False
            try:
                for node in ast.walk(func_def):
                    # 跳过自身，只关心内部再定义的 FunctionDef / AsyncFunctionDef / Lambda
                    if node is func_def:
                        continue
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                        has_inner_def = True
                        break
            except Exception:
                has_inner_def = False

            if mode_value == "ast" and has_inner_def:
                log("[AST] 当前执行器暂不支持在函数/方法内部再定义的嵌套函数或 lambda，自动回退到 Python 模式。")
                mode_value = "python"

            raw_entries = getattr(self.params_frame, "_param_entries", {})  # type: ignore[attr-defined]
            call_kwargs: Dict[str, Any] = {}
            for idx, arg in enumerate(func_def.args.args):
                if is_method and idx == 0 and arg.arg in {"self", "cls"}:
                    continue
                widget = raw_entries.get(arg.arg)
                if widget is None:
                    continue
                text = widget.get()
                value = eval(text, {}, {})  # noqa: S307
                call_kwargs[arg.arg] = value

            # 无论 Python 模式还是 AST 模式，都先执行一次源码，构建模块环境
            env: dict = {}
            exec(self.exec_ctx.source, env, env)

            # 为 AST 执行器注入当前模块内函数的 AST 索引，支持“调用链”场景的子执行空间
            try:
                ast_func_index: Dict[str, ast.FunctionDef] = {}
                for fn in getattr(self.exec_ctx, "functions", []) or []:
                    if isinstance(fn, ast.FunctionDef):
                        ast_func_index[fn.name] = fn
                env["__ast_func_index__"] = ast_func_index
            except Exception:
                env.setdefault("__ast_func_index__", {})

            log("环境构建完成。")

            if mode_value == "ast" and entry_name:
                # ---- AST 模式：函数入口 & 方法入口都尝试走 SimpleFunctionExecutor ----
                ast_call_kwargs = dict(call_kwargs)

                if is_method:
                    # 为类方法入口构造一个简单实例，并把 self 显式注入到参数中
                    if not cls_name or cls_name not in env:
                        log(f"[AST] 未在环境中找到类 {cls_name!r}，回退到 Python 模式。")
                        mode_value = "python"
                    else:
                        try:
                            cls_obj = env[cls_name]
                            obj = cls_obj()
                        except Exception as exc:  # noqa: BLE001
                            log(f"[AST] 无法构造 {cls_name} 实例: {exc}，回退到 Python 模式。")
                            mode_value = "python"
                        else:
                            # 确保用户参数中没有残留的 self/cls 键
                            ast_call_kwargs.pop("self", None)
                            ast_call_kwargs.pop("cls", None)
                            ast_call_kwargs = {"self": obj, **ast_call_kwargs}

                            log(
                                f"[AST] 使用 SimpleFunctionExecutor 执行 {cls_name}.{fn_name}({call_kwargs!r}) ...",
                            )
                            executor = SimpleFunctionExecutor(func_def, module_globals=env)
                            result_obj = executor.run(ast_call_kwargs)
                else:
                    log(f"[AST] 使用 SimpleFunctionExecutor 执行 {entry_name}({call_kwargs!r}) ...")
                    # 关键：将执行过源码的 env 作为 module_globals 传入，
                    # 使 AST 执行可以访问类定义（例如 ASTViewerApp 等）。
                    executor = SimpleFunctionExecutor(func_def, module_globals=env)
                    result_obj = executor.run(ast_call_kwargs)

                if mode_value == "ast":
                    # 仅在 AST 执行未被回退时，处理 execution_zone / CAV / JSON
                    for line in result_obj.logs:
                        log(f"[AST] {line}")

                    # 若可用，展开 execution_zone，展示每一步的 scope_in / scope_out
                    zone = getattr(result_obj, "execution_zone", None)
                    if isinstance(zone, dict):
                        log("[AST] ---- execution_zone ----")
                        log(f"[AST] scope_level: {zone.get('scope_level')}")
                        log(f"[AST] scope_in: {zone.get('scope_in')!r}")
                        log(f"[AST] scope_out: {zone.get('scope_out')!r}")
                        steps = zone.get("exec_queue") or []
                        for idx, step in enumerate(steps, start=1):
                            code_repr = step.get("code")
                            lineno = step.get("lineno")
                            log(f"[AST] step {idx}: L{lineno} {code_repr}")
                            log(f"[AST]   scope_in:  {step.get('scope_in')!r}")
                            log(f"[AST]   scope_out: {step.get('scope_out')!r}")
                        log("[AST] ------------------------")

                        # 使用 execution_zone 作为顶层 execution_space，在 CAV 中渲染时间线
                        try:
                            self._render_execution_timeline(zone)
                        except Exception:
                            pass

                        # 将 execution_zone 写入 JSON 文件，作为演示数据源之一
                        try:
                            self._save_execution_zone_json(
                                entry_name,
                                zone,
                                result_obj.return_value,
                                tree=self.exec_ctx.tree,
                                functions=self.exec_ctx.functions,
                                classes=self.exec_ctx.classes,
                            )
                        except Exception as exc:  # noqa: BLE001
                            log(f"[AST] 写入 JSON 快照失败: {exc}")

                    log(f"[AST] 返回值: {result_obj.return_value!r}")
                    try:
                        widget = getattr(self, "exec_output", None)
                        if widget is not None and widget.winfo_exists():
                            widget.configure(state="disabled")
                    except tk.TclError:
                        pass
                    return

            if is_method and cls_name and fn_name:
                cls_obj = env[cls_name]
                obj = cls_obj()
                log(f"调用 {cls_name}().{fn_name}({call_kwargs!r}) ...")
                func = getattr(obj, fn_name)
                result = func(**call_kwargs)
                log(f"{cls_name}().{fn_name}({call_kwargs!r}) -> {result!r}")
            else:
                func = env[entry_name]
                log(f"调用 {entry_name}({call_kwargs!r}) ...")
                result = func(**call_kwargs)
                log(f"{entry_name}({call_kwargs!r}) -> {result!r}")
        except Exception as exc:  # noqa: BLE001
            log(f"执行失败: {exc}")
            # 窗口可能已被关闭，此时只弹框或静默失败
            try:
                messagebox.showerror("执行失败", str(exc))
            except tk.TclError:
                # Tk 已销毁时忽略弹窗错误
                pass

        # 最后一次安全地尝试禁用输出框
        try:
            widget = getattr(self, "exec_output", None)
            if widget is not None and widget.winfo_exists():
                widget.configure(state="disabled")
        except tk.TclError:
            pass


def main() -> None:
    app = VisualProgrammingApp()
    app.mainloop()


if __name__ == "__main__":
    main()
