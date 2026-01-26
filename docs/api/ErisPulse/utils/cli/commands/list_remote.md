# `ErisPulse.utils.cli.commands.list_remote` 模块

> 最后更新：2026-01-26 15:55:43

---

## 模块概述


List-Remote 命令实现

列出远程可用的组件

---

## 类列表


### `class ListRemoteCommand(Command)`

远程列表命令


#### 方法列表


##### `__init__()`

初始化命令

---


##### `add_arguments(parser: ArgumentParser)`

添加命令参数

---


##### `execute(args)`

执行命令

---


##### `_print_remote_packages(pkg_type: str, force_refresh: bool = False)`

打印远程包信息

:param pkg_type: 包类型 (modules/adapters/cli)
:param force_refresh: 是否强制刷新缓存

---

