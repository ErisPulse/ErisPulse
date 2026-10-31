# `ErisPulse.runtime.kernel` 模块

---

## 模块概述


统一编排内核（组合根）

框架生命周期的唯一组装点：加载器构造与注入、初始化/反初始化协调器的
创建此前散落在 sdk.py 与 sdk_initializer.py 两处，本类将其收拢为单一
权威；SDK 门面（sdk.py）只做薄转发。

> **提示**
> 1. Kernel 持有 SDK 弱归属关系（组合根天然知晓门面），但不反向暴露
> 2. 加载器与严格模式管理器由 build_loaders() 一次性组装，跨加载器共享
> 3. 协调器经 get_initializer()/get_uninitializer() 获取，每轮新建（加载器复用）

---

## 类列表


### `class Kernel`

统一编排内核

组合根：谁创建加载器、谁注入严格模式管理器、协调器从哪里拿依赖——
这些组装知识只存在于本类，SDK 门面与协调器不再各自为政。


#### 方法列表


##### `__init__(sdk_instance: SDK) -> None`

- **sdk_instance** (`SDK`): 门面实例

---


##### `build_loaders() -> tuple[Any, Any]`

构造适配器/模块加载器并完成全部注入（唯一组装点）

- 共享同一严格模式管理器：跨加载器统一收集违规、检查点统一报告
- 加载器引用注入 SDK：热重载（sdk.reload_module / reload_adapter /
  热重载监控）经由 SDK 访问，仅持有在内核内部则 SDK 侧读不到

**返回值**: (AdapterLoader, ModuleLoader)

---


##### `get_initializer() -> Initializer`

获取初始化协调器（每次调用新建一轮——init 生命周期一轮一个协调器）

加载器由 build_loaders 组装并跨轮复用；协调器本身不缓存：反初始化会
清空加载器引用，跨轮复用会拿到携带失效依赖的旧协调器。

**返回值** (`Initializer`): 实例

---


##### `get_uninitializer() -> Uninitializer`

获取反初始化协调器（每轮新建，与 get_initializer 同语义）

**返回值** (`Uninitializer`): 实例

---

