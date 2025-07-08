from ErisPulse import EventDataBase
from typing import Optional

class MyAdapterEventParser(EventDataBase):
    """
    事件处理工具
    
    继承自 EventDataBase 类，用于处理事件数据。
    
    :param event: 事件数据
    :type event: Dict[str, Any]

    继承类部分会接受并定义一个名为 self.event 的属性，用于存储事件数据
    """
    @property
    def platform(self) -> str:
        # 这里你需要返回事件平台
        return "MyAdapter"
    
    @property
    def type(self) -> str:
        # 这里你需要返回事件的类型(如果你在Adapter进行了事件映射, 这里需要返回映射后的类型)
        type = self.event.get("type")
        return type
    
    @property
    def content(self) -> str:
        # 这里你需要返回事件中的文本内容
        message_text = self.event.get("message", {}).get("text", "")
        return message_text
    
    @property
    def sender_type(self) -> str:
        # 这里你需要返回事件发送者类型
        sender_type = self.event.get("sender_type")
        return sender_type
    @property
    def sender_name(self) -> str:
        # 这里你需要返回事件发送者名称
        sender_name = self.event.get("sender_name")
        return sender_name
    @property
    def user_id(self) -> str:
        # 这里你需要返回事件发送者ID
        user_id = self.event.get("user_id")
        return user_id
    
    @property
    def group_id(self) -> str:
        # 这里你需要返回事件发送群组ID
        group_id = self.event.get("group_id")
        return group_id
    
    @property
    def channel_id(self) -> Optional[str]:
        # 这里你需要返回事件发送频道ID | 这不是一个必须实现的属性，如果你的适配器不支持频道消息，可以不实现这个属性
        channel_id = self.event.get("channel_id")
        return channel_id
    
    @property
    def message_id(self) -> str:
        # 这里你需要返回事件消息ID
        message_id = self.event.get("message_id")
        return message_id