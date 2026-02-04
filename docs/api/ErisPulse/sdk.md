# `ErisPulse.sdk` 模块

> 最后更新：2026-02-04 07:22:14

---

## 模块概述


ErisPulse SDK 主类

提供统一的 SDK 接口，整合所有核心模块和加载器

> **提示**
> example:
> >>> from ErisPulse import sdk
> >>> await sdk.init()
> >>> await sdk.adapter.startup()

---

## 类列表


### `class SDK`

ErisPulse SDK 主类

整合所有核心模块和加载器，提供统一的初始化和管理接口

> **提示**
> SDK 提供以下核心属性：
> - Event: 事件系统
> - lifecycle: 生命周期管理器
> - logger: 日志管理器
> - exceptions: 异常处理模块
> - storage: 存储管理器
> - env: 存储管理器别名
> - config: 配置管理器
> - adapter: 适配器管理器
> - AdapterFather: 适配器基类别名
> - BaseAdapter: 适配器基类
> - SendDSL: DSL 发送接口基类
> - module: 模块管理器
> - router: 路由管理器
> - adapter_server: 路由管理器别名


#### 方法列表


##### `__init__()`

初始化 SDK 实例

挂载所有核心模块到 SDK 实例

---


##### `__repr__()`

返回 SDK 的字符串表示

:return: str SDK 的字符串表示

---

