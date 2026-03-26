# ErisPulse 发送方法规范

本文档定义了 ErisPulse 适配器中 Send 类发送方法的命名规范和参数规范。

## 1. 标准方法命名

所有发送方法使用 **大驼峰命名法（PascalCase）**，首字母大写。

### 1.1 标准发送方法

| 方法名 | 说明 | 参数类型 |
|-------|------|---------|
| `Text` | 发送文本消息 | `str` |
| `Image` | 发送图片 | `bytes` \| `str` (URL/路径) |
| `Voice` | 发送语音 | `bytes` \| `str` (URL/路径) |
| `Video` | 发送视频 | `bytes` \| `str` (URL/路径) |
| `File` | 发送文件 | `bytes` \| `str` (URL/路径) |
| `At` | @用户/群组 | `str` (user_id) |
| `Face` | 发送表情 | `str` (emoji) |
| `Reply` | 回复消息 | `str` (message_id) |
| `Forward` | 转发消息 | `str` (message_id) |
| `Markdown` | 发送 Markdown 消息 | `str` |
| `HTML` | 发送 HTML 消息 | `str` |
| `Card` | 发送卡片消息 | `dict` |

### 1.2 链式修饰方法

| 方法名 | 说明 | 参数类型 |
|-------|------|---------|
| `At` | @用户（可多次调用） | `str` (user_id) |
| `AtAll` | @全体成员 | 无 |
| `Reply` | 回复消息 | `str` (message_id) |

### 1.3 协议方法

| 方法名 | 说明 |
|-------|------|
| `Raw_ob12` | 发送原始 OneBot12 格式消息 |
| `Raw_json` | 发送原始 JSON 格式消息 |
| `Raw_xml` | 发送原始 XML 格式消息 |

## 2. 参数规范详解

### 2.1 媒体消息参数规范

媒体消息（`Image`、`Voice`、`Video`、`File`）支持两种参数类型：

#### 2.1.1 字符串参数（URL 或文件路径）

**格式：** `str`

**支持类型：**
- **URL**：网络资源地址（如 `https://example.com/image.jpg`）
- **文件路径**：本地文件路径（如 `/path/to/file.jpg` 或 `C:\\path\\to\\file.jpg`）

**使用场景：**
- 文件已在网络上，直接发送 URL
- 文件在本地磁盘，发送文件路径
- 希望适配器自动处理文件上传

**推荐：** 优先使用 URL，如果 URL 不可用则使用本地文件路径

**示例：**
```python
# 使用 URL
send.Image("https://example.com/image.jpg")

# 使用本地文件路径
send.Image("/path/to/local/image.jpg")
send.Image("C:\\path\\to\\local\\image.jpg")
```

#### 2.1.2 二进制数据参数

**格式：** `bytes`

**使用场景：**
- 文件已在内存中（如从网络下载、从其他来源读取）
- 需要处理后再发送（如图片压缩、格式转换）
- 避免重复读取文件

**注意事项：**
- 大文件上传可能消耗较多内存
- 建议设置合理的文件大小限制

**示例：**
```python
# 从网络读取后发送
import requests
image_data = requests.get("https://example.com/image.jpg").content
send.Image(image_data)

# 从文件读取后发送
with open("/path/to/local/image.jpg", "rb") as f:
    image_data = f.read()
send.Image(image_data)
```

#### 2.1.3 参数处理优先级

当适配器接收到媒体消息参数时，应按以下顺序处理：

1. **URL 参数**：直接使用 URL 发送(部分平台适配器可能存在URL下载后再上传的操作)
2. **文件路径**：检测是否为本地路径，若是则上传文件
3. **二进制数据**：直接上传二进制数据

**适配器实现建议：**
```python
def Image(self, image: Union[bytes, str]):
    if isinstance(image, str):
        # 判断是 URL 还是本地路径
        if image.startswith(("http://", "https://")):
            # URL 直接发送
            return self._send_image_by_url(image)
        else:
            # 本地路径，读取后上传
            with open(image, "rb") as f:
                return self._upload_image(f.read())
    elif isinstance(image, bytes):
        # 二进制数据，直接上传
        return self._upload_image(image)
```

### 2.2 文本消息参数规范

**方法：** `Text`

**参数：** `text` (`str`)

**要求：**
- 支持纯文本内容
- 不进行格式化处理（如 Markdown、HTML）
- 建议限制文本长度（如 2000-5000 字符）
- 超长文本应提示用户截断或分段发送

**示例：**
```python
# 简单文本
send.Text("你好，世界！")

# 长文本（建议分段）
long_text = "很长的文本内容..."
if len(long_text) > 2000:
    # 分段发送
    for i in range(0, len(long_text), 2000):
        send.Text(long_text[i:i+2000])
else:
    send.Text(long_text)
```

### 2.3 @用户参数规范

**方法：** `At`（修饰方法）

**参数：** `user_id` (`str`)

**要求：**
- `user_id` 应为字符串类型的用户标识符
- 不同平台的 `user_id` 格式可能不同（数字、UUID、字符串等）
- 适配器负责将 `user_id` 转换为平台特定的格式

**示例：**
```python
# 单个 @ 用户
send.Text("你好").At("123456")

# 多个 @ 用户（链式调用）
send.Text("大家好").At("123456").At("789012")
```

### 2.4 回复消息参数规范

**方法：** `Reply`（修饰方法）

**参数：** `message_id` (`str`)

**要求：**
- `message_id` 应为字符串类型的消息标识符
- 应为之前收到的消息的 ID
- 某些平台可能不支持回复功能，适配器应优雅降级

**示例：**
```python
# 回复一条消息
send.Text("收到").Reply("msg_123456")
```

### 2.5 卡片消息参数规范

**方法：** `Card`

**参数：** `data` (`dict`)

**要求：**
- `data` 应为字典类型的卡片数据
- 具体格式取决于平台（如 Telegram 的 InlineKeyboard、OneBot12 的 card）
- 适配器应验证数据格式并转换为平台特定格式
- 不支持卡片的平台应降级为文本消息

**示例：**
```python
# 发送卡片数据
card_data = {
    "type": "image",
    "title": "卡片标题",
    "content": "卡片内容",
    "image": "https://example.com/image.jpg"
}
send.Card(card_data)
```

### 2.6 参数验证和错误处理

**通用要求：**
1. **类型检查**：验证参数类型是否正确
2. **范围检查**：验证参数值是否在合理范围内
3. **存在性检查**：验证必需参数是否存在
4. **格式检查**：验证 URL、文件路径等格式是否正确

**错误处理建议：**
```python
def Image(self, image: Union[bytes, str]):
    # 类型检查
    if not isinstance(image, (bytes, str)):
        raise TypeError("参数必须是 bytes 或 str 类型")
    
    # URL 格式检查
    if isinstance(image, str) and not image.startswith(("http://", "https://")):
        # 检查是否为本地文件路径
        if not os.path.exists(image):
            raise FileNotFoundError(f"文件不存在: {image}")
    
    # 文件大小检查
    if isinstance(image, bytes) and len(image) > 10 * 1024 * 1024:  # 10MB
        raise ValueError("文件大小超过限制（10MB）")
    
    # 发送消息
    return self._send_image(image)
```

## 3. 平台特有方法命名

**不推荐**在 Send 类中直接添加平台前缀方法。建议使用通用方法名或 `Raw_{协议}` 方法。

**不推荐：**
```python
def YunhuForm(self, form_id: str):  # ❌ 不推荐
    pass

def TelegramSticker(self, sticker_id: str):  # ❌ 不推荐
    pass
```

**推荐：**
```python
def Form(self, form_id: str):  # ✅ 通用方法名
    pass

def Sticker(self, sticker_id: str):  # ✅ 通用方法名
    pass

# 或使用 Raw 方法
def Raw_ob12(self, message):  # ✅ 发送 OneBot12 格式
    pass
```

## 4. 参数命名规范

| 参数名 | 说明 | 类型 |
|-------|------|------|
| `text` | 文本内容 | `str` |
| `url` / `file` | 文件 URL 或二进制数据 | `str` / `bytes` |
| `user_id` | 用户 ID | `str` / `int` |
| `group_id` | 群组 ID | `str` / `int` |
| `message_id` | 消息 ID | `str` |
| `data` | 数据对象（如卡片数据） | `dict` |

## 5. 返回值规范

- **发送方法**（如 `Text`, `Image`）：必须返回 `asyncio.Task` 对象
- **修饰方法**（如 `At`, `Reply`, `AtAll`）：必须返回 `self` 以支持链式调用

## 6. 相关文档

- [适配器系统 - SendDSL 详解](../core/adapters.md) - 查看调用方法和使用示例
- [适配器开发指南](../development/adapter.md) - 查看适配器实现要求
- [模块开发指南](../development/module.md) - 查看模块中的发送消息示例
