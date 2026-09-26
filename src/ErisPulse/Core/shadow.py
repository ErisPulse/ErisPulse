"""
ErisPulse 影子模块（方向十一：Shadow Modules & Canary Promote）

影子 = 同一模块的新版本，以**独立 owner**（如 ``roll_shadow``）与线上
旧版并存试运行：它收到真实事件的**副本**、其出站被**拦截记账**而非真正
发出——确认无害后 ``promote`` 一键转正，``dismiss`` 随时放弃。模块代码
零改动，全程 **API 驱动**（运行时操作，与 load / unload / reload 同类；
Dashboard / 自定义管理模块调用这些 API，无需用户手写任何配置）。

- 机制与诚实边界：docs/zh-CN/advanced/shadow.md

{!--< tips >!--}
1. ``sdk.module.shadow_start("roll", source="路径/到/v2")`` 启动影子：
   source 为新版代码的目录或单文件路径（建议放在 plugins 目录之外，
   避免被普通发现机制装载）；影子 owner 名默认取路径名
2. 出站拦截覆盖 Send DSL 与 Api DSL；绕过框架的裸 call_api / aiohttp /
   线程拦不住；ORM 读写不进存储覆盖层
3. 转正永远由人确认：``await sdk.module.promote_shadow("roll")``，失败
   自动回滚旧实例继续服务；``dismiss_shadow`` 随时放弃
{!--< /tips >!--}
"""

from collections import deque
import sys
from pathlib import Path
from typing import Any

from .logger import logger

__all__ = [
    "ShadowLedger",
    "ShadowManager",
    "ShadowOverlay",
    "shadow_ledger",
    "shadow_manager",
]

# 影子账本每个 owner 的最大保留条数（内存环形，超出丢弃最旧）
# 使用位置: ShadowLedger.record；修改影响: diff 对比的数据窗口大小
SHADOW_LEDGER_MAX_PER_OWNER = 500


class ShadowLedger:
    """
    影子账本：影子 owner 的意向出站记录（内存环形，按 owner 分桶）

    记录来源：出站闸（``Send`` DSL / ``Api`` DSL）在 owner 属影子时写入。
    每条含 kind（send/api）/ platform / method / target / trace_id / preview。
    """

    def __init__(self) -> None:
        self._entries: "dict[str, deque[dict[str, Any]]]" = {}

    def record(self, owner: str, entry: "dict[str, Any]") -> None:
        """
        记录一条影子意向出站

        :param owner: 影子 owner 名
        :param entry: 出站条目（kind/platform/method/target/trace_id/preview 等）
        """
        bucket = self._entries.setdefault(owner, deque(maxlen=SHADOW_LEDGER_MAX_PER_OWNER))
        bucket.append(entry)

    def entries(self, owner: str) -> "list[dict[str, Any]]":
        """
        读取影子 owner 的全部在账条目（时间序）

        :param owner: 影子 owner 名
        :return: 条目列表（无在账条目时为空列表）
        """
        return list(self._entries.get(owner, ()))

    def clear(self, owner: str) -> None:
        """
        清空影子 owner 的账本

        :param owner: 影子 owner 名
        """
        self._entries.pop(owner, None)


class ShadowOverlay:
    """
    存储内存覆盖层：影子 owner 的 KV 写隔离

    语义：写进覆盖层（不落库）、删为墓碑、读先查覆盖层——命中返回影子值，
    命中墓碑视为"已删除"（回退默认值），未命中透传真库。ORM 读写不在
    覆盖层语义内（文档声明）。
    """

    def __init__(self) -> None:
        self._data: "dict[str, Any]" = {}
        self._tombstones: "set[str]" = set()

    def write(self, key: str, value: Any) -> None:
        """写入覆盖层"""
        self._data[key] = value
        self._tombstones.discard(key)

    def delete(self, key: str) -> None:
        """写入墓碑（影子视角的删除）"""
        self._data.pop(key, None)
        self._tombstones.add(key)

    def read(self, key: str) -> "tuple[str, Any]":
        """
        查询覆盖层

        :param key: 存储键（含嵌套路径原样匹配）
        :return: (状态, 值)；状态 "hit"（影子值）/ "tombstone"（影子已删除，
                 不应透传真库）/ "miss"（未命中，透传真库）
        """
        if key in self._tombstones:
            return "tombstone", None
        if key in self._data:
            return "hit", self._data[key]
        return "miss", None


class ShadowManager:
    """
    影子模块管理器（单例）

    维护 原模块名 → 影子实例 的绑定、影子账本与存储覆盖层，并提供
    start（启动影子）/ promote（转正）/ dismiss（放弃）/ diff（对比）。
    子系统八道闸只依赖 ``ownership.is_shadow`` 与 :data:`shadow_ledger` /
    :func:`shadow_overlay`，不反向依赖本管理器。
    """

    def __init__(self) -> None:
        # 原模块名 → 影子绑定信息
        self._shadows: "dict[str, dict[str, str]]" = {}
        # 影子 owner → 覆盖层
        self._overlays: "dict[str, ShadowOverlay]" = {}

    # ---- 绑定查询 ----

    def shadow_owner_of(self, real_name: str) -> "str | None":
        """
        查询原模块当前绑定的影子 owner 名

        :param real_name: 原模块名
        :return: 影子 owner 名（未绑定为 None）
        """
        info = self._shadows.get(real_name)
        return info.get("shadow_owner") if info else None

    def real_name_of(self, shadow_owner: str) -> "str | None":
        """
        查询影子 owner 对应的原模块名

        :param shadow_owner: 影子 owner 名
        :return: 原模块名（非影子为 None）
        """
        for real, info in self._shadows.items():
            if info.get("shadow_owner") == shadow_owner:
                return real
        return None

    def bind(self, real_name: str, shadow_owner: str) -> None:
        """
        登记 绑定关系（影子启动成功后调用；同时向归属权登记影子状态）

        :param real_name: 原模块名
        :param shadow_owner: 影子 owner 名
        """
        self._shadows[real_name] = {"shadow_owner": shadow_owner}
        from .ownership import ownership

        ownership.register_shadow(shadow_owner)

    def unbind(self, shadow_owner: str) -> "str | None":
        """
        解除影子绑定（dismiss / 转正后调用；同步移除归属权影子状态）

        :param shadow_owner: 影子 owner 名
        :return: 对应原模块名（未绑定为 None）
        """
        from .ownership import ownership

        ownership.unregister_shadow(shadow_owner)
        real = self.real_name_of(shadow_owner)
        if real is not None:
            self._shadows.pop(real, None)
        self._overlays.pop(shadow_owner, None)
        shadow_ledger.clear(shadow_owner)
        return real

    # ---- 覆盖层 ----

    def overlay(self, shadow_owner: str) -> ShadowOverlay:
        """
        获取影子 owner 的存储覆盖层（惰性创建）

        :param shadow_owner: 影子 owner 名
        :return: 覆盖层实例
        """
        overlay = self._overlays.get(shadow_owner)
        if overlay is None:
            overlay = ShadowOverlay()
            self._overlays[shadow_owner] = overlay
        return overlay

    # ---- 启动 ----

    async def start(
        self,
        real_name: str,
        source: "str | Path",
        manager: Any,
        sdk: Any,
        owner: "str | None" = None,
        loader: "Any | None" = None,
    ) -> str:
        """
        启动影子：把新版代码以独立 owner 装载为 ``real_name`` 的影子实例

        source 为新版代码的**目录或单 .py 文件路径**（推荐放在 plugins 目录
        之外，避免被普通发现机制当作独立模块装载）。影子以独立 owner 运行：
        收到真实事件副本、出站被拦截记账、配置继承原模块配置节。

        :param real_name: 被 shadow 的已加载模块名
        :param source: 新版代码路径（目录含 ``__init__.py`` 或单 ``.py`` 文件）
        :param manager: 模块管理器实例
        :param sdk: SDK 实例
        :param owner: 影子 owner 名（默认取路径名，非法时回退
                      ``f"{real_name}_shadow"``）
        :param loader: 模块加载器实例（None 时自动取 ``sdk._module_loader``）
        :return: 影子 owner 名
        :raises RuntimeError: 原模块未加载 / 影子已存在 / 源路径无效 /
                              影子装载失败

        :example:
        >>> await sdk.module.shadow_start("roll", source="downloads/roll_v2")
        'roll_shadow'
        """
        if real_name not in getattr(manager, "_loaded_modules", set()):
            raise RuntimeError(f"module '{real_name}' is not loaded; cannot shadow it")
        if self.shadow_owner_of(real_name):
            raise RuntimeError(f"module '{real_name}' already has an active shadow")

        src = Path(source)
        if not src.exists():
            raise RuntimeError(f"shadow source path not found: {src}")

        owner = owner or src.stem.strip() or f"{real_name}_shadow"
        owner = "".join(ch if (ch.isalnum() or ch == "_") else "_" for ch in owner)
        if not owner or not owner[0].isalpha():
            owner = f"{real_name}_shadow"

        # 从源路径导入新版代码（复用插件加载器的导入与类识别机制；
        # 建议源放在 plugins 目录之外——plugins 内的同名/同代码文件会被
        # 普通发现机制当作独立模块装载）
        if loader is None:
            loader = getattr(sdk, "_module_loader", None)
        plugin_loader = getattr(loader, "_plugin_loader", None) if loader else None
        if plugin_loader is None:
            raise RuntimeError("plugin loader unavailable; cannot import shadow source")

        module_obj = plugin_loader._load_plugin(owner, src)
        if module_obj is None:
            raise RuntimeError(f"shadow source '{src}' contains no loadable module class")
        v_info = module_obj.moduleInfo
        v_class = v_info["module_class"]

        try:
            manager.register(owner, v_class, v_info)
            if not await manager.load(owner):
                raise RuntimeError("shadow load returned False")
        except Exception:
            try:
                manager.unregister(owner)
            except Exception:
                pass
            raise

        instance = manager.get(owner)
        try:
            instance._shadow_source = real_name  # 配置继承（cfg 回退）依据
        except Exception:
            pass
        if owner[:1].isalpha() and owner.isidentifier():
            setattr(sdk, owner, instance)

        # 影子源若恰好位于 plugins 目录，禁用其启用状态，
        # 防止下次启动被普通发现机制当作独立模块装载
        try:
            from .config import config as config_service

            config_service.setConfig(f"ErisPulse.modules.status.{owner}", False)
        except Exception:
            pass

        self.bind(real_name, owner)
        logger.info(f"shadow module '{owner}' started (shadowing '{real_name}')")
        return owner

    # ---- 转正 / 放弃 / 对比 ----

    async def promote(
        self, real_name: str, manager: Any, sdk: Any, loader: "Any | None" = None
    ) -> bool:
        """
        转正：卸载当前版本 → 影子以真名注册加载 → 失败自动回滚继续服务

        复用方向 10 的重载快照机制（当前版本与级联依赖者先行快照）。
        转正后建议尽快把新版本持久化安装（pip 升级 / 替换插件文件），
        使重启后仍然生效——运行时切换不会替你完成包管理。

        :param real_name: 原模块名
        :param manager: 模块管理器实例
        :param sdk: SDK 实例
        :param loader: 模块加载器实例（None 时自动取 ``sdk._module_loader``）
        :return: 是否转正成功
        """
        info = self._shadows.get(real_name)
        if not info:
            raise ValueError(f"no shadow bound for module '{real_name}'")
        shadow_owner = info["shadow_owner"]
        if real_name not in getattr(manager, "_loaded_modules", set()):
            raise RuntimeError(f"module '{real_name}' is not loaded; nothing to promote onto")

        v2_class = (getattr(manager, "_module_classes", {}) or {}).get(shadow_owner)
        if v2_class is None:
            raise RuntimeError(f"shadow '{shadow_owner}' is not registered")
        loaded = getattr(manager, "_loaded_modules", set())
        if shadow_owner not in loaded:
            raise RuntimeError(f"shadow '{shadow_owner}' is not loaded")

        if loader is None:
            loader = getattr(sdk, "_module_loader", None)
        if loader is None or not hasattr(loader, "_capture_reload_state"):
            raise RuntimeError("module loader does not support snapshot; cannot promote safely")

        # 快照当前版本与级联依赖者（purge_names=[]：promote 不清 sys.modules，
        # 内存释放推迟到回滚窗口之外）
        v1_snapshot = loader._capture_reload_state(real_name, manager, sdk, [])
        dep_names = manager._collect_dependents(real_name)
        dep_snapshots = {
            dep: loader._capture_reload_state(
                dep, manager, sdk, loader._dependent_purge_names(dep, manager)
            )
            for dep in dep_names
        }

        await manager.unload(real_name)

        v2_info = dict((getattr(manager, "_module_info", {}) or {}).get(shadow_owner) or {})
        v2_meta = dict(v2_info.get("meta") or {})
        v2_meta["name"] = real_name
        v2_meta["source"] = "shadow_promoted"
        v2_info["meta"] = v2_meta

        try:
            manager.register(real_name, v2_class, v2_info)
            if not await manager.load(real_name):
                raise RuntimeError("load returned False")
            setattr(sdk, real_name, manager.get(real_name))
            module_obj = sys.modules.get(v2_class.__module__)
            if module_obj is not None:
                loader._last_module_objs[real_name] = module_obj
        except Exception as e:
            logger.error(f"promote of '{real_name}' failed — rolling back current version: {e}")
            loader._restore_reload_snapshot(v1_snapshot, real_name, manager, sdk)
            loader._restore_failed_dependents(dep_snapshots, manager, sdk)
            return False

        # 转正成功：回收影子资源（旧事件处理器/账本随之失效）并解除绑定
        try:
            from .ownership import ownership as ownership_service

            await ownership_service.reclaim(shadow_owner)
        except Exception:
            pass
        try:
            manager.unregister(shadow_owner)
        except Exception:
            pass
        self.unbind(shadow_owner)
        logger.info(f"module '{real_name}' promoted from shadow '{shadow_owner}'")
        return True

    async def dismiss(self, real_name: str, manager: Any) -> bool:
        """
        放弃影子：回收影子资源、解除绑定、清空账本与命令目录

        :param real_name: 原模块名
        :param manager: 模块管理器实例
        :return: 是否成功
        """
        info = self._shadows.get(real_name)
        if not info:
            return False
        shadow_owner = info["shadow_owner"]
        from .ownership import ownership as ownership_service

        await ownership_service.reclaim(shadow_owner)
        try:
            manager.unregister(shadow_owner)
        except Exception:
            pass
        self.unbind(shadow_owner)
        try:
            from .Event import command as command_service

            for key in [
                k
                for k, v in command_service._shadow_catalog.items()
                if v.get("owner") == shadow_owner
            ]:
                command_service._shadow_catalog.pop(key, None)
        except Exception:
            pass
        logger.info(f"shadow '{shadow_owner}' dismissed (module '{real_name}' untouched)")
        return True

    def diff(self, real_name: str, transcript: "Any | None" = None) -> "dict[str, Any]":
        """
        行为对比：影子意向出站 × 真实发送时间线（按 trace_id 对齐）

        内容保真度受 transcript 出站 preview（50 字符截断）限制——逐字段
        对比以影子账本为准，transcript 仅作"实际发送发生"的佐证源。

        :param real_name: 原模块名
        :param transcript: 收件箱单例（None 时惰性导入）
        :return: {"shadow_owner", "count", "aligned": [{"shadow", "actual"}]}
        """
        info = self._shadows.get(real_name)
        if not info:
            return {"shadow_owner": None, "count": 0, "aligned": []}
        shadow_owner = info["shadow_owner"]
        entries = shadow_ledger.entries(shadow_owner)
        if transcript is None:
            try:
                from .transcript import transcript as transcript_service

                transcript = transcript_service
            except Exception:
                transcript = None

        aligned: "list[dict[str, Any]]" = []
        for entry in entries:
            tid = entry.get("trace_id")
            actual = transcript.get_by_trace(tid) if (transcript is not None and tid) else []
            aligned.append({"shadow": entry, "actual": actual})

        return {
            "shadow_owner": shadow_owner,
            "count": len(entries),
            "aligned": aligned,
        }


# 模块级单例：账本（出站闸热路径引用）与管理器
shadow_ledger = ShadowLedger()
shadow_manager = ShadowManager()
