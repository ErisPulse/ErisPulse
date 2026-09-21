"""
Init 命令实现

交互式初始化 ErisPulse 项目
"""

import asyncio
import concurrent.futures
import re
import sys
from argparse import ArgumentParser
from pathlib import Path

from rich.prompt import Confirm, IntPrompt
from rich.text import Text

from ..base import Command
from ..console import console
from ..i18n import i18n
from ..utils import PackageManager
from ..utils.display import _input, prompt_validated, section_header
from ..utils.package_manager import (
    append_pyproject_dependencies,
    create_project_venv,
    resolve_target_python,
    uv_add,
    warn_if_uv_isolated,
)


def _validate_project_name(name: str) -> bool:
    """项目名称校验：仅允许字母、数字、下划线、连字符和点号"""
    return bool(name) and all(c.isalnum() or c in ("_", "-", ".") for c in name)


def _validate_project_path(value: str) -> bool:
    """项目路径校验：末段（项目名）须为合法名称，父目录部分不限制"""
    from pathlib import PurePath

    if not value or value.strip() != value:
        return False
    try:
        Path(value)
    except (ValueError, OSError):
        return False
    return _validate_project_name(PurePath(value).name)


class InitCommand(Command):
    """
    init 命令

    交互式初始化 ErisPulse 项目
    """

    name = "init"
    description = i18n.t("cli.init.description")
    aliases = []

    def __init__(self):
        """
        初始化 InitCommand 实例，创建包管理器
        """
        self.package_manager = PackageManager()

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument(
            "path",
            nargs="?",
            default=None,
            help=i18n.t("cli.init.path_help"),
        )
        parser.add_argument("--project-name", "-n", help=i18n.t("cli.init.name_help"))
        parser.add_argument("--quick", "-q", action="store_true", help=i18n.t("cli.init.quick_help"))
        parser.add_argument("--force", "-f", action="store_true", help=i18n.t("cli.init.force_help"))
        parser.add_argument(
            "--here",
            action="store_true",
            help=i18n.t("cli.init.here_help"),
        )
        parser.add_argument("--no-uv", action="store_true", help=i18n.t("cli.init.nouv_help"))
        parser.add_argument("--no-venv", action="store_true", help=i18n.t("cli.init.novenv_help"))
        parser.add_argument(
            "--path",
            dest="path_dir",
            default=None,
            help=i18n.t("cli.init.path_dir_help"),
        )

    def execute(self, args):
        self.no_uv = getattr(args, "no_uv", False)
        self.no_venv = getattr(args, "no_venv", False)
        here = getattr(args, "here", False)
        path_arg = getattr(args, "path", None)
        path_dir = getattr(args, "path_dir", None)

        # uv 隔离环境检测：无项目的 `uv run` 语义下安装的包不会持久化
        warn_if_uv_isolated()

        # 解析创建位置与项目名（优先级：--here > 位置 path > --path/-n > 交互）
        target_dir: Path | None = None
        project_name = args.project_name

        if path_dir:
            target_dir = Path(path_dir)
        if path_arg:
            p = Path(path_arg)
            if project_name is None:
                project_name = p.name
            if target_dir is None and str(p.parent) not in (".", ""):
                target_dir = p.parent

        create_venv = not self.no_venv

        if args.quick:
            if here:
                name = project_name or Path.cwd().name
                success = self._init_project(
                    name, [], in_current_dir=True, create_venv=create_venv
                )
            elif project_name:
                success = self._init_project(
                    project_name, [], target_dir=target_dir, create_venv=create_venv
                )
            else:
                success = self._interactive_init(
                    args.project_name,
                    args.force,
                    here,
                    target_dir=target_dir,
                    create_venv=create_venv,
                )
        else:
            success = self._interactive_init(
                project_name,
                args.force,
                here,
                target_dir=target_dir,
                create_venv=create_venv,
            )

        if success:
            console.print(f"[success]  {i18n.t('cli.init.complete')}[/]")
        else:
            console.print(f"[error]  {i18n.t('cli.init.failed')}[/]")
            sys.exit(1)

    def _init_project(
        self,
        project_name: str,
        adapter_list: list | None = None,
        target_dir: Path | None = None,
        create_venv: bool = True,
        git_init: bool = False,
        in_current_dir: bool = False,
    ) -> bool:
        """
        创建项目目录结构并生成配置文件、依赖清单与虚拟环境

        :param project_name: [str] 项目名称
        :param adapter_list: [list] 适配器名称列表 (默认: None)
        :param target_dir: [Path | None] 项目父目录 (默认: None，即当前目录)
        :param create_venv: [bool] 是否创建虚拟环境并安装依赖 (默认: True)
        :param git_init: [bool] 是否初始化 git 仓库 (默认: False)
        :param in_current_dir: [bool] 是否在当前目录初始化 (默认: False)
        :return: [bool] 初始化成功返回 True，失败返回 False
        """
        if in_current_dir:
            project_path = Path()
            display_name = project_name or Path.cwd().name
        else:
            if not _validate_project_name(project_name):
                console.print(f"[error]  {i18n.t('cli.init.invalid_name')}[/]")
                return False

            if target_dir is not None:
                target_dir = Path(target_dir)
                target_dir.mkdir(parents=True, exist_ok=True)
                project_path = target_dir / project_name
            else:
                project_path = Path(project_name)
            display_name = project_name

            if project_path.exists():
                if project_path.is_dir():
                    console.print(f"[warning]  {i18n.t('cli.init.dir_exists', name=project_name)}[/]")
                else:
                    console.print(f"[error]  {i18n.t('cli.init.file_exists_not_dir', name=project_name)}[/]")
                    return False
            else:
                project_path.mkdir(parents=True, exist_ok=True)
                console.print(f"[success]  {i18n.t('cli.init.created_dir', name=project_name)}[/]")

        try:
            for dir_name in ["config", "logs"]:
                (project_path / dir_name).mkdir(exist_ok=True)
            # SSL 证书默认目录：跟随项目运行目录走，配置里用相对路径引用
            ssl_dir = project_path / "config" / "ssl"
            ssl_dir.mkdir(exist_ok=True)
            for ssl_name in ("cert.pem", "key.pem"):
                ssl_file = ssl_dir / ssl_name
                if not ssl_file.exists():
                    ssl_file.write_text(
                        "# 将你的证书/密钥 PEM 内容粘贴到本文件，或在配置中改用 ssl_cert/ssl_key 内联填写\n",
                        encoding="utf-8",
                    )

            config_file = project_path / "config" / "config.toml"
            if not config_file.exists():
                with config_file.open("w", encoding="utf-8") as f:
                    f.write("# ErisPulse 配置文件\n")
                    f.write("# 完整配置示例请参考 config.full.example\n\n")
                    f.write("[ErisPulse.server]\n")
                    f.write('host = "0.0.0.0"\n')
                    f.write("port = 8000\n\n")
                    f.write("[ErisPulse.logger]\n")
                    f.write('level = "INFO"\n')
                    if adapter_list:
                        f.write("\n[ErisPulse.adapters.status]\n")
                        f.writelines(f"{adapter} = false\n" for adapter in adapter_list)

            example_file = project_path / "config" / "config.full.example"
            if not example_file.exists():
                with example_file.open("w", encoding="utf-8") as f:
                    f.write(self._get_full_example_config(adapter_list))

            main_file = project_path / "main.py"
            if not main_file.exists():
                with main_file.open("w", encoding="utf-8") as f:
                    f.write(f'"""\n{display_name} 主程序\n\n')
                    f.write("这是 ErisPulse 自动生成的主程序文件\n")
                    f.write('"""\n\n')
                    f.write("import asyncio\n")
                    f.write("from ErisPulse import sdk\n\n")
                    f.write("async def main():\n")
                    f.write("    await sdk.run(keep_running=True)\n\n")
                    f.write('if __name__ == "__main__":\n')
                    f.write("    asyncio.run(main())\n")

            # ---- pyproject.toml（依赖清单）----
            pyproject_file = project_path / "pyproject.toml"
            if not pyproject_file.exists():
                pkg_name = re.sub(r"[^a-zA-Z0-9_.]", "_", display_name)
                with pyproject_file.open("w", encoding="utf-8") as f:
                    f.write("[project]\n")
                    f.write(f'name = "{pkg_name}"\n')
                    f.write('version = "0.1.0"\n')
                    f.write('description = "ErisPulse project"\n')
                    f.write('requires-python = ">=3.10"\n')
                    f.write("dependencies = [\n")
                    f.write('    "erispulse>=2.8.3",\n')
                    for adapter in adapter_list or []:
                        f.write(f'    "{adapter}",\n')
                    f.write("]\n")
                console.print(f"[success]  {i18n.t('cli.init.pyproject_created')}[/]")

            # ---- .gitignore ----
            gitignore_file = project_path / ".gitignore"
            if not gitignore_file.exists():
                with gitignore_file.open("w", encoding="utf-8") as f:
                    f.write(
                        "# Python\n"
                        "__pycache__/\n"
                        "*.py[cod]\n"
                        "*$py.class\n"
                        "build/\n"
                        "dist/\n"
                        "*.egg-info/\n"
                        ".eggs/\n"
                        "\n"
                        "# 虚拟环境与本地环境\n"
                        ".venv/\n"
                        "venv/\n"
                        "env/\n"
                        ".env\n"
                        "\n"
                        "# 工具缓存\n"
                        ".pytest_cache/\n"
                        ".mypy_cache/\n"
                        ".ruff_cache/\n"
                        ".coverage\n"
                        "coverage.xml\n"
                        "htmlcov/\n"
                        "\n"
                        "# ErisPulse 运行时数据（配置与日志含敏感信息，不入库）\n"
                        "config/\n"
                        "logs/\n"
                        "\n"
                        "# 编辑器与系统文件\n"
                        ".idea/\n"
                        ".vscode/\n"
                        "*.swp\n"
                        ".DS_Store\n"
                    )
                console.print(f"[success]  {i18n.t('cli.init.gitignore_created')}[/]")

            # ---- README.md ----
            readme_file = project_path / "README.md"
            if not readme_file.exists():
                with readme_file.open("w", encoding="utf-8") as f:
                    f.write(f"# {display_name}\n\nErisPulse 项目。\n\n```bash\nepsdk run\n```\n")
                console.print(f"[success]  {i18n.t('cli.init.readme_created')}[/]")

            # ---- 虚拟环境与依赖安装 ----
            if create_venv:
                console.print(f"[info]  {i18n.t('cli.init.venv_creating')}[/]")
                venv_python = None
                if uv_add(project_path, ["erispulse>=2.8.3"]):
                    # uv add 自动创建 .venv、安装依赖并写入 pyproject 依赖清单
                    venv_python = resolve_target_python(project_path)[0]
                    console.print(f"[success]  {i18n.t('cli.init.venv_created')}[/]")
                    console.print(f"[success]  {i18n.t('cli.init.deps_installed')}[/]")
                else:
                    venv_python = create_project_venv(project_path)
                    if venv_python:
                        console.print(f"[success]  {i18n.t('cli.init.venv_created')}[/]")
                        pm = PackageManager(python_executable=venv_python)
                        if pm.install_package(["erispulse>=2.8.3"]):
                            append_pyproject_dependencies(project_path, ["erispulse>=2.8.3"])
                            console.print(f"[success]  {i18n.t('cli.init.deps_installed')}[/]")
                        else:
                            console.print(
                                f"[warning]  {i18n.t('cli.init.deps_failed', packages='erispulse')}[/]"
                            )
                    else:
                        console.print(f"[warning]  {i18n.t('cli.init.venv_failed')}[/]")
                self._project_python = venv_python
                self._project_path = project_path

            # ---- git 仓库 ----
            if git_init:
                import shutil as _shutil
                import subprocess as _subprocess

                if _shutil.which("git") is None:
                    console.print(
                        f"[warning]  {i18n.t('cli.init.git_not_found')}[/]"
                    )
                else:
                    result = _subprocess.run(
                        ["git", "init"],
                        cwd=str(project_path),
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    if result.returncode == 0:
                        console.print(f"[success]  {i18n.t('cli.init.git_inited')}[/]")
                    else:
                        console.print(
                            f"[warning]  {i18n.t('cli.init.git_failed', error=(result.stderr or result.stdout).strip()[:120])}[/]"
                        )

            console.print(f"[success]  {i18n.t('cli.init.display_success', name=display_name)}[/]")
            console.print()
            console.print(Text(i18n.t("cli.create.next_steps"), style="bold"))
            if in_current_dir:
                console.print(f"    · {i18n.t('cli.init.edit_config', path='config/config.toml')}")
                console.print(f"    · {i18n.t('cli.init.run_direct')}")
            else:
                display_dir = display_name if target_dir is None else str(Path(target_dir) / display_name)
                console.print(f"    · {i18n.t('cli.init.edit_config', path=f'{display_dir}/config/config.toml')}")
                console.print(f"    · {i18n.t('cli.init.cd_and_run', dir=display_dir)}")
            return True

        except Exception as e:
            console.print(f"[error]  {i18n.t('cli.init.init_project_failed', error=e)}[/]")
            return False

    @staticmethod
    def _get_full_example_config(adapter_list=None):
        """
        生成完整的配置示例文本

        生成逻辑收归 ``ErisPulse.runtime.example_config``（框架运行与 CLI 共用：
        含自维护首行标记、静态框架段与已安装组件声明式段）。此处仅保留调用入口。

        :param adapter_list: [list] 适配器名称列表 (默认: None)
        :return: [str] 完整配置示例字符串
        """
        from ErisPulse.runtime.example_config import render_full_example

        return render_full_example(adapter_list=adapter_list)


    async def _fetch_available_adapters(self):
        """
        获取可用的适配器列表

        :return: [dict] 适配器名称到描述的映射，获取失败时返回内置默认列表
        """
        try:
            remote_packages = await self.package_manager.get_remote_packages()
            adapters = {}
            for name, info in remote_packages.get("adapters", {}).items():
                adapters[name] = info.get("description", "")
            if adapters:
                return adapters
        except Exception as e:
            console.print(f"[warning]  {i18n.t('cli.init.fetch_remote_failed', error=e)}[/]")

        return {
            "yunhu": i18n.t("cli.init.adapter_desc_yunhu"),
            "telegram": i18n.t("cli.init.adapter_desc_telegram"),
            "onebot11": i18n.t("cli.init.adapter_desc_onebot11"),
            "email": i18n.t("cli.init.adapter_desc_email"),
        }

    def _interactive_init(
        self,
        project_name: str | None = None,
        force: bool = False,
        here: bool = False,
        target_dir: Path | None = None,
        create_venv: bool = True,
    ) -> bool:
        """
        交互式初始化项目，引导用户配置项目位置及基本参数

        :param project_name: [str] 项目名称 (默认: None)
        :param force: [bool] 是否强制覆盖已存在目录 (默认: False)
        :param here: [bool] 是否在当前目录初始化 (默认: False)
        :param target_dir: [Path | None] 项目父目录 (默认: None)
        :param create_venv: [bool] 是否创建虚拟环境并安装依赖 (默认: True)
        :return: [bool] 初始化成功返回 True，失败返回 False
        """
        try:
            in_current_dir = here
            if not here:
                section_header(i18n.t("cli.init.location_section"))
                console.print(
                    f"    [bold]1.[/] {i18n.t('cli.init.location_option_current')}   [dim]— {i18n.t('cli.init.location_desc_current')}[/]"
                )
                console.print(
                    f"    [bold]2.[/] {i18n.t('cli.init.location_option_new')}     [dim]— {i18n.t('cli.init.location_desc_new')}[/]"
                )
                console.print()
                location_choice = IntPrompt.ask(i18n.t("cli.create.select_prompt"), default=2, choices=["1", "2"])
                console.print()
                in_current_dir = location_choice == 1

            if in_current_dir:
                default_name = Path.cwd().name
                project_name = prompt_validated(
                    i18n.t("cli.init.name_prompt"),
                    default=project_name or default_name,
                    validate=_validate_project_name,
                    error_msg=i18n.t("cli.init.name_error"),
                )
                project_path = Path()
            else:
                project_name = prompt_validated(
                    i18n.t("cli.init.name_with_path_hint"),
                    default=project_name or "my_erispulse_project",
                    validate=_validate_project_path,
                    error_msg=i18n.t("cli.init.name_error"),
                )
                p = Path(project_name)
                if target_dir is None and str(p.parent) not in (".", ""):
                    target_dir = p.parent
                project_name = p.name
                project_path = (Path(target_dir) if target_dir else Path()) / project_name
                if project_path.exists() and not force:
                    if not Confirm.ask(
                        f"  [cyan]{i18n.t('cli.init.dir_overwrite_prompt', name=project_name)}[/]",
                        default=False,
                    ):
                        console.print(f"[info]  {i18n.t('cli.init.cancelled')}[/]")
                        return False

            # 虚拟环境与 git 仓库问询
            if not getattr(self, "no_venv", False):
                create_venv = Confirm.ask(
                    f"  [cyan]{i18n.t('cli.init.venv_prompt')}[/]", default=True
                )
            git_init = Confirm.ask(
                f"  [cyan]{i18n.t('cli.init.git_prompt')}[/]", default=False
            )

            if not self._init_project(
                project_name,
                [],
                target_dir=target_dir,
                create_venv=create_venv,
                git_init=git_init,
                in_current_dir=in_current_dir,
            ):
                return False

            from ErisPulse import config

            project_config_path = project_path / "config" / "config.toml"
            config.CONFIG_FILE = str(project_config_path)
            config.reload()

            section_header(i18n.t("cli.init.basic_config"))

            current_level = config.getConfig("ErisPulse.logger.level", "INFO")
            console.print(f"  {i18n.t('cli.init.log_level')} [dim]({current_level})[/]")
            new_level = _input(">")
            if new_level and new_level.upper() in [
                "DEBUG",
                "INFO",
                "WARNING",
                "ERROR",
                "CRITICAL",
            ]:
                config.setConfig("ErisPulse.logger.level", new_level.upper())

            current_host = config.getConfig("ErisPulse.server.host", "0.0.0.0")
            console.print(f"  {i18n.t('cli.init.listen_host')} [dim]({current_host})[/]")
            new_host = _input(">")
            if new_host:
                config.setConfig("ErisPulse.server.host", new_host)

            current_port = str(config.getConfig("ErisPulse.server.port", 8000))
            console.print(f"  {i18n.t('cli.init.listen_port')} [dim]({current_port})[/]")
            new_port = _input(">")
            while new_port:
                try:
                    config.setConfig("ErisPulse.server.port", int(new_port))
                    break
                except ValueError:
                    console.print(f"[warning]  {i18n.t('cli.init.invalid_port', port=new_port)}[/]")
                    new_port = _input(">")

            if Confirm.ask(
                f"\n  [cyan]{i18n.t('cli.init.configure_adapters_prompt')}[/]",
                default=True,
            ):
                self._configure_adapters(project_path)

            config.force_save()
            return True

        except Exception as e:
            console.print(f"[error]  {i18n.t('cli.init.init_failed', error=e)}[/]")
            return False

    def _configure_adapters(self, project_path: Path):
        """
        交互式配置适配器

        :param project_path: [Path] 项目路径
        """
        from ErisPulse import config

        with console.status(f"[bold green]{i18n.t('cli.init.fetching_adapters')}...", spinner="dots"):
            try:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self._fetch_available_adapters())
                    adapters = future.result(timeout=10)
            except Exception as e:
                console.print(f"[error]  {i18n.t('cli.init.fetch_adapters_failed', error=e)}[/]")
                return

        if not adapters:
            console.print(f"[dim]  {i18n.t('cli.init.no_adapters')}[/]")
            return

        section_header(i18n.t("cli.init.adapters_section"))
        adapter_list = list(adapters.items())
        for i, (name, desc) in enumerate(adapter_list, 1):
            console.print(f"    [bold]{i}.[/] {name} [dim]— {desc}[/]")

        # 输入非法序号时保留输入并重新提示，留空跳过
        console.print(f"  {i18n.t('cli.init.select_adapters_prompt')}")
        indices = None
        while indices is None:
            selected = _input(">")
            if not selected.strip():
                console.print(f"[info]  {i18n.t('cli.init.no_adapters_selected')}[/]")
                return
            try:
                indices = [int(idx.strip()) for idx in selected.split(",")]
            except ValueError:
                console.print(f"[warning]  {i18n.t('cli.init.invalid_number')}[/]")

        enabled = []
        for idx in indices:
            if 1 <= idx <= len(adapter_list):
                name = adapter_list[idx - 1][0]
                enabled.append(name)
                config.setConfig(f"ErisPulse.adapters.status.{name}", True)
            else:
                console.print(f"[warning]  {i18n.t('cli.init.invalid_index', idx=idx)}[/]")

        for name, _ in adapter_list:
            if name not in enabled:
                config.setConfig(f"ErisPulse.adapters.status.{name}", False)

        console.print(f"[dim]  {i18n.t('cli.init.adapters_enabled', count=len(enabled))}[/]")

        if enabled and Confirm.ask(f"  [cyan]{i18n.t('cli.init.install_selected_prompt')}[/]", default=True):
            self._install_adapters(enabled, adapters)

    def _install_adapters(self, adapter_names, adapters_info):
        """
        安装选中的适配器

        安装成功后衔接交互式配置向导（写入新项目的 config.toml）

        :param adapter_names: [list] 适配器简称列表
        :param adapters_info: [dict] 适配器信息
        """
        from ErisPulse import config

        from ..utils import config_wizard

        project_python = getattr(self, "_project_python", None)
        pkg_manager = PackageManager(python_executable=project_python)
        pkg_manager.no_uv = getattr(self, "no_uv", False)
        for adapter_name in adapter_names:
            package_name = None
            try:
                remote_packages = pkg_manager._cache.get("remote_packages", {})
                if not remote_packages:
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, pkg_manager.get_remote_packages())
                        remote_packages = future.result(timeout=10)
                if adapter_name in remote_packages.get("adapters", {}):
                    package_name = remote_packages["adapters"][adapter_name].get("package")
            except Exception:
                pass

            if not package_name:
                package_name = adapter_name

            console.print(
                f"[info]  {i18n.t('cli.init.installing_adapter', name=adapter_name, package=package_name)}[/]"
            )
            success = pkg_manager.install_package([package_name])

            if not success:
                console.print(f"[error]  {i18n.t('cli.init.adapter_install_failed', name=adapter_name)}[/]")
            elif config_wizard.is_interactive():
                # 安装成功后衔接配置向导，写入已重定向到新项目的 config.toml
                try:
                    config_wizard.post_install_configure([package_name], config)
                except Exception as e:
                    console.print(f"[warning]  {i18n.t('cli.config.post_install_failed', error=e)}[/]")
