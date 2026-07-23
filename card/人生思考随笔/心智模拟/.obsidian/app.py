#!/usr/bin/env python3
"""模块化 AST Viewer 应用

特性：
- 左侧：文件列表（当前选择目录下的 .py 文件）
- TAB1：紧凑源码（左） + AST 树（中） + 节点详情（右）
- TAB2：盒子视图（Canvas，以节点顺序绘制缩进盒子树）
"""

import ast
import os
import json
import csv
import traceback
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Dict, Optional
import importlib.util

try:
    # 优先作为包运行：python -m ast_viewer.app
    from .editor import (
        edit_async,
        edit_call,
        edit_control,
        edit_dataflow,
        edit_exception,
        edit_expr,
        edit_imports,
        edit_meta,
        edit_structure,
    )
    from . import ast_edit_ops, ast_clipboard_ops, project_deps
except ImportError:  # 当直接 python ast_viewer/app.py 运行时使用
    from editor import (
        edit_async,
        edit_call,
        edit_control,
        edit_dataflow,
        edit_exception,
        edit_expr,
        edit_imports,
        edit_meta,
        edit_structure,
    )
    import ast_edit_ops
    import ast_clipboard_ops
    import project_deps


class ASTSuiteApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("AST Viewer Suite")
        self.geometry("1300x780")

        # 状态
        self.current_dir: Optional[str] = None
        self.current_file: Optional[str] = None
        self.current_root: Optional[ast.AST] = None
        self.current_source: str = ""

        # Tab1 状态
        self.node_by_item: Dict[str, ast.AST] = {}
        self.parent_map: Dict[ast.AST, tuple[Optional[ast.AST], str, Optional[int]]] = {}
        self.current_node: Optional[ast.AST] = None

        # 剪贴板状态（复制/剪切/组装临时节点）
        self.clipboard_active: bool = False
        self.clipboard_source_node: Optional[ast.AST] = None
        self.clipboard_status_var: Optional[tk.StringVar] = None
        self.clipboard_mode: Optional[str] = None  # "copy" / "cut" / "assemble" / None

        # 临时 AST 视图：可编辑源码 + 当前解析得到的子树
        self.clipboard_temp_node: Optional[ast.AST] = None
        self.clipboard_temp_source: str = ""

        # Tab2 状态
        self.box_item_to_node: Dict[int, ast.AST] = {}
        self.box_view_stack: list[ast.AST] = []
        self.box_current_node: Optional[ast.AST] = None

        # 项目视图状态
        self.dep_tree_item_to_node: Dict[str, project_deps.ModuleNode] = {}
        self.dependency_root: Optional[project_deps.ModuleNode] = None
        self._deps_project_root: Optional[Path] = None
        self.import_row_to_record: Dict[str, project_deps.ImportRecord] = {}

        # 项目仪表台状态（全局项目列表）
        self.projects_tree: Optional[ttk.Treeview] = None
        self._project_row_to_path: dict[str, Path] = {}

        # 项目局部历史视图状态
        self.project_history_tree: Optional[ttk.Treeview] = None
        self._history_row_to_record: dict[str, dict] = {}


        self._create_widgets()

    # ------------------------- UI 构建 -------------------------
    def _create_widgets(self) -> None:
        # 顶部工具条
        toolbar = ttk.Frame(self)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        btn_choose_dir = ttk.Button(toolbar, text="选择目录", command=self._on_choose_dir)
        btn_choose_dir.pack(side=tk.LEFT, padx=5, pady=5)

        self.lbl_dir = ttk.Label(toolbar, text="当前目录：<未选择>")
        self.lbl_dir.pack(side=tk.LEFT, padx=5)

        # 左侧文件列表 + 右侧 Notebook
        main = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        main.pack(fill=tk.BOTH, expand=True)

        # 左侧：文件列表
        left = ttk.Frame(main, width=260)
        main.add(left, weight=0)

        ttk.Label(left, text="Python 文件列表").pack(anchor=tk.W, padx=5, pady=(5, 0))
        self.file_list = tk.Listbox(left, height=20)
        self.file_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0), pady=5)
        sb_files = ttk.Scrollbar(left, orient=tk.VERTICAL, command=self.file_list.yview)
        sb_files.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 5), pady=5)
        self.file_list.configure(yscrollcommand=sb_files.set)
        self.file_list.bind("<<ListboxSelect>>", self._on_file_selected)

        # 右侧：Notebook
        right = ttk.Frame(main)
        main.add(right, weight=1)

        self.notebook = ttk.Notebook(right)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # TAB1：紧凑源码 + 中间 AST 视图（Tree/盒子 内部 Notebook）+ 节点详情
        tab1 = ttk.Frame(self.notebook)
        self.notebook.add(tab1, text="结构视图")

        # 三列布局
        tab1.columnconfigure(0, weight=1)
        tab1.columnconfigure(1, weight=1)
        tab1.columnconfigure(2, weight=1)
        tab1.rowconfigure(1, weight=1)

        ttk.Label(tab1, text="紧凑源码（unparse+parse）").grid(row=0, column=0, sticky="w", padx=5, pady=(5, 0))
        ttk.Label(tab1, text="AST 中间视图").grid(row=0, column=1, sticky="w", padx=5, pady=(5, 0))
        ttk.Label(tab1, text="节点详情").grid(row=0, column=2, sticky="w", padx=5, pady=(5, 0))

        # 左：源码
        self.code_text = tk.Text(tab1, wrap="none", font=("Consolas", 11))
        self.code_text.grid(row=1, column=0, sticky="nsew", padx=(5, 2), pady=5)
        self.code_text.tag_configure("highlight", background="#fffb8f")

        sb_code_y = ttk.Scrollbar(tab1, orient=tk.VERTICAL, command=self.code_text.yview)
        sb_code_y.grid(row=1, column=0, sticky="nse", padx=(0, 5), pady=5)
        sb_code_x = ttk.Scrollbar(tab1, orient=tk.HORIZONTAL, command=self.code_text.xview)
        sb_code_x.grid(row=2, column=0, sticky="ew", padx=(5, 2), pady=(0, 5))
        self.code_text.configure(yscrollcommand=sb_code_y.set, xscrollcommand=sb_code_x.set)

        # 中：内部 Notebook（Tree / 盒子）
        mid_nb = ttk.Notebook(tab1)
        mid_nb.grid(row=1, column=1, sticky="nsew", padx=2, pady=5)

        # 中-Tab1：AST 树
        tree_tab = ttk.Frame(mid_nb)
        mid_nb.add(tree_tab, text="Tree")

        tree_tab.rowconfigure(0, weight=1)
        tree_tab.columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(tree_tab)
        self.tree.grid(row=0, column=0, sticky="nsew")
        sb_tree_y = ttk.Scrollbar(tree_tab, orient=tk.VERTICAL, command=self.tree.yview)
        sb_tree_y.grid(row=0, column=0, sticky="nse", padx=(0, 5), pady=5)
        self.tree.configure(yscrollcommand=sb_tree_y.set)
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        # 右：节点详情 / 节点编辑 子 Tab
        self.right_nb = ttk.Notebook(tab1)
        self.right_nb.grid(row=1, column=2, sticky="nsew", padx=(2, 5), pady=5)

        # 子 Tab1：详情
        detail_tab = ttk.Frame(self.right_nb)
        self.right_nb.add(detail_tab, text="详情")

        self.detail_text = tk.Text(detail_tab, wrap="word", state="disabled", font=("Consolas", 11))
        self.detail_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        sb_detail_y = ttk.Scrollbar(detail_tab, orient=tk.VERTICAL, command=self.detail_text.yview)
        sb_detail_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.detail_text.configure(yscrollcommand=sb_detail_y.set)

        # 子 Tab2：编辑（顶部两行操作按钮 + 内部按功能分类再分子 Tab）
        self.right_edit_tab = ttk.Frame(self.right_nb)
        self.right_nb.add(self.right_edit_tab, text="编辑")

        # 第一行：快捷（删除选中）
        edit_toolbar_row1 = ttk.Frame(self.right_edit_tab)
        edit_toolbar_row1.pack(side=tk.TOP, fill=tk.X)

        btn_del = ttk.Button(edit_toolbar_row1, text="删除选中节点", command=self.delete_current_node)
        btn_del.pack(side=tk.LEFT, padx=2, pady=2)

        # 第二行：入口（复制到临时 / 剪切到临时 / 组装为临时节点）
        edit_toolbar_row2 = ttk.Frame(self.right_edit_tab)
        edit_toolbar_row2.pack(side=tk.TOP, fill=tk.X)

        btn_clip_copy = ttk.Button(
            edit_toolbar_row2,
            text="复制到临时",
            command=self.copy_to_clipboard,
        )
        btn_clip_copy.pack(side=tk.LEFT, padx=2, pady=2)

        btn_clip_cut = ttk.Button(
            edit_toolbar_row2,
            text="剪切到临时",
            command=self.cut_to_clipboard,
        )
        btn_clip_cut.pack(side=tk.LEFT, padx=2, pady=2)

        btn_clip_assemble = ttk.Button(
            edit_toolbar_row2,
            text="组装为临时节点",
            command=self.assemble_to_clipboard,
        )
        btn_clip_assemble.pack(side=tk.LEFT, padx=2, pady=2)

        # 第三行：状态标签
        edit_toolbar_row3 = ttk.Frame(self.right_edit_tab)
        edit_toolbar_row3.pack(side=tk.TOP, fill=tk.X)

        self.clipboard_status_var = tk.StringVar(value="模式：普通")
        lbl_clip_status = ttk.Label(edit_toolbar_row3, textvariable=self.clipboard_status_var)
        lbl_clip_status.pack(side=tk.LEFT, padx=8, pady=2)

        # 第四行：出口（替换成临时 / 在下方插入临时 / 退出临时）
        edit_toolbar_row4 = ttk.Frame(self.right_edit_tab)
        edit_toolbar_row4.pack(side=tk.TOP, fill=tk.X)

        btn_use_replace = ttk.Button(
            edit_toolbar_row4,
            text="替换成临时",
            command=self.replace_current_node,
        )
        btn_use_replace.pack(side=tk.LEFT, padx=2, pady=2)

        btn_use_insert = ttk.Button(
            edit_toolbar_row4,
            text="下方插入临时",
            command=self.insert_node_by_current_tab,
        )
        btn_use_insert.pack(side=tk.LEFT, padx=2, pady=2)

        btn_clip_end = ttk.Button(
            edit_toolbar_row4,
            text="退出临时",
            command=self.exit_clipboard_mode,
        )
        btn_clip_end.pack(side=tk.LEFT, padx=6, pady=2)

        self.edit_nb = ttk.Notebook(self.right_edit_tab)
        self.edit_nb.pack(fill=tk.BOTH, expand=True)

        # 按功能分类的编辑子 Tab（先搭结构，后续填具体控件）
        self.edit_tab_structure = ttk.Frame(self.edit_nb)
        self.edit_nb.add(self.edit_tab_structure, text="结构/作用域")
        edit_structure.build(self.edit_tab_structure, self)

        self.edit_tab_control = ttk.Frame(self.edit_nb)
        self.edit_nb.add(self.edit_tab_control, text="控制流")
        edit_control.build(self.edit_tab_control, self)

        self.edit_tab_data = ttk.Frame(self.edit_nb)
        self.edit_nb.add(self.edit_tab_data, text="数据流/赋值")
        edit_dataflow.build(self.edit_tab_data, self)

        self.edit_tab_call = ttk.Frame(self.edit_nb)
        self.edit_nb.add(self.edit_tab_call, text="调用/接口")
        edit_call.build(self.edit_tab_call, self)

        self.edit_tab_expr = ttk.Frame(self.edit_nb)
        self.edit_nb.add(self.edit_tab_expr, text="表达式/常量")
        edit_expr.build(self.edit_tab_expr, self)

        self.edit_tab_exception = ttk.Frame(self.edit_nb)
        self.edit_nb.add(self.edit_tab_exception, text="异常与上下文管理")
        edit_exception.build(self.edit_tab_exception, self)

        self.edit_tab_async = ttk.Frame(self.edit_nb)
        self.edit_nb.add(self.edit_tab_async, text="异步与模式匹配")
        edit_async.build(self.edit_tab_async, self)

        self.edit_tab_import = ttk.Frame(self.edit_nb)
        self.edit_nb.add(self.edit_tab_import, text="导入与模块组织")
        edit_imports.build(self.edit_tab_import, self)

        self.edit_tab_meta = ttk.Frame(self.edit_nb)
        self.edit_nb.add(self.edit_tab_meta, text="元数据与位置信息")
        edit_meta.build(self.edit_tab_meta, self)

        # 子 Tab3：临时 AST 视图（剪贴板源节点，可编辑源码+解析为子树）
        self.clipboard_tab = ttk.Frame(self.right_nb)
        self.right_nb.add(self.clipboard_tab, text="临时AST")

        # 顶部工具条：新建临时源码 / 解析按钮
        clip_toolbar = ttk.Frame(self.clipboard_tab)
        clip_toolbar.pack(side=tk.TOP, fill=tk.X)

        btn_clip_new = ttk.Button(
            clip_toolbar,
            text="新建临时源码",
            command=self.new_temp_from_empty,
        )
        btn_clip_new.pack(side=tk.LEFT, padx=5, pady=5)

        btn_clip_parse = ttk.Button(
            clip_toolbar,
            text="解析为临时子树",
            command=self.parse_clipboard_temp,
        )
        btn_clip_parse.pack(side=tk.LEFT, padx=5, pady=5)

        clip_pane = ttk.Panedwindow(self.clipboard_tab, orient=tk.HORIZONTAL)
        clip_pane.pack(fill=tk.BOTH, expand=True)

        # 左侧：源码
        clip_left = ttk.Frame(clip_pane)
        clip_pane.add(clip_left, weight=1)

        ttk.Label(clip_left, text="临时节点源码").pack(anchor="w", padx=5, pady=(5, 0))
        # 注意：此处 Text 保持可编辑，供用户修改后点击“解析为临时子树”
        self.clipboard_code_text = tk.Text(clip_left, wrap="none", font=("Consolas", 11))
        self.clipboard_code_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0), pady=5)

        sb_clip_code_y = ttk.Scrollbar(clip_left, orient=tk.VERTICAL, command=self.clipboard_code_text.yview)
        sb_clip_code_y.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 5), pady=5)
        sb_clip_code_x = ttk.Scrollbar(clip_left, orient=tk.HORIZONTAL, command=self.clipboard_code_text.xview)
        sb_clip_code_x.pack(side=tk.BOTTOM, fill=tk.X, padx=(5, 0), pady=(0, 5))
        self.clipboard_code_text.configure(yscrollcommand=sb_clip_code_y.set, xscrollcommand=sb_clip_code_x.set)

        # 右侧：AST 子树
        clip_right = ttk.Frame(clip_pane)
        clip_pane.add(clip_right, weight=1)

        ttk.Label(clip_right, text="临时节点 AST 子树").pack(anchor="w", padx=5, pady=(5, 0))
        self.clipboard_tree = ttk.Treeview(clip_right)
        self.clipboard_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0), pady=5)

        sb_clip_tree_y = ttk.Scrollbar(clip_right, orient=tk.VERTICAL, command=self.clipboard_tree.yview)
        sb_clip_tree_y.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 5), pady=5)
        self.clipboard_tree.configure(yscrollcommand=sb_clip_tree_y.set)

        # 初始刷新一次临时 AST 视图
        self._refresh_clipboard_view()

        # 中-Tab2：盒子视图
        box_tab = ttk.Frame(mid_nb)
        mid_nb.add(box_tab, text="Boxes")

        box_tab.rowconfigure(0, weight=0)
        box_tab.rowconfigure(1, weight=1)
        box_tab.columnconfigure(0, weight=1)

        toolbar2 = ttk.Frame(box_tab)
        toolbar2.grid(row=0, column=0, sticky="ew")

        self.box_btn_back = ttk.Button(toolbar2, text="↖ 返回上一层", command=self._box_on_back)
        self.box_btn_back.pack(side=tk.LEFT, padx=5, pady=5)

        self.box_btn_home = ttk.Button(toolbar2, text="⌂ 回到根", command=self._box_on_home)
        self.box_btn_home.pack(side=tk.LEFT, padx=5, pady=5)

        ttk.Label(toolbar2, text="展开深度：").pack(side=tk.LEFT, padx=(15, 2))
        self.box_depth_var = tk.StringVar(value="2")
        self.box_depth_menu = ttk.Combobox(toolbar2, textvariable=self.box_depth_var, state="readonly", width=6)
        self.box_depth_menu["values"] = ("1", "2", "3", "全部")
        self.box_depth_menu.pack(side=tk.LEFT, padx=2, pady=5)
        self.box_depth_menu.bind("<<ComboboxSelected>>", lambda _e: self._redraw_box_view())

        canvas_frame = ttk.Frame(box_tab)
        canvas_frame.grid(row=1, column=0, sticky="nsew")
        box_tab.rowconfigure(1, weight=1)

        self.box_canvas = tk.Canvas(canvas_frame, background="white")
        self.box_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        box_vbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.box_canvas.yview)
        box_vbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.box_canvas.configure(yscrollcommand=box_vbar.set)

        # 左键点击：选中节点；中键/右键拖拽：平移视图
        self.box_canvas.bind("<Button-1>", self._box_on_click)
        self.box_canvas.bind("<ButtonPress-2>", self._box_on_scan_start)
        self.box_canvas.bind("<B2-Motion>", self._box_on_scan_drag)
        self.box_canvas.bind("<ButtonPress-3>", self._box_on_scan_start)
        self.box_canvas.bind("<B3-Motion>", self._box_on_scan_drag)

        # TAB2：项目视图（依赖树 + Import 映射）
        project_tab = ttk.Frame(self.notebook)
        self.notebook.add(project_tab, text="项目视图")
        project_tab.rowconfigure(1, weight=1)
        project_tab.columnconfigure(0, weight=1)
        project_tab.columnconfigure(1, weight=1)

        # 顶部工具条：以当前文件作为入口构建依赖树
        proj_toolbar = ttk.Frame(project_tab)
        proj_toolbar.grid(row=0, column=0, columnspan=2, sticky="ew")


        btn_open_import = ttk.Button(
            proj_toolbar,
            text="打开选中导入模块 AST",
            command=self._on_open_import_module,
        )
        btn_open_import.pack(side=tk.LEFT, padx=5, pady=5)

        btn_build_from_import = ttk.Button(
            proj_toolbar,
            text="以选中导入模块为入口重建依赖树",
            command=self._on_build_project_view_from_import,
        )
        btn_build_from_import.pack(side=tk.LEFT, padx=5, pady=5)

        btn_show_missing = ttk.Button(
            proj_toolbar,
            text="查看未解析导入",
            command=self._on_show_missing_imports,
        )
        btn_show_missing.pack(side=tk.LEFT, padx=5, pady=5)

        btn_export_modules_json = ttk.Button(
            proj_toolbar,
            text="导出模块清单(JSON)",
            command=self._on_export_module_registry_json,
        )
        btn_export_modules_json.pack(side=tk.LEFT, padx=5, pady=5)

        btn_export_modules_csv = ttk.Button(
            proj_toolbar,
            text="导出模块清单(CSV)",
            command=self._on_export_module_registry_csv,
        )
        btn_export_modules_csv.pack(side=tk.LEFT, padx=5, pady=5)

        btn_compact_history = ttk.Button(
            proj_toolbar,
            text="整理历史记录",
            command=self._on_compact_deps_history,
        )
        btn_compact_history.pack(side=tk.LEFT, padx=5, pady=5)


        btn_merge_global = ttk.Button(
            proj_toolbar,
            text="合并所有项目到全局",
            command=self._on_merge_all_to_global,
        )
        btn_merge_global.pack(side=tk.LEFT, padx=5, pady=5)

        # 三栏布局：左 = 项目仪表台，中 = 模块依赖树，右 = Import 映射表
        proj_pane = ttk.Panedwindow(project_tab, orient=tk.HORIZONTAL)
        proj_pane.grid(row=1, column=0, columnspan=2, sticky="nsew")

        # 最左：项目仪表台（全局已注册项目根目录列表）
        dash_frame = ttk.Frame(proj_pane, width=260)
        proj_pane.add(dash_frame, weight=0)

        ttk.Label(dash_frame, text="项目仪表台（全局项目列表）").pack(anchor="w", padx=5, pady=(5, 0))
        btn_refresh_projects = ttk.Button(dash_frame, text="刷新项目列表", command=self._refresh_registered_projects)
        btn_refresh_projects.pack(anchor="w", padx=5, pady=(0, 5))

        self.projects_tree = ttk.Treeview(
            dash_frame,
            columns=("project_root",),
            show="headings",
            height=8,
        )
        self.projects_tree.heading("project_root", text="项目根目录")
        self.projects_tree.column("project_root", width=240, anchor="w")
        self.projects_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0), pady=5)
        sb_proj_y = ttk.Scrollbar(dash_frame, orient=tk.VERTICAL, command=self.projects_tree.yview)
        sb_proj_y.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 5), pady=5)
        self.projects_tree.configure(yscrollcommand=sb_proj_y.set)
        self.projects_tree.bind("<<TreeviewSelect>>", self._on_registered_project_selected)

        # 中：内部 Notebook（模块依赖树 / 项目局部历史）
        mid_frame = ttk.Frame(proj_pane, width=320)
        proj_pane.add(mid_frame, weight=1)

        mid_nb = ttk.Notebook(mid_frame)
        mid_nb.pack(fill=tk.BOTH, expand=True)

        # 中-Tab1：模块依赖树
        dep_tree_tab = ttk.Frame(mid_nb)
        mid_nb.add(dep_tree_tab, text="模块依赖树")

        dep_tree_toolbar = ttk.Frame(dep_tree_tab)
        dep_tree_toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        btn_build_dep_tree = ttk.Button(
            dep_tree_toolbar,
            text="以当前文件为入口构建依赖树",
            command=self._on_build_project_view,
        )
        btn_build_dep_tree.pack(side=tk.LEFT)

        dep_tree_content_frame = ttk.Frame(dep_tree_tab)
        dep_tree_content_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.dep_tree = ttk.Treeview(dep_tree_content_frame)
        self.dep_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0), pady=(0, 5))
        sb_dep_y = ttk.Scrollbar(dep_tree_content_frame, orient=tk.VERTICAL, command=self.dep_tree.yview)
        sb_dep_y.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 5), pady=(0, 5))
        self.dep_tree.configure(yscrollcommand=sb_dep_y.set)
        self.dep_tree.bind("<<TreeviewSelect>>", self._on_dep_tree_select)

        # 中-Tab2：项目局部历史
        history_tab = ttk.Frame(mid_nb)
        mid_nb.add(history_tab, text="项目历史 (JSON)")

        history_toolbar = ttk.Frame(history_tab)
        history_toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        btn_rebuild_history = ttk.Button(
            history_toolbar,
            text="重建本项目历史",
            command=self._on_rebuild_project_history,
        )
        btn_rebuild_history.pack(side=tk.LEFT)

        btn_merge_global2 = ttk.Button(
            history_toolbar,
            text="合并所有项目到全局",
            command=self._on_merge_all_to_global,
        )
        btn_merge_global2.pack(side=tk.LEFT, padx=(5, 0))

        history_content_frame = ttk.Frame(history_tab)
        history_content_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        columns_history = ("from_file", "to_file", "line", "import_name")
        self.project_history_tree = ttk.Treeview(history_content_frame, columns=columns_history, show="headings")
        self.project_history_tree.heading("from_file", text="来源文件")
        self.project_history_tree.heading("to_file", text="目标模块")
        self.project_history_tree.heading("line", text="行号")
        self.project_history_tree.heading("import_name", text="import 写法")
        self.project_history_tree.column("from_file", width=120, anchor="w")
        self.project_history_tree.column("to_file", width=120, anchor="w")
        self.project_history_tree.column("line", width=40, anchor="center")
        self.project_history_tree.column("import_name", width=100, anchor="w")

        sb_hist_y = ttk.Scrollbar(history_content_frame, orient=tk.VERTICAL, command=self.project_history_tree.yview)
        self.project_history_tree.configure(yscrollcommand=sb_hist_y.set)
        self.project_history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb_hist_y.pack(side=tk.RIGHT, fill=tk.Y)

        self._history_row_to_record = {}
        self.project_history_tree.bind("<Double-1>", self._on_project_history_row_double_click)

        # 右：Import 映射表
        right_frame = ttk.Frame(proj_pane)
        proj_pane.add(right_frame, weight=1)

        right_header = ttk.Frame(right_frame)
        right_header.pack(fill=tk.X, padx=5, pady=(5, 0))
        ttk.Label(right_header, text="导入映射表").pack(side=tk.LEFT)
        btn_show_referrers = ttk.Button(
            right_header,
            text="查看引用选中模块的入口",
            command=self._on_show_module_referrers,
        )
        btn_show_referrers.pack(side=tk.LEFT, padx=(10, 0))
        self.imports_tree = ttk.Treeview(
            right_frame,
            columns=("module", "file", "line"),
            show="headings",
        )
        self.imports_tree.heading("module", text="模块名")
        self.imports_tree.heading("file", text="文件路径")
        self.imports_tree.heading("line", text="行号")
        self.imports_tree.column("module", width=200, anchor="w")
        self.imports_tree.column("file", width=320, anchor="w")
        self.imports_tree.column("line", width=60, anchor="center")
        self.imports_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0), pady=5)
        sb_imp_y = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.imports_tree.yview)
        sb_imp_y.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 5), pady=5)
        self.imports_tree.configure(yscrollcommand=sb_imp_y.set)

        # 初始刷新一次项目仪表台
        self._refresh_registered_projects()


        # --------------------- 文件与解析逻辑 ----------------------
    def _on_choose_dir(self) -> None:
        path = filedialog.askdirectory()
        if not path:
            return
        self.current_dir = path
        self.lbl_dir.configure(text=f"当前目录：{path}")
        self._refresh_file_list()

    def _refresh_registered_projects(self) -> None:
        """刷新项目仪表台中显示的全局项目根目录列表。"""

        if self.projects_tree is None:
            return

        # 清空
        for iid in self.projects_tree.get_children():
            self.projects_tree.delete(iid)
        self._project_row_to_path.clear()

        try:
            roots = project_deps.load_registered_project_roots()
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("项目仪表台", f"读取全局项目列表失败：{exc}")
            return

        for root in roots:
            text = str(root)
            item_id = self.projects_tree.insert("", "end", values=(text,))
            self._project_row_to_path[item_id] = root

    def _on_registered_project_selected(self, _event: tk.Event) -> None:  # type: ignore[override]
        """在项目仪表台中选择某个项目根目录：切换当前目录并刷新文件列表。"""

        if self.projects_tree is None:
            return

        sel = self.projects_tree.selection()
        if not sel:
            return
        item_id = sel[0]
        root = self._project_row_to_path.get(item_id)
        if root is None:
            return

        # 切换主界面的当前目录
        self.current_dir = str(root)
        self.lbl_dir.configure(text=f"当前目录：{self.current_dir}")
        self._refresh_file_list()

        # 联动刷新项目历史 Tab
        self._refresh_project_history_view(root)

    def _refresh_file_list(self) -> None:
        self.file_list.delete(0, tk.END)
        if not self.current_dir:
            return
        try:
            entries = sorted(
                [
                    f
                    for f in os.listdir(self.current_dir)
                    if f.lower().endswith(".py") and os.path.isfile(os.path.join(self.current_dir, f))
                ]
            )
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("读取目录失败", str(exc))
            return

        for name in entries:
            self.file_list.insert(tk.END, name)

    def _on_file_selected(self, _event: tk.Event) -> None:  # type: ignore[override]
        sel = self.file_list.curselection()
        if not sel or self.current_dir is None:
            return
        filename = self.file_list.get(sel[0])
        full_path = os.path.join(self.current_dir, filename)
        self.current_file = full_path
        self._load_file(full_path)

    def _load_file(self, path: str) -> None:
        try:
            with open(path, "r", encoding="utf-8") as f:
                source_original = f.read()
            tree_original = ast.parse(source_original, filename=path, mode="exec")
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("解析失败", f"无法解析文件:\n{path}\n\n错误: {exc}")
            return

        # 统一使用紧凑版源码：unparse -> parse
        try:
            compact_source = ast.unparse(tree_original)
            tree_compact = ast.parse(compact_source, filename=path, mode="exec")
            self.current_source = compact_source
            self.current_root = tree_compact
        except Exception:
            # 回退到原始版本
            self.current_source = source_original
            self.current_root = tree_original

        # 更新 Tab1：源码 + AST 树
        self._refresh_tab1()
        # 更新 Tab2：盒子视图
        self._reset_box_view()

    def _rebuild_compact_from_current_root(self) -> None:
        """根据当前 AST 生成紧凑版源码再重新解析，用于刷新行号等位置信息。

        - 成功时：更新 current_source/current_root，并刷新 Tab1/盒子视图。
        - 失败时：弹出错误提示，但仍然基于当前 AST 刷新视图。
        """

        if self.current_root is None:
            return

        try:
            compact_source = ast.unparse(self.current_root)
            new_tree = ast.parse(
                compact_source,
                filename=self.current_file or "<memory>",
                mode="exec",
            )
            self.current_source = compact_source
            self.current_root = new_tree
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror(
                "重建源码失败",
                f"无法从当前 AST 生成紧凑源码并重新解析。\n\n错误: {exc}",
            )

        # 无论成功与否，都刷新一次视图（current_source/current_root 已尽量保持一致）
        self._refresh_tab1()
        self._reset_box_view()

    # ------------------------- TAB1 逻辑 ------------------------
    def _refresh_tab1(self) -> None:
        self.code_text.delete("1.0", tk.END)
        self.code_text.insert("1.0", self.current_source)
        self.code_text.tag_remove("highlight", "1.0", tk.END)

        for item in self.tree.get_children():
            self.tree.delete(item)
        self.node_by_item.clear()

        if self.current_root is None:
            return

        root = self.current_root

        def short_label(node: ast.AST) -> str:
            name = type(node).__name__
            lineno = getattr(node, "lineno", None)
            if isinstance(node, ast.FunctionDef):
                base = f"FunctionDef: {node.name}"
            elif isinstance(node, ast.AsyncFunctionDef):
                base = f"AsyncFunctionDef: {node.name}"
            elif isinstance(node, ast.ClassDef):
                base = f"ClassDef: {node.name}"
            else:
                base = name
            if isinstance(lineno, int) and lineno > 0:
                return f"[L{lineno}] {base}"
            return base

        def insert_node(parent: str, node: ast.AST) -> None:
            label = short_label(node)
            item_id = self.tree.insert(parent, "end", text=label, open=False)
            self.node_by_item[item_id] = node

            for child in ast.iter_child_nodes(node):
                insert_node(item_id, child)

        insert_node("", root)
        # 展开根节点
        for child in self.tree.get_children():
            self.tree.item(child, open=True)

        # 清空详情
        self._show_node_detail(None)

        # 重建 parent_map 以支持编辑操作
        self._rebuild_parent_map()

    def _rebuild_parent_map(self) -> None:
        """根据 current_root 重建 parent_map。"""

        self.parent_map.clear()
        if self.current_root is None:
            return

        root = self.current_root
        # 根节点记录为 (None, "", None)
        self.parent_map[root] = (None, "", None)

        def visit(parent: Optional[ast.AST], node: ast.AST) -> None:
            for field, value in ast.iter_fields(node):
                if isinstance(value, ast.AST):
                    self.parent_map[value] = (node, field, None)
                    visit(node, value)
                elif isinstance(value, list):
                    for idx, item in enumerate(value):
                        if isinstance(item, ast.AST):
                            self.parent_map[item] = (node, field, idx)
                            visit(item, item)

        visit(None, root)

    def _on_tree_select(self, _event: tk.Event) -> None:  # type: ignore[override]
        self.code_text.tag_remove("highlight", "1.0", tk.END)
        sel = self.tree.selection()
        if not sel:
            self._show_node_detail(None)
            return
        item_id = sel[0]
        node = self.node_by_item.get(item_id)
        if node is None:
            self._show_node_detail(None)
            return
        self._show_node_detail(node)
        self._highlight_in_code(node)

    def _show_node_detail(self, node: Optional[ast.AST]) -> None:
        self.current_node = node
        self.detail_text.configure(state="normal")
        self.detail_text.delete("1.0", tk.END)

        if node is None:
            self.detail_text.insert("1.0", "(未选择节点)")
            self.detail_text.configure(state="disabled")
            return

        lines = [f"Node type: {type(node).__name__}"]
        if hasattr(node, "lineno"):
            lines.append(
                f"lineno: {getattr(node, 'lineno', None)}, col_offset: {getattr(node, 'col_offset', None)}"
            )
        if hasattr(node, "end_lineno"):
            lines.append(
                f"end_lineno: {getattr(node, 'end_lineno', None)}, end_col_offset: {getattr(node, 'end_col_offset', None)}"
            )

        # 字段概览
        fields_lines = []
        for field, value in ast.iter_fields(node):
            if isinstance(value, ast.AST):
                fields_lines.append(f"  {field}: <{type(value).__name__}>")
            elif isinstance(value, list):
                if value and all(isinstance(v, ast.AST) for v in value):
                    kinds = ", ".join(type(v).__name__ for v in value)
                    fields_lines.append(f"  {field}: [{kinds}]")
                else:
                    fields_lines.append(f"  {field}: {repr(value)}")
            else:
                fields_lines.append(f"  {field}: {repr(value)}")

        if fields_lines:
            lines.append("\nFields:")
            lines.extend(fields_lines)

        # ast.dump
        try:
            dumped = ast.dump(node, include_attributes=True, indent=2)
            lines.append("\nAST dump (include_attributes=True):")
            lines.append(dumped)
        except TypeError:
            lines.append("\nAST dump:")
            lines.append(ast.dump(node, include_attributes=True))

        self.detail_text.insert("1.0", "\n".join(lines))
        # 根据节点类型切换到对应的编辑子 Tab
        self._select_edit_tab_for_node(node)
        self.detail_text.configure(state="disabled")

    def _highlight_in_code(self, node: Optional[ast.AST]) -> None:
        """在代码视图中高亮给定 AST 节点对应的源码范围。"""

        # 先清除旧高亮
        try:
            self.code_text.tag_remove("highlight", "1.0", tk.END)
        except Exception:  # noqa: BLE001
            return

        if node is None:
            return

        sline = getattr(node, "lineno", None)
        scol = getattr(node, "col_offset", None)
        eline = getattr(node, "end_lineno", None)
        ecol = getattr(node, "end_col_offset", None)

        if sline is None:
            return

        # 起始列默认从 0 开始
        if scol is None:
            scol = 0

        # 结束行/列可能不存在：
        # - 若有 end_lineno / end_col_offset，则使用它们；
        # - 否则高亮整行。
        if eline is not None and ecol is not None:
            start_index = f"{sline}.{scol}"
            end_index = f"{eline}.{ecol}"
        else:
            start_index = f"{sline}.{scol}"
            end_index = f"{sline}.end"

        try:
            self.code_text.tag_add("highlight", start_index, end_index)
            self.code_text.see(start_index)
        except tk.TclError:
            # 索引越界等情况直接忽略高亮
            pass

    # --------------------- 编辑操作（删除 / 替换 / 插入） ----------------------

    def delete_current_node(self) -> None:
        if self.current_root is None or self.current_node is None:
            messagebox.showwarning("删除节点", "当前未选中任何节点。")
            return

        try:
            self.current_root = ast_edit_ops.delete_node(self.current_root, self.current_node, self.parent_map)
        except ast_edit_ops.NodeOperationError as exc:  # type: ignore[attr-defined]
            messagebox.showerror("删除失败", str(exc))
            return

        # 删除后重建紧凑源码并重新解析，刷新整棵树
        self.current_node = None
        self._rebuild_compact_from_current_root()

    def replace_current_node(self) -> None:
        if self.current_root is None or self.current_node is None:
            messagebox.showwarning("替换节点", "当前未选中任何节点。")
            return

        # 使用临时通道中的节点子树作为替换内容
        if self.clipboard_temp_node is None and self.clipboard_source_node is None:
            messagebox.showwarning(
                "替换节点",
                "当前没有临时节点，请先通过复制/剪切/组装或在临时源码中解析生成临时节点子树。",
            )
            return

        source_for_clone = self.clipboard_temp_node or self.clipboard_source_node

        try:
            new_node = ast_clipboard_ops.clone_subtree(source_for_clone)
        except Exception:  # noqa: BLE001
            # clone 失败时退回直接复用引用（通常不会发生）
            new_node = source_for_clone

        try:
            self.current_root = ast_edit_ops.replace_node(
                self.current_root,
                self.current_node,
                new_node,
                self.parent_map,
            )
        except ast_edit_ops.NodeOperationError as exc:  # type: ignore[attr-defined]
            messagebox.showerror("替换失败", str(exc))
            return

        self.current_node = new_node
        # 替换后重建紧凑源码并重新解析，刷新整棵树
        self._rebuild_compact_from_current_root()

    def insert_node_by_current_tab(self) -> None:
        if self.current_root is None or self.current_node is None:
            messagebox.showwarning("插入节点", "当前未选中任何节点。")
            return

        # 使用临时通道中的节点子树作为插入内容
        if self.clipboard_temp_node is None and self.clipboard_source_node is None:
            messagebox.showwarning(
                "插入节点",
                "当前没有临时节点，请先通过复制/剪切/组装或在临时源码中解析生成临时节点子树。",
            )
            return

        source_for_clone = self.clipboard_temp_node or self.clipboard_source_node

        try:
            new_node = ast_clipboard_ops.clone_subtree(source_for_clone)
        except Exception:  # noqa: BLE001
            new_node = source_for_clone

        try:
            self.current_root = ast_edit_ops.insert_after(
                self.current_root,
                self.current_node,
                new_node,
                self.parent_map,
            )
        except ast_edit_ops.NodeOperationError as exc:  # type: ignore[attr-defined]
            messagebox.showerror("插入失败", str(exc))
            return

        self.current_node = new_node
        # 插入后重建紧凑源码并重新解析，刷新整棵树
        self._rebuild_compact_from_current_root()

    # --------------------- 剪贴板模式（复制/剪切） ---------------------

    def _set_clipboard_status(self, text: str) -> None:
        if self.clipboard_status_var is not None:
            self.clipboard_status_var.set(text)

    def _init_clipboard_temp_from_node(self, node: ast.AST) -> None:
        """使用给定节点初始化临时子树和源码文本。

        - 临时子树：优先使用 clone_subtree，失败时退回原节点引用。
        - 临时源码：优先使用 ast.unparse，失败时退回 repr。
        """

        try:
            self.clipboard_temp_node = ast_clipboard_ops.clone_subtree(node)
        except Exception:  # noqa: BLE001
            self.clipboard_temp_node = node

        try:
            self.clipboard_temp_source = ast.unparse(node)
        except Exception:  # noqa: BLE001
            self.clipboard_temp_source = repr(node)

    def copy_to_clipboard(self) -> None:
        """复制入口：用当前选中节点初始化临时节点与源码。"""

        if self.current_node is None:
            messagebox.showwarning("复制到临时节点", "请先在左侧 Tree/Boxes 中选中一个源节点。")
            return

        self.clipboard_active = True
        self.clipboard_mode = "copy"
        self.clipboard_source_node = self.current_node
        self._init_clipboard_temp_from_node(self.current_node)

        self._set_clipboard_status(f"模式：复制中（源: {type(self.current_node).__name__}）")
        self._refresh_clipboard_view()

    def cut_to_clipboard(self) -> None:
        """剪切入口：与复制类似，但后续可以选择删除源节点。"""

        if self.current_node is None:
            messagebox.showwarning("剪切到临时节点", "请先在左侧 Tree/Boxes 中选中一个源节点。")
            return

        self.clipboard_active = True
        self.clipboard_mode = "cut"
        self.clipboard_source_node = self.current_node
        self._init_clipboard_temp_from_node(self.current_node)

        self._set_clipboard_status(f"模式：剪切中（源: {type(self.current_node).__name__}）")
        self._refresh_clipboard_view()

    def assemble_to_clipboard(self) -> None:
        """组装入口：根据当前孙TAB上下文组装一个新节点并作为临时节点。"""

        new_node = self._create_node_for_current_context()
        if new_node is None:
            messagebox.showwarning("组装临时节点", "当前编辑上下文无法自动创建合适的新节点。")
            return

        self.clipboard_active = True
        self.clipboard_mode = "assemble"
        self.clipboard_source_node = None
        self._init_clipboard_temp_from_node(new_node)

        self._set_clipboard_status("模式：组装临时节点")
        self._refresh_clipboard_view()

    def start_clipboard_mode(self) -> None:
        """兼容旧名称：等价于复制到临时节点。"""

        self.copy_to_clipboard()

    def paste_from_clipboard(self) -> None:
        """将剪贴板中的子树粘贴到当前选中节点之后。"""

        # 需要处于临时通道中，且至少有一个临时节点来源（源节点或已解析的临时子树）
        if not self.clipboard_active or (
            self.clipboard_source_node is None and self.clipboard_temp_node is None
        ):
            messagebox.showwarning("粘贴节点", "当前没有可用的临时节点，请先通过复制/剪切/组装或在临时源码中解析生成。")
            return

        if self.current_root is None or self.current_node is None:
            messagebox.showwarning("粘贴节点", "请先在 Tree/Boxes 中选择一个目标节点。")
            return

        # 优先使用用户在“临时AST”中编辑并解析得到的临时子树
        source_for_clone = self.clipboard_temp_node or self.clipboard_source_node

        try:
            new_subtree = ast_clipboard_ops.clone_subtree(source_for_clone)
        except Exception:  # noqa: BLE001
            # 如果 clone 失败，直接复用引用（退化为“移动”语义，但通常不会发生）
            new_subtree = source_for_clone

        try:
            self.current_root = ast_edit_ops.insert_after(
                self.current_root,
                self.current_node,
                new_subtree,
                self.parent_map,
            )
        except ast_edit_ops.NodeOperationError as exc:  # type: ignore[attr-defined]
            messagebox.showerror("粘贴失败", str(exc))
            return

        self.current_node = new_subtree
        # 粘贴后，用当前 AST 生成紧凑源码再重新解析，刷新整棵树的行号等信息
        self._rebuild_compact_from_current_root()

    def exit_clipboard_mode(self) -> None:
        """退出临时节点模式。

        - 若处于剪切模式 (clipboard_mode == "cut") 且存在源节点，则询问是否删除源节点；
        - 确认删除时，在主树中删除该源节点并重建紧凑源码；
        - 最后统一清空剪贴板/临时节点状态并刷新“临时AST”视图。
        """

        # 若本就未激活临时通道，直接做一次清理即可
        if not self.clipboard_active:
            self.clipboard_mode = None
            self.clipboard_source_node = None
            self.clipboard_temp_node = None
            self.clipboard_temp_source = ""
            self._set_clipboard_status("模式：普通")
            self._refresh_clipboard_view()
            return

        # 剪切模式下，且有源节点与当前主树时，询问是否删除源节点
        if (
            self.clipboard_mode == "cut"
            and self.clipboard_source_node is not None
            and self.current_root is not None
        ):
            delete_src = messagebox.askyesno(
                "剪切模式",
                "是否删除原始源节点？\n\n是：视为剪切（源节点会被删除）\n否：视为复制（源节点保留）",
            )

            if delete_src:
                try:
                    self.current_root = ast_edit_ops.delete_node(
                        self.current_root,
                        self.clipboard_source_node,
                        self.parent_map,
                    )
                    # 删除后重建紧凑源码并刷新整棵树
                    self._rebuild_compact_from_current_root()
                except ast_edit_ops.NodeOperationError as exc:  # type: ignore[attr-defined]
                    messagebox.showerror("删除源节点失败", str(exc))

        # 统一重置模式与视图
        self.clipboard_active = False
        self.clipboard_mode = None
        self.clipboard_source_node = None
        self.clipboard_temp_node = None
        self.clipboard_temp_source = ""
        self._set_clipboard_status("模式：普通")
        self._refresh_clipboard_view()

    def _refresh_clipboard_view(self) -> None:
        """根据 clipboard_source_node 刷新“临时AST” Tab 的源码和子树。"""

        # 组件可能尚未构建完毕
        if not hasattr(self, "clipboard_code_text") or not hasattr(self, "clipboard_tree"):
            return

        # 清空现有内容
        self.clipboard_code_text.delete("1.0", tk.END)
        for item in self.clipboard_tree.get_children():
            self.clipboard_tree.delete(item)

        if self.clipboard_source_node is None and self.clipboard_temp_node is None:
            self.clipboard_code_text.insert(
                "1.0",
                "当前没有临时节点。\n\n可以：\n- 在主树中选择一个节点后点击“进入复制模式”；\n- 或在左侧输入一段源码后点击“解析为临时子树”。",
            )
            return

        # 选择展示用的节点：优先使用用户解析得到的临时子树
        node = self.clipboard_temp_node or self.clipboard_source_node

        # 源码展示：优先使用用户当前编辑源码（clipboard_temp_source），否则尝试 unparse
        if self.clipboard_temp_source:
            src = self.clipboard_temp_source
        else:
            try:
                src = ast.unparse(node)
            except Exception:  # noqa: BLE001
                src = repr(node)

        self.clipboard_code_text.insert("1.0", src)

        def short_label(n: ast.AST) -> str:
            name = type(n).__name__
            lineno = getattr(n, "lineno", None)
            if isinstance(lineno, int) and lineno > 0:
                return f"[L{lineno}] {name}"
            return name

        def insert_node(parent: str, n: ast.AST) -> None:
            label = short_label(n)
            item_id = self.clipboard_tree.insert(parent, "end", text=label, open=True)
            for child in ast.iter_child_nodes(n):
                insert_node(item_id, child)

        insert_node("", node)

    def parse_clipboard_temp(self) -> None:
        """从“临时AST”源码文本中解析出新的临时子树。

        用法：
        - 在进入复制模式后，临时 Tab 中会出现源节点的源码和子树；
        - 或者直接在左侧源码 Text 中输入一段代码；
        - 点击本方法对应的按钮进行解析，生成/覆盖“临时节点子树”；
        - 解析成功后，右侧子树会更新，后续替换/插入/粘贴时会优先使用该临时子树。
        """

        src = self.clipboard_code_text.get("1.0", tk.END).strip()
        if not src:
            messagebox.showwarning("解析临时子树", "源码为空，无法解析。")
            return

        # 允许“仅临时源码”作为入口：如果之前未激活剪贴板通道，这里自动激活
        if not self.clipboard_active:
            self.clipboard_active = True
            # 没有源节点时，仅作为“新建临时源码”模式使用
            self._set_clipboard_status("模式：新建临时源码")

        self.clipboard_temp_source = src

        try:
            # 尝试按模块解析，优先取单条语句/表达式作为子树
            module = ast.parse(src, mode="exec")
        except SyntaxError as exc:
            messagebox.showerror("解析失败", f"语法错误：{exc}")
            return

        new_node: ast.AST
        if isinstance(module, ast.Module) and len(module.body) == 1:
            new_node = module.body[0]
        else:
            # 多条语句或其他情况，整体作为 Module 插入
            new_node = module

        self.clipboard_temp_node = new_node
        self._refresh_clipboard_view()

    def new_temp_from_empty(self) -> None:
        """在临时AST Tab 中创建一个空的临时节点作为源码编辑起点。

        - 作为“中途入口”：不依赖当前选中节点或孙TAB上下文；
        - 创建一个最简单的占位语句（例如 `pass`），并通过临时通道初始化；
        - 用户可以在左侧源码区自由编写，然后点击“解析为临时子树”覆盖临时节点子树。
        """

        # 激活临时通道，视为一种组装/源码模式
        self.clipboard_active = True
        self.clipboard_mode = "assemble"
        self.clipboard_source_node = None

        # 创建一个最简单的占位语句节点作为起点
        try:
            module = ast.parse("pass", mode="exec")
            base_node: ast.AST = module.body[0] if isinstance(module, ast.Module) and module.body else module
        except SyntaxError:
            # 理论上不会失败，兜底使用 ast.Pass
            base_node = ast.Pass()

        self._init_clipboard_temp_from_node(base_node)
        self._set_clipboard_status("模式：新建临时源码")
        self._refresh_clipboard_view()

    def _classify_node_category(self, node: ast.AST) -> str:
        """根据 AST 节点类型，返回功能分类 key。

        返回值：structure / control / data / call / expr / exception / async / import / meta
        """

        # 结构 / 作用域
        if isinstance(
            node,
            (
                ast.Module,
                ast.FunctionDef,
                ast.ClassDef,
                ast.Lambda,
            ),
        ):
            return "structure"

        # 控制流（不含异常与上下文）
        if isinstance(
            node,
            (
                ast.If,
                ast.For,
                ast.While,
                ast.AsyncFor,
                ast.Break,
                ast.Continue,
                ast.Return,
                ast.IfExp,
            ),
        ):
            return "control"

        # 数据流 / 赋值
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.NamedExpr)):
            return "data"

        # 调用 / 接口
        if isinstance(node, (ast.Call, ast.keyword)):
            return "call"

        # 异常与上下文管理
        if isinstance(node, (ast.Try, ast.ExceptHandler, ast.Raise, ast.Assert, ast.With, ast.AsyncWith)):
            return "exception"

        # 异步与模式匹配
        if isinstance(
            node,
            (
                ast.AsyncFunctionDef,
                ast.Await,
                ast.AsyncFor,
                ast.AsyncWith,
                ast.Yield,
                ast.YieldFrom,
                getattr(ast, "Match", type("_Dummy", (), {})),  # Python3.10+ 才有
            ),
        ):
            return "async"

        # 导入与模块组织
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.alias)):
            return "import"

        # 表达式/常量（兜底处理常见表达式）
        if isinstance(
            node,
            (
                ast.Constant,
                ast.BinOp,
                ast.UnaryOp,
                ast.BoolOp,
                ast.Compare,
                ast.JoinedStr,
                ast.FormattedValue,
                ast.ListComp,
                ast.DictComp,
                ast.SetComp,
                ast.GeneratorExp,
            ),
        ):
            return "expr"

        # 其他暂时归到结构类，后续可再细分
        return "structure"

    def _select_edit_tab_for_node(self, node: ast.AST) -> None:
        """根据节点类型在右侧激活对应的编辑子 Tab。"""

        # 切换到右侧 Notebook 的“编辑”父 Tab
        try:
            self.right_nb.select(self.right_edit_tab)
        except Exception:
            return

        category = self._classify_node_category(node)

        mapping = {
            "structure": self.edit_tab_structure,
            "control": self.edit_tab_control,
            "data": self.edit_tab_data,
            "call": self.edit_tab_call,
            "expr": self.edit_tab_expr,
            "exception": self.edit_tab_exception,
            "async": self.edit_tab_async,
            "import": self.edit_tab_import,
            "meta": self.edit_tab_meta,
        }

        target = mapping.get(category, self.edit_tab_structure)
        try:
            self.edit_nb.select(target)
        except Exception:
            # Notebook 可能尚未初始化完全，忽略选择错误
            pass

        # 控制流进一步细分到孙 Tab（If / For / While / AsyncFor / Break&Continue / Return / IfExp）
        if category == "control" and hasattr(self, "control_nb"):
            try:
                if isinstance(node, ast.If):
                    self.control_nb.select(self.control_tab_if)
                elif isinstance(node, ast.For):
                    self.control_nb.select(self.control_tab_for)
                elif isinstance(node, ast.While):
                    self.control_nb.select(self.control_tab_while)
                elif isinstance(node, ast.AsyncFor):
                    self.control_nb.select(self.control_tab_asyncfor)
                elif isinstance(node, (ast.Break, ast.Continue)):
                    self.control_nb.select(self.control_tab_brkcont)
                elif isinstance(node, ast.Return):
                    self.control_nb.select(self.control_tab_return)
                elif isinstance(node, ast.IfExp):
                    self.control_nb.select(self.control_tab_ifexp)
            except Exception:
                # 如果内部 Notebook 尚未就绪或属性缺失，则忽略
                pass

        # 结构/作用域：Module / Function / Class / Other Scope
        if category == "structure" and hasattr(self, "structure_nb"):
            try:
                if isinstance(node, ast.Module):
                    self.structure_nb.select(self.structure_tab_module)
                elif isinstance(node, ast.FunctionDef):
                    self.structure_nb.select(self.structure_tab_function)
                elif isinstance(node, ast.ClassDef):
                    self.structure_nb.select(self.structure_tab_class)
                else:
                    self.structure_nb.select(self.structure_tab_other_scope)
            except Exception:
                pass

        # 数据流/赋值：Assign / AnnAssign / AugAssign / Name&Attribute / Other
        if category == "data" and hasattr(self, "dataflow_nb"):
            try:
                if isinstance(node, ast.Assign):
                    self.dataflow_nb.select(self.dataflow_tab_assign)
                elif isinstance(node, ast.AnnAssign):
                    self.dataflow_nb.select(self.dataflow_tab_annassign)
                elif isinstance(node, ast.AugAssign):
                    self.dataflow_nb.select(self.dataflow_tab_augassign)
                elif isinstance(node, (ast.Name, ast.Attribute)):
                    self.dataflow_nb.select(self.dataflow_tab_name_attr)
                else:
                    self.dataflow_nb.select(self.dataflow_tab_other)
            except Exception:
                pass

        # 调用/接口：Call / Args / Keywords / Interface
        if category == "call" and hasattr(self, "call_nb"):
            try:
                if isinstance(node, ast.Call):
                    self.call_nb.select(self.call_tab_call)
                elif isinstance(node, ast.keyword):
                    self.call_nb.select(self.call_tab_keywords)
                else:
                    self.call_nb.select(self.call_tab_interface)
            except Exception:
                pass

        # 表达式/常量：Constant / Op / Compare / Comprehension / Other
        if category == "expr" and hasattr(self, "expr_nb"):
            try:
                if isinstance(node, ast.Constant):
                    self.expr_nb.select(self.expr_tab_constant)
                elif isinstance(node, (ast.BinOp, ast.UnaryOp, ast.BoolOp)):
                    self.expr_nb.select(self.expr_tab_op)
                elif isinstance(node, ast.Compare):
                    self.expr_nb.select(self.expr_tab_compare)
                elif isinstance(
                    node,
                    (
                        ast.ListComp,
                        ast.DictComp,
                        ast.SetComp,
                        ast.GeneratorExp,
                    ),
                ):
                    self.expr_nb.select(self.expr_tab_comprehension)
                else:
                    self.expr_nb.select(self.expr_tab_other)
            except Exception:
                pass

        # 异常与上下文：Try / Except / Raise / Assert / With
        if category == "exception" and hasattr(self, "exception_nb"):
            try:
                if isinstance(node, ast.Try):
                    self.exception_nb.select(self.exception_tab_try)
                elif isinstance(node, ast.ExceptHandler):
                    self.exception_nb.select(self.exception_tab_except)
                elif isinstance(node, ast.Raise):
                    self.exception_nb.select(self.exception_tab_raise)
                elif isinstance(node, ast.Assert):
                    self.exception_nb.select(self.exception_tab_assert)
                elif isinstance(node, (ast.With, ast.AsyncWith)):
                    self.exception_nb.select(self.exception_tab_with)
            except Exception:
                pass

        # 异步与模式匹配：AsyncDef / Await / Yield / Match
        if category == "async" and hasattr(self, "async_nb"):
            try:
                if isinstance(node, (ast.AsyncFunctionDef, ast.AsyncFor, ast.AsyncWith)):
                    self.async_nb.select(self.async_tab_asyncdef)
                elif isinstance(node, ast.Await):
                    self.async_nb.select(self.async_tab_await)
                elif isinstance(node, (ast.Yield, ast.YieldFrom)):
                    self.async_nb.select(self.async_tab_yield)
                elif isinstance(node, getattr(ast, "Match", type("_Dummy", (), {}))):
                    self.async_nb.select(self.async_tab_match)
            except Exception:
                pass

        # 导入与模块组织：Import / ImportFrom / alias / Organize
        if category == "import" and hasattr(self, "imports_nb"):
            try:
                if isinstance(node, ast.Import):
                    self.imports_nb.select(self.imports_tab_import)
                elif isinstance(node, ast.ImportFrom):
                    self.imports_nb.select(self.imports_tab_importfrom)
                elif isinstance(node, ast.alias):
                    self.imports_nb.select(self.imports_tab_alias)
                else:
                    self.imports_nb.select(self.imports_tab_organize)
            except Exception:
                pass

    def _create_node_for_current_context(self) -> Optional[ast.AST]:
        """根据当前编辑 TAB + 孙 TAB，构造一个默认的新 AST 节点。

        这是一个启发式工厂，方便用户快速插入占位节点，后续再在右侧 UI 中细化编辑。
        若当前上下文无法判断合适类型，则返回 None。
        """

        # 顶层编辑分类
        try:
            main_idx = self.edit_nb.index("current")
        except Exception:
            return None

        # 0..8 按顺序对应：结构/作用域, 控制流, 数据流/赋值, 调用/接口, 表达式/常量,
        # 异常, 异步, 导入, 元数据
        # 这里只在前 7 类中创建具体节点，元数据一般不直接产生新语法节点。

        # 结构 / 作用域
        if main_idx == 0 and hasattr(self, "structure_nb"):
            try:
                sub_idx = self.structure_nb.index("current")
            except Exception:
                sub_idx = 0

            if sub_idx == 0:  # Module
                return ast.Module(body=[], type_ignores=[])
            if sub_idx == 1:  # Function
                return ast.FunctionDef(
                    name="new_func",
                    args=ast.arguments(posonlyargs=[], args=[], kwonlyargs=[], kw_defaults=[], defaults=[]),
                    body=[ast.Pass()],
                    decorator_list=[],
                    returns=None,
                    type_comment=None,
                )
            if sub_idx == 2:  # Class
                return ast.ClassDef(
                    name="NewClass",
                    bases=[],
                    keywords=[],
                    body=[ast.Pass()],
                    decorator_list=[],
                )
            # Other Scope
            return ast.Lambda(args=ast.arguments(posonlyargs=[], args=[], kwonlyargs=[], kw_defaults=[], defaults=[]), body=ast.Constant(None))

        # 控制流：根据当前孙 Tab 决定
        if main_idx == 1 and hasattr(self, "control_nb"):
            try:
                sub_idx = self.control_nb.index("current")
            except Exception:
                sub_idx = 0

            if sub_idx == 0:  # If
                return ast.If(test=ast.Constant(True), body=[ast.Pass()], orelse=[])
            if sub_idx == 1:  # For
                return ast.For(
                    target=ast.Name("i", ctx=ast.Store()),
                    iter=ast.Call(func=ast.Name("range", ctx=ast.Load()), args=[ast.Constant(10)], keywords=[]),
                    body=[ast.Pass()],
                    orelse=[],
                    type_comment=None,
                )
            if sub_idx == 2:  # While
                return ast.While(test=ast.Constant(True), body=[ast.Pass()], orelse=[])
            if sub_idx == 3:  # AsyncFor
                return ast.AsyncFor(
                    target=ast.Name("item", ctx=ast.Store()),
                    iter=ast.Name("async_iterable", ctx=ast.Load()),
                    body=[ast.Pass()],
                    orelse=[],
                    type_comment=None,
                )
            if sub_idx == 4:  # Break / Continue，默认创建 Break
                return ast.Break()
            if sub_idx == 5:  # Return
                return ast.Return(value=None)
            if sub_idx == 6:  # IfExp
                return ast.IfExp(test=ast.Constant(True), body=ast.Constant(1), orelse=ast.Constant(0))

        # 数据流 / 赋值
        if main_idx == 2 and hasattr(self, "dataflow_nb"):
            try:
                sub_idx = self.dataflow_nb.index("current")
            except Exception:
                sub_idx = 0

            if sub_idx == 0:  # Assign
                return ast.Assign(targets=[ast.Name("x", ctx=ast.Store())], value=ast.Constant(0), type_comment=None)
            if sub_idx == 1:  # AnnAssign
                return ast.AnnAssign(
                    target=ast.Name("x", ctx=ast.Store()),
                    annotation=ast.Name("int", ctx=ast.Load()),
                    value=ast.Constant(0),
                    simple=1,
                )
            if sub_idx == 2:  # AugAssign
                return ast.AugAssign(
                    target=ast.Name("x", ctx=ast.Store()),
                    op=ast.Add(),
                    value=ast.Constant(1),
                )
            if sub_idx == 3:  # Name / Attribute
                return ast.Assign(
                    targets=[ast.Name("name", ctx=ast.Store())],
                    value=ast.Constant("value"),
                    type_comment=None,
                )
            # Other
            return ast.Assign(targets=[ast.Name("x", ctx=ast.Store())], value=ast.Constant(None), type_comment=None)

        # 调用 / 接口
        if main_idx == 3 and hasattr(self, "call_nb"):
            try:
                sub_idx = self.call_nb.index("current")
            except Exception:
                sub_idx = 0

            func = ast.Name("func", ctx=ast.Load())
            if sub_idx == 0:  # Call
                return ast.Expr(value=ast.Call(func=func, args=[], keywords=[]))
            if sub_idx == 1:  # Args
                return ast.Expr(value=ast.Call(func=func, args=[ast.Constant(1), ast.Constant(2)], keywords=[]))
            if sub_idx == 2:  # Keywords
                return ast.Expr(
                    value=ast.Call(
                        func=func,
                        args=[],
                        keywords=[ast.keyword(arg="x", value=ast.Constant(1))],
                    )
                )
            # Interface
            return ast.Expr(value=ast.Call(func=func, args=[ast.Constant("arg")], keywords=[]))

        # 表达式 / 常量
        if main_idx == 4 and hasattr(self, "expr_nb"):
            try:
                sub_idx = self.expr_nb.index("current")
            except Exception:
                sub_idx = 0

            if sub_idx == 0:  # Constant
                return ast.Expr(value=ast.Constant(0))
            if sub_idx == 1:  # Op
                return ast.Expr(
                    value=ast.BinOp(
                        left=ast.Name("a", ctx=ast.Load()),
                        op=ast.Add(),
                        right=ast.Name("b", ctx=ast.Load()),
                    )
                )
            if sub_idx == 2:  # Compare
                return ast.Expr(
                    value=ast.Compare(
                        left=ast.Name("a", ctx=ast.Load()),
                        ops=[ast.Gt()],
                        comparators=[ast.Name("b", ctx=ast.Load())],
                    )
                )
            if sub_idx == 3:  # Comprehension
                return ast.Expr(
                    value=ast.ListComp(
                        elt=ast.Name("x", ctx=ast.Load()),
                        generators=[
                            ast.comprehension(
                                target=ast.Name("x", ctx=ast.Store()),
                                iter=ast.Name("xs", ctx=ast.Load()),
                                ifs=[],
                                is_async=0,
                            )
                        ],
                    )
                )
            # Other
            return ast.Expr(value=ast.Constant("expr"))

        # 异常 / 上下文
        if main_idx == 5 and hasattr(self, "exception_nb"):
            try:
                sub_idx = self.exception_nb.index("current")
            except Exception:
                sub_idx = 0

            if sub_idx == 0:  # Try
                return ast.Try(body=[ast.Pass()], handlers=[], orelse=[], finalbody=[])
            if sub_idx == 1:  # Except
                return ast.Raise(exc=ast.Name("Exception", ctx=ast.Load()), cause=None)
            if sub_idx == 2:  # Raise
                return ast.Raise(exc=ast.Name("Exception", ctx=ast.Load()), cause=None)
            if sub_idx == 3:  # Assert
                return ast.Assert(test=ast.Constant(True), msg=None)
            if sub_idx == 4:  # With
                return ast.With(
                    items=[ast.withitem(context_expr=ast.Name("cm", ctx=ast.Load()), optional_vars=None)],
                    body=[ast.Pass()],
                    type_comment=None,
                )

        # 异步 / 模式匹配
        if main_idx == 6 and hasattr(self, "async_nb"):
            try:
                sub_idx = self.async_nb.index("current")
            except Exception:
                sub_idx = 0

            if sub_idx == 0:  # AsyncDef
                return ast.AsyncFunctionDef(
                    name="async_func",
                    args=ast.arguments(posonlyargs=[], args=[], kwonlyargs=[], kw_defaults=[], defaults=[]),
                    body=[ast.Pass()],
                    decorator_list=[],
                    returns=None,
                    type_comment=None,
                )
            if sub_idx == 1:  # Await
                return ast.Expr(value=ast.Await(value=ast.Name("coro", ctx=ast.Load())))
            if sub_idx == 2:  # Yield
                return ast.Expr(value=ast.Yield(value=ast.Constant(1)))
            if sub_idx == 3:  # Match
                match_cls = getattr(ast, "Match", None)
                if match_cls is not None:
                    # 创建一个最简 Match 节点
                    return match_cls(
                        subject=ast.Name("value", ctx=ast.Load()),
                        cases=[],
                    )
                return None

        # 导入 / 模块组织
        if main_idx == 7 and hasattr(self, "imports_nb"):
            try:
                sub_idx = self.imports_nb.index("current")
            except Exception:
                sub_idx = 0

            if sub_idx == 0:  # Import
                return ast.Import(names=[ast.alias(name="module", asname=None)])
            if sub_idx == 1:  # ImportFrom
                return ast.ImportFrom(module="pkg", names=[ast.alias(name="name", asname=None)], level=0)
            if sub_idx == 2:  # alias
                return ast.Import(names=[ast.alias(name="name", asname="alias")])
            # Organize
            return ast.Import(names=[ast.alias(name="module", asname=None)])

        # 元数据 TAB 不直接创建语法节点
        return None

    def _build_project_view_from_entry(self, entry_path: Path, project_root: Path) -> None:
        if not entry_path.is_file():
            messagebox.showerror("项目视图", f"入口文件不存在：{entry_path}")
            return

        self._deps_project_root = project_root

        try:
            root = project_deps.build_dependency_tree(entry_path, project_root)
        except Exception as exc:  # noqa: BLE001
            # 打印完整异常堆栈到终端，便于后续排查
            traceback.print_exc()
            messagebox.showerror("项目视图", f"构建依赖树失败：{exc}")
            return

        self.dependency_root = root

        # 重建依赖树视图
        for item in self.dep_tree.get_children():
            self.dep_tree.delete(item)
        self.dep_tree_item_to_node.clear()

        def insert(node: project_deps.ModuleNode, parent: str = "") -> None:
            if self._deps_project_root is not None:
                try:
                    rel = os.path.relpath(node.file_path, self._deps_project_root)
                except ValueError:
                    rel = str(node.file_path)
            else:
                rel = str(node.file_path)

            # 根据 edge_kinds 在依赖树标签上标记导入方式
            prefix = ""
            if node.edge_kinds:
                if "relative" in node.edge_kinds and "absolute" in node.edge_kinds:
                    prefix = "[绝对+相对] "
                elif "relative" in node.edge_kinds:
                    prefix = "[相对] "
                elif "absolute" in node.edge_kinds:
                    prefix = "[绝对] "

            label = f"{prefix}{node.name} ({rel})"
            item_id = self.dep_tree.insert(parent, "end", text=label, open=True)
            self.dep_tree_item_to_node[item_id] = node

            for child in node.children:
                insert(child, item_id)

        insert(root)

        # 清空右侧导入映射表与映射，等待用户选择模块
        for item in self.imports_tree.get_children():
            self.imports_tree.delete(item)
        self.import_row_to_record.clear()

    def _on_build_project_view(self) -> None:
        if not self.current_file:
            messagebox.showwarning("项目视图", "请先在左侧选择一个入口文件。")
            return

        entry_path = Path(self.current_file)

        if self.current_dir:
            project_root = Path(self.current_dir)
        else:
            project_root = entry_path.parent

        self._build_project_view_from_entry(entry_path, project_root)

    def _refresh_project_history_view(self, project_root: Path) -> None:
        """刷新项目历史 Tab 的内容。"""

        if self.project_history_tree is None:
            return

        for iid in self.project_history_tree.get_children():
            self.project_history_tree.delete(iid)
        self._history_row_to_record.clear()

        try:
            records = project_deps.load_project_history_for_root(project_root)
        except Exception as exc:
            messagebox.showerror("项目历史", f"读取项目历史失败：{exc}")
            return

        for rec in records:
            try:
                from_file = Path(rec.get("from_file", ""))
                to_file = Path(rec.get("to_file", ""))
                from_display = os.path.relpath(from_file, project_root)
                to_display = os.path.relpath(to_file, project_root) if project_root in to_file.parents else str(to_file)
            except (ValueError, TypeError):
                from_display = str(rec.get("from_file", ""))
                to_display = str(rec.get("to_file", ""))

            line_str = str(rec.get("line_no", ""))
            import_name = str(rec.get("module_name", ""))

            item_id = self.project_history_tree.insert(
                "",
                "end",
                values=(from_display, to_display, line_str, import_name),
            )
            self._history_row_to_record[item_id] = rec

    def _on_project_history_row_double_click(self, _event: tk.Event) -> None:  # type: ignore[override]
        """双击项目历史记录，打开来源文件并跳转。"""

        if self.project_history_tree is None:
            return

        sel = self.project_history_tree.selection()
        if not sel:
            return
        item_id = sel[0]
        rec = self._history_row_to_record.get(item_id)
        if rec is None:
            return

        try:
            path = Path(rec.get("from_file", ""))
            line_no = int(rec.get("line_no", 0))
        except (ValueError, TypeError):
            return

        if not path.is_file():
            messagebox.showwarning("打开文件", f"无法找到文件：{path}")
            return

        # 打开来源文件并跳到行号
        self.current_dir = str(path.parent)
        self.lbl_dir.configure(text=f"当前目录：{self.current_dir}")
        self._refresh_file_list()

        self.current_file = str(path)
        self._load_file(self.current_file)

        if line_no:
            index = f"{line_no}.0"
            try:
                self.code_text.mark_set("insert", index)
                self.code_text.see(index)
            except Exception:  # noqa: BLE01
                pass

        try:
            tabs = self.notebook.tabs()
            if tabs:
                self.notebook.select(tabs[0])
        except Exception:  # noqa: BLE01
            pass

    def _on_dep_tree_select(self, _event: tk.Event) -> None:  # type: ignore[override]
        # 根据选中的模块节点刷新右侧导入映射表
        for item in self.imports_tree.get_children():
            self.imports_tree.delete(item)
        self.import_row_to_record.clear()

        sel = self.dep_tree.selection()
        if not sel:
            return
        item_id = sel[0]
        node = self.dep_tree_item_to_node.get(item_id)
        if node is None:
            return

        if self._deps_project_root is not None:
            project_root = self._deps_project_root
        elif self.current_dir:
            project_root = Path(self.current_dir)
        else:
            project_root = node.file_path.parent

        for rec in node.imports:
            raw_module = rec.module_name or ""
            level = getattr(rec, "level", 0)

            # 显示用模块名：
            # - 绝对导入: "editor"
            # - 相对导入且有模块名: "[相对] editor"
            # - 相对导入且无模块名（from . import x）: "<相对导入>"
            if level > 0 and raw_module:
                display_module = f"[相对] {raw_module}"
            elif level > 0 and not raw_module:
                display_module = "<相对导入>"
            else:
                display_module = raw_module

            if rec.file_path is not None:
                try:
                    file_display = os.path.relpath(rec.file_path, project_root)
                except ValueError:
                    file_display = str(rec.file_path)
            else:
                # 无项目内/外部物理路径时，尝试识别内建/冻结模块，仅用于展示
                file_display = ""
                if raw_module:
                    try:
                        spec = importlib.util.find_spec(raw_module)
                    except Exception:  # noqa: BLE001
                        spec = None
                    origin = getattr(spec, "origin", None) if spec is not None else None
                    if origin == "built-in":
                        file_display = "<内建模块，无物理文件>"
                    elif origin == "frozen":
                        file_display = "<冻结模块，无物理文件>"
            
            line_str = str(rec.line_no) if getattr(rec, "line_no", None) else ""
            item_id = self.imports_tree.insert("", "end", values=(display_module, file_display, line_str))
            self.import_row_to_record[item_id] = rec

    def _get_selected_import_record(self) -> Optional[project_deps.ImportRecord]:
        sel = self.imports_tree.selection()
        if not sel:
            return None
        item_id = sel[0]
        return self.import_row_to_record.get(item_id)

    def _on_open_import_module(self) -> None:
        rec = self._get_selected_import_record()
        if rec is None:
            messagebox.showwarning("打开导入模块", "请先在导入映射表中选择一条记录。")
            return

        path = rec.file_path
        if path is None:
            messagebox.showwarning("打开导入模块", "选中导入没有可用的物理路径（可能是内建/冻结模块）。")
            return

        if path.is_dir():
            candidate = path / "__init__.py"
            if candidate.is_file():
                path = candidate

        if not path.is_file():
            messagebox.showerror("打开导入模块", f"无法找到可打开的 Python 文件：{path}")
            return

        # 更新当前目录与文件列表
        self.current_dir = str(path.parent)
        self.lbl_dir.configure(text=f"当前目录：{self.current_dir}")
        self._refresh_file_list()

        self.current_file = str(path)
        self._load_file(self.current_file)

        # 在文件列表中选中对应文件（若存在）
        try:
            basename = path.name
            size = self.file_list.size()
            for idx in range(size):
                if self.file_list.get(idx) == basename:
                    self.file_list.selection_clear(0, tk.END)
                    self.file_list.selection_set(idx)
                    self.file_list.see(idx)
                    break
        except Exception:
            pass

        # 切换到结构视图 Tab，方便直接查看 AST
        try:
            tabs = self.notebook.tabs()
            if tabs:
                self.notebook.select(tabs[0])
        except Exception:
            pass

    def _on_build_project_view_from_import(self) -> None:
        rec = self._get_selected_import_record()
        if rec is None:
            messagebox.showwarning("项目视图", "请先在导入映射表中选择一条记录。")
            return

        path = rec.file_path
        if path is None:
            messagebox.showwarning("项目视图", "选中的导入没有可用的物理路径（可能是内建/冻结模块）。")
            return

        # 若该模块仍在当前项目根下，沿用原 project_root；否则以其所在目录作为新的项目根
        if self._deps_project_root is not None and self._deps_project_root in path.parents:
            project_root = self._deps_project_root
        else:
            project_root = path.parent

        self._build_project_view_from_entry(path, project_root)

    def _on_show_missing_imports(self) -> None:
        # 在独立窗口中展示当前依赖树构建过程中未能解析到物理路径的导入
        missing = project_deps.MISSING_IMPORTS
        if not missing:
            messagebox.showinfo("项目视图", "当前依赖树中所有导入都已解析到物理路径。")
            return

        win = tk.Toplevel(self)
        win.title("未解析导入列表")
        win.geometry("780x420")

        # 统计信息
        ttk.Label(win, text=f"共 {len(missing)} 条未解析导入").pack(anchor="w", padx=8, pady=(8, 0))

        frame = ttk.Frame(win)
        frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        columns = ("module", "file", "line")
        tree = ttk.Treeview(frame, columns=columns, show="headings")
        tree.heading("module", text="模块名")
        tree.heading("file", text="所在文件")
        tree.heading("line", text="行号")
        tree.column("module", width=200, anchor="w")
        tree.column("file", width=460, anchor="w")
        tree.column("line", width=60, anchor="center")

        sb_y = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=sb_y.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb_y.pack(side=tk.RIGHT, fill=tk.Y)

        # 选择一个合理的相对路径基准：优先使用当前依赖树的 project_root
        base_root: Optional[Path]
        if self._deps_project_root is not None:
            base_root = self._deps_project_root
        elif self.current_dir:
            base_root = Path(self.current_dir)
        else:
            base_root = None

        # 行 -> MissingImportInfo 映射，方便双击跳转
        row_to_info: dict[str, project_deps.MissingImportInfo] = {}

        for mi in missing:
            if base_root is not None:
                try:
                    file_display = os.path.relpath(mi.from_file, base_root)
                except ValueError:
                    file_display = str(mi.from_file)
            else:
                file_display = str(mi.from_file)

            line_str = str(mi.line_no) if mi.line_no else ""
            item_id = tree.insert("", "end", values=(mi.module_name, file_display, line_str))
            row_to_info[item_id] = mi

        # 双击表格行：打开对应文件并跳到相应行
        def on_row_double_click(_event: tk.Event) -> None:  # type: ignore[override]
            sel = tree.selection()
            if not sel:
                return
            item_id = sel[0]
            mi = row_to_info.get(item_id)
            if mi is None:
                return

            path = mi.from_file
            if not path.is_file():
                messagebox.showwarning("打开文件", f"无法找到文件：{path}")
                return

            # 更新当前目录与文件
            self.current_dir = str(path.parent)
            self.lbl_dir.configure(text=f"当前目录：{self.current_dir}")
            self._refresh_file_list()

            self.current_file = str(path)
            self._load_file(self.current_file)

            # 在文件列表中选中该文件
            try:
                basename = path.name
                size = self.file_list.size()
                for idx in range(size):
                    if self.file_list.get(idx) == basename:
                        self.file_list.selection_clear(0, tk.END)
                        self.file_list.selection_set(idx)
                        self.file_list.see(idx)
                        break
            except Exception:  # noqa: BLE001
                pass

            # 在源码视图中跳转到行号附近
            if mi.line_no:
                index = f"{mi.line_no}.0"
                try:
                    self.code_text.mark_set("insert", index)
                    self.code_text.see(index)
                except Exception:  # noqa: BLE001
                    pass

            # 切换到结构视图 Tab，方便同时看 AST/源码
            try:
                tabs = self.notebook.tabs()
                if tabs:
                    self.notebook.select(tabs[0])
            except Exception:  # noqa: BLE001
                pass

        tree.bind("<Double-1>", on_row_double_click)

        # 底部：导出按钮区域
        btn_frame = ttk.Frame(win)
        btn_frame.pack(fill=tk.X, padx=8, pady=(0, 8))

        def export_as_json() -> None:
            path_str = filedialog.asksaveasfilename(
                parent=win,
                defaultextension=".json",
                filetypes=[("JSON 文件", "*.json"), ("所有文件", "*.*")],
                title="导出未解析导入为 JSON",
            )
            if not path_str:
                return

            data = [
                {
                    "module_name": mi.module_name,
                    "from_file": str(mi.from_file),
                    "line_no": mi.line_no,
                }
                for mi in missing
            ]

            try:
                with open(path_str, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except Exception as exc:  # noqa: BLE001
                messagebox.showerror("导出失败", f"写入 JSON 失败：{exc}")

        def export_as_csv() -> None:
            path_str = filedialog.asksaveasfilename(
                parent=win,
                defaultextension=".csv",
                filetypes=[("CSV 文件", "*.csv"), ("所有文件", "*.*")],
                title="导出未解析导入为 CSV",
            )
            if not path_str:
                return

            try:
                with open(path_str, "w", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(["module_name", "from_file", "line_no"])
                    for mi in missing:
                        writer.writerow([mi.module_name, str(mi.from_file), mi.line_no])
            except Exception as exc:  # noqa: BLE001
                messagebox.showerror("导出失败", f"写入 CSV 失败：{exc}")

        btn_json = ttk.Button(btn_frame, text="导出为 JSON...", command=export_as_json)
        btn_json.pack(side=tk.LEFT, padx=(0, 8))

        btn_csv = ttk.Button(btn_frame, text="导出为 CSV...", command=export_as_csv)
        btn_csv.pack(side=tk.LEFT)

    def _on_show_module_referrers(self) -> None:
        """展示当前选中模块被哪些入口/上游模块引用。"""

        # 优先使用右侧导入映射表中选中的导入项作为目标模块；
        # 若未选中导入或无法获取物理路径，则退回左侧依赖树中选中的模块节点。

        target_path: Optional[Path] = None
        target_name: str = ""
        tree_node = None

        # 1) 先看右侧导入映射表
        rec = self._get_selected_import_record()
        if rec is not None and rec.file_path is not None:
            try:
                target_path = rec.file_path.resolve()
            except Exception:  # noqa: BLE001
                target_path = rec.file_path
            target_name = rec.module_name or target_path.stem

        # 2) 若右侧无有效选择，则退回依赖树
        if target_path is None:
            sel = self.dep_tree.selection()
            if not sel:
                messagebox.showwarning("项目视图", "请先在右侧导入映射表或左侧模块依赖树中选择一个模块。")
                return

            item_id = sel[0]
            tree_node = self.dep_tree_item_to_node.get(item_id)
            if tree_node is None:
                return

            try:
                target_path = tree_node.file_path.resolve()
            except Exception:  # noqa: BLE001
                target_path = tree_node.file_path
            target_name = tree_node.name

        if target_path is None:
            messagebox.showwarning("项目视图", "当前选中项没有可用的物理文件路径，无法查询引用入口。")
            return

        key = target_path.resolve()

        # 1) 当前会话内的反向依赖
        current_refs: list[project_deps.ReverseRefInfo] = list(
            project_deps.REVERSE_DEPENDENCIES.get(key, []),
        )

        # 2) 项目级历史文件（若有）：优先从 ast_deps_history/deps_*.json 聚合
        if self._deps_project_root is not None:
            project_refs = project_deps.load_history_refs_for_target_in_project(key, self._deps_project_root)
        else:
            project_refs = []

        # 3) 全局历史文件（用户 home 目录）
        try:
            global_history = Path.home() / ".ast_viewer_deps.json"
            global_refs = project_deps.load_history_refs_for_target(key, global_history)
        except Exception:  # noqa: BLE001
            global_refs = []

        # 合并并去重，同时记录每条引用来自哪些来源（当前 / 项目历史 / 全局历史）
        class _RefItem:
            def __init__(self, ref: project_deps.ReverseRefInfo) -> None:
                self.ref = ref
                self.sources: set[str] = set()

        items_by_key: dict[tuple[str, str, int, str, str], _RefItem] = {}

        def add_refs(refs: list[project_deps.ReverseRefInfo], source: str) -> None:
            for r in refs:
                k = (
                    str(r.from_file.resolve()),
                    str(r.to_file.resolve()),
                    int(r.line_no or 0),
                    r.kind,
                    r.module_name,
                )
                item = items_by_key.get(k)
                if item is None:
                    item = _RefItem(r)
                    items_by_key[k] = item
                item.sources.add(source)

        add_refs(current_refs, "current")
        add_refs(project_refs, "project")
        add_refs(global_refs, "global")

        items: list[_RefItem] = list(items_by_key.values())

        if not items:
            messagebox.showinfo("项目视图", "当前项目和历史记录中都没有其他模块显式导入该模块。")
            return

        win = tk.Toplevel(self)
        win.title("引用入口列表")
        win.geometry("820x420")

        header_file = tree_node.file_path if tree_node is not None else target_path
        ttk.Label(
            win,
            text=f"模块：{target_name}  (文件：{header_file})\n共有 {len(items)} 条引用 (含历史)",
        ).pack(anchor="w", padx=8, pady=(8, 0))

        # 过滤选项：当前会话 / 项目历史 / 全局历史
        filter_frame = ttk.Frame(win)
        filter_frame.pack(fill=tk.X, padx=8, pady=(4, 0))

        var_current = tk.BooleanVar(value=True)
        var_project = tk.BooleanVar(value=True)
        var_global = tk.BooleanVar(value=True)

        ttk.Checkbutton(filter_frame, text="当前会话", variable=var_current).pack(
            side=tk.LEFT,
            padx=(0, 8),
        )
        ttk.Checkbutton(filter_frame, text="项目历史", variable=var_project).pack(
            side=tk.LEFT,
            padx=(0, 8),
        )
        ttk.Checkbutton(filter_frame, text="全局历史", variable=var_global).pack(
            side=tk.LEFT,
        )

        frame = ttk.Frame(win)
        frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        columns = ("from_module", "from_file", "line", "kind", "import_name", "source")
        tree = ttk.Treeview(frame, columns=columns, show="headings")
        tree.heading("from_module", text="来源模块")
        tree.heading("from_file", text="来源文件")
        tree.heading("line", text="行号")
        tree.heading("kind", text="导入方式")
        tree.heading("import_name", text="import 写法")
        tree.column("from_module", width=160, anchor="w")
        tree.column("from_file", width=360, anchor="w")
        tree.column("line", width=60, anchor="center")
        tree.column("kind", width=80, anchor="center")
        tree.column("import_name", width=140, anchor="w")
        tree.heading("source", text="来源")
        tree.column("source", width=120, anchor="center")

        sb_y = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=sb_y.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb_y.pack(side=tk.RIGHT, fill=tk.Y)

        # 选择一个合理的相对路径基准：优先使用当前依赖树的 project_root
        base_root: Optional[Path]
        if self._deps_project_root is not None:
            base_root = self._deps_project_root
        elif self.current_dir:
            base_root = Path(self.current_dir)
        else:
            base_root = None

        row_to_ref: dict[str, project_deps.ReverseRefInfo] = {}

        def source_label(srcs: set[str]) -> str:
            parts: list[str] = []
            if "current" in srcs:
                parts.append("当前")
            if "project" in srcs:
                parts.append("项目历史")
            if "global" in srcs:
                parts.append("全局历史")
            return "+".join(parts) if parts else ""

        def refresh_tree() -> None:
            # 根据勾选项刷新表格
            for iid in tree.get_children():
                tree.delete(iid)

            enabled_sources: set[str] = set()
            if var_current.get():
                enabled_sources.add("current")
            if var_project.get():
                enabled_sources.add("project")
            if var_global.get():
                enabled_sources.add("global")

            row_to_ref.clear()

            for item in items:
                if not (item.sources & enabled_sources):
                    continue

                ref = item.ref
                from_path = ref.from_file
                if base_root is not None:
                    try:
                        file_display = os.path.relpath(from_path, base_root)
                    except ValueError:
                        file_display = str(from_path)
                else:
                    file_display = str(from_path)

                # 来源模块名：简单使用文件名（去后缀）
                from_module = from_path.stem
                line_str = str(ref.line_no) if ref.line_no else ""
                kind_label = "相对" if ref.kind == "relative" else "绝对"

                if ref.module_name:
                    import_name = ref.module_name
                else:
                    import_name = "<相对导入>"

                src_text = source_label(item.sources)

                row_id = tree.insert(
                    "",
                    "end",
                    values=(from_module, file_display, line_str, kind_label, import_name, src_text),
                )
                row_to_ref[row_id] = ref

        refresh_tree()

        # 勾选框变更时刷新
        def _on_filter_toggle() -> None:
            refresh_tree()

        var_current.trace_add("write", lambda *_: _on_filter_toggle())
        var_project.trace_add("write", lambda *_: _on_filter_toggle())
        var_global.trace_add("write", lambda *_: _on_filter_toggle())

        # 双击某条引用：打开来源文件并跳到对应行
        def on_ref_double_click(_event: tk.Event) -> None:  # type: ignore[override]
            sel_ids = tree.selection()
            if not sel_ids:
                return
            item = sel_ids[0]
            ref = row_to_ref.get(item)
            if ref is None:
                return

            path = ref.from_file
            if not path.is_file():
                messagebox.showwarning("打开文件", f"无法找到文件：{path}")
                return

            # 更新当前目录与文件
            self.current_dir = str(path.parent)
            self.lbl_dir.configure(text=f"当前目录：{self.current_dir}")
            self._refresh_file_list()

            self.current_file = str(path)
            self._load_file(self.current_file)

            # 在文件列表中选中该文件
            try:
                basename = path.name
                size = self.file_list.size()
                for idx in range(size):
                    if self.file_list.get(idx) == basename:
                        self.file_list.selection_clear(0, tk.END)
                        self.file_list.selection_set(idx)
                        self.file_list.see(idx)
                        break
            except Exception:  # noqa: BLE001
                pass

            # 在源码视图中跳转到 import 行附近
            if ref.line_no:
                index = f"{ref.line_no}.0"
                try:
                    self.code_text.mark_set("insert", index)
                    self.code_text.see(index)
                except Exception:  # noqa: BLE001
                    pass

            # 切换到结构视图 Tab
            try:
                tabs = self.notebook.tabs()
                if tabs:
                    self.notebook.select(tabs[0])
            except Exception:  # noqa: BLE001
                pass

        tree.bind("<Double-1>", on_ref_double_click)


    def _on_export_module_registry_json(self) -> None:
        """将当前依赖树导出为模块清单 JSON。"""

        if self.dependency_root is None:
            messagebox.showwarning("导出模块清单", "请先构建依赖树。")
            return

        path_str = filedialog.asksaveasfilename(
            parent=self,
            defaultextension=".json",
            filetypes=[("JSON 文件", "*.json"), ("所有文件", "*.*")],
            title="导出模块清单为 JSON",
        )
        if not path_str:
            return

        # 选择相对路径基准
        base_root: Optional[Path]
        if self._deps_project_root is not None:
            base_root = self._deps_project_root
        elif self.current_dir:
            base_root = Path(self.current_dir)
        else:
            base_root = self.dependency_root.file_path.parent

        def rel(p: Path) -> str:
            if base_root is None:
                return str(p)
            try:
                return os.path.relpath(p, base_root)
            except ValueError:
                return str(p)

        seen_files: set[Path] = set()
        modules: list[dict[str, object]] = []

        def walk(node: project_deps.ModuleNode) -> None:
            real = node.file_path.resolve()
            if real in seen_files:
                return
            seen_files.add(real)

            # edge_kinds 展示为排序后的列表
            edge_kinds = sorted(list(node.edge_kinds)) if node.edge_kinds else []

            imports_data: list[dict[str, object]] = []
            for rec in node.imports:
                kind = "relative" if getattr(rec, "level", 0) > 0 else "absolute"
                target_path: Optional[str]
                if rec.file_path is not None:
                    target_path = rel(rec.file_path)
                else:
                    target_path = None

                imports_data.append(
                    {
                        "module_name": rec.module_name,
                        "file_path": target_path,
                        "kind": kind,
                        "line_no": rec.line_no,
                    },
                )

            modules.append(
                {
                    "name": node.name,
                    "file_path": rel(node.file_path),
                    "edge_kinds": edge_kinds,
                    "imports": imports_data,
                },
            )

            for child in node.children:
                walk(child)

        walk(self.dependency_root)

        registry = {
            "project_root": str(base_root) if base_root is not None else None,
            "entry_file": rel(self.dependency_root.file_path),
            "modules": modules,
        }

        try:
            with open(path_str, "w", encoding="utf-8") as f:
                json.dump(registry, f, ensure_ascii=False, indent=2)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("导出失败", f"写入 JSON 失败：{exc}")

    def _on_export_module_registry_csv(self) -> None:
        """将当前依赖树导出为模块清单 CSV（按模块一行）。"""

        if self.dependency_root is None:
            messagebox.showwarning("导出模块清单", "请先构建依赖树。")
            return

        path_str = filedialog.asksaveasfilename(
            parent=self,
            defaultextension=".csv",
            filetypes=[("CSV 文件", "*.csv"), ("所有文件", "*.*")],
            title="导出模块清单为 CSV",
        )
        if not path_str:
            return

        if self._deps_project_root is not None:
            base_root = self._deps_project_root
        elif self.current_dir:
            base_root = Path(self.current_dir)
        else:
            base_root = self.dependency_root.file_path.parent

        def rel(p: Path) -> str:
            if base_root is None:
                return str(p)
            try:
                return os.path.relpath(p, base_root)
            except ValueError:
                return str(p)

        seen_files: set[Path] = set()
        rows: list[list[str]] = []

        def walk(node: project_deps.ModuleNode) -> None:
            real = node.file_path.resolve()
            if real in seen_files:
                return
            seen_files.add(real)

            edge_kinds = ",".join(sorted(list(node.edge_kinds))) if node.edge_kinds else ""

            import_modules: list[str] = []
            import_files: list[str] = []
            for rec in node.imports:
                if rec.module_name:
                    import_modules.append(rec.module_name)
                if rec.file_path is not None:
                    import_files.append(rel(rec.file_path))

            rows.append(
                [
                    node.name,
                    rel(node.file_path),
                    edge_kinds,
                    str(len(node.imports)),
                    ";".join(sorted(set(import_modules))),
                    ";".join(sorted(set(import_files))),
                ],
            )

            for child in node.children:
                walk(child)

        walk(self.dependency_root)

        try:
            with open(path_str, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        "name",
                        "file_path",
                        "edge_kinds",
                        "import_count",
                        "import_module_names",
                        "import_file_paths",
                    ],
                )
                for row in rows:
                    writer.writerow(row)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("导出失败", f"写入 CSV 失败：{exc}")

    def _on_rebuild_project_history(self) -> None:
        """重建当前项目的局部反向依赖历史文件。"""

        if self._deps_project_root is None:
            messagebox.showwarning("重建项目历史", "请先构建一次依赖树以确定项目根目录。")
            return

        history_dir = (Path(self._deps_project_root).resolve() / project_deps.PROJECT_HISTORY_DIR_NAME)
        if not messagebox.askyesno(
            "重建项目历史",
            "将遍历项目目录下所有 .py 文件，并在以下目录中按模块生成/覆盖 JSON 历史文件：\n"
            f"{history_dir}\n\n每个文件形如 deps_<模块名>.json。确定继续吗？",
        ):
            return

        try:
            count = project_deps.rebuild_project_history(self._deps_project_root)
            messagebox.showinfo("重建项目历史", f"完成！共写入 {count} 条反向依赖记录。")
        except Exception as exc:
            messagebox.showerror("重建项目历史", f"操作失败：{exc}")

    def _on_merge_all_to_global(self) -> None:
        """合并所有已注册项目的局部历史到全局历史文件。"""

        if not messagebox.askyesno(
            "合并所有项目到全局",
            f"将从所有已注册的项目根目录读取局部历史，合并去重后覆盖写入 {Path.home() / '.ast_viewer_deps.json'}，确定吗？",
        ):
            return

        try:
            written, removed = project_deps.merge_registered_project_histories_to_global()
            messagebox.showinfo(
                "合并所有项目到全局",
                f"完成！共写入 {written} 条记录到全局历史，移除了 {removed} 条重复记录。",
            )
        except Exception as exc:
            messagebox.showerror("合并所有项目到全局", f"操作失败：{exc}")

    def _on_compact_deps_history(self) -> None:
        """整理反向依赖历史文件，去掉重复记录。"""

        removed_project = 0
        removed_global = 0

        # 项目级历史：只有在已经有 project_root 时才尝试
        if self._deps_project_root is not None:
            try:
                proj_root = Path(self._deps_project_root).resolve()
                # 1) 新结构：遍历 ast_deps_history/deps_*.json 逐个整理
                history_dir = proj_root / project_deps.PROJECT_HISTORY_DIR_NAME
                if history_dir.is_dir():
                    for json_path in history_dir.glob("deps_*.json"):
                        try:
                            removed_project += project_deps.compact_history_file(json_path)
                        except Exception:  # noqa: BLE001
                            continue

                # 2) 兼容旧结构：单一 .ast_deps_history.json
                legacy_path = proj_root / ".ast_deps_history.json"
                try:
                    removed_project += project_deps.compact_history_file(legacy_path)
                except Exception:  # noqa: BLE001
                    pass
            except Exception:  # noqa: BLE001
                removed_project = 0

        # 全局历史：始终尝试（文件不存在时 compact 会直接返回 0）
        try:
            global_history = Path.home() / ".ast_viewer_deps.json"
            removed_global = project_deps.compact_history_file(global_history)
        except Exception:  # noqa: BLE001
            removed_global = 0

        if self._deps_project_root is not None:
            line_project = f"项目历史：删除 {removed_project} 条重复记录"
        else:
            line_project = "项目历史：未设置项目根目录，略过"

        line_global = f"全局历史：删除 {removed_global} 条重复记录"

        messagebox.showinfo("整理历史记录完成", "\n".join([line_project, line_global]))

    # ------------------------- TAB2 盒子视图 ------------------------
    def _reset_box_view(self) -> None:
        self.box_view_stack.clear()
        self.box_current_node = self.current_root
        self._redraw_box_view()

    def _get_box_max_depth(self) -> int:
        value = self.box_depth_var.get()
        if value == "全部":
            return 9999
        try:
            return int(value)
        except Exception:
            return 2

    def _redraw_box_view(self) -> None:
        self.box_canvas.delete("all")
        self.box_item_to_node.clear()

        if self.box_current_node is None:
            self.box_canvas.create_text(
                10,
                10,
                anchor="nw",
                text="(尚未加载 AST，请先在左侧选择文件)",
                font=("Consolas", 11),
            )
            self.box_canvas.configure(scrollregion=self.box_canvas.bbox("all"))
            return

        max_depth = self._get_box_max_depth()
        box_width = 260
        box_height = 40
        h_indent = 30
        v_spacing = 10

        def node_label(node: ast.AST) -> str:
            name = type(node).__name__
            lineno = getattr(node, "lineno", None)
            if isinstance(node, ast.FunctionDef):
                base = f"FunctionDef: {node.name}"
            elif isinstance(node, ast.AsyncFunctionDef):
                base = f"AsyncFunctionDef: {node.name}"
            elif isinstance(node, ast.ClassDef):
                base = f"ClassDef: {node.name}"
            else:
                base = name
            if isinstance(lineno, int) and lineno > 0:
                return f"[L{lineno}] {base}"
            return base

        def render(node: ast.AST, depth: int, y: int) -> int:
            x = depth * h_indent + 10
            label = node_label(node)

            rect_id = self.box_canvas.create_rectangle(
                x,
                y,
                x + box_width,
                y + box_height,
                outline="#444444",
                fill="#f8f8ff",
            )
            text_id = self.box_canvas.create_text(
                x + 8,
                y + box_height / 2,
                anchor="w",
                text=label,
                font=("Consolas", 10),
            )

            self.box_item_to_node[rect_id] = node
            self.box_item_to_node[text_id] = node

            y_next = y + box_height + v_spacing

            if depth + 1 > max_depth:
                return y_next

            for child in ast.iter_child_nodes(node):
                y_next = render(child, depth + 1, y_next)

            return y_next

        render(self.box_current_node, 0, 10)
        self.box_canvas.configure(scrollregion=self.box_canvas.bbox("all"))

    def _box_on_click(self, event: tk.Event) -> None:  # type: ignore[override]
        if self.box_current_node is None:
            return
        items = self.box_canvas.find_withtag("current") or self.box_canvas.find_closest(event.x, event.y)
        if not items:
            return
        item_id = items[0]
        node = self.box_item_to_node.get(item_id)
        if not isinstance(node, ast.AST):
            return

        # 进入该节点视图
        self.box_view_stack.append(self.box_current_node)
        self.box_current_node = node
        self._redraw_box_view()
        # 同步 Tab1 的详情与高亮
        self._show_node_detail(node)
        self._highlight_in_code(node)

    def _box_on_back(self) -> None:
        if not self.box_view_stack:
            return
        self.box_current_node = self.box_view_stack.pop()
        self._redraw_box_view()

    def _box_on_home(self) -> None:
        if self.current_root is None:
            return
        self.box_view_stack.clear()
        self.box_current_node = self.current_root
        self._redraw_box_view()

    def _box_on_scan_start(self, event: tk.Event) -> None:  # type: ignore[override]
        """开始拖拽平移盒子视图（中键或右键按下）。"""

        self.box_canvas.scan_mark(event.x, event.y)

    def _box_on_scan_drag(self, event: tk.Event) -> None:  # type: ignore[override]
        """拖拽过程中平移视图。"""

        self.box_canvas.scan_dragto(event.x, event.y, gain=1)


def main() -> None:
    app = ASTSuiteApp()
    app.mainloop()


if __name__ == "__main__":
    main()
