"""
进程内指标计数器（轻量注册表）

为 ``/health`` 与 ``/metrics`` 提供事件量等运行计数。单进程内存态：
不落盘、不跨进程、无锁（计数写入仅发生在事件循环线程）。

{!--< tips >!--}
1. 热路径成本为 dict 一次哈希查找 + 整数自增，可安全用于分发入口
2. 计数器名建议点分分层（``events.total`` / ``events.type.message``），
   ``snapshot()`` 原样返回；``/metrics`` 输出时做 Prometheus 名称净化
3. 实例身份与进程存活时长同源于本模块（``instance_id`` / ``uptime_seconds``）
{!--< /tips >!--}
"""

import os
import time
import uuid

__all__ = ["MetricsRegistry", "metrics"]


class MetricsRegistry:
    """计数器注册表（模块级单例 ``metrics``）"""

    __slots__ = ("_counters", "_instance_id", "_started_monotonic")

    def __init__(self) -> None:
        self._counters: dict[str, int] = {}
        self._started_monotonic: float = time.monotonic()
        # 实例身份：环境变量 ERISPULSE_INSTANCE_ID 优先（多实例部署区分实例），
        # 缺省为本次进程运行随机生成的短 id
        self._instance_id: str = (
            os.environ.get("ERISPULSE_INSTANCE_ID") or uuid.uuid4().hex[:12]
        )

    def inc(self, name: str, amount: int = 1) -> None:
        """
        计数器自增（计数只增不减）

        :param name: 计数器名（建议点分分层）
        :param amount: 自增量（正整数）
        """
        self._counters[name] = self._counters.get(name, 0) + amount

    def snapshot(self) -> dict[str, int]:
        """
        全量计数器快照

        :return: dict 计数器名 → 当前值的副本
        """
        return dict(self._counters)

    @property
    def instance_id(self) -> str:
        """实例身份（环境变量 ERISPULSE_INSTANCE_ID 覆盖优先）"""
        return self._instance_id

    @property
    def uptime_seconds(self) -> float:
        """进程运行时长（秒，基于 monotonic 时钟）"""
        return time.monotonic() - self._started_monotonic

    def render_prometheus(self, prefix: str = "erispulse") -> str:
        """
        渲染 Prometheus 文本格式输出

        计数器名的非 ``[a-zA-Z0-9_]`` 字符替换为下划线；每个计数器输出一行
        ``{prefix}_{净化名} {值}``（带 instance 标签），并附带 uptime gauge。

        :param prefix: 指标名前缀
        :return: str 文本格式内容（不带结尾换行）
        """
        lines: list[str] = []
        instance = self._instance_id
        for name, value in sorted(self._counters.items()):
            safe = name.replace(".", "_").replace("-", "_")
            lines.append(f'{prefix}_{safe}{{instance="{instance}"}} {value}')
        lines.append(
            f'{prefix}_uptime_seconds{{instance="{instance}"}} {self.uptime_seconds:.1f}'
        )
        return "\n".join(lines)


metrics = MetricsRegistry()
