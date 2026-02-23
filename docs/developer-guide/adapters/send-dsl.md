# SendDSL 详解

SendDSL 是 ErisPulse 适配器提供的链式调用风格的消息发送接口。

## 基本调用方式

### 1. 指定类型和ID

```python
await adapter.Send.To("group", "123").Text("Hello")
```

### 2. 仅指定ID

```python
await adapter.Send.To("123").Text("Hello")
```

### 3. 指定发送账号

```python
await adapter.Send.Using("bot1").Text("Hello")
```

### 4. 组合使用

```python
await adapter.Send.Using("bot1").To("group", "123").Text("Hello")
```

## 方法链

```
Using/Account() → To() → [修饰方法] → [发送方法]
```

## 发送方法

所有发送方法必须返回 `asyncio.Task` 对象。

### 基本方法

| 方法名 | 说明 | 返回值 |
|--------|------|---------|
| `Text(text: str)` | 发送文本消息 | `asyncio.Task` |
| `Image(file: bytes \| str)` | 发送图片 | `asyncio.Task` |
| `Voice(file: bytes \| str)` | 发送语音 | `asyncio.Task` |
| `Video(file: bytes \| str)` | 发送视频 | `asyncio.Task` |
| `File(file: bytes \| str)` | 发送文件 | `asyncio.Task` |

### 原始方法

| 方法名 | 说明 | 返回值 |
|--------|------|---------|
| `Raw_ob12(message)` | 发送 OneBot12 格式消息 | `asyncio.Task` |
| `Raw_json(json_str)` | 发送原始 JSON 消息 | `asyncio.Task` |

## 修饰方法

修饰方法返回 `self` 以支持链式调用。

### At 方法

```python
# @单个用户
await adapter.Send.To("group", "123").At("456").Text("你好")

# @多个用户
await adapter.Send.To("group", "123").At("456").At("789").Text("你们好")
```

### AtAll 方法

```python
# @全体成员
await adapter.Send.To("group", "123").AtAll().Text("大家好")
```

### Reply 方法

```python
# 回复消息
await adapter.Send.To("group", "123").Reply("msg_id").Text("回复内容")
```

### 组合修饰

```python
await adapter.Send.To("group", "123").At("456").Reply("msg_id").Text("回复@的消息")
```

## 账户管理

### Using 方法

```python
# 使用账户名
await adapter.Send.Using("account1").To("user", "123").Text("Hello")

# 使用账户 ID
await adapter.Send.Using("bot_id").To("user", "123").Text("Hello")
```

### Account 方法

`Account` 方法与 `Using` 等价：

```python
await adapter.Send.Account("account1").To("user", "123").Text("Hello")
```

## 异步处理

### 不等待结果

```python
# 消息在后台发送
task = adapter.Send.To("user", "123").Text("Hello")

# 继续执行其他操作
# ...
```

### 等待结果

```python
# 直接 await 获取结果
result = await adapter.Send.To("user", "123").Text("Hello")
print(f"发送结果: {result}")

# 先保存 Task，稍后等待
task = adapter.Send.To("user", "123").Text("Hello")
# ... 其他操作 ...
result = await task
```

## 命名规范

### PascalCase 命名

所有发送方法使用大驼峰命名法：

```python
# ✅ 正确
def Text(self, text: str):
    pass

def Image(self, file: bytes):
    pass

# ❌ 错误
def text(self, text: str):
    pass

def send_image(self, file: bytes):
    pass
```

### 平台特有方法

不推荐添加平台前缀方法：

```python
# ✅ 推荐
def Sticker(self, sticker_id: str):
    pass

# ❌ 不推荐
def TelegramSticker(self, sticker_id: str):
    pass
```

使用 `Raw` 方法替代：

```python
# ✅ 推荐
await adapter.Send.Raw_ob12([{"type": "sticker", ...}])

# ❌ 不推荐
def TelegramSticker(self, ...):
    pass
```

## 返回值

### Task 对象

所有发送方法返回 `asyncio.Task`：

```python
import asyncio

def Text(self, text: str):
    return asyncio.create_task(
        self._adapter.call_api(
            endpoint="/send",
            content=text,
            recvId=self._target_id,
            recvType=self._target_type
        )
    )
```

### 标准化响应

`call_api` 应返回标准化响应：

```python
async def call_api(self, endpoint: str, **params):
    return {
        "status": "ok" or "failed",
        "retcode": 0 or error_code,
        "data": {...},
        "message_id": "msg_id" or "",
        "message": "",
        "{platform}_raw": raw_response
    }
```

## 完整示例

### 基本使用

```python
from ErisPulse.Core import adapter

my_adapter = adapter.get("myplatform")

# 发送文本
await my_adapter.Send.To("user", "123").Text("Hello World!")

# 发送图片
await my_adapter.Send.To("group", "456").Image("https://example.com/image.jpg")

# 发送文件
with open("document.pdf", "rb") as f:
    await my_adapter.Send.To("user", "123").File(f.read())
```

### 链式调用

```python
# @用户 + 回复
await my_adapter.Send.To("group", "456").At("789").Reply("msg123").Text("回复@的消息")

# @全体 + 多个修饰
await my_adapter.Send.Using("bot1").To("group", "456").AtAll().Text("公告消息")
```

### 原始消息

```python
# 发送 OneBot12 格式消息
ob12_msg = [
    {"type": "text", "data": {"text": "Hello"}},
    {"type": "image", "data": {"file": "https://example.com/image.jpg"}}
]
await my_adapter.Send.To("group", "456").Raw_ob12(ob12_msg)
```

## 相关文档

- [适配器开发入门](getting-started.md) - 创建适配器
- [适配器核心概念](core-concepts.md) - 了解适配器架构
- [适配器最佳实践](best-practices.md) - 开发高质量适配器
- [发送方法命名规范](../../standards/send-type-naming.md) - 命名规范