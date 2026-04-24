# `ErisPulse.Core.config` 模块

---

## 模块概述


ErisPulse 配置中心

集中管理所有配置项，避免循环导入问题
提供自动补全缺失配置项的功能
添加内存缓存和延迟写入机制以提高性能

---

## 函数列表


### `parse_bool_config(value: Any)`

解析配置中的布尔值

:param value: 配置值（可以是 bool, int, str 等）
:return: 解析后的布尔值

支持的值：
- True: True, 1, "true", "True", "1", "yes", "Yes", "on", "On"
- False: False, 0, "false", "False", "0", "no", "No", "off", "Off"

---


## 类列表


### `class ConfigManager`

ConfigManager 类提供相关功能。


#### 方法列表


##### `_migrate_config()`

迁移旧配置文件到新位置
从项目根目录的 config.toml 迁移到 config/config.toml

---


##### `_load_config()`

从文件加载配置到缓存

---


##### `_sort_config_dict(config_dict: dict[str, Any])`

递归地对配置字典进行排序，确保同一模块的配置项排列在一起
:param config_dict: 待排序的配置字典
:return: 排序后的配置字典

---


##### `_flush_config()`

将待写入的配置刷新到文件

使用文件锁确保多线程环境下的原子性操作

---


##### `_schedule_write()`

安排延迟写入

线程安全：使用锁保护 Timer 的取消和创建

---


##### `_check_cache_validity()`

检查缓存有效性，必要时重新加载

---


##### `getConfig(key: str, default: Any = None)`

获取模块/适配器配置项（优先从缓存获取）
:param key: 配置项的键(支持点分隔符如"module.sub.key")
:param default: 默认值
:return: 配置项的值

---


##### `setConfig(key: str, value: Any, immediate: bool = False)`

设置模块/适配器配置（缓存+延迟写入）
:param key: 配置项键名(支持点分隔符如"module.sub.key")
:param value: 配置项值
:param immediate: 是否立即写入磁盘（默认为False，延迟写入）
:return: 操作是否成功

---


##### `force_save()`

强制立即保存所有待写入的配置到磁盘

---


##### `reload()`

重新从磁盘加载配置，丢弃所有未保存的更改

---

