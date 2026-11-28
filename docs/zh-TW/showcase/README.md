# 選型指南

> [!TIP]
> **什麼時候需要看這篇**：當你在幾個機器人框架 / AI 機器人平台之間做選擇，想知道 ErisPulse 適合誰、不適合誰時讀這篇。已經在使用 ErisPulse 則跳過。

我們不認為存在「最好的框架」，只存在「匹配場景的框架」。這個目錄用對照表說清 ErisPulse 與常見選項的設計差異，幫你做決定——包括什麼時候應該**不選**我們。

| 你在比較什麼 | 讀這篇 | 面向 |
|---|---|---|
| ErisPulse vs NoneBot2 | [對比：NoneBot2](comparison-nonebot.md) | 開發者 |
| ErisPulse（+QvQChat）vs AstrBot / LangBot | [對比：AstrBot 與 LangBot](comparison-agent-platforms.md) | 想要「群裡 AI 助手」的使用者 |
| 從 AstrBot 迁移到 ErisPulse | [遷移指南：從 AstrBot 到 ErisPulse](migrate-from-astrbot.md) | AstrBot 現有使用者 |

## 場景速查

- **想要裝好即用的 AI 聊天機器人，不寫程式**：AstrBot / LangBot 的起步體驗更快；若你重視熱重載、模組市場與 16 平台覆蓋，使用 ErisPulse + [QvQChat](../ecosystem/qvqchat.md) + [Dashboard](../ecosystem/dashboard.md) 也能到達同一終點，多花約半小時初始化
- **要寫業務程式碼、跨平台複用**：ErisPulse 的 OneBot12 統一事件模型讓一份 handler 天然跨平台，無需為平台差異寫適配分支
- **要為自己的模組/AI 做生態**：ErisPulse 模組宣告服務即成為 AI 工具（[QvQChat](../ecosystem/qvqchat.md) 自動發現），生態與智能體原生聯動
- **已有大量 NoneBot 插件依賴**：NoneBot2 十餘年插件生態是客觀優勢，遷移成本需自行權衡

## 閱讀紀律

對照內容基於各方公開文件整理，隨版本演進可能過時——**涉及決策前請以對方官方文件為準**。發現失實或過時的描述，歡迎提 Issue 或 PR 修訂，我們不刪除合理的批評。