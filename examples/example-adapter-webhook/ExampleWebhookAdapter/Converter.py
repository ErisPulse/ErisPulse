"""
ExampleWebhook 转换器

负责在平台特定事件格式和 ErisPulse 标准格式（OneBot12）之间进行转换。
继承 `BaseConverter` 以复用公共字段构造（`build_base_event`）与消息段助手
（`text` / `at` / `image`），与 CLI 脚手架模板（`epsdk create adapter --template webhook`）保持同一写法。
"""

from ErisPulse.Core.Bases import BaseConverter


class ExampleWebhookConverter(BaseConverter):
    """
    ExampleWebhook 转换器类

    将平台回调载荷转换为 OneBot12 标准格式；平台特有字段按扩展命名规范
    放入 `{platform}_raw` / `{platform}_raw_type`（由 `build_base_event` 统一处理）。
    """

    def __init__(self):
        super().__init__(platform="example_webhook")

    def convert(self, payload: dict) -> dict | None:
        """
        将平台回调载荷转换为 OneBot12 标准格式

        :param payload: 回调请求的 JSON 载荷
        :return: OneBot12 标准格式事件字典；无法识别时返回 None
        """
        if not isinstance(payload, dict):
            return None

        event_type = payload.get("type", "")
        base = self.build_base_event(payload, event_type)

        if event_type == "message":
            base["type"] = "message"
            base["detail_type"] = (
                "group" if payload.get("group_id") else "private"
            )
            base["user_id"] = str(payload.get("sender_id", ""))
            base["message"] = [self.text(payload.get("content", ""))]
            base["alt_message"] = payload.get("content", "")
            return base

        if event_type == "notification":
            base["type"] = "notice"
            base["detail_type"] = "notify"
            return base

        return None
