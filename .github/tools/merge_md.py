def merge_markdown_files(file_paths, output_file):
    with open(output_file, 'w', encoding='utf-8') as outfile:
        for file_path in file_paths:
            with open(file_path, 'r', encoding='utf-8') as infile:
                content = infile.read()
                outfile.write(f"<!-- {file_path} -->\n\n")
                outfile.write(content)
                outfile.write(f"\n\n <!--- End of {file_path} -->\n\n")

if __name__ == "__main__":
    files_to_merge = [
        "docs/REFERENCE.md",
        "docs/ADAPTERS.md",
        "docs/DEVELOPMENT.md",
    ]
    output_file = "docs/ForAIDocs/ErisPulseDevelop.md"
    
    merge_markdown_files(files_to_merge, output_file)