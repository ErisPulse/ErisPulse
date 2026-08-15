# `ErisPulse.Core.Bases.module` 模块

---

## 模块概述


ErisPulse 模块基础模块

提供模块基类定义和标准接口

---

## 类列表


### `class ModuleMeta`

模块介绍元信息声明类

模块通过 ``get_meta()`` 返回本类实例（属性键入，IDE 友好），
框架内部经 :meth:`to_dict` 解析——用户声明与内部规则解耦，
后续演进不影响既有声明。

> **提示**
> 1. 字段均可选，``None`` 字段不参与解析
> 2. ``description`` 等文本字段支持 i18n 字典 ``{"i18n": "key", "default": "兜底"}``
> 3. ``commands`` 缺省时自动从注册命令提取
> 4. 兼容直接返回 dict 的旧写法

**示例**:
```python
>>> @staticmethod
... def get_meta() -> ModuleMeta:
...     return ModuleMeta(
...         name="天气",
...         description="查询城市天气",
...         group="工具",
...         tags=["天气", "查询"],
...     )
```


#### 方法列表


##### `to_dict()`

转为字典（内部解析入口，过滤 None 字段）

**返回值**: 非空字段组成的字典

---


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
> 5. 可通过 I18nClass 声明翻译键集合，框架自动注册到 i18n 系统


#### 方法列表


##### `get_meta()`

获取模块介绍元信息（描述这个模块是什么、属于哪一类等）

与 ``get_load_strategy()`` 返回 :class:`ModuleLoadStrategy` 一致，
推荐返回 :class:`ModuleMeta` **配置类实例**（属性键入、IDE 补全），
也兼容直接返回 dict。元信息是模块的**通用介绍数据**，
供各类管理界面 / 生态模块消费（help 模块、Dashboard 模块列表、模块商店等）。

:class:`ModuleMeta` 字段：
- ``name``: 模块显示名（默认注册名）
- ``description``: 模块简介（这个模块是干什么的）
- ``version``: 版本号
- ``author``: 作者
- ``homepage``: 主页 / 仓库地址
- ``group``: 分组（按功能分类，如 "工具" / "娱乐"）
- ``tags``: 标签列表
- ``commands``: 模块提供的命令名列表（默认从注册命令自动提取）

**i18n 支持**：字段值可为纯字符串，或 i18n 字典
``{"i18n": "key.path", "default": "兜底文本"}``（与配置 description 约定一致）。
翻译键通过 ``I18nClass`` 声明注册（键路径 ``<模块名>.<属性名>``），
读取时 ``sdk.module.get_meta()`` 自动解析为当前语言文本。

> **提示**
> 读取已解析的元信息：``sdk.module.get_meta("MyModule")``；
> 若需要"模块简介 + 该模块注册的命令"的聚合数据，可用
> ``sdk.module.get_commands_overview()``。

**返回值** (`元信息（ModuleMeta`): 实例或 dict），模块未声明时返回空 dict

:example:
推荐写法（配置类）：
>>> class MyModule(BaseModule):
...     @staticmethod
...     def get_meta() -> ModuleMeta:
...         return ModuleMeta(
...             name="天气",
...             description="查询城市天气",
...             group="工具",
...             tags=["天气", "查询"],
...         )

兼容写法（dict）：
>>> class MyModule(BaseModule):
...     @staticmethod
...     def get_meta() -> dict:
...         return {
...             "name": "天气",
...             "description": "查询城市天气",
...         }

---


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
会先行调用 _ensure_i18n_registered() 注册声明的翻译键，
确保配置描述引用的 i18n 键在生成模板时已可用。

---


##### `_ensure_i18n_registered()`

注册 I18nClass 中声明的翻译键到 i18n 系统

使用模块注册名作为键名前缀和 domain，便于统一卸载。
方法是幂等的，多次调用不会产生副作用（重复注册会覆盖旧值）。

> **内部方法**
由 ModuleManager.load() 或首次访问 self.cfg 时隐式调用。

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

子类可覆写此方法以响应配置热更新。默认实现为空操作。

- **old_config** (`变更前的配置实例`): - **new_config**: 变更后的配置实例

---

