import os
import ast
import re
import argparse
from typing import List, Dict, Tuple, Optional, Set

def process_docstring(docstring: str) -> Optional[str]:
    """
    处理文档字符串中的特殊标签
    
    :param docstring: 原始文档字符串
    :return: 处理后的文档字符串或None（如果包含忽略标签）
    """
    if not docstring:
        return None
    
    # 检查忽略标签
    if "{!--< internal-use >!--}" in docstring or "{!--< ignore >!--}" in docstring:
        return None
    
    # 替换过时标签
    docstring = docstring.replace("{!--< deprecated >!--}", "**过时**：")
    
    # 替换实验性标签
    docstring = docstring.replace("{!--< experimental >!--}", "**实验性**：")
    
    # 处理提示标签（单行）
    docstring = re.sub(
        r"\{!--< tips >!--\}(.*?)\{!--< /tips >!--\}",
        lambda m: f"> **提示**：{m.group(1)}\n\n",
        docstring,
        flags=re.DOTALL
    )
    
    # 处理单行提示标签（没有结束标签）
    docstring = re.sub(
        r"\{!--< tips >!--\}([^\n]*)",
        lambda m: f"> **提示**：{m.group(1)}\n\n",
        docstring
    )
    
    return docstring.strip()

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
        print(f"⚠️ 语法错误，跳过文件: {file_path}")
        return None, [], []
    
    # 提取模块文档
    module_doc = ast.get_docstring(module)
    processed_module_doc = process_docstring(module_doc) if module_doc else None
    
    classes = []
    functions = []
    
    # 遍历AST节点
    for node in module.body:
        # 处理类定义
        if isinstance(node, ast.ClassDef):
            class_doc = ast.get_docstring(node)
            processed_class_doc = process_docstring(class_doc) if class_doc else None
            
            if processed_class_doc is None:
                continue
                
            methods = []
            # 提取类方法
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    method_doc = ast.get_docstring(item)
                    processed_method_doc = process_docstring(method_doc) if method_doc else None
                    
                    if processed_method_doc:
                        methods.append({
                            "name": item.name,
                            "doc": processed_method_doc
                        })
            
            classes.append({
                "name": node.name,
                "doc": processed_class_doc,
                "methods": methods
            })
        
        # 处理函数定义
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_doc = ast.get_docstring(node)
            processed_func_doc = process_docstring(func_doc) if func_doc else None
            
            if processed_func_doc:
                functions.append({
                    "name": node.name,
                    "doc": processed_func_doc
                })
    
    return processed_module_doc, classes, functions

def generate_markdown(module_path: str, module_doc: Optional[str], 
                     classes: List[Dict], functions: List[Dict]) -> str:
    """
    生成Markdown格式的API文档
    
    :param module_path: 模块路径（点分隔）
    :param module_doc: 模块文档
    :param classes: 类信息列表
    :param functions: 函数信息列表
    :return: Markdown格式的文档字符串
    """
    content = []
    
    # 模块标题
    content.append(f"# `{module_path}` 模块\n")
    
    # 模块文档
    if module_doc:
        content.append(f"{module_doc}\n")
    
    # 函数部分
    if functions:
        content.append("## 函数\n")
        for func in functions:
            content.append(f"### `{func['name']}`\n")
            content.append(f"{func['doc']}\n\n")
    
    # 类部分
    if classes:
        content.append("## 类\n")
        for cls in classes:
            content.append(f"### `{cls['name']}`\n")
            content.append(f"{cls['doc']}\n\n")
            
            # 类方法
            if cls["methods"]:
                content.append("#### 方法\n")
                for method in cls["methods"]:
                    content.append(f"##### `{method['name']}`\n")
                    content.append(f"{method['doc']}\n\n")
    
    return "\n".join(content)

def generate_api_docs(src_dir: str, output_dir: str):
    """
    生成API文档
    
    :param src_dir: 源代码目录
    :param output_dir: 输出目录
    """
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 遍历源代码目录
    for root, _, files in os.walk(src_dir):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                
                # 计算模块路径
                rel_path = os.path.relpath(file_path, src_dir)
                module_path = rel_path.replace(".py", "").replace(os.sep, "/")
                
                # 解析Python文件
                module_doc, classes, functions = parse_python_file(file_path)
                
                # 跳过没有文档的文件
                if not module_doc and not classes and not functions:
                    continue
                
                # 生成Markdown内容
                md_content = generate_markdown(module_path, module_doc, classes, functions)
                
                # 写入文件
                output_path = os.path.join(output_dir, f"{module_path}.md")
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(md_content)
                
                print(f"✅ 已生成: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="API文档生成器")
    parser.add_argument("--src", default="src", help="源代码目录 (默认: src)")
    parser.add_argument("--output", default="docs/api", help="输出目录 (默认: docs/api)")
    
    args = parser.parse_args()
    
    print(f"📁 源代码目录: {args.src}")
    print(f"📂 输出目录: {args.output}")
    print("⏳ 正在生成API文档...")
    
    generate_api_docs(args.src, args.output)
    
    print("🎉 API文档生成完成！")
