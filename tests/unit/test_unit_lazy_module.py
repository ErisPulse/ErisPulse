"""
懒加载模块（LazyModule）单元测试

覆盖懒加载包装器的核心行为以及针对动态加载副作用、
内存占用与 GC 的优化点：
- __slots__（无 __dict__）
- _sdk_ref 使用 weakref（避免 SDK <-> LazyModule 循环引用）
- inspect.signature 结果缓存
- 初始化失败后不再自动重试
- _needs_async_init 标志在成功后被清除
"""

import gc
import weakref

import pytest

from ErisPulse.Core.module import ModuleManager
from ErisPulse.loaders.module import LazyModule

# ==================== 测试用模块类 ====================


class _PlainModule:
    """不带 sdk 参数的普通模块"""

    def __init__(self):
        self.value = 42
        self.loaded = False

    def hello(self):
        return "plain"


class _SdkModule:
    """带 sdk 参数的普通模块"""

    def __init__(self, sdk=None):
        self.sdk = sdk
        self.value = 7

    def ping(self):
        return "pong"


class _FailingModule:
    """构造时抛出异常的模块"""

    def __init__(self):
        raise RuntimeError("init boom")


class _AsyncInitModule:
    """__init__ 为协程函数的模块（需要异步初始化）"""

    def __init__(self):  # type: ignore[empty-body]
        ...


# ==================== 辅助函数 ====================


def _make_info(is_base_module: bool = False) -> dict:
    return {"meta": {"name": "demo", "is_base_module": is_base_module}}


def _make_sdk():
    class _SDK:
        pass

    return _SDK()


# ==================== 内存 / GC 优化测试 ====================


class TestLazyModuleMemory:
    """内存与 GC 优化点验证"""

    def test_uses_slots_no_instance_dict(self):
        """LazyModule 使用 __slots__，实例布局上不应包含 __dict__ 描述符"""
        # __slots__ 声明中不包含 __dict__
        assert "__dict__" not in LazyModule.__slots__

        sdk = _make_sdk()
        lm = LazyModule("demo", _PlainModule, sdk, _make_info(), None)
        # 直接通过 object 层访问包装器的 __dict__，绕过 __getattr__ 代理
        with pytest.raises(AttributeError):
            object.__getattribute__(lm, "__dict__")

    def test_sdk_ref_is_weakref_breaking_cycle(self):
        """_sdk_ref 应是 weakref，打破 SDK <-> LazyModule 循环引用"""
        sdk = _make_sdk()
        lm = LazyModule("demo", _PlainModule, sdk, _make_info(), None)

        raw = object.__getattribute__(lm, "_sdk_ref")
        # weakref.ref 的实例类型
        import weakref as _wr

        assert isinstance(raw, _wr.ReferenceType)
        # 解引用后应得到原始 SDK 对象
        assert raw() is sdk

    def test_sdk_not_kept_alive_by_lazy_module(self):
        """LazyModule 不应强引用 SDK：当 SDK 被释放后 weakref 应失效

        注：由于 LazyModule 通常作为 SDK 的属性存在，SDK 强引用 LazyModule；
        这里验证反向引用是弱引用，从而避免循环引用进入分代 GC 的循环检测。
        """
        sdk = _make_sdk()
        lm = LazyModule("demo", _PlainModule, sdk, _make_info(), None)
        sdk_ref = weakref.ref(sdk)

        # 保持对 LazyModule 的引用，释放 SDK
        ref_to_lm = weakref.ref(lm)
        del sdk
        gc.collect()
        # SDK 应当可被回收（无人强引用它）
        assert sdk_ref() is None
        # 但 weakref 内部已失效
        assert object.__getattribute__(lm, "_sdk_ref")() is None
        del lm
        gc.collect()
        assert ref_to_lm() is None

    def test_signature_cached_in_init(self):
        """inspect.signature 结果应在 __init__ 时缓存为 _init_needs_sdk"""
        lm_with_sdk = LazyModule("demo", _SdkModule, _make_sdk(), _make_info(), None)
        assert object.__getattribute__(lm_with_sdk, "_init_needs_sdk") is True

        lm_without_sdk = LazyModule(
            "demo", _PlainModule, _make_sdk(), _make_info(), None
        )
        assert object.__getattribute__(lm_without_sdk, "_init_needs_sdk") is False


# ==================== 行为 / 回归测试 ====================


class TestLazyModuleBehavior:
    """懒加载核心行为与初始化语义"""

    def test_lazy_init_on_first_access(self):
        """首次访问属性时才触发实例化"""
        lm = LazyModule("demo", _PlainModule, _make_sdk(), _make_info(), None)
        assert object.__getattribute__(lm, "_initialized") is False
        assert object.__getattribute__(lm, "_instance") is None

        # 触发初始化
        assert lm.value == 42

        assert object.__getattribute__(lm, "_initialized") is True
        assert object.__getattribute__(lm, "_instance") is not None

    def test_method_access_proxies_to_instance(self):
        lm = LazyModule("demo", _PlainModule, _make_sdk(), _make_info(), None)
        assert lm.hello() == "plain"

    def test_cached_sdk_injected_when_needed(self):
        sdk = _make_sdk()
        lm = LazyModule("demo", _SdkModule, sdk, _make_info(), None)
        # 触发同步初始化
        assert lm.ping() == "pong"
        assert object.__getattribute__(lm, "_instance").sdk is sdk

    def test_setattr_proxies_to_initialized_instance(self):
        lm = LazyModule("demo", _PlainModule, _make_sdk(), _make_info(), None)
        # 先触发初始化
        _ = lm.value
        lm.value = 100
        assert object.__getattribute__(lm, "_instance").value == 100
        assert lm.value == 100

    def test_delattr_proxies_to_initialized_instance(self):
        lm = LazyModule("demo", _PlainModule, _make_sdk(), _make_info(), None)
        _ = lm.value
        del lm.value
        with pytest.raises(AttributeError):
            _ = lm.value

    def test_call_proxies_to_instance(self):
        class Callable:
            def __init__(self):
                self.calls = 0

            def __call__(self, x):
                self.calls += 1
                return x * 2

        lm = LazyModule("demo", Callable, _make_sdk(), _make_info(), None)
        assert lm(5) == 10
        assert object.__getattribute__(lm, "_instance").calls == 1

    def test_repr_before_and_after_init(self):
        lm = LazyModule("demo", _PlainModule, _make_sdk(), _make_info(), None)
        assert "not initialized" in repr(lm)
        _ = lm.value
        assert "not initialized" not in repr(lm)


class TestLazyModuleFailure:
    """失败短路：避免每次属性访问都重新尝试初始化（性能/副作用优化）"""

    def test_failed_module_does_not_retry_on_getattr(self):
        lm = LazyModule("demo", _FailingModule, _make_sdk(), _make_info(), None)
        # 第一次访问触发初始化并失败，应给出明确的 RuntimeError
        with pytest.raises(RuntimeError):
            _ = lm.value

        assert object.__getattribute__(lm, "_init_failed") is True
        assert object.__getattribute__(lm, "_initialized") is False

        # 再次访问应直接抛出 RuntimeError，而不是重新尝试构造
        # （_ensure_initialized 在失败后会立即返回）
        with pytest.raises(RuntimeError):
            _ = lm.value

    def test_ensure_initialized_short_circuits_after_failure(self):
        lm = LazyModule("demo", _FailingModule, _make_sdk(), _make_info(), None)
        # 触发一次失败
        with pytest.raises(RuntimeError):
            _ = lm.value

        # _ensure_initialized 应直接返回，不再重试（不会重抛构造异常）
        lm._ensure_initialized()
        assert object.__getattribute__(lm, "_initialized") is False
        assert object.__getattribute__(lm, "_init_failed") is True


class TestLazyModuleAsyncFlag:
    """_needs_async_init 标志管理"""

    def test_needs_async_init_flag_cleared_on_sync_success(self):
        # 非 BaseModule 且初始化成功，标志应保持 False
        lm = LazyModule("demo", _PlainModule, _make_sdk(), _make_info(), None)
        _ = lm.value
        assert object.__getattribute__(lm, "_needs_async_init") is False


# ==================== 方案 A：get() 透明懒加载集成测试 ====================


class TestManagerLazyTransparency:
    """验证 module.get() / module.XXX 对“已注册未加载”模块返回懒加载代理，
    而非 None / AttributeError，使懒加载对用户透明。"""

    @pytest.fixture
    def manager(self):
        mgr = ModuleManager()
        mgr._modules.clear()
        mgr._module_classes.clear()
        mgr._loaded_modules.clear()
        mgr._module_info.clear()
        mgr._lazy_modules.clear()
        return mgr

    def test_get_returns_lazy_proxy_when_registered_but_not_loaded(self, manager):
        """注册了懒加载代理后，get() 应返回代理而非 None"""
        sdk = _make_sdk()
        lm = LazyModule("demo", _PlainModule, sdk, _make_info(), manager)
        manager.register_lazy("demo", lm)

        result = manager.get("demo")
        assert result is lm

    def test_get_prefers_loaded_instance_over_lazy_proxy(self, manager):
        """模块加载后，get() 应优先返回真实实例"""
        sdk = _make_sdk()
        lm = LazyModule("demo", _PlainModule, sdk, _make_info(), manager)
        manager.register_lazy("demo", lm)

        real_instance = _PlainModule()
        manager._modules["demo"] = real_instance
        manager._loaded_modules.add("demo")

        assert manager.get("demo") is real_instance

    def test_get_returns_none_when_neither_loaded_nor_lazy(self, manager):
        """未注册代理也未加载时仍返回 None"""
        assert manager.get("nonexistent") is None

    def test_getattr_returns_lazy_proxy_transparently(self, manager):
        """module.MyModule 属性访问也应对懒加载透明"""
        sdk = _make_sdk()
        lm = LazyModule("demo", _PlainModule, sdk, _make_info(), manager)
        manager.register_lazy("demo", lm)

        # 属性访问应返回代理（而非抛 AttributeError）
        assert manager.demo is lm

    def test_unregister_lazy_removes_proxy(self, manager):
        """unregister_lazy 后 get() 应恢复为 None"""
        sdk = _make_sdk()
        lm = LazyModule("demo", _PlainModule, sdk, _make_info(), manager)
        manager.register_lazy("demo", lm)
        assert manager.get("demo") is lm

        manager.unregister_lazy("demo")
        assert manager.get("demo") is None

    def test_clear_resets_lazy_modules(self, manager):
        """clear() 应同时清空 _lazy_modules"""
        sdk = _make_sdk()
        manager.register_lazy(
            "demo", LazyModule("demo", _PlainModule, sdk, _make_info(), manager)
        )
        manager.clear()
        assert manager._lazy_modules == {}
        assert manager.get("demo") is None

    def test_accessing_proxy_via_get_triggers_init_once(self, manager):
        """通过 get() 拿到代理后访问属性会触发一次初始化，且 get() 之后返回真实实例"""
        sdk = _make_sdk()
        lm = LazyModule("demo", _PlainModule, sdk, _make_info(), manager)
        manager.register_lazy("demo", lm)

        proxy = manager.get("demo")
        # 访问属性触发同步初始化
        assert proxy.value == 42
        assert object.__getattribute__(lm, "_initialized") is True

    def test_get_does_not_trigger_loading_itself(self, manager):
        """get() 本身不应触发加载（查询无副作用）"""
        sdk = _make_sdk()
        lm = LazyModule("demo", _PlainModule, sdk, _make_info(), manager)
        manager.register_lazy("demo", lm)

        _ = manager.get("demo")
        _ = manager.get("demo")
        # 多次查询不应触发初始化
        assert object.__getattribute__(lm, "_initialized") is False

    @pytest.mark.asyncio
    async def test_basemodule_lazy_init_no_recursion(self, manager):
        """BaseModule 懒加载初始化路径不应因 get() 透明化而递归

        回归保护：_initialize() 中 await manager.load(name) 后会调用
        manager.get(name) 拿回实例。由于 load() 已填充 _modules，
        新的 get() 会优先命中 _modules 返回真实实例，不会回落到
        _lazy_modules 造成递归。
        """
        from ErisPulse.Core.Bases import BaseModule

        class BModule(BaseModule):
            def __init__(self, sdk=None):
                self.sdk = sdk
                self.loaded = False

            async def on_load(self, event):
                self.loaded = True
                return True

            async def on_unload(self, event):
                return True

        # 注册模块类，并创建懒加载代理
        manager.register("bm", BModule)
        sdk = _make_sdk()
        manager.set_sdk_ref(sdk)
        info = {"meta": {"name": "bm", "is_base_module": True}}
        lm = LazyModule("bm", BModule, sdk, info, manager)
        manager.register_lazy("bm", lm)

        # 触发 BaseModule 的异步初始化路径（走 manager.load）
        await lm._initialize()

        # 初始化成功，未发生递归
        assert object.__getattribute__(lm, "_initialized") is True
        # get() 现在返回真实实例（_modules 优先于 _lazy_modules）
        assert isinstance(manager.get("bm"), BModule)
        assert object.__getattribute__(lm, "_instance") is manager.get("bm")


# ==================== 参数命名对齐与兼容层测试 ====================


class TestManagerParamCompatShim:
    """验证管理器主参数对齐基类 name 后，旧关键字参数（module_name/platform）仍可用。"""

    @pytest.fixture
    def manager(self):
        mgr = ModuleManager()
        mgr._modules.clear()
        mgr._module_classes.clear()
        mgr._loaded_modules.clear()
        mgr._module_info.clear()
        mgr._lazy_modules.clear()
        return mgr

    def test_get_accepts_legacy_module_name_kwarg(self, manager):
        sdk = _make_sdk()
        lm = LazyModule("demo", _PlainModule, sdk, _make_info(), manager)
        manager.register_lazy("demo", lm)

        # 新参数名
        assert manager.get(name="demo") is lm
        # 旧关键字参数仍可用（兼容层）
        assert manager.get(module_name="demo") is lm

    def test_exists_accepts_legacy_module_name_kwarg(self, manager):
        manager._module_classes["demo"] = _PlainModule
        assert manager.exists(name="demo") is True
        assert manager.exists(module_name="demo") is True
        assert manager.exists(module_name="missing") is False

    def test_is_loaded_accepts_legacy_module_name_kwarg(self, manager):
        manager._loaded_modules.add("demo")
        assert manager.is_loaded(name="demo") is True
        assert manager.is_loaded(module_name="demo") is True

    def test_register_accepts_legacy_kwargs(self, manager):
        # 位置调用（对齐基类）
        manager.register("a", _PlainModule)
        assert manager.exists("a")

        # 旧关键字参数
        manager.register(module_name="b", module_class=_PlainModule)
        assert manager.exists("b")

    def test_adapter_get_accepts_legacy_platform_kwarg(self):
        """AdapterManager 同样保留 platform 关键字兼容"""
        from ErisPulse.Core.adapter import AdapterManager

        mgr = AdapterManager()
        # 未注册时两种调用都应返回 None / False，不抛 TypeError
        assert mgr.get(name="none") is None
        assert mgr.get(platform="none") is None
        assert mgr.exists(platform="none") is False
        assert mgr.is_running(platform="none") is False
