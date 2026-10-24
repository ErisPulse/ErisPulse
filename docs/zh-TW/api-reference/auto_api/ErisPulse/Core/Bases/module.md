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
@staticmethod
def get_meta() -> ModuleMeta:
    return ModuleMeta(
        name="天气",
        description="查询城市天气",
        group="工具",
        tags=["天气", "查询"],
    )
```


#### 方法列表


##### `to_dict() -> dict[str, Any]`

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
> 6. 对外服务在 get_meta() 的 services 字段声明（模块间调用契约，缺省全开放）


#### 嵌套类


##### `class ModuleState`

**内部方法**
模块状态 KV 视图（BaseModule.state 的返回类型）

键统一加 ``module.state.<模块名>.`` 前缀，避免模块间冲突；
值经 storage 序列化（JSON 兼容类型：str/int/float/bool/list/dict/None）。


###### 方法列表


####### `get(key: str, default: Any = None) -> Any`

读取状态值（同步，任意上下文可调）

- **key**: 状态键（自动加模块前缀）
- **default**: 键不存在时的返回值

**返回值**: 状态值

---


####### `set(key: str, value: Any) -> bool`

写入状态值（同步持久化）

- **key**: 状态键
- **value** (`JSON`): 兼容值

**返回值**: 是否成功

---


####### `async aget(key: str, default: Any = None) -> Any`

读取状态值（异步原生）

- **key**: 状态键
- **default**: 键不存在时的返回值

**返回值**: 状态值

---


####### `async aset(key: str, value: Any) -> bool`

写入状态值（异步原生）

- **key**: 状态键
- **value** (`JSON`): 兼容值

**返回值**: 是否成功

---


#### 方法列表


##### `get_meta() -> 'ModuleMeta | dict[str, Any]'`（staticmethod）

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
- ``services``: 模块对外提供的服务列表（模块间调用契约，缺省时公开方法全开放）
    - 简单形态：``["get_history", "translate"]``（方法名，介绍自动取 docstring 首行）
    - 完整形态：``[{"name": "get_history", "description": "查询会话历史"}]``
      （``description`` 支持纯字符串或 i18n 字典，声明后覆盖 docstring；
      ``parameters`` 为 ``{参数名: 说明}`` 参数提示——调用方经 ``sdk.module.services()``
      发现服务时可读，支持 i18n 字典，未声明的参数自动取 docstring ``:param:`` 行）
- ``min_sdk_version``: 运行时所需最低 SDK 版本（如 ``"2.8.1"``；
    SDK 低于该版本时框架在加载期明确报错并跳过本模块）

**i18n 支持**：字段值可为纯字符串，或 i18n 字典
``{"i18n": "key.path", "default": "兜底文本"}``（与配置 description 约定一致）。
翻译键通过 ``I18nClass`` 声明注册（键路径 ``<模块名>.<属性名>``），
读取时 ``sdk.module.get_meta()`` 自动解析为当前语言文本。

> **提示**
> 读取已解析的元信息：``sdk.module.get_meta("MyModule")``；
> 若需要"模块简介 + 该模块注册的命令"的聚合数据，可用
> ``sdk.module.get_commands_overview()``。

**返回值**: 元信息（ModuleMeta 实例或 dict），模块未声明时返回空 dict

**示例**:

推荐写法（配置类）：
```python
class MyModule(BaseModule):
    @staticmethod
    def get_meta() -> ModuleMeta:
        return ModuleMeta(
            name="天气",
            description="查询城市天气",
            group="工具",
            tags=["天气", "查询"],
        )
```

兼容写法（dict）：
```python
class MyModule(BaseModule):
    @staticmethod
    def get_meta() -> dict:
        return {
            "name": "天气",
            "description": "查询城市天气",
        }
```

---


##### `get_load_strategy() -> ModuleLoadStrategy | dict[str, Any]`（staticmethod）

获取模块加载策略

支持返回 ModuleLoadStrategy 对象或字典
所有属性统一处理，没有任何预定义字段

**返回值**: 加载策略对象或字典

> **提示**
> 常用配置项：
> - lazy_load: bool, 是否懒加载（默认 True）
> - priority: int, 加载优先级（默认 0，数值越大优先级越高）
> 使用方式：
> ```python
> class MyModule(BaseModule):
>     @staticmethod
>     def get_load_strategy() -> ModuleLoadStrategy:
>         return ModuleLoadStrategy(
>             lazy_load=False,
>             priority=100
>         )
> ```
>
> 或使用字典：
> ```python
> class MyModule(BaseModule):
>     @staticmethod
>     def get_load_strategy() -> dict:
>         return {
>             "lazy_load": False,
>             "priority": 100
>         }
> ```
>

---


##### `async on_load(event: dict[str, Any]) -> bool`

当模块被加载时调用

- **event**: 事件内容

**返回值**: 处理结果

> **提示**
> 其中，event事件内容为:
> `{ "module_name": "模块名" }`

---


##### `async on_unload(event: dict[str, Any]) -> bool`

当模块被卸载时调用

- **event**: 事件内容

**返回值**: 处理结果

> **提示**
> 其中，event事件内容为:
> `{ "module_name": "模块名" }`

---


##### `spawn(coro: Any) -> Any`

调度一个归属于本模块的后台任务（推荐的任务创建方式）

任务自动登记到模块名下：模块卸载时，框架在 ``on_unload`` 之后
兜底取消仍未结束的任务，防止任务持有 ``self`` 引用导致模块
实例无法被回收（热重载泄漏的常见根因）。

需要精细控制生命周期的任务，建议在 ``on_unload`` 中自行取消
并等待收尾；本方法作为兜底保障。

- **coro**: 待执行的协程

**返回值**: 创建出的 asyncio.Task（可忽略）

**示例**:

```python
async def _poll(self):
    while True:
        await asyncio.sleep(5)

async def on_load(self, event):
    self.spawn(self._poll())
```

---


##### `state -> 'BaseModule.ModuleState'`（property）

模块级持久化状态（storage 的命名空间视图）

「计数器 / 开关 / 上次运行时间」这类小状态不再需要建表或裸写
storage 键——键自动带 ``module.state.<模块名>.`` 前缀，模块卸载
重载后仍在；同步 ``get``/``set`` 可在任意上下文调用（内部经桥接
循环），异步路径用 ``aget``/``aset``。

**返回值** (`ModuleState`): 视图（每次访问返回新对象，无状态可放心用）

**示例**:

```python
count = self.state.get("runs", 0) + 1
self.state.set("runs", count)
```

---


##### `_get_config_key() -> str`

配置键名

使用模块注册名（由 ModuleManager 注入），而非类名。
这是因为多个模块的类名可能相同（如都叫 Main），
但注册名是唯一的。

**返回值**: 配置键名字符串

---


##### `_ensure_config_exists()`

确保配置模板存在，不存在则生成默认配置

**内部方法**
会先行调用 _ensure_i18n_registered() 注册声明的翻译键，
确保配置描述引用的 i18n 键在生成模板时已可用。

---


##### `_ensure_i18n_registered()`

注册 I18nClass 中声明的翻译键到 i18n 系统

使用模块注册名作为键名前缀和 domain，便于统一卸载。
方法是幂等的，多次调用不会产生副作用（重复注册会覆盖旧值）。

**内部方法**
由 ModuleManager.load() 或首次访问 self.cfg 时隐式调用。

---


##### `cfg -> Any`（property）

类型安全的配置对象（实时读取）

每次访问都从配置存储读取最新值，确保用户修改配置后立即生效。
返回的 dataclass 实例是只读快照，修改它不会回写存储。

**返回值** (`ConfigClass`): 对应的 dataclass 实例

**异常**: `AttributeError` - 未声明 ConfigClass 时抛出

---


##### `cfg(value: Any) -> None`

设置配置实例，同时同步写入配置存储（保证实时性）

---


##### `on_config_update(old_config: Any, new_config: Any) -> None`

配置变更回调（可选实现）

子类可覆写此方法以响应配置热更新。默认实现为空操作。

- **old_config**: 变更前的配置实例
- **new_config**: 变更后的配置实例

---

