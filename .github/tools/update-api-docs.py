import re
import os
from pathlib import Path

def extract_module_docs(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    match = re.search(r'^\"\"\"(.*?)\"\"\"', content, re.DOTALL)
    if not match:
        return None
    
    docstring = match.group(1).strip()
    return docstring

def update_reference_docs(module_name, docs, reference_path, module_path):
    if not docs:
        return
    
    reference_path.parent.mkdir(exist_ok=True)
    
    if not reference_path.exists():
        with open(reference_path, 'w', encoding='utf-8') as f:
            f.write("# API Reference Documentation\n\n")
    
    with open(reference_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    github_base_url = "https://raw.githubusercontent.com/ErisPulse/ErisPulse/refs/heads/main/"
    github_source_url = github_base_url + module_path.replace('\\', '/')
    
    section_header = f"## {module_name} (source: [{module_path}]({github_source_url}))"
    
    section_pattern = re.escape(section_header)
    match = re.search(section_pattern, content, re.IGNORECASE)
    
    if match:
        section_start = match.start()
        next_section = re.search(r'## ', content[section_start + 1:])
        section_end = section_start + next_section.start() if next_section else len(content)
        
        if docs.strip() in content[section_start:section_end]:
            print(f"Docs for {module_name} already up to date")
            return
            
        updated_content = (
            content[:section_start] +
            section_header + '\n\n' +
            docs + '\n\n' +
            content[section_end:]
        )
    else:
        updated_content = content + section_header + '\n\n' + docs + '\n\n'
    
    with open(reference_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    print(f"Updated docs for {module_name} in REFERENCE.md")

def main():
    module_dir = Path('src/ErisPulse')
    reference_path = Path('docs/REFERENCE.md')
    
    modules = ['__init__', '__main__', 'adapter', 'db', 'logger', 'raiserr', 'util']
    
    for module in modules:
        py_file = module_dir / f'{module}.py'
        if not py_file.exists():
            print(f"Warning: {py_file} not found")
            continue
            
        docs = extract_module_docs(py_file)
        if docs:
            update_reference_docs(module, docs, reference_path, f"ErisPulse/{module}.py")

if __name__ == '__main__':
    main()