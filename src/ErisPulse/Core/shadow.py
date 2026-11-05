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

import io
import re
import secrets
import shutil
import subprocess
import sys
import threading
import time
import zipfile
from collections import deque
from pathlib import Path
from typing import Any

from .Bases.errors import ShadowPromoteError, ShadowSourceError, ShadowStateError
from .constants import (
    SHADOW_EXTRACT_MAX_BYTES,
    SHADOW_EXTRACT_MAX_ENTRIES,
    SHADOW_PERSIST_TASKS_MAX,
    SHADOW_PIP_TIMEOUT_SECS,
    SHADOW_WHL_MAX_BYTES,
)
from .i18n import i18n
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


def _source_in_plugin_dirs(plugin_loader: Any, source: Path) -> bool:
    """{!--< internal-use >!--}
    判断影子源路径是否位于插件发现目录内（位于其内时才需要写 status 禁用，
    防止下次启动被普通发现机制当作独立模块装载）

    :param plugin_loader: 插件加载器（提供 ``get_plugins_dirs()``）
    :param source: 影子源路径
    :return: 源位于任一插件目录内时 True（判定失败按 False 处理——宁可不
        写配置也不误禁同名真实插件）
    """
    try:
        src = source.resolve()
        return any(src.is_relative_to(d.resolve()) for d in plugin_loader.get_plugins_dirs())
    except Exception:
        return False


class ShadowLedger:
    """
    影子账本：影子 owner 的意向出站记录（内存环形，按 owner 分桶）

    记录来源：出站闸（``Send`` DSL / ``Api`` DSL）在 owner 属影子时写入。
    每条含 kind（send/api）/ platform / method / target / trace_id / preview。
    """

    def __init__(self) -> None:
        self._entries: dict[str, deque[dict[str, Any]]] = {}

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
        self._data: dict[str, Any] = {}
        self._tombstones: set[str] = set()

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
        self._shadows: dict[str, dict[str, str]] = {}
        # 影子 owner → 覆盖层
        self._overlays: dict[str, ShadowOverlay] = {}
        # 「转正并持久化」后台 pip 任务状态：task_id → {status, output, ...}
        self._persist_tasks: dict[str, dict[str, Any]] = {}

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

    def bindings(self) -> "dict[str, str]":
        """
        当前全部影子绑定（只读视图）

        :return: ``{原模块名: 影子 owner 名}``
        """
        return {
            real: info["shadow_owner"]
            for real, info in self._shadows.items()
            if info.get("shadow_owner")
        }

    # ---- whl 摄取与「转正并持久化」 ----

    _WHL_SEG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
    _WHL_DIR_RE = re.compile(r"^[A-Za-z]:")  # Windows 盘符前缀（ZipSlip 防护）

    def ingest_whl(self, module_name: str, data: bytes, filename: str) -> "dict[str, str]":
        """
        摄取 whl 作为影子源：校验 → 原件落盘 → 解包 → 推导 source

        原件与解包目录同级（``shadows/<module>/<时间戳>/``）：解包目录供
        :meth:`~ShadowManager.start` 装载，原件供「转正并持久化」pip 安装。
        影子期**只解包不安装**（pip 排他），避免覆盖已装包。

        :param module_name: 被影子测试的模块名（仅作落盘目录段）
        :param data: whl 文件字节
        :param filename: whl 文件名（PEP 427：name-version-...whl）
        :return: ``{"source": 解包源目录, "whl_path": 原件路径}``
        :raises ShadowSourceError: 文件名/大小非法、zip 非法或无法推导源目录

        :example:
        >>> sdk.module.shadow_ingest_whl("roll", data=whl_bytes, filename="roll-2.0-py3-none-any.whl")
        {'source': '.../shadows/roll/2026.../roll', 'whl_path': '.../shadows/roll/2026.../roll-2.0-py3-none-any.whl'}
        """
        if not isinstance(module_name, str) or module_name in (".", "..") or not self._WHL_SEG_RE.match(module_name):
            raise ShadowSourceError(f"invalid module name: {module_name!r}")
        filename = str(filename or "")
        if not filename.lower().endswith(".whl"):
            raise ShadowSourceError("only .whl files are allowed")
        stem_parts = filename[:-4].split("-")
        if len(stem_parts) < 5 or any(not p for p in stem_parts):
            raise ShadowSourceError("invalid wheel filename (name-version-...whl)")
        if not isinstance(data, bytes) or not data:
            raise ShadowSourceError("empty whl payload")
        if len(data) > SHADOW_WHL_MAX_BYTES:
            raise ShadowSourceError(f"wheel too large (max {SHADOW_WHL_MAX_BYTES // (1024 * 1024)}MB)")

        ts = time.strftime("%Y%m%d_%H%M%S") + "_" + secrets.token_hex(3)
        dest = Path.cwd() / "shadows" / module_name / ts
        try:
            source = self._extract_shadow_whl(data, dest, stem_parts[0])
            whl_path = dest.parent / filename
            whl_path.write_bytes(data)
        except Exception as e:
            shutil.rmtree(dest, ignore_errors=True)
            if isinstance(e, ShadowSourceError):
                raise
            raise ShadowSourceError(f"whl ingest failed: {e}") from e
        return {"source": str(source), "whl_path": str(whl_path)}

    def validate_persist_whl(self, module_name: str, whl_path: "str | Path") -> Path:
        """
        校验「转正并持久化」的 whl 原件路径

        路径必须存在、是 .whl，且位于本模块的 ``shadows/<module>/`` 目录内。

        :param module_name: 模块名
        :param whl_path: 待校验路径
        :return: 规范化后的路径
        :raises ShadowSourceError: 路径缺失 / 非法 / 越界
        """
        shadows_root = (Path.cwd() / "shadows" / module_name).resolve()
        try:
            candidate = Path(whl_path).resolve()
        except (OSError, ValueError) as e:
            raise ShadowSourceError(f"invalid whl_path: {e}") from e
        if not candidate.is_file() or not candidate.name.lower().endswith(".whl"):
            raise ShadowSourceError(f"whl_path not found: {candidate}")
        if shadows_root not in candidate.parents:
            raise ShadowSourceError("whl_path outside module shadows dir")
        return candidate

    def persist_status(self, task_id: str) -> "dict[str, Any] | None":
        """
        查询「转正并持久化」后台 pip 任务状态

        :param task_id: :meth:`start_persist` 返回的任务 ID
        :return: ``{"status": running/success/error, "output": [...], ...}``；未知任务为 None
        """
        return self._persist_tasks.get(task_id)

    def start_persist(self, whl_path: "str | Path") -> "dict[str, Any]":
        """
        后台 pip 安装 whl 原件（转正成功后调用；进程内 fire-and-forget）

        :param whl_path: 经 :meth:`validate_persist_whl` 校验的 whl 路径
        :return: ``{"task_id": str}``
        """
        task_id = "sp_" + secrets.token_hex(4)
        self._record_persist_task(task_id, {"status": "running", "started_at": time.time(), "path": str(whl_path)})
        thread = threading.Thread(
            target=self._run_pip_persist, args=(task_id, Path(whl_path)), daemon=True
        )
        thread.start()
        return {"task_id": task_id}

    def _record_persist_task(self, task_id: str, entry: "dict[str, Any]") -> None:
        """{!--< internal-use >!--} 记录持久化任务状态（环形上限）"""
        self._persist_tasks[task_id] = entry
        while len(self._persist_tasks) > SHADOW_PERSIST_TASKS_MAX:
            oldest = next(iter(self._persist_tasks))
            self._persist_tasks.pop(oldest, None)

    def _run_pip_persist(self, task_id: str, whl_path: Path) -> None:
        """{!--< internal-use >!--} 执行 pip install 并回写任务状态"""
        lines: list[str] = []
        try:
            proc = subprocess.Popen(
                [sys.executable, "-m", "pip", "install", str(whl_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
            )
            try:
                out, _ = proc.communicate(timeout=SHADOW_PIP_TIMEOUT_SECS)
                lines = (out or "").splitlines()
                rc = proc.returncode
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.communicate()
                lines.append(f"pip install timed out after {SHADOW_PIP_TIMEOUT_SECS}s")
                rc = 1
        except Exception as e:
            rc = 1
            lines.append(str(e))

        status = "success" if rc == 0 else "error"
        entry = {
            "status": status,
            "started_at": self._persist_tasks.get(task_id, {}).get("started_at"),
            "finished_at": time.time(),
            "path": str(whl_path),
            "output": lines[-50:],
        }
        self._record_persist_task(task_id, entry)
        log = logger.info if rc == 0 else logger.warning
        log(
            i18n.t(
                "core.shadow.persist_finished" if rc == 0 else "core.shadow.persist_failed",
                path=whl_path,
                rc=rc,
            )
        )

    def _extract_shadow_whl(self, data: bytes, dest: Path, dist_name: str) -> Path:
        """
        {!--< internal-use >!--}
        解包 whl（zip）到 dest 并推导影子源目录

        安全限制：条目数 / 解包总大小上限、拒绝绝对路径 / 盘符 / ``..``
        （防 ZipSlip）。source 推导：唯一含 ``__init__.py`` 的顶层包目录优先
        （发行名匹配者优先），其次扁平 wheel 解包根，最后唯一同名单文件模块。
        """
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            entries = [i for i in zf.infolist() if not i.is_dir()]
            if len(entries) > SHADOW_EXTRACT_MAX_ENTRIES:
                raise ShadowSourceError(
                    f"too many entries in wheel (max {SHADOW_EXTRACT_MAX_ENTRIES})"
                )
            total = sum(i.file_size for i in entries)
            if total > SHADOW_EXTRACT_MAX_BYTES:
                raise ShadowSourceError(
                    f"wheel decompressed size too large (max {SHADOW_EXTRACT_MAX_BYTES // (1024 * 1024)}MB)"
                )
            for info in entries:
                name = info.filename.replace("\\", "/")
                if name.startswith("/") or self._WHL_DIR_RE.match(name):
                    raise ShadowSourceError(f"unsafe entry in wheel: {info.filename}")
                if any(part == ".." for part in name.split("/")):
                    raise ShadowSourceError(f"unsafe entry in wheel: {info.filename}")
            dest.mkdir(parents=True, exist_ok=True)
            dest_resolved = dest.resolve()
            for info in entries:
                target = dest / info.filename.replace("\\", "/")
                target.parent.mkdir(parents=True, exist_ok=True)
                if not str(target.resolve()).startswith(str(dest_resolved)):
                    raise ShadowSourceError(f"entry escapes target dir: {info.filename}")
                with zf.open(info) as src, target.open("wb") as out:
                    shutil.copyfileobj(src, out, length=1024 * 1024)
        return self._derive_shadow_source(dest, dist_name)

    @staticmethod
    def _norm_wheel_dist_name(name: str) -> str:
        """{!--< internal-use >!--} wheel 发行名归一化（PEP 503）"""
        return re.sub(r"[-_.]+", "-", name).lower()

    def _derive_shadow_source(self, dest: Path, dist_name: str) -> Path:
        """{!--< internal-use >!--} 从解包结果推导 shadow_start 可用的 source"""
        tops = sorted(dest.iterdir(), key=lambda p: p.name)
        norm = self._norm_wheel_dist_name
        pkg_dirs = [
            p
            for p in tops
            if p.is_dir()
            and not p.name.endswith(".dist-info")
            and not p.name.endswith(".data")
            and not p.name.endswith(".libs")
        ]
        with_init = [p for p in pkg_dirs if (p / "__init__.py").exists()]
        matched = [p for p in with_init if norm(p.name) == norm(dist_name)]
        if len(matched) == 1:
            return matched[0]
        if len(with_init) == 1:
            return with_init[0]
        # 扁平 wheel：包内容直接在解包根（根目录即含 __init__.py）
        if (dest / "__init__.py").exists():
            return dest
        # 单模块 wheel：顶层唯一与发行名同名的 .py 文件
        singles = [
            p for p in tops if p.is_file() and p.suffix == ".py" and norm(p.stem) == norm(dist_name)
        ]
        if len(singles) == 1:
            return singles[0]
        raise ShadowSourceError("no package dir with __init__.py found in wheel")

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

    @staticmethod
    def _cleanup_sdk_attr(sdk: Any, owner: str) -> None:
        """{!--< internal-use >!--}
        清理 start 时挂在 sdk 上的影子实例属性（转正 / 放弃后残留会指向已回收实例）

        :param sdk: SDK 实例（None 时跳过）
        :param owner: 影子 owner 名
        """
        if sdk is None:
            return
        try:
            if owner[:1].isalpha() and owner.isidentifier() and hasattr(sdk, owner):
                delattr(sdk, owner)
        except Exception:
            pass

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
        :raises ShadowStateError: 原模块未加载 / 影子已存在
        :raises ShadowSourceError: 源路径无效 / 加载器缺失 / 影子装载失败

        :example:
        >>> await sdk.module.shadow_start("roll", source="downloads/roll_v2")
        'roll_shadow'
        """
        if real_name not in getattr(manager, "_loaded_modules", set()):
            raise ShadowStateError(f"module '{real_name}' is not loaded; cannot shadow it")
        if self.shadow_owner_of(real_name):
            raise ShadowStateError(f"module '{real_name}' already has an active shadow")

        src = Path(source)
        if not src.exists():
            raise ShadowSourceError(f"shadow source path not found: {src}")

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
            raise ShadowSourceError("plugin loader unavailable; cannot import shadow source")

        module_obj = plugin_loader._load_plugin(owner, src)
        if module_obj is None:
            raise ShadowSourceError(f"shadow source '{src}' contains no loadable module class")
        v_info = module_obj.moduleInfo
        v_class = v_info["module_class"]

        try:
            manager.register(owner, v_class, v_info)
            if not await manager.load(owner):
                raise ShadowSourceError("shadow load returned False")
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

        # 影子源若恰好位于插件发现目录内，禁用其启用状态，防止下次启动被
        # 普通发现机制当作独立模块装载；源在目录外（推荐位置）时不写用户配置
        if _source_in_plugin_dirs(plugin_loader, src):
            try:
                from .config import config as config_service
                from .constants import CONFIG_KEY_MODULE_STATUS_OF

                config_service.setConfig(CONFIG_KEY_MODULE_STATUS_OF.format(owner), False)
            except Exception as e:
                logger.warning(i18n.t("core.shadow.status_disable_failed", owner=owner, error=e))

        self.bind(real_name, owner)
        logger.info(i18n.t("core.shadow.started", owner=owner, real_name=real_name))
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
            raise ShadowStateError(f"no shadow bound for module '{real_name}'")
        shadow_owner = info["shadow_owner"]
        if real_name not in getattr(manager, "_loaded_modules", set()):
            raise ShadowPromoteError(f"module '{real_name}' is not loaded; nothing to promote onto")

        v2_class = (getattr(manager, "_module_classes", {}) or {}).get(shadow_owner)
        if v2_class is None:
            raise ShadowPromoteError(f"shadow '{shadow_owner}' is not registered")
        loaded = getattr(manager, "_loaded_modules", set())
        if shadow_owner not in loaded:
            raise ShadowPromoteError(f"shadow '{shadow_owner}' is not loaded")

        if loader is None:
            loader = getattr(sdk, "_module_loader", None)
        if loader is None or not hasattr(loader, "_capture_reload_state"):
            raise ShadowPromoteError("module loader does not support snapshot; cannot promote safely")

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
                raise ShadowPromoteError("load returned False")
            setattr(sdk, real_name, manager.get(real_name))
            module_obj = sys.modules.get(v2_class.__module__)
            if module_obj is not None:
                loader._last_module_objs[real_name] = module_obj
        except Exception as e:
            logger.error(i18n.t("core.shadow.promote_failed", real_name=real_name, error=e))
            await loader._restore_reload_snapshot(v1_snapshot, real_name, manager, sdk)
            await loader._restore_failed_dependents(dep_snapshots, manager, sdk)
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
        self._cleanup_sdk_attr(sdk, shadow_owner)
        logger.info(i18n.t("core.shadow.promoted", real_name=real_name, owner=shadow_owner))
        return True

    async def dismiss(
        self, real_name: str, manager: Any, sdk: "Any | None" = None
    ) -> bool:
        """
        放弃影子：回收影子资源、解除绑定、清空账本与命令目录

        :param real_name: 原模块名
        :param manager: 模块管理器实例
        :param sdk: SDK 实例（可选；传入时清理挂在 sdk 上的影子实例属性残留）
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
        self._cleanup_sdk_attr(sdk, shadow_owner)
        logger.info(i18n.t("core.shadow.dismissed", owner=shadow_owner, real_name=real_name))
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

        aligned: list[dict[str, Any]] = []
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
