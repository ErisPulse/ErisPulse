"""
严格模式 (StrictModeManager) 单元测试

覆盖三个级别（宽松/跳过/致命）的违规处置、豁免清单、
致命违规的收集与统一报告。
"""

import pytest

from ErisPulse.loaders.strict import (
    StrictModeError,
    StrictModeLevel,
    StrictModeManager,
    Violation,
)

# ==================== decide：未继承基类场景 ====================


class TestStrictModeDecide:
    """decide() 用于"未继承基类"这类可容忍/可拒绝的违规"""

    def test_lenient_tolerates_non_base_class(self):
        # Level 0：容忍，返回 False（继续加载）
        mgr = StrictModeManager(level=0)
        assert mgr.decide("Foo", "module", "not_base_class") is False
        assert mgr.has_fatal_violations() is False

    def test_skip_rejects_non_base_class(self):
        # Level 1（默认）：拒绝，返回 True（跳过）
        mgr = StrictModeManager(level=1)
        assert mgr.decide("Foo", "module", "not_base_class") is True
        # Level 1 不收集致命违规
        assert mgr.has_fatal_violations() is False

    def test_fatal_rejects_and_records_non_base_class(self):
        # Level 2：拒绝，返回 True，并记录致命违规
        mgr = StrictModeManager(level=2)
        assert mgr.decide("Foo", "module", "not_base_class") is True
        assert mgr.has_fatal_violations() is True
        assert len(mgr.violations) == 1
        assert mgr.violations[0].reason == "not_base_class"

    def test_exempted_component_is_tolerated_even_at_fatal(self):
        # 豁免清单：即使致命级别也容忍
        mgr = StrictModeManager(
            level=2,
            exceptions={"modules": ["Legacy"], "adapters": []},
        )
        assert mgr.decide("Legacy", "module", "not_base_class") is False
        assert mgr.has_fatal_violations() is False

    def test_exempted_adapter_is_tolerated(self):
        mgr = StrictModeManager(
            level=2,
            exceptions={"modules": [], "adapters": ["OldAdapter"]},
        )
        assert mgr.decide("OldAdapter", "adapter", "not_base_class") is False

    def test_default_level_is_lenient(self):
        # 默认应为 0（宽松）
        mgr = StrictModeManager()
        assert mgr.level == 0
        assert mgr.level == int(StrictModeLevel.LENIENT)


# ==================== record_failure：异常类失败场景 ====================


class TestStrictModeRecordFailure:
    """record_failure() 用于异常类失败，仅致命级别收集"""

    def test_record_failure_silent_at_skip_level(self):
        # Level 1：不记录
        mgr = StrictModeManager(level=1)
        mgr.record_failure("Foo", "module", "load_failed", detail="boom")
        assert mgr.has_fatal_violations() is False

    def test_record_failure_collects_at_fatal_level(self):
        mgr = StrictModeManager(level=2)
        mgr.record_failure("Foo", "module", "load_failed", detail="boom")
        assert mgr.has_fatal_violations() is True
        v = mgr.violations[0]
        assert v.name == "Foo"
        assert v.reason == "load_failed"
        assert v.detail == "boom"

    def test_record_failure_respects_exemption(self):
        mgr = StrictModeManager(
            level=2, exceptions={"modules": ["Exempt"], "adapters": []}
        )
        mgr.record_failure("Exempt", "module", "load_failed")
        assert mgr.has_fatal_violations() is False


# ==================== 跨加载器收集（共享实例） ====================


class TestStrictModeSharedCollection:
    """同一 manager 实例应能收集来自不同组件类型的违规"""

    def test_collects_module_and_adapter_violations_together(self):
        mgr = StrictModeManager(level=2)
        mgr.decide("BadModule", "module", "not_base_class")
        mgr.record_failure("BadAdapter", "adapter", "load_failed", detail="x")
        assert len(mgr.violations) == 2
        assert mgr.has_fatal_violations() is True


# ==================== rejections：与级别无关的拒绝追踪 ====================


class TestStrictModeRejections:
    """rejections 在所有级别都记录被拒绝/跳过的组件，用于摘要展示"""

    def test_decide_rejection_tracked_at_skip_level(self):
        # Level 1（默认）拒绝也应进入 rejections
        mgr = StrictModeManager(level=1)
        mgr.decide("BadMod", "module", "not_base_class")
        assert len(mgr.rejections) == 1
        assert mgr.rejections[0].name == "BadMod"
        # 但不进入致命 violations
        assert mgr.has_fatal_violations() is False

    def test_decide_rejection_tracked_at_fatal_level(self):
        mgr = StrictModeManager(level=2)
        mgr.decide("BadMod", "module", "not_base_class")
        # 同时进入 rejections 和 violations
        assert len(mgr.rejections) == 1
        assert len(mgr.violations) == 1

    def test_record_failure_always_tracked_in_rejections(self):
        # 异常类失败在所有级别都进入 rejections
        mgr = StrictModeManager(level=1)
        mgr.record_failure("CrashMod", "module", "load_failed", detail="boom")
        assert len(mgr.rejections) == 1
        assert mgr.has_fatal_violations() is False  # Level 1 不致命

    def test_exempted_not_in_rejections(self):
        # 豁免组件不应进入 rejections
        mgr = StrictModeManager(
            level=1, exceptions={"modules": ["Legacy"], "adapters": []}
        )
        mgr.decide("Legacy", "module", "not_base_class")
        mgr.record_failure("Legacy", "module", "load_failed")
        assert len(mgr.rejections) == 0

    def test_lenient_tolerated_not_in_rejections(self):
        # Level 0 容忍（未拒绝）不应进入 rejections
        mgr = StrictModeManager(level=0)
        mgr.decide("Foo", "module", "not_base_class")
        assert len(mgr.rejections) == 0


# ==================== raise_if_fatal：检查点 ====================


class TestStrictModeRaiseIfFatal:
    """raise_if_fatal() 在检查点统一报告并抛出"""

    def test_no_raise_when_no_violations(self):
        mgr = StrictModeManager(level=2)
        mgr.raise_if_fatal()  # 不应抛出

    def test_no_raise_at_skip_level_even_with_failures(self):
        mgr = StrictModeManager(level=1)
        mgr.record_failure("Foo", "module", "load_failed")
        mgr.raise_if_fatal()  # Level 1 不抛出

    def test_raise_at_fatal_level_with_full_report(self):
        mgr = StrictModeManager(level=2)
        mgr.decide("BadModule", "module", "not_base_class")
        mgr.record_failure("BadAdapter", "adapter", "load_failed", detail="err")

        with pytest.raises(StrictModeError) as exc_info:
            mgr.raise_if_fatal()

        # 异常携带完整违规清单
        assert len(exc_info.value.violations) == 2
        names = {v.name for v in exc_info.value.violations}
        assert names == {"BadModule", "BadAdapter"}


# ==================== 数据模型 ====================


class TestViolationDataclass:
    def test_violation_fields(self):
        v = Violation("Foo", "module", "load_failed", detail="boom")
        assert v.name == "Foo"
        assert v.component_type == "module"
        assert v.reason == "load_failed"
        assert v.detail == "boom"

    def test_violation_default_detail(self):
        v = Violation("Foo", "adapter", "not_base_class")
        assert v.detail == ""
