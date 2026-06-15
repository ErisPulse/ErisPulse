# `ErisPulse.CLI.commands.language` 模块

---

## 模块概述


Language 命令实现

查看与切换 CLI 显示语言

---

## 类列表


### `class LanguageCommand(Command)`

language 命令

查看/切换 CLI 显示语言


#### 方法列表


##### `_interactive_select(current: str)`

交互式选择语言

- **current** (`str`): 当前语言代码

---


##### `_show_languages(current: str)`

列出所有支持的语言

- **current** (`str`): 当前语言代码

---


##### `_normalize_lang(lang: str)`

将用户输入的语言标识归一化为支持的语言代码

- **lang** (`str`): 用户输入（如 zh、zh-CN、en、ja、ru 等）
**返回值** (`str | None`): 归一化后的语言代码，不支持时返回 None

---

