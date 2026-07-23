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
import copy
import types
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

        self.step_detail_notebook = ttk.Notebook(self.step_detail_frame)
        self.step_detail_notebook.pack(fill="x", expand=False, padx=5, pady=(5, 2))

        self.step_info_tab = ttk.Frame(self.step_detail_notebook)
        self.ast_slots_tab = ttk.Frame(self.step_detail_notebook)
        self.var_browser_tab = ttk.Frame(self.step_detail_notebook)
        self.step_detail_notebook.add(self.step_info_tab, text="当前 Step 详情")
        self.step_detail_notebook.add(self.ast_slots_tab, text="AST 槽位分析")
        self.step_detail_notebook.add(self.var_browser_tab, text="变量浏览")

        self.step_detail_text = tk.Text(self.step_info_tab, wrap="word", font=("Consolas", 9), height=6)
        self.step_detail_text.pack(fill="x", expand=False)
        self.step_detail_text.configure(state="disabled")

        self.ast_analyze_text = tk.Text(self.ast_slots_tab, wrap="word", font=("Consolas", 9), height=6)
        self.ast_analyze_text.pack(fill="x", expand=False)
        self.ast_analyze_text.configure(state="disabled")

        self.var_browser_tree = ttk.Treeview(
            self.var_browser_tab,
            columns=("kind", "value"),
            show="tree headings",
        )
        self.var_browser_tree.heading("#0", text="名称")
        self.var_browser_tree.heading("kind", text="kind")
        self.var_browser_tree.heading("value", text="value")
        self.var_browser_tree.column("#0", width=120, anchor="w")
        self.var_browser_tree.column("kind", width=80, anchor="w")
        self.var_browser_tree.column("value", width=260, anchor="w")
        var_scrollbar = ttk.Scrollbar(
            self.var_browser_tab,
            orient="vertical",
            command=self.var_browser_tree.yview,
        )
        self.var_browser_tree.configure(yscrollcommand=var_scrollbar.set)
        self.var_browser_tree.pack(side=tk.LEFT, fill="both", expand=True)
        var_scrollbar.pack(side=tk.RIGHT, fill="y")

        # StepAstNode JSON 编辑区（仅在“瀑布流 + StepAstNode”模式下有意义）
        editor_frame = ttk.Frame(self.step_detail_frame)
        editor_frame.pack(fill="both", expand=True, padx=5, pady=(0, 5))

        # 临时节点剪贴板：四个入口 + 四个出口
        clipboard_frame = ttk.LabelFrame(editor_frame, text="临时 StepAstNode 模式")
        clipboard_frame.pack(fill="x", side=tk.TOP, pady=(0, 4))

        # 槽位调试与选择：调试分析按钮 + 槽位下拉
        slot_toolbar = ttk.Frame(clipboard_frame)
        slot_toolbar.pack(fill="x", side=tk.TOP, pady=(2, 0))
        ttk.Button(
            slot_toolbar,
            text="调试分析",
            command=self._timeline__analyze_ast_slots,
        ).pack(side=tk.LEFT, padx=(0, 4))

        ttk.Label(slot_toolbar, text="槽位：").pack(side=tk.LEFT)
        self.ast_slot_var = tk.StringVar(value="（当前节点未分析）")
        self.ast_slot_combo = ttk.Combobox(
            slot_toolbar,
            textvariable=self.ast_slot_var,
            state="readonly",
            width=56,
        )
        self.ast_slot_combo.pack(side=tk.LEFT, padx=(2, 0))
        self.ast_slot_combo.bind("<<ComboboxSelected>>", self._on_ast_slot_selected)
        self._ast_slot_items: list[dict[str, Any]] = []

        # 槽位状态单独一行
        self.ast_slot_status_var = tk.StringVar(value="槽位状态：未选中")
        slot_status_frame = ttk.Frame(clipboard_frame)
        slot_status_frame.pack(fill="x", side=tk.TOP, pady=(0, 0))
        ttk.Label(slot_status_frame, textvariable=self.ast_slot_status_var).pack(
            side=tk.LEFT, padx=(0, 0)
        )
        ttk.Button(
            slot_status_frame,
            text="应用到槽位",
            command=self._on_ast_slot_apply_clipboard,
        ).pack(side=tk.LEFT, padx=(8, 0))

        # 入口 / 出口 / 临时节点 状态行：放在模板 Notebook 之前
        entry_frame = ttk.Frame(clipboard_frame)
        entry_frame.pack(fill="x", side=tk.TOP)
        ttk.Label(entry_frame, text="入口：").pack(side=tk.LEFT)
        ttk.Button(
            entry_frame,
            text="复制到临时",
            command=self._on_ast_clipboard_copy_current,
        ).pack(side=tk.LEFT, padx=(2, 0))
        ttk.Button(
            entry_frame,
            text="剪切到临时",
            command=self._on_ast_clipboard_cut_current,
        ).pack(side=tk.LEFT, padx=(2, 0))

        exit_frame = ttk.Frame(clipboard_frame)
        exit_frame.pack(fill="x", side=tk.TOP, pady=(2, 0))
        ttk.Label(exit_frame, text="出口：").pack(side=tk.LEFT)
        ttk.Button(
            exit_frame,
            text="删除当前节点",
            command=self._on_ast_clipboard_delete_current,
        ).pack(side=tk.LEFT, padx=(2, 0))
        ttk.Button(
            exit_frame,
            text="用临时替换",
            command=self._on_ast_clipboard_replace_current,
        ).pack(side=tk.LEFT, padx=(2, 0))
        ttk.Button(
            exit_frame,
            text="在当前后插入临时",
            command=self._on_ast_clipboard_insert_sibling,
        ).pack(side=tk.LEFT, padx=(2, 0))
        ttk.Button(
            exit_frame,
            text="作为子节点插入",
            command=self._on_ast_clipboard_insert_child,
        ).pack(side=tk.LEFT, padx=(2, 0))

        status_frame = ttk.Frame(clipboard_frame)
        status_frame.pack(fill="x", side=tk.TOP, pady=(2, 0))
        ttk.Label(status_frame, text="临时节点：").pack(side=tk.LEFT)
        self.ast_clipboard_status_var = tk.StringVar(value="（无临时节点）")
        ttk.Label(status_frame, textvariable=self.ast_clipboard_status_var).pack(
            side=tk.LEFT, padx=(2, 0)
        )

        # 按 StepAstNode category 分类的模板入口 Notebook（每个分类下再细分具体节点面板）
        template_mode_nb = ttk.Notebook(clipboard_frame)
        template_mode_nb.pack(fill="x", side=tk.TOP, pady=(4, 0))

        template_tab = ttk.Frame(template_mode_nb)
        source_tab = ttk.Frame(template_mode_nb)
        template_mode_nb.add(template_tab, text="模板")
        template_mode_nb.add(source_tab, text="源码")

        self.ast_template_mode_nb = template_mode_nb

        template_nb = ttk.Notebook(template_tab)
        template_nb.pack(fill="x", side=tk.TOP, pady=(0, 0))

        control_tab = ttk.Frame(template_nb)
        data_tab = ttk.Frame(template_nb)
        call_tab = ttk.Frame(template_nb)
        expr_tab = ttk.Frame(template_nb)
        exception_tab = ttk.Frame(template_nb)
        async_tab = ttk.Frame(template_nb)
        import_tab = ttk.Frame(template_nb)
        meta_tab = ttk.Frame(template_nb)

        self.ast_template_nb = template_nb
        self.ast_template_control_tab = control_tab
        self.ast_template_data_tab = data_tab
        self.ast_template_call_tab = call_tab
        self.ast_template_expr_tab = expr_tab
        self.ast_template_exception_tab = exception_tab
        self.ast_template_async_tab = async_tab
        self.ast_template_import_tab = import_tab
        self.ast_template_meta_tab = meta_tab

        template_nb.add(control_tab, text="控制流")
        template_nb.add(data_tab, text="数据流/赋值")
        template_nb.add(call_tab, text="调用/接口")
        template_nb.add(expr_tab, text="表达式/常量")
        template_nb.add(exception_tab, text="异常与上下文管理")
        template_nb.add(async_tab, text="异步与模式匹配")
        template_nb.add(import_tab, text="导入与模块组织")
        template_nb.add(meta_tab, text="结构/作用域")

        self.ast_source_text = tk.Text(source_tab, wrap="word", font=("Consolas", 9), height=6)
        self.ast_source_text.pack(fill="x", expand=False, padx=(2, 2), pady=(2, 2))
        ttk.Button(
            source_tab,
            text="解析到临时(源码)",
            command=self._on_ast_source_parse_to_clipboard,
        ).pack(side=tk.TOP, anchor="w", padx=(2, 0), pady=(0, 2))

        # control 分类：控制流相关 AST 节点（If / For / While / AsyncFor / Break&Continue / Return / IfExp）
        control_nb = ttk.Notebook(control_tab)
        control_nb.pack(fill="x", expand=False, pady=(2, 0))

        control_if_tab = ttk.Frame(control_nb)
        control_for_tab = ttk.Frame(control_nb)
        control_while_tab = ttk.Frame(control_nb)
        control_asyncfor_tab = ttk.Frame(control_nb)
        control_break_tab = ttk.Frame(control_nb)
        control_return_tab = ttk.Frame(control_nb)
        control_ifexp_tab = ttk.Frame(control_nb)

        self.ast_control_nb = control_nb
        self.ast_control_if_tab = control_if_tab
        self.ast_control_for_tab = control_for_tab
        self.ast_control_while_tab = control_while_tab
        self.ast_control_asyncfor_tab = control_asyncfor_tab
        self.ast_control_break_tab = control_break_tab
        self.ast_control_return_tab = control_return_tab
        self.ast_control_ifexp_tab = control_ifexp_tab

        control_nb.add(control_if_tab, text="If")
        control_nb.add(control_for_tab, text="For")
        control_nb.add(control_while_tab, text="While")
        control_nb.add(control_asyncfor_tab, text="AsyncFor")
        control_nb.add(control_break_tab, text="Break/Continue")
        control_nb.add(control_return_tab, text="Return")
        control_nb.add(control_ifexp_tab, text="IfExp")

        ttk.Button(
            control_if_tab,
            text="生成模板：If (if cond:)",
            command=self._on_ast_template_if_simple,
        ).pack(side=tk.TOP, anchor="w", padx=(2, 0), pady=(2, 2))

        ttk.Label(
            control_if_tab,
            text=(
                "节点类型：If(test, body, orelse)\n"
                "可安置到：任意语句列表（Module/FunctionDef/ClassDef/... 的 body 或分支体）\n"
                "自身字段：\n"
                "  · test：接任意表达式节点（Name / Call / BinOp / Compare / Constant 等）\n"
                "  · body：接语句节点列表（Assign / Expr / If / For / While / Try / Return 等）\n"
                "  · orelse：接语句节点列表（结构同 body）\n"
            ),
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=(4, 0), pady=(0, 4))

        ttk.Label(
            control_for_tab,
            text=(
                "节点：For(target, iter, body, orelse)\n"
                "含义：for 语句，遍历 iter，将每次元素绑定到 target。\n"
                "可安置到：语句列表（与 If 相同）\n"
                "自身字段：target/iter 为表达式，body/orelse 为语句列表。\n"
                "当前未提供模板，可在 JSON 中手动编辑 StepAstNode(For)。\n"
            ),
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=(4, 0), pady=(4, 4))

        ttk.Label(
            control_while_tab,
            text=(
                "节点：While(test, body, orelse)\n"
                "含义：while 条件循环。\n"
                "可安置到：语句列表。\n"
                "自身字段：test 为表达式，body/orelse 为语句列表。\n"
            ),
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=(4, 0), pady=(4, 4))

        ttk.Label(
            control_asyncfor_tab,
            text=(
                "节点：AsyncFor(target, iter, body, orelse)\n"
                "含义：异步 for 循环（async for）。\n"
                "可安置到：语句列表（通常在 AsyncFunctionDef.body 中）。\n"
            ),
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=(4, 0), pady=(4, 4))

        ttk.Label(
            control_break_tab,
            text=(
                "节点：Break / Continue\n"
                "含义：循环内部的跳出/继续语句。\n"
                "可安置到：For/While/AsyncFor 的 body 或 orelse 中。\n"
                "自身字段：无额外字段，仅依赖所在执行上下文。\n"
            ),
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=(4, 0), pady=(4, 4))

        ttk.Label(
            control_return_tab,
            text=(
                "节点：Return(value)\n"
                "含义：从函数/方法返回值。\n"
                "可安置到：FunctionDef/AsyncFunctionDef.body 列表中。\n"
                "自身字段：value 为可选表达式（Name / Call / Constant 等）。\n"
            ),
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=(4, 0), pady=(4, 4))

        ttk.Label(
            control_ifexp_tab,
            text=(
                "节点：IfExp(test, body, orelse)\n"
                "含义：条件表达式（三元表达式）如 a if cond else b。\n"
                "可安置到：任意表达式槽位（与 BinOp/Call 等相同）。\n"
            ),
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=(4, 0), pady=(4, 4))

        # expr 分类：表达式/常量（Constant / Op / Compare / Comprehension / Other）
        expr_nb = ttk.Notebook(expr_tab)
        expr_nb.pack(fill="x", expand=False, pady=(2, 0))

        expr_const_tab = ttk.Frame(expr_nb)
        expr_op_tab = ttk.Frame(expr_nb)
        expr_compare_tab = ttk.Frame(expr_nb)
        expr_comprehension_tab = ttk.Frame(expr_nb)
        expr_other_tab = ttk.Frame(expr_nb)
        expr_binop_tab = ttk.Frame(expr_nb)

        self.ast_expr_nb = expr_nb
        self.ast_expr_const_tab = expr_const_tab
        self.ast_expr_binop_tab = expr_binop_tab
        self.ast_expr_op_tab = expr_op_tab
        self.ast_expr_compare_tab = expr_compare_tab
        self.ast_expr_comprehension_tab = expr_comprehension_tab
        self.ast_expr_other_tab = expr_other_tab

        expr_nb.add(expr_const_tab, text="Constant")
        expr_nb.add(expr_binop_tab, text="BinOp")
        expr_nb.add(expr_op_tab, text="Unary/BooOp")
        expr_nb.add(expr_compare_tab, text="Compare")
        expr_nb.add(expr_comprehension_tab, text="Comprehension")
        expr_nb.add(expr_other_tab, text="Other")

        ttk.Button(
            expr_binop_tab,
            text="生成模板：BinOp (a + b)",
            command=self._on_ast_template_binop_add,
        ).pack(side=tk.TOP, anchor="w", padx=(2, 0), pady=(2, 2))

        ttk.Label(
            expr_binop_tab,
            text=(
                "节点类型：BinOp(left, op, right)\n"
                "可安置到：任意表达式槽位（Assign.value / Return.value / Call.args[*] / If.test 等）\n"
                "自身字段：left/right 为表达式，op 为运算符标记（本模板为 'Add'）。\n"
            ),
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=(4, 0), pady=(0, 4))

        ttk.Label(
            expr_const_tab,
            text=(
                "节点：Constant(value)\n"
                "含义：字面量常量，如数字/字符串/True/False/None。\n"
                "可安置到：任意表达式槽位。\n"
            ),
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=(4, 0), pady=(4, 4))

        ttk.Label(
            expr_op_tab,
            text=(
                "节点：UnaryOp / BoolOp 等\n"
                "含义：一元运算（-x）与布尔运算（and/or）。\n"
                "可安置到：任意表达式槽位。\n"
            ),
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=(4, 0), pady=(4, 4))

        ttk.Label(
            expr_compare_tab,
            text=(
                "节点：Compare(left, ops, comparators)\n"
                "含义：比较表达式，例如 a > b, x in items 等。\n"
                "可安置到：If.test / While.test 等条件表达式位置。\n"
            ),
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=(4, 0), pady=(4, 4))

        ttk.Label(
            expr_comprehension_tab,
            text=(
                "节点：列表/字典/集合/生成器推导式相关节点\n"
                "含义：[x for x in xs if ...] 等结构。\n"
                "可安置到：任意表达式槽位。\n"
            ),
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=(4, 0), pady=(4, 4))

        ttk.Label(
            expr_other_tab,
            text="其他暂未单独分类的表达式节点，可按需在 JSON 中直接编辑。",
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=(4, 0), pady=(4, 4))

        # exception 分类：异常与上下文管理（Try / Except / Raise / Assert / With / AsyncWith）
        exception_nb = ttk.Notebook(exception_tab)
        exception_nb.pack(fill="x", expand=False, pady=(2, 0))
        exception_try_tab = ttk.Frame(exception_nb)
        exception_raise_tab = ttk.Frame(exception_nb)
        exception_assert_tab = ttk.Frame(exception_nb)
        exception_with_tab = ttk.Frame(exception_nb)
        exception_asyncwith_tab = ttk.Frame(exception_nb)

        self.ast_exception_nb = exception_nb
        self.ast_exception_try_tab = exception_try_tab
        self.ast_exception_raise_tab = exception_raise_tab
        self.ast_exception_assert_tab = exception_assert_tab
        self.ast_exception_with_tab = exception_with_tab
        self.ast_exception_asyncwith_tab = exception_asyncwith_tab

        exception_nb.add(exception_try_tab, text="Try/Except")
        exception_nb.add(exception_raise_tab, text="Raise")
        exception_nb.add(exception_assert_tab, text="Assert")
        exception_nb.add(exception_with_tab, text="With")
        exception_nb.add(exception_asyncwith_tab, text="AsyncWith")

        ttk.Button(
            exception_try_tab,
            text="生成模板：Try/Except",
            command=self._on_ast_template_try_simple,
        ).pack(side=tk.TOP, anchor="w", padx=(2, 0), pady=(2, 2))

        ttk.Label(
            exception_try_tab,
            text=(
                "节点类型：Try(body, handlers, orelse, finalbody) + ExceptHandler(type, name, body)\n"
                "可安置到：任意语句列表（Module/FunctionDef/If/For 等的 body）\n"
                "自身字段：body/handlers/orelse/finalbody 均为语句列表或处理器列表。\n"
            ),
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=(4, 0), pady=(0, 4))

        ttk.Label(
            exception_raise_tab,
            text=(
                "节点：Raise(exc, cause)\n"
                "含义：显式抛出异常。\n"
                "可安置到：语句列表。\n"
            ),
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=(4, 0), pady=(4, 4))

        ttk.Label(
            exception_assert_tab,
            text=(
                "节点：Assert(test, msg)\n"
                "含义：断言语句。\n"
            ),
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=(4, 0), pady=(4, 4))

        ttk.Label(
            exception_with_tab,
            text=(
                "节点：With(items, body)\n"
                "含义：with 上下文管理语句。\n"
            ),
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=(4, 0), pady=(4, 4))

        ttk.Label(
            exception_asyncwith_tab,
            text=(
                "节点：AsyncWith(items, body)\n"
                "含义：异步 with 语句。\n"
            ),
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=(4, 0), pady=(4, 4))

        # data 分类：数据流/赋值（Assign / AnnAssign / AugAssign / Name&Attribute / Other）
        data_nb = ttk.Notebook(data_tab)
        data_nb.pack(fill="x", expand=False, pady=(2, 0))
        data_assign_tab = ttk.Frame(data_nb)
        data_annassign_tab = ttk.Frame(data_nb)
        data_augassign_tab = ttk.Frame(data_nb)
        data_name_attr_tab = ttk.Frame(data_nb)
        data_other_tab = ttk.Frame(data_nb)

        self.ast_data_nb = data_nb
        self.ast_data_assign_tab = data_assign_tab
        self.ast_data_annassign_tab = data_annassign_tab
        self.ast_data_augassign_tab = data_augassign_tab
        self.ast_data_name_attr_tab = data_name_attr_tab
        self.ast_data_other_tab = data_other_tab

        data_nb.add(data_assign_tab, text="Assign")
        data_nb.add(data_annassign_tab, text="AnnAssign")
        data_nb.add(data_augassign_tab, text="AugAssign")
        data_nb.add(data_name_attr_tab, text="Name/Attribute")
        data_nb.add(data_other_tab, text="Other")

        ttk.Button(
            data_assign_tab,
            text="生成模板：Assign (x = y)",
            command=self._on_ast_template_assign_simple,
        ).pack(side=tk.TOP, anchor="w", padx=(2, 0), pady=(2, 2))

        ttk.Label(
            data_assign_tab,
            text=(
                "节点类型：Assign(targets, value, type_comment)\n"
                "可安置到：任意语句列表（函数体/模块体/类体等）\n"
                "自身字段：targets 为左值列表，value 为右值表达式。\n"
            ),
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=(4, 0), pady=(0, 4))

        ttk.Label(
            data_annassign_tab,
            text=(
                "节点：AnnAssign(target, annotation, value, simple)\n"
                "含义：带类型注解的赋值，如 x: int = 1。\n"
            ),
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=(4, 0), pady=(4, 4))

        ttk.Label(
            data_augassign_tab,
            text=(
                "节点：AugAssign(target, op, value)\n"
                "含义：原位运算赋值，如 a += 1。\n"
            ),
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=(4, 0), pady=(4, 4))

        ttk.Label(
            data_name_attr_tab,
            text=(
                "节点：Name / Attribute\n"
                "含义：变量名与属性访问，可出现在 Assign.targets / 任意表达式内部。\n"
            ),
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=(4, 0), pady=(4, 4))

        ttk.Label(
            data_other_tab,
            text="其他与数据读写相关的节点可归入此类，当前未单独提供模板。",
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=(4, 0), pady=(4, 4))

        # call 分类：调用/接口（Call / keyword / interface 等）
        call_nb = ttk.Notebook(call_tab)
        call_nb.pack(fill="x", expand=False, pady=(2, 0))

        call_func_tab = ttk.Frame(call_nb)
        call_method_tab = ttk.Frame(call_nb)
        call_args_tab = ttk.Frame(call_nb)
        call_keywords_tab = ttk.Frame(call_nb)
        call_interface_tab = ttk.Frame(call_nb)

        self.ast_call_nb = call_nb
        self.ast_call_call_tab = call_func_tab
        self.ast_call_method_tab = call_method_tab
        self.ast_call_args_tab = call_args_tab
        self.ast_call_keywords_tab = call_keywords_tab
        self.ast_call_interface_tab = call_interface_tab

        call_nb.add(call_func_tab, text="Call")
        call_nb.add(call_method_tab, text="MethodCall")
        call_nb.add(call_args_tab, text="Args")
        call_nb.add(call_keywords_tab, text="Keywords")
        call_nb.add(call_interface_tab, text="Interface")

        ttk.Button(
            call_func_tab,
            text="生成模板：Call (foo(x, y))",
            command=self._on_ast_template_call_simple,
        ).pack(side=tk.TOP, anchor="w", padx=(2, 0), pady=(2, 2))

        ttk.Label(
            call_func_tab,
            text=(
                "节点类型：Call(func, args, keywords)\n"
                "可安置到：任意表达式槽位；作为语句时需包一层 Expr。\n"
            ),
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=(4, 0), pady=(0, 4))

        ttk.Button(
            call_method_tab,
            text="生成模板：MethodCall (obj.m())",
            command=self._on_ast_template_method_call,
        ).pack(side=tk.TOP, anchor="w", padx=(2, 0), pady=(2, 2))

        ttk.Label(
            call_method_tab,
            text=(
                "节点：方法调用 Call(Attribute(...))\n"
                "含义：obj.m() 形式的调用，func 字段为 Attribute。\n"
            ),
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=(4, 0), pady=(0, 4))

        ttk.Label(
            call_args_tab,
            text=(
                "节点：Call.fields.args 列表\n"
                "含义：位置参数列表，每一项为一个表达式节点。\n"
            ),
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=(4, 0), pady=(4, 4))

        ttk.Label(
            call_keywords_tab,
            text=(
                "节点：keyword(name, value)\n"
                "含义：关键字参数节点，通常挂在 Call.fields.keywords 列表中。\n"
            ),
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=(4, 0), pady=(4, 4))

        ttk.Label(
            call_interface_tab,
            text="与接口抽象相关的更高阶节点，可在后续版本中扩展。",
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=(4, 0), pady=(4, 4))

        # async 分类：异步与模式匹配（AsyncDef / Await / Yield / Match 等）
        async_nb = ttk.Notebook(async_tab)
        async_nb.pack(fill="x", expand=False, pady=(2, 0))

        async_def_tab = ttk.Frame(async_nb)
        async_await_tab = ttk.Frame(async_nb)
        async_yield_tab = ttk.Frame(async_nb)
        async_match_tab = ttk.Frame(async_nb)

        self.ast_async_nb = async_nb
        self.ast_async_def_tab = async_def_tab
        self.ast_async_await_tab = async_await_tab
        self.ast_async_yield_tab = async_yield_tab
        self.ast_async_match_tab = async_match_tab

        async_nb.add(async_def_tab, text="AsyncFunctionDef")
        async_nb.add(async_await_tab, text="Await")
        async_nb.add(async_yield_tab, text="Yield/YieldFrom")
        async_nb.add(async_match_tab, text="Match")

        ttk.Label(
            async_def_tab,
            text=(
                "节点：AsyncFunctionDef\n"
                "含义：async def 定义的协程函数。\n"
            ),
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=(4, 0), pady=(4, 4))

        ttk.Label(
            async_await_tab,
            text=(
                "节点：Await(value)\n"
                "含义：等待一个可等待对象，如 await coro()。\n"
            ),
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=(4, 0), pady=(4, 4))

        ttk.Label(
            async_yield_tab,
            text=(
                "节点：Yield / YieldFrom\n"
                "含义：生成器/协程中的 yield 表达式。\n"
            ),
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=(4, 0), pady=(4, 4))

        ttk.Label(
            async_match_tab,
            text=(
                "节点：Match\n"
                "含义：结构化模式匹配（Python 3.10+ 的 match/case）。\n"
            ),
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=(4, 0), pady=(4, 4))

        # import 分类：导入与模块组织（Import / ImportFrom / alias / Organize）
        import_nb = ttk.Notebook(import_tab)
        import_nb.pack(fill="x", expand=False, pady=(2, 0))

        import_import_tab = ttk.Frame(import_nb)
        import_from_tab = ttk.Frame(import_nb)
        import_alias_tab = ttk.Frame(import_nb)
        import_organize_tab = ttk.Frame(import_nb)

        self.ast_import_nb = import_nb
        self.ast_import_import_tab = import_import_tab
        self.ast_import_from_tab = import_from_tab
        self.ast_import_alias_tab = import_alias_tab
        self.ast_import_organize_tab = import_organize_tab

        import_nb.add(import_import_tab, text="Import")
        import_nb.add(import_from_tab, text="ImportFrom")
        import_nb.add(import_alias_tab, text="alias")
        import_nb.add(import_organize_tab, text="Organize")

        ttk.Label(
            import_import_tab,
            text=(
                "节点：Import(names)\n"
                "含义：import x as y 形式的导入。\n"
            ),
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=(4, 0), pady=(4, 4))

        ttk.Label(
            import_from_tab,
            text=(
                "节点：ImportFrom(module, names, level)\n"
                "含义：from pkg import Name 形式的导入。\n"
            ),
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=(4, 0), pady=(4, 4))

        ttk.Label(
            import_alias_tab,
            text=(
                "节点：alias(name, asname)\n"
                "含义：Import/ImportFrom.names 列表中的条目。\n"
            ),
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=(4, 0), pady=(4, 4))

        ttk.Label(
            import_organize_tab,
            text="与导入整理/分组相关的更高阶操作，可在后续版本扩展。",
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=(4, 0), pady=(4, 4))

        # 结构/作用域 分类：Module / Function / Class / 其他作用域
        structure_nb = ttk.Notebook(meta_tab)
        structure_nb.pack(fill="x", expand=False, pady=(2, 0))

        structure_module_tab = ttk.Frame(structure_nb)
        structure_function_tab = ttk.Frame(structure_nb)
        structure_class_tab = ttk.Frame(structure_nb)
        structure_other_tab = ttk.Frame(structure_nb)

        self.ast_structure_nb = structure_nb
        self.ast_structure_module_tab = structure_module_tab
        self.ast_structure_function_tab = structure_function_tab
        self.ast_structure_class_tab = structure_class_tab
        self.ast_structure_other_tab = structure_other_tab

        structure_nb.add(structure_module_tab, text="Module")
        structure_nb.add(structure_function_tab, text="Function/Lambda")
        structure_nb.add(structure_class_tab, text="Class")
        structure_nb.add(structure_other_tab, text="Block/Scope")

        ttk.Label(
            structure_module_tab,
            text=(
                "节点：Module(body, type_ignores)\n"
                "含义：模块最外层语句列表。\n"
            ),
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=(4, 0), pady=(4, 4))

        ttk.Label(
            structure_function_tab,
            text=(
                "节点：FunctionDef / AsyncFunctionDef / Lambda\n"
                "含义：函数/方法定义与匿名函数。\n"
            ),
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=(4, 0), pady=(4, 4))

        ttk.Label(
            structure_class_tab,
            text=(
                "节点：ClassDef\n"
                "含义：类定义节点，body 中包含方法与类级语句。\n"
            ),
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=(4, 0), pady=(4, 4))

        ttk.Label(
            structure_other_tab,
            text="其他块级/作用域级节点（如推导式 body 等）可归入此类。",
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=(4, 0), pady=(4, 4))

        # 原有基于 JSON 文本的编辑操作
        json_btns_frame = ttk.Frame(editor_frame)
        json_btns_frame.pack(fill="x", side=tk.TOP, pady=(0, 2))
        ttk.Label(json_btns_frame, text="StepAstNode JSON 编辑：").pack(side=tk.LEFT)

        ttk.Button(
            json_btns_frame,
            text="替换当前节点(JSON)",
            command=self._on_ast_edit_apply_replace,
        ).pack(side=tk.LEFT, padx=(4, 0))
        ttk.Button(
            json_btns_frame,
            text="在当前后插入(JSON)",
            command=self._on_ast_edit_insert_after,
        ).pack(side=tk.LEFT, padx=(4, 0))
        ttk.Button(
            json_btns_frame,
            text="保存到 JSON 文件",
            command=self._on_ast_edit_save_json,
        ).pack(side=tk.LEFT, padx=(4, 0))

        self.ast_edit_text = tk.Text(editor_frame, wrap="none", font=("Consolas", 9), height=10)
        self.ast_edit_text.pack(fill="both", expand=True, pady=(2, 0))

        # Canvas 时间线的 UI 状态：根 execution_space / 选中路径 / 展开路径集合
        # 路径采用 "0-1-3" 形式表示从根 exec_queue 开始的下钻索引序列
        self._timeline_root_space: Dict[str, Any] | None = None
        self._timeline_selected_path: str | None = None
        self._timeline_expanded_paths: set[str] = set()
        self._timeline_hit_regions: list[dict[str, Any]] = []

        # StepAstNode 临时节点剪贴板
        self._ast_clipboard_node: Dict[str, Any] | None = None
        self._ast_clipboard_mode: str | None = None  # copy / cut / assemble / source

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
        self.entry_var = tk.StringVar(value="<module>")
        choices: list[str] = ["<module>"]
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
        elif name == "<module>":
            return self.exec_ctx.tree
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

        def _make_empty_scope() -> dict[str, Any]:
            """创建一个空的作用域结构。

            统一采用四分类形式：
            scope = {
              "own": {
                "modules": {},
                "attributes": {},
                "methods": {},
                "inner_classes": {},
              },
              "outer": {},
            }
            """

            return {
                "own": {
                    "modules": {},
                    "attributes": {},
                    "methods": {},
                    "inner_classes": {},
                },
                "outer": {},
            }

        self.exec_space_template = {
            "scope_level": "module",
            "scope_in": _make_empty_scope(),
            "scope_out": _make_empty_scope(),
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
            # 默认策略：根据值的类型做一个粗粒度推断
            if isinstance(value, (int, float, bool, str)) or value is None:
                inferred_kind = "constant"
            elif isinstance(value, types.ModuleType):
                inferred_kind = "module"
            elif isinstance(value, type):
                inferred_kind = "class_def"
            elif callable(value):
                inferred_kind = "function"
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
            scope_in = {
                "own": {
                    "modules": {},
                    "attributes": {},
                    "methods": {},
                    "inner_classes": {},
                },
                "outer": {},
            }
            self.exec_space_template["scope_in"] = scope_in

        own = scope_in.get("own")
        if not isinstance(own, dict):
            own = {
                "modules": {},
                "attributes": {},
                "methods": {},
                "inner_classes": {},
            }
            scope_in["own"] = own

        attrs_dict = own.get("attributes")
        if not isinstance(attrs_dict, dict):
            attrs_dict = {}
            own["attributes"] = attrs_dict

        for name in attrs.keys():
            if name not in attrs_dict:
                # 使用 {kind, name, value} 三元组形式为 scope_in.own.attributes 填充占位绑定
                attrs_dict[name] = self._make_scope_binding(name, None, kind="constant")

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
                "scope_in": {
                    "own": {
                        "modules": {},
                        "attributes": {},
                        "methods": {},
                        "inner_classes": {},
                    },
                    "outer": {},
                },
                "scope_out": {
                    "own": {
                        "modules": {},
                        "attributes": {},
                        "methods": {},
                        "inner_classes": {},
                    },
                    "outer": {},
                },
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
                "scope_in": {
                    "own": {
                        "modules": {},
                        "attributes": {},
                        "methods": {},
                        "inner_classes": {},
                    },
                    "outer": {},
                },
                "scope_out": {
                    "own": {
                        "modules": {},
                        "attributes": {},
                        "methods": {},
                        "inner_classes": {},
                    },
                    "outer": {},
                },
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
                "scope_in": {
                    "own": {
                        "modules": {},
                        "attributes": {},
                        "methods": {},
                        "inner_classes": {},
                    },
                    "outer": {},
                },
                "scope_out": {
                    "own": {
                        "modules": {},
                        "attributes": {},
                        "methods": {},
                        "inner_classes": {},
                    },
                    "outer": {},
                },
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

        self.exec_entry_var = tk.StringVar(value="<module>")
        choices: list[str] = ["<module>"]
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

        # 时间线渲染源：execution_space vs ast_step_space
        source_frame = ttk.Frame(frame)
        source_frame.grid(row=2, column=1, sticky="w", padx=5, pady=(0, 5))
        ttk.Label(source_frame, text="渲染源：").pack(side=tk.LEFT)
        self.timeline_source_var = tk.StringVar(value="execution_space")
        ttk.Radiobutton(
            source_frame,
            text="瀑布流 JSON",
            value="execution_space",
            variable=self.timeline_source_var,
        ).pack(side=tk.LEFT, padx=(4, 0))
        ttk.Radiobutton(
            source_frame,
            text="瀑布流 + StepAstNode",
            value="ast_step_space",
            variable=self.timeline_source_var,
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
        ast_editor = getattr(self, "ast_edit_text", None)

        if text is None:
            return

        text.configure(state="normal")
        text.delete("1.0", tk.END)

        if not space or not path_key:
            text.configure(state="disabled")
            if isinstance(ast_editor, tk.Text):
                ast_editor.delete("1.0", tk.END)
            # 清空变量浏览面板
            self._update_var_browser_panel({}, {})
            return

        # 通用路径下钻：支持 space/step/branch 三种节点类型
        if not isinstance(space, dict):
            text.configure(state="disabled")
            if isinstance(ast_editor, tk.Text):
                ast_editor.delete("1.0", tk.END)
            self._update_var_browser_panel({}, {})
            return

        parts = [int(p) for p in path_key.split("-") if p != ""]
        if not parts:
            text.configure(state="disabled")
            if isinstance(ast_editor, tk.Text):
                ast_editor.delete("1.0", tk.END)
            self._update_var_browser_panel({}, {})
            return

        node: dict[str, Any] | dict = space
        node_type: str = "space"  # "space" | "step" | "branch"
        scope_in_for_browser: Any = {}
        scope_out_for_browser: Any = {}

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
                if isinstance(ast_editor, tk.Text):
                    ast_editor.delete("1.0", tk.END)
                self._update_var_browser_panel({}, {})
                return
            candidate = children[idx]
            if not isinstance(candidate, dict):
                text.configure(state="disabled")
                if isinstance(ast_editor, tk.Text):
                    ast_editor.delete("1.0", tk.END)
                self._update_var_browser_panel({}, {})
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
                scope_in_for_browser = first_scope_in
                scope_out_for_browser = last_scope_out
            else:
                lines.append("")
                lines.append("branch.exec_queue: []")
                scope_in_for_browser = {}
                scope_out_for_browser = {}
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

            scope_in_for_browser = scope_in
            scope_out_for_browser = scope_out

        # 同步更新变量浏览面板，基于当前节点的 scope_in/scope_out
        self._update_var_browser_panel(scope_in_for_browser, scope_out_for_browser)

        text.insert("1.0", "\n".join(lines))
        text.configure(state="disabled")

        # 若当前为瀑布流 + StepAstNode 模式，且节点上挂有 _ast_node，则将其 JSON 填入编辑区
        if isinstance(ast_editor, tk.Text):
            ast_editor.configure(state="normal")
            ast_editor.delete("1.0", tk.END)
            try:
                source_mode = getattr(self, "timeline_source_var", None)
                source_value = source_mode.get() if isinstance(source_mode, tk.StringVar) else "execution_space"
                if source_value == "ast_step_space" and isinstance(node, dict) and "_ast_node" in node:
                    ast_node = node.get("_ast_node")
                    ast_editor.insert(
                        "1.0",
                        json.dumps(ast_node, ensure_ascii=False, indent=2),
                    )
            except Exception:
                pass
            ast_editor.configure(state="normal")

    def _update_var_browser_panel(self, scope_in: Any, scope_out: Any) -> None:
        """根据给定的 scope_in / scope_out 更新右侧“变量浏览”面板。

        预期结构：
        scope = {
          "own": {
            "modules": {name: {kind,name,value}},
            "attributes": {...},
            "methods": {...},
            "inner_classes": {...},
          },
          "outer": {...},
        }
        """

        tree = getattr(self, "var_browser_tree", None)
        if tree is None:
            return

        # 清空现有内容
        try:
            items = tree.get_children("")
            if items:
                tree.delete(*items)
        except Exception:
            return

        def _add_scope(root_label: str, scope: Any) -> None:
            if not isinstance(scope, dict):
                return
            own = scope.get("own")
            if not isinstance(own, dict):
                return

            root_id = tree.insert("", "end", text=root_label, values=("", ""))
            tree.item(root_id, open=True)

            for cat in ("modules", "attributes", "methods", "inner_classes"):
                cat_dict = own.get(cat)
                if not isinstance(cat_dict, dict) or not cat_dict:
                    continue
                cat_id = tree.insert(root_id, "end", text=cat, values=("", ""))
                tree.item(cat_id, open=True)

                for name, binding in sorted(cat_dict.items(), key=lambda kv: str(kv[0])):
                    if isinstance(binding, dict):
                        kind = str(binding.get("kind", ""))
                        value = binding.get("value")
                    else:
                        kind = ""
                        value = binding

                    try:
                        if isinstance(value, (str, int, float, bool)) or value is None:
                            value_repr = repr(value)
                        else:
                            value_repr = repr(value)
                    except Exception:
                        value_repr = "<unrepresentable>"

                    tree.insert(cat_id, "end", text=str(name), values=(kind, value_repr))

        _add_scope("scope_in", scope_in)
        _add_scope("scope_out", scope_out)

    # -------------------- StepAstNode JSON 编辑操作 --------------------

    # 临时节点剪贴板入口：复制 / 剪切 / 组装(JSON) / 源码(Py)
    def _on_ast_clipboard_copy_current(self) -> None:
        """将当前 Step 对应的 StepAstNode 复制到临时剪贴板。"""

        print("[ASTEdit][clipboard_copy] begin, path=", getattr(self, "_timeline_selected_path", None))

        source_mode = getattr(self, "timeline_source_var", None)
        source_value = source_mode.get() if isinstance(source_mode, tk.StringVar) else "execution_space"
        if source_value != "ast_step_space":
            messagebox.showinfo("不可用", "仅在“瀑布流 + StepAstNode”模式下才能使用临时节点。")
            return

        exec_node, _node_type = self._timeline__resolve_exec_node()
        if not isinstance(exec_node, dict):
            messagebox.showerror("未选中", "当前没有有效的执行节点可用作源节点。")
            return

        ast_node = exec_node.get("_ast_node")
        if not isinstance(ast_node, dict):
            messagebox.showerror("无 StepAstNode", "当前节点未关联 StepAstNode（_ast_node）。")
            return

        try:
            self._ast_clipboard_node = copy.deepcopy(ast_node)
            self._ast_clipboard_mode = "copy"
            print("[ASTEdit][clipboard_copy] stored ast_node_type=", ast_node.get("ast_node_type"))
            if hasattr(self, "ast_clipboard_status_var") and isinstance(self.ast_clipboard_status_var, tk.StringVar):
                self.ast_clipboard_status_var.set("模式：复制（已缓存临时节点）")
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("复制失败", f"无法复制当前 StepAstNode：{exc}")

    def _on_ast_clipboard_cut_current(self) -> None:
        """剪切当前 Step 对应的 StepAstNode：复制到临时并从 ast_step_space 中删除。"""

        print("[ASTEdit][clipboard_cut] begin, path=", getattr(self, "_timeline_selected_path", None))

        source_mode = getattr(self, "timeline_source_var", None)
        source_value = source_mode.get() if isinstance(source_mode, tk.StringVar) else "execution_space"
        if source_value != "ast_step_space":
            messagebox.showinfo("不可用", "仅在“瀑布流 + StepAstNode”模式下才能使用临时节点。")
            return

        data = getattr(self, "_timeline_loaded_json", None)
        if not isinstance(data, dict):
            messagebox.showerror("无 JSON", "当前没有已加载的 JSON 快照，无法剪切节点。")
            return

        ast_root = data.get("ast_step_space")
        if not isinstance(ast_root, dict):
            messagebox.showerror("无 ast_step_space", "JSON 中未找到 ast_step_space 字段。")
            return

        exec_node, _node_type = self._timeline__resolve_exec_node()
        if not isinstance(exec_node, dict):
            messagebox.showerror("未选中", "当前没有有效的执行节点可供剪切。")
            return

        target_ast_node = exec_node.get("_ast_node")
        if not isinstance(target_ast_node, dict):
            messagebox.showerror("无 StepAstNode", "当前节点未关联 StepAstNode（_ast_node）。")
            return

        # 在 ast_step_space 中寻找 target_ast_node 所在的列表及索引
        def _find_parent_list(container: Any, target: dict[str, Any]) -> tuple[list[Any] | None, int]:
            if isinstance(container, list):
                for idx, item in enumerate(container):
                    if item is target:
                        return container, idx
                    res_list, res_idx = _find_parent_list(item, target)
                    if res_list is not None:
                        return res_list, res_idx
            elif isinstance(container, dict):
                for v in container.values():
                    res_list, res_idx = _find_parent_list(v, target)
                    if res_list is not None:
                        return res_list, res_idx
            return None, -1

        parent_list, index = _find_parent_list(ast_root, target_ast_node)
        if parent_list is None or index < 0:
            print(
                "[ASTEdit][error] clipboard_cut: parent_list not found for ast_node_type=",
                target_ast_node.get("ast_node_type"),
                "path=",
                getattr(self, "_timeline_selected_path", None),
            )
            messagebox.showerror("未定位", "无法在 ast_step_space 中定位当前 StepAstNode 的父列表。")
            return

        try:
            self._ast_clipboard_node = copy.deepcopy(target_ast_node)
            self._ast_clipboard_mode = "cut"
            print("[ASTEdit][clipboard_cut] stored ast_node_type=", target_ast_node.get("ast_node_type"), "at index", index)
            parent_list.pop(index)
            if hasattr(self, "ast_clipboard_status_var") and isinstance(self.ast_clipboard_status_var, tk.StringVar):
                self.ast_clipboard_status_var.set("模式：剪切（源节点已从 ast_step_space 移除）")
            messagebox.showinfo("已剪切", "已将当前 StepAstNode 剪切到临时剪贴板（尚未写回 JSON 文件）。")
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("剪切失败", f"剪切节点失败：{exc}")

        # 剪切会修改 ast_step_space，需要刷新时间线
        self._timeline__refresh_after_ast_edit()

    def _on_ast_clipboard_from_editor(self) -> None:
        """从编辑区 JSON 文本解析 StepAstNode 到临时剪贴板。"""

        print("[ASTEdit][clipboard_from_editor] begin")

        editor = getattr(self, "ast_edit_text", None)
        if not isinstance(editor, tk.Text):
            return

        raw = editor.get("1.0", tk.END).strip()
        if not raw:
            messagebox.showwarning("空内容", "编辑区为空，无法组装临时节点。")
            return

        try:
            node = json.loads(raw)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("解析失败", f"编辑区 JSON 无法解析为 StepAstNode：{exc}")
            return

        if not isinstance(node, dict) or "ast_node_type" not in node:
            messagebox.showerror("结构错误", "临时节点内容必须是带 ast_node_type 的 StepAstNode 对象。")
            return

        self._ast_clipboard_node = node
        self._ast_clipboard_mode = "assemble"
        print("[ASTEdit][clipboard_from_editor] stored ast_node_type=", node.get("ast_node_type"))
        if hasattr(self, "ast_clipboard_status_var") and isinstance(self.ast_clipboard_status_var, tk.StringVar):
            self.ast_clipboard_status_var.set("模式：组装(JSON)（已缓存临时节点）")

    def _ast__build_step_node_from_ast(self, node: ast.AST) -> Dict[str, Any]:
        """内部工具：从 ast.AST 递归构造 StepAstNode。"""

        result: Dict[str, Any] = {
            "ast_node_type": type(node).__name__,
            "fields": {},
        }

        fields_dict: Dict[str, Any] = {}
        for field_name in getattr(node, "_fields", ()):  # type: ignore[attr-defined]
            value = getattr(node, field_name, None)

            if field_name == "ctx" and value is not None:
                fields_dict[field_name] = type(value).__name__
                continue

            if isinstance(value, ast.AST):
                child = self._ast__build_step_node_from_ast(value)
                fields_dict[field_name] = child
            elif isinstance(value, list):
                items: List[Any] = []
                for item in value:
                    if isinstance(item, ast.AST):
                        items.append(self._ast__build_step_node_from_ast(item))
                    else:
                        items.append(item)
                fields_dict[field_name] = items
            elif isinstance(value, (str, int, float, bool)) or value is None:
                fields_dict[field_name] = value
            else:
                fields_dict[field_name] = type(value).__name__

        result["fields"] = fields_dict
        return result

    def _on_ast_clipboard_from_source(self) -> None:
        """通过输入一段 Python 源码，将首个语句解析为 StepAstNode 存入临时剪贴板。"""

        src = simpledialog.askstring(
            "源码到临时",
            "请输入一段 Python 语句（例如：x = a + b）\n仅使用首个语句构造临时 StepAstNode：",
            parent=self.root,
        )
        if not src:
            return

        try:
            mod = ast.parse(src)
            body = getattr(mod, "body", [])
            if not body:
                messagebox.showerror("解析失败", "源码中未解析出任何语句。")
                return
            stmt = body[0]
            step_node = self._ast__build_step_node_from_ast(stmt)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("解析失败", f"无法从源码解析临时节点：{exc}")
            return

        self._ast_clipboard_node = step_node
        self._ast_clipboard_mode = "source"
        print("[ASTEdit][clipboard_from_source] stored ast_node_type=", step_node.get("ast_node_type"))
        if hasattr(self, "ast_clipboard_status_var") and isinstance(self.ast_clipboard_status_var, tk.StringVar):
            self.ast_clipboard_status_var.set("模式：源码(Py)（已缓存临时节点）")

        editor = getattr(self, "ast_edit_text", None)
        if isinstance(editor, tk.Text):
            editor.delete("1.0", tk.END)
            editor.insert("1.0", json.dumps(step_node, ensure_ascii=False, indent=2))

    def _on_ast_source_parse_to_clipboard(self) -> None:
        """从源码 Tab 文本框解析 Python 源码到临时 StepAstNode。"""

        editor_src = getattr(self, "ast_source_text", None)
        if not isinstance(editor_src, tk.Text):
            return

        src = editor_src.get("1.0", tk.END).strip()
        if not src:
            messagebox.showwarning("空源码", "源码文本框为空，无法解析。")
            return

        try:
            mod = ast.parse(src)
            body = getattr(mod, "body", [])
            if not body:
                messagebox.showerror("解析失败", "源码中未解析出任何语句。")
                return
            stmt = body[0]
            step_node = self._ast__build_step_node_from_ast(stmt)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("解析失败", f"无法从源码解析临时节点：{exc}")
            return

        self._ast_clipboard_node = step_node
        self._ast_clipboard_mode = "source"
        print("[ASTEdit][source_tab] stored ast_node_type=", step_node.get("ast_node_type"))
        if hasattr(self, "ast_clipboard_status_var") and isinstance(self.ast_clipboard_status_var, tk.StringVar):
            self.ast_clipboard_status_var.set("模式：源码(Py)（已缓存临时节点）")

        editor = getattr(self, "ast_edit_text", None)
        if isinstance(editor, tk.Text):
            editor.delete("1.0", tk.END)
            editor.insert("1.0", json.dumps(step_node, ensure_ascii=False, indent=2))

    # -------------------- StepAstNode 模板入口：按 category 快速组装临时节点 --------------------

    def _ast__set_clipboard_template(self, node: Dict[str, Any], mode_label: str) -> None:
        """内部工具：将模板 StepAstNode 写入临时剪贴板与 JSON 编辑区。"""

        self._ast_clipboard_node = node
        self._ast_clipboard_mode = "template"
        print("[ASTEdit][template] stored ast_node_type=", node.get("ast_node_type"), "label=", mode_label)
        if hasattr(self, "ast_clipboard_status_var") and isinstance(self.ast_clipboard_status_var, tk.StringVar):
            self.ast_clipboard_status_var.set(f"模式：模板({mode_label})（已缓存临时节点）")

        editor = getattr(self, "ast_edit_text", None)
        if isinstance(editor, tk.Text):
            editor.delete("1.0", tk.END)
            editor.insert("1.0", json.dumps(node, ensure_ascii=False, indent=2))

    def _on_ast_template_if_simple(self) -> None:
        """模板：简单 If 语句: if cond: pass"""

        # test 使用 Name("cond", ctx=Load)，body 中给一个占位 Expr(Constant(True))，方便后续替换。
        test_node: Dict[str, Any] = {
            "ast_node_type": "Name",
            "fields": {
                "id": "cond",
                "ctx": "Load",
            },
        }
        body_expr: Dict[str, Any] = {
            "ast_node_type": "Expr",
            "fields": {
                "value": {
                    "ast_node_type": "Constant",
                    "fields": {"value": True},
                },
            },
        }
        if_node: Dict[str, Any] = {
            "ast_node_type": "If",
            "fields": {
                "test": test_node,
                "body": [body_expr],
                "orelse": [],
            },
        }

        self._ast__set_clipboard_template(if_node, "control:If")

    def _on_ast_template_assign_simple(self) -> None:
        """模板：简单赋值语句: x = y"""

        target_node: Dict[str, Any] = {
            "ast_node_type": "Name",
            "fields": {
                "id": "x",
                "ctx": "Store",
            },
        }
        value_node: Dict[str, Any] = {
            "ast_node_type": "Name",
            "fields": {
                "id": "y",
                "ctx": "Load",
            },
        }
        assign_node: Dict[str, Any] = {
            "ast_node_type": "Assign",
            "fields": {
                "targets": [target_node],
                "value": value_node,
                "type_comment": None,
            },
        }

        self._ast__set_clipboard_template(assign_node, "data:Assign")

    def _on_ast_template_call_simple(self) -> None:
        """模板：函数调用表达式: foo(x, y)"""

        func_node: Dict[str, Any] = {
            "ast_node_type": "Name",
            "fields": {
                "id": "foo",
                "ctx": "Load",
            },
        }
        arg_x: Dict[str, Any] = {
            "ast_node_type": "Name",
            "fields": {
                "id": "x",
                "ctx": "Load",
            },
        }
        arg_y: Dict[str, Any] = {
            "ast_node_type": "Name",
            "fields": {
                "id": "y",
                "ctx": "Load",
            },
        }
        call_node: Dict[str, Any] = {
            "ast_node_type": "Call",
            "fields": {
                "func": func_node,
                "args": [arg_x, arg_y],
                "keywords": [],
            },
        }

        self._ast__set_clipboard_template(call_node, "call:Call")

    def _on_ast_template_method_call(self) -> None:
        """模板：方法调用表达式: obj.m()"""

        value_node: Dict[str, Any] = {
            "ast_node_type": "Name",
            "fields": {
                "id": "obj",
                "ctx": "Load",
            },
        }
        attr_node: Dict[str, Any] = {
            "ast_node_type": "Attribute",
            "fields": {
                "value": value_node,
                "attr": "m",
                "ctx": "Load",
            },
        }
        call_node: Dict[str, Any] = {
            "ast_node_type": "Call",
            "fields": {
                "func": attr_node,
                "args": [],
                "keywords": [],
            },
        }

        self._ast__set_clipboard_template(call_node, "call:MethodCall")

    def _on_ast_template_binop_add(self) -> None:
        """模板：二元运算表达式: a + b"""

        left_node: Dict[str, Any] = {
            "ast_node_type": "Name",
            "fields": {
                "id": "a",
                "ctx": "Load",
            },
        }
        right_node: Dict[str, Any] = {
            "ast_node_type": "Name",
            "fields": {
                "id": "b",
                "ctx": "Load",
            },
        }
        binop_node: Dict[str, Any] = {
            "ast_node_type": "BinOp",
            "fields": {
                "left": left_node,
                "op": "Add",  # 使用字符串标记操作符，便于在 JSON 中编辑为其它运算
                "right": right_node,
            },
        }

        self._ast__set_clipboard_template(binop_node, "expr:BinOp(+)")

    def _on_ast_template_try_simple(self) -> None:
        """模板：简单 Try/Except 结构。"""

        # try 区块主体：占位 Expr(Constant(True))，供后续替换
        try_body_expr: Dict[str, Any] = {
            "ast_node_type": "Expr",
            "fields": {
                "value": {
                    "ast_node_type": "Constant",
                    "fields": {"value": True},
                },
            },
        }

        # except 区块主体：占位 Expr(Call(Name("handle_error")))
        handler_call_node: Dict[str, Any] = {
            "ast_node_type": "Call",
            "fields": {
                "func": {
                    "ast_node_type": "Name",
                    "fields": {"id": "handle_error", "ctx": "Load"},
                },
                "args": [],
                "keywords": [],
            },
        }
        handler_body_expr: Dict[str, Any] = {
            "ast_node_type": "Expr",
            "fields": {
                "value": handler_call_node,
            },
        }

        except_handler_node: Dict[str, Any] = {
            "ast_node_type": "ExceptHandler",
            "fields": {
                "type": {
                    "ast_node_type": "Name",
                    "fields": {"id": "Exception", "ctx": "Load"},
                },
                "name": "e",
                "body": [handler_body_expr],
            },
        }

        try_node: Dict[str, Any] = {
            "ast_node_type": "Try",
            "fields": {
                "body": [try_body_expr],
                "handlers": [except_handler_node],
                "orelse": [],
                "finalbody": [],
            },
        }

        self._ast__set_clipboard_template(try_node, "exception:Try/Except")
    # ------------------------------------------------------------------
    # AST 模板区域：自动分类与槽位选择
    # ------------------------------------------------------------------

    def _ast__classify_node_category(self, ast_node_type: str | None) -> tuple[str, str]:
        """根据 ast_node_type 返回 (category_key, sub_key)。

        category_key 对应外层中文 Tab：
        - "control" / "data" / "call" / "expr" / "exception" / "async" / "import" / "structure"
        sub_key 对应子 Notebook 中的具体 Tab 选择。
        未识别时尽量落在 "expr" / "structure" 等泛用类。
        """

        t = ast_node_type or ""
        # 控制流
        if t in {"If", "IfExp"}:
            return "control", "If" if t == "If" else "IfExp"
        if t in {"For", "While", "AsyncFor", "Break", "Continue", "Return"}:
            mapping = {
                "For": ("control", "For"),
                "While": ("control", "While"),
                "AsyncFor": ("control", "AsyncFor"),
                "Break": ("control", "Break/Continue"),
                "Continue": ("control", "Break/Continue"),
                "Return": ("control", "Return"),
            }
            return mapping.get(t, ("control", "If"))

        # 数据流/赋值
        if t in {"Assign", "AnnAssign", "AugAssign"}:
            mapping = {
                "Assign": ("data", "Assign"),
                "AnnAssign": ("data", "AnnAssign"),
                "AugAssign": ("data", "AugAssign"),
            }
            return mapping[t]
        if t in {"Name", "Attribute"}:
            return "data", "Name/Attribute"

        # 调用/接口
        if t == "Call":
            return "call", "Call"
        if t == "keyword":
            return "call", "Keywords"

        # 表达式/常量
        if t in {"Constant", "Num", "Str"}:
            return "expr", "Constant"
        if t == "BinOp":
            return "expr", "BinOp"
        if t in {"UnaryOp", "BoolOp"}:
            return "expr", "Unary/BooOp"
        if t == "Compare":
            return "expr", "Compare"

        # 异常与上下文管理
        if t == "Try":
            return "exception", "Try/Except"
        if t == "Raise":
            return "exception", "Raise"
        if t == "Assert":
            return "exception", "Assert"
        if t == "With":
            return "exception", "With"
        if t == "AsyncWith":
            return "exception", "AsyncWith"

        # 异步/模式匹配
        if t == "AsyncFunctionDef":
            return "async", "AsyncFunctionDef"
        if t == "Await":
            return "async", "Await"
        if t in {"Yield", "YieldFrom"}:
            return "async", "Yield/YieldFrom"
        if t == "Match":
            return "async", "Match"

        # 导入与模块组织
        if t == "Import":
            return "import", "Import"
        if t == "ImportFrom":
            return "import", "ImportFrom"

        # 结构/作用域
        if t == "Module":
            return "structure", "Module"
        if t in {"FunctionDef", "Lambda"}:
            return "structure", "Function/Lambda"
        if t == "ClassDef":
            return "structure", "Class"

        # 默认回退：表达式或结构
        if t:
            return "expr", "Other"
        return "structure", "Block/Scope"

    def _ast__auto_select_template_tabs(self, ast_node_type: str | None) -> None:
        """根据 ast_node_type 自动切换模板 Notebook 的父/子 Tab。"""

        category, sub = self._ast__classify_node_category(ast_node_type)

        parent_nb = getattr(self, "ast_template_nb", None)
        if not isinstance(parent_nb, ttk.Notebook):
            return

        # 1. 选择外层父 Tab
        parent_index_map = {
            "control": self.ast_template_control_tab,
            "data": self.ast_template_data_tab,
            "call": self.ast_template_call_tab,
            "expr": self.ast_template_expr_tab,
            "exception": self.ast_template_exception_tab,
            "async": self.ast_template_async_tab,
            "import": self.ast_template_import_tab,
            "structure": self.ast_template_meta_tab,
        }
        parent_tab = parent_index_map.get(category)
        if parent_tab is not None:
            try:
                parent_nb.select(parent_tab)
            except tk.TclError:
                pass

        # 2. 选择对应分类下的子 Tab
        try:
            if category == "control":
                nb = getattr(self, "ast_control_nb", None)
                if isinstance(nb, ttk.Notebook):
                    mapping = {
                        "If": self.ast_control_if_tab,
                        "For": self.ast_control_for_tab,
                        "While": self.ast_control_while_tab,
                        "AsyncFor": self.ast_control_asyncfor_tab,
                        "Break/Continue": self.ast_control_break_tab,
                        "Return": self.ast_control_return_tab,
                        "IfExp": self.ast_control_ifexp_tab,
                    }
                    tab = mapping.get(sub)
                    if tab is not None:
                        nb.select(tab)
            elif category == "data":
                nb = getattr(self, "ast_data_nb", None)
                if isinstance(nb, ttk.Notebook):
                    mapping = {
                        "Assign": self.ast_data_assign_tab,
                        "AnnAssign": self.ast_data_annassign_tab,
                        "AugAssign": self.ast_data_augassign_tab,
                        "Name/Attribute": self.ast_data_name_attr_tab,
                        "Other": self.ast_data_other_tab,
                    }
                    tab = mapping.get(sub)
                    if tab is not None:
                        nb.select(tab)
            elif category == "call":
                nb = getattr(self, "ast_call_nb", None)
                if isinstance(nb, ttk.Notebook):
                    mapping = {
                        "Call": self.ast_call_call_tab,
                        "MethodCall": self.ast_call_method_tab,
                        "Args": self.ast_call_args_tab,
                        "Keywords": self.ast_call_keywords_tab,
                        "Interface": self.ast_call_interface_tab,
                    }
                    tab = mapping.get(sub)
                    if tab is not None:
                        nb.select(tab)
            elif category == "expr":
                nb = getattr(self, "ast_expr_nb", None)
                if isinstance(nb, ttk.Notebook):
                    mapping = {
                        "Constant": self.ast_expr_const_tab,
                        "BinOp": self.ast_expr_binop_tab,
                        "Unary/BooOp": self.ast_expr_op_tab,
                        "Compare": self.ast_expr_compare_tab,
                        "Comprehension": self.ast_expr_comprehension_tab,
                        "Other": self.ast_expr_other_tab,
                    }
                    tab = mapping.get(sub)
                    if tab is not None:
                        nb.select(tab)
            elif category == "exception":
                nb = getattr(self, "ast_exception_nb", None)
                if isinstance(nb, ttk.Notebook):
                    mapping = {
                        "Try/Except": self.ast_exception_try_tab,
                        "Raise": self.ast_exception_raise_tab,
                        "Assert": self.ast_exception_assert_tab,
                        "With": self.ast_exception_with_tab,
                        "AsyncWith": self.ast_exception_asyncwith_tab,
                    }
                    tab = mapping.get(sub)
                    if tab is not None:
                        nb.select(tab)
            elif category == "async":
                nb = getattr(self, "ast_async_nb", None)
                if isinstance(nb, ttk.Notebook):
                    mapping = {
                        "AsyncFunctionDef": self.ast_async_def_tab,
                        "Await": self.ast_async_await_tab,
                        "Yield/YieldFrom": self.ast_async_yield_tab,
                        "Match": self.ast_async_match_tab,
                    }
                    tab = mapping.get(sub)
                    if tab is not None:
                        nb.select(tab)
            elif category == "import":
                nb = getattr(self, "ast_import_nb", None)
                if isinstance(nb, ttk.Notebook):
                    mapping = {
                        "Import": self.ast_import_import_tab,
                        "ImportFrom": self.ast_import_from_tab,
                        "alias": self.ast_import_alias_tab,
                        "Organize": self.ast_import_organize_tab,
                    }
                    tab = mapping.get(sub)
                    if tab is not None:
                        nb.select(tab)
            elif category == "structure":
                nb = getattr(self, "ast_structure_nb", None)
                if isinstance(nb, ttk.Notebook):
                    mapping = {
                        "Module": self.ast_structure_module_tab,
                        "Function/Lambda": self.ast_structure_function_tab,
                        "Class": self.ast_structure_class_tab,
                        "Block/Scope": self.ast_structure_other_tab,
                    }
                    tab = mapping.get(sub)
                    if tab is not None:
                        nb.select(tab)
        except tk.TclError:
            # UI 刷新期间 Notebook 可能暂不可用，忽略异常
            pass

    def _on_ast_slot_selected(self, _event: tk.Event) -> None:  # type: ignore[override]
        """用户从下拉中选择了某个 AST 槽位，更新状态提示。"""

        idx = -1
        combo = getattr(self, "ast_slot_combo", None)
        if isinstance(combo, ttk.Combobox):
            try:
                idx = combo.current()
            except tk.TclError:
                idx = -1

        items = getattr(self, "_ast_slot_items", [])
        if not isinstance(items, list) or idx < 0 or idx >= len(items):
            self.ast_slot_status_var.set("槽位状态：未选中")
            return

        slot = items[idx]
        desc = slot.get("label") or ""
        accept = slot.get("accept_categories") or []
        accept_text = ",".join(accept) if accept else "任意（实验）"
        self.ast_slot_status_var.set(f"槽位状态：{desc} | 可接类别：{accept_text}")
    def _timeline__resolve_exec_node(self) -> tuple[dict[str, Any] | None, str]:
        """基于 _timeline_selected_path 返回当前 exec 节点及其类型(space/step/branch)。"""

        space = self._timeline_root_space
        path_key: str | None = getattr(self, "_timeline_selected_path", None)
        if not isinstance(space, dict) or not path_key:
            return None, "space"

        parts = [int(p) for p in path_key.split("-") if p != ""]
        if not parts:
            return None, "space"

        node: dict[str, Any] | dict = space
        node_type: str = "space"

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
        for idx in parts:
            if not children or idx < 0 or idx >= len(children):
                return None, node_type
            candidate = children[idx]
            if not isinstance(candidate, dict):
                return None, node_type
            node = candidate
            node_type = child_type
            children, child_type = _get_children(node, node_type)

        if not isinstance(node, dict):
            return None, node_type
        return node, node_type

    def _timeline__analyze_ast_slots(self) -> None:
        """调试辅助：解析当前选中时间线节点在 ast_step_space 中的父容器及可编辑槽位。

        - 父容器：
          - 若为列表元素，则 container_type="list"，可做删除/同级插入/替换；
          - 若为 dict 字段，则 container_type="dict"，可做占位点替换；
        - 当前节点自身：
          - 列出其 fields 中所有 list 字段（可作为子列表插入位置）；
          - 列出其 fields 中所有子 StepAstNode 字段（可作为子表达式替换占位点）。
        结果通过 print 打印在终端，前缀为 [ASTEdit][analyze]。
        """

        print("[ASTEdit][analyze] begin, path=", getattr(self, "_timeline_selected_path", None))

        source_mode = getattr(self, "timeline_source_var", None)
        source_value = source_mode.get() if isinstance(source_mode, tk.StringVar) else "execution_space"
        if source_value != "ast_step_space":
            print("[ASTEdit][analyze] skip: source is not ast_step_space, got=", source_value)
            return

        data = getattr(self, "_timeline_loaded_json", None)
        if not isinstance(data, dict):
            print("[ASTEdit][analyze] no loaded JSON snapshot")
            return

        ast_root = data.get("ast_step_space")
        if not isinstance(ast_root, dict):
            print("[ASTEdit][analyze] no ast_step_space in JSON")
            return

        exec_node, node_type = self._timeline__resolve_exec_node()
        if not isinstance(exec_node, dict):
            print("[ASTEdit][analyze] no valid exec_node for current path")
            return

        ast_node = exec_node.get("_ast_node")
        if not isinstance(ast_node, dict):
            print("[ASTEdit][analyze] current exec_node has no _ast_node binding")
            return

        def _find_parent_container(
            container: Any,
            target: dict[str, Any],
        ) -> tuple[str | None, Any | None, int | None, str | None]:
            """在 ast_step_space 中递归查找 target 所在的父容器。"""

            if isinstance(container, list):
                for idx, item in enumerate(container):
                    if item is target:
                        return "list", container, idx, None
                    c_type, c_parent, c_index, c_key = _find_parent_container(item, target)
                    if c_type is not None:
                        return c_type, c_parent, c_index, c_key
            elif isinstance(container, dict):
                for k, v in container.items():
                    if v is target:
                        return "dict", container, None, k
                    c_type, c_parent, c_index, c_key = _find_parent_container(v, target)
                    if c_type is not None:
                        return c_type, c_parent, c_index, c_key
            return None, None, None, None

        container_type, parent, index, key = _find_parent_container(ast_root, ast_node)

        # 进一步：基于 StepAstNode 语义找到“父级 StepAstNode”
        def _find_parent_step_node(
            container: Any,
            target: dict[str, Any],
            parent_step: dict[str, Any] | None,
        ) -> dict[str, Any] | None:
            """在 StepAstNode 树中查找 target 所属的父级 StepAstNode（按 fields 关系）。"""

            if container is target:
                return parent_step

            # StepAstNode 自身作为后续子树的 parent_step
            if isinstance(container, dict):
                next_parent = container if container.get("ast_node_type") else parent_step
                for v in container.values():
                    found = _find_parent_step_node(v, target, next_parent)
                    if found is not None:
                        return found
            elif isinstance(container, list):
                for item in container:
                    found = _find_parent_step_node(item, target, parent_step)
                    if found is not None:
                        return found
            return None

        parent_step = _find_parent_step_node(ast_root, ast_node, None)

        # 当前节点与父级节点各自的字段分析（仅关注 fields 下的 StepAstNode / StepAstNode 列表）
        def _collect_slots_for_node(owner: str, node: dict[str, Any], slot_items: list[dict[str, Any]]) -> None:
            fields = node.get("fields")
            if not isinstance(fields, dict):
                return

            label_prefix = "父级" if owner == "parent" else "当前"

            for fname, value in fields.items():
                # list 类型字段：既有“替换已有元素”的槽位，也有“插入新元素”的槽位
                if isinstance(value, list):
                    # 替换：fields['name'][i]
                    for i, item in enumerate(value):
                        if not isinstance(item, dict) or not item.get("ast_node_type"):
                            continue
                        cur_flag = "（当前节点）" if item is ast_node else ""
                        slot_label = f"[{label_prefix}-替换] fields['{fname}'][{i}]{cur_flag}"
                        slot_path = f"fields['{fname}'][{i}]"

                        accept = ["control", "data", "call", "expr", "exception"]

                        slot_items.append(
                            {
                                "label": slot_label,
                                "slot": slot_path,
                                "owner": owner,
                                "action": "replace",
                                "kind": "replace",
                                "container": value,
                                "container_type": "list",
                                "field_name": fname,
                                "index": i,
                                "index_or_key": i,
                                "accept_categories": accept,
                            }
                        )

                    # 插入：在该列表尾部插入一个新的子节点
                    size = len(value)
                    slot_label = f"[{label_prefix}-插入] fields['{fname}'] (len={size})"
                    slot_path = f"fields['{fname}']"
                    accept = ["control", "data", "call", "expr", "exception"]

                    slot_items.append(
                        {
                            "label": slot_label,
                            "slot": slot_path,
                            "owner": owner,
                            "action": "insert",
                            "kind": "insert",
                            "container": value,
                            "container_type": "list",
                            "field_name": fname,
                            "index": size,
                            "index_or_key": size,
                            "accept_categories": accept,
                        }
                    )

                # 单个子 StepAstNode 字段：只能做替换
                elif isinstance(value, dict) and value.get("ast_node_type"):
                    cur_flag = "（当前节点）" if value is ast_node else ""
                    slot_label = f"[{label_prefix}-替换] fields['{fname}']{cur_flag}"
                    slot_path = f"fields['{fname}']"
                    accept = ["expr", "call", "data"]

                    slot_items.append(
                        {
                            "label": slot_label,
                            "slot": slot_path,
                            "owner": owner,
                            "action": "replace",
                            "kind": "replace",
                            "container": fields,
                            "container_type": "dict",
                            "field_name": fname,
                            "index": None,
                            "index_or_key": fname,
                            "accept_categories": accept,
                        }
                    )

        # 终端调试输出：当前节点自身 fields 的基本信息
        fields = ast_node.get("fields")
        list_fields: list[str] = []
        list_field_sizes: dict[str, int] = {}
        dict_child_fields: list[str] = []

        if isinstance(fields, dict):
            for fname, value in fields.items():
                if isinstance(value, list):
                    list_fields.append(fname)
                    list_field_sizes[fname] = len(value)
                elif isinstance(value, dict) and value.get("ast_node_type"):
                    dict_child_fields.append(fname)

        # 终端调试输出
        print("[ASTEdit][analyze] node_type=", ast_node.get("ast_node_type"), "exec_node_type=", node_type)
        print("[ASTEdit][analyze] parent_container_type=", container_type, "index=", index, "key=", key)
        print("[ASTEdit][analyze] list_fields=", list_fields, "sizes=", list_field_sizes)
        print("[ASTEdit][analyze] dict_child_fields=", dict_child_fields)
        if isinstance(parent_step, dict):
            print("[ASTEdit][analyze] parent_step_type=", parent_step.get("ast_node_type"))

        # 构建槽位下拉选项：分别收集“父级节点字段槽位”和“当前节点字段槽位”
        slot_items: list[dict[str, Any]] = []
        if isinstance(parent_step, dict):
            _collect_slots_for_node("parent", parent_step, slot_items)
        _collect_slots_for_node("current", ast_node, slot_items)

        print("[ASTEdit][analyze] slot_items_total=", len(slot_items))

        # 同步写入 UI 中的“AST 槽位分析”Tab
        editor = getattr(self, "ast_analyze_text", None)
        if isinstance(editor, tk.Text):
            try:
                editor.configure(state="normal")
                editor.delete("1.0", tk.END)

                lines: list[str] = []
                lines.append(f"path: {getattr(self, '_timeline_selected_path', None)}")
                lines.append(f"node_type: {ast_node.get('ast_node_type')}")
                lines.append(f"exec_node_type: {node_type}")
                lines.append("")
                lines.append(f"parent_container_type: {container_type}, index={index}, key={key}")
                lines.append("")
                lines.append(f"list_fields: {list_fields}")
                lines.append(f"list_field_sizes: {list_field_sizes}")
                lines.append(f"dict_child_fields: {dict_child_fields}")
                if isinstance(parent_step, dict):
                    lines.append(f"parent_step_type: {parent_step.get('ast_node_type')}")
                lines.append("")
                lines.append("replace_slots:")
                for item in slot_items:
                    if item.get("action") == "replace":
                        lines.append(
                            f"  - [{item.get('owner')}] {item.get('slot')}: "
                            f"container_type={item.get('container_type')}, "
                            f"field={item.get('field_name')}, index={item.get('index')}"
                        )
                lines.append("")
                lines.append("insert_slots:")
                for item in slot_items:
                    if item.get("action") in ("insert", "insert_list"):
                        lines.append(
                            f"  - [{item.get('owner')}] {item.get('slot')}: "
                            f"container_type={item.get('container_type')}, "
                            f"field={item.get('field_name')}, index={item.get('index')}"
                        )

                editor.insert("1.0", "\n".join(lines))
            finally:
                editor.configure(state="disabled")

        # 自动切换模板 Tab（父 Tab + 节点孙 Tab）
        try:
            self._ast__auto_select_template_tabs(ast_node.get("ast_node_type"))
        except Exception:
            # 分类失败不影响其他功能
            pass

        self._ast_slot_items = slot_items

        combo = getattr(self, "ast_slot_combo", None)
        if isinstance(combo, ttk.Combobox):
            labels = [item.get("label", "") for item in slot_items]
            combo["values"] = labels
            # 默认选中第一个槽位（如果有）
            if labels:
                try:
                    combo.current(0)
                except tk.TclError:
                    pass
                # 主动触发一次状态更新
                try:
                    self._on_ast_slot_selected(None)  # type: ignore[arg-type]
                except Exception:
                    pass
            else:
                self.ast_slot_var.set("（无可编辑槽位）")
                self.ast_slot_status_var.set("槽位状态：无可编辑槽位")

    def _timeline__refresh_after_ast_edit(self) -> None:
        """在 ast_step_space 被就地修改后，基于内存中的 JSON 重新构造时间线视图。

        仅在 "瀑布流 + StepAstNode" 模式下生效，不重新读取/写入文件。
        """

        source_mode = getattr(self, "timeline_source_var", None)
        source_value = source_mode.get() if isinstance(source_mode, tk.StringVar) else "execution_space"
        if source_value != "ast_step_space":
            return

        data = getattr(self, "_timeline_loaded_json", None)
        if not isinstance(data, dict):
            return

        ast_root = data.get("ast_step_space")
        if not isinstance(ast_root, dict):
            return

        if ast_root.get("ast_node_type") != "FunctionDef":
            return

        def _build_exec_from_step_ast(node: Dict[str, Any]) -> Dict[str, Any]:
            fields = node.get("fields") or {}

            children: list[Dict[str, Any]] = []
            for value in fields.values():
                if isinstance(value, dict):
                    if value.get("ast_node_type"):
                        children.append(_build_exec_from_step_ast(value))
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict) and item.get("ast_node_type"):
                            children.append(_build_exec_from_step_ast(item))

            step: Dict[str, Any] = {
                "scope_level": "ast_step",
                "scope_in": node.get("scope_in") or {},
                "scope_out": node.get("scope_out") or {},
                "kind": node.get("ast_node_type"),
                "code": None,
                "exec_queue": children,
                "_ast_node": node,
            }
            return step

        fields = ast_root.get("fields") or {}
        body = fields.get("body") or []
        exec_queue: list[Dict[str, Any]] = []
        if isinstance(body, list):
            for stmt in body:
                if not isinstance(stmt, dict) or not stmt.get("ast_node_type"):
                    continue
                exec_queue.append(_build_exec_from_step_ast(stmt))

        space: Dict[str, Any] = {
            "scope_level": "function",
            "scope_in": ast_root.get("scope_in") or {},
            "scope_out": ast_root.get("scope_out") or {},
            "exec_queue": exec_queue,
            "_ast_root": ast_root,
        }

        self._timeline_root_space = space
        self._timeline_hit_regions = []

        try:
            self._render_execution_timeline(space)
        except Exception:
            pass

        try:
            self._update_step_detail()
        except Exception:
            pass

    def _on_ast_slot_apply_clipboard(self) -> None:
        """根据当前槽位选择，将临时 StepAstNode 应用到对应槽位（替换/插入）。"""

        # 需要有有效的临时节点
        if not isinstance(getattr(self, "_ast_clipboard_node", None), dict) or "ast_node_type" not in self._ast_clipboard_node:
            messagebox.showwarning("无临时节点", "当前没有有效的临时 StepAstNode，可通过上方模板或入口按钮生成。")
            return

        # 仅在瀑布流 + StepAstNode 模式下生效
        source_mode = getattr(self, "timeline_source_var", None)
        source_value = source_mode.get() if isinstance(source_mode, tk.StringVar) else "execution_space"
        if source_value != "ast_step_space":
            messagebox.showinfo("不可用", "仅在“瀑布流 + StepAstNode”模式下才能按槽位应用临时节点。")
            return

        data = getattr(self, "_timeline_loaded_json", None)
        if not isinstance(data, dict):
            messagebox.showerror("无 JSON", "当前没有已加载的 JSON 快照，无法应用槽位操作。")
            return

        ast_root = data.get("ast_step_space")
        if not isinstance(ast_root, dict):
            messagebox.showerror("无 ast_step_space", "JSON 中未找到 ast_step_space 字段。")
            return

        exec_node, node_type = self._timeline__resolve_exec_node()
        if not isinstance(exec_node, dict):
            messagebox.showerror("未选中", "当前没有有效的执行节点可供槽位应用。")
            return

        ast_node = exec_node.get("_ast_node")
        if not isinstance(ast_node, dict):
            messagebox.showerror("无 StepAstNode", "当前节点未关联 StepAstNode（_ast_node）。")
            return

        # 解析父容器信息，供 parent_list / parent_dict 槽位使用
        def _find_parent_container(container: Any, target: dict[str, Any]) -> tuple[str | None, Any | None, int | None, str | None]:
            if isinstance(container, list):
                for idx, item in enumerate(container):
                    if item is target:
                        return "list", container, idx, None
                    c_type, c_parent, c_index, c_key = _find_parent_container(item, target)
                    if c_type is not None:
                        return c_type, c_parent, c_index, c_key
            elif isinstance(container, dict):
                for k, v in container.items():
                    if v is target:
                        return "dict", container, None, k
                    c_type, c_parent, c_index, c_key = _find_parent_container(v, target)
                    if c_type is not None:
                        return c_type, c_parent, c_index, c_key
            return None, None, None, None

        container_type, parent, parent_index, parent_key = _find_parent_container(ast_root, ast_node)

        # 读取当前槽位选择
        items = getattr(self, "_ast_slot_items", [])
        combo = getattr(self, "ast_slot_combo", None)
        idx = -1
        if isinstance(combo, ttk.Combobox):
            try:
                idx = combo.current()
            except tk.TclError:
                idx = -1

        if idx is None or idx < 0 or idx >= len(items):
            # 尝试通过文本匹配
            current_label = self.ast_slot_var.get() if hasattr(self, "ast_slot_var") else ""
            for i, it in enumerate(items):
                if it.get("label") == current_label:
                    idx = i
                    break

        if not isinstance(items, list) or idx is None or idx < 0 or idx >= len(items):
            messagebox.showwarning("未选中槽位", "请先在下拉框中选择一个槽位。")
            return

        slot_info = items[idx]
        slot_path = slot_info.get("slot")
        slot_kind = slot_info.get("kind")
        index_or_key = slot_info.get("index_or_key")

        if not isinstance(slot_path, str) or not isinstance(slot_kind, str):
            messagebox.showerror("槽位错误", "当前槽位信息不完整，无法应用。")
            return

        node_to_insert = copy.deepcopy(self._ast_clipboard_node)

        try:
            container_obj = slot_info.get("container")
            container_kind2 = slot_info.get("container_type")
            field_name = slot_info.get("field_name")
            action = slot_info.get("action") or slot_kind

            handled = False
            if container_obj is not None and isinstance(container_kind2, str):
                if container_kind2 == "list":
                    lst = container_obj
                    if not isinstance(lst, list):
                        raise RuntimeError("槽位声明为 list 容器，但实际对象不是列表。")
                    if action == "replace":
                        if not isinstance(index_or_key, int) or index_or_key < 0 or index_or_key >= len(lst):
                            raise RuntimeError("列表索引超出范围，无法替换。")
                        lst[index_or_key] = node_to_insert
                    elif action in ("insert", "insert_list"):
                        if isinstance(index_or_key, int) and 0 <= index_or_key <= len(lst):
                            pos = index_or_key
                        else:
                            pos = len(lst)
                        lst.insert(pos, node_to_insert)
                    else:
                        raise RuntimeError(f"不支持的列表槽位操作: {action}")
                    handled = True
                elif container_kind2 == "dict":
                    dct = container_obj
                    if not isinstance(dct, dict):
                        raise RuntimeError("槽位声明为 dict 容器，但实际对象不是字典。")
                    if action not in ("replace",):
                        raise RuntimeError("字典字段槽位目前仅支持替换操作。")
                    if not isinstance(field_name, str):
                        raise RuntimeError("槽位缺少字段名，无法定位字典键。")
                    dct[field_name] = node_to_insert
                    handled = True

            if not handled:
                if slot_kind == "replace":
                    if slot_path.startswith("parent_list"):
                        if container_type != "list" or not isinstance(parent, list) or not isinstance(parent_index, int):
                            raise RuntimeError("父列表信息缺失，无法替换 parent_list[index]。")
                        parent[parent_index] = node_to_insert
                    elif slot_path.startswith("parent_dict"):
                        if container_type != "dict" or not isinstance(parent, dict) or not isinstance(parent_key, str):
                            raise RuntimeError("父字典信息缺失，无法替换 parent_dict[key]。")
                        parent[parent_key] = node_to_insert
                    elif slot_path.startswith("fields["):
                        fields = ast_node.get("fields")
                        if not isinstance(fields, dict):
                            raise RuntimeError("当前 StepAstNode 缺少 fields 信息，无法应用槽位。")

                        start = len("fields['")
                        end = slot_path.find("']", start)
                        if end <= start:
                            raise RuntimeError(f"无法解析槽位字段名: {slot_path}")
                        fname = slot_path[start:end]

                        if "]" in slot_path[end + 2 :]:
                            if not isinstance(index_or_key, int):
                                raise RuntimeError("槽位 index_or_key 非整数，无法定位列表索引。")
                            lst = fields.get(fname)
                            if not isinstance(lst, list):
                                raise RuntimeError(f"字段 {fname!r} 不是列表，无法按索引替换。")
                            if index_or_key < 0 or index_or_key >= len(lst):
                                raise RuntimeError("列表索引超出范围。")
                            lst[index_or_key] = node_to_insert
                        else:
                            fields[fname] = node_to_insert
                    else:
                        raise RuntimeError(f"不支持的替换槽位类型: {slot_path}")

                elif slot_kind in ("insert_list", "insert"):
                    if not slot_path.startswith("fields["):
                        raise RuntimeError("插入列表槽位目前仅支持 fields[...] 形式。")

                    fields = ast_node.get("fields")
                    if not isinstance(fields, dict):
                        raise RuntimeError("当前 StepAstNode 缺少 fields 信息，无法应用槽位。")

                    start = len("fields['")
                    end = slot_path.find("']", start)
                    if end <= start:
                        raise RuntimeError(f"无法解析槽位字段名: {slot_path}")
                    fname = slot_path[start:end]

                    lst = fields.get(fname)
                    if not isinstance(lst, list):
                        raise RuntimeError(f"字段 {fname!r} 不是列表，无法插入节点。")

                    if isinstance(index_or_key, int) and 0 <= index_or_key <= len(lst):
                        pos2 = index_or_key
                    else:
                        pos2 = len(lst)
                    lst.insert(pos2, node_to_insert)
                else:
                    raise RuntimeError(f"未知槽位类型: {slot_kind}")
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("应用失败", f"按槽位应用临时节点失败：{exc}")
            return

        print("[ASTEdit][slot_apply] kind=", slot_kind, "slot=", slot_path, "index_or_key=", index_or_key,
              "ast_node_type=", self._ast_clipboard_node.get("ast_node_type"))
        messagebox.showinfo("已应用", "已根据当前槽位将临时 StepAstNode 应用到 ast_step_space（尚未写回 JSON 文件）。")

        # 修改 ast_step_space 后刷新时间线
        self._timeline__refresh_after_ast_edit()

    # 基于临时节点剪贴板的四个出口操作：删除 / 替换 / 插入同级 / 插入子级

    def _on_ast_clipboard_delete_current(self) -> None:
        """在 ast_step_space 中删除当前 StepAstNode。"""

        print("[ASTEdit][clipboard_delete] begin, path=", getattr(self, "_timeline_selected_path", None))

        source_mode = getattr(self, "timeline_source_var", None)
        source_value = source_mode.get() if isinstance(source_mode, tk.StringVar) else "execution_space"
        if source_value != "ast_step_space":
            messagebox.showinfo("不可用", "仅在“瀑布流 + StepAstNode”模式下才能删除 StepAstNode。")
            return

        data = getattr(self, "_timeline_loaded_json", None)
        if not isinstance(data, dict):
            messagebox.showerror("无 JSON", "当前没有已加载的 JSON 快照，无法删除节点。")
            return

        ast_root = data.get("ast_step_space")
        if not isinstance(ast_root, dict):
            messagebox.showerror("无 ast_step_space", "JSON 中未找到 ast_step_space 字段。")
            return

        exec_node, _node_type = self._timeline__resolve_exec_node()
        if not isinstance(exec_node, dict):
            messagebox.showerror("未选中", "当前没有有效的执行节点可供删除。")
            return

        target_ast_node = exec_node.get("_ast_node")
        if not isinstance(target_ast_node, dict):
            messagebox.showerror("无 StepAstNode", "当前节点未关联 StepAstNode（_ast_node）。")
            return

        def _find_parent_list(container: Any, target: dict[str, Any]) -> tuple[list[Any] | None, int]:
            if isinstance(container, list):
                for idx, item in enumerate(container):
                    if item is target:
                        return container, idx
                    res_list, res_idx = _find_parent_list(item, target)
                    if res_list is not None:
                        return res_list, res_idx
            elif isinstance(container, dict):
                for v in container.values():
                    res_list, res_idx = _find_parent_list(v, target)
                    if res_list is not None:
                        return res_list, res_idx
            return None, -1

        parent_list, index = _find_parent_list(ast_root, target_ast_node)
        if parent_list is None or index < 0:
            print(
                "[ASTEdit][error] clipboard_delete: parent_list not found for ast_node_type=",
                target_ast_node.get("ast_node_type"),
                "path=",
                getattr(self, "_timeline_selected_path", None),
            )
            messagebox.showerror("未定位", "无法在 ast_step_space 中定位当前 StepAstNode 的父列表。")
            return

        try:
            parent_list.pop(index)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("删除失败", f"删除节点失败：{exc}")
            return

        print("[ASTEdit][clipboard_delete] removed ast_node_type=", target_ast_node.get("ast_node_type"), "at index", index)
        messagebox.showinfo("已删除", "已从 ast_step_space 中删除当前 StepAstNode（尚未写回 JSON 文件）。")

        # 删除后刷新基于 ast_step_space 的时间线视图
        self._timeline__refresh_after_ast_edit()

    def _on_ast_clipboard_replace_current(self) -> None:
        """用临时剪贴板中的 StepAstNode 替换当前 StepAstNode。"""

        if not isinstance(self._ast_clipboard_node, dict) or "ast_node_type" not in self._ast_clipboard_node:
            messagebox.showwarning("无临时节点", "当前没有有效的临时 StepAstNode，可通过上方入口按钮生成。")
            return

        source_mode = getattr(self, "timeline_source_var", None)
        source_value = source_mode.get() if isinstance(source_mode, tk.StringVar) else "execution_space"
        if source_value != "ast_step_space":
            messagebox.showinfo("不可用", "仅在“瀑布流 + StepAstNode”模式下才能替换 StepAstNode。")
            return

        data = getattr(self, "_timeline_loaded_json", None)
        if not isinstance(data, dict):
            messagebox.showerror("无 JSON", "当前没有已加载的 JSON 快照，无法替换节点。")
            return

        ast_root = data.get("ast_step_space")
        if not isinstance(ast_root, dict):
            messagebox.showerror("无 ast_step_space", "JSON 中未找到 ast_step_space 字段。")
            return

        exec_node, _node_type = self._timeline__resolve_exec_node()
        if not isinstance(exec_node, dict):
            messagebox.showerror("未选中", "当前没有有效的执行节点可供替换。")
            return

        target_ast_node = exec_node.get("_ast_node")
        if not isinstance(target_ast_node, dict):
            messagebox.showerror("无 StepAstNode", "当前节点未关联 StepAstNode（_ast_node）。")
            return

        # 支持两种容器：
        # - 列表元素：用于语句列表、参数列表等（原有逻辑）；
        # - 字段 dict：用于 Expr.value 等“标量字段”上的子表达式，实现“替换任意子表达式”。
        def _find_parent_container(
            container: Any,
            target: dict[str, Any],
        ) -> tuple[str | None, Any | None, int | None, str | None]:
            """在 ast_step_space 中递归查找 target 所在的父容器。

            返回 (container_type, parent, index, key)：
            - container_type == "list":  parent[index] is target
            - container_type == "dict":  parent[key] is target
            - container_type is None: 未找到
            """

            if isinstance(container, list):
                for idx, item in enumerate(container):
                    if item is target:
                        return "list", container, idx, None
                    c_type, c_parent, c_index, c_key = _find_parent_container(item, target)
                    if c_type is not None:
                        return c_type, c_parent, c_index, c_key
            elif isinstance(container, dict):
                for k, v in container.items():
                    if v is target:
                        return "dict", container, None, k
                    c_type, c_parent, c_index, c_key = _find_parent_container(v, target)
                    if c_type is not None:
                        return c_type, c_parent, c_index, c_key
            return None, None, None, None

        container_type, parent, index, key = _find_parent_container(ast_root, target_ast_node)
        if container_type is None:
            print(
                "[ASTEdit][error] clipboard_replace: parent_container not found for ast_node_type=",
                target_ast_node.get("ast_node_type"),
                "path=",
                getattr(self, "_timeline_selected_path", None),
            )
            messagebox.showerror("未定位", "无法在 ast_step_space 中定位当前 StepAstNode 的父容器。")
            return

        try:
            new_node = copy.deepcopy(self._ast_clipboard_node)
            if container_type == "list":
                assert isinstance(parent, list)
                assert isinstance(index, int)
                parent[index] = new_node
                print(
                    "[ASTEdit][clipboard_replace] replaced list index",
                    index,
                    "with ast_node_type=",
                    self._ast_clipboard_node.get("ast_node_type"),
                )
            elif container_type == "dict":
                assert isinstance(parent, dict)
                assert isinstance(key, str)
                parent[key] = new_node
                print(
                    "[ASTEdit][clipboard_replace] replaced dict key",
                    key,
                    "with ast_node_type=",
                    self._ast_clipboard_node.get("ast_node_type"),
                )
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("替换失败", f"替换节点失败：{exc}")
            return

        messagebox.showinfo("已替换", "已用临时 StepAstNode 替换当前节点（尚未写回 JSON 文件）。")

        # 替换当前节点后刷新时间线
        self._timeline__refresh_after_ast_edit()

    def _on_ast_clipboard_insert_sibling(self) -> None:
        """在 ast_step_space 中于当前 StepAstNode 后插入临时节点作为同级。"""

        if not isinstance(self._ast_clipboard_node, dict) or "ast_node_type" not in self._ast_clipboard_node:
            messagebox.showwarning("无临时节点", "当前没有有效的临时 StepAstNode，可通过上方入口按钮生成。")
            return

        source_mode = getattr(self, "timeline_source_var", None)
        source_value = source_mode.get() if isinstance(source_mode, tk.StringVar) else "execution_space"
        if source_value != "ast_step_space":
            messagebox.showinfo("不可用", "仅在“瀑布流 + StepAstNode”模式下才能插入 StepAstNode。")
            return

        data = getattr(self, "_timeline_loaded_json", None)
        if not isinstance(data, dict):
            messagebox.showerror("无 JSON", "当前没有已加载的 JSON 快照，无法插入节点。")
            return

        ast_root = data.get("ast_step_space")
        if not isinstance(ast_root, dict):
            messagebox.showerror("无 ast_step_space", "JSON 中未找到 ast_step_space 字段。")
            return

        exec_node, _node_type = self._timeline__resolve_exec_node()
        if not isinstance(exec_node, dict):
            messagebox.showerror("未选中", "当前没有有效的执行节点可供插入位置参考。")
            return

        target_ast_node = exec_node.get("_ast_node")
        if not isinstance(target_ast_node, dict):
            messagebox.showerror("无 StepAstNode", "当前节点未关联 StepAstNode（_ast_node）。")
            return

        def _find_parent_list(container: Any, target: dict[str, Any]) -> tuple[list[Any] | None, int]:
            if isinstance(container, list):
                for idx, item in enumerate(container):
                    if item is target:
                        return container, idx
                    res_list, res_idx = _find_parent_list(item, target)
                    if res_list is not None:
                        return res_list, res_idx
            elif isinstance(container, dict):
                for v in container.values():
                    res_list, res_idx = _find_parent_list(v, target)
                    if res_list is not None:
                        return res_list, res_idx
            return None, -1

        parent_list, index = _find_parent_list(ast_root, target_ast_node)
        if parent_list is None or index < 0:
            print(
                "[ASTEdit][error] clipboard_insert_sibling: parent_list not found for ast_node_type=",
                target_ast_node.get("ast_node_type"),
                "path=",
                getattr(self, "_timeline_selected_path", None),
            )
            messagebox.showerror("未定位", "无法在 ast_step_space 中定位当前 StepAstNode 的父列表。")
            return

        try:
            parent_list.insert(index + 1, copy.deepcopy(self._ast_clipboard_node))
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("插入失败", f"插入节点失败：{exc}")
            return

        print("[ASTEdit][clipboard_insert_sibling] inserted after index", index, "ast_node_type=", self._ast_clipboard_node.get("ast_node_type"))
        messagebox.showinfo("已插入", "已在当前节点之后插入一个临时 StepAstNode（尚未写回 JSON 文件）。")

        # 插入同级节点后刷新时间线
        self._timeline__refresh_after_ast_edit()

    def _on_ast_clipboard_insert_child(self) -> None:
        """将临时节点作为子节点插入到当前 StepAstNode 的 body 列表中。"""

        if not isinstance(self._ast_clipboard_node, dict) or "ast_node_type" not in self._ast_clipboard_node:
            messagebox.showwarning("无临时节点", "当前没有有效的临时 StepAstNode，可通过上方入口按钮生成。")
            return

        source_mode = getattr(self, "timeline_source_var", None)
        source_value = source_mode.get() if isinstance(source_mode, tk.StringVar) else "execution_space"
        if source_value != "ast_step_space":
            messagebox.showinfo("不可用", "仅在“瀑布流 + StepAstNode”模式下才能插入子节点。")
            return

        data = getattr(self, "_timeline_loaded_json", None)
        if not isinstance(data, dict):
            messagebox.showerror("无 JSON", "当前没有已加载的 JSON 快照，无法插入子节点。")
            return

        ast_root = data.get("ast_step_space")
        if not isinstance(ast_root, dict):
            messagebox.showerror("无 ast_step_space", "JSON 中未找到 ast_step_space 字段。")
            return

        exec_node, _node_type = self._timeline__resolve_exec_node()
        if not isinstance(exec_node, dict):
            messagebox.showerror("未选中", "当前没有有效的执行节点可供插入位置参考。")
            return

        target_ast_node = exec_node.get("_ast_node")
        if not isinstance(target_ast_node, dict):
            messagebox.showerror("无 StepAstNode", "当前节点未关联 StepAstNode（_ast_node）。")
            return

        fields = target_ast_node.get("fields")
        if not isinstance(fields, dict):
            messagebox.showerror("结构错误", "当前 StepAstNode 缺少 fields 信息，无法插入子节点。")
            return

        body = fields.get("body")
        if isinstance(body, list):
            try:
                body.append(copy.deepcopy(self._ast_clipboard_node))
            except Exception as exc:  # noqa: BLE001
                messagebox.showerror("插入失败", f"插入子节点失败：{exc}")
                return
            print("[ASTEdit][clipboard_insert_child] appended child ast_node_type=", self._ast_clipboard_node.get("ast_node_type"), "to body, new_len=", len(body))
            messagebox.showinfo("已插入", "已将临时 StepAstNode 作为子节点追加到当前节点的 body 中（尚未写回 JSON 文件）。")
            # 追加子节点后刷新时间线
            self._timeline__refresh_after_ast_edit()
            return

        messagebox.showerror("无法插入", "当前 StepAstNode 不包含可追加子节点的 body 列表字段。")

    def _on_ast_edit_apply_replace(self) -> None:
        """用编辑区中的 JSON 替换当前 Step 对应的 StepAstNode（原地更新 _ast_node）。"""

        print("[ASTEdit][json_replace] begin, path=", getattr(self, "_timeline_selected_path", None))

        # 仅在瀑布流 + StepAstNode 模式下生效
        source_mode = getattr(self, "timeline_source_var", None)
        source_value = source_mode.get() if isinstance(source_mode, tk.StringVar) else "execution_space"
        if source_value != "ast_step_space":
            messagebox.showinfo("不可用", "仅在“瀑布流 + StepAstNode”模式下才能编辑 StepAstNode。")
            return

        editor = getattr(self, "ast_edit_text", None)
        if not isinstance(editor, tk.Text):
            return

        raw = editor.get("1.0", tk.END).strip()
        if not raw:
            messagebox.showwarning("空内容", "编辑区为空，无法替换当前节点。")
            return

        try:
            new_node = json.loads(raw)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("解析失败", f"编辑区 JSON 无法解析: {exc}")
            return

        if not isinstance(new_node, dict) or "ast_node_type" not in new_node:
            messagebox.showerror("结构错误", "替换内容必须是带 ast_node_type 的 StepAstNode 对象。")
            return

        exec_node, _node_type = self._timeline__resolve_exec_node()
        if not isinstance(exec_node, dict):
            messagebox.showerror("未选中", "当前没有有效的执行节点可供替换。")
            return

        ast_node = exec_node.get("_ast_node")
        if not isinstance(ast_node, dict):
            messagebox.showerror("无 StepAstNode", "当前节点未关联 StepAstNode（_ast_node）。")
            return

        # 原地更新：保持外层引用不变，仅替换内部键值
        ast_node.clear()
        ast_node.update(new_node)

        print("[ASTEdit][json_replace] updated ast_node_type=", new_node.get("ast_node_type"))
        messagebox.showinfo("已更新", "当前 StepAstNode 已根据编辑区内容更新（尚未写回 JSON 文件）。")

        # JSON 替换当前节点后刷新时间线
        self._timeline__refresh_after_ast_edit()

    def _on_ast_edit_insert_after(self) -> None:
        """在 ast_step_space 中于当前 StepAstNode 后插入一个同级节点。"""

        print("[ASTEdit][json_insert_after] begin, path=", getattr(self, "_timeline_selected_path", None))

        source_mode = getattr(self, "timeline_source_var", None)
        source_value = source_mode.get() if isinstance(source_mode, tk.StringVar) else "execution_space"
        if source_value != "ast_step_space":
            messagebox.showinfo("不可用", "仅在“瀑布流 + StepAstNode”模式下才能插入 StepAstNode。")
            return

        data = getattr(self, "_timeline_loaded_json", None)
        if not isinstance(data, dict):
            messagebox.showerror("无 JSON", "当前没有已加载的 JSON 快照，无法插入节点。")
            return

        ast_root = data.get("ast_step_space")
        if not isinstance(ast_root, dict):
            messagebox.showerror("无 ast_step_space", "JSON 中未找到 ast_step_space 字段。")
            return

        editor = getattr(self, "ast_edit_text", None)
        if not isinstance(editor, tk.Text):
            return

        raw = editor.get("1.0", tk.END).strip()
        if not raw:
            messagebox.showwarning("空内容", "编辑区为空，无法插入节点。")
            return

        try:
            new_node = json.loads(raw)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("解析失败", f"编辑区 JSON 无法解析: {exc}")
            return

        if not isinstance(new_node, dict) or "ast_node_type" not in new_node:
            messagebox.showerror("结构错误", "插入内容必须是带 ast_node_type 的 StepAstNode 对象。")
            return

        exec_node, _node_type = self._timeline__resolve_exec_node()
        if not isinstance(exec_node, dict):
            messagebox.showerror("未选中", "当前没有有效的执行节点可供插入位置参考。")
            return

        target_ast_node = exec_node.get("_ast_node")
        if not isinstance(target_ast_node, dict):
            messagebox.showerror("无 StepAstNode", "当前节点未关联 StepAstNode（_ast_node）。")
            return

        # 在 ast_step_space 中寻找 target_ast_node 所在的列表及索引
        def _find_parent_list(container: Any, target: dict[str, Any]) -> tuple[list[Any] | None, int]:
            if isinstance(container, list):
                for idx, item in enumerate(container):
                    if item is target:
                        return container, idx
                    res_list, res_idx = _find_parent_list(item, target)
                    if res_list is not None:
                        return res_list, res_idx
            elif isinstance(container, dict):
                for v in container.values():
                    res_list, res_idx = _find_parent_list(v, target)
                    if res_list is not None:
                        return res_list, res_idx
            return None, -1

        parent_list, index = _find_parent_list(ast_root, target_ast_node)
        if parent_list is None or index < 0:
            messagebox.showerror("未定位", "无法在 ast_step_space 中定位当前 StepAstNode 的父列表。")
            return

        parent_list.insert(index + 1, new_node)
        print("[ASTEdit][json_insert_after] inserted ast_node_type=", new_node.get("ast_node_type"), "after index", index)
        messagebox.showinfo("已插入", "已在当前节点之后插入一个新的 StepAstNode（尚未写回 JSON 文件）。")

        # JSON 插入同级节点后刷新时间线
        self._timeline__refresh_after_ast_edit()

    def _on_ast_edit_save_json(self) -> None:
        """将内存中修改后的 ast_step_space 写回到原 JSON 文件。"""

        print("[ASTEdit][json_save] begin, path=", getattr(self, "_timeline_loaded_json_path", None))

        data = getattr(self, "_timeline_loaded_json", None)
        path = getattr(self, "_timeline_loaded_json_path", None)
        if not isinstance(data, dict) or not isinstance(path, str):
            messagebox.showerror("无 JSON", "当前没有可写回的 JSON 快照。")
            return

        try:
            out_path = Path(path)
            out_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("保存失败", f"写回 JSON 文件失败: {exc}")
            return

        print("[ASTEdit][json_save] saved to", path)
        messagebox.showinfo("已保存", f"已将修改后的 ast_step_space 写回到 JSON 文件:\n{path}")

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

        # 根据当前开关，选择时间线渲染源：execution_space 或 ast_step_space
        space: Dict[str, Any] | None = None
        source_mode = getattr(self, "timeline_source_var", None)
        source_value = source_mode.get() if isinstance(source_mode, tk.StringVar) else "execution_space"

        # 记录当前回放的 JSON 快照及路径，便于之后在 UI 中编辑 ast_step_space 并写回文件
        self._timeline_loaded_json = data
        self._timeline_loaded_json_path = path
        self._timeline_loaded_source = source_value

        if source_value == "ast_step_space":
            ast_root = data.get("ast_step_space")
            if isinstance(ast_root, dict) and ast_root.get("ast_node_type") == "FunctionDef":
                # ------------------------------------------------------------------
                # 先基于 JSON 中的 file_path 重新解析模块 AST，构造 name->FunctionDef 索引，
                # 再在 ast_step_space 中为 Call 节点挂载 call_def（被调函数的 StepAstNode）。
                # ------------------------------------------------------------------
                try:
                    file_path_val = data.get("file_path")
                    func_ast_index: Dict[str, ast.FunctionDef] = {}

                    # 仅对 local_module.definitions 中声明过的函数/方法名建立索引，
                    # 保证 call 绑定严格来源于 definitions，而不是任意顶层 FunctionDef。
                    defs_obj = (
                        data.get("local_module", {})
                        .get("definitions", {})
                    )
                    methods_defs = defs_obj.get("methods") or {}
                    inner_classes_defs = defs_obj.get("inner_classes") or {}

                    allowed_func_names: set[str] = set(methods_defs.keys())

                    if isinstance(file_path_val, str):
                        src_path = Path(file_path_val)
                        if src_path.exists():
                            source_text = src_path.read_text(encoding="utf-8")
                            mod_tree = ast.parse(source_text, filename=str(src_path))

                            for top_node in getattr(mod_tree, "body", []):
                                # 顶层函数：与 definitions.methods 对齐
                                if (
                                    isinstance(top_node, ast.FunctionDef)
                                    and top_node.name in allowed_func_names
                                ):
                                    func_ast_index[top_node.name] = top_node

                                # 类体方法：与 definitions.inner_classes[*].(instance/class/static)_methods 对齐
                                if (
                                    isinstance(top_node, ast.ClassDef)
                                    and top_node.name in inner_classes_defs
                                ):
                                    cls_name = top_node.name
                                    cls_defs = inner_classes_defs.get(cls_name) or {}
                                    inst_m = cls_defs.get("instance_methods") or cls_defs.get("methods") or {}
                                    cls_m = cls_defs.get("class_methods") or {}
                                    static_m = cls_defs.get("static_methods") or {}

                                    allowed_meth_names: set[str] = set(inst_m.keys()) | set(cls_m.keys()) | set(static_m.keys())

                                    if not allowed_meth_names:
                                        continue

                                    for stmt in top_node.body:
                                        if (
                                            isinstance(stmt, ast.FunctionDef)
                                            and stmt.name in allowed_meth_names
                                        ):
                                            # 直接在后面通过 method_step_cache 按方法名索引
                                            # 若多个类中出现同名方法，回放阶段无法区分具体实例，择一即可。
                                            func_ast_index.setdefault(stmt.name, stmt)

                    # 将 ast.AST(FunctionDef) 转换为 StepAstNode(FunctionDef)
                    def _ast_to_step_node_static_from_ast(node: ast.AST) -> Dict[str, Any]:
                        result: Dict[str, Any] = {
                            "ast_node_type": type(node).__name__,
                            "fields": {},
                        }

                        fields_dict: Dict[str, Any] = {}
                        for field_name in getattr(node, "_fields", ()):  # type: ignore[attr-defined]
                            value = getattr(node, field_name, None)

                            if field_name == "ctx" and value is not None:
                                fields_dict[field_name] = type(value).__name__
                                continue

                            if isinstance(value, ast.AST):
                                child = _ast_to_step_node_static_from_ast(value)
                                fields_dict[field_name] = child
                            elif isinstance(value, list):
                                items: List[Any] = []
                                for item in value:
                                    if isinstance(item, ast.AST):
                                        items.append(_ast_to_step_node_static_from_ast(item))
                                    else:
                                        items.append(item)
                                fields_dict[field_name] = items
                            elif isinstance(value, (str, int, float, bool)) or value is None:
                                fields_dict[field_name] = value
                            else:
                                fields_dict[field_name] = type(value).__name__

                        result["fields"] = fields_dict
                        return result

                    # 为同一个函数/方法名缓存一次 StepAstNode 视图，
                    # func_step_cache 既可用于顶层函数，也可用于类方法（按名称索引）。
                    func_step_cache: Dict[str, Dict[str, Any]] = {}
                    for fn_name, fn_node in func_ast_index.items():
                        try:
                            func_step_cache[fn_name] = _ast_to_step_node_static_from_ast(fn_node)
                        except Exception:
                            continue

                    def _attach_call_def(node: Dict[str, Any]) -> None:
                        """在给定 StepAstNode 树中，为所有 Call 节点挂载 call_def 字段。"""

                        if not isinstance(node, dict):
                            return

                        node_type = node.get("ast_node_type")
                        fields_obj = node.get("fields")

                        if isinstance(fields_obj, dict) and node_type == "Call":
                            func_expr = fields_obj.get("func")

                            # 1) 顶层函数调用：func = Name(id=...)
                            if (
                                isinstance(func_expr, dict)
                                and func_expr.get("ast_node_type") == "Name"
                                and isinstance(func_expr.get("fields"), dict)
                            ):
                                fn_name = func_expr["fields"].get("id")
                                if isinstance(fn_name, str):
                                    target_def = func_step_cache.get(fn_name)
                                    if target_def is not None:
                                        # 将函数定义的 StepAstNode 挂到 call_def 供 UI 展开
                                        fields_obj["call_def"] = target_def

                            # 2) 实例 / 类 / 静态方法调用：func = Attribute(value=..., attr=...)
                            if (
                                isinstance(func_expr, dict)
                                and func_expr.get("ast_node_type") == "Attribute"
                                and isinstance(func_expr.get("fields"), dict)
                            ):
                                attr_name = func_expr["fields"].get("attr")
                                if isinstance(attr_name, str):
                                    target_def2 = func_step_cache.get(attr_name)
                                    if target_def2 is not None:
                                        # 方法定义同样作为 StepAstNode 挂到 call_def，
                                        # 具体是实例/类/静态方法由 definitions 内部信息决定，
                                        # 这里回放阶段不再区分具体绑定实例。
                                        fields_obj["call_def"] = target_def2

                        # 递归处理子 StepAstNode
                        if isinstance(fields_obj, dict):
                            for value in fields_obj.values():
                                if isinstance(value, dict) and value.get("ast_node_type"):
                                    _attach_call_def(value)
                                elif isinstance(value, list):
                                    for item in value:
                                        if isinstance(item, dict) and item.get("ast_node_type"):
                                            _attach_call_def(item)

                    # 在整个 ast_step_space 根上执行一次挂载
                    if isinstance(ast_root, dict):
                        _attach_call_def(ast_root)
                except Exception:
                    # 解析失败或源文件缺失时，宁可不挂 call_def 也不要影响回放主流程
                    pass

                # 将 StepAstNode 递归映射为可被 _render_execution_timeline 消费的“伪 ExecutionSpaceObject”
                def _build_exec_from_step_ast(node: Dict[str, Any]) -> Dict[str, Any]:
                    """从单个 StepAstNode 递归构造一个 exec_like step。"""

                    fields = node.get("fields") or {}

                    # 收集所有子 StepAstNode 作为线性子执行单元
                    children: list[Dict[str, Any]] = []
                    for value in fields.values():
                        if isinstance(value, dict):
                            if value.get("ast_node_type"):
                                children.append(_build_exec_from_step_ast(value))
                        elif isinstance(value, list):
                            for item in value:
                                if isinstance(item, dict) and item.get("ast_node_type"):
                                    children.append(_build_exec_from_step_ast(item))

                    step: Dict[str, Any] = {
                        "scope_level": "ast_step",
                        "scope_in": node.get("scope_in") or {},
                        "scope_out": node.get("scope_out") or {},
                        # 使用 ast_node_type 作为 kind 标签，便于时间线与详情面板展示
                        "kind": node.get("ast_node_type"),
                        # 静态 ast_step_space 中目前没有源码字符串，这里暂留空
                        "code": None,
                        # 递归子 StepAstNode 作为线性子执行空间，双击即可展开下钻
                        "exec_queue": children,
                        # 保留原始 StepAstNode，若后续需要在详情面板中展示原始结构可复用
                        "_ast_node": node,
                    }
                    return step

                fields = ast_root.get("fields") or {}
                body = fields.get("body") or []
                exec_queue: list[Dict[str, Any]] = []
                if isinstance(body, list):
                    for stmt in body:
                        if not isinstance(stmt, dict) or not stmt.get("ast_node_type"):
                            continue
                        exec_queue.append(_build_exec_from_step_ast(stmt))

                space = {
                    "scope_level": "function",
                    "scope_in": ast_root.get("scope_in") or {},
                    "scope_out": ast_root.get("scope_out") or {},
                    "exec_queue": exec_queue,
                    "_ast_root": ast_root,
                }
            else:
                messagebox.showerror("结构错误", "JSON 中未找到有效的 ast_step_space(FunctionDef) 结构。")
                return
        else:
            raw_space = data.get("execution_space")
            if not isinstance(raw_space, dict):
                messagebox.showerror("结构错误", "JSON 中未找到 execution_space 字段或类型不正确。")
                return
            space = raw_space

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
            # 构造静态 ast_step_space：以 StepAstNode(FunctionDef) 为根，
            # 在函数体 body 中的每个语句节点上附加占位版 scope_in/scope_out。
            # 顶层不再是带 exec_queue 的 ExecutionSpaceObject，而是：
            # {ast_node_type: "FunctionDef", fields: {...}, scope_in: {...}, scope_out: {...}}。
            # ------------------------------------------------------------------

            ast_step_space: Dict[str, Any] | None = None
            try:
                entry_func: Optional[ast.FunctionDef] = None

                # 根据 entry_name 在 functions / classes 中解析出入口函数定义
                if "." in entry_name:
                    cls_name, meth_name = entry_name.split(".", 1)
                    for cls in classes or []:
                        if isinstance(cls, ast.ClassDef) and cls.name == cls_name:
                            for stmt in cls.body:
                                if isinstance(stmt, ast.FunctionDef) and stmt.name == meth_name:
                                    entry_func = stmt
                                    break
                            if entry_func is not None:
                                break
                else:
                    for fn in functions or []:
                        if isinstance(fn, ast.FunctionDef) and fn.name == entry_name:
                            entry_func = fn
                            break

                if isinstance(entry_func, ast.FunctionDef):
                    def _ast_to_step_node_static(node: ast.AST | None) -> Optional[Dict[str, Any]]:
                        """将 ast.AST 转为 StepAstNode 风格的轻量结构，不带行列号。"""

                        if node is None:
                            return None
                        if not isinstance(node, ast.AST):
                            return None

                        result: Dict[str, Any] = {
                            "ast_node_type": type(node).__name__,
                            "fields": {},
                        }

                        fields_dict: Dict[str, Any] = {}
                        for field_name in getattr(node, "_fields", ()):  # type: ignore[attr-defined]
                            value = getattr(node, field_name, None)

                            # ctx 字段统一转为类型名字符串，例如 Load/Store
                            if field_name == "ctx" and value is not None:
                                fields_dict[field_name] = type(value).__name__
                                continue

                            if isinstance(value, ast.AST):
                                child = _ast_to_step_node_static(value)
                                fields_dict[field_name] = child
                            elif isinstance(value, list):
                                items: List[Any] = []
                                for item in value:
                                    if isinstance(item, ast.AST):
                                        items.append(_ast_to_step_node_static(item))
                                    else:
                                        items.append(item)
                                fields_dict[field_name] = items
                            elif isinstance(value, (str, int, float, bool)) or value is None:
                                fields_dict[field_name] = value
                            else:
                                fields_dict[field_name] = type(value).__name__

                        result["fields"] = fields_dict
                        return result

                    def _make_unknown_binding(name: str) -> Dict[str, Any]:
                        return {"kind": "unknown", "name": name, "value": None}

                    # 先把整个 FunctionDef 转为 StepAstNode
                    root = _ast_to_step_node_static(entry_func)
                    if isinstance(root, dict):
                        fields_dict = root.get("fields")

                        # 在 body 列表中的每个语句 StepAstNode 上，根据 Assign/Call 形态
                        # 结合执行结果 zone.exec_queue，填入 scope_in/scope_out（若有）。
                        if isinstance(fields_dict, dict):
                            body_nodes = fields_dict.get("body")

                            # 入口函数对应的执行步骤列表（zone 即该函数的 execution_space）
                            exec_steps: List[Any] = []
                            if isinstance(zone, dict):
                                steps = zone.get("exec_queue")
                                if isinstance(steps, list):
                                    exec_steps = steps

                            def _extract_runtime_value(scope: Any, name: str) -> Any:
                                """从 scope 结构中提取某个名字的值。

                                若条目本身已是 {kind,name,value} 三元组，则返回其中的 value 字段。
                                """

                                if not isinstance(scope, dict):
                                    return None

                                # 执行引擎给出的原始 scope 通常是扁平 {name: value}
                                val = scope.get(name)

                                if isinstance(val, dict) and {"kind", "name", "value"} <= val.keys():
                                    return val.get("value")
                                return val

                            def _scope_to_bindings(scope: Any) -> Dict[str, Any]:
                                """将某一步的 scope(dict) 映射为四分类 {modules, attributes, methods, inner_classes} 形式。

                                这里的 scope 来源于执行引擎的 step["scope_in"/"scope_out"]，
                                在本阶段通常还是扁平 dict[{name: value}]；
                                为了与运行时快照统一，这里显式包装为三元组结构，并按 kind 做粗分类。
                                """

                                if not isinstance(scope, dict):
                                    return {}

                                modules: Dict[str, Any] = {}
                                attributes: Dict[str, Any] = {}
                                methods: Dict[str, Any] = {}
                                inner_classes: Dict[str, Any] = {}

                                for name, val in scope.items():
                                    if (
                                        isinstance(val, dict)
                                        and "kind" in val
                                        and "name" in val
                                        and "value" in val
                                    ):
                                        binding = val
                                    else:
                                        binding = self._make_scope_binding(name, val)

                                    kind_val = binding.get("kind")

                                    if kind_val in ("module", "module_ref"):
                                        modules[name] = binding
                                    elif kind_val in ("function", "func_def", "func_def_ref", "call", "method"):
                                        methods[name] = binding
                                    elif kind_val in ("class", "class_def", "class_def_ref", "inner_class"):
                                        inner_classes[name] = binding
                                    else:
                                        attributes[name] = binding

                                return {
                                    "modules": modules,
                                    "attributes": attributes,
                                    "methods": methods,
                                    "inner_classes": inner_classes,
                                }

                            if isinstance(body_nodes, list):
                                for idx, (stmt, node) in enumerate(zip(entry_func.body, body_nodes)):
                                    if not isinstance(node, dict):
                                        continue

                                    own_in: Dict[str, Any] = {}
                                    own_out: Dict[str, Any] = {}

                                    # 尝试获取该语句在执行结果中的 scope_in / scope_out（若存在）
                                    step_scope_in: Any = None
                                    step_scope_out: Any = None
                                    if 0 <= idx < len(exec_steps):
                                        step = exec_steps[idx]
                                        if isinstance(step, dict):
                                            step_scope_in = step.get("scope_in")
                                            step_scope_out = step.get("scope_out")

                                    fields_obj = node.get("fields")
                                    if isinstance(fields_obj, dict):
                                        node_type = node.get("ast_node_type")

                                        # 简单规则：Assign 目标 → scope_out.own（仅提取与本条语句直接相关的绑定）
                                        if node_type == "Assign":
                                            targets = fields_obj.get("targets") or []
                                            if isinstance(targets, list):
                                                for t in targets:
                                                    if (
                                                        isinstance(t, dict)
                                                        and t.get("ast_node_type") == "Name"
                                                        and isinstance(t.get("fields"), dict)
                                                    ):
                                                        tid = t["fields"].get("id")
                                                        if isinstance(tid, str):
                                                            # 优先从执行结果中取真实值，否则退回 unknown+None
                                                            runtime_val = _extract_runtime_value(step_scope_out, tid)
                                                            binding: Dict[str, Any]
                                                            if runtime_val is not None:
                                                                # 简单分类：基础类型视为 constant，其余保持 unknown
                                                                if isinstance(runtime_val, (int, float, str, bool)) or runtime_val is None:
                                                                    kind = "constant"
                                                                else:
                                                                    kind = "unknown"
                                                                binding = {"kind": kind, "name": tid, "value": runtime_val}
                                                            else:
                                                                binding = _make_unknown_binding(tid)
                                                            own_out[tid] = binding

                                        # Call 的位置参数 Name → scope_in.own
                                        value_field = fields_obj.get("value")
                                        if isinstance(value_field, dict):
                                            if value_field.get("ast_node_type") == "Call":
                                                args = value_field.get("fields", {}).get("args") or []
                                                if isinstance(args, list):
                                                    for arg in args:
                                                        if (
                                                            isinstance(arg, dict)
                                                            and arg.get("ast_node_type") == "Name"
                                                            and isinstance(arg.get("fields"), dict)
                                                        ):
                                                            aid = arg["fields"].get("id")
                                                            if isinstance(aid, str) and aid not in own_in:
                                                                runtime_val = _extract_runtime_value(step_scope_in, aid)
                                                                binding2: Dict[str, Any]
                                                                if runtime_val is not None:
                                                                    if isinstance(runtime_val, (int, float, str, bool)) or runtime_val is None:
                                                                        kind2 = "constant"
                                                                    else:
                                                                        kind2 = "unknown"
                                                                    binding2 = {"kind": kind2, "name": aid, "value": runtime_val}
                                                                else:
                                                                    binding2 = _make_unknown_binding(aid)
                                                                own_in[aid] = binding2

                                        # 定义型 AST 节点：同步整步 scope_in / scope_out 到 ast_step_space
                                        def_like = {"Assign", "FunctionDef", "ClassDef", "Import", "ImportFrom"}
                                        if isinstance(node_type, str) and node_type in def_like:
                                            in_bindings = _scope_to_bindings(step_scope_in)
                                            out_bindings = _scope_to_bindings(step_scope_out)
                                            if in_bindings:
                                                node["scope_in"] = {"own": in_bindings, "outer": {}}
                                            if out_bindings:
                                                node["scope_out"] = {"own": out_bindings, "outer": {}}
                                        else:
                                            # 其它节点仍按精简规则，仅挂与本语句直接相关的变量名
                                            if own_in:
                                                node["scope_in"] = {"own": _scope_to_bindings(own_in), "outer": {}}
                                            if own_out:
                                                node["scope_out"] = {"own": _scope_to_bindings(own_out), "outer": {}}

                        # 顶层函数节点本身也附加占位 scope_in/scope_out（四分类空结构）
                        root["scope_in"] = {
                            "own": {
                                "modules": {},
                                "attributes": {},
                                "methods": {},
                                "inner_classes": {},
                            },
                            "outer": {},
                        }
                        root["scope_out"] = {
                            "own": {
                                "modules": {},
                                "attributes": {},
                                "methods": {},
                                "inner_classes": {},
                            },
                            "outer": {},
                        }

                        def _propagate_scope_to_children(node_dict: Dict[str, Any]) -> None:
                            """将当前 StepAstNode 上已有的 scope_in/scope_out 透传给子 StepAstNode。

                            约定：
                            - 只在子节点缺少 scope_in/scope_out 时进行填充；
                            - 子节点如果已经有自己的 scope_in/scope_out（例如语句级占位），则保持不变；
                            - 不在此处新增任何绑定名，仅复用父节点的 scope 结构，
                              保证 Name 等非绑定节点若带 scope 也只是如实传递当前作用域。
                            """

                            if not isinstance(node_dict, dict):
                                return

                            parent_scope_in = node_dict.get("scope_in")
                            parent_scope_out = node_dict.get("scope_out")

                            fields_obj = node_dict.get("fields")
                            if not isinstance(fields_obj, dict):
                                return

                            for value in fields_obj.values():
                                # 单个子节点：StepAstNode(dict)
                                if isinstance(value, dict):
                                    if "ast_node_type" in value and "fields" in value:
                                        if parent_scope_in is not None and "scope_in" not in value:
                                            value["scope_in"] = parent_scope_in
                                        if parent_scope_out is not None and "scope_out" not in value:
                                            value["scope_out"] = parent_scope_out
                                        _propagate_scope_to_children(value)
                                # 列表字段：可能包含多个 StepAstNode
                                elif isinstance(value, list):
                                    for item in value:
                                        if isinstance(item, dict) and "ast_node_type" in item and "fields" in item:
                                            if parent_scope_in is not None and "scope_in" not in item:
                                                item["scope_in"] = parent_scope_in
                                            if parent_scope_out is not None and "scope_out" not in item:
                                                item["scope_out"] = parent_scope_out
                                            _propagate_scope_to_children(item)

                        # 从根节点开始，将语句级占位 scope 透传到子表达式级 StepAstNode
                        _propagate_scope_to_children(root)

                        ast_step_space = root
            except Exception:
                ast_step_space = None

            # ------------------------------------------------------------------
            # 根据 execution_zone 构建 instance_pool，并将其中的实例对象改写为句柄
            # 同时，将各级 scope_in/scope_out 中的绑定统一包装为 {kind, name, value}
            # ------------------------------------------------------------------

            instance_pool: Dict[str, Any] = {}
            pyid_to_oid: Dict[int, str] = {}
            class_counters: Dict[str, int] = {}

            def _wrap_scopes_in_place(obj: Any) -> None:
                """在 execution_zone 结构中，就地将 scope_in/scope_out 的条目包装为三元组。

                规则：
                - scope_in / scope_out 通常是扁平 dict[{name: value}]；
                - 统一提升为 {"own": {modules/attributes/methods/inner_classes}, "outer": {}} 形式；
                - 其中 own 下的四个子字典的值一律为 {kind, name, value} 三元组。
                """

                def _wrap_scope_dict(scope: Dict[str, Any]) -> Dict[str, Any]:
                    # 执行引擎给出的原始 scope：扁平 {name: value} 或 {name: triple}
                    modules: Dict[str, Any] = {}
                    attributes: Dict[str, Any] = {}
                    methods: Dict[str, Any] = {}
                    inner_classes: Dict[str, Any] = {}

                    for name, val in scope.items():
                        if (
                            isinstance(val, dict)
                            and "kind" in val
                            and "name" in val
                            and "value" in val
                        ):
                            binding = val
                        else:
                            binding = self._make_scope_binding(name, val)

                        kind_val = binding.get("kind")

                        if kind_val in ("module", "module_ref"):
                            modules[name] = binding
                        elif kind_val in ("function", "func_def", "func_def_ref", "call", "method"):
                            methods[name] = binding
                        elif kind_val in ("class", "class_def", "class_def_ref", "inner_class"):
                            inner_classes[name] = binding
                        else:
                            attributes[name] = binding

                    return {
                        "own": {
                            "modules": modules,
                            "attributes": attributes,
                            "methods": methods,
                            "inner_classes": inner_classes,
                        },
                        "outer": {},
                    }

                if isinstance(obj, dict):
                    for key in ("scope_in", "scope_out"):
                        scope = obj.get(key)
                        if isinstance(scope, dict):
                            obj[key] = _wrap_scope_dict(scope)
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

            # ast_step_space 中的 scope_in/scope_out 也可能携带运行时对象（例如实例 self / c），
            # 同样通过 _encode_value 编码为句柄，具体对象快照放入同一个 instance_pool。
            encoded_ast_step_space = _encode_value(ast_step_space) if ast_step_space is not None else None

            # 返回值也统一走一次编码，避免返回复杂对象时阻塞 JSON 序列化。
            encoded_return_value = _encode_value(return_value)

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
                "ast_module": None,
                "ast_step_space": encoded_ast_step_space,
                "entry": entry_name,
                "execution_space": encoded_zone,
                "return_value": encoded_return_value,
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

        # 基于新的 exec_ctx 重新构建入口函数列表（模块级 + 类方法 + 顶层函数）
        choices: list[str] = ["<module>"]
        for cls in self.exec_ctx.classes:
            for stmt in cls.body:
                if isinstance(stmt, ast.FunctionDef):
                    choices.append(f"{cls.name}.{stmt.name}")
        for fn in self.exec_ctx.functions:
            choices.append(fn.name)

        # 执行区入口下拉框（模块级 + 函数/方法）
        self.exec_entry_cb["values"] = choices
        if choices:
            if self.exec_entry_var.get() not in choices:
                self.exec_entry_var.set(choices[0])
        else:
            self.exec_entry_var.set("")

        self._refresh_exec_param_form()

        # 调用区入口下拉框与视图刷新（与执行区入口共用同一 choices）
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
            # 特殊入口：模块级（顶层作用域）
            if entry_name == "<module>":
                # AST 模式：使用 SimpleFunctionExecutor + 人工构造的 FunctionDef 包裹 Module.body
                if mode_value == "ast":
                    module_ast = getattr(self.exec_ctx, "tree", None)
                    if not isinstance(module_ast, ast.Module):
                        log("[AST] 当前 exec_ctx.tree 不是 ast.Module，回退到 Python 模式执行整模块源码。")
                        mode_value = "python"
                    else:
                        log("[AST] 使用 SimpleFunctionExecutor 以模块级入口执行 AST Module.body ...")

                        env: dict = {}

                        # 构建 __ast_func_index__ 映射，支持模块内函数调用链的子 execution_zone
                        ast_func_index: Dict[str, ast.FunctionDef] = {}
                        try:
                            for fn in getattr(self.exec_ctx, "functions", []) or []:
                                if isinstance(fn, ast.FunctionDef):
                                    ast_func_index[fn.name] = fn
                        except Exception:
                            ast_func_index = {}
                        env["__ast_func_index__"] = ast_func_index

                        # 人工构造一个零参数的 FunctionDef，将 Module.body 作为其函数体
                        try:
                            fake_def = ast.FunctionDef(
                                name="__module__",
                                args=ast.arguments(
                                    posonlyargs=[],
                                    args=[],
                                    vararg=None,
                                    kwonlyargs=[],
                                    kw_defaults=[],
                                    kwarg=None,
                                    defaults=[],
                                ),
                                body=list(getattr(module_ast, "body", []) or []),
                                decorator_list=[],
                            )
                        except TypeError:
                            # 兼容极端版本差异：若 ast.arguments 的签名不同，退回到 Python 模式
                            log("[AST] 构造模块级 FunctionDef 失败，回退到 Python 模式执行整模块源码。")
                            mode_value = "python"
                        else:
                            executor = SimpleFunctionExecutor(fake_def, module_globals=env)
                            # 模块级执行：locals 与 globals 共享同一 dict，模拟模块命名空间
                            executor.ctx.frame.locals = executor.ctx.frame.globals
                            result_obj = executor.run({})

                            for line in result_obj.logs:
                                log(f"[AST] {line}")

                            zone = getattr(result_obj, "execution_zone", None)
                            if isinstance(zone, dict):
                                zone["scope_level"] = "module"
                                log("[AST] ---- execution_zone(module) ----")
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
                                log("[AST] ----------------------------")

                                # 使用模块级 execution_zone 渲染时间线
                                try:
                                    self._render_execution_timeline(zone)
                                except Exception:
                                    pass

                                # 写入 JSON 快照，作为模块级示例
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

                            log(f"[AST] 模块级返回值: {result_obj.return_value!r}")
                            try:
                                widget = getattr(self, "exec_output", None)
                                if widget is not None and widget.winfo_exists():
                                    widget.configure(state="disabled")
                            except tk.TclError:
                                pass
                            return

                # Python 模式下的模块级入口：直接执行整模块源码
                env: dict = {}
                exec(self.exec_ctx.source, env, env)
                log("模块级入口：已执行整个模块源码。")

                try:
                    symbols = sorted(k for k in env.keys() if not k.startswith("__"))
                    log(f"模块级可见符号: {symbols!r}")
                except Exception:
                    pass

                try:
                    widget = getattr(self, "exec_output", None)
                    if widget is not None and widget.winfo_exists():
                        widget.configure(state="disabled")
                except tk.TclError:
                    pass
                return

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
