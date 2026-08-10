"""
ErisPulse 模块基础模块

提供模块基类定义和标准接口
"""

from abc import ABC, abstractmethod
from typing import Any, TypedDict

from ...loaders.strategy import ModuleLoadStrategy
from ..config import config as config_mgr
from ..constants import DEFAULT_LAZY_LOADING_ENABLED, DEFAULT_MODULE_PRIORITY
from ..i18n import i18n
from ..logger import logger


class ModuleEvent(TypedDict):
    """
    on_load / on_unload 事件数据

    :ivar module_name: str 模块名称
    """
    module_name: str


class BaseModule(ABC):
    """
    模块基类

    提供模块加载和卸载的标准接口，同时支持声明式配置管理。

    {!--< tips >!--}
    1. 必须实现 on_load / on_unload 方法
    2. 可通过 ConfigClass 声明配置类，框架自动管理配置
    3. 通过 self.cfg 访问类型安全的配置对象（实时读取）
    4. 可覆写 on_config_update() 响应配置热更新
    5. 可通过 I18nClass 声明翻译键集合，框架自动注册到 i18n 系统
    {!--< /tips >!--}
    """

    ConfigClass: type | None = None
    I18nClass: type | None = None

    @staticmethod
    def get_load_strategy() -> ModuleLoadStrategy | dict[str, Any]:
        """
        获取模块加载策略

        支持返回 ModuleLoadStrategy 对象或字典
        所有属性统一处理，没有任何预定义字段

        :return: 加载策略对象或字典

        {!--< tips >!--}
        常用配置项：
        - lazy_load: bool, 是否懒加载（默认 True）
        - priority: int, 加载优先级（默认 0，数值越大优先级越高）

        使用方式：
        >>> class MyModule(BaseModule):
        ...     @staticmethod
        ...     def get_load_strategy() -> ModuleLoadStrategy:
        ...         return ModuleLoadStrategy(
        ...             lazy_load=False,
        ...             priority=100
        ...         )

        或使用字典：
        >>> class MyModule(BaseModule):
        ...     @staticmethod
        ...     def get_load_strategy() -> dict:
        ...         return {
        ...             "lazy_load": False,
        ...             "priority": 100
        ...         }
        {!--< /tips >!--}
        """
        return ModuleLoadStrategy(
            lazy_load=DEFAULT_LAZY_LOADING_ENABLED,
            priority=DEFAULT_MODULE_PRIORITY,
        )

    # @staticmethod
    # def should_eager_load() -> bool:
    #     """
    #     模块是否应该在启动时加载
    #     默认为False(即懒加载)

    #     兼容方法，实际调用 get_load_strategy()

    #     :return: 是否应该在启动时加载

    #     {!--< tips >!--}
    #     旧版方法，建议使用 get_load_strategy() 替代
    #     {!--< /tips >!--}
    #     """
    #     strategy = BaseModule.get_load_strategy()
    #     if isinstance(strategy, dict):
    #         return not strategy.get('lazy_load', True)
    #     return not (strategy.lazy_load if 'lazy_load' in strategy else True)

    @abstractmethod
    async def on_load(self, event: dict[str, Any]) -> bool:
        """
        当模块被加载时调用

        :param event: 事件内容
        :return: 处理结果

        {!--< tips >!--}
        其中，event事件内容为:
            `{ "module_name": "模块名" }`
        {!--< /tips >!--}
        """
        raise NotImplementedError

    @abstractmethod
    async def on_unload(self, event: dict[str, Any]) -> bool:
        """
        当模块被卸载时调用

        :param event: 事件内容
        :return: 处理结果

        {!--< tips >!--}
        其中，event事件内容为:
            `{ "module_name": "模块名" }`
        {!--< /tips >!--}
        """
        raise NotImplementedError

    # ==================== 配置管理 ====================

    def _get_config_key(self) -> str:
        """
        配置键名

        使用模块注册名（由 ModuleManager 注入），而非类名。
        这是因为多个模块的类名可能相同（如都叫 Main），
        但注册名是唯一的。

        :return: 配置键名字符串
        """
        return getattr(self, "_module_name", None) or self.__class__.__name__

    def _ensure_config_exists(self):
        """
        确保配置模板存在，不存在则生成默认配置

        {!--< internal-use >!--}
        会先行调用 _ensure_i18n_registered() 注册声明的翻译键，
        确保配置描述引用的 i18n 键在生成模板时已可用。
        {!--< /internal-use >!--}
        """
        # 先行注册 i18n 键（在生成配置之前），保证配置描述中的 i18n 键可用
        self._ensure_i18n_registered()

        if self.ConfigClass is None:
            return
        from .config_schema import (
            dataclass_to_defaults_dict,
        )

        key = self._get_config_key()
        data = config_mgr.getConfig(key)

        if data is None:
            data = dataclass_to_defaults_dict(self.ConfigClass)
            config_mgr.setConfig(key, data, immediate=True)
            # 懒加载 logger（模块可能未注入 sdk）
            try:
                logger.info(i18n.t("core.module.config_template_generated", key=key))
            except ImportError:
                pass

    def _ensure_i18n_registered(self):
        """
        注册 I18nClass 中声明的翻译键到 i18n 系统

        使用模块注册名作为键名前缀和 domain，便于统一卸载。
        方法是幂等的，多次调用不会产生副作用（重复注册会覆盖旧值）。

        {!--< internal-use >!--}
        由 ModuleManager.load() 或首次访问 self.cfg 时隐式调用。
        {!--< /internal-use >!--}
        """
        if self.I18nClass is None:
            return
        from .i18n_schema import BaseI18n

        if not isinstance(self.I18nClass, type) or not issubclass(self.I18nClass, BaseI18n):
            # 非法声明静默跳过（避免影响模块加载流程）
            return

        prefix = f"{self._get_config_key()}."
        domain = self._get_config_key()
        try:
            self.I18nClass.register(prefix=prefix, domain=domain)
        except Exception:
            # i18n 注册失败不应中断模块初始化
            pass

    @property
    def cfg(self):
        """
        类型安全的配置对象（实时读取）

        每次访问都从配置存储读取最新值，确保用户修改配置后立即生效。
        返回的 dataclass 实例是只读快照，修改它不会回写存储。

        :return: ConfigClass 对应的 dataclass 实例
        :raises AttributeError: 未声明 ConfigClass 时抛出
        """
        if self.ConfigClass is None:
            raise AttributeError(
                i18n.t("core.module.config_class_not_declared")
            )
        from .config_schema import dict_to_dataclass

        data = config_mgr.getConfig(self._get_config_key())
        if data is None:
            # 配置不存在时生成默认模板后重试
            self._ensure_config_exists()
            data = config_mgr.getConfig(self._get_config_key()) or {}
        return dict_to_dataclass(self.ConfigClass, data)

    @cfg.setter
    def cfg(self, value):
        """设置配置实例，同时同步写入配置存储（保证实时性）"""
        if value is not None:
            from dataclasses import asdict


            try:
                config_mgr.setConfig(self._get_config_key(), asdict(value))
            except Exception:
                pass

    def on_config_update(self, old_config, new_config):  # noqa: B027
        """
        配置变更回调（可选实现）

        子类可覆写此方法以响应配置热更新。默认实现为空操作。

        :param old_config: 变更前的配置实例
        :param new_config: 变更后的配置实例
        """


__all__ = ["BaseModule"]
