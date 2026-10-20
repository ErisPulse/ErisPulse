# `ErisPulse.loaders.adapter` 模块

---

## 模块概述


ErisPulse 适配器加载器

从 PyPI entry-points 与本地插件文件夹加载和初始化适配器

> **提示**
> 1. 适配器必须通过 entry-points 机制注册到 erispulse.adapter 组，
> 或放入本地插件目录（默认 ``plugins/``，经 ``discover_adapters`` 发现）
> 2. 适配器类必须继承 BaseAdapter
> 3. 适配器不适用懒加载

---

## 类列表


### `class _AdapterReloadSnapshot`

**内部方法**
适配器热重载回滚快照（引用级别）

记录重载前与目标适配器相关的全部注册状态：adapterInfo（含类引用）、
实例、启动态、启动任务、bots 记录与将被清除的 ``sys.modules`` 条目。
任一重载步骤失败时按序恢复，旧适配器继续服务。

尽力而为语义：unload 已执行的副作用（断连 / bot offline / 事件注销）
不可撤销——恢复后旧实例处于"已收尾"状态，快照中的 bots 记录仅为登记。


### `class AdapterLoader(BaseLoader)`

适配器加载器

负责从 PyPI entry-points 与本地插件文件夹加载适配器
（本地插件优先：与 entry-point 适配器同名时覆盖，便于本地覆盖调试）

> **提示**
> 使用方式：
> ```python
> loader = AdapterLoader()
> adapter_objs, enabled, disabled = await loader.load(adapter_manager)
> ```
>


#### 方法列表


##### `__init__()`

初始化适配器加载器

---


##### `_get_entry_point_group() -> str`

获取 entry-point 组名

**返回值**: 入口点组名字符串

---


##### `async load(manager_instance: Any) -> tuple[dict[str, Any], list[str], list[str]]`

从 entry-points 加载对象（使用 AdapterFinder）

- **manager_instance**: 管理器实例

**返回值**:

    dict[str, Any]: 对象字典
    list[str]: 启用列表
    list[str]: 禁用列表

**异常**: `ImportError` - 当加载失败时抛出

---


##### `async _process_entry_point(entry_point: Any, objs: dict[str, Any], enabled_list: list[str], disabled_list: list[str], manager_instance: Any) -> tuple[dict[str, Any], list[str], list[str], bool]`

处理单个适配器 entry-point

- **entry_point**: entry-point 对象
- **objs**: 适配器对象字典
- **enabled_list**: 启用的适配器列表
- **disabled_list**: 停用的适配器列表
- **manager_instance**: 适配器管理器实例

**返回值**:

    dict[str, Any]: 更新后的适配器对象字典
    list[str]: 更新后的启用适配器列表
    list[str]: 更新后的禁用适配器列表
    bool: 是否为新适配器

**异常**: `ImportError` - 当适配器加载失败时抛出

---


##### `_merge_plugin_folder(objs: dict[str, Any], enabled_list: list[str], disabled_list: list[str], manager_instance: Any) -> None`

**内部方法**
发现本地适配器插件并并入加载结果

本地插件优先：与 entry-point 适配器同名时，本地插件覆盖安装包条目
（便于本地覆盖调试）。启用状态沿用 ``ErisPulse.adapters.status``。

- **objs**: 适配器对象字典（原地修改）
- **enabled_list**: 启用列表（原地修改）
- **disabled_list**: 禁用列表（原地修改）
- **manager_instance**: 适配器管理器实例

---


##### `_build_adapter_info(entry_point: Any, loaded_class: type, adapter_obj: Any, meta_name: str, dist: Any = None) -> dict[str, Any]`

**内部方法**
构造适配器 adapterInfo（首次加载与热重载共用）

- **entry_point**: entry-point 对象
- **loaded_class**: entry-point 加载出的适配器类
- **adapter_obj**: 适配器类定义所在的模块对象
- **meta_name**: 平台名
- **dist**: 发行版元数据（可为 None）

**返回值** (`adapterInfo`): 字典

---


##### `_infer_adapter_top_level(info: 'dict | None') -> 'list[str]'`（staticmethod）

**内部方法**
适配器清理范围兜底推导：适配器类 ``__module__`` 的顶层段

- **info** (`adapterInfo`): 字典（可为 None）

**返回值**: 顶层模块名列表（无法推导时为空）

---


##### `_invalidate_source_caches_from(entries: 'dict[str, Any]') -> None`（staticmethod）

**内部方法**
按捕获的 ``sys.modules`` 条目清除源文件字节码缓存（``__pycache__``）

同秒内且字节数不变的源码改写不会使 pyc 失效（mtime 秒级粒度 + size
校验），重载路径必须显式清除。须在 purge ``sys.modules`` **之前**用
快照条目调用（快照条目持有 ``__file__``）。

- **entries**: 将被清除的 sys.modules 条目快照

---


##### `_precheck_adapter_sources(adapter_name: str, old_obj: Any, old_info: 'dict | None', purge_names: 'list[str]') -> bool`

**内部方法**
重载卸载前的语法预检：对目标源码树逐文件 ``ast.parse``

失败（语法错误）即拒绝重载——旧适配器未卸载、继续服务。源码无法
定位或超过 ``MODULE_RELOAD_PRECHECK_MAX_FILES`` 时跳过预检并记 debug。

- **adapter_name**: 适配器名（日志用）
- **old_obj**: 重载前的快照条目（适配器模块对象）
- **old_info**: 重载前的 adapterInfo
- **purge_names**: 清理名单

**返回值**: 是否通过（True = 允许继续重载流程）

---


##### `_capture_adapter_state(adapter_name: str, manager_instance: Any, purge_names: 'list[str]') -> '_AdapterReloadSnapshot'`

**内部方法**
采集适配器重载回滚快照（引用级别）

- **adapter_name**: 适配器名
- **manager_instance**: 适配器管理器实例
- **purge_names**: 将要清除的 sys.modules 顶层名

**返回值**: 回滚快照

---


##### `_restore_adapter_snapshot(snapshot: '_AdapterReloadSnapshot', adapter_name: str, manager_instance: Any) -> None`

**内部方法**
恢复适配器重载快照（重发现 / 注册失败时调用）

恢复顺序：sys.modules 条目 → 注册存根与实例 → 启动态 / bots /
启动任务。尽力而为语义：unload 已执行的副作用（断连 / bot offline）
不可撤销，恢复后旧实例处于"已收尾"状态。

- **snapshot**: 重载前采集的快照
- **adapter_name**: 适配器名
- **manager_instance**: 适配器管理器实例

---


##### `async reload_adapter(adapter_name: str, manager_instance: Any, sdk_instance: Any, *, full: bool = True) -> bool`

热重载单个适配器（支持本地插件 / PyPI 安装包两种来源）

完整执行 语法预检 → 卸载（shutdown 即清理 + 注销）→ 清理源码字节码
缓存与 ``sys.modules`` 子树 → 重新发现/导入 → 重新注册 → 原运行态则
重新拉起 流程；任一步失败自动回滚旧注册状态（尽力而为语义：断连 /
bot offline 等 unload 副作用不可撤销）。不重载依赖它的其它适配器
（仅告警）。

- **adapter_name**: 适配器名（平台名）
- **manager_instance**: 适配器管理器实例
- **sdk_instance** (`SDK`): 实例
- **full**: 保留参数位（当前两种来源均执行全量清理，与模块语义对齐）

**返回值**: 是否重载成功（适配器被移除视为成功）

---


##### `async register_to_manager(adapters: list[str], adapter_objs: dict[str, Any], manager_instance: Any) -> bool`

将适配器注册到管理器

- **adapters**: 适配器名称列表
- **adapter_objs**: 适配器对象字典
- **manager_instance**: 适配器管理器实例

**返回值**: 适配器注册是否成功

> **提示**
> 此方法由初始化协调器调用

---

