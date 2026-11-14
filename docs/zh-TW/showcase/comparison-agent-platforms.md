# 對比：ErisPulse 與 AstrBot / LangBot

> [!TIP]
> **什麼時候需要讀這篇**：當你想要的是「群組裡的 AI 助手」，正在 AstrBot / LangBot 這類一體化平台和 ErisPulse 之間選型時讀這篇。要寫非 AI 業務程式碼則看 [對比：NoneBot2](comparison-nonebot.md)。

一句話定位差異：

- **AstrBot / LangBot**：一體化 AI 聊天機器人平台——安裝、設定 Key、開聊，LLM 對話是產品中心
- **ErisPulse**：機器人框架/SDK——AI 是其中一個可裝卸的模組（[QvQChat](../ecosystem/qvqchat.md)），框架本身還要承載非 AI 的業務邏輯

三者最終都能得到「群組裡有個會做事的 AI」，路徑和天花板不同。

## 對照

| 維度 | ErisPulse + QvQChat | AstrBot / LangBot |
|---|---|---|
| 起步體驗 | 初始化專案 + 裝適配器 + 裝 QvQChat + 配模型池，約10分鐘 | 安裝 + 配 Key 即用，更快 |
| 平台覆蓋 | 16 個平台適配器（含雲湖、郵件、終端、Webhook 橋） | 主流 IM 平台 |
| LLM 支援 | OpenAI 相容模型池（自我修復、故障轉移、難度路由）、MCP 用戶端 | 多家 Provider 內建接入 |
| AI 深度 | 工具循環 + 子智慧代理 + 長期記憶/使用者畫像 + 知識庫 + 電腦操作沙箱 + 定時「計畫-執行-審查」 | 對話、人格、知識庫、外掛工具 |
| 生態聯動 | 任意 ErisPulse 模組宣告服務即自動成為 AI 工具，裝卸模組即增減 AI 能力 | 安裝對應外掛擴展 AI 能力 |
| 反向開放 | [ApiMCP](../ecosystem/apimcp.md) 將機器人暴露為 MCP 工具，Claude 等 AI 用戶端可直接操控 | — |
| 熱重載 | 模組/適配器級，儲存即生效 | 外掛更新通常需重啟 |
| 非 AI 業務 | 框架原生：命令系統、多輪對話、ORM、定時任務、訊息統計等模組各自獨立 | 平台以 AI 對話為中心，非 AI 能力依賴外掛 |
| 管理面板 | Dashboard（模組/設定/日誌/事件 + 第三方視窗註冊）、手機 App、AI Builder | WebUI 內建 |
| 社群規模 | 較年輕，生態成長中 | 使用者基數更大、第三方外掛更多 |

## 什麼時候選誰

**選 AstrBot / LangBot**：你要的就是快速用上 AI 聊天，不打算寫業務程式碼，也不需要小眾平台（如雲湖）接入。它們是成熟的一體化方案。

**選 ErisPulse**：機器人除了 AI 還要做別的（定時推送、群組管理、訊息統計、橋接……），希望 AI 只是其中一個可拆的模組；或者你在意熱重載的開發節奏、模組市場的分發方式、以及「裝一個模組 AI 就多一項能力」的生態聯動；或者你需要 ApiMCP 這種讓外部 AI 操控機器人的反向通道。

> [!NOTE]
> 本對照基於雙方公開文件整理；AstrBot / LangBot 的使用者基數與外掛數量更大是客觀事實，涉及決策請以[對方官方文件](https://astrbot.app/) / ([LangBot](https://docs.langbot.app/))為準。

---

## 下一步

- **從 AstrBot 過來**：[遷移指南：從 AstrBot 到 ErisPulse](migrate-from-astrbot.md)
- **想直接看 ErisPulse 上的 AI 長什麼樣**：[QvQChat 通用智慧型代理人](../ecosystem/qvqchat.md)
- **想先跑起來再說**：[5 分鐘快速開始](../quick-start.md)