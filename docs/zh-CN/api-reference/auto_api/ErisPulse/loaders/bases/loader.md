# `ErisPulse.loaders.bases.loader` 模块

---

## 模块概述


ErisPulse 基础加载器

定义加载器的抽象基类，提供通用的加载器接口和结构

> **提示**
> 1. 所有具体加载器应继承自 BaseLoader
> 2. 子类需实现 _process_entry_point 方法
> 3. 支持启用/禁用配置管理

---

## 函数列表


### `resolve_min_sdk_version(component_obj: Any, name: str = '') -> str | None`

解析组件声明的运行时最低 SDK 版本（统一读取口径）

解析优先级：``get_meta()`` 声明（:class:`~ErisPulse.Core.Bases.ModuleMeta`
实例或 dict，模块体系的规范声明位置）> 类属性 ``min_sdk_version``
（适配器等无 meta 声明类组件的声明位置）> ``None``（未声明）。

- **component_obj**: 组件类
- **name**: 组件名称（仅用于 get_meta 异常时的诊断日志）

**返回值** (`str`): 声明的最低版本；未声明或声明为空返回 None

---


### `check_component_sdk_version(name: str, component_type: str, component_obj: Any, *, strict_recorder: Any = None, invalid_key: 'str | None' = None, unsupported_key: 'str | None' = None) -> bool`

运行时最低 SDK 版本检查（声明读取见 :func:`resolve_min_sdk_version`）

组件未声明或声明无法解析时放行（后者输出警告）；
版本不满足时输出明确错误、经 ``strict_recorder``（可选）按严格模式
登记拒绝并返回 False，由调用方跳过该组件——SDK 过低的组件加载后
几乎必然运行异常，提前拦截可给出可操作的诊断（升级 SDK 或换用
兼容版本组件）。

版本闸门的唯一实现：entry-point 加载（BaseLoader._check_sdk_version）
与本地插件加载（plugin_folder 两处）共用，保证 strict_mode 错误面
不因组件安装来源（PyPI / plugins 目录）而不同。

- **name**: 组件名称
- **component_type**: 组件类型（``module`` / ``adapter``，用于日志与严格模式登记）
- **component_obj**: 组件类（经统一口径解析其 min_sdk_version 声明）
- **strict_recorder**: 严格模式登记器（需提供 record_failure；None = 不登记）
- **invalid_key**: 声明不可解析的告警文案键（默认 ``loader.{component_type}.sdk_version_invalid``）
- **unsupported_key**: 版本不满足的错误文案键（默认 ``loader.{component_type}.sdk_version_unsupported``）

**返回值** (`bool`): 是否允许继续加载

---


## 类列表


### `class BaseLoader(ABC)`

基础加载器抽象类

提供通用的加载器接口和配置管理功能

> **提示**
> 子类需要实现：
> - _get_entry_point_group: 返回 entry-point 组名
> - _process_entry_point: 处理单个 entry-point

**内部方法**
此类仅供内部使用，不应直接实例化


#### 方法列表


##### `__init__(config_prefix: str)`

初始化基础加载器

- **config_prefix**: 配置前缀（如 "ErisPulse.adapters" 或 "ErisPulse.modules"）

---


##### `set_strict_manager(manager: Any) -> None`

注入严格模式管理器

- **manager** (`StrictModeManager`): 实例

**内部方法**
由初始化协调器调用，确保多个加载器共享同一管理器实例以统一收集违规

---


##### `_strict() -> Any`

获取严格模式管理器

**返回值** (`StrictModeManager`): 实例

**内部方法**
未注入时从配置创建，仅供独立调用/测试使用；正常启动流程总会被注入

---


##### `_check_sdk_version(name: str, component_type: str, component_obj: Any) -> bool`

运行时最低 SDK 版本检查（委托共享实现 :func:`check_component_sdk_version`）

- **name**: 组件名称
- **component_type**: 组件类型（``module`` / ``adapter``，用于日志与严格模式登记）
- **component_obj**: 组件类（经统一口径解析其 min_sdk_version 声明）

**返回值** (`bool`): 是否允许继续加载

**内部方法**
供 ModuleLoader / AdapterLoader 在构建组件信息前调用

---


##### `_ep_gate(meta_name: str, manager_instance: Any) -> tuple[bool, bool]`

entry-point 统一前闸门：未注册则补配置注册（默认启用），已禁用则跳过

- **meta_name**: 组件名称
- **manager_instance**: 管理器实例

**返回值**: (是否继续加载, 是否为新注册)

**内部方法**
供 ModuleLoader / AdapterLoader 的 _process_entry_point 序言调用

---


##### `_guarded_ep_load(kind: str, meta_name: str, load_fn: Callable[[], Any]) -> Any | None`

entry-point 加载统一错误信封

SystemExit 与异常在此统一转为"严格模式登记 + 错误日志 + 诊断留痕"并
返回 None——单组件加载失败不阻断同组其余组件，也绝不静默。

- **kind**: 组件类别（``module`` / ``adapter``，用于严格模式登记与文案键）
- **meta_name**: 组件名称
- **load_fn**: 实际加载与信息构建逻辑（"跳过该组件"分支返回 False 即可）

**返回值** (`load_fn`): 的返回值；加载失败时 None

**内部方法**
供 ModuleLoader / AdapterLoader 的 _process_entry_point 包裹中段逻辑

---


##### `_get_entry_point_group() -> str`

获取 entry-point 组名

**返回值**: entry-point 组名

**内部方法**
子类必须实现此方法

---


##### `async _process_entry_point(entry_point: Any, objs: dict[str, Any], enabled_list: list[str], disabled_list: list[str], manager_instance: Any) -> tuple[dict[str, Any], list[str], list[str], bool]`

处理单个 entry-point

- **entry_point**: entry-point 对象
- **objs**: 对象字典
- **enabled_list**: 启用列表
- **disabled_list**: 禁用列表
- **manager_instance**: 管理器实例（用于调用 exists/is_enabled 等方法）

**返回值**: (更新后的对象字典, 更新后的启用列表, 更新后的禁用列表, 是否为新项)

**内部方法**
子类必须实现此方法

---

