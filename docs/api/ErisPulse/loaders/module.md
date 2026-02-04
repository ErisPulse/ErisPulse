# `ErisPulse.loaders.module` 模块

> 最后更新：2026-02-04 06:11:34

---

## 模块概述


ErisPulse 模块加载器

专门用于从 PyPI 包加载和初始化普通模块

> **提示**
> 1. 模块必须通过 entry-points 机制注册到 erispulse.module 组
> 2. 模块类名应与 entry-point 名称一致
> 3. 模块支持懒加载机制

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

:return: "erispulse.module"

---


##### `async async _process_entry_point(entry_point: Any, objs: Dict[str, Any], enabled_list: List[str], disabled_list: List[str], manager_instance: Any)`

处理单个模块 entry-point

:param entry_point: entry-point 对象
:param objs: 模块对象字典
:param enabled_list: 启用的模块列表
:param disabled_list: 停用的模块列表
:param manager_instance: 模块管理器实例

:return: 
    Dict[str, Any]: 更新后的模块对象字典
    List[str]: 更新后的启用模块列表 
    List[str]: 更新后的禁用模块列表
    
**异常**: `ImportError` - 当模块加载失败时抛出

---


##### `_get_load_strategy(module_class: Type)`

获取模块加载策略

:param module_class: Type 模块类
:return: 加载策略对象或字典

> **内部方法** 
内部方法，用于获取模块的加载策略

---


##### `_strategy_with_lazy_load(strategy: Any, lazy_load: bool)`

创建修改 lazy_load 的新策略副本

:param strategy: 原始策略
:param lazy_load: 懒加载值
:return: 新策略

> **内部方法** 
内部方法，用于创建修改后的策略副本

---


##### `async async register_to_manager(modules: List[str], module_objs: Dict[str, Any], manager_instance: Any)`

将模块类注册到管理器

:param modules: 模块名称列表
:param module_objs: 模块对象字典
:param manager_instance: 模块管理器实例
:return: 模块注册是否成功

> **提示**
> 此方法由初始化协调器调用，仅注册模块类，不进行实例化

---


##### `async async initialize_modules(modules: List[str], module_objs: Dict[str, Any], manager_instance: Any, sdk_instance: Any)`

初始化模块（创建实例并挂载到 SDK）

:param modules: 模块名称列表
:param module_objs: 模块对象字典
:param manager_instance: 模块管理器实例
:param sdk_instance: SDK 实例
:return: 模块初始化是否成功

> **提示**
> 此方法处理模块的实际初始化和挂载

并行注册所有模块类（已在 register_to_manager 中完成）
这里处理模块的实例化和挂载

---


### `class LazyModule`

懒加载模块包装器

当模块第一次被访问时才进行实例化

> **提示**
> 1. 模块的实际实例化会在第一次属性访问时进行
> 2. 依赖模块会在被使用时自动初始化
> 3. 对于继承自 BaseModule 的模块，会自动调用生命周期方法


#### 方法列表


##### `__init__(module_name: str, module_class: Type, sdk_ref: Any, module_info: Dict[str, Any], manager_instance: Any)`

初始化懒加载包装器

:param module_name: str 模块名称
:param module_class: Type 模块类
:param sdk_ref: Any SDK 引用
:param module_info: Dict[str, Any] 模块信息字典
:param manager_instance: 模块管理器实例

---


##### `async async _initialize()`

实际初始化模块

**异常**: `Exception` - 当模块初始化失败时抛出

> **内部方法** 
内部方法，执行实际的模块初始化

---


##### `_ensure_initialized()`

确保模块已初始化

**异常**: `RuntimeError` - 当模块需要异步初始化时抛出

> **内部方法** 
内部方法，检查并确保模块已初始化

---


##### `_initialize_sync()`

同步初始化模块

> **内部方法** 
内部方法，在同步上下文中初始化模块

---


##### `async async _complete_async_init()`

完成异步初始化部分

> **内部方法** 
内部方法，处理模块的异步初始化部分

---


##### `__getattr__(name: str)`

属性访问时触发初始化

:param name: str 属性名
:return: Any 属性值

---


##### `__setattr__(name: str, value: Any)`

属性设置

:param name: str 属性名
:param value: Any 属性值

---


##### `__delattr__(name: str)`

属性删除

:param name: str 属性名

---


##### `__getattribute__(name: str)`

属性访问，初始化后直接委托给实际实例

:param name: str 属性名
:return: Any 属性值

---


##### `__dir__()`

返回模块属性列表

:return: List[str] 属性列表

---


##### `__repr__()`

返回模块表示字符串

:return: str 表示字符串

---


##### `__call__()`

代理函数调用

:param args: 位置参数
:param kwargs: 关键字参数
:return: 调用结果

---

