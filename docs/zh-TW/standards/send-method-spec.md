# ErisPulse 發送方法規範

本文件定義了 ErisPulse 适配器中 `Send` 類別發送方法的命名規範和參數規範。

## 1. 標準方法命名

所有發送方法使用 **大駝峰命名法**，首字母大寫。

### 1.1 標準發送方法

| 方法名 | 說明 | 參數類型 |
|-------|------|---------|
| `Text` | 傳送文字訊息 | `str` |
| `Image` | 傳送圖片 | `bytes` \| `str` (URL/路徑) |
| `Voice` | 傳送語音 | `bytes` \| `str` (URL/路徑) |
| `Video` | 傳送視頻 | `bytes` \| `str` (URL/路徑) |
| `File` | 傳送檔案 | `bytes` \| `str` (URL/路徑) |
| `At` | @用戶/群組 | `str` (user_id) |
| `Face` | 傳送表情 | `str` (emoji) |
| `Reply` | 回覆訊息 | `str` (message_id) |
| `Forward` | 轉發訊息 | `str` (message_id) |
| `Markdown` | 傳送 Markdown 訊息 | `str` |
| `HTML` | 傳送 HTML 訊息 | `str` |
| `Card` | 傳送卡片訊息 | `dict` |

### 1.2 鏈式修飾方法

| 方法名 | 說明 | 參數類型 |
|-------|------|---------|
| `At` | @用戶（可多次調用） | `str` (user_id) |
| `AtAll` | @全體成員 | 無 |
| `Reply` | 回覆訊息 | `str` (message_id) |

### 1.3 協議方法

| 方法名 | 說明 |
|-------|------|
| `Raw_ob12` | 傳送原始 OneBot12 格式訊息 |
| `Raw_json` | 傳送原始 JSON 格式訊息 |
| `Raw_xml` | 傳送原始 XML 格式訊息 |

## 2. 參數規範詳解

### 2.1 媒體訊息參數規範

媒體訊息（`Image`、`Voice`、`Video`、`File`）支援兩種參數類型：

#### 2.1.1 字串參數（URL 或檔案路徑）

**格式：** `str`

**支援類型：**
- **URL**：網路資源位址（如 `https://example.com/image.jpg`）
- **檔案路徑**：本機檔案路徑（如 `/path/to/file.jpg` 或 `C:\\path\\to\\file.jpg`）

**使用場景：**
- 檔案已在網路上，直接發送 URL
- 檔案在本機磁碟，發送檔案路徑
- 希望適配器自動處理檔案上傳

**推薦：** 優先使用 URL，如果 URL 不可用則使用本機檔案路徑

**範例：**
```python
# 使用 URL
send.Image("https://example.com/image.jpg")

# 使用本地文件路径
send.Image("/path/to/local/image.jpg")
send.Image("C:\\path\\to\\local\\image.jpg")
```

#### 2.1.2 二進位數據參數

**格式：** `bytes`

**使用場景：**
- 檔案已在記憶體中（如從網路下載、從其他來源讀取）
- 需要處理後再發送（如圖片壓縮、格式轉換）
- 避免重複讀取檔案

**注意事項：**
- 大檔案上傳可能消耗較多記憶體
- 建議設定合理的檔案大小限制

**範例：**
```python
# 從網路讀取後發送
import requests
image_data = requests.get("https://example.com/image.jpg").content
send.Image(image_data)

# 從檔案讀取後發送
with open("/path/to/local/image.jpg", "rb") as f:
    image_data = f.read()
send.Image(image_data)
```

#### 2.1.3 參數處理優先順序

當適配器接收到媒體訊息參數時，應按以下順序處理：

1. **URL 參數**：直接使用 URL 發送(部分平台适配器可能存在URL下载后再上传的操作)
2. **檔案路徑**：檢測是否為本地路徑，若是則上傳檔案
3. **二進位數據**：直接上傳二進位數據

**適配器實作建議：**
```python
def Image(self, image: Union[bytes, str]):
    if isinstance(image, str):
        # 判斷是 URL 還是本地路徑
        if image.startswith(("http://", "https://")):
            # URL 直接發送
            return self._send_image_by_url(image)
        else:
            # 本地路徑，讀取後上傳
            with open(image, "rb") as f:
                return self._upload_image(f.read())
    elif isinstance(image, bytes):
        # 二進位數據，直接上傳
        return self._upload_image(image)
```

### 2.2 文字訊息參數規範

**方法：** `Text`

**參數：** `text` (`str`)

**要求：**
- 支援純文字內容
- 不進行格式化處理（如 Markdown、HTML）
- 建議限制文字長度（如 2000-5000 字元）
- 超長文字應提示使用者截斷或分段發送

**範例：**
```python
# 簡單文字
send.Text("你好，世界！")

# 長文字（建議分段）
long_text = "很長的文字內容..."
if len(long_text) > 2000:
    # 分段發送
    for i in range(0, len(long_text), 2000):
        send.Text(long_text[i:i+2000])
else:
    send.Text(long_text)
```

### 2.3 @用戶參數規範

**方法：** `At`（修飾方法）

**參數：** `user_id` (`str`)

**要求：**
- `user_id` 應為字串類型的使用者識別符
- 不同平台的 `user_id` 格式可能不同（數字、UUID、字串等）
- 適配器負責將 `user_id` 轉換為平台特定的格式

**範例：**
```python
# 單個 @ 用戶
send.Text("你好").At("123456")

# 多個 @ 用戶（鏈式調用）
send.Text("大家好").At("123456").At("789012")
```

### 2.4 回覆訊息參數規範

**方法：** `Reply`（修飾方法）

**參數：** `message_id` (`str`)

**要求：**
- `message_id` 應為字串類型的訊息識別符
- 應為之前收到的訊息的 ID
- 某些平台可能不支援回覆功能，適配器應優雅降級

**範例：**
```python
# 回覆一條訊息
send.Text("收到").Reply("msg_123456")
```

### 2.5 卡片訊息參數規範

**方法：** `Card`

**參數：** `data` (`dict`)

**要求：**
- `data` 應為字典類型的卡片數據
- 具體格式取決於平台（如 Telegram 的 InlineKeyboard、OneBot12 的 card）
- 適配器應驗證數據格式並轉換為平台特定格式
- 不支援卡片的平台應降級為文字訊息

**範例：**
```python
# 發送卡片數據
card_data = {
    "type": "image",
    "title": "卡片標題",
    "content": "卡片內容",
    "image": "https://example.com/image.jpg"
}
send.Card(card_data)
```

### 2.6 參數驗證和錯誤處理

**通用要求：**
1. **類型檢查**：驗證參數類型是否正確
2. **範圍檢查**：驗證參數值是否在合理範圍內
3. **存在性檢查**：驗證必要參數是否存在
4. **格式檢查**：驗證 URL、檔案路徑等格式是否正確

**錯誤處理建議：**
```python
def Image(self, image: Union[bytes, str]):
    # 類型檢查
    if not isinstance(image, (bytes, str)):
        raise TypeError("參數必須是 bytes 或 str 類型")
    
    # URL 格式檢查
    if isinstance(image, str) and not image.startswith(("http://", "https://")):
        # 檢查是否為本地檔案路徑
        if not os.path.exists(image):
            raise FileNotFoundError(f"檔案不存在: {image}")
    
    # 檔案大小檢查
    if isinstance(image, bytes) and len(image) > 10 * 1024 * 1024:  # 10MB
        raise ValueError("檔案大小超過限制（10MB）")
    
    # 發送訊息
    return self._send_image(image)
```

## 3. 平台特有方法命名

**不推薦**在 `Send` 類別中直接新增平台前綴方法。建議使用通用方法名或 `Raw_{協議}` 方法。

**不推薦：**
```python
def YunhuForm(self, form_id: str):  # ❌ 不推薦
    pass

def TelegramSticker(self, sticker_id: str):  # ❌ 不推薦
    pass
```

**推薦：**
```python
def Form(self, form_id: str):  # ✅ 通用方法名
    pass

def Sticker(self, sticker_id: str):  # ✅ 通用方法名
    pass

# 或使用 Raw 方法
def Raw_ob12(self, message):  # ✅ 發送 OneBot12 格式
    pass
```

## 4. 參數命名規範

| 參數名 | 說明 | 類型 |
|-------|------|------|
| `text` | 文字內容 | `str` |
| `url` / `file` | 檔案 URL 或二進位數據 | `str` / `bytes` |
| `user_id` | 用戶 ID | `str` / `int` |
| `group_id` | 群組 ID | `str` / `int` |
| `message_id` | 訊息 ID | `str` |
| `data` | 數據對象（如卡片數據） | `dict` |

## 5. 返回值規範

- **發送方法**（如 `Text`, `Image`）：必須返回 `asyncio.Task` 物件
- **修飾方法**（如 `At`, `Reply`, `AtAll`）：必須返回 `self` 以支援鏈式調用

## 6. 相關文檔

- [适配器系统 - SendDSL 详解](../core/adapters.md) - 查看調用方法和使用範例
- [适配器开发指南](../development/adapter.md) - 查看适配器實作要求
- [模块开发指南](../development/module.md) - 查看模組中的發送訊息範例