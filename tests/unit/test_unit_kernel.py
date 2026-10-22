"""
统一编排内核单元测试（runtime/kernel.py）

组合根：加载器构造与注入、协调器惰性创建的唯一权威。
"""

import pytest

from ErisPulse import SDK
from ErisPulse.runtime.kernel import Kernel


@pytest.mark.unit
class TestKernelComposition:
    """组合根：加载器与协调器的唯一组装点"""

    def test_build_loaders_wires_shared_strict_manager(self):
        sdk = SDK()
        kernel = Kernel(sdk)
        adapter_loader, module_loader = kernel.build_loaders()

        assert sdk._adapter_loader is adapter_loader
        assert sdk._module_loader is module_loader
        # 两个加载器共享同一严格模式管理器（跨加载器统一收集违规）
        assert adapter_loader._strict_manager is module_loader._strict_manager

    def test_get_initializer_reuses_kernel_loaders(self):
        sdk = SDK()
        kernel = Kernel(sdk)
        adapter_loader, module_loader = kernel.build_loaders()

        initializer = kernel.get_initializer()
        again = kernel.get_initializer()
        # 协调器每轮新建（init 生命周期一轮一个），但加载器与严格管理器复用
        assert initializer is not again
        assert initializer._adapter_loader is adapter_loader
        assert initializer._module_loader is module_loader
        assert initializer._strict_manager is adapter_loader._strict_manager

    def test_get_initializer_builds_loaders_lazily(self):
        sdk = SDK()
        kernel = Kernel(sdk)
        # 未显式 build 时惰性补建
        initializer = kernel.get_initializer()
        assert sdk._module_loader is initializer._module_loader
        assert sdk._adapter_loader is initializer._adapter_loader

    def test_get_uninitializer_per_call(self):
        sdk = SDK()
        kernel = Kernel(sdk)
        u1 = kernel.get_uninitializer()
        u2 = kernel.get_uninitializer()
        assert u1 is not u2  # 每轮新建
        assert u1._sdk is sdk
