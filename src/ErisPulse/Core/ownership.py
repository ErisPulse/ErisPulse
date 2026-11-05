"""
ErisPulse 归属权统一门面

归属权（owner）系统对外的统一入口。框架各子系统（路由 / 处理器 / 命令 /
任务 / 覆写 / 生命周期 / 主人身份源……）各自维护按 owner 注册的资源，
本模块把它们聚合为四个动词，替代散落在各子系统上形态不一的清理与查询 API：

- :func:`ownership.reclaim` / :func:`ownership.reclaim_sync` —— 统一注销
  owner 名下的全部资源（模块卸载 / 禁用 / 失败回滚共用的回收路径）
- :func:`ownership.counts` —— 按 owner 统计在册资源（审计的计数面）
- :func:`ownership.orphans` —— 孤儿扫描：资源在册而 owner 已注销（泄漏实锤）
- :func:`ownership.audit` —— 泄漏审计（计数 + 孤儿 + 可选 gc 实例普查）
- :func:`ownership.nest` / :func:`ownership.unnest` —— 声明父子归属，
  父回收时按注册逆序先回收子（资源级，不触发子的模块级 ``on_unload``）

各子系统既有的 ``*_by_owner`` 注销函数保持不变，作为本门面的内部 SPI；
新增可回收资源时，子系统提供注销函数并登记进 :func:`reclaim_sync` 的
步骤表、在 :func:`counts` 提供只读计数，门面与审计器即自动覆盖。

{!--< tips >!--}
1. reclaim 的注销顺序固定（归属任务 / 外部清理钩子先行，注册类资源随后），
   每步独立容错——单步失败不阻断其余回收（与卸载流程兜底风格一致）
2. counts / orphans 只读，无任何清理副作用
3. audit(deep=True) 会 ``gc.collect()`` 并做 weakref 实例存活普查——存在
   全局暂停开销，仅显式调用（``epsdk audit --deep``）
{!--< /tips >!--}
"""

import asyncio
from typing import Any

from .i18n import i18n
from .logger import logger

__all__ = ["OwnershipManager", "ownership"]


def _log_reclaim_failure(step: str, error: Exception) -> None:
    """{!--< internal-use >!--} 回收步骤失败留痕（单步失败不阻断其余回收，但必须可观测）"""
    try:
        from .i18n import i18n

        message = i18n.t("core.ownership.reclaim_step_failed", step=step, error=error)
    except Exception:
        message = f"ownership reclaim step '{step}' failed: {error}"
    logger.warning(message)


class OwnershipManager:
    """
    归属权管理器（单例）

    聚合各子系统的 owner 归属资源：统一注销（reclaim）、只读计数（counts）、
    孤儿扫描（orphans）、泄漏审计（audit）、嵌套生命周期（nest / unnest），
    以及影子 owner 判定面（is_shadow / register_shadow / unregister_shadow——
    影子模块机制，见 ``Core/shadow`` 与 docs/zh-CN/advanced/shadow.md）。
    子系统内部表通过惰性导入访问，避免加载链耦合（与 module.py 清理链的
    既有风格一致）。
    """

    def __init__(self) -> None:
        # 影子 owner 集合：ShadowManager 装配影子模块时登记、dismiss 时移除。
        # 八道隔离闸（事件副本 / 命令目录 / 出站记账 / 存储覆盖层 / 生命周期
        # 静默 / 路由只登记）统一以此集合为判定来源
        self._shadow_owners: set[str] = set()
        # 嵌套生命周期关系：parent -> [child, ...] 保持注册顺序，回收时逆序。
        # _nested_parents 为反向索引（子 -> 父集合），用于子先亡时自动解绑。
        # _nested_inflight 标记正在异步级联回收的父 owner，避免同步路径重复级联。
        self._nested_children: dict[str, list[str]] = {}
        self._nested_parents: dict[str, set[str]] = {}
        self._nested_inflight: set[str] = set()

    # ==================== 嵌套生命周期 ====================

    def nest(self, parent: str, child: str) -> bool:
        """
        声明父子归属关系：父被回收时子先被完整回收

        拒绝自环与已存在的反向链（会形成环）；重复声明幂等。

        :param parent: 父 owner 名
        :param child: 子 owner 名
        :return: 是否声明成功

        :example:
        >>> from ErisPulse.Core import ownership
        >>> ownership.nest("ScriptEngine", "ScriptEngine.plugin_a")
        True
        """
        if not parent or not child:
            logger.warning(i18n.t("core.ownership.nest_invalid"))
            return False
        if parent == child or self._reaches(child, parent):
            logger.warning(
                i18n.t(
                    "core.ownership.nest_cycle",
                    parent=parent,
                    child=child,
                )
            )
            return False
        children = self._nested_children.setdefault(parent, [])
        if child not in children:
            children.append(child)
        self._nested_parents.setdefault(child, set()).add(parent)
        return True

    def unnest(self, parent: str, child: str) -> bool:
        """
        解除父子归属关系

        :param parent: 父 owner 名
        :param child: 子 owner 名
        :return: 是否解除了既有关系
        """
        children = self._nested_children.get(parent)
        if not children or child not in children:
            return False
        children.remove(child)
        if not children:
            self._nested_children.pop(parent, None)
        parents = self._nested_parents.get(child)
        if parents is not None:
            parents.discard(parent)
            if not parents:
                self._nested_parents.pop(child, None)
        return True

    def nested_children(self, parent: str) -> "frozenset[str]":
        """
        只读视图：父 owner 当前登记的子 owner

        :param parent: 父 owner 名
        :return: 子 owner 名集合
        """
        return frozenset(self._nested_children.get(parent, ()))

    def begin_nested_reclaim(self, owner: str) -> bool:
        """
        {!--< internal-use >!--}
        标记 owner 的异步级联回收即将开始

        供同步入口（如 ``ModuleManager.disable``）在调度后台级联前调用，
        使随后的 :meth:`reclaim_sync` 跳过子级联，避免与异步路径重复。

        :param owner: 父 owner 名
        :return: 是否存在需要级联的子 owner
        """
        if not self._nested_children.get(owner):
            return False
        self._nested_inflight.add(owner)
        return True

    async def reclaim_nested(self, owner: str) -> "dict[str, int]":
        """
        按注册逆序回收 owner 的全部子 owner（递归级联）

        每个子回收受 ``CLEANUP_CALLBACK_TIMEOUT_SECS`` 约束；超时或失败
        告警后继续处理其余子，并移除该父子关系（残留资源由 orphans 暴露）。

        :param owner: 父 owner 名
        :return: ``{"nested_children": 已处理子数}``
        """
        children = list(self._nested_children.get(owner, ()))
        if not children:
            self._nested_inflight.discard(owner)
            return {}
        self._nested_inflight.add(owner)
        processed = 0
        try:
            from .constants import CLEANUP_CALLBACK_TIMEOUT_SECS

            for child in reversed(children):
                try:
                    await asyncio.wait_for(
                        self.reclaim(child),
                        timeout=CLEANUP_CALLBACK_TIMEOUT_SECS,
                    )
                except asyncio.TimeoutError:
                    logger.warning(
                        i18n.t(
                            "core.ownership.nest_child_timeout",
                            parent=owner,
                            child=child,
                            timeout=CLEANUP_CALLBACK_TIMEOUT_SECS,
                        )
                    )
                except Exception as e:
                    _log_reclaim_failure(f"nested_child:{child}", e)
                finally:
                    self.unnest(owner, child)
                    processed += 1
        finally:
            self._nested_inflight.discard(owner)
        return {"nested_children": processed}

    def _reaches(self, start: str, target: str) -> bool:
        """{!--< internal-use >!--} 沿子关系判断 start 是否可达 target（环检测）"""
        if start == target:
            return True
        visited: set[str] = set()
        stack = [start]
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            for child in self._nested_children.get(current, ()):
                if child == target:
                    return True
                if child not in visited:
                    stack.append(child)
        return False

    def _detach_from_parents(self, child: str) -> None:
        """{!--< internal-use >!--} 子被独立回收后从所有父的登记中移除"""
        for parent in list(self._nested_parents.pop(child, set())):
            children = self._nested_children.get(parent)
            if not children:
                continue
            try:
                children.remove(child)
            except ValueError:
                pass
            if not children:
                self._nested_children.pop(parent, None)


    # ==================== 影子判定面 ====================

    def register_shadow(self, owner: str) -> None:
        """
        登记影子 owner（ShadowManager 装配影子模块时调用）

        :param owner: 影子 owner 名（如 ``"roll_shadow"``）
        """
        self._shadow_owners.add(owner)

    def unregister_shadow(self, owner: str) -> None:
        """
        移除影子 owner 登记（影子转正 / 放弃时调用）

        :param owner: 影子 owner 名
        """
        self._shadow_owners.discard(owner)

    def is_shadow(self, owner: "str | None") -> bool:
        """
        判定 owner 是否为影子模块 owner（八道隔离闸的统一判定入口）

        :param owner: owner 名
        :return: 是否为已登记的影子 owner
        """
        return bool(owner) and owner in self._shadow_owners

    def shadow_owners(self) -> "frozenset[str]":
        """
        当前全部影子 owner（只读视图）

        :return: 影子 owner 名集合
        """
        return frozenset(self._shadow_owners)

    # ==================== 统一注销 ====================

    async def reclaim(self, owner: str) -> "dict[str, int]":
        """
        统一注销 owner 名下的全部资源（异步完整版）

        顺序：取消归属后台任务 → 关闭归属连接 → 释放合作式登记资源 →
        触发外部清理钩子（on_cleanup）→ 注销全部注册类资源。模块卸载 /
        禁用的标准回收路径。

        :param owner: owner 名（模块名或适配器平台名）
        :return: 各类资源注销数量（键见 :meth:`reclaim_sync`，另含
                 ``tasks_cancelled`` / ``cleanups_run``）

        :example:
        >>> from ErisPulse.Core import ownership
        >>> await ownership.reclaim("roll")
        """
        result = await self.reclaim_nested(owner)
        result.update(await self.reclaim_tasks(owner))
        result.update(self.reclaim_sync(owner))
        self._detach_from_parents(owner)
        return result

    async def reclaim_tasks(self, owner: str) -> "dict[str, int]":
        """
        注销 owner 的进行中工作：归属后台任务取消 + 归属连接关闭 + 合作式资源释放 + 外部清理钩子触发

        :param owner: owner 名
        :return: {"tasks_cancelled": int, "connections_closed": int,
                 "tracked_released": int, "cleanups_run": int}
        """
        result = {"tasks_cancelled": 0, "connections_closed": 0, "cleanups_run": 0, "tracked_released": 0}
        try:
            from ..runtime.tasks import cancel_owner_tasks

            result["tasks_cancelled"] = await cancel_owner_tasks(owner)
        except Exception as e:
            _log_reclaim_failure("tasks_cancelled", e)
        try:
            from .connections import connections

            result["connections_closed"] = await connections.close_owner(owner)
        except Exception as e:
            _log_reclaim_failure("connections_closed", e)
        try:
            from ..runtime.resource_track import release_owner_tracked

            result["tracked_released"] = await release_owner_tracked(owner)
        except Exception as e:
            _log_reclaim_failure("tracked_released", e)
        try:
            from ..runtime.owner_cleanup import run_owner_cleanups

            result["cleanups_run"] = await run_owner_cleanups(owner)
        except Exception as e:
            _log_reclaim_failure("cleanups_run", e)
        return result

    def reclaim_sync(self, owner: str) -> "dict[str, int]":
        """
        注销 owner 的全部注册类资源（同步版，不含任务取消）

        涵盖：i18n 翻译域、路由（命名空间 + owner 兜底）、适配器事件处理器、
        自定义会话类型、平台事件方法注入、事件覆写、scope 覆写、命令与
        四类事件处理器、交互会话等待、主人身份源、生命周期钩子、
        日志订阅（logger.handler）、对话恢复工厂（resume handler）。
        每步独立容错，单步失败不阻断后续回收。

        :param owner: owner 名（模块名或适配器平台名）
        :return: 各类资源注销数量

        :example:
        >>> ownership.reclaim_sync("roll")
        {"routes_http": 2, "commands": 1, ...}
        """
        result: dict[str, int] = {}

        # 子先于父：独立调用 reclaim_sync 时先逆序级联子的注册类资源；
        # 异步 reclaim_nested 已标记 inflight 时由其负责，避免重复级联。
        nested_processed = 0
        if owner not in self._nested_inflight:
            for child in reversed(list(self._nested_children.get(owner, ()))):
                try:
                    self.reclaim_sync(child)
                except Exception as e:
                    _log_reclaim_failure(f"nested_child:{child}", e)
                finally:
                    self.unnest(owner, child)
                    nested_processed += 1
        if nested_processed:
            result["nested_children"] = nested_processed

        try:
            from .i18n import i18n as i18n_service

            i18n_service.unregister_domain(owner)
            result["i18n_domain"] = 1
        except Exception as e:
            _log_reclaim_failure("i18n_domain", e)

        try:
            from .router import router as router_service

            route_result = router_service.unregister_all_by_namespace(owner)
            result["routes_http"] = route_result.get("http_count", 0)
            result["routes_ws"] = route_result.get("websocket_count", 0)
            result["routes_sse"] = route_result.get("sse_count", 0)
            owner_result = router_service.unregister_all_by_owner(owner)
            result["middlewares"] = owner_result.get("middleware_count", 0)
            result["home_entries"] = owner_result.get("home_entry_count", 0)
        except Exception as e:
            _log_reclaim_failure("routes", e)

        try:
            from .adapter import adapter as adapter_service

            result["adapter_handlers"] = adapter_service.unregister_handlers_by_owner(owner)
        except Exception as e:
            _log_reclaim_failure("adapter_handlers", e)

        try:
            from .Event import (
                unregister_custom_types_by_owner,
                unregister_event_methods_by_owner,
            )

            result["custom_types"] = unregister_custom_types_by_owner(owner)
            result["event_methods"] = unregister_event_methods_by_owner(owner)
        except Exception as e:
            _log_reclaim_failure("event_types", e)

        try:
            from .Event import overrides

            result["overrides"] = overrides.unregister_by_owner(owner)
        except Exception as e:
            _log_reclaim_failure("overrides", e)

        try:
            from .scope import scope as scope_service

            result["scope_overrides"] = scope_service.unregister_by_owner(owner)
        except Exception as e:
            _log_reclaim_failure("scope_overrides", e)

        try:
            from .Event import command as command_service

            result["commands"] = command_service.unregister_by_owner(owner)
        except Exception as e:
            _log_reclaim_failure("commands", e)

        try:
            from .Event import message, meta, notice, request

            result["handlers_message"] = message.handler.unregister_by_owner(owner)
            result["handlers_notice"] = notice.handler.unregister_by_owner(owner)
            result["handlers_request"] = request.handler.unregister_by_owner(owner)
            result["handlers_meta"] = meta.handler.unregister_by_owner(owner)
        except Exception as e:
            _log_reclaim_failure("handlers", e)

        try:
            from .Event import interaction

            result["waiters_cancelled"] = interaction.cancel_by_owner(owner)
        except Exception as e:
            _log_reclaim_failure("waiters", e)

        try:
            from .master import master as master_service

            result["master_providers"] = master_service.unregister_by_owner(owner)
        except Exception as e:
            _log_reclaim_failure("master_providers", e)

        try:
            from .lifecycle import lifecycle as lifecycle_service

            result["lifecycle_hooks"] = lifecycle_service.unregister_by_owner(owner)
        except Exception as e:
            _log_reclaim_failure("lifecycle_hooks", e)

        try:
            from .logger import logger as logger_service

            result["log_handlers"] = logger_service.unregister_by_owner(owner)
        except Exception as e:
            _log_reclaim_failure("log_handlers", e)

        try:
            from .Event.conversation import unregister_resume_handlers_by_owner

            result["resume_handlers"] = unregister_resume_handlers_by_owner(owner)
        except Exception as e:
            _log_reclaim_failure("resume_handlers", e)

        self._detach_from_parents(owner)
        return {key: count for key, count in result.items() if count}

    # ==================== 只读计数 ====================

    def counts(self, owner: "str | None" = None) -> Any:
        """
        统计 owner 在册的归属资源（只读，无副作用）

        :param owner: owner 名；None 时返回全部 owner 的计数
        :return: ``owner`` 给定时为 {资源类: 数量}；None 时为
                 {owner: {资源类: 数量}}（未挂任何资源的 owner 不出现）

        :example:
        >>> ownership.counts("roll")
        {"commands": 1, "lifecycle_hooks": 2}
        """
        table: dict[str, dict[str, int]] = {}

        def _add(o: Any, kind: str, n: int) -> None:
            if o is None or n <= 0:
                return
            entry = table.setdefault(str(o), {})
            entry[kind] = entry.get(kind, 0) + n

        def _items_count(items: Any, get_owner: Any, kind: str) -> None:
            try:
                for item in items:
                    try:
                        o = get_owner(item)
                    except Exception:
                        continue
                    _add(o, kind, 1)
            except Exception:
                pass

        try:
            from ..runtime import tasks as tasks_module

            for o, task_set in (getattr(tasks_module, "_owner_tasks", {}) or {}).items():
                _add(o, "tasks", len(task_set or ()))
            for o, timer_set in (getattr(tasks_module, "_owner_timers", {}) or {}).items():
                _add(o, "timers", len(timer_set or ()))
            for o, thread_set in (getattr(tasks_module, "_owner_threads", {}) or {}).items():
                _add(o, "threads", sum(1 for t in (thread_set or ()) if t.is_alive()))
        except Exception:
            pass

        try:
            from .connections import connections as connections_service

            for o, conn_ids in (getattr(connections_service, "_by_owner", {}) or {}).items():
                _add(o, "connections", len(conn_ids or ()))
        except Exception:
            pass

        try:
            from ..runtime.owner_cleanup import _owner_cleanups

            for o, hooks in (_owner_cleanups or {}).items():
                _add(o, "cleanups", len(hooks or ()))
        except Exception:
            pass

        try:
            from ..runtime.resource_track import _owner_tracked

            for o, resources in (_owner_tracked or {}).items():
                _add(o, "tracked", len(resources or ()))
        except Exception:
            pass

        try:
            from .router import router as router_service

            for o, namespaces in (router_service._owner_namespaces or {}).items():
                for namespace in namespaces or ():
                    _add(o, "routes_http", len(router_service._http_routes.get(namespace, {})))
                    _add(o, "routes_ws", len(router_service._websocket_routes.get(namespace, {})))
                    _add(o, "routes_sse", len(router_service._sse_routes.get(namespace, {})))
            _items_count(
                router_service._middleware_records,
                lambda record: record.get("owner"),
                "middlewares",
            )
            _items_count(
                router_service._home_entries,
                lambda entry: entry.get("owner"),
                "home_entries",
            )
        except Exception:
            pass

        try:
            from .adapter import adapter as adapter_service

            _items_count(
                list(adapter_service._onebot_handlers.values())
                + list(adapter_service._raw_handlers.values()),
                lambda h: h.get("owner") if isinstance(h, dict) else getattr(h, "owner", None),
                "adapter_handlers",
            )
        except Exception:
            pass

        try:
            from .Event.session_type import _custom_type_owners

            _items_count(_custom_type_owners.items(), lambda kv: kv[1], "custom_types")
        except Exception:
            pass

        try:
            from .Event.wrapper import _event_method_owners

            for o, entries in (_event_method_owners or {}).items():
                _add(o, "event_methods", len(entries or ()))
        except Exception:
            pass

        try:
            from .Event.overrides import _runtime_owner_records

            _items_count(_runtime_owner_records.items(), lambda kv: kv[1], "overrides")
        except Exception:
            pass

        try:
            from .scope import scope as scope_service

            _items_count(
                getattr(scope_service, "_runtime_owners", {}).items(),
                lambda kv: kv[1],
                "scope_overrides",
            )
        except Exception:
            pass

        try:
            from .Event import command as command_service

            _items_count(
                (command_service.commands or {}).items(),
                lambda kv: (kv[1] or {}).get("owner") if isinstance(kv[1], dict) else None,
                "commands",
            )
        except Exception:
            pass

        try:
            from .Event import message, meta, notice, request

            for handler_box, kind in (
                (message.handler, "handlers_message"),
                (notice.handler, "handlers_notice"),
                (request.handler, "handlers_request"),
                (meta.handler, "handlers_meta"),
            ):
                _items_count(
                    getattr(handler_box, "handlers", []) or [],
                    lambda h: h.get("owner") if isinstance(h, dict) else getattr(h, "owner", None),
                    kind,
                )
        except Exception:
            pass

        try:
            from .Event import interaction as interaction_service

            for o, waiters in (interaction_service._by_owner or {}).items():
                _add(o, "waiters", len(waiters or ()))
            for o, timers in (interaction_service._timers_by_owner or {}).items():
                _add(o, "timers", len(timers or ()))
        except Exception:
            pass

        try:
            from .master import master as master_service

            _items_count(
                (master_service._provider_owners or {}).items(),
                lambda kv: kv[1],
                "master_providers",
            )
        except Exception:
            pass

        try:
            from .lifecycle import lifecycle as lifecycle_service

            for o, n in (lifecycle_service.get_owner_counts() or {}).items():
                _add(o, "lifecycle_hooks", n)
        except Exception:
            pass

        try:
            from .i18n import i18n as i18n_service

            for domain, keys in (getattr(i18n_service, "_domains", {}) or {}).items():
                _add(domain, "i18n_keys", len(keys or ()))
        except Exception:
            pass

        try:
            from .logger import logger as logger_service

            _items_count(
                getattr(logger_service, "_log_handlers", []) or [],
                lambda h: h.get("owner") if isinstance(h, dict) else getattr(h, "owner", None),
                "log_handlers",
            )
        except Exception:
            pass

        try:
            from .Event.conversation import _conversation_resume_handlers

            _items_count(
                (_conversation_resume_handlers or {}).items()
                if isinstance(_conversation_resume_handlers, dict)
                else [],
                lambda kv: kv[1],
                "resume_handlers",
            )
        except Exception:
            pass

        for parent, children in self._nested_children.items():
            if children:
                entry = table.setdefault(parent, {})
                entry["nested"] = len(children)

        if owner is not None:
            return table.get(str(owner), {})
        return table

    # ==================== 孤儿扫描与审计 ====================

    def orphans(self) -> "list[dict[str, Any]]":
        """
        孤儿 owner 扫描：资源仍在册、而 owner（模块 / 适配器）已注销

        这是资源泄漏的实锤信号——清理链对"有注册存根的 owner"生效，
        孤儿资源（如工具模块私有容器持有的句柄、第三方库内部的引用）
        框架无法自动回收，但本扫描让它们**可见**。

        :return: [{"owner": str, "total": int, "resources": {资源类: 数量}}, ...]
                 按 owner 名排序；无孤儿时为空列表

        :example:
        >>> from ErisPulse.Core import ownership
        >>> ownership.orphans()
        [{"owner": "ghost_module", "total": 2, "resources": {"commands": 1, ...}}]
        """
        registered: set[str] = set()
        try:
            from .module import module as module_manager

            registered |= set((getattr(module_manager, "_module_classes", {}) or {}).keys())
        except Exception:
            pass
        try:
            from .adapter import adapter as adapter_service

            registered |= set((getattr(adapter_service, "_adapters", {}) or {}).keys())
        except Exception:
            pass

        # 嵌套关系闭包：已注册 owner 名下的嵌套子（含多级）视为受管，
        # 不算孤儿；父已消失的残留关系仍会暴露
        governed: set[str] = set()
        queue = list(registered)
        while queue:
            parent = queue.pop()
            for child in self._nested_children.get(parent, ()):
                if child in governed:
                    continue
                governed.add(child)
                queue.append(child)

        all_counts = self.counts()
        result = []
        for o in sorted(all_counts):
            if o in registered or o in governed:
                continue
            resources = all_counts[o]
            result.append(
                {"owner": o, "total": sum(resources.values()), "resources": resources}
            )
        return result

    def audit(self, owner: "str | None" = None, deep: bool = False) -> "dict[str, Any]":
        """
        泄漏审计：计数 + 孤儿扫描（+ 可选 gc 实例普查）

        :param owner: 目标 owner（模块名）；None 时审计全局（全部 owner 计数）
        :param deep: 对模块实例做 weakref 存活普查——``gc.collect()`` 后检查
                     实例是否可回收，不可回收时给出引用方类型（有全局暂停
                     开销，仅显式使用）
        :return: 审计报告 dict（owner / counts / orphans / 深普查结果）

        :example:
        >>> ownership.audit("roll", deep=True)
        {"owner": "roll", "counts": {...}, "orphans": [], "instance_recyclable": True}
        """
        report: dict[str, Any] = {
            "owner": owner,
            "counts": self.counts(owner) if owner else self.counts(),
            "orphans": self.orphans(),
        }
        if owner is not None and deep:
            instance = None
            try:
                from .module import module as module_manager

                instance = (getattr(module_manager, "_modules", {}) or {}).get(owner)
            except Exception:
                pass
            if instance is not None:
                import gc
                import weakref

                ref = weakref.ref(instance)
                gc.collect()
                report["instance_recyclable"] = ref() is None
                if ref() is not None:
                    report["referrers"] = [
                        type(r).__name__ for r in gc.get_referrers(instance)[:8]
                    ]
            else:
                report["instance_recyclable"] = None
        if report["orphans"]:
            logger.warning(
                f"ownership audit: {len(report['orphans'])} orphan owner(s) detected: "
                f"{[o['owner'] for o in report['orphans']]}"
            )
        return report


# 模块级单例
ownership = OwnershipManager()
