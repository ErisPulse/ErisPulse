"""
Init 命令实现

交互式初始化 ErisPulse 项目
"""

import asyncio
import concurrent.futures
import subprocess
import sys
from argparse import ArgumentParser
from pathlib import Path

from rich.prompt import Confirm, Prompt
from rich.text import Text

from ..console import console
from ..utils import PackageManager
from ..utils.display import section_header, _input
from ..base import Command


class InitCommand(Command):
    name = "init"
    description = "初始化 ErisPulse 项目"

    def __init__(self):
        self.package_manager = PackageManager()

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument("--project-name", "-n", help="项目名称 (可选)")
        parser.add_argument(
            "--quick", "-q", action="store_true", help="快速模式，跳过交互式配置"
        )
        parser.add_argument(
            "--force", "-f", action="store_true", help="强制覆盖现有配置"
        )

    def execute(self, args):
        if args.quick and args.project_name:
            success = self._init_project(args.project_name, [])
        else:
            success = self._interactive_init(args.project_name, args.force)

        if success:
            console.print("[success]  项目初始化完成[/]")
        else:
            console.print("[error]  项目初始化失败[/]")
            sys.exit(1)

    def _init_project(self, project_name: str, adapter_list: list = None) -> bool:
        if not project_name or not all(
            c.isalnum() or c in ("_", "-", ".") for c in project_name
        ):
            console.print(
                "[error]  项目名称只能包含字母、数字、下划线、连字符和点号[/]"
            )
            return False

        try:
            project_path = Path(project_name)
            if project_path.exists():
                if project_path.is_dir():
                    console.print(f"[warning]  目录 {project_name} 已存在[/]")
                else:
                    console.print(f"[error]  文件 {project_name} 已存在且不是目录[/]")
                    return False
            else:
                project_path.mkdir()
                console.print(f"[success]  创建项目目录: {project_name}[/]")

            for dir_name in ["config", "logs"]:
                (project_path / dir_name).mkdir(exist_ok=True)

            config_file = project_path / "config" / "config.toml"
            if not config_file.exists():
                with open(config_file, "w", encoding="utf-8") as f:
                    f.write("# ErisPulse 配置文件\n")
                    f.write("# 完整配置示例请参考 config.full.example\n\n")
                    f.write("[ErisPulse.server]\n")
                    f.write('host = "0.0.0.0"\n')
                    f.write("port = 8000\n\n")
                    f.write("[ErisPulse.logger]\n")
                    f.write('level = "INFO"\n')
                    if adapter_list:
                        f.write("\n[ErisPulse.adapters.status]\n")
                        for adapter in adapter_list:
                            f.write(f"{adapter} = false\n")

            example_file = project_path / "config" / "config.full.example"
            if not example_file.exists():
                with open(example_file, "w", encoding="utf-8") as f:
                    f.write(self._get_full_example_config(adapter_list))

            main_file = project_path / "main.py"
            if not main_file.exists():
                with open(main_file, "w", encoding="utf-8") as f:
                    f.write(f'"""\n{project_name} 主程序\n\n')
                    f.write("这是 ErisPulse 自动生成的主程序文件\n")
                    f.write('"""\n\n')
                    f.write("import asyncio\n")
                    f.write("from ErisPulse import sdk\n\n")
                    f.write("async def main():\n")
                    f.write("    await sdk.run(keep_running=True)\n\n")
                    f.write('if __name__ == "__main__":\n')
                    f.write("    asyncio.run(main())\n")

            console.print(f"[success]  项目 {project_name} 初始化成功[/]")
            console.print()
            console.print(Text("  接下来:", style="bold"))
            console.print(f"    · 编辑 {project_name}/config/config.toml 配置适配器")
            console.print(f"    · cd {project_name} && epsdk run")
            return True

        except Exception as e:
            console.print(f"[error]  初始化项目失败: {e}[/]")
            return False

    @staticmethod
    def _get_full_example_config(adapter_list=None):
        lines = [
            "# ErisPulse 完整配置示例",
            "# 此文件展示所有可用配置项及其默认值",
            "# 如需使用，将所需配置复制到 config.toml 并按需修改",
            "",
            "# ==================== 服务器 ====================",
            "",
            "[ErisPulse.server]",
            'host = "0.0.0.0"              # 监听地址',
            "port = 8000                   # 监听端口",
            "ssl_certfile = null           # SSL 证书路径",
            "ssl_keyfile = null            # SSL 密钥路径",
            "",
            "# ==================== 日志 ====================",
            "",
            "[ErisPulse.logger]",
            'level = "INFO"                # 日志级别: DEBUG/INFO/WARNING/ERROR',
            'log_files = []                # 日志文件列表, 如 ["logs/app.log"]',
            "memory_limit = 1000           # 内存日志条数上限",
            "",
            "# ==================== 存储 ====================",
            "",
            "[ErisPulse.storage]",
            "use_global_db = false         # 是否使用全局数据库",
            "",
            "# ==================== 事件系统 ====================",
            "",
            "[ErisPulse.event.message]",
            "ignore_self = true            # 忽略自身消息",
            "",
            "[ErisPulse.event.command]",
            'prefix = "/"                  # 命令前缀',
            "case_sensitive = true         # 区分大小写",
            "allow_space_prefix = false    # 允许前缀前有空格",
            "must_at_bot = false           # 必须艾特Bot才触发",
            "",
            "# ==================== 框架 ====================",
            "",
            "[ErisPulse.framework]",
            "enable_lazy_loading = true    # 启用模块懒加载",
            "",
            "# ==================== 配置审计 ====================",
            "",
            "[ErisPulse.config.audit]",
            "enabled = false               # 是否启用配置审计",
            "max_entries = 1000            # 审计日志最大条数",
            "",
            "# ==================== 路由增强 ====================",
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
            "# ==================== 适配器状态 ====================",
            "",
            "[ErisPulse.adapters.status]",
        ]

        if adapter_list:
            for adapter in adapter_list:
                lines.append(f"# {adapter} = false")
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
                "# ==================== 模块状态 ====================",
                "",
                "[ErisPulse.modules.status]",
                "# MyModule = true",
                "",
            ]
        )

        return "\n".join(lines)

    async def _fetch_available_adapters(self):
        try:
            remote_packages = await self.package_manager.get_remote_packages()
            adapters = {}
            for name, info in remote_packages.get("adapters", {}).items():
                adapters[name] = info.get("description", "")
            if adapters:
                return adapters
        except Exception as e:
            console.print(f"[warning]  获取远程适配器列表失败: {e}[/]")

        return {
            "yunhu": "云湖平台适配器",
            "telegram": "Telegram机器人适配器",
            "onebot11": "OneBot11标准适配器",
            "email": "邮件适配器",
        }

    def _interactive_init(self, project_name: str = None, force: bool = False) -> bool:
        try:
            if not project_name:
                project_name = Prompt.ask("  项目名称", default="my_erispulse_project")

            project_path = Path(project_name)
            if project_path.exists() and not force:
                if not Confirm.ask(
                    f"  [cyan]目录 {project_name} 已存在，是否覆盖？[/]", default=False
                ):
                    console.print("[info]  操作已取消[/]")
                    return False

            if not self._init_project(project_name, []):
                return False

            from ErisPulse import config

            project_config_path = project_path / "config" / "config.toml"
            config.CONFIG_FILE = str(project_config_path)
            config.reload()

            section_header("基本配置")

            current_level = config.getConfig("ErisPulse.logger.level", "INFO")
            console.print(f"  日志级别 [dim]({current_level})[/]")
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
            console.print(f"  监听地址 [dim]({current_host})[/]")
            new_host = _input(">")
            if new_host:
                config.setConfig("ErisPulse.server.host", new_host)

            current_port = str(config.getConfig("ErisPulse.server.port", 8000))
            console.print(f"  监听端口 [dim]({current_port})[/]")
            new_port = _input(">")
            if new_port:
                try:
                    config.setConfig("ErisPulse.server.port", int(new_port))
                except ValueError:
                    console.print(f"[warning]  无效的端口号: {new_port}[/]")

            if Confirm.ask("\n  [cyan]是否配置适配器？[/]", default=True):
                self._configure_adapters(project_path)

            config.force_save()
            return True

        except Exception as e:
            console.print(f"[error]  初始化失败: {e}[/]")
            return False

    def _configure_adapters(self, project_path: Path):
        from ErisPulse import config

        with console.status("[bold green]正在获取适配器列表...", spinner="dots"):
            try:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run, self._fetch_available_adapters()
                    )
                    adapters = future.result(timeout=10)
            except Exception as e:
                console.print(f"[error]  获取适配器列表失败: {e}[/]")
                return

        if not adapters:
            console.print("[dim]  没有可用适配器[/]")
            return

        section_header("适配器")
        adapter_list = list(adapters.items())
        for i, (name, desc) in enumerate(adapter_list, 1):
            console.print(f"    [bold]{i}.[/] {name} [dim]— {desc}[/]")

        console.print("  选择要启用的适配器 (序号，逗号分隔)")
        selected = _input(">")
        if not selected.strip():
            console.print("[info]  未选择适配器[/]")
            return

        try:
            indices = [int(idx.strip()) for idx in selected.split(",")]
        except ValueError:
            console.print("[warning]  请输入数字序号[/]")
            return

        enabled = []
        for idx in indices:
            if 1 <= idx <= len(adapter_list):
                name = adapter_list[idx - 1][0]
                enabled.append(name)
                config.setConfig(f"ErisPulse.adapters.status.{name}", True)
            else:
                console.print(f"[warning]  序号 {idx} 无效[/]")

        for name, _ in adapter_list:
            if name not in enabled:
                config.setConfig(f"ErisPulse.adapters.status.{name}", False)

        console.print(f"[dim]  已启用 {len(enabled)} 个适配器[/]")

        if enabled and Confirm.ask("  [cyan]是否安装选中的适配器？[/]", default=True):
            self._install_adapters(enabled, adapters)

    def _install_adapters(self, adapter_names, adapters_info):
        pkg_manager = PackageManager()
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

            console.print(f"[info]  正在安装 {adapter_name} ({package_name})[/]")
            success = pkg_manager.install_package([package_name])

            if not success:
                console.print("[warning]  标准安装失败，尝试 uv...[/]")
                try:
                    result = subprocess.run(
                        [sys.executable, "-m", "uv", "pip", "install", package_name],
                        capture_output=True,
                        text=True,
                        timeout=300,
                    )
                    if result.returncode != 0:
                        console.print(f"[error]  {adapter_name} 安装失败[/]")
                except Exception as e:
                    console.print(f"[error]  {adapter_name} 安装出错: {e}[/]")
