# `ErisPulse.Core.Bases.module` 模块

---

## 模块概述


ErisPulse 模块基础模块

提供模块基类定义和标准接口

---

## 类列表


### `class ModuleEvent(TypedDict)`

on_load / on_unload 事件数据

:ivar module_name: str 模块名称


### `class BaseModule(ABC)`

模块基类

提供模块加载和卸载的标准接口，同时支持声明式配置管理。

> **提示**
> 1. 必须实现 on_load / on_unload 方法
> 2. 可通过 ConfigClass 声明配置类，框架自动管理配置
> 3. 通过 self.cfg 访问类型安全的配置对象（实时读取）
> 4. 可覆写 on_config_update() 响应配置热更新


#### 方法列表


##### `get_load_strategy()`

获取模块加载策略

支持返回 ModuleLoadStrategy 对象或字典
所有属性统一处理，没有任何预定义字段

**返回值** (`加载策略对象或字典`): > **提示**
> 常用配置项：
> - lazy_load: bool, 是否懒加载（默认 True）
> - priority: int, 加载优先级（默认 0，数值越大优先级越高）
> 使用方式：
> >>> class MyModule(BaseModule):
> ...     @staticmethod
> ...     def get_load_strategy() -> ModuleLoadStrategy:
> ...         return ModuleLoadStrategy(
> ...             lazy_load=False,
> ...             priority=100
> ...         )
> 或使用字典：
> >>> class MyModule(BaseModule):
> ...     @staticmethod
> ...     def get_load_strategy() -> dict:
> ...         return {
> ...             "lazy_load": False,
> ...             "priority": 100
> ...         }

---


##### `async on_load(event: dict[str, Any])`

当模块被加载时调用

- **event** (`事件内容`): **返回值** (`处理结果`): > **提示**
> 其中，event事件内容为:
> `{ "module_name": "模块名" }`

---


##### `async on_unload(event: dict[str, Any])`

当模块被卸载时调用

- **event** (`事件内容`): **返回值** (`处理结果`): > **提示**
> 其中，event事件内容为:
> `{ "module_name": "模块名" }`

---


##### `_get_config_key()`

配置键名

使用模块注册名（由 ModuleManager 注入），而非类名。
这是因为多个模块的类名可能相同（如都叫 Main），
但注册名是唯一的。

**返回值**: 配置键名字符串

---


##### `_ensure_config_exists()`

确保配置模板存在，不存在则生成默认配置

> **内部方法**

---


##### `cfg()`

类型安全的配置对象（实时读取）

每次访问都从配置存储读取最新值，确保用户修改配置后立即生效。
返回的 dataclass 实例是只读快照，修改它不会回写存储。

**返回值** (`ConfigClass`): 对应的 dataclass 实例
**异常**: `AttributeError` - 未声明 ConfigClass 时抛出

---


##### `cfg(value)`

设置配置实例，同时同步写入配置存储（保证实时性）

---


##### `on_config_update(old_config, new_config)`

配置变更回调（可选实现）

子类可覆写此方法以响应配置热更新。

- **old_config** (`变更前的配置实例`): - **new_config**: 变更后的配置实例

---

