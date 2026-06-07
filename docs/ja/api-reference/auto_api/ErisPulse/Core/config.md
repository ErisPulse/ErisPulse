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

:param value: Any 配置值（可以是 bool, int, str 等）
:return: bool 解析后的布尔值

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

:param config_file: str 配置文件路径 (默认: "config/config.toml")

---


##### `_migrate_config()`

迁移旧配置文件到新位置

从项目根目录的 config.toml 迁移到 config/config.toml

> **内部方法**

---


##### `_load_config()`

从文件加载配置到缓存

> **内部方法**

---


##### `_sort_config_dict(config_dict: dict[str, Any])`

递归地对配置字典进行排序

:param config_dict: dict 待排序的配置字典
:return: dict 排序后的配置字典

> **内部方法**

---


##### `_flush_config()`

将待写入的配置刷新到文件

使用文件锁确保多线程环境下的原子性操作

> **内部方法**

---


##### `_schedule_write()`

安排延迟写入

> **内部方法**

---


##### `_check_cache_validity()`

检查缓存有效性，必要时重新加载

> **内部方法**

---


##### `getConfig(key: str, default: Any = None)`

获取配置项

:param key: str 配置键, 支持点分隔符如 "module.sub.key"
:param default: Any 默认值 (默认: None)
:return: Any 配置值

**示例**:
```python
>>> value = sdk.config.getConfig("ErisPulse.server.port", 8000)
```

---


##### `setConfig(key: str, value: Any, immediate: bool = False)`

设置配置项

:param key: str 配置键, 支持点分隔符如 "module.sub.key"
:param value: Any 配置值
:param immediate: bool 是否立即写入磁盘 (默认: False, 延迟写入)
:return: bool 操作是否成功

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

