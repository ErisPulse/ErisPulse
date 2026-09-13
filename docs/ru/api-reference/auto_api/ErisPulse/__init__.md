# `ErisPulse.__init__` 模块

---

## 模块概述


ErisPulse SDK 主模块

提供SDK核心功能模块加载和初始化功能

> **提示**
> 1. 使用前请确保已正确安装所有依赖
> 2. 调用await sdk.init()进行初始化
> 3. 模块加载采用懒加载机制

---

## 函数列表


### `__getattr__(name: str)`

惰性解析 ``__version__``（首次访问时经包元数据读取）

- **name** (`属性名`): **返回值** (`属性值`): **异常**: `AttributeError` - 未知属性时抛出

> **内部方法**
避免在 ``import ErisPulse`` 时为读取版本号而加载 importlib.metadata
及其依赖链（email/zipfile/asyncio 等，冷启动约数十毫秒）

---

