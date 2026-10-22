# ErisPulse 发送方法规范

> [!TIP]
> **什么时候需要读这篇**：当你在适配器中实现 Send 类——方法命名、媒体参数（URL/路径/bytes）的形态支持、`Raw_ob12` 反向转换、合并转发能力时对照本文。不需要则跳过。

本文档定义了 ErisPulse 适配器中 Send 类发送方法的命名规范、参数规范和反向转换要求。

## 0. 关键词约定

本文档中的 **必须（MUST）**、**应当（SHOULD）**、**可以（MAY）** 按以下语义解释（参照 RFC 2119）：

| 关键词 | 语义 | 违反后果 |
|--------|------|---------|
| **必须** | 强制要求，框架行为/跨平台一致性依赖它 | 适配器视为不符合标准，模块代码可能无法工作 |
| **应当** | 强烈推荐；除非有充分理由，否则遵循 | 偏离时须在适配器文档中说明原因与替代行为 |
| **可以** | 可选项，按平台能力自行决定 | 无 |

## 1. 标准方法命名

所有发送方法使用 **大驼峰命名法（PascalCase）**，首字母大写。

### 1.1 标准发送方法

| 方法名 | 说明 | 参数类型 | 实现要求 |
|-------|------|---------|---------|
| `Text` | 发送文本消息 | `str` | 必须 |
| `Image` | 发送图片 | `str` \| `bytes` | 必须（基类已内置，见 §6.4） |
| `Voice` | 发送语音 | `str` \| `bytes` | 必须（基类已内置；平台不支持语音时按 §2.1.5 降级） |
| `Video` | 发送视频 | `str` \| `bytes` | 必须（基类已内置；平台不支持视频时按 §2.1.5 降级） |
| `File` | 发送文件 | `str` \| `bytes`，`filename: str \| None = None` | 必须（基类已内置） |
| `At` | @用户/群组 | `str` (user_id) | 修饰方法，按需 |
| `Face` | 发送表情 | `str` (emoji) | 可以 |
| `Reply` | 回复消息 | `str` (message_id) | 修饰方法，按需 |
| `Forward` | 转发消息 | `str` (message_id) | 可以 |
| `Markdown` | 发送 Markdown 消息 | `str` | 可以 |
| `HTML` | 发送 HTML 消息 | `str` | 可以 |
| `Card` | 发送卡片消息 | `dict` | 可以 |

> 标准方法（`Text`/`Image`/`Voice`/`Video`/`File`）由基类 `SendDSL` 内置并默认委托 `Raw_ob12`，适配器**无需重复实现**即可获得类型签名；仅当平台需要特殊逻辑时才覆盖单个方法（见 §6.4）。

### 1.2 链式修饰方法

| 方法名 | 说明 | 参数类型 |
|-------|------|---------|
| `At` | @用户（可多次调用） | `str` (user_id) |
| `AtAll` | @全体成员 | 无 |
| `Reply` | 回复消息 | `str` (message_id) |

### 1.3 协议方法

| 方法名 | 说明 | 是否必须 |
|-------|------|---------|
| `Raw_ob12` | 发送 OneBot12 格式消息段 | 必须 |

**`Raw_ob12` 是必须实现的方法**。这是适配器的核心职责之一：接收 OneBot12 标准消息段并将其转换为平台原生 API 调用。`Raw_ob12` 是反向转换（OneBot12 → 平台）的统一入口，确保模块可以不依赖平台特有方法，直接使用标准消息段发送消息。

**未重写 `Raw_ob12` 时的行为**：基类默认实现会记录 **error 级别**日志并返回标准错误响应格式（`status: "failed"`, `retcode: 10002`），提示适配器开发者必须实现此方法。

### 1.4 推荐的扩展命名约定

适配器如需支持发送非 OneBot12 格式的原始数据（如平台特定 JSON、XML 等），推荐使用以下命名约定：

| 推荐方法名 | 说明 |
|-----------|------|
| `Raw_json` | 发送任意 JSON 数据 |
| `Raw_xml` | 发送任意 XML 数据 |

**注意**：这些方法**不是**基类提供的默认方法，也不强制要求实现。它们仅作为命名约定，适配器可根据需要自行定义。如果适配器不支持这些格式，则无需定义。

**消息构建器（MessageBuilder）**：ErisPulse 提供了 `MessageBuilder` 工具类，用于方便地构建 OneBot12 消息段列表，配合 `Raw_ob12` 使用。详见 [MessageBuilder 详解](../advanced/message-builder.md)。

## 2. 参数规范详解

### 2.1 媒体消息发送协议（`Image` / `Voice` / `Video` / `File`）

本节是媒体发送的**统一协议标准**：模块以同一份代码调用四个媒体方法，适配器负责把
`file` 参数的各种形态转换为平台原生上传/发送行为。

#### 2.1.1 `file` 参数的合法形态

| 形态 | 示例 | 适配器要求 |
|------|------|-----------|
| HTTP(S) URL | `https://example.com/image.jpg` | **必须**接受 |
| 本地文件路径 | `/path/to/file.jpg`、`C:\path\to\file.jpg` | **必须**接受 |
| 二进制数据 | `b"\x89PNG..."` | **必须**接受 |
| `file://` URI | `file:///path/to/file.jpg` | **应当**接受（可转发为本地路径处理） |
| Base64 字符串 / Data URI | `iVBORw0KGgo=...`、`data:image/png;base64,...` | **应当**接受（与 OneBot12 生态惯例兼容） |

> 适配器**必须**在三种必须形态上行为一致——模块无论传 URL、路径还是 bytes，
> 收到的都是同一条消息。平台无法直接使用某形态时（如平台 API 不支持引用外部 URL），
> 由适配器自行下载/读取后上传，**不得**要求模块换形态重试。

#### 2.1.2 形态判定顺序

适配器实现媒体参数处理时，**应当**按以下顺序判定形态：

1. `bytes` 类型 → 直接上传
2. 字符串以 `http://` / `https://` 开头 → 按 URL 处理（直接引用或下载后上传，按平台能力）
3. 字符串以 `file://` 开头 → 剥离前缀按本地路径处理
4. 其余字符串 → 按本地路径处理（存在则读取上传；不存在则返回标准错误响应）

```python
def _resolve_media(self, file: "str | bytes") -> bytes:
    """形态判定与归一化（示例）"""
    if isinstance(file, (bytes, bytearray)):
        return bytes(file)
    if file.startswith(("http://", "https://")):
        return self._download(file)          # 平台不能引用 URL 时下载
    if file.startswith("file://"):
        file = file[len("file://"):]
    with open(file, "rb") as f:              # 本地路径
        return f.read()
```

#### 2.1.3 `File` 的文件名语义

`File` 方法签名：`File(file, filename=None)`（`filename` 为可选参数，基类已内置）。

文件名**推导顺序**（适配器在未显式提供 `filename` 时按此生成）：

1. 显式 `filename` 参数（最高优先）
2. URL 的 basename（如 `https://host/a/b/report.pdf` → `report.pdf`，须剥离 query string）
3. 本地路径的 basename（如 `/tmp/data/backup.zip` → `backup.zip`）
4. 平台默认生成（如 `file_{timestamp}`；**应当**保留真实扩展名——扩展名影响平台侧的
   类型识别与预览行为）

> `Image` / `Voice` / `Video` 同样**可以**接受 `filename`（经消息段 `data.filename` 传递），
> 但仅 `File` 的文件名有跨平台语义保证。

#### 2.1.4 平台限制的声明义务

各平台对媒体的大小上限、格式（MIME）、时长（音视频）等约束不同。适配器**应当**：

- 在适配器文档中声明支持的媒体类型与限制范围
- 超限或不支持的输入返回**标准错误响应**（`status: "failed"`；`retcode` 使用
  `10002` 或平台语义化错误码，`message` 说明原因），**不得**抛出异常中断模块逻辑

#### 2.1.5 能力降级阶梯

平台不支持某个媒体**类型**时，按以下阶梯降级（遵循总纲"能力降级不报错"原则）：

| 场景 | 降级行为 |
|------|---------|
| `Voice` 不支持语音消息 | **应当**按 `File`（或平台近缘形态）发送；无法表达时返回 `retcode=10002` |
| `Video` 不支持视频消息 | 同上 |
| 媒体类型完全不支持（无文件能力） | 返回 `retcode=10002`，`message` 注明不支持的数据类型 |
| 形态不支持（如无法处理 base64） | 返回 `retcode=10002`，**可以**在 `message` 中提示模块改用 URL/bytes |

**禁止**的行为：静默丢弃（无返回）、抛出异常、要求模块编写平台分支处理。

### 2.2 @用户参数规范

**方法：** `At`（修饰方法）

**参数：** `user_id` (`str`)

**要求：**
- `user_id` 应为字符串类型的用户标识符
- 不同平台的 `user_id` 格式可能不同（数字、UUID、字符串等）
- 适配器负责将 `user_id` 转换为平台特定的格式
- 注意需要把真正的发送方法调用放在最后的位置

**示例：**
```python
# 单个 @ 用户
Send.To("group", "g123").At("123456").Text("你好")

# 多个 @ 用户（链式调用）
send.To("group", "g123").At("123456").At("789012").Text("大家好")
```

### 2.3 回复消息参数规范

**方法：** `Reply`（修饰方法）

**参数：** `message_id` (`str`)

**要求：**
- `message_id` 应为字符串类型的消息标识符
- 应为之前收到的消息的 ID
- 某些平台可能不支持回复功能，适配器应优雅降级

**示例：**
```python
send.To("group", "g123").Reply("msg_123456").Text("收到")
```

### 2.4 合并转发能力（`MergeForward`，可选）

`MergeForward(nodes)` 是**可选的能力方法**：把多段内容打包为「合并转发 / 富文本折叠」形式发送，
由适配器按平台能力决定最佳呈现。与 §1.1 的 `Forward(from_chat_id, message_id)`（转发**已有**消息）
语义不同，二者并存。

> **标准背景**：OneBot12 核心标准没有 node 消息段，也没有合并转发 API——"消息结点"是 OneBot v11
> 生态（go-cqhttp 扩展）的实现层概念，v12 把这类平台特有能力下放给扩展机制。ErisPulse 的落地方式
> 即扩展机制等价物：**不新增标准消息段，而是可选能力方法 + `list_sends` 运行时探测**——实现了
> `MergeForward` 的适配器自动获得能力，未实现的调用方自动回退普通文本，模块零改动。

**方法签名：**

```python
def MergeForward(self, nodes: List[Dict]) -> asyncio.Task:
    """
    发送合并转发 / 富文本折叠消息

    :param nodes: 合并转发节点数组（go-cqhttp 扩展的 OneBot v11 节点格式）：
        [
            {
                "type": "node",
                "data": {
                    "user_id": "10000",     # 展示用发送者 id
                    "nickname": "MyBot",     # 展示用发送者昵称
                    "content": [            # 消息段数组，当前为 text 段
                        {"type": "text", "data": {"text": "【1/3】标题\n正文…"}}
                    ],
                },
            },
        ]
    :return: asyncio.Task，await 后返回标准响应格式
    """
```

**实现要求：**

1. **平台有原生合并转发**（OneBot11 系）：**必须**调用协议端专用端点
   （`send_group_forward_msg` / `send_private_forward_msg`）——NapCat 等实现会拒绝
   `send_msg` 携带的 node 段（retcode 1400）；专用端点失败时**可以**回退 `send_msg` 直发 node 段
2. **平台无原生转发但有富文本**（云湖 / Telegram / Kook / Discord / Matrix 等）：
   **应当**将节点渲染为平台的富文本折叠形态（HTML 折叠卡 / Card / Embed / blockquote 列表），
   参考样式与逐适配器任务清单见 `SDK/Adapter/ADAPTER_FORWARD_GUIDE.md`
3. **两者皆无**：**不得**实现本方法（更不得返回成功却把 node 字典当纯文本发出）——
   不实现时 `list_sends` 不含 `MergeForward`，调用方自动回退普通文本
4. **失败语义**：返回标准错误响应（`status: "failed"`）或抛出异常均可，调用方会回退纯文本发送，内容不丢失
5. **不得**在 `MergeForward` 内部再调用 `Raw_ob12` 发送同样的 nodes（OneBot11 的 `Raw_ob12`
   已内置纯 node 段自动路由，会成环）
6. **出站 node 段解析**（全适配器约定）：各适配器的 `Raw_ob12` 段分发应注册 `node` 段——
   纯 node 列表自动路由到本适配器的合并转发呈现（有 `MergeForward` 的平台等价于直接调用；
   无该方法的平台提取各节点文本以「昵称: 正文」逐行**原文输出**）；混合列表中 node 段的文本并入正文。
   任何适配器收到 node 段都不得静默丢弃。

**平台实现形态（详见 `SDK/Adapter/ADAPTER_FORWARD_GUIDE.md`）：**

- 原生端点：OneBot11、SnowLuma（三级回退：`send_group/private_forward_msg` 专用端点 → `upload_forward_msg`
  取 resid 发 forward 段 → 直发 node 段；SnowLuma API 全面向 NapCat 对齐，适配器可直接连接 NapCat 后端）
- 折叠 HTML `<details>` 卡：云湖（bot/用户协议）、Email、Sandbox、Allons(Ideaura)
- 白名单 HTML / 引用块：Telegram（`<b>`+`<blockquote>`）、Matrix（blockquote 变体，白名单剥离 details/内联样式）
- 平台卡片：Kook（Card header+section）、Discord（Embed fields）
- 官方 Markdown 引用列表：QQBot（官方 md 无折叠语法，服务端校验拒绝无效标签 40034011）
- 不实现（node 段原文输出降级）：OneBot12（标准无 node 段）、WeCom、Terminal、Webhook、WechatMp

**调用方探测示例：**

```python
sends = adapter.list_sends(platform)
if "MergeForward" in sends:
    await adapter.Send.To("group", "123").MergeForward(nodes)
else:
    await adapter.Send.To("group", "123").Text(plain_text)
```

> 参考实现：`ErisPulse-OneBot11Adapter`（专用端点 → `send_msg` 回退）；渲染模板与各适配器任务清单见
> `SDK/Adapter/ADAPTER_FORWARD_GUIDE.md`。

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

def Raw_ob12(self, message):  # ✅ 发送 OneBot12 格式
    pass
```

**扩展方法要求**：
- 方法名使用 PascalCase，不加平台前缀
- 必须返回 `asyncio.Task` 对象
- 必须提供完整的类型注解和文档字符串
- 参数设计应尽量与标准方法风格一致

## 4. 参数命名规范

| 参数名 | 说明 | 类型 |
|-------|------|------|
| `text` | 文本内容 | `str` |
| `file` | 媒体内容（URL / 路径 / 二进制，见 §2.1.1） | `str` / `bytes` |
| `filename` | 文件名（`File` 可选，见 §2.1.3） | `str` / `None` |
| `user_id` | 用户 ID | `str` / `int` |
| `group_id` | 群组 ID | `str` / `int` |
| `message_id` | 消息 ID | `str` |
| `data` | 数据对象（如卡片数据） | `dict` |

## 5. 返回值规范

- **发送方法**（如 `Text`, `Image`）：必须返回 `asyncio.Task` 对象
- **修饰方法**（如 `At`, `Reply`, `AtAll`）：必须返回 `self` 以支持链式调用

---

## 6. 反向转换规范（OneBot12 → 平台）

适配器不仅需要将平台原生事件转换为 OneBot12 格式（正向转换），还**必须**提供将 OneBot12 消息段转换回平台原生 API 调用的能力（反向转换）。反向转换的统一入口是 `Raw_ob12` 方法。

### 6.1 转换模型

```
正向转换（接收方向）                反向转换（发送方向）
─────────────────                ─────────────────
平台原生事件                       OneBot12 消息段列表
    │                                  │
    ▼                                  ▼
Converter.convert()               Send.Raw_ob12()
    │                                  │
    ▼                                  ▼
OneBot12 标准事件                  平台原生 API 调用
（含 {platform}_raw）             （返回标准响应格式）
```

**核心对称性**：正向转换保留原始数据在 `{platform}_raw` 中，反向转换接受 OneBot12 标准格式并还原为平台调用。

### 6.2 `Raw_ob12` 实现规范

`Raw_ob12` 接收 OneBot12 标准消息段列表，必须将其转换为平台原生 API 调用。

**方法签名**：

```python
def Raw_ob12(self, message_segments: List[Dict]) -> asyncio.Task:
    """
    发送 OneBot12 标准消息段

    :param message_segments: OneBot12 消息段列表
        [
            {"type": "text", "data": {"text": "Hello"}},
            {"type": "image", "data": {"file": "https://..."}},
            {"type": "mention", "data": {"user_id": "123"}},
        ]
    :return: asyncio.Task，await 后返回标准响应格式
    """
```

**实现要求**：

1. **必须处理所有标准消息段类型**：至少支持 `text`、`image`、`audio`、`video`、`file`、`mention`、`reply`
2. **必须处理平台扩展消息段**：对于 `{platform}_xxx` 类型的消息段，转换为平台对应的原生调用
3. **必须返回标准响应格式**：遵循 [API 响应标准](api-response.md)
4. **不支持的消息段应跳过并记录警告**，不应抛出异常导致整条消息发送失败

### 6.3 消息段转换规则

#### 6.3.1 标准消息段转换

适配器必须实现以下标准消息段的转换：

| OneBot12 消息段 | 转换要求 |
|----------------|---------|
| `text` | 直接使用 `data.text` |
| `image` | `data.file` 按 §2.1 媒体协议处理（三必须形态 + 判定顺序） |
| `audio` | 同 image 处理逻辑 |
| `video` | 同 image 处理逻辑 |
| `file` | 同 image 处理逻辑；文件名按 §2.1.3 推导顺序处理 `data.filename` |
| `mention` | 转换为平台的 @用户 机制（如 Telegram 的 `entities`，云湖的 `at_uid`） |
| `reply` | 转换为平台的回复引用机制 |
| `face` | 转换为平台的表情发送机制，不支持则跳过 |
| `location` | 转换为平台的位置发送机制，不支持则跳过 |

#### 6.3.2 平台扩展消息段转换

对于带平台前缀的消息段，适配器应识别并转换：

```python
def _convert_ob12_segments(self, segments: List[Dict]) -> Any:
    """将 OneBot12 消息段转换为平台原生格式"""
    platform_prefix = f"{self._platform_name}_"
    
    for segment in segments:
        seg_type = segment["type"]
        seg_data = segment["data"]
        
        if seg_type.startswith(platform_prefix):
            # 平台扩展消息段 → 平台原生调用
            self._handle_platform_segment(seg_type, seg_data)
        elif seg_type in self._standard_segment_handlers:
            # 标准消息段 → 平台等价操作
            self._standard_segment_handlers[seg_type](seg_data)
        else:
            # 未知消息段 → 记录警告并跳过
            logger.warning(f"不支持的消息段类型: {seg_type}")
```

#### 6.3.3 复合消息段处理

一条消息可能包含多个消息段，适配器需要正确处理复合消息：

```python
# 模块发送包含文本+图片+@用户 的消息
await send.Raw_ob12([
    {"type": "mention", "data": {"user_id": "123"}},
    {"type": "text", "data": {"text": "你好"}},
    {"type": "image", "data": {"file": "https://example.com/img.jpg"}}
])
```

**处理策略**：
- **优先合并**：如果平台支持在一条消息中同时包含文本、图片、@等，应合并发送
- **退而拆分**：如果平台不支持合并，按顺序拆分为多条消息发送
- **保持顺序**：消息段的发送顺序应与列表顺序一致

### 6.4 `Raw_ob12` 与标准方法的关系

适配器的标准发送方法（`Text`、`Image` 等）**已由 `SendDSL` 基类内置实现并默认委托给 `Raw_ob12`**，适配器子类无需重复实现：

```python
class Send(SendDSL):
    def Raw_ob12(self, message_segments: List[Dict]) -> asyncio.Task:
        """核心实现：OneBot12 消息段 → 平台 API（必须实现）"""
        return asyncio.create_task(self._send_ob12(message_segments))

    # Text/Image/Voice/Video/File 已从基类继承，自动委托 Raw_ob12
    # 如需平台特定逻辑，可覆盖单个方法：
    # def Text(self, text: str) -> asyncio.Task:
    #     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

**好处**：
- 转换逻辑集中在 `Raw_ob12` 一处，减少重复代码
- 标准方法和 `Raw_ob12` 行为完全一致
- 模块无论使用 `Text()` 还是 `Raw_ob12()` 都能得到相同结果
- 基类提供类型签名，IDE 能补全标准方法

### 6.5 实现示例

```python
class YunhuSend(SendDSL):
    """云湖平台 Send 实现"""
    
    def Raw_ob12(self, message_segments: list) -> asyncio.Task:
        """OneBot12 消息段 → 云湖 API 调用"""
        return asyncio.create_task(self._do_send(message_segments))
    
    async def _do_send(self, segments: list) -> dict:
        """实际发送逻辑"""
        # 1. 解析修饰器状态
        at_users = self._at_users or []
        reply_to = self._reply_to
        at_all = self._at_all
        
        # 2. 转换消息段
        yunhu_elements = []
        for seg in segments:
            seg_type = seg["type"]
            seg_data = seg["data"]
            
            if seg_type == "text":
                yunhu_elements.append({"type": "text", "content": seg_data["text"]})
            elif seg_type == "image":
                yunhu_elements.append({"type": "image", "url": seg_data["file"]})
            elif seg_type == "mention":
                at_users.append(seg_data["user_id"])
            elif seg_type == "reply":
                reply_to = seg_data["message_id"]
            elif seg_type == "yunhu_form":
                # 平台扩展消息段
                yunhu_elements.append({"type": "form", "form_id": seg_data["form_id"]})
            else:
                logger.warning(f"云湖不支持的消息段: {seg_type}")
        
        # 3. 调用云湖 API
        response = await self._call_yunhu_api(yunhu_elements, at_users, reply_to, at_all)
        
        # 4. 返回标准响应格式
        return {
            "status": "ok" if response["code"] == 0 else "failed",
            "retcode": response["code"],
            "data": {"message_id": response.get("msg_id", ""), "time": int(time.time())},
            "message_id": response.get("msg_id", ""),
            "message": "",
            "yunhu_raw": response
        }
```

---

## 7. 方法发现

模块开发者可以通过 API 查询适配器支持的发送方法（**不要**在模块中硬编码某平台的方法
清单——各适配器的扩展方法随版本演进，以运行时发现为准）：

```python
from ErisPulse import adapter

# 列出所有发送方法
methods = adapter.list_sends("myplatform")
# ["Batch", "Form", "Image", "Recall", "Sticker", "Text", ...]

# 查看方法详情
info = adapter.send_info("myplatform", "Form")
# {
#     "name": "Form",
#     "parameters": [{"name": "form_id", "type": "str", ...}],
#     "return_type": "Awaitable[Any]",
#     "docstring": "发送云湖表单"
# }
```

---

## 9. 适配器开发注意事项

关于如何正确重写 `BaseAdapter`、`Send`、`Request` 的 `__init__`，详见 [适配器开发入门 - `__init__` 注意事项](../developer-guide/adapters/getting-started.md#init-注意事项)。

---

---

## 10. 适配器实现检查清单

### 发送方法
- [ ] 标准方法（`Text`, `Image` 等）已实现
- [ ] 返回值均为 `asyncio.Task`
- [ ] 修饰方法（`At`, `Reply`, `AtAll`）返回 `self`
- [ ] 平台扩展方法使用 PascalCase，无平台前缀
- [ ] 所有方法有完整的类型注解和文档字符串

### 媒体发送协议
- [ ] `file` 参数**必须形态**全部支持：HTTP(S) URL / 本地路径 / `bytes`（见 §2.1.1）
- [ ] 形态判定顺序符合 §2.1.2（bytes → URL → `file://` → 路径）
- [ ] `File` 的文件名推导顺序符合 §2.1.3（显式 `filename` > URL basename > 路径 basename > 平台默认）
- [ ] 平台的媒体限制（大小 / MIME / 时长）已在适配器文档声明（§2.1.4）
- [ ] 不支持的媒体类型按 §2.1.5 降级阶梯处理：近缘类型降级或返回 `retcode=10002`，不抛异常、不静默丢弃

### 合并转发（可选，见 §2.4）
- [ ] 平台有原生合并转发时，`MergeForward` 走协议专用端点，失败回退 `send_msg`（OneBot11 系）
- [ ] 平台无原生转发但有富文本时，`MergeForward` 渲染为平台折叠形态（HTML 卡 / Card / Embed / blockquote）
- [ ] 两者皆无时**不实现** `MergeForward`，不返回成功却发出 node 字典纯文本
- [ ] `MergeForward` 内部不再调 `Raw_ob12` 转发同样 nodes

### 反向转换
- [ ] `Raw_ob12` **已实现**（必须，不可跳过）
- [ ] `Raw_ob12` 能处理所有标准消息段（`text`, `image`, `audio`, `video`, `file`, `mention`, `reply`）
- [ ] `Raw_ob12` 能处理平台扩展消息段（`{platform}_xxx` 类型）
- [ ] 标准发送方法（`Text`, `Image` 等）内部委托给 `Raw_ob12`，而非独立实现转换逻辑
- [ ] 不支持的消息段跳过并记录警告，不抛出异常
- [ ] 复合消息段正确处理（合并或按序拆分）

---

## 11. 消息构建器（MessageBuilder）——适配器侧须知

`MessageBuilder` 是 ErisPulse 提供的 OneBot12 消息段构建工具，供**模块侧**构建消息：
链式调用（或静态快速构建）最终产出标准消息段列表 `[{"type": ..., "data": ...}]`，
由调用方直接传给 `Raw_ob12`。

**适配器侧只需知道这一点**：`Raw_ob12` 接收到的就是这份产物——与手写的消息段列表
完全同构，按 §6.2 的段分发逻辑处理即可，无需感知它来自 MessageBuilder 还是字面量。

> 完整用法（双模式机制、全部消息段方法、`copy()` / `clear()` 工具方法与示例）见
> [MessageBuilder 详解](../advanced/message-builder.md)，本篇不再重复。

---

## 12. 相关文档

**实现发送返回值时配套对照**：
- [API 响应标准](api-response.md) - 适配器 API 响应格式标准

**同一适配器的其它侧**：
- [事件转换标准](event-conversion.md) - 完整的事件转换规范、扩展命名和消息段标准
- [会话类型标准](session-types.md) - 会话类型定义和映射关系
- [请求操作规范](request-action-spec.md) - 请求事件字段要求、HandleRequest DSL 及适配器实现要求