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


### `_iter_leaf_diff(old: dict[str, Any], new: dict[str, Any], prefix: str = '')`

递归比较两棵配置字典，返回新增或值变化的叶子键（点分路径）

仅收集 new 中相对 old 发生变化的叶子，用于把整棵配置的持久化
拆分为细粒度叶子写入，避免整棵覆盖导致用户热更新丢失。

> **内部方法**
语义：只增改、不处理删除（本模块的合并语义仅新增/覆盖叶子值）。

- **old** (`变更前的配置字典`): - **new**: 变更后的配置字典
- **prefix** (`递归时的路径前缀`): **返回值** (`(点分路径, 叶子值), ...`):

---


### `_ensure_erispulse_config_structure(config_dict: dict[str, Any])`

确保 ErisPulse 配置结构完整，补全缺失的配置项

- **config_dict** (`当前配置`): **返回值**: 补全后的完整配置

---


### `get_erispulse_config()`

获取 ErisPulse 框架配置，自动补全缺失的配置项并保存

**返回值** (`完整的`): ErisPulse 配置字典

---


### `_apply_env_overrides(config: dict[str, Any], root: str = CONFIG_ROOT_KEY)`

> **内部方法**
递归对配置字典应用环境变量覆盖

命名规则：``ErisPulse.server.port`` → ``ERISPULSE_SERVER_PORT``
（将点路径大写、``.`` 替换为 ``_``）。仅覆盖叶子值，按原值类型做 coerce。

---


### `_coerce_env_value(original: Any, env_str: str)`

按原值类型把环境变量字符串转换为对应 Python 类型

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

