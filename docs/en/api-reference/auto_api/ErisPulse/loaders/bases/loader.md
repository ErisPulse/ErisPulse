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


### `resolve_min_sdk_version(component_obj: Any, name: str = '')`

解析组件声明的运行时最低 SDK 版本（统一读取口径）

解析优先级：``get_meta()`` 声明（:class:`~ErisPulse.Core.Bases.ModuleMeta`
实例或 dict，模块体系的规范声明位置）> 类属性 ``min_sdk_version``
（适配器等无 meta 声明类组件的声明位置）> ``None``（未声明）。

- **component_obj** (`组件类`): - **name**: 组件名称（仅用于 get_meta 异常时的诊断日志）
**返回值** (`str`): 声明的最低版本；未声明或声明为空返回 None

---


## 类列表


### `class BaseLoader(ABC)`

基础加载器抽象类

提供通用的加载器接口和配置管理功能

> **提示**
> 子类需要实现：
> - _get_entry_point_group: 返回 entry-point 组名
> - _process_entry_point: 处理单个 entry-point

> **内部方法**
此类仅供内部使用，不应直接实例化


#### 方法列表


##### `__init__(config_prefix: str)`

初始化基础加载器

- **config_prefix** (`配置前缀（如`): "ErisPulse.adapters" 或 "ErisPulse.modules"）

---


##### `set_strict_manager(manager: Any)`

注入严格模式管理器

- **manager** (`StrictModeManager`): 实例

> **内部方法**
由初始化协调器调用，确保多个加载器共享同一管理器实例以统一收集违规

---


##### `_strict()`

获取严格模式管理器

**返回值** (`StrictModeManager`): 实例

> **内部方法**
未注入时从配置创建，仅供独立调用/测试使用；正常启动流程总会被注入

---


##### `_check_sdk_version(name: str, component_type: str, component_obj: Any)`

运行时最低 SDK 版本检查（声明读取见 :func:`resolve_min_sdk_version`）

组件未声明或声明无法解析时放行（后者输出警告）；
版本不满足时输出明确错误、按严格模式登记拒绝并返回 False，
由调用方跳过该组件——SDK 过低的组件加载后几乎必然运行异常，
提前拦截可给出可操作的诊断（升级 SDK 或换用兼容版本组件）。

- **name** (`组件名称`): - **component_type**: 组件类型（``module`` / ``adapter``，用于日志与严格模式登记）
- **component_obj** (`组件类（经统一口径解析其`): min_sdk_version 声明）
**返回值** (`bool`): 是否允许继续加载

> **内部方法**
供 ModuleLoader / AdapterLoader 在构建组件信息前调用

---


##### `_get_entry_point_group()`

获取 entry-point 组名

**返回值** (`entry-point`): 组名

> **内部方法**
子类必须实现此方法

---


##### `async _process_entry_point(entry_point: Any, objs: dict[str, Any], enabled_list: list[str], disabled_list: list[str], manager_instance: Any)`

处理单个 entry-point

- **entry_point** (`entry-point`): 对象
- **objs** (`对象字典`): - **enabled_list**: 启用列表
- **disabled_list** (`禁用列表`): - **manager_instance**: 管理器实例（用于调用 exists/is_enabled 等方法）
**返回值** (`(更新后的对象字典,`): 更新后的启用列表, 更新后的禁用列表, 是否为新项)

> **内部方法**
子类必须实现此方法

---


##### `async load(manager_instance: Any)`

从 entry-points 加载对象

- **manager_instance** (`管理器实例`): **返回值** (`dict[str,`): Any]: 对象字典
    list[str]: 启用列表
    list[str]: 禁用列表

**异常**: `ImportError` - 当加载失败时抛出

---


##### `_register_config(name: str, enabled: bool = False)`

注册配置项

- **name** (`名称`): - **enabled**: 是否启用
**返回值** (`操作是否成功`): > **内部方法**
内部方法，用于注册新的配置项

---


##### `_get_config_status(name: str)`

获取配置状态

- **name** (`名称`): **返回值** (`是否启用`): > **内部方法**
内部方法，用于获取配置状态
默认情况下（无配置），返回 True（启用）并写入配置

---

