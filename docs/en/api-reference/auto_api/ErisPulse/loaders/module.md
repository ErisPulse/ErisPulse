# `ErisPulse.loaders.module` 模块

---

## 模块概述


ErisPulse 模块加载器

专门用于从 PyPI 包加载和初始化普通模块

> **提示**
> 1. 模块必须通过 entry-points 机制注册到 erispulse.module 组
> 2. 模块类名应与 entry-point 名称一致
> 3. 模块支持懒加载机制

---

## 函数列表


### `_validate_sdk_attr_name(name: str)`

> **内部方法**
验证模块名称是否可以安全地作为 SDK 属性挂载

- **name** (`模块名称（entry-point`): name）
**返回值** (`True`): 如果名称安全，False 如果应拒绝

---


## 类列表


### `class ModuleLoader(BaseLoader)`

模块加载器

负责从 PyPI entry-points 加载模块，支持懒加载

> **提示**
> 使用方式：
> >>> loader = ModuleLoader()
> >>> module_objs, enabled, disabled = await loader.load(module_manager)


#### 方法列表


##### `__init__()`

初始化模块加载器

---


##### `_get_entry_point_group()`

获取 entry-point 组名

**返回值**: 入口点组名字符串

---


##### `async load(manager_instance: Any)`

从 entry-points 加载对象（使用 ModuleFinder）

- **manager_instance** (`管理器实例`): **返回值** (`dict[str,`): Any]: 对象字典
    list[str]: 启用列表
    list[str]: 禁用列表

**异常**: `ImportError` - 当加载失败时抛出

---


##### `async _process_entry_point(entry_point: Any, objs: dict[str, Any], enabled_list: list[str], disabled_list: list[str], manager_instance: Any)`

处理单个模块 entry-point

- **entry_point** (`entry-point`): 对象
- **objs** (`模块对象字典`): - **enabled_list**: 启用的模块列表
- **disabled_list** (`停用的模块列表`): - **manager_instance**: 模块管理器实例

**返回值** (`dict[str,`): Any]: 更新后的模块对象字典
    list[str]: 更新后的启用模块列表
    list[str]: 更新后的禁用模块列表
    bool: 是否为新模块

**异常**: `ImportError` - 当模块加载失败时抛出

---


##### `_extract_strategy_value(strategy: Any, key: str, default: Any)`

从策略对象或字典中提取值

- **strategy** (`策略对象（dict`): 或 ModuleLoadStrategy）
- **key** (`键名`): - **default**: 默认值
**返回值** (`提取到的值或默认值`): > **内部方法**
内部方法，统一处理 dict 和 ModuleLoadStrategy 两种策略类型

---


##### `_get_global_lazy_loading()`

获取全局懒加载配置

**返回值** (`是否启用懒加载（默认`): True）

> **内部方法**
内部方法，用于获取全局懒加载配置

---


##### `_resolve_strategy(module_class: type)`

按优先级从模块类解析加载策略

优先级：should_eager_load()（旧版兼容） → get_load_strategy()

- **module_class** (`模块类`): **返回值** (`策略对象或`): None

> **内部方法**
内部方法，用于解析模块的加载策略

---


##### `_apply_global_lazy_loading(strategy: Any, lazy_load: bool)`

应用全局懒加载配置到策略

- **strategy** (`原始策略`): - **lazy_load**: 懒加载值
**返回值** (`修改后的策略`): > **内部方法**
内部方法，用于应用全局配置覆盖

---


##### `_get_load_strategy(module_class: type)`

获取模块加载策略

优先级：
1. 模块的 should_eager_load() 方法（旧版兼容）
2. 模块的 get_load_strategy() 方法
3. 全局配置
4. 默认策略

全局配置会覆盖模块策略中的 lazy_load 设置

- **module_class** (`Type`): 模块类
**返回值** (`加载策略对象或字典`): > **内部方法**
内部方法，用于获取模块的加载策略

---


##### `async register_to_manager(modules: list[str], module_objs: dict[str, Any], manager_instance: Any)`

将模块类注册到管理器

- **modules** (`模块名称列表`): - **module_objs**: 模块对象字典
- **manager_instance** (`模块管理器实例`): **返回值** (`模块注册是否成功`): > **提示**
> 此方法由初始化协调器调用，仅注册模块类，不进行实例化

---


##### `_validate_dependencies(modules: list, module_objs: dict)`

验证所有模块的依赖是否满足

- **modules** (`list`): 模块名称列表
- **module_objs** (`dict`): 模块对象字典
**返回值** (`dict`): 缺少依赖的模块映射 {模块名: [缺少的依赖列表]}

> **内部方法**

---


##### `_topological_sort(modules: list, module_objs: dict)`

基于依赖关系和优先级的拓扑排序

- **modules** (`list`): 模块名称列表
- **module_objs** (`dict`): 模块对象字典
**返回值** (`list`): 排序后的模块 meta_name 列表

**异常**: `RuntimeError` - 当检测到循环依赖时

> **内部方法**

---


##### `async initialize_modules(modules: list[str], module_objs: dict[str, Any], manager_instance: Any, sdk_instance: Any)`

初始化模块（创建实例并挂载到 SDK）

- **modules** (`模块名称列表`): - **module_objs**: 模块对象字典
- **manager_instance** (`模块管理器实例`): - **sdk_instance**: SDK 实例
**返回值** (`模块初始化是否成功`): > **提示**
> 此方法处理模块的实际初始化和挂载
> 支持模块间依赖声明和拓扑排序加载

---


### `class LazyModule`

懒加载模块包装器

当模块第一次被访问时才进行实例化

> **提示**
> 1. 模块的实际实例化会在第一次属性访问时进行
> 2. 依赖模块会在被使用时自动初始化
> 3. 对于继承自 BaseModule 的模块，会自动调用生命周期方法


#### 方法列表


##### `__init__(module_name: str, module_class: type, sdk_ref: Any, module_info: dict[str, Any], manager_instance: Any)`

初始化懒加载包装器

- **module_name** (`str`): 模块名称
- **module_class** (`Type`): 模块类
- **sdk_ref** (`Any`): SDK 引用
- **module_info** (`dict[str,`): Any] 模块信息字典
- **manager_instance**: 模块管理器实例

---


##### `async _initialize()`

实际初始化模块

**异常**: `Exception` - 当模块初始化失败时抛出

> **内部方法**
内部方法，执行实际的模块初始化

---


##### `_ensure_initialized()`

确保模块已初始化

> **内部方法**
内部方法，检查并确保模块已初始化
> **内部方法**

设计说明：
- 支持同步/异步透明的懒加载机制，用户无需感知差异
- BaseModule 在异步上下文中通过辅助线程完成初始化
- BaseModule 在同步上下文中使用 asyncio.run() 确保初始化完成
- 非 BaseModule 保持原有逻辑，支持同步初始化
> **内部方法**

---


##### `_init_in_background_thread()`

在辅助线程中运行异步初始化，当前线程同步等待完成

> **内部方法**
当 _ensure_initialized 在已有事件循环中被调用时，无法使用
run_until_complete (会死锁)。通过在新线程中创建独立的事件循环
来运行异步初始化，同时当前线程通过 threading.Event 同步等待。
> **内部方法**

---


##### `_initialize_sync()`

同步初始化模块

> **内部方法**
内部方法，在同步上下文中初始化模块

---


##### `async _complete_async_init()`

完成异步初始化部分

> **内部方法**
内部方法，处理模块的异步初始化部分

---


##### `__getattr__(name: str)`

属性访问时触发初始化（仅在 __getattribute__ 未命中时调用）

- **name** (`str`): 属性名
**返回值** (`Any`): 属性值

---


##### `__setattr__(name: str, value: Any)`

属性设置

- **name** (`str`): 属性名
- **value** (`Any`): 属性值

---


##### `__delattr__(name: str)`

属性删除

- **name** (`str`): 属性名

---


##### `__getattribute__(name: str)`

属性访问，初始化后直接委托给实际实例

- **name** (`str`): 属性名
**返回值** (`Any`): 属性值

> **内部方法**
这是极热路径（Python 内部、hasattr、repr 等都会走这里），
因此必须保持轻量：不做日志、不做多余的属性查找。

---


##### `__dir__()`

返回模块属性列表

**返回值** (`list[str]`): 属性列表

---


##### `__repr__()`

返回模块表示字符串

**返回值** (`str`): 表示字符串

---


##### `__call__()`

代理函数调用

- **args** (`位置参数`): - **kwargs**: 关键字参数
**返回值**: 调用结果

---

