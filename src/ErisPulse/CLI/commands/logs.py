"""ep logs 命令：查看框架日志文件尾部"""

from argparse import ArgumentParser, Namespace
from pathlib import Path

from ..base import Command
from ..i18n import i18n


class LogsCommand(Command):
    """
    logs 命令

    查看框架日志文件尾部（默认最近 50 行），支持 --lines 与 --file 覆盖。
    日志路径与 [ErisPulse.logger] 配置一致（log_files 显式路径优先，其次
    log_dir 目录下的 erispulse.log）。
    """

    name = "logs"
    description = i18n.t("cli.logs.description")
    aliases = ["log", "tail"]
    category = "config"

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "-n",
            "--lines",
            type=int,
            default=50,
            help=i18n.t("cli.logs.lines_help"),
        )
        parser.add_argument(
            "-f",
            "--file",
            type=str,
            default="",
            help=i18n.t("cli.logs.file_help"),
        )

    def _resolve_log_path(self, override: str) -> Path | None:
        """解析日志文件路径（与 logger 的文件输出配置同源）"""
        if override:
            return Path(override)
        try:
            from ...runtime import get_logger_config

            logger_config = get_logger_config()
            log_files = logger_config.get("log_files")
            if log_files:
                candidates = log_files if isinstance(log_files, list) else [log_files]
                if candidates:
                    return Path(str(candidates[-1]))
            log_dir = logger_config.get("log_dir")
            if log_dir:
                filename = logger_config.get(
                    "log_filename", "erispulse.log"
                )
                return Path(str(log_dir)) / str(filename)
        except Exception:
            pass
        return Path("logs") / "erispulse.log"

    def execute(self, args: Namespace) -> None:
        log_path = self._resolve_log_path(getattr(args, "file", ""))
        lines = max(1, int(getattr(args, "lines", 50)))
        if log_path is None or not log_path.exists():
            print(i18n.t("cli.logs.not_found", path=str(log_path)))
            return
        try:
            with log_path.open(encoding="utf-8", errors="replace") as f:
                tail_lines = f.readlines()[-lines:]
        except OSError as e:
            print(i18n.t("cli.logs.read_failed", path=str(log_path), error=e))
            return
        print(i18n.t("cli.logs.header", path=str(log_path), lines=len(tail_lines)))
        for line in tail_lines:
            print(line, end="" if line.endswith("\n") else "\n")


__all__ = ["LogsCommand"]
