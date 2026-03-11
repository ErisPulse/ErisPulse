"""
ErisPulse API 文档生成器

从Python源代码自动生成API文档
"""

import os
import ast
import re
import argparse
from typing import List, Dict, Tuple, Optional


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


def extract_class_info(class_node: ast.ClassDef, is_nested: bool = False) -> Dict:
    """
    提取类的信息，包括嵌套类
    
    :param class_node: AST类节点
    :param is_nested: 是否为嵌套类
    :return: 类信息字典
    """
    class_doc = ast.get_docstring(class_node)
    
    methods = []
    nested_classes = []
    
    # 提取类方法和嵌套类
    for item in class_node.body:
        # 提取方法
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
        
        # 递归提取嵌套类
        elif isinstance(item, ast.ClassDef):
            nested_class_info = extract_class_info(item, is_nested=True)
            # 只添加有文档或方法/嵌套类的嵌套类
            if nested_class_info["doc"] or nested_class_info["methods"] or nested_class_info.get("nested_classes"):
                nested_classes.append(nested_class_info)
    
    # 获取类签名
    bases = [ast.unparse(base) for base in class_node.bases] if class_node.bases else []
    class_signature = f"class {class_node.name}({', '.join(bases)})" if bases else f"class {class_node.name}"
    
    return {
        "name": class_node.name,
        "signature": class_signature,
        "doc": class_doc,
        "methods": methods,
        "nested_classes": nested_classes,
        "is_nested": is_nested
    }


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
            class_info = extract_class_info(node, is_nested=False)
            
            # 只有类有文档或者有方法或嵌套类时才添加类
            if class_info["doc"] or class_info["methods"] or class_info.get("nested_classes"):
                classes.append(class_info)
        
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


def generate_class_markdown(cls: Dict, base_heading_level: int = 3) -> str:
    """
    生成类的Markdown文档，包括嵌套类
    
    :param cls: 类信息字典
    :param base_heading_level: 基础标题级别
    :return: Markdown格式的类文档字符串
    """
    content = []
    
    # 处理类文档
    processed_class_doc = process_docstring_for_markdown(cls["doc"]) if cls["doc"] else None
    class_doc = processed_class_doc if processed_class_doc else f"{cls['name']} 类提供相关功能。"
    
    # 类标题
    heading_prefix = "#" * base_heading_level
    content.append(f"""{heading_prefix} `{cls['signature']}`

{class_doc}

""")
    
    # 嵌套类（在方法之前显示）
    if cls.get("nested_classes"):
        nested_heading_level = base_heading_level + 1
        nested_heading_prefix = "#" * nested_heading_level
        content.append(f"{nested_heading_prefix} 嵌套类\n\n")
        
        for nested_cls in cls["nested_classes"]:
            # 递归生成嵌套类文档
            nested_content = generate_class_markdown(nested_cls, nested_heading_level + 1)
            content.append(nested_content)
    
    # 类方法
    if cls["methods"]:
        methods_heading_level = base_heading_level + 1
        methods_heading_prefix = "#" * methods_heading_level
        content.append(f"{methods_heading_prefix} 方法列表\n\n")
        
        for method in cls["methods"]:
            async_marker = "async " if method["is_async"] else ""
            processed_doc = process_docstring_for_markdown(method["doc"])
            
            method_heading_level = methods_heading_level + 1
            method_heading_prefix = "#" * method_heading_level
            content.append(f"""{method_heading_prefix} `{async_marker}{method['signature']}`

{processed_doc}

---

""")
    
    return "\n".join(content)


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
            # 使用辅助函数生成类文档（包括嵌套类）
            class_content = generate_class_markdown(cls, base_heading_level=3)
            content.append(class_content)
    
    return "\n".join(content)


def count_nested_classes(classes: List[Dict]) -> int:
    """
    递归统计嵌套类数量
    
    :param classes: 类列表
    :return: 嵌套类总数
    """
    count = 0
    for cls in classes:
        nested_classes = cls.get('nested_classes', [])
        if nested_classes:
            count += len(nested_classes)
            # 递归统计更深层的嵌套类
            count += count_nested_classes(nested_classes)
    return count


def count_all_methods(classes: List[Dict]) -> int:
    """
    递归统计所有类的方法数量（包括嵌套类）
    
    :param classes: 类列表
    :return: 方法总数
    """
    count = 0
    for cls in classes:
        count += len(cls.get('methods', []))
        # 递归统计嵌套类的方法
        nested_classes = cls.get('nested_classes', [])
        if nested_classes:
            count += count_all_methods(nested_classes)
    return count


def generate_index_markdown(modules_info: Dict[str, Dict]) -> str:
    """
    生成API文档索引页
    
    :param modules_info: 模块信息字典
    :return: Markdown格式的索引文档字符串
    """
    content = []
    
    # 统计信息（包括类的方法和嵌套类）
    total_modules = len(modules_info)
    total_classes = sum(len(info.get('classes', [])) for info in modules_info.values())
    total_functions = sum(len(info.get('functions', [])) for info in modules_info.values())
    # 统计所有类的方法（包括嵌套类）
    total_methods = sum(count_all_methods(info.get('classes', [])) for info in modules_info.values())
    # 统计所有嵌套类
    total_nested_classes = sum(count_nested_classes(info.get('classes', [])) for info in modules_info.values())
    
    content.append(f"""# ErisPulse API 文档

---

## 概述

本文档包含 ErisPulse SDK 的所有 API 参考文档。

> **⚠️ 重要说明**
> 本目录下的所有文档均为**自动生成**的 API 参考文档。
> 
> **请不要手动编辑此目录下的任何文件**，所有更改将在下次自动生成时被覆盖。
> 
> 如需修改 API 文档，请在源代码中更新对应模块、类和函数的 docstring。
> 
> 自动生成脚本位置：`scripts/tools/update-api-docs.py`

---

## 统计信息

- **模块总数**: {total_modules}
- **类总数**: {total_classes}（包括 {total_nested_classes} 个嵌套类）
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
                
                # 生成Markdown
                md_content = generate_markdown(module_path, module_doc, classes, functions)
                md_output_path = os.path.join(output_dir, f"{module_path.replace('.', '/')}.md")
                os.makedirs(os.path.dirname(md_output_path), exist_ok=True)
                
                with open(md_output_path, "w", encoding="utf-8") as f:
                    f.write(md_content)
                print(f"已生成: {md_output_path}")
    
    # 生成索引页
    if modules_info:
        index_content = generate_index_markdown(modules_info)
        index_path = os.path.join(output_dir, "README.md")
        
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(index_content)
        print(f"已生成: {index_path}")
    
    return modules_info


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="ErisPulse API文档生成器 v10.0",
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
    parser.add_argument("--output", default="docs/api-reference/auto_api", help="Markdown输出目录 (默认: docs/api-reference/auto_api)")
    parser.add_argument("--version", action="version", version="API文档生成器 v10.0")
    
    args = parser.parse_args()
    
    print(f"""╔══════════════════════════════════════════╗
║   ErisPulse API 文档生成器 v10.0      ║
╚══════════════════════════════════════════╝

源代码目录: {args.src}
输出目录: {args.output}

正在生成API文档...
""")
    
    modules_info = generate_api_docs(args.src, args.output)
    
    total_modules = len(modules_info)
    total_classes = sum(len(info.get('classes', [])) for info in modules_info.values())
    total_functions = sum(len(info.get('functions', [])) for info in modules_info.values())
    total_methods = sum(count_all_methods(info.get('classes', [])) for info in modules_info.values())
    total_nested_classes = sum(count_nested_classes(info.get('classes', [])) for info in modules_info.values())
    
    print("\n" + "="*50)
    print(f"API文档生成完成！")
    print(f"  模块总数: {total_modules}")
    print(f"  类总数: {total_classes}（包括 {total_nested_classes} 个嵌套类）")
    print(f"  方法总数: {total_methods}")
    print(f"  函数总数: {total_functions}")
    print("="*50)
