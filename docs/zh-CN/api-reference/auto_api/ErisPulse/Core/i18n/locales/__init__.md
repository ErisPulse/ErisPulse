# `ErisPulse.Core.i18n.locales.__init__` 模块

---

## 模块概述


ErisPulse 内置翻译数据包

按语言组织翻译数据，每种语言对应一个模块文件。

> **内部方法**
框架内置翻译，外部模块请通过 i18n.register() 注册自己的翻译。

---

## 函数列表


### `get_translations(lang_code: str)`

获取指定语言的内置翻译数据

- **lang_code** (`语言代码，如`): "zh-CN", "en"
**返回值** (`dict[str,`): str] 翻译键值对

> **内部方法**

---

