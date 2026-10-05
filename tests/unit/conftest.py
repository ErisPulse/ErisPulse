"""
单元测试共享夹具

框架的单例状态（命令注册表 / 事件处理器 / 适配器通道 / sys.modules 中的
框架模块条目）是进程级的：前置测试的残留会改变后续测试的分发行为与全量
断言结果，且 xdist 分组顺序不同，污染表现不稳定。本文件以 autouse 夹具
在每个测试前后做快照 / 恢复，实现双向隔离。
"""

import sys

import pytest

from ErisPulse.Core.Event import command as command_handler
from ErisPulse.Core.Event import message, meta, notice, request

# 命令注册表上按"整表快照/恢复"处理的 dict/set 属性（含命令治理状态表）
_COMMAND_DICTS = (
    "commands",
    "aliases",
    "groups",
    "permissions",
    "_shadow_catalog",
    "_gate._cooldowns",
    "_gate._rate_limits",
    "_gate._usage_counts",
    "_gate._cooldown_replied",
    "_gate._usage_replied",
)
_COMMAND_SETS = (
    "_gate._rate_limit_replied",
    "_gate._usage_persist_warned",
)

# 事件处理器来源（各含 .handler.handlers 列表与 .handler._handler_map 映射）
_EVENT_SOURCES = (message, notice, request, meta)


def _resolve(obj, path: str):
    for part in path.split("."):
        obj = getattr(obj, part)
    return obj


def _fill(container, snapshot) -> None:
    container.clear()
    if isinstance(snapshot, list):
        container.extend(snapshot)
    else:
        container.update(snapshot)


# 会话级 sys.modules 规范基线（首个使用本夹具的测试 setup 时建立，见夹具 docstring）
_SESSION_MODULES_SNAPSHOT = None


@pytest.fixture(autouse=True)
def _isolated_framework_singletons():
    """
    逐测试隔离框架单例状态（命令注册表 / 事件处理器 / 适配器通道 / sys.modules）

    - 命令注册表（含治理状态表）与已注册命令名 token 数
    - message / notice / request / meta 四类事件处理器表
    - 适配器事件通道（onebot / raw 处理器、中间件、bot 表）
    - sys.modules 中的 ``ErisPulse.*`` 条目（防合成模块 / mock 残留遮蔽真实模块，
      如 module 管理器单例属性被删导致 ``patch("ErisPulse.Core.module.module...")``
      解析出 ModuleNotFoundError）
    - ``ErisPulse.Core.module`` 模块命名空间（防单例名被删除 / 重绑定）
    - 交互会话状态（wait_reply 等待表与租约，含运行期对象，仅清理不恢复）
    """
    command_dict_snapshots = {path: dict(_resolve(command_handler, path)) for path in _COMMAND_DICTS}
    command_set_snapshots = {path: set(_resolve(command_handler, path)) for path in _COMMAND_SETS}
    max_name_tokens = command_handler._max_name_tokens

    event_snapshots = [
        (src.handler.handlers[:], dict(src.handler._handler_map)) for src in _EVENT_SOURCES
    ]

    from ErisPulse.Core.adapter import adapter

    adapter_channels = {
        name: getattr(adapter, name)
        for name in ("_onebot_handlers", "_raw_handlers", "_onebot_middlewares", "_bots")
    }
    adapter_snapshots = {
        name: (list(value) if isinstance(value, list) else dict(value))
        for name, value in adapter_channels.items()
    }

    module_sys = __import__("ErisPulse.Core.module", fromlist=["__file__"])
    module_vars_snapshot = dict(vars(module_sys))
    # sys.modules 快照以会话首次进入本夹具时的状态为规范基线（而非逐测试快照）：
    # sdk uninit / 硬重启的清理会删除 ErisPulse.* 子模块条目，若按上次测试的
    # setup 快照恢复，"缺失"状态会被永久化——之后本工人内任何
    # ``import ErisPulse.Core.xxx`` 都会重新执行模块体、产生第二个框架单例
    # （空管理器 / 空命令表），后续测试以随机组合集体失败。
    global _SESSION_MODULES_SNAPSHOT
    if _SESSION_MODULES_SNAPSHOT is None:
        _SESSION_MODULES_SNAPSHOT = {
            name: mod for name, mod in sys.modules.items() if name.split(".")[0] == "ErisPulse"
        }
    erispulse_modules_snapshot = _SESSION_MODULES_SNAPSHOT

    yield

    for path, snapshot in command_dict_snapshots.items():
        _fill(_resolve(command_handler, path), snapshot)
    for path, snapshot in command_set_snapshots.items():
        _fill(_resolve(command_handler, path), snapshot)
    command_handler._gate._usage_locks.clear()
    command_handler._max_name_tokens = max_name_tokens

    for src, (handlers, handler_map) in zip(_EVENT_SOURCES, event_snapshots, strict=True):
        _fill(src.handler.handlers, handlers)
        _fill(src.handler._handler_map, handler_map)

    for name, snapshot in adapter_snapshots.items():
        _fill(adapter_channels[name], snapshot)

    current_erispulse_modules = {
        name for name in sys.modules if name.split(".")[0] == "ErisPulse"
    }
    for name in current_erispulse_modules - set(erispulse_modules_snapshot):
        del sys.modules[name]
    sys.modules.update(erispulse_modules_snapshot)

    _fill(vars(module_sys), module_vars_snapshot)

    # 5.7 逐测试清空事件覆写：persist=True 的覆写（如 ACL / master 限制）会写入
    # 配置树，并在任意 config 事件时经 _reload 重放——仅内存 clear 挡不住
    # "陈旧覆写复活"（曾致 scope 分发测试的命令被前序 ACL 测试的
    # master=True 覆写静默限制为主人专用而随机失败）。delConfig 走脏覆盖层，
    # 读取即时生效、落盘经延迟写合并。
    try:
        from ErisPulse.Core import config as _config_mod
        from ErisPulse.Core.Event import overrides as _overrides_mod

        _overrides_mod.clear()
        _config_mod.config.delConfig("ErisPulse.event.overrides")
    except Exception:
        pass

    # interaction 状态（等待表 / 租约）含运行期对象，恢复无意义，直接清理
    try:
        from ErisPulse.Core.Event import interaction

        interaction.clear()
    except Exception:
        pass
