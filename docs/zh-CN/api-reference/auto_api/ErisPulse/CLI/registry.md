# `ErisPulse.CLI.registry` 模块

---

## 模块概述


CLI 命令注册器

负责命令的注册、查找和管理

---

## 类列表


### `class CommandRegistry`

命令注册器

管理所有已注册的 CLI 命令

> **提示**
> 1. 使用单例模式确保全局唯一
> 2. 支持命令的动态注册和查找
> 3. 支持第三方命令的兼容

:ivar _commands: 已注册的命令字典 {name: Command}


#### 方法列表


##### `__new__()`

实现单例模式

---


##### `register(command: Command)`

注册命令

:param command: 要注册的命令实例
**异常**: `ValueError` - 命令名称已存在时抛出

---


##### `register_external(name: str, command: Command)`

注册第三方命令

:param name: 命令名称
:param command: 命令实例

---


##### `get(name: str)`

获取命令

:param name: 命令名称
:return: 命令实例，未找到返回 None

---


##### `get_all()`

获取所有命令（包括外部命令）

:return: 所有命令列表

---


##### `list_all()`

列出所有命令名称

:return: 命令名称列表

---


##### `list_builtin()`

列出内置命令名称

:return: 内置命令名称列表

---


##### `list_external()`

列出外部命令名称

:return: 外部命令名称列表

---


##### `exists(name: str)`

检查命令是否存在

:param name: 命令名称
:return: 命令是否存在

---


##### `clear_external()`

清空外部命令

---

