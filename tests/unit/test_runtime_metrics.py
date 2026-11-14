"""进程内指标计数器（runtime.metrics）测试"""

from ErisPulse.runtime import metrics as metrics_module
from ErisPulse.runtime.metrics import MetricsRegistry


def test_inc_and_snapshot_isolation():
    reg = MetricsRegistry()
    reg.inc("events.total")
    reg.inc("events.total", 2)
    reg.inc("events.type.message")
    snap = reg.snapshot()
    assert snap["events.total"] == 3
    assert snap["events.type.message"] == 1
    # 快照是副本：外部修改不影响注册表
    snap["events.total"] = 999
    assert reg.snapshot()["events.total"] == 3


def test_instance_id_env_override(monkeypatch):
    monkeypatch.setenv("ERISPULSE_INSTANCE_ID", "node-a")
    reg = MetricsRegistry()
    assert reg.instance_id == "node-a"


def test_instance_id_random_fallback(monkeypatch):
    monkeypatch.delenv("ERISPULSE_INSTANCE_ID", raising=False)
    reg = MetricsRegistry()
    assert len(reg.instance_id) == 12


def test_uptime_and_prometheus_render():
    reg = MetricsRegistry()
    reg.inc("events.received_total", 7)
    reg.inc("events.type.request", 2)
    text = reg.render_prometheus()
    assert 'erispulse_events_received_total{instance="' in text
    assert "erispulse_events_type_request" in text
    assert "erispulse_uptime_seconds" in text
    assert reg.uptime_seconds >= 0


def test_module_singleton_alive():
    # 模块级单例可自增且 instance_id 稳定
    before = metrics_module.instance_id
    metrics_module.inc("selfcheck")
    assert metrics_module.snapshot().get("selfcheck", 0) >= 1
    assert metrics_module.instance_id == before
