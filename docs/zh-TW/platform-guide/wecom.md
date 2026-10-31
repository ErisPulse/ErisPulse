# 企業微信（WeCom）平台特性文件

WeComAdapter 是基於企業微信自建應用 API 建構的轉接器，透過回呼接收訊息、應用訊息介面主動傳送，並提供通訊錄與訊息卡片能力。

---

## 文件資訊

- 對應模組版本： 0.1.0
- 維護者： ErisPulse

## 基本資訊

- 平台簡介：企業微信自建應用機器人，適用於企業內部通知、智慧問答、辦公自動化等場景
- 配接器名稱：WeComAdapter
- 多帳戶支援：支援同時設定多個企業（每個帳戶對應一個 corpid + 應用）
- 連線方式：HTTP 回呼接收（企業微信後台設定接收訊息 URL）+ 主動 API 傳送
- 認證方式：corpid + secret 換取 access_token（自動重新整理）
- 回呼加解密：Token + EncodingAESKey（企業微信官方加解密協定）
- 鏈式修飾支援：支援 `.Reply()` 等鏈式修飾方法
- OneBot12 相容：傳送支援 OneBot12 標準訊息段

## 配置說明

```toml
# config.toml
[WeComAdapter.accounts.default]
corpid = "YOUR_CORP_ID"        # 企業 ID（必填，企業微信後台-我的企業）
secret = "YOUR_APP_SECRET"     # 應用 Secret（必填，自建應用詳情頁）
agentid = 1000002              # 應用 AgentId（必填，自建應用詳情頁）
callback_enabled = true        # 啟用回調接收（預設 true；關閉後僅能主動發送）
token = "YOUR_CALLBACK_TOKEN"  # 回調驗證 Token（企業微信後台接收訊息配置）
encoding_aes_key = "YOUR_AES_KEY_43CHARS"  # 回調加解密金鑰（43 位）
callback_path = "/wecom/{account}"         # 回調路徑，支援 {account} 佔位符
enabled = true
```

**配置項說明（每個帳戶）：**

- `corpid` / `secret` / `agentid`：從[企業微信管理後台](https://work.weixin.qq.com)的自建應用頁獲取（前兩項必填）
- `callback_enabled`：回調接收開關（預設開啟）。**關閉後配接器跳過回調路由註冊，僅保留主動發送能力**；面板中回調相關欄位隨之隱藏
- `token` / `encoding_aes_key`：回調訊息驗證與加解密，與企業微信後台「接收消息」配置一致
- `callback_path`：回調接收路徑（預設 `/wecom/{帳戶名}`），企業微信後台需配置完整 URL：`http(s)://你的位址:連接埠/wecom/<帳戶名>`

**接收訊息前置條件**：企業微信後台 → 自建應用 → 「接收消息」設定 API 接收，URL 填入上述完整回調位址，Token 與 EncodingAESKey 與配置一致。**注意**：企業微信要求回調 URL 可從公網存取（建議搭配反向代理）。

**API 環境**：
- API 基礎位址：`https://qyapi.weixin.qq.com/cgi-bin`
- access_token 自動取得與快取重新整理，無需手動管理

## 訊息發送

```python
from ErisPulse import sdk
wecom = sdk.adapter.get("wecom")

# 基礎訊息（target_type: "user"=成員 "group"=應用群聊）
await wecom.Send.To("user", "zhangsan").Text("你好")
await wecom.Send.To("group", "group_chat_id").Markdown("**加粗**通知")

# 媒體（本地路徑 / bytes / URL；自動上傳臨時素材後發送）
await wecom.Send.To("user", "zhangsan").Image("banner.png")
await wecom.Send.To("user", "zhangsan").Voice("voice.amr")
await wecom.Send.To("user", "zhangsan").Video("demo.mp4")
await wecom.Send.To("user", "zhangsan").File("report.pdf")

# 圖文與卡片
await wecom.Send.To("user", "zhangsan").News([
    {"title": "標題", "description": "摘要", "url": "https://...", "picurl": "https://.../img.png"},
])  # 最多 8 條

await wecom.Send.To("user", "zhangsan").TextCard(
    title="審批提醒",
    description="您有一條待審批單據",
    url="https://oa.example.com/approval/1",
    btntxt="去處理",
)

await wecom.Send.To("user", "zhangsan").TemplateCard(
    card_type="text_notice",  # 企業微信卡片類型，其餘參數按官方卡片 JSON 透傳
    source={"icon_url": "...", "desc": "OA"},
    main_title={"title": "會議提醒"},
)

# 被動回覆：收到訊息的 event.reply() 直接回覆來源用戶
```

## 標準 API 動作

```python
info = await wecom.Api.get_self_info()          # 應用資訊（corpid/agentid）
status = await wecom.Api.get_status()           # 執行狀態
ver = await wecom.Api.get_version()             # 轉接器版本

# 通訊錄（2.1.0 新增，自動注入 access_token）
user = await wecom.Api.get_user_info("zhangsan")            # 成員詳情（姓名/部門/職務/頭像）
depts = await wecom.Api.get_department_list(0)              # 部門列表（0=根部門）
members = await wecom.Api.get_department_users(2)           # 部門成員列表
uid = await wecom.Api.get_user_by_mobile("13800000000")     # 手機號碼查詢 userid
openid = await wecom.Api.userid_to_openid("zhangsan")       # userid → openid（紅包/對外支付）
userid = await wecom.Api.openid_to_userid("oXXXX")          # openid → userid

# 多帳戶
result = await wecom.Api.Using("corp2").get_user_info("lisi")

# 任意企業微信 API 直調（endpoint 相對 cgi-bin，自動帶 access_token）
result = await wecom.Api.call("message/send", touser="zhangsan", msgtype="text", agentid=1000002, text={"content": "hi"})
```

## 事件說明

- 訊息事件：`detail_type` 為 `private`（成員發送訊息）/ `group`（應用群聊訊息）；`user_id` 為成員 userid
- 事件物件提供 `get_raw_xml()`（原始回呼 XML）等擴充讀取方法
- 上報事件（訂閱/選單點擊等）轉換為 `request` / `notice` 類事件

## 注意事項

1. **回呼 URL 必須公網可達**：本地開發可用內網穿透；生產環境建議 Nginx 反代到 ErisPulse router 連接埠
2. **主動發送頻率**：受企業微信應用訊息介面限制（每應用每日量與企業規模相關），群發場景請用 `TaskCard`/`TemplateCard` 結合標籤
3. **access_token 有效性**：轉接器自動重新整理；多實例部署同一 corpid+secret 時注意官方 token 互踢限制（建議由一個實例統一收發為宜）
4. **媒體檔案**：Voice 需 AMR 格式（企業微信限制）；大檔案走臨時素材介面（轉接器自動處理）