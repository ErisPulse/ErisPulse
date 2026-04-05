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
from typing import (
    Any, Optional,
    Union, Awaitable
)

class SendDSL:
    """
    消息发送DSL基类
    
    用于实现 Send.To(...).Func(...) 风格的链式调用接口
    
    {!--< tips >!--}
    1. 子类应实现具体的消息发送方法(如Text, Image等)
    2. 通过__getattr__实现动态方法调用
    {!--< /tips >!--}
    """
    
    def __init__(self, adapter: 'BaseAdapter', target_type: Optional[str] = None, target_id: Optional[str] = None, account_id: Optional[str] = None):
        """
        初始化DSL发送器
        
        :param adapter: 所属适配器实例
        :param target_type: 目标类型(可选)
        :param target_id: 目标ID(可选)
        :param _account_id: 发送账号(可选)
        """
        self._adapter = adapter
        self._target_type = target_type
        self._target_id = target_id
        self._target_to = target_id
        self._account_id = account_id
    
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
            if attr_name.startswith('_'):
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
            f"平台 {self._adapter.__class__.__name__} "
            f"未实现 {name} 发送方法"
        )
        
        # 抛出 AttributeError，这样 hasattr() 能正常工作
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    
    def _unimplemented_modifier(self, method_name: str, **kwargs) -> 'SendDSL':
        """处理未实现的修饰方法，记录警告并返回自身以保持链式调用"""
        from ..logger import logger
        logger.warning(
            f"平台 {self._adapter.__class__.__name__} 未实现 {method_name} 方法，该修饰方法将被忽略。"
            f"参数: {kwargs}"
        )
        return self

    def At(self, **kwargs):
        return self._unimplemented_modifier("At", **kwargs)

    def Reply(self, **kwargs):
        return self._unimplemented_modifier("Reply", **kwargs)

    def AtAll(self, **kwargs):
        return self._unimplemented_modifier("AtAll", **kwargs)
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
        return asyncio.create_task(_not_impl())

    def To(self, target_type: str = None, target_id: Union[str, int] = None) -> 'SendDSL':
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

    def Using(self, account_id: Union[str, int]) -> 'SendDSL':
        """
        设置发送账号
        
        :param _account_id: 发送账号
        :return: SendDSL实例
        
        :example:
        >>> adapter.Send.Using("bot1").To("123").Text("Hello")
        >>> adapter.Send.To("123").Using("bot1").Text("Hello")  # 支持乱序
        """
        return self.__class__(self._adapter, self._target_type, self._target_id, account_id)
    
    def Account(self, account_id: Union[str, int]) -> 'SendDSL':
        """
        设置发送账号
        
        :param _account_id: 发送账号
        :return: SendDSL实例
        
        :example:
        >>> adapter.Send.Account("bot1").To("123").Text("Hello")
        >>> adapter.Send.To("123").Account("bot1").Text("Hello")  # 支持乱序
        """
        return self.__class__(self._adapter, self._target_type, self._target_id, account_id)

class BaseAdapter(ABC):
    """
    适配器基类
    
    提供与外部平台交互的标准接口，子类必须实现必要方法
    
    {!--< tips >!--}
    1. 必须实现call_api, start和shutdown方法
    2. 可以自定义Send类实现平台特定的消息发送逻辑
    3. 通过on装饰器注册事件处理器
    4. 支持OneBot12协议的事件处理
    {!--< /tips >!--}
    """
    
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
                "data": {
                    "message_id": "1234567890",
                    "time": 1755801512
                },
                "message_id": "1234567890",
                "message": "",
                "echo": None,
                "example_raw": {
                    "result": "success",
                }
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

            >>> # 适配器子类重写示例（必须）
            >>> def Raw_ob12(self, message, **kwargs):
            >>>     return asyncio.create_task(
            >>>         self._adapter.call_api(
            >>>             "send_message",
            >>>             message=message,
            >>>             target_type=self._target_type,
            >>>             target_id=self._target_id,
            >>>             account_id=self._account_id,
            >>>             **kwargs
            >>>         )
            >>>     )
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

            return asyncio.create_task(_send_raw())

    def __init__(self):
        self.Send = self.__class__.Send(self)

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
    
    async def emit(self) -> None:
        from ..logger import logger
        logger.error("适配器调用了一个被弃用的原生方法emit，请检查适配器的实现，如果你是开发者请查看ErisPulse的文档进行更新。如果你是普通用户请查看本适配器是否有更新")

    def send(self, target_type: str, target_id: str, message: Any, **kwargs: Any) -> asyncio.Task:
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
                raise AttributeError(f"未找到 {method_name} 方法，请确保已在 Send 类中定义")
            return await method(message, **kwargs)
        
        return asyncio.create_task(_send_wrapper())

__all__ = [
    "BaseAdapter",
    "SendDSL",
]
