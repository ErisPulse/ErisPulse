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


### `_detect_windows_locale()`

通过 Windows API 检测用户 locale

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

手动设置语言

---


##### `get_language()`

获取当前语言

---


##### `reset_language()`

重置为自动检测，并重新检测环境

---


##### `t(key: str, default: str | None = None)`

获取 CLI 翻译文本

:param key: 翻译键
:param default: 默认值
:param kwargs: 格式化参数
:return: 翻译文本

---

