"""
内存追踪工具单元测试

验证 runtime.memory 模块的快照采集、增量计算与 TRACE 日志输出。
"""

from unittest.mock import patch

from ErisPulse.runtime import memory


class TestMemorySnapshot:
    """内存快照测试"""

    def test_get_rss_mb_returns_float_or_none(self):
        """get_rss_mb 返回非负 float 或 None"""
        rss = memory.get_rss_mb()
        assert rss is None or rss >= 0

    def test_get_traced_mb_returns_float_or_none(self):
        """get_traced_mb 返回非负 float 或 None"""
        traced = memory.get_traced_mb()
        assert traced is None or traced >= 0

    def test_snapshot_structure(self):
        """snapshot 返回包含约定字段的字典"""
        snap = memory.snapshot("unit_test")
        assert set(snap.keys()) == {
            "label",
            "rss_mb",
            "traced_mb",
            "delta_mb",
        }
        assert snap["label"] == "unit_test"

    def test_snapshot_delta_computed_on_same_label(self):
        """同名标签二次快照应计算 delta（RSS 可采集时）"""
        memory.snapshot("delta_label")
        snap = memory.snapshot("delta_label")
        if snap["rss_mb"] is None:
            # 平台无法采集 RSS（无 psutil 且非 Linux）时，delta 合法为 None
            assert snap["delta_mb"] is None
        else:
            # delta 可能为 0.0，但不应为 None（已有基线）
            assert snap["delta_mb"] is not None

    def test_snapshot_different_label_has_no_delta(self):
        """新标签首次快照 delta 为 None"""
        snap = memory.snapshot("brand_new_label_xyz")
        assert snap["delta_mb"] is None

    def test_log_snapshot_does_not_raise(self):
        """log_snapshot 不应抛出异常"""
        memory.log_snapshot("log_test")

    def test_prev_rss_bounded_by_max_labels(self):
        """动态标签快照不导致 _prev_rss 无界增长"""
        cap = memory._MAX_SNAPSHOT_LABELS
        before = set(memory._prev_rss.keys())
        try:
            with patch("ErisPulse.runtime.memory.get_rss_mb", return_value=100.0):
                for i in range(cap + 50):
                    memory.snapshot(f"dyn_label_{i}")
            assert len(memory._prev_rss) <= cap
        finally:
            # 恢复现场，避免污染其它测试
            for key in list(memory._prev_rss.keys()):
                if key not in before:
                    del memory._prev_rss[key]
