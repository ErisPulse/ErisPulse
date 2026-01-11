# ErisPulse 适配器开发指南

## 1. 目录结构
一个标准的适配器包结构应该是：

```
MyAdapter/
├── pyproject.toml
├── README.md
├── LICENSE
└── MyAdapter/
    ├── __init__.py
    ├── Core.py
    └── Converter.py
```

### 1.1 `pyproject.toml` 文件
```toml
[project]
name = "ErisPulse-MyAdapter"
version = "1.0.0"
description = "MyAdapter是一个非常酷的平台，这个适配器可以帮你绽放更亮的光芒"
readme = "README.md"
requires-python = ">=3.9"
license = { file = "LICENSE" }
authors = [ { name = "yourname", email = "your@mail.com" } ]

dependencies = [
    
]

[project.urls]
"homepage" = "https://github.com/yourname/MyAdapter"

[project.entry-points]
"erispulse.adapter" = { "MyAdapter" = "MyAdapter:MyAdapter" }
```

### 1.2 `MyAdapter/__init__.py` 文件

顾名思义,这只是使你的模块变成一个Python包, 你可以在这里导入模块核心逻辑, 当然也可以让他保持空白

示例这里导入了模块核心逻辑

```python
from .Core import MyAdapter
```

### 1.3 `MyAdapter/Core.py`
实现适配器主类 `MyAdapter`，并提供适配器类继承 `BaseAdapter`, 实现嵌套类Send以实现例如 Send.To(type, id).Text("hello world") 的语法

```python
from ErisPulse import sdk
from ErisPulse.Core import BaseAdapter
from ErisPulse.Core import router, logger, config as config_manager, adapter

# 这里仅你使用 websocket 作为通信协议时需要 | 第一个作为参数的类型是 WebSocket, 第二个是 WebSocketDisconnect，当 ws 连接断开时触发你的捕捉
# 一般来说你不用在依赖中添加 fastapi, 因为它已经内置在 ErisPulse 中了
# from fastapi import WebSocket, WebSocketDisconnect

class MyAdapter(BaseAdapter):
    def __init__(self, sdk=None):    # 这里是不强制传入sdk的，你可以选择不传入 
        self.sdk = sdk
        self.logger = logger.get_child("MyAdapter")
        self.config_manager = config_manager
        self.adapter = adapter
        
        if self.logger:
            self.logger.info("MyAdapter 初始化完成")
        self.config = self._get_config()
        self.converter = self._setup_converter()  # 获取转换器实例
        self.convert = self.converter.convert

    def _setup_converter(self):
        from .Converter import MyPlatformConverter
        return MyPlatformConverter()

    def _get_config(self):
        # 加载配置方法，你需要在这里进行必要的配置加载逻辑
        if not self.config_manager:
            return {}
            
        config = self.config_manager.getConfig("MyAdapter", {})

        if config is None:
            default_config = {
                # 在这里定义默认配置
            }
            # 这里默认配置会生成到用户的 config.toml 文件中
            self.config_manager.setConfig("MyAdapter", default_config)
            return default_config
        return config

    class Send(BaseAdapter.Send):  # 继承BaseAdapter内置的Send类
        """
        Send消息发送DSL，支持四种调用方式(继承的Send类包含了To和Using方法):
        1. 指定类型和ID: To(type,id).Func() -> 设置_target_type和_target_id/_target_to
           示例: Send.To("group",123).Text("hi")
        2. 指定发送账号: Using(account_id).Func() -> 设置_account_id
           示例: Send.Using("bot1").Text("hi")
        3. 组合使用: Using(account_id).To(type,id).Func()
           示例: Send.Using("bot1").To("user","123").Text("hi")
        4. 直接调用: Func() -> 不设置目标属性
           示例: Send.Text("broadcast")
        """
        
        def Text(self, text: str):
            """发送文本消息（可重写实现）"""
            import asyncio
            return asyncio.create_task(
                self._adapter.call_api(
                    endpoint="/send",
                    content=text,
                    recvId=self._target_id,    # 来自To()设置的属性
                    recvType=self._target_type # 来自To(type,id)设置的属性
                )
            )
            
        def Image(self, file: bytes):
            """发送图片消息"""
            import asyncio
            return asyncio.create_task(
                self._adapter.call_api(
                    endpoint="/send_image",
                    file=file,
                    recvId=self._target_id,    # 自动使用To()设置的属性
                    recvType=self._target_type
                )
            )

    # 这里的call_api方法需要被实现, 哪怕他是类似邮箱时一个轮询一个发送stmp无需请求api的实现
    # 因为这是必须继承的方法
    async def call_api(self, endpoint: str, **params):
        raise NotImplementedError("需要实现平台特定的API调用")

    # 适配器设定了启动和停止的方法，用户可以直接通过 adapter.setup() 来启动所有适配器，
    # 当然在底层捕捉到adapter的错误时我们会尝试停止适配器再进行重启等操作
    # 启动方法，你需要在这里定义你的adapter启动时候的逻辑
    async def start(self):
        raise NotImplementedError("需要实现适配器启动逻辑")
    # 停止方法，你需要在这里进行必要的释放资源等逻辑
    async def shutdown(self):
        raise NotImplementedError("需要实现适配器关闭逻辑")
```

## 2. 接口规范说明

### 必须实现的方法

| 方法 | 描述 |
|------|------|
| `call_api(endpoint: str, **params)` | 调用平台 API |
| `start()` | 启动适配器 |
| `shutdown()` | 关闭适配器资源 |

> ⚠⚠⚠️ 注意：
> - 适配器类必须继承 `BaseAdapter` 基类；
> - 必须实现 `call_api`, `start`, `shutdown` 方法 和 `Send`类(继承自 `BaseAdapter.Send`)；
> - To中的接受者类型不允许例如 "private" 的格式，当然这是一个规范
> - 但为了兼容和标准性，用户发送时还是使用 "user" / "group" / "channel" / ... 等更标准的接受类型格式，如有必要，请你自行转换。

## 3. DSL 风格消息接口（SendDSL）

每个适配器可定义一组链式调用风格的方法，例如：

```python
class Send(BaseAdapter.Send):
    def Text(self, text: str):
        import asyncio
        return asyncio.create_task(
            self._adapter.call_api(...)
        )

    def Image(self, file: bytes):
        import asyncio
        return asyncio.create_task(
            self._upload_file_and_call_api(...)
        )
```
> **注意**：Send的链式调用方式，必须返回一个asyncio.Task对象。

#### ErisPulse的SendDSL支持以下不同组合的标准调用方式：

1. 指定类型和ID: `To(type,id).Func()`
   ```python
   # 获取适配器实例
   my_adapter = adapter.get("MyAdapter")
   
   await my_adapter.Send.To("user", "U1001").Text("Hello")
   ```
2. 仅指定ID: `To(id).Func()`
   ```python
   my_adapter = adapter.get("MyAdapter")

   await my_adapter.Send.To("U1001").Text("Hello")
   ```
3. 指定发送账号: `Using(account_id)`
   ```python
   my_adapter = adapter.get("MyAdapter")

   await my_adapter.Send.Using("bot1").To("U1001").Text("Hello")
   ```
4. 直接调用: `Func()`
   ```python
   my_adapter = adapter.get("MyAdapter")
   await my_adapter.Send.Text("Broadcast message")
   
   # 例如：
   email = adapter.get("email")
   await email.Send.Text("Broadcast message")
   ```

`To`方法可以指定接受者类型以及接受者ID，当To参数接受了单参数时，会设置`self._target_to`属性，当To参数接受了两个参数时，会设置`self._target_type`和`self._target_id`属性，可以在后续的调用中通过这些属性来获取接受者信息。
`Using`方法用于指定发送账号，会设置`self._account_id`属性，可以在后续API调用中使用。

## 4. 事件转换与路由注册

适配器需要处理平台原生事件并转换为OneBot12标准格式，同时需要向底层框架注册路由。以下是两种典型实现方式：

### 4.1 WebSocket 方式实现

```python
async def _ws_handler(self, websocket: WebSocket):
    """WebSocket连接处理器"""
    self.connection = websocket
    self.logger.info("客户端已连接")

    try:
        while True:
            data = await websocket.receive_text()
            try:
                # 转换为OneBot12标准事件
                onebot_event = self.convert(data)
                if onebot_event and self.adapter:
                    await self.adapter.emit(onebot_event)
            except json.JSONDecodeError:
                self.logger.error(f"JSON解析失败: {data}")
    except WebSocketDisconnect:
        self.logger.info("客户端断开连接")
    finally:
        self.connection = None

async def start(self):
    """注册WebSocket路由"""
    from ErisPulse.Core import router
    router.register_websocket(
        module_name="myplatform",  # 适配器名
        path="/ws",  # 路由路径
        handler=self._ws_handler,  # 处理器
        auth_handler=self._auth_handler  # 认证处理器(可选)
    )
```

### 4.2 WebHook 方式实现

```python
async def _webhook_handler(self, request: Request):
    """WebHook请求处理器"""
    try:
        data = await request.json()

        # 转换为OneBot12标准事件
        onebot_event = self.convert(data)
        if onebot_event and self.adapter:
            # 提交标准事件到框架 
            await self.adapter.emit(onebot_event)
        return JSONResponse({"status": "ok"})
    except Exception as e:
        if self.logger:
            self.logger.error(f"处理WebHook失败: {str(e)}")
        return JSONResponse({"status": "failed"}, status_code=400)

async def start(self):
    """注册WebHook路由"""
    from ErisPulse.Core import router
    router.register_http_route(
        module_name="myplatform",  # 适配器名
        path="/webhook",  # 路由路径
        handler=self._webhook_handler,  # 处理器
        methods=["POST"]  # 支持的HTTP方法
    )
```

### 4.3 事件转换器实现

适配器应提供标准的事件转换器，将平台原生事件转换为OneBot12格式 具体实现请参考[适配器标准化转换规范](../standards/event-conversion.md)：

```python
class MyPlatformConverter:
    def convert(self, raw_event: Dict) -> Optional[Dict]:
        """将平台原生事件转换为OneBot12标准格式"""
        if not isinstance(raw_event, dict):
            return None

        # 基础事件结构
        onebot_event = {
            "id": str(raw_event.get("event_id", uuid.uuid4())),
            "time": int(time.time()),
            "type": "",  # message/notice/request/meta_event
            "detail_type": "",
            "platform": "myplatform",
            "self": {
                "platform": "myplatform",
                "user_id": str(raw_event.get("bot_id", ""))
            },
            "myplatform_raw": raw_event,  # 保留原始数据
            "myplatform_raw_type": raw_event.get("type", "")    # 原始数据类型
        }

        # 根据事件类型分发处理
        event_type = raw_event.get("type")
        if event_type == "message":
            return self._handle_message(raw_event, onebot_event)
        elif event_type == "notice":
            return self._handle_notice(raw_event, onebot_event)
        
        return None
```

### 4.4 原始事件类型字段

从 ErisPulse 2.3.0 版本开始，适配器需要在转换的事件中包含原始事件类型字段：

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
            "myplatform_raw": raw_event,  # 保留原始数据
            "myplatform_raw_type": raw_event.get("type", "")  # 原始事件类型
        }
        return onebot_event
```

### 4.5 事件监听方式

适配器现在支持两种事件监听方式：

1. 监听 OneBot12 标准事件：
```python
from ErisPulse.Core import adapter

@adapter.on("message")
async def handle_message(event):
    # 处理标准消息事件
    pass

# 监听特定平台的事件
@adapter.on("message", platform="myplatform")
async def handle_platform_message(event):
    # 只处理来自 myplatform 的消息事件
    pass
```

2. 监听平台原始事件：
```python
from ErisPulse.Core import adapter

@adapter.on("text_message", raw=True, platform="myplatform")
async def handle_raw_message(raw_event):
    # 处理平台原始事件
    pass
```

## 5. API响应标准

适配器的`call_api`方法必须返回符合以下标准的响应结构（具体实现请参考[适配器标准化返回规范](../standards/api-response.md)：）：

### 5.1 成功响应格式

```python
{
    "status": "ok",  # 必须
    "retcode": 0,  # 必须，0表示成功
    "data": {  # 必须，成功时返回的数据
        "message_id": "123456",  # 消息ID(如果有)
        "time": 1632847927.599013  # 时间戳(如果有)
    },
    "message": "",  # 必须，成功时为空字符串
    "message_id": "123456",  # 可选，消息ID
    "echo": "1234",  # 可选，当请求中包含echo时返回
    "myplatform_raw": {...}  # 可选，原始响应数据
}
```

### 5.2 失败响应格式

```python
{
    "status": "failed",  # 必须
    "retcode": 10003,  # 必须，非0错误码
    "data": None,  # 必须，失败时为null
    "message": "缺少必要参数",  # 必须，错误描述
    "message_id": "",  # 可选，失败时为空字符串
    "echo": "1234",  # 可选，当请求中包含echo时返回
    "myplatform_raw": {...}  # 可选，原始响应数据
}
```

### 5.3 实现示例

```python
async def call_api(self, endpoint: str, **params):
    try:
        # 调用平台API
        raw_response = await self._platform_api_call(endpoint, **params)
        
        # 标准化响应
        standardized = {
            "status": "ok" if raw_response.get("success", False) else "failed",
            "retcode": 0 if raw_response.get("success", False) else raw_response.get("code", 10001),
            "data": raw_response.get("data"),
            "message": raw_response.get("message", ""),
            "message_id": raw_response.get("data", {}).get("message_id", ""),
            "myplatform_raw": raw_response
        }
        
        if "echo" in params:
            standardized["echo"] = params["echo"]
            
        return standardized
        
    except Exception as e:
        return {
            "status": "failed",
            "retcode": 34000,  # 平台错误代码段
            "data": None,
            "message": str(e),
            "message_id": ""
        }
```

## 6. 多Bot实现指南

如果你的平台支持同时运行多个机器人账号（多Bot），需要按照以下规范实现：

### 6.1 配置结构设计

采用分层配置结构，支持全局配置和独立账户配置：

```python
# 配置格式示例
{
    "YourPlatform_Adapter": {
        "global": {
            "retry_interval": 30,
            "timeout": 30
        },
        "bots": {
            "bot1": {
                "bot_id": "123456789",  # 必填，机器人唯一标识
                "token": "xxx",
                "webhook_path": "/webhook/bot1",
                "enabled": true
            },
            "bot2": {
                "bot_id": "987654321",
                "token": "yyy",
                "webhook_path": "/webhook/bot2",
                "enabled": true
            }
        }
    }
}
```

**关键设计原则：**
- 使用 `bot_id` 作为机器人的唯一标识符（必填）
- `bot_id` 用于SDK路由消息，与平台特定的账号标识不同
- 每个bot配置独立的 `token`、`webhook_path` 等参数
- 提供 `enabled` 字段控制bot的启用状态

### 6.2 Bot配置数据类

使用dataclass定义bot配置结构：

```python
from dataclasses import dataclass

@dataclass
class YourBotConfig:
    bot_id: str  # 机器人ID（必填，用于SDK路由）
    token: str  # 认证token
    webhook_path: str = "/webhook"  # Webhook路径
    enabled: bool = True  # 是否启用
    name: str = ""  # 账户名称
```

### 6.3 call_api 方法实现

**重要：** `call_api` 方法需要智能判断 `_account_id` 是账户名还是bot_id：

```python
async def call_api(self, endpoint: str, bot_id: str = None, _account_id: str = None, **params):
    """
    调用平台API

    :param endpoint: API端点
    :param bot_id: 显式指定的bot_id（优先级最高）
    :param _account_id: 账户名或bot_id（由Using方法设置）
    :param params: 其他API参数
    :return: 标准化的响应
    """
    # 确定使用的bot
    if bot_id is None:
        if _account_id is None:
            # 使用第一个启用的bot作为默认
            enabled_bots = [b for b in self.bots.values() if b.enabled]
            if not enabled_bots:
                raise ValueError("没有配置任何启用的机器人")
            bot = enabled_bots[0]
        else:
            # 判断_account_id是账户名还是bot_id
            if _account_id in self.bots:
                # _account_id是账户名，直接使用
                bot = self.bots[_account_id]
            else:
                # _account_id是bot_id，查找对应的账户
                for bot_name, bot_config in self.bots.items():
                    if bot_config.bot_id == _account_id:
                        bot = bot_config
                        break
                else:
                    raise ValueError(f"找不到bot_id或账户名为 {_account_id} 的机器人")
    else:
        # 显式指定了bot_id，根据bot_id查找
        for bot_name, bot_config in self.bots.items():
            if bot_config.bot_id == bot_id:
                bot = bot_config
                break
        else:
            raise ValueError(f"找不到bot_id为 {bot_id} 的机器人")

    if not bot.enabled:
        raise ValueError(f"机器人 {bot.name} 已禁用")

    # 使用bot配置调用API
    raw_response = await self._net_request(endpoint, params, bot.token=bot.token)

    # 标准化响应，使用bot_id标识机器人
    return {
        "status": "ok",
        "retcode": 0,
        "data": raw_response.get("data"),
        "message": "",
        "self": {"user_id": bot.bot_id},  # 使用bot_id作为self.user_id
        "yourplatform_raw": raw_response
    }
```

**注意事项：**
1. 优先级：显式指定的 `bot_id` > `_account_id` > 默认bot
2. `_account_id` 既可以是账户名，也可以是bot_id
3. 如果 `_account_id` 在 `self.bots` 字典中，则视为账户名
4. 否则视为bot_id，在各bot的配置中查找匹配的 `bot_id`
5. 返回响应中的 `self.user_id` 必须使用 `bot_id`
6. 日志中应同时记录bot_name和bot_id，便于调试

### 6.4 不需要重写Using方法

**重要：** 不需要重写Using方法！

BaseAdapter的SendDSL已经提供了Using方法，它会设置`self._account_id`属性。你的适配器只需要在`call_api`中智能判断`_account_id`是账户名还是bot_id（如6.3节所述）。

用户可以这样使用：
```python
# 使用账户名
await adapter.Send.Using("bot1").To("123").Text("Hello")

# 使用bot_id
await adapter.Send.Using("bot_id_123").To("123").Text("Hello")
```

### 6.5 Send方法实现

Send方法只需要将 `self._account_id` 传递给call_api，不需要额外处理bot_id：

```python
def Text(self, text: str):
    return asyncio.create_task(
        self._adapter.call_api(
            endpoint="/send",
            content=text,
            recvId=self._target_id,
            recvType=self._target_type,
            _account_id=self._account_id  # 传递_account_id，call_api会自动判断是账户名还是bot_id
        )
    )
```

**注意：** 不需要传递 `bot_id` 参数，因为 `call_api` 会根据 `_account_id` 自动判断是账户名还是bot_id。

### 6.6 事件处理中的bot_id

在事件处理时确保事件包含正确的bot_id：

```python
async def _process_webhook_event(self, data: Dict, bot_name: str):
    """处理webhook事件"""
    try:
        # 获取对应的bot配置
        bot = self.bots.get(bot_name)
        if not bot:
            self.logger.error(f"找不到bot配置: {bot_name}")
            return

        # 转换事件并传递bot_id
        onebot_event = self.convert(data, bot_id=bot.bot_id)

        if onebot_event:
            await self.adapter.emit(onebot_event)
    except Exception as e:
        self.logger.error(f"处理事件错误: {str(e)}")
```

Converter需要支持接收bot_id参数：

```python
def convert(self, data: Dict, bot_id: str = None) -> Optional[Dict]:
    """转换事件，使用传入的bot_id设置self.user_id"""
    base_event = {
        "id": str(uuid.uuid4()),
        "time": int(time.time()),
        "type": "message",
        "detail_type": "private",
        "platform": "yourplatform",
        "self": {
            "platform": "yourplatform",
            "user_id": bot_id or ""  # 使用传入的bot_id
        },
        "yourplatform_raw": data,
        "yourplatform_raw_type": data.get("type", "")
    }
    return base_event
```

### 6.7 向后兼容性处理

支持旧配置格式的自动迁移：

```python
def _load_bots_config(self) -> Dict[str, YourBotConfig]:
    """加载多bot配置"""
    bots = {}

    # 检查新格式的bot配置
    bot_configs = self.sdk.config.getConfig("YourPlatform_Adapter.bots", {})

    if not bot_configs:
        # 检查旧配置格式
        old_config = self.sdk.config.getConfig("YourPlatform_Adapter")
        if old_config and "token" in old_config:
            self.logger.warning("检测到旧格式配置，正在兼容处理...")
            self.logger.warning("建议迁移到新配置格式以获得更好的多bot支持")

            # 临时使用旧配置
            temp_config = {
                "default": {
                    "bot_id": "default",  # 用户需修改为实际的bot_id
                    "token": old_config.get("token", ""),
                    "enabled": True
                }
            }
            bot_configs = temp_config

    # 创建bot配置对象
    for bot_name, config in bot_configs.items():
        if "bot_id" not in config or not config["bot_id"]:
            self.logger.error(f"Bot {bot_name} 缺少bot_id配置，已跳过")
            continue

        merged_config = {
            "bot_id": config["bot_id"],
            "token": config.get("token", ""),
            "enabled": config.get("enabled", True),
            "name": bot_name
        }

        bots[bot_name] = YourBotConfig(**merged_config)

    return bots
```

### 6.8 多Bot实现检查清单

实现多bot功能时，请确保：

- [ ] 配置结构使用 `bots` 对象，每个bot有独立的 `bot_id`
- [ ] `call_api` 方法支持 `bot_id` 和 `_account_id` 参数
- [ ] `call_api` 能够智能判断 `_account_id` 是账户名还是bot_id
  - 如果 `_account_id` 在 `self.bots` 字典中，则视为账户名
  - 否则视为bot_id，在各bot的配置中查找匹配的 `bot_id`
- [ ] **不要重写Using方法**（BaseAdapter已经提供了Using方法）
- [ ] Send方法只传递 `_account_id` 参数，不需要传递 `bot_id`
- [ ] 响应中的 `self.user_id` 使用 `bot_id`
- [ ] Converter支持接收bot_id参数
- [ ] 事件处理中正确传递bot_id
- [ ] 实现旧配置格式的兼容性处理
- [ ] 为每个bot注册独立的Webhook/WS路由（如适用）
- [ ] 日志中记录bot_name和bot_id，便于调试
- [ ] 提供bot启用/禁用功能

## 7. 平台特性文档维护

请参考 [平台特性文档维护说明](../platform-features/maintain-notes.md) 来维护你的适配器平台特性文档。

主要需要包含以下内容：
1. 平台简介和适配器基本信息
2. 支持的消息发送类型和参数说明
3. 特有事件类型和格式说明
4. 扩展字段说明
5. OneBot12协议转换说明
6. API响应格式
7. 多bot支持说明（如果支持）
8. 最佳实践和注意事项

感谢您的支持！
