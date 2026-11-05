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


##### `_create_parser() -> ArgumentParser`

创建命令行参数解析器

**返回值**: 配置好的 ArgumentParser 实例

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


##### `_print_grouped_help() -> None`

按类别分组打印主帮助（Rich 表格渲染）

取代 argparse 默认的子命令平铺列表：命令按 category 归类展示
（名称 + 别名 + 描述），全局选项从 ``parser._actions`` 实时遍历
生成避免与实际参数漂移。子命令级 ``--help`` 保持 argparse 原样。

---


##### `_print_quickstart() -> None`

打印 Quick Start 面板

在 ``epsdk`` 不带任何子命令时输出，帮助新用户在 30 秒内看到
三步走路径（安装 / 创建项目 / 运行），降低首次使用门槛。

---


##### `_ensure_utf8_stdio() -> None`（staticmethod）

将标准流重配置为 UTF-8（Windows GBK 代码页兜底）

中文 Windows 控制台默认 GBK 编码，非 Rich 的裸 print 与子进程管道
输出遇到非 GBK 字符会 ``UnicodeEncodeError``——CLI 入口统一兜底，
一次性消灭该类偶发乱码/崩溃（历史点状爆发：翻译脚本、PowerShell BOM）。
仅在流支持 reconfigure 时生效（Python 3.7+ 的 io.TextIOWrapper）。

---


##### `_check_command_typo() -> None`

在 argparse 解析之前检查命令拼写

argparse 的子命令 choices 验证遇到无效命令时会直接打印错误并退出，
无法附加自定义提示。因此在此提前拦截，给出"你是不是想用 xxx"的拼写建议。

---


##### `_maybe_show_language_hint() -> None`

在前几次启动时提醒用户确认语言

由于检测到的语言可能不正确，提示会同时展示所有支持语言，
确保用户总能看懂。显示 {LANG_HINT_MAX_SHOWS} 次后自动静默消失。

---


##### `run() -> None`

运行 CLI

**异常**: `KeyboardInterrupt` - 用户中断时抛出

**异常**: `Exception` - 命令执行失败时抛出

---

