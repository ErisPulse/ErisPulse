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

## 核心功能
1. 适配器基类定义
2. 链式消息发送DSL
3. 适配器注册和管理
4. 事件处理系统
5. 中间件支持

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

## 最佳实践

1. 适配器实现
```python
class MyPlatformAdapter(sdk.BaseAdapter):
    class Send(sdk.BaseAdapter.Send):
        # 实现基本消息类型
        def Text(self, text: str):
            return asyncio.create_task(
                self._adapter.call_api(
                    endpoint="/send",
                    content=text,
                    recvId=self._target_id,
                    recvType=self._target_type
                )
            )
            
        # 添加自定义消息类型
        def Image(self, file: bytes):
            return asyncio.create_task(
                self._adapter.call_api(
                    endpoint="/send_image",
                    file=file,
                    recvId=self._target_id,
                    recvType=self._target_type
                )
            )
    
    async def call_api(self, endpoint: str, **params):
        # 实现API调用逻辑
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_base}{endpoint}",
                json=params
            ) as response:
                return await response.json()
                
    async def start(self):
        # 初始化连接
        self.client = await self._create_client()
        # 启动事件监听
        asyncio.create_task(self._listen_events())
        
    async def shutdown(self):
        # 清理资源
        if self.client:
            await self.client.close()
```

2. 事件处理
```python
# 注册事件处理器
adapter = MyPlatformAdapter()

@adapter.on("message")
async def handle_message(data):
    # 消息处理逻辑
    if data["type"] == "text":
        await process_text_message(data)
    elif data["type"] == "image":
        await process_image_message(data)

# 使用中间件
@adapter.middleware
async def auth_middleware(data):
    if not verify_token(data.get("token")):
        return None
    return data

@adapter.middleware
async def log_middleware(data):
    sdk.logger.info(f"处理事件: {data}")
    return data
```

3. 消息发送
```python
# 基本消息发送
async def send_welcome(user_id: str):
    await sdk.adapter.Platform.Send.To("user", user_id).Text("欢迎！")

# 复杂消息处理
async def process_group_notification(group_id: str, event: dict):
    # 发送格式化消息
    message = format_notification(event)
    await sdk.adapter.Platform.Send.To("group", group_id).Text(message)
    
    # 发送附加文件
    if event.get("has_attachment"):
        file_data = await get_attachment(event["attachment_id"])
        await sdk.adapter.Platform.Send.To("group", group_id).File(file_data)
```

## 注意事项

1. 适配器实现
   - 确保正确实现所有抽象方法
   - 处理所有可能的异常情况
   - 实现适当的重试机制
   - 注意资源的正确释放

2. 事件处理
   - 避免在事件处理器中执行长时间操作
   - 使用适当的错误处理
   - 考虑事件处理的顺序性
   - 合理使用中间件过滤机制

3. 消息发送
   - 实现消息发送的限流机制
   - 处理发送失败的情况
   - 注意消息格式的平台兼容性
   - 大文件传输时考虑分片

4. 生命周期管理
   - 确保适配器正确启动和关闭
   - 处理意外断开的情况
   - 实现自动重连机制
   - 注意资源泄漏问题

## db (source: [ErisPulse/db.py](https://raw.githubusercontent.com/ErisPulse/ErisPulse/refs/heads/main/ErisPulse/db.py))

# 环境配置

提供键值存储、事务支持、快照和恢复功能，用于管理框架配置数据。基于SQLite实现持久化存储，支持复杂数据类型和原子操作。

## 核心功能
1. 键值存储
2. 事务支持
3. 数据库快照
4. 自动备份
5. 配置文件集成

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

## 注意事项

1. 性能优化
   - 使用批量操作代替多次单独操作
   - 合理使用事务减少数据库操作次数
   - 避免存储过大的值，考虑分片存储

2. 数据安全
   - 定期创建快照备份重要数据
   - 使用事务确保数据一致性
   - 不要存储敏感信息（如密码）的明文

3. 配置管理
   - 使用有意义的键名和层次结构
   - 记录配置的更新历史
   - 定期清理不再使用的配置

4. 错误处理
   - 所有数据库操作都应该有错误处理
   - 重要操作前创建快照以便回滚
   - 记录所有关键操作的日志

## logger (source: [ErisPulse/logger.py](https://raw.githubusercontent.com/ErisPulse/ErisPulse/refs/heads/main/ErisPulse/logger.py))

# 日志系统

提供模块化、多级别的日志记录功能，支持内存存储和文件输出。实现了模块级别的日志控制、彩色输出和灵活的存储选项。

## 核心功能
1. 多级别日志记录
2. 模块级别日志控制
3. 内存日志存储
4. 文件输出支持
5. 自动调用者识别
6. 异常捕获装饰器

## API 文档

### 基本日志操作
#### debug(msg: str, *args, **kwargs) -> None
记录调试级别的日志信息。
- 参数:
  - msg: 日志消息
  - *args: 传递给底层logger的位置参数
  - **kwargs: 传递给底层logger的关键字参数
- 返回:
  - None
- 示例:
```python
# 基本调试信息
sdk.logger.debug("初始化配置")

# 带有变量的调试信息
config_value = get_config("timeout")
sdk.logger.debug(f"读取配置: timeout = {config_value}")

# 在条件下记录调试信息
if is_development_mode():
    sdk.logger.debug("开发模式下的详细信息: %s", detailed_info)
```

#### info(msg: str, *args, **kwargs) -> None
记录信息级别的日志信息。
- 参数:
  - msg: 日志消息
  - *args: 传递给底层logger的位置参数
  - **kwargs: 传递给底层logger的关键字参数
- 返回:
  - None
- 示例:
```python
# 基本信息记录
sdk.logger.info("应用已启动")

# 带有上下文的信息
user_count = get_active_users()
sdk.logger.info(f"当前活跃用户: {user_count}")

# 记录操作结果
sdk.logger.info("数据导入完成，共处理 %d 条记录", record_count)
```

#### warning(msg: str, *args, **kwargs) -> None
记录警告级别的日志信息。
- 参数:
  - msg: 日志消息
  - *args: 传递给底层logger的位置参数
  - **kwargs: 传递给底层logger的关键字参数
- 返回:
  - None
- 示例:
```python
# 基本警告信息
sdk.logger.warning("配置文件未找到，使用默认配置")

# 性能警告
if response_time > threshold:
    sdk.logger.warning(f"响应时间过长: {response_time}ms > {threshold}ms")

# 资源使用警告
memory_usage = get_memory_usage()
if memory_usage > 80:
    sdk.logger.warning("内存使用率高: %d%%", memory_usage)
```

#### error(msg: str, *args, **kwargs) -> None
记录错误级别的日志信息。
- 参数:
  - msg: 日志消息
  - *args: 传递给底层logger的位置参数
  - **kwargs: 传递给底层logger的关键字参数
- 返回:
  - None
- 示例:
```python
# 基本错误信息
sdk.logger.error("数据库连接失败")

# 带有异常信息的错误
try:
    process_data()
except Exception as e:
    sdk.logger.error(f"数据处理错误: {str(e)}")

# 带有错误代码的错误
sdk.logger.error("API请求失败，状态码: %d, 错误: %s", status_code, error_message)
```

#### critical(msg: str, *args, **kwargs) -> None
记录致命错误级别的日志信息，并终止程序。
- 参数:
  - msg: 日志消息
  - *args: 传递给底层logger的位置参数
  - **kwargs: 传递给底层logger的关键字参数
- 返回:
  - None (程序会终止)
- 示例:
```python
# 致命错误记录
if not database_connection:
    sdk.logger.critical("无法连接到主数据库，应用无法继续运行")

# 安全相关的致命错误
if security_breach_detected():
    sdk.logger.critical("检测到安全漏洞，强制关闭系统")

# 资源耗尽的致命错误
if disk_space < min_required:
    sdk.logger.critical("磁盘空间不足 (%dMB)，无法继续运行", disk_space)
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

### 异常捕获 (准备弃用)
#### catch(func_or_level=None, level="error")
异常捕获装饰器。
- 参数:
  - func_or_level: 要装饰的函数或日志级别
  - level: 捕获异常时使用的日志级别
- 返回:
  - function: 装饰后的函数
- 注意:
  - 此功能已集成到 raiserr 模块中，建议使用 raiserr 进行异常处理
- 示例:
```python
# 基本用法 (不推荐，请使用raiserr)
@sdk.logger.catch
def risky_function():
    # 可能抛出异常的代码
    process_data()

# 指定日志级别 (不推荐，请使用raiserr)
@sdk.logger.catch(level="critical")
def very_important_function():
    # 关键操作
    update_database()
```

## 最佳实践
1. 日志级别使用
```python
# 开发环境使用详细日志
if is_development():
    sdk.logger.set_level("DEBUG")
    sdk.logger.debug("详细的调试信息")
else:
    sdk.logger.set_level("INFO")
    
# 性能敏感模块使用更高级别
sdk.logger.set_module_level("PerformanceModule", "WARNING")
```

2. 结构化日志信息
```python
# 使用一致的格式
def log_api_request(endpoint, method, status, duration):
    sdk.logger.info(
        f"API请求: {method} {endpoint} - 状态: {status}, 耗时: {duration}ms"
    )

# 包含关键上下文
def log_user_action(user_id, action, result):
    sdk.logger.info(
        f"用户操作: [用户:{user_id}] {action} - 结果: {result}"
    )
```

3. 日志文件管理
```python
# 按日期分割日志文件
from datetime import datetime
import os

def setup_logging():
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(log_dir, f"app_{today}.log")
    
    sdk.logger.set_output_file(log_file)
    sdk.logger.info(f"日志文件已设置: {log_file}")
```

4. 异常处理与日志
```python
# 推荐方式：使用raiserr结合logger
def process_with_logging():
    try:
        result = perform_operation()
        sdk.logger.info(f"操作成功: {result}")
        return result
    except Exception as e:
        sdk.logger.error(f"操作失败: {str(e)}")
        sdk.raiserr.OperationError(f"处理失败: {str(e)}")
```

## 注意事项
1. 日志级别选择
   - DEBUG: 详细的调试信息，仅在开发环境使用
   - INFO: 常规操作信息，适用于生产环境
   - WARNING: 潜在问题或异常情况
   - ERROR: 错误但不影响整体功能
   - CRITICAL: 致命错误，导致程序终止

2. 性能考虑
   - 避免在高频循环中记录过多日志
   - 使用适当的日志级别减少不必要的输出
   - 考虑日志文件大小和轮转策略

3. 敏感信息保护
   - 不要记录密码、令牌等敏感信息
   - 在记录用户数据前进行脱敏处理
   - 遵循数据保护法规要求

4. 迁移建议
   - 从catch装饰器迁移到raiserr模块
   - 使用结构化的错误处理方式
   - 结合日志和错误管理实现完整的异常处理流程

## mods (source: [ErisPulse/mods.py](https://raw.githubusercontent.com/ErisPulse/ErisPulse/refs/heads/main/ErisPulse/mods.py))

# 模块管理系统

提供模块的注册、状态管理和依赖解析功能。支持模块信息存储、状态切换和批量操作。

## 核心功能
1. 模块信息管理
2. 模块状态控制
3. 批量模块操作
4. 存储前缀自定义
5. 模块依赖管理

## API 文档

### 模块状态管理
#### set_module_status(module_name: str, status: bool) -> None
设置模块的启用状态。
- 参数:
  - module_name: 模块名称
  - status: 模块状态，True为启用，False为禁用
- 返回:
  - None
- 示例:
```python
# 启用模块
sdk.mods.set_module_status("MyModule", True)

# 禁用模块
sdk.mods.set_module_status("MyModule", False)

# 条件性启用模块
if check_dependencies():
    sdk.mods.set_module_status("MyModule", True)
else:
    sdk.logger.warning("依赖检查失败，模块未启用")
```

#### get_module_status(module_name: str) -> bool
获取模块的启用状态。
- 参数:
  - module_name: 模块名称
- 返回:
  - bool: 模块状态，True为启用，False为禁用
- 示例:
```python
# 检查模块是否启用
if sdk.mods.get_module_status("MyModule"):
    print("模块已启用")
else:
    print("模块已禁用")
    
# 在条件中使用
if sdk.mods.get_module_status("DatabaseModule") and sdk.mods.get_module_status("NetworkModule"):
    start_application()
```

### 模块信息管理
#### set_module(module_name: str, module_info: dict) -> None
设置模块信息。
- 参数:
  - module_name: 模块名称
  - module_info: 模块信息字典，包含模块的元数据和配置
- 返回:
  - None
- 示例:
```python
# 设置基本模块信息
sdk.mods.set_module("MyModule", {
    "status": True,
    "info": {
        "meta": {
            "name": "MyModule",
            "version": "1.0.0",
            "description": "示例模块",
            "author": "开发者"
        },
        "dependencies": {
            "requires": ["CoreModule"],
            "optional": ["OptionalModule"],
            "pip": ["requests", "numpy"]
        }
    }
})

# 更新现有模块信息
module_info = sdk.mods.get_module("MyModule")
module_info["info"]["meta"]["version"] = "1.1.0"
sdk.mods.set_module("MyModule", module_info)
```

#### get_module(module_name: str) -> dict | None
获取模块信息。
- 参数:
  - module_name: 模块名称
- 返回:
  - dict: 模块信息字典
  - None: 如果模块不存在
- 示例:
```python
# 获取模块信息
module_info = sdk.mods.get_module("MyModule")
if module_info:
    print(f"模块版本: {module_info['info']['meta']['version']}")
    print(f"模块描述: {module_info['info']['meta']['description']}")
    print(f"模块状态: {'启用' if module_info['status'] else '禁用'}")
else:
    print("模块不存在")
```

#### get_all_modules() -> dict
获取所有模块信息。
- 参数: 无
- 返回:
  - dict: 包含所有模块信息的字典，键为模块名，值为模块信息
- 示例:
```python
# 获取所有模块
all_modules = sdk.mods.get_all_modules()

# 统计启用和禁用的模块
enabled_count = 0
disabled_count = 0
for name, info in all_modules.items():
    if info.get("status", False):
        enabled_count += 1
    else:
        disabled_count += 1
        
print(f"已启用模块: {enabled_count}")
print(f"已禁用模块: {disabled_count}")

# 查找特定类型的模块
adapters = [name for name, info in all_modules.items() 
           if "adapter" in info.get("info", {}).get("meta", {}).get("tags", [])]
print(f"适配器模块: {adapters}")
```

#### update_module(module_name: str, module_info: dict) -> None
更新模块信息。
- 参数:
  - module_name: 模块名称
  - module_info: 更新后的模块信息字典
- 返回:
  - None
- 示例:
```python
# 更新模块版本
module_info = sdk.mods.get_module("MyModule")
module_info["info"]["meta"]["version"] = "1.2.0"
sdk.mods.update_module("MyModule", module_info)

# 添加新的配置项
module_info = sdk.mods.get_module("MyModule")
if "config" not in module_info:
    module_info["config"] = {}
module_info["config"]["debug_mode"] = True
sdk.mods.update_module("MyModule", module_info)
```

#### remove_module(module_name: str) -> bool
删除模块。
- 参数:
  - module_name: 模块名称
- 返回:
  - bool: 是否成功删除
- 示例:
```python
# 删除模块
if sdk.mods.remove_module("OldModule"):
    print("模块已成功删除")
else:
    print("模块不存在或删除失败")
    
# 条件删除
if sdk.mods.get_module_status("TestModule") and is_test_environment():
    sdk.mods.remove_module("TestModule")
    print("测试模块已在生产环境中移除")
```

#### set_all_modules(modules_info: Dict[str, dict]) -> None
批量设置多个模块信息。
- 参数:
  - modules_info: 模块信息字典的字典，键为模块名，值为模块信息
- 返回:
  - None
- 示例:
```python
# 批量设置模块
sdk.mods.set_all_modules({
    "Module1": {
        "status": True,
        "info": {"meta": {"name": "Module1", "version": "1.0.0"}}
    },
    "Module2": {
        "status": True,
        "info": {"meta": {"name": "Module2", "version": "1.0.0"}}
    }
})

# 从配置文件加载模块信息
import json
with open("modules_config.json", "r") as f:
    modules_config = json.load(f)
sdk.mods.set_all_modules(modules_config)
```

### 前缀管理
#### update_prefixes(module_prefix: str = None, status_prefix: str = None) -> None
更新存储前缀。
- 参数:
  - module_prefix: 模块存储前缀
  - status_prefix: 状态存储前缀
- 返回:
  - None
- 示例:
```python
# 更新模块前缀
sdk.mods.update_prefixes(module_prefix="custom.module.")

# 更新状态前缀
sdk.mods.update_prefixes(status_prefix="custom.status.")

# 同时更新两个前缀
sdk.mods.update_prefixes(
    module_prefix="app.modules.",
    status_prefix="app.status."
)
```

#### module_prefix 属性
获取当前模块存储前缀。
- 返回:
  - str: 当前模块存储前缀
- 示例:
```python
# 获取当前模块前缀
prefix = sdk.mods.module_prefix
print(f"当前模块前缀: {prefix}")

# 在自定义存储操作中使用
custom_key = f"{sdk.mods.module_prefix}custom.{module_name}"
sdk.env.set(custom_key, custom_data)
```

#### status_prefix 属性
获取当前状态存储前缀。
- 返回:
  - str: 当前状态存储前缀
- 示例:
```python
# 获取当前状态前缀
prefix = sdk.mods.status_prefix
print(f"当前状态前缀: {prefix}")

# 在自定义状态操作中使用
custom_status_key = f"{sdk.mods.status_prefix}custom.{module_name}"
sdk.env.set(custom_status_key, is_active)
```

## 最佳实践
1. 模块信息结构
```python
# 推荐的模块信息结构
module_info = {
    "status": True,  # 模块启用状态
    "info": {
        "meta": {
            "name": "ModuleName",  # 模块名称
            "version": "1.0.0",    # 模块版本
            "description": "模块描述",
            "author": "作者",
            "license": "MIT",
            "tags": ["tag1", "tag2"]  # 分类标签
        },
        "dependencies": {
            "requires": ["RequiredModule1"],  # 必需依赖
            "optional": ["OptionalModule1"],  # 可选依赖
            "pip": ["package1", "package2"]   # pip包依赖
        }
    },
    "config": {  # 模块配置（可选）
        "setting1": "value1",
        "setting2": "value2"
    }
}
```

2. 模块状态管理
```python
# 根据条件启用/禁用模块
def toggle_modules_by_environment():
    env_type = get_environment_type()
    
    # 开发环境启用调试模块
    if env_type == "development":
        sdk.mods.set_module_status("DebugModule", True)
        sdk.mods.set_module_status("PerformanceModule", False)
    
    # 生产环境禁用调试模块，启用性能模块
    elif env_type == "production":
        sdk.mods.set_module_status("DebugModule", False)
        sdk.mods.set_module_status("PerformanceModule", True)
```

3. 模块依赖检查
```python
# 检查模块依赖
def check_module_dependencies(module_name):
    module_info = sdk.mods.get_module(module_name)
    if not module_info:
        return False
        
    dependencies = module_info.get("info", {}).get("dependencies", {}).get("requires", [])
    
    for dep in dependencies:
        dep_info = sdk.mods.get_module(dep)
        if not dep_info or not dep_info.get("status", False):
            sdk.logger.warning(f"模块 {module_name} 的依赖 {dep} 未启用或不存在")
            return False
            
    return True
```

## 注意事项
1. 模块名称应唯一，避免冲突
2. 模块信息结构应保持一致，便于管理
3. 更新模块信息前应先获取现有信息，避免覆盖
4. 批量操作时注意性能影响
5. 自定义前缀时确保不与系统其他键冲突

## raiserr (source: [ErisPulse/raiserr.py](https://raw.githubusercontent.com/ErisPulse/ErisPulse/refs/heads/main/ErisPulse/raiserr.py))

# 错误管理系统

提供错误类型注册、抛出和管理功能，集成全局异常处理。支持自定义错误类型、错误链追踪和全局异常捕获。

## 核心功能
1. 错误类型注册和管理
2. 动态错误抛出
3. 全局异常处理
4. 错误信息追踪
5. 异步错误处理

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

### 全局异常处理
#### global_exception_handler(exc_type: type, exc_value: Exception, exc_traceback: traceback)
全局同步异常处理器。
- 参数:
  - exc_type: 异常类型
  - exc_value: 异常值
  - exc_traceback: 异常追踪信息
- 示例:
```python
# 系统会自动捕获未处理的异常
def risky_operation():
    raise Exception("未处理的异常")
    
# 异常会被global_exception_handler捕获并处理
risky_operation()
```

#### async_exception_handler(loop: asyncio.AbstractEventLoop, context: dict)
全局异步异常处理器。
- 参数:
  - loop: 事件循环实例
  - context: 异常上下文信息
- 示例:
```python
async def async_operation():
    raise Exception("异步操作错误")
    
# 异常会被async_exception_handler捕获并处理
asyncio.create_task(async_operation())
```

## 最佳实践
1. 错误类型注册
```python
# 为特定功能模块注册错误类型
sdk.raiserr.register("DatabaseError", "数据库操作错误")
sdk.raiserr.register("NetworkError", "网络连接错误")
sdk.raiserr.register("ValidationError", "数据验证错误")

# 使用继承关系组织错误类型
class ModuleError(Exception):
    pass
sdk.raiserr.register("ConfigError", "配置错误", ModuleError)
sdk.raiserr.register("PluginError", "插件错误", ModuleError)
```

2. 错误处理流程
```python
def process_data(data):
    try:
        if not data:
            sdk.raiserr.ValidationError("数据不能为空")
        if not isinstance(data, dict):
            sdk.raiserr.ValidationError("数据必须是字典类型")
            
        # 处理数据...
        
    except Exception as e:
        # 错误会被自动记录并处理
        sdk.raiserr.ProcessingError(f"数据处理失败: {str(e)}")
```

3. 异步环境使用
```python
async def async_task():
    try:
        result = await some_async_operation()
        if not result.success:
            sdk.raiserr.AsyncOperationError("异步操作失败")
    except Exception as e:
        # 异步错误会被async_exception_handler捕获
        raise
```

## 注意事项
1. 错误类型命名应具有描述性，便于理解错误来源
2. 错误消息应包含足够的上下文信息，便于调试
3. 适当使用exit参数，只在致命错误时设置为True
4. 避免在全局异常处理器中执行耗时操作
5. 确保异步代码中的错误能够被正确捕获和处理

## util (source: [ErisPulse/util.py](https://raw.githubusercontent.com/ErisPulse/ErisPulse/refs/heads/main/ErisPulse/util.py))

# 工具函数集合

提供各种实用工具函数和装饰器，简化开发流程。包括依赖关系处理、性能优化、异步执行和错误重试等功能。

## 核心功能
1. 依赖关系管理
2. 函数结果缓存
3. 异步执行支持
4. 自动重试机制
5. 可视化工具

## API 文档

### 依赖关系处理
#### topological_sort(elements: list, dependencies: dict, error: callable) -> list
对元素进行拓扑排序，解析依赖关系。
- 参数:
  - elements: 需要排序的元素列表
  - dependencies: 依赖关系字典，键为元素，值为该元素依赖的元素列表
  - error: 发生循环依赖时调用的错误处理函数
- 返回:
  - list: 排序后的元素列表
- 异常:
  - 当存在循环依赖时，调用error函数
- 示例:
```python
# 基本使用
modules = ["ModuleA", "ModuleB", "ModuleC"]
dependencies = {
    "ModuleB": ["ModuleA"],
    "ModuleC": ["ModuleB"]
}
sorted_modules = sdk.util.topological_sort(modules, dependencies, sdk.raiserr.CycleDependencyError)

# 复杂依赖处理
modules = ["Database", "Cache", "API", "UI"]
dependencies = {
    "Cache": ["Database"],
    "API": ["Database", "Cache"],
    "UI": ["API"]
}
try:
    sorted_modules = sdk.util.topological_sort(
        modules, 
        dependencies,
        sdk.raiserr.CycleDependencyError
    )
    print("加载顺序:", sorted_modules)
except Exception as e:
    print(f"依赖解析失败: {e}")
```

#### show_topology() -> str
可视化显示当前模块的依赖关系。
- 参数: 无
- 返回:
  - str: 格式化的依赖关系树文本
- 示例:
```python
# 显示所有模块依赖
topology = sdk.util.show_topology()
print(topology)

# 在日志中记录依赖关系
sdk.logger.info("模块依赖关系:\n" + sdk.util.show_topology())
```

### 性能优化装饰器
#### @cache
缓存函数调用结果的装饰器。
- 参数: 无
- 返回:
  - function: 被装饰的函数
- 示例:
```python
# 缓存计算密集型函数结果
@sdk.util.cache
def calculate_complex_data(param1: int, param2: str) -> dict:
    # 复杂计算...
    return result

# 缓存配置读取
@sdk.util.cache
def get_config(config_name: str) -> dict:
    return load_config_from_file(config_name)

# 带有可变参数的缓存
@sdk.util.cache
def process_data(*args, **kwargs) -> Any:
    return complex_processing(args, kwargs)
```

### 异步执行工具
#### @run_in_executor
将同步函数转换为异步执行的装饰器。
- 参数: 无
- 返回:
  - function: 异步包装的函数
- 示例:
```python
# 包装同步IO操作
@sdk.util.run_in_executor
def read_large_file(file_path: str) -> str:
    with open(file_path, 'r') as f:
        return f.read()

# 包装CPU密集型操作
@sdk.util.run_in_executor
def process_image(image_data: bytes) -> bytes:
    # 图像处理...
    return processed_data

# 在异步环境中使用
async def main():
    # 这些操作会在线程池中执行，不会阻塞事件循环
    file_content = await read_large_file("large_file.txt")
    processed_image = await process_image(image_data)
```

#### ExecAsync(async_func: Callable, *args, **kwargs) -> Any
在当前线程中执行异步函数。
- 参数:
  - async_func: 要执行的异步函数
  - *args: 传递给异步函数的位置参数
  - **kwargs: 传递给异步函数的关键字参数
- 返回:
  - Any: 异步函数的执行结果
- 示例:
```python
# 在同步环境中执行异步函数
async def fetch_data(url: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

# 同步环境中调用
result = sdk.util.ExecAsync(fetch_data, "https://api.example.com/data")

# 批量异步操作
async def process_multiple(items: list) -> list:
    results = []
    for item in items:
        result = await process_item(item)
        results.append(result)
    return results

# 在同步代码中执行
results = sdk.util.ExecAsync(process_multiple, items_list)
```

### 错误重试机制
#### @retry(max_attempts: int = 3, delay: int = 1)
为不稳定的操作添加自动重试机制的装饰器。
- 参数:
  - max_attempts: 最大重试次数，默认3次
  - delay: 重试间隔时间（秒），默认1秒
- 返回:
  - function: 包装了重试逻辑的函数
- 示例:
```python
# 基本重试
@sdk.util.retry()
def unstable_network_call() -> dict:
    return requests.get("https://api.example.com/data").json()

# 自定义重试参数
@sdk.util.retry(max_attempts=5, delay=2)
def connect_database() -> Connection:
    return create_database_connection()

# 带有条件的重试
@sdk.util.retry(max_attempts=3)
def process_with_retry(data: dict) -> bool:
    if not validate_data(data):
        raise ValueError("Invalid data")
    return process_data(data)
```

## 最佳实践
1. 依赖管理
```python
# 模块依赖定义
module_deps = {
    "core": [],
    "database": ["core"],
    "api": ["database"],
    "ui": ["api"]
}

# 验证并排序依赖
try:
    load_order = sdk.util.topological_sort(
        list(module_deps.keys()),
        module_deps,
        sdk.raiserr.CycleDependencyError
    )
    
    # 按顺序加载模块
    for module in load_order:
        load_module(module)
except Exception as e:
    sdk.logger.error(f"模块加载失败: {e}")
```

2. 性能优化
```python
# 合理使用缓存
@sdk.util.cache
def get_user_preferences(user_id: str) -> dict:
    return database.fetch_user_preferences(user_id)

# 异步处理耗时操作
@sdk.util.run_in_executor
def process_large_dataset(data: list) -> list:
    return [complex_calculation(item) for item in data]
```

3. 错误处理和重试
```python
# 组合使用重试和异步
@sdk.util.retry(max_attempts=3, delay=2)
@sdk.util.run_in_executor
def reliable_network_operation():
    response = requests.get("https://api.example.com")
    response.raise_for_status()
    return response.json()

# 带有自定义错误处理的重试
@sdk.util.retry(max_attempts=5)
def safe_operation():
    try:
        return perform_risky_operation()
    except Exception as e:
        sdk.logger.warning(f"操作失败，准备重试: {e}")
        raise
```

## 注意事项
1. 缓存使用
   - 注意内存占用，避免缓存过大数据
   - 考虑缓存失效策略
   - 不要缓存频繁变化的数据

2. 异步执行
   - 避免在 run_in_executor 中执行过长的操作
   - 注意异常处理和资源清理
   - 合理使用线程池

3. 重试机制
   - 设置合适的重试次数和间隔
   - 只对可重试的操作使用重试装饰器
   - 注意避免重试导致的资源浪费

4. 依赖管理
   - 保持依赖关系清晰简单
   - 避免循环依赖
   - 定期检查和更新依赖关系

