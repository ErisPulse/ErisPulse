# Sandbox 平台特性文件

SandboxAdapter 是 ErisPulse 內建的沙盒適配器，用於本地開發與模組調試——無需真實平台即可模擬訊息的收發。

---

## 文件資訊

- 對應模組版本: 4.1.0
- 維護者: ErisPulse

## 基本資訊

- 平台簡介：本地沙盒環境，提供虛擬使用者/群組、Web 調試面板與訊息持久化
- 適配器名稱：SandboxAdapter
- 平台標識：`sandbox`
- 單帳戶設計（本地調試場景）
- 框架要求：軟依賴 `ErisPulse>=2.7.1`（執行時檢測提示，不強制）

## v5 範式更新（4.1.0）

- **Api DSL 最小集**：`get_self_info` / `get_status` / `get_version` / `get_supported_actions`
- **spawn_background 任務歸屬**：心跳任務改用 `runtime.spawn_background`
- **框架軟依賴**：運行時偵測 `ErisPulse>=2.7.1` 並提示
- 導入路徑更新至 `Core.Bases`（BaseConfig）

## 標準 API 動作示例

```python
from ErisPulse import sdk
sandbox = sdk.adapter.get("sandbox")

result = await sandbox.Api.get_self_info()   # 沙盒機器人身份
result = await sandbox.Api.get_status()
result = await sandbox.Api.get_supported_actions()
```

## 使用說明

- 沙盒提供虛擬用戶與群組，模組可像真實平台一樣收發訊息
- Web 調試面板可手動發送訊息觸發模組處理邏輯
- 訊息數據持久化儲存，重啟後可恢復