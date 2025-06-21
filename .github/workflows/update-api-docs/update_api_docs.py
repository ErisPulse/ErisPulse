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

def update_reference_docs(module_name, docs, reference_path, module_path):
    """Update the REFERENCE.md file with module documentation.
    
    Args:
        module_name: Name of the module
        docs: Extracted documentation string
        reference_path: Path to REFERENCE.md file
        module_path: Relative path to the module file
    """
    if not docs:
        return
    
    # Create docs directory if not exists
    reference_path.parent.mkdir(exist_ok=True)
    
    # Initialize file if not exists
    if not reference_path.exists():
        with open(reference_path, 'w', encoding='utf-8') as f:
            f.write("# API Reference Documentation\n\n")
    
    # Read existing content
    with open(reference_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Prepare section header
    section_header = f"## {module_name} (source: {module_path})"
    
    # Check if section exists
    section_pattern = re.escape(section_header)
    match = re.search(section_pattern, content, re.IGNORECASE)
    
    if match:
        # Section exists - check if docs are the same
        section_start = match.start()
        next_section = re.search(r'## ', content[section_start + 1:])
        section_end = section_start + next_section.start() if next_section else len(content)
        
        if docs.strip() in content[section_start:section_end]:
            print(f"Docs for {module_name} already up to date")
            return
            
        # Update existing section
        updated_content = (
            content[:section_start] +
            section_header + '\n\n' +
            docs + '\n\n' +
            content[section_end:]
        )
    else:
        # Add new section at the end
        updated_content = content + section_header + '\n\n' + docs + '\n\n'
    
    # Write back to file
    with open(reference_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    print(f"Updated docs for {module_name} in REFERENCE.md")

def main():
    # Paths
    module_dir = Path('ErisPulse')
    reference_path = Path('docs/REFERENCE.md')
    
    # Process each module
    modules = ['__init__', '__main__', 'adapter', 'db', 'logger', 'mods', 'raiserr', 'util']
    
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