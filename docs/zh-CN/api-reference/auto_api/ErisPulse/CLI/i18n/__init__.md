# `ErisPulse.CLI.i18n.__init__` 模块

---

## 模块概述


ErisPulse CLI 国际化模块

独立于 Core i18n 的 CLI 国际化模块，完全解耦。

> **提示**
> 1. 与 Core i18n 完全独立，无任何依赖关系
> 2. 支持的语言: zh-CN, zh-TW, en, ja, ru
> 3. 外部模块通过 CLI.i18n.t() 获取 CLI 相关翻译

---

## 函数列表


### `_resolve_nearest(locale_str: str)`

将任意 locale 映射到最近的支持语言

---


### `_resolve_windows_locale_name(locale_name: str)`

将 Windows locale 名称（如 'Chinese (Simplified)_China'）映射到支持语言

locale.getlocale() 在 Windows 上可能返回语言全称而非代码

- **locale_name** (`Windows`): locale 名称
**返回值** (`支持的语言代码或`): None

---


### `_detect_windows_locale()`

通过 Windows API 检测用户默认 locale

使用 GetUserDefaultLocaleName / GetLocaleInfoW 获取
BCP 47 格式的 locale 名称（如 "zh-CN", "en-US"）

**返回值** (`locale`): 字符串或 None

---


### `_detect_language()`

自动检测用户语言环境

---


## 类列表


### `class CliI18n`

CLI 国际化管理器

与 Core i18n 完全独立，专门处理 CLI 命令的翻译文本。


#### 方法列表


##### `_load_builtin()`

加载内置 CLI 翻译

---


##### `set_language(lang: str)`

手动设置语言并持久化

---


##### `get_language()`

获取当前语言

---


##### `reset_language()`

重置为自动检测，并重新检测环境

---


##### `_state_path()`

获取 CLI 状态文件路径

**返回值** (`Path`): 状态文件路径 (~/.erispulse/cli_state.json)

---


##### `_load_state()`

加载 CLI 持久化状态

> **内部方法**

**返回值** (`dict`): 状态字典，读取失败时返回空字典

---


##### `_save_state(state: dict)`

保存 CLI 持久化状态

> **内部方法**

- **state** (`dict`): 状态字典

---


##### `_persist_language(lang: str)`

持久化语言选择到状态文件

> **内部方法**

- **lang** (`str`): 语言代码

---


##### `get_lang_hint_shown_count()`

获取语言提示已显示次数

**返回值** (`int`): 已显示次数

---


##### `increment_lang_hint()`

语言提示显示次数 +1 并持久化

**返回值** (`int`): 更新后的已显示次数

---


##### `t(key: str, default: str | None = None)`

获取 CLI 翻译文本

- **key** (`翻译键`): - **default**: 默认值
- **kwargs** (`格式化参数`): **返回值**: 翻译文本

---


##### `t_in(target_lang: str, key: str, default: str | None = None)`

获取指定语言的翻译文本（用于多语言同时展示）

- **target_lang** (`str`): 目标语言代码
- **key** (`str`): 翻译键
- **default** (`str`): 默认值 (默认: None)
- **kwargs** (`格式化参数`): **返回值** (`str`): 翻译文本

---

