"""
ErisPulse 消息构建器

提供链式调用风格的 OneBot12 标准消息段构建工具

{!--< tips >!--}
1. 用于构建 OneBot12 标准消息段列表（list[dict]）
2. 配合 Raw_ob12 使用，是反向转换的搭档工具
3. 支持链式调用和快速构建两种模式
{!--< /tips >!--}
"""

import types
from typing import Any, Dict, List, Optional, Union


class _DualMethod:
    """
    双模式方法描述符

    通过类访问时返回静态工厂方法（返回 list），
    通过实例访问时返回链式实例方法（返回 self）。
    """

    def __init__(self, instance_fn, static_fn):
        self._instance_fn = instance_fn
        self._static_fn = static_fn

    def __get__(self, obj, objtype=None):
        if obj is None:
            # 类级别访问 → 返回静态工厂函数
            return self._static_fn
        # 实例级别访问 → 返回绑定方法
        return types.MethodType(self._instance_fn, obj)


class MessageBuilder:
    """
    OneBot12 消息段构建器

    提供链式调用风格构建标准消息段列表，配合 `Send.Raw_ob12()` 使用。

    {!--< tips >!--}
    使用方式：
    1. 链式调用：MessageBuilder().text("Hi").image("url").build()
    2. 快速构建：MessageBuilder.text("Hi")
    3. 配合发送：await send.To("group","123").Raw_ob12(MessageBuilder().text("Hi").build())
    {!--< /tips >!--}
    """

    def __init__(self):
        self._segments: List[Dict[str, Any]] = []

    # ==================== 链式调用方法（实例方法）====================

    def _text_inst(self, text: str) -> 'MessageBuilder':
        self._segments.append({
            "type": "text",
            "data": {"text": text}
        })
        return self

    def _image_inst(self, file: Union[str, bytes]) -> 'MessageBuilder':
        self._segments.append({
            "type": "image",
            "data": {"file": file}
        })
        return self

    def _audio_inst(self, file: Union[str, bytes]) -> 'MessageBuilder':
        self._segments.append({
            "type": "audio",
            "data": {"file": file}
        })
        return self

    def _video_inst(self, file: Union[str, bytes]) -> 'MessageBuilder':
        self._segments.append({
            "type": "video",
            "data": {"file": file}
        })
        return self

    def _file_inst(self, file: Union[str, bytes], filename: Optional[str] = None) -> 'MessageBuilder':
        data: Dict[str, Any] = {"file": file}
        if filename is not None:
            data["filename"] = filename
        self._segments.append({
            "type": "file",
            "data": data
        })
        return self

    def _mention_inst(self, user_id: str, user_name: Optional[str] = None) -> 'MessageBuilder':
        data: Dict[str, Any] = {"user_id": user_id}
        if user_name is not None:
            data["user_name"] = user_name
        self._segments.append({
            "type": "mention",
            "data": data
        })
        return self

    def _reply_inst(self, message_id: str) -> 'MessageBuilder':
        self._segments.append({
            "type": "reply",
            "data": {"message_id": message_id}
        })
        return self

    def _at_all_inst(self) -> 'MessageBuilder':
        self._segments.append({
            "type": "mention_all",
            "data": {}
        })
        return self

    def _custom_inst(self, segment_type: str, data: Dict[str, Any]) -> 'MessageBuilder':
        self._segments.append({
            "type": segment_type,
            "data": data
        })
        return self

    # ==================== 快速构建方法（静态函数）====================

    @staticmethod
    def _text_static(text: str) -> List[Dict[str, Any]]:
        return [{"type": "text", "data": {"text": text}}]

    @staticmethod
    def _image_static(file: Union[str, bytes]) -> List[Dict[str, Any]]:
        return [{"type": "image", "data": {"file": file}}]

    @staticmethod
    def _audio_static(file: Union[str, bytes]) -> List[Dict[str, Any]]:
        return [{"type": "audio", "data": {"file": file}}]

    @staticmethod
    def _video_static(file: Union[str, bytes]) -> List[Dict[str, Any]]:
        return [{"type": "video", "data": {"file": file}}]

    @staticmethod
    def _file_static(file: Union[str, bytes], filename: Optional[str] = None) -> List[Dict[str, Any]]:
        data: Dict[str, Any] = {"file": file}
        if filename is not None:
            data["filename"] = filename
        return [{"type": "file", "data": data}]

    @staticmethod
    def _mention_static(user_id: str, user_name: Optional[str] = None) -> List[Dict[str, Any]]:
        data: Dict[str, Any] = {"user_id": user_id}
        if user_name is not None:
            data["user_name"] = user_name
        return [{"type": "mention", "data": data}]

    @staticmethod
    def _reply_static(message_id: str) -> List[Dict[str, Any]]:
        return [{"type": "reply", "data": {"message_id": message_id}}]

    @staticmethod
    def _at_all_static() -> List[Dict[str, Any]]:
        return [{"type": "mention_all", "data": {}}]

    # ==================== 双模式方法绑定 ====================

    text = _DualMethod(_text_inst, _text_static)
    image = _DualMethod(_image_inst, _image_static)
    audio = _DualMethod(_audio_inst, _audio_static)
    video = _DualMethod(_video_inst, _video_static)
    file = _DualMethod(_file_inst, _file_static)
    mention = _DualMethod(_mention_inst, _mention_static)
    reply = _DualMethod(_reply_inst, _reply_static)
    at_all = _DualMethod(_at_all_inst, _at_all_static)

    # ==================== 别名和特殊方法 ====================

    def at(self, user_id: str, user_name: Optional[str] = None) -> 'MessageBuilder':
        """
        添加 @用户 消息段（mention 的别名）

        :param user_id: 用户 ID
        :param user_name: 用户名（可选）
        :return: MessageBuilder 实例

        :example:
        >>> MessageBuilder().at("123456").text("你好").build()
        """
        return self._mention_inst(user_id, user_name)

    @staticmethod
    def at(user_id: str, user_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        快速构建 @用户 消息段（mention 的别名）

        :param user_id: 用户 ID
        :param user_name: 用户名（可选）
        :return: 包含单个消息段的列表
        """
        return MessageBuilder._mention_static(user_id, user_name)

    # at 使用 _DualMethod 支持两种调用方式
    at = _DualMethod(_mention_inst, _mention_static)

    def custom(self, segment_type: str, data: Dict[str, Any]) -> 'MessageBuilder':
        """
        添加自定义消息段

        用于添加平台扩展消息段或其他非标准消息段

        :param segment_type: 消息段类型（如 "yunhu_form"）
        :param data: 消息段数据
        :return: MessageBuilder 实例

        :example:
        >>> MessageBuilder().custom("yunhu_form", {"form_id": "123"}).build()
        """
        return self._custom_inst(segment_type, data)

    # ==================== 构建方法 ====================

    def build(self) -> List[Dict[str, Any]]:
        """
        构建消息段列表

        :return: OneBot12 标准消息段列表

        :example:
        >>> segments = MessageBuilder().text("Hello").image("url").build()
        >>> # [{"type": "text", "data": {"text": "Hello"}}, {"type": "image", "data": {"file": "url"}}]
        """
        return list(self._segments)

    # ==================== 工具方法 ====================

    def copy(self) -> 'MessageBuilder':
        """
        复制当前构建器（深拷贝消息段列表）

        :return: 新的 MessageBuilder 实例

        :example:
        >>> base = MessageBuilder().text("基础内容")
        >>> msg1 = base.copy().image("img1").build()
        >>> msg2 = base.copy().image("img2").build()
        """
        new_builder = MessageBuilder()
        new_builder._segments = [dict(seg) for seg in self._segments]
        # 深拷贝嵌套的 data 字典
        for i, seg in enumerate(new_builder._segments):
            if isinstance(seg.get("data"), dict):
                new_builder._segments[i] = {"type": seg["type"], "data": dict(seg["data"])}
                # 深拷贝 data 内的嵌套字典
                for k, v in new_builder._segments[i]["data"].items():
                    if isinstance(v, dict):
                        new_builder._segments[i]["data"][k] = dict(v)
        return new_builder

    def clear(self) -> 'MessageBuilder':
        """
        清空已添加的消息段

        :return: MessageBuilder 实例自身

        :example:
        >>> builder = MessageBuilder().text("将被清除")
        >>> builder.clear().text("新内容").build()
        """
        self._segments.clear()
        return self

    def __len__(self) -> int:
        """返回已添加的消息段数量"""
        return len(self._segments)

    def __bool__(self) -> bool:
        """是否有消息段"""
        return bool(self._segments)

    def __repr__(self) -> str:
        return f"MessageBuilder(segments={len(self._segments)})"


__all__ = [
    "MessageBuilder",
]