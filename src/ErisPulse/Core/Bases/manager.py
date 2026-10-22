"""
ErisPulse 管理器基类

提供适配器和模块管理器的统一接口定义

{!--< tips >!--}
适配器管理器和模块管理器都应继承此基类以保持接口一致性
{!--< /tips >!--}
"""

from abc import ABC, abstractmethod
from typing import Any, ClassVar


class ManagerBase(ABC):
    """
    管理器基类

    定义适配器和模块管理器的统一接口

    {!--< tips >!--}
    统一方法：
    - register(): 注册类
    - unregister(): 取消注册
    - get(): 获取实例
    - exists(): 检查是否存在
    - enable()/disable(): 启用/禁用
    - is_enabled(): 检查是否启用
    - is_running(): 检查是否运行
    - list_*(): 列出相关项
    - sdk_ref(): 运行时 SDK 引用解析
    {!--< /tips >!--}
    """

    # 显式注入的 SDK 引用（可选覆盖，供测试直赋）；正常路径经 sdk_ref() 懒导入根单例
    _sdk: Any = None

    def sdk_ref(self) -> Any:
        """
        解析运行时 SDK 引用

        显式注入的 ``_sdk`` 优先（测试 / 高级用法直赋）；缺失时懒导入根包
        单例——管理器不再依赖外部接线调用（旧 ``set_sdk_ref`` 从未被生产
        链路调用，导致热重载 / 依赖通知在真实部署中静默失效）。

        :return: SDK 实例
        """
        sdk = self._sdk
        if sdk is not None:
            return sdk
        from ... import sdk as root_sdk

        return root_sdk

    # ==================== 共享工具 ====================

    # 弃用参数告警去重集合；(owner, old) 键已含管理器类名，共享一份即可保持"每处仅告警一次"
    _DEPRECATED_KWARG_WARNED: ClassVar[set[tuple[str, str]]] = set()

    @staticmethod
    def _warn_deprecated_kwarg(owner: str, old: str, new: str) -> None:
        """
        {!--< internal-use >!--}
        当检测到使用已弃用的旧关键字参数时，记录一次弃用日志并说明迁移方式

        :param owner: 所属方法名（如 "ModuleManager.get"）
        :param old: 已弃用的旧参数名
        :param new: 推荐使用的新参数名
        """
        key = (owner, old)
        if key in ManagerBase._DEPRECATED_KWARG_WARNED:
            return
        ManagerBase._DEPRECATED_KWARG_WARNED.add(key)
        from ..i18n import i18n
        from ..logger import logger

        logger.warning(
            i18n.t(
                "core.deprecated.kwarg",
                owner=owner,
                old=old,
                new=new,
            )
        )

    @staticmethod
    def _is_subclass(klass: type, base_cls: type) -> bool:
        # 安全 issubclass：klass 非类型时不抛 TypeError；跨导入路径重载的同名类按 MRO 名字比对兜底
        try:
            if issubclass(klass, base_cls):
                return True
        except TypeError:
            pass
        if base_cls.__name__ == klass.__name__:
            return False
        for parent in klass.__mro__:
            if (
                parent.__name__ == base_cls.__name__
                and parent.__module__ == base_cls.__module__
            ):
                return True
        return False

    @staticmethod
    def _shutdown_timeout() -> float:
        """
        {!--< internal-use >!--}
        读取组件优雅收尾（on_unload / shutdown）的超时（秒）

        复用 ``ErisPulse.framework.uninit_timeout`` 配置（反初始化流程的统一
        超时预算，整体仍有 uninit 的 wait_for 兜底）；未配置或非法时回退常量默认值。

        :return: 超时秒数（>0）
        """
        from ...runtime import get_framework_config
        from ..constants import DEFAULT_UNINIT_TIMEOUT_SECS

        try:
            value = get_framework_config().get("uninit_timeout")
            if isinstance(value, (int, float)) and value > 0:
                return float(value)
        except Exception:
            pass
        return float(DEFAULT_UNINIT_TIMEOUT_SECS)

    # ==================== 注册与取消注册 ====================

    @abstractmethod
    def register(self, name: str, class_type: type, info: dict | None = None) -> bool:
        """
        注册类

        :param name: 名称
        :param class_type: 类类型
        :param info: 额外信息
        :return: 是否注册成功
        """
        ...

    @abstractmethod
    def unregister(self, name: str) -> bool:
        """
        取消注册

        :param name: 名称
        :return: 是否取消成功
        """
        ...

    # ==================== 实例获取 ====================

    @abstractmethod
    def get(self, name: str) -> Any:
        """
        获取实例

        :param name: 名称
        :return: 实例或 None
        """
        ...

    # ==================== 存在性检查 ====================

    @abstractmethod
    def exists(self, name: str) -> bool:
        """
        检查是否存在（在配置中注册）

        :param name: 名称
        :return: 是否存在
        """
        ...

    # ==================== 启用/禁用管理 ====================

    @abstractmethod
    def is_enabled(self, name: str) -> bool:
        """
        检查是否启用

        :param name: 名称
        :return: 是否启用
        """
        ...

    @abstractmethod
    def enable(self, name: str) -> bool:
        """
        启用

        :param name: 名称
        :return: 是否成功
        """
        ...

    @abstractmethod
    def disable(self, name: str) -> bool:
        """
        禁用

        :param name: 名称
        :return: 是否成功
        """
        ...

    # ==================== 列表方法 ====================

    @abstractmethod
    def list_registered(self) -> list[str]:
        """
        列出所有已注册的项

        :return: 名称列表
        """
        ...

    @abstractmethod
    def list_items(self) -> dict[str, bool]:
        """
        列出所有项及其状态

        :return: {名称: 是否启用} 字典
        """
        ...

    # ==================== 运行状态检查 ====================

    @abstractmethod
    def is_running(self, name: str) -> bool:
        """
        检查项是否正在运行

        对于适配器：检查是否已启动
        对于模块：检查是否已加载

        :param name: 名称
        :return: 是否正在运行
        """
        ...

    @abstractmethod
    def list_running(self) -> list[str]:
        """
        列出所有正在运行的项

        对于适配器：列出所有已启动的适配器
        对于模块：列出所有已加载的模块

        :return: 名称列表
        """
        ...

    # ==================== SDK 引用 ====================

    # 显式注入的 SDK 引用（set_sdk_ref 可选覆盖）；正常路径经 sdk_ref() 懒导入根单例
    _sdk: Any = None

    def sdk_ref(self) -> Any:
        """
        获取 SDK 引用

        优先返回显式注入的引用（set_sdk_ref），未注入时懒导入根 SDK 单例。
        管理器在任何启动流程下都无需手动注入即可获得正确引用。

        :return: SDK 实例
        """
        if self._sdk is not None:
            return self._sdk
        from ... import sdk as root_sdk

        return root_sdk


__all__ = ["ManagerBase"]
