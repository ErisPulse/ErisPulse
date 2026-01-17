"""
ErisPulse API 文档生成器

从Python源代码自动生成API文档
"""

import os
import ast
import re
import argparse
import hashlib
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from collections import defaultdict


def compute_content_hash(content: str) -> str:
    """
    计算内容的SHA256哈希值（排除最后更新时间）
    
    :param content: 内容字符串
    :return: 哈希值
    """
    # 移除最后更新时间行以避免时间戳影响哈希
    lines = content.split('\n')
    filtered_lines = [line for line in lines if not line.strip().startswith('> 最后更新：')]
    normalized_content = '\n'.join(filtered_lines)
    return hashlib.sha256(normalized_content.encode('utf-8')).hexdigest()


def should_update_file(file_path: str, new_content: str) -> bool:
    """
    检查文件是否需要更新（基于内容哈希）
    
    :param file_path: 文件路径
    :param new_content: 新内容
    :return: 是否需要更新
    """
    if not os.path.exists(file_path):
        return True
    
    # 读取现有文件内容并计算哈希
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            existing_content = f.read()
        existing_hash = compute_content_hash(existing_content)
        new_hash = compute_content_hash(new_content)
        return existing_hash != new_hash
    except Exception:
        return True


def format_timestamp(timestamp: Optional[float] = None) -> str:
    """
    格式化时间戳为可读字符串
    
    :param timestamp: 时间戳，如果为None则使用当前时间
    :return: 格式化后的时间字符串
    """
    if timestamp is None:
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')


def process_docstring_for_markdown(docstring: str) -> Optional[str]:
    """
    将文档字符串转换为纯Markdown格式
    
    :param docstring: 原始文档字符串
    :return: Markdown格式的文档字符串或None（如果包含忽略标签）
    """
    if not docstring:
        return None
    
    # 检查忽略标签
    if "{!--< ignore >!--}" in docstring:
        return None
    
    lines = docstring.split('\n')
    result = []
    in_code_block = False
    in_tip_block = False
    tip_content = []
    
    for line in lines:
        # 处理代码块
        if '```' in line:
            in_code_block = not in_code_block
            result.append(line)
            continue
        
        if in_code_block:
            result.append(line)
            continue
        
        # 处理提示块（多行）
        if "{!--< tips >!--}" in line:
            in_tip_block = True
            tip_content = [line.split("{!--< tips >!--}")[-1].strip()]
            continue
        
        if "{!--< /tips >!--}" in line:
            in_tip_block = False
            before_end = line.split("{!--< /tips >!--}")[0].strip()
            if before_end:
                tip_content.append(before_end)
            
            if tip_content:
                result.append("> **提示**")
                for tip_line in tip_content:
                    if tip_line:
                        result.append(f"> {tip_line}")
                result.append("")
            tip_content = []
            continue
        
        if in_tip_block:
            tip_content.append(line.strip())
            continue
        
        # 处理单行提示标签
        if "{!--< tips >!--}" in line:
            content = line.split("{!--< tips >!--}")[-1].strip()
            result.append(f"> **提示**: {content}")
            continue
        
        # 处理内部使用标签
        if "{!--< internal-use >!--}" in line:
            content = line.split("{!--< internal-use >!--}")[-1].strip()
            result.append(f"> **内部方法** {content}")
            continue
        
        # 处理过时标签
        if "{!--< deprecated >!--}" in line:
            content = line.split("{!--< deprecated >!--}")[-1].strip()
            result.append(f"> **已弃用** {content}")
            continue
        
        # 处理实验性功能标签
        if "{!--< experimental >!--}" in line:
            content = line.split("{!--< experimental >!--}")[-1].strip()
            result.append(f"> **实验性功能** {content}")
            continue
        
        # 跳过处理过的标签行
        if "{!--<" in line and ">!--}" in line:
            continue
        
        result.append(line)
    
    # 处理参数说明
    processed = "\n".join(result)
    
    # 转换 :param 格式
    processed = re.sub(
        r":param (\w+):\s*\[([^\]]+)\]\s*(.*)",
        r"- **\1** (`\2`): \3",
        processed
    )
    
    # 转换 :return 格式（单行）
    processed = re.sub(
        r":return:\s*\[([^\]]+)\]\s*(.*)",
        r"**返回值** (`\1`): \2",
        processed
    )
    
    # 转换 :raises 格式
    processed = re.sub(
        r":raises (\w+):\s*(.*)",
        r"**异常**: `\1` - \2",
        processed
    )
    
    # 转换 :example 格式（支持多行，以 >>> 开头的行）
    example_pattern = r":example:\s*\n((?:>>>.*(?:\n|$))+)"
    processed = re.sub(
        example_pattern,
        lambda m: f"\n**示例**:\n```python\n{m.group(1).strip()}\n```\n",
        processed,
        flags=re.DOTALL
    )
    
    # 清理多余的空行
    processed = re.sub(r"\n{3,}", "\n\n", processed.strip())
    
    return processed


def parse_python_file(file_path: str) -> Tuple[Optional[str], List[Dict], List[Dict]]:
    """
    解析Python文件，提取模块文档、类和函数信息
    
    :param file_path: Python文件路径
    :return: (模块文档, 类列表, 函数列表)
    """
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()
    
    try:
        module = ast.parse(source)
    except SyntaxError:
        print(f"语法错误，跳过文件: {file_path}")
        return None, [], []
    
    # 提取模块文档
    module_doc = ast.get_docstring(module)
    
    classes = []
    functions = []
    
    # 遍历AST节点
    for node in module.body:
        # 处理类定义
        if isinstance(node, ast.ClassDef):
            class_doc = ast.get_docstring(node)
            
            methods = []
            # 提取类方法
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    method_doc = ast.get_docstring(item)
                    
                    if method_doc:  # 只有方法有文档才添加
                        # 获取函数签名
                        args = []
                        defaults = dict(zip(
                            [arg.arg for arg in item.args.args][-len(item.args.defaults):],
                            item.args.defaults
                        )) if item.args.defaults else {}
                        
                        for arg in item.args.args:
                            if arg.arg == "self" or arg.arg == "cls":
                                continue
                            arg_str = arg.arg
                            if arg.annotation:
                                arg_str += f": {ast.unparse(arg.annotation)}"
                            if arg.arg in defaults:
                                default_val = ast.unparse(defaults[arg.arg])
                                arg_str += f" = {default_val}"
                            args.append(arg_str)
                        
                        signature = f"{item.name}({', '.join(args)})"
                        if isinstance(item, ast.AsyncFunctionDef):
                            signature = f"async {signature}"
                        
                        methods.append({
                            "name": item.name,
                            "signature": signature,
                            "doc": method_doc,
                            "is_async": isinstance(item, ast.AsyncFunctionDef)
                        })
            
            # 获取类签名
            bases = [ast.unparse(base) for base in node.bases] if node.bases else []
            class_signature = f"class {node.name}({', '.join(bases)})" if bases else f"class {node.name}"
            
            # 只有类有文档或者有方法时才添加类
            if class_doc or methods:
                classes.append({
                    "name": node.name,
                    "signature": class_signature,
                    "doc": class_doc,
                    "methods": methods
                })
        
        # 处理函数定义
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_doc = ast.get_docstring(node)
            
            if func_doc:
                # 获取函数签名
                args = []
                defaults = dict(zip(
                    [arg.arg for arg in node.args.args][-len(node.args.defaults):],
                    node.args.defaults
                )) if node.args.defaults else {}
                
                for arg in node.args.args:
                    arg_str = arg.arg
                    if arg.annotation:
                        arg_str += f": {ast.unparse(arg.annotation)}"
                    if arg.arg in defaults:
                        default_val = ast.unparse(defaults[arg.arg])
                        arg_str += f" = {default_val}"
                    args.append(arg_str)
                
                signature = f"{node.name}({', '.join(args)})"
                if isinstance(node, ast.AsyncFunctionDef):
                    signature = f"async {signature}"
                
                functions.append({
                    "name": node.name,
                    "signature": signature,
                    "doc": func_doc,
                    "is_async": isinstance(node, ast.AsyncFunctionDef)
                })
    
    return module_doc, classes, functions


def generate_markdown(module_path: str, module_doc: Optional[str], 
                     classes: List[Dict], functions: List[Dict]) -> str:
    """
    生成Markdown格式API文档
    
    :param module_path: 模块路径（点分隔）
    :param module_doc: 模块文档
    :param classes: 类信息列表
    :param functions: 函数信息列表
    :return: Markdown格式的文档字符串
    """
    content = []
    
    # 处理模块文档
    processed_module_doc = process_docstring_for_markdown(module_doc) if module_doc else None
    
    # 文档头部
    content.append(f"""# `{module_path}` 模块

> 最后更新：{format_timestamp()}

---

## 模块概述

""")
    
    # 模块文档
    if processed_module_doc:
        content.append(f"{processed_module_doc}\n\n---\n")
    else:
        content.append("该模块暂无概述信息。\n\n---\n")
    
    # 函数部分
    if functions:
        content.append("## 函数列表\n\n")
        for func in functions:
            async_marker = "async " if func["is_async"] else ""
            processed_doc = process_docstring_for_markdown(func["doc"])
            
            content.append(f"""### `{async_marker}{func['signature']}`

{processed_doc}

---

""")
    
    # 类部分
    if classes:
        content.append("## 类列表\n\n")
        for cls in classes:
            processed_class_doc = process_docstring_for_markdown(cls["doc"]) if cls["doc"] else None
            class_doc = processed_class_doc if processed_class_doc else f"{cls['name']} 类提供相关功能。"
            
            content.append(f"""### `{cls['signature']}`

{class_doc}

""")
            
            # 类方法
            if cls["methods"]:
                content.append("#### 方法列表\n\n")
                for method in cls["methods"]:
                    async_marker = "async " if method["is_async"] else ""
                    processed_doc = process_docstring_for_markdown(method["doc"])
                    
                    content.append(f"""##### `{async_marker}{method['signature']}`

{processed_doc}

---

""")
    
    return "\n".join(content)


def generate_index_markdown(modules_info: Dict[str, Dict]) -> str:
    """
    生成API文档索引页
    
    :param modules_info: 模块信息字典
    :return: Markdown格式的索引文档字符串
    """
    content = []
    
    # 统计信息（包括类的方法）
    total_modules = len(modules_info)
    total_classes = sum(len(info.get('classes', [])) for info in modules_info.values())
    total_functions = sum(len(info.get('functions', [])) for info in modules_info.values())
    # 统计所有类的方法
    total_methods = sum(sum(len(cls.get('methods', [])) for cls in info.get('classes', [])) for info in modules_info.values())
    
    content.append(f"""# ErisPulse API 文档

> 最后更新：{format_timestamp()}

---

## 概述

本文档包含 ErisPulse SDK 的所有 API 参考文档。

- **模块总数**: {total_modules}
- **类总数**: {total_classes}
- **函数总数**: {total_functions}
- **方法总数**: {total_methods}

---

## 模块列表

""")
    
    # 按模块路径排序
    sorted_modules = sorted(modules_info.keys())
    
    for module_path in sorted_modules:
        info = modules_info[module_path]
        classes = info.get('classes', [])
        functions = info.get('functions', [])
        
        # 计算类的方法总数
        methods_count = sum(len(cls.get('methods', [])) for cls in classes)
        
        # 计算相对路径
        md_path = module_path.replace('.', '/') + '.md'
        
        # 统计标识
        badges = []
        if classes:
            badges.append(f"📦 {len(classes)} 个类")
        if methods_count > 0:
            badges.append(f"🔧 {methods_count} 个方法")
        if functions:
            badges.append(f"⚙️ {len(functions)} 个函数")
        badge_str = ' | '.join(badges) if badges else "📄 模块文档"
        
        content.append(f"""### [{module_path}]({md_path})

{badge_str}

""")
    
    return "\n".join(content)


def generate_api_docs(src_dir: str, output_dir: str) -> Dict[str, Dict]:
    """
    生成API文档
    
    :param src_dir: 源代码目录
    :param output_dir: Markdown输出目录
    :return: 模块信息字典
    """
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    modules_info = {}
    
    # 遍历源代码目录
    for root, _, files in os.walk(src_dir):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                
                # 计算模块路径
                rel_path = os.path.relpath(file_path, src_dir)
                module_path = rel_path.replace(".py", "").replace(os.sep, ".")
                
                # 解析Python文件
                module_doc, classes, functions = parse_python_file(file_path)
                
                # 跳过没有文档的文件
                if not module_doc and not classes and not functions:
                    continue
                
                # 保存模块信息
                modules_info[module_path] = {
                    "classes": classes,
                    "functions": functions
                }
                
                # 生成Markdown（使用增量更新）
                md_content = generate_markdown(module_path, module_doc, classes, functions)
                md_output_path = os.path.join(output_dir, f"{module_path.replace('.', '/')}.md")
                os.makedirs(os.path.dirname(md_output_path), exist_ok=True)
                
                if should_update_file(md_output_path, md_content):
                    with open(md_output_path, "w", encoding="utf-8") as f:
                        f.write(md_content)
                    print(f"已生成Markdown: {md_output_path}")
                else:
                    print(f"Markdown未变化，跳过: {md_output_path}")
    
    # 生成索引页
    if modules_info:
        index_content = generate_index_markdown(modules_info)
        index_path = os.path.join(output_dir, "README.md")
        
        if should_update_file(index_path, index_content):
            with open(index_path, "w", encoding="utf-8") as f:
                f.write(index_content)
            print(f"已生成索引: {index_path}")
        else:
            print(f"索引未变化，跳过: {index_path}")
    
    return modules_info


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="ErisPulse API文档生成器 v9.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用默认设置
  python .github/tools/update-api-docs.py
  
  # 自定义源目录和输出目录
  python .github/tools/update-api-docs.py --src src --output docs/api
        """
    )
    
    parser.add_argument("--src", default="src", help="源代码目录 (默认: src)")
    parser.add_argument("--output", default="docs/api", help="Markdown输出目录 (默认: docs/api)")
    parser.add_argument("--version", action="version", version="API文档生成器 v9.0")
    
    args = parser.parse_args()
    
    print(f"""╔══════════════════════════════════════════╗
║   ErisPulse API 文档生成器 v9.0      ║
╚══════════════════════════════════════════╝

源代码目录: {args.src}
输出目录: {args.output}

正在生成API文档...
""")
    
    modules_info = generate_api_docs(args.src, args.output)
    
    total_modules = len(modules_info)
    total_classes = sum(len(info.get('classes', [])) for info in modules_info.values())
    total_functions = sum(len(info.get('functions', [])) for info in modules_info.values())
    total_methods = sum(sum(len(cls.get('methods', [])) for cls in info.get('classes', [])) for info in modules_info.values())
    
    print("\n" + "="*50)
    print(f"API文档生成完成！")
    print(f"  模块总数: {total_modules}")
    print(f"  类总数: {total_classes}")
    print(f"  方法总数: {total_methods}")
    print(f"  函数总数: {total_functions}")
    print("="*50)
