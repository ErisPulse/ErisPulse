# `ErisPulse.Core.config` 模块

<sup>更新时间: 2025-12-21 14:28:48</sup>

---

## 模块概述


ErisPulse 配置中心

集中管理所有配置项，避免循环导入问题
提供自动补全缺失配置项的功能
添加内存缓存和延迟写入机制以提高性能

---

## 类列表

### `class ConfigManager`

    ConfigManager 类提供相关功能。

    
#### 方法列表

##### `_load_config()`

    从文件加载配置到缓存

    ---
    
##### `_flush_config()`

    将待写入的配置刷新到文件

    ---
    
##### `_schedule_write()`

    安排延迟写入

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
    
<sub>文档最后更新于 2025-12-21 14:28:48</sub>