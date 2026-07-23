# ASTSuiteApp 业务逻辑与架构分析

> 基于 `.obsidian/app.py` 的单体版 AST Viewer 应用

## 1. 总体概览
ASTSuiteApp 是一个基于 Tkinter 的本地桌面工具，用来**浏览、编辑和分析 Python 源码的抽象语法树（AST）**。整体可以理解为一个「AST 工作台」，包含三条主能力线：

- **文件级 AST 查看与编辑**：选中某个 `.py` 文件后，自动解析为 AST，左侧显示紧凑源码，中间是树状 AST 视图，右侧是节点详情与结构化编辑面板。
- **结构可视化（盒子视图）**：用缩进盒子的方式把 AST 绘制在 Canvas 上，支持按层级深入浏览，并与源码/详情联动高亮。
- **项目级依赖分析**：以某个入口文件为起点，构建模块依赖树，展示导入映射表、项目历史和全局反向依赖信息，并支持导出/整理历史。

运行时的整体分层大致如下：

- **UI 层（Tk + ttk 控件）**：
  - 顶部工具条：选择目录、显示当前工作目录。
  - 左侧文件列表：当前目录下所有 `.py` 文件。
  - 右侧 Notebook：
    - Tab1：结构视图（源码 + AST 树 + 详情/编辑/临时 AST + 盒子视图）。
    - Tab2：项目视图（项目仪表台 + 依赖树/项目历史 + 导入映射表）。

- **业务逻辑层（ASTSuiteApp 方法）**：
  - `_on_*` / `_refresh_*` / `_build_*` 等方法，把用户操作（点击、选择、双击）串成完整业务流。
  - 维护当前目录、当前文件、当前 AST 树、当前选中节点、剪贴板状态、依赖树状态等。

- **服务层 / 工具模块**：
  - `ast_edit_ops`：封装对 AST 树的结构性操作（删除、替换、插入等），隐藏底层字段操作细节。
  - `ast_clipboard_ops`：负责 AST 子树的克隆和剪贴板相关逻辑。
  - `project_deps`：负责项目依赖分析、导入记录抽取、反向依赖历史文件的读写与维护。
  - 标准库 `ast` / `json` / `csv` / `importlib.util` / `traceback` 等提供解析、序列化和诊断能力。

## 2. 业务逻辑主流程
这一节只关注「从选目录到查看/编辑 AST」的主链路，不展开项目视图与历史功能的细节（留到后面章节）。

### 2.1 目录与文件选择

- **选择目录**（工具条按钮 → `_on_choose_dir`）：
  - 通过 `filedialog.askdirectory()` 让用户选择一个目录。
  - 将结果写入 `self.current_dir`，并更新顶部标签 `lbl_dir` 显示当前目录。
  - 调用 `_refresh_file_list()` 刷新左侧文件列表。

- **刷新文件列表**（`_refresh_file_list`）：
  - 在 `current_dir` 下枚举所有以 `.py` 结尾且为文件的条目。
  - 排序后逐行插入 `Listbox(self.file_list)`，形成「可选源码文件列表」。

- **选择文件**（`_on_file_selected`）：
  - 从 `file_list` 的当前选中项读取文件名，拼成绝对路径 `full_path`。
  - 写入 `self.current_file`，并调用 `_load_file(full_path)` 进入解析流程。

### 2.2 解析源码并统一为紧凑 AST

- **加载与解析**（`_load_file`）：
  - 读取磁盘上的源码文本 `source_original`。
  - 使用 `ast.parse(source_original)` 得到 `tree_original`。
  - 尝试 `ast.unparse(tree_original)` 得到「紧凑源码」`compact_source`，再对其重新 `ast.parse` 得到 `tree_compact`。
    - 若成功：
      - `current_source = compact_source`
      - `current_root = tree_compact`
    - 若失败：
      - 回退到原始源码与原始 AST：`current_source = source_original`，`current_root = tree_original`。
  - 完成后：
    - 调用 `_refresh_tab1()` 刷新结构视图（源码 + AST 树 + 详情/编辑）。
    - 调用 `_reset_box_view()` 重置盒子视图（以当前 AST 根节点为起点）。

- **从 AST 反推紧凑源码并重建**（`_rebuild_compact_from_current_root`）：
  - 在进行 AST 修改（删除/插入/替换/粘贴等）后，为保证「源码显示」与「AST 行号/列号」一致，会经过这一步：
    - 用 `ast.unparse(self.current_root)` 生成新的紧凑源码。
    - 用该源码重新 `ast.parse` 为新的 AST。
    - 更新 `current_source` 与 `current_root`，然后再次刷新 Tab1 与盒子视图。
  - 这样主流程始终保持：**所有编辑都作用在 AST 上，但界面展示的源码始终是 AST 反向生成的一致版本**。

### 2.3 AST 浏览与节点查看

- **刷新结构视图**（`_refresh_tab1`）：
  - 左侧源码区：
    - 清空 `code_text`，写入 `current_source`，清除旧的高亮标签。
  - 中部 AST 树：
    - 清空 `Treeview(self.tree)`，重新构建整棵树：
      - 使用 `ast.iter_child_nodes` 递归遍历 `current_root`。
      - 为每个节点构造简短 label（节点类型 + 行号 + 函数/类名等），插入 TreeView。
      - 同时写入 `node_by_item[item_id] = node`，建立「Tree 行 → AST 节点」映射。
  - 右侧详情区：
    - 调用 `_show_node_detail(None)` 清空详情。
  - 维护编辑所需的父子关系：
    - 调用 `_rebuild_parent_map()`，为整棵 AST 建立 `parent_map[node] = (parent, field_name, index)`。

- **选择 AST 节点**（`_on_tree_select`）：
  - 从 TreeView 选中行取出对应 AST 节点 `node = node_by_item[item_id]`。
  - 调用 `_show_node_detail(node)`：
    - 在右侧详情 Text 中打印：节点类型、位置信息、字段概览以及 `ast.dump(include_attributes=True)`。
    - 调用 `_select_edit_tab_for_node(node)`，根据节点类型自动切到合适的编辑子 Tab（结构/控制流/赋值/表达式等）。
  - 调用 `_highlight_in_code(node)`：
    - 根据 `lineno/col_offset/end_lineno/end_col_offset` 计算 Text 索引范围。
    - 在 `code_text` 中打上高亮标签，并滚动到对应源码位置。

### 2.4 编辑入口与剪贴板模式（概览）

详细行为会在后续章节拆开写，这里只从业务流角度做一个总览：

- 用户在 AST 树或盒子视图中选中某个节点（设置 `current_node`）。
- 右侧「编辑」Tab 的按钮提供几类入口：
  - 删除当前节点：`delete_current_node()`。
  - 使用临时节点替换当前节点：`replace_current_node()`。
  - 在当前节点之后插入临时节点：`insert_node_by_current_tab()` 或 `paste_from_clipboard()`。
- 所有结构性操作底层都委托给 `ast_edit_ops` 与 `ast_clipboard_ops`，完成后都会调用 `_rebuild_compact_from_current_root()`。
- 剪贴板模式（复制/剪切/组装/新建临时源码）则通过一组状态字段 + “临时AST”Tab 来管理，既可以从现有 AST 抽取子树，也可以从新写的一段源码解析出临时子树，用于后续替换/插入。

## 3. UI 层结构
这一节只从「界面布局和控件结构」角度描述，不展开内部业务逻辑（例如依赖分析算法、AST 操作细节）。

### 3.1 顶级窗口与主分栏

- **顶级类**：`class ASTSuiteApp(tk.Tk)` 直接继承自 `tk.Tk`。
- **窗口属性**：
  - 标题：`AST Viewer Suite`。
  - 默认尺寸：`1300x780`。

主布局结构：

1. 顶部：工具条 `toolbar`（`ttk.Frame`）
   - 按钮：`选择目录` → 触发 `_on_choose_dir`。
   - 标签：`当前目录：<未选择>` → 实时显示当前工作目录。

2. 中间：左右分栏 `main = ttk.Panedwindow(..., orient=HORIZONTAL)`
   - 左侧：文件列表区域 `left`。
   - 右侧：主内容区域 `right`，内含一个 Notebook。

### 3.2 左侧文件列表 Pane

- 容器：`left = ttk.Frame(main, width=260)` 被添加到 `Panedwindow` 中，权重较小（不随窗口扩展过多拉伸）。
- 组件：
  - 顶部标签：`Python 文件列表`。
  - `self.file_list = tk.Listbox(left, ...)` 用于显示当前目录下所有 `.py` 文件。
  - 垂直滚动条 `sb_files = ttk.Scrollbar(left, orient=VERTICAL, command=self.file_list.yview)`。
- 交互：
  - `file_list` 绑定事件 `<<ListboxSelect>>` 到 `_on_file_selected`，完成「点选文件 → 加载 AST → 刷新右侧各视图」。

### 3.3 右侧 Notebook：结构视图 / 项目视图

- 容器：`right = ttk.Frame(main)`，权重为 1（随窗口扩展）。
- 主 Notebook：`self.notebook = ttk.Notebook(right)`，包含两个 Tab：
  - **Tab1：结构视图**（源码 + AST + 详情/编辑/临时 AST + 盒子视图）。
  - **Tab2：项目视图**（项目仪表台 + 依赖树/项目历史 + 导入映射表）。

下面分别拆两部分。

### 3.4 结构视图 Tab 的三列布局

Tab1 内部采用**三列表格布局**：左列源码，中列 AST 中间视图，右列节点详情/编辑。

1. **左列：源码 Text 区**
   - 组件：
     - `self.code_text = tk.Text(..., wrap='none', font=('Consolas', 11))`。
     - 垂直滚动条 `sb_code_y`、水平滚动条 `sb_code_x`。
   - 特性：
     - 使用 tag `highlight` 支持高亮当前选中 AST 节点对应的源码区间。
     - 仅作为显示/浏览用，实际“权威源码”来自 AST 的 `unparse`。

2. **中列：内部 Notebook（Tree / Boxes）**

   - 使用 `mid_nb = ttk.Notebook(tab1)` 构建子层级 Notebook：
     - 子 Tab `Tree`：
       - `self.tree = ttk.Treeview(tree_tab)` 展示 AST 的树形结构。
       - 滚动条 `sb_tree_y` 绑定 `yview`。
       - 事件 `<<TreeviewSelect>>` 交给 `_on_tree_select`，从而联动右侧详情和源码高亮。
     - 子 Tab `Boxes`：
       - 上方工具条 `toolbar2`：
         - 「返回上一层」按钮 `_box_on_back`。
         - 「回到根」按钮 `_box_on_home`。
         - 展开深度下拉框 `self.box_depth_menu`（1/2/3/全部），变化时触发 `_redraw_box_view`。
       - 下方 `canvas_frame` 内的 `self.box_canvas = tk.Canvas(...)`：
         - 配合垂直滚动条 `box_vbar` 显示完整 AST 盒子布局。
         - 绑定鼠标事件：
           - 左键点击 `_box_on_click`：选中盒子并进入该节点子树视图。
           - 中键/右键拖拽 `_box_on_scan_start` / `_box_on_scan_drag`：平移视图。

3. **右列：详情 / 编辑 / 临时 AST Notebook**

   - 外层 Notebook：`self.right_nb = ttk.Notebook(tab1)`，包含三个子 Tab：

   **(1) 详情 Tab**
   - `detail_tab` 中的 `self.detail_text = tk.Text(..., state='disabled')`：
     - 专门用于只读展示当前节点的属性、字段列表和 `ast.dump` 结果。
     - 配有垂直滚动条 `sb_detail_y`。

   **(2) 编辑 Tab**
   - 容器：`self.right_edit_tab`。
   - 顶部四行工具条：
     - 行 1：
       - 「删除选中节点」按钮 → `delete_current_node`。
     - 行 2：
       - 「复制到临时」→ `copy_to_clipboard`。
       - 「剪切到临时」→ `cut_to_clipboard`。
       - 「组装为临时节点」→ `assemble_to_clipboard`。
     - 行 3：
       - 状态标签 `self.clipboard_status_var`（例如“模式：普通/复制中/剪切中/组装临时节点/新建临时源码”）。
     - 行 4：
       - 「替换成临时」→ `replace_current_node`。
       - 「下方插入临时」→ `insert_node_by_current_tab`。
       - 「退出临时」→ `exit_clipboard_mode`。

   - 内部编辑 Notebook：`self.edit_nb = ttk.Notebook(self.right_edit_tab)`：
     - 通过 `edit_structure.build(...)` / `edit_control.build(...)` 等函数，在 9 个子 Tab 中放置具体的编辑控件：
       - 结构/作用域、控制流、数据流/赋值、调用/接口、表达式/常量、异常与上下文管理、异步与模式匹配、导入与模块组织、元数据与位置信息。
     - `_classify_node_category` 与 `_select_edit_tab_for_node` 会根据当前选中 AST 节点类型，在这里自动切到合适的编辑 Tab/孙 Tab。

   **(3) 临时 AST Tab**
   - 顶部工具条：
     - 「新建临时源码」→ `new_temp_from_empty`。
     - 「解析为临时子树」→ `parse_clipboard_temp`。
   - 中间使用 `ttk.Panedwindow` 左右分栏：
     - 左侧：
       - 标签「临时节点源码」。
       - `self.clipboard_code_text = tk.Text(...)`，允许用户直接编辑一段临时代码。
       - 搭配水平/垂直滚动条 `sb_clip_code_x / sb_clip_code_y`。
     - 右侧：
       - 标签「临时节点 AST 子树」.
       - `self.clipboard_tree = ttk.Treeview(...)` 展示临时子树的结构；滚动条 `sb_clip_tree_y`.
   - `_refresh_clipboard_view` 会在剪贴板状态变化时刷新该 Tab 的源码与树形视图.

## 4. 服务层与依赖模块

这一节聚焦于「ASTSuiteApp 本身不直接实现，而是委托外部模块完成」的那部分逻辑，也就是你可以视为**服务层 / 工具层**的模块.

### 4.1 AST 编辑服务：`ast_edit_ops`

在 `app.py` 中，所有对 AST 结构进行「删除/替换/插入」的操作都不会直接在 `ast.AST` 对象上手写字段操作，而是统一委托给 `ast_edit_ops`：

- 典型调用点：
  - `delete_current_node` → `ast_edit_ops.delete_node(...)`
  - `replace_current_node` → `ast_edit_ops.replace_node(...)`
  - `insert_node_by_current_tab`、`paste_from_clipboard` → `ast_edit_ops.insert_after(...)`
  - `exit_clipboard_mode`（在剪切模式下真正删除源节点）→ `ast_edit_ops.delete_node(...)`

- 输入参数模式大致一致：
  - 当前整棵树根：`self.current_root`
  - 目标节点：`self.current_node` 或 `clipboard_source_node`
  - 父子关系表：`self.parent_map`（在 `_rebuild_parent_map` 中由 ASTSuiteApp 维护）

- 返回值：
  - 返回新的根节点 `new_root`（可能等于旧根，也可能是经过修改的副本），再被赋值给 `self.current_root`.

通过这种方式：

- **UI/业务层只负责「选中哪个节点、要做什么操作」**；
- **真正「如何在 AST 树中安全修改结构」被封装在 `ast_edit_ops` 中**；
- 出错时由 `NodeOperationError` 这类自定义异常（通过 `messagebox.showerror` 告知用户）来反馈问题.

这让 ASTSuiteApp 在结构上更像一个「前端 + 调度器」，而不是把所有 AST 操作细节都堆在一个类里.

### 4.2 剪贴板与子树克隆：`ast_clipboard_ops`

剪贴板相关逻辑在 UI 层有大量状态与交互，但真正对 AST 子树做「安全复制」的责任也被下沉到了独立模块 `ast_clipboard_ops`：

- 关键调用：
  - `_init_clipboard_temp_from_node`：
    - `self.clipboard_temp_node = ast_clipboard_ops.clone_subtree(node)`
  - `replace_current_node` / `insert_node_by_current_tab` / `paste_from_clipboard`：
    - 都先通过 `clone_subtree(source_for_clone)` 得到一个可插入的新子树，再交给 `ast_edit_ops` 做结构性替换/插入.

- 失败兜底策略：
  - 如果 `clone_subtree` 抛异常，UI 层直接退回到「复用原节点引用」的方式，虽然语义退化为“移动”，但保证操作不会完全失败.

- 配合剪贴板状态字段：
  - `clipboard_active` / `clipboard_mode`：当前是否处于剪贴板模式以及模式类型（copy/cut/assemble）。
  - `clipboard_source_node`：原始 AST 节点引用.
  - `clipboard_temp_node`：克隆或解析得到的临时子树.

可以把 `ast_clipboard_ops` 理解为：

- UI 层告诉它「我要把这个节点当作可移动/复制的单元」，
- 它负责返回一个在语义上等价、在结构上独立的新子树，供后续插入/替换使用.

### 4.3 项目依赖分析与历史：`project_deps`

项目视图和历史管理几乎完全依赖 `project_deps` 模块，ASTSuiteApp 只负责：

- 触发分析（如点击按钮）。
- 把分析结果映射到 UI 控件（Treeview、表格、弹窗）。

#### 4.3.1 依赖树构建

- 入口：
  - `_on_build_project_view`：以当前文件为入口；
  - `_on_build_project_view_from_import`：以某条导入记录对应的模块为入口.

- 核心调用：
  - `root = project_deps.build_dependency_tree(entry_path, project_root)`
  - 返回值 `root` 是一棵 `ModuleNode` 树，每个节点描述一个模块：
    - `name`：模块名.
    - `file_path`：物理文件路径（`Path`）。
    - `imports`：该模块内部的导入记录列表（`ImportRecord`）。
    - `children`：依赖树中的下游模块节点.
    - `edge_kinds`：该节点被导入时用到的导入方式集合（绝对/相对）。

- ASTSuiteApp 使用方式：
  - 把这棵树渲染到 `self.dep_tree`（模块依赖树 TreeView）。
  - 同时维护 `dep_tree_item_to_node` 映射，方便后续通过 UI 选中项反查 `ModuleNode`.

#### 4.3.2 导入映射与未解析导入

- `node.imports` 中的元素来自 `project_deps.ImportRecord`：
  - 包含模块名、导入方式（level）、行号、映射到的物理文件路径等.
- ASTSuiteApp 在 `_on_dep_tree_select` 中遍历 `node.imports`，构建右侧导入映射表：
  - 对于能解析到物理路径的模块，展示相对路径.
  - 对于无法解析到物理文件的模块，通过 `importlib.util.find_spec` 判断是否为「内建模块」或「冻结模块」，以纯文本提示.

- 未解析导入列表：
  - 局部变量 `project_deps.MISSING_IMPORTS` 由 `project_deps` 在构建依赖树时填充.
  - `_on_show_missing_imports` 读取该列表，在独立窗口中展示，并提供导出 JSON/CSV 的能力.

#### 4.3.3 反向依赖历史与全局合并

`project_deps` 还负责维护「谁导入了谁」的历史信息：

- 当前会话内的反向依赖：
  - `project_deps.REVERSE_DEPENDENCIES` 字典，键为模块路径，值为一组 `ReverseRefInfo`.
  - `_on_show_module_referrers` 会先读取当前会话中的这部分信息.

- 项目级历史：
  - 以项目根目录为单位，存放在 `ast_deps_history/deps_*.json` 中.
  - ASTSuiteApp 通过：
    - `project_deps.load_project_history_for_root(project_root)` 加载并显示到「项目历史(JSON)」Tab；
    - `project_deps.rebuild_project_history(project_root)` 在 `_on_rebuild_project_history` 中重建全部历史文件；
    - `project_deps.compact_history_file(path)` 在 `_on_compact_deps_history` 中压缩去重.

- 全局历史：
  - 存放在用户 home 目录下的 `~/.ast_viewer_deps.json`.
  - `_on_show_module_referrers` 在汇总反向依赖时会调用：
    - `project_deps.load_history_refs_for_target_in_project(...)`
    - `project_deps.load_history_refs_for_target(...)` 读取项目级和全局级的历史记录.
  - `_on_merge_all_to_global` 则通过 `project_deps.merge_registered_project_histories_to_global()` 将多个项目的历史合并去重后写入全局文件.

从 ASTSuiteApp 的视角看：

- **project_deps 是整个「项目级能力」的核心服务层**：
  - 自己负责扫描项目、解析导入、构建依赖树与反向依赖索引.
  - 应用只负责发起调用、展示结果和触发「重建/压缩/合并」这些高层操作按钮.

### 4.4 小结：UI 作为壳，服务模块作为内核

  - 管理状态（当前目录/文件/AST/剪贴板/依赖树）。
  - 负责事件流转和界面刷新.
  - 不直接实现复杂算法和结构操作，而是把这些工作交给专门的服务模块.

## 5. 小结与与后续重构方向

### 5.1 现有单体架构的优点

- **上手成本低**：
  - 所有 UI、状态与业务逻辑集中在一个 `ASTSuiteApp` 类中，新读者只要顺着 `__init__` → `_create_widgets` → 各种 `_on_*` 方法看下去，就能掌握整体行为。

- **交互链路清晰**：
  - 「选目录 → 选文件 → 解析 AST → 浏览/编辑 → 盒子视图 → 项目视图/历史」这条主链路在同一个文件里闭合，便于整体观察和调试。

- **服务调用边界已经初步形成**：
  - AST 编辑相关都委托给 `ast_edit_ops` / `ast_clipboard_ops`。
  - 项目级分析与历史管理都委托给 `project_deps`。
  - UI 层和算法/数据处理层已经有了相对清晰的责任划分，这一点为重构打了基础。

### 5.2 局限与风险

- **类体过于庞大**：
  - `ASTSuiteApp` 同时承担：窗口搭建、状态管理、事件分发、AST 视图刷新、项目视图刷新等职责，方法数量和长度都偏大。
  - 对于后期维护者来说，任何改动都需要在一个大文件里定位多处逻辑，容易产生「牵一发动全身」的副作用。

- **UI 与状态强耦合**：
  - 大量方法直接操作 Tk 控件（`Treeview`、`Text`、`Canvas` 等）和内部状态字段，如果以后要换 UI 框架或拆出服务层 API，会比较辛苦。

- **项目级能力与文件级能力混在同一个类中**：
  - 单文件 AST 浏览/编辑逻辑和项目依赖/历史逻辑共存在同一个 Tk 应用类里，概念上已经是两个子系统，但在代码上没有明显隔离。

- **扩展点难以复用**：
  - 比如「只想要一个纯项目依赖分析 CLI 工具」或「只想在别的 UI 里复用 AST 编辑能力」，目前都需要从这个大类里“扒逻辑”。

### 5.3 与模块化版本的对照与演进方向

你现在在 `ast_viewer/` 下已经有了更模块化的版本（如 `app_main.py` + `services/` + `views/`），可以把这个 `.obsidian/app.py` 看成「单体版原型」的完整解剖图，为后续演进提供参照。基于当前分析，可以总结出几个明确的重构方向：

- **方向 1：UI 拆分为独立视图类**
  - 把「结构视图」「盒子视图」「项目视图」抽成独立的 `View` 类或模块：
    - 结构视图负责：源码 Text + AST Tree + 详情/编辑逻辑。
    - 盒子视图负责：Canvas 盒子渲染与点击交互。
    - 项目视图负责：项目仪表台 + 依赖树 + 历史/导入表联动。
  - 主应用壳只负责：窗口框架、菜单/工具条、视图之间的协调与状态分发。

- **方向 2：进一步稳定服务层 API**
  - 在 `ast_edit_ops` / `ast_clipboard_ops` / `project_deps` 之上，抽一层更稳定的「服务接口」：
    - 如 `AstService` 负责「加载文件 → 解析 AST → 提供节点 CRUD 操作」。
    - `ProjectService` 负责「给定入口文件 → 返回依赖树/反向依赖/历史聚合结果」。
  - 这样 UI 与服务可以做到**完全解耦**，未来可复用到 Web UI 或其他桌面框架中。

- **方向 3：显式状态管理**
  - 将当前零散的状态字段（`current_dir` / `current_file` / `current_root` / 剪贴板状态 / 依赖树状态等）收拢到专门的 `AppState` 或若干小的状态对象中：
    - 例如 `FileState`、`AstState`、`ClipboardState`、`ProjectState`。
  - 主应用和各视图通过这些状态对象进行读写，减少「到处直接改属性」带来的隐形耦合。

- **方向 4：事件与回调机制标准化**
  - 当前许多交互是直接在方法里调用其他方法（如 `_on_dep_tree_select` 内直接重建右侧表格）。
  - 可以演进为：
    - 视图之间通过「回调/信号」通信（已经在新架构中部分实现）。
    - 主应用只订阅「文件已切换」「AST 已更新」「依赖树已刷新」这类事件，再协调更新其他视图。

综合来看：

- `.obsidian/app.py` 这个版本已经很好地展示了**产品能力全集**，适合作为「业务语义对照表」。
- `ast_viewer` 目录下的模块化版本则承接了「架构演进」的工作，把这些能力拆成服务和视图模块。

这份文档的角色就是：

- 帮你在脑中保留一份「单体版 ASTSuiteApp 的完整业务地图」，
- 方便在之后迭代中随时对照：某个功能在老版本里是如何串起来的，现在在模块化版本里又被拆去了哪里.
