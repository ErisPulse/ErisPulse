#!/usr/bin/env python3
"""
ErisPulse 全组件性能基准

覆盖：启动 / 配置 / 事件分发 / 存储 / 发送 DSL / 路由 / 模块系统 / 端到端整体，
共 8 个套件。纯标准库实现（time.perf_counter_ns + statistics），不引入新依赖。

{!--< internal-use >!--}
手动基准脚本（pytest 不会收集本文件：无 test_ 前缀用例函数，且 tests/performance
已被 pytest addopts 忽略）。运行期间所有状态（config.toml / sqlite 数据库 / 日志）
均落在系统临时目录中，绝不触碰仓库真实配置。

用法::

    python tests/performance/benchmark.py                        # 全套件
    python tests/performance/benchmark.py --suite event,config   # 指定套件
    python tests/performance/benchmark.py --quick                # 快速冒烟档
    python tests/performance/benchmark.py --json base.json       # 落盘基线
    python tests/performance/benchmark.py --compare base.json    # 对比旧基线
    python tests/performance/benchmark.py --html report.html     # 生成 HTML 报告
    python tests/performance/benchmark.py --backend mysql        # 存储套件切后端
    python tests/performance/benchmark.py --keep                 # 保留临时工作目录

退出码：无失败项 0；任一基准项失败 1（跳过不算失败）。
{!--< /internal-use >!--}
"""

from __future__ import annotations

import argparse
import asyncio
import inspect
import json
import os
import platform
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"

PASS, FAIL, SKIP = "PASS", "FAIL", "SKIP"
_SUITE_ORDER = ["config", "event", "storage", "send", "router", "module", "overall", "startup"]

# 框架单例（_import_framework() 之后可用）
sdk = None
adapter = None
config = None
module = None
storage = None
lifecycle = None

_WORKDIR: Path | None = None
_results: list[BenchResult] = []
_QUICK = False


# ==================== 统计核心 ====================


@dataclass
class BenchResult:
    """单个基准项的结果与延迟样本（ms）"""

    suite: str
    name: str
    ops_per_sec: float = 0.0
    ops_per_round: int = 1
    rounds: int = 0
    latencies_ms: list[float] = field(default_factory=list)
    note: str = ""
    metric: str = "ops"  # ops=吞吐型；duration=单次耗时型（init / import 等）
    status: str = PASS
    detail: str = ""

    @property
    def mean_ms(self) -> float:
        return statistics.fmean(self.latencies_ms) if self.latencies_ms else 0.0

    def _pct(self, p: float) -> float:
        """线性插值百分位（ms），样本不足时退化为均值"""
        vals = sorted(self.latencies_ms)
        if not vals:
            return 0.0
        if len(vals) == 1:
            return vals[0]
        k = (len(vals) - 1) * p
        lo = int(k)
        hi = min(lo + 1, len(vals) - 1)
        frac = k - lo
        return vals[lo] * (1 - frac) + vals[hi] * frac

    @property
    def p50_ms(self) -> float:
        return self._pct(0.50)

    @property
    def p95_ms(self) -> float:
        return self._pct(0.95)

    @property
    def p99_ms(self) -> float:
        return self._pct(0.99)

    @property
    def min_ms(self) -> float:
        return min(self.latencies_ms) if self.latencies_ms else 0.0

    @property
    def max_ms(self) -> float:
        return max(self.latencies_ms) if self.latencies_ms else 0.0

    def to_json(self) -> dict:
        return {
            "suite": self.suite,
            "name": self.name,
            "status": self.status,
            "metric": self.metric,
            "ops_per_sec": round(self.ops_per_sec, 2),
            "ops_per_round": self.ops_per_round,
            "rounds": self.rounds,
            "mean_ms": round(self.mean_ms, 6),
            "p50_ms": round(self.p50_ms, 6),
            "p95_ms": round(self.p95_ms, 6),
            "p99_ms": round(self.p99_ms, 6),
            "min_ms": round(self.min_ms, 6),
            "max_ms": round(self.max_ms, 6),
            "samples": len(self.latencies_ms),
            "note": self.note,
            "detail": self.detail,
        }


def _record(result: BenchResult) -> None:
    _results.append(result)
    line = f"  [{result.status}] {result.name}"
    if result.status == PASS:
        if result.metric == "duration":
            line += f"  {_fmt_ms(result.p50_ms)}ms/次"
        else:
            line += f"  {_fmt_ops(result.ops_per_sec)} ops/s  avg {_fmt_ms(result.mean_ms)}ms"
        if result.note:
            line += f"   ({result.note})"
    elif result.detail:
        line += f" — {result.detail}"
    print(line)


def _record_fail(suite: str, name: str, err: BaseException) -> None:
    _record(BenchResult(suite=suite, name=name, status=FAIL, detail=repr(err)))


def _record_skip(suite: str, name: str, reason: str) -> None:
    _record(BenchResult(suite=suite, name=name, status=SKIP, detail=reason))


# ---------- 运行器 ----------


async def bench_ops(
    suite: str,
    name: str,
    fn,
    *,
    ops: int,
    rounds: int,
    collect: bool = False,
    note: str = "",
    warmup: int | None = None,
    metric: str = "ops",
) -> None:
    """批量基准：fn 为单次操作（返回值可为协程，自动等待）。

    collect=False 时整轮计时（每轮均值作为延迟样本，避免计时开销污染微基准）；
    collect=True 时逐操作计时，得到真实每操作延迟分布（p50/p95/p99）。
    """
    n_warm = min(ops, 200) if warmup is None else warmup
    for _ in range(n_warm):
        r = fn()
        if inspect.isawaitable(r):
            await r

    round_ms: list[float] = []
    per_op: list[float] = []
    for _ in range(rounds):
        if collect:
            lat = []
            for _ in range(ops):
                t0 = time.perf_counter_ns()
                r = fn()
                if inspect.isawaitable(r):
                    await r
                lat.append((time.perf_counter_ns() - t0) / 1e6)
            per_op.extend(lat)
            round_ms.append(sum(lat))
        else:
            t0 = time.perf_counter_ns()
            for _ in range(ops):
                r = fn()
                if inspect.isawaitable(r):
                    await r
            round_ms.append((time.perf_counter_ns() - t0) / 1e6)

    total_ops = ops * rounds
    total_ms = sum(round_ms)
    samples = per_op or [ms / ops for ms in round_ms]
    _record(
        BenchResult(
            suite=suite,
            name=name,
            ops_per_sec=total_ops / (total_ms / 1000) if total_ms > 0 else 0.0,
            ops_per_round=ops,
            rounds=rounds,
            latencies_ms=samples,
            note=note,
            metric=metric,
        )
    )


async def bench_round(
    suite: str,
    name: str,
    run_round,
    *,
    rounds: int,
    note: str = "",
    metric: str = "ops",
) -> None:
    """自定义基准：run_round()（同步或协程）返回 (ops, elapsed_ms, per_op_ms 或 None)"""
    is_coro = inspect.iscoroutinefunction(run_round)
    total_ops, total_ms = 0, 0.0
    per_op: list[float] = []
    for _ in range(rounds):
        r = run_round()
        ops, elapsed_ms, lat = (await r) if is_coro else r
        total_ops += ops
        total_ms += elapsed_ms
        if lat:
            per_op.extend(lat)
    if not per_op:
        per_op = [total_ms / total_ops] if total_ops else [total_ms]
    _record(
        BenchResult(
            suite=suite,
            name=name,
            ops_per_sec=total_ops / (total_ms / 1000) if total_ms > 0 else 0.0,
            ops_per_round=max(1, total_ops // max(rounds, 1)),
            rounds=rounds,
            latencies_ms=per_op,
            note=note,
            metric=metric,
        )
    )


# ---------- quick 档缩放 ----------


def _sc(ops: int, rounds: int) -> dict:
    """bench_ops 的 ops/rounds 参数（quick 档缩减到约 1/4）"""
    if _QUICK:
        return {"ops": max(5, ops // 4), "rounds": max(2, rounds // 2)}
    return {"ops": ops, "rounds": rounds}


def _sr(rounds: int) -> int:
    """bench_round 的 rounds 参数（quick 档减半）"""
    return max(2, rounds // 2) if _QUICK else rounds


# ==================== 隔离与引导 ====================


def _prepare(args: argparse.Namespace) -> Path:
    """创建临时工作目录并切换（config 路径是 cwd 相对），在任何 ErisPulse 导入之前调用"""
    global _WORKDIR
    workdir = Path(tempfile.mkdtemp(prefix="erispulse_bench_"))
    _WORKDIR = workdir
    os.chdir(workdir)

    cfg_dir = workdir / "config"
    cfg_dir.mkdir(exist_ok=True)
    (cfg_dir / "config.toml").write_text(
        "# ErisPulse 性能基准临时配置（自动生成，可随临时目录一并删除）\n"
        "[bench]\n"
        'hot = "hotvalue"\n'
        "counter = 0\n\n"
        "[bench.section]\n"
        "alpha = 1\n"
        'beta = "x"\n',
        encoding="utf-8",
    )

    os.environ["ERISPULSE_SERVER_AUTO_START"] = "false"  # 禁止 uvicorn 随 sdk.init 启动
    os.environ["ERISPULSE_LOGGER_LEVEL"] = "WARNING"  # 压制控制台日志（EVENT 级=21 < WARNING=30）
    if args.backend != "sqlite":
        os.environ["ERISPULSE_STORAGE_BACKEND"] = args.backend
    return workdir


def _import_framework() -> None:
    global sdk, adapter, config, module, storage, lifecycle
    sys.path.insert(0, str(SRC_ROOT))
    import ErisPulse
    from ErisPulse import sdk as _sdk
    from ErisPulse.Core import adapter as _adapter
    from ErisPulse.Core import config as _config
    from ErisPulse.Core import lifecycle as _lifecycle
    from ErisPulse.Core import module as _module
    from ErisPulse.Core import storage as _storage

    sdk, adapter, config, module, storage, lifecycle = (
        _sdk,
        _adapter,
        _config,
        _module,
        _storage,
        _lifecycle,
    )
    globals()["_EP_VERSION"] = ErisPulse.__version__


# ==================== 通用工具 ====================


def _make_event(
    idx: int,
    *,
    text: str = "bench",
    detail_type: str = "private",
    etype: str = "message",
    platform: str = "bench",
) -> dict:
    return {
        "id": f"bench_{idx}",
        "time": 1712345678,
        "type": etype,
        "detail_type": detail_type,
        "platform": platform,
        "self": {"platform": platform, "user_id": "bot_bench"},
        "user_id": "u1",
        "message": [{"type": "text", "data": {"text": text}}],
        "alt_message": text,
    }


def _reset_bus() -> None:
    """清空全局适配器总线上的处理器/中间件（属性与 tests/performance/conftest.py 一致）"""
    adapter._onebot_handlers.clear()
    adapter._raw_handlers.clear()
    adapter._onebot_middlewares.clear()


def _event_hard_reset() -> None:
    """彻底卸载消息桥并清空事件系统（总线/命令表/挂载标志全部复位，可安全重新挂载）"""
    from ErisPulse.Core.Event import _clear_all_handlers, command

    command._clear_commands()
    _clear_all_handlers()
    _reset_bus()


def _ensure_command_bound() -> None:
    """确保命令分发器已注册且消息桥已挂载到总线（幂等；复位陈旧标志后重绑）"""
    from ErisPulse.Core.Event import command, message

    if message.handler is None:
        return
    for info in message.handler.handlers:
        func = info.get("func")
        if func is not None and "_handle_message" in getattr(func, "__qualname__", ""):
            return
    try:
        command._dispatcher_registered = False
    except AttributeError:
        pass
    command.bind_message_handler(message.handler)


async def _wait_count(seen: list, expected: int, *, timeout: float = 60.0) -> None:
    t0 = time.perf_counter()
    while len(seen) < expected:
        if time.perf_counter() - t0 > timeout:
            raise TimeoutError(f"等待处理器完成超时: {len(seen)}/{expected}")
        await asyncio.sleep(0)


async def _drain_background() -> None:
    """让即发即忘的后台任务有机会收敛，避免退出时悬挂任务告警"""
    for _ in range(20):
        await asyncio.sleep(0)
    await asyncio.sleep(0.05)


# ==================== 套件：config 配置 ====================


async def suite_config(args: argparse.Namespace) -> None:
    """配置系统：热读 / 脏覆盖层 / 写入 / 全量 / 声明式 ConfigClass / 框架配置合成"""
    from dataclasses import dataclass

    from ErisPulse.Core.Bases import BaseAdapter, BaseConfig
    from ErisPulse.runtime.frame_config import get_event_config

    suite = "config"

    # 1. getConfig 热读（缓存命中快路径：RLock + 两次整数比较 + 字典走路径）
    await bench_ops(suite, "getConfig 热读(缓存命中)", lambda: config.getConfig("bench.hot"), **_sc(20000, 5))

    # 2. getConfig 脏覆盖层读（写后立读：脏键扫描 + deepcopy + 深合并）
    for i in range(5):
        config.setConfig(f"bench.dirty.k{i}", i)
    await bench_ops(
        suite, "getConfig 脏覆盖层读", lambda: config.getConfig("bench.dirty.k0"),
        **_sc(5000, 5), note="5 个脏键存在时",
    )

    # 3. setConfig persist=False（脏队列 + 写延迟定时器调度）
    idx = {"i": 0}

    def _set_dirty():
        idx["i"] += 1
        config.setConfig(f"bench.dirty.k{idx['i'] % 7}", idx["i"])

    await bench_ops(suite, "setConfig persist=False", _set_dirty, **_sc(5000, 5))

    # 4. setConfig immediate=True（tomlkit 全文件重解析 + 原子写 + fsync）
    def _set_immediate():
        idx["i"] += 1
        config.setConfig("bench.flush.key", idx["i"], immediate=True)

    await bench_ops(
        suite, "setConfig immediate=True", _set_immediate,
        **_sc(30, 5), warmup=2, note="全文件 tomlkit 重解析+fsync",
    )

    # 5. getAllConfig（全量 deepcopy + 脏键重放）
    await bench_ops(suite, "getAllConfig 全量快照", lambda: config.getAllConfig(), **_sc(300, 5))

    # 6. setConfig + delConfig 往返
    def _del_roundtrip():
        config.setConfig("bench.del.k", 1)
        config.delConfig("bench.del.k")

    await bench_ops(suite, "setConfig+delConfig 往返", _del_roundtrip, **_sc(2000, 5))

    # 7. cfg 属性访问（ConfigClass dataclass 每次访问全量重建 + 逐字段环境变量覆写检查）
    class _CfgAdapter(BaseAdapter):
        async def start(self):
            pass

        async def shutdown(self):
            pass

        async def call_api(self, endpoint: str, **params):
            return {"status": "ok", "retcode": 0}

        @dataclass
        class ConfigClass(BaseConfig):
            """基准适配器配置"""

            name: str = "bench"
            limit: int = 10

    a = _CfgAdapter()
    await bench_ops(suite, "cfg 属性访问(ConfigClass 重建)", lambda: a.cfg.name, **_sc(2000, 5))

    # 8. get_event_config()（整节 deepcopy + 环境变量逐叶遍历，消息热路径上的真实成本）
    await bench_ops(suite, "get_event_config() 合成", lambda: get_event_config(), **_sc(2000, 5))

    config.force_save()  # 清空脏队列并取消延迟写定时器，避免写盘线程干扰后续套件


# ==================== 套件：event 事件分发 ====================


async def suite_event(args: argparse.Namespace) -> None:
    """事件分发：总线直连 / 中间件 / 匹配过滤 / 注册成本 / 消息桥 / 命令 / 洪泛"""
    from ErisPulse.Core.Event import command, message
    from ErisPulse.Core.Event.base import BaseEventHandler

    suite = "event"
    _event_hard_reset()
    eid = {"n": 0}

    def _next_event(**kw) -> dict:
        eid["n"] += 1
        return _make_event(eid["n"], **kw)

    # ---- A. 总线直连（无消息桥，纯 bus 路径）----

    # 1. 单 handler 串行延迟（emit→Task 创建→handler 执行完整往返；dedupe 开启、唯一事件 id）
    seen: list[int] = []

    @adapter.on("message")
    async def _h1(data):
        seen.append(time.perf_counter_ns())

    async def _emit_serial():
        await adapter.emit(_next_event())
        await _wait_count(seen, len(seen) + 1)

    await bench_ops(suite, "总线单 handler 串行延迟", _emit_serial, **_sc(400, 4), collect=True, note="dedupe 开启/唯一 id")

    # 2. 单 handler 洪泛吞吐（gather 1000 事件再等全部完成）
    async def _flood_1000():
        n = 1000
        base = len(seen)
        events = [_next_event() for _ in range(n)]
        t0 = time.perf_counter_ns()
        await asyncio.gather(*[adapter.emit(e) for e in events])
        await _wait_count(seen, base + n)
        return n, (time.perf_counter_ns() - t0) / 1e6, None

    await bench_round(suite, "总线单 handler 洪泛吞吐", _flood_1000, rounds=_sr(4), note="1000 事件/轮")

    seen.clear()
    _reset_bus()

    # 3. 10 handlers/事件 吞吐
    got10: list[int] = []
    for i in range(10):

        @adapter.on("message")
        async def _h10(data, _i=i):
            got10.append(_i)

    async def _flood_500_10():
        n = 500
        base = len(got10)
        events = [_next_event() for _ in range(n)]
        t0 = time.perf_counter_ns()
        await asyncio.gather(*[adapter.emit(e) for e in events])
        await _wait_count(got10, base + n * 10)
        return n, (time.perf_counter_ns() - t0) / 1e6, None

    await bench_round(suite, "总线 10 handlers/事件 吞吐", _flood_500_10, rounds=_sr(4), note="500 事件 × 10 handler")
    got10.clear()
    _reset_bus()

    # 4-5. 中间件链 ×3 / ×5（串行延迟对照）
    for count in (3, 5):

        @adapter.on("message")
        async def _hm(data):
            seen.append(1)

        for i in range(count):

            async def _mw(data, _i=i):
                data[f"mw{_i}"] = True
                return data

            adapter.middleware(_mw)

        async def _emit_mw():
            await adapter.emit(_next_event())
            await _wait_count(seen, len(seen) + 1)

        await bench_ops(suite, f"中间件链 ×{count} 串行延迟", _emit_mw, **_sc(300, 4), collect=True)
        seen.clear()
        _reset_bus()

    # 6. detail_type 过滤成本（10 个带 detail_type 的 handler：每事件每 handler 现场编译 matcher）
    gotdt: list[int] = []
    for i in range(10):

        @adapter.on("message", detail_type="private")
        async def _hdt(data, _i=i):
            gotdt.append(_i)

    async def _emit_dt():
        await adapter.emit(_next_event())
        await _wait_count(gotdt, len(gotdt) + 10)

    await bench_ops(
        suite, "detail_type 过滤 ×10 延迟", _emit_dt,
        **_sc(300, 4), collect=True, note="每事件×10 handler 现场编译 matcher",
    )
    gotdt.clear()
    _reset_bus()

    # 7. handler 注册成本（每次注册触发 O(n log n) 重排；event_type 留空避免向总线挂载包装器）
    for n in (100, 1000):

        def _reg_round(n=n):
            h = BaseEventHandler("")

            async def _noop(data):
                pass

            t0 = time.perf_counter_ns()
            for _ in range(n):
                h.register(_noop)
            return n, (time.perf_counter_ns() - t0) / 1e6, None

        await bench_round(suite, f"handler 注册 ×{n}", _reg_round, rounds=_sr(5), note="含每次注册的列表重排")

    # 8-9. lifecycle.fire 零监听 / 十监听（fire 即发即忘，只计调度成本）
    async def _fire_nobody():
        lifecycle.fire("bench.nobody", {"x": 1})
        await asyncio.sleep(0)

    await bench_ops(suite, "lifecycle.fire 零监听", _fire_nobody, **_sc(20000, 5))

    def _hook(data):
        pass

    lifecycle.on("bench.somebody")(_hook)

    async def _fire_somebody():
        lifecycle.fire("bench.somebody", {"x": 1})
        await asyncio.sleep(0)

    await bench_ops(suite, "lifecycle.fire ×10 监听", _fire_somebody, **_sc(5000, 5), note="即发即忘调度成本")
    lifecycle._hooks.pop("bench.somebody", None)
    await _drain_background()

    # ---- B. 消息桥 + 命令（真实全链路：bus → _process_event → 优先级分组）----
    _ensure_command_bound()
    cmd_done: list[int] = []

    @command("bench", help="基准命令")
    async def _bench_cmd(event):
        cmd_done.append(time.perf_counter_ns())

    # 10. 命令命中（串行延迟）
    async def _cmd_hit():
        await adapter.emit(_next_event(text="/bench 1"))
        await _wait_count(cmd_done, len(cmd_done) + 1)

    await bench_ops(suite, "命令命中串行延迟(/bench)", _cmd_hit, **_sc(400, 4), collect=True, note="命令分发器优先级 100")

    # 11. 命令 miss（非命令消息的前缀扫描成本；无 handler，含 transcript 记录）
    async def _cmd_miss():
        return await adapter.emit(_next_event(text="hello world"))

    await bench_ops(suite, "命令 miss 串行延迟(无命令消息)", _cmd_miss, **_sc(400, 4), collect=True, note="仅命令分发器扫描")

    # 12. 消息桥单 handler（含命令扫描 + transcript 记录，默认配置全链路）
    bridge_seen: list[int] = []

    async def _bridge_h(event):
        bridge_seen.append(time.perf_counter_ns())

    msg_bridge_handle = message.on_message()(_bridge_h)

    async def _bridge_once():
        await adapter.emit(_next_event(text="ping"))
        await _wait_count(bridge_seen, len(bridge_seen) + 1)

    await bench_ops(suite, "消息桥单 handler 串行延迟", _bridge_once, **_sc(400, 4), collect=True, note="含命令扫描+transcript 写")

    # 13. transcript 关闭对照（隔离每消息存储写成本）
    config.setConfig("ErisPulse.transcript.enabled", False)
    try:
        await bench_ops(
            suite, "消息桥单 handler(transcript 关)", _bridge_once,
            **_sc(400, 4), collect=True, note="对照：去掉每消息存储写",
        )
    finally:
        config.setConfig("ErisPulse.transcript.enabled", True)

    # 14. 同优先级 4 handlers（gather + Event 浅拷贝 + 字段合并/冲突检测）
    bridge4: list[int] = []
    handles4 = []
    for i in range(4):

        async def _bh4(event, _i=i):
            bridge4.append(_i)

        handles4.append(message.on_message()(_bh4))

    async def _bridge4_once():
        await adapter.emit(_next_event(text="ping"))
        await _wait_count(bridge4, len(bridge4) + 4)

    await bench_ops(
        suite, "消息桥同优先级 ×4 延迟", _bridge4_once,
        **_sc(300, 4), collect=True, note="gather+浅拷贝+合并",
    )
    for h in handles4:
        message.remove_message_handler(h)
    bridge4.clear()

    # 15. 事件洪泛持续负载（全链路，报每事件 emit→handler 完成延迟分布）
    flood_n = 1500 if args.quick else 5000
    emit_at: dict[str, int] = {}
    fin_at: dict[str, int] = {}

    async def _flood_h(event):
        fin_at[event["id"]] = time.perf_counter_ns()

    flood_handle = message.on_message()(_flood_h)

    async def _flood_full():
        ids = []
        events = []
        for _ in range(flood_n):
            eid["n"] += 1
            ev_id = f"bench_{eid['n']}"
            ids.append(ev_id)
            ev = _make_event(eid["n"], text="flood")
            ev["id"] = ev_id
            events.append(ev)
        emit_at.clear()
        fin_at.clear()
        t0 = time.perf_counter_ns()
        for ev in events:
            emit_at[ev["id"]] = time.perf_counter_ns()
        await asyncio.gather(*[adapter.emit(e) for e in events])
        deadline = time.perf_counter() + 120
        while len(fin_at) < flood_n:
            if time.perf_counter() > deadline:
                raise TimeoutError(f"洪泛未在时限内完成: {len(fin_at)}/{flood_n}")
            await asyncio.sleep(0)
        elapsed = (time.perf_counter_ns() - t0) / 1e6
        lat = [(fin_at[i] - emit_at[i]) / 1e6 for i in ids if i in emit_at and i in fin_at]
        return flood_n, elapsed, lat

    await bench_round(suite, f"事件洪泛全链路 ×{flood_n}", _flood_full, rounds=_sr(2), note="完成延迟含队列排队")
    message.remove_message_handler(flood_handle)

    # ---- 清理 ----
    message.remove_message_handler(msg_bridge_handle)
    _event_hard_reset()
    await _drain_background()
    config.force_save()


# ==================== 套件：storage 存储 ====================


async def suite_storage(args: argparse.Namespace) -> None:
    """存储：KV 异步/同步、批量、查询构建器、事务、ORM（后端由 --backend 决定，默认 sqlite）"""
    from ErisPulse.Core.Bases import Field, Model

    suite = "storage"
    backend = args.backend

    # ---- 预置数据 ----
    seed = {f"bench.k.{i}": {"n": i, "s": f"s{i}"} for i in range(100)}
    await storage.aset_multi(seed)

    del_total = 4000 if args.quick else 20000
    for chunk_start in range(0, del_total, 2000):
        chunk = {f"bench.del.{i}": i for i in range(chunk_start, min(chunk_start + 2000, del_total))}
        await storage.aset_multi(chunk)
    del_cursor = {"i": 0}

    # 1. aset（UPSERT + json.dumps，轮换 100 键）
    set_i = {"i": 0}

    async def _aset():
        set_i["i"] += 1
        await storage.aset(f"bench.k.{set_i['i'] % 100}", {"n": set_i["i"], "s": f"s{set_i['i']}"})

    await bench_ops(suite, f"aset UPSERT [{backend}]", _aset, **_sc(2000, 5), collect=True)

    # 2. aget（按键查询 + json.loads）
    get_i = {"i": 0}

    async def _aget():
        get_i["i"] += 1
        return await storage.aget(f"bench.k.{get_i['i'] % 100}")

    await bench_ops(suite, f"aget 读取 [{backend}]", _aget, **_sc(2000, 5), collect=True)

    # 3. adelete（轮换删除预置键池）
    async def _adelete():
        del_cursor["i"] += 1
        return await storage.adelete(f"bench.del.{del_cursor['i'] % del_total}")

    await bench_ops(suite, f"adelete 删除 [{backend}]", _adelete, **_sc(1000, 4), collect=True)

    # 4-5. 同步 API（AsyncBridge 线程桥往返）
    sync_i = {"i": 0}

    def _sync_set():
        sync_i["i"] += 1
        storage.set(f"bench.k.{sync_i['i'] % 100}", {"n": sync_i["i"]})

    await bench_ops(suite, f"同步 set(线程桥) [{backend}]", _sync_set, **_sc(1000, 4), collect=True)

    await bench_ops(suite, f"同步 get(线程桥) [{backend}]", lambda: storage.get("bench.k.0"), **_sc(1000, 4), collect=True)

    # 6-7. 批量 multi（每次调用 100 键）
    multi_data = {f"bench.k.{i}": {"n": i, "batch": True} for i in range(100)}
    multi_keys = list(multi_data)

    async def _aset_multi():
        return await storage.aset_multi(multi_data)

    await bench_ops(suite, f"aset_multi ×100键 [{backend}]", _aset_multi, **_sc(100, 5), warmup=3, note="单次调用 100 键")

    async def _aget_multi():
        return await storage.aget_multi(multi_keys)

    await bench_ops(suite, f"aget_multi ×100键 [{backend}]", _aget_multi, **_sc(100, 5), warmup=3, note="单次调用 100 键")

    # 8. 查询构建器（自建表 SELECT ... WHERE）
    try:
        await storage.aDropTable("bench_qb")
    except Exception:
        pass
    await storage.aCreateTable("bench_qb", {"id": "INTEGER PRIMARY KEY", "k": "VARCHAR(64)", "v": "TEXT"})
    for start in range(0, 1000, 200):
        rows = [{"id": i, "k": f"k{i}", "v": f"v{i}"} for i in range(start, start + 200)]
        await storage.Table("bench_qb").InsertMulti(rows).aExecute()

    qb_i = {"i": 0}

    async def _qb_select():
        qb_i["i"] += 1
        k = qb_i["i"] % 1000
        return await storage.Table("bench_qb").Select().Where("k = ?", f"k{k}").aExecute()

    await bench_ops(suite, f"查询构建器 SELECT [{backend}]", _qb_select, **_sc(500, 5), collect=True)

    # 9. 事务（每轮一次事务含 20 条写入）
    tx_i = {"i": 0}

    async def _tx_once():
        t0 = time.perf_counter_ns()
        async with storage.atransaction():
            base = tx_i["i"]
            for j in range(20):
                tx_i["i"] += 1
                await storage.aset(f"bench.tx.{base + j}", j)
        return (time.perf_counter_ns() - t0) / 1e6

    await bench_ops(
        suite, f"事务(20 写入/次) [{backend}]", _tx_once,
        **_sc(40, 5), warmup=2, collect=True, metric="duration", note="每次一个事务",
    )

    # 10-13. ORM（create / where.first / count / all）
    class BenchPerfUser(Model):
        id: int = Field(primary_key=True, autoincrement=True)
        name: str = Field(max_length=64)
        age: int = Field(default=0, ge=0)

    try:
        await storage.aDropTable(BenchPerfUser.table_name())
    except Exception:
        pass
    await BenchPerfUser.create_table()
    for i in range(500):
        await BenchPerfUser.create(name=f"u{i}", age=i % 80)

    orm_i = {"i": 0}

    async def _orm_create():
        orm_i["i"] += 1
        return await BenchPerfUser.create(name=f"bench{orm_i['i']}", age=orm_i["i"] % 80)

    await bench_ops(suite, f"ORM create [{backend}]", _orm_create, **_sc(500, 5), collect=True)

    async def _orm_get():
        orm_i["i"] += 1
        pid = (orm_i["i"] % 500) + 1
        return await BenchPerfUser.where(BenchPerfUser.id == pid).first()

    await bench_ops(suite, f"ORM where(id).first [{backend}]", _orm_get, **_sc(1000, 5), collect=True)

    await bench_ops(suite, f"ORM count [{backend}]", BenchPerfUser.count, **_sc(200, 5))

    async def _orm_all():
        return await BenchPerfUser.where().all()

    await bench_ops(suite, f"ORM all(500行) [{backend}]", _orm_all, **_sc(30, 4), warmup=2)


# ==================== 套件：send 发送 DSL ====================


async def suite_send(args: argparse.Namespace) -> None:
    """发送：SendDSL 链构建与完整 hooked 发送路径（mock 传输层，无网络）"""
    from ErisPulse.Core.Bases import BaseAdapter

    suite = "send"

    class _SendBenchAdapter(BaseAdapter):
        async def start(self):
            pass

        async def shutdown(self):
            pass

        async def call_api(self, endpoint: str, **params):
            return {"status": "ok", "retcode": 0, "data": {}, "message_id": "m"}

    a = _SendBenchAdapter()
    a._platform = "bench"

    # 1. DSL 链构建（Build 模式只累积意图不发送：属性解析 + hook 包装 + 意图累积）
    def _chain_build():
        return a.Send.To("user", "1").At("9").Reply("m1").Build().Text("x").Text("y")

    await bench_ops(suite, "SendDSL 链构建(不发送)", _chain_build, **_sc(5000, 5))

    # 2. 完整 hooked 发送（scope 出站检查 + shadow 检查 + transcript + send rules + mock 传输）
    async def _hooked_send():
        return await a.Send.To("user", "1").Text("hi")

    await bench_ops(
        suite, "完整 hooked 发送(mock 传输)", _hooked_send,
        **_sc(1000, 5), collect=True, note="含 scope/transcript/规则包装",
    )


# ==================== 套件：router 路由 ====================


async def suite_router(args: argparse.Namespace) -> None:
    """路由：ASGI 层请求吞吐（httpx ASGITransport，无网络栈）；自定义路由含框架中间件管线"""
    try:
        from httpx import ASGITransport, AsyncClient
    except ImportError:
        _record_skip("router", "ASGI 请求基准", "缺少 httpx（uv sync --extra test 后可用）")
        return

    from ErisPulse.Core.router import RouterManager

    suite = "router"
    mgr = RouterManager()
    group = mgr.group("Bench", "/bench")

    @group.get("/echo")
    async def _echo(request):
        return {"ok": True, "echo": "bench"}

    transport = ASGITransport(app=mgr.app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:

        async def _get_health():
            r = await client.get("/health")
            return r.status_code

        await bench_ops(suite, "GET /health (ASGI)", _get_health, **_sc(500, 5), collect=True)

        async def _get_echo():
            r = await client.get("/bench/echo")
            return r.status_code

        await bench_ops(
            suite, "GET /bench/echo (框架管线)", _get_echo,
            **_sc(500, 5), collect=True, note="含 scope/owner 中间件管线",
        )


# ==================== 套件：module 模块系统 ====================


async def suite_module(args: argparse.Namespace) -> None:
    """模块：跨模块 RPC / 属性访问路径 / 后台任务派发"""
    from ErisPulse.Core.Bases import BaseModule
    from ErisPulse.runtime.tasks import spawn_background

    suite = "module"

    class BenchSvc(BaseModule):
        async def on_load(self, event: dict):
            return True

        async def on_unload(self, event: dict):
            return True

        async def ping(self):
            return True

    module._module_classes["BenchSvc"] = BenchSvc
    await module.load("BenchSvc")

    # 1. 跨模块 RPC（协议化调用：服务校验 + owner 归因 + 超时包装）
    await bench_ops(
        suite, "module.call RPC 往返", lambda: module.call("BenchSvc", "ping"),
        **_sc(2000, 5), collect=True,
    )

    # 2. 已加载模块属性访问（ModuleManager.__getattr__ → 实例路径）
    await bench_ops(suite, "module.<Name>.attr 访问", lambda: module.BenchSvc.ping, **_sc(20000, 5))

    # 3. spawn_background 任务派发（调度 + owner 追踪 + 完成回收）
    async def _noop():
        pass

    async def _spawn_once():
        t = spawn_background(_noop())
        if t is not None:
            await t

    await bench_ops(suite, "spawn_background 派发", _spawn_once, **_sc(2000, 5), collect=True)


# ==================== 套件：overall 端到端整体 ====================


async def suite_overall(args: argparse.Namespace) -> None:
    """整体：命令→存储→出站发送 全链路，以及混合负载"""
    from ErisPulse.Core.Bases import BaseAdapter
    from ErisPulse.Core.Event import command

    suite = "overall"

    class _E2EAdapter(BaseAdapter):
        async def start(self):
            pass

        async def shutdown(self):
            pass

        async def call_api(self, endpoint: str, **params):
            return {"status": "ok", "retcode": 0, "data": {}, "message_id": "m"}

    adapter.register("bench_e2e", _E2EAdapter)
    e2e = adapter.bench_e2e

    done: list[int] = []

    _event_hard_reset()
    _ensure_command_bound()  # 挂载消息桥并绑定命令分发器（上一套件可能已卸载）

    @command("order", help="端到端基准命令")
    async def _order_cmd(event):
        n = event["command"]["args"][0] if event["command"]["args"] else "0"
        await storage.aset(f"bench.order.{n}", {"n": n, "ts": time.time()})
        await e2e.call_api("send_private_msg", user_id="u1", message="ok")
        done.append(time.perf_counter_ns())

    # 1. 端到端全链路（消息事件 → 命令处理 → 存储写入 → 出站发送）
    eid = {"n": 100000}

    async def _e2e_once():
        eid["n"] += 1
        await adapter.emit(_make_event(eid["n"], text=f"/order {eid['n']}"))
        await _wait_count(done, len(done) + 1)

    await bench_ops(
        suite, "端到端 命令→存储→发送", _e2e_once,
        **_sc(300, 4), collect=True, note="emit→命令→aset→call_api",
    )

    # 2. 混合负载（每迭代：20 读 + 2 写配置 + 1 aset + 1 aget + 1 事件 + 1 发送）
    mix_seen: list[int] = []

    @adapter.on("message")
    async def _mix_h(data):
        mix_seen.append(1)

    cfg_i = {"i": 0}

    async def _mix_iter():
        cfg_i["i"] += 1
        i = cfg_i["i"]
        for _j in range(20):
            config.getConfig("bench.hot")
        config.setConfig(f"bench.mix.{i % 3}", i)
        await storage.aset(f"bench.k.{i % 100}", i)
        await storage.aget(f"bench.k.{i % 100}")
        await adapter.emit(_make_event(500000 + i, text="mix"))
        await _wait_count(mix_seen, len(mix_seen) + 1)
        await e2e.call_api("send_private_msg", user_id="u1", message="m")

    await bench_ops(
        suite, "混合负载(读20+写2+存2+事件1+发送1)", _mix_iter,
        **_sc(100, 4), warmup=3, note="单迭代为上述一组操作",
    )

    mix_seen.clear()
    _event_hard_reset()
    await _drain_background()
    config.force_save()


# ==================== 套件：startup 启动 ====================


async def suite_startup(args: argparse.Namespace) -> None:
    """启动：解释器对照 / 冷导入 / sdk.init 空载 / 装载 1 适配器+1 模块 / uninit"""
    suite = "startup"
    cycles = 2 if args.quick else 3

    # 1. 解释器启动对照（python -c pass，父进程墙钟）
    def _py_baseline():
        t0 = time.perf_counter_ns()
        subprocess.run([sys.executable, "-c", "pass"], cwd=str(_WORKDIR), check=True, capture_output=True)
        return 1, (time.perf_counter_ns() - t0) / 1e6, None

    await bench_round(suite, "解释器启动对照(python -c pass)", _py_baseline, rounds=_sr(5), metric="duration")

    # 2. 冷导入 ErisPulse（子进程内计时，首次运行弃掉作为文件缓存预热）
    child_code = "import time; t0 = time.perf_counter(); import ErisPulse; print(time.perf_counter() - t0)"

    def _cold_import():
        proc = subprocess.run(
            [sys.executable, "-c", child_code], cwd=str(_WORKDIR), check=True, capture_output=True, text=True
        )
        return 1, float(proc.stdout.strip().splitlines()[-1]) * 1000, None

    _cold_import()  # 预热文件系统缓存
    await bench_round(suite, "冷导入 ErisPulse(子进程)", _cold_import, rounds=_sr(5), metric="duration")

    # 3-4. sdk.init() 空载 / sdk.uninit()（多个 init→uninit 周期，捕获 init 阶段汇总）
    init_ms: list[float] = []
    uninit_ms: list[float] = []
    complete_payload: dict = {}

    def _on_complete(data=None):
        if isinstance(data, dict):
            complete_payload.update(data)

    lifecycle.on("core.init.complete")(_on_complete)

    # 预热周期：首周期含 fastapi/uvicorn 等惰性导入的一次性成本，不计入统计
    await sdk.init()
    await sdk.uninit()

    for _ in range(cycles):
        t0 = time.perf_counter_ns()
        await sdk.init()
        init_ms.append((time.perf_counter_ns() - t0) / 1e6)
        t1 = time.perf_counter_ns()
        await sdk.uninit()
        uninit_ms.append((time.perf_counter_ns() - t1) / 1e6)

    stages = complete_payload.get("stage_durations") or complete_payload.get("stages")
    init_note = "0 适配器/0 模块，router auto_start 关闭"
    if isinstance(stages, dict) and stages:
        breakdown = ", ".join(f"{k}={v * 1000:.0f}ms" for k, v in stages.items())
        init_note += f"；阶段: {breakdown}"

    _record(
        BenchResult(
            suite=suite, name="sdk.init() 空载", metric="duration",
            ops_per_round=1, rounds=len(init_ms), latencies_ms=list(init_ms), note=init_note,
        )
    )
    _record(
        BenchResult(
            suite=suite, name="sdk.uninit()", metric="duration",
            ops_per_round=1, rounds=len(uninit_ms), latencies_ms=list(uninit_ms),
        )
    )

    # 5. 冷启动 + 装载 1 适配器 + 1 模块（程序化注册，不走 CLI / entry-points）
    from ErisPulse.Core.Bases import BaseAdapter, BaseModule

    class _LoadAdapter(BaseAdapter):
        async def start(self):
            pass

        async def shutdown(self):
            pass

        async def call_api(self, endpoint: str, **params):
            return {"status": "ok", "retcode": 0}

    class _LoadModule(BaseModule):
        async def on_load(self, event: dict):
            return True

        async def on_unload(self, event: dict):
            return True

    t0 = time.perf_counter_ns()
    await sdk.init()
    adapter.register("bench_load", _LoadAdapter)
    module._module_classes["BenchLoadModule"] = _LoadModule
    await module.load("BenchLoadModule")
    load_ms = (time.perf_counter_ns() - t0) / 1e6
    await sdk.uninit()

    _record(
        BenchResult(
            suite=suite, name="启动+装载1适配器+1模块", metric="duration",
            ops_per_round=1, rounds=1, latencies_ms=[load_ms],
            note="init 预热后单次采样：init+register+module.load",
        )
    )


# ==================== 套件注册 ====================

_SUITES = {
    "config": ("config 配置系统", suite_config),
    "event": ("event 事件分发", suite_event),
    "storage": ("storage 存储", suite_storage),
    "send": ("send 发送 DSL", suite_send),
    "router": ("router 路由", suite_router),
    "module": ("module 模块系统", suite_module),
    "overall": ("overall 端到端整体", suite_overall),
    "startup": ("startup 启动", suite_startup),
}


# ==================== 输出与报告 ====================


def _dw(text: str) -> int:
    """显示宽度（CJK 全角计 2）"""
    return sum(2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1 for ch in text)


def _pad(text: str, width: int) -> str:
    return text + " " * max(0, width - _dw(text))


def _fmt_ops(v: float) -> str:
    if v >= 1_000_000:
        return f"{v / 1_000_000:,.2f}M"
    return f"{v:,.0f}"


def _fmt_ms(v: float) -> str:
    if v >= 100:
        return f"{v:,.1f}"
    if v >= 1:
        return f"{v:.2f}"
    if v >= 0.01:
        return f"{v:.3f}"
    return f"{v:.4f}"


def _pct_label(delta: float) -> str:
    return f"{delta:+.1f}%"


def _env_meta(args: argparse.Namespace) -> dict:
    gil = "enabled"
    try:
        if hasattr(sys, "_is_gil_enabled"):
            gil = "enabled" if sys._is_gil_enabled() else "disabled (free-threaded)"
    except Exception:
        pass
    return {
        "timestamp": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "python": sys.version.split()[0],
        "implementation": platform.python_implementation(),
        "platform": f"{platform.system()} {platform.release()} ({platform.machine()})",
        "cpu": platform.processor() or platform.machine(),
        "cpu_count": os.cpu_count(),
        "gil": gil,
        "erispulse": globals().get("_EP_VERSION", "unknown"),
        "backend": args.backend,
        "quick": args.quick,
    }


def _print_header(meta: dict) -> None:
    print("=" * 78)
    print("ErisPulse 全组件性能基准")
    print("=" * 78)
    print(f"  ErisPulse : {meta['erispulse']}   Python : {meta['python']} ({meta['implementation']})")
    print(f"  平台      : {meta['platform']}   CPU×{meta['cpu_count']}   GIL: {meta['gil']}")
    print(f"  存储后端  : {meta['backend']}   quick 档: {'是' if meta['quick'] else '否'}")
    print(f"  时间      : {meta['timestamp']}")
    print("=" * 78)


def _print_summary() -> None:
    print("\n" + "=" * 78)
    print("结果汇总")
    print("=" * 78)
    cur_suite = None
    for r in _results:
        if r.suite != cur_suite:
            cur_suite = r.suite
            title = _SUITES[cur_suite][0] if cur_suite in _SUITES else cur_suite
            print(f"\n── {title} " + "─" * max(4, 56 - _dw(title)))
            print(
                _pad("  基准项", 50)
                + _pad("吞吐/速率", 12)
                + _pad("avg", 9)
                + _pad("p50", 9)
                + _pad("p95", 9)
                + "p99"
            )
        if r.status != PASS:
            print(f"  [{r.status}] {r.name}" + (f" — {r.detail}" if r.detail else ""))
            continue
        thr = "—" if r.metric == "duration" else _fmt_ops(r.ops_per_sec)
        print(
            _pad(f"  {r.name}", 50)
            + _pad(thr, 12)
            + _pad(_fmt_ms(r.mean_ms), 9)
            + _pad(_fmt_ms(r.p50_ms), 9)
            + _pad(_fmt_ms(r.p95_ms), 9)
            + _fmt_ms(r.p99_ms)
        )
    total = len(_results)
    passed = sum(1 for r in _results if r.status == PASS)
    failed = sum(1 for r in _results if r.status == FAIL)
    skipped = total - passed - failed
    tail = f"== 结果: {passed}/{total} 完成"
    if failed:
        tail += f"，{failed} 失败"
    if skipped:
        tail += f"，{skipped} 跳过"
    print("\n" + tail + " ==")


def _write_json(path: Path, meta: dict) -> None:
    payload = {"meta": meta, "results": [r.to_json() for r in _results]}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n基线已写入: {path}")


def _compare(base_path: Path) -> None:
    base_payload = json.loads(base_path.read_text(encoding="utf-8"))
    base = {(r["suite"], r["name"]): r for r in base_payload.get("results", [])}
    print("\n" + "=" * 78)
    print(f"基线对比（vs {base_path.name}，吞吐变化 ≥±5% 视为显著）")
    print("=" * 78)
    print(_pad("  基准项", 50) + _pad("基线 ops/s", 14) + _pad("当前 ops/s", 14) + _pad("吞吐变化", 10) + "p50 变化")
    regress = improve = 0
    for r in _results:
        if r.status != PASS or r.metric == "duration":
            continue
        b = base.get((r.suite, r.name))
        if not b:
            continue
        b_thr = b.get("ops_per_sec", 0)
        delta_thr = (r.ops_per_sec - b_thr) / b_thr * 100 if b_thr else 0.0
        b_p50 = b.get("p50_ms", 0)
        delta_p50 = (r.p50_ms - b_p50) / b_p50 * 100 if b_p50 else 0.0
        if delta_thr <= -5:
            regress += 1
        elif delta_thr >= 5:
            improve += 1
        print(
            _pad(f"  {r.name}", 50)
            + _pad(_fmt_ops(b_thr), 14)
            + _pad(_fmt_ops(r.ops_per_sec), 14)
            + _pad(_pct_label(delta_thr), 10)
            + _pct_label(delta_p50)
        )
    print(f"\n== 对比: {improve} 项提升，{regress} 项回归 ==")


# ---------- HTML 报告（日系清新风） ----------

_BOTANICAL_SVGS = [
    '<path d="M60 112 C 60 84, 60 52, 60 18" />'
    '<path d="M60 84 C 44 78, 36 64, 39 50 C 53 55, 59 68, 60 84" />'
    '<path d="M60 56 C 76 50, 84 36, 81 22 C 67 27, 61 40, 60 56" />',
    '<path d="M60 112 C 58 86, 64 56, 58 20" />'
    '<path d="M60 92 C 74 84, 80 70, 76 56 C 63 62, 58 76, 60 92" />'
    '<path d="M59 60 C 45 52, 40 38, 44 26 C 56 32, 60 46, 59 60" />',
    '<path d="M60 112 C 62 82, 56 54, 62 22" />'
    '<path d="M61 78 C 48 70, 44 56, 48 44 C 59 50, 62 64, 61 78" />'
    '<path d="M60 46 C 72 38, 76 26, 72 16 C 62 22, 58 34, 60 46" />',
]


def _render_html(meta: dict) -> str:
    def esc(s: str) -> str:
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def rows_for(suite: str) -> str:
        out = []
        for r in _results:
            if r.suite != suite:
                continue
            if r.status != PASS:
                badge = "失败" if r.status == FAIL else "跳过"
                out.append(
                    f'<tr class="dim"><td>{esc(r.name)}</td>'
                    f'<td colspan="5"><span class="pill">{badge}</span> {esc(r.detail)}</td></tr>'
                )
                continue
            thr = "—" if r.metric == "duration" else _fmt_ops(r.ops_per_sec) + " ops/s"
            note = f'<span class="note">{esc(r.note)}</span>' if r.note else ""
            out.append(
                f"<tr><td>{esc(r.name)}{note}</td>"
                f'<td class="num">{thr}</td>'
                f'<td class="num">{_fmt_ms(r.mean_ms)}</td>'
                f'<td class="num">{_fmt_ms(r.p50_ms)}</td>'
                f'<td class="num">{_fmt_ms(r.p95_ms)}</td>'
                f'<td class="num">{_fmt_ms(r.p99_ms)}</td></tr>'
            )
        return "\n".join(out)

    sections = []
    for idx, sname in enumerate(_SUITE_ORDER):
        if not any(r.suite == sname for r in _results):
            continue
        title = _SUITES[sname][0].split(" ", 1)[-1]
        flip = ' style="transform:scaleX(-1)"' if idx % 2 else ""
        sections.append(f"""
  <section>
    <div class="branch" aria-hidden="true"{flip}>
      <svg viewBox="0 0 120 120" fill="none" stroke="#98d8c8" stroke-width="1" stroke-linecap="round" opacity="0.65">
        {_BOTANICAL_SVGS[idx % len(_BOTANICAL_SVGS)]}
      </svg>
    </div>
    <h2>{esc(title)}</h2>
    <div class="card">
      <table>
        <thead><tr><th>基准项</th><th>吞吐</th><th>avg (ms)</th><th>p50 (ms)</th><th>p95 (ms)</th><th>p99 (ms)</th></tr></thead>
        <tbody>
{rows_for(sname)}
        </tbody>
      </table>
    </div>
  </section>""")

    quick_note = "快速档（样本数约为主档的 1/4，仅用于冒烟对照）" if meta["quick"] else "完整档"
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ErisPulse 性能基准报告</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: #fafaf8; color: #4a5568;
    font-family: "Helvetica Neue", "Segoe UI", "Hiragino Sans", "Yu Gothic UI", "Noto Sans CJK SC", sans-serif;
    font-weight: 300; line-height: 1.7; letter-spacing: 0.01em;
  }}
  .wrap {{ max-width: 880px; margin: 0 auto; padding: 96px 32px 64px; }}
  h1 {{ font-weight: 200; font-size: 2.6rem; letter-spacing: 0.06em; }}
  .sub {{ color: #6b7280; font-size: 0.95rem; margin-top: 12px; }}
  .meta {{
    margin-top: 56px; background: #ffffff; border: 1px solid rgba(212, 212, 207, 0.4);
    border-radius: 16px; padding: 32px 36px;
  }}
  .meta dl {{ display: grid; grid-template-columns: auto 1fr; gap: 8px 28px; font-size: 0.9rem; }}
  .meta dt {{ color: #6b7280; }}
  section {{ padding: 88px 0 0; position: relative; }}
  .branch {{ position: absolute; right: 8px; top: 64px; width: 96px; height: 96px; }}
  .branch svg {{ width: 100%; height: 100%; transition: opacity 0.5s ease-in-out; }}
  h2 {{
    font-weight: 200; font-size: 1.45rem; letter-spacing: 0.05em; color: #4a5568;
    padding-bottom: 14px; border-bottom: 1px solid rgba(212, 212, 207, 0.5); max-width: 70%;
  }}
  .card {{
    margin-top: 28px; background: #ffffff; border: 1px solid rgba(212, 212, 207, 0.3);
    border-radius: 16px; padding: 12px 28px;
  }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.88rem; }}
  th {{
    text-align: left; font-weight: 300; color: #6b7280; letter-spacing: 0.05em;
    padding: 14px 10px 10px; border-bottom: 1px solid rgba(212, 212, 207, 0.4);
  }}
  td {{ padding: 13px 10px; border-bottom: 1px solid rgba(212, 212, 207, 0.25); color: #4a5568; }}
  tbody tr {{ transition: background-color 0.5s ease-in-out; }}
  tbody tr:hover {{ background-color: rgba(152, 216, 200, 0.08); }}
  tbody tr:last-child td {{ border-bottom: none; }}
  .num {{ font-variant-numeric: tabular-nums; }}
  .note {{ display: block; color: #6b7280; font-size: 0.78rem; }}
  .pill {{
    display: inline-block; border: 1px solid rgba(212, 212, 207, 0.5); border-radius: 999px;
    padding: 1px 12px; font-size: 0.78rem; color: #6b7280;
  }}
  .dim td {{ color: #6b7280; }}
  footer {{ margin-top: 96px; color: #6b7280; font-size: 0.82rem; text-align: center; }}
  @media (prefers-reduced-motion: reduce) {{
    * {{ transition: none !important; }}
  }}
  @media (max-width: 640px) {{
    .wrap {{ padding: 64px 20px 48px; }}
    h1 {{ font-size: 2rem; }}
    .card {{ padding: 8px 14px; overflow-x: auto; }}
    th:nth-child(n+4), td:nth-child(n+4) {{ display: none; }}
  }}
</style>
</head>
<body>
  <div class="wrap">
    <h1>ErisPulse 性能基准</h1>
    <p class="sub">{esc(meta['erispulse'])} · {quick_note} · 生成于 {esc(meta['timestamp'])}</p>
    <div class="meta">
      <dl>
        <dt>Python</dt><dd>{esc(meta['python'])}（{esc(meta['implementation'])}，GIL {esc(meta['gil'])}）</dd>
        <dt>平台</dt><dd>{esc(meta['platform'])} · CPU × {meta['cpu_count']} · {esc(meta['cpu'])}</dd>
        <dt>存储后端</dt><dd>{esc(meta['backend'])}</dd>
        <dt>说明</dt><dd>吞吐列为主指标（越高越好）；avg / p50 / p95 / p99 为单操作毫秒延迟（越低越好）。
        事件分发项均在默认配置下测量（含每消息 transcript 记录与命令前缀扫描），临时目录隔离运行。</dd>
      </dl>
    </div>
    {''.join(sections)}
    <footer>— 数据来自本地基准运行，仅供相对比较 · ErisPulse —</footer>
  </div>
</body>
</html>"""


def _write_html(path: Path, meta: dict) -> None:
    path.write_text(_render_html(meta), encoding="utf-8")
    print(f"HTML 报告已写入: {path}")


# ==================== 入口 ====================


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ErisPulse 全组件性能基准")
    parser.add_argument(
        "--suite", default="all",
        help="逗号分隔的套件名: " + ",".join(_SUITE_ORDER) + "（默认 all）",
    )
    parser.add_argument("--json", default="", help="将基线结果写入 JSON 文件")
    parser.add_argument("--compare", default="", help="与旧基线 JSON 对比（差值百分比）")
    parser.add_argument("--html", default="", help="生成 HTML 报告")
    parser.add_argument("--quick", action="store_true", help="快速档（样本数约 1/4，用于冒烟）")
    parser.add_argument("--backend", default="sqlite", choices=["sqlite", "mysql", "postgres"], help="存储套件后端")
    parser.add_argument("--keep", action="store_true", help="保留临时工作目录（排查用）")
    return parser.parse_args()


async def _run(args: argparse.Namespace) -> None:
    global _QUICK
    _QUICK = args.quick

    selected = list(_SUITE_ORDER)
    if args.suite != "all":
        selected = [s.strip() for s in args.suite.split(",") if s.strip()]
        for s in selected:
            if s not in _SUITES:
                raise SystemExit(f"未知套件: {s}（可选: {','.join(_SUITE_ORDER)}）")

    for sname in selected:
        title, fn = _SUITES[sname]
        print(f"\n──── {title} " + "─" * max(4, 58 - _dw(title)))
        try:
            await fn(args)
        except Exception as exc:  # 套件级兜底：记录失败并继续后续套件
            _record_fail(sname, "（套件异常中止）", exc)


def main() -> int:
    args = _parse_args()
    workdir = _prepare(args)
    try:
        _import_framework()
        meta = _env_meta(args)
        _print_header(meta)
        asyncio.run(_run(args))
        _print_summary()
        if args.json:
            _write_json(Path(args.json), meta)
        if args.compare:
            _compare(Path(args.compare))
        if args.html:
            _write_html(Path(args.html), meta)
        failed = sum(1 for r in _results if r.status == FAIL)
        return 1 if failed else 0
    finally:
        if args.keep:
            print(f"\n临时工作目录已保留: {workdir}")
        else:
            shutil.rmtree(workdir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
