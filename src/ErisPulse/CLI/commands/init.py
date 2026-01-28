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

from ..console import console
from ..utils import PackageManager
from ..base import Command


class InitCommand(Command):
    name = "init"
    description = "初始化 ErisPulse 项目"
    
    def __init__(self):
        self.package_manager = PackageManager()
    
    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument(
            '--project-name', '-n',
            help='项目名称 (可选，交互式初始化时将会询问)'
        )
        parser.add_argument(
            '--quick', '-q',
            action='store_true',
            help='快速模式，跳过交互式配置'
        )
        parser.add_argument(
            '--force', '-f',
            action='store_true',
            help='强制覆盖现有配置'
        )
    
    def execute(self, args):
        if args.quick and args.project_name:
            # 快速模式：只创建项目，不进行交互配置
            success = self._init_project(args.project_name, [])
        else:
            # 交互式模式：引导用户完成项目和配置设置
            success = self._interactive_init(args.project_name, args.force)
        
        if success:
            console.print("[success]项目初始化完成[/]")
        else:
            console.print("[error]项目初始化失败[/]")
            sys.exit(1)
    
    def _init_project(self, project_name: str, adapter_list: list = None) -> bool:
        """
        初始化新项目
        
        :param project_name: 项目名称
        :param adapter_list: 需要初始化的适配器列表
        :return: 是否初始化成功
        """
        try:
            project_path = Path(project_name)
            if project_path.exists():
                if project_path.is_dir():
                    console.print(f"[yellow]目录 {project_name} 已存在[/yellow]")
                else:
                    console.print(f"[red]文件 {project_name} 已存在且不是目录[/red]")
                    return False
            else:
                project_path.mkdir()
                console.print(f"[green]创建项目目录: {project_name}[/green]")
            
            # 创建基本目录结构
            dirs = ["config", "logs"]
            for dir_name in dirs:
                dir_path = project_path / dir_name
                dir_path.mkdir(exist_ok=True)
                console.print(f"[green]创建目录: {dir_name}[/green]")
            
            # 创建配置文件
            config_file = project_path / "config.toml"
            if not config_file.exists():
                with open(config_file, "w", encoding="utf-8") as f:
                    f.write("# ErisPulse 配置文件\n\n")
                    f.write("[ErisPulse]\n")
                    f.write("# 全局配置\n\n")
                    f.write("[ErisPulse.server]\n")
                    f.write('host = "0.0.0.0"\n')
                    f.write("port = 8000\n\n")
                    f.write("[ErisPulse.logger]\n")
                    f.write('level = "INFO"\n')
                    f.write("log_files = [\"logs/app.log\"]\n")
                    f.write("memory_limit = 1000\n\n")
                    
                    # 添加适配器配置
                    if adapter_list:
                        f.write("[ErisPulse.adapters]\n")
                        f.write("# 适配器配置\n\n")
                        f.write("[ErisPulse.adapters.status]\n")
                        for adapter in adapter_list:
                            f.write(f'{adapter} = false  # 默认禁用，需要时启用\n')
                        f.write("\n")
                
                console.print("[green]创建配置文件: config.toml[/green]")
            
            # 创建主程序文件
            main_file = project_path / "main.py"
            if not main_file.exists():
                with open(main_file, "w", encoding="utf-8") as f:
                    f.write('"""')
                    f.write(f"\n{project_name} 主程序\n\n")
                    f.write("这是 ErisPulse 自动生成的主程序文件\n")
                    f.write("您可以根据需要修改此文件\n")
                    f.write('"""\n\n')
                    f.write("import asyncio\n")
                    f.write("from ErisPulse import sdk\n\n")
                    f.write("async def main():\n")
                    f.write('    """主程序入口"""\n')
                    f.write("    # 初始化 SDK\n")
                    f.write("    await sdk.init()\n\n")
                    f.write("    # 启动适配器\n")
                    f.write("    await sdk.adapter.startup()\n\n")
                    f.write('    print("ErisPulse 已启动，按 Ctrl+C 退出")\n')
                    f.write("    try:\n")
                    f.write("        while True:\n")
                    f.write("            await asyncio.sleep(1)\n")
                    f.write("    except KeyboardInterrupt:\n")
                    f.write("        print(\"\\n正在关闭...\")\n")
                    f.write("        await sdk.adapter.shutdown()\n\n")
                    f.write("if __name__ == \"__main__\":\n")
                    f.write("    asyncio.run(main())\n")
                
                console.print("[green]创建主程序文件: main.py[/green]")
            
            console.print("\n[bold green]项目 {} 初始化成功![/bold green]".format(project_name))
            console.print("\n[cyan]接下来您可以:[/cyan]")
            console.print(f"1. 编辑 {project_name}/config.toml 配置适配器")
            console.print(f"2. 运行 [cyan]cd {project_name} \n     ep run[/cyan] 启动项目")
            console.print("\n访问 https://github.com/ErisPulse/ErisPulse/tree/main/docs 获取更多信息和文档")
            return True
            
        except Exception as e:
            console.print(f"[red]初始化项目失败: {e}[/]")
            return False
    
    async def _fetch_available_adapters(self):
        """
        从云端获取可用适配器列表
        
        :return: 适配器名称到描述的映射
        """
        try:
            # 使用与 PackageManager 相同的机制获取远程包列表
            remote_packages = await self.package_manager.get_remote_packages()
            
            adapters = {}
            for name, info in remote_packages.get("adapters", {}).items():
                adapters[name] = info.get("description", "")
            
            if adapters:
                return adapters
            else:
                console.print("[yellow]从远程源获取的适配器列表为空[/yellow]")
        except Exception as e:
            console.print(f"[red]从远程源获取适配器列表时出错: {e}[/red]")
        
        # 如果云端请求失败，返回默认适配器列表
        console.print("[yellow]使用默认适配器列表[/yellow]")
        return {
            "yunhu": "云湖平台适配器",
            "telegram": "Telegram机器人适配器",
            "onebot11": "OneBot11标准适配器",
            "email": "邮件适配器"
        }
    
    def _configure_adapters_interactive_sync(self, project_path: str = None):
        """
        交互式配置适配器的同步版本
        
        :param project_path: 项目路径
        """
        from ErisPulse import config
        
        # 如果提供了项目路径，则加载项目配置
        if project_path:
            project_config_path = Path(project_path) / "config.toml"
            if project_config_path.exists():
                config.CONFIG_FILE = str(project_config_path)
                config.reload()
                console.print(f"[green]已加载项目配置: {project_config_path}[/green]")
        
        console.print("\n[bold]配置适配器[/bold]")
        console.print("[info]正在从云端获取可用适配器列表...[/info]")
        
        # 获取可用适配器列表（同步方式）
        try:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self._fetch_available_adapters())
                adapters = future.result(timeout=10)
        except Exception as e:
            console.print(f"[red]获取适配器列表失败: {e}[/red]")
            adapters = {}
        
        if not adapters:
            console.print("[red]未能获取到适配器列表[/red]")
            return
        
        # 显示可用适配器列表
        adapter_list = list(adapters.items())
        for i, (name, desc) in enumerate(adapter_list, 1):
            console.print(f"  {i}. {name} - {desc}")
        
        # 选择适配器
        selected_indices = Prompt.ask("\n[cyan]请输入要启用的适配器序号，多个用逗号分隔 (如: 1,3):[/cyan] ")
        if not selected_indices:
            console.print("[info]未选择任何适配器[/info]")
            return
        
        try:
            indices = [int(idx.strip()) for idx in selected_indices.split(",")]
            enabled_adapters = []
            
            for idx in indices:
                if 1 <= idx <= len(adapter_list):
                    adapter_name = adapter_list[idx-1][0]
                    enabled_adapters.append(adapter_name)
                    config.setConfig(f"ErisPulse.adapters.status.{adapter_name}", True)
                    console.print(f"[green]已启用适配器: {adapter_name}[/green]")
                else:
                    console.print(f"[red]无效的序号: {idx}[/]")
            
            # 禁用未选择的适配器
            all_adapter_names = [name for name, _ in adapter_list]
            for name in all_adapter_names:
                if name not in enabled_adapters:
                    config.setConfig(f"ErisPulse.adapters.status.{name}", False)
            
            console.print(f"\n[info]已启用 {len(enabled_adapters)} 个适配器[/info]")
            
            # 询问是否要安装适配器
            if enabled_adapters and Confirm.ask("\n[cyan]是否要安装选中的适配器？[/cyan]", default=True):
                self._install_adapters(enabled_adapters, adapters)
            
            # 保存配置
            config.force_save()
            
        except ValueError:
            console.print("[red]输入格式错误，请输入数字序号[/red]")
    
    def _install_adapters(self, adapter_names, adapters_info):
        """
        安装选中的适配器
        
        :param adapter_names: 适配器名称列表
        :param adapters_info: 适配器信息字典
        """
        from ..utils import PackageManager
        pkg_manager = PackageManager()
        
        for adapter_name in adapter_names:
            # 获取包名
            package_name = None
            try:
                remote_packages = pkg_manager._cache.get("remote_packages", {})
                if not remote_packages:
                    # 如果没有缓存，尝试同步获取
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, pkg_manager.get_remote_packages())
                        remote_packages = future.result(timeout=10)
                
                if adapter_name in remote_packages.get("adapters", {}):
                    package_name = remote_packages["adapters"][adapter_name].get("package")
            except Exception:
                pass
            
            # 如果没有找到包名，使用适配器名称作为包名
            if not package_name:
                package_name = adapter_name
            
            # 安装适配器
            console.print(f"[info]正在安装适配器: {adapter_name} ({package_name})[/info]")
            success = pkg_manager.install_package([package_name])
            
            if success:
                console.print(f"[green]适配器 {adapter_name} 安装成功[/green]")
            else:
                # 如果标准安装失败，尝试使用 uv
                console.print("[yellow]标准安装失败，尝试使用 uv 安装...[/yellow]")
                try:
                    result = subprocess.run(
                        [sys.executable, "-m", "uv", "pip", "install", package_name],
                        capture_output=True,
                        text=True,
                        timeout=300
                    )
                    
                    if result.returncode == 0:
                        console.print(f"[green]适配器 {adapter_name} 通过 uv 安装成功[/green]")
                    else:
                        console.print(f"[red]适配器 {adapter_name} 通过 uv 安装失败[/red]")
                except Exception as e:
                    console.print(f"[red]适配器 {adapter_name} 通过 uv 安装时出错: {e}[/]")
    
    def _interactive_init(self, project_name: str = None, force: bool = False) -> bool:
        """
        交互式初始化项目
        
        :param project_name: 项目名称
        :param force: 是否强制覆盖
        :return: 是否初始化成功
        """
        try:
            # 获取项目名称（如果未提供）
            if not project_name:
                project_name = Prompt.ask("[cyan]请输入项目名称 (默认: my_erispulse_project):[/cyan] ")
                if not project_name:
                    project_name = "my_erispulse_project"
            
            # 检查项目是否已存在
            project_path = Path(project_name)
            if project_path.exists() and not force:
                if not Confirm.ask(f"[yellow]目录 {project_name} 已存在，是否覆盖？[/]", default=False):
                    console.print("[info]操作已取消[/]")
                    return False
            
            # 创建项目
            if not self._init_project(project_name, []):
                return False
            
            # 加载项目配置
            from ErisPulse import config
            project_config_path = project_path / "config.toml"
            
            config.CONFIG_FILE = str(project_config_path)
            config.reload()
            
            # 交互式配置向导
            console.print("\n[bold blue]现在进行基本配置:[/bold blue]")
            
            # 获取日志级别配置
            current_level = config.getConfig("ErisPulse.logger.level", "INFO")
            console.print(f"\n当前日志级别: [cyan]{current_level}[/]")
            new_level = Prompt.ask("[yellow]请输入新的日志级别 (DEBUG/INFO/WARNING/ERROR/CRITICAL)，回车保持当前值:[/yellow] ")
            
            if new_level and new_level.upper() in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
                config.setConfig("ErisPulse.logger.level", new_level.upper())
                console.print(f"[green]日志级别已更新为: {new_level.upper()}[/]")
            elif new_level:
                console.print(f"[red]无效的日志级别: {new_level}[/red]")
            
            # 获取服务器配置
            console.print("\n[bold]服务器配置[/bold]")
            current_host = config.getConfig("ErisPulse.server.host", "0.0.0.0")
            current_port = config.getConfig("ErisPulse.server.port", 8000)
            
            console.print(f"当前主机: [cyan]{current_host}[/]")
            new_host = Prompt.ask("[yellow]请输入主机地址，回车保持当前值:[/yellow] ")
            
            if new_host:
                config.setConfig("ErisPulse.server.host", new_host)
                console.print(f"[green]主机地址已更新为: {new_host}[/]")
            
            console.print(f"当前端口: [cyan]{current_port}[/]")
            new_port = Prompt.ask("[yellow]请输入端口号，回车保持当前值:[/yellow] ")
            
            if new_port:
                try:
                    port_int = int(new_port)
                    config.setConfig("ErisPulse.server.port", port_int)
                    console.print(f"[green]端口已更新为: {port_int}[/]")
                except ValueError:
                    console.print(f"[red]无效的端口号: {new_port}[/red]")
            
            # 询问是否要配置适配器
            if Confirm.ask("\n[cyan]是否要配置适配器？[/cyan]", default=True):
                self._configure_adapters_interactive_sync(str(project_path))
            
            # 保存配置
            config.force_save()
            console.print("\n[bold green]项目和配置初始化完成![/bold green]")
            
            # 显示下一步操作
            console.print("\n[cyan]接下来您可以:[/cyan]")
            console.print(f"1. 编辑 {project_name}/config.toml 进一步配置")
            console.print(f"2. 运行 [cyan]cd {project_name} \n        ep run[/] 启动项目")
            
            return True
            
        except Exception as e:
            console.print(f"[red]交互式初始化失败: {e}[/]")
            return False
