"""
ErisPulse 基础加载器

定义加载器的抽象基类，提供通用的加载器接口和结构

{!--< tips >!--}
1. 所有具体加载器应继承自 BaseLoader
2. 子类需实现 _process_entry_point 方法
3. 支持启用/禁用配置管理
{!--< /tips >!--}
"""

from abc import ABC, abstractmethod
from typing import Any

from ...Core.config import config
from ...Core.i18n import i18n
from ...Core.logger import logger
from ...runtime.version import check_min_sdk_version


def resolve_min_sdk_version(component_obj: Any, name: str = "") -> str | None:
    """
    解析组件声明的运行时最低 SDK 版本（统一读取口径）

    解析优先级：``get_meta()`` 声明（:class:`~ErisPulse.Core.Bases.ModuleMeta`
    实例或 dict，模块体系的规范声明位置）> 类属性 ``min_sdk_version``
    （适配器等无 meta 声明类组件的声明位置）> ``None``（未声明）。

    :param component_obj: 组件类
    :param name: 组件名称（仅用于 get_meta 异常时的诊断日志）
    :return: str 声明的最低版本；未声明或声明为空返回 None
    """
    get_meta = getattr(component_obj, "get_meta", None)
    if callable(get_meta):
        try:
            declared = get_meta()
        except Exception as e:
            # get_meta 崩溃不应阻断加载流程，版本检查按未声明处理
            logger.warning(
                i18n.t(
                    "loader.base.sdk_version_meta_failed", name=name, error=e
                )
            )
        else:
            if isinstance(declared, dict):
                value = declared.get("min_sdk_version")
                if value:
                    return str(value)
            else:
                value = getattr(declared, "min_sdk_version", None)
                if value:
                    return str(value)
    value = getattr(component_obj, "min_sdk_version", None)
    return str(value) if value else None


class BaseLoader(ABC):
    """
    基础加载器抽象类

    提供通用的加载器接口和配置管理功能

    {!--< tips >!--}
    子类需要实现：
    - _get_entry_point_group: 返回 entry-point 组名
    - _process_entry_point: 处理单个 entry-point
    {!--< /tips >!--}

    {!--< internal-use >!--}
    此类仅供内部使用，不应直接实例化
    {!--< /internal-use >!--}
    """

    def __init__(self, config_prefix: str):
        """
        初始化基础加载器

        :param config_prefix: 配置前缀（如 "ErisPulse.adapters" 或 "ErisPulse.modules"）
        """
        self._config_prefix = config_prefix
        # 严格模式管理器，由初始化协调器注入；未注入时按需从配置创建
        self._strict_manager: Any = None

    def set_strict_manager(self, manager: Any) -> None:
        """
        注入严格模式管理器

        :param manager: StrictModeManager 实例

        {!--< internal-use >!--}
        由初始化协调器调用，确保多个加载器共享同一管理器实例以统一收集违规
        {!--< /internal-use >!--}
        """
        self._strict_manager = manager

    def _strict(self) -> Any:
        """
        获取严格模式管理器

        :return: StrictModeManager 实例

        {!--< internal-use >!--}
        未注入时从配置创建，仅供独立调用/测试使用；正常启动流程总会被注入
        {!--< /internal-use >!--}
        """
        if self._strict_manager is None:
            from ..strict import StrictModeManager

            self._strict_manager = StrictModeManager.from_config()
        return self._strict_manager

    def _check_sdk_version(self, name: str, component_type: str, component_obj: Any) -> bool:
        """
        运行时最低 SDK 版本检查（声明读取见 :func:`resolve_min_sdk_version`）

        组件未声明或声明无法解析时放行（后者输出警告）；
        版本不满足时输出明确错误、按严格模式登记拒绝并返回 False，
        由调用方跳过该组件——SDK 过低的组件加载后几乎必然运行异常，
        提前拦截可给出可操作的诊断（升级 SDK 或换用兼容版本组件）。

        :param name: 组件名称
        :param component_type: 组件类型（``module`` / ``adapter``，用于日志与严格模式登记）
        :param component_obj: 组件类（经统一口径解析其 min_sdk_version 声明）
        :return: bool 是否允许继续加载

        {!--< internal-use >!--}
        供 ModuleLoader / AdapterLoader 在构建组件信息前调用
        {!--< /internal-use >!--}
        """
        declared = resolve_min_sdk_version(component_obj, name=name)
        if not declared:
            return True

        satisfied, current, required, parseable = check_min_sdk_version(str(declared))
        if not parseable:
            logger.warning(
                i18n.t(
                    f"loader.{component_type}.sdk_version_invalid",
                    name=name,
                    value=declared,
                )
            )
            return True
        if satisfied:
            return True

        logger.error(
            i18n.t(
                f"loader.{component_type}.sdk_version_unsupported",
                name=name,
                required=required,
                current=current,
            )
        )
        self._strict().record_failure(
            name,
            component_type,
            "sdk_version_mismatch",
            detail=f"min_sdk_version={declared}, current={current}",
        )
        return False

    @abstractmethod
    def _get_entry_point_group(self) -> str:
        """
        获取 entry-point 组名

        :return: entry-point 组名

        {!--< internal-use >!--}
        子类必须实现此方法
        {!--< /internal-use >!--}
        """
        ...

    @abstractmethod
    async def _process_entry_point(
        self,
        entry_point: Any,
        objs: dict[str, Any],
        enabled_list: list[str],
        disabled_list: list[str],
        manager_instance: Any,
    ) -> tuple[dict[str, Any], list[str], list[str], bool]:
        """
        处理单个 entry-point

        :param entry_point: entry-point 对象
        :param objs: 对象字典
        :param enabled_list: 启用列表
        :param disabled_list: 禁用列表
        :param manager_instance: 管理器实例（用于调用 exists/is_enabled 等方法）
        :return: (更新后的对象字典, 更新后的启用列表, 更新后的禁用列表, 是否为新项)

        {!--< internal-use >!--}
        子类必须实现此方法
        {!--< /internal-use >!--}
        """
        ...

    async def load(
        self, manager_instance: Any
    ) -> tuple[dict[str, Any], list[str], list[str]]:
        """
        从 entry-points 加载对象

        :param manager_instance: 管理器实例
        :return:
            dict[str, Any]: 对象字典
            list[str]: 启用列表
            list[str]: 禁用列表

        :raises ImportError: 当加载失败时抛出
        """
        objs: dict[str, Any] = {}
        enabled_list: list[str] = []
        disabled_list: list[str] = []

        group_name = self._get_entry_point_group()
        logger.info(i18n.t("loader.base.load_start", group=group_name))

        try:
            # 加载 entry-points
            import importlib.metadata

            entry_points = importlib.metadata.entry_points()
            if hasattr(entry_points, "select"):
                entries = entry_points.select(group=group_name)
            else:
                entries = entry_points.get(group_name, [])  # type: ignore[attr-defined]

            # 处理每个 entry-point
            for entry_point in entries:
                objs, enabled_list, disabled_list, _ = await self._process_entry_point(
                    entry_point, objs, enabled_list, disabled_list, manager_instance
                )

            logger.info(i18n.t("loader.base.load_done", group=group_name))

        except Exception as e:
            logger.error(i18n.t("loader.base.load_failed", group=group_name, error=e))
            raise ImportError(i18n.t("loader.base.import_failed", group=group_name, error=e)) from e

        return objs, enabled_list, disabled_list

    def _register_config(self, name: str, enabled: bool = False) -> bool:
        """
        注册配置项

        :param name: 名称
        :param enabled: 是否启用
        :return: 操作是否成功

        {!--< internal-use >!--}
        内部方法，用于注册新的配置项
        {!--< /internal-use >!--}
        """
        config_key = f"{self._config_prefix}.status.{name}"
        config.setConfig(config_key, enabled)
        status = (
            i18n.t("loader.base.status_enabled")
            if enabled
            else i18n.t("loader.base.status_disabled")
        )
        logger.info(
            i18n.t(
                "loader.base.registered",
                prefix=self._config_prefix,
                name=name,
                status=status,
            )
        )
        return True

    def _get_config_status(self, name: str) -> bool:
        """
        获取配置状态

        :param name: 名称
        :return: 是否启用

        {!--< internal-use >!--}
        内部方法，用于获取配置状态
        默认情况下（无配置），返回 True（启用）并写入配置
        {!--< /internal-use >!--}
        """
        config_key = f"{self._config_prefix}.status.{name}"
        status = config.getConfig(config_key)

        if status is None:
            config.setConfig(config_key, True)
            return True

        if isinstance(status, str):
            return status.lower() not in ("false", "0", "no", "off")

        return bool(status)
