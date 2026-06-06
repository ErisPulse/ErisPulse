"""
MyAdapter转换器

用于在平台特定消息格式和ErisPulse标准格式之间进行转换
"""

import time
import uuid


class MyPlatformConverter:
    """
    MyAdapter转换器类

    负责将平台特定的事件格式转换为ErisPulse标准格式（OneBot12）
    """

    def __init__(self, platform: str = "myplatform"):
        self.platform = platform

    def convert(self, raw_event: dict) -> dict:
        """
        将平台原生事件转换为 OneBot12 标准格式

        :param raw_event: 平台原始事件数据
        :return: OneBot12 标准格式事件字典
        """
        if not isinstance(raw_event, dict):
            return None

        event_type = raw_event.get("type", "")

        base_event = {
            "id": str(raw_event.get("event_id", uuid.uuid4())),
            "time": raw_event.get("timestamp", int(time.time())),
            "platform": self.platform,
            "self": {
                "platform": self.platform,
                "user_id": str(raw_event.get("bot_id", "")),
            },
            f"{self.platform}_raw": raw_event,
            f"{self.platform}_raw_type": event_type,
        }

        if event_type == "message":
            base_event["type"] = "message"
            base_event["detail_type"] = (
                "group" if raw_event.get("group_id") else "private"
            )
            base_event["user_id"] = str(raw_event.get("sender_id", ""))
            base_event["message"] = [
                {"type": "text", "data": {"text": raw_event.get("content", "")}}
            ]
            base_event["alt_message"] = raw_event.get("content", "")
        elif event_type == "notification":
            base_event["type"] = "notice"
            base_event["detail_type"] = "notify"
        else:
            base_event["type"] = "unknown"
            base_event["detail_type"] = "unknown"

        return base_event
