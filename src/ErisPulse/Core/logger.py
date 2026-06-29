"""
ErisPulse 日志系统

提供模块化日志记录功能，支持多级日志、模块过滤和内存存储。

{!--< tips >!--}
1. 支持按模块设置不同日志级别
2. 日志可存储在内存中供后续分析
3. 自动识别调用模块名称
{!--< /tips >!--}
"""

import datetime
import inspect
import json as _json
import logging
from collections.abc import Callable

from rich.console import Console
from rich.highlighter import NullHighlighter
from rich.logging import RichHandler
from rich.text import Text
from rich.theme import Theme

from .constants import (
    DEFAULT_LOG_MEMORY_LIMIT,
    LOG_RICH_THEME,
    LOG_TIME_FORMAT,
    LOGGER_NAME,
)
from .i18n import i18n

TRACE = 5
EVENT = 21  # 等同 INFO 级别，用于事件收发日志

logging.addLevelName(TRACE, "TRACE")
logging.addLevelName(EVENT, "EVENT")

_CUSTOM_LEVELS: dict[str, int] = {"TRACE": TRACE, "EVENT": EVENT}

_LOG_THEME = Theme(LOG_RICH_THEME)


class _JsonFormatter(logging.Formatter):
    """
    JSON 日志格式化器

    {!--< internal-use >!--}
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)
        return _json.dumps(log_entry, ensure_ascii=False)


class Logger:
    """
    日志管理器

    提供模块化日志记录和存储功能

    {!--< tips >!--}
    1. 使用set_module_level设置模块日志级别
    2. 使用get_logs获取历史日志
    3. 支持标准日志级别(DEBUG, INFO等)
    {!--< /tips >!--}
    """

    def __init__(self):
        self._max_logs = DEFAULT_LOG_MEMORY_LIMIT
        self._logs = {}
        self._module_levels = {}
        self._json_mode = False
        self._logger = logging.getLogger(LOGGER_NAME)
        self._logger.setLevel(logging.DEBUG)
        self._file_handlers: list[logging.FileHandler] = []
        self._console = Console(theme=_LOG_THEME)
        # 外部日志订阅者：{handler_id: (callback, min_level_num)}
        self._log_handlers: dict[str, tuple[Callable, int]] = {}
        if not self._logger.handlers:
            console_handler = RichHandler(
                console=self._console,
                show_time=True,
                show_level=True,
                show_path=False,
                markup=False,
                highlighter=NullHighlighter(),
                log_time_format=LOG_TIME_FORMAT,
            )
            self._logger.addHandler(console_handler)
        self._setup_config()

    # ==================== 日志订阅 ====================

    def handler(self, handler_id: str = "", *, min_level: str = "TRACE"):
        """
        日志订阅装饰器

        >>> @sdk.logger.handler("dashboard", min_level="INFO")
        ... def on_log(log_data: dict): ...

        >>> sdk.logger.handler("dashboard", min_level="INFO")(on_log)

        :param handler_id: 订阅器唯一标识，为空时使用函数名
        :param min_level: 最低日志级别
        """

        def decorate(f):
            hid = handler_id or f.__name__
            self._register_handler(hid, f, min_level)
            return f

        return decorate

    def _register_handler(
        self, handler_id: str, callback: Callable[[dict], None], min_level: str
    ) -> None:
        """
        {!--< internal-use >!--}
        内部注册逻辑
        """
        level_value = self._resolve_level(min_level)
        if level_value is None:
            return
        self._log_handlers[handler_id] = (callback, level_value)
        # 补发内存中已有的历史日志（按 level 筛选）
        for logs in self._logs.values():
            for log_data in logs:
                if log_data.get("level_num", 0) >= level_value:
                    try:
                        callback(log_data)
                    except Exception:
                        pass

    def remove_handler(self, handler_id: str) -> bool:
        """
        移除日志订阅器

        :param handler_id: 注册时使用的标识
        :return: bool 是否成功移除
        """
        return self._log_handlers.pop(handler_id, None) is not None

    def _notify_handlers(
        self, level_name: str, level_const: int, module: str, msg: str
    ) -> None:
        """
        {!--< internal-use >!--}
        向所有符合条件的订阅器推送结构化日志
        """
        if not self._log_handlers:
            return
        log_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "level": level_name,
            "level_num": level_const,
            "module": module,
            "message": str(msg),
        }
        for callback, min_level in self._log_handlers.values():
            if level_const >= min_level:
                try:
                    callback(log_data)
                except Exception:
                    pass  # 订阅器异常不应影响日志流程

    def set_memory_limit(self, limit: int) -> bool:
        """
        设置日志内存存储上限

        :param limit: 日志存储上限
        :return: bool 设置是否成功
        """
        if limit > 0:
            self._max_logs = limit
            # 更新所有已存在的日志列表大小
            for module_name in self._logs:
                while len(self._logs[module_name]) > self._max_logs:
                    self._logs[module_name].pop(0)
            return True
        else:
            self._logger.warning(i18n.t("core.logger.memory_limit_invalid"))
            return False

    def _resolve_level(self, level: str) -> int | None:
        """
        将字符串级别名解析为对应的数值常量

        :param level: 日志级别名称
        :return: 对应的 logging 级别数值，无效时返回 None

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        level = level.upper()
        if hasattr(logging, level):
            return getattr(logging, level)
        return _CUSTOM_LEVELS.get(level)

    def set_level(self, level: str) -> bool:
        """
        设置全局日志级别

        支持标准级别 (DEBUG/INFO/WARNING/ERROR/CRITICAL)
        及自定义级别 (TRACE/EVENT)

        :param level: 日志级别名称
        :return: bool 设置是否成功
        """
        try:
            level_value = self._resolve_level(level)
            if level_value is not None:
                self._logger.setLevel(level_value)
                return True
            return False
        except Exception:
            self._logger.error(i18n.t("core.logger.invalid_level", level=level))
            return False

    def set_module_level(self, module_name: str, level: str) -> bool:
        """
        设置指定模块日志级别

        支持标准级别 (DEBUG/INFO/WARNING/ERROR/CRITICAL)
        及自定义级别 (TRACE/EVENT)

        :param module_name: 模块名称
        :param level: 日志级别名称
        :return: bool 设置是否成功
        """
        level_value = self._resolve_level(level)
        if level_value is not None:
            self._module_levels[module_name] = level_value
            self._logger.info(
                i18n.t(
                    "core.logger.module_level_set",
                    module=module_name,
                    level=level.upper(),
                )
            )
            return True
        else:
            self._logger.error(i18n.t("core.logger.invalid_level", level=level))
            return False

    def set_output_file(self, path) -> bool:
        """
        设置日志输出

        :param path: 日志文件路径 Str/List
        :return: bool 设置是否成功
        """
        if self._file_handlers:
            for handler in self._file_handlers:
                self._logger.removeHandler(handler)
                handler.close()
            self._file_handlers.clear()

        if isinstance(path, str):
            path = [path]

        success = False
        for p in path:
            try:
                handler = logging.FileHandler(p, encoding="utf-8")
                if self._json_mode:
                    handler.setFormatter(_JsonFormatter())
                else:
                    handler.setFormatter(logging.Formatter("%(message)s"))
                self._logger.addHandler(handler)
                self._file_handlers.append(handler)
                success = True
            except Exception as e:
                self._logger.error(
                    i18n.t("core.logger.set_output_failed", path=p, error=e)
                )

        if not success:
            self._logger.warning(i18n.t("core.logger.no_output_set"))

        return success

    def set_json_format(self, enabled: bool = True) -> bool:
        """
        启用或禁用 JSON 结构化日志输出

        启用后，所有日志（控制台和文件）将以 JSON 格式输出，
        适合 ELK / Grafana Loki / Datadog 等日志聚合系统。

        :param enabled: 是否启用 JSON 格式（默认 True）
        :return: bool 设置是否成功

        :example:
        >>> # 在 config.toml 中配置
        >>> [ErisPulse.logger]
        >>> format = "json"
        >>>
        >>> # 或代码中动态切换
        >>> logger.set_json_format(True)
        """
        self._json_mode = enabled

        # 移除现有控制台处理器
        new_handlers = []
        for handler in self._logger.handlers:
            if isinstance(handler, RichHandler):
                self._logger.removeHandler(handler)
            else:
                new_handlers.append(handler)

        if enabled:
            # 添加 JSON 控制台处理器
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(_JsonFormatter())
            stream_handler.set_name("json_console")
            self._logger.addHandler(stream_handler)
        else:
            # 恢复 Rich 控制台处理器
            console_handler = RichHandler(
                console=self._console,
                show_time=True,
                show_level=True,
                show_path=False,
                markup=False,
                highlighter=NullHighlighter(),
                log_time_format=LOG_TIME_FORMAT,
            )
            self._logger.addHandler(console_handler)

        # 更新文件处理器格式
        for handler in self._file_handlers:
            if enabled:
                handler.setFormatter(_JsonFormatter())
            else:
                handler.setFormatter(logging.Formatter("%(message)s"))

        return True

    def save_logs(self, path) -> bool:
        """
        保存所有在内存中记录的日志

        :param path: 日志文件路径 Str/List
        :return: bool 设置是否成功
        """
        if not self._logs or all(len(logs) == 0 for logs in self._logs.values()):
            self._logger.warning(i18n.t("core.logger.no_logs_to_save"))
            return False

        if isinstance(path, str):
            path = [path]

        success = False
        for p in path:
            try:
                with open(p, "w", encoding="utf-8") as file:
                    for module, logs in self._logs.items():
                        if self._json_mode:
                            for log in logs:
                                file.write(_json.dumps(log, ensure_ascii=False) + "\n")
                        else:
                            file.write(f"Module: {module}\n")
                            for log in logs:
                                file.write(f"  {log}\n")
                self._logger.info(i18n.t("core.logger.saved", path=p))
                success = True
            except Exception as e:
                self._logger.error(i18n.t("core.logger.save_failed", path=p, error=e))

        return success

    def get_logs(self, module_name: str = None) -> dict:
        """
        获取日志内容

        JSON 模式下返回结构化 dict 列表，Rich 模式下返回字符串列表。

        :param module_name (可选): 模块名称，None表示获取所有日志
        :return: dict 日志内容
        """
        if module_name is None:
            return {k: self._format_for_output(v) for k, v in self._logs.items()}
        return {module_name: self._format_for_output(self._logs.get(module_name, []))}

    def iter_logs(self, module_name: str = None):
        """
        流式迭代日志（生成器）

        适合处理大量日志或推送到 SSE / WebSocket。

        :param module_name: [str] 模块名称，None 表示所有模块
        :return: [Iterator[dict | str]] JSON 模式下为 dict，Rich 模式下为 str

        :example:
        >>> for log in logger.iter_logs():
        ...     print(log)
        """
        if module_name:
            yield from self._format_for_output(self._logs.get(module_name, []))
        else:
            for logs in self._logs.values():
                yield from self._format_for_output(logs)

    def _format_for_output(self, entries: list) -> list:
        """
        {!--< internal-use >!--}
        将内部 dict 转换为向后兼容的输出格式
        """
        if self._json_mode:
            return [
                {
                    "timestamp": e["timestamp"],
                    "module": e["module"],
                    "message": e["message"],
                }
                for e in entries
            ]
        return [f"{e['timestamp'][:19]} - {e['message']}" for e in entries]

    def _save_in_memory(
        self, module_name: str, level_name: str, level_const: int, msg: str
    ) -> None:
        """
        {!--< internal-use >!--}
        将日志保存到内存
        """
        if module_name not in self._logs:
            self._logs[module_name] = []

        if len(self._logs[module_name]) >= self._max_logs:
            self._logs[module_name].pop(0)

        self._logs[module_name].append(
            {
                "timestamp": datetime.datetime.now().isoformat(),
                "level": level_name,
                "level_num": level_const,
                "module": module_name,
                "message": str(msg),
            }
        )

    def _setup_config(self):
        from ..runtime import get_logger_config

        logger_config = get_logger_config()
        if "level" in logger_config:
            self.set_level(logger_config["level"])
        if "log_files" in logger_config and logger_config["log_files"]:
            self.set_output_file(logger_config["log_files"])
        if "memory_limit" in logger_config:
            self.set_memory_limit(logger_config["memory_limit"])
        if logger_config.get("format") == "json":
            self.set_json_format(True)

    def _get_effective_level(self, module_name):
        return self._module_levels.get(module_name, self._logger.level)

    def _log(self, level_name: str, level_const: int, msg, *args, **kwargs):
        """
        内部日志方法，统一处理日志记录流程

        :param level_name: 日志级别名称（对应logging模块的方法名）
        :param level_const: 日志级别常量
        :param msg: 日志消息
        :param args: 额外的格式化参数
        :param kwargs: 额外的关键字参数
        """
        caller_module = self._get_caller()
        if self._get_effective_level(caller_module) <= level_const:
            self._save_in_memory(caller_module, level_name, level_const, msg)
            self._notify_handlers(level_name, level_const, caller_module, msg)
            self._logger.log(level_const, f"[{caller_module}] {msg}", *args, **kwargs)

    def _get_caller(self):
        try:
            frame = inspect.currentframe()
            if frame is None:
                return "Unknown"

            logger_module = inspect.getmodule(frame)

            while frame is not None:
                frame = frame.f_back
                if frame is None:
                    return "Unknown"
                module = inspect.getmodule(frame)
                if module is not None and module is not logger_module:
                    break

            if frame is None:
                return "Unknown"

            module = inspect.getmodule(frame)
            if module is None:
                return "Unknown"

            module_name = module.__name__
            if module_name == "__main__":
                module_name = "Main"
            elif module_name.endswith(".Core"):
                module_name = module_name[:-5]

            return module_name
        except Exception:
            return "Unknown"

    def get_child(self, child_name: str = "UnknownChild", *, relative: bool = True):
        """
        获取子日志记录器

        :param child_name: 子模块名称(可选)
        :param relative: 是否相对于调用者模块（默认True）
            - True: 使用"调用模块.子模块"作为完整名称
            - False: 直接使用child_name作为完整名称
        :return: LoggerChild 子日志记录器实例

        :example:
        >>> # 相对模式（默认）：自动添加调用模块前缀
        >>> child_logger = logger.get_child("database")
        >>> # 假设调用者是"mymodule"，完整名称将是"mymodule.database"
        >>>
        >>> # 绝对模式：直接使用指定名称
        >>> child_logger = logger.get_child("custom.module.name", relative=False)
        >>> # 完整名称将是"custom.module.name"
        >>>
        >>> # 获取当前模块的日志记录器
        >>> my_logger = logger.get_child()
        """
        if child_name and not relative:
            # 使用完整的指定名称，不添加前缀
            return LoggerChild(self, child_name)

        caller_module = self._get_caller()
        if child_name:
            full_module_name = f"{caller_module}.{child_name}"
        else:
            full_module_name = caller_module
        return LoggerChild(self, full_module_name)

    def trace(self, msg, *args, **kwargs):
        """记录 TRACE 级别日志（比 DEBUG 更细粒度）"""
        self._log("trace", TRACE, msg, *args, **kwargs)

    def event(self, msg, *args, **kwargs):
        """记录 EVENT 级别日志（事件收发专用，级别等同 INFO）"""
        self._log("event", EVENT, msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        """记录 DEBUG 级别日志"""
        self._log("debug", logging.DEBUG, msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        """记录 INFO 级别日志"""
        self._log("info", logging.INFO, msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        """记录 WARNING 级别日志"""
        self._log("warning", logging.WARNING, msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        """记录 ERROR 级别日志"""
        self._log("error", logging.ERROR, msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        """
        记录 CRITICAL 级别日志
        这是最高级别的日志，表示严重的系统错误
        注意：此方法不会触发程序崩溃，仅记录日志

        {!--< tips >!--}
        1. 不会触发程序崩溃，如需终止程序请显式调用 sys.exit()
        2. 会在日志文件中添加 CRITICAL 标记便于后续分析
        {!--< /tips >!--}
        """
        self._log("critical", logging.CRITICAL, msg, *args, **kwargs)

    # ==================== 视觉输出方法 ====================

    def print_section_header(self, title: str):
        """
        打印日志分组标题

        :param title: 分组标题
        """
        self._console.print()
        line = Text()
        line.append("  ── ", style="dim")
        line.append(title, style="bold")
        self._console.print(line)

    def print_section_footer(self):
        """
        打印分组结束标记
        """
        self._console.print(Text("  " + "─" * 48, style="dim"))

    def print_tree_item(
        self,
        text: str,
        level: int = 0,
        is_last: bool = False,
        tag: str = "",
        tag_style: str = "dim",
    ):
        """
        打印树状结构项目

        :param text: 文本内容
        :param level: 缩进层级
        :param is_last: 是否是最后一项
        :param tag: 可选的样式化后缀标签（如 "[懒加载]"）
        :param tag_style: 标签的 rich 样式（默认 dim）
        """
        indent = "    " * (level + 1)
        connector = "╰─ " if is_last else "├─ "
        line = Text()
        line.append(indent)
        line.append(connector, style="dim")
        line.append(text)
        if tag:
            line.append(f"  {tag}", style=tag_style)
        self._console.print(line)

    def print_info(self, text: str, level: int = 1):
        """
        打印信息

        :param text: 文本内容
        :param level: 缩进层级
        """
        indent = "    " * level
        line = Text()
        line.append(indent)
        line.append("· ", style="dim")
        line.append(text)
        self._console.print(line)

    def print_section_separator(self):
        """
        打印简单的分隔线
        """
        self._console.print()

    def __getattr__(self, name: str) -> "LoggerChild":
        """
        通过属性访问自动创建子logger

        :param name: 子logger名称
        :return: LoggerChild 子logger实例
        :raises AttributeError: 当访问无效属性时抛出

        :example:
        >>> # 自动创建子logger并记录日志
        >>> logger.mymodule.info("message")
        >>>
        >>> # 支持嵌套访问
        >>> logger.mymodule.database.info("db message")
        >>>
        >>> # 相当于 logger.get_child("mymodule").info("message")
        """

        # 自动创建子logger，使用绝对模式（不添加调用者前缀）
        return self.get_child(name, relative=False)


class LoggerChild:
    """
    子日志记录器

    用于创建具有特定名称的子日志记录器，仅改变模块名称，其他功能全部委托给父日志记录器
    """

    def __init__(self, parent_logger: Logger, name: str):
        """
        初始化子日志记录器

        :param parent_logger: 父日志记录器实例
        :param name: 子日志记录器名称
        """
        self._parent = parent_logger
        self._name = name

    def _log(self, level_name: str, level_const: int, msg, *args, **kwargs):
        """
        内部日志方法

        :param level_name: 日志级别名称
        :param level_const: 日志级别常量
        :param msg: 日志消息
        """
        parts = self._name.split(".")
        deduped = [parts[0]]
        for p in parts[1:]:
            if p != deduped[-1]:
                deduped.append(p)
        display_name = ".".join(deduped)

        if self._parent._get_effective_level(display_name.split(".")[0]) <= level_const:
            self._parent._save_in_memory(display_name, level_name, level_const, msg)
            self._parent._notify_handlers(level_name, level_const, display_name, msg)
            self._parent._logger.log(
                level_const, f"[{display_name}] {msg}", *args, **kwargs
            )

    def trace(self, msg, *args, **kwargs):
        """记录 TRACE 级别日志（比 DEBUG 更细粒度）"""
        self._log("trace", TRACE, msg, *args, **kwargs)

    def event(self, msg, *args, **kwargs):
        """记录 EVENT 级别日志（事件收发专用，级别等同 INFO）"""
        self._log("event", EVENT, msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        """记录 DEBUG 级别日志"""
        self._log("debug", logging.DEBUG, msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        """记录 INFO 级别日志"""
        self._log("info", logging.INFO, msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        """记录 WARNING 级别日志"""
        self._log("warning", logging.WARNING, msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        """记录 ERROR 级别日志"""
        self._log("error", logging.ERROR, msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        """
        记录 CRITICAL 级别日志
        这是最高级别的日志，表示严重的系统错误
        注意：此方法不会触发程序崩溃，仅记录日志
        """
        self._log("critical", logging.CRITICAL, msg, *args, **kwargs)

    def get_child(self, child_name: str):
        """
        获取子日志记录器的子记录器

        :param child_name: 子模块名称
        :return: LoggerChild 子日志记录器实例
        """
        full_child_name = f"{self._name}.{child_name}"
        return LoggerChild(self._parent, full_child_name)

    def __getattr__(self, name: str) -> "LoggerChild":
        """
        通过属性访问自动创建子logger

        :param name: 子logger名称
        :return: LoggerChild 子logger实例
        :raises AttributeError: 当访问无效属性时抛出

        :example:
        >>> # 嵌套创建子logger
        >>> child = logger.mymodule
        >>> nested_child = child.database  # 相当于 logger.mymodule.database
        >>> nested_child.info("db message")
        """

        # 返回嵌套的子logger
        return self.get_child(name)


logger: Logger = Logger()

__all__ = ["logger"]
