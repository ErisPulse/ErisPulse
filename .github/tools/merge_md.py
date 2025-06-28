def merge_markdown_files(file_paths, output_file):
    with open(output_file, 'w', encoding='utf-8') as outfile:
        # 写入头部说明：介绍每个文件的作用（不包含路径）
        outfile.write("# ErisPulse 开发文档合集\n\n")
        outfile.write("本文件由多个开发文档合并而成，用于辅助 AI 理解 ErisPulse 的模块开发规范与 SDK 使用方式。\n\n")

        outfile.write("## 各文件对应内容说明\n\n")
        outfile.write("| 文件名 | 作用 |\n")
        outfile.write("|--------|------|\n")
        outfile.write("| README.md | 项目概览、安装说明和快速入门指南 |\n")
        outfile.write("| DEVELOPMENT.md | 模块结构定义、入口文件格式、Main 类规范 |\n")
        outfile.write("| ADAPTERS.md | 平台适配器说明，包括事件监听和消息发送方式 |\n")
        outfile.write("| REFERENCE.md | SDK 接口调用方式（如 `sdk.env`, `sdk.logger`, `sdk.adapter` 等） |\n\n")

        outfile.write("## 合并内容开始\n\n")

        for file_path in file_paths:
            filename = file_path.split("/")[-1]
            with open(file_path, 'r', encoding='utf-8') as infile:
                content = infile.read()
                outfile.write(f"<!-- {filename} -->\n\n")
                outfile.write(content)
                outfile.write(f"\n\n<!--- End of {filename} -->\n\n")

if __name__ == "__main__":
    files_to_merge = [
        "README.md",
        
        "docs/DEVELOPMENT.md",
        
        "docs/REFERENCE.md",

        "docs/ADAPTERS.md",

        "docs/CLI.md"
    ]
    output_file = "docs/ForAIDocs/ErisPulseDevelop.md"

    merge_markdown_files(files_to_merge, output_file)