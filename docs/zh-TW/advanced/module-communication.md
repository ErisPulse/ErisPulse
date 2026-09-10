# 模組間通信

> [!NOTE]  
> 本章內容需要 ErisPulse **2.8.0+**。

ErisPulse 的模組之間有**三層通訊模型**，依「點對點 → 定向 → 廣播」排列：

| 層 | API | 語義 | 典型場景 |
|---|---|---|---|
| **RPC** | `await sdk.module.call("Chat", "get_history", ...)` | 點對點請求-回應，帶契約 / 審計 / 超時 | 調用另一模組的能力（查詢歷史、翻譯、退款） |
| **定向事件** | `await lifecycle.emit("message_received", {...}, to="Chat")` | 僅分發給指定模組註冊的生命周期鉤子 | 上游狀態變更通知下游（「收到新訊息了」） |
| **廣播** | `await lifecycle.emit("config.updated", {...})` | 全框架可見的生命周期事件 | 配置熱更新、模組上下線 |

{!--< tips >!--}
選型口訣：**要回傳值用 `call`，只通知一個模組的鉤子用 `emit(..., to=...)`，通知所有人用 `emit(...)`**。
{!--< /tips >!--}

## RPC：module.call

```python
result = await sdk.module.call("Chat", "get_history", session_id, n=20)
```

與裸屬性存取 `sdk.module.Chat.get_history(...)`（保持不變）的差異：

| | `module.call()` | 裸屬性存取 |
|---|---|---|
| 目標未註冊 / 未啟用 | 抛 `ModuleNotAvailableError` | 抛 `AttributeError` |
| 慢載入模組 | **自動喚醒**（事件驅動模組走激活鎖） | 異步初始化模組拋 RuntimeError |
| `current_owner` | 歸因到**目標模組**（其內部 wait_reply / 發送 / 日誌正確歸屬） | 保持呼叫方 |
| 超時 | 預設 30 秒（`timeout=` 覆蓋，None 不限時） | 無 |
| scope 審計 | 呼叫方過出站閘口 `actions.<呼叫方>.call` | 無 |
| 契約校驗 | `meta.services` 白名單 | 無 |

### 異常體系

```
ModuleError                      # 模組系統異常基類
└── ModuleCallError              # 跨模組呼叫基類（含 module / method 屬性）
    ├── ModuleNotAvailableError  # 目標未註冊 / 未啟用 / 喚醒失敗
    ├── ServiceNotProvidedError  # 方法不在 services 白名單 / 私有方法 / 不存在
    └── ModuleCallTimeoutError   # 協程方法超時
```

均掛在 `ErisPulseError` 體系下，可 `from ErisPulse.Core import ModuleCallError` 捕獲。

## 服務契約：meta.services

服務方在 `get_meta()` 中宣告所提供的白名單（與 `commands` 欄位對稱）：

```python
from ErisPulse.Core.Bases import BaseModule, ModuleMeta

class ChatModule(BaseModule):
    @staticmethod
    def get_meta() -> ModuleMeta:
        return ModuleMeta(
            name="聊天",
            services=[
                "get_history",                                       # 簡單形式
                {"name": "translate", "description": "把文本翻譯成指定語言"},  # 帶說明
            ],
        )

    async def get_history(self, session_id, n=20): ...
    async def translate(self, text, target_lang): ...
    def _internal_helper(self): ...   # 下劃線方法始終禁止被外部呼叫
```

**開發者無感是預設**：

- 未宣告 `services` → 所有**公開**方法天然可被 `module.call()` 呼叫（與裸屬性存取一致），
  無需任何宣告
- 宣告後 → 收緊為白名單，越界呼叫拋出 `ServiceNotProvidedError`——用於標記
  "這些方法才是對外承諾"
- 限制的**主控制權在使用者端**：`scope.actions` 配置決定「誰能呼叫誰」（見下文審計），
  模組作者的 `services` 僅是服務面宣告，兩層互不替代

**服務說明**：為每個服務配上人類 / AI 可讀的描述——不需要就不寫，
說明自動取**方法 docstring 首行**（框架本就要求 docstring 風格）：

```python
async def translate(self, text, target_lang):
    """把文本翻譯成指定語言"""    # ← 這一行自動成為服務說明
    ...
```

需要精細控制（覆蓋 docstring / 多語言）時用 dict 形式宣告 description（支援 i18n 字典）：

```python
services=[
    {"name": "translate", "description": "把文本翻譯成指定語言"},
    {"name": "summarize", "description": {"i18n": "Chat.meta.svc.summarize", "default": "摘要對話"}},
]
```

## 服務目錄：services()

```python
sdk.module.services()
# {'Chat': [{'name': 'get_history', 'signature': '(session_id, n=20)',
#            'description': '把文本翻譯成指定語言'}]}

sdk.module.services("Chat")   # 僅查詢指定模組
```

- 僅列出**明確宣告** `meta.services` 的模組（未宣告的模組不出現在目錄中）
- 每個服務帶有方法簽名字串（使用 `inspect.signature` 提取）與介紹文字
- 同時進入拓撲：`sdk.module.get_topology()` 的各模組條目帶有 `services` 欄位

{!--< tips >!--}
**MCP 化路線**：服務目錄（名稱 + 簽名 + 描述）即為 MCP tool 的形狀——
每個服務自然地長成 ``{"name", "description", "parameters"}``。
未來框架可將 ``services()`` 直接暴露為 MCP server 端點，讓 AI 發現並呼叫模組能力；
``scope.actions.call`` 審計自然成為 AI 呼叫的安全閘口。
{!--< /tips >!--}

## 出站審計：誰能呼叫誰

每次 `module.call()` 都會以**呼叫方模組**的身份過**出站閘口**的審計：

```toml
[ErisPulse.scope.actions.CallerModule.call]
deny = ["Chat.get_history"]        # 禁止 CallerModule 呼叫 Chat 的 get_history
# allow = ["Chat.get_*"]           # 或白名單：僅允許呼叫 Chat 的 get 開頭服務
```

- `name` 格式為 `<目標模組>.<方法名>`，支援精確 / glob / `re:` 正則
- 框架層呼叫（無 owner 上下文，例如啟動腳本）不受審計約束
- 被拒絕的呼叫會拋出 `ModuleCallError`（TRACE 日誌 `core.module.call_denied`）

配置方式詳見 [作用域（scope）](docs/zh-TW/scope.md) 的出站維度。

## 定向事件：lifecycle.emit 的 to 參數

生命週期事件支援定向傳播：`to` 指定目標擁有者（owner）後，事件只分發給以該
owner 身份註冊的鉤子（模組在 `on_load` 內註冊的鉤子自動歸屬本模組），
其它模組與通配符 `*` 處理器不感知。

```python
from ErisPulse.Core.lifecycle import lifecycle

# 投遞方：事件只投給 Chat 模組註冊的鉤子
await lifecycle.emit("message_received", {"text": "hi", "from": "u1"}, to="Chat")

# 訂閱方（Chat 模組內）：註冊同名鉤子，owner 在註冊時自動記錄
@lifecycle.on("message_received")
async def on_message_received(data): ...

@lifecycle.on("message")          # 點式父級前綴同樣生效（按 owner 過濾）
async def on_any(data): ...
```

語義細節：

- 目標 owner 無已註冊鉤子 → 事件**靜默丟棄**（**不發往不存在的地方**），
  可用 `lifecycle.has_handlers("message_received")` 提前探測
- `data` 為 dict 時自動攜帶 `_trace_id`（不覆蓋已有值），與全鏈路追蹤打通
- 廣播與定向共用一套鉤子註冊：`emit(...)` 不帶 `to` 即全框架廣播，
  帶 `to` 則同一事件只對目標模組可見
- `emit_sync` / `submit_event`（相容 API）同樣支援 `to=` 參數

> [!NOTE]
> 定向事件是輕量通知，**不做目標校驗與懶喚醒**；需要目標存在性校驗、
> 契約審計或返回值時，改用 [RPC：module.call](#rpcmodulecall)。

## 慢載與呼叫

`module.call()` 對慢載模組是**透明喚醒**：

- 事件驅動慢載模組（`activate_on` 聲明）→ 走激活鎖 `_activate()`，激活後觸發器 stub 自動註銷
- 普通慢載模組 → 同步初始化或常規載入路徑（冪等）
- 喚醒失敗 → `ModuleNotAvailableError`

也就是說：**呼叫方不需要關心目標模組是否已載入**，也不需要為了喚醒它而等待任何事件。

定向事件（`lifecycle.emit(..., to=...)`）不做慢載喚醒——目標未載入即無鉤子，  
事件靜默丟棄；需要確保傳送到時改用 `module.call()`。

## 冷啟動回放

新裝 / 重啟的模組錯過了一段聊天——`get_load_strategy(replay=...)` 讓框架在模組
就緒後，把會話收件箱裡最近的訊息**回放給該模組自己**：

```python
from ErisPulse.loaders import ModuleLoadStrategy

class MyAIModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(
            lazy_load=False,
            priority=100,
            replay="5m",        # 回放最近 5 分鐘（"1h" / "300" 秒寫法均可）
        )

    async def on_load(self, event):
        @message.on_message()
        async def handle(e):
            if e.get("replayed"):
                # 合成事件：僅補上下文，不要觸發發送等副作用
                ...
```

語義細節：

- 數據來源是[會話收件箱](interaction.md#會話收件箱eventhistory)（`sdk.transcript.recent()`），
  模組加載完成後後台執行，不阻塞啟動
- 合成事件帶 `replayed: True` 標誌、完整的 `platform / detail_type / user_id / alt_message`，
  **只分發給本模組的處理器**——其他模組不受回放影響
- 收件箱未啟用 / 無記錄 / 時長聲明非法（`replay_invalid` 警告）時靜默跳過

## 事件冪等去重

平台 websocket 重新連接後，經常會重複推送同一事件（相同的 `event["id"]`）——分發入口會根據 id 做 LRU 去重（容量 4096），相同 id 的事件只會分發一次。

```toml
[ErisPulse.framework]
event_dedupe = true   # 預設開啟；測試環境固定 id 合成事件可關閉
```

適配器**註冊**（新連接生命週期的起點）時會自動重置去重緩存。

## 相關文件

- [互動對話系統](interaction.md) - wait_reply / 定時器 / 多路等待 / 對話互斥
- [作用域（scope）](scope.md) - 出站維度審計的完整設定
- [歸屬權（owner）系統](ownership.md) - owner 上下文如何貫穿跨模組呼叫
- [懶加載系統](lazy-loading.md) - 懶加載與事件驅動懶激活（activate_on）
- [生命週期管理](lifecycle.md) - 廣播層事件總線的機制