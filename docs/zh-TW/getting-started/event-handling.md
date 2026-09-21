# 事件處理入門

本指南介紹如何處理 ErisPulse 中的各類事件。

## 事件類型概覽

ErisPulse 支持以下事件類型：

| 事件類型 | 說明 | 適用場景 |
|---------|------|---------|
| 消息事件 | 用戶發送的任何消息 | 聊天機器人、內容過濾 |
| 命令事件 | 以命令前綴開頭的消息 | 命令處理、功能入口 |
| 通知事件 | 系統通知（好友添加、群成員變化等） | 歡迎消息、狀態通知 |
| 請求事件 | 用戶請求（好友請求、群邀請） | 自動處理請求 |
| 元事件 | 系統級事件（連接、心跳） | 連接監控、狀態檢查 |

## 消息事件處理

> **提示**: 建議在事件處理器中使用 `Event` 類型註解，以獲得 IDE 自動補全和類型檢查支持。

```python
from ErisPulse.Core.Event import Event  # 導入事件類型用於註解
```

### 監聽所有消息

```python
from ErisPulse.Core.Event import message, Event

@message.on_message()
async def message_handler(event: Event):
    text = event.get_text()
    user_id = event.get_user_id()
    sdk.logger.info(f"收到 {user_id} 的消息: {text}")
```

### 監聽私聊消息

```python
@message.on_private_message()
async def private_handler(event: Event):
    user_id = event.get_user_id()
    await event.reply(f"你好，{user_id}！這是私聊消息。")
```

### 監聽群聊消息

```python
@message.on_group_message()
async def group_handler(event: Event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    sdk.logger.info(f"群 {group_id} 中 {user_id} 發送了消息")
```

### 監聽@消息

```python
@message.on_at_message()
async def at_handler(event: Event):
    # 獲取被@的用戶列表
    mentions = event.get_mentions()
    await event.reply(f"你@了這些用戶: {mentions}")
```

### 通配符與正則監聽

四個消息裝飾器（`on_message` / `on_private_message` / `on_group_message` /
`on_at_message`）均支持 `pattern`（glob 通配符）與 `regex`（正則），不匹配的消息
**不會觸發**處理器：

```python
# glob 通配符：* 任意串、? 單字符、[seq] 字符集
@message.on_message(pattern="簽到*")
async def signin_handler(event: Event):
    await event.reply("簽到成功")

# 正則：匹配金額
@message.on_message(regex=r"\d+\s*元")
async def price_handler(event: Event):
    await event.reply(f"收到金額：{event.get_text()}")

# pattern 與 regex 同時給出 → 兩者都須匹配
@message.on_message(pattern="*元", regex=r"\d+\s*元")
async def combined_handler(event: Event):
    pass
```

`wait_reply` 同樣支持這兩個參數（見[等待回覆](../developer-guide/modules/event-wrapper.md#等待回覆功能)）。

## 命令事件處理

### 基本命令

```python
from ErisPulse.Core.Event import command

@command("help", help="顯示幫助信息")
async def help_handler(event):
    help_text = """
可用命令：
/help - 顯示幫助
/ping - 測試連接
/info - 查看信息
    """
    await event.reply(help_text)
```

### 命令別名

```python
@command(["help", "h"], aliases=["幫助"], help="顯示幫助信息")
async def help_handler(event):
    await event.reply("幫助信息...")
```

用戶可以使用以下任何方式調用：
- `/help`
- `/h`
- `/幫助`

### 命令參數

```python
@command("echo", help="回顯消息")
async def echo_handler(event):
    # 獲取命令參數
    args = event.get_command_args()
    
    if not args:
        await event.reply("請輸入要回顯的訊息")
    else:
        await event.reply(f"你說了: {' '.join(args)}")
```

參數保留用戶輸入的原始大小寫（即使配置為大小寫不敏感，
命令名匹配歸一也不會影響參數內容）。

### 聲明式參數與選項（args= / options=）

手動解析參數需要自己處理類型轉換與錯誤提示。聲明 `args=` / `options=` 後，
框架在權限檢查通過後自動解析命令參數並**按名注入處理器**；用戶輸入錯誤時
自動回覆本地化提示與用法（不會拋異常崩潰），`/help <命令>` 也會自動展示用法：

```python
@command(
    "roll",
    args="<count:int> [sides:int=6]",
    options={"verbose": "-v/--verbose", "label": "--label"},
    help="擲骰子",
)
async def roll_handler(event, count: int, sides: int = 6, verbose: bool = False, label: str = ""):
    total = sum(random.randint(1, sides) for _ in range(count))
    await event.reply(f"擲了 {count} 次 {sides} 面骰，總點數：{total}")
```

`args=` 位置參數語法：`<count:int>` 必填、`[sides:int=6]` 可選（含默認值）。支持類型：

| 類型 | 示例輸入 | 說明 |
|------|---------|------|
| `str` | `hello` | 文本（缺省類型） |
| `int` / `float` | `3` / `0.5` | 數值 |
| `bool` | `是` / `yes` / `はい` / `да` / `true` / `no` / `取消` | 布爾值，複用交互確認（`Event.confirm()`）的確認詞表 |
| `literal` | `<mode:literal=fast|slow>` | 枚舉，僅接受列出的值；可選形式默認取首個 |
| `duration` | `90s`、`1h30m`、`1d` | 時長，按秒折算為 float |
| `rest` | `<text:rest>` | 剩餘全部文本（必須位於最後） |

`options=` 選項為字典式聲明：鍵為處理器參數名，值為旗標形式（多個別名以 `/` 分隔）。
註解為 `bool` 的參數是布爾旗標（出現即 `True`）；其餘（缺省按 `str`）是帶值選項，
支持 `--label hello` 與 `--label=hello` 兩種取值，類型跟隨處理器註解。
選項先被識別剔除，剩餘 token 再按 `args=` 解析（`rest` 覆蓋剔除選項後的剩餘文本）。

**行為要點**：

- 權限檢查先於參數解析——無權限用戶不會觸發解析
- 解析失敗（類型不符 / 缺少參數 / 參數過多 / 未知選項）自動回覆本地化錯誤 + 用法，命令仍被認領
- 聲明的參數名必須存在於處理器簽名中，否則註冊期拋 `ValueError`
- 不聲明 `args=` / `options=` 的命令行為完全不變（向後兼容）

### 命令治理（cooldown= / rate_limit= / deprecated=）

手寫冷卻計時、限流窗口、廢棄提示可用聲明替代，三者可任意組合。

**冷卻**——時長語法與 `args=` 的 `duration` 類型一致（如 `"30s"`、`"1h30m"`、`"1d"`）：

```python
@command("daily", cooldown="1d", cooldown_key="user", cooldown_reply="今天已簽到")
async def daily_handler(event):
    await event.reply("簽到成功！")
```

**限流**——滑動窗口聲明 `"次數/窗口"`（如 `"5/minute"`、`"10/s"`、`"3/2m"`）：

```python
@command("search", rate_limit="5/minute", rate_limit_key="user")
async def search_handler(event):
    await event.reply("搜索結果")
```

**廢棄**——調用時自動回覆廢棄文案，`deprecated_reject=True` 拒絕執行：

```python
@command("oldcmd", deprecated="請用 /newcmd", deprecated_reject=True)
async def old_handler(event): ...
```

鍵粒度（`cooldown_key=` / `rate_limit_key=`）：`"user"`（默認，同一用戶共享）、
`"session"`（同一會話共享，如同一群）、`"global"`（所有用戶所有會話共享）。

**行為要點**：

- 冷卻 / 限流命中默認**靜默丟棄**（對稱於作用域靜默）；聲明 `cooldown_reply=` / `rate_limit_reply=` 後命中即回覆該文案
- 命令命中即認領——治理命中的命令不會漏給低优先級消息處理器
- 治理判定位於全部權限檢查與參數解析通過、實際執行前：無權限用戶不觸發，參數錯誤不消耗
- 同時聲明冷卻與限流時冷卻先判（冷卻命中不占限流窗口）
- `deprecated=` 默認回覆文案後**繼續執行**；`deprecated_reject=True` 拒絕執行（`command.executed` 鉤子記 `success=False, error="deprecated"`）
- `/help` 列表與單命令幫助自動顯示廢棄標記與文案
- 狀態為進程內內存，模組卸載時自動清理；跨進程共享 / 重啟持久化不在範圍內
- 聲明在註冊期校驗（fail-fast）：語法非法、鍵粒度非白名單值、reply 未搭配主聲明均拋 `ValueError`

### 處理器節流（throttle=）

消息處理器防刷屏聲明——同鍵事件在間隔內至多處理一條，其餘靜默丟棄：

```python
from ErisPulse import sdk

@sdk.message.on_message(throttle="2s", throttle_key="user")
async def handler(event): ...
```

`on_message` / `on_private_message` / `on_group_message` / `on_at_message`
均支持；`throttle_key=` 與命令治理同一套鍵粒度（user / session / global），
時長語法與 `duration` 一致。節流與 `pattern=` / `regex=` 等既有條件疊加
生效（全部滿足才觸發）；間隔內丟棄僅記 TRACE 日誌；聲明在註冊期校驗。

### 依賴注入（Depends）

公共依賴（數據庫會話、配置讀取等）可抽為依賴函數，處理器以
`Depends(依賴函數)` 作為參數默認值聲明，框架在調用前自動以上下文對象
調用依賴函數並按名注入：

```python
from ErisPulse.Core import Depends

async def get_session(event):
    return await sdk.module.call("DB", "get_session")

@command("admin")
async def admin_handler(event, db=Depends(get_session)):
    ...
```

默認開啟**請求級緩存**：同一次事件分發內，相同依賴函數只解析一次、所有
注入點共享結果（如 `get_db` 在一次事件中只建一次數據庫會話）；跨請求自動
不複用。可用 `Depends(get_db, use_cache=False)` 關閉單條依賴的緩存。

覆蓋全部框架注入點——命令處理器、事件處理器（`message.on_message()` 等）、
生命週期鉤子（`sdk.lifecycle.on`）、SSE 路由處理器。依賴函數的第一個參數
是注入點上下文對象（事件場景為 `Event`，生命週期為事件 `data`，
路由為 `HttpRequest` / `SseEmitter`）；同步與異步依賴函數均可聲明。

**聲明其它模組的服務**（語法糖）：

```python
@command("query")
async def query_handler(event, session=Depends.module("DB", "get_session")):
    ...
```

`Depends.module(模組名, 方法名, *固定參數)` 等價於在依賴函數內調用
`sdk.module.call(...)`。模組實例化（`__init__`）不在覆蓋範圍——實例化時無
上下文對象；FastAPI 承載的 HTTP 路由請用 FastAPI 原生 `fastapi.Depends`。

**行為要點**：

- 聲明在註冊期校驗（fail-fast）：依賴不可調用、或與 `args=` / `options=` 參數重名時拋 `ValueError`
- 依賴函數拋出的異常與處理器自身異常同口徑處理（命令自動回覆錯誤）
- 不聲明 `Depends` 的處理器零開銷（分發期無任何反射）
- FastAPI 承載的 HTTP 路由請使用 FastAPI 原生 `fastapi.Depends`

### 命令組

```python
@command("admin.reload", group="admin", help="重新載入模組")
async def reload_handler(event):
    await event.reply("模組已重新載入")

@command("admin.stop", group="admin", help="停止機器人")
async def stop_handler(event):
    await event.reply("機器人已停止")
```

`group` 參數僅用於幫助列表歸類；上面示例中的 `admin.reload` 是一個**整體命令名**
（點號只是命名風格，用戶需輸入 `/admin.reload`）。

### 子命令

命令名支持**空格分隔**的多 token 形式，實現 `/admin add`、`/admin user ban` 這樣的子命令：

```python
@command("admin", help="管理命令")
async def admin_handler(event):
    await event.reply("用法：/admin add | /admin remove")

@command("admin add", help="添加管理員")
async def admin_add_handler(event):
    target = event.get_command_args()[0]
    await event.reply(f"已添加 {target}")

@command("admin remove", aliases=["a remove"], help="移除管理員")
async def admin_remove_handler(event):
    await event.reply("已移除")
```

匹配規則（**最長前綴匹配**）：

- `/admin add x` 优先命中 `admin add`，`event.get_command_args()` 返回 `["x"]`（子命令名之后的參數）
- 仅注册了 `admin` 时，`/admin add x` 命中 `admin`，`get_command_args()` 返回 `["add", "x"]`（歷史行為不變）
- 別名支持多 token 形式（如 `a remove`），也可用單 token 別名（如 `a`）指向子命令
- 父子命令同時註冊時，未註冊的子命令輸入（如 `/admin list x`）回落到父命令

**權限繼承**：子命令未聲明 `permission` 時，自動繼承父鏈上最近聲明了權限的祖先命令——
保護 `/admin` 即自動保護其下全部子命令；子命令自身聲明的權限優先：

```python
def is_admin(event):
    return event.get_user_id() in {"user123"}

@command("admin", permission=is_admin, help="管理命令")
async def admin_handler(event):
    ...

# 無需重複聲明 permission，自動繼承 is_admin
@command("admin add", help="添加管理員")
async def admin_add_handler(event):
    ...
```

注意：`master=True` 與 `hidden` **不會**繼承，需要時請在子命令上單獨聲明；
用戶 ACL（黑白名單）按命令全名匹配，glob 規則如 `"admin*"` 可覆蓋整組子命令。

`/help` 的命令總覽中，子命令會自動掛到可見的父命令下縮進展示
（`admin` → `admin add` 縮進一級，`admin user` → `admin user ban` 縮進兩級）。

### 命令權限與訪問控制

命令權限分三層，從上到下逐層判定（**上層拒絕則不再看下層**）：

```python
# ① 命令權限 ACL（用戶側配置）：按命令的用戶黑白名單，拒絕時回覆"權限不足"
# ② master=True —— 僅框架主人可執行（框架自動檢查，拒絕時回覆"權限不足"）
@command("restart", master=True, help="重啟模組")
async def restart_handler(event):
    await event.reply("模組已重啟")

# ③ permission=調用函數 —— 命令自身的控制邏輯（返回 True 才執行）
def is_admin(event):
    return event.get_user_id() in {"user123", "user456"}

@command("panel", permission=is_admin, help="管理面板")
async def panel_handler(event):
    await event.reply("歡迎來到管理面板")
```

**命令用戶 ACL**（`ErisPulse.event.command.acl`）：用戶可為任意命令配置用戶黑白名單，
命令名支持精確與 glob 模式（如 `"roll*"`），拒絕時回覆"權限不足"：

```toml
# config.toml —— 僅允許 123456 執行 restart；666 一律拒絕
[ErisPulse.event.command.acl.restart]
allow = ["onebot11:123456"]
deny = ["onebot11:666"]
```

判定順序：`deny` 命中 → 拒絕；`allow` 非空且未命中 → 拒絕；未配置 ACL 時遵循
`event.command.default_allow`（`false` = 嚴格模式，無 ACL 即拒；`true` 時交給開發者默認
`master=True` / `permission`）。運行時 API（命令名支持 glob）：

```python
from ErisPulse.Core.Event import command

command.allow_user("restart", "onebot11", "123456")   # 允許名單
command.deny_user("restart", "onebot11", "666")       # 拒絕名單
command.remove_acl("restart")                          # 清除黑白名單
command.get_acl("restart")                             # 查詢當前名單
```

> 命令處理器從事件包導入：`from ErisPulse.Core.Event import command`；
> 也可經 SDK 事件包訪問：`sdk.Event.command`（兩者為同一單例）。
> 在模組內通常已隨命令裝飾器導入（`from ErisPulse.Core.Event import command`）。

跨命令 / 跨用戶的**事件級**訪問控制（某人 / 某群 / 某 Bot 的消息收不收）
走作用域**身份維度**（`scope.identity`）；**模組級**可用性（哪些模組能用）
走作用域**模組維度**（`scope.platforms / bots / sessions`）。
詳見[作用域（scope）](../advanced/scope.md)。

> 建議：命令內部需要聯動業務邏輯的用 `master=True` / `permission`；純按用戶 / 群做
> 訪問控制的用作用域身份維度；控制模組可用性的用作用域模組維度。

### 命令優先級

```python
# 優先級數值越大，執行越早
@message.on_message(priority=10)
async def high_priority_handler(event):
    await event.reply("高優先級處理器")

@message.on_message(priority=1)
async def low_priority_handler(event):
    await event.reply("低優先級處理器")
```

### 並行事件處理

ErisPulse 事件系統採用**同優先級並行、不同優先級串行**的調度模型：

```
事件到達
    ↓
priority=10 組: [處理器C ||處理器D] 並行 → 合併結果
    ↓ (如未中斷)
priority=0 組: [處理器A ||處理器B] 並行 → 合併結果
    ↓
...
```

- **同優先級並行**：優先級相同的多個處理器會同時執行，提高吞吐量
- **跨級串行**：不同優先級的組按順序執行（數值越大越先執行），確保高優先級處理器先運行
- **Copy-On-Write**：處理器無修改時不創建副本，確保零開銷
- **衝突處理**：同優先級多處理器修改同一字段時，使用最後修改值並記錄警告日誌
- **中斷機制**：任意處理器調用 `event.done()`（默認）或 `event.done(claim=False)` 後，跳過後續低優先級組。認領與阻斷的區別見下文[「鏈路控制：認領與阻斷」](#鏈路控制認領與阻斷)

```python
# 示例：同優先級處理器並行執行
@message.on_message(priority=0)
async def handler_a(event):
    # 處理任務A
    event['result_a'] = process_a()

@message.on_message(priority=0)
async def handler_b(event):
    # 與 handler_a 並行執行
    event['result_b'] = process_b()

# 不同優先級串行執行
@message.on_message(priority=10)
async def handler_c(event):
    # 優先級最高，最先執行
    pass
```

> **併發上限**：所有匹配 handler 的 Task 會**立即創建**，但通過一個信號量限制**同時在途執行數**，默認上限 **64**（`ErisPulse.framework.handler_max_concurrency`，支持熱更新）。超過上限的 Task 在信號量上排隊，等前面的完成後再進。事件洪峰時這就是你的「泄壓閥」。
>
> **慢日誌**：單個處理器耗時超過 **1 秒**時，框架會在日誌打 WARNING（`handler_slow`）。`wait_reply` 的等待時間會從耗時裡剔除，不會因為「等人回覆」誤報慢。

## 中間件：分發前改寫或否決

中間件在事件分發**之前**順序執行，防火牆、限流、事件脫敏等場景的正統實現點：

```python
from ErisPulse.Core import adapter

@adapter.middleware
async def firewall(data):
    if _is_banned(data.get("user_id")):
        return False          # 否決：事件被丟棄，不進入任何處理器，無出站副作用
    data["checked"] = True    # 返回 dict：改寫載荷（與歷史行為一致）
    # 返回 None：放行，載荷不變（歷史行為）
    return data
```

| 返回值 | 行為 |
|--------|------|
| `False` | **否決**：事件立即丟棄，不進入任何處理器 |
| `dict` | 改寫事件載荷後繼續分發 |
| `None` | 放行，載荷不變 |

否決時框架輸出 TRACE 日誌並觸發 `adapter.event.blocked` 生命週期鉤子（攜帶中間件名與完整事件），供審計「事件為什麼沒響應」。

## 命令分發決策鏈：為什麼命令沒觸發

一條命令訊息依次經過：**命令文本判定 → 命令名/別名命中（未命中附拼寫建議）→ 命中即認領 → 作用域 → 用戶 ACL → 主人 → 權限 → 冷卻/限流 → 參數解析 → 執行**。任何一步不滿足即終止；治理命中（冷卻/限流）默認靜默丟棄，權限類拒絕會回覆用戶。

測試中 `ErisPulse-Testing` 的 `dispatch()` 直接返回這條決策鏈（`DispatchTrace`，`trace.explain()` 輸出逐行因果），生產環境可用 `ErisPulse.Core.Event.start_dispatch_trace()` 采集同樣的記錄。

## 作用域過濾：為什麼我的模組沒收到訊息

事件到達後有兩道**靜默**過濾（都不回覆、不報錯）：

1. **身份維度**（`ErisPulse.scope.identity`）：事件進入分發入口時，按 用戶 > 群 > Bot > 适配器 判定收不收。
   被拒絕的**整個事件**直接丟棄，任何處理器（含命令分發器）都不會觸發。
2. **模組維度**（`ErisPulse.scope`）：事件到達某模組的處理器/命令時，按 会話 > Bot > 平台 判定
   該模組是否可用，**不通過就靜默跳過**。

```toml
# 例1：某群所有訊息不傳播
[ErisPulse.scope.identity.sessions.onebot11."group_123"]
deny = true

# 例2：把 MyModule 屏蔽在某個 Bot
[ErisPulse.scope.bots.onebot11."123456"]
blocked = ["MyModule"]
```

此時該群的訊息到達時，`MyModule` 的命令與事件處理器**都不會被調度**。這不是 bug，是過濾機制——排查「模組沒反應」時優先檢查作用域的身份與模組綁定。

- 過濾日誌只在 **TRACE** 級可見（`core.scope.identity_denied` / `core.scope.denied`），默認 INFO 看不到任何痕跡
- 框架級處理器（如命令分發器 `scope_exempt=True`）不受**模組維度**影響，但受**身份維度**影響（整個事件已丟棄）
- 命令執行前還有第三道：命令用戶 ACL（拒絕時回覆"權限不足"，見上節）
- 第四道是**事件覆寫**（見下節）

> [!NOTE]
> **作用域過濾與事件認領（claim）的關係**：兩道靜默過濾都發生在處理器
> **調度之前**——被過濾跳過的處理器沒有機會執行，自然也不參與
> `event.done()` / `mark_processed()` 的認領狀態。事件是否已被認領，
> 只由**實際執行**的處理器（命令命中認領、回覆命中認領、顯式調用）決定；
> 作用域拒絕本身既不認領也不阻斷（靜默跳過，訊息繼續走完剩餘分發鏈）。

> 作用域配置、匹配語法、運行時 API 見 [作用域（scope）](../../advanced/scope.md)。

## 事件覆寫：不改模組代碼，覆寫任意事件類型的行為

> [!NOTE]
> 本特性需要 ErisPulse **2.8.0+**。

事件處理器在註冊時聲明的參數（`pattern` / `regex` / `master` / `hidden` 等）只是**開發者默認**。
統一覆寫系統讓用戶按**事件類型**覆寫任意模組的行為——OneBot12 標準類型
（meta / message / notice / request）與 ErisPulse 擴展類型（command）各自擁有專屬的可覆寫參數：

| 事件類型 | 可覆寫參數 | 作用 |
|---------|-----------|------|
| `message` | `pattern` / `regex` / `detail_types` | 文本觸發條件 + 訊息子類型白名單 |
| `notice` | `detail_types` / `pattern` / `regex` | 通知子類型白名單 + 文本條件 |
| `request` | `detail_types` / `pattern` / `regex` | 請求子類型白名單 + 文本條件 |
| `meta` | `detail_types` | 元事件子類型白名單（connect / heartbeat 等） |
| `command` | `master` / `hidden` / `aliases` / `prefix` / `help` / `usage` | 命令實現參數（用戶優先） |
| `acl`（command 專屬） | `allow` / `deny` | 命令用戶黑白名單（按命令名 glob） |

```toml
# message：覆寫文本觸發條件（與代碼內條件 AND）
[ErisPulse.event.overrides.message.ChatModule]
pattern = "閒聊*"

# notice：只響應特定通知子類型
[ErisPulse.event.overrides.notice.MyModule]
detail_types = ["group_increase"]

# command：覆寫實現參數（用戶優先——可收緊或放開開發者默認）
[ErisPulse.event.overrides.command.MyModule.restart]
master = true
hidden = true

# acl：命令用戶黑白名單（跨命令 glob）
[ErisPulse.event.overrides.acl."roll*"]
allow = ["onebot11:u_vip"]

# ACL 兜底（false = 嚴格模式：無 ACL 即拒）
acl_default_allow = true
```

運行時 API（`from ErisPulse.Core.Event import overrides` 或 `sdk.Event.overrides`，
**類型子命名空間**——每類型對稱的 `set` / `get` / `delete` 三件套）：

```python
from ErisPulse.Core.Event import overrides

overrides.message.set("ChatModule", pattern="閒聊*")   # message 文本條件
overrides.notice.set("MyModule", detail_types=["group_increase"])
overrides.command.set("MyModule", "restart", master=True)  # 命令參數
overrides.acl.set("roll*", deny=["onebot11:u_bad"])    # 命令用戶黑名單

overrides.message.get("ChatModule")     # {"pattern": "閒聊*"}
overrides.message.delete("ChatModule")  # 恢復開發者默認
```

- 覆寫條件與處理器代碼內條件**同時生效**（AND 語義）；`command` 參數與開發者聲明**深合併**（覆寫優先）
- `detail_types`：事件缺 `detail_type` 時放行（不誤殺未知事件）
- `pattern` / `regex`：無文本的事件（connect / heartbeat 等）不受約束，直接放行
- `command` 覆寫鍵 `master` 同步映射存儲鍵 `must_master`；禁用命令統一走 `acl` deny
- **鍵名映射說明**：`overrides.command.set("My", "restart", master=True)` 的參數名
  `master` 僅為配置別名，實際存儲鍵與 `get()` 返回值中的鍵名統一為 **`must_master`**
  （`get()` 返回 `{"must_master": true}`）——運行時判斷讀取的是存儲鍵，請勿按
  `master` 鍵名讀取
- 配置改了立即生效（熱更新），格式校驗告警（未知參數 / 壞條目忽略）

## 鏈路控制：認領與阻斷

> [!NOTE]
> `event.done()` / `event.mark_processed()` 的 `claim=` / `stop=` 參數本特性需要 ErisPulse **2.7.1+**。

ErisPulse 將「認領」與「阻斷」兩個正交語義解耦，通過 `event.done()` 統一控制，便於在命令處理周圍疊加日誌、審計、權限等觀察層。

**兩個概念的準確定義：**

- **認領（claim）**：標記事件已被本處理器處理（寫入 `_processed`）。命令分發器看到已認領的事件會**跳過去重**——避免同一訊息被多個命令處理器重複處理。典型場景：命令匹配成功後認領，阻止命令分發器再介入。
- **阻斷（stop）**：阻止事件向**更低優先級**處理器傳播（寫入 `_propagation_stopped`）。低優先級處理器將不再看到該事件。典型場景：高優先級處理器已完整處理事件，不希望低優先級再執行。

| `event.done(...)` | 認領 | 阻斷 | 場景 |
|-------------------|------|------|------|
| `event.done()` | ✔ | ✔ | 命令 / 處理器處理完的標準做法 |
| `event.done(stop=False)` | ✔ | ✘ | 僅認領，讓低優先級觀察者（日誌 / 統計）繼續看到 |
| `event.done(claim=False)` | ✘ | ✔ | 僅阻斷（如防火牆 / 限流），但不做命令去重 |

`event.done(claim=, stop=)` 是 `event.mark_processed(claim=, stop=)` 的別名，二者參數與行為完全等價。

```python
@command("help")
async def help_cmd(event):
    event.done()            # 認領 + 阻斷（命令處理完的標準做法）

@message.on_message(priority=50)
async def observer(event):
    event.done(stop=False)  # 僅認領：低優先級仍會執行（日誌 / 統計）

@message.on_message(priority=100)
async def firewall(event):
    if denied(event):
        event.done(claim=False)  # 僅阻斷：低優先級不執行，但不做去重
```

### 命令與回覆的 block 配置

**命令命中即認領**：訊息一旦匹配到已註冊命令名（含子命令/別名），無論後續作用域或權限判定結果如何，都會被認領並默認阻斷傳播——被權限拒絕的命令再也不會漏給低優先級訊息處理器（消除"命令被拒後 on_message 又響應一次"的雙重響應）。

可透過配置放行阻斷，讓低優先級觀察者（日誌 / 審計 / 權限）也能看到這些訊息：

```toml
[ErisPulse.event.command]
block = false   # 命令訊息繼續流向低優先級處理器（認領不受影響，不會重複消費）

[ErisPulse.event.wait_reply]
block = false   # 被 wait_reply 消費的回覆繼續流向低優先級處理器
```

> 注意：`block` 只控制**阻斷**（stop），不影響**認領**（claim）——命中的命令永遠不會被訊息處理器重複消費；未命中任何命令的訊息照常流向訊息處理器。

## 通知事件處理

### 好友添加

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event):
    user_id = event.get_user_id()
    nickname = event.get_user_nickname() or "新朋友"
    await event.reply(f"歡迎添加我為好友，{nickname}！")
```

### 群成員增加

```python
@notice.on_group_increase()
async def member_increase_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"歡迎新成員 {user_id} 加入群 {group_id}")
```

### 群成員減少

```python
@notice.on_group_decrease()
async def member_decrease_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"成員 {user_id} 離開了群 {group_id}")
```

## 請求事件處理

### 好友請求

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def friend_request_handler(event):
    user_id = event.get_user_id()
    comment = event.get_comment()
    
    sdk.logger.info(f"收到好友請求: {user_id}, 附言: {comment}")
    
    # 可以透過適配器 API 處理請求
    # 具體實現請參考各適配器文件
```

### 群邀請請求

```python
@request.on_group_request()
async def group_request_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    
    await event.reply(f"收到群 {group_id} 的邀請，來自 {user_id}")
```

## 元事件處理

### 連接事件

```python
from ErisPulse.Core.Event import meta

@meta.on_connect()
async def connect_handler(event):
    platform = event.get_platform()
    sdk.logger.info(f"{platform} 平台已連接")

@meta.on_disconnect()
async def disconnect_handler(event):
    platform = event.get_platform()
    sdk.logger.warning(f"{platform} 平台已斷開連接")
```

### 心跳事件

```python
@meta.on_heartbeat()
async def heartbeat_handler(event):
    platform = event.get_platform()
    sdk.logger.debug(f"{platform} 心跳檢測")
```

### Bot 狀態查詢

當適配器發送 meta 事件後，框架自動追蹤 Bot 狀態，你可以隨時查詢：

```python
from ErisPulse import sdk

# 檢查某個 Bot 是否在線
if sdk.adapter.is_bot_online("telegram", "123456"):
    telegram = sdk.adapter.get("telegram")
    await telegram.Send.To("user", "123456").Text("Bot 在線")

# 列出當前所有在線 Bot
bots = sdk.adapter.list_bots()
for platform, bot_list in bots.items():
    for bot_id, info in bot_list.items():
        print(f"{platform}/{bot_id}: {info['status']}")

# 獲取完整狀態摘要
summary = sdk.adapter.get_status_summary()
```

## 交互式處理

### 使用 reply 方法發送回覆

`event.reply()` 方法支援多種修飾參數，方便發送帶有 @、回覆等功能的訊息：

```python
# 簡單回覆
await event.reply("你好")

# 發送不同類型的訊息
await event.reply("http://example.com/image.jpg", method="Image")  # 圖片
await event.reply("http://example.com/voice.mp3", method="Voice")  # 語音

# @單個用戶
await event.reply("你好", at_users=["user123"])

# @多個用戶
await event.reply("大家好", at_users=["user1", "user2", "user3"])

# 回覆訊息
await event.reply("回覆內容", reply_to="msg_id")

# @全體成員
await event.reply("公告", at_all=True)

# 組合使用：@用戶 + 回覆訊息
await event.reply("內容", at_users=["user1"], reply_to="msg_id")
```

### 等待用戶回覆

```python
@command("ask", help="詢問用戶")
async def ask_handler(event):
    await event.reply("請輸入你的名字:")
    
    # 等待用戶回覆，超時時間 30 秒
    reply = await event.wait_reply(timeout=30)
    
    if reply:
        name = reply.get_text()
        await event.reply(f"你好，{name}！")
    else:
        await event.reply("等待超時，請重新輸入。")
```

> [!TIP]
> **等待期間命令仍然可用**（2.8.3+）：以命令前綴開頭且命中已註冊命令的
> 訊息（如 `/cancel`）會**執行命令**而非作為回覆內容，等待繼續掛起——
> 用戶可以隨時取消/切換，命令執行完仍可繼續回覆。需要"等待吞掉一切文本"
> 的旧行為時：配置 `ErisPulse.event.wait_reply.cmdpass = true`，或單次
> `wait_reply(cmdpass=True)`。

### 帶驗證的等待回覆

```python
@command("age", help="詢問年齡")
async def age_handler(event):
    def validate_age(event_data):
        """驗證年齡是否有效"""
        try:
            age = int(event_data.get_text())
            return 0 <= age <= 150
        except ValueError:
            return False
    
    await event.reply("請輸入你的年齡 (0-150):")
    
    reply = await event.wait_reply(
        timeout=60,
        validator=validate_age
    )
    
    if reply:
        age = int(reply.get_text())
        await event.reply(f"你的年齡是 {age} 歲")
    else:
        await event.reply("輸入無效或超時")
```

### 帶回調的等待回覆

```python
@command("confirm", help="確認操作")
async def confirm_handler(event):
    async def handle_confirmation(reply_event):
        text = reply_event.get_text().lower()
        
        if text in ["是", "yes", "y"]:
            await event.reply("操作已確認！")
        else:
            await event.reply("操作已取消。")
    
    await event.reply("確認執行此操作嗎？(是/否)")
    
    await event.wait_reply(
        timeout=30,
        callback=handle_confirmation
    )
```

### 確認對話 (confirm)

等待用戶確認或否定，自動識別內置中英文確認詞：

```python
@command("confirm", help="確認操作")
async def confirm_handler(event):
    if await event.confirm("確定要執行此操作嗎？"):
        await event.reply("已確認，執行中...")
    else:
        await event.reply("已取消")

# 自定義確認詞
if await event.confirm("繼續嗎？", yes_words={"go", "繼續"}, no_words={"stop", "停止"}):
    pass
```

### 選擇菜單 (choose)

用戶可回覆選項編號或選項文本：

```python
@command("choose", help="選擇")
async def choose_handler(event):
    choice = await event.choose(
        "請選擇顏色：",
        ["紅色", "綠色", "藍色"]
    )
    
    if choice is not None:
        colors = ["紅色", "綠色", "藍色"]
        await event.reply(f"你選擇了：{colors[choice]}")
    else:
        await event.reply("超時未選擇")
```

**合併模式**：`merge_prompt=True` 時將選項拼入提示訊息，用用戶指定的 `method` 一條訊息發送：

```python
# 用 Markdown 發送合併後的提示 + 選項
choice = await event.choose(
    "## 請選擇顏色\n{options}\n請回覆編號",
    ["紅色", "綠色", "藍色"],
    method="Markdown",
    merge_prompt=True,
)
```

> `{options}` 占位符控制選項插入位置；不寫則追加到 prompt 末尾。
> 可透過 `placeholder` 參數自定義占位符（如 `placeholder="[choices]"`）。
> `options_format="auto"`（默認）根據 method 自動選擇樣式：Markdown→無序列表，Html→有序列表，其他→純文本列表。
> 文本類方法（Text/Markdown/Html 等）默認合併選項到末尾；非文本方法（Image 等）默認拆分為兩條訊息。

### 收集表單 (collect)

多步驟收集用戶輸入：

```python
@command("register", help="註冊")
async def register_handler(event):
    data = await event.collect([
        {"key": "name", "prompt": "請輸入姓名："},
        {"key": "age", "prompt": "請輸入年齡：", 
         "validator": lambda e: e.get_text().isdigit()},
        {"key": "email", "prompt": "請輸入郵箱："}
    ])
    
    if data:
        await event.reply(f"註冊成功！\n姓名：{data['name']}\n年齡：{data['age']}\n郵箱：{data['email']}")
    else:
        await event.reply("註冊超時或輸入無效")
```

### 等待任意事件 (wait_for)

等待滿足條件的任意事件，不限於同一用戶：

```python
@command("wait_member", help="等待新成員")
async def wait_member_handler(event):
    await event.reply("等待群成員加入...")
    
    evt = await event.wait_for(
        event_type="notice",
        condition=lambda e: e.get_detail_type() == "group_member_increase",
        timeout=120
    )
    
    if evt:
        await event.reply(f"歡迎新成員：{evt.get_user_id()}")
    else:
        await event.reply("等待超時")
```

### 多輪對話 (conversation)

創建可互動的多輪對話上下文：

```python
@command("survey", help="問卷調查")
async def survey_handler(event):
    conv = event.conversation(timeout=60)
    
    await conv.say("歡迎參與問卷調查！")
    
    while conv.is_active:
        reply = await conv.wait()
        
        if reply is None:
            await conv.say("對話超時，再見！")
            break
        
        text = reply.get_text()
        
        if text == "退出":
            await conv.say("再見！")
            break
        
        await conv.say(f"你說了：{text}，繼續輸入或回覆'退出'結束")
```

### 內建確認詞

ErisPulse 內建了中英文確認詞集合：

- **確認詞** (`CONFIRM_YES_WORDS`): 是、yes、y、確認、確定、好、好的、ok、true、對、嗯、行、同意、沒問題...
- **否定詞** (`CONFIRM_NO_WORDS`): 否、no、n、取消、不、不要、不行、cancel、false、錯、拒絕、不可以...

## 事件數據訪問

### Event 對象常用方法

```python
@command("info")
async def info_handler(event):
    # 基礎信息
    event_id = event.get_id()
    event_time = event.get_time()
    event_type = event.get_type()
    detail_type = event.get_detail_type()
    
    # 發送者信息
    user_id = event.get_user_id()
    nickname = event.get_user_nickname()
    
    # 訊息內容
    message_segments = event.get_message()
    alt_message = event.get_alt_message()
    text = event.get_text()
    
    # 群組信息
    group_id = event.get_group_id()
    
    # 機器人信息
    self_id = event.get_self_user_id()
    self_platform = event.get_self_platform()
    
    # 原始數據
    raw_data = event.get_raw()
    raw_type = event.get_raw_type()
    
    # 平台信息
    platform = event.get_platform()
    
    # 訊息類型判斷
    is_private = event.is_private_message()
    is_group = event.is_group_message()
    is_at = event.is_at_message()
    
    # 命令信息
    if event.is_command():
        cmd_name = event.get_command_name()
        cmd_args = event.get_command_args()
        cmd_raw = event.get_command_raw()
```

### 平台擴展方法

除了內建方法外，各平台適配器還會註冊平台專有方法，方便你訪問平台特有的數據。

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    platform = event.get_platform()

    # 根據平台調用專有方法
    if platform == "telegram":
        chat_type = event.get_chat_type()      # Telegram 專有方法
    elif platform == "email":
        subject = event.get_subject()           # 郵件專有方法
```

如果不確定平台是否註冊了某個方法，可以查詢某個平台註冊了哪些方法：

```python
from ErisPulse.Core.Event import get_platform_event_methods

methods = get_platform_event_methods("telegram")
# ["get_chat_type", "is_bot_message", ...]
```

> 各平台註冊的專有方法請參閱對應的 [平台文件](../platform-guide/)。

## 事件處理最佳實踐

### 1. 異常處理

```python
@command("process")
async def process_handler(event):
    try:
        # 業務邏輯
        result = await do_some_work()
        await event.reply(f"結果: {result}")
    except ValueError as e:
        # 預期的業務錯誤
        await event.reply(f"參數錯誤: {e}")
    except Exception as e:
        # 未預期的錯誤
        sdk.logger.error(f"處理失敗: {e}")
        await event.reply("處理失敗，請稍後重試")
```

### 2. 日誌記錄

```python
@message.on_message()
async def message_handler(event):
    user_id = event.get_user_id()
    text = event.get_text()
    
    sdk.logger.info(f"處理訊息: {user_id} - {text}")
    
    # 使用模組自己的日誌
    from ErisPulse import sdk
    logger = sdk.logger.get_child("MyHandler")
    logger.debug(f"詳細調試資訊")
```

### 3. 條件處理

```python
@message.on_message(priority=0)
async def conditional_handler(event):
    """條件處理 - 在處理器內部判斷"""
    # 只處理特定用戶的訊息
    if event.get_user_id() in ["bot1", "bot2"]:
        return
    
    # 只處理包含特定關鍵詞的訊息
    if "關鍵詞" not in event.get_text():
        return
    
    await event.reply("條件滿足，處理訊息")
```