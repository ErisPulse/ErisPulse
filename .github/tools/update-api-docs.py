import re
import os
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import inspect

def extract_module_docs(file_path: Path) -> Optional[Tuple[str, Dict[str, str]]]:
    """
    提取模块文档字符串和元数据标签
    
    :param file_path: Python文件路径
    :return: (文档字符串, 标签字典) 或 None
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 匹配模块文档字符串
    match = re.search(r'^\"\"\"(.*?)\"\"\"', content, re.DOTALL)
    if not match:
        return None
    
    docstring = match.group(1).strip()
    tags = extract_tags(docstring)
    
    return docstring, tags

def extract_tags(docstring: str) -> Dict[str, str]:
    """
    从文档字符串中提取特殊标签
    
    :param docstring: 文档字符串
    :return: 标签字典 {tag_name: tag_content}
    """
    tags = {}
    
    # 匹配单行标签
    single_tags = re.findall(r'\{!--<\s*([a-z-]+)\s*>!--\}', docstring)
    for tag in single_tags:
        tags[tag] = True
    
    # 匹配多行标签
    multiline_tags = re.findall(
        r'\{!--<\s*([a-z-]+)\s*>!--\}(.*?)\{!--<\s*/\1\s*>!--\}',
        docstring, 
        re.DOTALL
    )
    for tag, content in multiline_tags:
        tags[tag] = content.strip()
    
    return tags

def extract_function_dunctions(file_path: Path) -> List[Dict]:
    """
    提取文件中的所有函数及其文档
    
    :param file_path: Python文件路径
    :return: 函数信息列表
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 匹配函数定义和文档字符串
    functions = []
    pattern = re.compile(
        r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*?)\)\s*(?:->\s*([^:\n]+))?\s*:\s*\"\"\"(.*?)\"\"\"',
        re.DOTALL
    )
    
    for match in pattern.finditer(content):
        func_name = match.group(1)
        params_str = match.group(2)
        return_type = match.group(3)
        docstring = match.group(4).strip()
        
        # 解析参数
        params = []
        for param in re.split(r',\s*(?![^()]*\))', params_str):
            if '=' in param:
                name, default = param.split('=', 1)
                default = default.strip()
            else:
                name = param
                default = None
            
            # 提取类型提示
            if ':' in name:
                param_name, param_type = name.split(':', 1)
                param_name = param_name.strip()
                param_type = param_type.strip()
            else:
                param_name = name.strip()
                param_type = None
            
            params.append({
                'name': param_name,
                'type': param_type,
                'default': default
            })
        
        # 提取文档标签
        tags = extract_tags(docstring)
        
        # 提取参数和返回描述
        param_docs = {}
        return_doc = None
        raises = []
        
        lines = docstring.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if line.startswith(':param'):
                # 参数文档
                parts = re.split(r':\s+', line[6:].strip(), maxsplit=2)
                if len(parts) >= 2:
                    param_name = parts[0]
                    param_docs[param_name] = parts[1] if len(parts) == 2 else parts[2]
            elif line.startswith(':return:'):
                # 返回文档
                return_doc = line[8:].strip()
            elif line.startswith(':raises'):
                # 异常文档
                parts = line[7:].strip().split(':', 1)
                if len(parts) == 2:
                    raises.append({
                        'type': parts[0].strip(),
                        'description': parts[1].strip()
                    })
        
        functions.append({
            'name': func_name,
            'params': params,
            'return_type': return_type,
            'docstring': docstring,
            'param_docs': param_docs,
            'return_doc': return_doc,
            'raises': raises,
            'tags': tags
        })
    
    return functions

def should_include_function(func_info: Dict) -> bool:
    """
    根据标签判断是否应包含此函数在文档中
    
    :param func_info: 函数信息字典
    :return: 是否包含
    """
    tags = func_info.get('tags', {})
    return not ('ignore' in tags or 'internal-use' in tags)

def format_function_docs(func_info: Dict) -> str:
    """
    格式化函数文档为Markdown
    
    :param func_info: 函数信息字典
    :return: Markdown格式的文档
    """
    tags = func_info.get('tags', {})
    
    # 处理过时方法
    if 'deprecated' in tags:
        deprecated_note = f"\n> ⚠️ **Deprecated**: {tags['deprecated']}\n"
    else:
        deprecated_note = ""
    
    # 处理实验性方法
    experimental_note = ""
    if 'experimental' in tags:
        experimental_note = "\n> 🔬 **Experimental**: This API is experimental and may change in future versions.\n"
    
    # 处理提示
    tips_note = ""
    if 'tips' in tags:
        tips_content = tags['tips']
        tips_note = f"\n> 💡 **Note**: {tips_content}\n"
    
    # 构建函数签名
    params_str = []
    for param in func_info['params']:
        param_str = param['name']
        if param['type']:
            param_str += f": {param['type']}"
        if param['default'] is not None:
            param_str += f" = {param['default']}"
        params_str.append(param_str)
    
    signature = f"{func_info['name']}({', '.join(params_str)})"
    if func_info['return_type']:
        signature += f" -> {func_info['return_type']}"
    
    # 构建参数文档
    params_doc = ""
    for param in func_info['params']:
        param_name = param['name']
        param_desc = func_info['param_docs'].get(param_name, "")
        
        param_line = f"- `{param_name}`"
        if param['type']:
            param_line += f" ({param['type']})"
        if param['default'] is not None:
            param_line += f" [optional, default: {param['default']}]"
        if param_desc:
            param_line += f": {param_desc}"
        
        params_doc += param_line + "\n"
    
    # 构建返回文档
    return_doc = ""
    if func_info['return_doc'] or func_info['return_type']:
        return_doc = "\n**Returns**\n\n"
        if func_info['return_type']:
            return_doc += f"- Type: `{func_info['return_type']}`\n"
        if func_info['return_doc']:
            return_doc += f"- Description: {func_info['return_doc']}\n"
    
    # 构建异常文档
    raises_doc = ""
    if func_info['raises']:
        raises_doc = "\n**Raises**\n\n"
        for exc in func_info['raises']:
            raises_doc += f"- `{exc['type']}`: {exc['description']}\n"
    
    # 组合所有部分
    docs = f"""### `{signature}`

{deprecated_note}{experimental_note}{tips_note}

**Description**  
{func_info['docstring'].split(':param')[0].strip()}

**Parameters**  
{params_doc.strip()}

{return_doc.strip()}

{raises_doc.strip()}
"""
    
    return docs.strip()

def generate_module_docs(module_path: Path, output_path: Path) -> None:
    """
    生成模块文档
    
    :param module_path: Python模块路径
    :param output_path: 输出文档路径
    """
    module_docs = extract_module_docs(module_path)
    functions = extract_function_dunctions(module_path)
    
    if not module_docs and not functions:
        return
    
    module_name = module_path.stem
    docstring, tags = module_docs or ("", {})
    
    # 创建输出目录
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 写入模块文档
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# {module_name}\n\n")
        
        # 写入模块描述
        if docstring:
            if 'tips' in tags:
                f.write(f"> 💡 **Note**: {tags['tips']}\n\n")
            
            # 移除标签内容
            clean_docstring = re.sub(r'\{!--<.*?>!--\}', '', docstring)
            f.write(f"{clean_docstring}\n\n")
        
        # 写入函数文档
        for func in functions:
            if should_include_function(func):
                f.write(format_function_docs(func) + "\n\n")


def update_api_docs(source_dir: Path, docs_dir: Path) -> None:
    """
    更新所有API文档
    
    :param source_dir: 源代码目录
    :param docs_dir: 文档输出目录
    """
    # 遍历所有Python文件
    for py_file in source_dir.glob('**/*.py'):
        if py_file.name.startswith('_') and py_file.name != '__init__.py':
            continue
        
        # 确定输出路径
        rel_path = py_file.relative_to(source_dir)
        docs_path = docs_dir / 'api' / rel_path.with_suffix('.md')
        
        # 生成文档
        generate_module_docs(py_file, docs_path)

if __name__ == '__main__':
    # 配置路径
    source_dir = Path('src')  # 源代码目录
    docs_dir = Path('docs')   # 文档输出目录
    
    # 更新API文档
    update_api_docs(source_dir, docs_dir)
