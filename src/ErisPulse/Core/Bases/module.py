"""
ErisPulse 模块基础模块

提供模块基类定义和标准接口
"""

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from typing import Any, TypedDict

from ...loaders.strategy import ModuleLoadStrategy
from ..config import config as config_mgr
from ..constants import DEFAULT_LAZY_LOADING_ENABLED, DEFAULT_MODULE_PRIORITY
from ..i18n import i18n
from ..logger import logger


@dataclass
class ModuleMeta:
    """
    模块介绍元信息声明类

    模块通过 ``get_meta()`` 返回本类实例（属性键入，IDE 友好），
    框架内部经 :meth:`to_dict` 解析——用户声明与内部规则解耦，
    后续演进不影响既有声明。

    {!--< tips >!--}
    1. 字段均可选，``None`` 字段不参与解析
    2. ``description`` 等文本字段支持 i18n 字典 ``{"i18n": "key", "default": "兜底"}``
    3. ``commands`` 缺省时自动从注册命令提取
    4. 兼容直接返回 dict 的旧写法
    {!--< /tips >!--}

    :example:
    >>> @staticmethod
    ... def get_meta() -> ModuleMeta:
    ...     return ModuleMeta(
    ...         name="天气",
    ...         description="查询城市天气",
    ...         group="工具",
    ...         tags=["天气", "查询"],
    ...     )
    """

    name: str | None = None
    description: str | dict[str, Any] | None = None
    version: str | None = None
    author: str | None = None
    homepage: str | None = None
    group: str | None = None
    tags: list[str] = field(default_factory=list)
    commands: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        """
        转为字典（内部解析入口，过滤 None 字段）

        :return: 非空字段组成的字典
        """
        return {k: v for k, v in asdict(self).items() if v is not None}


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
    def get_meta() -> "ModuleMeta | dict[str, Any]":
        """
        获取模块介绍元信息（描述这个模块是什么、属于哪一类等）

        与 ``get_load_strategy()`` 返回 :class:`ModuleLoadStrategy` 一致，
        推荐返回 :class:`ModuleMeta` **配置类实例**（属性键入、IDE 补全），
        也兼容直接返回 dict。元信息是模块的**通用介绍数据**，
        供各类管理界面 / 生态模块消费（help 模块、Dashboard 模块列表、模块商店等）。

        :class:`ModuleMeta` 字段：
        - ``name``: 模块显示名（默认注册名）
        - ``description``: 模块简介（这个模块是干什么的）
        - ``version``: 版本号
        - ``author``: 作者
        - ``homepage``: 主页 / 仓库地址
        - ``group``: 分组（按功能分类，如 "工具" / "娱乐"）
        - ``tags``: 标签列表
        - ``commands``: 模块提供的命令名列表（默认从注册命令自动提取）

        **i18n 支持**：字段值可为纯字符串，或 i18n 字典
        ``{"i18n": "key.path", "default": "兜底文本"}``（与配置 description 约定一致）。
        翻译键通过 ``I18nClass`` 声明注册（键路径 ``<模块名>.<属性名>``），
        读取时 ``sdk.module.get_meta()`` 自动解析为当前语言文本。

        {!--< tips >!--}
        读取已解析的元信息：``sdk.module.get_meta("MyModule")``；
        若需要"模块简介 + 该模块注册的命令"的聚合数据，可用
        ``sdk.module.get_commands_overview()``。
        {!--< /tips >!--}

        :return: 元信息（ModuleMeta 实例或 dict），模块未声明时返回空 dict

        :example:
        推荐写法（配置类）：
        >>> class MyModule(BaseModule):
        ...     @staticmethod
        ...     def get_meta() -> ModuleMeta:
        ...         return ModuleMeta(
        ...             name="天气",
        ...             description="查询城市天气",
        ...             group="工具",
        ...             tags=["天气", "查询"],
        ...         )

        兼容写法（dict）：
        >>> class MyModule(BaseModule):
        ...     @staticmethod
        ...     def get_meta() -> dict:
        ...         return {
        ...             "name": "天气",
        ...             "description": "查询城市天气",
        ...         }
        """
        return ModuleMeta()

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

    # ==================== 后台任务 ====================

    def spawn(self, coro):
        """
        调度一个归属于本模块的后台任务（推荐的任务创建方式）

        任务自动登记到模块名下：模块卸载时，框架在 ``on_unload`` 之后
        兜底取消仍未结束的任务，防止任务持有 ``self`` 引用导致模块
        实例无法被回收（热重载泄漏的常见根因）。

        需要精细控制生命周期的任务，建议在 ``on_unload`` 中自行取消
        并等待收尾；本方法作为兜底保障。

        :param coro: 待执行的协程
        :return: 创建出的 asyncio.Task（可忽略）

        :example:
        >>> async def _poll(self):
        ...     while True:
        ...         await asyncio.sleep(5)
        ...
        >>> async def on_load(self, event):
        ...     self.spawn(self._poll())
        """
        from ...runtime.tasks import spawn_background

        return spawn_background(coro, owner=self._get_config_key())

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
