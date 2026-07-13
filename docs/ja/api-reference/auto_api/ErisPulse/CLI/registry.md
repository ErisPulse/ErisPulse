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

:ivar _commands: 已注册的命令字典 {name: Command}
:ivar _aliases: 命令别名到命令名的映射 {alias: command_name}


#### 方法列表


##### `__new__()`

实现单例模式

---


##### `register(command: Command)`

注册命令

- **command** (`要注册的命令实例`): **异常**: `ValueError` - 命令名称已存在时抛出

---


##### `resolve(name: str)`

将命令名或别名解析为规范命令名

- **name** (`命令名或别名`): **返回值** (`str`): 规范命令名，未找到返回 None

---


##### `get(name: str)`

获取命令（支持通过别名查找）

- **name** (`命令名称或别名`): **返回值** (`命令实例，未找到返回`): None

---


##### `get_all()`

获取所有命令

**返回值**: 所有命令列表

---


##### `list_all()`

列出所有命令名称

**返回值**: 命令名称列表

---


##### `list_builtin()`

列出内置命令名称

**返回值**: 内置命令名称列表

---


##### `list_aliases()`

列出所有命令别名映射

**返回值** (`dict`): 别名到规范命令名的映射 {alias: command_name}

---


##### `exists(name: str)`

检查命令是否存在（支持别名）

- **name** (`命令名称或别名`): **返回值**: 命令是否存在

---

