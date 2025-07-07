# __init__

> 💡 **Note**: 1. 使用前请确保已正确安装所有依赖
2. 调用sdk.init()进行初始化
3. 模块加载顺序由依赖关系决定

ErisPulse SDK 主模块

提供SDK核心功能模块加载和初始化功能


1. 使用前请确保已正确安装所有依赖
2. 调用sdk.init()进行初始化
3. 模块加载顺序由依赖关系决定


### `load() -> Tuple[Dict[str, object], List[str], List[str]]`



**Description**  
从PyPI包entry-points加载模块

        :return: 
            Dict[str, object]: 模块对象字典
            List[str]: 启用的模块列表
            List[str]: 停用的模块列表
            
        :raises ImportError: 当无法加载模块时抛出

**Parameters**  
- ``

**Returns**

- Type: `Tuple[Dict[str, object], List[str], List[str]]`

**Raises**

- `ImportError`: 当无法加载模块时抛出

### `load(module_path: str) -> Tuple[Dict[str, object], List[str], List[str]]`


> ⚠️ **Deprecated**: True


**Description**  
{!--< deprecated >!--} 我们不再推荐在目录下放置模块, 这只是一个兼容性适配
        扫描并加载目录中的模块

**Parameters**  
- `module_path` (str): 模块目录路径

**Returns**

- Type: `Tuple[Dict[str, object], List[str], List[str]]`

**Raises**

- `ImportError`: 当模块加载失败时抛出

### `init() -> bool`


> 💡 **Note**: 1. 此方法是SDK初始化的入口点
        2. 如果初始化失败会抛出InitError异常
        3. 初始化过程会自动处理模块依赖关系


**Description**  
初始化所有模块
        
        执行步骤:
        1. 从PyPI包和本地目录加载模块
        2. 解析模块依赖关系并进行拓扑排序
        3. 注册模块适配器
        4. 初始化各模块
        
        :return: bool: 模块初始化是否成功
        
        {!--< tips >!--}
        1. 此方法是SDK初始化的入口点
        2. 如果初始化失败会抛出InitError异常
        3. 初始化过程会自动处理模块依赖关系
        {!--< /tips >!--}
        
        :raises InitError: 当初始化失败时抛出

**Parameters**  
- ``

**Returns**

- Type: `bool`
- Description: bool: 模块初始化是否成功

**Raises**

- `InitError`: 当初始化失败时抛出

### `init_progress() -> Tuple[bool, bool]`


> 💡 **Note**: 1. 如果文件已存在，函数会返回(False, False)
    2. 此函数通常由SDK内部调用，不建议直接使用


**Description**  
初始化项目环境文件

    :return: 
        bool: 项目环境文件是否初始化成功(文件已存在时返回False)
        bool: 项目入口文件是否初始化成功(文件已存在时返回False)
    
    {!--< tips >!--}
    1. 如果文件已存在，函数会返回(False, False)
    2. 此函数通常由SDK内部调用，不建议直接使用
    {!--< /tips >!--}

**Parameters**  
- ``

**Returns**

- Type: `Tuple[bool, bool]`

### `init() -> bool`


> 💡 **Note**: 1. 这是SDK的主要入口函数
    2. 如果初始化失败会抛出InitError异常
    3. 建议在main.py中调用此函数


**Description**  
SDK初始化入口
    
    执行步骤:
    1. 准备运行环境(创建env.py和main.py)
    2. 加载环境变量
    3. 初始化所有模块
    
    :return: bool: SDK初始化是否成功
    
    {!--< tips >!--}
    1. 这是SDK的主要入口函数
    2. 如果初始化失败会抛出InitError异常
    3. 建议在main.py中调用此函数
    {!--< /tips >!--}
    
    :raises InitError: 当初始化失败时抛出

**Parameters**  
- ``

**Returns**

- Type: `bool`
- Description: bool: SDK初始化是否成功

**Raises**

- `InitError`: 当初始化失败时抛出

