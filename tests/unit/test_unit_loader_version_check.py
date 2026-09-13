"""
加载器运行时版本检查单元测试

测试 min_sdk_version 声明的运行时检查：
版本比较语义、check_min_sdk_version 判定、BaseLoader 共享检查与跳过行为
"""

import logging
from typing import Any

import pytest

from ErisPulse.Core.Bases.module import ModuleMeta
from ErisPulse.loaders.bases.loader import BaseLoader, resolve_min_sdk_version
from ErisPulse.runtime.version import (
    check_min_sdk_version,
    compare_versions,
    parse_version,
)


class TestCompareVersions:
    """compare_versions 版本比较语义（PEP 440 子集，与 CLI 包管理器同口径）"""

    @pytest.mark.parametrize(
        "a,b,expected",
        [
            ("2.8.0", "2.8.0", 0),
            ("2.8.0", "2.8.1", -1),
            ("2.9.0", "2.8.1", 1),
            ("2.8", "2.8.0", 0),  # 段数不足以 0 补齐
            ("2.8.1-dev.0", "2.8.1", -1),  # 预发布低于正式版
            ("2.8.1-dev.0", "2.8.1-dev.1", -1),
            ("2.8.1-dev.0", "2.8.0", 1),
            ("2.8.1-alpha", "2.8.1-beta", -1),
            ("2.8.1-beta", "2.8.1-rc", -1),
            ("2.8.1-dev", "2.8.1-rc", -1),  # dev 最低（正式版 > rc > beta > alpha > dev）
            ("v2.8.1", "2.8.1", 0),  # v 前缀
            ("2.10.0", "2.9.9", 1),  # 多位数段
            ("1.0", "1.0.post1", -1),  # post 段
            ("2.8.1", "2.8.1+local", -1),  # 本地段
            ("1!1.0", "2.0", 1),  # epoch 优先
        ],
    )
    def test_compare(self, a, b, expected):
        result = compare_versions(a, b)
        if expected == 0:
            assert result == 0
        elif expected < 0:
            assert result < 0
        else:
            assert result > 0

    def test_unparseable_degrades_to_string_compare(self):
        # 与 CLI 同口径：无法解析时不抛异常，退化为字符串比较
        assert compare_versions("not-a-version", "2.8.1") != 0
        assert parse_version("not-a-version") is None


class TestCheckMinSdkVersion:
    """check_min_sdk_version 判定逻辑"""

    def test_empty_declaration_passes(self):
        satisfied, _, _, parseable = check_min_sdk_version("")
        assert satisfied is True
        assert parseable is True

    def test_satisfied(self):
        satisfied, current, required, parseable = check_min_sdk_version("0.0.1")
        assert satisfied is True
        assert parseable is True
        assert required == "0.0.1"
        assert current and current != "unknown"

    def test_not_satisfied(self):
        satisfied, current, required, parseable = check_min_sdk_version("999.0.0")
        assert satisfied is False
        assert parseable is True

    def test_unparseable_declaration_passes_with_flag(self):
        satisfied, _, _, parseable = check_min_sdk_version("not-a-version")
        assert satisfied is True  # 无法解析时放行
        assert parseable is False


class TestResolveMinSdkVersion:
    """resolve_min_sdk_version 声明解析优先级（get_meta 优先，类属性回退）"""

    def test_from_meta_instance(self):
        class Module:
            @staticmethod
            def get_meta() -> ModuleMeta:
                return ModuleMeta(min_sdk_version="2.9.0", version="1.0")

        assert resolve_min_sdk_version(Module) == "2.9.0"

    def test_from_meta_dict(self):
        class Module:
            @staticmethod
            def get_meta() -> dict:
                return {"name": "x", "min_sdk_version": "2.9.0"}

        assert resolve_min_sdk_version(Module) == "2.9.0"

    def test_class_attr_fallback(self):
        class Adapter:
            min_sdk_version = "2.8.1"

        assert resolve_min_sdk_version(Adapter) == "2.8.1"

    def test_meta_wins_over_class_attr(self):
        class Module:
            min_sdk_version = "2.8.0"

            @staticmethod
            def get_meta() -> ModuleMeta:
                return ModuleMeta(min_sdk_version="2.9.0")

        assert resolve_min_sdk_version(Module) == "2.9.0"

    def test_no_declaration_returns_none(self):
        class Module:
            pass

        assert resolve_min_sdk_version(Module) is None

    def test_meta_crash_treated_as_undeclared(self, caplog):
        class Module:
            @staticmethod
            def get_meta() -> ModuleMeta:
                raise RuntimeError("boom")

        with caplog.at_level(logging.WARNING):
            assert resolve_min_sdk_version(Module, name="Broken") is None
        assert any("Broken" in r.message for r in caplog.records)


class TestModuleMetaField:
    """ModuleMeta.min_sdk_version 字段序列化"""

    def test_to_dict_includes_declaration(self):
        meta = ModuleMeta(name="x", min_sdk_version="2.8.1")
        assert meta.to_dict()["min_sdk_version"] == "2.8.1"

    def test_to_dict_filters_none(self):
        meta = ModuleMeta(name="x")
        assert "min_sdk_version" not in meta.to_dict()


class TestLoaderSdkVersionCheck:
    """BaseLoader._check_sdk_version 共享检查行为"""

    @pytest.fixture
    def loader(self):
        class _DummyLoader(BaseLoader):
            def _get_entry_point_group(self) -> str:
                return "test"

            async def _process_entry_point(self, *args: Any, **kwargs: Any):
                return {}, [], [], False

        return _DummyLoader(config_prefix="ErisPulse.test")

    def test_no_declaration_passes(self, loader):
        class Module:
            pass

        assert loader._check_sdk_version("TestModule", "module", Module) is True

    def test_satisfied_declaration_passes(self, loader):
        class Module:
            min_sdk_version = "0.0.1"

        assert loader._check_sdk_version("TestModule", "module", Module) is True

    def test_unsatisfied_declaration_rejected(self, loader, monkeypatch, caplog):
        class Module:
            min_sdk_version = "999.0.0"

        recorded = []
        monkeypatch.setattr(
            loader, "_strict", lambda: type(
                "_S", (), {"record_failure": staticmethod(lambda *a, **k: recorded.append((a, k)))}
            )()
        )

        with caplog.at_level(logging.ERROR):
            result = loader._check_sdk_version("TestModule", "module", Module)

        assert result is False
        assert recorded, "拒绝时应向严格模式管理器登记"
        assert any("999.0.0" in r.message for r in caplog.records)

    def test_invalid_declaration_warns_but_passes(self, loader, caplog):
        class Module:
            min_sdk_version = "what-version"

        with caplog.at_level(logging.WARNING):
            result = loader._check_sdk_version("TestModule", "module", Module)

        assert result is True
        assert any("what-version" in r.message for r in caplog.records)
