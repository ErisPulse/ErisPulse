# ErisPulse Comment Style Specification

When creating core EP methods, method comments must be added. The comment format is as follows:

## Module-level Documentation Comments

Each module file should begin with a module documentation comment:
```python
"""
[Module Name]
[Description of module functionality]

{!--< tips >!--}
Important usage notes or considerations
{!--< /tips >!--}
"""
```

## Method Comments

### Basic Format
```python
def func(param1: type1, param2: type2) -> return_type:
    """
    [Function description]
    
    :param param1: [Type1] [Parameter description 1]
    :param param2: [Type2] [Parameter description 2]
    :return: [Return type] [Return description]
    """
    pass
```

### Complete Format (for complex methods)
```python
def complex_func(param1: type1, param2: type2 = None) -> Tuple[type1, type2]:
    """
    [Detailed function description]
    [Can include multiple lines of description]
    
    :param param1: [Type1] [Parameter description 1]
    :param param2: [Type2] [Optional parameter description 2] (Default: None)
    
    :return: 
        type1: [Description of return parameter 1]
        type2: [Description of return parameter 2]
    
    :raises ErrorType: [Error description]
    """
    pass
```

## Special Tags (for API Documentation Generation)

When a method's comment contains the following content, it will have the corresponding effect during API documentation generation:

| Tag Format | Effect | Example |
|---------|------|------|
| `{!--< internal-use >!--}` | Mark as internal use, not included in documentation | `{!--< internal-use >!--}` |
| `{!--< ignore >!--}` | Ignore this method, not included in documentation | `{!--< ignore >!--}` |
| `{!--< deprecated >!--}` | Mark as deprecated method | `{!--< deprecated >!--} Please use new_func() instead` |
| `{!--< experimental >!--}` | Mark as experimental feature | `{!--< experimental >!--} May be unstable` |
| `{!--< tips >!--}...{!--< /tips >!--}` | Multi-line tip content | `{!--< tips >!--}\nImportant tip content\n{!--< /tips >!--}` |
| `{!--< tips >!--}` | Single-line tip content | `{!--< tips >!--} Note: This method requires initialization first` |

> **Boundary Clarification**: In the main documentation (Markdown files under `docs/`), use GitHub-style admonitions (`> [!TIP]` etc.) to indicate notes; in docstrings, use the tags described in this section — **these two systems are independent and should not be mixed** (docstring `> [!TIP]` will not be recognized as a tip block by the API documentation generator, and `{!--< >!--}` tags in Markdown will not be processed either).

## Tag Parsing Contract

The following is the **actual parsing behavior** of `process_docstring_for_markdown()` in `scripts/tools/generate-api-docs.py` (core transformation performed line-by-line in `_process_doc_lines()`). When writing tags, expect results according to this contract:

1. **`{!--< ignore >!--}` applies globally**: Before conversion starts, a substring check is performed on the entire docstring. If matched, the module / class / method will **not generate documentation at all**. The position is irrelevant—even if written inside a code fence, it still takes effect.
2. **Code fences have priority**: Once a line contains a ` ``` ` fence marker, all lines inside the fence are passed through unchanged, and other tags inside the fence **will not be parsed**.
3. **`tips` are collected line by line**: The text after the opening tag on the same line, plus subsequent lines, until a line containing `{!--< /tips >!--}` is encountered (taking the text before the closing tag), is rendered as a `> **Tip**` blockquote; examples and code blocks within the block are converted normally. Text before the opening tag on the same line and after the closing tag on the same line are **discarded**.
4. **No error for unclosed tips**: If the closing tag is missing, the content is silently collected until the end of the docstring and rendered as a tip block—no error or warning is issued, and issues are discovered by reviewing the generated result.
5. **Single-line tags match as substrings**: `internal-use` / `deprecated` / `experimental` are output as **internal method** / **deprecated** / **experimental feature** plus the text after the last occurrence of the tag in that line; text before the tag is discarded.
6. **Unknown or miswritten tags**: If a line contains both `{!--<` and `>!--}` but is not one of the above known tags, the line is **silently skipped**; if the tag format is incorrect (e.g., `{!--< tip >--}` missing the `!`), it does not meet the skipping condition and will **leak into the generated API documentation verbatim**—please visually inspect the output after generation.

## Best Practices

1. **Type Hints**: Use Python type hinting syntax
   ```python
   def func(param: int) -> str:
   ```

2. **Parameter Documentation**: Specify default values for optional parameters
   ```python
   :param timeout: [int] Timeout in seconds (default: 30)
   ```

3. **Return Value Documentation**: Use `Tuple` or clearly specify multiple return values
   ```python
   :return: 
       str: Status information
       int: Status code
   ```

4. **Exception Documentation**: Use `:raises` to document possible exceptions
   ```python
   :raises ValueError: Thrown when the parameter is invalid
   ```

5. **Internal Methods**: Add the `{!--< internal-use >!--}` tag for non-public APIs

6. **Deprecated Methods**: Mark deprecated methods and provide alternatives
   ```python
   {!--< deprecated >!--} Use new_method() instead | 2025-07-09
   ```