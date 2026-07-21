"""
ErisPulse 基础加载器

定义加载器的抽象基类，提供通用的加载器接口和结构

{!--< tips >!--}
1. 所有具体加载器应继承自 BaseLoader
2. 子类需实现 _process_entry_point 方法
3. 支持启用/禁用配置管理
{!--< /tips >!--}
"""

import importlib.metadata
from abc import ABC, abstractmethod
from typing import Any

from ...Core.config import config
from ...Core.logger import logger


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
        logger.info(f"正在加载 {group_name} entry-points...")

        try:
            # 加载 entry-points
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

            logger.info(f"{group_name} 加载完成")

        except Exception as e:
            logger.error(f"加载 {group_name} entry-points 失败: {e}")
            raise ImportError(f"无法加载 {group_name}: {e}") from e

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
        status = "启用" if enabled else "禁用"
        logger.info(f"{self._config_prefix} {name} 已注册并{status}")
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
