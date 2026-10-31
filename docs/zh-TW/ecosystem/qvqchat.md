# ErisPulse-QvQChat 通用智慧代理

> [!TIP]
> **什麼時候需要讀這篇**：當你想給機器人加 AI 智慧代理能力（工具循環、串流對話、MCP、長期記憶），或想把自己模組的服務暴露給智慧代理呼叫時讀這篇。不需要則跳過。

[ErisPulse-QvQChat](https://pypi.org/project/ErisPulse-QvQChat/) 是一個 **通用智慧代理模組**，圍繞工具循環建構：收發訊息、呼叫生態模組服務、編寫並執行程式碼、操作電腦、生成圖片語音、管理排程任務與長期記憶——全部透過同一套工具協定完成。

> [!IMPORTANT]
> QvQChat 需要單獨安裝：
>
> ```bash
> epsdk install ErisPulse-QvQChat
> ```
>
> 同時需要在「模型池」新增至少一個 OpenAI 相容模型（Base URL、API Key、模型名稱）。

## 核心能力

| 能力 | 說明 |
|---|---|
| 工具循環 | 模型輸出工具呼叫 → 並行執行 → 結果回填 → 繼續推理，直到給出最終回答 |
| 串流對話 | SSE 逐字輸出，工具步驟即時可見；重新整理 / 切走再回來，進度不丟 |
| 上下文壓縮 | 超過 token 閾值自動把舊對話壓縮為摘要（預設 128000 估算，可自訂） |
| 生態服務橋 | 自動發現模組宣告的服務並轉為工具，裝卸模組即增減能力 |
| MCP 用戶端 | stdio 與 Streamable HTTP，MCP 工具併入同一工具集 |
| 子智慧代理 | `spawn_agent` 派出獨立會話的子智慧代理探索任務，只回報結論 |
| 行程內執行 | `run_python_sdk` 主行程內執行 Python，直接存取執行時物件 |
| 電腦操作 | 三級安全沙箱（strict / standard / permissive），危險操作確認，全程稽核 |
| 視覺理解 | 圖片自動注入模型（不支援圖片時自動剝離重試） |
| 附件 | 任意檔案依 hash 去重後寫入磁碟，路徑交給 AI 自行處理；Ctrl+V 貼上截圖 |
| 分享會話 | 臨時唯讀連結（有效期 + token 預算），匯出 Markdown |
| 排程任務 | cron / 一次性 / 間隔，持久化，權限隨建立者 |
| 會話接管 | 管理員可讓智慧代理獨佔一個會話 |
| 人格系統 | 系統提示詞 + 開場對話 + 工具白名單，可按會話綁定 |
| 長期記憶 | 每會話記憶條目，按相似度檢索注入 |
| AI 自動命名 | 會話首輪回覆後自動生成簡短標題 |

## 模組擴展

任何 ErisPulse 模組宣告 `services` 即自動成為 QvQChat 的工具，無需專門介面：

```python
from ErisPulse.Core.Bases import BaseModule, ModuleMeta

class Main(BaseModule):
    @staticmethod
    def get_meta() -> ModuleMeta:
        return ModuleMeta(name="Draw", services=[
            {"name": "draw", "description": "根據描述生成圖片，回傳圖片 URL"},
        ])

    async def draw(self, prompt: str, size: str = "1024x1024"):
        return {"image_url": "https://..."}
```

服務的方法簽名自動對映為工具的 JSON Schema 參數定義，docstring 首行作為參數說明。

### 深度整合（可選）

模組可以額外實作以下任意服務，每個服務**獨立可選**——一個模組可以只做人格擴展，也可以只注入提示詞：

#### `qvq_prompts()` → 注入系統提示詞

回傳 `list[str]` 或 `list[{"text": str, "priority": int}]`，依 `priority` 升冪拼接。

```python
async def qvq_prompts(self):
    return [
        {"text": "畫圖後用 send_message 把圖片發給使用者。", "priority": 10},
        {"text": "支援的風格：動漫、寫實、水彩、像素。", "priority": 20},
    ]
```

#### `qvq_personas()` → 註冊人格預設

回傳人格清單，id 自動加 `ext.<模組名>.` 前綴，模組卸載自動清理。適合專門提供人格擴展的模組（如情感陪伴、翻譯專員、程式碼審查員等）。

```python
async def qvq_personas(self):
    return [
        {"id": "companion", "name": "暖男", "system": "你是一個溫暖體貼的聊天夥伴..."},
        {"id": "coder", "name": "程式碼導師", "system": "...", "tools": ["read_file", "run_python"]},
    ]
```

`tools` 可選限定該人格可用的工具子集。

#### `qvq_schemas()` → 顯式參數 schema

回傳 `dict[服務名, JSON Schema]`，覆寫方法簽名推斷。參數複雜或需要嚴格驗證時使用。

```python
async def qvq_schemas(self):
    return {
        "draw": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "畫面描述"},
                "size": {"type": "string", "enum": ["512x512", "1024x1024"]},
            },
            "required": ["prompt"],
        },
    }
```

### 重新整理時機

深度整合服務的重新整理時機：啟動、模組裝卸、Dashboard「工具」頁手動重新整理。

## 事件訂閱

QvQChat 廣播兩個生命週期事件：

| 事件 | 時機 | 負載 |
|---|---|---|
| `qvq.message` | 收到使用者訊息 | `chat_key` `platform` `sender_id` `sender_name` `text` `is_group` |
| `qvq.replied` | 回覆發出後 | `chat_key` `reply` `tools` |

```python
async def setup(self):
    sdk.lifecycle.on("qvq.message", self.on_message)
```

## 作為服務被呼叫

| 服務 | 簽名 | 說明 |
|---|---|---|
| `chat` | `(session_id, prompt, persona="")` | 與智慧代理對話，回傳文字 |
| `run_prompt` | `(chat_key, prompt, ...)` | 執行提示詞，結果可傳送到目標會話 |
| `get_status` | `()` | 執行狀態摘要 |

## 配套外掛

三個獨立模組擴充了 QvQChat，也順便示範了擴充點能做什麼——安裝 QvQChat 後依需求加裝：

| 外掛 | 用途 |
|---|---|
| [ErisPulse-QvQStalker](https://github.com/wsu2059q/ErisPulse-QvQStalker) | 旁聽群聊自動插話：熱度追蹤、五層判定和衝動值共同決定智慧型代理何時開口，15 項行為參數可在設定頁直接調整 |
| [ErisPulse-QvQMemes](https://github.com/wsu2059q/ErisPulse-QvQMemes) | 給智慧型代理一個表情包習慣：`send_sticker` 工具讓模型自己挑選該發哪張，群組圖片自動收錄並由視覺模型加上標籤 |
| [ErisPulse-QvQCompanion](https://github.com/wsu2059q/ErisPulse-QvQCompanion) | 擬人化陪伴：語氣人設注入、衝動值主動開口、靜默時段與每日上限 |

三個外掛都透過上文「模組擴充」的約定服務接入，本身也是擴充寫法的參考實作。

## 介面

透過 `/QvQChat/view` 獨立存取，或嵌入 Dashboard 側邊欄。

![概覽](https://raw.githubusercontent.com/wsu2059q/ErisPulse-QvQChat/main/.github/assets/overview.png)

![對話](https://raw.githubusercontent.com/wsu2059q/ErisPulse-QvQChat/main/.github/assets/chat.png)

---

## 下一步

- **把自己的模組變成智慧代理工具**：在 `get_meta()` 宣告 `services` 即可，欄位語意詳見 [核心模組 API - 服務契約](../api-reference/core-modules.md)
- **訂閱智慧代理訊息做連動**：用[生命週期事件](../advanced/lifecycle.md)監聽 `qvq.message` / `qvq.replied`
- **不用智慧代理、只要多輪問答表單**：內建的 [Conversation 多輪對話](../advanced/conversation.md)是更輕量的選擇
- **網頁端管理**：搭配 [ErisPulse-Dashboard](dashboard.md) 側邊欄使用