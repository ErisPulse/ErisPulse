# API Reference Documentation

## __init__ (source: [ErisPulse/__init__.py](https://raw.githubusercontent.com/ErisPulse/ErisPulse/refs/heads/main/ErisPulse/__init__.py))

# SDK 核心初始化

提供SDK全局对象构建和初始化功能。

## 主要功能
- 构建全局sdk对象
- 预注册核心错误类型
- 提供SDK初始化入口
- 集成各核心模块

## API 文档
### 核心对象：
    - sdk: 全局SDK命名空间对象
    - sdk.init(): SDK初始化入口函数

### 预注册错误类型：
    - CaughtExternalError: 外部捕获异常
    - InitError: 初始化错误
    - MissingDependencyError: 缺少依赖错误  
    - InvalidDependencyError: 无效依赖错误
    - CycleDependencyError: 循环依赖错误
    - ModuleLoadError: 模块加载错误

### 示例用法：

```
from ErisPulse import sdk

# 初始化SDK
sdk.init()

# 访问各模块功能
sdk.logger.info("SDK已初始化")
```

## __main__ (source: [ErisPulse/__main__.py](https://raw.githubusercontent.com/ErisPulse/ErisPulse/refs/heads/main/ErisPulse/__main__.py))

# CLI 入口

提供命令行界面(CLI)用于模块管理、源管理和开发调试。

## 主要功能
- 模块管理: 安装/卸载/启用/禁用
- 源管理: 添加/删除/更新源
- 热重载: 开发时自动重启
- 彩色终端输出

## 主要命令
### 模块管理:
    init: 初始化SDK
    install: 安装模块
    uninstall: 卸载模块
    enable: 启用模块
    disable: 禁用模块
    list: 列出模块
    update: 更新模块列表
    upgrade: 升级模块

### 源管理:
    origin add: 添加源
    origin del: 删除源  
    origin list: 列出源

### 开发调试:
    run: 运行脚本
    --reload: 启用热重载

### 示例用法:

```
# 安装模块
epsdk install MyModule

# 启用热重载
epsdk run main.py --reload

# 管理源
epsdk origin add https://example.com/map.json
```

## adapter (source: [ErisPulse/adapter.py](https://raw.githubusercontent.com/ErisPulse/ErisPulse/refs/heads/main/ErisPulse/adapter.py))

# 适配器系统

提供平台适配器基类、消息发送DSL和适配器管理功能。支持多平台消息处理、事件驱动和生命周期管理。

## API 文档

### 适配器基类 (BaseAdapter)
适配器基类提供了与外部平台交互的标准接口。

#### call_api(endpoint: str, **params) -> Any
调用平台API的抽象方法。
- 参数:
  - endpoint: API端点
  - **params: API参数
- 返回:
  - Any: API调用结果
- 说明:
  - 必须由子类实现
  - 处理与平台的实际通信
- 示例:
```python
class MyPlatformAdapter(BaseAdapter):
    async def call_api(self, endpoint: str, **params):
        if endpoint == "/send":
            return await self._send_message(params)
        elif endpoint == "/upload":
            return await self._upload_file(params)
        raise NotImplementedError(f"未实现的端点: {endpoint}")
```

#### start() -> None
启动适配器的抽象方法。
- 参数: 无
- 返回:
  - None
- 说明:
  - 必须由子类实现
  - 处理适配器的初始化和启动逻辑
- 示例:
```python
class MyPlatformAdapter(BaseAdapter):
    async def start(self):
        self.client = await self._create_client()
        self.ws = await self.client.create_websocket()
        self._start_heartbeat()
```

#### shutdown() -> None
关闭适配器的抽象方法。
- 参数: 无
- 返回:
  - None
- 说明:
  - 必须由子类实现
  - 处理资源清理和关闭逻辑
- 示例:
```python
class MyPlatformAdapter(BaseAdapter):
    async def shutdown(self):
        if self.ws:
            await self.ws.close()
        if self.client:
            await self.client.close()
```

#### on(event_type: str = "*") -> Callable
事件监听装饰器。
- 参数:
  - event_type: 事件类型，默认"*"表示所有事件
- 返回:
  - Callable: 装饰器函数
- 示例:
```python
adapter = MyPlatformAdapter()

@adapter.on("message")
async def handle_message(data):
    print(f"收到消息: {data}")

@adapter.on("error")
async def handle_error(error):
    print(f"发生错误: {error}")

# 处理所有事件
@adapter.on()
async def handle_all(event):
    print(f"事件: {event}")
```

#### emit(event_type: str, data: Any) -> None
触发事件。
- 参数:
  - event_type: 事件类型
  - data: 事件数据
- 返回:
  - None
- 示例:
```python
class MyPlatformAdapter(BaseAdapter):
    async def _handle_websocket_message(self, message):
        # 处理消息并触发相应事件
        if message.type == "chat":
            await self.emit("message", {
                "type": "chat",
                "content": message.content,
                "sender": message.sender
            })
```

#### middleware(func: Callable) -> Callable
添加中间件处理器。
- 参数:
  - func: 中间件函数
- 返回:
  - Callable: 中间件函数
- 示例:
```python
adapter = MyPlatformAdapter()

@adapter.middleware
async def log_middleware(data):
    print(f"处理数据: {data}")
    return data

@adapter.middleware
async def filter_middleware(data):
    if "spam" in data.get("content", ""):
        return None
    return data
```

### 消息发送DSL (SendDSL)
提供链式调用风格的消息发送接口。

#### To(target_type: str = None, target_id: str = None) -> 'SendDSL'
设置消息目标。
- 参数:
  - target_type: 目标类型（可选）
  - target_id: 目标ID
- 返回:
  - SendDSL: 发送器实例
- 示例:
```python
# 发送到用户
sdk.adapter.Platform.Send.To("user", "123").Text("Hello")

# 发送到群组
sdk.adapter.Platform.Send.To("group", "456").Text("Hello Group")

# 简化形式（只有ID）
sdk.adapter.Platform.Send.To("123").Text("Hello")
```

#### Text(text: str) -> Task
发送文本消息。
- 参数:
  - text: 文本内容
- 返回:
  - Task: 异步任务
- 示例:
```python
# 发送简单文本
await sdk.adapter.Platform.Send.To("user", "123").Text("Hello")

# 发送格式化文本
name = "Alice"
await sdk.adapter.Platform.Send.To("123").Text(f"Hello {name}")
```

### 适配器管理 (AdapterManager)
管理多个平台适配器的注册、启动和关闭。

#### register(platform: str, adapter_class: Type[BaseAdapter]) -> bool
注册新的适配器类。
- 参数:
  - platform: 平台名称
  - adapter_class: 适配器类
- 返回:
  - bool: 注册是否成功
- 示例:
```python
# 注册适配器
sdk.adapter.register("MyPlatform", MyPlatformAdapter)

# 注册多个适配器
adapters = {
    "Platform1": Platform1Adapter,
    "Platform2": Platform2Adapter
}
for name, adapter in adapters.items():
    sdk.adapter.register(name, adapter)
```

#### startup(platforms: List[str] = None) -> None
启动指定的适配器。
- 参数:
  - platforms: 要启动的平台列表，None表示所有平台
- 返回:
  - None
- 示例:
```python
# 启动所有适配器
await sdk.adapter.startup()

# 启动指定适配器
await sdk.adapter.startup(["Platform1", "Platform2"])
```

#### shutdown() -> None
关闭所有适配器。
- 参数: 无
- 返回:
  - None
- 示例:
```python
# 关闭所有适配器
await sdk.adapter.shutdown()

# 在程序退出时关闭
import atexit
atexit.register(lambda: asyncio.run(sdk.adapter.shutdown()))
```

## db (source: [ErisPulse/db.py](https://raw.githubusercontent.com/ErisPulse/ErisPulse/refs/heads/main/ErisPulse/db.py))

# 环境配置

提供键值存储、事务支持、快照和恢复功能，用于管理框架配置数据。基于SQLite实现持久化存储，支持复杂数据类型和原子操作。

## API 文档

### 基本操作
#### get(key: str, default: Any = None) -> Any
获取配置项的值。
- 参数:
  - key: 配置项键名
  - default: 如果键不存在时返回的默认值
- 返回:
  - Any: 配置项的值，如果是JSON格式则自动解析为Python对象
- 示例:
```python
# 获取基本配置
timeout = sdk.env.get("network.timeout", 30)

# 获取结构化数据
user_settings = sdk.env.get("user.settings", {})
if "theme" in user_settings:
    apply_theme(user_settings["theme"])

# 条件获取
debug_mode = sdk.env.get("app.debug", False)
if debug_mode:
    enable_debug_features()
```

#### set(key: str, value: Any) -> bool
设置配置项的值。
- 参数:
  - key: 配置项键名
  - value: 配置项的值，复杂类型会自动序列化为JSON
- 返回:
  - bool: 操作是否成功
- 示例:
```python
# 设置基本配置
sdk.env.set("app.name", "MyApplication")

# 设置结构化数据
sdk.env.set("server.config", {
    "host": "localhost",
    "port": 8080,
    "workers": 4
})

# 更新现有配置
current_settings = sdk.env.get("user.settings", {})
current_settings["last_login"] = datetime.now().isoformat()
sdk.env.set("user.settings", current_settings)
```

#### delete(key: str) -> bool
删除配置项。
- 参数:
  - key: 要删除的配置项键名
- 返回:
  - bool: 操作是否成功
- 示例:
```python
# 删除临时配置
sdk.env.delete("temp.session")

# 条件删除
if not is_feature_enabled():
    sdk.env.delete("feature.config")

# 清理旧配置
for key in sdk.env.get_all_keys():
    if key.startswith("deprecated."):
        sdk.env.delete(key)
```

#### get_all_keys() -> list[str]
获取所有配置项的键名。
- 参数: 无
- 返回:
  - list[str]: 所有配置项的键名列表
- 示例:
```python
# 列出所有配置
all_keys = sdk.env.get_all_keys()
print(f"当前有 {len(all_keys)} 个配置项")

# 按前缀过滤
user_keys = [k for k in sdk.env.get_all_keys() if k.startswith("user.")]
print(f"用户相关配置: {user_keys}")

# 导出配置摘要
config_summary = {}
for key in sdk.env.get_all_keys():
    parts = key.split(".")
    if len(parts) > 1:
        category = parts[0]
        if category not in config_summary:
            config_summary[category] = 0
        config_summary[category] += 1
print("配置分类统计:", config_summary)
```

### 批量操作
#### get_multi(keys: list) -> dict
批量获取多个配置项的值。
- 参数:
  - keys: 要获取的配置项键名列表
- 返回:
  - dict: 键值对字典，只包含存在的键
- 示例:
```python
# 批量获取配置
settings = sdk.env.get_multi([
    "app.name", 
    "app.version", 
    "app.debug"
])
print(f"应用: {settings.get('app.name')} v{settings.get('app.version')}")

# 获取相关配置组
db_keys = ["database.host", "database.port", "database.user", "database.password"]
db_config = sdk.env.get_multi(db_keys)
connection = create_db_connection(**db_config)

# 配置存在性检查
required_keys = ["api.key", "api.endpoint", "api.version"]
config = sdk.env.get_multi(required_keys)
missing = [k for k in required_keys if k not in config]
if missing:
    raise ValueError(f"缺少必要配置: {missing}")
```

#### set_multi(items: dict) -> bool
批量设置多个配置项的值。
- 参数:
  - items: 要设置的键值对字典
- 返回:
  - bool: 操作是否成功
- 示例:
```python
# 批量设置基本配置
sdk.env.set_multi({
    "app.name": "MyApp",
    "app.version": "1.0.0",
    "app.debug": True
})

# 更新系统设置
sdk.env.set_multi({
    "system.max_connections": 100,
    "system.timeout": 30,
    "system.retry_count": 3
})

# 从外部配置导入
import json
with open("config.json", "r") as f:
    external_config = json.load(f)
    
# 转换为扁平结构
flat_config = {}
for section, values in external_config.items():
    for key, value in values.items():
        flat_config[f"{section}.{key}"] = value
        
sdk.env.set_multi(flat_config)
```

#### delete_multi(keys: list) -> bool
批量删除多个配置项。
- 参数:
  - keys: 要删除的配置项键名列表
- 返回:
  - bool: 操作是否成功
- 示例:
```python
# 批量删除临时配置
temp_keys = [k for k in sdk.env.get_all_keys() if k.startswith("temp.")]
sdk.env.delete_multi(temp_keys)

# 删除特定模块的所有配置
module_keys = [k for k in sdk.env.get_all_keys() if k.startswith("module_name.")]
sdk.env.delete_multi(module_keys)

# 清理测试数据
test_keys = ["test.user", "test.data", "test.results"]
sdk.env.delete_multi(test_keys)
```

### 事务管理
#### transaction() -> contextmanager
创建事务上下文，确保多个操作的原子性。
- 参数: 无
- 返回:
  - contextmanager: 事务上下文管理器
- 示例:
```python
# 基本事务
with sdk.env.transaction():
    sdk.env.set("user.id", user_id)
    sdk.env.set("user.name", user_name)
    sdk.env.set("user.email", user_email)

# 带有条件检查的事务
def update_user_safely(user_id, new_data):
    with sdk.env.transaction():
        current = sdk.env.get(f"user.{user_id}", None)
        if not current:
            return False
            
        for key, value in new_data.items():
            sdk.env.set(f"user.{user_id}.{key}", value)
        
        sdk.env.set(f"user.{user_id}.updated_at", time.time())
    return True

# 复杂业务逻辑事务
def transfer_credits(from_user, to_user, amount):
    with sdk.env.transaction():
        # 检查余额
        from_balance = sdk.env.get(f"user.{from_user}.credits", 0)
        if from_balance < amount:
            raise ValueError("余额不足")
            
        # 更新余额
        sdk.env.set(f"user.{from_user}.credits", from_balance - amount)
        
        to_balance = sdk.env.get(f"user.{to_user}.credits", 0)
        sdk.env.set(f"user.{to_user}.credits", to_balance + amount)
        
        # 记录交易
        transaction_id = str(uuid.uuid4())
        sdk.env.set(f"transaction.{transaction_id}", {
            "from": from_user,
            "to": to_user,
            "amount": amount,
            "timestamp": time.time()
        })
```

### 快照管理
#### snapshot(name: str = None) -> str
创建数据库快照。
- 参数:
  - name: 快照名称，默认使用当前时间戳
- 返回:
  - str: 快照文件路径
- 示例:
```python
# 创建命名快照
sdk.env.snapshot("before_migration")

# 创建定期备份
def create_daily_backup():
    date_str = datetime.now().strftime("%Y%m%d")
    return sdk.env.snapshot(f"daily_{date_str}")

# 在重要操作前创建快照
def safe_operation():
    snapshot_path = sdk.env.snapshot("pre_operation")
    try:
        perform_risky_operation()
    except Exception as e:
        sdk.logger.error(f"操作失败: {e}")
        sdk.env.restore(snapshot_path)
        return False
    return True
```

#### restore(snapshot_name: str) -> bool
从快照恢复数据库。
- 参数:
  - snapshot_name: 快照名称或路径
- 返回:
  - bool: 恢复是否成功
- 示例:
```python
# 恢复到指定快照
success = sdk.env.restore("before_migration")
if success:
    print("成功恢复到之前的状态")
else:
    print("恢复失败")

# 回滚到最近的每日备份
def rollback_to_last_daily():
    snapshots = sdk.env.list_snapshots()
    daily_snapshots = [s for s in snapshots if s[0].startswith("daily_")]
    if daily_snapshots:
        latest = daily_snapshots[0]  # 列表已按时间排序
        return sdk.env.restore(latest[0])
    return False

# 灾难恢复
def disaster_recovery():
    snapshots = sdk.env.list_snapshots()
    if not snapshots:
        print("没有可用的快照")
        return False
        
    print("可用快照:")
    for i, (name, date, size) in enumerate(snapshots):
        print(f"{i+1}. {name} - {date} ({size/1024:.1f} KB)")
        
    choice = input("选择要恢复的快照编号: ")
    try:
        index = int(choice) - 1
        if 0 <= index < len(snapshots):
            return sdk.env.restore(snapshots[index][0])
    except ValueError:
        pass
    return False
```

#### list_snapshots() -> list
列出所有可用的快照。
- 参数: 无
- 返回:
  - list: 快照信息列表，每项包含(名称, 创建时间, 大小)
- 示例:
```python
# 列出所有快照
snapshots = sdk.env.list_snapshots()
print(f"共有 {len(snapshots)} 个快照")

# 显示快照详情
for name, date, size in snapshots:
    print(f"名称: {name}")
    print(f"创建时间: {date}")
    print(f"大小: {size/1024:.2f} KB")
    print("-" * 30)

# 查找特定快照
def find_snapshot(prefix):
    snapshots = sdk.env.list_snapshots()
    return [s for s in snapshots if s[0].startswith(prefix)]
```

#### delete_snapshot(name: str) -> bool
删除指定的快照。
- 参数:
  - name: 要删除的快照名称
- 返回:
  - bool: 删除是否成功
- 示例:
```python
# 删除指定快照
sdk.env.delete_snapshot("old_backup")

# 清理过期快照
def cleanup_old_snapshots(days=30):
    snapshots = sdk.env.list_snapshots()
    cutoff = datetime.now() - timedelta(days=days)
    for name, date, _ in snapshots:
        if date < cutoff:
            sdk.env.delete_snapshot(name)
            print(f"已删除过期快照: {name}")

# 保留最新的N个快照
def retain_latest_snapshots(count=5):
    snapshots = sdk.env.list_snapshots()
    if len(snapshots) > count:
        for name, _, _ in snapshots[count:]:
            sdk.env.delete_snapshot(name)
```

## 最佳实践

1. 配置组织
```python
# 使用层次结构组织配置
sdk.env.set("app.server.host", "localhost")
sdk.env.set("app.server.port", 8080)
sdk.env.set("app.database.url", "postgresql://localhost/mydb")

# 使用命名空间避免冲突
sdk.env.set("module1.config.timeout", 30)
sdk.env.set("module2.config.timeout", 60)
```

2. 事务使用
```python
# 确保数据一致性
def update_configuration(config_data):
    with sdk.env.transaction():
        # 验证
        for key, value in config_data.items():
            if not validate_config(key, value):
                raise ValueError(f"无效的配置: {key}")
                
        # 更新
        for key, value in config_data.items():
            sdk.env.set(key, value)
            
        # 记录更新
        sdk.env.set("config.last_updated", time.time())
```

3. 快照管理
```python
# 定期创建快照
def schedule_backups():
    # 每日快照
    if not sdk.env.snapshot(f"daily_{datetime.now().strftime('%Y%m%d')}"):
        sdk.logger.error("每日快照创建失败")
        
    # 清理旧快照
    cleanup_old_snapshots(days=30)
    
# 自动备份重要操作
def safe_bulk_update(updates):
    snapshot_name = f"pre_update_{time.time()}"
    sdk.env.snapshot(snapshot_name)
    
    try:
        with sdk.env.transaction():
            for key, value in updates.items():
                sdk.env.set(key, value)
    except Exception as e:
        sdk.logger.error(f"批量更新失败: {e}")
        sdk.env.restore(snapshot_name)
        raise
```

## logger (source: [ErisPulse/logger.py](https://raw.githubusercontent.com/ErisPulse/ErisPulse/refs/heads/main/ErisPulse/logger.py))

# 日志系统

提供模块化、多级别的日志记录功能，支持内存存储和文件输出。实现了模块级别的日志控制、彩色输出和灵活的存储选项。

## API 文档

### 基本日志操作

以debug为例：
> 此外，还有其他级别的日志记录函数，如info, warning, error, critical等，用法相同。

debug(msg: str, *args, **kwargs) -> None

记录调试级别的日志信息。
- 参数:
  - msg: 日志消息
  - *args: 传递给底层logger的位置参数
  - **kwargs: 传递给底层logger的关键字参数
- 返回:
  - None
- 示例:

```python
sdk.logger.debug("这是一条日志")
```

### 日志级别控制
#### set_level(level: str) -> None
设置全局日志级别。
- 参数:
  - level: 日志级别，可选值为 "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
- 返回:
  - None
- 示例:
```python
# 设置为调试级别
sdk.logger.set_level("DEBUG")

# 设置为生产环境级别
sdk.logger.set_level("INFO")

# 根据环境设置日志级别
if is_production():
    sdk.logger.set_level("WARNING")
else:
    sdk.logger.set_level("DEBUG")
```

#### set_module_level(module_name: str, level: str) -> bool
设置特定模块的日志级别。
- 参数:
  - module_name: 模块名称
  - level: 日志级别，可选值为 "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
- 返回:
  - bool: 设置是否成功
- 示例:
```python
# 为特定模块设置详细日志
sdk.logger.set_module_level("NetworkModule", "DEBUG")

# 为敏感模块设置更高级别
sdk.logger.set_module_level("AuthModule", "WARNING")

# 根据配置设置模块日志级别
for module, level in config.get("logging", {}).items():
    success = sdk.logger.set_module_level(module, level)
    if not success:
        print(f"无法为模块 {module} 设置日志级别 {level}")
```

### 日志存储和输出
#### set_output_file(path: str | list) -> None
设置日志输出文件。
- 参数:
  - path: 日志文件路径，可以是单个字符串或路径列表
- 返回:
  - None
- 异常:
  - 如果无法设置日志文件，会抛出异常
- 示例:
```python
# 设置单个日志文件
sdk.logger.set_output_file("app.log")

# 设置多个日志文件
sdk.logger.set_output_file(["app.log", "debug.log"])

# 使用日期命名日志文件
from datetime import datetime
log_file = f"logs/app_{datetime.now().strftime('%Y%m%d')}.log"
sdk.logger.set_output_file(log_file)
```

#### save_logs(path: str | list) -> None
保存内存中的日志到文件。
- 参数:
  - path: 保存路径，可以是单个字符串或路径列表
- 返回:
  - None
- 异常:
  - 如果无法保存日志，会抛出异常
- 示例:
```python
# 保存到单个文件
sdk.logger.save_logs("saved_logs.txt")

# 保存到多个文件
sdk.logger.save_logs(["main_log.txt", "backup_log.txt"])

# 在应用退出前保存日志
import atexit
atexit.register(lambda: sdk.logger.save_logs("final_logs.txt"))
```

## raiserr (source: [ErisPulse/raiserr.py](https://raw.githubusercontent.com/ErisPulse/ErisPulse/refs/heads/main/ErisPulse/raiserr.py))

# 错误管理系统

提供错误类型注册、抛出和管理功能，集成全局异常处理。支持自定义错误类型、错误链追踪和全局异常捕获。

## API 文档

### 错误注册
#### register(name: str, doc: str = "", base: type = Exception) -> type
注册新的错误类型。
- 参数:
  - name: 错误类型名称
  - doc: 错误描述文档
  - base: 基础异常类，默认为Exception
- 返回:
  - type: 注册的错误类型类
- 示例:
```python
# 注册一个简单错误
sdk.raiserr.register("SimpleError", "简单的错误类型")

# 注册带有自定义基类的错误
class CustomBase(Exception):
    pass
sdk.raiserr.register("AdvancedError", "高级错误", CustomBase)
```

#### info(name: str = None) -> dict | None
获取错误类型信息。
- 参数:
  - name: 错误类型名称，如果为None则返回所有错误类型信息
- 返回:
  - dict: 包含错误类型信息的字典，包括类型名、文档和类引用
  - None: 如果指定的错误类型不存在
- 示例:
```python
# 获取特定错误信息
error_info = sdk.raiserr.info("SimpleError")
print(f"错误类型: {error_info['type']}")
print(f"错误描述: {error_info['doc']}")

# 获取所有注册的错误信息
all_errors = sdk.raiserr.info()
for name, info in all_errors.items():
    print(f"{name}: {info['doc']}")
```

### 错误抛出
#### ErrorType(msg: str, exit: bool = False)
动态生成的错误抛出函数。
- 参数:
  - msg: 错误消息
  - exit: 是否在抛出错误后退出程序
- 示例:
```python
# 抛出不退出的错误
sdk.raiserr.SimpleError("操作失败")

# 抛出导致程序退出的错误
sdk.raiserr.CriticalError("致命错误", exit=True)

# 带有异常捕获的使用方式
try:
    sdk.raiserr.ValidationError("数据验证失败")
except Exception as e:
    print(f"捕获到错误: {e}")
```

## util (source: [ErisPulse/util.py](https://raw.githubusercontent.com/ErisPulse/ErisPulse/refs/heads/main/ErisPulse/util.py))

# 工具函数集合

提供各种实用工具函数和装饰器，简化开发流程。

## API 文档
### 拓扑排序：
    - topological_sort(elements, dependencies, error): 拓扑排序依赖关系
    - show_topology(): 可视化模块依赖关系

### 装饰器：
    - @cache: 缓存函数结果
    - @run_in_executor: 将同步函数转为异步
    - @retry(max_attempts=3, delay=1): 失败自动重试

### 异步执行：
    - ExecAsync(async_func, *args, **kwargs): 异步执行函数

### 示例用法：

```
from ErisPulse import sdk

# 拓扑排序
sorted_modules = sdk.util.topological_sort(modules, dependencies, error)

# 缓存装饰器
@sdk.util.cache
def expensive_operation(param):
    return heavy_computation(param)
    
# 异步执行
@sdk.util.run_in_executor
def sync_task():
    pass
    
# 重试机制
@sdk.util.retry(max_attempts=3, delay=1)
def unreliable_operation():
    pass
```

