# `ErisPulse.CLI.constants` 模块

---

## 模块概述


CLI 本地常量

ErisPulse 的 CLI 与主库刻意保持隔离：CLI 运行时不应触发主库初始化
（``ErisPulse/__init__.py`` 会全量加载 Core 并实例化 ConfigManager /
StorageManager 等单例）。因此 CLI 需要的常量在此独立维护，**不**从
``ErisPulse.Core.constants`` 导入。

与主库共享的"跨进程 / 跨子系统契约"（如硬重启退出码、入口点组名）在此
镜像一份，由 ``tests/unit/test_unit_cli.py::TestCrossProcessContracts``
钉死——任一侧漂移即测试失败。

> **内部方法**

---
