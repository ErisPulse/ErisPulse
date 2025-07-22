# 📦 `ErisPulse.__init__` 模块

*自动生成于 2025-07-22 16:35:31*

---

## 模块概述

ErisPulse SDK 主模块

提供SDK核心功能模块加载和初始化功能

💡 **提示**：

1. 使用前请确保已正确安装所有依赖
2. 调用sdk.init()进行初始化
3. 模块加载采用懒加载机制

---

## 🛠️ 函数

### `init_progress`

初始化项目环境文件

1. 检查并创建main.py入口文件
2. 确保基础目录结构存在

:return: bool 是否创建了新的main.py文件

💡 **提示**：

1. 如果main.py已存在则不会覆盖
2. 此方法通常由SDK内部调用

---

### `_prepare_environment`

⚠️ **内部方法**：

准备运行环境

1. 初始化项目环境文件
2. 加载环境变量配置

:return: bool 环境准备是否成功

---

### `init`

SDK初始化入口

执行步骤:
1. 准备运行环境
2. 初始化所有模块和适配器

:return: bool SDK初始化是否成功

💡 **提示**：

1. 这是SDK的主要入口函数
2. 如果初始化失败会抛出InitError异常
3. 建议在main.py中调用此函数

⚠️ **可能抛出**: `InitError` - 当初始化失败时抛出

---

### `load_module`

手动加载指定模块

:param module_name: str 要加载的模块名称
:return: bool 加载是否成功

💡 **提示**：

1. 可用于手动触发懒加载模块的初始化
2. 如果模块不存在或已加载会返回False

---

## 🏛️ 类

### `LazyModule`

懒加载模块包装器

当模块第一次被访问时才进行实例化

💡 **提示**：

1. 模块的实际实例化会在第一次属性访问时进行
2. 依赖模块会在被使用时自动初始化


#### 🧰 方法

##### `__init__`

初始化懒加载包装器

:param module_name: str 模块名称
:param module_class: Type 模块类
:param sdk_ref: Any SDK引用
:param module_info: Dict[str, Any] 模块信息字典

---

##### `_initialize`

实际初始化模块

⚠️ **可能抛出**: `LazyLoadError` - 当模块初始化失败时抛出

---

##### `__getattr__`

属性访问时触发初始化

:param name: str 要访问的属性名
:return: Any 模块属性值

---

##### `__call__`

调用时触发初始化

:param args: 位置参数
:param kwargs: 关键字参数
:return: Any 模块调用结果

---

##### `__bool__`

判断模块布尔值时触发初始化

:return: bool 模块布尔值

---

##### `__str__`

转换为字符串时触发初始化

:return: str 模块字符串表示

---

##### `__copy__`

浅拷贝时返回自身，保持懒加载特性

:return: self

---

##### `__deepcopy__`

深拷贝时返回自身，保持懒加载特性

:param memo: memo
:return: self

---

### `AdapterLoader`

适配器加载器

专门用于从PyPI包加载和初始化适配器

💡 **提示**：

1. 适配器必须通过entry-points机制注册到erispulse.adapter组
2. 适配器类必须继承BaseAdapter
3. 适配器不适用懒加载


#### 🧰 方法

##### `load`

从PyPI包entry-points加载适配器

:return: 
    Dict[str, object]: 适配器对象字典 {适配器名: 模块对象}
    List[str]: 启用的适配器名称列表
    List[str]: 停用的适配器名称列表
    
⚠️ **可能抛出**: `ImportError` - 当无法加载适配器时抛出

---

##### `_process_adapter`

⚠️ **内部方法**：

处理单个适配器entry-point

:param entry_point: entry-point对象
:param adapter_objs: 适配器对象字典
:param enabled_adapters: 启用的适配器列表
:param disabled_adapters: 停用的适配器列表

:return: 
    Dict[str, object]: 更新后的适配器对象字典
    List[str]: 更新后的启用适配器列表 
    List[str]: 更新后的禁用适配器列表
    
⚠️ **可能抛出**: `ImportError` - 当适配器加载失败时抛出

---

### `ModuleLoader`

模块加载器

专门用于从PyPI包加载和初始化普通模块

💡 **提示**：

1. 模块必须通过entry-points机制注册到erispulse.module组
2. 模块类名应与entry-point名称一致


#### 🧰 方法

##### `load`

从PyPI包entry-points加载模块

:return: 
    Dict[str, object]: 模块对象字典 {模块名: 模块对象}
    List[str]: 启用的模块名称列表
    List[str]: 停用的模块名称列表
    
⚠️ **可能抛出**: `ImportError` - 当无法加载模块时抛出

---

##### `_process_module`

⚠️ **内部方法**：

处理单个模块entry-point

:param entry_point: entry-point对象
:param module_objs: 模块对象字典
:param enabled_modules: 启用的模块列表
:param disabled_modules: 停用的模块列表

:return: 
    Dict[str, object]: 更新后的模块对象字典
    List[str]: 更新后的启用模块列表 
    List[str]: 更新后的禁用模块列表
    
⚠️ **可能抛出**: `ImportError` - 当模块加载失败时抛出

---

##### `_should_lazy_load`

检查模块是否应该懒加载

:param module_class: Type 模块类
:return: bool 如果返回 False，则立即加载；否则懒加载

---

### `ModuleInitializer`

模块初始化器

负责协调适配器和模块的初始化流程

💡 **提示**：

1. 初始化顺序：适配器 → 模块
2. 模块初始化采用懒加载机制


#### 🧰 方法

##### `init`

初始化所有模块和适配器

执行步骤:
1. 从PyPI包加载适配器
2. 从PyPI包加载模块
3. 预记录所有模块信息
4. 注册适配器
5. 初始化各模块

:return: bool 初始化是否成功
⚠️ **可能抛出**: `InitError` - 当初始化失败时抛出

---

##### `_initialize_modules`

⚠️ **内部方法**：

初始化模块

:param modules: List[str] 模块名称列表
:param module_objs: Dict[str, Any] 模块对象字典

:return: bool 模块初始化是否成功

---

##### `_register_adapters`

⚠️ **内部方法**：

注册适配器

:param adapters: List[str] 适配器名称列表
:param adapter_objs: Dict[str, Any] 适配器对象字典

:return: bool 适配器注册是否成功

---


*文档最后更新于 2025-07-22 16:35:31*