# ErisPulse-QvQChat 通用智能體

[ErisPulse-QvQChat](https://pypi.org/project/ErisPulse-QvQChat/) 是一個 **通用智能體模組**，圍繞工具循環建構：收發訊息、呼叫生態模組服務、撰寫並執行程式碼、操作電腦、產生圖片語音、管理定時任務與長期記憶——全部透過同一套工具協定完成。

> [!IMPORTANT]
> QvQChat 需要單獨安裝：
>
> ```bash
> epsdk install ErisPulse-QvQChat
> ```
>
> 同時需要在「模型池」新增至少一個 OpenAI 兼容模型（Base URL、API Key、模型名）。

## 核心能力

| 能力 | 說明 |
|---|---|
| 工具循環 | 模型輸出工具調用 → 並發執行 → 結果回填 → 繼續推理，直到給出最終回答 |
| 流式對話 | SSE 逐字輸出，工具步驟實時可見；刷新 / 切走再回來，進度不丟 |
| 上下文壓縮 | 超過 token 閾值自動把舊對話壓縮為摘要（預設 128000 估算，可自定義） |
| 生態服務橋 | 自動發現模塊聲明的服務並轉為工具，裝卸模塊即增減能力 |
| MCP 客戶端 | stdio 與 Streamable HTTP，MCP 工具並入同一工具集 |
| 子智能體 | `spawn_agent` 派出獨立會話的子智能體探索任務，只回報結論 |
| 進程內執行 | `run_python_sdk` 主進程內運行 Python，直接訪問運行時物件 |
| 電腦操作 | 三級安全沙箱（strict / standard / permissive），危險操作確認，全程審計 |
| 視覺理解 | 圖片自動注入模型（不支援圖片時自動剝離重試） |
| 附件 | 任意檔案按 hash 去重落盤，路徑交給 AI 自行處理；Ctrl+V 粘貼截圖 |
| 分享會話 | 臨時只讀連結（有效期 + token 預算），匯出 Markdown |
| 定時任務 | cron / 一次性 / 間隔，持久化，權限隨創建者 |
| 會話接管 | 管理員可讓智能體獨佔一個會話 |
| 人格系統 | 系統提示詞 + 開場對話 + 工具白名單，可按會話綁定 |
| 長期記憶 | 每會話記憶條目，按相似度檢索注入 |
| AI 自動命名 | 會話首輪回覆後自动生成簡短標題 |

## 模組擴展

任何 ErisPulse 模組宣告 `services` 即自動成為 QvQChat 的工具，無需專門介面：

```python
from ErisPulse.Core.Bases import BaseModule, ModuleMeta

class Main(BaseModule):
    @staticmethod
    def get_meta() -> ModuleMeta:
        return ModuleMeta(name="Draw", services=[
            {"name": "draw", "description": "根據描述生成圖片，返回圖片 URL"},
        ])

    async def draw(self, prompt: str, size: str = "1024x1024"):
        return {"image_url": "https://..."}
```

服務的方法簽名自動映射為工具的 JSON Schema 參數定義，docstring 首行作為參數說明。

### 深度集成（可選）

模組可以額外實現以下任意服務，每個服務**獨立可選**——一個模組可以只做人格擴展，也可以只注入提示詞：

#### `qvq_prompts()` → 注入系統提示詞

傳回 `list[str]` 或 `list[{"text": str, "priority": int}]`，按 `priority` 升序拼接。

```python
async def qvq_prompts(self):
    return [
        {"text": "畫圖後用 send_message 把圖片發給使用者。", "priority": 10},
        {"text": "支援的風格：動漫、寫實、水彩、像素。", "priority": 20},
    ]
```

#### `qvq_personas()` → 註冊人格預設

傳回人格列表，id 自動加 `ext.<模組名>.` 前綴，模組卸載自動清理。適合專門提供人格擴展的模組（如情感陪伴、翻譯專員、程式碼審查員等）。

```python
async def qvq_personas(self):
    return [
        {"id": "companion", "name": "暖男", "system": "你是一個溫暖體貼的聊天夥伴..."},
        {"id": "coder", "name": "程式碼導師", "system": "...", "tools": ["read_file", "run_python"]},
    ]
```

`tools` 可選限定該人格可用的工具子集。

#### `qvq_schemas()` → 显式參數 schema

傳回 `dict[服務名, JSON Schema]`，覆蓋方法簽名推斷。參數複雜或需要嚴格校驗時使用。

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

### 刷新時機

深度集成服務的刷新時機：啟動、模組裝卸、Dashboard「工具」頁手動刷新。

## 事件訂閱

QvQChat 廣播兩個生命週期事件：

| 事件 | 時機 | 載荷 |
|---|---|---|
| `qvq.message` | 收到使用者訊息 | `chat_key` `platform` `sender_id` `sender_name` `text` `is_group` |
| `qvq.replied` | 回覆發出後 | `chat_key` `reply` `tools` |

```python
async def setup(self):
    sdk.lifecycle.on("qvq.message", self.on_message)
```

## 作為服務被調用

| 服務 | 簽名 | 說明 |
|---|---|---|
| `chat` | `(session_id, prompt, persona="")` | 與智能體對話，返回文本 |
| `run_prompt` | `(chat_key, prompt, ...)` | 運行提示詞，結果可發送到目標會話 |
| `get_status` | `()` | 運行狀態摘要 |

## 界面

可透過 `/QvQChat/view` 獨立存取，或嵌入 Dashboard 頁面側邊欄。

![概覽](https://raw.githubusercontent.com/wsu2059q/ErisPulse-QvQChat/main/.github/assets/overview.png)

![對話](https://raw.githubusercontent.com/wsu2059q/ErisPulse-QvQChat/main/.github/assets/chat.png)