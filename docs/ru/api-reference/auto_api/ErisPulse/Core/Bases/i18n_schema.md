# `ErisPulse.Core.Bases.i18n_schema` 模块

---

## 模块概述


ErisPulse i18n 键声明 Schema 模块

提供基于类属性的 i18n 翻译键声明，支持框架自动注册。
适用于适配器、模块、外部项目等任何需要批量声明翻译键的场景。

> **提示**
> 1. 继承 BaseI18n 基类，通过类属性声明翻译键（命名与 BaseConfig 对齐）
> 2. 每个属性对应一个翻译键，属性名（加模块前缀）作为键路径
> 3. 也可通过 I18nKey(key=...) 显式指定完整键路径
> 4. 框架在加载模块/适配器时自动注册所有声明的翻译键
> 5. 配合 BaseModule.I18nClass / BaseAdapter.I18nClass 使用，无需手动调用 i18n.register()
> 6. ``default`` 是语言无关的兜底文本，不会注册到任何语言；
> 要让翻译生效，必须显式传入至少一个语言参数（``zh_CN=`` / ``en=`` 等）

---

## 类列表


### `class I18nKey`

单个 i18n 翻译键的声明

- **default** (`兜底文本（语言无关）。当所有已注册语言均未覆盖此键时，`): 作为最后的显示文本。**不会注册到任何语言**。
                各国开发者可使用自己母语填写此字段，框架不做任何假设。
- **key** (`完整的翻译键路径（如`): ``"mymodule.welcome"``）。
            省略时使用属性名 + 调用方提供的前缀自动生成。
- **zh_CN** (`简体中文翻译`): - **zh_TW**: 繁体中文翻译
- **en** (`英文翻译`): - **ja**: 日文翻译
- **ru** (`俄文翻译`): 使用示例::

    from ErisPulse.Core.Bases import BaseI18n, I18nKey

    class MyModule(BaseModule):
        class I18nClass(BaseI18n):
            # 自动生成键: mymodule.welcome
            welcome: I18nKey = I18nKey(
                default="Welcome",        # 语言无关的兜底
                zh_CN="欢迎",
                zh_TW="歡迎",
                en="Welcome",
                ja="ようこそ",
                ru="Добро пожаловать",
            )

            # 显式指定键路径
            deep: I18nKey = I18nKey(
                key="mymodule.deep.nested.key",
                default="Default text",
                zh_CN="默认文本",
                zh_TW="預設文本",
                en="Default text",
                ja="デフォルトテキスト",
                ru="Текст по умолчанию",
            )


#### 方法列表


##### `explicit_key()`

获取显式指定的键路径（如有）

**返回值** (`显式键名字符串，或`): None 表示使用前缀+属性名自动生成

---


### `class BaseI18n`

i18n 键声明集合的基类

命名与 :class:`BaseConfig` 对齐：用户通过嵌套类继承此类声明翻译键，
框架会在模块/适配器加载时自动调用 :meth:`register` 将所有声明的翻译键
注册到 i18n 系统。

> **提示**
> 1. 类属性必须是 :class:`I18nKey` 实例，否则被忽略
> 2. 属性名以下划线开头的会被忽略（视为私有/内部）
> 3. 自动生成的键路径为 ``<前缀><属性名>``，前缀通常是模块名 + ``.``
> 4. 通过 :class:`I18nKey` 的 ``key=`` 参数可显式指定完整键路径
> 5. 同一 domain 可被多次注册，键值会被覆盖更新
> 6. ``I18nKey.default`` 是语言无关的兜底文本，不参与注册；
> 实际翻译必须通过 ``zh_CN=`` / ``en=`` 等参数显式声明

使用示例::

    from ErisPulse.Core.Bases import BaseModule, BaseI18n, I18nKey

    class MyModule(BaseModule):
        class I18nClass(BaseI18n):
            welcome: I18nKey = I18nKey(
                default="Welcome",
                zh_CN="欢迎",
                zh_TW="歡迎",
                en="Welcome",
                ja="ようこそ",
                ru="Добро пожаловать",
            )
            goodbye: I18nKey = I18nKey(
                default="Bye",
                zh_CN="再见",
                zh_TW="再見",
                en="Goodbye",
                ja="さようなら",
                ru="До свидания",
            )

也可独立使用（手动注册）::

    class MyKeys(BaseI18n):
        hello: I18nKey = I18nKey(
            default="Hello",
            zh_CN="你好",
            zh_TW="你好",
            en="Hello",
            ja="こんにちは",
            ru="Привет",
        )

    MyKeys.register(prefix="myapp.", domain="myapp")


#### 方法列表


##### `_collect_keys()`

收集类中所有声明的 I18nKey

遍历 MRO（含父类继承），收集所有非下划线开头的 I18nKey 类属性。
子类同名属性会覆盖父类（与 Python 属性查找语义一致）。

**返回值** (```{属性名:`): I18nKey 实例}`` 字典

---


##### `register(prefix: str = '', domain: str = 'app')`

注册所有翻译键到 i18n 系统

仅注册 :class:`I18nKey` 中显式声明的语言翻译。
``default`` 字段是语言无关的兜底文本，不参与注册。

- **prefix** (`键名前缀（通常是模块名`): + ``.``，如 ``"mymodule."``）。
              仅对未显式指定 ``key`` 的翻译键生效。
- **domain** (`i18n`): 域标识，用于卸载时按域统一清理。
              建议使用模块名。
**返回值** (`注册的翻译条目总数`): 
**示例**:
```python
>>> class MyKeys(BaseI18n):
...     hello: I18nKey = I18nKey(
...         default="Hello",
...         zh_CN="你好",
...         en="Hello",
...     )
>>> MyKeys.register(prefix="myapp.", domain="myapp")
2  # zh-CN + en
```

---

