"""
ErisPulse 事件包装类

提供便捷的事件访问方法

{!--< tips >!--}
1. 继承自dict，完全兼容字典访问
2. 提供便捷方法简化事件处理
3. 支持点式访问 event.platform
{!--< /tips >!--}
"""

from typing import Any, Dict, List, Optional, Callable, Awaitable
from .. import adapter, logger


class Event(dict):
    """
    事件包装类
    
    提供便捷的事件访问方法
    
    {!--< tips >!--}
    所有方法都是可选的，不影响原有字典访问方式
    {!--< /tips >!--}
    """

    def __init__(self, event_data: Dict[str, Any]):
        """
        初始化事件包装器
        
        :param event_data: 原始事件数据
        """
        super().__init__(event_data)
        self._event_data = event_data

    # ==================== 核心必填字段方法 ====================

    def get_id(self) -> str:
        """
        获取事件ID
        
        :return: 事件ID
        """
        return self.get("id", "")

    def get_time(self) -> int:
        """
        获取事件时间戳
        
        :return: Unix时间戳（秒级）
        """
        return self.get("time", 0)

    def get_type(self) -> str:
        """
        获取事件类型
        
        :return: 事件类型（message/notice/request/meta等）
        """
        return self.get("type", "")

    def get_detail_type(self) -> str:
        """
        获取事件详细类型
        
        :return: 事件详细类型（private/group/friend等）
        """
        return self.get("detail_type", "")

    def get_platform(self) -> str:
        """
        获取平台名称
        
        :return: 平台名称
        """
        return self.get("platform", "")

    # ==================== 机器人信息方法 ====================

    def get_self_platform(self) -> str:
        """
        获取机器人平台
        
        :return: 机器人平台名称
        """
        return self.get("self", {}).get("platform", "")

    def get_self_user_id(self) -> str:
        """
        获取机器人用户ID
        
        :return: 机器人用户ID
        """
        return self.get("self", {}).get("user_id", "")

    def get_self_info(self) -> Dict[str, Any]:
        """
        获取机器人完整信息
        
        :return: 机器人信息字典
        """
        return self.get("self", {})

    # ==================== 消息事件专用方法 ====================

    def get_message(self) -> List[Dict[str, Any]]:
        """
        获取消息段数组
        
        :return: 消息段数组
        """
        return self.get("message", [])

    def get_alt_message(self) -> str:
        """
        获取消息备用文本
        
        :return: 消息备用文本
        """
        return self.get("alt_message", "")

    def get_text(self) -> str:
        """
        获取纯文本内容
        
        :return: 纯文本内容
        """
        return self.get_alt_message()

    def get_message_text(self) -> str:
        """
        获取纯文本内容（别名）
        
        :return: 纯文本内容
        """
        return self.get_alt_message()

    def has_mention(self) -> bool:
        """
        是否包含@消息
        
        :return: 是否包含@消息
        """
        message_segments = self.get_message()
        self_id = self.get_self_user_id()
        
        for segment in message_segments:
            if segment.get("type") == "mention":
                if segment.get("data", {}).get("user_id") == self_id:
                    return True
        return False

    def get_mentions(self) -> List[str]:
        """
        获取所有被@的用户ID列表
        
        :return: 被@的用户ID列表
        """
        message_segments = self.get_message()
        mentions = []
        
        for segment in message_segments:
            if segment.get("type") == "mention":
                user_id = segment.get("data", {}).get("user_id")
                if user_id:
                    mentions.append(user_id)
        
        return mentions

    def get_user_id(self) -> str:
        """
        获取发送者ID
        
        :return: 发送者用户ID
        """
        return self.get("user_id", "")

    def get_user_nickname(self) -> str:
        """
        获取发送者昵称
        
        :return: 发送者昵称
        """
        return self.get("user_nickname", "")

    def get_group_id(self) -> str:
        """
        获取群组ID
        
        :return: 群组ID（群聊消息）
        """
        return self.get("group_id", "")

    def get_channel_id(self) -> str:
        """
        获取频道ID
        
        :return: 频道ID（频道消息）
        """
        return self.get("channel_id", "")

    def get_guild_id(self) -> str:
        """
        获取服务器ID
        
        :return: 服务器ID（服务器消息）
        """
        return self.get("guild_id", "")

    def get_thread_id(self) -> str:
        """
        获取话题/子频道ID
        
        :return: 话题ID（话题消息）
        """
        return self.get("thread_id", "")

    def get_sender(self) -> Dict[str, Any]:
        """
        获取发送者信息字典
        
        :return: 发送者信息字典
        """
        return {
            "user_id": self.get_user_id(),
            "nickname": self.get_user_nickname(),
            "group_id": self.get_group_id() if self.is_group_message() else None
        }

    # ==================== 消息类型判断 ====================

    def is_message(self) -> bool:
        """
        是否为消息事件
        
        :return: 是否为消息事件
        """
        return self.get_type() == "message"

    def is_private_message(self) -> bool:
        """
        是否为私聊消息
        
        :return: 是否为私聊消息
        """
        return self.is_message() and self.get_detail_type() == "private"

    def is_group_message(self) -> bool:
        """
        是否为群聊消息
        
        :return: 是否为群聊消息
        """
        return self.is_message() and self.get_detail_type() == "group"

    def is_at_message(self) -> bool:
        """
        是否为@消息
        
        :return: 是否为@消息
        """
        return self.has_mention()

    # ==================== 通知事件专用方法 ====================

    def get_operator_id(self) -> str:
        """
        获取操作者ID
        
        :return: 操作者ID
        """
        return self.get("operator_id", "")

    def get_operator_nickname(self) -> str:
        """
        获取操作者昵称
        
        :return: 操作者昵称
        """
        return self.get("operator_nickname", "")

    # ==================== 通知类型判断 ====================

    def is_notice(self) -> bool:
        """
        是否为通知事件
        
        :return: 是否为通知事件
        """
        return self.get_type() == "notice"

    def is_group_member_increase(self) -> bool:
        """
        群成员增加
        
        :return: 是否为群成员增加事件
        """
        return self.is_notice() and self.get_detail_type() == "group_member_increase"

    def is_group_member_decrease(self) -> bool:
        """
        群成员减少
        
        :return: 是否为群成员减少事件
        """
        return self.is_notice() and self.get_detail_type() == "group_member_decrease"

    def is_friend_add(self) -> bool:
        """
        好友添加
        
        :return: 是否为好友添加事件
        """
        return self.is_notice() and self.get_detail_type() == "friend_add"

    def is_friend_delete(self) -> bool:
        """
        好友删除
        
        :return: 是否为好友删除事件
        """
        return self.is_notice() and self.get_detail_type() == "friend_delete"

    # ==================== 请求事件专用方法 ====================

    def get_comment(self) -> str:
        """
        获取请求附言
        
        :return: 请求附言
        """
        return self.get("comment", "")

    # ==================== 请求类型判断 ====================

    def is_request(self) -> bool:
        """
        是否为请求事件
        
        :return: 是否为请求事件
        """
        return self.get_type() == "request"

    def is_friend_request(self) -> bool:
        """
        是否为好友请求
        
        :return: 是否为好友请求
        """
        return self.is_request() and self.get_detail_type() == "friend"

    def is_group_request(self) -> bool:
        """
        是否为群组请求
        
        :return: 是否为群组请求
        """
        return self.is_request() and self.get_detail_type() == "group"

    # ==================== 回复功能 ====================

    def _get_adapter_and_target(self) -> tuple:
        """
        获取适配器实例和目标信息
        
        基于 OneBot12 标准，直接使用事件的 detail_type 字段
        
        :return: (适配器实例, 发送目标类型, 目标ID)
        """
        platform = self.get_platform()
        if not platform:
            raise ValueError("平台信息缺失")

        adapter_instance = getattr(adapter, platform, None)
        if not adapter_instance:
            raise ValueError(f"找不到平台 {platform} 的适配器")

        # 直接使用事件的 detail_type
        detail_type = self.get_detail_type()
        
        # 根据 detail_type 获取对应的目标 ID 字段
        # 遵循 OneBot12 标准：private、group 是标准类型
        # 也兼容各平台可能扩展的类型：channel、guild、thread 等
        id_field_map = {
            # OneBot12 标准类型
            "private": "user_id",
            "group": "group_id",
            
            # 平台扩展类型
            "user": "user_id",  # 兼容某些平台使用 user 的情况
            "channel": "channel_id",
            "guild": "guild_id",
            "thread": "thread_id",
            "supergroup": "group_id",  # Telegram supergroup 映射到 group_id
        }
        
        # 获取对应的目标 ID 字段名，默认使用 user_id
        id_field = id_field_map.get(detail_type, "user_id")
        
        # 获取目标 ID
        target_id = self.get(id_field, "")
        
        # 如果目标 ID 为空，尝试从其他字段获取（兼容性处理）
        if not target_id:
            if detail_type in ["group", "channel", "guild", "supergroup"]:
                # 对于群组/频道相关类型，尝试多个可能的字段
                target_id = (
                    self.get("group_id") or 
                    self.get("channel_id") or 
                    self.get("guild_id") or 
                    ""
                )
            else:
                # 对于其他类型（主要是 private），使用 user_id
                target_id = self.get_user_id()

        if not target_id:
            raise ValueError(f"无法获取目标 ID (detail_type={detail_type})")

        # 映射到适配器发送方法的目标类型
        # 事件中的 detail_type "private" 需要映射为发送目标的 "user"
        send_target_type_map = {
            "private": "user",
            "group": "group",
            "user": "user",
            "channel": "channel",
            "guild": "guild",
            "thread": "thread",
            "supergroup": "group",
        }
        send_target_type = send_target_type_map.get(detail_type, detail_type)

        return adapter_instance, send_target_type, target_id

    async def reply(self, 
                   content: str, 
                   method: str = "Text",
                   **kwargs) -> Any:
        """
        通用回复方法
        
        基于适配器的Text方法，但可以通过method参数指定其他发送方法
        
        :param content: 发送内容（文本、URL等，取决于method参数）
        :param method: 适配器发送方法，默认为"Text"
                       可选值: "Text", "Image", "Voice", "Video", "File" 等
        :param kwargs: 额外参数，例如Mention方法的user_id
        :return: 适配器发送方法的返回值
        
        :example:
        >>> await event.reply("你好")  # 发送文本
        >>> await event.reply("http://example.com/image.jpg", method="Image")  # 发送图片
        >>> await event.reply("回复内容", method="Mention", user_id="123456")  # @用户并发送
        >>> await event.reply("http://example.com/voice.mp3", method="Voice")  # 发送语音
        """
        adapter_instance, detail_type, target_id = self._get_adapter_and_target()
        
        # 构建发送链
        send_chain = adapter_instance.Send.To(detail_type, target_id)
        
        # 处理特殊方法
        if method == "Mention":
            user_id = kwargs.get("user_id")
            if user_id is None:
                user_id = self.get_user_id()
            send_chain = send_chain.Mention(user_id)
            method = "Text"
        
        # 调用指定方法
        send_method = getattr(send_chain, method, None)
        if not send_method or not callable(send_method):
            raise ValueError(f"适配器不支持方法: {method}")
        
        return await send_method(content)

    async def forward_to_group(self, group_id: str):
        """
        转发到群组
        
        :param group_id: 目标群组ID
        """
        adapter_instance = getattr(adapter, self.get_platform(), None)
        if not adapter_instance:
            raise ValueError(f"找不到平台 {self.get_platform()} 的适配器")
        await adapter_instance.Forward.To("group", group_id).Event(self)

    async def forward_to_user(self, user_id: str):
        """
        转发给用户
        
        :param user_id: 目标用户ID
        """
        adapter_instance = getattr(adapter, self.get_platform(), None)
        if not adapter_instance:
            raise ValueError(f"找不到平台 {self.get_platform()} 的适配器")
        await adapter_instance.Forward.To("user", user_id).Event(self)

    # ==================== 等待回复功能 ====================

    async def wait_reply(self,
                        prompt: str = None,
                        timeout: float = 60.0,
                        callback: Callable[[Dict[str, Any]], Awaitable[Any]] = None,
                        validator: Callable[[Dict[str, Any]], bool] = None) -> Optional['Event']:
        """
        等待用户回复
        
        :param prompt: 提示消息，如果提供会发送给用户
        :param timeout: 等待超时时间(秒)
        :param callback: 回调函数，当收到回复时执行
        :param validator: 验证函数，用于验证回复是否有效
        :return: 用户回复的事件数据，如果超时则返回None
        """
        # 导入command处理器以复用等待逻辑
        from .command import command as command_handler

        # 发送提示消息（如果提供）
        if prompt:
            try:
                # 使用相同的目标获取逻辑
                adapter_instance, detail_type, target_id = self._get_adapter_and_target()
                await adapter_instance.Send.To(detail_type, target_id).Text(prompt)
            except Exception as e:
                logger.warning(f"发送提示消息失败: {e}")

        # 使用command处理器的wait_reply方法
        result = await command_handler.wait_reply(
            self,
            prompt=None,  # 已经发送过提示了
            timeout=timeout,
            callback=callback,
            validator=validator
        )

        # 将结果转换为Event对象
        if result:
            return Event(result)
        return None

    # ==================== 原始数据和元信息 ====================

    def get_raw(self) -> Dict[str, Any]:
        """
        获取原始事件数据
        
        :return: 原始事件数据字典
        """
        platform = self.get_platform()
        raw_key = f"{platform}_raw" if platform else "raw"
        return self.get(raw_key, {})

    def get_raw_type(self) -> str:
        """
        获取原始事件类型
        
        :return: 原始事件类型
        """
        platform = self.get_platform()
        raw_type_key = f"{platform}_raw_type" if platform else "raw_type"
        return self.get(raw_type_key, "")

    # ==================== 命令信息 ====================

    def get_command_name(self) -> str:
        """
        获取命令名称
        
        :return: 命令名称
        """
        return self.get("command", {}).get("name", "")

    def get_command_args(self) -> List[str]:
        """
        获取命令参数
        
        :return: 命令参数列表
        """
        return self.get("command", {}).get("args", [])

    def get_command_raw(self) -> str:
        """
        获取命令原始文本
        
        :return: 命令原始文本
        """
        return self.get("command", {}).get("raw", "")

    def get_command_info(self) -> Dict[str, Any]:
        """
        获取完整命令信息
        
        :return: 命令信息字典
        """
        return self.get("command", {})

    def is_command(self) -> bool:
        """
        是否为命令
        
        :return: 是否为命令
        """
        return "command" in self and bool(self.get("command"))

    # ==================== 工具方法 ====================

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        
        :return: 事件数据字典
        """
        return dict(self)

    def is_processed(self) -> bool:
        """
        是否已被处理
        
        :return: 是否已被处理
        """
        return self.get("_processed", False)

    def mark_processed(self):
        """
        标记为已处理
        """
        self["_processed"] = True

    # ==================== 魔术方法 ====================

    def __getattr__(self, name: str) -> Any:
        """
        支持点式访问字典键
        
        :param name: 属性名
        :return: 属性值
        """
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def __repr__(self) -> str:
        """
        字符串表示
        
        :return: 字符串表示
        """
        event_type = self.get_type()
        detail_type = self.get_detail_type()
        platform = self.get_platform()
        return f"Event(type={event_type}, detail_type={detail_type}, platform={platform})"


__all__ = [
    "Event"
]
