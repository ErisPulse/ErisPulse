# `ErisPulse.CLI.cli` 模块

> 最后更新：2026-02-01 03:21:24

---

## 模块概述


主 CLI 类

ErisPulse 命令行接口主入口

---

## 类列表


### `class CLI`

ErisPulse 命令行接口主类

提供完整的命令行交互功能，支持动态加载第三方命令


#### 方法列表


##### `__init__()`

初始化 CLI

---


##### `_create_parser()`

创建命令行参数解析器

:return: 配置好的 ArgumentParser 实例

---


##### `_auto_discover_commands()`

自动发现并注册 commands 目录中的所有命令

动态扫描 commands 目录，查找所有继承自 Command 基类的命令类
并自动注册到命令注册表中。

---


##### `_register_builtin_commands()`

注册所有内置命令（通过自动发现）

---


##### `_load_external_commands()`

加载第三方 CLI 命令

---


##### `_print_version()`

打印版本信息

---


##### `run()`

运行 CLI

**异常**: `KeyboardInterrupt` - 用户中断时抛出
**异常**: `Exception` - 命令执行失败时抛出

---


##### `_execute_external_command(args)`

执行第三方命令

:param args: 解析后的参数

---

