# `ErisPulse.Core.Bases.config_schema` 模块

---

## 模块概述


ErisPulse 通用配置 Schema 模块

提供基于 dataclass 的配置定义，支持 TOML 注释生成和多语言 WebUI 表单元数据。

适用于适配器、模块、外部项目等任何需要声明式配置的场景。

> **提示**
> 1. 使用 BaseConfig 作为单账户/全局配置基类（AdapterConfig 为其别名，保持兼容）
> 2. 使用 BotAccountConfig 作为多账户配置基类
> 3. 通过 field(metadata=...) 声明字段描述、控件类型等信息
> 4. description 支持 i18n 多语言：{"i18n": "key.path", "default": "默认文本"}
> 5. 使用 dataclass_to_toml_with_comments() 生成带注释的配置模板
> 6. 使用 dict_to_dataclass() 从 TOML 字典填充 dataclass
> 7. 使用 validate_config() 校验配置实例
> 8. 使用 get_config_schema() 生成 WebUI JSON Schema（含 i18n 支持）

---

## 函数列表


### `_resolve_description_text(meta: Mapping | None)`

从 metadata 提取人类可读的描述文本

用于 TOML 注释生成、校验错误信息等不需要多语言的场景。
description 可以是:
  - 普通字符串: "账户备注名称"
  - i18n 字典:   {"i18n": "module.field.desc", "default": "账户备注名称"}

- **meta** (`field.metadata`): 字典
**返回值**: 人类可读的描述字符串

---


### `_resolve_description_schema(meta: Mapping | None)`

从 metadata 提取 schema 可用的描述信息

- 普通字符串原样返回（WebUI 直接展示）
- i18n 字典原样返回（WebUI 根据 language 查找翻译）

- **meta** (`field.metadata`): 字典
**返回值** (`字符串或`): i18n 描述字典

---


### `_get_ui_meta(meta: Mapping | None)`

从 metadata 获取 UI 配置（兼容新旧键名）

优先级: "ui"（新） > "webui"（旧，保留兼容）

- **meta** (`field.metadata`): 字典
**返回值** (`UI`): 元数据字典

---


### `_type_default(type_hint)`

根据类型注解返回合理的默认值

> **内部方法**

- **type_hint** (`Python`): 类型注解
**返回值** (`对应类型的默认值（int→0,`): float→0.0, bool→False, list→[], dict→{}, str→""）

---


### `_python_type_to_toml_type(type_hint)`

将 Python 类型注解转为 TOML 类型字符串

> **内部方法**

- **type_hint** (`Python`): 类型注解
**返回值** (`TOML`): 类型名（integer/float/boolean/array/table/string）

---


### `_format_toml_value(value)`

将 Python 值格式化为 TOML 值字符串

> **内部方法**

- **value** (`Python`): 值（str/int/float/bool/list/dict 等）
**返回值** (`TOML`): 格式的字符串

---


### `_get_field_default(f)`

获取 dataclass 字段的默认值

> **内部方法**

- **f** (`dataclass`): Field 对象
**返回值** (`字段的默认值（优先`): default，其次 default_factory，最后根据类型推断）

---


### `_is_empty(value)`

判断值是否为空（None / 空字符串 / 空列表 / 空字典）

> **内部方法**

- **value** (`任意值`): **返回值**: 是否为空

---


### `_coerce_value(value, type_hint)`

将值强制转换为目标类型（如 str→int、str→bool）

> **内部方法**

- **value** (`原始值`): - **type_hint**: 目标类型注解
**返回值**: 转换后的值（转换失败时返回原值）

---


### `dataclass_to_defaults_dict(config_class: type)`

从 dataclass 类生成默认值字典

- **config_class** (`dataclass`): 类
**返回值**: 默认值字典

---


### `dataclass_to_toml_with_comments(config_class: type, existing_values: dict | None = None)`

将 dataclass class 转为带注释的 TOML 文本

用于首次写入配置文件时生成可读的配置模板。
description 若为 i18n 字典，则使用其 default/fallback 文本。

- **config_class** (`dataclass`): 类
- **existing_values** (`已有的配置值（覆盖默认值）`): **返回值** (`TOML`): 文本字符串

---


### `dict_to_dataclass(config_class: type, data: dict)`

从 TOML dict 填充 dataclass 实例

- 处理类型转换（str → int 等）
- 忽略 dataclass 中不存在的字段
- 使用 default/default_factory 填充缺失字段

- **config_class** (`dataclass`): 类
- **data** (`字典数据（通常来自`): TOML 解析）
**返回值** (`dataclass`): 实例

---


### `validate_config(instance)`

校验 dataclass 实例

- 检查 required 字段是否非空
- 返回错误信息列表（空列表表示通过）
- description 若为 i18n 字典，错误信息使用其 fallback/default 文本

- **instance** (`dataclass`): 实例
**返回值**: 错误信息列表

---


### `get_config_schema(config_class: type)`

从 dataclass 生成 WebUI 可用的 JSON Schema

包含字段名、类型、描述（支持 i18n）、控件类型、分组、排序等。
description 若为 i18n 字典则原样透传，WebUI 根据语言键查找翻译。

- **config_class** (`dataclass`): 类
**返回值** (`schema`): 字典

---


### `register_config_i18n(config_class: type, lang: str, translations: dict[str, str] | None = None, domain: str = 'config')`

将配置类的字段描述注册到 i18n 系统

遍历 config_class 的所有字段，提取 description 中的 i18n 键，
调用 i18n.register() 注册翻译。

两种用法：
1. 自动模式（translations=None）：将字段 description.default 注册到指定 lang
   （description.default 是语言无关的兜底文本，调用者自行决定注册到哪种语言）
2. 手动模式：提供 translations 字典（{i18n_key: translated_text}）

使用示例::

    # 将默认文本注册为中文翻译
    register_config_i18n(MyAdapterConfig, "zh-CN")

    # 将默认文本注册为英文翻译
    register_config_i18n(MyAdapterConfig, "en")

    # 手动提供英文翻译（覆盖默认文本）
    register_config_i18n(MyAdapterConfig, "en", {
        "my_adapter.endpoint": "API Endpoint",
        "my_adapter.token": "Platform Token",
    })

- **config_class** (`dataclass`): 配置类
- **lang** (`语言代码（如`): "zh-CN", "en"）
- **translations** (`手动提供的翻译字典，None`): 则自动提取
- **domain** (`i18n`): 域标识，默认 "config"
**返回值**: 注册的翻译条目数

---


### `_resolve_i18n_text(value, i18n_mgr)`

解析单个值的 i18n 文本

接受纯字符串（原样返回）或 i18n 字典（解析为当前语言文本）。

- **value** (`原始值（str`): 或 {"i18n": ..., "default": ...}）
- **i18n_mgr** (`I18nManager`): 实例
**返回值**: 解析后的字符串

---


### `resolve_config_schema(config_class: type, resolve_i18n: bool = True)`

获取配置 Schema，可选地将所有 i18n 文本字段解析为当前语言的文本

与 get_config_schema() 的区别：
- 当 resolve_i18n=True 时，所有用户可见文本字段（description、options label、
  placeholder、group_labels）为解析后的字符串（适合直接展示）
- 当 resolve_i18n=False 时，等同于 get_config_schema()（透传 i18n 字典）

支持的 i18n 字段（均采用 ``{"i18n": "key", "default": "文本"}`` 格式）：
- ``description``: 字段描述
- ``options[].label``: select 控件选项标签
- ``placeholder``: 输入框占位符
- ``group_labels``: 分组显示名（通过 ``_schema_meta["group_labels"]`` 声明）

纯字符串值会被原样透传（向后兼容）。

- **config_class** (`dataclass`): 配置类
- **resolve_i18n** (`是否将`): i18n 文本解析为当前语言
**返回值** (`schema`): 字典

---


## 类列表


### `class BaseConfig`

通用配置基类

适用于任何模块/项目的单账户或全局配置场景。
继承此类即可获得 TOML 序列化、校验、WebUI Schema 等能力。

使用示例::

    @dataclass
    class MyModuleConfig(BaseConfig):
        api_key: str = field(
            default="",
            metadata={
                "description": {"i18n": "my_module.api_key", "default": "API 密钥"},
                "required": True,
                "secret": True,
                "ui": {"widget": "password", "group": "connection", "order": 1},
            },
        )


### `class BotAccountConfig`

多账户配置基类

适用于需要管理多个账户的场景（如多 Bot）。
继承此类自动获得 enabled/name 基础字段。

使用示例::

    @dataclass
    class MyBotConfig(BotAccountConfig):
        bot_id: str = field(
            default="",
            metadata={
                "description": {"i18n": "my_adapter.bot_id", "default": "Bot ID"},
                "required": True,
                "ui": {"widget": "text", "group": "basic", "order": 1},
            },
        )


### `class I18nConfig`

国际化配置

控制框架的显示语言和翻译行为

