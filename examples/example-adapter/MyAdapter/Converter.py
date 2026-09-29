"""
MyAdapter 转换器

负责在平台特定事件格式和 ErisPulse 标准格式（OneBot12）之间进行转换。
继承 `BaseConverter` 以复用公共字段构造（`build_base_event`）与消息段助手
（`text` / `at` / `image`），与 CLI 脚手架模板（`epsdk create adapter`）保持同一写法。
"""

from ErisPulse.Core.Bases import BaseConverter


class MyAdapterConverter(BaseConverter):
    """
    MyAdapter 转换器类

    将平台原生事件转换为 OneBot12 标准格式；平台特有字段按扩展命名规范
    放入 `{platform}_raw` / `{platform}_raw_type`（由 `build_base_event` 统一处理）。
    """

    def __init__(self):
        super().__init__(platform="myplatform")

    def convert(self, raw_event: dict) -> dict | None:
        """
        将平台原生事件转换为 OneBot12 标准格式

        :param raw_event: 平台原始事件数据
        :return: OneBot12 标准格式事件字典；无法识别时返回 None
        """
        if not isinstance(raw_event, dict):
            return None

        event_type = raw_event.get("type", "")
        base = self.build_base_event(raw_event, event_type)

        if event_type == "message":
            base["type"] = "message"
            base["detail_type"] = (
                "group" if raw_event.get("group_id") else "private"
            )
            base["user_id"] = str(raw_event.get("sender_id", ""))
            base["message"] = [self.text(raw_event.get("content", ""))]
            base["alt_message"] = raw_event.get("content", "")
            return base

        if event_type == "notification":
            base["type"] = "notice"
            base["detail_type"] = "notify"
            return base

        return None
