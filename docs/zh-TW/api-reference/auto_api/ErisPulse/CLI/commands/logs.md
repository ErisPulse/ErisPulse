# `ErisPulse.CLI.commands.logs` 模块

---

## 模块概述


ep logs 命令：查看框架日志文件尾部

---

## 类列表


### `class LogsCommand(Command)`

logs 命令

查看框架日志文件尾部（默认最近 50 行），支持 --lines 与 --file 覆盖。
日志路径与 [ErisPulse.logger] 配置一致（log_files 显式路径优先，其次
log_dir 目录下的 erispulse.log）。


#### 方法列表


##### `_resolve_log_path(override: str) -> Path | None`

解析日志文件路径（与 logger 的文件输出配置同源）

---

