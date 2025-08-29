# `ErisPulse.Core.config` 模块

<sup>更新时间: 2025-08-30 06:55:36</sup>

---

## 模块概述


ErisPulse 配置中心

集中管理所有配置项，避免循环导入问题
提供自动补全缺失配置项的功能

---

## 类列表

### `class ConfigManager`

    ConfigManager 类提供相关功能。

    
#### 方法列表

##### `getConfig(key: str, default: Any = None)`

    获取模块/适配器配置项
:param key: 配置项的键(支持点分隔符如"module.sub.key")
:param default: 默认值
:return: 配置项的值

    ---
    
##### `setConfig(key: str, value: Any)`

    设置模块/适配器配置
:param key: 配置项键名(支持点分隔符如"module.sub.key")
:param value: 配置项值
:return: 操作是否成功

    ---
    
<sub>文档最后更新于 2025-08-30 06:55:36</sub>