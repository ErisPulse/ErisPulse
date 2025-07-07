# mods

> 💡 **Note**: 1. 使用模块前缀区分不同模块的配置
2. 支持模块状态持久化存储
3. 自动处理模块间的依赖关系

ErisPulse 模块管理器

提供模块的注册、状态管理和依赖关系处理功能。支持模块的启用/禁用、版本控制和依赖解析。


1. 使用模块前缀区分不同模块的配置
2. 支持模块状态持久化存储
3. 自动处理模块间的依赖关系


### `module_prefix(self) -> str`



**Description**  
获取模块数据前缀
        
        :return: 模块数据前缀字符串

**Parameters**  
- `self`

**Returns**

- Type: `str`
- Description: 模块数据前缀字符串

### `status_prefix(self) -> str`



**Description**  
获取模块状态前缀
        
        :return: 模块状态前缀字符串

**Parameters**  
- `self`

**Returns**

- Type: `str`
- Description: 模块状态前缀字符串

### `set_module_status(self, module_name: str, status: bool) -> None`



**Description**  
设置模块启用状态

**Parameters**  
- `self`
- `module_name` (str): 模块名称
- `status` (bool): 启用状态

**Returns**

- Type: `None`

### `get_module_status(self, module_name: str) -> bool`



**Description**  
获取模块启用状态

**Parameters**  
- `self`
- `module_name` (str): 模块名称

**Returns**

- Type: `bool`
- Description: 模块是否启用

### `set_module(self, module_name: str, module_info: Dict[str, Any]) -> None`



**Description**  
设置模块信息

**Parameters**  
- `self`
- `module_name` (str): 模块名称
- `module_info` (Dict[str): 模块信息字典
- `Any]`

**Returns**

- Type: `None`

### `get_module(self, module_name: str) -> Optional[Dict[str, Any]]`



**Description**  
获取模块信息

**Parameters**  
- `self`
- `module_name` (str): 模块名称

**Returns**

- Type: `Optional[Dict[str, Any]]`
- Description: 模块信息字典或None

### `set_all_modules(self, modules_info: Dict[str, Dict[str, Any]]) -> None`



**Description**  
批量设置多个模块信息

**Parameters**  
- `self`
- `modules_info` (Dict[str): 模块信息字典
- `Dict[str`
- `Any]]`

**Returns**

- Type: `None`

### `get_all_modules(self) -> Dict[str, Dict[str, Any]]`



**Description**  
获取所有模块信息
        
        :return: 模块信息字典
        
        :example:
        >>> all_modules = mods.get_all_modules()
        >>> for name, info in all_modules.items():
        >>>     print(f"{name}: {info.get('status')}")

**Parameters**  
- `self`

**Returns**

- Type: `Dict[str, Dict[str, Any]]`
- Description: 模块信息字典

### `update_module(self, module_name: str, module_info: Dict[str, Any]) -> None`



**Description**  
更新模块信息

**Parameters**  
- `self`
- `module_name` (str): 模块名称
- `module_info` (Dict[str): 完整的模块信息字典
- `Any]`

**Returns**

- Type: `None`

### `remove_module(self, module_name: str) -> bool`



**Description**  
移除模块

**Parameters**  
- `self`
- `module_name` (str): 模块名称

**Returns**

- Type: `bool`
- Description: 是否成功移除

### `update_prefixes(self, module_prefix: Optional[str] = None, status_prefix: Optional[str] = None) -> None`



**Description**  
更新模块前缀配置

**Parameters**  
- `self`
- `module_prefix` (Optional[str]) [optional, default: None]: 新的模块数据前缀(可选)
- `status_prefix` (Optional[str]) [optional, default: None]: 新的模块状态前缀(可选)

**Returns**

- Type: `None`

