# `ErisPulse.runtime.frame_config` 模块

---

## 模块概述


ErisPulse 框架配置管理模块

提供默认配置定义及配置完整性管理功能

---

## 函数列表


### `_deep_merge(base: dict[str, Any], override: dict[str, Any])`

深度合并两个字典，override 中的值覆盖 base 中的对应值

- **base** (`基础字典`): - **override**: 覆盖字典
**返回值**: 合并后的新字典

---


### `_ensure_erispulse_config_structure(config_dict: dict[str, Any])`

确保 ErisPulse 配置结构完整，补全缺失的配置项

- **config_dict** (`当前配置`): **返回值**: 补全后的完整配置

---


### `get_erispulse_config()`

获取 ErisPulse 框架配置，自动补全缺失的配置项并保存

**返回值** (`完整的`): ErisPulse 配置字典

---


### `get_config(section: str | None = None)`

获取 ErisPulse 配置

- **section** (`配置部分名称（如`): "server"、"logger" 等），None 表示获取完整配置
**返回值**: 配置字典或配置项

---


### `update_erispulse_config(new_config: dict[str, Any])`

更新 ErisPulse 配置，自动补全缺失的配置项

- **new_config** (`新的配置字典`): **返回值**: 是否更新成功

---


### `get_server_config()`

获取服务器配置，确保结构完整

**返回值**: 服务器配置字典

---


### `get_logger_config()`

获取日志配置，确保结构完整

**返回值**: 日志配置字典

---


### `get_storage_config()`

获取存储模块配置

**返回值**: 存储配置字典

---


### `get_event_config()`

获取事件系统配置

**返回值**: 事件系统配置字典

---


### `get_framework_config()`

获取框架配置

**返回值**: 框架配置字典

---


### `get_i18n_config()`

获取国际化配置

**返回值**: 国际化配置字典

---


### `get_master_config()`

获取框架主人系统配置

**返回值**: 框架主人配置字典

---

