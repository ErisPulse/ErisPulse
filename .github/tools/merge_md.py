import os
from datetime import datetime

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
            outfile.write(f"{i}. [{file_info.get('description', filename)}](#{filename.replace('.', '').replace(' ', '-')})\n")
        outfile.write("\n")

        outfile.write("## 各文件对应内容说明\n\n")
        outfile.write("| 文件名 | 作用 |\n")
        outfile.write("|--------|------|\n")
        
        # 写入文件说明
        for file_info in files_to_merge:
            filename = os.path.basename(file_info['path'])
            outfile.write(f"| [{filename}](#{filename.replace('.', '').replace(' ', '-')}) | {file_info.get('description', '')} |\n")
        
        outfile.write("\n---\n\n")

        # 合并文件内容
        for file_info in files_to_merge:
            file_path = file_info['path']
            if os.path.exists(file_path):
                filename = os.path.basename(file_path)
                outfile.write(f"<a id=\"{filename.replace('.', '').replace(' ', '-')}\"></a>\n")
                outfile.write(f"## {file_info.get('description', filename)}\n\n")
                
                with open(file_path, 'r', encoding='utf-8') as infile:
                    content = infile.read()
                    outfile.write(content)
                    outfile.write(f"\n\n---\n\n")
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
            anchor = rel_path.replace(os.sep, "_").replace(".md", "")
            outfile.write(f"- [{rel_path}](#{anchor})\n")
        outfile.write("\n---\n\n")

        # 合并API文档内容
        for file_path in api_files:
            rel_path = os.path.relpath(file_path, api_dir)
            anchor = rel_path.replace(os.sep, "_").replace(".md", "")
            
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

def generate_full_document():
    print("正在生成完整文档...")
    
    # 要合并的文件
    files_to_merge = [
        {"path": "docs/quick-start.md", "description": "快速开始指南"},
        {"path": "docs/platform-features.md", "description": "平台功能说明"},
        {"path": "docs/core/concepts.md", "description": "核心概念"},
        {"path": "docs/core/modules.md", "description": "核心模块"},
        {"path": "docs/core/adapters.md", "description": "适配器系统"},
        {"path": "docs/core/event-system.md", "description": "事件系统"},
        {"path": "docs/core/best-practices.md", "description": "最佳实践"},
        {"path": "docs/development/module.md", "description": "模块开发指南"},
        {"path": "docs/development/adapter.md", "description": "适配器开发指南"},
        {"path": "docs/standards/api-response.md", "description": "API响应标准"},
        {"path": "docs/standards/event-conversion.md", "description": "事件转换标准"},
    ]
    
    # 过滤不存在的文件
    existing_files = [f for f in files_to_merge if os.path.exists(f['path'])]
    if len(existing_files) != len(files_to_merge):
        print(f"警告: {len(files_to_merge) - len(existing_files)} 个文件不存在，已跳过")
    
    output_file = "docs/ai/AIDocs/ErisPulse-Full.md"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    merge_md_files(output_file, existing_files, "完整开发文档")
    merge_api_docs("docs/api", output_file)
    
    print(f"完整文档生成完成，已保存到: {output_file}")

def generate_dev_documents():
    print("正在生成开发文档...")
    
    # 模块开发文档
    module_files = [
        {"path": "docs/quick-start.md", "description": "快速开始指南"},
        {"path": "docs/core/concepts.md", "description": "基础架构和设计理念"},
        {"path": "docs/core/modules.md", "description": "核心模块"},
        {"path": "docs/core/adapters.md", "description": "适配器"},
        {"path": "docs/core/event-system.md", "description": "事件系统"},
        {"path": "docs/platform-features.md", "description": "平台功能说明"},
        {"path": "docs/standards/event-conversion.md", "description": "标准事件的定义"},
        {"path": "docs/standards/api-response.md", "description": "api响应的格式" },
    ]
    
    # 过滤不存在的文件
    existing_module_files = [f for f in module_files if os.path.exists(f['path'])]
    
    module_output = "docs/ai/AIDocs/ErisPulse-ModuleDev.md"
    os.makedirs(os.path.dirname(module_output), exist_ok=True)
    merge_md_files(module_output, existing_module_files, "模块开发文档")

    print(f"模块开发文档生成完成，已保存到: {module_output}")
    
    # 适配器开发文档
    adapter_files  = [
        {"path": "docs/quick-start.md", "description": "快速开始指南"},
        {"path": "docs/platform-features.md", "description": "平台功能说明"},
        {"path": "docs/core/concepts.md", "description": "核心概念"},
        {"path": "docs/core/modules.md", "description": "核心模块"},
        {"path": "docs/core/adapters.md", "description": "适配器系统"},
        {"path": "docs/core/event-system.md", "description": "事件系统"},
        {"path": "docs/core/best-practices.md", "description": "最佳实践"},
        {"path": "docs/development/module.md", "description": "模块开发指南"},
        {"path": "docs/development/adapter.md", "description": "适配器开发指南"},
        {"path": "docs/standards/api-response.md", "description": "API响应标准"},
        {"path": "docs/standards/event-conversion.md", "description": "事件转换标准"},
    ]
    
    # 过滤不存在的文件
    existing_adapter_files = [f for f in adapter_files if os.path.exists(f['path'])]
    
    adapter_output = "docs/ai/AIDocs/ErisPulse-AdapterDev.md"
    os.makedirs(os.path.dirname(adapter_output), exist_ok=True)
    merge_md_files(adapter_output, existing_adapter_files, "适配器开发文档")
    merge_api_docs("docs/api", adapter_output)
    
    print(f"适配器开发文档生成完成，已保存到: {adapter_output}")

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
    merge_api_docs("docs/api", output_path)
    
    print(f"{title}生成完成，已保存到: {output_path}")

if __name__ == "__main__":
    try:
        generate_full_document()
        generate_dev_documents()
        print("所有文档生成完成")
    except Exception as e:
        print(f"文档生成过程中出现错误: {str(e)}")