# adapter

> 💡 **Note**: 1. 适配器必须继承BaseAdapter并实现必要方法
2. 使用SendDSL实现链式调用风格的消息发送接口
3. 适配器管理器支持多平台适配器的注册和生命周期管理

ErisPulse 适配器系统

提供平台适配器基类、消息发送DSL和适配器管理功能。支持多平台消息处理、事件驱动和生命周期管理。


1. 适配器必须继承BaseAdapter并实现必要方法
2. 使用SendDSL实现链式调用风格的消息发送接口
3. 适配器管理器支持多平台适配器的注册和生命周期管理


### `__init__(self, adapter: 'BaseAdapter', target_type: Optional[str] = None, target_id: Optional[str] = None)`



**Description**  
初始化DSL发送器

**Parameters**  
- `self`
- `adapter` ('BaseAdapter'): 所属适配器实例
- `target_type` (Optional[str]) [optional, default: None]: 目标类型(可选)
- `target_id` (Optional[str]) [optional, default: None]: 目标ID(可选)

### `To(self, target_type: str = None, target_id: str = None) -> 'SendDSL'`



**Description**  
设置消息目标

**Parameters**  
- `self`
- `target_type` (str) [optional, default: None]: 目标类型(可选)
- `target_id` (str) [optional, default: None]: 目标ID(可选)

**Returns**

- Type: `'SendDSL'`
- Description: SendDSL实例

### `__getattr__(self, name: str) -> Callable[..., Awaitable[Any]]`



**Description**  
动态获取消息发送方法

**Parameters**  
- `self`
- `name` (str): 方法名

**Returns**

- Type: `Callable[..., Awaitable[Any]]`
- Description: 消息发送函数

**Raises**

- `AttributeError`: 当方法不存在时抛出

### `wrapper(*args, **kwargs) -> Awaitable[Any]`



**Description**  
消息发送包装函数

**Parameters**  
- `*args`
- `**kwargs`

**Returns**

- Type: `Awaitable[Any]`
- Description: 异步任务

### `Text(self, text: str) -> Awaitable[Any]`



**Description**  
基础文本消息发送方法

**Parameters**  
- `self`
- `text` (str): 文本内容

**Returns**

- Type: `Awaitable[Any]`
- Description: 异步任务

### `__init__(self)`



**Description**  
初始化适配器

**Parameters**  
- `self`

### `on(self, event_type: str = "*") -> Callable[[Callable], Callable]`



**Description**  
事件监听装饰器

**Parameters**  
- `self`
- `event_type` (str) [optional, default: "*"]: 事件类型，默认"*"表示所有事件

**Returns**

- Type: `Callable[[Callable], Callable]`
- Description: 装饰器函数

### `decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)
            self._handlers[event_type].append(wrapper)
            return wrapper
        return decorator

    def middleware(self, func: Callable) -> Callable`



**Description**  
添加中间件处理器

**Parameters**  
- `func` (Callable) -> Callable:
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)
            self._handlers[event_type].append(wrapper)
            return wrapper
        return decorator

    def middleware(self): 中间件函数
- `func` (Callable): 中间件函数

**Returns**

- Type: `Callable`
- Description: 中间件函数

### `call_api(self, endpoint: str, **params: Any) -> Any`



**Description**  
调用平台API的抽象方法

**Parameters**  
- `self`
- `endpoint` (str): API端点
- `**params` (Any)

**Returns**

- Type: `Any`
- Description: API调用结果

**Raises**

- `NotImplementedError`: 必须由子类实现

### `start(self) -> None`



**Description**  
启动适配器的抽象方法
        
        :raises NotImplementedError: 必须由子类实现

**Parameters**  
- `self`

**Returns**

- Type: `None`

**Raises**

- `NotImplementedError`: 必须由子类实现

### `shutdown(self) -> None`



**Description**  
关闭适配器的抽象方法
        
        :raises NotImplementedError: 必须由子类实现

**Parameters**  
- `self`

**Returns**

- Type: `None`

**Raises**

- `NotImplementedError`: 必须由子类实现

### `add_handler(self, *args: Any) -> None`



**Description**  
添加事件处理器

**Parameters**  
- `self`
- `*args` (Any)

**Returns**

- Type: `None`

**Raises**

- `TypeError`: 当参数数量无效时抛出

### `wrapper(*handler_args, **handler_kwargs): return await handler(*handler_args, **handler_kwargs)

        self._handlers[event_type].append(wrapper)
        
    async def emit(self, event_type: str, data: Any) -> None`



**Description**  
触发事件

**Parameters**  
- `*handler_args, **handler_kwargs)` (return await handler(*handler_args, **handler_kwargs)

        self._handlers[event_type].append(wrapper)
        
    async def emit(self)
- `event_type` (str): 事件类型
- `data` (Any): 事件数据

**Returns**

- Type: `None`

### `send(self, target_type: str, target_id: str, message: Any, **kwargs: Any) -> Any`



**Description**  
发送消息的便捷方法

**Parameters**  
- `self`
- `target_type` (str): 目标类型
- `target_id` (str): 目标ID
- `message` (Any): 消息内容
- `**kwargs` (Any)

**Returns**

- Type: `Any`
- Description: 发送结果

**Raises**

- `AttributeError`: 当发送方法不存在时抛出

### `__init__(self): self._adapters: Dict[str, BaseAdapter] = {}
        self._adapter_instances: Dict[Type[BaseAdapter], BaseAdapter] = {}
        self._platform_to_instance: Dict[str, BaseAdapter] = {}
        self._started_instances: Set[BaseAdapter] = set()

    def register(self, platform: str, adapter_class: Type[BaseAdapter]) -> bool`



**Description**  
注册新的适配器类

**Parameters**  
- `self)` (self._adapters: Dict[str)
- `BaseAdapter]` [optional, default: {}
        self._adapter_instances: Dict[Type[BaseAdapter]]
- `BaseAdapter]` [optional, default: {}
        self._platform_to_instance: Dict[str]
- `BaseAdapter]` [optional, default: {}
        self._started_instances: Set[BaseAdapter] = set()

    def register(self]
- `platform` (str): 平台名称
- `adapter_class` (Type[BaseAdapter]): 适配器类

**Returns**

- Type: `bool`
- Description: 注册是否成功

**Raises**

- `TypeError`: 当适配器类无效时抛出

### `startup(self, platforms: List[str] = None) -> None`



**Description**  
启动指定的适配器

**Parameters**  
- `self`
- `platforms` (List[str]) [optional, default: None]: 要启动的平台列表，None表示所有平台

**Returns**

- Type: `None`

**Raises**

- `ValueError`: 当平台未注册时抛出

### `shutdown(self) -> None`



**Description**  
关闭所有适配器
        
        :example:
        >>> await adapter.shutdown()

**Parameters**  
- `self`

**Returns**

- Type: `None`

### `get(self, platform: str) -> Optional[BaseAdapter]`



**Description**  
获取指定平台的适配器实例

**Parameters**  
- `self`
- `platform` (str): 平台名称

**Returns**

- Type: `Optional[BaseAdapter]`
- Description: 适配器实例或None

### `__getattr__(self, platform: str) -> BaseAdapter`



**Description**  
通过属性访问获取适配器实例

**Parameters**  
- `self`
- `platform` (str): 平台名称

**Returns**

- Type: `BaseAdapter`
- Description: 适配器实例

**Raises**

- `AttributeError`: 当平台未注册时抛出

### `platforms(self) -> List[str]`



**Description**  
获取所有已注册的平台列表
        
        :return: 平台名称列表
            
        :example:
        >>> print("已注册平台:", adapter.platforms)

**Parameters**  
- `self`

**Returns**

- Type: `List[str]`
- Description: 平台名称列表

