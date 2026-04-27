# Matrix平台特性文件

MatrixAdapter 是基於 [Matrix協議](https://spec.matrix.org/) 構建的適配器，整合了Matrix協議的所有核心功能模組，提供統一的事件處理和消息操作介面。

---

## 文件資訊

- 對應模組版本: 1.0.0
- 維護者: ErisPulse

## 基本資訊

- 平台簡介：Matrix是一個開放的去中心化通訊協議，支援私聊、群組等多種場景
- 適配器名稱：MatrixAdapter
- 連接方式：Long Polling（通過 Matrix Sync API `/sync`）
- 認證方式：基於 access_token 或 user_id + password 登入獲取 token
- 鏈式修飾支援：支援 `.Reply()`、`.At()`、`.AtAll()` 等鏈式修飾方法
- OneBot12相容：支援傳送 OneBot12 格式消息

## 配置說明

```toml
# config.toml
[Matrix_Adapter]
homeserver = "https://matrix.org"          # Matrix伺服器位址（必填）
access_token = "YOUR_ACCESS_TOKEN"          # 存取令牌（與 user_id+password 二選一）
user_id = ""                                # Matrix使用者ID（如 @bot:matrix.org）
password = ""                               # Matrix使用者密碼
auto_accept_invites = true                  # 是否自動接受房間邀請（可選，預設為true）
```

**配置項說明：**
- `homeserver`：Matrix伺服器位址（必填），預設為 `https://matrix.org`
- `access_token`：存取令牌，可從Matrix用戶端獲取。如果已有 token，直接填寫即可
- `user_id`：