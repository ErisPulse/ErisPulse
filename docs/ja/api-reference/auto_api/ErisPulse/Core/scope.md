# `ErisPulse.Core.scope` 模块

---

## 模块概述


ErisPulse 作用域（scope）

控制权完全交给用户：在模块 / 适配器 / 处理器 / 出站调用注册的**上层**
（配置 ``ErisPulse.scope`` 或运行时 ``sdk.scope``）统一声明"**什么范围内生效**"。
事件管线在入口、处理器过滤与出站闸口自动读取并执行。

作用域按事件处理生命周期回答三个问题：

- 模块维度：某个上下文里哪些模块可用（平台 / Bot / 会话三级绑定）
- 身份维度：谁的事件收不收（适配器 / Bot / 会话 / 用户四级策略）
- 出站维度：模块能向外做什么（限制模块发起消息发送 / 标准 API 动作 / 请求操作）

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
    merge = true                  # 在平台级绑定基础上追加（默认整体覆盖）
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

    # ③ 出站维度：限制模块发起出站动作（默认全允许，显式收紧才禁）
    [ErisPulse.scope.actions.MyModule]
    send = { deny = true }                                   # 全禁发送
    send = { allow = ["Text", "Image*"], deny = ["File"] }   # 方法级细粒度
    api = { allow = ["get_*"] }                              # 仅允许查询类 API
    request = { deny = true }                                # 禁止处理请求

匹配条目统一语法（见 :mod:`ErisPulse.Core.text_match`）：
**精确名** / **glob**（``*`` / ``?`` / ``[seq]``）/ **``re:`` 正则**，默认大小写不敏感。

> **提示**
> 1. 通过 ``from ErisPulse.Core import scope`` 导入单例（``sdk.scope`` 同对象）
> 2. 判定：``scope.is_allowed(...)`` / ``scope.is_identity_allowed(...)`` /
> ``scope.is_action_allowed(...)`` —— 对应 ①②④ 三个判定闸口
> 3. 读写：像字典一样用点分路径操作任意配置节 ——
> ``scope.get("platforms.onebot11")`` / ``scope.set("actions.My", {...})`` /
> ``scope.delete("actions.My.send")``，也支持 ``scope[key]`` / ``scope[key] = v`` / ``del scope[key]``
> 4. 事件处理器文本条件覆写见 :mod:`ErisPulse.Core.Event.overrides`；
> 命令 ACL / 参数覆写见 :mod:`ErisPulse.Core.Event.command`

---

## 函数列表


### `_is_identity_binding(binding)`

> **内部方法**
读取身份绑定的策略（deny 优先于 allow）

- **binding** (`绑定字典（{"allow":`): true} 或 {"deny": true}）
**返回值** (`"allow"`): / "deny"；未配置或格式非法时返回 None

---


### `_normalize_action_rule(rule)`

> **内部方法**
归一化出站动作规则

合法输入形态：

- ``True`` → ``{}``（无限制，等价未配置）
- ``False`` → ``{"deny": True}``（全禁）
- dict → 仅保留 ``allow``（字符串列表）与 ``deny``（布尔或字符串列表）键

- **rule** (`配置中的动作规则（bool`): / dict）
**返回值** (`规范化规则字典；allow`): / deny 类型非法时返回 None

---


### `_deep_merge(dst: dict, src: dict)`

> **内部方法** 把 src 深合并进 dst（原地修改）

---


## 类列表


### `class ScopeManager`

作用域管理器（单例）

统一管理三维作用域配置（模块 / 身份 / 出站），配置即一棵
``ErisPulse.scope`` 字典树。API 面向原生字典风格收敛：

- **判定**：:meth:`is_allowed` / :meth:`is_identity_allowed` /
  :meth:`is_action_allowed`（三个闸口的问询）
- **读写**：:meth:`get` / :meth:`set` / :meth:`delete`（点分路径直达任意节，
  同时支持 ``scope[path]`` / ``scope[path] = value`` / ``del scope[path]``）
- **全局**：:meth:`clear` / :meth:`stats` / :meth:`reset_stats` / :meth:`topology`

支持配置热更新、LRU 缓存与运行统计。
命令 ACL / 参数覆写由命令系统自持（``ErisPulse.event.command``）。


#### 方法列表


##### `_warn_invalid(path: str, actual: str)`

> **内部方法** 输出配置格式告警（同一路径去重）

---


##### `_validated_bucket(config: dict, key: str)`

> **内部方法** 读取并校验一个 dict 型配置节（非法时告警并忽略）

---


##### `_load_config()`

> **内部方法** 从配置加载配置树（含格式校验）

---


##### `_apply_tree(tree: dict)`

> **内部方法** 校验并应用配置树到内存（含格式校验）

---


##### `_validated_actions(scope_config: dict)`

> **内部方法** 加载并校验出站动作规则

---


##### `_on_config_updated(_data: dict)`

配置变更回调：重建配置树

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


##### `_effective_module_cfg(platform: str, bot_id: str | None, session_id: str | None)`

> **内部方法**
沿"平台 → Bot → 会话"解析链计算生效的模块绑定

默认语义为**整体覆盖**：高优先级绑定完整替换低优先级；
子级绑定含 ``merge = true`` 时与低优先级**逐条目并集**
（modules / blocked 各自取并集）。``merge`` 为控制键，不进入条目。

- **platform** (`平台名称`): - **bot_id**: Bot 用户 ID，None 表示不匹配 Bot 级
- **session_id** (`会话`): ID（群 / 频道 / 私聊），None 表示不匹配会话级
**返回值** (`生效绑定`): {"modules": [...], "blocked": [...]}，无绑定时返回 None

---


##### `_get_binding(platform: str, bot_id: str | None, session_id: str | None)`

> **内部方法**
获取平台 / Bot / 会话的生效模块绑定（含 merge 链式合并）

- **platform** (`平台名称`): - **bot_id**: Bot 用户 ID，None 表示不匹配 Bot 级
- **session_id** (`会话`): ID（群 / 频道 / 私聊），None 表示不匹配会话级
**返回值** (`(modules`): 匹配器, blocked 匹配器) 或 None

---


##### `is_allowed(platform: str, bot_id: str | None, module_name: str | None, session_id: str | None = None)`

判断模块是否允许在指定 Bot / 会话使用（① 模块维度）

模块名匹配大小写不敏感，条目支持 glob / ``re:`` 正则。
结果带 LRU 缓存，配置变更 / set / delete 时自动失效。
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

判断事件是否放行（② 身份维度：谁的事件收不收）

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


##### `is_action_allowed(owner: str, action: str, name: str | None = None)`

判断模块是否允许执行某类出站动作（④ 出站维度）

判定语义：**默认允许**——未配置、或 owner 为空（框架层调用）均视为允许。
规则判定顺序：``deny = true`` → 拒绝；``deny`` 列表命中 ``name`` → 拒绝；
``allow`` 列表非空且 ``name`` 未命中（或未提供）→ 拒绝；其余放行。
结果带 LRU 缓存，配置变更 / set / delete 时自动失效。

- **owner** (`模块名（owner）`): - **action**: 动作类型，取值 ``_ACTION_NAMES``（"send" / "api" / "request"）
- **name** (`具体调用名（send`): 传发送方法名如 "Text" / "Image"，
             api 传标准动作名如 "get_group_info"；request 无需提供）
**返回值** (`是否允许执行`): 
**示例**:
```python
>>> scope.is_action_allowed("MyModule", "send")
True
>>> scope.is_action_allowed("MyModule", "send", name="Image")
False
```

---


##### `_compute_action_allowed(owner: str, action: str, name: str | None)`

> **内部方法** 计算出站动作是否允许（无缓存）

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


##### `_logger_trace(message: str)`

> **内部方法** 输出 TRACE 日志（logger 未就绪时静默）

---


##### `_module_path(platform: str, bot_id: str | None, session_id: str | None)`

> **内部方法** 模块维度路径（会话 > Bot > 平台）

---


##### `_identity_path(platform: str, bot_id: str | None, session_id: str | None, user_id: str | None)`

> **内部方法** 身份维度路径（用户 > 会话 > Bot > 适配器）

---


##### `set_module(platform: str, bot_id: str | None = None, session_id: str | None = None)`

绑定模块作用域（① 模块维度）

- **platform** (`平台名称`): - **bot_id**: Bot 用户 ID，None 且 session_id 为空时绑定平台级
- **session_id** (`会话`): ID（群 / 频道 / 私聊）。指定时绑定该会话；
                   否则有 bot_id 时绑定该 Bot；否则绑定平台级
- **modules** (`白名单模块条目（精确`): / glob / ``re:`` 正则）
- **blocked** (`黑名单模块条目`): - **merge**: True 时与该级现有绑定**逐条目并集**（modules / blocked 各自合并），
              False 整体替换该节点（默认）
- **persist** (`是否持久化到配置文件`): (默认: True)

**示例**:
```python
>>> scope.set_module("onebot11", bot_id="123456", modules=["Chat", "Tool*"])
>>> scope.set_module("onebot11", bot_id="123456", modules=["Music"], merge=True)
```

---


##### `get_module(platform: str, bot_id: str | None = None, session_id: str | None = None, default = None)`

读取该层级原始模块绑定（不含 merge 跨级合并的最终生效结果，
需判定生效性请用 :meth:`is_allowed`）

- **platform** (`平台名称`): - **bot_id**: Bot 用户 ID
- **session_id** (`会话`): ID
- **default** (`无绑定时返回值（默认`): None）
**返回值** (```{"modules":`): [...], "blocked": [...]}`` 或 default

---


##### `delete_module(platform: str, bot_id: str | None = None, session_id: str | None = None, persist: bool = True)`

移除该层级模块绑定（恢复 default_allow 兜底）

- **platform** (`平台名称`): - **bot_id**: Bot 用户 ID
- **session_id** (`会话`): ID
- **persist** (`是否持久化到配置文件`): (默认: True)
**返回值**: 是否存在并被删除

---


##### `set_identity(platform: str, bot_id: str | None = None, session_id: str | None = None, user_id: str | None = None)`

绑定身份准入策略（② 身份维度，层级由参数决定：用户 > 会话 > Bot > 适配器）

绑定键支持 glob / ``re:`` 正则（如 ``user_id="spam_*"``）。

- **platform** (`平台名称`): - **bot_id**: Bot 用户 ID
- **session_id** (`会话`): ID
- **user_id** (`用户`): ID
- **allow** (`放行该来源事件`): - **deny**: 拒绝该来源事件（allow 与 deny 同时给定时以 deny 为准）
- **persist** (`是否持久化到配置文件`): (默认: True)

**示例**:
```python
>>> scope.set_identity("onebot11", user_id="u_bad", deny=True)   # 拉黑
>>> scope.set_identity("onebot11", user_id="spam_*", deny=True)  # glob 批量拉黑
>>> scope.set_identity("onebot11", session_id="g1", allow=True)  # 例外放行
```

---


##### `get_identity(platform: str, bot_id: str | None = None, session_id: str | None = None, user_id: str | None = None, default = None)`

读取该来源的身份绑定（原始配置形态，含 glob 键不展开；
需判定生效性请用 :meth:`is_identity_allowed`）

- **platform** (`平台名称`): - **bot_id**: Bot 用户 ID
- **session_id** (`会话`): ID
- **user_id** (`用户`): ID
- **default** (`无绑定时返回值（默认`): None）
**返回值** (```{"allow":`): True}`` / ``{"deny": True}`` 或 default

---


##### `delete_identity(platform: str, bot_id: str | None = None, session_id: str | None = None, user_id: str | None = None, persist: bool = True)`

移除该来源的身份绑定（恢复 default_allow 兜底）

- **platform** (`平台名称`): - **bot_id**: Bot 用户 ID
- **session_id** (`会话`): ID
- **user_id** (`用户`): ID
- **persist** (`是否持久化到配置文件`): (默认: True)
**返回值**: 是否存在并被删除

---


##### `set_action(module: str, action: str)`

设置模块某类出站动作的限制规则（③ 出站维度）

仅影响本模块从事件处理器（handler 执行期 owner 上下文）发起的出站调用；
框架层内部调用（owner 为空）恒放行。

- **module** (`模块名`): - **action**: 动作类型（"send" / "api" / "request"）
- **allow** (`白名单条目（str`): 或 list；send 匹配发送方法名、api 匹配标准动作名）
- **deny** (`全禁（True）或黑名单条目（str`): / list）
- **persist** (`是否持久化到配置文件`): (默认: True)

**示例**:
```python
>>> scope.set_action("MyModule", "send", deny=True)                # 全禁发送
>>> scope.set_action("MyModule", "send", allow=["Text"])           # 仅允许发文本
>>> scope.set_action("MyModule", "api", deny=["set_*", "leave_*"]) # 禁管理类 API
```

---


##### `get_action(module: str, action: str, default = None)`

读取模块某类出站动作的原始规则（bool 原样存储，判定层归一化）

- **module** (`模块名`): - **action**: 动作类型
- **default** (`未配置时返回值（默认`): None）
**返回值** (```{"allow":`): [...], "deny": ...}`` / ``False`` 等原始形态或 default

---


##### `delete_action(module: str, action: str | None = None, persist: bool = True)`

移除模块的出站动作限制（恢复默认允许）

- **module** (`模块名`): - **action**: 动作类型；None 表示移除该模块全部动作限制
- **persist** (`是否持久化到配置文件`): (默认: True)
**返回值**: 是否有内容被移除

---


##### `_split_path(path: str)`

> **内部方法** 点分路径切分为段（过滤空段）

---


##### `_node_at(path: str)`

> **内部方法** 按点分路径取节点（不存在返回 None）

---


##### `get(path: str, default = None)`

读取作用域配置树中任意节（深拷贝）

- **path** (`点分路径，如`): ``"platforms.onebot11"``、``"identity.users.onebot11"``
             （身份）、``"actions.MyModule"``（出站）；
             空路径返回整棵树
- **default** (`节不存在时的返回值（默认`): None）
**返回值** (`节的深拷贝；不存在时返回`): ``default``

**示例**:
```python
>>> scope.get("actions.MyModule.send", {})
{"deny": True}
```

---


##### `set(path: str, value, persist: bool = True)`

写入作用域配置树中任意节（dict 深合并，标量直接覆盖）

写入后判定缓存自动失效，配置即时生效。

- **path** (`点分路径，如`): ``"bots.onebot11.123456"``（模块绑定）、
             ``"identity.users.onebot11.u_bad"``（拉黑用户）、
             
             ``"actions.MyModule.send"``（出站规则）
- **value** (`写入值（dict`): 时与现有值深合并，其余类型直接覆盖）
- **persist** (`是否持久化到配置文件`): (默认: True)

**示例**:
```python
>>> scope.set("bots.onebot11.123456", {"modules": ["Chat"], "blocked": []})
>>> scope.set("identity.users.onebot11.u_bad", {"deny": True})   # 拉黑用户
>>> scope.set("actions.MyModule.send", {"deny": True})           # 全禁发送
```

---


##### `delete(path: str, persist: bool = True)`

删除作用域配置树中任意键（父节经整节替换持久化，支持级联清空空父节）

- **path** (`点分路径，如`): ``"bots.onebot11.123456"``、
             ``"identity.users.onebot11.u_bad"``、``"actions.MyModule.send"``
- **persist** (`是否持久化到配置文件`): (默认: True)
**返回值** (`是否存在并被删除`): 
**示例**:
```python
>>> scope.delete("bots.onebot11.123456")       # 移除 Bot 绑定
>>> scope.delete("identity.users.onebot11.u_bad")  # 取消拉黑
>>> scope.delete("actions.MyModule")           # 解除模块全部出站限制
```

---


##### `__getitem__(path: str)`

``scope[path]``：等价 :meth:`get`，节点不存在时抛 KeyError

---


##### `__setitem__(path: str, value)`

``scope[path] = value``：等价 :meth:`set`（默认持久化）

---


##### `__delitem__(path: str)`

``del scope[path]``：等价 :meth:`delete`，不存在时抛 KeyError

---


##### `__contains__(path: str)`

``path in scope``：判断配置树中是否存在该节点

---


##### `clear()`

清空所有作用域配置（仅内存生效，不持久化）

---


##### `stats()`

获取作用域运行统计

统计项：``module_calls`` / ``module_filtered``（模块维度）、
``identity_checks`` / ``identity_denied``（身份维度）、
``action_checks`` / ``action_denied``（出站维度）、
``cache_hits`` / ``cache_misses``（LRU 缓存）。

**返回值**: 统计字典

---


##### `reset_stats()`

重置作用域运行统计

---


##### `topology()`

获取作用域配置的结构化数据（便于 WebUI 展示拓扑树）

等价于整棵配置树的深拷贝。

**返回值** (`全维度配置结构（模块`): / 身份 / 文本 / 出站动作）

---

