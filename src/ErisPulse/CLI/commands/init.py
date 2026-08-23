"""
Init 命令实现

交互式初始化 ErisPulse 项目
"""

import asyncio
import concurrent.futures
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


def _validate_project_name(name: str) -> bool:
    """项目名称校验：仅允许字母、数字、下划线、连字符和点号"""
    return bool(name) and all(c.isalnum() or c in ("_", "-", ".") for c in name)


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
        parser.add_argument("--project-name", "-n", help=i18n.t("cli.init.name_help"))
        parser.add_argument(
            "--quick", "-q", action="store_true", help=i18n.t("cli.init.quick_help")
        )
        parser.add_argument(
            "--force", "-f", action="store_true", help=i18n.t("cli.init.force_help")
        )
        parser.add_argument(
            "--here",
            action="store_true",
            help=i18n.t("cli.init.here_help"),
        )
        parser.add_argument(
            "--no-uv", action="store_true", help=i18n.t("cli.init.nouv_help")
        )

    def execute(self, args):
        self.no_uv = getattr(args, "no_uv", False)
        here = getattr(args, "here", False)

        if args.quick:
            if here:
                name = args.project_name or Path.cwd().name
                success = self._init_project(name, [], in_current_dir=True)
            elif args.project_name:
                success = self._init_project(args.project_name, [])
            else:
                success = self._interactive_init(args.project_name, args.force, here)
        else:
            success = self._interactive_init(args.project_name, args.force, here)

        if success:
            console.print(f"[success]  {i18n.t('cli.init.complete')}[/]")
        else:
            console.print(f"[error]  {i18n.t('cli.init.failed')}[/]")
            sys.exit(1)

    def _init_project(
        self,
        project_name: str,
        adapter_list: list | None = None,
        in_current_dir: bool = False,
    ) -> bool:
        """
        创建项目目录结构并生成配置文件

        :param project_name: [str] 项目名称
        :param adapter_list: [list] 适配器名称列表 (默认: None)
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

            project_path = Path(project_name)
            display_name = project_name

            if project_path.exists():
                if project_path.is_dir():
                    console.print(
                        f"[warning]  {i18n.t('cli.init.dir_exists', name=project_name)}[/]"
                    )
                else:
                    console.print(
                        f"[error]  {i18n.t('cli.init.file_exists_not_dir', name=project_name)}[/]"
                    )
                    return False
            else:
                project_path.mkdir()
                console.print(
                    f"[success]  {i18n.t('cli.init.created_dir', name=project_name)}[/]"
                )

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
                        "# 将你的证书/密钥 PEM 内容粘贴到本文件，"
                        "或在配置中改用 ssl_cert/ssl_key 内联填写\n",
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

            console.print(
                f"[success]  {i18n.t('cli.init.display_success', name=display_name)}[/]"
            )
            console.print()
            console.print(Text(i18n.t("cli.create.next_steps"), style="bold"))
            if in_current_dir:
                console.print(
                    f"    · {i18n.t('cli.init.edit_config', path='config/config.toml')}"
                )
                console.print(f"    · {i18n.t('cli.init.run_direct')}")
            else:
                console.print(
                    f"    · {i18n.t('cli.init.edit_config', path=f'{display_name}/config/config.toml')}"
                )
                console.print(
                    f"    · {i18n.t('cli.init.cd_and_run', dir=display_name)}"
                )
            return True

        except Exception as e:
            console.print(
                f"[error]  {i18n.t('cli.init.init_project_failed', error=e)}[/]"
            )
            return False

    @staticmethod
    def _get_full_example_config(adapter_list=None):
        """
        生成完整的配置示例文本

        配置注释跟随 CLI 语言（缺失语言回退英文），
        文案键集中于 ``scaffold_text`` 的 ``cfg.*`` 键族维护。

        :param adapter_list: [list] 适配器名称列表 (默认: None)
        :return: [str] 完整配置示例字符串
        """
        from ..utils.scaffold_text import ScaffoldText

        st = ScaffoldText()
        lines = [
            st.t("cfg.header.title"),
            st.t("cfg.header.desc"),
            st.t("cfg.header.usage"),
            "",
            st.t("cfg.section.server"),
            "",
            "[ErisPulse.server]",
            f'host = "0.0.0.0"              # {st.t("cfg.server.host")}',
            f"port = 8000                   # {st.t('cfg.server.port')}",
            f"auto_start = true             # {st.t('cfg.server.auto_start')}",
            f'ssl_certfile = "config/ssl/cert.pem"   # {st.t("cfg.server.ssl_certfile")}',
            f'ssl_keyfile = "config/ssl/key.pem"    # {st.t("cfg.server.ssl_keyfile")}',
            st.t("cfg.server.ssl_inline_hint"),
            '# ssl_cert = """-----BEGIN CERTIFICATE-----',
            "# ...",
            '# -----END CERTIFICATE-----"""',
            '# ssl_key = """-----BEGIN PRIVATE KEY-----',
            "# ...",
            '# -----END PRIVATE KEY-----"""',
            "",
            st.t("cfg.section.logger"),
            "",
            "[ErisPulse.logger]",
            f'level = "INFO"                # {st.t("cfg.logger.level")}',
            f"log_files = []                # {st.t('cfg.logger.log_files')}",
            f'log_dir = ""                  # {st.t("cfg.logger.log_dir")}',
            f'log_rotation = "size"         # {st.t("cfg.logger.log_rotation")}',
            f"log_max_size_mb = 10          # {st.t('cfg.logger.log_max_size_mb')}",
            f"log_backup_count = 5          # {st.t('cfg.logger.log_backup_count')}",
            f'log_rotation_when = "midnight"  # {st.t("cfg.logger.log_rotation_when")}',
            f"memory_limit = 1000           # {st.t('cfg.logger.memory_limit')}",
            "",
            st.t("cfg.section.storage"),
            "",
            "[ErisPulse.storage]",
            f"use_global_db = false         # {st.t('cfg.storage.use_global_db')}",
            "",
            st.t("cfg.section.event"),
            "",
            "[ErisPulse.event.message]",
            f"ignore_self = true            # {st.t('cfg.event.ignore_self')}",
            "",
            "[ErisPulse.event.command]",
            f'prefix = "/"                  # {st.t("cfg.command.prefix")}',
            f"case_sensitive = true         # {st.t('cfg.command.case_sensitive')}",
            f"allow_space_prefix = false    # {st.t('cfg.command.allow_space_prefix')}",
            f"must_at_bot = false           # {st.t('cfg.command.must_at_bot')}",
            "",
            st.t("cfg.section.framework"),
            "",
            "[ErisPulse.framework]",
            f"enable_lazy_loading = true     # {st.t('cfg.framework.enable_lazy_loading')}",
            f'plugins_dir = "plugins"        # {st.t("cfg.framework.plugins_dir")}',
            f"uninit_timeout = 30            # {st.t('cfg.framework.uninit_timeout')}",
            f"                                {st.t('cfg.framework.uninit_timeout_line1')}",
            f"                                {st.t('cfg.framework.uninit_timeout_line2')}",
            f"strict_mode = false            # {st.t('cfg.framework.strict_mode')}",
            f"strict_mode_exceptions = {{ modules = [], adapters = [] }}  # {st.t('cfg.framework.strict_mode_exceptions')}",
            f"handler_max_concurrency = 64   # {st.t('cfg.framework.handler_max_concurrency')}",
            f"proactive_gc_interval = 300    # {st.t('cfg.framework.proactive_gc_interval')}",
            f"proactive_gc_generation = 2    # {st.t('cfg.framework.proactive_gc_generation')}",
            f"proactive_gc_full_every = 10   # {st.t('cfg.framework.proactive_gc_full_every')}",
            f"proactive_gc_memory_growth_mb = 100  # {st.t('cfg.framework.proactive_gc_memory_growth_mb')}",
            f"proactive_gc_idle_only = true  # {st.t('cfg.framework.proactive_gc_idle_only')}",
            f"proactive_gc_gen0_min = 100    # {st.t('cfg.framework.proactive_gc_gen0_min')}",
            f"offline_bot_expiry = 3600      # {st.t('cfg.framework.offline_bot_expiry')}",
            "",
            st.t("cfg.section.router"),
            "",
            "[ErisPulse.router.cors]",
            "enabled = false",
            'allow_origins = ["*"]',
            'allow_methods = ["*"]',
            'allow_headers = ["*"]',
            "allow_credentials = false",
            "max_age = 600",
            "",
            "[ErisPulse.router.security]",
            "enabled = false",
            "",
            "[ErisPulse.router.security.headers]",
            'X-Content-Type-Options = "nosniff"',
            'X-Frame-Options = "DENY"',
            "",
            st.t("cfg.section.adapter_status"),
            "",
            "[ErisPulse.adapters.status]",
        ]

        if adapter_list:
            lines.extend(f"# {adapter} = false" for adapter in adapter_list)
        else:
            lines.extend(
                [
                    "# yunhu = false",
                    "# telegram = false",
                    "# onebot11 = false",
                ]
            )

        lines.extend(
            [
                "",
                st.t("cfg.section.module_status"),
                "",
                "[ErisPulse.modules.status]",
                "# MyModule = true",
                "",
            ]
        )

        return "\n".join(lines)

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
            console.print(
                f"[warning]  {i18n.t('cli.init.fetch_remote_failed', error=e)}[/]"
            )

        return {
            "yunhu": i18n.t("cli.init.adapter_desc_yunhu"),
            "telegram": i18n.t("cli.init.adapter_desc_telegram"),
            "onebot11": i18n.t("cli.init.adapter_desc_onebot11"),
            "email": i18n.t("cli.init.adapter_desc_email"),
        }

    def _interactive_init(
        self, project_name: str | None = None, force: bool = False, here: bool = False
    ) -> bool:
        """
        交互式初始化项目，引导用户配置项目位置及基本参数

        :param project_name: [str] 项目名称 (默认: None)
        :param force: [bool] 是否强制覆盖已存在目录 (默认: False)
        :param here: [bool] 是否在当前目录初始化 (默认: False)
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
                location_choice = IntPrompt.ask(
                    i18n.t("cli.create.select_prompt"), default=2, choices=["1", "2"]
                )
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
                    i18n.t("cli.init.name_prompt"),
                    default=project_name or "my_erispulse_project",
                    validate=_validate_project_name,
                    error_msg=i18n.t("cli.init.name_error"),
                )
                project_path = Path(project_name)
                if project_path.exists() and not force:
                    if not Confirm.ask(
                        f"  [cyan]{i18n.t('cli.init.dir_overwrite_prompt', name=project_name)}[/]",
                        default=False,
                    ):
                        console.print(f"[info]  {i18n.t('cli.init.cancelled')}[/]")
                        return False

            if not self._init_project(project_name, [], in_current_dir=in_current_dir):
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
            console.print(
                f"  {i18n.t('cli.init.listen_host')} [dim]({current_host})[/]"
            )
            new_host = _input(">")
            if new_host:
                config.setConfig("ErisPulse.server.host", new_host)

            current_port = str(config.getConfig("ErisPulse.server.port", 8000))
            console.print(
                f"  {i18n.t('cli.init.listen_port')} [dim]({current_port})[/]"
            )
            new_port = _input(">")
            while new_port:
                try:
                    config.setConfig("ErisPulse.server.port", int(new_port))
                    break
                except ValueError:
                    console.print(
                        f"[warning]  {i18n.t('cli.init.invalid_port', port=new_port)}[/]"
                    )
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

        with console.status(
            f"[bold green]{i18n.t('cli.init.fetching_adapters')}...", spinner="dots"
        ):
            try:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run, self._fetch_available_adapters()
                    )
                    adapters = future.result(timeout=10)
            except Exception as e:
                console.print(
                    f"[error]  {i18n.t('cli.init.fetch_adapters_failed', error=e)}[/]"
                )
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
                console.print(
                    f"[warning]  {i18n.t('cli.init.invalid_index', idx=idx)}[/]"
                )

        for name, _ in adapter_list:
            if name not in enabled:
                config.setConfig(f"ErisPulse.adapters.status.{name}", False)

        console.print(
            f"[dim]  {i18n.t('cli.init.adapters_enabled', count=len(enabled))}[/]"
        )

        if enabled and Confirm.ask(
            f"  [cyan]{i18n.t('cli.init.install_selected_prompt')}[/]", default=True
        ):
            self._install_adapters(enabled, adapters)

    def _install_adapters(self, adapter_names, adapters_info):
        """
        安装选中的适配器

        :param adapter_names: [list] 适配器简称列表
        :param adapters_info: [dict] 适配器信息
        """
        pkg_manager = PackageManager()
        pkg_manager.no_uv = getattr(self, "no_uv", False)
        for adapter_name in adapter_names:
            package_name = None
            try:
                remote_packages = pkg_manager._cache.get("remote_packages", {})
                if not remote_packages:
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            asyncio.run, pkg_manager.get_remote_packages()
                        )
                        remote_packages = future.result(timeout=10)
                if adapter_name in remote_packages.get("adapters", {}):
                    package_name = remote_packages["adapters"][adapter_name].get(
                        "package"
                    )
            except Exception:
                pass

            if not package_name:
                package_name = adapter_name

            console.print(
                f"[info]  {i18n.t('cli.init.installing_adapter', name=adapter_name, package=package_name)}[/]"
            )
            success = pkg_manager.install_package([package_name])

            if not success:
                console.print(
                    f"[error]  {i18n.t('cli.init.adapter_install_failed', name=adapter_name)}[/]"
                )
