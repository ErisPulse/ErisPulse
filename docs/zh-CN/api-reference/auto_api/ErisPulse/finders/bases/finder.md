# `ErisPulse.finders.bases.finder` 模块

---

## 模块概述


ErisPulse 基础发现器

定义发现器的抽象基类，提供通用的发现器接口和结构

> **提示**
> 1. 所有具体发现器应继承自 BaseFinder
> 2. 子类需实现 _get_entry_point_group 方法
> 3. 支持缓存机制，避免重复查询

---

## 类列表


### `class _RemoteDist`

远程环境的 Distribution 轻量代理

模拟 ``importlib.metadata.Distribution`` 的必要接口（name / version / metadata），
用于在跨环境查询时提供与本地 Distribution 一致的访问体验。


#### 方法列表


##### `metadata()`

模拟 Distribution.metadata，提供 Summary 等字段的查询

---


### `class _RemoteEntryPoint`

远程环境的 EntryPoint 轻量代理

模拟 ``importlib.metadata.EntryPoint`` 的必要接口
（name / value / group / dist / load()），
用于跨环境查询时与本地 EntryPoint 对象保持一致的外部访问模式。

> **提示**
> ``load()`` 仅在目标环境与当前环境一致时有意义；跨环境时调用 ``load()``
> 会抛出 ``RuntimeError``，应通过 ``value`` 自行解析。


#### 方法列表


##### `load()`

加载 entry-point 引用对象

**异常**: `RuntimeError` - 跨环境查询时不支持在当前进程加载目标环境的对象

---


### `class BaseFinder(ABC)`

基础发现器抽象类

提供通用的发现器接口和缓存功能

> **提示**
> 子类需要实现：
> - _get_entry_point_group: 返回 entry-point 组名

> **内部方法**
此类仅供内部使用，不应直接实例化


#### 方法列表


##### `__init__(python_executable: str | None = None)`

初始化基础发现器

- **python_executable** (`str | None`): 目标 Python 解释器路径。
    当指定且与当前解释器不同时，通过子进程查询该环境的 entry-points，
    用于跨环境场景（如 epsdk 安装在 pipx，用户包在项目 venv）。
    默认为 None，表示查询当前解释器环境。

---


##### `last_error()`

最近一次 entry-point 发现操作的错误信息

**返回值** (`str | None`): 发现失败时的错误描述，成功或从未失败时返回 None

---


##### `_get_entry_point_group()`

获取 entry-point 组名

**返回值** (`entry-point`): 组名

> **内部方法**
子类必须实现此方法

---


##### `_is_remote_target()`

判断是否查询远程目标环境（非当前解释器）

**返回值** (`bool`): 目标环境与当前解释器不同时返回 True

---


##### `_fetch_remote_entry_points(group_name: str)`

通过子进程查询目标 Python 环境的 entry-points

- **group_name** (`str`): entry-point 组名
**返回值** (`list[Any`): ] EntryPoint 或兼容对象的列表

> **内部方法**
当目标环境不是当前解释器时，运行子进程获取该环境的 entry-points，
返回模拟 ``importlib.metadata.EntryPoint`` 接口的轻量对象。

---


##### `_get_entry_points()`

获取所有 entry-points

**返回值** (`entry-point`): 对象列表

> **内部方法**
内部方法，使用缓存机制获取 entry-points。
当配置了目标 Python 解释器且与当前不同时，通过子进程查询目标环境。

---


##### `find_all()`

查找所有 entry-points

**返回值** (`entry-point`): 对象列表

---


##### `find_by_name(name: str)`

按名称查找 entry-point

- **name** (`entry-point`): 名称
**返回值** (`entry-point`): 对象，未找到返回 None

---


##### `get_entry_point_map()`

获取 entry-point 映射字典

**返回值** (`{name:`): entry_point} 字典

---


##### `_ensure_cache()`

确保缓存已加载且未过期

---


##### `get_group_name()`

获取 entry-point 组名

**返回值** (`entry-point`): 组名

---


##### `get_top_level_modules(package_name: str)`

获取指定 PyPI 包的顶层 Python 模块名

- **package_name** (`PyPI`): 包名
**返回值** (`顶层`): Python 模块名列表

> **提示**
> 通过读取包的 top_level.txt 获取顶层模块名。
> 如果 top_level.txt 不可用，则从 entry-points 的模块路径推导。
> 用于重启时清理 sys.modules 缓存。

---


##### `clear_cache()`

清除缓存

> **提示**
> 当安装/卸载包后调用此方法清除缓存

---


##### `set_cache_expiry(expiry: int)`

设置缓存过期时间

- **expiry** (`过期时间（秒）`): > **内部方法**
内部方法，用于调整缓存策略

---


##### `__iter__()`

迭代器接口

**返回值** (`entry-point`): 迭代器

---


##### `__len__()`

返回 entry-point 数量

**返回值** (`entry-point`): 数量

---


##### `__contains__(name: str)`

检查 entry-point 是否存在

- **name** (`entry-point`): 名称
**返回值**: 是否存在

---


##### `__repr__()`

返回发现器的字符串表示

**返回值**: 字符串表示

---

