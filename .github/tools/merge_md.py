import os

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
        outfile.write("本文件由多个开发文档合并而成，用于辅助 AI 理解 ErisPulse 的相关功能。\n\n")

        outfile.write("## 各文件对应内容说明\n\n")
        outfile.write("| 文件名 | 作用 |\n")
        outfile.write("|--------|------|\n")
        
        # 写入文件说明
        for file_info in files_to_merge:
            outfile.write(f"| {os.path.basename(file_info['path'])} | {file_info.get('description', '')} |\n")
        
        outfile.write("\n## 合并内容开始\n\n")

        # 合并文件内容
        for file_info in files_to_merge:
            file_path = file_info['path']
            if os.path.exists(file_path):
                filename = os.path.basename(file_path)
                with open(file_path, 'r', encoding='utf-8') as infile:
                    content = infile.read()
                    outfile.write(f"<!-- {filename} -->\n\n")
                    outfile.write(content)
                    outfile.write(f"\n\n<!--- End of {filename} -->\n\n")
            else:
                print(f"⚠️ 文件不存在，跳过: {file_path}")

def merge_api_docs(api_dir, output_file):
    """
    合并API文档
    
    :param api_dir: API文档目录
    :param output_file: 输出文件路径
    """
    with open(output_file, 'a', encoding='utf-8') as outfile:
        outfile.write("<!-- API文档 -->\n\n")
        outfile.write("# API参考\n\n")

        # 递归遍历API目录
        for root, _, files in os.walk(api_dir):
            for file in files:
                if file.endswith('.md'):
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, api_dir)
                    
                    with open(file_path, 'r', encoding='utf-8') as infile:
                        content = infile.read()
                        outfile.write(f"## {rel_path}\n\n")
                        outfile.write(content)
                        outfile.write("\n\n")
        
        outfile.write("<!--- End of API文档 -->\n")

def generate_full_document():
    """生成完整文档"""
    print("⏳ 正在生成完整文档...")
    
    # 定义要合并的文件
    files_to_merge = [
        {"path": "docs/quick-start.md", "description": "快速开始指南"},
        {"path": "docs/UseCore.md", "description": "核心功能使用说明"},
        {"path": "docs/PlatformFeatures.md", "description": "平台功能说明"},
        {"path": "docs/Development/Module.md", "description": "模块开发指南"},
        {"path": "docs/Development/Adapter.md", "description": "适配器开发指南"},
        {"path": "docs/AdapterStandards/APIResponse.md", "description": "API响应标准"},
        {"path": "docs/AdapterStandards/EventConversion.md", "description": "事件转换标准"},
    ]
    
    output_file = "docs/AIDocs/ErisPulse-Full.md"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    merge_md_files(output_file, files_to_merge, "完整开发文档")
    merge_api_docs("docs/api", output_file)
    
    print(f"🎉 完整文档生成完成，已保存到: {output_file}")

def generate_core_document():
    """生成核心功能文档"""
    print("⏳ 正在生成核心功能文档...")
    
    files_to_merge = [
        {"path": "docs/quick-start.md", "description": "快速开始指南"},
        {"path": "docs/UseCore.md", "description": "核心功能使用说明"},
        {"path": "docs/PlatformFeatures.md", "description": "平台功能说明"},
    ]
    
    output_file = "docs/AIDocs/ErisPulse-Core.md"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    merge_md_files(output_file, files_to_merge, "核心功能文档")
    merge_api_docs("docs/api/ErisPulse/Core", output_file)
    
    print(f"🎉 核心功能文档生成完成，已保存到: {output_file}")

def generate_dev_documents():
    """生成开发文档（模块和适配器）"""
    print("⏳ 正在生成开发文档...")
    
    # 模块开发文档
    module_files = [
        {"path": "docs/UseCore.md", "description": "核心功能使用说明"},
        {"path": "docs/PlatformFeatures.md", "description": "平台支持的发送类型及差异性说明"},
        {"path": "docs/Development/Module.md", "description": "模块开发指南"}
    ]
    
    module_output = "docs/AIDocs/ErisPulse-ModuleDev.md"
    merge_md_files(module_output, module_files, "模块开发文档")
    merge_api_docs("docs/api/", module_output)
    print(f"🎉 模块开发文档生成完成，已保存到: {module_output}")
    
    # 适配器开发文档
    adapter_files = [
        {"path": "docs/UseCore.md", "description": "核心功能使用说明"},
        {"path": "docs/Development/Adapter.md", "description": "适配器开发指南"},
        {"path": "docs/AdapterStandards/APIResponse.md", "description": "API响应标准"},
        {"path": "docs/AdapterStandards/EventConversion.md", "description": "事件转换标准"},
    ]
    
    adapter_output = "docs/AIDocs/ErisPulse-AdapterDev.md"
    merge_md_files(adapter_output, adapter_files, "适配器开发文档")
    merge_api_docs("docs/api", adapter_output)
    print(f"🎉 适配器开发文档生成完成，已保存到: {adapter_output}")

if __name__ == "__main__":
    # 生成所有文档
    generate_full_document()
    generate_core_document()
    generate_dev_documents()
    
    print("✅ 所有文档生成完成")