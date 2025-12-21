# `ErisPulse.__init__` 模块

<sup>更新时间: 2025-12-21 14:28:48</sup>

---

## 模块概述


ErisPulse SDK 主模块

提供SDK核心功能模块加载和初始化功能

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 使用前请确保已正确安装所有依赖
2. 调用await sdk.init()进行初始化
3. 模块加载采用懒加载机制</p></div>

---

## 函数列表

### async `async init_progress()`

初始化项目环境文件

1. 检查并创建main.py入口文件
2. 确保基础目录结构存在

:return: bool 是否创建了新的main.py文件

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 如果main.py已存在则不会覆盖
2. 此方法通常由SDK内部调用</p></div>

---

### async `async _prepare_environment()`

<div class='admonition warning'><p class='admonition-title'>内部方法</p><p></p></div>
准备运行环境

初始化项目环境文件

:return: bool 环境准备是否成功

---

### async `async init()`

SDK初始化入口

:return: bool SDK初始化是否成功

---

### `init_task()`

SDK初始化入口，返回Task对象

:return: asyncio.Task 初始化任务

---

### async `async uninit()`

SDK反初始化

执行以下操作：
1. 关闭所有适配器
2. 卸载所有模块
3. 清理所有事件处理器
4. 清理僵尸线程

:return: bool 反初始化是否成功

---

### async `async restart()`

SDK重新启动

执行完整的反初始化后再初始化过程

:return: bool 重新加载是否成功

---

### async `async run()`

无头模式运行ErisPulse

此方法提供了一种无需入口启动的方式，适用于与其它框架集成的场景

---

### async `async load_module(module_name: str)`

手动加载指定模块

:param module_name: str 要加载的模块名称
:return: bool 加载是否成功

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 可用于手动触发懒加载模块的初始化
2. 如果模块不存在或已加载会返回False</p></div>

---

## 类列表

### `class LazyModule`

    懒加载模块包装器

当模块第一次被访问时才进行实例化

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 模块的实际实例化会在第一次属性访问时进行
2. 依赖模块会在被使用时自动初始化
3. 对于继承自 BaseModule 的模块，会自动调用生命周期方法</p></div>

    
#### 方法列表

##### `__init__(module_name: str, module_class: Type, sdk_ref: Any, module_info: Dict[str, Any])`

    初始化懒加载包装器

:param module_name: str 模块名称
:param module_class: Type 模块类
:param sdk_ref: Any SDK引用
:param module_info: Dict[str, Any] 模块信息字典

    ---
    
##### async `async _initialize()`

    实际初始化模块

<dt>异常</dt><dd><code>LazyLoadError</code> 当模块初始化失败时抛出</dd>

    ---
    
##### `_ensure_initialized()`

    确保模块已初始化

<dt>异常</dt><dd><code>LazyLoadError</code> 当模块未初始化时抛出</dd>

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

    ---
    
### `class AdapterLoader`

    适配器加载器

专门用于从PyPI包加载和初始化适配器

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 适配器必须通过entry-points机制注册到erispulse.adapter组
2. 适配器类必须继承BaseAdapter
3. 适配器不适用懒加载</p></div>

    
#### 方法列表

##### async `async load()`

    从PyPI包entry-points加载适配器

:return: 
    Dict[str, object]: 适配器对象字典 {适配器名: 模块对象}
    List[str]: 启用的适配器名称列表
    List[str]: 停用的适配器名称列表
    
<dt>异常</dt><dd><code>ImportError</code> 当无法加载适配器时抛出</dd>

    ---
    
##### async `async _process_adapter(entry_point: Any, adapter_objs: Dict[str, object], enabled_adapters: List[str], disabled_adapters: List[str])`

    <div class='admonition warning'><p class='admonition-title'>内部方法</p><p></p></div>
处理单个适配器entry-point

:param entry_point: entry-point对象
:param adapter_objs: 适配器对象字典
:param enabled_adapters: 启用的适配器列表
:param disabled_adapters: 停用的适配器列表

:return: 
    Dict[str, object]: 更新后的适配器对象字典
    List[str]: 更新后的启用适配器列表 
    List[str]: 更新后的禁用适配器列表
    
<dt>异常</dt><dd><code>ImportError</code> 当适配器加载失败时抛出</dd>

    ---
    
### `class ModuleLoader`

    模块加载器

专门用于从PyPI包加载和初始化普通模块

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 模块必须通过entry-points机制注册到erispulse.module组
2. 模块类名应与entry-point名称一致</p></div>

    
#### 方法列表

##### async `async load()`

    从PyPI包entry-points加载模块

:return: 
    Dict[str, object]: 模块对象字典 {模块名: 模块对象}
    List[str]: 启用的模块名称列表
    List[str]: 停用的模块名称列表
    
<dt>异常</dt><dd><code>ImportError</code> 当无法加载模块时抛出</dd>

    ---
    
##### async `async _process_module(entry_point: Any, module_objs: Dict[str, object], enabled_modules: List[str], disabled_modules: List[str])`

    <div class='admonition warning'><p class='admonition-title'>内部方法</p><p></p></div>
处理单个模块entry-point

:param entry_point: entry-point对象
:param module_objs: 模块对象字典
:param enabled_modules: 启用的模块列表
:param disabled_modules: 停用的模块列表

:return: 
    Dict[str, object]: 更新后的模块对象字典
    List[str]: 更新后的启用模块列表 
    List[str]: 更新后的禁用模块列表
    
<dt>异常</dt><dd><code>ImportError</code> 当模块加载失败时抛出</dd>

    ---
    
##### `_should_lazy_load(module_class: Type)`

    检查模块是否应该懒加载

:param module_class: Type 模块类
:return: bool 如果返回 False，则立即加载；否则懒加载

    ---
    
### `class ModuleInitializer`

    模块初始化器（注意：适配器是一个特殊的模块）

负责协调适配器和模块的初始化流程

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 初始化顺序：适配器 → 模块
2. 模块初始化采用懒加载机制</p></div>

    
#### 方法列表

##### async `async init()`

    初始化所有模块和适配器

执行步骤:
1. 从PyPI包加载适配器
2. 从PyPI包加载模块
3. 预记录所有模块信息
4. 注册适配器
5. 初始化各模块

:return: bool 初始化是否成功
<dt>异常</dt><dd><code>InitError</code> 当初始化失败时抛出</dd>

    ---
    
##### async `async _initialize_modules(modules: List[str], module_objs: Dict[str, Any])`

    <div class='admonition warning'><p class='admonition-title'>内部方法</p><p></p></div>
初始化模块

:param modules: List[str] 模块名称列表
:param module_objs: Dict[str, Any] 模块对象字典

:return: bool 模块初始化是否成功

    ---
    
##### async `async _register_adapters(adapters: List[str], adapter_objs: Dict[str, Any])`

    <div class='admonition warning'><p class='admonition-title'>内部方法</p><p></p></div>
注册适配器

:param adapters: List[str] 适配器名称列表
:param adapter_objs: Dict[str, Any] 适配器对象字典

:return: bool 适配器注册是否成功

    ---
    
<sub>文档最后更新于 2025-12-21 14:28:48</sub>