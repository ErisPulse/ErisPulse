# 對比：ErisPulse 與 NoneBot2

> [!TIP]
> **什麼時候需要閱讀這篇**：當你會在 Python 機器人框架中寫程式碼，並正在 NoneBot2 和 ErisPulse 之間做選擇時閱讀這篇。如果不寫程式碼則可跳過。

用一句話定位差異：

- **NoneBot2**：擁有最豐富插件生態的異步機器人框架，事件處理模型成熟，社群累積超過十年
- **ErisPulse**：以 OneBot12 統一事件模型為核心的機器人 SDK，一份 handler 天然跨平台，模組級熱重載與生態服務契約是原生設計

兩者都是「開發者寫程式碼」的框架，而不是安裝好即可使用的產品。

## 設計差異對照

| 維度 | ErisPulse | NoneBot2 |
|---|---|---|
| 跨平台方式 | OneBot12 統一事件模型內建於核心，handler 無需感知平台差異 | 各適配器各有事件模型，跨平台依賴統一消息抽象插件（如 alconna） |
| 插件體系 | 模塊 = PyPI 包 + `epsdk` CLI 安裝 + [模塊市場](https://www.erisdev.com/#market)索引 | 插件 = PyPI 包（`nonebot-plugin-*`），商店網站檢索，pip 安裝 |
| 發送 API | SendDSL 鏈式發送：@、回覆、重試、超時、批量一行完成 | Matcher 側 `send` / 各適配器 API，統一消息抽象由插件提供 |
| 熱重載 | 模塊/適配器級熱重載，保存即生效，進程不重啟 | dev 模式整進程 reload（文件變更重啟進程） |
| AI 集成 | 框架零 AI 依賴；模塊聲明服務契約即自動成為 [QvQChat](../ecosystem/qvqchat.md) 智能體的工具；[ApiMCP](../ecosystem/apimcp.md) 可把機器人反向開放給 Claude 等 MCP 客戶端 | 由社區插件按需組合 |
| 管理工具 | 官方 [Dashboard](../ecosystem/dashboard.md) Web 面板、`epsdk` CLI、ErisPulse-App 手機客戶端 | 社區 WebUI 插件、nb-cli |
| 生產特性 | 三維作用域、歸屬權自動回收、影子模塊灰度、模塊間 RPC 服務契約 | 依賴注入、鉤子系統、社區方案 |
| 存儲 | 統一 KV + SQL API（sqlite/mysql/postgres 配置切換） | 各插件自選方案 |

## 什麼時候選誰

**選 NoneBot2**：你需要它生態中已經存在的某個具體插件；或團隊已深度熟悉其事件模型。插件存量是硬性優勢，其他差異都可以透過程式碼彌補，生態則不行。

**選 ErisPulse**：跨平台一致性是你的核心訴求（統一事件模型 + 16 個平台適配器）；你想要「改程式碼不重啟」的開發節奏；你想讓模組能力直接進入 AI 工具箱，而不是單獨再接一次 LLM。

> [!NOTE]
> 本對照基於雙方公開文件整理，NoneBot2 的插件生態與社群規模顯著更大是客觀事實；涉及決策請以[對方官方文件](https://nonebot.dev/)為準。

---

## 下一步

- **想看 ErisPulse 寫起來長怎樣**：[5 分鐘快速入門](../quick-start.md)
- **想了解統一事件模型的細節**：[基礎概念](../getting-started/basic-concepts.md)
- **在對比「群裡 AI 助手」類一體化平台**：[對比：AstrBot 與 LangBot](comparison-agent-platforms.md)