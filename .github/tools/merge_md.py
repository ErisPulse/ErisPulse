import os
from datetime import datetime

"""
ErisPulse文档合并工具

使用方法:
1. 默认生成包含API的完整文档和开发文档:
   python merge_md.py

2. 生成不包含API的文档版本:
   python merge_md.py no-api

3. 只生成完整文档:
   python merge_md.py full

4. 只生成开发文档:
   python merge_md.py dev

5. 只生成核心文档:
   python merge_md.py core

输出文件位置:
- 完整文档: docs/ai/AIDocs/ErisPulse-Full.md
- 模块开发文档: docs/ai/AIDocs/ErisPulse-ModuleDev.md  
- 适配器开发文档: docs/ai/AIDocs/ErisPulse-AdapterDev.md
- 核心文档: docs/ai/AIDocs/ErisPulse-Core.md

no-api版本输出文件位置:
- 完整文档(no-api): docs/ai/AIDocs/no-api/ErisPulse-Full.md
- 模块开发文档(no-api): docs/ai/AIDocs/no-api/ErisPulse-ModuleDev.md  
- 适配器开发文档(no-api): docs/ai/AIDocs/no-api/ErisPulse-AdapterDev.md
- 核心文档(no-api): docs/ai/AIDocs/no-api/ErisPulse-Core.md
"""

def merge_md_files(output_file, files_to_merge, title="文档合集"):
    """
    合并多个Markdown文件
    
    :param output_file: 输出文件路径
    :param files_to_merge: 要合并的文件列表，包含文件路径和描述
    :param title: 文档标题
    """
    with open(output_file, 'w', encoding='utf-8') as outfile:
        # 写入头部说明
        outfile.write(f"# ErisPulse {title}\n\n")
        outfile.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        outfile.write("本文件由多个开发文档合并而成，用于辅助开发者理解 ErisPulse 的相关功能。\n\n")

        # 写入目录
        outfile.write("## 目录\n\n")
        for i, file_info in enumerate(files_to_merge, 1):
            filename = os.path.basename(file_info['path'])
            outfile.write(f"{i}. [{file_info.get('description', filename)}](#{filename.replace('.', '').replace(' ', '-').replace('/', '').replace('(', '').replace(')', '')})\n")
        outfile.write("\n")

        outfile.write("## 各文件对应内容说明\n\n")
        outfile.write("| 文件名 | 作用 |\n")
        outfile.write("|--------|------|\n")
        
        # 写入文件说明
        for file_info in files_to_merge:
            filename = os.path.basename(file_info['path'])
            outfile.write(f"| [{filename}](#{filename.replace('.', '').replace(' ', '-').replace('/', '').replace('(', '').replace(')', '')}) | {file_info.get('description', '')} |\n")
        
        outfile.write("\n---\n\n")

        # 合并文件内容
        for file_info in files_to_merge:
            file_path = file_info['path']
            if os.path.exists(file_path):
                filename = os.path.basename(file_path)
                anchor_name = filename.replace('.', '').replace(' ', '-').replace('/', '').replace('(', '').replace(')', '')
                outfile.write(f"<a id=\"{anchor_name}\"></a>\n")
                outfile.write(f"## {file_info.get('description', filename)}\n\n")
                
                with open(file_path, 'r', encoding='utf-8') as infile:
                    content = infile.read()
                    outfile.write(content)
                    outfile.write("\n\n---\n\n")
            else:
                print(f"文件不存在，跳过: {file_path}")

def merge_api_docs(api_dir, output_file):
    """
    合并API文档
    
    :param api_dir: API文档目录
    :param output_file: 输出文件路径
    """
    if not os.path.exists(api_dir):
        print(f"API文档目录不存在: {api_dir}")
        return
        
    with open(output_file, 'a', encoding='utf-8') as outfile:
        outfile.write("# API参考\n\n")
        
        # 收集所有API文档文件
        api_files = []
        for root, _, files in os.walk(api_dir):
            for file in files:
                if file.endswith('.md'):
                    file_path = os.path.join(root, file)
                    api_files.append(file_path)
        
        # 按路径排序以保持一致性
        api_files.sort()
        
        # 生成API文档目录
        outfile.write("## API文档目录\n\n")
        for file_path in api_files:
            rel_path = os.path.relpath(file_path, api_dir)
            anchor = rel_path.replace(os.sep, "_").replace(".md", "").replace("/", "_").replace("\\", "_")
            outfile.write(f"- [{rel_path}](#{anchor})\n")
        outfile.write("\n---\n\n")

        # 合并API文档内容
        for file_path in api_files:
            rel_path = os.path.relpath(file_path, api_dir)
            anchor = rel_path.replace(os.sep, "_").replace(".md", "").replace("/", "_").replace("\\", "_")
            
            outfile.write(f"<a id=\"{anchor}\"></a>\n")
            outfile.write(f"## {rel_path}\n\n")
            
            try:
                with open(file_path, 'r', encoding='utf-8') as infile:
                    content = infile.read()
                    lines = content.split('\n')
                    if lines and lines[0].startswith('# '):
                        content = '\n'.join(lines[1:])
                    
                    outfile.write(content)
                    outfile.write("\n\n")
            except Exception as e:
                outfile.write(f"无法读取文件 {file_path}: {str(e)}\n\n")
        
        outfile.write("---\n")

def get_core_files():
    """
    获取core目录下的所有文档文件
    """
    core_files = []
    core_dir = "docs/core"
    
    if os.path.exists(core_dir):
        # 按重要性排序的文件列表
        important_files = [
            "README.md",
            "concepts.md", 
            "modules.md",
            "adapters.md",
            "event-system.md",
            "cli.md",
            "best-practices.md"
        ]
        
        # 按顺序添加文件
        for filename in important_files:
            file_path = os.path.join(core_dir, filename)
            if os.path.exists(file_path):
                description = ""
                if filename == "README.md":
                    description = "核心功能文档列表"
                elif filename == "concepts.md":
                    description = "核心概念"
                elif filename == "modules.md":
                    description = "核心模块详解"
                elif filename == "adapters.md":
                    description = "适配器系统"
                elif filename == "event-system.md":
                    description = "事件系统"
                elif filename == "cli.md":
                    description = "命令行接口"
                elif filename == "best-practices.md":
                    description = "最佳实践"
                
                core_files.append({
                    "path": file_path,
                    "description": description
                })
    
    return core_files

def get_development_files():
    """
    获取development目录下的所有文档文件
    """
    dev_files = []
    dev_dir = "docs/development"
    
    if os.path.exists(dev_dir):
        # 按重要性排序的文件列表
        important_files = [
            "README.md",
            "module.md",
            "adapter.md", 
            "cli.md"
        ]
        
        # 按顺序添加文件
        for filename in important_files:
            file_path = os.path.join(dev_dir, filename)
            if os.path.exists(file_path):
                description = ""
                if filename == "README.md":
                    description = "开发者指南列表"
                elif filename == "module.md":
                    description = "模块开发指南"
                elif filename == "adapter.md":
                    description = "适配器开发指南"
                elif filename == "cli.md":
                    description = "CLI开发指南"
                
                dev_files.append({
                    "path": file_path,
                    "description": description
                })
    
    return dev_files

def get_standards_files():
    """
    获取standards目录下的所有文档文件
    """
    standards_files = []
    standards_dir = "docs/standards"
    
    if os.path.exists(standards_dir):
        # 按重要性排序的文件列表
        important_files = [
            "README.md",
            "event-conversion.md",
            "api-response.md"
        ]
        
        # 按顺序添加文件
        for filename in important_files:
            file_path = os.path.join(standards_dir, filename)
            if os.path.exists(file_path):
                description = ""
                if filename == "README.md":
                    description = "标准规范总览"
                elif filename == "event-conversion.md":
                    description = "事件转换标准"
                elif filename == "api-response.md":
                    description = "API响应标准"
                
                standards_files.append({
                    "path": file_path,
                    "description": description
                })
    
    return standards_files

def get_platform_features_files():
    """
    获取platform-features目录下的所有文档文件
    """
    platform_files = []
    platform_dir = "docs/platform-features"
    
    if os.path.exists(platform_dir):
        # 按重要性排序的文件列表
        important_files = [
            "README.md",
            "yunhu.md",
            "telegram.md",
            "onebot11.md",
            "email.md"
        ]
        
        # 按顺序添加文件
        for filename in important_files:
            file_path = os.path.join(platform_dir, filename)
            if os.path.exists(file_path):
                # 跳过维护说明文件
                if filename == "maintain-notes.md":
                    continue
                    
                description = ""
                if filename == "README.md":
                    description = "平台特性总览"
                elif filename == "yunhu.md":
                    description = "云湖平台特性"
                elif filename == "telegram.md":
                    description = "Telegram平台特性"
                elif filename == "onebot11.md":
                    description = "OneBot11平台特性"
                elif filename == "email.md":
                    description = "邮件平台特性"
                
                platform_files.append({
                    "path": file_path,
                    "description": description
                })
    
    return platform_files

def generate_full_document(include_api=True):
    print("正在生成完整文档...")
    
    # 基础文件
    base_files = [
        {"path": "docs/README.md", "description": "文档总览"},
        {"path": "docs/quick-start.md", "description": "快速开始指南"},
    ]
    
    # 添加核心文档
    core_files = get_core_files()
    
    # 添加开发文档
    dev_files = get_development_files()
    
    # 添加标准文档
    standards_files = get_standards_files()
    
    # 添加平台特性文件
    platform_files = get_platform_features_files()
    
    # 合并所有文件
    files_to_merge = base_files + core_files + dev_files + standards_files + platform_files
    
    # 过滤不存在的文件
    existing_files = [f for f in files_to_merge if os.path.exists(f['path'])]
    if len(existing_files) != len(files_to_merge):
        print(f"警告: {len(files_to_merge) - len(existing_files)} 个文件不存在，已跳过")
    
    # 根据是否包含API决定输出路径
    if include_api:
        output_file = "docs/ai/AIDocs/ErisPulse-Full.md"
    else:
        output_file = "docs/ai/AIDocs/no-api/ErisPulse-Full.md"
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    merge_md_files(output_file, existing_files, "完整开发文档")
    
    # 根据参数决定是否合并API文档
    if include_api:
        merge_api_docs("docs/api", output_file)
    
    api_status = "包含API" if include_api else "不包含API"
    print(f"完整文档生成完成（{api_status}），已保存到: {output_file}")

def generate_dev_documents(include_api=True):
    print("正在生成开发文档...")
    
    # 模块开发文档
    module_files = [
        {"path": "docs/README.md", "description": "文档总览"},
        {"path": "docs/quick-start.md", "description": "快速开始指南"},
        {"path": "docs/core/concepts.md", "description": "基础架构和设计理念"},
        {"path": "docs/core/modules.md", "description": "核心模块"},
        {"path": "docs/core/adapters.md", "description": "适配器"},
        {"path": "docs/core/event-system.md", "description": "事件系统"},
    ]
    
    # 添加开发文档 (包括模块开发指南)
    dev_files = get_development_files()
    module_dev_files = [f for f in dev_files if "模块" in f["description"] or "指南列表" in f["description"]]
    
    # 添加标准文档
    standards_files = get_standards_files()
    
    # 添加平台特性文件
    platform_files = get_platform_features_files()
    
    # 合并所有文件
    files_to_merge = module_files + module_dev_files + standards_files + platform_files
    
    # 过滤不存在的文件
    existing_files = [f for f in files_to_merge if os.path.exists(f['path'])]
    
    # 根据是否包含API决定输出路径
    if include_api:
        module_output = "docs/ai/AIDocs/ErisPulse-ModuleDev.md"
    else:
        module_output = "docs/ai/AIDocs/no-api/ErisPulse-ModuleDev.md"
    
    os.makedirs(os.path.dirname(module_output), exist_ok=True)
    merge_md_files(module_output, existing_files, "模块开发文档")

    api_status = "包含API" if include_api else "不包含API"
    print(f"模块开发文档生成完成（{api_status}），已保存到: {module_output}")
    
    # 适配器开发文档
    adapter_files = [
        {"path": "docs/README.md", "description": "文档总览"},
        {"path": "docs/quick-start.md", "description": "快速开始指南"},
        {"path": "docs/core/concepts.md", "description": "核心概念"},
        {"path": "docs/core/modules.md", "description": "核心模块"},
        {"path": "docs/core/adapters.md", "description": "适配器系统"},
        {"path": "docs/core/event-system.md", "description": "事件系统"},
        {"path": "docs/core/best-practices.md", "description": "最佳实践"},
    ]
    
    # 添加开发文档 (包括适配器开发指南)
    adapter_dev_files = [f for f in dev_files if "适配器" in f["description"] or "指南列表" in f["description"]]
    
    # 合并所有文件
    files_to_merge = adapter_files + adapter_dev_files + standards_files + platform_files
    
    # 过滤不存在的文件
    existing_files = [f for f in files_to_merge if os.path.exists(f['path'])]
    
    # 根据是否包含API决定输出路径
    if include_api:
        adapter_output = "docs/ai/AIDocs/ErisPulse-AdapterDev.md"
    else:
        adapter_output = "docs/ai/AIDocs/no-api/ErisPulse-AdapterDev.md"
    
    os.makedirs(os.path.dirname(adapter_output), exist_ok=True)
    merge_md_files(adapter_output, existing_files, "适配器开发文档")
    
    # 根据参数决定是否合并API文档
    if include_api:
        merge_api_docs("docs/api", adapter_output)
    
    print(f"适配器开发文档生成完成（{api_status}），已保存到: {adapter_output}")

def generate_core_document(include_api=True):
    print("正在生成核心文档...")
    
    # 基础文件
    base_files = [
        {"path": "docs/README.md", "description": "文档总览"},
        {"path": "docs/quick-start.md", "description": "快速开始指南"},
    ]
    
    # 核心文档
    core_files = get_core_files()
    
    # 添加平台特性文件
    platform_files = get_platform_features_files()
    
    # 合并所有文件
    files_to_merge = base_files + core_files + platform_files
    
    # 过滤不存在的文件
    existing_files = [f for f in files_to_merge if os.path.exists(f['path'])]
    
    # 根据是否包含API决定输出路径
    if include_api:
        core_output = "docs/ai/AIDocs/ErisPulse-Core.md"
    else:
        core_output = "docs/ai/AIDocs/no-api/ErisPulse-Core.md"
    
    os.makedirs(os.path.dirname(core_output), exist_ok=True)
    merge_md_files(core_output, existing_files, "核心功能文档")
    
    # 根据参数决定是否合并API文档
    if include_api:
        merge_api_docs("docs/api", core_output)
    
    api_status = "包含API" if include_api else "不包含API"
    print(f"核心文档生成完成（{api_status}），已保存到: {core_output}")

def generate_custom_document(title, files, api_dirs, output_path):
    """
    生成自定义文档
    
    :param title: 文档标题
    :param files: 要合并的文件列表
    :param api_dirs: 要合并的API目录列表
    :param output_path: 输出路径
    """
    print(f"正在生成{title}...")
    
    # 过滤不存在的文件
    existing_files = [f for f in files if os.path.exists(f['path'])]
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    merge_md_files(output_path, existing_files, title)
    
    # API文档
    for api_dir in api_dirs:
        merge_api_docs(api_dir, output_path)
    
    print(f"{title}生成完成，已保存到: {output_path}")

def generate_no_api_documents():
    print("正在生成no-api版本文档...")
    
    # 生成不包含API的完整文档
    generate_full_document(include_api=False)
    
    # 生成不包含API的开发文档
    generate_dev_documents(include_api=False)
    
    # 生成不包含API的核心文档
    generate_core_document(include_api=False)
    
    print("所有no-api版本文档生成完成")

if __name__ == "__main__":
    import sys
    
    try:
        # 检查命令行参数
        if len(sys.argv) > 1:
            if sys.argv[1] == "no-api":
                generate_no_api_documents()
            elif sys.argv[1] == "full":
                generate_full_document()
                generate_dev_documents()
                generate_core_document()
            elif sys.argv[1] == "dev":
                generate_dev_documents()
            elif sys.argv[1] == "core":
                generate_core_document()
            else:
                print(f"未知参数: {sys.argv[1]}")
                print("可用参数: no-api, full, dev, core")
        else:
            generate_no_api_documents()
            generate_full_document()
            generate_dev_documents()
            generate_core_document()
        print("所有文档生成完成")
    except Exception as e:
        print(f"文档生成过程中出现错误: {str(e)}")