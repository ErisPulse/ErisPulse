# ErisPulse 發送方法規範

本文檔定義了 ErisPulse 適配器中 Send 類發送方法的命名規範、參數規範和反向轉換要求。

## 0. 關鍵詞約定

本文檔中的 **必須（MUST）**、**應當（SHOULD）**、**可以（MAY）** 按以下語義解釋（參照 RFC 2119）：

| 關鍵詞 | 語義 | 違反後果 |
|--------|------|---------|
| **必須** | 強制要求，框架行為/跨平台一致性依賴它 | 適配器視為不符合標準，模組代碼可能無法工作 |
| **應當** | 強烈推薦；除非有充分理由，否則遵循 | 偏離時須在適配器文件中說明原因與替代行為 |
| **可以** | 可選項，按平台能力自行決定 | 無 |

## 1. 標準方法命名

所有發送方法使用 **大駝峰命名法（PascalCase）**，首字母大寫。

### 1.1 標準發送方法

| 方法名 | 說明 | 參數類型 | 實現要求 |
|-------|------|---------|---------|
| `Text` | 發送文本消息 | `str` | 必須 |
| `Image` | 發送圖片 | `str` \| `bytes` | 必須（基類已內置，見 §6.4） |
| `Voice` | 發送語音 | `str` \| `bytes` | 必須（基類已內置；平台不支援語音時按 §2.1.5 降級） |
| `Video` | 發送影片 | `str` \| `bytes` | 必須（基類已內置；平台不支援影片時按 §2.1.5 降級） |
| `File` | 發送檔案 | `str` \| `bytes`，`filename: str \| None = None` | 必須（基類已內置） |
| `At` | @使用者/群組 | `str` (user_id) | 修飾方法，按需 |
| `Face` | 發送表情 | `str` (emoji) | 可以 |
| `Reply` | 回覆訊息 | `str` (message_id) | 修飾方法，按需 |
| `Forward` | 轉發訊息 | `str` (message_id) | 可以 |
| `Markdown` | 發送 Markdown 消息 | `str` | 可以 |
| `HTML` | 發送 HTML 消息 | `str` | 可以 |
| `Card` | 發送卡片消息 | `dict` | 可以 |

> 標準方法（`Text`/`Image`/`Voice`/`Video`/`File`）由基類 `SendDSL` 內置並預設委派 `Raw_ob12`，適配器**無需重複實現**即可獲得類型簽名；僅當平台需要特殊邏輯時才覆蓋單個方法（見 §6.4）。

### 1.2 鏈式修飾方法

| 方法名 | 說明 | 參數類型 |
|-------|------|---------|
| `At` | @使用者（可多次呼叫） | `str` (user_id) |
| `AtAll` | @全體成員 | 無 |
| `Reply` | 回覆訊息 | `str` (message_id) |

### 1.3 協議方法

| 方法名 | 說明 | 是否必須 |
|-------|------|---------|
| `Raw_ob12` | 發送 OneBot12 格式訊息段 | 必須 |

**`Raw_ob12` 是必須實現的方法**。這是適配器的核心職責之一：接收 OneBot12 標準訊息段並將其轉換為平台原生 API 呼叫。`Raw_ob12` 是反向轉換（OneBot12 → 平台）的統一入口，確保模組可以不依賴平台特有方法，直接使用標準訊息段發送訊息。

**未重寫 `Raw_ob12` 時的行為**：基類預設實現會記錄 **error 級別**日誌並返回標準錯誤回應格式（`status: "failed"`, `retcode: 10002`），提示適配器開發者必須實現此方法。

### 1.4 推薦的擴展命名約定

適配器如需支援發送非 OneBot12 格式的原始資料（如平台特定 JSON、XML 等），推薦使用以下命名約定：

| 推薦方法名 | 說明 |
|-----------|------|
| `Raw_json` | 發送任意 JSON 資料 |
| `Raw_xml` | 發送任意 XML 資料 |

**注意**：這些方法**不是**基類提供的預設方法，也不強制要求實現。它們僅作為命名約定，適配器可依需要自行定義。如果適配器不支援這些格式，則無需定義。

**訊息建構器（MessageBuilder）**：ErisPulse 提供了 `MessageBuilder` 工具類，用於方便地建構 OneBot12 訊息段列表，配合 `Raw_ob12` 使用。詳見 [訊息建構器](#11-訊息建構器-messagebuilder) 章節。

## 2. 參數規範詳解

### 2.1 媒體訊息發送協定（`Image` / `Voice` / `Video` / `File`）

本節是媒體發送的**統一協定標準**：模組以同一份程式碼呼叫四個媒體方法，適配器負責將
`file` 參數的各種形態轉換為平台原生的上傳/發送行為。

#### 2.1.1 `file` 參數的合法形態

| 形態 | 示例 | 適配器要求 |
|------|------|-----------|
| HTTP(S) URL | `https://example.com/image.jpg` | **必須**接受 |
| 本地檔案路徑 | `/path/to/file.jpg`、`C:\path\to\file.jpg` | **必須**接受 |
| 二進位數據 | `b"\x89PNG..."` | **必須**接受 |
| `file://` URI | `file:///path/to/file.jpg` | **應當**接受（可轉發為本地路徑處理） |
| Base64 字串 / Data URI | `iVBORw0KGgo=...`、`data:image/png;base64,...` | **應當**接受（與 OneBot12 生態慣例相容） |

> 適配器**必須**在三種必須形態上行為一致——模組無論傳 URL、路徑還是 bytes，
> 收到的都是同一條訊息。平台無法直接使用某形態時（如平台 API 不支援引用外部 URL），
> 由適配器自行下載/讀取後上傳，**不得**要求模組換形態重試。

#### 2.1.2 形態判定順序

適配器實作媒體參數處理時，**應當**按以下順序判定形態：

1. `bytes` 類型 → 直接上傳
2. 字串以 `http://` / `https://` 開頭 → 按 URL 處理（直接引用或下載後上傳，按平台能力）
3. 字串以 `file://` 開頭 → 剝離前綴按本地路徑處理
4. 其餘字串 → 按本地路徑處理（存在則讀取上傳；不存在則返回標準錯誤回應）

```python
def _resolve_media(self, file: "str | bytes") -> bytes:
    """形態判定與歸一化（示例）"""
    if isinstance(file, (bytes, bytearray)):
        return bytes(file)
    if file.startswith(("http://", "https://")):
        return self._download(file)          # 平台不能引用 URL 時下載
    if file.startswith("file://"):
        file = file[len("file://"):]
    with open(file, "rb") as f:              # 本地路徑
        return f.read()
```

#### 2.1.3 `File` 的檔案名語義

`File` 方法簽名：`File(file, filename=None)`（`filename` 為可選參數，基類已內建）。

檔案名**推導順序**（適配器在未顯式提供 `filename` 時按此生成）：

1. 显式 `filename` 參數（最高優先）
2. URL 的 basename（如 `https://host/a/b/report.pdf` → `report.pdf`，須剝離 query string）
3. 本地路徑的 basename（如 `/tmp/data/backup.zip` → `backup.zip`）
4. 平台預設生成（如 `file_{timestamp}`；**應當**保留真實副檔名——副檔名影響平台側的
   類型識別與預覽行為）

> `Image` / `Voice` / `Video` 同樣**可以**接受 `filename`（經訊息段 `data.filename` 傳遞），
> 但僅 `File` 的檔案名有跨平台語義保證。

#### 2.1.4 平台限制的聲明義務

各平台對媒體的大小上限、格式（MIME）、時長（音訊/視訊）等限制不同。適配器**應當**：

- 在適配器文件中聲明支援的媒體類型與限制範圍
- 超限或不支援的輸入返回**標準錯誤回應**（`status: "failed"`；`retcode` 使用
  `10002` 或平台語義化錯誤碼，`message` 說明原因），**不得**拋出例外中斷模組邏輯

#### 2.1.5 能力降級階梯

平台不支援某個媒體**類型**時，按以下階梯降級（遵循總綱"能力降級不報錯"原則）：

| 場景 | 降級行為 |
|------|---------|
| `Voice` 不支援語音訊息 | **應當**按 `File`（或平台近緣形態）發送；無法表達時返回 `retcode=10002` |
| `Video` 不支援視訊訊息 | 同上 |
| 媒體類型完全不支援（無檔案能力） | 返回 `retcode=10002`，`message` 注明不支援的資料類型 |
| 形態不支援（如無法處理 base64） | 返回 `retcode=10002`，**可以**在 `message` 中提示模組改用 URL/bytes |

**禁止**的行為：靜默丟棄（無回應）、拋出例外、要求模組編寫平台分支處理。

### 2.2 @使用者參數規範

**方法：** `At`（修飾方法）

**參數：** `user_id` (`str`)

**要求：**
- `user_id` 應為字串類型的使用者標識符
- 不同平台的 `user_id` 格式可能不同（數字、UUID、字串等）
- 適配器負責將 `user_id` 轉換為平台特定的格式
- 注意需要把真正的發送方法呼叫放在最後的位置

**示例：**
```python
# 單個 @ 使用者
Send.To("group", "g123").At("123456").Text("你好")

# 多個 @ 使用者（鏈式呼叫）
send.To("group", "g123").At("123456").At("789012").Text("大家好")
```

### 2.3 回覆訊息參數規範

**方法：** `Reply`（修飾方法）

**參數：** `message_id` (`str`)

**要求：**
- `message_id` 應為字串類型的訊息標識符
- 應為之前收到的訊息的 ID
- 某些平台可能不支援回覆功能，適配器應優雅降級

**示例：**
```python
send.To("group", "g123").Reply("msg_123456").Text("收到")
```

## 3. 平台特有方法命名

**不建議**在 Send 類中直接添加平台前綴方法。建議使用通用方法名或 `Raw_{協議}` 方法。

**不建議：**
```python
def YunhuForm(self, form_id: str):  # ❌ 不建議
    pass

def TelegramSticker(self, sticker_id: str):  # ❌ 不建議
    pass
```

**建議：**
```python
def Form(self, form_id: str):  # ✅ 通用方法名
    pass

def Sticker(self, sticker_id: str):  # ✅ 通用方法名
    pass

def Raw_ob12(self, message):  # ✅ 發送 OneBot12 格式
    pass
```

**擴展方法要求**：
- 方法名使用 PascalCase，不加平台前綴
- 必須返回 `asyncio.Task` 對象
- 必須提供完整的類型註解和文件字串
- 參數設計應盡量與標準方法風格一致

## 4. 參數命名規範

| 參數名 | 說明 | 類型 |
|-------|------|------|
| `text` | 文本內容 | `str` |
| `file` | 媒體內容（URL / 路徑 / 二進制，見 §2.1.1） | `str` / `bytes` |
| `filename` | 檔案名（`File` 可選，見 §2.1.3） | `str` / `None` |
| `user_id` | 用戶 ID | `str` / `int` |
| `group_id` | 群組 ID | `str` / `int` |
| `message_id` | 消息 ID | `str` |
| `data` | 數據物件（如卡片數據） | `dict` |

## 5. 返回值規範

- **發送方法**（例如 `Text`, `Image`）：必須返回 `asyncio.Task` 物件
- **修飾方法**（例如 `At`, `Reply`, `AtAll`）：必須返回 `self` 以支援鏈式呼叫

---

## 6. 反向轉換規範（OneBot12 → 平台）

適配器不僅需要將平台原生事件轉換為 OneBot12 格式（正向轉換），還**必須**提供將 OneBot12 消息段轉換回平台原生 API 調用的能力（反向轉換）。反向轉換的統一入口是 `Raw_ob12` 方法。

### 6.1 轉換模型

```
正向轉換（接收方向）                反向轉換（發送方向）
─────────────────                ─────────────────
平台原生事件                       OneBot12 消息段列表
    │                                  │
    ▼                                  ▼
Converter.convert()               Send.Raw_ob12()
    │                                  │
    ▼                                  ▼
OneBot12 標準事件                  平台原生 API 調用
（含 {platform}_raw）             （返回標準響應格式）
```

**核心對稱性**：正向轉換保留原始數據在 `{platform}_raw` 中，反向轉換接受 OneBot12 標準格式並還原為平台調用。

### 6.2 `Raw_ob12` 實現規範

`Raw_ob12` 接收 OneBot12 標準消息段列表，必須將其轉換為平台原生 API 調用。

**方法簽名**：

```python
def Raw_ob12(self, message_segments: List[Dict]) -> asyncio.Task:
    """
    發送 OneBot12 標準消息段

    :param message_segments: OneBot12 消息段列表
        [
            {"type": "text", "data": {"text": "Hello"}},
            {"type": "image", "data": {"file": "https://..."}},
            {"type": "mention", "data": {"user_id": "123"}},
        ]
    :return: asyncio.Task，await 後返回標準響應格式
    """
```

**實現要求**：

1. **必須處理所有標準消息段類型**：至少支援 `text`、`image`、`audio`、`video`、`file`、`mention`、`reply`
2. **必須處理平台擴展消息段**：對於 `{platform}_xxx` 類型的消息段，轉換為平台對應的原生調用
3. **必須返回標準響應格式**：遵循 [API 響應標準](api-response.md)
4. **不支援的消息段應跳過並記錄警告**，不應拋出異常導致整條消息發送失敗

### 6.3 消息段轉換規則

#### 6.3.1 標準消息段轉換

適配器必須實現以下標準消息段的轉換：

| OneBot12 消息段 | 轉換要求 |
|----------------|---------|
| `text` | 直接使用 `data.text` |
| `image` | `data.file` 按 §2.1 媒體協議處理（三必須形態 + 判定順序） |
| `audio` | 同 image 處理邏輯 |
| `video` | 同 image 處理邏輯 |
| `file` | 同 image 處理邏輯；檔案名按 §2.1.3 推導順序處理 `data.filename` |
| `mention` | 轉換為平台的 @使用者 機制（如 Telegram 的 `entities`，雲湖的 `at_uid`） |
| `reply` | 轉換為平台的回覆引用機制 |
| `face` | 轉換為平台的表情發送機制，不支援則跳過 |
| `location` | 轉換為平台的位置發送機制，不支援則跳過 |

#### 6.3.2 平台擴展消息段轉換

對於帶平台前綴的消息段，適配器應識別並轉換：

```python
def _convert_ob12_segments(self, segments: List[Dict]) -> Any:
    """將 OneBot12 消息段轉換為平台原生格式"""
    platform_prefix = f"{self._platform_name}_"
    
    for segment in segments:
        seg_type = segment["type"]
        seg_data = segment["data"]
        
        if seg_type.startswith(platform_prefix):
            # 平台擴展消息段 → 平台原生調用
            self._handle_platform_segment(seg_type, seg_data)
        elif seg_type in self._standard_segment_handlers:
            # 標準消息段 → 平台等價操作
            self._standard_segment_handlers[seg_type](seg_data)
        else:
            # 未知消息段 → 記錄警告並跳過
            logger.warning(f"不支援的消息段類型: {seg_type}")
```

#### 6.3.3 複合消息段處理

一條訊息可能包含多個消息段，適配器需要正確處理複合訊息：

```python
# 模組發送包含文字+圖片+@使用者 的訊息
await send.Raw_ob12([
    {"type": "mention", "data": {"user_id": "123"}},
    {"type": "text", "data": {"text": "你好"}},
    {"type": "image", "data": {"file": "https://example.com/img.jpg"}}
])
```

**處理策略**：
- **優先合併**：如果平台支援在一條訊息中同時包含文字、圖片、@等，應合併發送
- **退而拆分**：如果平台不支援合併，按順序拆分為多條訊息發送
- **保持順序**：消息段的發送順序應與列表順序一致

### 6.4 `Raw_ob12` 與標準方法的關係

適配器的標準發送方法（`Text`、`Image` 等）**已由 `SendDSL` 基類內建實現並預設委託給 `Raw_ob12`**，適配器子類無需重複實現：

```python
class Send(SendDSL):
    def Raw_ob12(self, message_segments: List[Dict]) -> asyncio.Task:
        """核心實現：OneBot12 消息段 → 平台 API（必須實現）"""
        return asyncio.create_task(self._send_ob12(message_segments))

    # Text/Image/Voice/Video/File 已從基類繼承，自動委託 Raw_ob12
    # 如需平台特定邏輯，可覆蓋單個方法：
    # def Text(self, text: str) -> asyncio.Task:
    #     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

**好處**：
- 轉換邏輯集中在 `Raw_ob12` 一處，減少重複程式碼
- 標準方法和 `Raw_ob12` 行為完全一致
- 模組無論使用 `Text()` 還是 `Raw_ob12()` 都能得到相同結果
- 基類提供類型簽名，IDE 能補全標準方法

### 6.5 實現範例

```python
class YunhuSend(SendDSL):
    """雲湖平台 Send 實現"""
    
    def Raw_ob12(self, message_segments: list) -> asyncio.Task:
        """OneBot12 消息段 → 雲湖 API 調用"""
        return asyncio.create_task(self._do_send(message_segments))
    
    async def _do_send(self, segments: list) -> dict:
        """實際發送邏輯"""
        # 1. 解析修飾器狀態
        at_users = self._at_users or []
        reply_to = self._reply_to
        at_all = self._at_all
        
        # 2. 轉換消息段
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
                # 平台擴展消息段
                yunhu_elements.append({"type": "form", "form_id": seg_data["form_id"]})
            else:
                logger.warning(f"雲湖不支援的消息段: {seg_type}")
        
        # 3. 調用雲湖 API
        response = await self._call_yunhu_api(yunhu_elements, at_users, reply_to, at_all)
        
        # 4. 返回標準響應格式
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

## 7. 方法發現

模組開發者可以透過 API 查詢適配器支援的發送方法（**不要**在模組中硬編碼某平台的方法清單——各適配器的擴展方法會隨版本演進，請以執行時發現為準）：

```python
from ErisPulse import adapter

# 列出所有發送方法
methods = adapter.list_sends("myplatform")
# ["Batch", "Form", "Image", "Recall", "Sticker", "Text", ...]

# 查看方法詳情
info = adapter.send_info("myplatform", "Form")
# {
#     "name": "Form",
#     "parameters": [{"name": "form_id", "type": "str", ...}],
#     "return_type": "Awaitable[Any]",
#     "docstring": "發送雲湖表單"
# }
```

---

## 9. 適配器開發注意事項

關於如何正確重寫 `BaseAdapter`、`Send`、`Request` 的 `__init__`，詳見 [適配器開發入門 - `__init__` 注意事項](../developer-guide/adapters/getting-started.md#init-注意事項)。

## 10. 适配器實現檢查清單

### 發送方法
- [ ] 標準方法（`Text`, `Image` 等）已實現
- [ ] 返回值均為 `asyncio.Task`
- [ ] 修飾方法（`At`, `Reply`, `AtAll`）返回 `self`
- [ ] 平台擴展方法使用 PascalCase，無平台前綴
- [ ] 所有方法有完整的類型註解和文件字串

### 媒體發送協議
- [ ] `file` 參數**必須形態**全部支援：HTTP(S) URL / 本地路徑 / `bytes`（見 §2.1.1）
- [ ] 形態判定順序符合 §2.1.2（bytes → URL → `file://` → 路徑）
- [ ] `File` 的檔案名推導順序符合 §2.1.3（顯式 `filename` > URL basename > 路徑 basename > 平台預設）
- [ ] 平台的媒體限制（大小 / MIME / 時長）已在適配器文件中聲明（§2.1.4）
- [ ] 不支援的媒體類型按 §2.1.5 降級階梯處理：近緣類型降級或返回 `retcode=10002`，不拋異常、不靜默丟棄

### 反向轉換
- [ ] `Raw_ob12` **已實現**（必須，不可跳過）
- [ ] `Raw_ob12` 能處理所有標準訊息段（`text`, `image`, `audio`, `video`, `file`, `mention`, `reply`）
- [ ] `Raw_ob12` 能處理平台擴展訊息段（`{platform}_xxx` 類型）
- [ ] 標準發送方法（`Text`, `Image` 等）內部委託給 `Raw_ob12`，而非獨立實現轉換邏輯
- [ ] 不支援的訊息段跳過並記錄警告，不拋出異常
- [ ] 複合訊息段正確處理（合併或按序拆分）

## 11. 消息建構器（MessageBuilder）

`MessageBuilder` 是 ErisPulse 提供的消息段建構工具，配合 `Raw_ob12` 使用，簡化 OneBot12 消息段的建構過程。

### 11.1 導入

```python
from ErisPulse.Core import MessageBuilder
# 或
from ErisPulse.Core.Event import MessageBuilder
```

### 11.2 鏈式呼叫建構

```python
# 建構包含文字、圖片、@使用者的消息
segments = (
    MessageBuilder()
    .mention("123456")
    .text("你好，看看這張圖")
    .image("https://example.com/img.jpg")
    .reply("msg_789")
    .build()
)

# 發送
await adapter.Send.To("group", "456").Raw_ob12(segments)
```

### 11.3 快速建構單段

```python
# 快速建構單個消息段（返回 list[dict]，可直接傳給 Raw_ob12）
await adapter.Send.To("user", "123").Raw_ob12(MessageBuilder.text("Hello"))
await adapter.Send.To("group", "456").Raw_ob12(MessageBuilder.image("https://..."))
await adapter.Send.To("group", "456").Raw_ob12(MessageBuilder.mention("123"))
await adapter.Send.To("group", "456").Raw_ob12(MessageBuilder.reply("msg_id"))
await adapter.Send.To("group", "456").Raw_ob12(MessageBuilder.at_all())
```

### 11.4 配合 Event.reply_ob12 使用

```python
from ErisPulse.Core import MessageBuilder

@message()
async def handle(event: Event):
    await event.reply_ob12(
        MessageBuilder()
        .mention(event.get_user_id())
        .text("收到你的消息")
        .build()
    )
```

### 11.5 支援的消息段方法

| 方法 | 說明 | data 字段 |
|------|------|----------|
| `text(text)` | 文字 | `text` |
| `image(file)` | 圖片 | `file` |
| `audio(file)` | 音頻 | `file` |
| `video(file)` | 視頻 | `file` |
| `file(file, filename=None)` | 文件 | `file`, `filename`(可選) |
| `mention(user_id, user_name=None)` | @使用者 | `user_id`, `user_name`(可選) |
| `at(user_id, user_name=None)` | @使用者（`mention` 的別名） | 同 `mention` |
| `reply(message_id)` | 回覆 | `message_id` |
| `at_all()` | @全體成員 | `{}` |
| `custom(type, data)` | 自定義/平台擴展 | 自定義 |

### 11.6 工具方法

```python
builder = MessageBuilder().text("基礎內容")

# 複製（深拷貝）
msg1 = builder.copy().image("img1").build()
msg2 = builder.copy().image("img2").build()

# 清空
builder.clear().text("新內容").build()

# 判斷是否為空
if builder:
    print(f"包含 {len(builder)} 個消息段")
```

## 12. 相關文件

- [事件轉換標準](event-conversion.md) - 完整的事件轉換規範、擴展命名和訊息段標準
- [API 回應標準](api-response.md) - 適配器 API 回應格式標準
- [會話類型標準](session-types.md) - 會話類型定義和映射關係
- [請求操作規範](request-action-spec.md) - 請求事件欄位要求、HandleRequest DSL 及適配器實現要求