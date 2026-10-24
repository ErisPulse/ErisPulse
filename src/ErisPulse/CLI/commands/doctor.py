"""
Doctor 命令实现

运行环境诊断，输出 ErisPulse CLI 的 Python / 后端 / 配置 / 网络健康状态。
"""

import asyncio
import os
import platform
import shutil
import subprocess
import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path

from rich.table import Table

from ..base import Command
from ..console import console
from ..constants import CLI_UV_PROBE_TIMEOUT_SECS
from ..i18n import i18n
from ..utils import PackageManager
from ..utils.package_manager import PythonSource, is_uv_project, resolve_target_python


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

    def add_arguments(self, parser: ArgumentParser) -> None:
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

    def execute(self, args: Namespace) -> None:
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

        # 3. 目标解释器（安装目标环境）+ 解析决策链
        target_python = pm._get_target_python()
        rows.append(
            (self._status(True), i18n.t("cli.doctor.target_python"), target_python)
        )

        # 3.2 解释器解析决策链（逐级展示命中/未设置——「为什么是它」可观测）
        chain = self._resolve_python_chain()
        for label_key, detail in chain:
            rows.append(
                (self._status(True), "", f"{i18n.t(label_key)}: {detail}")
            )

        # 3.3 uv 项目面板：uv 版本 / UV_* 变量 / 项目判定依据
        rows.extend(self._uv_project_rows())

        # 3.5 项目虚拟环境（.venv 存在性与 pip 可用性）
        project_venv_py, project_venv_source = resolve_target_python(Path.cwd())
        venv_detected = (
            project_venv_source
            in (PythonSource.PROJECT_VENV, PythonSource.UV_PROJECT, PythonSource.ACTIVE_VENV)
            or Path(".venv").exists()
        )
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

        # 4.6 历史配置污染体检（升级遗留残留：影子状态键 / 游离配置节）
        try:
            pollution = self._scan_config_pollution(config_path)
            fix_context["config_pollution"] = pollution
            if pollution:
                rows.append(
                    (
                        self._status(False),
                        i18n.t("cli.doctor.pollution"),
                        i18n.t(
                            "cli.doctor.pollution_found",
                            count=len(pollution),
                            keys=", ".join(k for k, _bug, _d in pollution[:5]),
                        ),
                    )
                )
                for key, bug, desc in pollution[:5]:
                    rows.append((self._status(False), "", f"{key} ({bug}): {desc}"))
            else:
                rows.append(
                    (
                        self._status(True),
                        i18n.t("cli.doctor.pollution"),
                        i18n.t("cli.doctor.pollution_ok"),
                    )
                )
        except Exception:
            # 体检失败不阻塞其余诊断项
            fix_context["config_pollution"] = []
            rows.append(
                (
                    self._status(True),
                    i18n.t("cli.doctor.pollution"),
                    i18n.t("cli.doctor.pollution_skipped"),
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

    # 框架自身的配置节名（游离节检测的白名单；新增框架节时同步）
    _FRAMEWORK_SECTIONS = frozenset(
        {
            "server",
            "logger",
            "storage",
            "event",
            "master",
            "framework",
            "i18n",
            "scope",
            "interaction",
            "transcript",
            "modules",
            "adapters",
            "router",
        }
    )

    def _scan_config_pollution(self, config_path: Path) -> "list[tuple[str, str, str]]":
        """
        扫描历史升级遗留的配置污染（只读，不做任何修改）

        两类已知模式：
        1. **影子状态残留**（BUG-034 / #432 时代）：``ErisPulse.{modules,adapters}.status``
           下以 ``_shadow`` 结尾的键——运行时绑定曾以影子键落盘，现行版本已改
           用内存覆盖层，残留键只会误导排障
        2. **游离配置节**（BUG-046 时代）：``ErisPulse.<X>`` 顶层嵌套节既不是
           框架自身节，也没有对应组件状态键——多由嵌套模板漂移把组件配置
           写到了错误层级产生

        :param config_path: [Path] 配置文件路径
        :return: [(键路径, 来源 bug 标识, 一句话说明)] 列表；无污染 / 文件不存在为空
        """
        if not config_path.exists():
            return []
        import tomlclass

        data = tomlclass.load_path(str(config_path)).unwrap()
        root = data.get("ErisPulse")
        if not isinstance(root, dict):
            return []

        findings: list[tuple[str, str, str]] = []

        # 1. 影子状态残留
        for kind in ("modules", "adapters"):
            status = root.get(kind, {}).get("status")
            if isinstance(status, dict):
                for key in status:
                    if isinstance(key, str) and key.endswith("_shadow"):
                        path = f"ErisPulse.{kind}.status.{key}"
                        findings.append((path, "BUG-034", i18n.t("cli.doctor.pollution_shadow")))

        # 2. 游离配置节：非框架节且无对应组件状态键
        known_components = set()
        for kind in ("modules", "adapters"):
            status = root.get(kind, {}).get("status")
            if isinstance(status, dict):
                known_components.update(k for k in status if isinstance(k, str))
        for section, value in root.items():
            if (
                section not in self._FRAMEWORK_SECTIONS
                and section not in known_components
                and isinstance(value, dict)
            ):
                path = f"ErisPulse.{section}"
                findings.append((path, "BUG-046", i18n.t("cli.doctor.pollution_stray")))

        return findings

    def _fix_config_pollution(self, pollution: "list[tuple[str, str, str]]") -> None:
        """
        清理历史配置污染（tomlclass 无损路径：注释/顺序/行尾逐字节保真）

        :param pollution: [list] ``_scan_config_pollution`` 的发现列表
        """
        import tempfile

        import tomlclass

        config_path = Path("config") / "config.toml"
        doc = tomlclass.load_path(str(config_path))
        removed = 0
        for key_path, _bug, _desc in pollution:
            parts = key_path.split(".")
            node = doc
            try:
                for part in parts[:-1]:
                    node = node[part]
                del node[parts[-1]]
                removed += 1
            except Exception:
                pass
        # 原子写回（与 ConfigManager._atomic_write_text 同款：mkstemp + replace）
        text = doc.dumps()
        fd, tmp_name = tempfile.mkstemp(
            dir=str(config_path.parent), suffix=".toml.tmp"
        )
        os.close(fd)
        tmp_path = Path(tmp_name)
        try:
            with tmp_path.open("w", encoding="utf-8", newline="") as fh:
                fh.write(text)
            tmp_path.replace(config_path)
        except Exception:
            tmp_path.unlink(missing_ok=True)
            raise
        console.print(
            f"[success]  {i18n.t('cli.doctor.fix_pollution_removed', count=removed)}"
        )

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

        # 2.5 历史配置污染清理（体检发现项，需确认）
        pollution = fix_context.get("config_pollution") or []
        if pollution:
            from ..utils.interactive import confirm

            names = "\n".join(f"  - {key} ({bug})" for key, bug, _d in pollution)
            console.print(f"[info]  {i18n.t('cli.doctor.fix_pollution_prompt')}[/]")
            console.print(names)
            try:
                if confirm(i18n.t("cli.doctor.fix_pollution_confirm"), default=False):
                    self._fix_config_pollution(pollution)
                else:
                    console.print(
                        f"[dim]  {i18n.t('cli.doctor.fix_pollution_skipped')}[/]"
                    )
            except Exception as e:
                console.print(
                    f"[error]  {i18n.t('cli.doctor.fix_pollution_failed', error=e)}[/]"
                )

        # 3. 待完善组件配置：逐个拉起向导补必填项
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

    def _resolve_python_chain(self) -> "list[tuple[str, str]]":
        """
        {!--< internal-use >!--}
        解释器解析决策链展示（逐级命中/未设置）

        :return: [(i18n 键, 详情)] 列表
        """
        chain: list[tuple[str, str]] = []

        def _py_of(base: Path) -> "str | None":
            cand = base / ("Scripts" if sys.platform == "win32" else "bin") / (
                "python.exe" if sys.platform == "win32" else "python"
            )
            return str(cand) if cand.exists() else None

        env_var = os.environ.get("ERISPULSE_PYTHON")
        chain.append(
            (
                "cli.doctor.chain_env_var",
                env_var if env_var and Path(env_var).exists() else i18n.t("cli.doctor.chain_unset"),
            )
        )

        uv_env = os.environ.get("UV_PROJECT_ENVIRONMENT")
        if uv_env:
            base = Path(uv_env)
            if not base.is_absolute():
                base = Path.cwd() / base
            found = _py_of(base)
            chain.append(
                (
                    "cli.doctor.chain_uv_project",
                    found or i18n.t("cli.doctor.chain_no_python", path=uv_env),
                )
            )
        else:
            chain.append(("cli.doctor.chain_uv_project", i18n.t("cli.doctor.chain_unset")))

        project_venv = _py_of(Path.cwd() / ".venv")
        chain.append(
            (
                "cli.doctor.chain_project_venv",
                project_venv or i18n.t("cli.doctor.chain_unset"),
            )
        )

        uv_python = os.environ.get("UV_PYTHON")
        if uv_python and Path(uv_python).exists():
            chain.append(("cli.doctor.chain_uv_python", uv_python))
        else:
            chain.append(("cli.doctor.chain_uv_python", i18n.t("cli.doctor.chain_unset")))

        venv = os.environ.get("VIRTUAL_ENV")
        chain.append(
            (
                "cli.doctor.chain_virtualenv",
                (str(Path(venv))) if venv else i18n.t("cli.doctor.chain_unset"),
            )
        )
        return chain

    def _uv_project_rows(self) -> "list[tuple[str, str, str]]":
        """
        {!--< internal-use >!--}
        uv 项目面板行：uv 版本 / UV_* 变量 / 项目判定依据

        :return: [(状态, 标签, 详情)] 行列表
        """

        rows: list[tuple[str, str, str]] = []

        uv_version = "-"
        uv_cmd = shutil.which("uv")
        if uv_cmd:
            try:
                probe = subprocess.run(
                    [uv_cmd, "--version"],
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=CLI_UV_PROBE_TIMEOUT_SECS,
                )
                if probe.returncode == 0:
                    uv_version = probe.stdout.strip() or "-"
            except Exception:
                pass
        rows.append(
            (
                self._status(True),
                i18n.t("cli.doctor.uv_version"),
                uv_version,
            )
        )

        for env_name in ("UV_PROJECT_ENVIRONMENT", "UV_PYTHON", "UV_NO_SYNC"):
            value = os.environ.get(env_name)
            rows.append(
                (
                    self._status(True),
                    i18n.t("cli.doctor.uv_env"),
                    f"{env_name}={value}" if value else f"{env_name}: {i18n.t('cli.doctor.chain_unset')}",
                )
            )

        if is_uv_project(Path.cwd()):
            basis = []
            if Path("uv.lock").exists():
                basis.append("uv.lock")
            pyproject = Path("pyproject.toml")
            if pyproject.exists() and "[tool.uv]" in pyproject.read_text(
                encoding="utf-8", errors="replace"
            ):
                basis.append("[tool.uv]")
            pyvenv = Path(".venv") / "pyvenv.cfg"
            if pyvenv.exists() and any(
                ln.strip().startswith("uv =")
                for ln in pyvenv.read_text(encoding="utf-8", errors="replace").splitlines()
            ):
                basis.append("pyvenv.cfg")
            detail = i18n.t("cli.doctor.uv_project_yes", basis=", ".join(basis) or "-")
            # uv 项目但目标环境不在 uv 管理范围内：提示装错环境风险
            target_src = resolve_target_python(Path.cwd())[1]
            if target_src not in (PythonSource.UV_PROJECT, PythonSource.PROJECT_VENV):
                rows.append(
                    (
                        self._status(False),
                        i18n.t("cli.doctor.uv_project"),
                        i18n.t("cli.doctor.uv_project_mismatch", source=str(target_src)),
                    )
                )
            else:
                rows.append((self._status(True), i18n.t("cli.doctor.uv_project"), detail))
        else:
            rows.append(
                (
                    self._status(True),
                    i18n.t("cli.doctor.uv_project"),
                    i18n.t("cli.doctor.uv_project_no"),
                )
            )
        return rows

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
