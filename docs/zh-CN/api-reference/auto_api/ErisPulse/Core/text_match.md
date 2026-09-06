# `ErisPulse.Core.text_match` 模块

---

## 模块概述


ErisPulse 统一文本/条目匹配工具

为全系统（scope 控制面 / message 装饰器 / wait_reply / adapter.on / activate_on）
提供**同一套**匹配条目语法，避免各处各自实现、语义漂移：

- ``精确名``：如 ``"Chat"``、``"u_admin"`` —— 全值精确比较（大小写不敏感）
- ``glob``：含 ``*`` / ``?`` / ``[seq]`` 的条目，如 ``"Tool*"``、``"spam_*"`` ——
  glob 全值匹配（大小写不敏感）
- ``re:正则``：以 ``re:`` 前缀声明的正则条目，如 ``"re:^Danger.*"`` ——
  正则 ``search`` 匹配（默认大小写不敏感，可在正则内用 ``(?-i)`` 或 ``(?i)`` 控制）

约定：
- 默认**大小写不敏感**（对齐 scope 模块名匹配的既有语义）
- 纯精确条目走快路径（无正则/无 glob 开销）
- 正则条目编译结果带 LRU 缓存；非法正则静默降级为"不匹配"（不抛错）

> **提示**
> 1. ``compile_entry_matcher(entry)`` 把单条目编译为 ``fn(text) -> bool``
> 2. ``compile_entry_list(entries)`` 把条目列表编译为"任一命中"匹配器
> 3. ``compile_text_matcher(pattern, regex)`` 给装饰器用（glob 与 regex 须都命中）
> 4. ``extract_text(event)`` 提取事件纯文本（``alt_message`` 优先）

---

## 函数列表


### `_compile_regex(pattern: str)`

> **内部方法**
编译正则（带 LRU 缓存）。非法正则返回哨兵对象，调用方视为"不匹配"。

- **pattern** (`正则源码`): **返回值** (`编译后的`): Pattern，或 ``_INVALID_REGEX``

---


### `is_entry_pattern(entry: str)`

判断条目是否包含模式语法（glob 或 re: 前缀）

无模式字符的纯字符串走精确快路径。

- **entry** (`匹配条目`): **返回值** (`True`): 表示是 glob / 正则条目

---


### `compile_entry_matcher(entry: str)`

编译单个匹配条目为判定函数

三种语法：

- 精确名（无模式字符）→ 大小写不敏感全值比较
- glob（含 ``*`` / ``?`` / ``[seq]``）→ 大小写不敏感 glob 全值匹配
- ``re:...`` → 大小写不敏感正则 ``search``；非法正则恒不匹配

- **entry** (`匹配条目`): **返回值** (```fn(text:`): str) -> bool``

---


### `compile_entry_list(entries: list[str] | None)`

编译条目列表为"任一命中即 True"的判定函数

- **entries** (`条目列表，None`): / 空返回 None（表示不限制）
**返回值** (```fn(text:`): str) -> bool``，None 表示空列表

---


### `compile_text_matcher(pattern: str | None, regex: str | None)`

编译文本匹配条件函数（glob pattern 与 regex 须**都**命中才返回 True）

供 message 装饰器 / wait_reply / adapter.on 使用：
接收**事件对象**并内部提取文本，再按 pattern / regex 判定。

- ``pattern``：glob 通配符（大小写不敏感全值匹配）
- ``regex``：正则（大小写不敏感 ``search``）；注意此处为正则源码，**不加** ``re:`` 前缀
- 两者同时给定 → AND；均未给定 → 返回 None（不限制）

- **pattern** (`glob`): 通配符，None 表示不校验
- **regex** (`正则源码，None`): 表示不校验
**返回值** (`条件函数，均未给定时返回`): None

---


### `extract_text(event: Any)`

提取事件对象的纯文本内容（供文本匹配使用）

优先取 ``alt_message``（适配器提供的纯文本回退）；否则拼接 ``message``
段中 ``type == "text"`` 的文本。提取失败返回空字符串。

- **event** (`事件数据（dict`): 或 Event 包装对象）
**返回值**: 消息纯文本

---


### `entry_matches(entry: str, text: str)`

单次便捷匹配（无需预编译）

- **entry** (`匹配条目（精确`): / glob / ``re:`` 正则）
- **text** (`待匹配文本`): **返回值**: 是否命中

---

