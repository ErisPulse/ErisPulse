# `ErisPulse.loaders.initializer` 模块

> 最后更新：2026-01-31 19:10:05

---

## 模块概述


ErisPulse 初始化协调器

负责协调适配器和模块的加载流程

> **提示**
> 1. 初始化顺序：适配器 → 模块
> 2. 支持并行加载优化
> 3. 统一的错误处理和事件提交

---

## 类列表


### `class Initializer`

初始化协调器

协调适配器和模块的加载流程，提供统一的初始化接口

> **提示**
> 使用方式：
> >>> initializer = Initializer(sdk_instance)
> >>> success = await initializer.init()


#### 方法列表


##### `__init__(sdk_instance: Any)`

初始化协调器

:param sdk_instance: SDK 实例

---


##### `async async init()`

初始化所有模块和适配器

执行步骤:
1. 从 PyPI 包加载适配器
2. 从 PyPI 包加载模块
3. 注册适配器
4. 注册模块
5. 初始化模块

:return: bool 初始化是否成功

**异常**: `ImportError` - 当加载失败时抛出

---

