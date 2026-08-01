# `ErisPulse.Core.config` 模块

---

## 模块概述


ErisPulse 配置中心

集中管理所有配置项，避免循环导入问题
提供自动补全缺失配置项的功能
添加内存缓存和延迟写入机制以提高性能

> **提示**
> 1. 使用 getConfig(key) / setConfig(key, value) 读写配置
> 2. 配置变更可通过生命周期钩子监听: @lifecycle.on("config.set")

---

## 函数列表


### `parse_bool_config(value: Any)`

解析配置中的布尔值

- **value** (`Any`): 配置值（可以是 bool, int, str 等）
**返回值** (`bool`): 解析后的布尔值

> **提示**
> 支持的值:
> - True: True, 1, "true", "True", "1", "yes", "Yes", "on", "On"
> - False: False, 0, "false", "False", "0", "no", "No", "off", "Off"

---


## 类列表


### `class ConfigManager`

ConfigManager 类提供相关功能。


#### 方法列表


##### `__init__(config_file: str = DEFAULT_CONFIG_FILE_PATH)`

初始化配置管理器

- **config_file** (`str`): 配置文件路径 (默认: "config/config.toml")

---


##### `_start_config_watcher()`

启动后台线程定期检查配置文件变化

当用户手动编辑 ``config.toml`` 时，后台线程检测到 mtime 变化后
自动重载缓存并发射 ``config.updated`` 生命周期事件。

> **内部方法**

---


##### `_watch_config_file()`

记录配置文件的当前 mtime，用于后续检测外部修改

> **内部方法**

---


##### `_migrate_config()`

迁移旧配置文件到新位置

从项目根目录的 config.toml 迁移到 config/config.toml

> **内部方法**

---


##### `_load_config()`

从文件加载配置到缓存

对加载失败按三种状态分别给出可操作的诊断信息：

- 文件缺失：正常首次启动，静默使用空配置
- TOML 语法错误：输出出错行号/列号与原因，保留上次有效缓存（不擦除）
- 权限/其他错误：输出明确原因，保留上次有效缓存（不擦除）

**返回值** (`bool`): 加载成功（含文件缺失）返回 True；解析/权限等错误返回 False

> **内部方法**

---


##### `_log_config_error(message: str, level: str = 'error')`

将配置加载诊断信息写入日志

> **内部方法**
统一处理 logger 尚未就绪的早期场景，失败时静默忽略。

- **message** (`str`): 日志消息
- **level** (`str`): 日志级别（``error``/``warning``/``debug``）

---


##### `_sort_config_dict(config_dict: dict[str, Any])`

递归地对配置字典按键排序

- **config_dict** (`dict`): 待排序的配置字典
**返回值** (`dict`): 排序后的配置字典

> **内部方法**

---


##### `_malformed_sentinel_path()`

跨进程告警冷却哨兵文件路径

位于配置文件同级目录下的隐藏文件，通过其 mtime 实现跨进程去重：
无论 ``epsdk run`` 子进程、``python main.py`` 直跑、还是多实例场景，
所有进程共享同一文件系统，自然协调告警频率。

> **内部方法**

---


##### `_flush_config()`

将待写入的配置刷新到文件

使用文件锁确保多线程环境下的原子性操作

> **内部方法**

---


##### `_register_atexit()`

注册 atexit 钩子，确保进程退出时未持久化的配置被 flush

> **内部方法**

---


##### `_flush_on_exit()`

atexit 回调：进程退出时强制刷新所有脏配置，并清理哨兵文件

> **内部方法**
哨兵文件（``.flush_malformed_cooldown``）是运行时跨进程去重的临时标记，

---


##### `_schedule_write()`

安排延迟写入

> **内部方法**

---


##### `_check_cache_validity()`

检查缓存有效性，必要时重新加载

同时检测配置文件是否被外部修改（手动编辑磁盘文件），
若文件 mtime 变化则自动重载。更新内容会在下一次
``getConfig`` 调用时生效，无需重启程序。

> **内部方法**

---


##### `_check_file_change()`

检测配置文件是否被外部程序或用户手动编辑

对比记录的 mtime 与当前文件 mtime，若不一致说明文件已被外部修改。

**返回值** (`bool`): 文件是否已变化

> **内部方法**

---


##### `_emit_config_updated(old_config: dict[str, Any])`

发射 ``config.updated`` 生命周期事件，通知适配器/模块配置已变更

用户手动编辑 ``config.toml`` 后，下一次 ``getConfig`` 调用会自动检测
到文件变更并触发此事件。适配器通过 ``on_config_update(old, new)`` 响应。

- **old_config** (`变更前的配置快照`): > **内部方法**

---


##### `getConfig(key: str, default: Any = None)`

获取配置项

- **key** (`str`): 配置键, 支持点分隔符如 "module.sub.key"
- **default** (`Any`): 默认值 (默认: None)
**返回值** (`Any`): 配置值

**示例**:
```python
>>> value = sdk.config.getConfig("ErisPulse.server.port", 8000)
```

---


##### `setConfig(key: str, value: Any, immediate: bool = False)`

设置配置项

- **key** (`str`): 配置键, 支持点分隔符如 "module.sub.key"
- **value** (`Any`): 配置值
- **immediate** (`bool`): 是否立即写入磁盘 (默认: False, 延迟写入)
**返回值** (`bool`): 操作是否成功

**示例**:
```python
>>> sdk.config.setConfig("ErisPulse.server.port", 9000)
>>> sdk.config.setConfig("ErisPulse.server.port", 9000, immediate=True)
```

---


##### `force_save()`

强制立即保存所有待写入的配置到磁盘

> **提示**
> 注意！除非您知道您在干什么，否则请勿直接强制保存！

---


##### `reload()`

重新从磁盘加载配置，丢弃所有未保存的更改

> **提示**
> reload 时，未持久化的配置项会被丢弃，并重新从配置文件中加载

---


##### `async agetConfig(key: str, default: Any = None)`

异步获取配置项

- **key** (`str`): 配置键, 支持点分隔符
- **default** (`Any`): 默认值
**返回值** (`Any`): 配置值

---


##### `async asetConfig(key: str, value: Any, immediate: bool = False)`

异步设置配置项

- **key** (`str`): 配置键
- **value** (`Any`): 配置值
- **immediate** (`bool`): 是否立即写入磁盘
**返回值** (`bool`): 操作是否成功

---


##### `async aforce_save()`

异步强制保存所有待写入的配置到磁盘

---


##### `async areload()`

异步重新从磁盘加载配置

---

