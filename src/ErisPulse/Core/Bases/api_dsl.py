"""
ErisPulse 标准 API 动作 DSL 模块

提供 ApiDSL——OneBot12 标准 API 动作的强类型 DSL 基类，由适配器基类的
``Api`` 内嵌类继承使用；``ErisPulse.Core.Bases.adapter`` 对其 re-export，
既有导入路径（``ErisPulse.Core.Bases.adapter.ApiDSL`` / ``ErisPulse.Core.Bases.ApiDSL``）不变。

{!--< tips >!--}
1. 标准方法默认委托给 ``adapter.call_api(action_name, ...)``，适配器可按需覆盖
2. 使用 ``adapter.Api.Using("bot1").get_user_info("123")`` 指定 Bot 账号
3. 平台扩展动作通过 ``call("prefix.action", **params)`` 调用
{!--< /tips >!--}
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    # Self 用于让链式方法返回子类类型，使 IDE 能补全平台特有方法
    # typing.Self 仅在 3.11+ 提供，3.10 需 typing_extensions 兜底
    from typing_extensions import Self

    from .adapter import BaseAdapter

class ApiDSL:
    """
    标准 API 动作 DSL 基类

    提供 OneBot12 标准动作的强类型方法，模块开发者只需面向标准接口编程，
    由适配器负责映射到平台原生 API。

    与 SendDSL（消息发送）、RequestDSL（请求操作）并行。覆盖 OneBot12 标准
    动作中的用户 / 群组 / 频道（Guild）/ 消息管理 / 元（Meta）常规接口，以及
    文件资源动作（upload_file / get_file / 分片，见方法 docstring 降级说明）；
    唯一例外是 ``send_message``——由 ``SendDSL.Raw_ob12`` 承担，不在本类重复。

    {!--< tips >!--}
    1. 标准方法默认委托给 ``adapter.call_api(action_name, ...)``，适配器可按需覆盖
    2. 使用 ``adapter.Api.Using("bot1").get_user_info("123")`` 指定 Bot 账号
    3. 平台扩展动作通过 ``call("prefix.action", **params)`` 调用
    4. 所有方法返回标准 API 响应格式（status / retcode / data / message_id / message）
    5. 适配器可覆盖单个标准方法以映射到平台 API，无需全部实现
    6. 分片动作按阶段拆分为 prepare / transfer / finish 三个方法（见各自文档）
    {!--< /tips >!--}
    """

    def __init__(
        self,
        adapter: "BaseAdapter",
        account_id: str | None = None,
    ):
        """
        初始化标准 API 动作 DSL

        :param adapter: 所属适配器实例
        :param account_id: 执行操作的 Bot 账号（可选）
        """
        self._adapter = adapter
        self._account_id = account_id

    def Using(self, account_id: str | int) -> "Self":
        """
        指定执行操作的 Bot 账号

        :param account_id: 账号标识
        :return: 新的 ApiDSL 实例

        :example:
        >>> info = await adapter.myplatform.Api.Using("bot1").get_user_info("123")
        """
        return self.__class__(self._adapter, str(account_id))

    @property
    def api_context(self) -> dict:
        """
        获取当前 API 操作上下文

        :return: 包含 account_id 的字典
        """
        return {
            "account_id": self._account_id,
        }

    def _merge_context(self, params: dict) -> dict:
        """
        将 api_context 合并到参数字典

        :param params: 业务参数
        :return: 合并后的参数字典
        """
        merged = dict(params)
        merged.update(self.api_context)
        return merged

    async def _api_call(self, action: str, **params: Any) -> dict[str, Any]:
        """
        {!--< internal-use >!--}
        API 动作统一授权入口

        先经作用域出站维度检查（scope.actions.<owner>.api）：
        模块被限制时直接返回标准拒绝响应，不发起网络请求；
        owner 为空（框架层调用）或未配置限制时正常委托 ``call_api``。
        name 传标准动作名，支持动作级细粒度规则（如仅放行 get_* 查询类）。

        :param action: OneBot12 标准动作名或平台扩展动作名
        :param params: 动作参数（已合并 api_context）
        :return: 标准 API 响应
        """
        from ...runtime.context import get_current_owner
        from ..scope import scope as _scope

        # 延迟导入：_action_denied_response 定义在 adapter.py（供三个 DSL 共用），避免模块级循环导入
        from .adapter import _action_denied_response

        if not _scope.is_action_allowed(get_current_owner() or "", "api", name=action):
            return await _action_denied_response(self._adapter, "api")
        return await self._adapter.call_api(action, **params)

    # ==================== 用户相关动作 ====================

    async def get_self_info(self) -> dict[str, Any]:
        """
        获取机器人自身信息

        :return: 标准响应，data 包含 user_id / user_name / user_displayname

        :example:
        >>> result = await adapter.myplatform.Api.get_self_info()
        >>> my_name = result["data"]["user_name"]
        """
        return await self._api_call("get_self_info", **self._merge_context({}))

    async def get_user_info(self, user_id: str) -> dict[str, Any]:
        """
        获取用户信息

        :param user_id: 用户 ID（可以是好友，也可以是陌生人）
        :return: 标准响应，data 包含 user_id / user_name / user_displayname / user_remark

        :example:
        >>> result = await adapter.myplatform.Api.get_user_info("123456")
        >>> user_name = result["data"]["user_name"]
        """
        return await self._api_call("get_user_info", **self._merge_context({"user_id": str(user_id)}))

    async def get_friend_list(self) -> dict[str, Any]:
        """
        获取好友列表

        :return: 标准响应，data 为好友信息列表

        :example:
        >>> result = await adapter.myplatform.Api.get_friend_list()
        >>> friends = result["data"]
        """
        return await self._api_call("get_friend_list", **self._merge_context({}))

    # ==================== 群组相关动作 ====================

    async def get_group_info(self, group_id: str) -> dict[str, Any]:
        """
        获取群信息

        :param group_id: 群 ID
        :return: 标准响应，data 包含 group_id / group_name

        :example:
        >>> result = await adapter.myplatform.Api.get_group_info("123456")
        >>> group_name = result["data"]["group_name"]
        """
        return await self._api_call("get_group_info", **self._merge_context({"group_id": str(group_id)}))

    async def get_group_list(self) -> dict[str, Any]:
        """
        获取群列表

        :return: 标准响应，data 为群信息列表

        :example:
        >>> result = await adapter.myplatform.Api.get_group_list()
        >>> groups = result["data"]
        """
        return await self._api_call("get_group_list", **self._merge_context({}))

    async def get_group_member_info(self, group_id: str, user_id: str) -> dict[str, Any]:
        """
        获取群成员信息

        :param group_id: 群 ID
        :param user_id: 用户 ID
        :return: 标准响应，data 包含 user_id / user_name / user_displayname

        :example:
        >>> result = await adapter.myplatform.Api.get_group_member_info("123", "456")
        >>> member = result["data"]
        """
        return await self._api_call(
            "get_group_member_info", **self._merge_context({"group_id": str(group_id), "user_id": str(user_id)})
        )

    async def get_group_member_list(self, group_id: str) -> dict[str, Any]:
        """
        获取群成员列表

        :param group_id: 群 ID
        :return: 标准响应，data 为群成员信息列表

        :example:
        >>> result = await adapter.myplatform.Api.get_group_member_list("123456")
        >>> members = result["data"]
        """
        return await self._api_call("get_group_member_list", **self._merge_context({"group_id": str(group_id)}))

    async def set_group_name(self, group_id: str, group_name: str) -> dict[str, Any]:
        """
        设置群名称

        :param group_id: 群 ID
        :param group_name: 新群名称
        :return: 标准响应

        :example:
        >>> await adapter.myplatform.Api.set_group_name("123456", "新群名")
        """
        return await self._api_call(
            "set_group_name", **self._merge_context({"group_id": str(group_id), "group_name": group_name})
        )

    async def leave_group(self, group_id: str) -> dict[str, Any]:
        """
        退出群

        :param group_id: 群 ID
        :return: 标准响应

        :example:
        >>> await adapter.myplatform.Api.leave_group("123456")
        """
        return await self._api_call("leave_group", **self._merge_context({"group_id": str(group_id)}))

    # ==================== 频道（Guild）相关动作 ====================

    async def get_guild_info(self, guild_id: str) -> dict[str, Any]:
        """
        获取频道（服务器）信息

        :param guild_id: 频道 ID
        :return: 标准响应，data 包含 guild_id / guild_name

        :example:
        >>> result = await adapter.myplatform.Api.get_guild_info("100001")
        >>> guild_name = result["data"]["guild_name"]
        """
        return await self._api_call("get_guild_info", **self._merge_context({"guild_id": str(guild_id)}))

    async def get_guild_list(self) -> dict[str, Any]:
        """
        获取频道（服务器）列表

        :return: 标准响应，data 为 list[get_guild_info 响应]

        :example:
        >>> result = await adapter.myplatform.Api.get_guild_list()
        >>> guilds = result["data"]
        """
        return await self._api_call("get_guild_list", **self._merge_context({}))

    async def set_guild_name(self, guild_id: str, guild_name: str) -> dict[str, Any]:
        """
        设置频道（服务器）名称

        :param guild_id: 频道 ID
        :param guild_name: 新的频道名称
        :return: 标准响应

        :example:
        >>> await adapter.myplatform.Api.set_guild_name("100001", "新频道名")
        """
        return await self._api_call(
            "set_guild_name",
            **self._merge_context({"guild_id": str(guild_id), "guild_name": guild_name}),
        )

    async def get_guild_member_info(self, guild_id: str, user_id: str) -> dict[str, Any]:
        """
        获取频道（服务器）成员信息

        :param guild_id: 频道 ID
        :param user_id: 用户 ID
        :return: 标准响应，data 包含 user_id / user_name / user_displayname

        :example:
        >>> result = await adapter.myplatform.Api.get_guild_member_info("100001", "123456")
        >>> display_name = result["data"]["user_displayname"]
        """
        return await self._api_call(
            "get_guild_member_info",
            **self._merge_context({"guild_id": str(guild_id), "user_id": str(user_id)}),
        )

    async def get_guild_member_list(self, guild_id: str) -> dict[str, Any]:
        """
        获取频道（服务器）成员列表

        :param guild_id: 频道 ID
        :return: 标准响应，data 为 list[get_guild_member_info 响应]

        :example:
        >>> result = await adapter.myplatform.Api.get_guild_member_list("100001")
        >>> members = result["data"]
        """
        return await self._api_call("get_guild_member_list", **self._merge_context({"guild_id": str(guild_id)}))

    async def leave_guild(self, guild_id: str) -> dict[str, Any]:
        """
        退出频道（服务器）

        :param guild_id: 频道 ID
        :return: 标准响应

        :example:
        >>> await adapter.myplatform.Api.leave_guild("100001")
        """
        return await self._api_call("leave_guild", **self._merge_context({"guild_id": str(guild_id)}))

    async def get_channel_info(self, guild_id: str, channel_id: str) -> dict[str, Any]:
        """
        获取频道下的子频道信息

        :param guild_id: 频道（服务器）ID
        :param channel_id: 子频道 ID
        :return: 标准响应，data 包含 channel_id / channel_name

        :example:
        >>> result = await adapter.myplatform.Api.get_channel_info("100001", "200001")
        >>> channel_name = result["data"]["channel_name"]
        """
        return await self._api_call(
            "get_channel_info",
            **self._merge_context({"guild_id": str(guild_id), "channel_id": str(channel_id)}),
        )

    async def get_channel_list(self, guild_id: str, *, joined_only: bool = False) -> dict[str, Any]:
        """
        获取频道下的子频道列表

        :param guild_id: 频道（服务器）ID
        :param joined_only: 仅返回已加入的子频道（默认 False）
        :return: 标准响应，data 为 list[get_channel_info 响应]

        :example:
        >>> result = await adapter.myplatform.Api.get_channel_list("100001")
        >>> channels = result["data"]
        """
        return await self._api_call(
            "get_channel_list",
            **self._merge_context({"guild_id": str(guild_id), "joined_only": bool(joined_only)}),
        )

    async def set_channel_name(self, guild_id: str, channel_id: str, channel_name: str) -> dict[str, Any]:
        """
        设置子频道名称

        :param guild_id: 频道（服务器）ID
        :param channel_id: 子频道 ID
        :param channel_name: 新的子频道名称
        :return: 标准响应

        :example:
        >>> await adapter.myplatform.Api.set_channel_name("100001", "200001", "新子频道名")
        """
        return await self._api_call(
            "set_channel_name",
            **self._merge_context(
                {"guild_id": str(guild_id), "channel_id": str(channel_id), "channel_name": channel_name}
            ),
        )

    async def get_channel_member_info(self, guild_id: str, channel_id: str, user_id: str) -> dict[str, Any]:
        """
        获取子频道成员信息

        :param guild_id: 频道（服务器）ID
        :param channel_id: 子频道 ID
        :param user_id: 用户 ID
        :return: 标准响应，data 包含 user_id / user_name / user_displayname

        :example:
        >>> result = await adapter.myplatform.Api.get_channel_member_info("100001", "200001", "123456")
        """
        return await self._api_call(
            "get_channel_member_info",
            **self._merge_context({"guild_id": str(guild_id), "channel_id": str(channel_id), "user_id": str(user_id)}),
        )

    async def get_channel_member_list(self, guild_id: str, channel_id: str) -> dict[str, Any]:
        """
        获取子频道成员列表

        :param guild_id: 频道（服务器）ID
        :param channel_id: 子频道 ID
        :return: 标准响应，data 为 list[get_channel_member_info 响应]

        :example:
        >>> result = await adapter.myplatform.Api.get_channel_member_list("100001", "200001")
        >>> members = result["data"]
        """
        return await self._api_call(
            "get_channel_member_list",
            **self._merge_context({"guild_id": str(guild_id), "channel_id": str(channel_id)}),
        )

    async def leave_channel(self, guild_id: str, channel_id: str) -> dict[str, Any]:
        """
        退出子频道

        :param guild_id: 频道（服务器）ID
        :param channel_id: 子频道 ID
        :return: 标准响应

        :example:
        >>> await adapter.myplatform.Api.leave_channel("100001", "200001")
        """
        return await self._api_call(
            "leave_channel",
            **self._merge_context({"guild_id": str(guild_id), "channel_id": str(channel_id)}),
        )

    # ==================== 消息管理动作 ====================

    async def delete_message(self, message_id: str) -> dict[str, Any]:
        """
        撤回 / 删除消息

        :param message_id: 消息 ID
        :return: 标准响应

        :example:
        >>> await adapter.myplatform.Api.delete_message("msg_123456")
        """
        return await self._api_call("delete_message", **self._merge_context({"message_id": str(message_id)}))

    # ==================== 文件相关动作 ====================

    async def upload_file(
        self,
        *,
        type: str,
        name: str,
        url: str | None = None,
        path: str | None = None,
        data: bytes | None = None,
        headers: dict[str, str] | None = None,
        sha256: str | None = None,
    ) -> dict[str, Any]:
        """
        上传文件到平台资源库（OB12 文件资源模型）

        .. note:: 依赖平台特有的 ``file_id`` 文件资源能力，通用性不足，**ErisPulse
            常规路径不使用**——模块发送文件请用 ``SendDSL.File(file)``（发送时直传）。
            本方法仅当适配器后端具备 ``file_id`` 资源能力时透传；多数平台适配器
            不会实现它，调用方需自行处理 ``10002``。
            ``file_id`` 资源模型标准化到框架层是未来方向，当前版本不提供。

        :param type: 上传方式（``url`` / ``path`` / ``data``）
        :param name: 文件名（如 ``foo.jpg``）
        :param url: 文件 URL（``type="url"`` 时必须传入）
        :param path: 文件路径（``type="path"`` 时必须传入）
        :param data: 文件数据（``type="data"`` 时必须传入）
        :param headers: 下载 URL 时附加的 HTTP 请求头（可选）
        :param sha256: 文件数据的 SHA256 校验和（可选）
        :return: 标准响应，data 包含 file_id

        :example:
        >>> result = await adapter.Api.upload_file(type="url", name="logo.jpg", url="https://example.com/logo.jpg")
        >>> file_id = result["data"]["file_id"]
        """
        params: dict[str, Any] = {"type": type, "name": name}
        if url is not None:
            params["url"] = url
        if path is not None:
            params["path"] = path
        if data is not None:
            params["data"] = data
        if headers is not None:
            params["headers"] = headers
        if sha256 is not None:
            params["sha256"] = sha256
        return await self._api_call("upload_file", **self._merge_context(params))

    async def get_file(self, file_id: str, type: str = "url") -> dict[str, Any]:
        """
        从平台资源库获取文件（OB12 文件资源模型）

        .. note:: 依赖平台特有的 ``file_id`` 文件资源能力，通用性不足，**ErisPulse
            常规路径不使用**；仅当适配器后端具备该能力时透传，多数平台不会实现
            （返回 ``10002``）。``file_id`` 资源模型标准化到框架层是未来方向，
            当前版本不提供。

        :param file_id: 文件 ID
        :param type: 获取方式（``url`` / ``path`` / ``data``），默认 ``url``
        :return: 标准响应，data 包含 name / url 或 path 或 data

        :example:
        >>> result = await adapter.myplatform.Api.get_file("file_abc", "url")
        >>> download_url = result["data"]["url"]
        """
        return await self._api_call("get_file", **self._merge_context({"file_id": str(file_id), "type": type}))

    # ==================== 文件分片动作（大文件） ====================
    # OB12 文件资源模型（file_id 两段式），依赖平台特有文件资源能力、通用性不足。
    # ErisPulse 常规路径不采用——模块发送大文件请用 SendDSL.File(file) 发送时直传；
    # 分片动作仅供后端具备该能力的适配器透传，框架内尚无实现方。
    # file_id 资源模型标准化到框架层是未来方向，当前版本不提供。

    async def upload_file_fragmented_prepare(self, name: str, total_size: int) -> dict[str, Any]:
        """
        分片上传 · 准备阶段（OB12 文件资源模型，见分组说明——框架内尚无实现方）

        分片上传三步：``prepare`` → ``transfer``（循环，逐片调用）→ ``finish``。
        本方法为第一阶段，创建传输会话并返回 ``file_id``（后续阶段使用）。

        :param name: 文件名（如 ``foo.jpg``）
        :param total_size: 完整文件大小（字节）
        :return: 标准响应，data 包含 file_id（仅供传输阶段使用）

        :example:
        >>> r = await adapter.Api.upload_file_fragmented_prepare("foo.jpg", 1048576)
        >>> file_id = r["data"]["file_id"]
        """
        return await self._api_call(
            "upload_file_fragmented",
            **self._merge_context({"stage": "prepare", "name": name, "total_size": int(total_size)}),
        )

    async def upload_file_fragmented_transfer(self, file_id: str, offset: int, data: bytes) -> dict[str, Any]:
        """
        分片上传 · 传输阶段（OB12 文件资源模型，见分组说明——框架内尚无实现方）

        将文件按字节偏移逐片写入：``offset`` 从 0 开始，每片长度为 ``len(data)``。

        :param file_id: prepare 阶段返回的文件 ID
        :param offset: 本次分片的字节偏移
        :param data: 本次分片数据
        :return: 标准响应

        :example:
        >>> await adapter.Api.upload_file_fragmented_transfer(file_id, 0, chunk)
        >>> await adapter.Api.upload_file_fragmented_transfer(file_id, len(chunk), next_chunk)
        """
        return await self._api_call(
            "upload_file_fragmented",
            **self._merge_context({"stage": "transfer", "file_id": file_id, "offset": int(offset), "data": data}),
        )

    async def upload_file_fragmented_finish(self, file_id: str, sha256: str) -> dict[str, Any]:
        """
        分片上传 · 完成阶段（OB12 文件资源模型，见分组说明——框架内尚无实现方）

        :param file_id: prepare 阶段返回的文件 ID
        :param sha256: **整个文件**的 SHA256（全小写十六进制）
        :return: 标准响应，data 包含 file_id（供以后使用）

        :example:
        >>> await adapter.Api.upload_file_fragmented_finish(file_id, sha256_hex)
        """
        return await self._api_call(
            "upload_file_fragmented",
            **self._merge_context({"stage": "finish", "file_id": file_id, "sha256": sha256}),
        )

    async def get_file_fragmented_prepare(self, file_id: str) -> dict[str, Any]:
        """
        分片下载 · 准备阶段（OB12 文件资源模型，见分组说明——框架内尚无实现方）

        分片下载两步：``prepare``（获取文件元信息）→ ``transfer``（循环取片）。

        :param file_id: 文件 ID
        :return: 标准响应，data 包含 name / total_size / sha256

        :example:
        >>> r = await adapter.Api.get_file_fragmented_prepare("file_abc")
        >>> meta = r["data"]
        """
        return await self._api_call(
            "get_file_fragmented", **self._merge_context({"stage": "prepare", "file_id": file_id})
        )

    async def get_file_fragmented_transfer(self, file_id: str, offset: int, size: int) -> dict[str, Any]:
        """
        分片下载 · 传输阶段（OB12 文件资源模型，见分组说明——框架内尚无实现方）

        按 ``offset`` 取一片，``size`` 为本次请求的字节数（最后一片可小于 size）。

        :param file_id: 文件 ID
        :param offset: 本次分片的字节偏移
        :param size: 本次请求大小（字节）
        :return: 标准响应，data 包含 data（本次分片字节）

        :example:
        >>> while offset < total_size:
        ...     r = await adapter.Api.get_file_fragmented_transfer(file_id, offset, 65536)
        ...     offset += len(r["data"]["data"])
        """
        return await self._api_call(
            "get_file_fragmented",
            **self._merge_context({"stage": "transfer", "file_id": file_id, "offset": int(offset), "size": int(size)}),
        )

    # ==================== 元（Meta）动作 ====================

    async def get_latest_events(self, limit: int = 0, timeout: int = 0) -> dict[str, Any]:
        """
        获取最新事件（仅 HTTP 通信方式必须支持）

        :param limit: 最多返回事件数量（0 = 不限制）
        :param timeout: 长轮询等待秒数（0 = 短轮询，不等待）
        :return: 标准响应，data 为事件对象数组（从旧到新，不含元事件）
        """
        return await self._api_call(
            "get_latest_events",
            **self._merge_context({"limit": int(limit), "timeout": int(timeout)}),
        )

    async def get_supported_actions(self) -> dict[str, Any]:
        """
        获取实现支持的动作列表

        :return: 标准响应，data 为动作名字符串数组（可能不含 get_latest_events）
        """
        return await self._api_call("get_supported_actions", **self._merge_context({}))

    async def get_status(self) -> dict[str, Any]:
        """
        获取运行状态

        :return: 标准响应，data 包含 good / bots
            - good: 各模块是否均正常（bool）
            - bots: 机器人账号状态列表，每项含 self{platform, user_id} 与 online
        """
        return await self._api_call("get_status", **self._merge_context({}))

    async def get_version(self) -> dict[str, Any]:
        """
        获取实现版本信息

        :return: 标准响应，data 包含 impl / version / onebot_version
        """
        return await self._api_call("get_version", **self._merge_context({}))

    # ==================== 通用扩展动作 ====================

    async def call(self, action: str, **params: Any) -> dict[str, Any]:
        """
        调用平台扩展动作（逃生舱）

        用于调用 OneBot12 标准之外的平台扩展动作。
        建议使用 ``{prefix}.{action}`` 命名（如 ``telegram.send_sticker``），
        遵循 OneBot12 扩展规则。

        :param action: 动作名称（标准动作名或 ``{prefix}.{action}`` 扩展动作名）
        :param params: 动作参数
        :return: 标准响应格式

        :example:
        >>> # 调用平台扩展动作
        >>> result = await adapter.myplatform.Api.call("telegram.send_sticker", sticker_id="CAACAgIAAxkBAA...")
        >>>
        >>> # 也可用于调用标准动作（等价于直接调用对应方法）
        >>> result = await adapter.myplatform.Api.call("get_user_info", user_id="123")
        """
        return await self._api_call(action, **self._merge_context(params))
