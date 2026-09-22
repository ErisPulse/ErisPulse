# `ErisPulse.Core.Bases.api_dsl` 模块

---

## 模块概述


ErisPulse 标准 API 动作 DSL 模块

提供 ApiDSL——OneBot12 标准 API 动作的强类型 DSL 基类，由适配器基类的
``Api`` 内嵌类继承使用；``ErisPulse.Core.Bases.adapter`` 对其 re-export，
既有导入路径（``ErisPulse.Core.Bases.adapter.ApiDSL`` / ``ErisPulse.Core.Bases.ApiDSL``）不变。

> **提示**
> 1. 标准方法默认委托给 ``adapter.call_api(action_name, ...)``，适配器可按需覆盖
> 2. 使用 ``adapter.Api.Using("bot1").get_user_info("123")`` 指定 Bot 账号
> 3. 平台扩展动作通过 ``call("prefix.action", **params)`` 调用

---

## 类列表


### `class ApiDSL`

标准 API 动作 DSL 基类

提供 OneBot12 标准动作的强类型方法，模块开发者只需面向标准接口编程，
由适配器负责映射到平台原生 API。

与 SendDSL（消息发送）、RequestDSL（请求操作）并行。覆盖 OneBot12 标准
动作中的用户 / 群组 / 频道（Guild）/ 消息管理 / 元（Meta）常规接口，以及
文件资源动作（upload_file / get_file / 分片，见方法 docstring 降级说明）；
唯一例外是 ``send_message``——由 ``SendDSL.Raw_ob12`` 承担，不在本类重复。

> **提示**
> 1. 标准方法默认委托给 ``adapter.call_api(action_name, ...)``，适配器可按需覆盖
> 2. 使用 ``adapter.Api.Using("bot1").get_user_info("123")`` 指定 Bot 账号
> 3. 平台扩展动作通过 ``call("prefix.action", **params)`` 调用
> 4. 所有方法返回标准 API 响应格式（status / retcode / data / message_id / message）
> 5. 适配器可覆盖单个标准方法以映射到平台 API，无需全部实现
> 6. 分片动作按阶段拆分为 prepare / transfer / finish 三个方法（见各自文档）


#### 方法列表


##### `__init__(adapter: 'BaseAdapter', account_id: str | None = None)`

初始化标准 API 动作 DSL

- **adapter** (`所属适配器实例`): - **account_id**: 执行操作的 Bot 账号（可选）

---


##### `Using(account_id: str | int)`

指定执行操作的 Bot 账号

- **account_id** (`账号标识`): **返回值** (`新的`): ApiDSL 实例

**示例**:
```python
>>> info = await adapter.myplatform.Api.Using("bot1").get_user_info("123")
```

---


##### `api_context()`

获取当前 API 操作上下文

**返回值** (`包含`): account_id 的字典

---


##### `_merge_context(params: dict)`

将 api_context 合并到参数字典

- **params** (`业务参数`): **返回值**: 合并后的参数字典

---


##### `async _api_call(action: str)`

> **内部方法**
API 动作统一授权入口

先经作用域出站维度检查（scope.actions.<owner>.api）：
模块被限制时直接返回标准拒绝响应，不发起网络请求；
owner 为空（框架层调用）或未配置限制时正常委托 ``call_api``。
name 传标准动作名，支持动作级细粒度规则（如仅放行 get_* 查询类）。

- **action** (`OneBot12`): 标准动作名或平台扩展动作名
- **params** (`动作参数（已合并`): api_context）
**返回值** (`标准`): API 响应

---


##### `async get_self_info()`

获取机器人自身信息

**返回值** (`标准响应，data`): 包含 user_id / user_name / user_displayname

**示例**:
```python
>>> result = await adapter.myplatform.Api.get_self_info()
>>> my_name = result["data"]["user_name"]
```

---


##### `async get_user_info(user_id: str)`

获取用户信息

- **user_id** (`用户`): ID（可以是好友，也可以是陌生人）
**返回值** (`标准响应，data`): 包含 user_id / user_name / user_displayname / user_remark

**示例**:
```python
>>> result = await adapter.myplatform.Api.get_user_info("123456")
>>> user_name = result["data"]["user_name"]
```

---


##### `async get_friend_list()`

获取好友列表

**返回值** (`标准响应，data`): 为好友信息列表

**示例**:
```python
>>> result = await adapter.myplatform.Api.get_friend_list()
>>> friends = result["data"]
```

---


##### `async get_group_info(group_id: str)`

获取群信息

- **group_id** (`群`): ID
**返回值** (`标准响应，data`): 包含 group_id / group_name

**示例**:
```python
>>> result = await adapter.myplatform.Api.get_group_info("123456")
>>> group_name = result["data"]["group_name"]
```

---


##### `async get_group_list()`

获取群列表

**返回值** (`标准响应，data`): 为群信息列表

**示例**:
```python
>>> result = await adapter.myplatform.Api.get_group_list()
>>> groups = result["data"]
```

---


##### `async get_group_member_info(group_id: str, user_id: str)`

获取群成员信息

- **group_id** (`群`): ID
- **user_id** (`用户`): ID
**返回值** (`标准响应，data`): 包含 user_id / user_name / user_displayname

**示例**:
```python
>>> result = await adapter.myplatform.Api.get_group_member_info("123", "456")
>>> member = result["data"]
```

---


##### `async get_group_member_list(group_id: str)`

获取群成员列表

- **group_id** (`群`): ID
**返回值** (`标准响应，data`): 为群成员信息列表

**示例**:
```python
>>> result = await adapter.myplatform.Api.get_group_member_list("123456")
>>> members = result["data"]
```

---


##### `async set_group_name(group_id: str, group_name: str)`

设置群名称

- **group_id** (`群`): ID
- **group_name** (`新群名称`): **返回值** (`标准响应`): 
**示例**:
```python
>>> await adapter.myplatform.Api.set_group_name("123456", "新群名")
```

---


##### `async leave_group(group_id: str)`

退出群

- **group_id** (`群`): ID
**返回值** (`标准响应`): 
**示例**:
```python
>>> await adapter.myplatform.Api.leave_group("123456")
```

---


##### `async get_guild_info(guild_id: str)`

获取频道（服务器）信息

- **guild_id** (`频道`): ID
**返回值** (`标准响应，data`): 包含 guild_id / guild_name

**示例**:
```python
>>> result = await adapter.myplatform.Api.get_guild_info("100001")
>>> guild_name = result["data"]["guild_name"]
```

---


##### `async get_guild_list()`

获取频道（服务器）列表

**返回值** (`标准响应，data`): 为 list[get_guild_info 响应]

**示例**:
```python
>>> result = await adapter.myplatform.Api.get_guild_list()
>>> guilds = result["data"]
```

---


##### `async set_guild_name(guild_id: str, guild_name: str)`

设置频道（服务器）名称

- **guild_id** (`频道`): ID
- **guild_name** (`新的频道名称`): **返回值** (`标准响应`): 
**示例**:
```python
>>> await adapter.myplatform.Api.set_guild_name("100001", "新频道名")
```

---


##### `async get_guild_member_info(guild_id: str, user_id: str)`

获取频道（服务器）成员信息

- **guild_id** (`频道`): ID
- **user_id** (`用户`): ID
**返回值** (`标准响应，data`): 包含 user_id / user_name / user_displayname

**示例**:
```python
>>> result = await adapter.myplatform.Api.get_guild_member_info("100001", "123456")
>>> display_name = result["data"]["user_displayname"]
```

---


##### `async get_guild_member_list(guild_id: str)`

获取频道（服务器）成员列表

- **guild_id** (`频道`): ID
**返回值** (`标准响应，data`): 为 list[get_guild_member_info 响应]

**示例**:
```python
>>> result = await adapter.myplatform.Api.get_guild_member_list("100001")
>>> members = result["data"]
```

---


##### `async leave_guild(guild_id: str)`

退出频道（服务器）

- **guild_id** (`频道`): ID
**返回值** (`标准响应`): 
**示例**:
```python
>>> await adapter.myplatform.Api.leave_guild("100001")
```

---


##### `async get_channel_info(guild_id: str, channel_id: str)`

获取频道下的子频道信息

- **guild_id** (`频道（服务器）ID`): - **channel_id**: 子频道 ID
**返回值** (`标准响应，data`): 包含 channel_id / channel_name

**示例**:
```python
>>> result = await adapter.myplatform.Api.get_channel_info("100001", "200001")
>>> channel_name = result["data"]["channel_name"]
```

---


##### `async get_channel_list(guild_id: str)`

获取频道下的子频道列表

- **guild_id** (`频道（服务器）ID`): - **joined_only**: 仅返回已加入的子频道（默认 False）
**返回值** (`标准响应，data`): 为 list[get_channel_info 响应]

**示例**:
```python
>>> result = await adapter.myplatform.Api.get_channel_list("100001")
>>> channels = result["data"]
```

---


##### `async set_channel_name(guild_id: str, channel_id: str, channel_name: str)`

设置子频道名称

- **guild_id** (`频道（服务器）ID`): - **channel_id**: 子频道 ID
- **channel_name** (`新的子频道名称`): **返回值** (`标准响应`): 
**示例**:
```python
>>> await adapter.myplatform.Api.set_channel_name("100001", "200001", "新子频道名")
```

---


##### `async get_channel_member_info(guild_id: str, channel_id: str, user_id: str)`

获取子频道成员信息

- **guild_id** (`频道（服务器）ID`): - **channel_id**: 子频道 ID
- **user_id** (`用户`): ID
**返回值** (`标准响应，data`): 包含 user_id / user_name / user_displayname

**示例**:
```python
>>> result = await adapter.myplatform.Api.get_channel_member_info("100001", "200001", "123456")
```

---


##### `async get_channel_member_list(guild_id: str, channel_id: str)`

获取子频道成员列表

- **guild_id** (`频道（服务器）ID`): - **channel_id**: 子频道 ID
**返回值** (`标准响应，data`): 为 list[get_channel_member_info 响应]

**示例**:
```python
>>> result = await adapter.myplatform.Api.get_channel_member_list("100001", "200001")
>>> members = result["data"]
```

---


##### `async leave_channel(guild_id: str, channel_id: str)`

退出子频道

- **guild_id** (`频道（服务器）ID`): - **channel_id**: 子频道 ID
**返回值** (`标准响应`): 
**示例**:
```python
>>> await adapter.myplatform.Api.leave_channel("100001", "200001")
```

---


##### `async delete_message(message_id: str)`

撤回 / 删除消息

- **message_id** (`消息`): ID
**返回值** (`标准响应`): 
**示例**:
```python
>>> await adapter.myplatform.Api.delete_message("msg_123456")
```

---


##### `async upload_file()`

上传文件到平台资源库（OB12 文件资源模型）

.. note:: 依赖平台特有的 ``file_id`` 文件资源能力，通用性不足，**ErisPulse
    常规路径不使用**——模块发送文件请用 ``SendDSL.File(file)``（发送时直传）。
    本方法仅当适配器后端具备 ``file_id`` 资源能力时透传；多数平台适配器
    不会实现它，调用方需自行处理 ``10002``。
    ``file_id`` 资源模型标准化到框架层是未来方向，当前版本不提供。

- **type** (`上传方式（``url```): / ``path`` / ``data``）
- **name** (`文件名（如`): ``foo.jpg``）
- **url** (`文件`): URL（``type="url"`` 时必须传入）
- **path** (`文件路径（``type="path"```): 时必须传入）
- **data** (`文件数据（``type="data"```): 时必须传入）
- **headers** (`下载`): URL 时附加的 HTTP 请求头（可选）
- **sha256** (`文件数据的`): SHA256 校验和（可选）
**返回值** (`标准响应，data`): 包含 file_id

**示例**:
```python
>>> result = await adapter.Api.upload_file(type="url", name="logo.jpg", url="https://example.com/logo.jpg")
>>> file_id = result["data"]["file_id"]
```

---


##### `async get_file(file_id: str, type: str = 'url')`

从平台资源库获取文件（OB12 文件资源模型）

.. note:: 依赖平台特有的 ``file_id`` 文件资源能力，通用性不足，**ErisPulse
    常规路径不使用**；仅当适配器后端具备该能力时透传，多数平台不会实现
    （返回 ``10002``）。``file_id`` 资源模型标准化到框架层是未来方向，
    当前版本不提供。

- **file_id** (`文件`): ID
- **type** (`获取方式（``url```): / ``path`` / ``data``），默认 ``url``
**返回值** (`标准响应，data`): 包含 name / url 或 path 或 data

**示例**:
```python
>>> result = await adapter.myplatform.Api.get_file("file_abc", "url")
>>> download_url = result["data"]["url"]
```

---


##### `async upload_file_fragmented_prepare(name: str, total_size: int)`

分片上传 · 准备阶段（OB12 文件资源模型，见分组说明——框架内尚无实现方）

分片上传三步：``prepare`` → ``transfer``（循环，逐片调用）→ ``finish``。
本方法为第一阶段，创建传输会话并返回 ``file_id``（后续阶段使用）。

- **name** (`文件名（如`): ``foo.jpg``）
- **total_size** (`完整文件大小（字节）`): **返回值** (`标准响应，data`): 包含 file_id（仅供传输阶段使用）

**示例**:
```python
>>> r = await adapter.Api.upload_file_fragmented_prepare("foo.jpg", 1048576)
>>> file_id = r["data"]["file_id"]
```

---


##### `async upload_file_fragmented_transfer(file_id: str, offset: int, data: bytes)`

分片上传 · 传输阶段（OB12 文件资源模型，见分组说明——框架内尚无实现方）

将文件按字节偏移逐片写入：``offset`` 从 0 开始，每片长度为 ``len(data)``。

- **file_id** (`prepare`): 阶段返回的文件 ID
- **offset** (`本次分片的字节偏移`): - **data**: 本次分片数据
**返回值** (`标准响应`): 
**示例**:
```python
>>> await adapter.Api.upload_file_fragmented_transfer(file_id, 0, chunk)
>>> await adapter.Api.upload_file_fragmented_transfer(file_id, len(chunk), next_chunk)
```

---


##### `async upload_file_fragmented_finish(file_id: str, sha256: str)`

分片上传 · 完成阶段（OB12 文件资源模型，见分组说明——框架内尚无实现方）

- **file_id** (`prepare`): 阶段返回的文件 ID
- **sha256** (`**整个文件**的`): SHA256（全小写十六进制）
**返回值** (`标准响应，data`): 包含 file_id（供以后使用）

**示例**:
```python
>>> await adapter.Api.upload_file_fragmented_finish(file_id, sha256_hex)
```

---


##### `async get_file_fragmented_prepare(file_id: str)`

分片下载 · 准备阶段（OB12 文件资源模型，见分组说明——框架内尚无实现方）

分片下载两步：``prepare``（获取文件元信息）→ ``transfer``（循环取片）。

- **file_id** (`文件`): ID
**返回值** (`标准响应，data`): 包含 name / total_size / sha256

**示例**:
```python
>>> r = await adapter.Api.get_file_fragmented_prepare("file_abc")
>>> meta = r["data"]
```

---


##### `async get_file_fragmented_transfer(file_id: str, offset: int, size: int)`

分片下载 · 传输阶段（OB12 文件资源模型，见分组说明——框架内尚无实现方）

按 ``offset`` 取一片，``size`` 为本次请求的字节数（最后一片可小于 size）。

- **file_id** (`文件`): ID
- **offset** (`本次分片的字节偏移`): - **size**: 本次请求大小（字节）
**返回值** (`标准响应，data`): 包含 data（本次分片字节）

**示例**:
```python
>>> while offset < total_size:
...     r = await adapter.Api.get_file_fragmented_transfer(file_id, offset, 65536)
...     offset += len(r["data"]["data"])
```

---


##### `async get_latest_events(limit: int = 0, timeout: int = 0)`

获取最新事件（仅 HTTP 通信方式必须支持）

- **limit** (`最多返回事件数量（0`): = 不限制）
- **timeout** (`长轮询等待秒数（0`): = 短轮询，不等待）
**返回值** (`标准响应，data`): 为事件对象数组（从旧到新，不含元事件）

---


##### `async get_supported_actions()`

获取实现支持的动作列表

**返回值** (`标准响应，data`): 为动作名字符串数组（可能不含 get_latest_events）

---


##### `async get_status()`

获取运行状态

**返回值** (`标准响应，data`): 包含 good / bots
    - good: 各模块是否均正常（bool）
    - bots: 机器人账号状态列表，每项含 self{platform, user_id} 与 online

---


##### `async get_version()`

获取实现版本信息

**返回值** (`标准响应，data`): 包含 impl / version / onebot_version

---


##### `async call(action: str)`

调用平台扩展动作（逃生舱）

用于调用 OneBot12 标准之外的平台扩展动作。
建议使用 ``{prefix}.{action}`` 命名（如 ``telegram.send_sticker``），
遵循 OneBot12 扩展规则。

- **action** (`动作名称（标准动作名或`): ``{prefix}.{action}`` 扩展动作名）
- **params** (`动作参数`): **返回值** (`标准响应格式`): 
**示例**:
```python
>>> # 调用平台扩展动作
>>> result = await adapter.myplatform.Api.call("telegram.send_sticker", sticker_id="CAACAgIAAxkBAA...")
>>>
>>> # 也可用于调用标准动作（等价于直接调用对应方法）
>>> result = await adapter.myplatform.Api.call("get_user_info", user_id="123")
```

---

