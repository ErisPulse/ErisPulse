# `ErisPulse.Core.Event.overrides` 模块

---

## 模块概述


ErisPulse 事件覆写系统（overrides）

不改模块代码，按事件类型覆写任意事件处理器的触发条件与实现参数。
控制权完全交给用户：在处理器注册的**上层**（配置 ``ErisPulse.event.overrides``
或运行时 ``sdk.Event.overrides``）声明，事件管线在过滤链自动读取并执行。

事件类型遵循 OneBot12 标准：**meta** / **message** / **notice** / **request**；
**command** 为 ErisPulse 扩展类型。每个类型拥有各自的覆写规格：

===== ================ ==================================
类型   可覆写参数        说明
===== ================ ==================================
meta   detail_types     detail_type 白名单（connect 等）
notice detail_types      + pattern / regex
request detail_types     + pattern / regex
message pattern / regex  文本触发条件
command master 等参数    实现参数覆写 + acl 用户准入
acl    allow / deny      命令用户黑白名单（command 专属，按命令名 glob）
===== ================ ==================================

配置树（``ErisPulse.event.overrides``）：

.. code-block:: toml

    # message：覆写文本触发条件
    [ErisPulse.event.overrides.message.MyModule]
    pattern = "签到*"
    regex = "re:\\d+"

    # notice / request / meta：detail_type 白名单（条目支持精确 / glob / re: 正则）
    [ErisPulse.event.overrides.notice.MyModule]
    detail_types = ["group_increase"]
    [ErisPulse.event.overrides.meta.MyModule]
    detail_types = ["connect"]

    # command（扩展类型）：实现参数覆写（用户优先，可收紧或放开开发者默认）
    [ErisPulse.event.overrides.command.MyModule]
    hidden = true
    [ErisPulse.event.overrides.command.MyModule.restart]
    master = true
    aliases = ["rs"]

    # acl（command 专属）：用户黑白名单（用户标识 "platform:uid"）
    [ErisPulse.event.overrides.acl."roll*"]
    allow = ["onebot11:u_vip"]
    deny = ["onebot11:u_bad"]

    # ACL 兜底（false = 严格模式：无 ACL 即拒）
    acl_default_allow = true

覆写语义：

- **pattern / regex**（文本条件）：与代码内条件 AND；无文本的事件不受约束，直接放行
- **detail_types**：detail_type 白名单，未命中即不触发；事件缺 detail_type 时放行
- **command 参数**：与开发者声明深合并，本次覆写优先；覆写键 ``master`` 映射存储键 ``must_master``
- **acl**：``deny`` 命中 → 拒绝；``allow`` 非空且未命中 → 拒绝；未配置遵循 ``acl_default_allow``

匹配条目统一语法（见 :mod:`ErisPulse.Core.text_match`）：
**精确名** / **glob**（``*`` / ``?`` / ``[seq]``）/ **``re:`` 正则**，默认大小写不敏感。

> **提示**
> 1. 通过 ``from ErisPulse.Core.Event import overrides`` 导入（``sdk.Event.overrides`` 同一模块）
> 2. 类型子命名空间：``overrides.message.set("My", pattern="签到*")`` /
> ``overrides.command.set("My", "roll", master=True)`` / ``overrides.acl.set("roll*", deny=[...])``
> 3. 每类型均有 ``set`` / ``get`` / ``delete`` 三件套；acl 额外提供 ``is_allowed`` 判定

---

## 函数列表


### `_record_runtime_owner(path: str, persist: bool)`

> **内部方法** 记录（persist=False）或清除（persist=True）路径的调用方归属

---


### `_warn_invalid(path: str, actual: str)`

> **内部方法** 输出配置格式告警（同一路径去重）

---


### `_snapshot()`

> **内部方法** 内存最终态快照（供持久化后重放，保证写后立读）

---


### `_apply(tree: dict)`

> **内部方法** 校验并应用完整覆写配置树到内存（含格式校验）

---


### `_reload(_data: dict | None = None)`

配置变更回调：从配置重建覆写缓存

---


### `_persist_section(section_key: str, value)`

> **内部方法** 持久化单个覆写分区，并以内存快照重放（写后立读）

---


### `condition_for(event_type: str, owner: str)`

> **内部方法**
获取某事件类型下某模块的覆写过滤条件（detail_types 白名单 + pattern/regex 文本条件）

- **event_type** (`事件类型（message`): / notice / request / meta）
- **owner** (`模块名`): **返回值** (`事件条件函数，该类型未配置覆写时返回`): None

---


### `topology()`

获取事件覆写配置的结构化数据（便于 WebUI 展示拓扑树）

**返回值** (`按事件类型分组的覆写结构`): + command / acl 类别

---


### `clear()`

清空全部覆写配置（仅内存生效，不持久化）

---


### `_persist_all()`

> **内部方法** 全量持久化（acl_default_allow 标量需要整节写入）

---


### `unregister_by_owner(caller: str)`

兜底清理指定调用方在运行时（persist=False）写入的全部覆写

仅清理内存态覆写；``persist=True`` 的写入属用户配置语义，不在此
清理范围（随配置持久保留，需用户显式删除）。供模块卸载时调用，
避免卸载后模块运行时写入的覆写残留生效。

- **caller** (`调用方（模块名`): / 适配器平台名）
**返回值** (`int`): 清理的覆写条目数量

---


## 类列表


### `class _TypeNamespace`

> **内部方法**
标准事件类型的覆写命名空间（message / notice / request / meta）

提供 ``set`` / ``get`` / ``delete`` 三件套；可覆写参数由 :data:`_TYPE_SPECS`
规格约束（未知参数抛 ValueError，fail-fast）。


#### 方法列表


##### `set(module: str)`

覆写该模块在本事件类型的触发条件（整体替换语义）

- **module** (`模块名`): - **persist**: 是否持久化到配置文件 (默认: True)
- **params** (`该类型的可覆写参数（``detail_types```): / ``pattern`` / ``regex``，
               按类型规格而定）；全空参数 = 移除覆写

**示例**:
```python
>>> overrides.message.set("ChatModule", pattern="闲聊*")
>>> overrides.notice.set("MyModule", detail_types=["group_increase"])
```

---


##### `get(module: str, default = None)`

读取该模块在本事件类型的覆写参数

- **module** (`模块名`): - **default**: 未配置时返回值（默认 None）
**返回值** (`覆写参数字典或`): default

---


##### `delete(module: str, persist: bool = True)`

移除该模块在本事件类型的覆写（恢复开发者声明的默认行为）

- **module** (`模块名`): - **persist**: 是否持久化到配置文件 (默认: True)
**返回值**: 是否存在并被移除

---


### `class _CommandNamespace`

command（扩展类型）的覆写命名空间

实现参数覆写（master / hidden / aliases / prefix / help / usage，用户优先），
支持模块级标量与命令级子表两种粒度（命令级优先）。


#### 方法列表


##### `set(owner: str, command_name: str | None = None)`

覆写命令实现参数（command 扩展类型，用户优先语义）

覆写遵循**用户优先**：显式设置的参数直接生效（可收紧或放开开发者默认）。
禁用统一走 acl deny，参数覆写不承载禁用语义。

- **owner** (`模块名`): - **command_name**: 命令名；None 表示模块级覆写
- **persist** (`是否持久化到配置文件`): (默认: True)
- **params** (`可覆写参数（master`): / hidden / aliases / prefix / help / usage）

**示例**:
```python
>>> overrides.command.set("MyModule", "restart", master=True, hidden=True)
>>> overrides.command.set("MyModule", hidden=True)   # 模块级
```

---


##### `get(owner: str, command_name: str | None = None, default = None)`

读取模块 / 命令的覆写参数（命令级优先合并）

- **owner** (`模块名`): - **command_name**: 命令名；None 表示仅模块级参数
- **default** (`未配置时返回值（默认`): {}）
**返回值**: 合并后的参数字典

---


##### `apply(owner: str, command_name: str, defaults: dict)`

> **内部方法**
把命令默认参数与覆写合并（覆写优先）

覆写键 ``master`` 同步映射到命令存储键 ``must_master``（用户优先）。

- **owner** (`模块名`): - **command_name**: 命令名
- **defaults** (`命令默认参数字典`): **返回值**: 合并后的生效参数字典

---


##### `delete(owner: str, command_name: str | None = None, persist: bool = True)`

移除模块 / 命令的覆写参数

- **owner** (`模块名`): - **command_name**: 命令名；None 表示移除该模块全部覆写
- **persist** (`是否持久化到配置文件`): (默认: True)
**返回值**: 是否有内容被移除

---


### `class _AclNamespace`

acl 命名空间（command 扩展类型专属：命令用户黑白名单）

按命令名组织（支持 glob / ``re:`` 正则，精确键优先），用户标识 ``platform:uid``。


#### 方法列表


##### `set(command_name: str)`

设置命令的用户黑白名单

- **command_name** (`命令名（支持`): glob / ``re:`` 正则）
- **allow** (`白名单（非空时仅名单内用户可执行）`): - **deny**: 黑名单（deny 优先于 allow）
- **persist** (`是否持久化到配置文件`): (默认: True)

**示例**:
```python
>>> overrides.acl.set("roll*", allow=["onebot11:u_vip"])
>>> overrides.acl.set("restart", deny="onebot11:u_bad")
```

---


##### `match(command_name: str)`

> **内部方法**
获取命令的生效 ACL（精确键优先，未命中再按 glob / ``re:`` 匹配）

- **command_name** (`命令主名`): **返回值** (`{"allow":`): [...], "deny": [...]}，未配置时返回 None

---


##### `get(command_name: str)`

查询命令当前的用户黑白名单

- **command_name** (`命令名（可含模式）`): **返回值** (`{"allow":`): [...], "deny": [...]}

---


##### `delete(command_name: str, persist: bool = True)`

清除命令的用户黑白名单（恢复开发者默认权限逻辑）

- **command_name** (`命令名（可含模式）`): - **persist**: 是否持久化到配置文件 (默认: True)
**返回值**: 是否存在并被清除

---


##### `is_allowed(command_name: str, platform: str, user_id: str)`

判断用户对命令是否被 ACL 允许（判定链）

``deny`` 命中 → 拒绝；``allow`` 非空且未命中 → 拒绝；
未配置 ACL 遵循 ``acl_default_allow``（false = 严格模式：无 ACL 即拒）。

- **command_name** (`命令主名`): - **platform**: 用户所属平台
- **user_id** (`用户`): ID
**返回值**: 是否允许执行

---


##### `default_allow()`

ACL 兜底开关（``event.overrides.acl_default_allow``）

---


##### `list_commands()`

列出已配置 ACL 的命令名（含 glob 模式键）

**返回值**: 命令名列表（排序）

---

