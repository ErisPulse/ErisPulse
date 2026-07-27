# `ErisPulse.runtime.__init__` 模块

---

## 模块概述


ErisPulse 运行时配置和管理模块

提供框架启动时的配置管理、异常处理等基础功能

> **提示**
> 内部使用模块，框架启动时自动加载

---

## 函数列表


### `__getattr__(name: str)`

首次访问时从 Core.Bases.config_schema 懒加载 Schema 类型与工具函数

---

