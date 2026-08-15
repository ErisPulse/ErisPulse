"""
模块上下文管理单元测试

测试 owner_scope() 上下文管理器、get_current_owner() 与 sdk.context 暴露。
"""

from ErisPulse import sdk
from ErisPulse.runtime.context import get_current_owner, owner_scope


class TestOwnerScope:
    """owner_scope 上下文管理器"""

    def test_scope_sets_and_resets(self):
        """进入 owner_scope 设置 owner，退出自动复位"""
        assert get_current_owner() is None
        with owner_scope("MyModule"):
            assert get_current_owner() == "MyModule"
        assert get_current_owner() is None

    def test_scope_with_none(self):
        """owner=None 清除当前 owner"""
        with owner_scope("A"):
            with owner_scope(None):
                assert get_current_owner() is None

    def test_nested_scope(self):
        """嵌套作用域正确复位"""
        with owner_scope("A"):
            with owner_scope("B"):
                assert get_current_owner() == "B"
            assert get_current_owner() == "A"

    def test_scope_resets_on_exception(self):
        """异常时仍复位 owner"""
        with owner_scope("A"):
            try:
                with owner_scope("B"):
                    raise RuntimeError("boom")
            except RuntimeError:
                pass
            assert get_current_owner() == "A"
        assert get_current_owner() is None


class TestSdkContext:
    """sdk.context 暴露模块上下文管理"""

    def test_sdk_context_exposed(self):
        """sdk.context 指向 runtime.context 子模块"""
        assert sdk.context.__name__ == "ErisPulse.runtime.context"

    def test_sdk_context_owner_scope(self):
        """通过 sdk.context.owner_scope 使用上下文管理"""
        assert sdk.context.get_current_owner() is None
        with sdk.context.owner_scope("SdkMod"):
            assert sdk.context.get_current_owner() == "SdkMod"
        assert sdk.context.get_current_owner() is None
