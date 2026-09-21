# `ErisPulse.Core.Event.command_args` 模块

---

## 模块概述


ErisPulse 命令参数与选项解析模块

为 ``@command(args=..., options=...)`` 提供声明式参数解析：

- ``args=`` 声明位置参数：``<count:int>``（必填）、``[sides:int=6]``（可选含默认值）。
  类型支持 ``str`` / ``int`` / ``float`` / ``bool`` / ``literal``（枚举，``<mode:literal=fast|slow>``，
  可选形式默认取首个枚举值）/ ``duration``（如 ``90s``、``1h30m``，按秒折算为 float）/
  ``rest``（剩余全部文本，必须位于最后）
- ``options=`` 字典式声明选项：键为处理器参数名，值为旗标形式。``bool`` 注解的参数
  为布尔旗标（如 ``"-v/--verbose"``）；其余（缺省按 ``str``）为带值选项，支持
  ``--label hello`` 与 ``--label=hello`` 两种取值形式
- 解析顺序：选项先被识别剔除，剩余 token 再交给 ``args=`` 解析（``rest`` 覆盖剔除选项后的剩余文本）
- 声明在注册期解析并校验（语法错误 / 处理器签名不匹配直接抛 ValueError，fail-fast）；
  用户输入在分发期解析，失败抛出 :class:`CommandArgsError`（携带 i18n 键与插值参数），
  由命令分发层自动回复本地化错误提示

> **提示**
> 1. 未声明 ``args=`` / ``options=`` 的命令行为完全不变（向后兼容）
> 2. 本模块为命令系统内部实现（``Core/Event/command.py`` 消费），不属公共 API

---

## 函数列表


### `_bool_value(raw: str, arg_name: str = '?')`

> **内部方法**
将用户输入 token 转换为布尔值

复用交互式确认（``Event.confirm()``）维护的确认词表
(:data:`~ErisPulse.Core.constants.CONFIRM_YES_WORDS` /
:data:`~ErisPulse.Core.constants.CONFIRM_NO_WORDS`，zh/en/ja/ru），
与交互确认同一判定口径、同一维护来源。

- **raw** (`用户输入的原始`): token
- **arg_name** (`参数名（错误提示用，缺省为`): "?"）
**返回值** (`转换后的布尔值`): **异常**: `CommandArgsError` - token 不在确认词表内

---


### `_duration_value(raw: str)`

> **内部方法**
将时长 token（如 ``90s``、``1h30m``）转换为秒数

- **raw** (`用户输入的原始`): token
**返回值** (`折算后的秒数（float）`): **异常**: `CommandArgsError` - 格式不合法或包含未知单位

---


### `_convert_value(type_name: str, raw: str, arg_name: str, choices: tuple[str, ...] | None = None)`

> **内部方法**
按声明类型转换单个 token（分发期转换入口）

- **type_name** (`声明的类型名（str/int/float/bool/literal/duration）`): - **raw**: 用户输入的原始 token
- **arg_name** (`参数名（错误提示用）`): - **choices**: literal 类型的枚举值（其余类型为 None）
**返回值** (`转换后的值`): **异常**: `CommandArgsError` - 转换失败（携带本地化错误键）

---


### `_convert_default(type_name: str, raw: str, spec: str)`

> **内部方法**
注册期转换声明中的默认值（语法错误抛 ValueError fail-fast）

- **type_name** (`声明的类型名`): - **raw**: 声明的默认值原文
- **spec** (`完整`): args= 声明（错误提示用）
**返回值** (`转换后的默认值`): **异常**: `ValueError` - 默认值与声明类型不匹配

---


### `parse_args_spec(spec: str, handler: Callable[..., Any] | None = None)`

解析 ``args=`` 声明字符串（注册期调用，fail-fast）

语法：``<name:type>`` 必填、``[name:type=default]`` 可选；``literal`` 类型的
``=`` 后为枚举表（``a|b|c``，可选形式默认取首个）；``rest`` 类型必须是最后一个条目；
必填条目不得出现在可选条目之后（避免二义性匹配）。
可选条目未声明默认值（``[name:type]``）时回填处理器签名同名参数的默认值，
避免注入 ``None`` 静默覆盖处理器自身的默认值（签名亦无默认值时仍为 ``None``）。

- **spec** (`声明字符串，如`): ``"<count:int> [sides:int=6] [mode:literal=fast|slow]"``
- **handler** (`命令处理器（可选；用于回填未声明默认值的可选条目）`): **返回值** (`位置参数规格列表（按声明顺序）`): **异常**: `ValueError` - 声明语法无效（携带本地化错误信息）

**示例**:
```python
>>> parse_args_spec("<count:int> [sides:int=6]")
```

---


### `_annotation_type_key(param: inspect.Parameter | None)`

> **内部方法**
解析处理器参数注解为类型键（兼容真实类型对象与字符串注解）

- **param** (`处理器参数（None`): 返回 None）
**返回值** (`"str"/"int"/"float"/"bool"；未注解返回`): None；不支持返回原始注解文本

---


### `parse_options_spec(options: dict[str, Any], handler: Callable[..., Any])`

解析 ``options=`` 声明（注册期调用，fail-fast）

键为处理器参数名，值为旗标形式字符串（多个别名以 ``/`` 分隔，如
``"-v/--verbose"``）。注解为 ``bool`` 的参数解析为布尔旗标；``str`` / ``int`` /
``float``（缺省视为 ``str``）为带值选项，默认值取处理器签名的参数默认值。

- **options** (`选项声明字典，如`): ``{"verbose": "-v/--verbose", "label": "--label"}``
- **handler** (`命令处理器（读取注解、默认值并校验签名）`): **返回值** (`选项规格字典（键为处理器参数名）`): **异常**: `ValueError` - 旗标形式不合法 / 注解不受支持 / 参数未在处理器签名中定义

**示例**:
```python
>>> parse_options_spec({"verbose": "-v/--verbose"}, handler)
```

---


### `_looks_like_option(token: str)`

> **内部方法**
判断 token 是否形如选项旗标（类数字 token 如负数不算）

- **token** (`待判断的`): token
**返回值** (`是否形如选项（"-x"、"--xx"；"-1"、"-0.5"、"-"`): 均不算）

---


### `_extract_options(tokens: list[str], options_spec: dict[str, OptionArg])`

> **内部方法**
从 token 列表中识别并剔除选项（分发期第一步）

支持独立取值（``--label hello``）与内联取值（``--label=hello``）；布尔旗标
可用内联形式显式赋值（``-v=false``）。未声明的形如选项的 token 视为未知选项。

- **tokens** (`命令名之后的原始`): token 列表
- **options_spec** (`选项规格字典`): **返回值** (`(剔除选项后的剩余`): token, 选项参数名 → 已转换值)
**异常**: `CommandArgsError` - 未知选项 / 带值选项缺少取值 / 内联值转换失败

---


### `_bind_positionals(tokens: list[str], args_spec: list[PositionalArg])`

> **内部方法**
按位置参数规格绑定剩余 token（分发期第二步）

- **tokens** (`剔除选项后的剩余`): token
- **args_spec** (`位置参数规格列表`): **返回值** (`参数名`): → 已转换值
**异常**: `CommandArgsError` - 缺少必填参数 / token 转换失败 / 参数过多

---


### `bind_command_arguments(tokens: list[str], args_spec: list[PositionalArg] | None = None, options_spec: dict[str, OptionArg] | None = None)`

将命令 token 列表解析为处理器关键字参数（分发期调用）

解析顺序：选项先被识别剔除，剩余 token 再交给 ``args=`` 解析（``rest`` 为
剔除选项后的剩余文本）。仅在声明了 ``args=`` / ``options=`` 的命令上调用。

- **tokens** (`命令名之后的原始`): token 列表
- **args_spec** (`位置参数规格（未声明为`): None）
- **options_spec** (`选项规格（未声明为`): None）
**返回值** (`处理器关键字参数（直接`): ``handler(event, **kwargs)`` 注入）
**异常**: `CommandArgsError` - 任一 token 无法按声明解析（捕获后自动回复本地化提示）

**示例**:
```python
>>> bind_command_arguments(["3", "--label", "hi"], args_spec, options_spec)
{"count": 3, "label": "hi", ...}
```

---


### `format_usage(args_spec: list[PositionalArg] | None, options_spec: dict[str, OptionArg] | None)`

依据参数/选项规格生成 usage 尾串（未提供 usage= 时自动展示与错误提示附带）

形态：位置参数 ``<count>`` / ``[sides=6]`` / ``<mode:a|b|c>`` / ``<text...>``；
选项 ``[-v, --verbose]`` / ``[--label TEXT]``。

- **args_spec** (`位置参数规格（未声明为`): None）
- **options_spec** (`选项规格（未声明为`): None）
**返回值** (`usage`): 尾串（无任何声明时为空字符串）

**示例**:
```python
>>> format_usage(args_spec, options_spec)
"<count> [sides=6] [-v, --verbose] [--label TEXT]"
```

---


### `parse_duration(text: str)`

将时长声明（如 ``"90s"``、``"1h30m"``、``"1d"``）转换为秒数

语法与 ``args=`` 声明的 ``duration`` 类型一致：1~n 段"数值+单位"
（单位 s / m / h / d，大小写不敏感）。供命令治理声明（``cooldown=``）
等场景在注册期复用同一解析口径。

- **text** (`时长声明字符串`): **返回值** (`折算后的秒数（float）`): **异常**: `ValueError` - 格式不合法、包含未知单位或折算值非正

---


## 类列表


### `class PositionalArg`

args= 声明的单个位置参数（注册期解析产物）


### `class OptionArg`

options= 声明的单个选项（注册期解析产物）


### `class CommandArgsError(Exception)`

> **内部方法**
命令参数解析错误（用户输入侧）

携带 i18n 键与插值参数，由命令分发层捕获后自动回复本地化错误提示；
``str(exception)`` 即本地化后的完整错误文本。

