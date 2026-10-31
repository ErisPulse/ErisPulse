# Minecraft 平台特性文件

MinecraftAdapter 是基於 RCON 協議的 Minecraft Java 版伺服器適配器，支援命令執行、訊息傳送與日誌事件監聽。

---

## 文件資訊

- 對應模組版本: 0.1.0
- 維護者: ErisPulse

## 基本資訊

- 平台簡介：Minecraft Java 版伺服器機器人（透過 RCON 遠端控制台）
- 适配器名稱：MinecraftAdapter
- 多伺服器支援：支援（每帳號一臺伺服器，斷線自動重連）
- 連接方式：RCON TCP 長連線（保活 + 指數退避重連）
- 認證方式：RCON 密碼（server.properties 的 rcon.password）
- 事件監聽：日誌 tail（可選，聊天/加入/退出）
- 鏈式修飾支援：支援 `.At()` 等鏈式修飾方法
- OneBot12 兼容：僅 text 段（RCON 無法發送媒體）

## 伺服器前置設定

`server.properties`：

```properties
enable-rcon=true
rcon.port=25575
rcon.password=your_rcon_password
```

## 配置說明

```toml
[MinecraftAdapter.accounts.default]
host = "127.0.0.1"             # RCON 伺服器位址
port = 25575                   # RCON 端口
password = "your_rcon_password"
bot_id = ""                    # 留空預設為帳戶名
enable_log_tail = false        # 啟用日誌監聽（聊天/加入/退出事件）
log_path = "logs/latest.log"   # 日誌檔案路徑
poll_interval = 1.0            # 日誌掃描間隔（秒）
enabled = true
```

**配置項說明（每個帳戶）：**

- `host` / `port` / `password`：RCON 端點（必填）
- `bot_id`：事件中的機器人標識（預設為帳戶名），同時作為全服廣播的 `group_id`
- `enable_log_tail`：日誌事件開關（預設關閉）。關閉時適配器為純命令模式（只發送、不產生事件）
- `log_path`：日誌檔案路徑。要求適配器與伺服器**同機執行**或日誌目錄已掛載；支援日誌滾動（latest.log 輪轉後自動重置讀取位置）
- `poll_interval`：日誌掃描間隔（秒，最小 0.2）

## 消息發送

所有發送方法返回 Task，await 後得到標準響應（見「返回值格式」）。

### 基礎發送

```python
from ErisPulse import sdk
mc = sdk.adapter.get("minecraft")

# 單人消息（tellraw 純文本）
await mc.Send.To("user", "Steve").Text("Hello Steve")

# 全服廣播（say）
await mc.Send.To("server", "myserver").Text("伺服器廣播")
```

### 鏈式修飾方法

```python
# @玩家（tellraw 中內聯渲染為玩家名）
await mc.Send.To("server", "myserver").At("Steve").Text(" 看看這個")
```

### 多伺服器發送

```python
await mc.Send.Using("server2").To("server", "s2").Text("來自第二台伺服器")
```

### 支援與不支援的消息段

| 段 | 支援 | 說明 |
|----|------|------|
| `text` | 支援 | 拼接後按目標類型轉 tellraw / say |
| `mention` | 支援 | 渲染為玩家名內聯 |
| `reply` | 部分支援 | 接受但 Minecraft 無引用展示 |
| `image` / `audio` / `video` / `file` | 不支援 | 回傳 `retcode=10002` 並列出段類型 |

### 目標類型

| target_type | 行為 |
|-------------|------|
| `user` | `tellraw <玩家名> {"text":"..."}` 僅該玩家可見 |
| `server` / `group` | `say <內容>` 全服廣播（group_id 為 bot_id） |

## 標準 API 動作（Api）

```python
from ErisPulse import sdk
mc = sdk.adapter.get("minecraft")

# 在線玩家列表（解析 list 命令輸出）
result = await mc.Api.get_player_list()       # {"players": ["Steve", "Alex"], "raw": "..."}

# 連接狀態
result = await mc.Api.get_status()            # {"status": "ok", "connected": true}

# 伺服器身份
result = await mc.Api.get_self_info()         # {user_id, user_name, host}

# 版本
result = await mc.Api.get_version()

# 多伺服器
result = await mc.Api.Using("server2").get_player_list()
```

### 支援的標準動作

| 方法 | 說明 | 數據來源 |
|------|------|---------|
| `get_status()` | RCON 連接狀態 | 本地 |
| `get_self_info()` | 伺服器身份（bot_id/帳戶名/host:port） | 本地 |
| `get_player_list()` | 在線玩家列表（解析 `list` 命令輸出） | RCON |
| `get_version()` | 適配器版本 | 本地 |

### 平台擴展動作

透過 `Api.exec(cmd)` 執行任意 RCON 命令（等價於 `call_api("exec", command=...)`）：

```python
# 白名單管理
await mc.Api.exec("whitelist add Alex")
await mc.Api.exec("whitelist remove Alex")

# 伺服器管理
await mc.Api.exec("time set day")
await mc.Api.exec("weather clear")
await mc.Api.exec("op Alex")
await mc.Api.exec("kick Steve")

# 數據與計分板
await mc.Api.exec("scoreboard objectives add kills deathCount")
```

> **安全提醒**：`Api.exec` 擁有伺服器控制台完整權限（包括 stop/deop 等），請勿將未鑑權的入口暴露給不可信調用方。

### 不支援的標準動作

以下標準動作 RCON 無對應能力，調用返回 `retcode=10002` 或 `33001`（未連接）：

- `delete_message`（Minecraft 無訊息撤回）
- `get_friend_list` / `get_group_list`（用 `get_player_list` 替代）

### 通用動作入口

```python
# send_message：等價於 Send 鏈
result = await mc.call_api(
    "send_message",
    _account_id="default",
    target_type="user", target_id="Steve",
    message=[{"type": "text", "data": {"text": "hi"}}],
)
```

## 發送方法返回值

```python
{
    "status": "ok",                  # ok / failed
    "retcode": 0,                    # 0 成功；33001 未連接/執行失敗；10002 不支援
    "data": {"command_output": "..."},  # RCON 命令回顯
    "self": {"platform": "minecraft", "user_id": "mc1"},
    "message_id": "uuid",            # 生成的消息標識（tellraw/say 無真實消息 ID）
    "message": "",
    "minecraft_raw": {"output": "..."}
}
```

## 事件類型（enable_log_tail = true）

需要 `platform == "minecraft"` 檢測再使用本平台特性。**RCON 協議收不到聊天事件**（純請求-響應協議），事件面依賴日誌監聽。

### 事件映射

| 伺服器日誌行 | Adapter 事件 | 說明 |
|--------------|--------------|------|
| `[12:34:56] [...]: <Steve> 你好` | message（`detail_type: server`） | 玩家聊天 |
| `[12:35:00] [...]: Alex joined the game` | notice（`detail_type: server_joined`） | 玩家加入 |
| `[12:36:00] [...]: Alex left the game` | notice（`detail_type: server_left`） | 玩家退出 |

### 事件欄位示例

```python
# 聊天
{
  "id": "uuid",
  "time": 1793277000,
  "type": "message",
  "detail_type": "server",
  "platform": "minecraft",
  "self": {"platform": "minecraft", "user_id": "mc1", "user_name": "mc1", "account_id": "default"},
  "user_id": "Steve",                      # 玩家名
  "message": [{"type": "text", "data": {"text": "你好世界"}}],
  "alt_message": "你好世界",
  "group_id": "mc1",                       # bot_id
  "minecraft_raw": {"line": "[12:34:56] [Server thread/INFO]: <Steve> 你好世界"},
  "minecraft_raw_type": "log_line"
}

# 加入（notice）
{
  "type": "notice",
  "detail_type": "server_joined",          # 或 server_left
  "user_id": "Alex",
  "operator_id": "Alex",
  "group_id": "mc1",
  "minecraft_raw": {"line": "..."},
  "minecraft_raw_type": "log_line"
}
```

### 回環去重

`say` / `tellraw` 命令的回顯同樣會寫入日誌。適配器在發送時記錄內容指紋（30 秒視窗），日誌中出現相同內容時跳過發射，避免 bot 發出的消息被當成收到的事件回環。

## 注意事項

1. **RCON 無法接收聊天事件**：協議本身的限制（純請求-回應），事件面必須啟用日誌監聽
2. **日誌路徑可達性**：適配器與伺服器同機運行，或日誌目錄已掛載（容器場景掛載 `logs/`）
3. **日誌格式**：依賴 vanilla / 主流服務端（Paper、Fabric 等）預設格式；修改過日誌格式的插件（如自定義 chat 插件）可能解析不到
4. **RCON 併發限制**：Minecraft RCON 為單連接串行處理；適配器內建鎖與保活（30 秒空命令）
5. **回環去重視窗**：30 秒內相同內容只發射一次
6. **安全**：`Api.exec` 為控制台級權限，請勿暴露給不可信調用方