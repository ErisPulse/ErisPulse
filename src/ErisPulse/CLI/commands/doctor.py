"""
Doctor 命令实现

运行环境诊断，输出 ErisPulse CLI 的 Python / 后端 / 配置 / 网络健康状态。
"""

import asyncio
import platform
import sys
from argparse import ArgumentParser
from pathlib import Path

from rich.table import Table

from ..base import Command
from ..console import console
from ..i18n import i18n
from ..utils import PackageManager


class DoctorCommand(Command):
    """
    doctor 命令

    诊断当前环境：Python 版本、安装后端（uv/pip）、目标解释器、
    配置文件、PyPI 连通性与代理设置。
    """

    name = "doctor"
    description = i18n.t("cli.doctor.description")
    aliases = ["diag"]

    def __init__(self):
        """初始化 DoctorCommand，创建包管理器实例"""
        self.package_manager = PackageManager()

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument(
            "--verbose",
            action="store_true",
            help=i18n.t("cli.doctor.verbose_help"),
        )

    def execute(self, args):
        pm = self.package_manager
        rows: list[tuple[str, str, str]] = []
        failed = False

        # 1. Python 解释器
        py_ok = sys.version_info >= (3, 10)
        rows.append(
            (
                self._status(py_ok),
                i18n.t("cli.doctor.python"),
                f"{platform.python_version()} ({sys.executable})",
            )
        )
        if not py_ok:
            failed = True

        # 2. 安装后端（uv / pip）
        uv_cmd = pm._get_uv_command()
        if uv_cmd:
            rows.append(
                (self._status(True), i18n.t("cli.doctor.backend"), f"uv ({uv_cmd[0]})")
            )
        else:
            rows.append(
                (
                    self._status(True),
                    i18n.t("cli.doctor.backend"),
                    i18n.t("cli.doctor.backend_pip"),
                )
            )

        # 3. 目标解释器（安装目标环境）
        target_python = pm._get_target_python()
        rows.append(
            (self._status(True), i18n.t("cli.doctor.target_python"), target_python)
        )

        # 4. 配置文件
        config_path = Path("config") / "config.toml"
        if config_path.exists():
            rows.append(
                (
                    self._status(True),
                    i18n.t("cli.doctor.config"),
                    str(config_path.resolve()),
                )
            )
        else:
            rows.append(
                (
                    self._status(False),
                    i18n.t("cli.doctor.config"),
                    f"{i18n.t('cli.doctor.config_missing')} ({config_path})",
                )
            )
            failed = True

        # 5. PyPI 连通性
        try:
            remote = asyncio.run(pm.get_remote_packages())
            pkg_count = len(remote.get("modules", {})) + len(
                remote.get("adapters", {})
            )
            rows.append(
                (
                    self._status(True),
                    i18n.t("cli.doctor.pypi"),
                    i18n.t("cli.doctor.pypi_ok", count=pkg_count),
                )
            )
        except Exception:
            failed = True
            rows.append(
                (
                    self._status(False),
                    i18n.t("cli.doctor.pypi"),
                    i18n.t("cli.doctor.pypi_fail"),
                )
            )

        # 6. 代理
        proxy = pm._get_system_proxy()
        if proxy:
            https_proxy = proxy.get("https") or proxy.get("http", "")
            rows.append(
                (
                    self._status(True),
                    i18n.t("cli.doctor.proxy"),
                    https_proxy,
                )
            )
        else:
            rows.append(
                (
                    self._status(True),
                    i18n.t("cli.doctor.proxy"),
                    i18n.t("cli.doctor.proxy_none"),
                )
            )

        # 输出诊断报告
        table = Table(
            show_header=False,
            box=None,
            pad_edge=False,
            expand=True,
        )
        for status, label, detail in rows:
            table.add_row(status, f"[info]{label}[/]", detail)

        console.print(table)

        if failed:
            console.print(f"[error]{i18n.t('cli.doctor.failed')}[/]")
            for status, label, _ in rows:
                if status != self._status(True):
                    console.print(
                        f"  [error]-[/] [info]{label}[/]"
                    )
        else:
            console.print(f"[success]{i18n.t('cli.doctor.all_ok')}[/]")

    @staticmethod
    def _status(ok: bool) -> str:
        """
        生成诊断项的状态标记文本（OK / FAIL，不使用 emoji）

        :param ok: bool 诊断项是否正常
        :return: str 带样式的状态标记文本
        """
        from ..i18n import i18n

        return (
            f"[success]{i18n.t('cli.doctor.status_ok')}[/]"
            if ok
            else f"[error]{i18n.t('cli.doctor.status_fail')}[/]"
        )


__all__ = ["DoctorCommand"]
