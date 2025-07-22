# 📦 `ErisPulse.Core.config` 模块

*自动生成于 2025-07-22 16:35:31*

---

## 模块概述

ErisPulse 配置中心

集中管理所有配置项，避免循环导入问题
提供自动补全缺失配置项的功能

---

## 🛠️ 函数

### `_ensure_config_structure`

确保配置结构完整，补全缺失的配置项

:param config: 当前配置
:return: 补全后的完整配置

---

### `get_config`

获取当前配置，自动补全缺失的配置项并保存

:return: 完整的配置字典

---

### `update_config`

更新配置，自动补全缺失的配置项

:param new_config: 新的配置字典
:return: 是否更新成功

---

### `get_server_config`

获取服务器配置，确保结构完整

:return: 服务器配置字典

---

### `get_logger_config`

获取日志配置，确保结构完整

:return: 日志配置字典

---


*文档最后更新于 2025-07-22 16:35:31*