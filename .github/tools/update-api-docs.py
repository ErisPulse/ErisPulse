import os
import ast
import re
import argparse
from typing import List, Dict, Tuple, Optional
from datetime import datetime

def process_docstring(docstring: str) -> Optional[str]:
    """
    处理文档字符串中的特殊标签
    
    :param docstring: 原始文档字符串
    :return: 处理后的文档字符串或None（如果包含忽略标签）
    """
    if not docstring:
        return None
    
    # 检查忽略标签
    if "{!--< ignore >!--}" in docstring:
        return None
    
    # 替换 {!--< internal-use >!--} 
    docstring = re.sub(
        r"{!--< internal-use >!--}(.*)",
        lambda m: f"<div class='admonition warning'><p class='admonition-title'>内部方法</p><p>{m.group(1).strip()}</p></div>",
        docstring
    )

    # 替换过时标签
    docstring = re.sub(
        r"\{!--< deprecated >!--\}(.*)",
        lambda m: f"<div class='admonition attention'><p class='admonition-title'>已弃用</p><p>{m.group(1).strip()}</p></div>",
        docstring
    )
    
    # 替换实验性标签
    docstring = re.sub(
        r"\{!--< experimental >!--\}(.*)",
        lambda m: f"<div class='admonition tip'><p class='admonition-title'>实验性功能</p><p>{m.group(1).strip()}</p></div>",
        docstring
    )
    
    # 处理提示标签（多行）
    docstring = re.sub(
        r"\{!--< tips >!--\}(.*?)\{!--< /tips >!--\}",
        lambda m: f"<div class='admonition tip'><p class='admonition-title'>提示</p><p>{m.group(1).strip()}</p></div>",
        docstring,
        flags=re.DOTALL
    )
    
    # 处理单行提示标签
    docstring = re.sub(
        r"\{!--< tips >!--\}([^\n]*)",
        lambda m: f"<div class='admonition tip'><p class='admonition-title'>提示</p><p>{m.group(1).strip()}</p></div>",
        docstring
    )
    
    # 参数说明
    docstring = re.sub(
        r":param (\w+):\s*\[([^\]]+)\]\s*(.*)",
        lambda m: f"<dt><code>{m.group(1)}</code> <span class='type-hint'>{m.group(2)}</span></dt><dd>{m.group(3).strip()}</dd>",
        docstring
    )
    
    # 返回值说明
    docstring = re.sub(
        r":return:\s*\[([^\]]+)\]\s*(.*)",
        lambda m: f"<dt>返回值</dt><dd><span class='type-hint'>{m.group(1)}</span> {m.group(2).strip()}</dd>",
        docstring
    )
    
    # 异常说明
    docstring = re.sub(
        r":raises (\w+):\s*(.*)",
        lambda m: f"<dt>异常</dt><dd><code>{m.group(1)}</code> {m.group(2).strip()}</dd>",
        docstring
    )
    
    # 示例代码
    docstring = re.sub(
        r":example:\s*(.*?)(?=\n\w|\Z)",
        lambda m: f"<details class='example'><summary>示例</summary>\n\n```python\n{m.group(1).strip()}\n```\n</details>",
        docstring,
        flags=re.DOTALL
    )
    
    # 统一换行符为两个换行
    docstring = re.sub(r"\n{2,}", "\n\n", docstring.strip())
    
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
        print(f"语法错误，跳过文件: {file_path}")
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
            processed_class_doc = process_docstring(class_doc) if class_doc else ""
            
            # 不管类有没有文档，都要处理其中的方法
            methods = []
            # 提取类方法
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    method_doc = ast.get_docstring(item)
                    processed_method_doc = process_docstring(method_doc) if method_doc else None
                    
                    if processed_method_doc:  # 只有方法有文档才添加
                        # 获取函数签名
                        args = []
                        defaults = dict(zip([arg.arg for arg in item.args.args][-len(item.args.defaults):], item.args.defaults)) if item.args.defaults else {}
                        for arg in item.args.args:
                            if arg.arg == "self":
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
                            "doc": processed_method_doc,
                            "is_async": isinstance(item, ast.AsyncFunctionDef)
                        })
            
            # 获取类签名
            bases = [ast.unparse(base) for base in node.bases] if node.bases else []
            class_signature = f"class {node.name}({', '.join(bases)})" if bases else f"class {node.name}"
            
            # 只有类有文档或者有方法时才添加类
            if processed_class_doc or methods:
                classes.append({
                    "name": node.name,
                    "signature": class_signature,
                    "doc": processed_class_doc,
                    "methods": methods
                })
        
        # 处理函数定义
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_doc = ast.get_docstring(node)
            processed_func_doc = process_docstring(func_doc) if func_doc else None
            
            if processed_func_doc:
                # 获取函数签名
                args = []
                defaults = dict(zip([arg.arg for arg in node.args.args][-len(node.args.defaults):], node.args.defaults)) if node.args.defaults else {}
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
                    "doc": processed_func_doc,
                    "is_async": isinstance(node, ast.AsyncFunctionDef)
                })
    
    return processed_module_doc, classes, functions

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
    
    # 文档头部
    content.append(f"""# `{module_path}` 模块

<sup>更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</sup>

---

## 模块概述

""")
    
    # 模块文档
    if module_doc:
        content.append(f"{module_doc}\n\n---\n")
    else:
        content.append("该模块暂无概述信息。\n\n---\n")
    
    # 函数部分
    if functions:
        content.append("## 函数列表\n")
        for func in functions:
            async_marker = "async " if func["is_async"] else ""
            content.append(f"""### {async_marker}`{func['signature']}`

{func['doc']}

---
""")
    
    # 类部分
    if classes:
        content.append("## 类列表\n")
        for cls in classes:
            # 如果类没有文档，显示默认信息
            class_doc = cls['doc'] if cls['doc'] else f"{cls['name']} 类提供相关功能。"
            content.append(f"""### `{cls['signature']}`

    {class_doc}

    """)
            
            # 类方法
            if cls["methods"]:
                content.append("#### 方法列表\n")
                for method in cls["methods"]:
                    async_marker = "async " if method["is_async"] else ""
                    content.append(f"""##### {async_marker}`{method['signature']}`

    {method['doc']}

    ---
    """)
    
    # 文档尾部
    content.append(f"<sub>文档最后更新于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</sub>")
    
    return "\n".join(content)

def generate_html(module_path: str, module_doc: Optional[str], 
                  classes: List[Dict], functions: List[Dict]) -> str:
    """
    生成HTML格式API文档
    
    :param module_path: 模块路径（点分隔）
    :param module_doc: 模块文档
    :param classes: 类信息列表
    :param functions: 函数信息列表
    :return: HTML格式的文档字符串
    """
    # 处理模块文档中的参数列表
    if module_doc:
        module_doc = re.sub(
            r"(:param .+?:.+?)(?=:param|\Z)",
            r"<dl>\1</dl>",
            module_doc + "\n",
            flags=re.DOTALL
        )
        module_doc = re.sub(
            r"<dl>(.*?)</dl>", 
            lambda m: f"<dl class='params'>{m.group(1)}</dl>",
            module_doc,
            flags=re.DOTALL
        )

    html_content = [f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{module_path} - ErisPulse API 文档</title>
    <style>
        :root {{
            --primary-color: #3498db;
            --secondary-color: #2c3e50;
            --background-color: #f8f9fa;
            --code-background: #f1f1f1;
            --border-color: #e1e1e1;
            --text-color: #333;
            --heading-color: #2c3e50;
            --warning-color: #f39c12;
            --danger-color: #e74c3c;
            --success-color: #27ae60;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: var(--text-color);
            background-color: var(--background-color);
            margin: 0;
            padding: 0;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}

        header {{
            background-color: white;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            padding: 20px 0;
            margin-bottom: 30px;
        }}

        h1, h2, h3, h4, h5, h6 {{
            color: var(--heading-color);
        }}

        h1 {{
            border-bottom: 2px solid var(--primary-color);
            padding-bottom: 10px;
        }}

        h2 {{
            border-left: 4px solid var(--primary-color);
            padding-left: 10px;
        }}

        a {{
            color: var(--primary-color);
            text-decoration: none;
        }}

        a:hover {{
            text-decoration: underline;
        }}

        code {{
            background-color: var(--code-background);
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'Consolas', 'Courier New', monospace;
        }}

        pre {{
            background-color: var(--code-background);
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }}

        pre code {{
            background-color: transparent;
            padding: 0;
        }}

        .admonition {{
            margin: 20px 0;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid;
        }}

        .admonition.warning {{
            background-color: #fff3cd;
            border-color: var(--warning-color);
        }}

        .admonition.attention {{
            background-color: #f8d7da;
            border-color: var(--danger-color);
        }}

        .admonition.tip {{
            background-color: #d1ecf1;
            border-color: var(--success-color);
        }}

        .admonition-title {{
            font-weight: bold;
            margin-bottom: 5px;
        }}

        .example {{
            margin: 15px 0;
        }}

        .example summary {{
            cursor: pointer;
            padding: 10px;
            background-color: var(--code-background);
            border-radius: 5px;
        }}

        dl.params {{
            display: grid;
            grid-template-columns: auto 1fr;
            gap: 10px;
            margin: 15px 0;
        }}

        dt {{
            font-weight: bold;
            text-align: right;
        }}

        dd {{
            margin-inline-start: 0;
        }}

        .type-hint {{
            font-size: 0.9em;
            color: #6c757d;
            font-style: italic;
        }}

        .signature {{
            background-color: var(--code-background);
            padding: 10px 15px;
            border-radius: 5px;
            font-family: 'Consolas', 'Courier New', monospace;
            margin: 10px 0;
            overflow-x: auto;
        }}

        .function-signature, .class-signature {{
            border-left: 3px solid var(--primary-color);
        }}

        .method-signature {{
            border-left: 3px solid #95a5a6;
        }}

        footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid var(--border-color);
            text-align: center;
            color: #6c757d;
            font-size: 0.9em;
        }}

        @media (max-width: 768px) {{
            .container {{
                padding: 10px;
            }}
            
            dl.params {{
                grid-template-columns: 1fr;
            }}
            
            dt {{
                text-align: left;
            }}
        }}
    </style>
</head>
<body>
    <header>
        <div class="container">
            <h1>`{module_path}` 模块</h1>
            <p><small>更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small></p>
        </div>
    </header>
    
    <div class="container">
        <section>
            <h2>模块概述</h2>
"""]
    
    # 模块文档
    if module_doc:
        html_content.append(f"<div>{module_doc}</div>\n")
    else:
        html_content.append("<p>该模块暂无概述信息。</p>\n")
    
    # 函数部分
    if functions:
        html_content.append("</section>\n\n<section>\n<h2>函数列表</h2>\n")
        for func in functions:
            async_marker = "async " if func["is_async"] else ""
            html_content.append(f"""<article>
    <h3><code class="signature function-signature">{async_marker}{func['signature']}</code></h3>
    <div>{func['doc']}</div>
</article>
""")
    
    # 类部分
    if classes:
        html_content.append("</section>\n\n<section>\n<h2>类列表</h2>\n")
        for cls in classes:
            html_content.append(f"""<article>
    <h3><code class="signature class-signature">{cls['signature']}</code></h3>
    <div>{cls['doc']}</div>
""")
            
            # 类方法
            if cls["methods"]:
                html_content.append("<h4>方法列表</h4>\n")
                for method in cls["methods"]:
                    async_marker = "async " if method["is_async"] else ""
                    html_content.append(f"""<article>
        <h5><code class="signature method-signature">{async_marker}{method['signature']}</code></h5>
        <div>{method['doc']}</div>
    </article>
""")
            html_content.append("</article>\n")
    
    # 文档尾部
    html_content.append(f"""</section>
    </div>
    
    <footer>
        <div class="container">
            <p>文档最后更新于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </footer>
</body>
</html>""")

    return "\n".join(html_content)

def generate_api_docs(src_dir: str, output_dir: str, format: str = "markdown"):
    """
    生成API文档
    
    :param src_dir: 源代码目录
    :param output_dir: 输出目录
    :param format: 输出格式 ("markdown" 或 "html")
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
                module_path = rel_path.replace(".py", "").replace(os.sep, ".")
                
                # 解析Python文件
                module_doc, classes, functions = parse_python_file(file_path)
                
                # 跳过没有文档的文件
                if not module_doc and not classes and not functions:
                    print(f"跳过无文档文件: {file_path}")
                    continue
                
                # 生成内容
                if format == "html":
                    content = generate_html(module_path, module_doc, classes, functions)
                    ext = ".html"
                else:
                    content = generate_markdown(module_path, module_doc, classes, functions)
                    ext = ".md"
                
                # 写入文件
                output_path = os.path.join(output_dir, f"{module_path.replace('.', '/')}{ext}")
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(content)
                
                print(f"已生成: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="API文档生成器")
    parser.add_argument("--src", default="src", help="源代码目录 (默认: src)")
    parser.add_argument("--output", default="docs/api", help="输出目录 (默认: docs/api)")
    parser.add_argument("--format", choices=["markdown", "html"], default="markdown", help="输出格式 (默认: markdown)")
    parser.add_argument("--version", action="version", version="API文档生成器 3.0")
    
    args = parser.parse_args()
    
    print(f"""源代码目录: {args.src}
输出目录: {args.output}
输出格式: {args.format}
正在生成API文档...""")
    
    generate_api_docs(args.src, args.output, args.format)
    
    print("API文档生成完成！")