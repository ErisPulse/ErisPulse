"""
ErisPulse 适配器基础模块

提供适配器和消息发送DSL的基类实现

{!--< tips >!--}
1. 用于实现与不同平台的交互接口
2. 提供统一的消息发送DSL风格接口
{!--< /tips >!--}
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Any
from collections.abc import Awaitable


class SendDSL:
    """
    消息发送DSL基类

    用于实现 Send.To(...).Func(...) 风格的链式调用接口

    内置支持 At/AtAll/Reply 修饰器，适配器子类无需重复实现。
    通过 send_context 属性可显式获取发送上下文（目标类型、目标ID、发送账号）。
    通过 _apply_modifiers() 方法可自动将修饰器状态合并到消息段。

    {!--< tips >!--}
    1. 子类应实现具体的消息发送方法(如Text, Image等)
    2. 通过__getattr__实现动态方法调用
    3. At/AtAll/Reply 已内置实现，无需子类覆盖
    4. 使用 self.send_context 获取发送上下文
    5. 使用 self._apply_modifiers(message) 合并修饰器到消息段
    {!--< /tips >!--}
    """

    def __init__(
        self,
        adapter: "BaseAdapter",
        target_type: str | None = None,
        target_id: str | None = None,
        account_id: str | None = None,
    ):
        """
        初始化DSL发送器

        :param adapter: 所属适配器实例
        :param target_type: 目标类型(可选)
        :param target_id: 目标ID(可选)
        :param account_id: 发送账号(可选)
        """
        self._adapter = adapter
        self._target_type = target_type
        self._target_id = target_id
        self._target_to = target_id
        self._account_id = account_id
        self._at_user_ids: list[str] = []
        self._reply_message_id: str | None = None
        self._at_all: bool = False

    def __getattr__(self, name: str):
        """
        动态属性访问处理，实现大小写不敏感调用

        1. 如果找到匹配的方法（忽略大小写），返回该方法
        2. 如果没找到，打印警告并抛出 AttributeError

        :param name: 属性名
        :return: 匹配的方法或属性
        :raises AttributeError: 当属性不存在时抛出
        """
        # 检查所有实际存在的方法
        for attr_name in dir(self.__class__):
            # 跳过特殊方法
            if attr_name.startswith("_"):
                continue

            # 大小写不敏感匹配
            if attr_name.lower() == name.lower():
                # 返回实际的方法绑定到当前实例
                attr = getattr(self.__class__, attr_name)
                if callable(attr):
                    return attr.__get__(self, self.__class__)
                return attr

        # 没有找到匹配的方法，打印警告
        from ..logger import logger

        logger.warning(
            f"平台 {self._adapter.__class__.__name__} 未实现 {name} 发送方法"
        )

        # 抛出 AttributeError，这样 hasattr() 能正常工作
        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{name}'"
        )

    def At(self, user_id: str) -> "SendDSL":
        """
        @指定用户（可链式多次调用）

        :param user_id: 要@的用户ID
        :return: SendDSL实例自身，支持链式调用

        :example:
        >>> await adapter.Send.To("group", "123").At("456").Text("Hello")
        >>> await adapter.Send.To("group", "123").At("456").At("789").Text("@多人")
        """
        self._at_user_ids.append(user_id)
        return self

    def AtAll(self) -> "SendDSL":
        """
        @全体成员

        :return: SendDSL实例自身，支持链式调用

        :example:
        >>> await adapter.Send.To("group", "123").AtAll().Text("公告")
        """
        self._at_all = True
        return self

    def Reply(self, message_id: str) -> "SendDSL":
        """
        回复指定消息

        :param message_id: 要回复的消息ID
        :return: SendDSL实例自身，支持链式调用

        :example:
        >>> await adapter.Send.To("group", "123").Reply("msg_456").Text("回复内容")
        """
        self._reply_message_id = message_id
        return self

    def _apply_modifiers(self, message) -> list[dict]:
        """
        将 At/AtAll/Reply 修饰器应用到消息段

        修饰器按以下顺序添加到消息段前：
        1. mention_all (@全体)
        2. mention (@用户，按调用顺序)
        3. reply (回复)

        :param message: OneBot12 消息段（dict 或 list[dict]）
        :return: 合并后的消息段列表

        :example:
        >>> segments = self._apply_modifiers([
        >>>     {"type": "text", "data": {"text": "Hello"}}
        >>> ])
        """
        if isinstance(message, dict):
            segments = [message]
        else:
            segments = list(message)

        modifier_segments = []

        if self._at_all:
            modifier_segments.append({"type": "mention_all", "data": {}})

        for uid in self._at_user_ids:
            modifier_segments.append({"type": "mention", "data": {"user_id": uid}})

        if self._reply_message_id:
            modifier_segments.append({"type": "reply", "data": {"message_id": self._reply_message_id}})

        return modifier_segments + segments

    @property
    def send_context(self) -> dict:
        """
        获取当前发送上下文（目标信息 + 发送账号）

        :return: 包含 target_type, target_id, account_id 的字典

        :example:
        >>> ctx = self.send_context
        >>> # {"target_type": "group", "target_id": "123", "account_id": "bot1"}
        >>> await self._adapter.call_api(
        >>>     endpoint="/send_message",
        >>>     message=segments,
        >>>     **self.send_context,
        >>>     **kwargs
        >>> )
        """
        return {
            "target_type": self._target_type,
            "target_id": self._target_id,
            "account_id": self._account_id,
        }

    def Raw_ob12(self, message, **kwargs):
        """
        发送 OneBot12 格式消息段（必须由适配器子类重写）

        :param message: OneBot12 消息段列表或单个消息段
        :param kwargs: 其他参数
        :return: asyncio.Task
        """
        from ..logger import logger

        logger.error(
            f"平台 {self._adapter.__class__.__name__} 未实现 Raw_ob12 方法，"
            f"消息未被发送。适配器必须实现此方法以支持 OneBot12 消息段发送。"
        )

        async def _not_impl():
            return {
                "status": "failed",
                "retcode": 10002,
                "data": None,
                "message_id": "",
                "message": f"平台 {self._adapter.__class__.__name__} 未实现 Raw_ob12 方法",
            }

        try:
            return asyncio.create_task(_not_impl())
        except RuntimeError:
            return asyncio.ensure_future(_not_impl())

    def To(self, target_type: str = None, target_id: str | int = None) -> "SendDSL":
        """
        设置消息目标

        支持自动类型转换：
        - 当 target_type 为 "private" 时，自动转换为 "user"
        - 当只提供 target_id（字符串或数字）时，默认推断为 "user"

        :param target_type: 目标类型(可选)
        :param target_id: 目标ID(可选)
        :return: SendDSL实例

        :example:
        >>> # 标准用法
        >>> adapter.Send.To("user", "123").Text("Hello")
        >>> # 自动转换 private → user
        >>> adapter.Send.To("private", "123").Text("Hello")
        >>> # 简化形式（默认推断为 user）
        >>> adapter.Send.To("123").Text("Hello")
        """
        from ..Event.session_type import is_standard_type

        # 处理简化形式：只提供一个参数作为 target_id
        if target_id is None and target_type is not None:
            target_id = target_type
            target_type = None

        # 如果没有明确指定 target_type，尝试推断
        if target_type is None:
            # 将 target_id 作为字符串处理
            if target_id is not None:
                # 默认推断为 user（对应 private）
                # 这里我们假设如果只提供 ID，通常是发送给用户
                target_type = "user"

        # 自动转换 private → user
        if target_type == "private":
            target_type = "user"

        return self.__class__(self._adapter, target_type, target_id, self._account_id)

    def Using(self, account_id: str | int) -> "SendDSL":
        """
        设置发送账号

        :param _account_id: 发送账号
        :return: SendDSL实例

        :example:
        >>> adapter.Send.Using("bot1").To("123").Text("Hello")
        >>> adapter.Send.To("123").Using("bot1").Text("Hello")  # 支持乱序
        """
        return self.__class__(
            self._adapter, self._target_type, self._target_id, account_id
        )

    def Account(self, account_id: str | int) -> "SendDSL":
        """
        设置发送账号

        :param _account_id: 发送账号
        :return: SendDSL实例

        :example:
        >>> adapter.Send.Account("bot1").To("123").Text("Hello")
        >>> adapter.Send.To("123").Account("bot1").Text("Hello")  # 支持乱序
        """
        return self.__class__(
            self._adapter, self._target_type, self._target_id, account_id
        )


class RequestDSL:
    """
    请求操作 DSL 基类

    用于对请求事件（好友请求、群邀请等）执行同意/拒绝操作。
    采用与 Send 一致的工厂实例模式：``adapter.Request("req_id").accept()``

    适配器只需在内部类中重写 ``accept`` / ``reject`` 即可。

    {!--< tips >!--}
    1. 使用 ``adapter.Request(request_id).accept()`` 同意请求
    2. 使用 ``adapter.Request(request_id).reject()`` 拒绝请求
    3. 适配器重写 ``accept`` / ``reject`` 实现平台逻辑
    4. 基类默认返回 ``retcode=10002``（不支持的操作）
    {!--< /tips >!--}
    """

    def __init__(self, adapter: "BaseAdapter", request_id: str | None = None, account_id: str | None = None):
        """
        初始化请求操作 DSL

        :param adapter: 所属适配器实例
        :param request_id: 请求ID
        :param account_id: 执行操作的 Bot 账号
        """
        self._adapter = adapter
        self._request_id = request_id
        self._account_id = account_id

    def __call__(self, request_id: str) -> "RequestDSL":
        """
        设置请求ID，返回新的 RequestDSL 实例

        使得 ``adapter.Request("req_id")`` 可以直接调用

        :param request_id: 请求ID
        :return: 新的 RequestDSL 实例
        """
        return self.__class__(self._adapter, request_id, self._account_id)

    def Using(self, account_id: str | int) -> "RequestDSL":
        """
        指定执行操作的 Bot 账号

        :param account_id: 账号标识
        :return: 新的 RequestDSL 实例

        :example:
        >>> adapter.Request("req_123").Using("bot1").accept()
        """
        return self.__class__(self._adapter, self._request_id, account_id)

    def accept(self, **kwargs) -> Awaitable[Any]:
        """
        同意请求

        :param kwargs: 平台扩展参数（如 comment 备注）
        :return: asyncio.Task，await 后返回标准响应格式

        :example:
        >>> result = await adapter.Request("req_123").accept()
        >>> result = await adapter.Request("req_123").accept(comment="欢迎")
        """
        return self._create_task(self._do_accept(**kwargs))

    def reject(self, **kwargs) -> Awaitable[Any]:
        """
        拒绝请求

        :param kwargs: 平台扩展参数（如 comment 拒绝理由）
        :return: asyncio.Task，await 后返回标准响应格式

        :example:
        >>> result = await adapter.Request("req_123").reject()
        >>> result = await adapter.Request("req_123").reject(comment="暂不添加")
        """
        return self._create_task(self._do_reject(**kwargs))

    async def _do_accept(self, **kwargs) -> dict[str, Any]:
        """
        同意请求的具体实现（适配器子类重写）

        :param kwargs: 平台扩展参数
        :return: 标准响应格式
        """
        return self._not_implemented_response("accept")

    async def _do_reject(self, **kwargs) -> dict[str, Any]:
        """
        拒绝请求的具体实现（适配器子类重写）

        :param kwargs: 平台扩展参数
        :return: 标准响应格式
        """
        return self._not_implemented_response("reject")

    def _not_implemented_response(self, action: str) -> dict[str, Any]:
        """
        生成「未实现」的标准错误响应

        :param action: 操作名称（accept/reject）
        :return: 标准错误响应字典
        """
        from ..logger import logger

        platform_name = self._adapter.__class__.__name__
        logger.warning(
            f"平台 {platform_name} 未实现 Request.{action}() 方法，"
            f"请求 {self._request_id} 未被处理。"
        )
        return {
            "status": "failed",
            "retcode": 10002,
            "data": None,
            "message_id": "",
            "message": f"平台 {platform_name} 未实现请求操作 ({action})",
        }

    def _create_task(self, coro) -> Awaitable[Any]:
        """创建 asyncio.Task"""
        try:
            return asyncio.create_task(coro)
        except RuntimeError:
            return asyncio.ensure_future(coro)

    @property
    def request_context(self) -> dict:
        """
        获取当前请求操作上下文

        :return: 包含 request_id, account_id 的字典
        """
        return {
            "request_id": self._request_id,
            "account_id": self._account_id,
        }


class BaseAdapter(ABC):
    """
    适配器基类

    提供与外部平台交互的标准接口，子类必须实现必要方法

    {!--< tips >!--}
    1. 必须实现call_api, start和shutdown方法
    2. 可以自定义Send类实现平台特定的消息发送逻辑
    3. 可以自定义Request类实现平台特定的请求操作逻辑
    4. 通过on装饰器注册事件处理器
    5. 支持OneBot12协议的事件处理
    {!--< /tips >!--}
    """

    class Request(RequestDSL):
        """
        请求操作 DSL 实现

        适配器子类重写 ``accept`` / ``reject`` 以实现平台特定逻辑。

        {!--< tips >!--}
        1. 默认实现返回 ``retcode=10002``（不支持的操作）
        2. 适配器应重写 ``accept`` / ``reject`` 方法
        3. 通过 ``self._adapter.call_api()`` 调用平台 API
        4. 通过 ``self._request_id`` 获取请求标识
        5. 通过 ``self._account_id`` 获取 Bot 账号
        {!--< /tips >!--}
        """
        pass

    class Send(SendDSL):
        """
        消息发送DSL实现

        {!--< tips >!--}
        1. 子类可以重写Text方法提供平台特定实现
        2. 可以添加新的消息类型(如Image, Voice等)
        {!--< /tips >!--}
        """

        def Example(self, text: str) -> Awaitable[Any]:
            """
            示例消息发送方法

            :param text: 文本内容
            :return: 异步任务
            :example:
            >>> await adapter.Send.To("123").Example("Hello")
            """
            mock_response = {
                "status": "ok",
                "retcode": 0,
                "data": {"message_id": "1234567890", "time": 1755801512},
                "message_id": "1234567890",
                "message": "",
                "echo": None,
                "example_raw": {
                    "result": "success",
                },
            }

            async def _send_example():
                from ..logger import logger

                logger.info(f"发送示例消息: {text}")
                return mock_response

            return asyncio.create_task(_send_example())

        def Raw_ob12(self, message, **kwargs: Any) -> Awaitable[Any]:
            """
            发送 OneBot12 格式消息段（必须由适配器子类重写）

            此方法是反向转换（OneBot12 → 平台）的统一入口，适配器必须重写此方法。
            未重写时，基类默认实现会记录错误日志并返回标准错误响应。

            推荐使用框架提供的辅助方法：
            - self._apply_modifiers(message) - 合并 At/AtAll/Reply 修饰器到消息段
            - self.send_context - 获取发送上下文 (target_type, target_id, account_id)

            :param message: OneBot12 格式的消息段数组或单个消息段
                [
                    {"type": "text", "data": {"text": "Hello"}},
                    {"type": "image", "data": {"file": "https://..."}},
                ]
            :param kwargs: 其他参数
            :return: asyncio.Task，await 后返回标准响应格式

            :example:
            >>> # 用户调用
            >>> await adapter.Send.To("user", "123").Raw_ob12([
            >>>     {"type": "text", "data": {"text": "Hello"}},
            >>>     {"type": "image", "data": {"file": "https://..."}}
            >>> ])
            >>>
            >>> # 适配器子类重写示例（推荐：使用框架辅助方法）
            >>> def Raw_ob12(self, message, **kwargs):
            >>>     async def _do_send():
            >>>         segments = self._apply_modifiers(message)
            >>>         return await self._adapter.call_api(
            >>>             endpoint="/send_message",
            >>>             message=segments,
            >>>             **self.send_context,
            >>>             **kwargs
            >>>         )
            >>>     return asyncio.create_task(_do_send())
            """

            async def _send_raw():
                from ..logger import logger

                logger.error(
                    f"适配器 {self._adapter.__class__.__name__} 未实现 Raw_ob12 方法，"
                    f"消息未被发送。适配器必须实现此方法以支持 OneBot12 消息段发送。"
                )
                return {
                    "status": "failed",
                    "retcode": 10002,
                    "data": None,
                    "message_id": "",
                    "message": f"适配器 {self._adapter.__class__.__name__} 未实现 Raw_ob12 方法",
                }

            try:
                return asyncio.create_task(_send_raw())
            except RuntimeError:
                return asyncio.ensure_future(_send_raw())

    def __init__(self):
        self.Send = self.__class__.Send(self)
        self.Request = self.__class__.Request(self)

    @abstractmethod
    async def call_api(self, endpoint: str, **params: Any) -> Any:
        """
        调用平台API的抽象方法

        :param endpoint: API端点
        :param params: API参数
        :return: API调用结果
        :raises NotImplementedError: 必须由子类实现
        """
        raise NotImplementedError("适配器必须实现call_api方法")

    @abstractmethod
    async def start(self) -> None:
        """
        启动适配器的抽象方法

        :raises NotImplementedError: 必须由子类实现
        """
        raise NotImplementedError("适配器必须实现start方法")

    @abstractmethod
    async def shutdown(self) -> None:
        """
        关闭适配器的抽象方法

        :raises NotImplementedError: 必须由子类实现
        """
        raise NotImplementedError("适配器必须实现shutdown方法")

    async def emit(self, *args, **kwargs):
        raise NotImplementedError(
            "适配器的 emit 方法已被弃用。请使用 adapter.emit() 通过 AdapterManager 提交事件。"
            "如果你是适配器开发者，请查看 ErisPulse 文档进行更新。"
        )

    def send(
        self, target_type: str, target_id: str, message: Any, **kwargs: Any
    ) -> asyncio.Task:
        """
        发送消息的便捷方法，返回一个 asyncio Task

        :param target_type: 目标类型
        :param target_id: 目标ID
        :param message: 消息内容
        :param kwargs: 其他参数
            - method: 发送方法名(默认为"Text")
        :return: asyncio.Task 对象，用户可以自主决定是否等待

        :raises AttributeError: 当发送方法不存在时抛出

        :example:
        >>> task = adapter.send("user", "123", "Hello")
        >>> # 用户可以选择等待: result = await task
        >>> # 或者不等待让其在后台执行
        >>> await adapter.send("group", "456", "Hello", method="Markdown")  # 直接等待
        """

        async def _send_wrapper():
            method_name = kwargs.pop("method", "Text")
            method = getattr(self.Send.To(target_type, target_id), method_name, None)
            if not method:
                raise AttributeError(
                    f"未找到 {method_name} 方法，请确保已在 Send 类中定义"
                )
            return await method(message, **kwargs)

        try:
            return asyncio.create_task(_send_wrapper())
        except RuntimeError:
            return asyncio.ensure_future(_send_wrapper())


__all__ = [
    "BaseAdapter",
    "SendDSL",
    "RequestDSL",
]
