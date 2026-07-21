# `ErisPulse.CLI.cli` 模块

---

## 模块概述


主 CLI 类

ErisPulse 命令行接口主入口

---

## 类列表


### `class CLI`

ErisPulse 命令行接口主类

提供完整的命令行交互功能


#### 方法列表


##### `__init__()`

初始化 CLI

---


##### `_create_parser()`

创建命令行参数解析器

**返回值** (`配置好的`): ArgumentParser 实例

---


##### `_auto_discover_commands()`

自动发现并注册 commands 目录中的所有命令

动态扫描 commands 目录，查找所有继承自 Command 基类的命令类
并自动注册到命令注册表中。

---


##### `_register_builtin_commands()`

注册所有内置命令（通过自动发现）

---


##### `_print_version()`

打印版本信息

---


##### `_print_quickstart()`

打印 Quick Start 面板

在 ``epsdk`` 不带任何子命令时输出，帮助新用户在 30 秒内看到
三步走路径（安装 / 创建项目 / 运行），降低首次使用门槛。

---


##### `_check_command_typo()`

在 argparse 解析之前检查命令拼写

argparse 的子命令 choices 验证遇到无效命令时会直接打印错误并退出，
无法附加自定义提示。因此在此提前拦截，给出"你是不是想用 xxx"的拼写建议。

---


##### `_maybe_show_language_hint()`

在前几次启动时提醒用户确认语言

由于检测到的语言可能不正确，提示会同时展示所有支持语言，
确保用户总能看懂。显示 {LANG_HINT_MAX_SHOWS} 次后自动静默消失。

---


##### `run()`

运行 CLI

**异常**: `KeyboardInterrupt` - 用户中断时抛出
**异常**: `Exception` - 命令执行失败时抛出

---

