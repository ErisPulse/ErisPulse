# `ErisPulse.utils.cli.commands.run` 模块

> 最后更新：2026-01-26 15:55:43

---

## 模块概述


Run 命令实现

运行主程序

---

## 类列表


### `class RunCommand(Command)`

运行命令


#### 方法列表


##### `add_arguments(parser: ArgumentParser)`

添加命令参数

---


##### `execute(args)`

执行命令

---


##### `_setup_watchdog(script_path: str, reload_mode: bool)`

设置文件监控

:param script_path: 要监控的脚本路径
:param reload_mode: 是否启用重载模式

---


##### `_cleanup()`

清理资源

---

