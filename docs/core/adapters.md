# ErisPulse 适配器系统

适配器系统是 ErisPulse 实现跨平台支持的核心组件，负责将不同平台的事件转换为统一的 OneBot12 标准事件。

## 适配器职责

1. **事件转换**：将平台特定事件转换为 OneBot12 标准事件
2. **响应发送**：将 OneBot12 标准响应转换为平台特定格式
3. **连接管理**：管理与平台的连接和通信


### 1. SendDSL 消息发送

适配器通过 SendDSL 实现链式调用风格的消息发送接口。

#### 1.1 基础调用方式

**To 方法 - 设置消息目标**

`To` 方法用于设置消息的接收者。支持两种调用方式：

1. **指定类型和ID**：`To(type, id)` - 设置 `_target_type` 和 `_target_id`
2. **仅指定ID**：`To(id)` - 设置 `_target_to`

```python
from ErisPulse.Core import adapter

my_platform = adapter.get("MyPlatform")

# 指定类型和ID
my_platform.Send.To('user', '123').Text("hello world")

# 仅指定ID（适用于某些平台，如邮件）
my_platform.Send.To('123').Text("hello world")
```

**Using/Account 方法 - 设置发送账号**

`Using` 和 `Account` 方法用于指定发送消息的机器人账号。

```python
# 使用 Using 方法
my_platform.Send.Using('account_id').Text("hello world")

# 使用 Account 方法（与 Using 等价）
my_platform.Send.Account('account_id').Text("hello world")
```

**组合使用**

中间方法可以组合使用，顺序不限：

```python
# Using + To
my_platform.Send.Using('bot1').To('user', '123').Text("hello world")

# To + Using
my_platform.Send.To('user', '123').Using('bot1').Text("hello world")
```

#### 1.2 发送方法调用

```python
from ErisPulse.Core import adapter

my_platform = adapter.get("MyPlatform")

# 不等待结果，消息在后台发送
my_platform.Send.To("user", "123").Text("Hello")

# 等待结果，消息在发送后返回结果
task = my_platform.Send.To("user", "123").Text("Hello")

# 等待结果，并获取结果
result = await task

# 直接 await 获取结果
result = await my_platform.Send.To("user", "123").Text("Hello")
```
> **提示**：返回的 Task 维持了协程的完整状态机，因此可以将其存储在变量中供后续使用。对于大多数消息发送场景，您不需要等待发送结果。只有在需要确认消息是否成功发送或获取特定返回信息时，才需要 `await` Task 对象。

#### 1.3 链式修饰方法

链式修饰方法用于在发送消息前设置额外的参数（如 @用户、回复消息等）。这些方法返回 `self`，支持连续调用。

```python
# @单个用户
await my_platform.Send.To('group', '123').At('456').Text("你好")

# @多个用户
await my_platform.Send.To('group', '123').At('456').At('789').Text("你们好")

# @全体成员
await my_platform.Send.To('group', '123').AtAll().Text("大家好")

# 回复消息
await my_platform.Send.To('group', '123').Reply('msg_id').Text("回复内容")

# 组合使用
await my_platform.Send.Using('bot1').To('group', '123').At('456').Reply('789').Text("你好")
```

#### 1.4 发送原始消息

某些适配器提供了直接发送原始格式消息的方法：

```python
# 发送 OneBot12 格式的消息段
await my_platform.Send.To('user', '123').Raw_ob12({
    "type": "text",
    "data": {"text": "Hello"}
})

# 发送消息段数组
await my_platform.Send.To('group', '123').Raw_ob12([
    {"type": "text", "data": {"text": "Hello"}},
    {"type": "image", "data": {"file_id": "xxx"}}
])
```

#### 1.5 方法命名规范

详细的发送方法命名规范请参考 [发送方法命名规范](../standards/send-type-naming.md)。


### 2. 事件监听

有三种事件监听方式：

1. 平台原生事件监听：
   ```python
   from ErisPulse.Core import adapter, logger
   
   @adapter.on("event_type", raw=True, platform="yunhu")
   async def handler_1(data):
       logger.info(f"收到原生事件: {data}")

   @adapter.on("event_type")
   async def handler_2(data):
      platform = data.get("self").get("platform")
      raw_data = data.get(f"{platform}_raw")
      logger.info(f"收到 {platform} 原生事件: {raw_data}")
   ```

2. OneBot12标准事件监听：
   ```python
   from ErisPulse.Core import adapter, logger

   @adapter.on("event_type")  # 所有平台的标准事件
   async def handler(data):
       if data.get("self").get("platform") == "yunhu":
           logger.info(f"收到云湖标准事件: {data}")
   ```

3. 使用 `ErisPulse` 内置的 `Event` 模块进行事件监听（OneBot12标准事件）
    ```python
    from ErisPulse.Core.Event import message, command, notice, request

    @message.on_message()
    async def message_handler(event):
      logger.info(f"收到消息事件: {event}")

    @command(["help", "h"], aliases=["帮助"], help="显示帮助信息")
    async def help_handler(event):
      logger.info(f"收到命令事件: {event}")

    @notice.on_group_increase()
    async def notice_handler(event):
      logger.info(f"收到群成员增加事件: {event}")
    
    @request.on_friend_request()
    async def request_handler(event):
      logger.info(f"收到好友请求事件: {event}")
    ```

ErisPulse对于OneBot12协议进行了一些修改，你可能需要先阅读 `docs/standards` 下的转换标准和api返回规则。


更建议你使用 `Event` 模块来处理事件，它提供了更丰富的功能和语法。
