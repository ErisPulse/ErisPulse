import argparse
import os
import sys
import shutil
import aiohttp
import zipfile
import fnmatch
import asyncio
import subprocess
import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich import box
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.formatted_text import HTML
from .db import env

console = Console()
class SourceManager:
    def __init__(self):
        self._init_sources()

    def _init_sources(self):
        if not env.get('origins'):
            env.set('origins', [])

    async def _validate_url(self, url):
        if not url.startswith(('http://', 'https://')):
            protocol = Prompt.ask("未指定协议，请输入使用的协议", 
                                choices=['http', 'https'], 
                                default="https")
            url = f"{protocol}://{url}"
        
        if not url.endswith('.json'):
            url = f"{url}/map.json"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    if response.headers.get('Content-Type', '').startswith('application/json'):
                        return url
                    else:
                        console.print(Panel(
                            f"[red]源 {url} 返回的内容不是有效的 JSON 格式[/red]",
                            title="错误",
                            border_style="red"
                        ))
                        return None
        except Exception as e:
            console.print(Panel(
                f"[red]访问源 {url} 失败: {e}[/red]",
                title="错误",
                border_style="red"
            ))
            return None

    def add_source(self, value):
        validated_url = asyncio.run(self._validate_url(value))
        if not validated_url:
            console.print(Panel(
                "[red]提供的源不是一个有效源，请检查后重试[/red]",
                title="错误",
                border_style="red"
            ))
            return False

        origins = env.get('origins')
        if validated_url not in origins:
            origins.append(validated_url)
            env.set('origins', origins)
            console.print(Panel(
                f"[green]源 {validated_url} 已成功添加[/green]",
                border_style="green"
            ))
            return True
        else:
            console.print(Panel(
                f"[yellow]源 {validated_url} 已存在，无需重复添加[/yellow]",
                border_style="yellow"
            ))
            return False

    def update_sources(self):
        origins = env.get('origins')
        providers = {}
        modules = {}
        module_alias = {}
        
        table = Table(
            title="源更新状态",
            show_header=True,
            header_style="bold magenta",
            box=box.ROUNDED
        )
        table.add_column("源", style="cyan")
        table.add_column("模块", style="green")
        table.add_column("地址", style="blue")

        async def fetch_source_data():
            async with aiohttp.ClientSession() as session:
                for origin in origins:
                    console.print(f"[cyan]正在获取 {origin}...[/cyan]")
                    try:
                        async with session.get(origin) as response:
                            response.raise_for_status()
                            if response.headers.get('Content-Type', '').startswith('application/json'):
                                content = await response.json()
                                providers[content["name"]] = content["base"]
                                
                                for module in content["modules"].keys():
                                    module_content = content["modules"][module]
                                    modules[f'{module}@{content["name"]}'] = module_content
                                    module_origin_name = module_content["path"]
                                    module_alias_name = module
                                    module_alias[f'{module_origin_name}@{content["name"]}'] = module_alias_name

                                    table.add_row(
                                        content['name'],
                                        module,
                                        f"{providers[content['name']]}{module_origin_name}"
                                    )
                            else:
                                console.print(Panel(
                                    f"[red]源 {origin} 返回的内容不是有效的 JSON 格式[/red]",
                                    title="错误",
                                    border_style="red"
                                ))
                    except Exception as e:
                        console.print(Panel(
                            f"[red]获取 {origin} 时出错: {e}[/red]",
                            title="错误",
                            border_style="red"
                        ))

        asyncio.run(fetch_source_data())
        console.print(table)
        from datetime import datetime
        env.set('providers', providers)
        env.set('modules', modules)
        env.set('module_alias', module_alias)
        env.set('last_origin_update_time', datetime.now().isoformat())
        
        console.print(Panel(
            "[green]源更新完成[/green]",
            border_style="green"
        ))

    def list_sources(self):
        origins = env.get('origins')
        if not origins:
            console.print(Panel(
                "[yellow]当前没有配置任何源[/yellow]",
                border_style="yellow"
            ))
            return

        table = Table(title="已配置的源", show_header=True, header_style="bold magenta")
        table.add_column("序号", style="cyan", justify="center")
        table.add_column("源地址", style="green")
        
        for idx, origin in enumerate(origins, 1):
            table.add_row(str(idx), origin)
        
        console.print(table)

    def del_source(self, value):
        origins = env.get('origins')
        if value in origins:
            origins.remove(value)
            env.set('origins', origins)
            console.print(Panel(
                f"[green]源 {value} 已成功删除[/green]",
                border_style="green"
            ))
        else:
            console.print(Panel(
                f"[red]源 {value} 不存在[/red]",
                title="错误",
                border_style="red"
            ))
def enable_module(module_name):
    module_info = env.get_module(module_name)
    if module_info:
        with console.status(f"[cyan]正在启用模块 {module_name}...[/cyan]"):
            env.set_module_status(module_name, True)
        console.print(Panel(
            f"[green]✓ 模块 {module_name} 已成功启用[/green]",
            border_style="green"
        ))
    else:
        console.print(Panel(
            f"[red]模块 {module_name} 不存在[/red]",
            title="错误",
            border_style="red"
        ))

def disable_module(module_name):
    module_info = env.get_module(module_name)
    if module_info:
        with console.status(f"[cyan]正在禁用模块 {module_name}...[/cyan]"):
            env.set_module_status(module_name, False)
        console.print(Panel(
            f"[yellow]✓ 模块 {module_name} 已成功禁用[/yellow]",
            border_style="yellow"
        ))
    else:
        console.print(Panel(
            f"[red]模块 {module_name} 不存在[/red]",
            title="错误",
            border_style="red"
        ))

async def fetch_url(session, url):
    try:
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.read()
    except Exception as e:
        console.print(f"[red]请求失败: {e}[/red]")
        return None

def extract_and_setup_module(module_name, module_url, zip_path, module_dir):
    try:
        console.print(f"[cyan]正在从 {module_url} 下载模块...[/cyan]")
        
        async def download_module():
            async with aiohttp.ClientSession() as session:
                content = await fetch_url(session, module_url)
                if content is None:
                    return False
                
                with open(zip_path, 'wb') as zip_file:
                    zip_file.write(content)

                if not os.path.exists(module_dir):
                    os.makedirs(module_dir)

                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(module_dir)
                
                init_file_path = os.path.join(module_dir, '__init__.py')
                if not os.path.exists(init_file_path):
                    sub_module_dir = os.path.join(module_dir, module_name)
                    m_sub_module_dir = os.path.join(module_dir, f"m_{module_name}")
                    for sub_dir in [sub_module_dir, m_sub_module_dir]:
                        if os.path.exists(sub_dir) and os.path.isdir(sub_dir):
                            for item in os.listdir(sub_dir):
                                source_item = os.path.join(sub_dir, item)
                                target_item = os.path.join(module_dir, item)
                                if os.path.exists(target_item):
                                    os.remove(target_item)
                                shutil.move(source_item, module_dir)
                            os.rmdir(sub_dir)

                console.print(f"[green]模块 {module_name} 文件已成功解压并设置[/green]")
                return True
        
        return asyncio.run(download_module())

    except Exception as e:
        console.print(Panel(f"[red]处理模块 {module_name} 文件失败: {e}[/red]", title="错误", border_style="red"))
        if os.path.exists(zip_path):
            try:
                os.remove(zip_path)
            except Exception as cleanup_error:
                console.print(f"[red]清理失败: {cleanup_error}[/red]")
        return False

    finally:
        if os.path.exists(zip_path):
            try:
                os.remove(zip_path)
            except Exception as cleanup_error:
                console.print(f"[red]清理失败: {cleanup_error}[/red]")

def install_pip_dependencies(dependencies):
    if not dependencies:
        return True

    console.print("[cyan]正在安装pip依赖...[/cyan]")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install"] + dependencies,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        console.print(result.stdout.decode())
        return True
    except subprocess.CalledProcessError as e:
        console.print(Panel(f"[red]安装pip依赖失败: {e.stderr.decode()}[/red]", title="错误", border_style="red"))
        return False

def install_module(module_name, force=False):
    # 显示安装摘要
    console.print(Panel.fit(
        f"[bold]准备安装模块:[/bold] [cyan]{module_name}[/cyan]",
        title="安装摘要",
        border_style="blue"
    ))
    
    last_update_time = env.get('last_origin_update_time', None)
    if last_update_time:
        from datetime import datetime, timedelta
        last_update = datetime.fromisoformat(last_update_time)
        if datetime.now() - last_update > timedelta(hours=0):
            console.print(Panel(
                "[yellow]距离上次源更新已超过72小时，源内可能有新模块或更新。[/yellow]",
                border_style="yellow"
            ))
            update_confirmation = Confirm.ask(
                "[yellow]是否在安装模块前更新源？[/yellow]", 
                default=True
            )
            if update_confirmation:
                with console.status("[cyan]正在更新源...[/cyan]"):
                    SourceManager().update_sources()
                env.set('last_origin_update_time', datetime.now().isoformat())
                console.print("[green]✓ 源更新完成[/green]")

    module_info = env.get_module(module_name)
    if module_info and not force:
        meta = module_info.get('info', {}).get('meta', {})
        console.print(Panel(
            f"[yellow]模块 {module_name} 已存在[/yellow]\n"
            f"版本: {meta.get('version', '未知')}\n"
            f"描述: {meta.get('description', '无描述')}",
            title="模块已存在",
            border_style="yellow"
        ))
        if not Confirm.ask("[yellow]是否要强制重新安装？[/yellow]", default=False):
            return

    providers = env.get('providers', {})
    if isinstance(providers, str):
        providers = json.loads(providers)

    module_info = []
    for provider, url in providers.items():
        module_key = f"{module_name}@{provider}"
        modules_data = env.get('modules', {})
        if isinstance(modules_data, str):
            modules_data = json.loads(modules_data)

        if module_key in modules_data:
            module_data = modules_data[module_key]
            console.print(f"[cyan]正在处理模块 {module_name} 源: {provider}...[/cyan]")
            console.print(f"[cyan]源地址: {url}[/cyan] | 信息: {module_data}")
            meta = module_data.get("meta", {})
            depsinfo = module_data.get("dependencies", {})

            module_info.append({
                'provider': provider,
                'url': url,
                'path': module_data.get('path', ''),
                'version': meta.get('version', '未知'),
                'description': meta.get('description', '无描述'),
                'author': meta.get('author', '未知'),
                'dependencies': depsinfo.get("requires", []),
                'optional_dependencies': depsinfo.get("optional", []),
                'pip_dependencies': depsinfo.get("pip", [])
            })

    if not module_info:
        console.print(Panel(
            f"[red]未找到模块 {module_name}[/red]",
            title="错误",
            border_style="red"
        ))
        if providers:
            console.print("[cyan]当前可用源:[/cyan]")
            for provider in providers:
                console.print(f"  - {provider}")
        return

    if len(module_info) > 1:
        console.print(f"[cyan]找到 {len(module_info)} 个源的 {module_name} 模块：[/cyan]")
        table = Table(title="可选模块源", show_header=True, header_style="bold magenta")
        table.add_column("编号", style="cyan")
        table.add_column("源", style="green")
        table.add_column("版本", style="blue")
        table.add_column("描述", style="white")
        table.add_column("作者", style="yellow")
        for i, info in enumerate(module_info):
            console.print(info)
            table.add_row(str(i+1), info['provider'], info.get('meta', {}).get('version', '未知'), info.get('description', {}).get('requires'), info.get('meta', {}).get('author', '未知'))
        console.print(table)

        while True:
            choice = Prompt.ask("请选择要安装的源 (输入编号)", default="1")
            if choice.isdigit() and 1 <= int(choice) <= len(module_info):
                selected_module = module_info[int(choice)-1]
                break
            else:
                console.print("[red]输入无效，请重新选择[/red]")
    else:
        selected_module = module_info[0]

    for dep in selected_module['dependencies']:
        console.print(f"[cyan]正在安装依赖模块 {dep}...[/cyan]")
        install_module(dep)

    third_party_deps = selected_module.get('pip_dependencies', [])
    if third_party_deps:
        console.print(f"[cyan]模块 {module_name} 需要以下pip依赖: {', '.join(third_party_deps)}[/cyan]")
        if not install_pip_dependencies(third_party_deps):
            console.print(f"[red]无法安装模块 {module_name} 的pip依赖，安装终止[/red]")
            return
    
    module_url = selected_module['url'] + selected_module['path']
    script_dir = os.path.dirname(os.path.abspath(__file__))
    module_dir = os.path.join(script_dir, 'modules', module_name)
    zip_path = os.path.join(script_dir, f"{module_name}.zip")

    if not extract_and_setup_module(
        module_name=module_name,
        module_url=module_url,
        zip_path=zip_path,
        module_dir=module_dir
    ):
        return

    env.set_module(module_name, {
        'status': True,
        'info': {
            'meta': {
                'version': selected_module['version'],
                'description': selected_module['description'],
                'author': selected_module['author'],
                'pip_dependencies': selected_module['pip_dependencies']
            },
            'dependencies': {
                'requires': selected_module['dependencies'],
                'optional': selected_module['optional_dependencies'],
                'pip': selected_module['pip_dependencies']
            }
        }
    })
    console.print(f"[green]模块 {module_name} 安装成功[/green]")

def uninstall_module(module_name):
    # 显示卸载摘要
    console.print(Panel.fit(
        f"[bold]准备卸载模块:[/bold] [cyan]{module_name}[/cyan]",
        title="卸载摘要",
        border_style="blue"
    ))
    
    module_info = env.get_module(module_name)
    if not module_info:
        console.print(Panel(
            f"[red]模块 {module_name} 不存在[/red]",
            title="错误",
            border_style="red"
        ))
        return
    meta = module_info.get('info', {}).get('meta', {})
    depsinfo = module_info.get('info', {}).get('dependencies', {})

    # 显示模块信息
    console.print(Panel(
        f"版本: {meta.get('version', '未知')}\n"
        f"描述: {meta.get('description', '无描述')}\n"
        f"pip依赖: {', '.join(depsinfo.get('pip', [])) or '无'}",
        title="模块信息",
        border_style="green"
    ))
    
    if not Confirm.ask("[red]确认要卸载此模块吗？[/red]", default=False):
        console.print("[yellow]卸载已取消[/yellow]")
        return

    script_dir = os.path.dirname(os.path.abspath(__file__))
    module_path = os.path.join(script_dir, 'modules', module_name)

    module_file_path = module_path + '.py'
    if os.path.exists(module_file_path):
        try:
            with console.status(f"[cyan]正在删除模块文件 {module_name}...[/cyan]"):
                os.remove(module_file_path)
        except Exception as e:
            console.print(Panel(
                f"[red]删除模块文件 {module_name} 时出错: {e}[/red]",
                title="错误",
                border_style="red"
            ))
    elif os.path.exists(module_path) and os.path.isdir(module_path):
        try:
            with console.status(f"[cyan]正在删除模块目录 {module_name}...[/cyan]"):
                shutil.rmtree(module_path)
        except Exception as e:
            console.print(Panel(
                f"[red]删除模块目录 {module_name} 时出错: {e}[/red]",
                title="错误",
                border_style="red"
            ))
    else:
        console.print(Panel(
            f"[red]模块 {module_name} 不存在[/red]",
            title="错误",
            border_style="red"
        ))
        return

    pip_dependencies = depsinfo.get('pip', [])
    if pip_dependencies:
        all_modules = env.get_all_modules()
        unused_pip_dependencies = []
        
        essential_packages = {'aiohttp', 'rich'}

        for dep in pip_dependencies:
            if dep in essential_packages:
                console.print(f"[yellow]跳过必要模块 {dep} 的卸载[/yellow]")
                continue

            is_dependency_used = False
            for name, info in all_modules.items():
                if name != module_name and dep in info.get('info', {}).get('dependencies', {}).get('pip', []):
                    is_dependency_used = True
                    break
            if not is_dependency_used:
                unused_pip_dependencies.append(dep)
        
        if unused_pip_dependencies:
            console.print(Panel(
                f"以下 pip 依赖不再被其他模块使用:\n{', '.join(unused_pip_dependencies)}",
                title="可卸载依赖",
                border_style="cyan"
            ))
            confirm = Confirm.ask("[yellow]是否卸载这些 pip 依赖？[/yellow]", default=False)
            if confirm:
                with console.status(f"[cyan]正在卸载 pip 依赖: {', '.join(unused_pip_dependencies)}[/cyan]"):
                    try:
                        subprocess.run(
                            [sys.executable, "-m", "pip", "uninstall", "-y"] + unused_pip_dependencies,
                            check=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE
                        )
                        console.print(Panel(
                            f"[green]成功卸载 pip 依赖: {', '.join(unused_pip_dependencies)}[/green]",
                            border_style="green"
                        ))
                    except subprocess.CalledProcessError as e:
                        console.print(Panel(
                            f"[red]卸载 pip 依赖失败: {e.stderr.decode()}[/red]",
                            title="错误",
                            border_style="red"
                        ))
    
    if env.remove_module(module_name):
        console.print(Panel(
            f"[green]✓ 模块 {module_name} 已成功卸载[/green]",
            border_style="green"
        ))
    else:
        console.print(Panel(
            f"[red]模块 {module_name} 不存在[/red]",
            title="错误",
            border_style="red"
        ))
def upgrade_all_modules(force=False):
    all_modules = env.get_all_modules()
    if not all_modules:
        console.print("[yellow]未找到任何模块，无法更新[/yellow]")
        return

    providers = env.get('providers', {})
    if isinstance(providers, str):
        providers = json.loads(providers)

    modules_data = env.get('modules', {})
    if isinstance(modules_data, str):
        modules_data = json.loads(modules_data)

    updates_available = []
    for module_name, module_info in all_modules.items():
        local_version = module_info.get('info', []).get('meta', []).get('version', '0.0.0')
        for provider, url in providers.items():
            module_key = f"{module_name}@{provider}"
            if module_key in modules_data:
                remote_module = modules_data[module_key]
                remote_version = remote_module.get('meta', {}).get('version', '1.14.514')
                if remote_version > local_version:
                    updates_available.append({
                        'name': module_name,
                        'local_version': local_version,
                        'remote_version': remote_version,
                        'provider': provider,
                        'url': url,
                        'path': remote_module.get('path', ''),
                    })

    if not updates_available:
        console.print("[green]所有模块已是最新版本，无需更新[/green]")
        return

    console.print("\n[cyan]以下模块有可用更新：[/cyan]")
    table = Table(title="可用更新", show_header=True, header_style="bold magenta")
    table.add_column("模块", style="cyan")
    table.add_column("当前版本", style="yellow")
    table.add_column("最新版本", style="green")
    table.add_column("源", style="blue")
    for update in updates_available:
        table.add_row(update['name'], update['local_version'], update['remote_version'], update['provider'])
    console.print(table)

    if not force:
        confirm = Confirm.ask("[yellow]警告：更新模块可能会导致兼容性问题，请在更新前查看插件作者的相关声明。\n是否继续？[/yellow]", default=False)
        if not confirm:
            console.print("[yellow]更新已取消[/yellow]")
            return

    for update in updates_available:
        console.print(f"[cyan]正在更新模块 {update['name']}...[/cyan]")
        module_url = update['url'] + update['path']
        script_dir = os.path.dirname(os.path.abspath(__file__))
        module_dir = os.path.join(script_dir, 'modules', update['name'])
        zip_path = os.path.join(script_dir, f"{update['name']}.zip")

        if not extract_and_setup_module(
            module_name=update['name'],
            module_url=module_url,
            zip_path=zip_path,
            module_dir=module_dir
        ):
            continue

        all_modules[update['name']]['info']['version'] = update['remote_version']
        env.set_all_modules(all_modules)
        console.print(f"[green]模块 {update['name']} 已更新至版本 {update['remote_version']}[/green]")

def list_modules(module_name=None):
    all_modules = env.get_all_modules()
    if not all_modules:
        console.print(Panel(
            "[yellow]未在数据库中发现注册模块,正在初始化模块列表...[/yellow]",
            border_style="yellow"
        ))
        from . import init as init_module
        init_module()
        all_modules = env.get_all_modules()

    if not all_modules:
        console.print(Panel(
            "[red]未找到任何模块[/red]",
            title="错误",
            border_style="red"
        ))
        return

    # 显示模块总数
    console.print(Panel.fit(
        f"[bold]找到 {len(all_modules)} 个模块[/bold]",
        border_style="blue"
    ))

    table = Table(
        title="模块列表",
        show_header=True,
        header_style="bold magenta",
        expand=True,
        box=box.ROUNDED
    )
    table.add_column("模块名称", style="cyan", min_width=20)
    table.add_column("状态", style="green", justify="center")
    table.add_column("版本", style="blue", justify="center")
    table.add_column("描述", style="white", min_width=30)
    table.add_column("依赖", style="yellow", min_width=15)
    table.add_column("可选依赖", style="magenta", min_width=15)
    table.add_column("pip依赖", style="cyan", min_width=20)

    for name, info in all_modules.items():
        status = "[green]✓[/green]" if info.get("status", True) else "[red]✗[/red]"
        meta = info.get('info', {}).get('meta', {})
        depsinfo = info.get('info', {}).get('dependencies', {})
        optional_deps = depsinfo.get('optional', [])
        available_optional_deps = []
        missing_optional_deps = []

        if optional_deps:
            for dep in optional_deps:
                if isinstance(dep, list):
                    # 处理嵌套列表
                    available_deps = [d for d in dep if d in all_modules]
                    if available_deps:
                        available_optional_deps.extend(available_deps)
                    else:
                        missing_optional_deps.extend(dep)
                elif dep in all_modules:
                    # 单个字符串依赖
                    available_optional_deps.append(dep)
                else:
                    missing_optional_deps.append(dep)

            optional_dependencies = (
                f"[green]可用: {', '.join(available_optional_deps)}[/green]\n"
                f"[red]缺失: {', '.join(missing_optional_deps)}[/red]"
                if missing_optional_deps
                else ', '.join(available_optional_deps) or '无'
            )
        else:
            optional_dependencies = '无'

        dependencies = '\n'.join(depsinfo.get('requires', [])) or '无'
        pip_dependencies = '\n'.join(depsinfo.get('pip', [])) or '无'

        table.add_row(
            f"[bold]{name}[/bold]",
            status,
            meta.get('version', '未知'),
            meta.get('description', '无描述'),
            dependencies,
            optional_dependencies,
            pip_dependencies
        )

    console.print(table)

    # 显示模块状态统计
    enabled_count = sum(1 for m in all_modules.values() if m.get("status", True))
    disabled_count = len(all_modules) - enabled_count
    console.print(Panel(
        f"[green]已启用: {enabled_count}[/green]  [red]已禁用: {disabled_count}[/red]",
        title="模块状态统计",
        border_style="blue"
    ))

def main():
    parser = argparse.ArgumentParser(
        description="ErisPulse 命令行工具",
        prog="ep"
    )
    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # 添加子命令解析器（与原代码一致）
    enable_parser = subparsers.add_parser('enable', help='启用指定模块')
    enable_parser.add_argument('module_names', nargs='+', help='要启用的模块名称（支持多个模块，用空格分隔）')
    enable_parser.add_argument('--init', action='store_true', help='在启用模块前初始化模块数据库')

    disable_parser = subparsers.add_parser('disable', help='禁用指定模块')
    disable_parser.add_argument('module_names', nargs='+', help='要禁用的模块名称（支持多个模块，用空格分隔）')
    disable_parser.add_argument('--init', action='store_true', help='在禁用模块前初始化模块数据库')

    list_parser = subparsers.add_parser('list', help='列出所有模块信息')
    list_parser.add_argument('--module', '-m', type=str, help='指定要展示的模块名称')

    update_parser = subparsers.add_parser('update', help='更新模块列表')

    upgrade_parser = subparsers.add_parser('upgrade', help='升级模块列表')
    upgrade_parser.add_argument('--force', action='store_true', help='跳过二次确认，强制更新')

    uninstall_parser = subparsers.add_parser('uninstall', help='删除指定模块')
    uninstall_parser.add_argument('module_names', nargs='+', help='要卸载的模块名称（支持多个模块，用空格分隔）')

    install_parser = subparsers.add_parser('install', help='安装指定模块（支持多个模块，用空格分隔）')
    install_parser.add_argument('module_name', nargs='+', help='要安装的模块名称（支持多个模块，用空格分隔）')
    install_parser.add_argument('--force', action='store_true', help='强制重新安装模块')
    install_parser.add_argument('--init', action='store_true', help='在安装模块前初始化模块数据库')

    origin_parser = subparsers.add_parser('origin', help='管理模块源')
    origin_subparsers = origin_parser.add_subparsers(dest='origin_command', help='源管理命令')

    add_origin_parser = origin_subparsers.add_parser('add', help='添加模块源')
    add_origin_parser.add_argument('url', type=str, help='要添加的模块源URL')

    list_origin_parser = origin_subparsers.add_parser('list', help='列出所有模块源')

    del_origin_parser = origin_subparsers.add_parser('del', help='删除模块源')
    del_origin_parser.add_argument('url', type=str, help='要删除的模块源URL')

    args = parser.parse_args()
    source_manager = SourceManager()

    # 初始化模块数据库
    if hasattr(args, 'init') and args.init:
        console.print("[yellow]正在初始化模块列表...[/yellow]")
        from . import init as init_module
        init_module()

    if args.command == 'enable':
        for module_name in args.module_names:
            module_name = module_name.strip()
            if not module_name:
                continue
            if '*' in module_name or '?' in module_name:
                console.print(f"[cyan]正在匹配模块模式: {module_name}...[/cyan]")
                all_modules = env.get_all_modules()
                if not all_modules:
                    console.print(Panel("[red]未找到任何模块，请先更新源或检查配置[/red]", title="错误", border_style="red"))
                    continue
                matched_modules = [name for name in all_modules.keys() if fnmatch.fnmatch(name, module_name)]
                if not matched_modules:
                    console.print(Panel(f"[red]未找到匹配模块模式 {module_name} 的模块[/red]", title="错误", border_style="red"))
                    continue
                console.print(f"[green]找到 {len(matched_modules)} 个匹配模块:[/green]")
                for i, matched_module in enumerate(matched_modules, start=1):
                    console.print(f"  {i}. {matched_module}")
                confirm = Confirm.ask("[yellow]是否启用所有匹配模块？[/yellow]", default=True)
                if not confirm:
                    console.print("[yellow]操作已取消[/yellow]")
                    continue
                for matched_module in matched_modules:
                    enable_module(matched_module)
            else:
                enable_module(module_name)
    elif args.command == 'disable':
        for module_name in args.module_names:
            module_name = module_name.strip()
            if not module_name:
                continue
            if '*' in module_name or '?' in module_name:
                console.print(f"[cyan]正在匹配模块模式: {module_name}...[/cyan]")
                all_modules = env.get_all_modules()
                if not all_modules:
                    console.print(Panel("[red]未找到任何模块，请先更新源或检查配置[/red]", title="错误", border_style="red"))
                    continue
                matched_modules = [name for name in all_modules.keys() if fnmatch.fnmatch(name, module_name)]
                if not matched_modules:
                    console.print(Panel(f"[red]未找到匹配模块模式 {module_name} 的模块[/red]", title="错误", border_style="red"))
                    continue
                console.print(f"[green]找到 {len(matched_modules)} 个匹配模块:[/green]")
                for i, matched_module in enumerate(matched_modules, start=1):
                    console.print(f"  {i}. {matched_module}")
                confirm = Confirm.ask("[yellow]是否禁用所有匹配模块？[/yellow]", default=True)
                if not confirm:
                    console.print("[yellow]操作已取消[/yellow]")
                    continue
                for matched_module in matched_modules:
                    disable_module(matched_module)
            else:
                disable_module(module_name)
    elif args.command == 'list':
        list_modules(args.module)
    elif args.command == 'uninstall':
        for module_name in args.module_names:
            module_name = module_name.strip()
            if not module_name:
                continue
            if '*' in module_name or '?' in module_name:
                console.print(f"[cyan]正在匹配模块模式: {module_name}...[/cyan]")
                all_modules = env.get_all_modules()
                if not all_modules:
                    console.print(Panel("[red]未找到任何模块，请先更新源或检查配置[/red]", title="错误", border_style="red"))
                    continue
                matched_modules = [name for name in all_modules.keys() if fnmatch.fnmatch(name, module_name)]
                if not matched_modules:
                    console.print(Panel(f"[red]未找到匹配模块模式 {module_name} 的模块[/red]", title="错误", border_style="red"))
                    continue
                console.print(f"[green]找到 {len(matched_modules)} 个匹配模块:[/green]")
                for i, matched_module in enumerate(matched_modules, start=1):
                    console.print(f"  {i}. {matched_module}")
                confirm = Confirm.ask("[yellow]是否卸载所有匹配模块？[/yellow]", default=True)
                if not confirm:
                    console.print("[yellow]操作已取消[/yellow]")
                    continue
                for matched_module in matched_modules:
                    uninstall_module(matched_module)
            else:
                uninstall_module(module_name)
    elif args.command == 'install':
        for module_name in args.module_name:
            module_name = module_name.strip()
            if not module_name:
                continue
            if '*' in module_name or '?' in module_name:
                console.print(f"[cyan]正在匹配模块模式: {module_name}...[/cyan]")
                all_modules = env.get_all_modules()
                if not all_modules:
                    console.print(Panel(
                        "[red]未找到任何模块，请先更新源或检查配置[/red]",
                        title="错误",
                        border_style="red"
                    ))
                    continue

                matched_modules = [
                    name for name in all_modules.keys() if fnmatch.fnmatch(name, module_name)
                ]

                if not matched_modules:
                    console.print(Panel(
                        f"[red]未找到匹配模块模式 {module_name} 的模块[/red]",
                        title="错误",
                        border_style="red"
                    ))
                    continue

                console.print(f"[green]找到 {len(matched_modules)} 个匹配模块:[/green]")
                for i, matched_module in enumerate(matched_modules, start=1):
                    console.print(f"  {i}. {matched_module}")

                confirm = Confirm.ask("[yellow]是否安装所有匹配模块？[/yellow]", default=True)
                if not confirm:
                    console.print("[yellow]安装已取消[/yellow]")
                    continue

                for matched_module in matched_modules:
                    install_module(matched_module, args.force)
            else:
                install_module(module_name, args.force)
    elif args.command == 'update':
        SourceManager().update_sources()
    elif args.command == 'upgrade':
        upgrade_all_modules(args.force)
    elif args.command == 'origin':
        if args.origin_command == 'add':
            success = source_manager.add_source(args.url)
            if success:
                update_confirmation = Confirm.ask(
                    "[yellow]源已添加，是否立即更新源以获取最新模块信息？[/yellow]",
                    default=True
                )
                if update_confirmation:
                    source_manager.update_sources()
        elif args.origin_command == 'list':
            source_manager.list_sources()
        elif args.origin_command == 'del':
            source_manager.del_source(args.url)
        else:
            origin_parser.print_help()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
