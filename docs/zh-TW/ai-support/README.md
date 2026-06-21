# AI 輔助開發

ErisPulse 提供兩種互補的 AI 輔助開發方式，讓 AI 能基於最新的框架規範生成程式碼：

- **物料文件**：一份大 Markdown，一次性灌入上下文，適合整專案開發
- **MCP 伺服器**：讓 AI 按需檢索官方文件，適合日常程式碼補全和查詢 API

| | 物料文件 | MCP 伺服器 |
|---|---|---|
| 形式 | 一份大 Markdown，**一次性灌入** | AI **按需檢索** |
| 上下文成本 | 高（佔 token） | 低（只取相關片段） |
| 即時性 | 隨版本發布更新 | 即時（GitHub 拉取 + 快取） |
| 適合 | 上下文視窗大、做整專案開發 | 日常程式碼補全、查詢 API |
| 客戶端 | 任何 AI 工具 | 僅支援 MCP 的客戶端 |

兩者並不衝突：開發大型專案時可以同時使用——物料文件打底，MCP 兜底查漏。

## 物料文件

物料文件位於 `prompts/` 目錄下，按開發場景分為三種：

| 文件 | 場景 | 說明 |
|------|------|------|
| **ErisPulse-ModuleDev.md** | 模組開發 | 覆蓋模組開發全流程（事件處理、路由、生命週期等） |
| **ErisPulse-AdapterDev.md** | 適配器開發 | 在模組開發基礎上，外加適配器核心概念、SendDSL、平台適配指南 |
| **ErisPulse-Full.md** | 全站參考 | 上述全部內容 + 完整使用者指南與 API 參考合集 |

獲取方式：從 `prompts/` 目錄直接獲取（與文件同步更新），或從 [GitHub Releases](https://github.com/ErisPulse/ErisPulse/releases) 下載對應版本。

### 使用方式

1. 根據目標選擇文件（模組 → `ModuleDev`，適配器 → `AdapterDev`，複雜需求 → `Full`）
2. 將文件內容作為上下文提供給 AI：IDE 內放入工作區，對話類直接貼上，API 調用作為 system message 注入
3. 用下方範本描述需求，越具體生成品質越高

### 需求描述範本

**模組：**

```
請基於 ErisPulse 模組開發規範，生成一個 [模組名稱] 模組的完整程式碼。

功能描述：[核心功能]
需要監聽的事件：[訊息 / 命令 / 通知 / 請求]，處理邏輯：[操作]
需要的設定項：[鍵名]：[用途]（[必填/可選]，預設值：[值]）
其他要求：[額外限制]
```

**適配器：**

```
請基於 ErisPulse 適配器開發規範，生成一個 [適配器名稱] 適配器的完整程式碼。

平台資訊：[名稱]，通訊協定：[WebSocket / WebHook / HTTP 輪詢]，API 文件：[位址]
事件轉換：平台事件 [類型] → OneBot12 映射 [關係]
需要實現的傳送方法：[Text / Image / Voice ...]
設定項：[鍵名]：[用途]（[必填/可選]）
```

## MCP 伺服器

ErisPulse 提供官方 **MCP（Model Context Protocol）伺服器**，部署在 [`mcp.erisdev.com`](https://mcp.erisdev.com/)。接入支援 MCP 的 AI 編碼助手（Claude Desktop、Cursor 等）後，AI 就能在你寫程式碼時**直接檢索、查閱 ErisPulse 官方文件**，而不需要手動貼上。

### 提供的工具

接入後，AI 會獲得以下工具：

| 工具 | 參數 | 說明 |
|------|------|------|
| **`search_docs`** | `query` (必填), `top_k?=5`, `lang?=zh-CN` | BM25 關鍵字檢索，可一次傳多個關鍵字 |
| **`read_document`** | `doc_path` (必填), `lang?=zh-CN` | 讀取單篇文件完整 Markdown |
| **`list_documents`** | `lang?=zh-CN` | 列出當前語言下所有文件標題、路徑、分類 |
| **`list_languages`** | — | 列出文件支援的所有語言及文件數量 |

支援語言：`zh-CN` / `en` / `zh-TW` / `ja` / `ru`。檢索技巧：用**多個關鍵字**而不是整句，例如 `命令註冊 事件監聽` 比 `怎麼註冊一個命令` 更好。

### 接入 Claude Desktop

編輯設定檔（macOS：`~/Library/Application Support/Claude/claude_desktop_config.json`；Windows：`%APPDATA%\Claude\claude_desktop_config.json`）：

```json
{
  "mcpServers": {
    "erispulse": {
      "url": "https://mcp.erisdev.com/"
    }
  }
}
```

> 需要 Claude Desktop 0.85+。舊版本可透過 `mcp-remote` 橋接：`{ "command": "npx", "args": ["mcp-remote", "https://mcp.erisdev.com/"] }`。

### 接入 Cursor

編輯 `~/.cursor/mcp.json`（全域）或專案內 `.cursor/mcp.json`：

```json
{
  "mcpServers": {
    "erispulse": {
      "url": "https://mcp.erisdev.com/"
    }
  }
}
```

服務預設公開，無需 Token。為防濫用有 IP 限流（每 IP 每分鐘 60 次）。Worker 源碼在本庫 workers 檔案夾下，支援自部署。

## 常見問題

**生成的程式碼不符合預期？**  
檢查是否提供了完整文件；在需求中補充更多細節（輸入輸出示例、邊界條件）；讓 AI 分步生成（先骨架再補功能）；參考 [examples/](../../examples/) 目錄範例作為補充上下文。

**MCP 接入後 AI 沒調用 `search_docs`？**  
確認客戶端加載了該 server（Claude Desktop 重啟後右下角應有圖示）；部分客戶端需要在 prompt 裡顯式提示「使用 ErisPulse 文件工具查證 API」。

## 下一步

- [模組開發入門](../developer-guide/modules/getting-started.md) -- 手動開發模組的完整教學
- [適配器開發入門](../developer-guide/adapters/getting-started.md) -- 手動開發適配器的完整教學
- [範例程式碼](../../examples/) -- 參考已有的模組和適配器實作
- [模組建構器](https://www.erisdev.com/builder.html) -- 瀏覽器內的視覺化 AI 模組生成器