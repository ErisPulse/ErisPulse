import os

def merge_markdown_files(api_dir, additional_files, output_file):
    """
    合并API文档和其他指定文档
    
    :param api_dir: API文档目录
    :param additional_files: 需要合并的其他文档列表
    :param output_file: 输出文件路径
    """
    with open(output_file, 'w', encoding='utf-8') as outfile:
        # 写入头部说明
        outfile.write("# ErisPulse 开发文档合集\n\n")
        outfile.write("本文件由多个开发文档合并而成，用于辅助 AI 理解 ErisPulse 的模块开发规范与 SDK 使用方式。\n\n")

        outfile.write("## 各文件对应内容说明\n\n")
        outfile.write("| 文件名 | 作用 |\n")
        outfile.write("|--------|------|\n")
        outfile.write("| ADAPTERS.md | 平台适配器说明，包括事件监听和消息发送方式 |\n")
        outfile.write("| Conversion-Standard.md | 数据转换标准说明 |\n")
        outfile.write("| DEVELOPMENT.md | 模块结构定义、入口文件格式、Main 类规范 |\n")
        outfile.write("| UseCore.md | 核心功能使用说明 |\n")
        outfile.write("| API文档 | 自动生成的API参考文档 |\n\n")

        outfile.write("## 合并内容开始\n\n")

        # 首先合并指定的其他文档
        for file_path in additional_files:
            if os.path.exists(file_path):
                filename = os.path.basename(file_path)
                with open(file_path, 'r', encoding='utf-8') as infile:
                    content = infile.read()
                    outfile.write(f"<!-- {filename} -->\n\n")
                    outfile.write(content)
                    outfile.write(f"\n\n<!--- End of {filename} -->\n\n")
            else:
                print(f"⚠️ 文件不存在，跳过: {file_path}")

        # 然后合并API目录下的所有Markdown文件
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

if __name__ == "__main__":
    api_directory = "docs/api"
    
    additional_documents = [
        "docs/UseCore.md",
        "docs/DEVELOPMENT.md",
        "docs/ADAPTERS.md",
        "docs/Conversion-Standard​.md"
    ]
    
    # 输出文件路径
    output_file_path = "docs/ForAIDocs/ErisPulseDevelop.md"

    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

    print("⏳ 正在合并文档...")
    merge_markdown_files(api_directory, additional_documents, output_file_path)
    print(f"🎉 文档合并完成，已保存到: {output_file_path}")