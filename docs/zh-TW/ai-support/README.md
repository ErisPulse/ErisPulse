# AI 輔助開發

ErisPulse 提供兩種互補的 AI 輔助開發方式，讓 AI 能基於最新框架規範產生程式碼：

- **物料文件**：一份大型 Markdown，一次灌入上下文，適合整體專案開發
- **MCP 伺服器**：讓 AI 按需檢索官方文件，適合日常程式碼補全和查詢 API

| | 物料文件 | MCP 伺服器 |
|---|---|---|
| 形式 | 一份大型 Markdown，**一次灌入** | AI **按需檢索** |
| 上下文成本 | 高（佔 token） | 低（只取相關片段） |
| 即時性 | 隨版本發布更新 | 即時（GitHub 拉取 + 快取） |
| 適合 | 上下文視窗大、進行整體專案開發 | 日常程式碼補全、查詢 API |
| 客戶端 | 任何 AI 工具 | 僅支援 MCP 的客戶端 |

兩者並不衝突：開發大型專案時可以同時使用——物料文件打底，MCP 查漏補缺。

## 物料文件

物料文件位於 `prompts/` 目錄下，按開發場景分為三種：

| 文件 | 場景 | 說明 |
|------|------|------|
| **ErisPulse-ModuleDev.md** | 模組開發 | 覆蓋模組開發全流程（事件處理、路由、生命週期等） |
| **ErisPulse-AdapterDev.md** | 適配器開發 | 在模組開發基礎上，外加適配器核心概念、SendDSL、平台適配指南 |
| **ErisPulse-Full.md** | 全棧參考 | 上述全部內容 + 完整用戶指南與 API 參考合集 |

獲取方式：從 `prompts/` 目錄直接獲取（與文件同步更新），或從 [GitHub Releases](https://github.com/ErisPulse/ErisPulse/releases) 下載對應版本。

### 使用方式

1. 根據目標選擇文件（模組 → `ModuleDev`，適配器 → `AdapterDev`，複雜需求 → `Full`）
2. 將文件內容作為上下文提供給 AI：IDE 內放入工作區，對話類直接貼上，API 調用作為 system message 注入
3. 用下方模板描述需求，越具體生成質量越高

### 需求描述模板

**模組：**

```
請基於 ErisPulse 模組開發規範，生成一個 [模組名稱] 模組的完整程式碼。

功能描述：[核心功能]
需要監聽的事件：[消息 / 命令 / 通知 / 請求]，處理邏輯：[操作]
需要的配置項：[鍵名]：[用途]（[必填/可選]，預設值：[值]）
其他要求：[額外約束]
```

**適配器：**

```
請基於 ErisPulse 適配器開發規範，生成一個 [適配器名稱] 適配器的完整程式碼。

平台資訊：[名稱]，通訊協定：[WebSocket / WebHook / HTTP 輪詢]，API 文件：[位址]
事件轉換：平台事件 [類型] → OneBot12 映射 [關係]
需要實現的發送方法：[Text / Image / Voice ...]
配置項：[鍵名]：[用途]（[必填/可選]）

## MCP 伺服器

ErisPulse 提供一個文件檢索 MCP 伺服器，讓 AI 編碼助手（支援 MCP 的均可）在你寫程式碼時直接檢索、查閱 ErisPulse 官方文件。

接入方式有兩種：**本地程序（推薦）**或**官方線上端點**。工具集一致：

| 工具 | 參數 | 說明 |
|------|------|------|
| **`search_docs`** | `query` (必填), `top_k?=5`, `lang?=zh-TW` | BM25 關鍵字檢索，可一次傳多個關鍵字 |
| **`read_document`** | `doc_path` (必填), `lang?=zh-TW` | 讀取單篇文件完整 Markdown |
| **`list_documents`** | `lang?=zh-TW` | 列出當前語言下所有文件標題、路徑、分類 |
| **`list_languages`** | — | 列出文件支援的所有語言及文件數量 |

支援語言：`zh-CN` / `en` / `zh-TW` / `ja` / `ru`。檢索技巧：用**多個關鍵字**而不是整句，例如 `命令註冊 事件監聽` 比 `怎麼註冊一個命令` 更好。

### 方式一：本地程序（推薦）

安裝後直接本地啟動：

```bash
npm i -g @erisdev/mcp-server   # 全域安裝 → 出現 epsdk-mcp 命令
epsdk-mcp --server               # 啟動 MCP 服務；首次運行自動拉取文件到 ~/.cache/erispulse-mcp/docs
```

不全域安裝也可透過 `npx` 直接執行（免裝）：

```bash
npx @erisdev/mcp-server --server
```

有本地文件目錄時指定它（不聯網）：

```bash
ERISPULSE_DOCS_DIR=/path/to/erispulse/docs epsdk-mcp --server
```

在 MCP 客戶端中按 **stdio 傳輸**配置，標準鍵值（`command` + `args` 指向上面的啟動方式；具體配置位置與格式見各客戶端自己的 MCP 接入文件）：

```json
{
  "command": "epsdk-mcp",
  "args": ["--server"]
}
```

或

```json
{
  "command": "npx",
  "args": ["@erisdev/mcp-server", "--server"]
}
```

### 方式二：官方線上端點

不想本地起程序時，連官方托管的 [`mcp.erisdev.com`](https://mcp.erisdev.com/)。MCP 客戶端按 **HTTP 傳輸**配置：

```json
{
  "url": "https://mcp.erisdev.com/"
}
```

服務預設公開、無需 Token，有 IP 限流（每 IP 每分鐘 60 次）。官方端點可隨時停用，**生產工作流程建議用方式一（本地程序）或自托管**。

## 常見問題

**產生的程式碼不符合預期？**
檢查是否提供了完整的文件；在需求中補充更多細節（輸入輸出範例、邊界條件）；讓 AI 分步產生（先骨架再補功能）；參考 [examples/](../../examples/) 目錄中的範例作為額外的上下文。

**MCP 接入後 AI 沒有呼叫 `search_docs`？**
確認客戶端已載入該 server（**重啟客戶端後可看到工具已生效**）；部分客戶端需要在 prompt 中明確提示「使用 ErisPulse 文件工具查證 API」。


## 下一步

- [模組開發入門](../developer-guide/modules/getting-started.md) -- 手動開發模組的完整教程
- [適配器開發入門](../developer-guide/adapters/getting-started.md) -- 手動開發適配器的完整教程
- [範例程式碼](../../examples/) -- 參考已有的模組和適配器實作
- [模組建構器](https://www.erisdev.com/builder.html) -- 瀏覽器內的視覺化 AI 模組產生器