# `ErisPulse.Core.i18n.__init__` 模块

---

## 模块概述


ErisPulse 国际化模块

提供多语言支持，支持自动检测用户语言环境并按就近原则映射到支持的语言。

> **提示**
> 1. 框架内部和外部的模块都通过 i18n.t() 获取翻译文本
> 2. 支持的语言: zh-CN (简体中文), zh-TW (繁体中文), en (英文), ja (日文), ru (俄文)
> 3. 自动检测语言环境，也可手动设置: i18n.set_language("en")
> 4. 外部模块可通过 i18n.register() 注册自己的翻译

---

## 类列表


### `class I18nManager`

国际化管理器

负责语言检测、翻译查找和翻译注册。

语言检测优先级:
1. 手动通过 set_language() 设置的语言
2. 环境变量 ERISPULSE_LANG（临时覆盖）
3. 全局持久化设置（epsdk i18n 写入 ~/.erispulse/cli_state.json）
4. 配置项 ErisPulse.i18n.language（"auto" 表示自动检测）
5. 系统默认 locale (locale.getdefaultlocale)
6. 默认语言 (zh-CN)

就近映射规则:
- zh-TW, zh-HK, zh-MO, zh-Hant -> zh-TW (繁体中文)
- zh-CN, zh-SG, zh-MY, zh-Hans, zh 及其他 zh* -> zh-CN (简体中文)
- en, en-US, en-GB 及其他 en* -> en
- ja, ja-JP 及其他 ja* -> ja
- ru, ru-RU 及其他 ru* -> ru
- 其他未识别的语言 -> 默认语言


#### 方法列表


##### `_load_builtin_translations()`

加载框架内置翻译数据

> **内部方法**

---


##### `_resolve_nearest(locale_str: str)`

将任意 locale 字符串映射到最近的支持语言

:param locale_str: locale 字符串，如 "zh_TW.UTF-8", "en_US", "ja"
:return: 支持的语言代码

> **内部方法**

---


##### `_detect_language()`

自动检测用户语言环境（跨平台）

检测顺序:
Windows:
1. Windows API: GetUserDefaultLocaleName
2. 环境变量 LANGUAGE / LC_ALL / LC_MESSAGES / LANG
3. locale.getlocale() / locale.getdefaultlocale()

Unix/macOS:
1. 环境变量 LANGUAGE / LC_ALL / LC_MESSAGES / LANG
2. locale.getlocale() / locale.getdefaultlocale()

:return: 检测到的支持语言代码

> **内部方法**

---


##### `_resolve_windows_locale_name(locale_name: str)`

将 Windows locale 名称（如 'Chinese (Simplified)_China'）映射到支持语言

locale.getlocale() 在 Windows 上可能返回语言全称而非代码

:param locale_name: Windows locale 名称
:return: 支持的语言代码或 None

> **内部方法**

---


##### `_detect_windows_locale()`

通过 Windows API 检测用户默认 locale

使用 GetUserDefaultLocaleName / GetSystemDefaultLocaleName 获取
BCP 47 格式的 locale 名称（如 "zh-CN", "en-US"）

:return: locale 字符串或 None

> **内部方法**

---


##### `_get_effective_language()`

获取当前生效的语言

优先级: 手动设置 > ERISPULSE_LANG 环境变量 > 全局持久化设置 > 配置项 > 检测到的语言

配置值为 "auto" 时使用自动检测的语言。

> **内部方法**

---


##### `_global_state_path()`

全局状态文件路径

:return: Path 全局状态文件路径 (~/.erispulse/cli_state.json)

> **内部方法** 
与 CLI 的 i18n 共享同一文件，作为跨项目的语言持久化位置

---


##### `_load_global_language()`

从全局状态文件读取持久化的语言选择

:return: 语言代码或 None

> **内部方法** 
读取失败或未设置时返回 None，不影响后续优先级

---


##### `set_language(lang: str)`

手动设置当前语言，同时写入全局持久化

:param lang: 语言代码，如 "zh-CN", "en", "ja", "ru"
会自动按就近原则映射到支持的语言。
设置后立即生效，并写入 `~/.erispulse/cli_state.json`
跨所有项目生效（等效于 `epsdk i18n`）。
如需临时覆盖，使用环境变量 `ERISPULSE_LANG`

**示例**:
```python
>>> i18n.set_language("en")
>>> i18n.set_language("zh-TW")  # 繁体中文
```

---


##### `_persist_global_language(lang: str)`

将语言选择写入全局状态文件

:param lang: 已解析的语言代码

> **内部方法** 
与 CLI i18n 的 _persist_language 写入同一文件，覆盖 language 键

---


##### `get_language()`

获取当前生效的语言代码

:return: str 语言代码，如 "zh-CN", "en"

---


##### `get_supported_languages()`

获取所有支持的语言列表

:return: list[str] 支持的语言代码列表

---


##### `reset_language()`

重置为自动检测的语言（清除手动设置），并重新检测环境

---


##### `t(default: str | None = None)`

获取翻译文本

:param key: str 翻译键，如 "core.sdk.init.starting"
:param default: str 默认值，当翻译不存在时返回。默认为 None（返回 key 本身）
:param kwargs: 格式化参数，如 t("key", name="world") 会填充 {name}
:return: str 翻译后的文本

**示例**:
```python
>>> i18n.t("core.sdk.init.starting")
>>> i18n.t("core.adapter.load_failed", platform="OneBot")
>>> i18n.t("my_module.welcome", default="Welcome!")
```

---


##### `gettext(default: str | None = None)`

t() 的别名，兼容 gettext 风格

:param key: str 翻译键
:param default: str 默认值
:param kwargs: 格式化参数
:return: str 翻译后的文本

---


##### `_lookup(key: str, lang: str)`

在指定语言中查找翻译键

> **内部方法**

---


##### `register(lang: str, translations: dict[str, str], domain: str = 'app')`

注册翻译文本（供外部模块使用）

:param lang: str 语言代码，如 "en", "zh-CN"（会按就近原则映射）
:param translations: dict[str, str] 翻译键值对，如 {"my_module.welcome": "Welcome!"}
:param domain: str 域名，用于区分不同模块的翻译，默认 "app"

**示例**:
```python
>>> i18n.register("zh-CN", {
...     "mybot.welcome": "欢迎使用机器人",
...     "mybot.goodbye": "再见",
... }, domain="mybot")
>>> i18n.register("en", {
...     "mybot.welcome": "Welcome to the bot",
...     "mybot.goodbye": "Goodbye",
... }, domain="mybot")
```

---


##### `unregister_domain(domain: str)`

卸载指定域的所有翻译

:param domain: str 域名

**示例**:
```python
>>> i18n.unregister_domain("mybot")
```

---


##### `has_translation(key: str, lang: str | None = None)`

检查翻译键是否存在

:param key: str 翻译键
:param lang: str 指定语言，默认为当前语言
:return: bool 是否存在翻译

---


##### `reload()`

重新加载内置翻译并重新检测语言

---

