"""
OneBot12 事件转换器基类

适配器在"平台原生事件 → OneBot12 标准格式"之间转换时使用。
本基类提供 OneBot12 ``base_event`` 公共字段的构建与常用消息段辅助方法，
子类只需实现类型映射（``convert``）与平台特有字段填充。

{!--< tips >!--}
1. ``build_base_event`` 已填充 id/time/platform/self/{platform}_raw 等公共字段
2. 常用消息段（text / at / image）可直接复用静态方法
3. 子类必须实现 ``convert()``，无法识别的事件返回 ``None``
{!--< /tips >!--}
"""

import time
import uuid


class BaseConverter:
    """
    事件转换器基类

    :param platform: [str] 平台标识（如 "myplatform" / "onebot11"）
    """

    def __init__(self, platform: str):
        self.platform: str = platform

    def build_base_event(self, raw_event: dict, raw_type: str = "") -> dict:
        """
        构建 OneBot12 标准事件的公共字段（id / time / platform / self / raw）

        :param raw_event: 平台原始事件
        :param raw_type: 平台原始事件类型
        :return: 含公共字段的事件字典
        """
        return {
            "id": str(raw_event.get("event_id", uuid.uuid4())),
            "time": raw_event.get("timestamp", int(time.time())),
            "platform": self.platform,
            "self": {
                "platform": self.platform,
                "user_id": str(raw_event.get("bot_id", "")),
            },
            f"{self.platform}_raw": raw_event,
            f"{self.platform}_raw_type": raw_type,
        }

    # ==================== 常用消息段辅助 ====================

    @staticmethod
    def text(text: str) -> dict:
        """构造文本消息段"""
        return {"type": "text", "data": {"text": text}}

    @staticmethod
    def at(user_id: str) -> dict:
        """构造 @ 消息段"""
        return {"type": "at", "data": {"user_id": user_id}}

    @staticmethod
    def image(file: str) -> dict:
        """构造图片消息段"""
        return {"type": "image", "data": {"file": file}}

    # ==================== 子类必须实现 ====================

    def convert(self, raw_event: dict) -> dict | None:
        """
        将平台原生事件转换为 OneBot12 标准格式

        :param raw_event: 平台原始事件数据
        :return: OneBot12 标准格式事件字典；无法识别时返回 None
        """
        from ..i18n import i18n

        raise NotImplementedError(
            i18n.t("core.converter.must_implement_convert", name=self.__class__.__name__)
        )


__all__ = ["BaseConverter"]
