# `ErisPulse.CLI.utils.scaffold_text` 模块

---

## 模块概述


脚手架模板多语言文案

`epsdk create` 生成的模块/适配器模板里的注释、docstring 与日志消息
跟随脚手架用户的语言。本模块用独立类集中维护这些文案，避免散落在
``create.py`` 模板字符串里难以维护。

语言代码沿用 CLI i18n 的 5 种：zh-CN / zh-TW / en / ja / ru。
用户语言未知时回退英文（en）。

> **内部方法**

---

## 类列表


### `class ScaffoldText`

脚手架模板多语言文案

按用户语言提供模板注释 / docstring / 日志文本。缺失语言回退英文。
文案键集中定义在模块级 ``_TRANSLATIONS``，新增语言只需补充对应条目。


#### 方法列表


##### `__init__(lang: str | None = None)`

- **lang** (`str|None`): 目标语言代码；None 时自动检测 CLI 当前语言

---


##### `_detect_lang()`

从 CLI i18n 检测当前语言，失败回退默认

---


##### `t(key: str)`

获取指定文案键在目标语言下的文本

- **key** (`文案键（见`): ``_TRANSLATIONS`` / ``_EN_FALLBACK``）
- **kwargs** (`填充占位符（如`): ``name=``/``event=``/``content=``）
**返回值**: 文本；未知键返回键名

---


##### `all()`

返回当前语言下所有文案（未格式化）

---

