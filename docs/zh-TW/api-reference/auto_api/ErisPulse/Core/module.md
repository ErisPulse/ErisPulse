# `ErisPulse.Core.module` 模块

---

## 模块概述


ErisPulse 模块系统

提供标准化的模块注册、加载和管理功能，与适配器系统保持一致的设计模式

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


##### `_register_config_change_routing() -> None`

**内部方法**
注册 config.set / config.updated 事件订阅，将配置变更路由到各模块的 on_config_update

- ``config.set``：代码或 Dashboard 调用 setConfig 时即时触发（单 key 变更）
- ``config.updated``：用户手动编辑配置文件后由文件监听任务触发（整树变更）

---


##### `_on_config_set(data: dict) -> None`

**内部方法**
处理 config.set 事件：找出受影响的模块并触发 on_config_update

---


##### `_on_config_updated(data: dict) -> None`

**内部方法**
处理 config.updated 事件：对比新旧配置树，找出配置变化的模块并触发 on_config_update

---


##### `_cleanup_lazy(module_name: str) -> None`

**内部方法**
清理模块的懒加载代理与 SDK 属性（模块未实例化时也有效）

- **module_name**: 模块名称

---


##### `_resolve_config_key(instance: Any) -> str`（staticmethod）

**内部方法**
解析模块的配置键名（优先用注入的注册名，回退类名）

---


##### `_notify_config_update(instance: Any, module_name: str, old_dict: dict | None, new_dict: dict | None) -> None`

**内部方法**
调用模块的 on_config_update 回调，传入类型安全的配置对象

- **instance**: 模块实例
- **module_name**: 模块名（用于日志）
- **old_dict**: 变更前的配置字典（可能为 None）
- **new_dict**: 变更后的配置字典（可能为 None）

---


##### `register(name: str | None = None, class_type: type | None = None, info: dict | None = None, *, module_name: str | None = None, module_class: type | None = None, module_info: dict | None = None) -> bool`

注册模块类

- **name**: 模块名称
- **class_type**: 模块类
- **info**: 模块信息
- **module_name** (`已弃用`): 兼容旧关键字参数，等同 name
- **module_class** (`已弃用`): 兼容旧关键字参数，等同 class_type
- **module_info** (`已弃用`): 兼容旧关键字参数，等同 info

**返回值**: 是否注册成功

**异常**: `TypeError` - 当模块类无效时抛出

**示例**:

```python
module.register("MyModule", MyModuleClass)
```

---


##### `_synthesize_runtime_meta(module_name: str, module_class: type) -> dict[str, Any]`（staticmethod）

**内部方法**
为运行时注册的模块合成最小 meta（来源标记 / top_level / 定义模块）

``top_level`` 取定义模块 ``__module__`` 的顶层段（与 sdk 层推导规则
一致），供 reload 清理 ``sys.modules`` 使用；描述 / 版本 / 作者字段
从 ``get_meta()`` 尽力补全（不可用则省略）。

---


##### `_register_reload_snapshot(loader: Any, module_name: str, module_class: type) -> None`

**内部方法**
运行时注册后同步登记模块加载器的重载快照条目

快照条目为模块类定义所在的模块对象（``sys.modules`` 项），并为其
挂载合成 moduleInfo（若尚无）——reload 编排经该条目读取 meta 与
top_level。定义模块不可用或已被占用 moduleInfo 时回退为轻量命名
空间载体（reload 仅读取 ``__name__`` 与 ``moduleInfo``）。

---


##### `register_lazy(name: str, lazy_proxy: Any) -> None`

注册懒加载代理

- **name**: 模块名称
- **lazy_proxy**: 懒加载代理对象（LazyModule）

**内部方法**
由加载器在创建 LazyModule 后调用。注册后 get() 会返回该代理，
从而使“懒加载对用户透明”：已注册但未加载的模块不再返回 None。

---


##### `unregister_lazy(name: str) -> None`

取消注册懒加载代理

- **name**: 模块名称

**内部方法**
卸载/取消注册模块时调用，保持 _lazy_modules 与实际挂载状态一致。

---


##### `async load(name: str | None = None, *, module_name: str | None = None) -> bool`

加载指定模块（标准化加载逻辑）

- **name**: 模块名称
- **module_name** (`已弃用`): 兼容旧关键字参数，等同 name

**返回值**: 是否加载成功

**示例**:

```python
await module.load("MyModule")
```

---


##### `_collect_dependents(name: str) -> list[str]`

**内部方法**
收集直接或间接依赖指定模块的模块闭包（BFS）

返回顺序为由近及远（直接依赖者在前、间接依赖者在后）；
卸载时应按相反顺序执行，保证每个依赖者卸载时其依赖仍可用。

- **name**: 目标模块名

**返回值**: 依赖者模块名列表（不含 name 本身）

---


##### `async unload(name: str | None = None, *, module_name: str | None = None, purge: bool = False, reason: str = 'unload') -> bool`

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

卸载与热重载共用全局互斥：与进行中的 reload / restart / 归眠串行
（消除外部卸载与重载交叉导致的双重 ``on_unload``）；等待上限
``UNLOAD_LOCK_WAIT_TIMEOUT_SECS`` 秒，超时降级直接执行并留痕
（持锁重载卡死的极端场景不阻塞调用方）。

- **name**: 模块名称，None表示卸载所有模块（默认None）
- **module_name** (`已弃用`): 兼容旧关键字参数，等同 name
- **purge**: 是否一并删除注册存根并清理 sys.modules（默认 False）
- **reason**: 卸载来意标注，透传给 ``on_before_unload`` 钩子与

         ``module.before_unload`` 事件（``"unload"`` / ``"reload"`` /
         ``"disable"`` / ``"cascade"``；框架内部使用，常规调用保持默认）
**返回值**: 是否卸载成功

**示例**:

```python
await module.unload("MyModule")  # 卸载单个模块（依赖者级联卸载）
await module.unload("MyModule", purge=True)  # 彻底卸载（释放类引用）
await module.unload()  # 卸载所有模块
```

---


##### `async _unload_locked(name: str | None, *, purge: bool = False, reason: str = 'unload') -> bool`

**内部方法**
unload 的实现体（调用方已持有热重载互斥锁，或已限时降级）

- **name**: 模块名称，None 表示卸载所有模块
- **purge**: 是否一并删除注册存根并清理 sys.modules
- **reason**: 卸载来意标注

**返回值**: 是否卸载成功

---


##### `async sleep(name: str | None = None, *, module_name: str | None = None) -> bool`

归眠指定模块（懒加载休眠）

与 unload 的差异：释放运行时资源（on_unload / 归属任务 / 连接 /
注册资源），但**保留懒加载代理与注册存根**——模块回到"已注册未
加载"状态（与从未激活不可区分），下次属性访问 / ``module.call`` /
``activate_on`` 事件将透明唤醒（重新实例化并 on_load）。

归眠前触发 ``on_before_unload``（reason=``"dormant"``），模块可借
此把状态保存到 storage，唤醒后在 ``on_load`` 中恢复。自动归眠需在
加载策略中声明 ``get_load_strategy(dormant_after="30m")``；任何已
加载模块均可手动归眠。

- **name**: 模块名称
- **module_name** (`已弃用`): 兼容旧关键字参数，等同 name

**返回值**: 是否归眠成功（未加载/未注册返回 True——无事可做）

**示例**:

```python
await module.sleep("HeavyTool")   # 闲置归眠，释放资源
```

---


##### `touch_activity(module_name: str) -> None`

**内部方法**
记录模块活跃时间戳（休眠清扫判定用）

埋点位置：事件处理器调用（Core/Event/base._invoke_handler）、
命令执行（Core/Event/command）、``module.call`` 目标解析。

- **module_name**: 模块注册名

---


##### `_ensure_dormancy_sweeper() -> None`

**内部方法**
确保休眠清扫器后台循环已启动（幂等；无休眠声明时不启动）

---


##### `async _dormancy_sweep_loop() -> None`

**内部方法**
休眠清扫循环：按固定间隔扫描已加载且声明 dormant_after 的模块，
闲置超阈值即自动归眠（uninit 时随后台任务统一取消）

---


##### `async _dormancy_sweep() -> None`

**内部方法**
单轮休眠扫描：对闲置超过阈值的已加载模块自动归眠

依赖方策略：不级联、不跳过——懒模块的依赖方经由持久代理
（``sdk.<Name>``）/ ``module.call`` 访问，归眠后与"从未激活"不可
区分，唤醒路径照常生效。

---


##### `async reload(name: str, *, full: bool = True) -> bool`

热重载单个模块（支持任意来源：本地插件 / 运行时注册 / PyPI 安装包）

经模块加载器完整执行 语法预检 → 卸载旧实例 → 清理注册与
``sys.modules`` 缓存（按顶层包名 + ``invalidate_caches``，默认全量）
→ 重新发现/导入 → 重新注册并加载 流程；依赖该模块的模块会**级联
重载**并默认重导代码。本地插件（``plugins/`` 目录）来源重扫描插件
目录；运行时注册来源按定义模块重导并按类名重取；PyPI 安装包来源
重新查询 entry-point 并重导入模块代码（pip 升级后调用即可生效）。

``full=False`` 切换为**轻量重载**：仅按元数据清理 ``sys.modules``，
PyPI 依赖者卸载后直接重新实例化——仅供超大依赖树的性能敏感场景。

- **name**: 模块名（entry-point 名称、插件名或运行时注册名）
- **full**: 是否全量重载（默认 True；False 为轻量逃生门）

**返回值**: 是否重载成功（SDK 未初始化时返回 False）

**示例**:

```python
await sdk.module.reload("dice")      # 本地插件
await sdk.module.reload("MyRuntime") # 运行时注册模块
await sdk.module.reload("Weather")   # PyPI 安装包模块（默认全量）
```

---


##### `async reload_all() -> 'dict[str, bool]'`

全量热重载所有已注册模块（尽力而为语义）

经模块加载器执行 卸载全部 → 清理全部 ``sys.modules`` 子树 →
重新发现/注册 → 按依赖拓扑序加载 → 此前已加载的懒加载模块重新
激活 流程，一次刷新全部模块代码（pip 批量升级后调用即可全部生效）。
单模块失败仅记录诊断并跳过，不影响其余模块；无整体回滚——
on_unload 副作用不可撤销，与单模块热重载语义一致。

**返回值**: 模块注册名 → 是否重载成功（发现阶段即失败的模块不在结果中；

         SDK 未初始化时返回空字典）

**示例**:

```python
await sdk.module.reload_all()
```

---


##### `async _run_before_unload(module_name: str, instance: Any, reason: str, timeout: float) -> None`

**内部方法**
触发卸载前钩子与 ``module.before_unload`` 事件（卸载/禁用流水线第一步）

先广播事件（第三方状态管家模块可观测），再调用实例可选钩子
``on_before_unload(event)``——event 携带 ``module_name`` 与 ``reason``
（``"reload"`` / ``"unload"`` / ``"disable"`` / ``"cascade"``）。
任一失败仅告警，不阻塞后续卸载流程（与 on_unload 容忍语义一致）。

- **module_name**: 模块注册名
- **instance**: 模块实例（可为 None——仅广播事件）
- **reason**: 卸载来意
- **timeout**: 钩子优雅执行超时（秒）

---


##### `async _unload_single_module(module_name: str, *, reason: str = 'unload', sleep: bool = False) -> bool`

**内部方法**
卸载单个模块（``sleep=True`` 时为归眠：释放资源但保留懒加载代理）

- **module_name**: 模块名称
- **reason**: 卸载来意（透传给 on_before_unload 钩子与 before_unload 事件）
- **sleep**: 归眠模式——保留懒加载代理与注册存根，模块回到"已注册未加载"状态

**返回值**: 是否卸载成功

---


##### `_record_load_error(module_name: str, e: BaseException) -> None`

**内部方法**
记录模块加载失败现场（``last_error()`` / ``get_info().last_error`` 消费）

- **module_name**: 模块注册名
- **e**: 失败异常

---


##### `_cleanup_failed_module_cache(module_name: str) -> None`

**内部方法**
加载失败后的缓存自清洗

失败模块的 ``sys.modules`` 条目没有任何保留价值——主动弹出并刷新
插件路径记录，保证「改完代码再 load / reload 一次」必定读到磁盘
新代码，而不是复用失败存根 + 旧 import 缓存的组合。不影响注册表
中已登记的模块类（重新 load 无需重新 register）。

---


##### `async _half_unload_failed_module(module_name: str, instance: Any) -> None`

**内部方法**
加载失败（on_load 异常 / 构造后阶段异常）时的半卸载

对已构造实例按正常卸载同序触发资源回收（on_unload → 取消归属
任务 → 外部清理钩子 → 框架资源注销），保证 ``__init__`` /
``on_load`` 半途注册的资源不成为"有主孤儿"。

与正常卸载的差异：不触碰 ``_modules`` / ``_loaded_modules`` /
``_module_services`` 与 sdk 属性——失败路径从未写入这些注册表；
``on_unload`` 已执行的副作用（断连等）与正常卸载一致不可撤销，
但实例与注册资源不再泄漏。

- **module_name**: 模块注册名
- **instance**: 已构造的实例（构造函数本身抛异常时为 None）

---


##### `_cleanup_module_registrations(module_name: str) -> None`

**内部方法**
清理模块在加载上下文内注册的全部框架资源（unload / disable 共用）

委托归属权统一门面（``Core/ownership``）完成：i18n 翻译域、路由
（命名空间 + owner 兜底：中间件 / 首页入口 / 非命名空间路由）、
适配器事件处理器与中间件、命令与事件处理器、自定义会话类型、
平台事件方法注入、事件覆写、scope 覆写、交互会话等待、主人身份源
provider、生命周期钩子。每步失败仅记录日志，不中断后续清理。

- **module_name**: 模块名

---


##### `audit(module_name: str, deep: bool = False) -> 'dict[str, Any]'`

归属权泄漏审计（透传归属权统一门面）

- **module_name**: 目标模块名
- **deep**: 附带 gc 实例普查（weakref 存活检查 + 引用方类型；

             有全局暂停开销，仅显式排障使用）
**返回值**: 审计报告 dict（owner / counts / orphans / 深普查结果）

**示例**:

```python
report = sdk.module.audit("roll", deep=True)
report["instance_recyclable"]
True
```

---


##### `is_shadow_module(module_name: str) -> bool`

判断模块名是否为影子 owner（拓扑 / Dashboard 展示用）

- **module_name**: 模块名

**返回值**: 是否为影子 owner

---


##### `async shadow_start(module_name: str, source: 'str | Any', owner: 'str | None' = None) -> str`

启动影子：把新版代码以独立 owner 装载为 ``module_name`` 的影子实例
（运行时 API；模块代码零改动，影子的出站被拦截记账、不真正发出）

- **module_name**: 被 shadow 的已加载模块名
- **source**: 新版代码路径（目录含 ``__init__.py`` 或单 ``.py`` 文件；

               建议放在 plugins 目录之外）
- **owner**: 影子 owner 名（默认取路径名）

**返回值**: 影子 owner 名

**示例**:

```python
await sdk.module.shadow_start("roll", source="downloads/roll_v2")
'roll_shadow'
```

---


##### `async promote_shadow(module_name: str) -> bool`

影子转正：卸载当前版本 → 影子以真名注册加载 → 失败自动回滚

转正永远由人确认（无自动晋升）；复用重载快照机制保证失败时旧实例
继续服务（尽力而为语义：on_unload 已执行的副作用不可撤销）。转正后
请尽快持久化安装新版本（pip 升级 / 替换插件文件），使重启后仍生效。

- **module_name**: 原模块名

**返回值**: 是否转正成功

**异常**: `ValueError` - 该模块未绑定影子时

**示例**:

```python
await sdk.module.promote_shadow("roll")
```

---


##### `async dismiss_shadow(module_name: str) -> bool`

放弃影子：回收影子资源并解除绑定（原模块不受影响）

- **module_name**: 原模块名

**返回值**: 是否成功（未绑定影子时 False）

**示例**:

```python
await sdk.module.dismiss_shadow("roll")
```

---


##### `shadow_diff(module_name: str) -> 'dict[str, Any]'`

影子与线上的行为对比（影子意向出站 × transcript 实际发送，按 trace_id 对齐）

- **module_name**: 原模块名

**返回值**: 对比报告 dict（shadow_owner / count / aligned）

**示例**:

```python
report = sdk.module.shadow_diff("roll")
report["count"]
3
```

---


##### `_purge_module_stub(module_name: str) -> tuple[str, Any, Any]`

**内部方法**
删除模块注册存根，释放模块类引用（并清理插件来源的 sys.modules）

返回 (module_name, class_weakref, instance_weakref) 供回收诊断。

- **module_name**: 模块名

**返回值**: 供 `_report_purge_recyclability` 消费的弱引用三元组

---


##### `_purge_sys_modules(module_name: str, top_level: list[str]) -> None`（staticmethod）

**内部方法**
从 sys.modules 移除插件自身模块与其子包（保守：不清理第三方/共享库）

移除前先清除对应源文件的字节码缓存：purge 卸载 → 改码 → 重新
load 的链路同样保证读到新代码（同秒同字节数改写不再命中旧 pyc）。

- **module_name**: 插件模块名
- **top_level**: 顶层包名列表（用于清理包内子模块）

---


##### `_report_purge_recyclability(refs: list[tuple[str, Any, Any]]) -> None`

**内部方法**
purge 卸载后诊断模块类/实例是否可回收，泄漏时告警并列出引用方

- **refs**: `_purge_module_stub` 产出的 (name, class_ref, instance_ref) 列表

---


##### `get(name: str | None = None, *, module_name: str | None = None) -> '_TModule | Any | None'`

获取模块实例或懒加载代理

- **name**: 模块名称
- **module_name** (`已弃用`): 兼容旧关键字参数，等同 name

**返回值**: 模块实例 / 懒加载代理 / None

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
> ```python
> my_module: MyModule = sdk.module.get("MyModule")
> ```
>

**示例**:

```python
my_module = module.get("MyModule")
```

---


##### `exists(name: str | None = None, *, module_name: str | None = None) -> bool`

检查模块是否已注册

- **name**: 模块名称
- **module_name** (`已弃用`): 兼容旧关键字参数，等同 name

**返回值**: 模块是否已注册（即 module.register() 已被调用）

> **提示**
> exists() 只检查模块类是否已注册到管理器，用于验证模块是否可以加载。
> 如需检查模块是否启用，请使用 is_enabled()。

---


##### `is_loaded(name: str | None = None, *, module_name: str | None = None) -> bool`

检查模块是否已加载

- **name**: 模块名称
- **module_name** (`已弃用`): 兼容旧关键字参数，等同 name

**返回值**: 模块是否已加载

**示例**:

```python
if module.is_loaded("MyModule"):
    ...
```

---


##### `is_running(name: str | None = None, *, module_name: str | None = None) -> bool`

检查模块是否正在运行（已加载）

- **name**: 模块名称
- **module_name** (`已弃用`): 兼容旧关键字参数，等同 name

**返回值**: 模块是否正在运行

**示例**:

```python
if module.is_running("MyModule"):
    print("MyModule 正在运行")
```

---


##### `list_running() -> list[str]`

列出所有正在运行的模块（已加载）

**返回值**: 模块名称列表

**示例**:

```python
running = module.list_running()
print("正在运行的模块:", running)
```

---


##### `list_registered() -> list[str]`

列出所有已注册的模块

**返回值**: 模块名称列表

**示例**:

```python
registered = module.list_registered()
```

---


##### `list_loaded() -> list[str]`

列出所有已加载的模块

**返回值**: 模块名称列表

**示例**:

```python
loaded = module.list_loaded()
```

---


##### `_config_register(module_name: str, enabled: bool = DEFAULT_MODULE_ENABLED) -> bool`

注册新模块信息

**内部方法**
此方法仅供内部使用

- **module_name**: 模块名称
- **enabled**: 是否启用模块 (默认: DEFAULT_MODULE_ENABLED)

**返回值**: 是否操作成功

---


##### `is_enabled(name: str | None = None, *, module_name: str | None = None) -> bool`

检查模块是否启用

- **name**: 模块名称
- **module_name** (`已弃用`): 兼容旧关键字参数，等同 name

**返回值**: 模块是否启用

> **提示**
> 模块启用条件：
> 1. 模块在配置文件中（ErisPulse.modules.status.{module_name} 存在）
> 2. 配置值为启用状态
> 如果模块未在配置中，默认启用并自动写入配置

---


##### `enable(name: str | None = None, *, module_name: str | None = None) -> bool`

启用模块

- **name** (`str`): 模块名称
- **module_name** (`已弃用`): 兼容旧关键字参数，等同 name

**返回值** (`bool`): 操作是否成功

---


##### `disable(name: str | None = None, *, module_name: str | None = None) -> bool`

禁用模块

- **name** (`str`): 模块名称
- **module_name** (`已弃用`): 兼容旧关键字参数，等同 name

**返回值** (`bool`): 操作是否成功

---


##### `unregister(name: str | None = None, *, module_name: str | None = None) -> bool`

取消注册模块

- **name**: 模块名称
- **module_name** (`已弃用`): 兼容旧关键字参数，等同 name

**返回值**: 是否取消成功

**内部方法**
注意：此方法仅取消注册，不卸载已加载的模块

---


##### `clear() -> None`

清除所有模块实例和类

**内部方法**
此方法用于反初始化时完全重置模块管理器状态

---


##### `list_items() -> dict[str, bool]`

列出所有模块状态

合并配置项与已注册模块，确保禁用模块也可见。

**返回值** (`dict[str, bool`): ] {模块名: 是否启用} 字典

---


##### `last_error(name: str | None = None, *, module_name: str | None = None) -> dict | None`

查询模块最近一次加载失败现场

``load()`` 失败（构造 / on_load 异常 / SystemExit）时记录异常对象、
完整 traceback 与时间戳；下次加载成功后自动清除。失败详情同时随
``get_info()`` 以 ``last_error`` 字段暴露——RPC / 编程调用方直接
取用，无需翻日志文件。

- **name**: 模块名称
- **module_name** (`已弃用`): 兼容旧关键字参数，等同 name

**返回值**: 失败现场字典 ``{"exception", "traceback", "at"}``，无记录返回 None

**示例**:

```python
await module.load("X")  # doctest: +SKIP
False
module.last_error("X")["exception"]  # doctest: +SKIP
"AttributeError('...')"
```

---


##### `get_info(name: str | None = None, *, module_name: str | None = None) -> dict | None`

获取模块信息

返回值为注册元信息的浅拷贝，附加运行时诊断字段：

- ``last_error``：最近一次加载失败现场（见 :meth:`last_error`）
- ``running_identity``：实际在跑的代码身份（``{"module", "version"}``）
- ``stale``：注册版本 ≠ 运行版本时为 True（"改了代码忘 reload" 一眼可见）

- **name**: 模块名称
- **module_name** (`已弃用`): 兼容旧关键字参数，等同 name

**返回值**: 模块信息字典（含诊断字段），不存在则返回None

**示例**:

```python
info = module.get_info("MyModule")
```

---


##### `get_meta(name: str | None = None, *, resolve_i18n: bool = True, module_name: str | None = None) -> dict | None`

获取模块的介绍元信息（描述这个模块是什么、属于哪一类等）

元信息是模块的**通用介绍数据**，供 help 模块、Dashboard 模块列表、
模块商店等各类界面 / 生态模块消费。

**i18n 支持**：元信息字段值可为纯字符串，或 i18n 字典
``{"i18n": "key.path", "default": "兜底文本"}``（与配置 description 约定一致）。
翻译键通过模块的 ``I18nClass`` 声明注册（键路径 ``<模块名>.<属性名>``）。
``resolve_i18n=True``（默认）时解析为当前语言文本；``False`` 时透传原始字典。

解析优先级：模块类声明的 ``get_meta()`` > 注册时传入的 ``info``，缺失字段自动补全。

- **name**: 模块名称
- **resolve_i18n**: 是否解析 i18n 字典为当前语言文本（默认 True）
- **module_name** (`已弃用`): 兼容旧关键字参数，等同 name

**返回值**: 元信息字典，模块未注册时返回 None

**示例**:

```python
meta = module.get_meta("Weather")
meta["description"]  # 当前语言下的模块简介
```

---


##### `_resolve_meta_value(value: Any) -> Any`（staticmethod）

**内部方法**
解析元信息字段值：i18n 字典 → 当前语言文本；其余原样返回

- **value**: 原始值（str 或 {"i18n": ..., "default": ...}）

**返回值**: 解析后的值

---


##### `_commands_of(module_name: str) -> list[str]`

**内部方法** 列出该模块注册的主命令名

---


##### `get_commands_overview(*, event: Any = None, platform: str | None = None, bot_id: str | None = None, session_id: str | None = None) -> dict[str, dict[str, Any]]`

获取命令总览（模块 meta + 其注册的命令，按模块聚合）

聚合每个模块的**介绍元信息**与其**注册的命令**（含别名 / 分组 / 帮助文本），
便于 help 模块、管理界面等按模块展示"这个模块是干什么的 + 有哪些命令"。
命令的 help / hidden 字段为合并控制面覆盖后的生效值（用户优先）。

传入作用域上下文（``event`` 或 ``platform`` / ``bot_id`` / ``session_id``
任一）时，当前会话不可用模块不进入总览（会话感知总览）。

- **event**: 可选，事件上下文（Event 或 dict）
- **platform**: 可选，平台名（与 event 叠加时显式参数优先）
- **bot_id**: 可选，Bot 标识
- **session_id**: 可选，会话标识

**返回值**: {模块名: {"meta": {...}, "commands": [{name, aliases, group, help, hidden}]}}

**示例**:

```python
overview = module.get_commands_overview()
overview["Weather"]["meta"]["description"]
"查询城市天气"
overview["Weather"]["commands"][0]["name"]
"weather"
overview = module.get_commands_overview(event=event)   # 会话感知
```

---


##### `get_status_summary() -> dict[str, Any]`

获取模块的完整状态摘要

便于WebUI展示所有模块的注册、加载和启用状态，
包含已禁用模块以便于管理。

**返回值**: 状态摘要字典

**示例**:

```python
summary = module.get_status_summary()
# {
#     "modules": {
#         "MyModule": {
#             "status": "loaded",
#             "enabled": True,
#             "is_base_module": True
#         },
#         "DisabledModule": {
#             "status": "disabled",
#             "enabled": False,
#             "is_base_module": None
#         }
#     }
# }
```

---


##### `get_topology(*, json_safe: bool = True) -> dict[str, Any]`

获取模块的拓扑树数据（便于 WebUI 展示）

聚合每个模块拥有的命令、事件处理器、路由与生命周期钩子，
按 owner（模块名）归并，展示模块与资源的归属关系。

- **json_safe**: 是否输出可直接 JSON 序列化的安全结构（默认 True）。

                  安全模式下 ``info`` 只保留纯数据的 ``meta`` 子表
                  （丢弃 ``module_class`` / ``strategy`` 等运行时对象），
                  并对整树做序列化兜底净化。

**返回值**: 拓扑树字典

    {"modules": {name: {
        "loaded": bool, "enabled": bool,
        "load_strategy": {"lazy": bool|None, "priority": int|None},
        "info": dict|None,
        "commands": [str, ...],
        "services": [str, ...],
        "handlers": {event_type: count},
        "routes": {"http": [...], "ws": [...], "sse": [...]},
        "lifecycle_hooks": int,
        "scope_applies": bool,
    }}}

**示例**:

```python
topology = module.get_topology()
print(topology["modules"]["Chat"]["commands"])
["chat"]
```

---


##### `_parse_replay_duration(value: Any) -> float`（classmethod）

**内部方法**
解析回放时长声明（``"5m"`` / ``"1h"`` / ``"300"``）

- **value**: 时长值

**返回值**: 秒数

---


##### `_build_replay_event(record: dict[str, Any]) -> Any | None`

**内部方法**
从收件箱记录构造回放合成事件

合成事件带 ``replayed: True`` 标志（处理器可据此跳过副作用）；
``user_id`` 优先取记录的 sender，私聊场景回退为 target。

- **record**: 收件箱记录（role / text / ts / sender / session_key）

**返回值**: 合成事件（Event）；无法解析会话键时返回 None

---


##### `async _replay_events(module_name: str, replay: Any) -> None`

**内部方法**
执行冷启动事件回放：收件箱最近消息 → 仅分发给该模块的处理器

- **module_name**: 模块名
- **replay**: 回放时长声明（"5m" / "1h" / 秒数）

---


##### `_resolve_services(module_name: str) -> 'list[dict[str, Any]] | None'`

**内部方法**
解析模块的服务契约（get_meta().services），规范化为字典列表

- **module_name**: 模块名称

**返回值**: ``[{"name": ..., "description": <str|i18n dict|None>,

    "parameters": <dict|None>}, ...]``；未声明时返回 None（公开方法全开放）

---


##### `_service_names(module_name: str) -> 'list[str] | None'`

**内部方法**
获取服务白名单（名字列表）

- **module_name**: 模块名称

**返回值**: 服务名列表；未声明时返回 None

---


##### `_docstring_first_line(func: Any) -> str`（staticmethod）

**内部方法**
提取函数 docstring 的摘要行（服务介绍的自动兜底）

兼容规范的多行 docstring（空行开头）：取**第一个非空行**，
跳过 doctest 装饰行（``>>>`` / ``...``）。无 docstring 时返回空串。

- **func**: 函数 / 绑定方法

**返回值**: 摘要文本（可能为空串）

---


##### `_service_description(module_name: str, entry: dict[str, Any]) -> str`

**内部方法**
解析服务介绍：显式声明（i18n 字典解析）> 方法 docstring 首行 > 空串

- **module_name**: 模块名
- **entry**: 规范化服务条目（{"name", "description"}）

**返回值**: 介绍文本

---


##### `_docstring_params(func: Any) -> dict[str, str]`（staticmethod）

**内部方法**
从 docstring 提取参数说明（``:param name: 文本`` 行），作为服务参数提示的自动兜底

兼容 Sphinx 带类型形态（``:param int n: ...``，取末位词为参数名）；
每个参数取说明首行，重复声明取首个。

- **func**: 函数 / 绑定方法

**返回值**: ``{参数名: 说明文本}``（无 docstring 或无参数区时为空字典）

---


##### `_service_parameters(module_name: str, entry: dict[str, Any]) -> dict[str, str]`

**内部方法**
解析服务参数提示：显式声明（i18n 字典解析）与方法 docstring ``:param:`` 行按参数合并，
单参数内显式声明优先

仅保留方法签名中实际存在的参数（首个 ``self`` / ``cls`` 与变长参数除外）——
声明与签名不一致时以签名为准，保证提示不会描述不存在的调用面。

- **module_name**: 模块名
- **entry**: 规范化服务条目（{"name", "description", "parameters"}）

**返回值**: ``{参数名: 提示文本}``（无任何提示来源时为空字典）

---


##### `services(module_name: str | None = None) -> 'dict[str, list[dict[str, Any]]]'`

服务目录：列出模块通过 ``get_meta().services`` 声明的对外服务

仅包含**显式声明**的模块（未声明的模块不出现在结果中）；
每个服务附带方法签名字符串、介绍文本与参数提示：

- **介绍来源**：``services`` 中 ``{"name", "description"}`` 的显式声明

  （支持 i18n 字典，解析为当前语言）> 方法 docstring 首行 > 空串
- **签名**：``inspect.signature`` 提取
- **参数提示**：``parameters`` 中 ``{参数名: 说明}`` 显式声明

  （支持 i18n 字典）与方法 docstring ``:param:`` 行按参数合并，
  单参数内显式声明优先；仅含签名内实际存在的参数

懒加载（已注册未加载）模块同样进入目录——服务发现先于加载发生，
调用方可据此决定是否 ``call()`` 唤醒目标模块。

为后续 MCP 化（调用点暴露给 AI）与生态服务发现提供数据基础。

- **module_name**: 仅查询指定模块；None 时列出全部已注册模块中声明了服务的

**返回值**: ``{模块名: [{"name", "signature", "description", "parameters"}]}``

**示例**:

```python
sdk.module.services()
{'Chat': [{'name': 'get_history',
           'signature': '(session_id, n=20)',
           'description': '查询会话历史',
           'parameters': {'session_id': '会话 ID', 'n': '返回条数'}}]}
sdk.module.services("Chat")
{'Chat': [{'name': 'get_history', ...}]}
```

---


##### `async _resolve_call_target(module_name: str) -> Any`

**内部方法**
解析模块间调用的目标实例（含懒加载模块唤醒）

- **module_name**: 模块名称

**返回值**: 模块实例

**异常**: `ModuleNotAvailableError` - 模块未注册 / 未启用 / 唤醒失败时

---


##### `async call(module_name: str, method: str, *args: Any, timeout: float | None = None, **kwargs: Any) -> Any`

跨模块调用目标模块的服务方法（协议化 RPC）

与 ``module.<Name>.<method>()`` 裸属性访问的差异：
目标模块未注册 / 未启用时抛出类型化异常而非 AttributeError；
懒加载模块自动唤醒；``get_meta().services`` 契约白名单校验；
调用方经过 scope 出站维度（``actions.<caller>.call``）审计；
被调方法执行期间 ``current_owner`` 归因到目标模块，
其内部的 wait_reply / 出站发送 / 日志等正确归属；
调用方身份保留在 ``current_caller`` 上下文中（``get_current_caller()``
读取），供被调方识别调用来源；
协程方法带超时语义（超时抛 :class:`ModuleCallTimeoutError`）。

- **module_name**: 目标模块名
- **method**: 目标方法名
- **args**: 位置参数（透传给目标方法）
- **timeout**: 超时秒数（默认 30 秒；None 表示不限时；仅对协程方法生效）
- **kwargs**: 关键字参数（透传给目标方法）

**返回值**: 目标方法的返回值

**异常**: `ModuleNotAvailableError` - 目标模块未注册 / 未启用 / 唤醒失败

**异常**: `ServiceNotProvidedError` - 方法不在目标模块的 ``services`` 白名单内（或为私有方法 / 不存在）

**异常**: `ModuleCallError` - 调用方被 scope 出站规则拒绝

**异常**: `ModuleCallTimeoutError` - 协程方法超时

**示例**:

```python
result = await sdk.module.call("Chat", "get_history", session_id, n=20)
```

> **提示**
> 服务方在 ``get_meta().services`` 声明契约收紧调用面（缺省时公开方法全开放）:
> ```
> class ChatModule(BaseModule):
>     @staticmethod
>     def get_meta() -> ModuleMeta:
>         return ModuleMeta(services=["get_history", "translate"])
> 
>     async def get_history(self, session_id, n=20): ...
> ```
>

---


##### `__getattr__(module_name: str) -> Any`

通过属性访问获取模块实例

- **module_name** (`str`): 模块名称

**返回值** (`Any`): 模块实例

**异常**: `AttributeError` - 当模块不存在或未启用时

**示例**:

```python
my_module = module.MyModule
```

---


##### `__contains__(module_name: str) -> bool`

检查模块是否存在且处于启用状态

- **module_name** (`str`): 模块名称

**返回值** (`bool`): 模块是否存在且启用

**示例**:

```python
if "MyModule" in module:
    ...
```

---

