# `ErisPulse.runtime.sdk_initializer` 模块

---

## 模块概述


ErisPulse SDK 初始化 / 反初始化协调器

Initializer（核心初始化编排）与 Uninitializer（优雅反初始化编排）的实现模块。
由 ``ErisPulse.SDK`` 以类属性别名暴露（``SDK.Initializer`` / ``SDK.Uninitializer``），
既有构造方式（``Initializer(sdk_instance)``）与签名不变。

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


##### `__init__(sdk_instance: SDK)`

初始化协调器

- **sdk_instance** (`SDK`): 实例

---


##### `__getattr__(name: str)`

将未找到的属性委托给 SDK 实例（如 logger、adapter 等）

---


##### `async init()`

初始化所有模块和适配器

执行步骤:
1. 并行发现适配器和模块
2. 注册适配器
3. 启动适配器
4. 注册模块
5. 初始化模块
6. 启动路由服务器

**返回值** (`bool`): 初始化是否成功

**异常**: `ImportError` - 当加载失败时抛出

---


### `class Uninitializer`

反初始化协调器

协调适配器和模块的卸载流程，提供统一的反初始化接口

> **提示**
> 使用方式：
> >>> uninitializer = Uninitializer(sdk_instance)
> >>> success = await uninitializer.uninit()


#### 方法列表


##### `__init__(sdk_instance: SDK)`

反初始化协调器

- **sdk_instance** (`SDK`): 实例

---


##### `__getattr__(name: str)`

将未找到的属性委托给 SDK 实例（如 logger、adapter 等）

---


##### `async uninit()`

执行反初始化

执行步骤:
1. 关闭所有适配器实例
2. 卸载所有模块
3. 停止路由服务器
4. 清理所有事件处理器
5. 清理适配器管理器和模块管理器
6. 清理 LazyModule 引用
7. 清理单例残留状态
8. 清理 SDK 模块属性
9. 重置初始化状态

**返回值** (`bool`): 反初始化是否成功

---

