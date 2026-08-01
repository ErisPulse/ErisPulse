# `ErisPulse.CLI.commands.create` 模块

---

## 模块概述


Create 命令实现

脚手架工具，快速创建 Module / Adapter 项目模板

---

## 函数列表


### `_camel_to_snake(name: str)`

将 PascalCase/CamelCase 名称转换为 snake_case

- **name** (`str`): 原始名称
**返回值** (`str`): 转换后的 snake_case 名称

---


### `_to_converter_name(name: str)`

根据适配器名称生成转换器类名

- **name** (`str`): 适配器名称
**返回值** (`str`): 转换器类名（名称后追加 Converter）

---


### `_validate_name(name: str)`

校验项目/模块/适配器名称是否合法

名称必须以字母开头，且只能包含字母、数字和下划线。

- **name** (`str`): 待校验的名称
**返回值** (`bool`): 合法返回 True，否则 False

---


### `_scaffold_text(name: str)`

构建当前语言的脚手架文案映射，并预填充 {name} 占位符

- **name** (`str`): 模块/适配器名称
**返回值** (`dict`): ScaffoldText.all() 的文案字典（含占位符替换）

---


## 类列表


### `class CreateCommand(Command)`

create 命令

脚手架工具，快速创建 Module / Adapter 项目模板


#### 方法列表


##### `_interactive_select_type()`

交互式选择创建类型（Module 或 Adapter）

**返回值** (`str`): 返回 "module" 或 "adapter"

---


##### `_ask_missing(args, field_name: str, prompt_text: str, default: str = '')`

获取参数值，若缺失则交互式提示输入

- **args** (`Any`): 解析后的命令参数对象
- **field_name** (`str`): 参数字段名
- **prompt_text** (`str`): 提示文本
- **default** (`str`): 默认值 (默认: "")
**返回值** (`str`): 获取到的参数值

---


##### `_create_module(args, name: str)`

创建 Module 项目脚手架

- **args** (`Any`): 解析后的命令参数对象
- **name** (`str`): 模块名称
**返回值** (`None`): 无返回值

---


##### `_create_adapter(args, name: str)`

创建 Adapter 项目脚手架

- **args** (`Any`): 解析后的命令参数对象
- **name** (`str`): 适配器名称
**返回值** (`None`): 无返回值

---

