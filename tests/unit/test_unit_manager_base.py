"""
ManagerBase 共享工具守护测试

module.py 与 adapter.py 曾各自维护逐行相同的工具方法副本（2.11 架构重写
Stage 1 收拢到 ManagerBase）；本文件防止"再复制一份回去"的回归。
"""

import pytest

from ErisPulse.Core.adapter import AdapterManager
from ErisPulse.Core.Bases.manager import ManagerBase
from ErisPulse.Core.module import ModuleManager


@pytest.mark.unit
class TestSharedUtilsDedup:
    """工具方法必须是继承自 ManagerBase 的同一函数对象，不得在子类自带副本"""

    def test_utils_are_inherited_not_duplicated(self):
        assert ModuleManager._is_subclass is ManagerBase._is_subclass
        assert AdapterManager._is_subclass is ManagerBase._is_subclass
        assert ModuleManager._warn_deprecated_kwarg is ManagerBase._warn_deprecated_kwarg
        assert AdapterManager._warn_deprecated_kwarg is ManagerBase._warn_deprecated_kwarg
        assert ModuleManager._shutdown_timeout is ManagerBase._shutdown_timeout
        assert AdapterManager._shutdown_timeout is ManagerBase._shutdown_timeout

    def test_is_subclass_basic_semantics(self):
        assert ManagerBase._is_subclass(bool, int) is True
        assert ManagerBase._is_subclass(int, int) is True
        assert ManagerBase._is_subclass(int, str) is False

    def test_shutdown_timeout_positive(self):
        assert ManagerBase._shutdown_timeout() > 0

    def test_deprecated_kwarg_warned_once(self):
        ManagerBase._DEPRECATED_KWARG_WARNED.clear()
        ManagerBase._warn_deprecated_kwarg("TestOwner.method", "old", "new")
        size_after_first = len(ManagerBase._DEPRECATED_KWARG_WARNED)
        ManagerBase._warn_deprecated_kwarg("TestOwner.method", "old", "new")
        assert size_after_first == 1
        assert len(ManagerBase._DEPRECATED_KWARG_WARNED) == 1
        ManagerBase._DEPRECATED_KWARG_WARNED.clear()

    def test_sdk_ref_lazy_resolution(self):
        """未注入 _sdk 的管理器懒解析根单例；显式注入优先"""
        from ErisPulse import sdk as root_sdk

        assert ModuleManager().sdk_ref() is root_sdk
        assert AdapterManager().sdk_ref() is root_sdk

        class FakeSDK:
            pass

        mgr = ModuleManager()
        mgr._sdk = FakeSDK()
        assert isinstance(mgr.sdk_ref(), FakeSDK)
