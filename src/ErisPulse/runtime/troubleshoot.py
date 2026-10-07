"""
模块排查诊断（EPRFC-2026-001 方向五·场景一 / 二）

回答两类"没反应"问题的诊断 API：

- :func:`explain_module`——模块没加载：依赖缺失 / 被配置禁用 / SDK 版本
  不满足 / 懒加载未实例化，逐项给出结构化原因
- :func:`explain_event`——事件没响应：适配器未注册 / 身份被作用域拉黑 /
  各已加载模块的作用域可用性 / 命令是否命中，输出判定结论

{!--< tips >!--}
1. 两个函数均为纯读诊断，不改任何状态
2. 返回 dict（机器可读），配 :func:`format_report` 渲染为人类可读文本
3. conclusion / reasons 文案经 i18n 以当前语言渲染（``runtime.troubleshoot.*`` 键）
{!--< /tips >!--}
"""

from __future__ import annotations

from typing import Any

from ..Core.i18n import i18n
from .version import check_min_sdk_version

__all__ = ["explain_module", "explain_event", "format_report"]


def explain_module(name: str) -> dict[str, Any]:
    """
    诊断"模块为什么没加载"（场景一）

    :param name: 模块注册名
    :return: 结构化诊断结果——``registered``（类是否已注册）、``loaded``
        （是否已加载）、``lazy``（懒加载策略）、``enabled``（配置启用状态，
        None 表示未配置即默认启用）、``missing_dependencies``（未就绪依赖）、
        ``sdk_version_ok``（SDK 版本是否满足，无法判定时为 None）、
        ``conclusion``（一句话结论）、``reasons``（原因列表）
    """
    from ..Core import module as module_mgr

    result: dict[str, Any] = {
        "name": name,
        "registered": False,
        "loaded": False,
        "lazy": False,
        "enabled": None,
        "missing_dependencies": [],
        "sdk_version_ok": None,
        "conclusion": "",
        "reasons": [],
    }

    cls = module_mgr._module_classes.get(name)
    if cls is None:
        result["conclusion"] = i18n.t("runtime.troubleshoot.module_not_registered", name=name)
        result["reasons"].append(i18n.t("runtime.troubleshoot.module_not_registered_reason"))
        return result
    result["registered"] = True

    result["loaded"] = module_mgr.is_loaded(name)

    # 加载策略：懒加载未实例化属正常状态而非故障
    try:
        strategy = cls.get_load_strategy()
        result["lazy"] = bool(getattr(strategy, "lazy_load", False))
    except Exception:
        pass
    if not result["loaded"] and result["lazy"]:
        result["conclusion"] = i18n.t("runtime.troubleshoot.module_lazy", name=name)
        result["reasons"].append(i18n.t("runtime.troubleshoot.module_lazy_reason"))
        return result

    # 配置启用状态：None = 未配置（默认启用）；False = 被显式禁用
    from ..Core.config import parse_bool_config

    enabled_raw = None
    try:
        from ..Core import config as config_instance

        enabled_raw = config_instance.getConfig(f"ErisPulse.modules.status.{name}")
    except Exception:
        pass
    if enabled_raw is not None:
        result["enabled"] = parse_bool_config(enabled_raw)
        if result["enabled"] is False:
            result["reasons"].append(
                i18n.t("runtime.troubleshoot.module_disabled_reason", name=name)
            )

    # SDK 版本要求
    try:
        meta = cls.get_meta()
        min_sdk = getattr(meta, "min_sdk_version", None)
        if min_sdk:
            ok, current, _norm, parseable = check_min_sdk_version(min_sdk)
            result["sdk_version_ok"] = ok or not parseable
            if not (ok or not parseable):
                result["reasons"].append(
                    i18n.t(
                        "runtime.troubleshoot.module_sdk_version_reason",
                        current=current,
                        required=min_sdk,
                    )
                )
    except Exception:
        pass

    # 依赖就绪检查（仅声明了 depends 的模块）
    try:
        strategy = cls.get_load_strategy()
        depends = list(getattr(strategy, "depends", []) or [])
    except Exception:
        depends = []
    for dep in depends:
        if not module_mgr.is_loaded(dep):
            result["missing_dependencies"].append(dep)
    if result["missing_dependencies"]:
        result["reasons"].append(
            i18n.t(
                "runtime.troubleshoot.module_deps_reason",
                deps=", ".join(result["missing_dependencies"]),
            )
        )

    if not result["reasons"]:
        result["conclusion"] = i18n.t("runtime.troubleshoot.module_registered_not_loaded", name=name)
        result["reasons"].append(
            i18n.t("runtime.troubleshoot.module_registered_not_loaded_reason")
        )
    else:
        result["conclusion"] = "; ".join(result["reasons"])
    return result


def explain_event(event: dict[str, Any]) -> dict[str, Any]:
    """
    诊断"事件为什么没响应"（场景二）

    :param event: 事件数据（dict 或 Event 包装）
    :return: 结构化诊断结果——``adapter_registered``（平台适配器是否已注册）、
        ``identity_allowed``（身份维度是否放行）、``available_modules``（当前
        会话可用的已加载模块）、``blocked_modules``（被作用域屏蔽的模块）、
        ``command_like``（文本是否形如命令）、``command_registered``（命令是否
        已注册）、``conclusion``、``reasons``
    """
    from ..Core import adapter as adapter_mgr
    from ..Core.Event.command import command as command_handler
    from ..Core.scope import scope as scope_mgr

    def _get(key, default=None):
        try:
            return event.get(key, default)
        except Exception:
            return default

    platform = _get("platform", "")
    self_info = _get("self") or {}
    bot_id = self_info.get("account_id") or self_info.get("user_id") or None
    user_id = _get("user_id") or None
    session_id = scope_mgr.session_id_from_event(event) or None

    result: dict[str, Any] = {
        "platform": platform,
        "adapter_registered": False,
        "identity_allowed": None,
        "available_modules": [],
        "blocked_modules": [],
        "command_like": False,
        "command_registered": None,
        "conclusion": "",
        "reasons": [],
    }

    # 平台适配器是否注册
    result["adapter_registered"] = (
        bool(platform) and hasattr(adapter_mgr, platform) and platform in adapter_mgr._adapters
    )
    if not result["adapter_registered"]:
        result["reasons"].append(
            i18n.t("runtime.troubleshoot.event_adapter_missing_reason", platform=platform)
        )

    # 身份维度（谁的事件收不收）
    result["identity_allowed"] = scope_mgr.is_identity_allowed(
        str(platform or ""), bot_id, session_id, user_id
    )
    if result["identity_allowed"] is False:
        result["reasons"].append(
            i18n.t("runtime.troubleshoot.event_identity_blocked_reason")
        )

    # 各已加载模块的会话可用性
    from ..Core import module as module_mgr

    for mod_name in list(module_mgr._modules.keys()):
        if scope_mgr.is_allowed(str(platform or ""), bot_id, mod_name, session_id):
            result["available_modules"].append(mod_name)
        else:
            result["blocked_modules"].append(mod_name)
    if result["blocked_modules"]:
        result["reasons"].append(
            i18n.t(
                "runtime.troubleshoot.event_modules_blocked_reason",
                modules=", ".join(result["blocked_modules"]),
            )
        )

    # 命令命中判定（仅消息事件有意义）
    alt = _get("alt_message") or ""
    prefixes = command_handler.prefix if isinstance(command_handler.prefix, list) else [command_handler.prefix]
    if alt and any(alt.startswith(p) for p in prefixes):
        # 形如命令（带前缀）：进一步判定是否命中注册命令
        result["command_like"] = True
        result["command_registered"] = command_handler._is_command_text(alt)
        if result["command_registered"] is False:
            result["reasons"].append(
                i18n.t("runtime.troubleshoot.event_command_unregistered_reason", text=alt)
            )

    if not result["reasons"]:
        result["conclusion"] = i18n.t("runtime.troubleshoot.event_entry_passed")
        result["reasons"].append(i18n.t("runtime.troubleshoot.event_entry_passed_reason"))
    else:
        result["conclusion"] = "; ".join(result["reasons"])
    return result


def format_report(result: dict[str, Any]) -> str:
    """
    将诊断结果渲染为人类可读文本（当前语言）

    :param result: :func:`explain_module` 或 :func:`explain_event` 的返回值
    :return: 多行文本（结论 + 原因列表）
    """
    name = result.get("name") or result.get("platform") or ""
    lines = [
        i18n.t("runtime.troubleshoot.report_title", name=name),
        i18n.t("runtime.troubleshoot.report_conclusion", conclusion=result.get("conclusion", "")),
    ]
    lines.extend(f"  - {reason}" for reason in result.get("reasons", []))
    return "\n".join(lines)
