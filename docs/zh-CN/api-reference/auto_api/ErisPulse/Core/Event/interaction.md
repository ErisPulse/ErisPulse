# `ErisPulse.Core.Event.interaction` 模块

---

## 模块概述


ErisPulse 交互会话管理

提供跨模块的交互会话（等待回复 / 会话租约）统一管理：

- **等待回复**：``command.wait_reply`` / ``Conversation`` 等交互式方法的底层等待表，
  按 ``platform:bot:user:target`` 会话键索引，支持 pattern / regex / validator 过滤；
- **归属维度**：每条等待记录注册时的 owner（模块名），模块卸载 / 适配器关闭时
  按维度精确取消挂起的等待，等待方立即收到 :class:`InteractionCancelled` 而非干等超时；
- **权限复查**：回复命中时复查 scope 身份维度（用户被拉黑）与模块维度
  （owner 模块在该会话被解绑），任一失败终止会话；
- **会话互斥**：``acquire()`` 声明对某会话的独占租约，其他模块的 ``acquire``
  与 ``wait_reply`` 可据此感知"该用户正被谁占用"。

> **提示**
> 使用方式::
> from ErisPulse.Core.Event.interaction import interaction
> # 查询会话当前归属（谁正在与该用户交互）
> owner = interaction.get_owner_of(event)
> # 声明会话互斥租约（deny 策略：被占用时返回 None）
> lease = interaction.acquire(event)
> if lease is None:
> ...  # 会话被其他模块占用
> try:
> ...  # 独占交互
> finally:
> lease.release()
> # 上下文管理器形式
> with interaction.hold(event) as lease:
> ...
> 模块卸载 / 适配器关闭时，框架自动调用 ``cancel_by_owner`` / ``cancel_by_platform``
> 清理对应挂起会话，无需手动干预。

---

## 类列表


### `class InteractionCancelled(InteractionError)`

交互会话被取消

挂起的 ``wait_reply`` / 租约因非超时原因终止时设置到 future 上，
等待方可捕获本异常获取原因；上层 ``wait_reply`` 将其转换为返回 None。

:attribute reason: 取消原因（conflict / owner_unload / platform_stop / revoked / cancelled / cleared）
:attribute wait_key: 关联的会话键


### `class _Entry`

> **内部方法** 交互会话条目（等待回复或互斥租约）


### `class InteractionLease`

会话互斥租约

由 :meth:`InteractionManager.acquire` 创建，声明对某会话（platform:bot:user:target）
的独占占用。持有期间其他模块对该会话的 ``acquire`` 返回 None，
新的 ``wait_reply`` 也会因会话被占用而无法与您的等待混淆（占用不阻断已有等待，
但会拒绝新的租约竞争者）。

支持同步上下文管理器用法；租约到期后自动失效（惰性检查），release 可提前释放。


#### 方法列表


##### `expired()`

租约是否已过期

---


##### `renew(ttl: float | None = None)`

续租

- **ttl** (`续租时长（秒），None`): 表示使用原 TTL
**返回值**: 是否续租成功（会话已被他人抢占时失败）

---


##### `release()`

释放租约

**返回值** (`是否释放成功（已过期或被抢占时返回`): False）

---


### `class InteractionManager`

交互会话管理器

统一管理等待回复与会话租约，按会话键（platform:bot:user:target）唯一索引，
并维护 owner（归属模块）与 platform（适配器）两个反向索引，
支持按维度精确取消挂起会话。


#### 方法列表


##### `make_key(event: Any)`

> **内部方法**
从事件推导会话键（platform:bot:user:target）

与命令等待回复的推导规则一致；事件可能为 Event 包装类或原始 dict。

- **event** (`事件数据（Event`): 或 dict）
**返回值**: 会话键字符串

---


##### `_index_add(entry: _Entry)`

> **内部方法** 将条目加入反向索引

---


##### `_index_remove(entry: _Entry)`

> **内部方法** 将条目从反向索引移除

---


##### `_remove(key: str)`

> **内部方法** 移除条目并维护索引，返回被移除的条目

---


##### `register(event: Any, future: asyncio.Future, callback: Any = None, validator: Any = None, pattern: str | None = None, regex: str | None = None, owner: str | None = None)`

> **内部方法**
注册等待回复条目

同一会话键已有等待时，旧等待被取消（等待方收到
:class:`InteractionCancelled`（reason="conflict"）），
修复旧实现中相互覆盖导致旧方干等超时的问题。

- **event** (`触发等待的原始事件`): - **future**: 回复到达时 set_result 的 future
- **callback** (`回复回调（由调用方在`): wait_reply 中执行）
- **validator** (`回复验证函数，验证失败则继续等待`): - **pattern**: glob 文本过滤
- **regex** (`正则文本过滤`): - **owner**: 归属者（模块名），None 时从 current_owner 上下文捕获
**返回值**: 注册的条目（含推导的会话键）

---


##### `async resolve(event: 'Event')`

> **内部方法**
尝试将消息事件匹配到挂起的等待（回复命中判定链）

判定链：会话键命中 → pattern/regex 过滤 → validator 校验 →
权限复查（scope 身份维度 + owner 模块维度）→ 唤醒等待方并认领事件。

权限复查失败时终止整个等待（等待方收到 InteractionCancelled），
消息本身不消费、继续走常规处理。

- **event** (`消息事件（Event`): 包装类）
**返回值** (`是否命中并消费了等待（True`): 时事件已被 mark_processed）

---


##### `_check_revoked(entry: _Entry, event: 'Event')`

> **内部方法**
回复命中的权限复查

- **entry** (`等待条目`): - **event**: 回复事件
**返回值** (`撤销原因描述；通过复查时返回`): None

---


##### `_cancel_entry(key: str, entry: _Entry, reason: str)`

> **内部方法** 取消条目：移除索引并向等待方投递取消

---


##### `cancel(key: str, reason: str = REASON_CANCELLED)`

取消指定会话键上的等待 / 租约

- **key** (`会话键（platform:bot:user:target）`): - **reason**: 取消原因
**返回值**: 是否存在并取消了条目

---


##### `cancel_by_owner(owner: str)`

按归属者取消所有挂起会话（模块卸载链路调用）

- **owner** (`归属者（模块名）`): **返回值**: 取消的会话数量

---


##### `cancel_by_platform(platform: str)`

按平台取消所有挂起会话（适配器关闭链路调用）

- **platform** (`平台名称`): **返回值**: 取消的会话数量

---


##### `clear()`

清除所有挂起会话（框架关闭链路调用）

**返回值**: 清除的会话数量

---


##### `_get_active_entry(key: str)`

> **内部方法** 获取会话键上的活跃条目（租约惰性过期）

---


##### `get_owner_of(event: Any)`

查询会话当前归属（谁正在与该用户交互）

可用于发送前避免打扰正在对话中的用户、或实现跨模块会话协调。

- **event** (`事件数据（Event`): 或 dict，用于推导会话键）
**返回值** (`占用者的`): owner（模块名）；会话空闲时返回 None

**示例**:
```python
>>> owner = sdk.interaction.get_owner_of(event)
>>> if owner and owner != "MyModule":
...     ...  # 该用户正被其他模块占用
```

---


##### `acquire(event: Any, owner: str | None = None, ttl: float = DEFAULT_INTERACTION_LEASE_TTL_SECS)`

获取会话互斥租约（deny 策略：被占用时返回 None）

会话空闲时创建租约；已被等待回复或其他租约占用时返回 None。
租约到期自动失效（惰性检查），也可显式 ``release()`` / ``renew()``。

- **event** (`事件数据（Event`): 或 dict，用于推导会话键）
- **owner** (`归属者（模块名），None`): 时从 current_owner 上下文捕获
- **ttl** (`租约存活时间（秒）`): **返回值** (`租约对象；会话被占用时返回`): None

**示例**:
```python
>>> lease = sdk.interaction.acquire(event)
>>> if lease is None:
...     return  # 会话正被其他模块占用
>>> try:
...     ...  # 独占交互
... finally:
...     lease.release()
```

---


##### `hold(event: Any, owner: str | None = None, ttl: float = DEFAULT_INTERACTION_LEASE_TTL_SECS)`

会话互斥租约的上下文管理器形式

退出时自动释放；获取失败抛出 :class:`SessionOccupiedError`。

- **event** (`事件数据`): - **owner**: 归属者（模块名），None 时从 current_owner 上下文捕获
- **ttl** (`租约存活时间（秒）`): **返回值** (`上下文管理器，yield`): :class:`InteractionLease`
**异常**: `SessionOccupiedError` - 会话已被其他 owner 占用时

**示例**:
```python
>>> with sdk.interaction.hold(event) as lease:
...     ...  # 独占交互，退出自动释放
```

---


##### `release(key: str, owner: str | None = None)`

释放指定会话的租约

仅租约持有者（owner 匹配）可释放；owner 为 None 时仅当租约无归属才可释放。

- **key** (`会话键或事件数据`): - **owner**: 请求释放者的 owner
**返回值**: 是否释放成功

---


##### `_renew_lease(entry: _Entry, ttl: float | None)`

> **内部方法** 续租

---


##### `counts()`

获取挂起会话统计（诊断用）

**返回值** (`含`): waits / leases / owners 计数的字典

**示例**:
```python
>>> sdk.interaction.counts()
{'waits': 2, 'leases': 1, 'owners': {'Chat': 3}}
```

---


### `class SessionOccupiedError(InteractionError)`

会话已被其他模块占用（:meth:`InteractionManager.hold` 获取失败时抛出）


### `class _LeaseContext`

> **内部方法** hold() 的上下文管理器实现

