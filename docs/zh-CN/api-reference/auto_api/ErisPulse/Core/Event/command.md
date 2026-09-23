# `ErisPulse.Core.Event.command` 模块

---

## 模块概述


ErisPulse 命令处理模块

提供基于装饰器的命令注册和处理功能

命令是特殊的消息事件处理器（ErisPulse 扩展类型），其用户侧配置
由统一覆写系统持有（``ErisPulse.event.overrides``，见
:mod:`ErisPulse.Core.Event.overrides`）：**用户黑白名单（ACL）** 在
``overrides.acl`` 类别（命令名支持 glob，``acl_default_allow`` 兜底严格模式）；
**实现参数覆写**（master / hidden / aliases 等）在 ``overrides.command`` 类别
（用户优先语义）。本模块的命令判定链消费覆写系统的生效结果。

> **提示**
> 1. 支持命令别名和命令组
> 2. 支持命令权限控制（master / permission 函数 / 覆写系统 ACL）
> 3. 支持命令帮助系统
> 4. 支持等待用户回复交互
> 5. 支持声明式参数与选项（``args=`` / ``options=``）：自动类型转换、本地化错误提示与 usage 生成

---

## 类列表


### `class CommandHandler`

命令处理器

提供命令注册、处理和管理功能


#### 方法列表


##### `_cooldowns()`

> **内部方法** 命令冷却状态表（cooldown= 声明）

---


##### `_rate_limits()`

> **内部方法** 命令限流状态表（rate_limit= 滑动窗口）

---


##### `_usage_counts()`

> **内部方法** 配额内存计数表（usage= 持久化读缓存）

---


##### `_refresh_command_config()`

从配置读取命令解析相关参数

支持配置热更新：``config.updated`` 事件触发后再次调用即可刷新
前缀 / 大小写 / 空格前缀 / 是否须 @机器人 等解析参数。

---


##### `_on_config_updated(_data: dict)`

配置变更回调：刷新命令解析参数、实现参数覆盖与用户 ACL

---


##### `_recompute_max_name_tokens()`

> **内部方法**
重算已注册命令名 / 别名中的最大 token 数

命令名支持空格分隔的子命令形式（如 ``"admin add"``），匹配阶段按
最长前缀尝试；此缓存在注册与注销后重算，消息分发期只做字典查找。

---


##### `_resolve_command_tokens(parts: list[str])`

> **内部方法**
按"最长前缀匹配"从已切分的命令 token 中解析命令名

依次尝试 ``parts[:n]``（n 从最大注册 token 数降到 1）组成的候选名，
先查别名映射再查命令表；命中即返回，未命中继续降级尝试。

- **parts** (`空格切分后的命令`): token 列表（大小写已按配置归一）
**返回值** (```(命中的候选名（可能为别名形式）,`): 解析后的命令全名, 命中的 token 数)``；
         全部未命中返回 ``(None, None, 0)``

---


##### `_inherited_permission(name: str)`

> **内部方法**
沿命令名父链向上查找最近声明了权限函数的祖先命令

子命令（空格分隔的多 token 命令名，如 ``"admin add"``）自身未声明
permission 时调用：逐级去掉末尾 token 查找已注册祖先，返回第一个
声明了权限的祖先的权限函数——保护父命令即保护其下全部子命令
（声明了权限的祖先会跳过未声明权限的中间祖先继续上溯）。
仅读取注册值，不递归用户覆写。

- **name** (`已解析的命令全名`): **返回值** (`祖先的权限检查函数；无可继承权限时返回`): None

---


##### `parse_rate_limit(spec: str)`

解析限流声明（如 ``"5/minute"``、``"10/s"``）为 (次数, 窗口秒)

滑动窗口语义：窗口内至多放行 ``次数`` 次，超出静默丢弃。单位支持
second / minute / hour / day（含单字母缩写与可选数值前缀，大小写不敏感）。

- **spec** (`限流声明字符串`): **返回值** (`(limit,`): window_seconds)
**异常**: `ValueError` - 语法非法或数值非正时

---


##### `parse_usage(spec: str)`

解析配额声明（如 ``"3/day"``）为 (次数, 周期单位)

自然周期语义：周期边界对齐本地时区的自然分钟 / 小时 / 日（如 day 为
当日 00:00 起，次日自动重置），与 :meth:`parse_rate_limit` 的滑动窗口
相区分（rate_limit 防瞬时刷屏，usage_limit 管业务配额）。

- **spec** (`配额声明字符串`): **返回值** (`(limit,`): unit)；语法非法时返回错误描述字符串（调用方包装 ValueError）

---


##### `usage_period_key(unit: str)`

计算当前自然周期的标识键（本地时区）

> **内部方法**
供分发期配额判定使用；周期切换键随之变化即自动重置

- **unit** (`周期单位（minute`): / hour / day）
**返回值** (`周期键（如`): ``"2026-09-21"``）

---


##### `_scope()`

> **内部方法**
延迟获取作用域单例（避免模块初始化阶段的循环依赖）

用于模块维度作用域检查与事件上下文提取。

**返回值** (`scope`): 单例（ScopeManager）

---


##### `__call__(name: str | list[str] | None = None, aliases: list[str] | None = None, group: str | None = None, priority: int = 0, permission: Callable | None = None, help: str | None = None, usage: str | None = None, hidden: bool = False, master: bool = False, args: str | None = None, options: dict | None = None, cooldown: str | None = None, cooldown_key: str = 'user', cooldown_reply: str | None = None, rate_limit: str | None = None, rate_limit_key: str = 'user', rate_limit_reply: str | None = None, usage_limit: str | None = None, usage_limit_key: str = 'user', usage_limit_reply: str | None = None, deprecated: str | None = None, deprecated_reject: bool = False)`

命令装饰器

- **name** (`命令名称，可以是字符串或字符串列表`): - **aliases**: 命令别名列表
- **group** (`命令组名称`): - **priority**: 处理器优先级
- **permission** (`权限检查函数，返回True时允许执行命令`): - **help**: 命令帮助信息
- **usage** (`命令使用方法`): - **hidden**: 是否在帮助中隐藏命令
- **master** (`是否仅允许框架主人执行（框架自动检查`): ``master.is_master(event)``）
- **args** (`声明式位置参数定义，如`): ``"<count:int> [sides:int=6]"``。类型支持
    ``str`` / ``int`` / ``float`` / ``bool`` / ``literal``（枚举，``<mode:literal=fast|slow>``）/
    ``duration``（如 ``90s``、``1h30m``）/ ``rest``（剩余全部文本，须在最后）。
    可选条目未声明默认值（``[name:type]``）时回填处理器签名同名参数的默认值。
    声明后框架在权限检查通过后自动解析并按名注入处理器参数，用户输入错误时
    自动回复本地化提示与用法（不会抛异常崩溃）；不声明则保持原行为
- **options** (`声明式选项定义，如`): ``{"verbose": "-v/--verbose", "label": "--label"}``。
    键为处理器参数名，值为旗标形式（多个别名以 ``/`` 分隔）：注解为 ``bool`` 的参数
    为布尔旗标；其余（缺省按 ``str``）为带值选项，支持 ``--label hello`` 与
    ``--label=hello`` 取值，类型跟随处理器注解。选项先于位置参数解析——``rest``
    覆盖剔除选项后的剩余文本。声明参数名必须存在于处理器签名中（否则注册期抛 ValueError）
- **cooldown** (`命令冷却声明（EPRFC-2026-001`): 方向七），时长语法与 ``args=`` 的
    ``duration`` 类型一致（如 ``"30s"``、``"1h30m"``、``"1d"``）。冷却命中时命令
    默认静默丢弃（对称于作用域静默），命令仍保持已认领状态（不漏给低优先级
    消息处理器）；冷却在全部权限检查与参数解析通过、命令实际执行前开始计时，
    参数错误不消耗冷却。进程内内存状态，模块卸载时自动清理
- **cooldown_key** (`冷却键粒度：``"user"``（默认，同一用户全局共享）/`): ``"session"``
    （同一会话共享）/ ``"global"``（所有用户所有会话共享）。``user`` / ``session``
    复用 ``platform:bot:目标`` 会话键体系。非法值注册期抛 ValueError
- **cooldown_reply** (`冷却命中时的回复文案（可选）。缺省静默丢弃；指定后冷却`): 命中即回复该文案（原文发送，不做格式化）
- **rate_limit** (`滑动窗口限流声明（EPRFC-2026-001`): 方向七），如 ``"5/minute"`` /
    ``"10/s"`` / ``"100/day"``——窗口内至多执行次数，超出默认静默丢弃（命令仍被
    认领）；与 ``cooldown=`` 共享会话键体系，可同时声明（冷却先判、限流后判）
- **rate_limit_key** (`限流键粒度：``"user"``（默认）/`): ``"session"`` / ``"global"``
- **rate_limit_reply** (`限流命中时的回复文案（可选，缺省静默丢弃）`): - **usage_limit**: 自然周期配额声明（如 ``"3/day"`` / ``"5/hour"`` / ``"10/minute"``）——
    每键在自然周期（分钟 / 小时 / 日，本地时区）内至多执行 ``次数``，周期切换自动
    重置；计数经 storage KV 持久化，重启不丢（与 ``rate_limit=`` 滑动窗口的
    区别：rate_limit 防瞬时刷屏，usage 管业务配额如"每日签到 3 次"）
- **usage_limit_key** (`配额键粒度：``"user"``（默认）/`): ``"session"`` / ``"global"``
- **usage_limit_reply** (`配额用尽时的回复文案（可选，缺省静默丢弃）`): - **deprecated**: 命令废弃声明（EPRFC-2026-001 方向七）：非空文案即标记废弃——
    调用时自动回复该文案（help 列表显示废弃标记），默认仍继续执行
- **deprecated_reject** (`废弃命令拒绝执行（默认`): False 继续执行；True 时回复
    废弃文案后不再执行处理器）
**返回值** (`装饰器函数`): 
**示例**:
```python
>>> @command("roll", args="<count:int> [sides:int=6]",
...          options={"verbose": "-v/--verbose", "label": "--label"})
... async def roll(event, count: int, sides: int = 6, verbose: bool = False, label: str = ""):
...     await event.reply(f"掷了 {count} 次 {sides} 面骰")
>>> @command("daily", cooldown="1d", cooldown_key="user", cooldown_reply="今天已签到")
... async def daily(event):
...     await event.reply("签到成功！")
>>> @command("search", rate_limit="5/minute", rate_limit_key="user")
... async def search(event): ...
>>> @command("oldcmd", deprecated="请用 /newcmd", deprecated_reject=True)
... async def old(event): ...
```

---


##### `unregister(handler: Callable)`

注销命令处理器

- **handler** (`要注销的命令处理器`): **返回值**: 是否成功注销

---


##### `unregister_by_owner(owner: str)`

> **内部方法**
按归属者精确移除命令

- **owner** (`归属者（模块名）`): **返回值**: 移除的命令数量

---


##### `async wait_reply(event: dict[str, Any], prompt: str | None = None, timeout: float = DEFAULT_WAIT_TIMEOUT_SECS, callback: Callable[[dict[str, Any]], Awaitable[Any]] | None = None, validator: Callable[[dict[str, Any]], bool] | None = None, method: str = DEFAULT_SEND_METHOD, pattern: str | None = None, regex: str | None = None, session: bool = False, cmdpass: bool | None = None)`

等待用户回复

- **event** (`原始事件数据`): - **prompt**: 提示消息，如果提供会发送给用户
- **timeout** (`等待超时时间(秒)`): - **callback**: 回调函数，当收到回复时执行
- **validator** (`验证函数，用于验证回复是否有效`): - **method**: 发送方法，默认为 "Text"
- **pattern** (`glob`): 通配符（``*`` / ``?`` / ``[seq]``），回复文本不匹配时继续等待
- **regex** (`正则表达式，回复文本不匹配时继续等待（与`): pattern 同时给定时须都匹配）
- **session** (`会话级等待——同会话（群`): / 频道）中**任何人**的回复均可命中
    （如群协作场景：" anyone 输入「开始」即开始"）；默认 False 仅等待原回复者
- **cmdpass** (`是否跳过命令匹配的三态（None=跟随全局配置，默认不跳过——`): 等待期间命中已注册命令的消息放行给命令分发器执行，等待继续挂起；
    True=跳过命令匹配，等待期间消息一律作为回复消费）
**返回值** (`用户回复的事件数据，如果超时则返回None`): > **提示**
> 等待期间归属模块被卸载 / 适配器关闭 / 同会话被新的等待或租约取代 /
> 回复者权限被撤销时，等待立即终止并返回 None（底层为
> :class:`~ErisPulse.Core.Event.interaction.InteractionCancelled`）。

---


##### `async _handle_message(event: dict[str, Any])`

处理消息事件中的命令

> **内部方法**
内部使用的方法，用于从消息中解析并执行命令

- **event**: 消息事件数据

---


##### `_is_command_text(text: str)`

判定文本是否形如一条已注册命令（前缀 + 命令名/别名命中），不执行命令

供交互等待（wait_reply）的命令穿透判定复用——等待期间命中命令的
消息放行给命令分发器执行。判定口径与 :meth:`_try_execute_command`
的匹配逻辑一致（前缀 / 大小写归一 / 子命令最长前缀匹配）。

- **text** (`待判定的消息文本`): **返回值** (`是否形如已注册命令`): > **内部方法**
内部使用的方法

---


##### `async _try_execute_command(event: 'Event', original_text: str, prefix: str)`

尝试执行命令

> **内部方法**
内部使用的方法，用于尝试解析和执行命令

- **event** (`消息事件数据`): - **original_text**: 原始文本内容（命令名匹配时按配置做大小写归一，参数保留原文）
- **prefix** (`已匹配的命令前缀（可能已转换为小写）`): **返回值**: 是否成功执行命令

---


##### `async _check_pending_reply(event: 'Event')`

检查是否是等待回复的消息

判定链（会话键命中 → pattern/regex 过滤 → validator 校验 →
权限复查 → 唤醒等待方并认领事件）委托交互会话管理器
:meth:`~ErisPulse.Core.Event.interaction.InteractionManager.resolve`。

- **event**: 消息事件数据

---


##### `async _send_event_text(event: dict[str, Any], text: str)`

> **内部方法**
向事件来源会话发送文本（各 _send_* 提示的公共发送通道）

- **event** (`事件数据`): - **text**: 已本地化的待发送文本
- **error_log_key** (`发送失败时的错误日志`): i18n 键

---


##### `async _send_permission_denied(event: dict[str, Any])`

发送权限拒绝消息

> **内部方法**
内部使用的方法

- **event**: 事件数据

---


##### `async _send_command_error(event: dict[str, Any], error: str)`

发送命令错误消息

> **内部方法**
内部使用的方法

- **event** (`事件数据`): - **error**: 错误信息

---


##### `async _send_args_error(event: dict[str, Any], text: str)`

发送命令参数错误消息（args= / options= 解析失败时的本地化提示 + 用法）

> **内部方法**
内部使用的方法

- **event** (`事件数据`): - **text**: 已本地化的错误文本（含用法行）

---


##### `_cooldown_scope_key(kind: str, event: 'Event')`

> **内部方法**
计算冷却作用域键（复用 ``platform:bot:目标`` 会话键体系）

- **kind** (`粒度（user`): / session / global，注册期已校验）
- **event** (`事件数据`): **返回值**: 作用域键字符串

---


##### `_usage_line(cmd_name: str, effective: dict, display_prefix: str | None = None)`

> **内部方法**
计算命令的生效 usage 行（帮助展示与参数错误提示共用）

优先取开发者声明的 ``usage=``（含覆写）；未声明且注册了 ``args=`` /
``options=`` 时按声明自动生成；否则回退 ``{前缀}{命令名}``。

- **cmd_name** (`命令名`): - **effective**: 合并覆写后的命令生效参数
- **display_prefix** (`显示用前缀（None`): 时取配置前缀首个）
**返回值** (`usage`): 字符串

---


##### `bind_message_handler(handler: BaseEventHandler)`

> **内部方法**
绑定到共享的消息事件处理器

将命令分发器 _handle_message 注册到共享的 BaseEventHandler 中，
使命令处理和通用消息处理共享同一个优先级队列。

- **handler** (`MessageHandler`): 持有的 BaseEventHandler 实例

---


##### `_register_dispatcher()`

> **内部方法**
将命令分发器注册到共享 handler（如尚未注册）

---


##### `_clear_commands()`

> **内部方法**
清除所有已注册的命令，并从共享 handler 中注销命令分发器

**返回值**: 被清除的命令数量

---


##### `get_command(name: str)`

获取命令信息（返回合并覆写系统命令参数后的**生效参数**）

传入作用域上下文（``event`` 或 ``platform`` / ``bot_id`` / ``session_id``
任一）时，命令归属模块在当前会话不可用则返回 ``None``（与分发静默语义一致）。

- **name** (`命令名称（支持别名）`): - **event**: 可选，事件上下文（Event 或 dict）
- **platform** (`可选，平台名（与`): event 二选一或叠加，显式参数优先）
- **bot_id** (`可选，Bot`): 标识
- **session_id** (`可选，会话标识`): **返回值** (`合并覆盖后的命令信息字典；不存在或该会话不可用返回`): None

**示例**:
```python
>>> command.get_command("admin")
>>> command.get_command("admin", event=event)   # 会话不可用时返回 None
```

---


##### `get_commands()`

获取所有命令

传入作用域上下文时，过滤掉当前会话不可用模块的命令（值为原始注册信息，
需要覆盖合并后的生效参数请用 :meth:`get_command` / :meth:`get_visible_commands`）；
不传上下文时返回完整注册表（与原行为一致）。

- **event** (`可选，事件上下文（Event`): 或 dict）
- **platform** (`可选，平台名`): - **bot_id**: 可选，Bot 标识
- **session_id** (`可选，会话标识`): **返回值**: 命令信息字典

---


##### `get_group_commands(group: str)`

获取命令组中的命令

传入作用域上下文时，过滤掉当前会话不可用模块的命令。

- **group** (`命令组名称`): - **event**: 可选，事件上下文（Event 或 dict）
- **platform** (`可选，平台名`): - **bot_id**: 可选，Bot 标识
- **session_id** (`可选，会话标识`): **返回值**: 命令名称列表

---


##### `get_visible_commands()`

获取所有可见命令（非隐藏命令）

可见性判定读取覆写系统命令参数（``event.overrides.command.<module>.<command>.hidden``）：
用户显式覆盖 ``hidden`` 后，帮助列表随之变化（用户优先）。
传入作用域上下文（``event`` 或 ``platform`` / ``bot_id`` / ``session_id``
任一）时，额外按模块维度过滤该会话不可用模块的命令（与分发静默语义一致）。

- **event** (`可选，事件上下文（Event`): 或 dict）
- **platform** (`可选，平台名（与`): event 叠加时显式参数优先）
- **bot_id** (`可选，Bot`): 标识
- **session_id** (`可选，会话标识`): **返回值**: 可见命令信息字典（值为合并覆盖后的生效参数）

---


##### `_context_from_event(event: Any)`

> **内部方法**
从事件提取作用域查询上下文（platform / bot / session）

---


##### `_resolve_query_context(event: Any = None, platform: str | None = None, bot_id: str | None = None, session_id: str | None = None)`

> **内部方法**
归一查询上下文：event 与显式关键字参数合并（显式参数优先）

**返回值** (`{"platform":`): str, "bot_id": str|None, "session_id": str|None}；
         完全未提供任何上下文时返回 None（不做会话过滤）

---


##### `_effective_info(name: str, info: dict)`

> **内部方法**
合并实现参数覆盖后的命令生效参数（帮助渲染与可见性判定用）

- **name** (`命令主名`): - **info**: 注册时的命令信息字典
**返回值**: 与执行路径同源的覆盖合并结果（无覆盖时原样返回）

---


##### `help(command_name: str | None = None, show_hidden: bool = False, event: Any = None)`

生成帮助信息

传入 ``event`` 时按作用域对输出做会话感知调整：① 模块维度——
该会话（platform / bot / session）下被作用域禁用的模块，其命令不再列出
（与分发静默语义一致）；② 覆盖——帮助文本 / usage / 可见性读取
``event.overrides.command`` 覆写值（用户优先）。
子命令（空格分隔多 token 命令名）在其可见父命令下缩进展示。

- **command_name** (`命令名称，如果为None则生成所有命令的帮助`): - **show_hidden**: 是否显示隐藏命令
- **event** (`可选，事件上下文（Event`): 或 dict）。提供时按作用域过滤
              当前会话不可用模块的命令；None 时不过滤（保持原行为）
**返回值** (`帮助信息字符串`): 
**示例**:
```python
>>> # 全量帮助（不感知会话）
>>> command.help()
>>> # 会话感知帮助：只列出当前会话可用的命令
>>> command.help(event=event)
```

---


##### `_owner_blocked(info: dict, ctx: dict[str, str | None])`

> **内部方法**
判断命令归属模块在给定作用域上下文下是否被模块维度禁用

- **info** (`命令信息字典`): - **ctx**: {"platform": str, "bot_id": str|None, "session_id": str|None}
**返回值** (`是否被禁用（owner`): 为空视为框架层资源，恒不阻止）

---

