"""
管理员管理系统

提供统一的用户管理员身份识别能力，供命令系统（``must_admin`` 参数）
及业务层（``admin.is_admin()``）使用。

管理员配置位于 ``ErisPulse.admin.users``，支持两种格式：
1. **dict**（按平台指定）：``{"yunhu": ["123"], "telegram": ["456"]}``
2. **list**（全局管理员，所有平台生效）：``["123", "456"]``

{!--< tips >!--}
1. 通过 ``from ErisPulse.Core import admin`` 导入单例
2. ``admin.is_admin(event)`` 或 ``admin.is_admin(platform, user_id)`` 检查身份
3. 支持运行时 ``admin.add()`` / ``admin.remove()`` 动态增删（不持久化到配置文件）
{!--< /tips >!--}
"""

from typing import Any, Union

from ..runtime.frame_config import get_admin_config

# Event 对象的类型提示（避免循环导入）
_EventLike = Any  # 具有 get_platform() / get_user_id() 方法的对象


class AdminManager:
    """
    管理员管理器（单例）

    从配置读取管理员列表，并支持运行时增删。
    管理员检查同时考虑配置中的管理员和运行时添加的管理员。
    """

    def __init__(self):
        # 运行时管理员（不持久化）：{(platform, user_id)} 或 {(None, user_id)} 表示全局
        self._runtime_admins: set[tuple[str | None, str]] = set()

    def _load_config_admins(self) -> tuple[dict[str, set[str]], set[str]]:
        """
        从配置加载管理员列表

        :return: (platform_admins, global_admins)
            - platform_admins: {platform: {user_id, ...}}
            - global_admins: {user_id, ...}
        """
        admin_config = get_admin_config()
        users = admin_config.get("users", {})

        platform_admins: dict[str, set[str]] = {}
        global_admins: set[str] = set()

        if isinstance(users, dict):
            for platform, ids in users.items():
                if not isinstance(ids, list):
                    ids = [ids]
                platform_admins[str(platform)] = {str(i) for i in ids}
        elif isinstance(users, list):
            # list 格式 = 全局管理员
            global_admins = {str(i) for i in users}

        return platform_admins, global_admins

    def is_admin(
        self,
        platform_or_event: Union[str, _EventLike],
        user_id: str | None = None,
    ) -> bool:
        """
        检查是否为管理员

        支持两种调用方式：
        - ``admin.is_admin(event)`` — 从事件对象提取 platform 和 user_id
        - ``admin.is_admin(platform, user_id)`` — 显式指定

        检查范围：配置中的管理员 + 运行时添加的管理员。
        全局管理员（配置为 list 或运行时添加为 None 平台）对所有平台生效。

        :param platform_or_event: 平台名称 或 事件对象
        :param user_id: 用户 ID（当第一个参数为平台名时使用）
        :return: 是否为管理员

        :example:
        >>> from ErisPulse.Core import admin
        >>>
        >>> # 从事件检查
        >>> if admin.is_admin(event):
        ...     await event.reply("管理员你好")
        >>>
        >>> # 显式检查
        >>> if admin.is_admin("yunhu", "123456"):
        ...     print("是管理员")
        """
        # 从事件对象提取
        if user_id is None and hasattr(platform_or_event, "get_platform"):
            event = platform_or_event
            platform = event.get_platform() or ""
            user_id = event.get_user_id() or ""
        else:
            platform = str(platform_or_event or "")
            user_id = str(user_id or "")

        if not user_id:
            return False

        platform_admins, global_admins = self._load_config_admins()

        # 检查全局管理员（配置）
        if user_id in global_admins:
            return True

        # 检查平台指定管理员（配置）
        if platform and platform in platform_admins:
            if user_id in platform_admins[platform]:
                return True

        # 检查运行时管理员
        if (None, user_id) in self._runtime_admins:
            return True  # 运行时全局
        if platform and (platform, user_id) in self._runtime_admins:
            return True  # 运行时指定平台

        return False

    def list(self) -> dict[str, list[str]]:
        """
        获取所有管理员列表

        :return: 字典，``{"global": [...], "<platform>": [...]}`
            global 键包含对所有平台生效的管理员
        """
        platform_admins, global_admins = self._load_config_admins()

        result: dict[str, list[str]] = {}

        # 全局（配置 + 运行时）
        all_global = set(global_admins)
        for (plat, uid) in self._runtime_admins:
            if plat is None:
                all_global.add(uid)
        if all_global:
            result["global"] = sorted(all_global)

        # 按平台（配置 + 运行时）
        all_platforms = set(platform_admins.keys())
        for (plat, _) in self._runtime_admins:
            if plat is not None:
                all_platforms.add(plat)
        for plat in sorted(all_platforms):
            ids = set(platform_admins.get(plat, set()))
            for (p, uid) in self._runtime_admins:
                if p == plat:
                    ids.add(uid)
            if ids:
                result[plat] = sorted(ids)

        return result

    def add(self, platform: str | None, user_id: str) -> None:
        """
        运行时添加管理员（不持久化到配置文件，重启后失效）

        :param platform: 平台名称，None 表示全局管理员
        :param user_id: 用户 ID

        :example:
        >>> from ErisPulse.Core import admin
        >>> admin.add("yunhu", "123456")   # 指定平台
        >>> admin.add(None, "999")          # 全局
        """
        self._runtime_admins.add((platform, str(user_id)))

    def remove(self, platform: str | None, user_id: str) -> bool:
        """
        移除运行时添加的管理员

        注意：此方法仅移除运行时添加的管理员，不影响配置文件中的管理员。
        要移除配置中的管理员，请修改 ``ErisPulse.admin.users`` 配置。

        :param platform: 平台名称，None 表示全局
        :param user_id: 用户 ID
        :return: 是否成功移除（不存在则返回 False）
        """
        key = (platform, str(user_id))
        if key in self._runtime_admins:
            self._runtime_admins.remove(key)
            return True
        return False

    def reset(self) -> None:
        """
        清空所有运行时管理员（用于测试或软重启）

        注意：不影响配置文件中的管理员。
        """
        self._runtime_admins.clear()


# 模块级单例
admin = AdminManager()
