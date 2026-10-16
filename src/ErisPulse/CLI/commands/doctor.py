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
from ..utils.package_manager import resolve_target_python


class DoctorCommand(Command):
    """
    doctor 命令

    诊断当前环境：Python 版本、安装后端（uv/pip）、目标解释器、
    配置文件、PyPI 连通性与代理设置。
    """

    name = "doctor"
    description = i18n.t("cli.doctor.description")
    aliases = ["diag"]
    category = "config"

    def __init__(self):
        """初始化 DoctorCommand，创建包管理器实例"""
        py_exec, _py_source = resolve_target_python()
        self.package_manager = PackageManager(python_executable=py_exec)

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument(
            "--verbose",
            action="store_true",
            help=i18n.t("cli.doctor.verbose_help"),
        )
        parser.add_argument(
            "--fix",
            action="store_true",
            help=i18n.t("cli.doctor.fix_help"),
        )

    def execute(self, args):
        rows, failed, fix_context = self._collect_diagnosis()
        self._print_report(rows, failed)

        if getattr(args, "fix", False):
            self._attempt_fixes(fix_context)

    def _collect_diagnosis(self) -> tuple[list, bool, dict]:
        """
        运行全部诊断项并收集结果

        :return: ([tuple]) 三元组 ``(rows, failed, fix_context)``：
            rows 为 (状态, 标签, 详情) 行列表；failed 为是否存在失败项；
            fix_context 携带 ``--fix`` 所需的上下文（缺失配置路径、待完善
            目标列表、不可自动修复项提示）。
        """
        pm = self.package_manager
        rows: list[tuple[str, str, str]] = []
        failed = False
        fix_context: dict = {
            "config_missing": False,
            "config_path": Path("config") / "config.toml",
            "incomplete_targets": [],
            "unrecoverable": [],
        }

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
            fix_context["unrecoverable"].append(i18n.t("cli.doctor.fix_hint_python"))

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

        # 3.5 项目虚拟环境（.venv 存在性与 pip 可用性）
        project_venv_py = resolve_target_python(Path.cwd())[0]
        venv_detected = project_venv_py != sys.executable or Path(".venv").exists()
        if venv_detected:
            venv_pip = (
                Path(".venv")
                / ("Scripts" if sys.platform == "win32" else "bin")
                / "pip.exe"
                if sys.platform == "win32"
                else Path(".venv") / "bin" / "pip"
            )
            pip_note = (
                i18n.t("cli.doctor.venv_pip_ok")
                if venv_pip.exists()
                else i18n.t("cli.doctor.venv_pip_uv")
            )
            rows.append(
                (
                    self._status(True),
                    i18n.t("cli.doctor.venv"),
                    f"{project_venv_py}（{pip_note}）",
                )
            )
        else:
            rows.append(
                (
                    self._status(True),
                    i18n.t("cli.doctor.venv"),
                    i18n.t("cli.doctor.venv_missing"),
                )
            )

        # 4. 配置文件
        config_path = fix_context["config_path"]
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
            fix_context["config_missing"] = True

        # 4.5 组件配置健康（配置文件存在 ≠ 必填项齐全：复用配置向导的
        # schema 状态检测，"装好了跑不起来"多因适配器必填项缺失）
        try:
            from ..utils.config_wizard import (
                STATUS_INCOMPLETE,
                get_target_status,
                load_config_targets,
            )

            incomplete: list[str] = []
            error_hints: list[str] = []
            for target in load_config_targets():
                status, _errors = get_target_status(target)
                # 仅"待完善"（开了但必填项缺失）判 FAIL；完全未配置属
                # 用户尚未开始配置，不算故障
                if status == STATUS_INCOMPLETE:
                    incomplete.append(target.name)
                    error_hints.extend(_errors)
                    fix_context["incomplete_targets"].append(target)
            if incomplete:
                failed = True
                rows.append(
                    (
                        self._status(False),
                        i18n.t("cli.doctor.component_config"),
                        i18n.t(
                            "cli.doctor.component_config_incomplete",
                            names=", ".join(incomplete),
                        ),
                    )
                )
                # 附带前两条校验问题（错误消息已含配置文件注释回读），
                # 把"哪个字段、文件里怎么写的"直接给到用户
                rows.extend(
                    (self._status(False), "", hint) for hint in error_hints[:2]
                )
            else:
                rows.append(
                    (
                        self._status(True),
                        i18n.t("cli.doctor.component_config"),
                        i18n.t("cli.doctor.component_config_ok"),
                    )
                )
        except Exception:
            # 发现失败（如依赖缺失）不阻塞其余诊断项
            rows.append(
                (
                    self._status(True),
                    i18n.t("cli.doctor.component_config"),
                    i18n.t("cli.doctor.component_config_skipped"),
                )
            )

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
            fix_context["unrecoverable"].append(i18n.t("cli.doctor.fix_hint_pypi"))
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

        return rows, failed, fix_context

    def _print_report(self, rows: list, failed: bool):
        """
        输出诊断报告表格与失败项摘要

        :param rows: [list] (状态, 标签, 详情) 行列表
        :param failed: [bool] 是否存在失败项
        """
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

    def _attempt_fixes(self, fix_context: dict):
        """
        对可自动修复的诊断失败项执行修复

        修复范围：缺失的 ``config.toml``（与 init 建项同源生成）与"待完善"
        组件配置（逐个拉起交互式向导）。Python 版本、网络连通等需人工
        介入的项仅输出行动建议。修复动作逐项即时反馈，不在完成后重跑
        全套诊断（避免重复网络探测）。

        :param fix_context: [dict] ``_collect_diagnosis`` 返回的修复上下文
        """
        from ErisPulse import config as app_config

        from ..utils.config_wizard import (
            STATUS_OK,
            get_target_status,
            is_interactive,
            run_wizard,
        )
        from ..utils.scaffold_text import ScaffoldText

        console.print(f"\n[bold]{i18n.t('cli.doctor.fix_section')}[/]")

        # 1. 补建缺失的 config.toml（新建直写，不涉及既有文件的编辑路径）
        config_path = fix_context["config_path"]
        if fix_context["config_missing"]:
            if config_path.exists():
                console.print(
                    f"[dim]  {i18n.t('cli.doctor.fix_config_exists')}[/]"
                )
            else:
                try:
                    config_path.parent.mkdir(parents=True, exist_ok=True)
                    config_path.write_text(
                        ScaffoldText().initial_config_toml(), encoding="utf-8"
                    )
                    console.print(
                        f"[success]  {i18n.t('cli.doctor.fix_config_created', path=config_path)}[/]"
                    )
                except OSError as e:
                    console.print(
                        f"[error]  {i18n.t('cli.doctor.fix_config_create_failed', error=e)}[/]"
                    )

        # 2. 待完善组件配置：逐个拉起向导补必填项
        targets = fix_context["incomplete_targets"]
        if targets:
            if not is_interactive():
                console.print(
                    f"[warning]  {i18n.t('cli.doctor.fix_non_interactive')}[/]"
                )
            else:
                names = ", ".join(t.name for t in targets)
                console.print(
                    f"[info]  {i18n.t('cli.doctor.fix_wizard_start', names=names)}[/]"
                )
                for target in targets:
                    try:
                        run_wizard(target, app_config)
                        status, _errors = get_target_status(target, app_config)
                    except KeyboardInterrupt:
                        console.print(f"\n[warning]  {i18n.t('cli.doctor.fix_wizard_interrupted')}[/]")
                        break
                    if status == STATUS_OK:
                        console.print(
                            f"[success]  {i18n.t('cli.doctor.fix_wizard_done', name=target.name)}[/]"
                        )
                    else:
                        console.print(
                            f"[warning]  {i18n.t('cli.doctor.fix_wizard_still_incomplete', name=target.name)}[/]"
                        )

        # 3. 不可自动修复项：输出行动建议
        hints = fix_context["unrecoverable"]
        if hints:
            console.print(f"[dim]  {i18n.t('cli.doctor.fix_unrecoverable')}[/]")
            for hint in hints:
                console.print(f"    [dim]-[/] {hint}")

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
