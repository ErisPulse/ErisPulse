"""
框架主人管理系统

提供统一的用户主人身份识别能力，供命令系统（``master`` 参数）
及业务层（``master.is_master()``）使用。

主人配置位于 ``ErisPulse.master.users``，支持两种格式：
1. **dict**（按平台指定）：``{"yunhu": ["123"], "telegram": ["456"]}``
2. **list**（全局主人，所有平台生效）：``["123", "456"]``

{!--< tips >!--}
1. 通过 ``from ErisPulse.Core import master`` 导入单例
2. ``master.is_master(event)`` 或 ``master.is_master(platform, user_id)`` 检查身份
3. 支持运行时 ``master.add()`` / ``master.remove()`` 动态增删（不持久化到配置文件）
{!--< /tips >!--}
"""

from typing import Any

from ..runtime.frame_config import get_master_config, update_erispulse_config
from .i18n import i18n

# Event 对象的类型提示（避免循环导入）
_EventLike = Any  # 具有 get_platform() / get_user_id() 方法的对象


class MasterManager:
    """
    框架主人管理器（单例）

    从配置读取主人列表，并支持运行时增删。
    主人检查同时考虑配置中的主人和运行时添加的主人。
    """

    def __init__(self):
        # 运行时主人（不持久化）：{(platform, user_id)} 或 {(None, user_id)} 表示全局
        self._runtime_masters: set[tuple[str | None, str]] = set()

    def _load_config_masters(self) -> tuple[dict[str, set[str]], set[str]]:
        """
        从配置加载主人列表

        :return: (platform_masters, global_masters)
            - platform_masters: {platform: {user_id, ...}}
            - global_masters: {user_id, ...}
        """
        master_config = get_master_config()
        users = master_config.get("users", {})

        platform_masters: dict[str, set[str]] = {}
        global_masters: set[str] = set()

        if isinstance(users, dict):
            for platform, ids in users.items():
                if not isinstance(ids, list):
                    ids = [ids]
                platform_masters[str(platform)] = {str(i) for i in ids}
        elif isinstance(users, list):
            global_masters = {str(i) for i in users}

        return platform_masters, global_masters

    def is_master(
        self,
        platform_or_event: str | _EventLike,
        user_id: str | None = None,
    ) -> bool:
        """
        检查是否为框架主人

        支持两种调用方式：
        - ``master.is_master(event)`` — 从事件对象提取 platform 和 user_id
        - ``master.is_master(platform, user_id)`` — 显式指定

        检查范围：配置中的主人 + 运行时添加的主人。
        全局主人（配置为 list 或运行时添加为 None 平台）对所有平台生效。

        :param platform_or_event: 平台名称 或 事件对象
        :param user_id: 用户 ID（当第一个参数为平台名时使用）
        :return: 是否为框架主人

        :example:
        >>> from ErisPulse.Core import master
        >>>
        >>> # 从事件检查
        >>> if master.is_master(event):
        ...     await event.reply("主人你好")
        >>>
        >>> # 显式检查
        >>> if master.is_master("yunhu", "123456"):
        ...     print("是主人")
        """
        if user_id is None and not isinstance(platform_or_event, str):
            event = platform_or_event
            platform = event.get_platform() or ""
            user_id = event.get_user_id() or ""
        else:
            platform = str(platform_or_event or "")
            user_id = str(user_id or "")

        if not user_id:
            return False

        platform_masters, global_masters = self._load_config_masters()

        if user_id in global_masters:
            return True

        if platform and platform in platform_masters:
            if user_id in platform_masters[platform]:
                return True

        if (None, user_id) in self._runtime_masters:
            return True
        return bool(platform and (platform, user_id) in self._runtime_masters)

    def list(self) -> dict[str, list[str]]:
        """
        获取所有主人列表

        :return: 字典，``{"global": [...], "<platform>": [...]}``
            global 键包含对所有平台生效的主人
        """
        platform_masters, global_masters = self._load_config_masters()

        result: dict[str, list[str]] = {}

        all_global = set(global_masters)
        for (plat, uid) in self._runtime_masters:
            if plat is None:
                all_global.add(uid)
        if all_global:
            result["global"] = sorted(all_global)

        all_platforms = set(platform_masters.keys())
        for (plat, _) in self._runtime_masters:
            if plat is not None:
                all_platforms.add(plat)
        for plat in sorted(all_platforms):
            ids = set(platform_masters.get(plat, set()))
            for (p, uid) in self._runtime_masters:
                if p == plat:
                    ids.add(uid)
            if ids:
                result[plat] = sorted(ids)

        return result

    def add(self, platform: str | None, user_id: str, persist: bool = True) -> None:
        """
        添加主人

        :param platform: 平台名称，None 表示全局主人
        :param user_id: 用户 ID
        :param persist: 是否持久化到配置文件 (默认: True)
                        为 True 时写入 ``ErisPulse.master.users`` 配置，重启后仍然生效；
                        为 False 时仅运行时生效，重启后失效。

        :example:
        >>> from ErisPulse.Core import master
        >>> master.add("yunhu", "123456")       # 持久化到配置
        >>> master.add("yunhu", "999", persist=False)  # 仅本次运行有效
        >>> master.add(None, "888")             # 全局主人
        """
        uid = str(user_id)

        if not persist:
            self._runtime_masters.add((platform, uid))
            return

        # 持久化到配置文件
        current = get_master_config()
        users = current.get("users", {})

        if isinstance(users, dict):
            if platform is None:
                # 全局主人 → 转为混合格式: 保留现有 platform dict，添加 global key
                raise ValueError(
                    i18n.t("core.master.global_persist_not_supported")
                )
            platform_key = str(platform)
            ids = set(users.get(platform_key, []))
            ids.add(uid)
            users[platform_key] = sorted(ids)
        elif isinstance(users, list):
            ids = set(users)
            ids.add(uid)
            users = sorted(ids)
        else:
            users = [uid]

        update_erispulse_config({"master": {"users": users}})

    def remove(self, platform: str | None, user_id: str, persist: bool = True) -> bool:
        """
        移除主人

        :param platform: 平台名称，None 表示全局
        :param user_id: 用户 ID
        :param persist: 是否持久化移除 (默认: True)
                        为 True 时同时从配置文件中移除；
                        为 False 时仅移除运行时记录。
        :return: 是否成功移除（不存在则返回 False）

        :example:
        >>> from ErisPulse.Core import master
        >>> master.remove("yunhu", "123456")           # 持久化
        >>> master.remove("yunhu", "999", persist=False)  # 仅运行时
        """
        uid = str(user_id)
        key = (platform, uid)

        found = False
        if key in self._runtime_masters:
            self._runtime_masters.remove(key)
            found = True

        if persist:
            current = get_master_config()
            users = current.get("users", {})

            if isinstance(users, dict):
                if platform is not None:
                    platform_key = str(platform)
                    if platform_key in users:
                        ids = [i for i in users[platform_key] if str(i) != uid]
                        if ids:
                            users[platform_key] = ids
                        else:
                            del users[platform_key]
                        found = True
                        update_erispulse_config({"master": {"users": users}})
            elif isinstance(users, list):
                new_ids = [i for i in users if str(i) != uid]
                if len(new_ids) != len(users):
                    users = new_ids
                    found = True
                    update_erispulse_config({"master": {"users": users}})

        return found

    def reset(self) -> None:
        """
        清空所有运行时主人（用于测试或软重启）

        注意：不影响配置文件中的主人。
        """
        self._runtime_masters.clear()


# 模块级单例
master: MasterManager = MasterManager()

__all__ = [
    "MasterManager",
    "master",
]
