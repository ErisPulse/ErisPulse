"""
ErisPulse 会话类型管理模块

提供会话类型的标准化定义、映射、转换和推断功能

{!--< tips >!--}
1. 定义了通用的会话类型和ID字段映射
2. 提供接收类型到发送类型的自动转换（如 private → user）
3. 支持根据ID字段自动推断会话类型
4. 允许适配器注册自定义类型映射
{!--< /tips >!--}
"""

from __future__ import annotations

from enum import Enum
from typing import TypeAlias

from .. import logger


# Python 3.11+ 提供了 enum.StrEnum，3.10 需手动实现
# 项目要求 >=3.10，这里统一用本地实现，避免 pyright 识别不了两种不同的 StrEnum
class StrEnum(str, Enum):
    """字符串枚举：成员值同时是 str，可直接用于字符串上下文。"""
    ...


ReceiveTypeStr: TypeAlias = str
SendTypeStr: TypeAlias = str
SessionTypeMap: TypeAlias = dict[str, str]
OptionalStr: TypeAlias = str | None

# ==================== 标准会话类型定义 ====================


class ReceiveType(StrEnum):
    PRIVATE = "private"
    GROUP = "group"
    CHANNEL = "channel"
    GUILD = "guild"
    THREAD = "thread"
    USER = "user"


class SendType(StrEnum):
    USER = "user"
    GROUP = "group"
    CHANNEL = "channel"
    GUILD = "guild"
    THREAD = "thread"


# 接收事件类型（OneBot12 标准 + ErisPulse 扩展）
RECEIVE_TYPES = {t.value for t in ReceiveType}

# 发送目标类型
SEND_TYPES = {t.value for t in SendType}

# ==================== 类型到ID字段的映射 ====================

# 接收类型 → ID 字段
RECEIVE_TYPE_TO_ID_FIELD: dict[str, str] = {
    ReceiveType.PRIVATE.value: "user_id",
    ReceiveType.GROUP.value: "group_id",
    ReceiveType.CHANNEL.value: "channel_id",
    ReceiveType.GUILD.value: "guild_id",
    ReceiveType.THREAD.value: "thread_id",
    ReceiveType.USER.value: "user_id",
}

# ID 字段 → 接收类型（用于自动推断）
ID_FIELD_TO_RECEIVE_TYPE: dict[str, str] = {
    "user_id": ReceiveType.PRIVATE.value,
    "group_id": ReceiveType.GROUP.value,
    "channel_id": ReceiveType.CHANNEL.value,
    "guild_id": ReceiveType.GUILD.value,
    "thread_id": ReceiveType.THREAD.value,
}

# ==================== 类型转换映射 ====================

# 接收类型 → 发送类型
RECEIVE_TO_SEND_TYPE: dict[str, str] = {
    ReceiveType.PRIVATE.value: SendType.USER.value,
    ReceiveType.GROUP.value: SendType.GROUP.value,
    ReceiveType.CHANNEL.value: SendType.CHANNEL.value,
    ReceiveType.GUILD.value: SendType.GUILD.value,
    ReceiveType.THREAD.value: SendType.THREAD.value,
    ReceiveType.USER.value: SendType.USER.value,
}

# 发送类型 → 接收类型
SEND_TO_RECEIVE_TYPE: dict[str, str] = {
    SendType.USER.value: ReceiveType.PRIVATE.value,
    SendType.GROUP.value: ReceiveType.GROUP.value,
    SendType.CHANNEL.value: ReceiveType.CHANNEL.value,
    SendType.GUILD.value: ReceiveType.GUILD.value,
    SendType.THREAD.value: ReceiveType.THREAD.value,
}

# ==================== 自定义类型扩展 ====================

# 自定义类型映射（由适配器注册）
_custom_type_to_id_field: dict[str, str] = {}
_custom_id_field_to_type: dict[str, str] = {}
_custom_receive_to_send: dict[str, str] = {}
_custom_send_to_receive: dict[str, str] = {}


def register_custom_type(
    receive_type: str, send_type: str, id_field: str, platform: str | None = None
) -> bool:
    """
    注册自定义会话类型

    :param receive_type: 接收事件类型（detail_type）
    :param send_type: 发送目标类型
    :param id_field: 对应的ID字段名
    :param platform: 平台名称（可选，用于区分同名不同平台的类型）
    :return: 是否注册成功
    """
    try:
        # 如果指定了平台，添加平台前缀
        if platform:
            receive_type_key = f"{platform}_{receive_type}"
        else:
            receive_type_key = receive_type

        # 注册映射
        _custom_type_to_id_field[receive_type_key] = id_field
        _custom_id_field_to_type[id_field] = receive_type_key
        _custom_receive_to_send[receive_type_key] = send_type
        _custom_send_to_receive[send_type] = receive_type_key

        logger.trace(
            f"已注册自定义会话类型: {receive_type_key} → {send_type} (ID字段: {id_field})"
        )
        return True
    except Exception as e:
        logger.error(f"注册自定义会话类型失败: {e}")
        return False


def unregister_custom_type(receive_type: str, platform: str | None = None) -> bool:
    """
    注销自定义会话类型

    :param receive_type: 接收事件类型
    :param platform: 平台名称
    :return: 是否注销成功
    """
    try:
        if platform:
            receive_type_key = f"{platform}_{receive_type}"
        else:
            receive_type_key = receive_type

        if receive_type_key in _custom_type_to_id_field:
            id_field = _custom_type_to_id_field[receive_type_key]
            send_type = _custom_receive_to_send[receive_type_key]

            del _custom_type_to_id_field[receive_type_key]
            del _custom_id_field_to_type[id_field]
            del _custom_receive_to_send[receive_type_key]
            del _custom_send_to_receive[send_type]

            logger.trace(f"已注销自定义会话类型: {receive_type_key}")
            return True
        return False
    except Exception as e:
        logger.error(f"注销自定义会话类型失败: {e}")
        return False


# ==================== 类型获取方法 ====================


def get_id_field(receive_type: str, platform: str | None = None) -> str:
    """
    根据接收类型获取对应的ID字段名

    :param receive_type: 接收事件类型
    :param platform: 平台名称（可选）
    :return: ID字段名
    """
    # 先检查自定义类型
    if platform:
        custom_key = f"{platform}_{receive_type}"
        if custom_key in _custom_type_to_id_field:
            return _custom_type_to_id_field[custom_key]

    if receive_type in _custom_type_to_id_field:
        return _custom_type_to_id_field[receive_type]

    # 使用标准映射
    return RECEIVE_TYPE_TO_ID_FIELD.get(receive_type, "user_id")


def get_receive_type(id_field: str, platform: str | None = None) -> str:
    """
    根据ID字段获取对应的接收类型

    :param id_field: ID字段名
    :param platform: 平台名称（可选）
    :return: 接收类型
    """
    # 先检查自定义类型
    if id_field in _custom_id_field_to_type:
        return _custom_id_field_to_type[id_field]

    # 使用标准映射
    return ID_FIELD_TO_RECEIVE_TYPE.get(id_field, "private")


def convert_to_send_type(receive_type: str | None, platform: str | None = None) -> str:
    """
    将接收类型转换为发送目标类型

    :param receive_type: 接收事件类型（``None`` 时返回默认值 ``"user"``）
    :param platform: 平台名称（可选）
    :return: 发送目标类型

    :example:
    >>> convert_to_send_type("private")  # 返回 "user"
    >>> convert_to_send_type("group")   # 返回 "group"
    >>> convert_to_send_type(None)       # 返回 "user"
    """
    # 先检查自定义类型
    if receive_type is None:
        return SendType.USER.value

    if platform:
        custom_key = f"{platform}_{receive_type}"
        if custom_key in _custom_receive_to_send:
            return _custom_receive_to_send[custom_key]

    if receive_type in _custom_receive_to_send:
        return _custom_receive_to_send[receive_type]

    # 使用标准映射
    return RECEIVE_TO_SEND_TYPE.get(receive_type, SendType.USER.value)


def convert_to_receive_type(send_type: str, platform: str | None = None) -> str:
    """
    将发送目标类型转换为接收类型

    :param send_type: 发送目标类型
    :param platform: 平台名称（可选）
    :return: 接收类型

    :example:
    >>> convert_to_receive_type("user")   # 返回 "private"
    >>> convert_to_receive_type("group")  # 返回 "group"
    """
    # 先检查自定义类型
    if send_type in _custom_send_to_receive:
        return _custom_send_to_receive[send_type]

    # 使用标准映射
    return SEND_TO_RECEIVE_TYPE.get(send_type, "private")


# ==================== 自动推断方法 ====================


def infer_receive_type(event: dict, platform: str | None = None) -> str:
    """
    根据事件数据自动推断接收类型

    检查顺序：
    1. 如果 ``detail_type`` 是已知的会话类型（标准或自定义），直接使用
    2. notice/request 事件的 ``detail_type`` 是语义子类型（如 ``group_member_increase``），
       不是会话类型，此时根据 ID 字段推断
    3. 最后根据存在的 ID 字段，按优先级返回

    :param event: 事件数据字典
    :param platform: 平台名称（可选）
    :return: 推断的接收类型

    :example:
    >>> # 消息事件：detail_type 就是会话类型
    >>> event = {"type": "message", "detail_type": "group", "group_id": "123"}
    >>> infer_receive_type(event)  # 返回 "group"
    >>>
    >>> # 通知事件：detail_type 是语义子类型，从 ID 字段推断
    >>> event = {"type": "notice", "detail_type": "group_member_increase", "group_id": "123"}
    >>> infer_receive_type(event)  # 返回 "group"（而非 "group_member_increase"）
    >>>
    >>> event = {"type": "notice", "detail_type": "friend_increase", "user_id": "456"}
    >>> infer_receive_type(event)  # 返回 "private"
    """
    detail_type = event.get("detail_type")

    if detail_type:
        # 只有当 detail_type 是已知会话类型（标准或自定义）时才直接返回。
        # notice/request 事件的 detail_type（如 group_member_increase / friend）
        # 是语义子类型，不是会话类型，需从 ID 字段推断正确的会话类型。
        if detail_type in RECEIVE_TYPES:
            return detail_type

        # 检查自定义会话类型
        if platform:
            custom_key = f"{platform}_{detail_type}"
            if custom_key in _custom_type_to_id_field:
                return detail_type
        if detail_type in _custom_type_to_id_field:
            return detail_type

    # 从 ID 字段推断会话类型
    # 优先级：group > channel > guild > thread > user
    if event.get("group_id"):
        return "group"
    if event.get("channel_id"):
        return "channel"
    if event.get("guild_id"):
        return "guild"
    if event.get("thread_id"):
        return "thread"
    if event.get("user_id"):
        return "private"

    # 都没有，默认返回 private
    logger.warning("无法从事件数据推断会话类型，使用默认值 'private'")
    return "private"


def get_target_id(event: dict, platform: str | None = None) -> str:
    """
    获取事件的目标ID（根据推断的会话类型）

    :param event: 事件数据字典
    :param platform: 平台名称（可选）
    :return: 目标ID

    :example:
    >>> event = {"detail_type": "group", "group_id": "123"}
    >>> get_target_id(event)  # 返回 "123"
    """
    receive_type = infer_receive_type(event, platform)
    id_field = get_id_field(receive_type, platform)
    return event.get(id_field, "")


def get_send_type_and_target_id(
    event: dict, platform: str | None = None
) -> tuple[str, str]:
    """
    获取发送类型和目标ID（一步完成类型转换和ID获取）

    :param event: 事件数据字典
    :param platform: 平台名称（可选）
    :return: (发送类型, 目标ID)

    :example:
    >>> event = {"detail_type": "private", "user_id": "123"}
    >>> get_send_type_and_target_id(event)  # 返回 ("user", "123")
    """
    receive_type = infer_receive_type(event, platform)
    send_type = convert_to_send_type(receive_type, platform)
    target_id = event.get(get_id_field(receive_type, platform), "")
    return send_type, target_id


# ==================== 工具方法 ====================


def is_standard_type(receive_type: str) -> bool:
    """
    检查是否为标准接收类型

    :param receive_type: 接收事件类型
    :return: 是否为标准类型
    """
    return receive_type in RECEIVE_TYPES


def is_valid_send_type(send_type: str) -> bool:
    """
    检查是否为有效的发送类型

    :param send_type: 发送目标类型
    :return: 是否为有效类型
    """
    return send_type in SEND_TYPES


def get_standard_types() -> set[str]:
    """
    获取所有标准接收类型

    :return: 标准类型集合
    """
    return RECEIVE_TYPES.copy()


def get_send_types() -> set[str]:
    """
    获取所有发送类型

    :return: 发送类型集合
    """
    return SEND_TYPES.copy()


def clear_custom_types(platform: str | None = None) -> int:
    """
    清除自定义类型映射

    :param platform: 平台名称（可选，如果指定则只清除该平台的类型）
    :return: 清除的类型数量
    """
    global _custom_type_to_id_field, _custom_id_field_to_type
    global _custom_receive_to_send, _custom_send_to_receive

    if platform:
        # 只清除指定平台的类型
        to_remove = [
            k for k in _custom_type_to_id_field if k.startswith(f"{platform}_")
        ]
        count = len(to_remove)
        for key in to_remove:
            id_field = _custom_type_to_id_field[key]
            send_type = _custom_receive_to_send[key]
            del _custom_type_to_id_field[key]
            _custom_id_field_to_type.pop(id_field, None)
            del _custom_receive_to_send[key]
            _custom_send_to_receive.pop(send_type, None)
        return count
    # 清除所有自定义类型
    count = len(_custom_type_to_id_field)
    _custom_type_to_id_field.clear()
    _custom_id_field_to_type.clear()
    _custom_receive_to_send.clear()
    _custom_send_to_receive.clear()
    return count


__all__ = [
    # 标准类型常量
    "RECEIVE_TYPES",
    "SEND_TYPES",
    "ReceiveType",
    "SendType",
    "clear_custom_types",
    "convert_to_receive_type",
    "convert_to_send_type",
    # 类型获取方法
    "get_id_field",
    "get_receive_type",
    "get_send_type_and_target_id",
    "get_send_types",
    "get_standard_types",
    "get_target_id",
    # 自动推断方法
    "infer_receive_type",
    # 工具方法
    "is_standard_type",
    "is_valid_send_type",
    # 自定义类型注册
    "register_custom_type",
    "unregister_custom_type",
]
