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
from .db import env
from .mods import mods

def print_panel(msg, title=None, border_style=None):
    print("=" * 60)
    if title:
        print(f"[{title}]")
    print(msg)
    print("=" * 60)

def print_table(headers, rows, title=None):
    if title:
        print(f"== {title} ==")
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))
    fmt = " | ".join("{:<" + str(w) + "}" for w in col_widths)
    print(fmt.format(*headers))
    print("-" * (sum(col_widths) + 3 * (len(headers) - 1)))
    for row in rows:
        print(fmt.format(*row))

def confirm(msg, default=False):
    yes = {'y', 'yes', ''}
    no = {'n', 'no'}
    prompt = f"{msg} [{'Y/n' if default else 'y/N'}]: "
    while True:
        ans = input(prompt).strip().lower()
        if not ans:
            return default
        if ans in yes:
            return True
        if ans in no:
            return False

def ask(msg, choices=None, default=None):
    prompt = f"{msg}"
    if choices:
        prompt += f" ({'/'.join(choices)})"
    if default:
        prompt += f" [default: {default}]"
    prompt += ": "
    while True:
        ans = input(prompt).strip()
        if not ans and default:
            return default
        if not choices or ans in choices:
            return ans

class SourceManager:
    def __init__(self):
        self._init_sources()

    def _init_sources(self):
        if not env.get('origins'):
            env.set('origins', [])

    async def _validate_url(self, url):
        if not url.startswith(('http://', 'https://')):
            protocol = ask("未指定协议，请输入使用的协议", choices=['http', 'https'], default="https")
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
                        print_panel(f"源 {url} 返回的内容不是有效的 JSON 格式", "错误")
                        return None
        except Exception as e:
            print_panel(f"访问源 {url} 失败: {e}", "错误")
            return None

    def add_source(self, value):
        validated_url = asyncio.run(self._validate_url(value))
        if not validated_url:
            print_panel("提供的源不是一个有效源，请检查后重试", "错误")
            return False
        origins = env.get('origins')
        if validated_url not in origins:
            origins.append(validated_url)
            env.set('origins', origins)
            print_panel(f"源 {validated_url} 已成功添加", "成功")
            return True
        else:
            print_panel(f"源 {validated_url} 已存在，无需重复添加", "提示")
            return False

    def update_sources(self):
        origins = env.get('origins')
        providers = {}
        modules = {}
        module_alias = {}
        table_rows = []
        async def fetch_source_data():
            async with aiohttp.ClientSession() as session:
                for origin in origins:
                    print(f"正在获取 {origin}...")
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
                                    table_rows.append([
                                        content['name'],
                                        module,
                                        f"{providers[content['name']]}{module_origin_name}"
                                    ])
                            else:
                                print_panel(f"源 {origin} 返回的内容不是有效的 JSON 格式", "错误")
                    except Exception as e:
                        print_panel(f"获取 {origin} 时出错: {e}", "错误")
        asyncio.run(fetch_source_data())
        print_table(["源", "模块", "地址"], table_rows, "源更新状态")
        from datetime import datetime
        env.set('providers', providers)
        env.set('modules', modules)
        env.set('module_alias', module_alias)
        env.set('last_origin_update_time', datetime.now().isoformat())
        print_panel("源更新完成", "成功")

    def list_sources(self):
        origins = env.get('origins')
        if not origins:
            print_panel("当前没有配置任何源", "提示")
            return
        rows = [[str(idx), origin] for idx, origin in enumerate(origins, 1)]
        print_table(["序号", "源地址"], rows, "已配置的源")

    def del_source(self, value):
        origins = env.get('origins')
        if value in origins:
            origins.remove(value)
            env.set('origins', origins)
            print_panel(f"源 {value} 已成功删除", "成功")
        else:
            print_panel(f"源 {value} 不存在", "错误")

def enable_module(module_name):
    module_info = mods.get_module(module_name)
    if module_info:
        mods.set_module_status(module_name, True)
        print_panel(f"✓ 模块 {module_name} 已成功启用", "成功")
    else:
        print_panel(f"模块 {module_name} 不存在", "错误")

def disable_module(module_name):
    module_info = mods.get_module(module_name)
    if module_info:
        mods.set_module_status(module_name, False)
        print_panel(f"✓ 模块 {module_name} 已成功禁用", "成功")
    else:
        print_panel(f"模块 {module_name} 不存在", "错误")

async def fetch_url(session, url):
    try:
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.read()
    except Exception as e:
        print(f"请求失败: {e}")
        return None

def extract_and_setup_module(module_name, module_url, zip_path, module_dir):
    try:
        print(f"正在从 {module_url} 下载模块...")
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
                print(f"模块 {module_name} 文件已成功解压并设置")
                return True
        return asyncio.run(download_module())
    except Exception as e:
        print_panel(f"处理模块 {module_name} 文件失败: {e}", "错误")
        if os.path.exists(zip_path):
            try:
                os.remove(zip_path)
            except Exception as cleanup_error:
                print(f"清理失败: {cleanup_error}")
        return False
    finally:
        if os.path.exists(zip_path):
            try:
                os.remove(zip_path)
            except Exception as cleanup_error:
                print(f"清理失败: {cleanup_error}")

def install_pip_dependencies(dependencies):
    if not dependencies:
        return True
    print("正在安装pip依赖...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install"] + dependencies,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print(result.stdout.decode())
        return True
    except subprocess.CalledProcessError as e:
        print_panel(f"安装pip依赖失败: {e.stderr.decode()}", "错误")
        return False

def install_module(module_name, force=False):
    print_panel(f"准备安装模块: {module_name}", "安装摘要")
    last_update_time = env.get('last_origin_update_time', None)
    if last_update_time:
        from datetime import datetime, timedelta
        last_update = datetime.fromisoformat(last_update_time)
        if datetime.now() - last_update > timedelta(hours=720):
            print_panel("距离上次源更新已超过30天，源内可能有新模块或更新。", "提示")
            if confirm("是否在安装模块前更新源？", default=True):
                SourceManager().update_sources()
                env.set('last_origin_update_time', datetime.now().isoformat())
                print("✓ 源更新完成")
    module_info = mods.get_module(module_name)
    if module_info and not force:
        meta = module_info.get('info', {}).get('meta', {})
        print_panel(
            f"模块 {module_name} 已存在\n版本: {meta.get('version', '未知')}\n描述: {meta.get('description', '无描述')}",
            "模块已存在"
        )
        if not confirm("是否要强制重新安装？", default=False):
            return
    providers = env.get('providers', {})
    if isinstance(providers, str):
        providers = json.loads(providers)
    module_info_list = []
    for provider, url in providers.items():
        module_key = f"{module_name}@{provider}"
        modules_data = env.get('modules', {})
        if isinstance(modules_data, str):
            modules_data = json.loads(modules_data)
        if module_key in modules_data:
            module_data = modules_data[module_key]
            meta = module_data.get("meta", {})
            depsinfo = module_data.get("dependencies", {})
            module_info_list.append({
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
    if not module_info_list:
        print_panel(f"未找到模块 {module_name}", "错误")
        if providers:
            print("当前可用源:")
            for provider in providers:
                print(f"  - {provider}")
        return
    if len(module_info_list) > 1:
        print(f"找到 {len(module_info_list)} 个源的 {module_name} 模块：")
        rows = []
        for i, info in enumerate(module_info_list):
            rows.append([
                str(i+1), info['provider'], info['version'], info['description'], info['author']
            ])
        print_table(["编号", "源", "版本", "描述", "作者"], rows, "可选模块源")
        while True:
            choice = ask("请选择要安装的源 (输入编号)", default="1")
            if choice.isdigit() and 1 <= int(choice) <= len(module_info_list):
                selected_module = module_info_list[int(choice)-1]
                break
            else:
                print("输入无效，请重新选择")
    else:
        selected_module = module_info_list[0]
    for dep in selected_module['dependencies']:
        print(f"正在安装依赖模块 {dep}...")
        install_module(dep)
    third_party_deps = selected_module.get('pip_dependencies', [])
    if third_party_deps:
        print(f"模块 {module_name} 需要以下pip依赖: {', '.join(third_party_deps)}")
        if not install_pip_dependencies(third_party_deps):
            print(f"无法安装模块 {module_name} 的pip依赖，安装终止")
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
    mods.set_module(module_name, {
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
    print(f"模块 {module_name} 安装成功")

def uninstall_module(module_name):
    print_panel(f"准备卸载模块: {module_name}", "卸载摘要")
    module_info = mods.get_module(module_name)
    if not module_info:
        print_panel(f"模块 {module_name} 不存在", "错误")
        return
    meta = module_info.get('info', {}).get('meta', {})
    depsinfo = module_info.get('info', {}).get('dependencies', {})
    print_panel(
        f"版本: {meta.get('version', '未知')}\n描述: {meta.get('description', '无描述')}\npip依赖: {', '.join(depsinfo.get('pip', [])) or '无'}",
        "模块信息"
    )
    if not confirm("确认要卸载此模块吗？", default=False):
        print("卸载已取消")
        return
    script_dir = os.path.dirname(os.path.abspath(__file__))
    module_path = os.path.join(script_dir, 'modules', module_name)
    module_file_path = module_path + '.py'
    if os.path.exists(module_file_path):
        try:
            os.remove(module_file_path)
        except Exception as e:
            print_panel(f"删除模块文件 {module_name} 时出错: {e}", "错误")
    elif os.path.exists(module_path) and os.path.isdir(module_path):
        try:
            shutil.rmtree(module_path)
        except Exception as e:
            print_panel(f"删除模块目录 {module_name} 时出错: {e}", "错误")
    else:
        print_panel(f"模块 {module_name} 不存在", "错误")
        return
    pip_dependencies = depsinfo.get('pip', [])
    if pip_dependencies:
        all_modules = mods.get_all_modules()
        unused_pip_dependencies = []
        essential_packages = {'aiohttp'}
        for dep in pip_dependencies:
            if dep in essential_packages:
                print(f"跳过必要模块 {dep} 的卸载")
                continue
            is_dependency_used = False
            for name, info in all_modules.items():
                if name != module_name and dep in info.get('info', {}).get('dependencies', {}).get('pip', []):
                    is_dependency_used = True
                    break
            if not is_dependency_used:
                unused_pip_dependencies.append(dep)
        if unused_pip_dependencies:
            print_panel(
                f"以下 pip 依赖不再被其他模块使用:\n{', '.join(unused_pip_dependencies)}",
                "可卸载依赖"
            )
            if confirm("是否卸载这些 pip 依赖？", default=False):
                try:
                    subprocess.run(
                        [sys.executable, "-m", "pip", "uninstall", "-y"] + unused_pip_dependencies,
                        check=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    print_panel(
                        f"成功卸载 pip 依赖: {', '.join(unused_pip_dependencies)}",
                        "成功"
                    )
                except subprocess.CalledProcessError as e:
                    print_panel(
                        f"卸载 pip 依赖失败: {e.stderr.decode()}",
                        "错误"
                    )
    if mods.remove_module(module_name):
        print_panel(f"✓ 模块 {module_name} 已成功卸载", "成功")
    else:
        print_panel(f"模块 {module_name} 不存在", "错误")

def upgrade_all_modules(force=False):
    all_modules = mods.get_all_modules()
    if not all_modules:
        print("未找到任何模块，无法更新")
        return
    providers = env.get('providers', {})
    if isinstance(providers, str):
        providers = json.loads(providers)
    modules_data = env.get('modules', {})
    if isinstance(modules_data, str):
        modules_data = json.loads(modules_data)
    updates_available = []
    for module_name, module_info in all_modules.items():
        local_version = module_info.get('info', {}).get('meta', {}).get('version', '0.0.0')
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
        print("所有模块已是最新版本，无需更新")
        return
    print("\n以下模块有可用更新：")
    rows = []
    for update in updates_available:
        rows.append([update['name'], update['local_version'], update['remote_version'], update['provider']])
    print_table(["模块", "当前版本", "最新版本", "源"], rows, "可用更新")
    if not force:
        if not confirm("警告：更新模块可能会导致兼容性问题，请在更新前查看插件作者的相关声明。\n是否继续？", default=False):
            print("更新已取消")
            return
    for update in updates_available:
        print(f"正在更新模块 {update['name']}...")
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
        mods.set_all_modules(all_modules)
        print(f"模块 {update['name']} 已更新至版本 {update['remote_version']}")

def list_modules(module_name=None):
    all_modules = mods.get_all_modules()
    if not all_modules:
        print_panel("未在数据库中发现注册模块,正在初始化模块列表...", "提示")
        from . import init as init_module
        init_module()
        all_modules = mods.get_all_modules()
    if not all_modules:
        print_panel("未找到任何模块", "错误")
        return
    print_panel(f"找到 {len(all_modules)} 个模块", "统计")
    rows = []
    for name, info in all_modules.items():
        status = "✓" if info.get("status", True) else "✗"
        meta = info.get('info', {}).get('meta', {})
        depsinfo = info.get('info', {}).get('dependencies', {})
        optional_deps = depsinfo.get('optional', [])
        available_optional_deps = []
        missing_optional_deps = []
        if optional_deps:
            for dep in optional_deps:
                if isinstance(dep, list):
                    available_deps = [d for d in dep if d in all_modules]
                    if available_deps:
                        available_optional_deps.extend(available_deps)
                    else:
                        missing_optional_deps.extend(dep)
                elif dep in all_modules:
                    available_optional_deps.append(dep)
                else:
                    missing_optional_deps.append(dep)
            if missing_optional_deps:
                optional_dependencies = f"可用: {', '.join(available_optional_deps)} 缺失: {', '.join(missing_optional_deps)}"
            else:
                optional_dependencies = ', '.join(available_optional_deps) or '无'
        else:
            optional_dependencies = '无'
        dependencies = ', '.join(depsinfo.get('requires', [])) or '无'
        pip_dependencies = ', '.join(depsinfo.get('pip', [])) or '无'
        rows.append([
            name, status, meta.get('version', '未知'), meta.get('description', '无描述'),
            dependencies, optional_dependencies, pip_dependencies
        ])
    print_table(
        ["模块名称", "状态", "版本", "描述", "依赖", "可选依赖", "pip依赖"],
        rows,
        "模块列表"
    )
    enabled_count = sum(1 for m in all_modules.values() if m.get("status", True))
    disabled_count = len(all_modules) - enabled_count
    print_panel(f"已启用: {enabled_count}  已禁用: {disabled_count}", "模块状态统计")

def main():
    parser = argparse.ArgumentParser(
        description="ErisPulse 命令行工具",
        prog="ep"
    )
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
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
    if hasattr(args, 'init') and args.init:
        print("正在初始化模块列表...")
        from . import init as init_module
        init_module()
    if args.command == 'enable':
        for module_name in args.module_names:
            module_name = module_name.strip()
            if not module_name:
                continue
            if '*' in module_name or '?' in module_name:
                print(f"正在匹配模块模式: {module_name}...")
                all_modules = mods.get_all_modules()
                if not all_modules:
                    print_panel("未找到任何模块，请先更新源或检查配置", "错误")
                    continue
                matched_modules = [name for name in all_modules.keys() if fnmatch.fnmatch(name, module_name)]
                if not matched_modules:
                    print_panel(f"未找到匹配模块模式 {module_name} 的模块", "错误")
                    continue
                print(f"找到 {len(matched_modules)} 个匹配模块:")
                for i, matched_module in enumerate(matched_modules, start=1):
                    print(f"  {i}. {matched_module}")
                if not confirm("是否启用所有匹配模块？", default=True):
                    print("操作已取消")
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
                print(f"正在匹配模块模式: {module_name}...")
                all_modules = mods.get_all_modules()
                if not all_modules:
                    print_panel("未找到任何模块，请先更新源或检查配置", "错误")
                    continue
                matched_modules = [name for name in all_modules.keys() if fnmatch.fnmatch(name, module_name)]
                if not matched_modules:
                    print_panel(f"未找到匹配模块模式 {module_name} 的模块", "错误")
                    continue
                print(f"找到 {len(matched_modules)} 个匹配模块:")
                for i, matched_module in enumerate(matched_modules, start=1):
                    print(f"  {i}. {matched_module}")
                if not confirm("是否禁用所有匹配模块？", default=True):
                    print("操作已取消")
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
                print(f"正在匹配模块模式: {module_name}...")
                all_modules = mods.get_all_modules()
                if not all_modules:
                    print_panel("未找到任何模块，请先更新源或检查配置", "错误")
                    continue
                matched_modules = [name for name in all_modules.keys() if fnmatch.fnmatch(name, module_name)]
                if not matched_modules:
                    print_panel(f"未找到匹配模块模式 {module_name} 的模块", "错误")
                    continue
                print(f"找到 {len(matched_modules)} 个匹配模块:")
                for i, matched_module in enumerate(matched_modules, start=1):
                    print(f"  {i}. {matched_module}")
                if not confirm("是否卸载所有匹配模块？", default=True):
                    print("操作已取消")
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
                print(f"正在匹配模块模式: {module_name}...")
                all_modules = mods.get_all_modules()
                if not all_modules:
                    print_panel("未找到任何模块，请先更新源或检查配置", "错误")
                    continue
                matched_modules = [name for name in all_modules.keys() if fnmatch.fnmatch(name, module_name)]
                if not matched_modules:
                    print_panel(f"未找到匹配模块模式 {module_name} 的模块", "错误")
                    continue
                print(f"找到 {len(matched_modules)} 个匹配模块:")
                for i, matched_module in enumerate(matched_modules, start=1):
                    print(f"  {i}. {matched_module}")
                if not confirm("是否安装所有匹配模块？", default=True):
                    print("安装已取消")
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
                if confirm("源已添加，是否立即更新源以获取最新模块信息？", default=True):
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
