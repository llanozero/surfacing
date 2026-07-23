#!/usr/bin/env python3
"""
workflow_editor.py - 工作流可视化编辑器（Tkinter UI）

功能：
- 加载和编辑工作流 JSON
- 工具箱：展示定义区的类和函数
- 定义区编辑：新建/编辑/删除方法和属性
- 工作流编辑：可视化节点和边
- 类的继承与复用
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import json
import ast
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import os


class WorkflowData:
    """工作流数据模型"""
    
    def __init__(self, filepath: Optional[str] = None):
        self.filepath = filepath
        self.data = {
            "schema_version": "2.0",
            "namespaces": [
                {
                    "name": "__global__",
                    "kind": "module",
                    "definitions": []
                }
            ],
            "workflow": {
                "nodes": [],
                "edges": []
            }
        }
        if filepath and os.path.exists(filepath):
            self.load(filepath)
    
    def load(self, filepath: str) -> None:
        """加载工作流 JSON"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
            # 如果是旧格式（没有 schema_version），做一次性转换到 v2 结构
            if "schema_version" not in loaded and "definitions" in loaded:
                namespaces: List[Dict[str, Any]] = []

                # 处理全局函数到 __global__ 命名空间
                global_definitions: List[Dict[str, Any]] = []
                for func in loaded.get("definitions", {}).get("functions", []):
                    global_definitions.append({
                        "name": func.get("name", "unknown_function"),
                        "kind": "function",
                        "inputs": func.get("inputs", []),
                        "outputs": func.get("outputs", ["return_value"]),
                        "code": func.get("code", "")
                    })
                if global_definitions:
                    namespaces.append({
                        "name": "__global__",
                        "kind": "module",
                        "definitions": global_definitions
                    })

                # 处理类到 class 命名空间
                for cls in loaded.get("definitions", {}).get("classes", []):
                    definitions: List[Dict[str, Any]] = []
                    for attr in cls.get("attributes", []):
                        definitions.append({
                            "name": attr,
                            "kind": "variable"
                        })
                    for method in cls.get("methods", []):
                        definitions.append({
                            "name": method.get("name", "unknown_method"),
                            "kind": "function",
                            "inputs": method.get("inputs", []),
                            "outputs": method.get("outputs", ["return_value"]),
                            "code": method.get("code", "")
                        })
                    namespaces.append({
                        "name": cls.get("name", "UnknownClass"),
                        "kind": "class",
                        "definitions": definitions
                    })

                workflow = loaded.get("workflow", {"nodes": [], "edges": []})
                self.data = {
                    "schema_version": "2.0",
                    "namespaces": namespaces,
                    "workflow": workflow
                }
            else:
                self.data = loaded
            self.filepath = filepath
        except Exception as e:
            raise Exception(f"加载工作流失败: {e}")
    
    def save(self, filepath: Optional[str] = None) -> None:
        """保存工作流 JSON"""
        try:
            save_path = filepath or self.filepath
            if not save_path:
                raise Exception("未指定保存路径")
            
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            self.filepath = save_path
        except Exception as e:
            raise Exception(f"保存工作流失败: {e}")
    
    def add_class(self, class_name: str, attributes: List[str] = None, methods: List[Dict] = None) -> None:
        """添加类定义"""
        if attributes is None:
            attributes = []
        if methods is None:
            methods = []

        definitions: List[Dict[str, Any]] = []
        for attr in attributes:
            definitions.append({
                "name": attr,
                "kind": "variable"
            })
        for method in methods:
            definitions.append({
                "name": method.get("name", "unknown_method"),
                "kind": "function",
                "inputs": method.get("inputs", []),
                "outputs": method.get("outputs", ["return_value"]),
                "code": method.get("code", "")
            })

        self.data.setdefault("namespaces", []).append({
            "name": class_name,
            "kind": "class",
            "definitions": definitions
        })
    
    def add_method(self, class_name: str, method_name: str, inputs: List[str] = None, outputs: List[str] = None) -> None:
        """添加方法到类"""
        if inputs is None:
            inputs = []
        if outputs is None:
            outputs = ["return_value"]

        for ns in self.data.get("namespaces", []):
            if ns.get("name") == class_name and ns.get("kind") == "class":
                definitions = ns.setdefault("definitions", [])
                definitions.append({
                    "name": method_name,
                    "kind": "function",
                    "inputs": inputs,
                    "outputs": outputs,
                    "code": f"# {method_name}"
                })
                return
        raise Exception(f"类 {class_name} 不存在")
    
    def add_attribute(self, class_name: str, attr_name: str) -> None:
        """添加属性到类"""
        for ns in self.data.get("namespaces", []):
            if ns.get("name") == class_name and ns.get("kind") == "class":
                definitions = ns.setdefault("definitions", [])
                # 避免重复属性
                for d in definitions:
                    if d.get("kind") == "variable" and d.get("name") == attr_name:
                        return
                definitions.append({
                    "name": attr_name,
                    "kind": "variable"
                })
                return
        raise Exception(f"类 {class_name} 不存在")
    
    def remove_method(self, class_name: str, method_name: str) -> None:
        """删除类的方法"""
        for ns in self.data.get("namespaces", []):
            if ns.get("name") == class_name and ns.get("kind") == "class":
                definitions = ns.get("definitions", [])
                ns["definitions"] = [
                    d for d in definitions
                    if not (d.get("kind") == "function" and d.get("name") == method_name)
                ]
                return
    
    def remove_attribute(self, class_name: str, attr_name: str) -> None:
        """删除类的属性"""
        for ns in self.data.get("namespaces", []):
            if ns.get("name") == class_name and ns.get("kind") == "class":
                definitions = ns.get("definitions", [])
                ns["definitions"] = [
                    d for d in definitions
                    if not (d.get("kind") == "variable" and d.get("name") == attr_name)
                ]
                return
    
    def get_classes(self) -> List[Dict]:
        """获取所有类"""
        classes: List[Dict[str, Any]] = []
        for ns in self.data.get("namespaces", []):
            # 类和 __global__ 模块都视为“类”以便在 UI 中统一展示
            if ns.get("kind") == "class" or (ns.get("kind") == "module" and ns.get("name") == "__global__"):
                attrs: List[str] = []
                methods: List[Dict[str, Any]] = []
                for definition in ns.get("definitions", []):
                    if definition.get("kind") == "variable":
                        attrs.append(definition.get("name", ""))
                    elif definition.get("kind") == "function":
                        methods.append(definition)
                classes.append({
                    "name": ns.get("name", "UnknownClass"),
                    "attributes": attrs,
                    "methods": methods
                })
        return classes
    
    def get_functions(self) -> List[Dict]:
        """获取所有函数"""
        functions: List[Dict[str, Any]] = []
        for ns in self.data.get("namespaces", []):
            if ns.get("kind") == "module" and ns.get("name") == "__global__":
                for definition in ns.get("definitions", []):
                    if definition.get("kind") == "function":
                        functions.append(definition)
        return functions

    def add_global_function(self, func_name: str, inputs: List[str]) -> None:
        """在全局命名空间中添加函数定义"""
        if inputs is None:
            inputs = []
        namespaces = self.data.setdefault("namespaces", [])
        global_ns = None
        for ns in namespaces:
            if ns.get("kind") == "module" and ns.get("name") == "__global__":
                global_ns = ns
                break
        if global_ns is None:
            global_ns = {"name": "__global__", "kind": "module", "definitions": []}
            namespaces.insert(0, global_ns)
        definitions = global_ns.setdefault("definitions", [])
        definitions.append({
            "name": func_name,
            "kind": "function",
            "inputs": inputs,
            "outputs": ["return_value"],
            "code": f"# {func_name}"
        })

    def move_function(self, from_namespace: str, to_namespace: str, func_name: str, new_name: Optional[str] = None) -> None:
        namespaces = self.data.get("namespaces", [])
        from_ns = None
        to_ns = None

        for ns in namespaces:
            name = ns.get("name")
            kind = ns.get("kind")
            if name == from_namespace and (kind == "class" or (kind == "module" and name == "__global__")):
                from_ns = ns
            if name == to_namespace and (kind == "class" or (kind == "module" and name == "__global__")):
                to_ns = ns

        if from_ns is None:
            raise Exception(f"源命名空间不存在: {from_namespace}")
        if to_ns is None:
            raise Exception(f"目标命名空间不存在: {to_namespace}")

        from_defs = from_ns.get("definitions", [])
        func_def = None
        for d in from_defs:
            if d.get("kind") == "function" and d.get("name") == func_name:
                func_def = d
                break

        if func_def is None:
            raise Exception(f"在 {from_namespace} 中未找到函数: {func_name}")

        old_name = func_name
        if new_name and new_name != func_name:
            func_def["name"] = new_name
            func_name = new_name

        from_defs.remove(func_def)
        to_defs = to_ns.setdefault("definitions", [])
        to_defs.append(func_def)

        workflow = self.data.get("workflow", {})
        nodes = workflow.get("nodes", [])

        # 从 __global__ 移动到类：将简单函数调用视为类方法调用
        if from_namespace == "__global__" and to_namespace != "__global__":
            for node in nodes:
                if node.get("type") == "function_call" and node.get("tool") == old_name:
                    node["type"] = "method_call"
                    node["tool"] = f"{to_namespace}.{func_name}"

        # 从类移动到 __global__：将类前缀方法调用视为全局函数调用
        if from_namespace != "__global__" and to_namespace == "__global__":
            full_old = f"{from_namespace}.{old_name}"
            full_new = func_name
            for node in nodes:
                if node.get("type") == "method_call" and node.get("tool") == full_old:
                    node["type"] = "function_call"
                    node["tool"] = full_new

    def move_variable(self, from_namespace: str, to_namespace: str, var_name: str) -> None:
        namespaces = self.data.get("namespaces", [])
        from_ns = None
        to_ns = None

        for ns in namespaces:
            name = ns.get("name")
            kind = ns.get("kind")
            if name == from_namespace and (kind == "class" or (kind == "module" and name == "__global__")):
                from_ns = ns
            if name == to_namespace and (kind == "class" or (kind == "module" and name == "__global__")):
                to_ns = ns

        if from_ns is None:
            raise Exception(f"源命名空间不存在: {from_namespace}")
        if to_ns is None:
            raise Exception(f"目标命名空间不存在: {to_namespace}")

        from_defs = from_ns.get("definitions", [])
        var_def = None
        for d in from_defs:
            if d.get("kind") == "variable" and d.get("name") == var_name:
                var_def = d
                break

        if var_def is None:
            raise Exception(f"在 {from_namespace} 中未找到属性: {var_name}")

        from_defs.remove(var_def)
        to_defs = to_ns.setdefault("definitions", [])
        to_defs.append(var_def)

    def rename_variable(self, namespace: str, old_name: str, new_name: str) -> None:
        namespaces = self.data.get("namespaces", [])
        target_ns = None
        for ns in namespaces:
            name = ns.get("name")
            kind = ns.get("kind")
            if name == namespace and (kind == "class" or (kind == "module" and name == "__global__")):
                target_ns = ns
                break
        if target_ns is None:
            raise Exception(f"命名空间不存在: {namespace}")

        defs = target_ns.get("definitions", [])
        for d in defs:
            if d.get("kind") == "variable" and d.get("name") == old_name:
                d["name"] = new_name
                return
        raise Exception(f"在 {namespace} 中未找到属性: {old_name}")


class ToolboxPanel(ttk.Frame):
    """工具箱面板 - 显示定义区的类和函数"""
    
    def __init__(self, parent, workflow_data: WorkflowData, on_select_callback=None):
        super().__init__(parent)
        self.workflow_data = workflow_data
        self.on_select_callback = on_select_callback
        self.selected_item = None
        self.item_map: Dict[str, Dict[str, Any]] = {}
        
        self._build_ui()
    
    def _build_ui(self) -> None:
        """构建工具箱 UI"""
        # 标题
        title_label = ttk.Label(self, text="命名空间", font=("Arial", 12, "bold"))
        title_label.pack(fill=tk.X, padx=5, pady=5)
        
        # 按钮框
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text="+ 新建类", command=self._add_class).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="+ 新建函数", command=self._add_function).pack(side=tk.LEFT, padx=2)
        
        # 树形视图
        self.tree = ttk.Treeview(self, height=20)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 绑定事件
        self.tree.bind("<Double-1>", self._on_item_double_click)
        self.tree.bind("<Button-3>", self._on_right_click)
        
        # 刷新工具箱
        self.refresh()
    
    def refresh(self) -> None:
        """刷新工具箱显示"""
        # 清空树
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.item_map.clear()
        
        # 基于 namespaces 构建命名空间树
        namespaces = self.workflow_data.data.get("namespaces", [])
        for ns in namespaces:
            ns_name = ns.get("name", "unknown")
            ns_kind = ns.get("kind", "unknown")
            label = f"{ns_name} ({ns_kind})"
            ns_id = self.tree.insert("", tk.END, text=label, open=True)
            self.item_map[ns_id] = {
                "type": "namespace",
                "namespace": ns_name,
                "kind": ns_kind,
            }

            # 命名空间内的定义
            for definition in ns.get("definitions", []):
                def_name = definition.get("name", "")
                def_kind = definition.get("kind", "")
                if def_kind == "function":
                    def_label = f"ƒ {def_name}"
                elif def_kind == "variable":
                    def_label = f"v {def_name}"
                else:
                    def_label = def_name
                def_id = self.tree.insert(ns_id, tk.END, text=def_label, open=False)
                self.item_map[def_id] = {
                    "type": "definition",
                    "namespace": ns_name,
                    "namespace_kind": ns_kind,
                    "kind": def_kind,
                    "name": def_name,
                }

    def find_item(self, namespace: Optional[str] = None, namespace_kind: Optional[str] = None,
                  name: Optional[str] = None, kind: Optional[str] = None) -> Optional[Tuple[str, Dict[str, Any]]]:
        for item_id, info in self.item_map.items():
            info_type = info.get("type")

            if name is None:
                if info_type != "namespace":
                    continue
                if namespace is not None and info.get("namespace") != namespace:
                    continue
                if namespace_kind is not None and info.get("kind") != namespace_kind:
                    continue
                return item_id, info
            else:
                if info_type != "definition":
                    continue
                if namespace is not None and info.get("namespace") != namespace:
                    continue
                if namespace_kind is not None and info.get("namespace_kind") != namespace_kind:
                    continue
                if kind is not None and info.get("kind") != kind:
                    continue
                if info.get("name") != name:
                    continue
                return item_id, info
        return None
    
    def _add_class(self) -> None:
        """添加新类"""
        dialog = tk.Toplevel(self)
        dialog.title("新建类")
        dialog.geometry("300x100")
        
        ttk.Label(dialog, text="类名:").pack(padx=10, pady=5)
        name_entry = ttk.Entry(dialog)
        name_entry.pack(padx=10, pady=5, fill=tk.X)
        
        def create():
            class_name = name_entry.get().strip()
            if not class_name:
                messagebox.showwarning("警告", "类名不能为空")
                return
            
            try:
                self.workflow_data.add_class(class_name)
                self.refresh()
                dialog.destroy()
                messagebox.showinfo("成功", f"类 '{class_name}' 创建成功")
            except Exception as e:
                messagebox.showerror("错误", str(e))
        
        ttk.Button(dialog, text="创建", command=create).pack(pady=10)
    
    def _add_function(self) -> None:
        """添加新函数"""
        dialog = tk.Toplevel(self)
        dialog.title("新建函数")
        dialog.geometry("300x150")
        
        ttk.Label(dialog, text="函数名:").pack(padx=10, pady=5)
        name_entry = ttk.Entry(dialog)
        name_entry.pack(padx=10, pady=5, fill=tk.X)
        
        ttk.Label(dialog, text="参数 (逗号分隔):").pack(padx=10, pady=5)
        params_entry = ttk.Entry(dialog)
        params_entry.pack(padx=10, pady=5, fill=tk.X)
        
        def create():
            func_name = name_entry.get().strip()
            if not func_name:
                messagebox.showwarning("警告", "函数名不能为空")
                return
            
            params = [p.strip() for p in params_entry.get().split(",") if p.strip()]
            
            try:
                # 在全局命名空间中添加函数定义（v2 schema）
                self.workflow_data.add_global_function(func_name, params)
                self.refresh()
                dialog.destroy()
                messagebox.showinfo("成功", f"函数 '{func_name}' 创建成功")
            except Exception as e:
                messagebox.showerror("错误", str(e))
        
        ttk.Button(dialog, text="创建", command=create).pack(pady=10)
    
    def _on_item_double_click(self, event) -> None:
        """双击项目"""
        item = self.tree.selection()[0] if self.tree.selection() else None
        if not item:
            return
        
        info = self.item_map.get(item)
        if self.on_select_callback and info:
            self.on_select_callback(info, item)
    
    def _on_right_click(self, event) -> None:
        """右键菜单"""
        item = self.tree.identify_row(event.y)
        if not item:
            return
        
        self.tree.selection_set(item)
        text = self.tree.item(item, "text")
        
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="编辑", command=lambda: self._edit_item(item, text))
        menu.add_command(label="删除", command=lambda: self._delete_item(item, text))
        menu.post(event.x_root, event.y_root)
    
    def _edit_item(self, item_id, text) -> None:
        """编辑项目"""
        messagebox.showinfo("编辑", f"编辑: {text}")
    
    def _delete_item(self, item_id, text) -> None:
        """删除项目"""
        if messagebox.askyesno("确认", f"确定删除 '{text}' 吗？"):
            self.tree.delete(item_id)


class DefinitionPanel(ttk.Frame):
    """定义区编辑面板 - 编辑类的属性和方法"""
    
    def __init__(self, parent, workflow_data: WorkflowData):
        super().__init__(parent)
        self.workflow_data = workflow_data
        self.current_class = None
        self._current_attribute_name: Optional[str] = None
        self.attr_detail_name_var = tk.StringVar()
        self.attr_type_var = tk.StringVar()
        self._current_method_name: Optional[str] = None
        self.method_detail_name_var = tk.StringVar()
        self.method_detail_inputs_var = tk.StringVar()
        self.method_detail_outputs_var = tk.StringVar()
        self.method_owner_var = tk.StringVar()
        self._updating_owner = False
        
        self._cached_classes: List[Dict[str, Any]] = []
        
        self._build_ui()
    
    def _build_ui(self) -> None:
        """构建定义区 UI"""
        # 标题
        title_label = ttk.Label(self, text="定义区编辑", font=("Arial", 12, "bold"))
        title_label.pack(fill=tk.X, padx=5, pady=5)
        
        # 类选择
        select_frame = ttk.Frame(self)
        select_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(select_frame, text="选择类:").pack(side=tk.LEFT, padx=5)
        self.class_var = tk.StringVar()
        self.class_combo = ttk.Combobox(select_frame, textvariable=self.class_var, state="readonly")
        self.class_combo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.class_combo.bind("<<ComboboxSelected>>", self._on_class_selected)
        
        # 属性区
        attrs_frame = ttk.LabelFrame(self, text="属性")
        attrs_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 属性列表
        self.attrs_listbox = tk.Listbox(attrs_frame, height=6)
        self.attrs_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.attrs_listbox.bind("<<ListboxSelect>>", self._on_attribute_selected)
        
        # 属性按钮
        attrs_btn_frame = ttk.Frame(attrs_frame)
        attrs_btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(attrs_btn_frame, text="+ 新建属性", command=self._add_attribute).pack(side=tk.LEFT, padx=2)
        ttk.Button(attrs_btn_frame, text="- 删除属性", command=self._delete_attribute).pack(side=tk.LEFT, padx=2)
        ttk.Button(attrs_btn_frame, text="更改所属", command=self._change_attribute_owner).pack(side=tk.LEFT, padx=2)
        
        attr_detail_frame = ttk.LabelFrame(self, text="属性详情")
        attr_detail_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        attr_row0 = ttk.Frame(attr_detail_frame)
        attr_row0.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(attr_row0, text="名称:").pack(side=tk.LEFT)
        self.attr_name_entry = ttk.Entry(attr_row0, textvariable=self.attr_detail_name_var)
        self.attr_name_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        attr_row1 = ttk.Frame(attr_detail_frame)
        attr_row1.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(attr_row1, text="类型:").pack(side=tk.LEFT)
        self.attr_type_combo = ttk.Combobox(
            attr_row1,
            textvariable=self.attr_type_var,
            state="readonly",
            values=["None", "str", "int", "float", "bool", "list", "dict"],
            width=10,
        )
        self.attr_type_combo.pack(side=tk.LEFT, padx=5)

        attr_row2 = ttk.Frame(attr_detail_frame)
        attr_row2.pack(fill=tk.BOTH, padx=5, pady=2)
        ttk.Label(attr_row2, text="值:").pack(anchor=tk.W)
        self.attr_value_text = tk.Text(attr_row2, height=3, wrap=tk.WORD)
        self.attr_value_text.pack(fill=tk.BOTH, expand=True)

        save_attr_btn = ttk.Button(attr_detail_frame, text="保存属性", command=self._save_attribute_changes)
        save_attr_btn.pack(padx=5, pady=5, anchor=tk.E)
        
        # 方法区
        methods_frame = ttk.LabelFrame(self, text="方法")
        methods_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 方法列表
        self.methods_listbox = tk.Listbox(methods_frame, height=6)
        self.methods_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.methods_listbox.bind("<<ListboxSelect>>", self._on_method_selected)
        
        # 方法按钮
        methods_btn_frame = ttk.Frame(methods_frame)
        methods_btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(methods_btn_frame, text="+ 新建方法", command=self._add_method).pack(side=tk.LEFT, padx=2)
        ttk.Button(methods_btn_frame, text="- 删除方法", command=self._delete_method).pack(side=tk.LEFT, padx=2)
        ttk.Button(methods_btn_frame, text="✎ 编辑方法", command=self._edit_method).pack(side=tk.LEFT, padx=2)
        ttk.Button(methods_btn_frame, text="更改所属", command=self._change_method_owner).pack(side=tk.LEFT, padx=2)
        
        # 方法详情
        detail_frame = ttk.LabelFrame(self, text="方法详情")
        detail_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        row0 = ttk.Frame(detail_frame)
        row0.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(row0, text="名称:").pack(side=tk.LEFT)
        self.method_name_entry = ttk.Entry(row0, textvariable=self.method_detail_name_var)
        self.method_name_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Label(row0, text="所属:").pack(side=tk.RIGHT)
        self.method_owner_combo = ttk.Combobox(row0, textvariable=self.method_owner_var, state="readonly", width=14)
        self.method_owner_combo.pack(side=tk.RIGHT, padx=5)
        self.method_owner_combo.bind("<<ComboboxSelected>>", self._on_method_owner_changed)

        row1 = ttk.Frame(detail_frame)
        row1.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(row1, text="参数:").pack(side=tk.LEFT)
        self.method_inputs_entry = ttk.Entry(row1, textvariable=self.method_detail_inputs_var)
        self.method_inputs_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        row2 = ttk.Frame(detail_frame)
        row2.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(row2, text="返回值:").pack(side=tk.LEFT)
        self.method_outputs_entry = ttk.Entry(row2, textvariable=self.method_detail_outputs_var)
        self.method_outputs_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        code_frame = ttk.LabelFrame(detail_frame, text="代码")
        code_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.method_code_text = tk.Text(code_frame, height=5, wrap=tk.WORD)
        self.method_code_text.pack(fill=tk.BOTH, expand=True)
        # 方法代码默认为可编辑状态

        save_btn = ttk.Button(detail_frame, text="保存修改", command=self._save_method_changes)
        save_btn.pack(padx=5, pady=5, anchor=tk.E)
        
        # 刷新类列表
        self._refresh_class_list()
    
    def _refresh_class_list(self) -> None:
        """刷新类列表"""
        self._cached_classes = self.workflow_data.get_classes()
        classes = [cls["name"] for cls in self._cached_classes]
        self.class_combo["values"] = classes
    
    def _on_class_selected(self, event) -> None:
        """选择类"""
        class_name = self.class_var.get()
        if not class_name:
            return
        
        self.current_class = class_name
        self._refresh_attributes()
        self._refresh_methods()
        self._clear_attribute_detail()
        self._clear_method_detail()
    
    def _refresh_attributes(self) -> None:
        """刷新属性列表"""
        self.attrs_listbox.delete(0, tk.END)
        
        if not self.current_class:
            return
        
        for cls in self._cached_classes:
            if cls["name"] == self.current_class:
                for attr in cls["attributes"]:
                    self.attrs_listbox.insert(tk.END, attr)
                break
        self._clear_attribute_detail()

    def _on_attribute_selected(self, event) -> None:
        self._update_attribute_detail()

    def _clear_attribute_detail(self) -> None:
        self._current_attribute_name = None
        self.attr_detail_name_var.set("")
        self.attr_type_var.set("None")
        if hasattr(self, "attr_value_text"):
            self.attr_value_text.delete("1.0", tk.END)

    def _update_attribute_detail(self) -> None:
        self._clear_attribute_detail()
        if not self.current_class:
            return
        selection = self.attrs_listbox.curselection()
        if not selection:
            return
        attr_name = self.attrs_listbox.get(selection[0])
        self._current_attribute_name = attr_name

        namespaces = self.workflow_data.data.get("namespaces", [])
        target_def = None
        for ns in namespaces:
            name = ns.get("name")
            kind = ns.get("kind")
            if name == self.current_class and (kind == "class" or (kind == "module" and name == "__global__")):
                for d in ns.get("definitions", []):
                    if d.get("kind") == "variable" and d.get("name") == attr_name:
                        target_def = d
                        break
            if target_def:
                break
        if target_def is None:
            return

        value_type = target_def.get("value_type")
        if value_type is None:
            if "value" not in target_def:
                value_type = "None"
                value = None
            else:
                value = target_def.get("value")
                if value is None:
                    value_type = "None"
                elif isinstance(value, bool):
                    value_type = "bool"
                elif isinstance(value, int):
                    value_type = "int"
                elif isinstance(value, float):
                    value_type = "float"
                elif isinstance(value, str):
                    value_type = "str"
                elif isinstance(value, list):
                    value_type = "list"
                elif isinstance(value, dict):
                    value_type = "dict"
                else:
                    value_type = "str"
        else:
            value = target_def.get("value")

        self.attr_detail_name_var.set(attr_name)
        self.attr_type_var.set(value_type)
        if value is None:
            text = ""
        elif isinstance(value, (list, dict)):
            try:
                text = json.dumps(value, ensure_ascii=False, indent=2)
            except Exception:
                text = str(value)
        else:
            text = str(value)
        self.attr_value_text.delete("1.0", tk.END)
        self.attr_value_text.insert(tk.END, text)

    def _parse_attribute_value(self, value_type: str, raw: str) -> Any:
        if value_type == "None":
            return None
        if value_type == "str":
            return raw
        if value_type == "int":
            try:
                return int(raw)
            except Exception:
                raise ValueError("属性值不是有效的整数")
        if value_type == "float":
            try:
                return float(raw)
            except Exception:
                raise ValueError("属性值不是有效的浮点数")
        if value_type == "bool":
            lower = raw.lower()
            if lower in ("true", "1", "yes", "y", "t"):
                return True
            if lower in ("false", "0", "no", "n", "f"):
                return False
            raise ValueError("属性值不是有效的布尔值（可用 true/false 或 1/0）")
        if value_type in ("list", "dict"):
            if not raw:
                return [] if value_type == "list" else {}
            try:
                value = json.loads(raw)
            except Exception:
                try:
                    value = ast.literal_eval(raw)
                except Exception:
                    raise ValueError("属性值不是有效的列表/字典表达式（请使用 JSON 或 Python 字面量）")
            if value_type == "list" and not isinstance(value, list):
                raise ValueError("属性类型为 list，但解析结果不是列表")
            if value_type == "dict" and not isinstance(value, dict):
                raise ValueError("属性类型为 dict，但解析结果不是字典")
            return value
        return raw

    def _save_attribute_changes(self) -> None:
        if not self.current_class:
            messagebox.showwarning("警告", "请先选择一个类或 __global__")
            return
        if not self._current_attribute_name:
            messagebox.showwarning("警告", "请先选择一个属性")
            return

        old_name = self._current_attribute_name
        new_name = self.attr_detail_name_var.get().strip()
        if not new_name:
            messagebox.showwarning("警告", "属性名不能为空")
            return
        if new_name != old_name and self._namespace_has_name(self.current_class, new_name):
            messagebox.showwarning("名称重复", "当前命名空间已存在同名属性或方法，请修改名称")
            return

        value_type = self.attr_type_var.get().strip() or "None"
        raw = self.attr_value_text.get("1.0", tk.END).strip()
        try:
            value = self._parse_attribute_value(value_type, raw)
        except ValueError as e:
            messagebox.showerror("错误", str(e))
            return

        namespaces = self.workflow_data.data.get("namespaces", [])
        target_def = None
        for ns in namespaces:
            name = ns.get("name")
            kind = ns.get("kind")
            if name == self.current_class and (kind == "class" or (kind == "module" and name == "__global__")):
                for d in ns.get("definitions", []):
                    if d.get("kind") == "variable" and d.get("name") == old_name:
                        target_def = d
                        break
            if target_def:
                break

        if target_def is None:
            messagebox.showerror("错误", f"在 {self.current_class} 中未找到属性: {old_name}")
            return

        target_def["name"] = new_name
        target_def["value_type"] = value_type
        target_def["value"] = value

        self._cached_classes = self.workflow_data.get_classes()
        self._refresh_attributes()
        self.select_attribute(new_name)

        editor = self.winfo_toplevel()
        if hasattr(editor, "toolbox"):
            editor.toolbox.refresh()
        messagebox.showinfo("成功", "属性已保存")
    
    def _refresh_methods(self) -> None:
        """刷新方法列表"""
        self.methods_listbox.delete(0, tk.END)
        
        if not self.current_class:
            return
        
        for cls in self.workflow_data.get_classes():
            if cls["name"] == self.current_class:
                for method in cls["methods"]:
                    self.methods_listbox.insert(tk.END, method["name"])
                break

    def select_method(self, method_name: str) -> None:
        self.methods_listbox.selection_clear(0, tk.END)
        size = self.methods_listbox.size()
        for i in range(size):
            if self.methods_listbox.get(i) == method_name:
                self.methods_listbox.selection_set(i)
                self.methods_listbox.see(i)
                self._update_method_detail()
                break

    def select_attribute(self, attr_name: str) -> None:
        self.attrs_listbox.selection_clear(0, tk.END)
        size = self.attrs_listbox.size()
        for i in range(size):
            if self.attrs_listbox.get(i) == attr_name:
                self.attrs_listbox.selection_set(i)
                self.attrs_listbox.see(i)
                break
    
    def show_global_function(self, func_name: str) -> None:
        # 将 __global__ 视为特殊类，复用相同展示逻辑
        self.class_var.set("__global__")
        self._on_class_selected(None)
        self.select_method(func_name)
    
    def _on_method_selected(self, event) -> None:
        self._update_method_detail()

    def _namespace_has_name(self, namespace: str, name: str) -> bool:
        classes = self.workflow_data.get_classes()
        for cls in classes:
            if cls["name"] == namespace:
                if name in cls.get("attributes", []):
                    return True
                for m in cls.get("methods", []):
                    if m.get("name") == name:
                        return True
                return False
        return False

    def _clear_method_detail(self) -> None:
        self._current_method_name = None
        self.method_detail_name_var.set("")
        self.method_detail_inputs_var.set("")
        self.method_detail_outputs_var.set("")
        self.method_code_text.configure(state="normal")
        self.method_code_text.delete("1.0", tk.END)

    def _update_method_detail(self) -> None:
        self._clear_method_detail()
        if not self.current_class:
            return
        selection = self.methods_listbox.curselection()
        if not selection:
            return
        method_name = self.methods_listbox.get(selection[0])
        self._current_method_name = method_name
        for cls in self.workflow_data.get_classes():
            if cls["name"] == self.current_class:
                for method in cls["methods"]:
                    if method.get("name") == method_name:
                        self.method_detail_name_var.set(method_name)
                        self.method_detail_inputs_var.set(", ".join(method.get("inputs", [])))
                        self.method_detail_outputs_var.set(", ".join(method.get("outputs", [])))
                        code = method.get("code", "")
                        owners = [c["name"] for c in self.workflow_data.get_classes()]
                        self._updating_owner = True
                        self.method_owner_combo["values"] = owners
                        self.method_owner_var.set(self.current_class)
                        self._updating_owner = False
                        self.method_code_text.configure(state="normal")
                        self.method_code_text.delete("1.0", tk.END)
                        if code:
                            self.method_code_text.insert(tk.END, code)
                        return

    def _save_method_changes(self) -> None:
        if not self.current_class:
            messagebox.showwarning("警告", "请先选择一个类或 __global__")
            return
        if not self._current_method_name:
            messagebox.showwarning("警告", "请先选择一个方法")
            return

        old_name = self._current_method_name
        new_name = self.method_detail_name_var.get().strip()
        owner = self.method_owner_var.get().strip() or self.current_class
        if not new_name or not owner:
            messagebox.showwarning("警告", "请先选择要保存的方法")
            return

        # 命名空间内重名检查
        if new_name != old_name and self._namespace_has_name(owner, new_name):
            messagebox.showwarning("名称重复", "当前命名空间已存在同名属性或方法，请修改名称")
            return

        inputs_str = self.method_detail_inputs_var.get()
        outputs_str = self.method_detail_outputs_var.get()
        inputs = [p.strip() for p in inputs_str.split(",") if p.strip()] if inputs_str else []
        outputs = [p.strip() for p in outputs_str.split(",") if p.strip()] if outputs_str else []
        code = self.method_code_text.get("1.0", tk.END).rstrip("\n")

        namespaces = self.workflow_data.data.get("namespaces", [])
        target_ns = None
        for ns in namespaces:
            name = ns.get("name")
            kind = ns.get("kind")
            if name == owner and (kind == "class" or (kind == "module" and name == "__global__")):
                target_ns = ns
                break

        if target_ns is None:
            messagebox.showerror("错误", f"未找到命名空间: {owner}")
            return

        defs = target_ns.get("definitions", [])
        for d in defs:
            if d.get("kind") == "function" and d.get("name") == old_name:
                # 更新定义
                d["name"] = new_name
                d["inputs"] = inputs
                d["outputs"] = outputs if outputs else ["return_value"]
                d["code"] = code

                # 同步更新 workflow 中对该方法的引用
                workflow = self.workflow_data.data.get("workflow", {})
                nodes = workflow.get("nodes", [])
                if owner == "__global__":
                    for node in nodes:
                        if node.get("type") == "function_call" and node.get("tool") == old_name:
                            node["tool"] = new_name
                else:
                    full_old = f"{owner}.{old_name}"
                    full_new = f"{owner}.{new_name}"
                    for node in nodes:
                        if node.get("type") == "method_call" and node.get("tool") == full_old:
                            node["tool"] = full_new

                # 刷新 UI
                self._cached_classes = self.workflow_data.get_classes()
                self._refresh_methods()
                self.select_method(new_name)

                editor = self.winfo_toplevel()
                if hasattr(editor, "toolbox"):
                    editor.toolbox.refresh()
                if hasattr(editor, "_draw_workflow"):
                    editor._draw_workflow()

                messagebox.showinfo("成功", "方法已保存")
                return

        messagebox.showerror("错误", f"在 {owner} 中未找到方法: {old_name}")

    def _on_method_owner_changed(self, event) -> None:
        if self._updating_owner:
            return
        if not self.current_class:
            return
        selection = self.methods_listbox.curselection()
        if not selection:
            return
        new_owner = self.method_owner_var.get().strip()
        if not new_owner or new_owner == self.current_class:
            return
        method_name = self.methods_listbox.get(selection[0])
        try:
            self.workflow_data.move_function(self.current_class, new_owner, method_name)
        except Exception as e:
            messagebox.showerror("错误", str(e))
            self._updating_owner = True
            self.method_owner_var.set(self.current_class)
            self._updating_owner = False
            return

        self.current_class = new_owner
        self._refresh_class_list()
        self.class_var.set(new_owner)
        self._refresh_attributes()
        self._refresh_methods()
        self.select_method(method_name)

        editor = self.winfo_toplevel()
        if hasattr(editor, "toolbox"):
            editor.toolbox.refresh()
    
    def _add_attribute(self) -> None:
        """添加属性"""
        if not self.current_class:
            messagebox.showwarning("警告", "请先选择一个类")
            return
        
        while True:
            attr_name = simpledialog.askstring("新建属性", "属性名:")
            if not attr_name:
                return
            if self._namespace_has_name(self.current_class, attr_name):
                messagebox.showwarning("名称重复", "当前命名空间已存在同名属性或方法，请修改名称")
                continue
            break
        
        try:
            self.workflow_data.add_attribute(self.current_class, attr_name)
            self._refresh_attributes()
            messagebox.showinfo("成功", f"属性 '{attr_name}' 添加成功")
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def _change_attribute_owner(self) -> None:
        if not self.current_class:
            messagebox.showwarning("警告", "请先选择一个类")
            return
        selection = self.attrs_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请选择一个属性")
            return
        attr_name = self.attrs_listbox.get(selection[0])

        owners = [c["name"] for c in self.workflow_data.get_classes()]
        dialog = tk.Toplevel(self)
        dialog.title("更改属性所属")
        dialog.geometry("280x120")

        ttk.Label(dialog, text=f"属性: {attr_name}").pack(padx=10, pady=5)
        ttk.Label(dialog, text="新的所属:").pack(padx=10, pady=5)
        owner_var = tk.StringVar(value=self.current_class)
        owner_combo = ttk.Combobox(dialog, textvariable=owner_var, values=owners, state="readonly")
        owner_combo.pack(padx=10, pady=5, fill=tk.X)

        def apply_change():
            new_owner = owner_var.get().strip()
            if not new_owner or new_owner == self.current_class:
                dialog.destroy()
                return

            new_name = attr_name
            if self._namespace_has_name(new_owner, new_name):
                while True:
                    candidate = simpledialog.askstring(
                        "名称冲突",
                        f"命名空间 '{new_owner}' 中已存在同名属性或方法，请修改名称:",
                        initialvalue=new_name,
                        parent=dialog,
                    )
                    if not candidate:
                        return
                    if self._namespace_has_name(new_owner, candidate):
                        messagebox.showwarning("名称重复", "该名称仍然重复，请再次修改")
                        continue
                    new_name = candidate.strip()
                    break
                try:
                    self.workflow_data.rename_variable(self.current_class, attr_name, new_name)
                except Exception as e:
                    messagebox.showerror("错误", str(e))
                    return
                attr_name_local = new_name
            else:
                attr_name_local = attr_name

            try:
                self.workflow_data.move_variable(self.current_class, new_owner, attr_name_local)
            except Exception as e:
                messagebox.showerror("错误", str(e))
                return

            self.current_class = new_owner
            self._refresh_class_list()
            self.class_var.set(new_owner)
            self._refresh_attributes()

            editor = self.winfo_toplevel()
            if hasattr(editor, "toolbox"):
                editor.toolbox.refresh()
            dialog.destroy()

        ttk.Button(dialog, text="确认", command=apply_change).pack(pady=10)
    
    def _delete_attribute(self) -> None:
        """删除属性"""
        if not self.current_class:
            return
        
        selection = self.attrs_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请选择一个属性")
            return
        
        attr_name = self.attrs_listbox.get(selection[0])
        if messagebox.askyesno("确认", f"确定删除属性 '{attr_name}' 吗？"):
            try:
                self.workflow_data.remove_attribute(self.current_class, attr_name)
                self._refresh_attributes()
            except Exception as e:
                messagebox.showerror("错误", str(e))
    
    def _add_method(self) -> None:
        """添加方法"""
        if not self.current_class:
            messagebox.showwarning("警告", "请先选择一个类")
            return
        
        dialog = tk.Toplevel(self)
        dialog.title("新建方法")
        dialog.geometry("300x150")
        
        ttk.Label(dialog, text="方法名:").pack(padx=10, pady=5)
        name_entry = ttk.Entry(dialog)
        name_entry.pack(padx=10, pady=5, fill=tk.X)
        
        ttk.Label(dialog, text="参数 (逗号分隔):").pack(padx=10, pady=5)
        params_entry = ttk.Entry(dialog)
        params_entry.pack(padx=10, pady=5, fill=tk.X)
        
        def create():
            method_name = name_entry.get().strip()
            if not method_name:
                messagebox.showwarning("警告", "方法名不能为空")
                return
            if self._namespace_has_name(self.current_class, method_name):
                messagebox.showwarning("名称重复", "当前命名空间已存在同名属性或方法，请修改名称")
                return
            
            params = [p.strip() for p in params_entry.get().split(",") if p.strip()]
            
            try:
                self.workflow_data.add_method(self.current_class, method_name, params)
                self._refresh_methods()
                dialog.destroy()
                messagebox.showinfo("成功", f"方法 '{method_name}' 添加成功")
            except Exception as e:
                messagebox.showerror("错误", str(e))
        
        ttk.Button(dialog, text="创建", command=create).pack(pady=10)
    
    def _delete_method(self) -> None:
        """删除方法"""
        if not self.current_class:
            return
        
        selection = self.methods_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请选择一个方法")
            return
        
        method_name = self.methods_listbox.get(selection[0])
        if messagebox.askyesno("确认", f"确定删除方法 '{method_name}' 吗？"):
            try:
                self.workflow_data.remove_method(self.current_class, method_name)
                self._refresh_methods()
            except Exception as e:
                messagebox.showerror("错误", str(e))
    
    def _edit_method(self) -> None:
        """编辑方法"""
        selection = self.methods_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请选择一个方法")
            return
        
        method_name = self.methods_listbox.get(selection[0])
        messagebox.showinfo("编辑", f"编辑方法: {method_name}")

    def _change_method_owner(self) -> None:
        if not self.current_class:
            messagebox.showwarning("警告", "请先选择一个类或 __global__")
            return
        selection = self.methods_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请选择一个方法")
            return
        method_name = self.methods_listbox.get(selection[0])

        owners = [c["name"] for c in self.workflow_data.get_classes()]
        dialog = tk.Toplevel(self)
        dialog.title("更改方法所属")
        dialog.geometry("280x140")

        ttk.Label(dialog, text=f"方法: {method_name}").pack(padx=10, pady=5)
        ttk.Label(dialog, text="新的所属:").pack(padx=10, pady=5)
        owner_var = tk.StringVar(value=self.current_class)
        owner_combo = ttk.Combobox(dialog, textvariable=owner_var, values=owners, state="readonly")
        owner_combo.pack(padx=10, pady=5, fill=tk.X)

        def apply_change():
            new_owner = owner_var.get().strip()
            if not new_owner or new_owner == self.current_class:
                dialog.destroy()
                return

            new_name = method_name
            if self._namespace_has_name(new_owner, new_name):
                while True:
                    candidate = simpledialog.askstring(
                        "名称冲突",
                        f"命名空间 '{new_owner}' 中已存在同名属性或方法，请修改名称:",
                        initialvalue=new_name,
                        parent=dialog,
                    )
                    if not candidate:
                        return
                    if self._namespace_has_name(new_owner, candidate):
                        messagebox.showwarning("名称重复", "该名称仍然重复，请再次修改")
                        continue
                    new_name = candidate.strip()
                    break

            try:
                self.workflow_data.move_function(self.current_class, new_owner, method_name, new_name if new_name != method_name else None)
            except Exception as e:
                messagebox.showerror("错误", str(e))
                return

            self.current_class = new_owner
            self._refresh_class_list()
            self.class_var.set(new_owner)
            self._refresh_attributes()
            self._refresh_methods()
            self.select_method(new_name)

            editor = self.winfo_toplevel()
            if hasattr(editor, "toolbox"):
                editor.toolbox.refresh()
            if hasattr(editor, "_draw_workflow"):
                editor._draw_workflow()
            dialog.destroy()

        ttk.Button(dialog, text="确认", command=apply_change).pack(pady=10)


class WorkflowEditor(tk.Tk):
    """工作流编辑器主窗口"""
    
    def __init__(self, filepath: Optional[str] = None):
        super().__init__()
        self.title("工作流编辑器")
        self.geometry("1200x700")
        
        self.workflow_data = WorkflowData(filepath)
        self.node_list = None
        self._current_cfg: Optional[Dict[str, Any]] = None
        self._current_cfg_path: Optional[str] = None
        
        self._build_ui()
        self._setup_menu()
        
        # 如果提供了文件路径，更新标题
        if filepath:
            self.title(f"工作流编辑器 - {filepath}")
        
        # 刷新 UI
        self.toolbox.refresh()
        self.definition_panel._refresh_class_list()
        self._draw_workflow()
    
    def _build_ui(self) -> None:
        """构建主 UI"""
        # 主框架
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧：命名空间树
        left_frame = ttk.Frame(main_frame, width=260)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=5, pady=5)
        
        self.toolbox = ToolboxPanel(left_frame, self.workflow_data, on_select_callback=self._on_namespace_selected)
        self.toolbox.pack(fill=tk.BOTH, expand=True)
        
        # 中间：定义编辑区
        center_frame = ttk.Frame(main_frame, width=360)
        center_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=5, pady=5)

        self.definition_panel = DefinitionPanel(center_frame, self.workflow_data)
        self.definition_panel.pack(fill=tk.BOTH, expand=True)

        # 右侧：执行流程区（节点列表 + 画布）
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        ttk.Label(right_frame, text="执行流程", font=("Arial", 12, "bold")).pack(fill=tk.X, pady=5)

        # 节点列表
        list_frame = ttk.Frame(right_frame)
        list_frame.pack(fill=tk.X, padx=5, pady=5)

        self.node_list = tk.Listbox(list_frame, height=8)
        self.node_list.pack(side=tk.LEFT, fill=tk.X, expand=True)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.node_list.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.node_list.config(yscrollcommand=scrollbar.set)
        self.node_list.bind("<<ListboxSelect>>", self._on_node_selected)

        # 画布
        self.canvas = tk.Canvas(right_frame, bg="white", relief=tk.SUNKEN)
        self.canvas.pack(fill=tk.BOTH, expand=True)
    
    def _setup_menu(self) -> None:
        """设置菜单"""
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="新建", command=self._new_workflow)
        file_menu.add_command(label="打开", command=self._open_workflow)
        file_menu.add_command(label="打开CFG", command=self._open_cfg_file)
        file_menu.add_command(label="保存", command=self._save_workflow)
        file_menu.add_command(label="另存为", command=self._save_as_workflow)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.quit)
        
        # 编辑菜单
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="编辑", menu=edit_menu)
        edit_menu.add_command(label="新建类", command=self._new_class)
        edit_menu.add_command(label="新建函数", command=self._new_function)
    
    def _new_workflow(self) -> None:
        """新建工作流"""
        self.workflow_data = WorkflowData()
        self.toolbox.refresh()
        self.definition_panel._refresh_class_list()
        messagebox.showinfo("成功", "新建工作流成功")
    
    def _open_workflow(self) -> None:
        """打开工作流"""
        filepath = filedialog.askopenfilename(
            title="打开工作流",
            filetypes=[("JSON 文件", "*.json"), ("所有文件", "*.*")]
        )
        if not filepath:
            return
        
        try:
            self.workflow_data.load(filepath)
            self.toolbox.refresh()
            self.definition_panel._refresh_class_list()
            messagebox.showinfo("成功", f"工作流已打开: {filepath}")
        except Exception as e:
            messagebox.showerror("错误", str(e))
    
    def _save_workflow(self) -> None:
        """保存工作流 - 覆盖原加载的文件"""
        if not self.workflow_data.filepath:
            self._save_as_workflow()
            return
        
        try:
            self.workflow_data.save()
            self.title(f"工作流编辑器 - {self.workflow_data.filepath}")
            messagebox.showinfo("成功", f"工作流已保存到: {self.workflow_data.filepath}")
        except Exception as e:
            messagebox.showerror("错误", str(e))
    
    def _save_as_workflow(self) -> None:
        """另存为工作流"""
        filepath = filedialog.asksaveasfilename(
            title="另存为",
            defaultextension=".json",
            filetypes=[("JSON 文件", "*.json"), ("所有文件", "*.*")]
        )
        if not filepath:
            return
        
        try:
            self.workflow_data.save(filepath)
            messagebox.showinfo("成功", f"工作流已保存: {filepath}")
        except Exception as e:
            messagebox.showerror("错误", str(e))
    
    def _new_class(self) -> None:
        """新建类"""
        self.toolbox._add_class()
    
    def _new_function(self) -> None:
        """新建函数"""
        self.toolbox._add_function()

    def _on_namespace_selected(self, info: Dict[str, Any], item_id: str) -> None:
        """命名空间树选择回调：联动定义编辑区"""
        if not info:
            return

        item_type = info.get("type")

        # 命名空间级别：选择类
        if item_type == "namespace" and info.get("kind") == "class":
            class_name = info.get("namespace")
            if class_name:
                self.definition_panel.class_var.set(class_name)
                self.definition_panel._on_class_selected(None)

        # 定义级别：类的方法或属性
        if item_type == "definition" and info.get("namespace_kind") == "class":
            class_name = info.get("namespace")
            name = info.get("name")
            kind = info.get("kind")
            if not class_name or not name:
                return

            self.definition_panel.class_var.set(class_name)
            self.definition_panel._on_class_selected(None)

            if kind == "function":
                self.definition_panel.select_method(name)
            elif kind == "variable":
                self.definition_panel.select_attribute(name)
        
        # 定义级别：全局函数（module）
        if item_type == "definition" and info.get("namespace_kind") == "module" and info.get("kind") == "function":
            name = info.get("name")
            if not name:
                return
            self.definition_panel.show_global_function(name)
    
    def _on_node_selected(self, event) -> None:
        selection = self.node_list.curselection() if self.node_list is not None else None
        if not selection:
            return
        index = selection[0]
        nodes = self.workflow_data.data["workflow"].get("nodes", [])
        if index >= len(nodes):
            return
        node = nodes[index]
        node_type = node.get("type", "")
        tool = node.get("tool", "")
        if not tool:
            return
        self._navigate_to_tool(node_type, tool)

    def _navigate_to_tool(self, node_type: str, tool: str) -> None:
        namespaces = self.workflow_data.data.get("namespaces", [])

        # 处理函数调用
        if node_type == "function_call":
            # 优先认为是类构造器
            for ns in namespaces:
                if ns.get("kind") == "class" and ns.get("name") == tool:
                    found = self.toolbox.find_item(namespace=tool, namespace_kind="class")
                    if found:
                        item_id, info = found
                        self.toolbox.tree.selection_set(item_id)
                        self.toolbox.tree.see(item_id)
                        self._on_namespace_selected(info, item_id)
                        return

            # 其次尝试全局函数
            found = self.toolbox.find_item(namespace="__global__", namespace_kind="module", name=tool, kind="function")
            if found:
                item_id, info = found
                self.toolbox.tree.selection_set(item_id)
                self.toolbox.tree.see(item_id)
                self._on_namespace_selected(info, item_id)
                return

            # 再次尝试类中的同名方法
            found = self.toolbox.find_item(namespace=None, namespace_kind="class", name=tool, kind="function")
            if found:
                item_id, info = found
                self.toolbox.tree.selection_set(item_id)
                self.toolbox.tree.see(item_id)
                self._on_namespace_selected(info, item_id)
                return

        # 处理方法调用
        if node_type == "method_call":
            if "." in tool:
                method_name = tool.split(".", 1)[1]
            else:
                method_name = tool

            found = self.toolbox.find_item(namespace=None, namespace_kind="class", name=method_name, kind="function")
            if found:
                item_id, info = found
                self.toolbox.tree.selection_set(item_id)
                self.toolbox.tree.see(item_id)
                self._on_namespace_selected(info, item_id)
    
    def _draw_workflow(self) -> None:
        """绘制工作流图"""
        self.canvas.delete("all")
        if self.node_list is not None:
            self.node_list.delete(0, tk.END)
        
        nodes = self.workflow_data.data["workflow"]["nodes"]
        edges = self.workflow_data.data["workflow"]["edges"]
        
        if not nodes:
            # 如果没有节点，显示提示信息
            self.canvas.create_text(
                self.canvas.winfo_width() // 2,
                self.canvas.winfo_height() // 2,
                text="工作流为空\n点击左侧工具箱创建类和函数",
                font=("Arial", 14),
                fill="gray"
            )
            return
        
        # 计算节点位置（简单的网格布局）
        node_positions = {}
        cols = max(1, int(len(nodes) ** 0.5))
        x_spacing = 150
        y_spacing = 100
        
        for i, node in enumerate(nodes):
            node_id = node["id"]
            row = i // cols
            col = i % cols
            x = 50 + col * x_spacing
            y = 50 + row * y_spacing
            node_positions[node_id] = (x, y)
        
        # 绘制边
        for edge in edges:
            from_part = edge.get("from", "")
            to_part = edge.get("to", "")
            
            if "." in from_part and "." in to_part:
                from_node_id = from_part.split(".")[0]
                to_node_id = to_part.split(".")[0]
                
                if from_node_id in node_positions and to_node_id in node_positions:
                    x1, y1 = node_positions[from_node_id]
                    x2, y2 = node_positions[to_node_id]
                    
                    # 绘制箭头
                    self.canvas.create_line(
                        x1 + 40, y1 + 20,
                        x2 - 40, y2 - 20,
                        arrow=tk.LAST,
                        fill="blue",
                        width=2
                    )
        
        # 绘制节点
        for node in nodes:
            node_id = node["id"]
            if node_id not in node_positions:
                continue
            
            x, y = node_positions[node_id]
            node_type = node.get("type", "unknown")
            tool_name = node.get("tool", "")

            # 更新节点列表显示
            if self.node_list is not None:
                summary = f"{node_id} | {node_type} | {tool_name}"
                self.node_list.insert(tk.END, summary)
            
            # 根据节点类型选择颜色
            color_map = {
                "function_call": "#90EE90",
                "method_call": "#87CEEB",
                "class_init": "#FFB6C1",
                "assign": "#FFD700",
                "condition": "#FFA500",
                "loop": "#DDA0DD"
            }
            color = color_map.get(node_type, "#CCCCCC")
            
            # 绘制节点矩形
            self.canvas.create_rectangle(
                x - 40, y - 20,
                x + 40, y + 20,
                fill=color,
                outline="black",
                width=2
            )
            
            # 绘制节点标签
            label = f"{node_id}\n{tool_name[:12]}"
            self.canvas.create_text(
                x, y,
                text=label,
                font=("Arial", 9),
                justify=tk.CENTER
            )
        
        # 绘制图例
        legend_y = 20
        legend_items = [
            ("function_call", "#90EE90", "函数调用"),
            ("method_call", "#87CEEB", "方法调用"),
            ("class_init", "#FFB6C1", "类实例化"),
            ("assign", "#FFD700", "赋值"),
            ("condition", "#FFA500", "条件"),
            ("loop", "#DDA0DD", "循环")
        ]
        
        legend_x = self.canvas.winfo_width() - 150
        for i, (_, color, label) in enumerate(legend_items):
            y = legend_y + i * 20
            self.canvas.create_rectangle(
                legend_x, y - 8,
                legend_x + 15, y + 8,
                fill=color,
                outline="black"
            )
            self.canvas.create_text(
                legend_x + 25, y,
                text=label,
                font=("Arial", 9),
                anchor=tk.W
            )

    def _open_cfg_file(self) -> None:
        filepath = filedialog.askopenfilename(
            title="打开 CFG 文件",
            filetypes=[("CFG JSON", "*.cfg.json"), ("JSON 文件", "*.json"), ("所有文件", "*.*")],
        )
        if not filepath:
            return
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception as e:
            messagebox.showerror("错误", f"加载 CFG 失败: {e}")
            return

        self._current_cfg = cfg
        self._current_cfg_path = filepath
        self._draw_cfg(cfg)

    def _draw_cfg(self, cfg_data: Dict[str, Any]) -> None:
        """绘制单个 cfg.json 所描述的线性 CFG（entry/basic/exit）"""
        self.canvas.delete("all")
        if self.node_list is not None:
            self.node_list.delete(0, tk.END)

        cfg = cfg_data.get("cfg", {})
        nodes = cfg.get("nodes", [])
        edges = cfg.get("edges", [])

        if not nodes:
            self.canvas.create_text(
                self.canvas.winfo_width() // 2,
                self.canvas.winfo_height() // 2,
                text="CFG 为空",
                font=("Arial", 14),
                fill="gray",
            )
            return

        node_map: Dict[str, Dict[str, Any]] = {}
        for n in nodes:
            node_id = n.get("id")
            if node_id:
                node_map[node_id] = n

        entry_id: Optional[str] = None
        for n in nodes:
            if n.get("type") == "entry":
                entry_id = n.get("id")
                break

        ordered_ids: List[str] = []
        if entry_id is not None:
            next_map: Dict[str, str] = {}
            for e in edges:
                if e.get("type") == "seq":
                    from_id = e.get("from")
                    to_id = e.get("to")
                    if from_id and to_id:
                        next_map[from_id] = to_id

            current = entry_id
            visited = set()
            while current and current in node_map and current not in visited:
                ordered_ids.append(current)
                visited.add(current)
                current = next_map.get(current)

            for node_id in node_map.keys():
                if node_id not in visited:
                    ordered_ids.append(node_id)
        else:
            ordered_ids = [n.get("id") for n in nodes if n.get("id")]  # type: ignore

        positions: Dict[str, Tuple[int, int]] = {}
        x_start = 100
        y = self.canvas.winfo_height() // 2 or 200
        if y <= 0:
            y = 200
        x_spacing = 200
        for index, node_id in enumerate(ordered_ids):
            x = x_start + index * x_spacing
            positions[node_id] = (x, y)

        for e in edges:
            from_id = e.get("from")
            to_id = e.get("to")
            if not from_id or not to_id:
                continue
            if from_id not in positions or to_id not in positions:
                continue
            x1, y1 = positions[from_id]
            x2, y2 = positions[to_id]
            self.canvas.create_line(
                x1 + 60,
                y1,
                x2 - 60,
                y2,
                arrow=tk.LAST,
                fill="gray30",
                width=2,
            )

        for node_id in ordered_ids:
            node = node_map.get(node_id)
            if not node:
                continue
            x, y = positions[node_id]
            node_type = node.get("type", "")
            ast_type = node.get("ast_type", "")

            if node_type in ("entry", "exit"):
                self.canvas.create_oval(
                    x - 45,
                    y - 25,
                    x + 45,
                    y + 25,
                    fill="#E0E0E0" if node_type == "entry" else "#F0E0E0",
                    outline="black",
                    width=2,
                )
            else:
                self.canvas.create_rectangle(
                    x - 70,
                    y - 25,
                    x + 70,
                    y + 25,
                    fill="#D0F0FF" if node_type == "basic" else "#CCCCCC",
                    outline="black",
                    width=2,
                )

            if ast_type:
                label = f"{ast_type}\n{node_id}"
            else:
                label = node_id

            self.canvas.create_text(
                x,
                y,
                text=label,
                font=("Arial", 9),
                justify=tk.CENTER,
            )

            if self.node_list is not None:
                summary = node_id
                if node_type:
                    summary += f" | {node_type}"
                if ast_type:
                    summary += f" | {ast_type}"
                self.node_list.insert(tk.END, summary)


def main():
    import sys
    
    # 检查是否提供了文件路径
    filepath = None
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    
    app = WorkflowEditor(filepath)
    app.mainloop()


if __name__ == "__main__":
    main()
