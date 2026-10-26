"""
统一编排内核（组合根）

框架生命周期的唯一组装点：加载器构造与注入、初始化/反初始化协调器的
创建此前散落在 sdk.py 与 sdk_initializer.py 两处，本类将其收拢为单一
权威；SDK 门面（sdk.py）只做薄转发。

{!--< tips >!--}
1. Kernel 持有 SDK 弱归属关系（组合根天然知晓门面），但不反向暴露
2. 加载器与严格模式管理器由 build_loaders() 一次性组装，跨加载器共享
3. 协调器经 get_initializer()/get_uninitializer() 获取，每轮新建（加载器复用）
{!--< /tips >!--}
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..sdk import SDK
    from .sdk_initializer import Initializer, Uninitializer


class Kernel:
    """
    统一编排内核

    组合根：谁创建加载器、谁注入严格模式管理器、协调器从哪里拿依赖——
    这些组装知识只存在于本类，SDK 门面与协调器不再各自为政。
    """

    def __init__(self, sdk_instance: SDK) -> None:
        """
        :param sdk_instance: SDK 门面实例
        """
        self._sdk = sdk_instance
        self._adapter_loader: Any = None
        self._module_loader: Any = None
        self._strict_manager: Any = None
        self._initializer: Any = None
        self._uninitializer: Any = None

    def build_loaders(self) -> tuple[Any, Any]:
        """
        构造适配器/模块加载器并完成全部注入（唯一组装点）

        - 共享同一严格模式管理器：跨加载器统一收集违规、检查点统一报告
        - 加载器引用注入 SDK：热重载（sdk.reload_module / reload_adapter /
          热重载监控）经由 SDK 访问，仅持有在内核内部则 SDK 侧读不到

        :return: (AdapterLoader, ModuleLoader)
        """
        # 懒导入：本模块在 runtime/__init__ 早期被导入，loaders 顶层引入会经
        # lifecycle ↔ runtime.context 形成部分初始化环（实测 ImportError）
        from ..loaders.adapter import AdapterLoader
        from ..loaders.module import ModuleLoader
        from ..loaders.strict import StrictModeManager

        self._adapter_loader = AdapterLoader()
        self._module_loader = ModuleLoader()
        self._strict_manager = StrictModeManager.from_config()
        self._adapter_loader.set_strict_manager(self._strict_manager)
        self._module_loader.set_strict_manager(self._strict_manager)
        # 版本闸门登记器同步传播到本地插件加载器（strict 错误面与安装来源解耦）
        try:
            self._module_loader._plugin_loader.set_strict_recorder(self._strict_manager)
        except Exception:
            pass
        self._sdk._module_loader = self._module_loader
        self._sdk._adapter_loader = self._adapter_loader
        return self._adapter_loader, self._module_loader

    def get_initializer(self) -> Initializer:
        """
        获取初始化协调器（每次调用新建一轮——init 生命周期一轮一个协调器）

        加载器由 build_loaders 组装并跨轮复用；协调器本身不缓存：反初始化会
        清空加载器引用，跨轮复用会拿到携带失效依赖的旧协调器。

        :return: Initializer 实例
        """
        from .sdk_initializer import Initializer

        if self._adapter_loader is None or self._module_loader is None:
            self.build_loaders()
        # 协调器实现经 SDK 解析：SDK.Initializer / Uninitializer 类别名是
        # 文档承诺的既有扩展缝（测试/第三方可替换），Kernel 尊重该缝
        initializer_cls = getattr(self._sdk, "Initializer", Initializer)
        self._initializer = initializer_cls(
            self._sdk,
            adapter_loader=self._adapter_loader,
            module_loader=self._module_loader,
            strict_manager=self._strict_manager,
        )
        return self._initializer

    def get_uninitializer(self) -> Uninitializer:
        """
        获取反初始化协调器（每轮新建，与 get_initializer 同语义）

        :return: Uninitializer 实例
        """
        from .sdk_initializer import Uninitializer

        uninitializer_cls = getattr(self._sdk, "Uninitializer", Uninitializer)
        self._uninitializer = uninitializer_cls(self._sdk)
        return self._uninitializer


__all__ = ["Kernel"]
