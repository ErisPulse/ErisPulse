# ErisPulse 适配器標準化回傳規範

## 1. 說明  
為什麼會有這個規範？  

為了確保各平台發送介面返回的統一性與 OneBot12 兼容性，ErisPulse 適配器在 API 回應格式上採用了 OneBot12 定義的消息發送回傳結構標準。  

不過 ErisPulse 的協定有一些特殊性定義：  
- 1. 基礎欄位中，`message_id` 是必需的，但 OneBot12 標準中並無此欄位  
- 2. 回傳內容中需要添加 `{platform_name}_raw` 欄位，用於存放原始回應資料

## 2. 基礎返回結構  
所有動作響應必須包含以下基礎字段：

| 字段名 | 數據類型 | 必選 | 說明 |
|-------|---------|------|------|
| status | string | 是 | 執行狀態，必須是"ok"或"failed" |
| retcode | int64 | 是 | 返回碼，遵循OneBot12返回碼規則 |
| data | any | 是 | 响应数据，成功时包含请求结果，失败时为null |
| message_id | string | 是 | 消息ID，用於標識消息，沒有則為空字串 |
| message | string | 是 | 錯誤信息，成功時為空字串 |
| {platform_name}_raw | any | 否 | 原始響應數據 |

可選字段：
| 字段名 | 數據類型 | 必選 | 說明 |
|-------|---------|------|------|
| echo | string | 否 | 當請求中包含echo字段時，原樣返回 |

## 3. 完整欄位規範

### 3.1 通用欄位

#### 成功回應範例
```json
{
    "status": "ok",
    "retcode": 0,
    "data": {
        "message_id": "1234",
        "time": 1632847927.599013
    },
    "message_id": "1234",
    "message": "",
    "echo": "1234",
    "telegram_raw": {...}
}
```

#### 失敗回應範例
```json
{
    "status": "failed",
    "retcode": 10003,
    "data": null,
    "message_id": "",
    "message": "缺少必要參數: user_id",
    "echo": "1234",
    "telegram_raw": {...}
}
```

### 3.2 回傳碼規範

#### 0 成功（OK）
- 0: 成功（OK）

#### 1xxxx 動作請求錯誤（Request Error）
| 錯誤碼 | 錯誤名 | 說明 |
|-------|-------|------|
| 10001 | Bad Request | 無效的動作請求 |
| 10002 | Unsupported Action | 不支援的動作請求 |
| 10003 | Bad Param | 無效的動作請求參數 |
| 10004 | Unsupported Param | 不支援的動作請求參數 |
| 10005 | Unsupported Segment | 不支援的訊息段類型 |
| 10006 | Bad Segment Data | 無效的訊息段參數 |
| 10007 | Unsupported Segment Data | 不支援的訊息段參數 |
| 10101 | Who Am I | 未指定機器人帳號 |
| 10102 | Unknown Self | 未知的機器人帳號 |

#### 2xxxx 動作處理器錯誤（Handler Error）
| 錯誤碼 | 錯誤名 | 說明 |
|-------|-------|------|
| 20001 | Bad Handler | 動作處理器實作錯誤 |
| 20002 | Internal Handler Error | 動作處理器執行時拋出例外 |

#### 3xxxx 動作執行錯誤（Execution Error）
| 錯誤碼範圍 | 錯誤類型 | 說明 |
|-----------|---------|------|
| 31xxx | Database Error | 資料庫錯誤 |
| 32xxx | Filesystem Error | 檔案系統錯誤 |
| 33xxx | Network Error | 網路錯誤 |
| 34xxx | Platform Error | 機器人平台錯誤 |
| 35xxx | Logic Error | 動作邏輯錯誤 |
| 36xxx | I Am Tired | 實現決定罷工 |

#### 保留錯誤段
- 4xxxx、5xxxx: 保留段，不應使用
- 6xxxx～9xxxx: 其他錯誤段，供實現自訂使用

## 4. 實現要求
1. 所有回應必須包含 status、retcode、data 和 message 欄位
2. 當請求中包含非空 echo 欄位時，回應必須包含相同值的 echo 欄位
3. 回傳碼必須嚴格遵循 OneBot12 規範
4. 錯誤訊息 (message) 應當是人類可讀的描述

## 5. 扩展規範

ErisPulse 在 OneBot12 標準返回結構之上做了以下擴展：

### 5.1 `message_id` 必選字段

OneBot12 標準中 `message_id` 位於 `data` 對象內部且非強制。ErisPulse 將其提升為頂層**必選**字段：

- 無法獲取 `message_id` 時應設為空字串 `""`
- 確保 `message_id` 始終存在，模組無需做 null 檢查

### 5.2 `{platform}_raw` 原始回應字段

回應值中應包含 `{platform}_raw` 字段，存放平台原始回應數據的完整副本：

```json
{
    "status": "ok",
    "retcode": 0,
    "data": {"message_id": "1234", "time": 1632847927},
    "message_id": "1234",
    "message": "",
    "telegram_raw": {
        "ok": true,
        "result": {"message_id": 1234, "date": 1632847927, ...}
    }
}
```

**要求**：
- `{platform}_raw` 必須是原始回應的深拷貝，而非引用
- `platform` 必須與適配器註冊時的平台名完全一致（大小寫敏感）
- 原始回應中的錯誤資訊也應保留，便於除錯

### 5.3 框架擴展回應碼（34xxx 平台錯誤段的低三位自訂）

OneBot12 規範允許實現自訂 `3xxxx` 的低三位。`34xxx` 語意為 **Platform Error**
（機器人平台錯誤，如平台限制導致失敗）。`34xxx` 內部按職責分層使用：

| 低三位段 | 歸屬 | 用途 |
|---------|------|------|
| `340xx` | 適配器實現 | 請求操作族（Request Not Found / Already Handled / Not Supported / Permission Denied，見 request-action-spec §7） |
| `341xx`～`345xx` | 適配器實現 | 平台側權限 / 風控 / 帳號限制等錯誤（實現自定低三位，原始錯誤放 `{platform}_raw`） |
| `346xx` | **ErisPulse 框架（保留）** | 框架自身攔截與通用失敗，適配器/模組請勿占用 |
| `347xx`～`349xx` | 適配器實現 | 其它平台執行錯誤 |

ErisPulse 框架目前使用的 `346xx` 碼：

| 錯誤碼 | 錯誤名 | 說明 |
|-------|-------|------|
| 34600 | SDK Failure | 框架通用失敗（`make_error()` 預設回傳碼） |
| 34601 | Action Denied | 出站動作被控制面禁用（`scope.actions`），呼叫未發起，直接回傳該回應 |

> 職責區分：`34601` 是**框架在呼叫前攔截**（模組根本沒資格發起動作）；
> `34004` / `34xxx` 平台碼是**動作已發出但平台拒絕**（如 Bot 無權限、被風控）。
> 模組判斷權限問題時同時檢查這兩種：先看 `34601`（自己模組被 scope 禁），
> 再看 `34xxx`（平台側限制）。

回應結構為 §2 標準失敗回應：

```json
{
    "status": "failed",
    "retcode": 34601,
    "data": null,
    "message_id": "",
    "message": "action 'send' denied by scope.actions"
}
```

### 5.4 適配器實現檢查清單

- [ ] 包含 `status`, `retcode`, `data`, `message_id`, `message` 字段
- [ ] 回應碼遵循 OneBot12 規範（詳見 §3.2）
- [ ] `message_id` 始終存在（無法獲取時為空字串）
- [ ] `{platform}_raw` 包含平台原始回應數據

## 6. 注意事項
- 對於 3xxxx 錯誤碼，低三位可由實作自行定義
- 避免使用保留錯誤區段 (4xxxx、5xxxx)
- **`34600` / `34601` 為 ErisPulse 框架保留碼**（見 §5.3），適配器/模組應避免使用
- 錯誤訊息應當簡潔明瞭，便於除錯