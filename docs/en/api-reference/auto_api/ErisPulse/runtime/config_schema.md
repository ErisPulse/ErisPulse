# `ErisPulse.runtime.config_schema` 模块

---

## 模块概述


ErisPulse 通用配置 Schema 模块（向后兼容 shim）

实际定义已迁移至 :mod:`ErisPulse.Core.Bases.config_schema`。
本模块通过 ``__getattr__`` 懒加载，避免在 runtime 包初始化阶段触发
``Core.Bases.__init__`` 的完整加载链（会引入 lifecycle → runtime 循环）。

> **内部方法**
新增代码请从 ``ErisPulse.Core.Bases`` 导入。

---

## 函数列表


### `__getattr__(name: str)`

懒加载：首次访问时从 Core.Bases.config_schema 导入

---

