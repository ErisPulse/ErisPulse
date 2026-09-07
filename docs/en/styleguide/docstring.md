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

When a method comment contains the following content, it will produce the corresponding effect during API documentation generation:

| Tag Format | Effect | Example |
|---------|------|------|
| `{!--< internal-use >!--}` | Mark as internal use, not included in documentation | `{!--< internal-use >!--}` |
| `{!--< ignore >!--}` | Ignore this method, not included in documentation | `{!--< ignore >!--}` |
| `{!--< deprecated >!--}` | Mark as deprecated method | `{!--< deprecated >!--} Please use new_func() instead` |
| `{!--< experimental >!--}` | Mark as experimental feature | `{!--< experimental >!--} May be unstable` |
| `{!--< tips >!--}...{!--< /tips >!--}` | Multi-line tip content | `{!--< tips >!--}\nImportant tip content\n{!--< /tips >!--}` |
| `{!--< tips >!--}` | Single-line tip content | `{!--< tips >!--} Note: This method requires initialization first` |

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