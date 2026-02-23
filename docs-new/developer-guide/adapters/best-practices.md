# 适配器开发最佳实践

本文档提供了 ErisPulse 适配器开发的最佳实践建议。

## 连接管理

### 1. 实现连接重试

```python
import asyncio

class MyAdapter(BaseAdapter):
    async def start(self):
        retry_count = 0
        max_retries = 5
        
        while retry_count < max_retries:
            try:
                await self._connect_to_platform()
                self.logger.info("连接成功")
                break
            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    # 指数退避策略
                    wait_time = min(60 * (2 ** retry_count), 600)
                    self.logger.warning(
                        f"连接失败，{wait_time}秒后重试 ({retry_count}/{max_retries}): {e}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error("连接失败，已达到最大重试次数")
                    raise
```

### 2. 连接状态管理

```python
class MyAdapter(BaseAdapter):
    def __init__(self, sdk):
        super().__init__()
        self.connection = None
        self._connected = False
    
    async def _ws_handler(self, websocket: WebSocket):
        self.connection = websocket
        self._connected = True
        self.logger.info("连接已建立")
        
        try:
            while True:
                data = await websocket.receive_text()
                await self._process_event(data)
        except WebSocketDisconnect:
            self.logger.info("连接已断开")
        finally:
            self.connection = None
            self._connected = False
```

### 3. 心跳保活

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        self.connection = await self._connect_to_platform()
        # 启动心跳任务
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
    
    async def _heartbeat_loop(self):
        """心跳保活"""
        while self.connection:
            try:
                await self.connection.send_json({"type": "ping"})
                await asyncio.sleep(30)  # 30秒一次心跳
            except Exception as e:
                self.logger.error(f"心跳失败: {e}")
                break
```

## 事件转换

### 1. 严格遵循 OneBot12 标准

```python
class MyPlatformConverter:
    def convert(self, raw_event):
        """转换事件"""
        onebot_event = {
            "id": str(raw_event.get("event_id", uuid.uuid4())),
            "time": int(time.time()),
            "type": self._convert_type(raw_event.get("type")),
            "detail_type": self._convert_detail_type(raw_event),
            "platform": "myplatform",
            "self": {
                "platform": "myplatform",
                "user_id": str(raw_event.get("bot_id", ""))
            },
            "myplatform_raw": raw_event,  # 保留原始数据（必须）
            "myplatform_raw_type": raw_event.get("type", "")  # 原始类型（必须）
        }
        return onebot_event
```

### 2. 时间戳标准化

```python
def _convert_timestamp(self, timestamp):
    """转换为 10 位秒级时间戳"""
    if not timestamp:
        return int(time.time())
    
    # 如果是毫秒级时间戳
    if timestamp > 10**12:
        return int(timestamp / 1000)
    
    # 如果是秒级时间戳
    return int(timestamp)
```

### 3. 事件 ID 生成

```python
import uuid

def _generate_event_id(self, raw_event):
    """生成事件 ID"""
    event_id = raw_event.get("event_id")
    if event_id:
        return str(event_id)
    # 如果平台没有提供 ID，生成 UUID
    return str(uuid.uuid4())
```

## SendDSL 实现

### 1. 必须返回 Task 对象

```python
class Send(BaseAdapter.Send):
    def Text(self, text: str):
        """发送文本消息"""
        import asyncio
        return asyncio.create_task(
            self._adapter.call_api(
                endpoint="/send",
                content=text,
                recvId=self._target_id,
                recvType=self._target_type
            )
        )
```

### 2. 链式修饰方法返回 self

```python
class Send(BaseAdapter.Send):
    def At(self, user_id: str) -> 'Send':
        """@用户"""
        if not hasattr(self, '_at_user_ids'):
            self._at_user_ids = []
        self._at_user_ids.append(user_id)
        return self  # 必须返回 self
    
    def Reply(self, message_id: str) -> 'Send':
        """回复消息"""
        self._reply_message_id = message_id
        return self  # 必须返回 self
```

### 3. 支持平台特有方法

```python
class Send(BaseAdapter.Send):
    def Sticker(self, sticker_id: str):
        """发送表情包"""
        import asyncio
        return asyncio.create_task(
            self._adapter.call_api(
                endpoint="/send_sticker",
                sticker_id=sticker_id,
                recvId=self._target_id,
                recvType=self._target_type
            )
        )
    
    def Card(self, card_data: dict):
        """发送卡片消息"""
        import asyncio
        return asyncio.create_task(
            self._adapter.call_api(
                endpoint="/send_card",
                card=card_data,
                recvId=self._target_id,
                recvType=self._target_type
            )
        )
```

## API 响应

### 1. 标准化响应格式

```python
async def call_api(self, endpoint: str, **params):
    try:
        raw_response = await self._platform_api_call(endpoint, **params)
        
        return {
            "status": "ok" if raw_response.get("success") else "failed",
            "retcode": 0 if raw_response.get("success") else raw_response.get("code", 10001),
            "data": raw_response.get("data"),
            "message_id": raw_response.get("data", {}).get("message_id", ""),
            "message": "",
            "myplatform_raw": raw_response
        }
    except Exception as e:
        return {
            "status": "failed",
            "retcode": 34000,
            "data": None,
            "message_id": "",
            "message": str(e),
            "myplatform_raw": None
        }
```

### 2. 错误码规范

遵循 OneBot12 标准错误码：

```python
# 1xxxx - 动作请求错误
10001: Bad Request
10002: Unsupported Action
10003: Bad Param

# 2xxxx - 动作处理器错误
20001: Bad Handler
20002: Internal Handler Error

# 3xxxx - 动作执行错误
31000: Database Error
32000: Filesystem Error
33000: Network Error
34000: Platform Error
35000: Logic Error
```

## 多账户支持

### 1. 账户配置验证

```python
def _get_config(self):
    """验证配置"""
    config = self.config_manager.getConfig("MyAdapter", {})
    accounts = config.get("accounts", {})
    
    if not accounts:
        # 创建默认账户
        default_account = {
            "token": "",
            "enabled": False
        }
        config["accounts"] = {"default": default_account}
        self.config_manager.setConfig("MyAdapter", config)
    
    return config
```

### 2. 账户选择机制

```python
async def _get_account_for_message(self, event):
    """根据事件选择发送账户"""
    bot_id = event.get("self", {}).get("user_id")
    
    # 查找匹配的账户
    for account_name, account_config in self.accounts.items():
        if account_config.get("bot_id") == bot_id:
            return account_name
    
    # 如果没有找到，使用第一个启用的账户
    for account_name, account_config in self.accounts.items():
        if account_config.get("enabled", True):
            return account_name
    
    return None
```

## 错误处理

### 1. 分类异常处理

```python
async def call_api(self, endpoint: str, **params):
    try:
        response = await self._platform_api_call(endpoint, **params)
        return self._standardize_response(response)
    except aiohttp.ClientError as e:
        # 网络错误
        self.logger.error(f"网络错误: {e}")
        return self._error_response("网络请求失败", 33000)
    except asyncio.TimeoutError:
        # 超时错误
        self.logger.error(f"请求超时: {endpoint}")
        return self._error_response("请求超时", 32000)
    except json.JSONDecodeError:
        # JSON 解析错误
        self.logger.error("JSON 解析失败")
        return self._error_response("响应格式错误", 10006)
    except Exception as e:
        # 未知错误
        self.logger.error(f"未知错误: {e}", exc_info=True)
        return self._error_response(str(e), 34000)
```

### 2. 日志记录

```python
class MyAdapter(BaseAdapter):
    def __init__(self, sdk=None):
        super().__init__(sdk)
        self.logger = logger.get_child("MyAdapter")
    
    async def start(self):
        self.logger.info("适配器启动中...")
        # ...
        self.logger.info("适配器启动完成")
    
    async def shutdown(self):
        self.logger.info("适配器关闭中...")
        # ...
        self.logger.info("适配器关闭完成")
```

## 测试

### 1. 单元测试

```python
import pytest
from ErisPulse.Core.Bases import BaseAdapter

class TestMyAdapter:
    def test_converter(self):
        """测试转换器"""
        converter = MyPlatformConverter()
        raw_event = {"type": "message", "content": "Hello"}
        result = converter.convert(raw_event)
        assert result is not None
        assert result["platform"] == "myplatform"
        assert "myplatform_raw" in result
    
    def test_api_response(self):
        """测试 API 响应格式"""
        adapter = MyAdapter()
        response = adapter.call_api("/test", param="value")
        assert "status" in response
        assert "retcode" in response
```

### 2. 集成测试

```python
@pytest.mark.asyncio
async def test_adapter_start():
    """测试适配器启动"""
    adapter = MyAdapter()
    await adapter.start()
    assert adapter._connected is True

@pytest.mark.asyncio
async def test_send_message():
    """测试发送消息"""
    adapter = MyAdapter()
    await adapter.start()
    
    result = await adapter.Send.To("user", "123").Text("Hello")
    assert result is not None
```

## 文档维护

### 1. 维护平台特性文档

在 `docs-new/platform-guide/` 下创建 `{platform}.md` 文档：

```markdown
# 平台名称适配器文档

## 基本信息
- 对应模块版本: 1.0.0
- 维护者: Your Name

## 支持的消息发送类型
...

## 特有事件类型
...

## 配置选项
...
```

### 2. 更新版本信息

发布新版本时，更新文档中的版本信息：

```toml
[project]
version = "2.0.0"  # 更新版本号
```

## 相关文档

- [适配器开发入门](getting-started.md) - 创建第一个适配器
- [适配器核心概念](core-concepts.md) - 了解适配器架构
- [SendDSL 详解](send-dsl.md) - 学习消息发送