# raiserr

> 💡 **Note**: 1. 使用register注册自定义错误类型
2. 通过info获取错误信息
3. 自动捕获未处理异常

ErisPulse 错误管理系统

提供错误类型注册、抛出和管理功能，集成全局异常处理。支持自定义错误类型、错误链追踪和全局异常捕获。


1. 使用register注册自定义错误类型
2. 通过info获取错误信息
3. 自动捕获未处理异常


### `__init__(self): self._types = {}

    def register(self, name: str, doc: str = "", base: Type[Exception] = Exception) -> Type[Exception]`



**Description**  
注册新的错误类型

**Parameters**  
- `self)` (self._types) [optional, default: {}

    def register(self]
- `name` (str): 错误类型名称
- `doc` (str) [optional, default: ""]: 错误描述文档
- `base` (Type[Exception]) [optional, default: Exception]: 基础异常类

**Returns**

- Type: `Type[Exception]`
- Description: 注册的错误类

### `__getattr__(self, name: str) -> Callable[..., None]`



**Description**  
动态获取错误抛出函数

**Parameters**  
- `self`
- `name` (str): 错误类型名称

**Returns**

- Type: `Callable[..., None]`
- Description: 错误抛出函数

**Raises**

- `AttributeError`: 当错误类型未注册时抛出

### `raiser(msg: str, exit: bool = False) -> None`



**Description**  
错误抛出函数

**Parameters**  
- `msg` (str): 错误消息
- `exit` (bool) [optional, default: False]: 是否退出程序

**Returns**

- Type: `None`

### `info(self, name: Optional[str] = None) -> Dict[str, Any]`



**Description**  
获取错误信息

**Parameters**  
- `self`
- `name` (Optional[str]) [optional, default: None]: 错误类型名称(可选)

**Returns**

- Type: `Dict[str, Any]`
- Description: 错误信息字典

