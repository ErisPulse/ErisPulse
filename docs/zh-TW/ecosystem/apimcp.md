# ErisPulse-ApiMCP 使用 AI 客戶端控制機器人

> [!TIP]  
> **什麼時候需要閱讀這篇**：當你想讓 Claude Desktop 等支援 MCP 的 AI 客戶端直接操控你的機器人——發送消息、查看消息、調用模組、管理適配器、觀測事件流——時請閱讀這篇。不需要則可跳過。

[ErisPulse-ApiMCP](https://github.com/wsu2059q/ErisPulse-ApiMCP) 透過 **MCP（Model Context Protocol）** 將機器人的運行時能力開放給 AI 客戶端：安裝後，Claude Desktop 中會新增 14 個工具，AI 可以替你收發消息、排查模組問題、訂閱群聊事件——機器人從「你管理的程式」變成「AI 的手和眼」。

> [!IMPORTANT]  
> ApiMCP 需要單獨安裝，且**必須明確配置 token** 後橋接功能才會啟用：  
>  
> ```bash
> epsdk install ErisPulse-ApiMCP
> ```  
>  
> 在 `config.toml` 的 `[ApiMCP]` 節點中設置 `token = "長隨機串"`（或環境變數 `ERISPULSE_APIMCP_TOKEN`）。未配置時，除了探活端點外所有端點都會返回 503，避免令牌靜默洩漏。

## 工作原理

兩層結構，機器人本體不引入任何 AI 依賴：

- **機器人進程內**：ApiMCP 模組在框架內建 HTTP server 上掛一個 REST 橋（`/apimcp/*`，token 鑑權，預設限流 30 請求/分鐘）
- **獨立進程**：`erispulse-apimcp` 命令用官方 `mcp` SDK 起 stdio server，把 MCP 工具呼叫轉發到機器人 HTTP 橋

```
Claude Desktop ──MCP(stdio)──► erispulse-apimcp ──HTTP──► 機器人進程 REST 橋 ──► sdk.*
```

機器人不線上或橋未配置時，工具回傳可讀錯誤與排查指引，不拋出堆疊。

## Claude Desktop 接入

編輯 `claude_desktop_config.json`（Windows: `%APPDATA%\Claude\`；macOS: `~/Library/Application Support/Claude/`）：

```json
{
  "mcpServers": {
    "erispulse": {
      "command": "erispulse-apimcp",
      "env": {
        "ERISPULSE_APIMCP_URL": "http://127.0.0.1:8000",
        "ERISPULSE_APIMCP_TOKEN": "你的token"
      }
    }
  }
}
```

儲存後完全重新啟動 Claude Desktop，工具列表出現 `erispulse` 伺服器即表示接入成功。任何支援 MCP stdio server 的客戶端（Claude Code、Cursor 等）都能用同樣方式接入。

## 14 個工具概覽

| 類別 | 工具 | 說明 |
|---|---|---|
| 模組 | `list_modules` / `get_module_info` / `call_module` / `reload_module` | 查看與呼叫已安裝模組的公開服務，觸發熱重載 |
| 適配器 | `list_adapters` / `get_adapter_status` / `reload_adapter` | 平台在線狀態；適配器重載預設禁用 |
| 消息 | `send_message` / `recent_messages` | 向任意平台發送文字/圖片/音訊/視訊/檔案；經 [transcript](../advanced/transcript.md) 回看最近消息 |
| 事件 | `subscribe_events` / `unsubscribe` / `poll_events` | 訂閱訊息/通知等事件，環形緩衝（預設 1000 條），增量輪詢 |
| 運行時 | `get_topology` / `sdk_health` | 運行時拓撲（已脫敏）與健康摘要 |

一個典型用法：AI 先 `subscribe_events(["message"])`，然後周期性 `poll_events` 觀察群裡在聊什麼，決定要不要 `send_message` 插話或 `call_module` 觸發某個模組的能力。

## 安全要點

- **token 即完全控制權**：能讀取訊息、發送訊息、呼叫白名單內模組方法。切勿提交至倉庫或貼到公開頻道；多租戶場景請拆分多個機器人實例
- **最小授權**：`module_call_whitelist` 收窄可呼叫模組（支援 `模組.方法` 精確放行），`send_target_whitelist` 收窄發送目標（如只允許發送到某個群組），`allow_adapter_reload` 保持預設關閉
- **只監聽本機**：僅本機使用時把框架 HTTP server 設為 `server.host = "127.0.0.1"`；跨機器必須內網 + 反向代理加 TLS
- 輸出經過鍵名級淨化（密鑰/路徑類鍵整鍵丟棄）；深度淨化是模組自身責任，敏感會話勿開放訂閱

完整配置項目（緩衝容量、回溯視窗、事件類型白名單等）與 REST 端點明細見[項目 README](https://github.com/wsu2059q/ErisPulse-ApiMCP)。

## 下一步

- **希望 AI 在群組中「活」起來而不僅僅被操控**：QvQChat 是正向方向——智能體主動聊天工作，請參閱 [QvQChat 通用智能體](qvqchat.md)；ApiMCP 是反向方向——外部 AI 操控機器人，兩者可同時安裝
- **想知道最近消息的數據來自哪裡**：[會話收件箱 transcript](../advanced/transcript.md)
- **想了解機器人的 HTTP server**：[路由系統](../advanced/router.md)