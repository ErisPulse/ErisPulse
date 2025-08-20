#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🌟 艾莉丝的版本探知魔法阵 ~
这是一个用于自动检测和更新 packages.json 中模块版本的魔法脚本
"""

import json
import requests
import os
from datetime import datetime, timezone
import re

# 魔法咒语准备
headers = {
    'Authorization': f'token {os.environ["GITHUB_TOKEN"]}',
    'Accept': 'application/vnd.github.v3+json'
}

def get_latest_pypi_version(package_name):
    try:
        print(f"正在探查 {package_name} 的 PyPI 版本...")
        response = requests.get(f'https://pypi.org/pypi/{package_name}/json', timeout=10)
        if response.status_code == 200:
            data = response.json()
            version = data['info']['version']
            print(f"找到了 {package_name} 的最新版本: {version}")
            return version
    except Exception as e:
        print(f"💢 探查 {package_name} 的 PyPI 版本时遇到了障碍: {e}")
    return None

def get_latest_github_release(repo_url):
    try:
        print(f"正在探查 {repo_url} 的 GitHub 发布版本...")
        if 'github.com' in repo_url:
            # 从仓库 URL 提取 owner/repo
            parts = repo_url.rstrip('/').split('/')
            owner_repo = f"{parts[-2]}/{parts[-1]}"
            
            response = requests.get(f'https://api.github.com/repos/{owner_repo}/releases/latest', headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                version = data['tag_name'].lstrip('v')  # 移除可能的 'v' 前缀
                print(f"✨ 找到了 {owner_repo} 的最新发布版本: {version}")
                return version
    except Exception as e:
        print(f"💢 探查 {repo_url} 的 GitHub 版本时遇到了障碍: {e}")
    return None

def is_version_newer(new_version, old_version):
    try:
        def version_to_tuple(v):
            # 移除版本字符串中的非数字和点字符（如 dev, alpha, beta 等）
            v = re.sub(r'[^\d.]', '', v)
            return tuple(map(int, (v.split('.'))))
        
        return version_to_tuple(new_version) > version_to_tuple(old_version)
    except Exception:
        # 如果无法解析，保守地认为需要更新
        return new_version != old_version

def update_packages():
    print("🌟 艾莉丝的版本探知魔法阵启动!")
    
    # 读取当前的魔法书
    try:
        with open('packages.json', 'r', encoding='utf-8') as f:
            packages = json.load(f)
        print("成功打开了 packages.json 魔法书!")
    except Exception as e:
        print(f"无法打开 packages.json 魔法书: {e}")
        return
    
    current_time = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    packages['last_updated'] = current_time
    print(f"更新时间戳: {current_time}")
    
    updated_count = 0
    
    for category in ['modules', 'adapters', 'cli_extensions']:
        if category in packages:
            print(f"开始探查 {category} 分类...")
            for name, info in packages[category].items():
                try:
                    old_version = info.get('version', '0.0.0')
                    print(f"检查 {name} (当前版本: {old_version})")
                    
                    # 尝试从 PyPI 获取最新版本
                    new_version = None
                    if 'package' in info:
                        new_version = get_latest_pypi_version(info.get('package', ''))
                    
                    # 如果 PyPI 获取失败，尝试从 GitHub 获取
                    if not new_version and 'repository' in info:
                        new_version = get_latest_github_release(info['repository'])
                    
                    # 如果找到了新版本且版本更高，则更新
                    if new_version and is_version_newer(new_version, old_version):
                        packages[category][name]['version'] = new_version
                        print(f"更新 {name}: {old_version} -> {new_version}")
                        updated_count += 1
                    else:
                        print(f"✨ {name} 已经是最新版本啦~")
                        
                except Exception as e:
                    print(f"处理 {name} 时遇到了意外: {e}")
    
    # 写回魔法书
    try:
        with open('packages.json', 'w', encoding='utf-8') as f:
            json.dump(packages, f, ensure_ascii=False, indent=4)
        print(f"魔法书更新完成! 共更新了 {updated_count} 个模块~")
    except Exception as e:
        print(f"无法保存魔法书: {e}")
        return
    
    if updated_count > 0:
        print("艾莉丝的版本探知魔法大成功!")
    else:
        print("今天没有发现需要更新的模块呢~")

if __name__ == '__main__':
    update_packages()