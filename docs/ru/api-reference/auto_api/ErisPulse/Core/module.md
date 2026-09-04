# `ErisPulse.Core.module` 模块

---

## 模块概述


ErisPulse 模块系统

提供标准化的模块注册、加载和管理功能，与适配器系统保持一致的设计模式

---

## 函数列表


### `_warn_deprecated_kwarg(owner: str, old: str, new: str)`

> **内部方法**
当检测到使用已弃用的旧关键字参数时，记录一次弃用日志并说明迁移方式

- **owner** (`所属方法名（如`): "ModuleManager.get"）
- **old** (`已弃用的旧参数名`): - **new**: 推荐使用的新参数名

---


## 类列表


### `class ModuleManager(ManagerBase)`

模块管理器

提供标准化的模块注册、加载和管理功能，模仿适配器管理器的模式

> **提示**
> 1. 使用register方法注册模块类
> 2. 使用load/unload方法加载/卸载模块
> 3. 通过get方法获取模块实例


#### 方法列表


##### `_unload_timeout()`

> **内部方法**
读取模块 on_unload 优雅收尾的超时（秒）

复用 ``ErisPulse.framework.uninit_timeout`` 配置（反初始化流程的统一超时预算，
整体仍有 uninit 的 wait_for 兜底）；未配置或非法时回退常量默认值。

**返回值**: 超时秒数（>0）

---


##### `set_sdk_ref(sdk)`

设置 SDK 引用

- **sdk** (`SDK`): 实例
**返回值** (`bool`): 是否设置成功

---


##### `_register_config_change_routing()`

> **内部方法**
注册 config.set / config.updated 事件订阅，将配置变更路由到各模块的 on_config_update

- ``config.set``：代码或 Dashboard 调用 setConfig 时即时触发（单 key 变更）
- ``config.updated``：用户手动编辑配置文件后由文件监听任务触发（整树变更）

---


##### `_on_config_set(data: dict)`

> **内部方法**
处理 config.set 事件：找出受影响的模块并触发 on_config_update

---


##### `_on_config_updated(data: dict)`

> **内部方法**
处理 config.updated 事件：对比新旧配置树，找出配置变化的模块并触发 on_config_update

---


##### `_cleanup_lazy(module_name: str)`

> **内部方法**
清理模块的懒加载代理与 SDK 属性（模块未实例化时也有效）

- **module_name**: 模块名称

---


##### `_resolve_config_key(instance: Any)`

> **内部方法**
解析模块的配置键名（优先用注入的注册名，回退类名）

---


##### `_notify_config_update(instance: Any, module_name: str, old_dict: dict | None, new_dict: dict | None)`

> **内部方法**
调用模块的 on_config_update 回调，传入类型安全的配置对象

- **instance** (`模块实例`): - **module_name**: 模块名（用于日志）
- **old_dict** (`变更前的配置字典（可能为`): None）
- **new_dict** (`变更后的配置字典（可能为`): None）

---


##### `register(name: str | None = None, class_type: type | None = None, info: dict | None = None)`

注册模块类

- **name** (`模块名称`): - **class_type**: 模块类
- **info** (`模块信息`): - **module_name** (`已弃用`): 兼容旧关键字参数，等同 name
- **module_class** (`已弃用`): 兼容旧关键字参数，等同 class_type
- **module_info** (`已弃用`): 兼容旧关键字参数，等同 info
**返回值** (`是否注册成功`): **异常**: `TypeError` - 当模块类无效时抛出

**示例**:
```python
>>> module.register("MyModule", MyModuleClass)
```

---


##### `register_lazy(name: str, lazy_proxy: Any)`

注册懒加载代理

- **name** (`模块名称`): - **lazy_proxy**: 懒加载代理对象（LazyModule）

> **内部方法**
由加载器在创建 LazyModule 后调用。注册后 get() 会返回该代理，
从而使“懒加载对用户透明”：已注册但未加载的模块不再返回 None。

---


##### `unregister_lazy(name: str)`

取消注册懒加载代理

- **name** (`模块名称`): > **内部方法**
卸载/取消注册模块时调用，保持 _lazy_modules 与实际挂载状态一致。

---


##### `async load(name: str | None = None)`

加载指定模块（标准化加载逻辑）

- **name** (`模块名称`): - **module_name** (`已弃用`): 兼容旧关键字参数，等同 name
**返回值** (`是否加载成功`): 
**示例**:
```python
>>> await module.load("MyModule")
```

---


##### `_collect_dependents(name: str)`

> **内部方法**
收集直接或间接依赖指定模块的模块闭包（BFS）

返回顺序为由近及远（直接依赖者在前、间接依赖者在后）；
卸载时应按相反顺序执行，保证每个依赖者卸载时其依赖仍可用。

- **name** (`目标模块名`): **返回值** (`依赖者模块名列表（不含`): name 本身）

---


##### `async unload(name: str | None = None)`

卸载指定模块或所有模块

卸载被其它模块依赖的模块时，依赖它的模块会**级联卸载**
（依赖者先卸载，日志说明级联链），避免依赖者持有失效引用继续运行。

``purge`` 控制是否**一并删除注册存根**：

- ``purge=False``（默认）：只取消加载——卸载实例与资源，但保留
  注册存根（模块类与元信息），模块仍可被 discover 重新发现、`load()`
  重新实例化，无需重新 `register()`
- ``purge=True``：彻底卸载——同时删除注册存根（释放模块类引用），
  并对插件文件夹来源的模块清理 ``sys.modules``，使插件及其独占依赖
  可被 GC 回收（解决 NoneBot 式卸载后插件与依赖内存不释放的问题）；
  级联卸载的依赖者同样被 purge。卸载后重新加载需重新 `register()`

- **name** (`模块名称，None表示卸载所有模块（默认None）`): - **module_name** (`已弃用`): 兼容旧关键字参数，等同 name
- **purge** (`是否一并删除注册存根并清理`): sys.modules（默认 False）
**返回值** (`是否卸载成功`): 
**示例**:
```python
>>> await module.unload("MyModule")  # 卸载单个模块（依赖者级联卸载）
>>> await module.unload("MyModule", purge=True)  # 彻底卸载（释放类引用）
>>> await module.unload()  # 卸载所有模块
```

---


##### `async _unload_single_module(module_name: str)`

> **内部方法**
卸载单个模块

- **module_name** (`模块名称`): **返回值**: 是否卸载成功

---


##### `_purge_module_stub(module_name: str)`

> **内部方法**
删除模块注册存根，释放模块类引用（并清理插件来源的 sys.modules）

返回 (module_name, class_weakref, instance_weakref) 供回收诊断。

- **module_name** (`模块名`): **返回值** (`供`): `_report_purge_recyclability` 消费的弱引用三元组

---


##### `_purge_sys_modules(module_name: str, top_level: list[str])`

> **内部方法**
从 sys.modules 移除插件自身模块与其子包（保守：不清理第三方/共享库）

- **module_name** (`插件模块名`): - **top_level**: 顶层包名列表（用于清理包内子模块）

---


##### `_report_purge_recyclability(refs: list[tuple[str, Any, Any]])`

> **内部方法**
purge 卸载后诊断模块类/实例是否可回收，泄漏时告警并列出引用方

- **refs** (``_purge_module_stub``): 产出的 (name, class_ref, instance_ref) 列表

---


##### `get(name: str | None = None)`

获取模块实例或懒加载代理

- **name** (`模块名称`): - **module_name** (`已弃用`): 兼容旧关键字参数，等同 name
**返回值** (`模块实例`): / 懒加载代理 / None

> **提示**
> 不会触发加载。返回值优先级：
> 1. 已加载的真实实例（_modules）
> 2. 懒加载代理（_lazy_modules，访问其属性才会触发初始化）
> 3. None（模块未注册或未挂载）
> 这使得 ``module.get()`` 与 ``sdk.xxx`` / ``module.MyModule``
> 在“懒加载对用户透明”上保持一致：已注册但未加载的模块不再返回 None。
> 由于框架通过 entry_points 动态发现模块，入口点无法静态获知
> 具体模块类型；返回值为泛型 ``_TModule``（默认基类）。
> 若调用方与模块同项目且能导入模块类，可添加类型注解获得更精确补全：
> >>> my_module: MyModule = sdk.module.get("MyModule")

**示例**:
```python
>>> my_module = module.get("MyModule")
```

---


##### `exists(name: str | None = None)`

检查模块是否已注册

- **name** (`模块名称`): - **module_name** (`已弃用`): 兼容旧关键字参数，等同 name
**返回值** (`模块是否已注册（即`): module.register() 已被调用）

> **提示**
> exists() 只检查模块类是否已注册到管理器，用于验证模块是否可以加载。
> 如需检查模块是否启用，请使用 is_enabled()。

---


##### `is_loaded(name: str | None = None)`

检查模块是否已加载

- **name** (`模块名称`): - **module_name** (`已弃用`): 兼容旧关键字参数，等同 name
**返回值** (`模块是否已加载`): 
**示例**:
```python
>>> if module.is_loaded("MyModule"):
...     ...
```

---


##### `is_running(name: str | None = None)`

检查模块是否正在运行（已加载）

- **name** (`模块名称`): - **module_name** (`已弃用`): 兼容旧关键字参数，等同 name
**返回值** (`模块是否正在运行`): 
**示例**:
```python
>>> if module.is_running("MyModule"):
>>>     print("MyModule 正在运行")
```

---


##### `list_running()`

列出所有正在运行的模块（已加载）

**返回值** (`模块名称列表`): 
**示例**:
```python
>>> running = module.list_running()
>>> print("正在运行的模块:", running)
```

---


##### `list_registered()`

列出所有已注册的模块

**返回值** (`模块名称列表`): 
**示例**:
```python
>>> registered = module.list_registered()
```

---


##### `list_loaded()`

列出所有已加载的模块

**返回值** (`模块名称列表`): 
**示例**:
```python
>>> loaded = module.list_loaded()
```

---


##### `_config_register(module_name: str, enabled: bool = DEFAULT_MODULE_ENABLED)`

注册新模块信息

> **内部方法**
此方法仅供内部使用

- **module_name** (`模块名称`): - **enabled**: 是否启用模块 (默认: DEFAULT_MODULE_ENABLED)
**返回值**: 是否操作成功

---


##### `is_enabled(name: str | None = None)`

检查模块是否启用

- **name** (`模块名称`): - **module_name** (`已弃用`): 兼容旧关键字参数，等同 name
**返回值** (`模块是否启用`): > **提示**
> 模块启用条件：
> 1. 模块在配置文件中（ErisPulse.modules.status.{module_name} 存在）
> 2. 配置值为启用状态
> 如果模块未在配置中，默认启用并自动写入配置

---


##### `enable(name: str | None = None)`

启用模块

- **name** (`str`): 模块名称
- **module_name** (`已弃用`): 兼容旧关键字参数，等同 name
**返回值** (`bool`): 操作是否成功

---


##### `disable(name: str | None = None)`

禁用模块

- **name** (`str`): 模块名称
- **module_name** (`已弃用`): 兼容旧关键字参数，等同 name
**返回值** (`bool`): 操作是否成功

---


##### `unregister(name: str | None = None)`

取消注册模块

- **name** (`模块名称`): - **module_name** (`已弃用`): 兼容旧关键字参数，等同 name
**返回值** (`是否取消成功`): > **内部方法**
注意：此方法仅取消注册，不卸载已加载的模块

---


##### `clear()`

清除所有模块实例和类

> **内部方法**
此方法用于反初始化时完全重置模块管理器状态

---


##### `list_items()`

列出所有模块状态

合并配置项与已注册模块，确保禁用模块也可见。

**返回值** (`dict[str, bool`): ] {模块名: 是否启用} 字典

---


##### `get_info(name: str | None = None)`

获取模块信息

- **name** (`模块名称`): - **module_name** (`已弃用`): 兼容旧关键字参数，等同 name
**返回值** (`模块信息字典，不存在则返回None`): 
**示例**:
```python
>>> info = module.get_info("MyModule")
```

---


##### `get_meta(name: str | None = None)`

获取模块的介绍元信息（描述这个模块是什么、属于哪一类等）

元信息是模块的**通用介绍数据**，供 help 模块、Dashboard 模块列表、
模块商店等各类界面 / 生态模块消费。

**i18n 支持**：元信息字段值可为纯字符串，或 i18n 字典
``{"i18n": "key.path", "default": "兜底文本"}``（与配置 description 约定一致）。
翻译键通过模块的 ``I18nClass`` 声明注册（键路径 ``<模块名>.<属性名>``）。
``resolve_i18n=True``（默认）时解析为当前语言文本；``False`` 时透传原始字典。

解析优先级：模块类声明的 ``get_meta()`` > 注册时传入的 ``info``，缺失字段自动补全。

- **name** (`模块名称`): - **resolve_i18n**: 是否解析 i18n 字典为当前语言文本（默认 True）
- **module_name** (`已弃用`): 兼容旧关键字参数，等同 name
**返回值** (`元信息字典，模块未注册时返回`): None

**示例**:
```python
>>> meta = module.get_meta("Weather")
>>> meta["description"]  # 当前语言下的模块简介
```

---


##### `_resolve_meta_value(value: Any)`

> **内部方法**
解析元信息字段值：i18n 字典 → 当前语言文本；其余原样返回

- **value** (`原始值（str`): 或 {"i18n": ..., "default": ...}）
**返回值**: 解析后的值

---


##### `_commands_of(module_name: str)`

> **内部方法** 列出该模块注册的主命令名

---


##### `get_commands_overview()`

获取命令总览（模块 meta + 其注册的命令，按模块聚合）

聚合每个模块的**介绍元信息**与其**注册的命令**（含别名 / 分组 / 帮助文本），
便于 help 模块、管理界面等按模块展示"这个模块是干什么的 + 有哪些命令"。

**返回值** (`{模块名:`): {"meta": {...}, "commands": [{name, aliases, group, help, hidden}]}}

**示例**:
```python
>>> overview = module.get_commands_overview()
>>> overview["Weather"]["meta"]["description"]
"查询城市天气"
>>> overview["Weather"]["commands"][0]["name"]
"weather"
```

---


##### `get_status_summary()`

获取模块的完整状态摘要

便于WebUI展示所有模块的注册、加载和启用状态，
包含已禁用模块以便于管理。

**返回值** (`状态摘要字典`): 
**示例**:
```python
>>> summary = module.get_status_summary()
>>> # {
>>> #     "modules": {
>>> #         "MyModule": {
>>> #             "status": "loaded",
>>> #             "enabled": True,
>>> #             "is_base_module": True
>>> #         },
>>> #         "DisabledModule": {
>>> #             "status": "disabled",
>>> #             "enabled": False,
>>> #             "is_base_module": None
>>> #         }
>>> #     }
>>> # }
```

---


##### `get_topology()`

获取模块的拓扑树数据（便于 WebUI 展示）

聚合每个模块拥有的命令、事件处理器、路由与生命周期钩子，
按 owner（模块名）归并，展示模块与资源的归属关系。

**返回值** (`拓扑树字典`): {"modules": {name: {
        "loaded": bool, "enabled": bool,
        "load_strategy": {"lazy": bool|None, "priority": int|None},
        "info": dict|None,
        "commands": [str, ...],
        "handlers": {event_type: count},
        "routes": {"http": [...], "ws": [...], "sse": [...]},
        "lifecycle_hooks": int,
        "scope_applies": bool,
    }}}

**示例**:
```python
>>> topology = module.get_topology()
>>> print(topology["modules"]["Chat"]["commands"])
["chat"]
```

---


##### `__getattr__(module_name: str)`

通过属性访问获取模块实例

- **module_name** (`str`): 模块名称
**返回值** (`Any`): 模块实例
**异常**: `AttributeError` - 当模块不存在或未启用时

**示例**:
```python
>>> my_module = module.MyModule
```

---


##### `__contains__(module_name: str)`

检查模块是否存在且处于启用状态

- **module_name** (`str`): 模块名称
**返回值** (`bool`): 模块是否存在且启用

**示例**:
```python
>>> if "MyModule" in module:
...     ...
```

---

