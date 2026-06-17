"""
ErisPulse 严格模式

提供统一的模块/适配器加载合规性管理。

{!--< tips >!--}
1. 通过 ErisPulse.framework.strict_mode 配置级别（0=宽松, 1=跳过, 2=致命）
2. 通过 ErisPulse.framework.strict_mode_exceptions 配置豁免清单
3. StrictModeManager 由初始化协调器创建并注入到各加载器，确保跨加载器收集违规
{!--< /tips >!--}
"""

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any

from ..Core.constants import DEFAULT_STRICT_MODE
from ..Core.i18n import i18n
from ..Core.logger import logger


class StrictModeLevel(IntEnum):
    """
    严格模式级别

    {!--< internal-use >!--}
    内部枚举，对应配置中的 strict_mode 数值
    {!--< /internal-use >!--}
    """

    LENIENT = 0
    SKIP = 1
    FATAL = 2


class StrictModeError(Exception):
    """
    严格模式致命错误

    当严格模式级别为 2（致命）且检测到违规时，在检查点抛出此异常，
    用于中止整个启动流程。

    {!--< tips >!--}
    此异常不应被加载器捕获吞掉，应向上传播至初始化协调器
    {!--< /tips >!--}
    """

    def __init__(self, message: str, violations: list | None = None):
        super().__init__(message)
        self.violations: list = violations if violations is not None else []


@dataclass
class Violation:
    """
    单条违规记录

    :param name: 组件名称（entry-point name）
    :param component_type: 组件类型，"module" 或 "adapter"
    :param reason: 违规原因标识，如 "not_base_class", "load_failed",
        "register_failed", "init_failed", "invalid_name"
    :param detail: 可选的详细描述
    """

    name: str
    component_type: str
    reason: str
    detail: str = ""


@dataclass
class StrictModeManager:
    """
    严格模式管理器

    统一处理模块/适配器加载过程中的合规性判定与违规收集。

    {!--< tips >!--}
    使用方式：
    >>> manager = StrictModeManager.from_config()
    >>> # 未继承基类时判定是否拒绝
    >>> if manager.decide(name, "module", "not_base_class"):
    ...     # 跳过该模块
    ...     pass
    >>> # 异常类失败仅记录（调用方已自行跳过）
    >>> manager.record_failure(name, "module", "load_failed", detail=str(e))
    >>> # 在检查点统一抛出致命错误
    >>> manager.raise_if_fatal()
    {!--< /tips >!--}
    """

    level: int = DEFAULT_STRICT_MODE
    exceptions: dict[str, Any] = field(default_factory=dict)
    _violations: list[Violation] = field(default_factory=list)
    _rejections: list[Violation] = field(default_factory=list)
    _exemption_sets: dict[str, set] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        """初始化豁免集合，便于快速查找"""
        mods = self.exceptions.get("modules") or []
        adps = self.exceptions.get("adapters") or []
        self._exemption_sets = {
            "module": set(mods),
            "adapter": set(adps),
        }

    @classmethod
    def from_config(cls) -> "StrictModeManager":
        """
        从框架配置创建管理器实例

        :return: 配置好的管理器实例；读取配置失败时回退到默认值

        {!--< internal-use >!--}
        由初始化协调器调用，读取 ErisPulse.framework.strict_mode 及豁免清单
        {!--< /internal-use >!--}
        """
        try:
            from ..runtime import get_framework_config

            fw = get_framework_config() or {}
            level = int(fw.get("strict_mode", DEFAULT_STRICT_MODE))
            exceptions = fw.get("strict_mode_exceptions") or {}
            return cls(level=level, exceptions=exceptions)
        except Exception as e:
            logger.debug(i18n.t("loader.strict.config_failed", error=e))
            return cls()

    def is_exempt(self, name: str, component_type: str) -> bool:
        """
        判断组件是否在豁免清单中

        :param name: 组件名称
        :param component_type: 组件类型
        :return: 是否豁免
        """
        return name in self._exemption_sets.get(component_type, set())

    def decide(self, name: str, component_type: str, reason: str) -> bool:
        """
        报告一次可"容忍或拒绝"的违规，并返回处置决定

        主要用于"未继承基类"这类违规：在宽松级别下可容忍继续加载，
        在严格级别下应拒绝（跳过）。

        :param name: 组件名称
        :param component_type: 组件类型
        :param reason: 违规原因标识
        :return: True 表示应拒绝（跳过）该组件；False 表示应容忍（继续加载）

        {!--< internal-use >!--}
        在致命级别下，非豁免违规会同时被记录，待检查点统一抛出
        {!--< /internal-use >!--}
        """
        if self.is_exempt(name, component_type):
            logger.warning(
                i18n.t(
                    "loader.strict.exempted",
                    name=name,
                    type=component_type,
                    reason=reason,
                )
            )
            return False

        # 象免清单的配置键名：module -> modules, adapter -> adapters
        list_key = "modules" if component_type == "module" else "adapters"

        if self.level >= StrictModeLevel.FATAL:
            violation = Violation(name, component_type, reason)
            self._violations.append(violation)
            self._rejections.append(violation)
            logger.error(
                i18n.t(
                    "loader.strict.rejected_fatal",
                    name=name,
                    type=component_type,
                    reason=reason,
                    list_key=list_key,
                )
            )
            return True

        if self.level >= StrictModeLevel.SKIP:
            self._rejections.append(Violation(name, component_type, reason))
            logger.error(
                i18n.t(
                    "loader.strict.rejected",
                    name=name,
                    type=component_type,
                    reason=reason,
                    list_key=list_key,
                )
            )
            return True

        # 宽松级别：容忍该违规，仅警告
        logger.warning(
            i18n.t(
                "loader.strict.tolerated",
                name=name,
                type=component_type,
                reason=reason,
            )
        )
        return False

    def record_failure(
        self,
        name: str,
        component_type: str,
        reason: str,
        detail: str = "",
    ) -> None:
        """
        记录一次异常类失败

        与 decide 不同，此方法假定调用方已自行跳过该组件（例如捕获了异常）。
        被拒绝的组件会记入 _rejections（与级别无关，用于摘要展示）；
        仅在致命级别下额外记入 _violations，以便检查点统一报告并中止。

        :param name: 组件名称
        :param component_type: 组件类型
        :param reason: 违规原因标识
        :param detail: 详细描述（如异常信息）

        {!--< internal-use >!--}
        调用方应同时输出自己的具体错误日志，此方法不重复输出
        {!--< /internal-use >!--}
        """
        if self.is_exempt(name, component_type):
            return
        rejection = Violation(name, component_type, reason, detail=detail)
        self._rejections.append(rejection)
        if self.level >= StrictModeLevel.FATAL:
            self._violations.append(rejection)

    def has_fatal_violations(self) -> bool:
        """
        是否存在致命级别的违规

        :return: 当前为致命级别且已收集到违规时返回 True
        """
        return self.level >= StrictModeLevel.FATAL and len(self._violations) > 0

    @property
    def violations(self) -> list[Violation]:
        """已收集的致命违规列表（只读视图）"""
        return list(self._violations)

    @property
    def rejections(self) -> list[Violation]:
        """被拒绝/跳过的组件列表（只读视图，与级别无关，用于摘要展示）"""
        return list(self._rejections)

    def raise_if_fatal(self) -> None:
        """
        在检查点统一报告并抛出致命错误

        当处于致命级别且收集到违规时，先打印完整违规清单，再抛出
        StrictModeError 中止启动。无致命违规时直接返回。

        :raises StrictModeError: 存在致命违规时抛出
        """
        if not self.has_fatal_violations():
            return

        logger.error(
            i18n.t(
                "loader.strict.fatal_report_header",
                count=len(self._violations),
            )
        )
        for index, violation in enumerate(self._violations, start=1):
            logger.error(
                i18n.t(
                    "loader.strict.fatal_report_item",
                    index=index,
                    name=violation.name,
                    type=violation.component_type,
                    reason=violation.reason,
                    detail=violation.detail,
                )
            )

        raise StrictModeError(
            i18n.t("loader.strict.fatal_abort", count=len(self._violations)),
            violations=list(self._violations),
        )


__all__ = [
    "StrictModeLevel",
    "StrictModeError",
    "Violation",
    "StrictModeManager",
]
