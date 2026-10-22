# `ErisPulse.Core.Bases.manager` 模块

---

## 模块概述


ErisPulse 管理器基类

提供适配器和模块管理器的统一接口定义

> **提示**
> 适配器管理器和模块管理器都应继承此基类以保持接口一致性

---

## 类列表


### `class ManagerBase(ABC)`

管理器基类

定义适配器和模块管理器的统一接口

> **提示**
> 统一方法：
> - register(): 注册类
> - unregister(): 取消注册
> - get(): 获取实例
> - exists(): 检查是否存在
> - enable()/disable(): 启用/禁用
> - is_enabled(): 检查是否启用
> - is_running(): 检查是否运行
> - list_*(): 列出相关项
> - sdk_ref(): 运行时 SDK 引用解析


#### 方法列表


##### `sdk_ref() -> Any`

解析运行时 SDK 引用

显式注入的 ``_sdk`` 优先（测试 / 高级用法直赋）；缺失时懒导入根包
单例——管理器不再依赖外部接线调用（旧 ``set_sdk_ref`` 从未被生产
链路调用，导致热重载 / 依赖通知在真实部署中静默失效）。

**返回值** (`SDK`): 实例

---


##### `_warn_deprecated_kwarg(owner: str, old: str, new: str) -> None`（staticmethod）

**内部方法**
当检测到使用已弃用的旧关键字参数时，记录一次弃用日志并说明迁移方式

- **owner**: 所属方法名（如 "ModuleManager.get"）
- **old**: 已弃用的旧参数名
- **new**: 推荐使用的新参数名

---


##### `_shutdown_timeout() -> float`（staticmethod）

**内部方法**
读取组件优雅收尾（on_unload / shutdown）的超时（秒）

复用 ``ErisPulse.framework.uninit_timeout`` 配置（反初始化流程的统一
超时预算，整体仍有 uninit 的 wait_for 兜底）；未配置或非法时回退常量默认值。

**返回值**: 超时秒数（>0）

---


##### `register(name: str, class_type: type, info: dict | None = None) -> bool`

注册类

- **name**: 名称
- **class_type**: 类类型
- **info**: 额外信息

**返回值**: 是否注册成功

---


##### `unregister(name: str) -> bool`

取消注册

- **name**: 名称

**返回值**: 是否取消成功

---


##### `get(name: str) -> Any`

获取实例

- **name**: 名称

**返回值**: 实例或 None

---


##### `exists(name: str) -> bool`

检查是否存在（在配置中注册）

- **name**: 名称

**返回值**: 是否存在

---


##### `is_enabled(name: str) -> bool`

检查是否启用

- **name**: 名称

**返回值**: 是否启用

---


##### `enable(name: str) -> bool`

启用

- **name**: 名称

**返回值**: 是否成功

---


##### `disable(name: str) -> bool`

禁用

- **name**: 名称

**返回值**: 是否成功

---


##### `list_registered() -> list[str]`

列出所有已注册的项

**返回值**: 名称列表

---


##### `list_items() -> dict[str, bool]`

列出所有项及其状态

**返回值**: {名称: 是否启用} 字典

---


##### `is_running(name: str) -> bool`

检查项是否正在运行

对于适配器：检查是否已启动
对于模块：检查是否已加载

- **name**: 名称

**返回值**: 是否正在运行

---


##### `list_running() -> list[str]`

列出所有正在运行的项

对于适配器：列出所有已启动的适配器
对于模块：列出所有已加载的模块

**返回值**: 名称列表

---

