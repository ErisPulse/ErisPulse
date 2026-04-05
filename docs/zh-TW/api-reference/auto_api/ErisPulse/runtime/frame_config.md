# `ErisPulse.runtime.frame_config` 模块

---

## 模块概述


ErisPulse 框架配置管理模块

提供默认配置定义及配置完整性管理功能

---

## 函数列表


### `_ensure_erispulse_config_structure(config_dict: Dict[str, Any])`

确保 ErisPulse 配置结构完整，补全缺失的配置项

:param config_dict: 当前配置
:return: 补全后的完整配置

---


### `get_erispulse_config()`

获取 ErisPulse 框架配置，自动补全缺失的配置项并保存

:return: 完整的 ErisPulse 配置字典

---


### `get_config(section: Optional[str] = None)`

获取 ErisPulse 配置

:param section: 配置部分名称（如 "server"、"logger" 等），None 表示获取完整配置
:return: 配置字典或配置项

---


### `update_erispulse_config(new_config: Dict[str, Any])`

更新 ErisPulse 配置，自动补全缺失的配置项

:param new_config: 新的配置字典
:return: 是否更新成功

---


### `get_server_config()`

获取服务器配置，确保结构完整

:return: 服务器配置字典

---


### `get_logger_config()`

获取日志配置，确保结构完整

:return: 日志配置字典

---


### `get_storage_config()`

获取存储模块配置

:return: 存储配置字典

---


### `get_event_config()`

获取事件系统配置

:return: 事件系统配置字典

---


### `get_framework_config()`

获取框架配置

:return: 框架配置字典

---

