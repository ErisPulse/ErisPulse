# `ErisPulse.CLI.utils.display` 模块

---

## 模块概述


ErisPulse CLI 显示工具

提供分页、优雅输出等 UI 组件

---

## 函数列表


### `_terminal_height()`

获取终端高度（行数）

**返回值** (`int`): 终端高度，获取失败时返回 24

---


### `_page_size()`

根据终端高度计算每页显示的行数

**返回值** (`int`): 每页显示行数，最小为 5

---


### `_input(prompt_label: str = '>')`

读取用户输入，遇到EOF或中断时返回 "q"

- **prompt_label** (`str`): 提示标签 (默认: ">")
**返回值** (`str`): 用户输入内容（已去除首尾空白）

---


### `prompt_validated(message: str, default: str = '', validate: Callable[[str], bool | str | None] | None = None, error_msg: str | None = None)`

交互式输入，校验失败时保留上次输入并重新提示，直到通过校验。

- **message** (`str`): 提示文本
- **default** (`str`): 初始默认值（也作为校验失败后保留的可编辑值） (默认: "")
- **validate** (`Callable`): 校验函数；返回 True/None 表示通过，
                 返回 False 使用 error_msg，返回字符串则作为本次错误提示 (默认: None)
- **error_msg** (`str`): validate 返回 False 时的默认错误提示
**返回值** (`str`): 通过校验的输入值

---


### `section_header(title: str)`

打印格式化的分节标题

- **title** (`str`): 标题文本

---


### `section_footer()`

打印格式化的分节结束分隔线

---


### `tree_item(text: str, level: int = 0, is_last: bool = False)`

打印树形结构的层级项

- **text** (`str`): 显示文本
- **level** (`int`): 层级深度 (默认: 0)
- **is_last** (`bool`): 是否为同级最后一项 (默认: False)

---


### `info_line(text: str, level: int = 1)`

打印带缩进和项目符号的信息行

- **text** (`str`): 显示文本
- **level** (`int`): 缩进层级 (默认: 1)

---


### `paginated_table(table: Table, items: list[Any], row_builder, page_size: int | None = None)`

将列表项分页渲染到表格中，支持翻页交互

- **table** (`Table`): 表格模板（用于列样式）
- **items** (`List[Any`): ] 待渲染的数据项列表
- **row_builder** (`Callable`): 行构建函数，接收 (table, index, item)
- **page_size** (`Optional[int`): ] 每页行数，为空则自动计算 (默认: None)
**返回值** (`int`): 已展示的项数

---


### `interactive_select_table(title_text: str, items: list[Any], columns: list, row_builder, page_size: int | None = None)`

渲染可交互多选的分页表格，支持按序号选择、翻页与确认

- **title_text** (`str`): 表格标题
- **items** (`List[Any`): ] 待选择的数据项列表
- **columns** (`list`): 表格列配置列表
- **row_builder** (`Callable`): 行构建函数，接收 (table, index, item, selected)
- **page_size** (`Optional[int`): ] 每页行数，为空则自动计算 (默认: None)
**返回值** (`List[Any`): ] 用户选中的数据项列表

---

