# `ErisPulse.CLI.utils.config_wizard` 模块

---

## 模块概述


ErisPulse CLI 配置向导共享工具

基于声明式配置（ConfigClass / AccountConfigClass）生成 schema 驱动的
交互式表单，供 ``epsdk config`` 命令与 install / init 安装后衔接复用。

模块与适配器共用同一套渲染逻辑；适配器额外包含多账户（bot 账户）配置环节。

> **提示**
> 1. load_config_targets() 发现所有可配置目标（entry-points + 本地 plugins/）
> 2. get_target_status() 检查目标的配置状态（未配置/必填缺失/就绪）
> 3. run_wizard() 对单个目标运行交互式配置向导并写入 config.toml
> 4. post_install_configure() 在安装包后衔接配置引导

---

## 函数列表


### `_normalize_dist_name(name: str | None)`

按 PEP 503 规范化 PyPI 发行包名称

大小写不敏感，``-`` / ``_`` / ``.`` 连续序列统一为单个 ``-``，
用于安装包名与 entry-point 所属包名的宽松匹配。

- **name** (`原始包名`): **返回值**: 规范化后的包名

---


### `is_interactive()`

检测当前是否处于可交互的终端环境

**返回值** (`stdin`): 与 stdout 均为 TTY 时返回 True

---


### `_resolve_adapter_config_key(cls)`

在不实例化适配器类的前提下解析其配置键

默认实现（继承自 BaseAdapter）返回类名；子类覆写 ``_get_config_key``
时以伪 self 对象调用（大多数覆写是 self 属性的纯函数），
调用失败则回退类名。

- **cls** (`适配器类`): **返回值**: 配置键名字符串

---


### `_target_from_class(kind: str, name: str, cls, package = None, source = 'entrypoint')`

从目标类构造 ConfigTarget（读取类属性声明，不实例化）

- **kind** (`目标类型`): - **name**: 目标名
- **cls** (`适配器/模块类`): - **package**: 所属包名
- **source** (`来源标识`): **返回值** (`ConfigTarget；类不合法时返回`): None

---


### `_plugin_module_class(module_obj)`

从本地插件模块对象中提取模块类

- **module_obj** (`插件模块对象（声明`): ``moduleInfo`` 字典）
**返回值** (`模块类；未声明或类型不合法时返回`): None

---


### `load_config_targets()`

发现当前环境中所有可配置目标

覆盖 entry-points（``erispulse.adapter`` / ``erispulse.module`` 组）
与本地插件目录（``plugins/``）。加载失败的条目跳过并提示。

**返回值** (`ConfigTarget`): 列表（含未声明配置的目标，调用方按需过滤）

---


### `get_target_status(target: ConfigTarget, config = None)`

检查目标的配置状态

- **target** (`ConfigTarget`): - **config**: ConfigManager 实例（None 时使用全局单例）
**返回值** (`(状态,`): 错误列表)。状态取值：
    - ok：已配置且校验通过
    - incomplete：必填项缺失或校验失败
    - unconfigured：配置键不存在（从未生成）
    - none：目标未声明任何配置

---


### `_sort_fields(schema_fields: dict)`

按 schema 的 order 元数据稳定排序字段（未声明 order 的保持声明顺序靠前）

- **schema_fields** (`get_config_schema()["fields"]`): 字典
**返回值** (`(字段名,`): 字段 schema) 列表

---


### `_coerce_scalar(raw: str, type_name: str)`

将用户输入字符串转换为目标类型的标量值

- **raw** (`原始输入`): - **type_name**: TOML 类型名（integer/float/boolean/string）
**返回值** (`转换后的值；无法转换时抛出`): ValueError

---


### `_plain_options(options: list)`

提取 select 选项的纯值列表（兼容字符串与 {label, value} 字典两种格式）

- **options** (`schema`): 中的 options 列表
**返回值**: 选项值列表

---


### `_option_label(option)`

获取 select 选项的显示标签

- **option** (`单个选项（字符串或`): {label, value} 字典）
**返回值**: 标签字符串

---


### `_with_source(label: str, source: str)`

在 label 行尾追加来源标注（当前值 / 默认值）

- **label** (`已构造的字段标签行`): - **source**: 来源标注文本（空则不追加）
**返回值**: 带标注的显示文本

---


### `_source_label(has_value: bool, value, bool_text: str = '')`

生成字段值来源标注文本（当前值 / 默认值）

- **has_value** (`字段是否已有当前配置值（存储中存在）`): - **value**: 值（布尔传入 bool_text 已本地化）
- **bool_text** (`布尔值本地化"是/否"文本`): **返回值**: 标注字符串；无值则返回空串

---


### `_prompt_field(name: str, field_schema: dict, current, has_value: bool = False)`

交互式询问单个配置字段的值

按 widget / 类型渲染控件（password / select / switch / 数值 / 文本），
输入即时校验（options / min / max / required），非法时重新询问；
空输入表示保留当前值（secret 字段不回显当前值）。
值来源（已有配置 / schema 默认）以 ``(当前：x)`` / ``(默认：x)`` 标注。

- **name** (`字段名`): - **field_schema**: 字段 schema（来自 resolve_config_schema）
- **current** (`当前值（默认值兜底为`): schema default）
- **has_value** (`字段是否已有当前配置值（决定标注"当前"/"默认"）`): **返回值**: 用户确认后的字段值

---


### `_values_equal(a, b)`

宽松比较两个标量是否相等（容忍 int/str 形式差异）

- **a** (`值`): a
- **b** (`值`): b
**返回值**: 是否相等

---


### `fill_config_fields(config_class, current_values: dict)`

渲染整个配置类的表单并收集用户输入

- **config_class** (`dataclass`): 配置类
- **current_values** (`当前存储的配置字典（作为各字段初值）`): **返回值**: 收集后的配置字典

---


### `_validate_dataclass(config_class, data: dict)`

校验字典是否能通过配置类的完整约束

- **config_class** (`dataclass`): 配置类
- **data** (`配置字典`): **返回值**: 错误列表（空列表表示通过）

---


### `_prompt_account_name(existing: dict, default: str = '')`

询问新的账户名（非空且不与现有账户重名）

- **existing** (`现有账户字典`): - **default**: 默认账户名
**返回值** (`合法账户名；用户中断返回`): None

---


### `_pick_account_name(names: list[str])`

从账户名列表中交互选择一个账户

显示 ``1. xxx`` 编号列表，输入序号选择；空输入返回（None），
非法序号重新询问。

- **names** (`账户名列表`): **返回值** (`选中的账户名；用户留空/中断返回`): None

---


### `_resolve_accounts_key(target: ConfigTarget, config)`

解析适配器多账户配置的存储键

新键为 ``<config_key>.accounts``；旧版使用 ``<config_key>.bots``，
仅当新键不存在而旧键存在时回退（兼容既有 config.toml）。

- **target** (`适配器`): ConfigTarget
- **config** (`ConfigManager`): 实例
**返回值**: 账户配置存储键

---


### `_run_accounts_section(target: ConfigTarget, config)`

运行多账户配置环节（添加 / 编辑 / 删除循环）

- **target** (`适配器`): ConfigTarget
- **config** (`ConfigManager`): 实例
**返回值** (`编辑后的账户字典`): {账户名: 字段字典}

---


### `run_wizard(target: ConfigTarget, config = None)`

对单个目标运行交互式配置向导

流程：同步字段 i18n 语言 → 就绪提示 → 全局配置表单 →（适配器）
账户管理环节 →（适配器）启用开关 → 整体校验 → 写入 config.toml
（立即落盘），末尾统一打印保存结果；全局表单校验失败且放弃重填
时直接中止（不写入任何配置）。

- **target** (`ConfigTarget`): - **config**: ConfigManager 实例（None 时使用全局单例）
**返回值**: 是否成功写入了配置

---


### `post_install_configure(dist_names: list[str] | None, config = None)`

安装完成后衔接配置向导

刷新 entry-points 缓存后，按 PyPI 名称规范化匹配刚安装的包，
仅对包含配置声明的目标逐个询问是否立即配置。非交互环境跳过并
打印 ``epsdk config <name>`` 指引。

- **dist_names** (`本次成功安装的发行包名列表`): - **config**: ConfigManager 实例（None 时使用全局单例）
- **interactive** (`是否交互（None`): 时自动检测 TTY）

---


## 类列表


### `class ConfigTarget`

可配置目标（适配器或模块）的元信息

仅承载类级别的声明信息（ConfigClass / AccountConfigClass），
不实例化目标类，避免在 CLI 上下文触发配置模板生成等副作用。


#### 方法列表


##### `__init__(kind: Literal['adapter', 'module'], name: str)`

- **kind** (`目标类型："adapter"`): | "module"
- **name** (`目标名（适配器为平台名，模块为注册名）`): - **config_class**: ConfigClass 声明（未声明为 None）
- **account_class** (`AccountConfigClass`): 声明（仅适配器，未声明为 None）
- **config_key** (`配置存储键（适配器默认类名，模块为注册名）`): - **package**: 所属 PyPI 包名（本地插件为 None）
- **source** (`来源："entrypoint"`): | "plugins"

---


##### `configurable()`

是否包含任何配置声明

---


##### `kind_label()`

目标类型显示名（适配器/模块）

---

