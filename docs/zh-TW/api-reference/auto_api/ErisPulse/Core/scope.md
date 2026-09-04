# `ErisPulse.Core.scope` 模块

---

## 模块概述


ErisPulse 统一控制面（scope）

控制权完全交给用户：在模块 / 适配器 / 命令 / 处理器注册的**上层**（配置 ``ErisPulse.scope``
或运行时 ``sdk.scope``）统一声明"谁 / 什么 / 什么条件下，允许或禁止"，以及覆盖
模块 / 命令的默认实现参数。事件管线在每一级自动读取并执行。

本系统是 2.8.0 的权限/访问控制**唯一**入口，收敛了原有的：

- 模块维度（原作用域三级绑定）
- 身份维度（原事件准入 access：适配器 / Bot / 会话 / 用户）
- 命令维度（原命令权限 ACL：按命令的用户黑白名单）
- 处理器/文本维度（新增：按模块过滤消息文本）
- 实现参数覆盖（新增：覆盖模块/命令的 master / hidden / aliases / prefix 等）
- 出站动作维度（新增：禁止模块发起消息发送 / 标准 API 动作 / 请求操作）

配置树（``ErisPulse.scope``）：

.. code-block:: toml

    [ErisPulse.scope]
    default_allow = true          # 全局兜底（未命中任何规则时放行/拒绝）

    # ① 模块维度：哪些模块可用（优先级 会话 > Bot > 平台）
    [ErisPulse.scope.platforms.onebot11]
    modules = ["Chat", "Tool*"]   # 精确名 / glob / re:正则
    blocked = ["re:^Danger"]
    [ErisPulse.scope.bots.onebot11."123456"]
    modules = ["Chat"]
    [ErisPulse.scope.sessions.onebot11."789012345"]
    modules = ["Chat"]

    # ② 身份维度：谁的事件收不收（优先级 用户 > 会话 > Bot > 适配器）
    [ErisPulse.scope.identity.adapters.onebot11]
    deny = true
    [ErisPulse.scope.identity.bots.onebot11."123456"]
    deny = true
    [ErisPulse.scope.identity.sessions.onebot11."g_blocked"]
    deny = true
    [ErisPulse.scope.identity.users.onebot11]
    allow = ["u_admin"]
    deny = ["u_bad", "spam_*"]    # 支持 glob / re:正则

    # ③ 命令维度：谁能执行某命令（命令名支持 glob）
    [ErisPulse.scope.commands."roll*"]
    allow = ["onebot11:u_vip"]
    deny = ["onebot11:u_bad"]

    # ④ 处理器/文本维度：某模块的事件处理器按 pattern / regex 过滤
    [ErisPulse.scope.handlers.MyModule]
    pattern = "签到*"
    regex = "re:\d+\s*元"

    # ⑤ 实现参数覆盖：覆盖模块/命令的默认实现参数（禁用走命令 deny）
    [ErisPulse.scope.overrides.MyModule.restart]
    master = true   hidden = true   aliases = ["rs"]   prefix = "!"

    # ⑥ 出站动作维度：禁止模块发起出站动作（默认全允许，显式禁用才收紧）
    [ErisPulse.scope.actions.MyModule]
    send = false      # 禁止 MyModule 回复/主动发消息（Event.reply / Send DSL）
    api = false       # 禁止 MyModule 调用标准 API 动作（Api DSL / call_api）
    request = false   # 禁止 MyModule 对请求事件执行 accept/reject

匹配条目统一语法（见 :mod:`ErisPulse.Core.text_match`）：
**精确名** / **glob**（``*`` / ``?`` / ``[seq]``）/ **``re:`` 正则**，默认大小写不敏感。

> **提示**
> 1. 通过 ``from ErisPulse.Core import scope`` 导入单例（``sdk.scope`` 同对象）
> 2. ``scope.is_allowed(platform, bot_id, module, session_id)`` 判断模块是否可用
> 3. ``scope.is_identity_allowed(...)`` 判断事件是否放行（原 access）
> 4. ``scope.allow_user("roll*", platform, uid)`` 命令 ACL（命令名支持 glob）
> 5. ``scope.override("MyModule", "restart", master=True)`` 覆盖实现参数
> 6. ``scope.set_action("MyModule", "send", False)`` 禁止模块回复/发消息
> 7. ``scope.get_stats()`` 查看过滤统计

---

## 函数列表


### `_is_identity_binding(binding)`

> **内部方法**
读取身份绑定的策略（deny 优先于 allow）

- **binding** (`绑定字典（{"allow":`): true} 或 {"deny": true}）
**返回值** (`"allow"`): / "deny"；未配置或格式非法时返回 None

---


## 类列表


### `class ScopeManager`

统一控制面管理器（单例）

管理六维配置：模块（modules）/ 身份（identity）/ 命令（commands）/
处理器（handlers）/ 覆盖（overrides）/ 出站动作（actions）。支持配置热更新、
运行时增删、LRU 缓存与运行统计。


#### 方法列表


##### `_load_bindings()`

> **内部方法** 从配置加载绑定缓存

---


##### `_on_config_updated(_data: dict)`

配置变更回调：重建绑定缓存

---


##### `_invalidate_cache()`

> **内部方法** 清空 LRU 结果缓存

---


##### `_normalize(cfg: dict)`

> **内部方法**
归一化绑定配置为 (modules 匹配器, blocked 匹配器)

条目统一走 :func:`text_match.compile_entry_list`（精确 / glob / re: 正则，
大小写不敏感）。空列表返回 None（不限制）。

- **cfg** (`绑定配置字典（可含`): modules / blocked 字段）
**返回值** (`(modules`): 匹配器, blocked 匹配器)

---


##### `_get_binding(platform: str, bot_id: str | None, session_id: str | None)`

> **内部方法**
获取平台 / Bot / 会话的生效模块绑定

解析优先级：会话级 > Bot 级 > 平台级；均不存在时返回 None。

- **platform** (`平台名称`): - **bot_id**: Bot 用户 ID，None 表示不匹配 Bot 级
- **session_id** (`会话`): ID（群 / 频道 / 私聊），None 表示不匹配会话级
**返回值** (`(modules`): 匹配器, blocked 匹配器) 或 None

---


##### `is_allowed(platform: str, bot_id: str | None, module_name: str | None, session_id: str | None = None)`

判断模块是否允许在指定 Bot / 会话使用

模块名匹配大小写不敏感，条目支持 glob / ``re:`` 正则。
结果带 LRU 缓存，配置变更 / bind / unbind 时自动失效。
无绑定（默认）时遵循 ``default_allow``；模块名为空（框架层资源）始终放行。

- **platform** (`平台名称`): - **bot_id**: Bot 用户 ID，None 表示不匹配 Bot 级绑定
- **module_name** (`模块名称`): - **session_id**: 会话 ID（群 / 频道 / 私聊），None 表示不匹配会话级绑定
**返回值** (`是否允许`): 
**示例**:
```python
>>> from ErisPulse.Core import scope
>>> scope.is_allowed("onebot11", "123456", "Chat")
True
>>> scope.is_allowed("onebot11", "123456", "Chat", "group_9")
True
```

---


##### `_compute_allowed(platform: str, bot_id: str | None, session_id: str | None, module_key: str)`

> **内部方法** 计算模块是否允许（无缓存）

---


##### `_resolve_identity_policy(platform: str, bot_id: str | None, session_id: str | None, user_id: str | None)`

> **内部方法**
按特异性解析生效的身份策略：用户级 > 会话级 > Bot 级 > 适配器级

每个桶内：先精确命中，未命中再按 glob / ``re:`` 正则匹配该平台下全部条目。
取第一个产生策略的桶。

**返回值** (`"allow"`): / "deny"；均未配置绑定时返回 None

---


##### `is_identity_allowed(platform: str, bot_id: str | None = None, session_id: str | None = None, user_id: str | None = None)`

判断事件是否放行（身份维度，原事件准入）

解析优先级：**用户级 > 会话级 > Bot 级 > 适配器级**，取最具体的
已配置绑定；均未配置时遵循 ``default_allow``。
被拒绝的事件应在分发入口**完全丢弃**（不进入任何处理器）。

- **platform** (`平台名称（适配器标识）`): - **bot_id**: Bot 用户 ID，None 表示不匹配 Bot 级绑定
- **session_id** (`会话`): ID（群 / 频道 / 私聊），None 表示不匹配会话级
- **user_id** (`用户`): ID，None 表示不匹配用户级
**返回值** (`是否放行该事件`): 
**示例**:
```python
>>> scope.is_identity_allowed("onebot11", "123456", "group_9", "999")
False
```

---


##### `is_user_blocked(platform: str, user_id: str | None)`

检查用户是否被拉黑（身份维度 deny）

- **platform** (`平台名称`): - **user_id**: 用户 ID
**返回值**: 是否被拉黑

---


##### `get_blocked_users()`

获取所有被拉黑的用户（精确 deny 绑定）

**返回值** (```{platform:`): [user_id, ...]}``（按平台分组、用户 ID 排序）

---


##### `_command_acl(command_name: str)`

> **内部方法**
获取命令的生效 ACL（按 glob / ``re:`` 匹配命令名）

- **command_name** (`命令主名`): **返回值** (`{"allow":`): [...], "deny": [...]}，未配置时返回 None

---


##### `is_command_allowed(command_name: str, platform: str, user_id: str)`

判断用户对命令是否被 ACL 允许

判定顺序：deny 命中 → False；allow 非空且未命中 → False；
allow 命中 → True；未配置 ACL 时遵循全局 ``default_allow``
（false = 严格模式，命令未配置 ACL 即拒绝）。

- **command_name** (`命令主名`): - **platform**: 用户所属平台
- **user_id** (`用户`): ID
**返回值**: 是否允许执行

---


##### `handler_condition(owner: str)`

> **内部方法**
获取模块的文本过滤条件（handlers 桶）

- **owner** (`模块名`): **返回值** (`事件条件函数，未配置时返回`): None

---


##### `get_override(owner: str, command_name: str | None = None)`

获取模块 / 命令的实现参数覆盖

存储形态：``overrides.<module>`` 下标量值为模块级参数（如 ``hidden = true``），
子表（dict 值）为命令级覆盖（如 ``overrides.<module>.<command>``）。

- **owner** (`模块名`): - **command_name**: 命令名；None 表示仅模块级参数
**返回值** (`覆盖字典（模块级参数`): + 命令级覆盖，命令级优先），未配置返回 {}

---


##### `apply_override(owner: str, command_name: str, defaults: dict)`

> **内部方法**
把命令默认参数与覆盖合并（覆盖优先）

覆盖键 ``master`` 会同步映射到命令存储键 ``must_master``：
用户优先——用户在控制面显式配置 ``master = true/false`` 时直接生效
（既可收紧也可放开开发者默认），未配置时保持开发者默认。

- **owner** (`模块名`): - **command_name**: 命令名
- **defaults** (`命令默认参数字典`): **返回值**: 合并后的参数字典

---


##### `bot_id_from_event(event: dict)`

从事件数据提取 Bot 标识

- **event** (`事件数据（dict`): 或 Event 包装对象）
**返回值** (`Bot`): 标识（account_id 优先，回退 user_id），无法识别时返回空字符串

---


##### `session_id_from_event(event: dict)`

从事件数据提取会话标识（群 / 频道 / 私聊的目标 ID）

直接按 ID 字段存在性提取（优先级 group > channel > guild > thread > user），
不做会话类型推断：meta（connect / disconnect / heartbeat）等不含任何
会话 ID 字段的事件会返回空字符串，不会触发 ``infer_receive_type`` 的
兜底推断与日志。语义与原实现（经推断后取值）等价——原实现中缺少
全部 ID 字段的事件同样返回空。

- **event** (`事件数据（dict`): 或 Event 包装对象）
**返回值** (`会话`): ID（如 group_id / channel_id / user_id），无法识别时返回空字符串

---


##### `_put_cache(cache: OrderedDict, key: tuple, value: bool)`

> **内部方法** 写入 LRU 缓存（超过容量时淘汰最旧）

---


##### `get(platform: str, bot_id: str | None = None, session_id: str | None = None)`

获取平台 / Bot / 会话的生效模块绑定（原始配置形态）

解析优先级：会话级 > Bot 级 > 平台级。

- **platform** (`平台名称`): - **bot_id**: Bot 用户 ID，None 表示不匹配 Bot 级
- **session_id** (`会话`): ID，None 表示不匹配会话级
**返回值** (`{"modules":`): [...], "blocked": [...]}，无绑定时返回 None

**示例**:
```python
>>> scope.get("onebot11", "123456")
{"modules": ["Chat"], "blocked": []}
```

---


##### `bind_module(platform: str, bot_id: str | None = None, session_id: str | None = None)`

绑定模块作用域（① 模块维度）

- **platform** (`平台名称`): - **bot_id**: Bot 用户 ID，None 且 session_id 为空时表示平台级绑定
- **session_id** (`会话`): ID。指定时绑定到该会话；否则有 bot_id 时绑定到该 Bot；
                   否则绑定到平台级
- **modules** (`白名单模块条目列表（精确`): / glob / ``re:`` 正则）
- **blocked** (`黑名单模块条目列表`): - **persist**: 是否持久化到配置文件 (默认: True)
- **merge** (`是否**合并**而非替换现有绑定（默认`): False）

---


##### `unbind_module(platform: str, bot_id: str | None = None, session_id: str | None = None, persist: bool = True)`

移除模块作用域绑定（恢复为允许全部模块）

**返回值** (`是否成功移除（不存在则返回`): False）

---


##### `bind_identity(platform: str, bot_id: str | None = None, session_id: str | None = None, user_id: str | None = None)`

绑定身份准入策略（② 身份维度，指定来源的事件放行 / 拒绝）

绑定层级由参数决定：给定 ``user_id`` 绑定用户级；否则给定
``session_id`` 绑定会话级；否则给定 ``bot_id`` 绑定 Bot 级；
否则绑定适配器级。``allow`` 与 ``deny`` 必须二选一（同时给定时以 ``deny`` 为准）。
绑定键支持 glob / ``re:`` 正则（如 ``user_id="spam_*"``）。

**示例**:
```python
>>> scope.bind_identity("onebot11", user_id="999", deny=True)
>>> scope.bind_identity("onebot11", user_id="spam_*", deny=True)
```

---


##### `unbind_identity(platform: str, bot_id: str | None = None, session_id: str | None = None, user_id: str | None = None, persist: bool = True)`

移除身份准入绑定（该来源恢复遵循 default_allow）

**返回值** (`是否成功移除（绑定不存在时返回`): False）

---


##### `block_user(platform: str, user_id: str, persist: bool = True)`

拉黑用户：该用户的所有类型事件在分发入口被完全丢弃

等价于 ``bind_identity(platform, user_id=user_id, deny=True)``。

- **platform** (`平台名称`): - **user_id**: 用户 ID
- **persist** (`是否持久化到配置文件`): (默认: True)

---


##### `unblock_user(platform: str, user_id: str, persist: bool = True)`

取消拉黑用户（移除该用户的准入绑定）

**返回值** (`是否成功移除（该用户本无绑定或绑定非`): deny 时返回 False）

---


##### `_acl_mutate(command_name: str, list_name: str, platform: str, user_id: str)`

> **内部方法**
增删命令 ACL 名单成员

- **command_name** (`命令名（可含`): glob / ``re:`` 模式）
- **list_name** (`名单名（"allow"`): / "deny"）
- **platform** (`用户所属平台`): - **user_id**: 用户 ID
- **remove** (`是否移除（True`): 移除成员，False 追加成员）
- **persist**: 是否持久化

---


##### `allow_user(command_name: str, platform: str, user_id: str, persist: bool = True)`

将用户加入命令的 allow 名单（白名单非空时仅名单内用户可执行）

命令名支持 glob / ``re:`` 正则。

**示例**:
```python
>>> scope.allow_user("roll*", "onebot11", "123456")
```

---


##### `deny_user(command_name: str, platform: str, user_id: str, persist: bool = True)`

将用户加入命令的 deny 名单（deny 优先于 allow 与默认权限）

命令名支持 glob / ``re:`` 正则。

**示例**:
```python
>>> scope.deny_user("roll*", "onebot11", "666")
```

---


##### `get_acl(command_name: str)`

查询命令当前的用户黑白名单

- **command_name** (`命令名（可含模式）`): **返回值** (`{"allow":`): [...], "deny": [...]}（用户标识 "platform:user_id"）

---


##### `remove_acl(command_name: str, persist: bool = True)`

清除命令的用户黑白名单（恢复开发者默认权限逻辑）

- **command_name** (`命令名（可含模式）`): - **persist**: 是否持久化
**返回值**: 是否存在并被清除

---


##### `_action_cfg(owner: str)`

> **内部方法**
读取模块的出站动作配置

- **owner** (`模块名（owner），无`): owner 时返回 None
**返回值** (`动作开关字典（{"send":`): bool, "api": bool, "request": bool}），未配置返回 None

---


##### `is_action_allowed(owner: str, action: str)`

判断模块是否允许执行某类出站动作（⑥ 出站动作维度）

判定语义：**默认允许**——未配置、或 owner 为空（框架层调用）均视为允许；
仅当用户显式禁用（``scope.actions.<owner>.<action> = false``）才拒绝。
与身份/命令维度的"默认允许兜底"不同，本维度是出站能力的收紧开关，
空白即放行，声明式禁用。

- **owner** (`模块名（owner）`): - **action**: 动作类型，取值 ``_ACTION_NAMES``（"send" / "api" / "request"）
**返回值**: 是否允许执行

---


##### `set_action(owner: str, action: str, allowed: bool, persist: bool = True)`

设置模块某类出站动作的允许/禁用（⑥ 出站动作维度）

仅影响本模块从事件处理器（handler 执行期 owner 上下文）发起的出站调用。
不影响框架层内部调用（owner 为空时恒放行）。

- **owner** (`模块名（owner）`): - **action**: 动作类型（"send" / "api" / "request"）
- **allowed** (`False`): 禁止该动作，True 允许
- **persist** (`是否持久化`): (默认: True)

**示例**:
```python
>>> scope.set_action("MyModule", "send", False)  # 禁止 MyModule 回复消息
>>> scope.set_action("MyModule", "api", False)  # 禁止 MyModule 调用标准 API
>>> scope.set_action("MyModule", "request", False)  # 禁止 MyModule 处理请求操作
```

---


##### `unset_action(owner: str, action: str | None = None, persist: bool = True)`

移除模块的出站动作限制（恢复默认允许）

- **owner** (`模块名`): - **action**: 动作类型；None 表示移除该模块全部动作限制
- **persist** (`是否持久化`): **返回值**: 是否有内容被移除

---


##### `get_action_rules(owner: str)`

查询模块当前的出站动作限制

- **owner** (`模块名`): **返回值** (`动作开关字典（含默认允许的未配置项为`): True）

---


##### `bind_handler(owner: str, pattern: str | None = None, regex: str | None = None, persist: bool = True)`

绑定模块的文本过滤条件（④ 处理器维度）

- **owner** (`模块名`): - **pattern**: glob 通配符，不匹配的消息不触发该模块处理器
- **regex** (`正则源码（可带`): ``re:`` 前缀），与 pattern 同时给定时须都命中
- **persist** (`是否持久化`): (默认: True)

---


##### `unbind_handler(owner: str, persist: bool = True)`

移除模块的文本过滤条件

**返回值**: 是否成功移除

---


##### `override(owner: str, command_name: str | None = None, persist: bool = True)`

覆盖模块 / 命令的实现参数（⑤ 覆盖维度）

覆盖遵循**用户优先**：显式设置的参数直接生效（可收紧也可放开开发者默认）。
覆盖值只影响**实现参数**（master / hidden / aliases / prefix 等），
不用于禁用——禁用统一走命令 deny（``deny_user`` / ``scope.commands``）。

- **owner** (`模块名`): - **command_name**: 命令名；None 表示模块级覆盖
- **persist** (`是否持久化`): (默认: True)
- **params** (`要覆盖的参数（如`): ``master=True`` 收紧、``master=False`` 放开、``hidden=True``、``aliases=["rs"]``）

**示例**:
```python
>>> scope.override("MyModule", "restart", master=True, hidden=True)
```

---


##### `remove_override(owner: str, command_name: str | None = None, persist: bool = True)`

移除模块 / 命令的实现参数覆盖

**返回值**: 是否成功移除

---


##### `list_bindings()`

列出全部控制面绑定（含出站动作维度）

**返回值** (`{"platforms",`): "bots", "sessions", "identity", "commands",
        "handlers", "overrides", "actions"} 结构（深拷贝）

---


##### `clear()`

清空所有控制面绑定（仅内存生效，不持久化）

---


##### `get_stats()`

获取控制面运行统计

统计项：``module_calls`` / ``module_filtered``（模块维度）、
``identity_checks`` / ``identity_denied``（身份维度）、
``command_checks`` / ``command_denied``（命令维度）、
``action_checks`` / ``action_denied``（出站动作维度）、
``cache_hits`` / ``cache_misses``（模块维度 LRU）。

**返回值**: 统计字典

---


##### `reset_stats()`

重置控制面运行统计

---


##### `get_topology()`

获取控制面绑定的结构化数据（便于 WebUI 展示拓扑树）

**返回值** (`全维度绑定结构（模块`): / 身份 / 命令 / 处理器 / 覆盖 / 出站动作）

---


##### `_raw_get(bucket: str, platform: str, key: str)`

> **内部方法** 读取指定模块绑定（供 merge 使用，浅拷贝）

---


##### `_resolve_module_target(platform: str, bot_id: str | None, session_id: str | None)`

> **内部方法**
根据参数解析模块维度目标桶与键

**返回值** (`(bucket,`): key) 元组

---


##### `_resolve_identity_target(platform: str, bot_id: str | None, session_id: str | None, user_id: str | None)`

> **内部方法**
根据参数解析身份维度目标桶与键（用户级 > 会话级 > Bot 级 > 适配器级）

**返回值** (`(bucket,`): key) 元组

---


##### `_logger_trace(message: str)`

> **内部方法** 输出 TRACE 日志（logger 未就绪时静默）

---


##### `_raw_bindings()`

> **内部方法** 读取当前绑定缓存（深拷贝，避免外部篡改）

---

