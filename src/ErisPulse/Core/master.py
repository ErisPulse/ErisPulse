"""
框架主人管理系统

提供统一的用户主人身份识别能力，供命令系统（``master`` 参数）
及业务层（``master.is_master()``）使用。

主人配置位于 ``ErisPulse.master.users``，支持两种格式：
1. **dict**（按平台指定）：``{"yunhu": ["123"], "telegram": ["456"]}``
2. **list**（全局主人，所有平台生效）：``["123", "456"]``

除内置身份源（配置 + 运行时增删）外，还支持通过
``master.provider`` 注册自定义身份源，实现可插拔的身份判定
（如对接适配器管理员接口、数据库角色等）。

{!--< tips >!--}
1. 通过 ``from ErisPulse.Core import master`` 导入单例
2. ``master.is_master(event)`` 或 ``master.is_master(platform, user_id)`` 检查身份
3. 支持运行时 ``master.add()`` / ``master.remove()`` 动态增删（不持久化到配置文件）
4. ``@master.provider`` 注册自定义身份源，任一 provider 放行即认定为主人；
   注销用 ``fn.unregister()``
{!--< /tips >!--}
"""

from collections.abc import Callable
from typing import Any

from ..runtime.frame_config import get_master_config, update_erispulse_config
from .i18n import i18n
from .logger import logger

# Event 对象的类型提示（避免循环导入）
_EventLike = Any  # 具有 get_platform() / get_user_id() 方法的对象

# 自定义身份源 provider 签名：(platform, user_id) -> bool
MasterProvider = Callable[[str, str], bool]


class MasterManager:
    """
    框架主人管理器（单例）

    从配置读取主人列表，并支持运行时增删。
    主人检查同时考虑配置中的主人、运行时添加的主人，
    以及通过 :meth:`provider` 注册的自定义身份源（provider 链）。

    {!--< tips >!--}
    1. 默认身份源：``ErisPulse.master.users`` 配置 + 运行时 ``add()`` 记录
    2. ``@master.provider`` 可注册自定义身份源，
       ``fn(platform, user_id) -> bool``，任一 provider 放行即认定为主人
    3. provider 异常会被捕获并跳过（不阻断身份判定链）
    {!--< /tips >!--}
    """

    def __init__(self):
        # 运行时主人（不持久化）：{(platform, user_id)} 或 {(None, user_id)} 表示全局
        self._runtime_masters: set[tuple[str | None, str]] = set()
        # 自定义身份源 provider 链（注册顺序依次尝试）
        self._providers: list[MasterProvider] = []
        # provider 归属：id(fn) -> owner 名（支持按 owner 自动清理，如模块卸载）
        self._provider_owners: dict[int, str] = {}

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

        检查范围：配置中的主人 + 运行时添加的主人 + 已注册的 provider 链。
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
        if platform and (platform, user_id) in self._runtime_masters:
            return True

        return self._check_providers(platform, user_id)

    def _check_providers(self, platform: str, user_id: str) -> bool:
        """
        {!--< internal-use >!--}
        依次尝试 provider 链，任一放行即认定为主人

        provider 异常被捕获并跳过（记录 warning），不阻断后续判定。

        :param platform: 平台名称
        :param user_id: 用户 ID
        :return: 是否有 provider 认定该用户为主人
        """
        for fn in self._providers:
            try:
                if fn(platform, user_id):
                    return True
            except Exception as e:
                logger.warning(i18n.t("core.master.provider_error", error=e))
        return False

    def provider(self, fn: MasterProvider) -> MasterProvider:
        """
        注册自定义身份源 provider（装饰器 / 函数调用两用）

        签名：``fn(platform: str, user_id: str) -> bool``，返回 True 表示
        认定该用户为主人。所有 provider 在内置身份源（配置 + 运行时记录）
        未命中时依次尝试，任一放行即认定为主人。

        注册后原函数会挂上 ``fn.unregister()``，调用即可撤销该 provider。

        provider 归属自动记录：若在模块 owner 上下文（如模块 ``on_load``）
        内注册，模块卸载时会被框架自动注销（无需手动 ``unregister``）；
        模块级装饰器用法（非加载上下文）为常驻身份源，仅显式注销。

        :param fn: 身份源检查函数（普通函数 / 模块级函数皆可挂 ``unregister``；
                   绑定实例方法请用模块级函数或在注册后自行保存注销句柄）
        :return: 原函数（已注册，并尽可能挂载 ``unregister`` 方法）

        :example:
        >>> from ErisPulse.Core import master
        >>>
        >>> # 装饰器用法（常驻身份源，推荐）
        >>> @master.provider
        ... def admin_provider(platform, user_id):
        ...     return user_id in {"999"}  # 自定义判定逻辑
        >>>
        >>> master.is_master("yunhu", "999")  # True
        >>> admin_provider.unregister()  # 不再需要时注销

        >>> # 函数式用法（模块加载期注册、卸载期注销）
        >>> fn = master.provider(admin_provider)
        >>> fn.unregister()
        """
        if fn not in self._providers:
            self._providers.append(fn)

        from ..runtime.context import current_owner

        owner = current_owner.get()
        if owner:
            self._provider_owners[id(fn)] = owner

        try:
            fn.unregister = lambda: self._drop_provider(fn)  # type: ignore[attr-defined]
        except (AttributeError, TypeError):
            # 绑定方法等无 __dict__ 的可调用对象无法挂载注销函数，
            # 注册仍生效；请改用模块级函数，或自行记录注销入口
            logger.debug(f"provider {fn!r} cannot carry unregister(); use a module-level function")
        return fn

    def _drop_provider(self, fn: MasterProvider) -> None:
        """
        {!--< internal-use >!--}
        从 provider 链移除指定函数（幂等）

        :param fn: 已注册的 provider 函数
        """
        try:
            self._providers.remove(fn)
        except ValueError:
            return
        self._provider_owners.pop(id(fn), None)

    def unregister_by_owner(self, owner: str) -> int:
        """
        注销指定 owner（模块）注册的全部 provider

        模块在加载上下文（on_load）内注册的 provider 会由框架在卸载时
        自动调用本方法，实现作用域清理——模块开发者无需在 on_unload 手动注销。

        :param owner: 模块名（owner）
        :return: 注销的 provider 数量
        """
        if not owner:
            return 0
        removed = 0
        for fn in list(self._providers):
            if self._provider_owners.get(id(fn)) == owner:
                self._drop_provider(fn)
                removed += 1
        return removed

    def list(self) -> dict[str, list[str]]:
        """
        获取所有主人列表

        :return: 字典，``{"global": [...], "<platform>": [...]}``
            global 键包含对所有平台生效的主人
        """
        platform_masters, global_masters = self._load_config_masters()

        result: dict[str, list[str]] = {}

        all_global = set(global_masters)
        for plat, uid in self._runtime_masters:
            if plat is None:
                all_global.add(uid)
        if all_global:
            result["global"] = sorted(all_global)

        all_platforms = set(platform_masters.keys())
        for plat, _ in self._runtime_masters:
            if plat is not None:
                all_platforms.add(plat)
        for plat in sorted(all_platforms):
            ids = set(platform_masters.get(plat, set()))
            for p, uid in self._runtime_masters:
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
        >>> master.add("yunhu", "123456")  # 持久化到配置
        >>> master.add("yunhu", "999", persist=False)  # 仅本次运行有效
        >>> master.add(None, "888")  # 全局主人
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
                raise ValueError(i18n.t("core.master.global_persist_not_supported"))
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
        >>> master.remove("yunhu", "123456")  # 持久化
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
        清空所有运行时主人与已注册的 provider（用于测试或软重启）

        注意：不影响配置文件中的主人。
        软重启时模块会被重新加载，provider 持有的旧引用一并清空，
        由模块在新生命周期中重新注册。
        """
        self._runtime_masters.clear()
        self._providers.clear()
        self._provider_owners.clear()


# 模块级单例
master: MasterManager = MasterManager()

__all__ = [
    "MasterManager",
    "MasterProvider",
    "master",
]
