# 終端平台特性文件

TerminalAdapter 是命令行終端適配器——終端即聊天會話，用於本地快速調試模塊邏輯。

---

## 文件資訊

- 對應模組版本: 1.1.0
- 維護者: ErisPulse

## 基本資訊

- 平台簡介：將本地命令列當作聊天對話，stdin 輸入即為訊息，模組回應直接列印到終端機
- 適配器名稱：TerminalAdapter
- 平台標識：`terminal`
- 單帳戶設計（用於本地除錯場景）
- 框架要求：軟依賴 `ErisPulse>=2.7.1`（執行時偵測提示，不強制）

## 配置說明

```toml
[Terminal]
bot_id = "terminal_bot"   # 沙盒機器人ID
bot_name = "Terminal"     # 顯示名稱
```

## v5 範式更新（1.1.0）

- **spawn_background 任務歸屬**：stdin 讀取迴圈改用 `runtime.spawn_background`
- **框架軟依賴**：運行時檢測 `ErisPulse>=2.7.1` 並提示；啟動輸出版本日誌

## 使用說明

```python
# 模組照常監聽訊息即可
from ErisPulse.Core.Event import message

@message.on_message()
async def handle(event):
    if event.get("platform") == "terminal":
        await event.reply("收到：" + event.get_text())
```

- 終端輸入的文本即使用者訊息，支援多行（以空行結束）
- 適用於開發期快速驗證模組邏輯，無需接入真實平台