import re
import os
from pathlib import Path

def extract_module_docs(file_path):
    """Extract the module documentation from a Python file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Match the module docstring (triple-quoted string at start of file)
    match = re.search(r'^\"\"\"(.*?)\"\"\"', content, re.DOTALL)
    if not match:
        return None
    
    docstring = match.group(1).strip()
    return docstring

def update_reference_docs(module_name, docs, reference_path):
    """Update the REFERENCE.md file with module documentation."""
    if not docs:
        return
    
    # Read existing reference docs
    with open(reference_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the section for this module
    section_pattern = rf'## \d+\. .*\({module_name}\)'
    match = re.search(section_pattern, content, re.IGNORECASE)
    
    if not match:
        print(f"Warning: No section found for {module_name} in REFERENCE.md")
        return
    
    section_start = match.start()
    next_section = re.search(r'## \d+\. ', content[section_start + 1:])
    section_end = section_start + next_section.start() if next_section else len(content)
    
    # Check if docs already exist in this section
    if docs.strip() in content[section_start:section_end]:
        print(f"Docs for {module_name} already up to date")
        return
    
    # Insert the docs before the next section
    updated_content = (
        content[:section_start] +
        match.group(0) + '\n\n' +
        docs + '\n\n' +
        content[section_end:]
    )
    
    # Write back to file
    with open(reference_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    print(f"Updated docs for {module_name} in REFERENCE.md")

def main():
    # Paths
    module_dir = Path('ErisPulse')
    reference_path = Path('docs/REFERENCE.md')
    
    # Process each module
    modules = ['adapter', 'db', 'logger', 'mods', 'raiserr', 'util']
    
    for module in modules:
        py_file = module_dir / f'{module}.py'
        if not py_file.exists():
            print(f"Warning: {py_file} not found")
            continue
            
        docs = extract_module_docs(py_file)
        if docs:
            update_reference_docs(module, docs, reference_path)

if __name__ == '__main__':
    main()