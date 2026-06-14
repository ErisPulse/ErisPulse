# `ErisPulse.runtime.config_schema` 模块

---

## 模块概述


ErisPulse 适配器配置 Schema 模块

提供基于 dataclass 的配置定义，支持 TOML 注释生成和 WebUI 表单元数据。

> **提示**
> 1. 使用 AdapterConfig 作为单账户/全局配置基类
> 2. 使用 BotAccountConfig 作为多账户配置基类
> 3. 通过 field(metadata=...) 声明字段描述、控件类型等信息
> 4. 使用 dataclass_to_toml_with_comments() 生成带注释的配置模板
> 5. 使用 dict_to_dataclass() 从 TOML 字典填充 dataclass
> 6. 使用 validate_config() 校验配置实例

---

## 函数列表


### `dataclass_to_defaults_dict(config_class: type)`

从 dataclass 类生成默认值字典

:param config_class: dataclass 类
:return: 默认值字典

---


### `_type_default(type_hint)`

根据类型注解返回合理的默认值

---


### `_python_type_to_toml_type(type_hint)`

将 Python 类型注解转为 TOML 类型字符串

---


### `_format_toml_value(value)`

将 Python 值格式化为 TOML 值字符串

---


### `dataclass_to_toml_with_comments(config_class: type, existing_values: dict | None = None)`

将 dataclass class 转为带注释的 TOML 文本
用于首次写入配置文件时生成可读的配置模板

:param config_class: dataclass 类
:param existing_values: 已有的配置值（覆盖默认值）
:return: TOML 文本字符串

---


### `dict_to_dataclass(config_class: type, data: dict)`

从 TOML dict 填充 dataclass 实例

- 处理类型转换（str → int 等）
- 忽略 dataclass 中不存在的字段
- 使用 default/default_factory 填充缺失字段

:param config_class: dataclass 类
:param data: 字典数据（通常来自 TOML 解析）
:return: dataclass 实例

---


### `_coerce_value(value, type_hint)`

将值强制转换为目标类型

---


### `validate_config(instance)`

校验 dataclass 实例

- 检查 required 字段是否非空
- 返回错误信息列表（空列表表示通过）

:param instance: dataclass 实例
:return: 错误信息列表

---


### `_is_empty(value)`

判断值是否为空

---


### `get_config_schema(config_class: type)`

从 dataclass 生成 WebUI 可用的 JSON Schema

包含字段名、类型、描述、控件类型、分组、排序等

:param config_class: dataclass 类
:return: schema 字典

---


### `_get_field_default(f)`

获取字段的默认值

---


## 类列表


### `class I18nConfig`

国际化配置

控制框架的显示语言和翻译行为


### `class AdapterConfig`

适配器全局配置基类（单账户/无账户适配器使用）


### `class BotAccountConfig`

Bot 账户配置基类（多账户适配器使用）

