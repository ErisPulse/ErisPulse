# `ErisPulse.Core.scope` 模块

---

## 模块概述


ErisPulse 作用域系统

提供模块与适配器 Bot / 平台 / 会话之间的绑定能力，控制"某个 Bot 只能使用哪些模块"。
默认情况下所有模块对所有 Bot 开放；仅在配置了绑定后才开始过滤，完全向后兼容，
模块与适配器无需任何改动即可适配作用域。

作用域配置位于 ``ErisPulse.scope``，支持三级绑定：

1. **平台级**（作用于该平台所有 Bot / 会话）：
   ``ErisPulse.scope.platforms.<platform>.modules / blocked``
2. **Bot 级**（作用于该 Bot 的所有会话）：
   ``ErisPulse.scope.bots.<platform>.<bot_id>.modules / blocked``
3. **会话级**（最具体，作用于某个群 / 频道 / 私聊）：
   ``ErisPulse.scope.sessions.<platform>.<session_id>.modules / blocked``

解析优先级：**会话级 > Bot 级 > 平台级**。模块名匹配**大小写不敏感**。

语义：
- ``modules``（白名单）非空时，只有列出的模块允许使用
- ``blocked``（黑名单）中的模块被禁用
- 两者均未配置时，遵循 ``default_allow``（默认允许全部；设为 false 则隐式拒绝）
- 被作用域禁用的模块收到消息时静默忽略，不回复提示

> **提示**
> 1. 通过 ``from ErisPulse.Core import scope`` 导入单例
> 2. ``scope.is_allowed(platform, bot_id, module, session_id)`` 判断模块是否可用
> 3. ``scope.bind()`` 默认替换绑定，``merge=True`` 可合并
> 4. ``scope.get_stats()`` 查看过滤统计（调试被静默忽略的模块）
> 5. ``scope.default_allow`` 设为 false 可开启"隐式拒绝"严格模式

---

## 类列表


### `class ScopeManager`

作用域管理器（单例）

从配置读取模块-Bot/平台/会话绑定，并支持运行时增删。
判断逻辑：会话级绑定优先于 Bot 级，Bot 级优先于平台级，均未配置时遵循 default_allow。


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
归一化绑定配置为 (白名单集合, 黑名单集合)

模块名统一转小写，实现大小写不敏感匹配。

- **cfg** (`绑定配置字典（可含`): modules / blocked 字段）
**返回值** (`(modules`): 集合, blocked 集合)

---


##### `_get_binding(platform: str, bot_id: str | None, session_id: str | None)`

> **内部方法**
获取平台 / Bot / 会话的生效绑定

解析优先级：会话级 > Bot 级 > 平台级；均不存在时返回 None。

- **platform** (`平台名称`): - **bot_id**: Bot 用户 ID，None 表示不匹配 Bot 级
- **session_id** (`会话`): ID（群 / 频道 / 私聊），None 表示不匹配会话级
**返回值** (`(allow,`): blocked) 或 None

---


##### `is_allowed(platform: str, bot_id: str | None, module_name: str | None, session_id: str | None = None)`

判断模块是否允许在指定 Bot / 会话使用

模块名匹配大小写不敏感。结果带 LRU 缓存，配置变更 / bind / unbind 时自动失效。
无绑定（默认）时遵循 ``default_allow``（默认允许全部）；模块名为空（框架层资源）始终放行。

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


##### `_put_cache(key: tuple, value: bool)`

> **内部方法** 写入 LRU 缓存（超过容量时淘汰最旧）

---


##### `bot_id_from_event(event: dict)`

从事件数据提取 Bot 标识

- **event** (`事件数据（dict`): 或 Event 包装对象）
**返回值** (`Bot`): 标识（account_id 优先，回退 user_id），无法识别时返回空字符串

---


##### `session_id_from_event(event: dict)`

从事件数据提取会话标识（群 / 频道 / 私聊的目标 ID）

- **event** (`事件数据（dict`): 或 Event 包装对象）
**返回值** (`会话`): ID（如 group_id / channel_id / user_id），无法识别时返回空字符串

---


##### `get(platform: str, bot_id: str | None = None, session_id: str | None = None)`

获取平台 / Bot / 会话的生效绑定

- **platform** (`平台名称`): - **bot_id**: Bot 用户 ID，None 表示不匹配 Bot 级
- **session_id** (`会话`): ID，None 表示不匹配会话级
**返回值** (`{"modules":`): [...], "blocked": [...]}，无绑定时返回 None

**示例**:
```python
>>> scope.get("onebot11", "123456")
{"modules": ["Chat"], "blocked": []}
>>> scope.get("onebot11", "123456", "group_9")
{"modules": ["Chat"], "blocked": []}
```

---


##### `bind(platform: str, bot_id: str | None = None, session_id: str | None = None)`

绑定模块作用域

- **platform** (`平台名称`): - **bot_id**: Bot 用户 ID，None 且 session_id 为空时表示平台级绑定
- **session_id** (`会话`): ID（群 / 频道 / 私聊）。指定时绑定到该会话；
                   否则有 bot_id 时绑定到该 Bot；否则绑定到平台级
- **modules** (`白名单模块列表，None`): / 空列表表示不限制
- **blocked** (`黑名单模块列表，None`): / 空列表表示不限制
- **persist** (`是否持久化到配置文件`): (默认: True)
                 为 False 时仅本次运行生效，重启后失效
- **merge** (`是否**合并**而非替换现有绑定（默认`): False）。
              merge=True 时，新模块并入现有白名单、新禁用并入现有黑名单；
              merge=False（默认）时整体替换。

**示例**:
```python
>>> scope.bind("onebot11", "123456", modules=["Chat"])
>>> scope.bind("onebot11", "123456", "group_9", modules=["Chat"])  # 会话级
>>> scope.bind("onebot11", blocked=["Danger"])  # 平台级黑名单
>>> scope.bind("onebot11", "123456", [], [], persist=False)  # 仅运行时
>>> scope.bind("onebot11", "123456", modules=["Music"], merge=True)  # 追加
```

---


##### `unbind(platform: str, bot_id: str | None = None, session_id: str | None = None, persist: bool = True)`

移除平台 / Bot / 会话的作用域绑定（恢复为允许全部模块）

- **platform** (`平台名称`): - **bot_id**: Bot 用户 ID，None 且 session_id 为空时表示移除平台级绑定
- **session_id** (`会话`): ID。指定时移除会话级绑定；否则有 bot_id 时移除 Bot 级
- **persist** (`是否持久化移除`): (默认: True)
**返回值** (`是否成功移除（不存在则返回`): False）

**示例**:
```python
>>> scope.unbind("onebot11", "123456")
True
>>> scope.unbind("onebot11", "123456", "group_9")  # 移除会话级绑定
True
```

---


##### `list_bindings()`

列出全部作用域绑定（含原始配置）

**返回值** (`{"platforms":`): {...}, "bots": {...}, "sessions": {...}} 结构

**示例**:
```python
>>> scope.list_bindings()
{"platforms": {"onebot11": {"modules": ["Chat"]}}, "bots": {}, "sessions": {}}
```

---


##### `clear()`

清空所有作用域绑定（运行时生效，不持久化）

---


##### `get_stats()`

获取作用域运行统计（便于调试被静默忽略的模块）

统计项：``is_allowed_calls``（判断次数）、``filtered_count``（被过滤次数）、
``cache_hits`` / ``cache_misses``（LRU 缓存命中/未命中）。

**返回值** (`统计字典`): 
**示例**:
```python
>>> scope.get_stats()
{"is_allowed_calls": 10, "filtered_count": 3, "cache_hits": 5, "cache_misses": 5}
```

---


##### `reset_stats()`

重置作用域运行统计

---


##### `get_topology()`

获取作用域绑定的结构化数据（便于 WebUI 展示拓扑树）

**返回值** (`{"platforms":`): {...}, "bots": {...}, "sessions": {...}}

**示例**:
```python
>>> scope.get_topology()
{"platforms": {"onebot11": {"modules": [...], "blocked": [...]}},
 "bots": {"onebot11": {"123456": {"modules": [...], "blocked": [...]}}},
 "sessions": {"onebot11": {"group_9": {"modules": [...], "blocked": [...]}}}}
```

---


##### `_raw_get(bucket: str, platform: str, key: str)`

> **内部方法** 读取指定绑定（供 merge 使用，浅拷贝）

---


##### `_resolve_target(platform: str, bot_id: str | None, session_id: str | None)`

> **内部方法**
根据参数解析目标绑定桶与键

- **platform** (`平台名称`): - **bot_id**: Bot 用户 ID
- **session_id** (`会话`): ID
**返回值** (`(bucket,`): key) 元组

---


##### `_logger_trace(message: str)`

> **内部方法** 输出 TRACE 日志（logger 未就绪时静默）

---


##### `_raw_bindings()`

> **内部方法** 读取当前绑定缓存（深拷贝，避免外部篡改）

---

