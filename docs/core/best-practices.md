# ErisPulse 最佳实践

本文档提供了 ErisPulse 开发和部署的最佳实践建议。

## 1. 模块开发最佳实践

### 1.1 模块结构设计

```python
class Main:
    def __init__(self):
        self.sdk = sdk
        self.logger = sdk.logger.get_child("MyModule")
        self.storage = sdk.storage
        self.config = self._load_config()
        
    def _load_config(self):
        config = self.sdk.config.getConfig("MyModule")
        if not config:
            default_config = self._get_default_config()
            self.sdk.config.setConfig("MyModule", default_config)
            return default_config
        return config
        
    def _get_default_config(self):
        return {
            "api_url": "https://api.example.com",
            "timeout": 30,
            "retry_count": 3
        }
```

### 1.2 异步编程模型

优先使用异步库，避免阻塞主线程：

```python
import aiohttp

class Main:
    def __init__(self):
        self.session = aiohttp.ClientSession()
    
    async def fetch_data(self, url):
        async with self.session.get(url) as response:
            return await response.json()
    
    async def shutdown(self):
        await self.session.close()
```

### 1.3 异常处理

统一异常处理机制，记录详细日志：

```python
import traceback

class Main:
    async def handle_event(self, event):
        try:
            # 业务逻辑
            await self.process_event(event)
        except Exception as e:
            self.logger.error(f"处理事件时出错: {e}")
            self.logger.debug(f"错误详情: {traceback.format_exc()}")
```

## 2. 适配器开发最佳实践

### 2.1 连接管理

实现连接重试机制，确保服务稳定性：

```python
import asyncio

class MyAdapter(BaseAdapter):
    async def start(self):
        retry_count = 0
        while retry_count < 5:
            try:
                await self._connect_to_platform()
                break
            except Exception as e:
                retry_count += 1
                wait_time = min(60 * (2 ** retry_count), 600)  # 指数退避
                self.logger.warning(f"连接失败，{wait_time}秒后重试: {e}")
                await asyncio.sleep(wait_time)
```

### 2.2 事件转换

严格按照 OneBot12 标准进行事件转换：

```python
class MyPlatformConverter:
    def convert(self, raw_event):
        onebot_event = {
            "id": self._generate_event_id(raw_event),
            "time": self._convert_timestamp(raw_event.get("timestamp")),
            "type": self._convert_event_type(raw_event.get("type")),
            "detail_type": self._convert_detail_type(raw_event),
            "platform": "myplatform",
            "self": {
                "platform": "myplatform",
                "user_id": str(raw_event.get("bot_id", ""))
            },
            "myplatform_raw": raw_event  # 保留原始数据
        }
        return onebot_event
```

## 3. 配置管理最佳实践

### 3.1 配置结构化

使用结构化配置，便于管理和维护：

```python
# config.toml
[MyModule]
api_url = "https://api.example.com"
timeout = 30

[MyModule.database]
host = "localhost"
port = 5432
name = "mymodule"

[MyModule.features]
enable_cache = true
cache_ttl = 3600
```

### 3.2 配置验证

对配置进行验证，确保配置正确性：

```python
def _validate_config(self, config):
    required_fields = ["api_url", "timeout"]
    for field in required_fields:
        if field not in config:
            raise ValueError(f"缺少必要配置项: {field}")
    
    if not isinstance(config["timeout"], int) or config["timeout"] <= 0:
        raise ValueError("timeout 配置必须为正整数")
```

## 4. 存储系统最佳实践

### 4.1 事务使用

在关键操作中使用事务，确保数据一致性：

```python
async def update_user_data(self, user_id, data):
    with self.sdk.storage.transaction():
        self.sdk.storage.set(f"user:{user_id}:profile", data["profile"])
        self.sdk.storage.set(f"user:{user_id}:settings", data["settings"])
```

## 5. 日志系统最佳实践

### 5.1 日志级别使用

合理使用不同日志级别：

```python
class Main:
    def __init__(self):
        self.logger = sdk.logger.get_child("MyModule")
    
    async def process_event(self, event):
        self.logger.debug(f"开始处理事件: {event['id']}")
        
        try:
            result = await self._handle_event(event)
            self.logger.info(f"事件处理成功: {event['id']}")
            return result
        except ValueError as e:
            self.logger.warning(f"事件处理警告: {e}")
        except Exception as e:
            self.logger.error(f"事件处理失败: {e}")
            raise
```

### 5.2 日志输出配置

配置日志输出到文件，便于问题排查：

```python
# 在模块初始化时配置日志输出
sdk.logger.set_output_file(["app.log", "module.log"])
sdk.logger.set_module_level("MyModule", "DEBUG")
```

## 6. 性能优化最佳实践

### 6.1 缓存使用

对频繁查询的数据使用缓存：

```python
import asyncio

class Main:
    def __init__(self):
        self._cache = {}
        self._cache_lock = asyncio.Lock()
    
    async def get_user_info(self, user_id):
        async with self._cache_lock:
            if user_id in self._cache:
                # 检查缓存是否过期
                if self._cache[user_id]["expires"] > asyncio.get_event_loop().time():
                    return self._cache[user_id]["data"]
                else:
                    del self._cache[user_id]
        
        # 从数据库获取数据
        user_info = await self._fetch_user_info_from_db(user_id)
        
        # 缓存数据
        async with self._cache_lock:
            self._cache[user_id] = {
                "data": user_info,
                "expires": asyncio.get_event_loop().time() + 3600  # 1小时过期
            }
        
        return user_info
```

### 6.2 资源管理

及时释放资源，避免内存泄漏：

```python
class Main:
    def __init__(self):
        self.resources = []
    
    async def create_resource(self):
        resource = await self._create_new_resource()
        self.resources.append(resource)
        return resource
    
    async def cleanup_resources(self):
        for resource in self.resources:
            await resource.close()
        self.resources.clear()
```

## 7. 安全最佳实践

### 7.1 敏感数据保护

避免将密钥、密码等硬编码在代码中：

```python
# config.toml
[MyModule]
api_key = "YOUR_API_KEY_HERE"  # 用户需要替换为实际值

# 代码中
class Main:
    def __init__(self):
        config = self.sdk.config.getConfig("MyModule")
        self.api_key = config.get("api_key")
        if not self.api_key or self.api_key == "YOUR_API_KEY_HERE":
            raise ValueError("请在 config.toml 中配置 API 密钥")
```

## 8. 部署最佳实践

### 8.1 环境配置

使用环境变量配置敏感信息：

```python
import os

class Main:
    def __init__(self):
        self.config = self._load_config()
        self._load_env_config()
    
    def _load_env_config(self):
        # 从环境变量加载配置，覆盖默认配置
        api_key = os.getenv("MYMODULE_API_KEY")
        if api_key:
            self.config["api_key"] = api_key
```

### 8.2 监控和健康检查

实现健康检查接口：

```python
from fastapi import APIRouter

class Main:
    def __init__(self):
        self._register_health_check()
    
    def _register_health_check(self):
        router = APIRouter()
        
        @router.get("/health")
        async def health_check():
            return {
                "status": "ok",
                "module": "MyModule",
                "version": "1.0.0"
            }
        
        self.sdk.router.register_http_route(
            module_name="MyModule",
            path="/health",
            handler=health_check,
            methods=["GET"]
        )
```

遵循这些最佳实践可以帮助您开发出高质量、稳定可靠的 ErisPulse 模块和适配器。