# `ErisPulse.CLI.commands.types` 模块

---

## 模块概述


Types 命令实现

扫描已安装的模块/适配器，生成带类型提示的存根文件，
让 IDE 能补全平台特有的发送方法和模块方法。

> **提示**
> 1. 通过 entry-points 发现所有已安装的模块/适配器
> 2. 导入类并内省其公开方法（适配器含 Send 子类）
> 3. 在当前目录生成 ``_ep_types.py``，提供类型化的访问器
> 4. 用户 ``from _ep_types import adapter, module`` 即可获得精确补全

---

## 函数列表


### `_is_send_method(name: str, func: Any)`

判断一个类属性是否是"发送方法"

发送方法的特征：公开（非下划线开头）、可调用、不在排除集合中。

- **name** (`属性名`): - **func**: 属性值
**返回值**: 是否为发送方法

---


### `_is_module_method(name: str, func: Any)`

判断一个类属性是否是模块的公开方法

- **name** (`属性名`): - **func**: 属性值
**返回值**: 是否为公开方法

---


### `_safe_type_name(cls: type, fallback: str)`

获取类的类型名用于存根导入，处理无法导入的情况

- **cls** (`类对象`): - **fallback**: 无法确定时的兜底名
**返回值**: 存根中使用的类型名

---


### `_build_send_class_stub(send_cls: type)`

为适配器的 Send 子类构造存根代码

扫描 Send 类的平台特有方法，生成继承 SendDSL 的子类声明。

- **send_cls** (`Send`): 类对象
**返回值**: 存根代码片段

---


### `_pascal_case_ep_name(name: str)`

将 entry-point 名转换为 PascalCase 类型名

处理各种命名风格：
- ``yunhu`` → ``Yunhu``
- ``MyModule`` → ``MyModule``（保持原样）
- ``my_adapter`` → ``MyAdapter``
- ``ErisPulse-Dashboard`` → ``ErisPulseDashboard``

- **name** (`entry-point`): 名称
**返回值** (`PascalCase`): 类型名

---


## 类列表


### `class TypesCommand(Command)`

types 命令

生成 ErisPulse 模块/适配器的类型存根文件，启用 IDE 补全。


#### 方法列表


##### `_collect_adapters()`

扫描所有已安装的适配器，收集类型信息

**返回值** (`适配器信息列表`): [{"name": str, "class": type, "module_path": str, "qualname": str}, ...]

---


##### `_collect_modules()`

扫描所有已安装的模块，收集类型信息

**返回值** (`模块信息列表`): [{"name": str, "class": type, "module_path": str, "qualname": str, "methods": list[str]}, ...]

---


##### `_introspect_remote(python_executable: str, group: str, kind: str)`

在目标 Python 环境中内省 entry-points 及其类信息

通过子进程在目标环境中加载 entry-point 引用的类，提取内省信息
（模块路径、限定名、平台特有的发送方法名、模块的公开方法名）。
这样无论是当前环境还是跨环境场景，都能正确采集类型信息。

- **python_executable** (`str`): 目标 Python 解释器路径
- **group** (`str`): entry-point 组名
- **kind** (`str`): "adapter" 或 "module"，决定内省内容
**返回值** (`list[dict`): ] 内省结果列表

---


##### `_build_introspect_script(group: str, kind: str)`

构造在目标环境中运行的内省脚本

- **group** (`str`): entry-point 组名
- **kind** (`str`): "adapter" 或 "module"
**返回值** (`str`): Python 脚本字符串

---


##### `_generate_stub(adapters_info: list[dict], modules_info: list[dict])`

生成完整的存根文件内容

仅提供类型导入供用户作为变量标注使用，不导出任何实例。
用户自行调用 ``sdk.module.get(...)`` / ``sdk.adapter.get(...)`` 获取实例，
并用本文件导入的类型作为变量类型注解，从而获得 IDE 补全。

所有导入都在 ``TYPE_CHECKING`` 下，运行时零开销、零行为改变。

- **adapters_info** (`适配器信息`): - **modules_info**: 模块信息
**返回值**: 存根文件内容

---

