# db

> 💡 **Note**: 1. 支持JSON序列化存储复杂数据类型
2. 提供事务支持确保数据一致性
3. 自动快照功能防止数据丢失

ErisPulse 环境配置模块

提供键值存储、事务支持、快照和恢复功能，用于管理框架配置数据。基于SQLite实现持久化存储，支持复杂数据类型和原子操作。


1. 支持JSON序列化存储复杂数据类型
2. 提供事务支持确保数据一致性
3. 自动快照功能防止数据丢失


### `get(self, key: str, default: Any = None) -> Any`



**Description**  
获取配置项的值

**Parameters**  
- `self`
- `key` (str): 配置项键名
- `default` (Any) [optional, default: None]: 默认值(当键不存在时返回)

**Returns**

- Type: `Any`
- Description: 配置项的值

### `get_all_keys(self) -> List[str]`



**Description**  
获取所有配置项的键名
        
        :return: 键名列表
        
        :example:
        >>> all_keys = env.get_all_keys()
        >>> print(f"共有 {len(all_keys)} 个配置项")

**Parameters**  
- `self`

**Returns**

- Type: `List[str]`
- Description: 键名列表

### `set(self, key: str, value: Any) -> bool`



**Description**  
设置配置项的值

**Parameters**  
- `self`
- `key` (str): 配置项键名
- `value` (Any): 配置项的值

**Returns**

- Type: `bool`
- Description: 操作是否成功

### `set_multi(self, items: Dict[str, Any]) -> bool`



**Description**  
批量设置多个配置项

**Parameters**  
- `self`
- `items` (Dict[str): 键值对字典
- `Any]`

**Returns**

- Type: `bool`
- Description: 操作是否成功

### `delete(self, key: str) -> bool`



**Description**  
删除配置项

**Parameters**  
- `self`
- `key` (str): 配置项键名

**Returns**

- Type: `bool`
- Description: 操作是否成功

### `delete_multi(self, keys: List[str]) -> bool`



**Description**  
批量删除多个配置项

**Parameters**  
- `self`
- `keys` (List[str]): 键名列表

**Returns**

- Type: `bool`
- Description: 操作是否成功

### `get_multi(self, keys: List[str]) -> Dict[str, Any]`



**Description**  
批量获取多个配置项的值

**Parameters**  
- `self`
- `keys` (List[str]): 键名列表

**Returns**

- Type: `Dict[str, Any]`
- Description: 键值对字典

### `transaction(self) -> 'EnvManager._Transaction'`



**Description**  
创建事务上下文
        
        :return: 事务上下文管理器
        
        :example:
        >>> with env.transaction():
        >>>     env.set("key1", "value1")
        >>>     env.set("key2", "value2")

**Parameters**  
- `self`

**Returns**

- Type: `'EnvManager._Transaction'`
- Description: 事务上下文管理器

### `__init__(self, env_manager: 'EnvManager'):
            self.env_manager = env_manager
            self.conn = None
            self.cursor = None

        def __enter__(self) -> 'EnvManager._Transaction'`



**Description**  
进入事务上下文

**Parameters**  
- `self, env_manager` ('EnvManager'):
            self.env_manager) [optional, default: env_manager
            self.conn = None
            self.cursor = None

        def __enter__(self]

**Returns**

- Type: `'EnvManager._Transaction'`

### `__exit__(self, exc_type: Type[Exception], exc_val: Exception, exc_tb: Any) -> None`



**Description**  
退出事务上下文

**Parameters**  
- `self`
- `exc_type` (Type[Exception])
- `exc_val` (Exception)
- `exc_tb` (Any)

**Returns**

- Type: `None`

### `set_snapshot_interval(self, seconds: int) -> None`



**Description**  
设置自动快照间隔

**Parameters**  
- `self`
- `seconds` (int): 间隔秒数

**Returns**

- Type: `None`

### `clear(self) -> bool`



**Description**  
清空所有配置项
        
        :return: 操作是否成功
        
        :example:
        >>> env.clear()  # 清空所有配置

**Parameters**  
- `self`

**Returns**

- Type: `bool`
- Description: 操作是否成功

### `load_env_file(self) -> bool`



**Description**  
加载env.py文件中的配置项
        
        :return: 操作是否成功
        
        :example:
        >>> env.load_env_file()  # 加载env.py中的配置

**Parameters**  
- `self`

**Returns**

- Type: `bool`
- Description: 操作是否成功

### `__getattr__(self, key: str) -> Any`



**Description**  
通过属性访问配置项

**Parameters**  
- `self`
- `key` (str): 配置项键名

**Returns**

- Type: `Any`
- Description: 配置项的值

**Raises**

- `KeyError`: 当配置项不存在时抛出

### `__setattr__(self, key: str, value: Any) -> None`



**Description**  
通过属性设置配置项

**Parameters**  
- `self`
- `key` (str): 配置项键名
- `value` (Any): 配置项的值

**Returns**

- Type: `None`

### `snapshot(self, name: Optional[str] = None) -> str`



**Description**  
创建数据库快照

**Parameters**  
- `self`
- `name` (Optional[str]) [optional, default: None]: 快照名称(可选)

**Returns**

- Type: `str`
- Description: 快照文件路径

### `restore(self, snapshot_name: str) -> bool`



**Description**  
从快照恢复数据库

**Parameters**  
- `self`
- `snapshot_name` (str): 快照名称或路径

**Returns**

- Type: `bool`
- Description: 恢复是否成功

### `list_snapshots(self) -> List[Tuple[str, datetime, int]]`



**Description**  
列出所有可用的快照
        
        :return: 快照信息列表(名称, 创建时间, 大小)
        
        :example:
        >>> for name, date, size in env.list_snapshots():
        >>>     print(f"{name} - {date} ({size} bytes)")

**Parameters**  
- `self`

**Returns**

- Type: `List[Tuple[str, datetime, int]]`
- Description: 快照信息列表(名称, 创建时间, 大小)

### `delete_snapshot(self, snapshot_name: str) -> bool`



**Description**  
删除指定的快照

**Parameters**  
- `self`
- `snapshot_name` (str): 快照名称

**Returns**

- Type: `bool`
- Description: 删除是否成功

