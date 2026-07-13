# 常見任務範例

本指南提供常見功能的實作範例，幫助您快速實作常用功能。

## 內容列表

1. 資料持久化
2. 定時任務
3. 訊息過濾
4. 多平台適配
5. 訊息傳送進階（重試/逾時/批次）
6. 權限控制
7. 訊息統計
8. 搜尋功能
9. 圖片處理

## 資料持久化

### 簡單計數器

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command

@command("count", help="檢視命令呼叫次數")
async def count_handler(event):
    # 取得計數
    count = sdk.storage.get("command_count", 0)
    
    # 增加計數
    count += 1
    sdk.storage.set("command_count", count)
    
    await event.reply(f"這是第 {count} 次呼叫此命令")
```

### 使用者資料儲存

```python
@command("profile", help="檢視個人資料")
async def profile_handler(event):
    user_id = event.get_user_id()
    
    # 取得使用者資料
    user_data = sdk.storage.get(f"user:{user_id}", {
        "nickname": "",
        "join_date": None,
        "message_count": 0
    })
    
    profile_text = f"""
暱稱: {user_data['nickname']}
加入時間: {user_data['join_date']}
訊息數: {user_data['message_count']}
    """
    
    await event.reply(profile_text.strip())

@command("setnick", help="設定暱稱")
async def setnick_handler(event):
    user_id = event.get_user_id()
    args = event.get_command_args()
    
    if not args:
        await event.reply("請輸入暱稱")
        return
    
    # 更新使用者資料
    user_data = sdk.storage.get(f"user:{user_id}", {})
    user_data["nickname"] = " ".join(args)
    sdk.storage.set(f"user:{user_id}", user_data)
    
    await event.reply(f"暱稱已設定為: {' '.join(args)}")
```

## 定時任務

### 簡單計時器

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command
import asyncio

class TimerModule:
    def __init__(self):
        self.sdk = sdk
        self._tasks = []
    
    async def on_load(self, event):
        """模組載入時啟動定時任務"""
        self._start_timers()
        
        @command("timer", help="計時器管理")
        async def timer_handler(event):
            await event.reply("計時器正在執行中...")
    
    def _start_timers(self):
        """啟動定時任務"""
        # 每 60 秒執行一次
        task = asyncio.create_task(self._every_minute())
        self._tasks.append(task)
        
        # 每天凌晨執行
        task = asyncio.create_task(self._daily_task())
        self._tasks.append(task)
    
    async def _every_minute(self):
        """每分鐘執行的任務"""
        self.sdk.logger.info("每分鐘任務執行")
        # 你的邏輯...
    
    async def _daily_task(self):
        """每天凌晨執行的任務（註：基於 UTC 時間計算，如需本地時間請自行調整）"""
        import time
        
        while True:
            # 計算到凌晨的時間
            now = time.time()
            midnight = now + (86400 - now % 86400)
            
            await asyncio.sleep(midnight - now)
            
            # 執行任務
            self.sdk.logger.info("每日任務執行")
            # 你的邏輯...
```

### 使用生命週期事件

```python
@sdk.lifecycle.on("core.init.complete")
async def init_complete_handler(event_data):
    """SDK 初始化完成後啟動定時任務"""
    import asyncio
    
    async def daily_reminder():
        """每日提醒"""
        await asyncio.sleep(86400)  # 24小時
        sdk.logger.info("執行每日任務")
    
    # 啟動背景任務
    asyncio.create_task(daily_reminder())
```

## 訊息過濾

### 關鍵字過濾

```python
from ErisPulse.Core.Event import message

blocked_words = ["垃圾", "廣告", "釣魚"]

@message.on_message()
async def filter_handler(event):
    text = event.get_text()
    
    # 檢查是否包含敏感詞
    for word in blocked_words:
        if word in text:
            sdk.logger.warning(f"攔截敏感訊息: {word}")
            return  # 不處理此訊息
    
    # 正常處理訊息
    await event.reply(f"收到: {text}")
```

### 黑名單過濾

```python
# 從設定或儲存載入黑名單
blacklist = sdk.storage.get("user_blacklist", [])

@message.on_message()
async def blacklist_handler(event):
    user_id = event.get_user_id()
    
    if user_id in blacklist:
        sdk.logger.info(f"黑名單使用者: {user_id}")
        return  # 不處理
    
    # 正常處理
    await event.reply(f"你好，{user_id}")
```

## 多平台適配

### 平台特定回應

```python
@command("help", help="顯示說明")
async def help_handler(event):
    platform = event.get_platform()
    
    if platform == "yunhu":
        await event.reply("雲湖平台說明...")
    elif platform == "telegram":
        await event.reply("Telegram platform help...")
    elif platform == "onebot11":
        await event.reply("OneBot11 help...")
    else:
        await event.reply("通用說明訊息")
```

### 平台特性檢測

```python
@command("rich", help="傳送富文字訊息")
async def rich_handler(event):
    platform = event.get_platform()
    
    if platform == "yunhu":
        # 雲湖支援 HTML
        yunhu = sdk.adapter.get("yunhu")
        await yunhu.Send.To("user", event.get_user_id()).Html(
            "<b>加粗文字</b><i>斜體文字</i>"
        )
    elif platform == "telegram":
        # Telegram 支援 Markdown
        telegram = sdk.adapter.get("telegram")
        await telegram.Send.To("user", event.get_user_id()).Markdown(
            "**加粗文字** *斜體文字*"
        )
    else:
        # 其他平台使用純文字
        await event.reply("加粗文字 斜體文字")
```

## 訊息傳送進階（重試/逾時/批次）

除了簡單的 `event.reply()`，您還可以透過適配器的 Send DSL 實作更複雜的傳送場景：失敗自動重試、逾時取消、成功後執行邏輯、批次傳送多條訊息。

> 下方的範例用 `event.get_detail_type()` 和 `event.get_target_id()` 從事件中取得目標類型和 ID（群聊自動取 group_id，私聊自動取 user_id），避免硬編碼。

### 傳送成功後執行邏輯

```python
@command("pay", help="模擬支付")
async def pay_handler(event):
    yunhu = sdk.adapter.get(event.get_platform())
    user_id = event.get_user_id()
    # 傳送成功後才扣積分
    await (yunhu.Send.To(event.get_detail_type(), event.get_target_id())
           .Hook(lambda r: sdk.storage.set(f"points:{user_id}", -10))
           .Text("支付成功，已扣除 10 積分"))
```

### 失敗重試 + 逾時取消

```python
@command("notice", help="傳送重要通知")
async def notice_handler(event):
    adapter_inst = sdk.adapter.get(event.get_platform())
    # 最多重試 3 次，每次逾時 10 秒
    task = (adapter_inst.Send.To(event.get_detail_type(), event.get_target_id())
            .Retry(3)
            .Timeout(10)
            .OnError(lambda ctx: sdk.logger.error(f"通知傳送失敗: {ctx.error}"))
            .Text("這是一條重要通知"))
    # 不等待，背景傳送
```

### 批次傳送多條訊息

一條鏈路傳送多條訊息，統一執行：

```python
@command("announce", help="傳送公告")
async def announce_handler(event):
    adapter_inst = sdk.adapter.get(event.get_platform())
    # 建構多條訊息，統一傳送（預設並行）
    results = await (adapter_inst.Send.To(event.get_detail_type(), event.get_target_id())
                    .Build()
                    .Text("📋 今日公告")
                    .Image("https://example.com/banner.jpg")
                    .Text("詳細內容見上方圖片")
                    .Retry(2)            # 失敗的項目各自重試
                    .send_all())
    sdk.logger.info(f"批次傳送完成，共 {len(results)} 條")
```

> 更完整的規則與批次說明請參考 [平台特性指南](../platform-guide/README.md#傳送規則裝飾器)。

## 權限控制

### 管理員檢查

```python
# 設定主人列表
MASTERS = ["user123", "user456"]

def is_master(user_id):
    """檢查是否為框架主人"""
    return user_id in MASTERS

@command("master", help="框架主人命令")
async def master_handler(event):
    user_id = event.get_user_id()
    
    if not is_master(user_id):
        await event.reply("權限不足，此命令僅框架主人可用")
        return
    
    await event.reply("框架主人命令執行成功")

@command("addmaster", help="新增框架主人")
async def addmaster_handler(event):
    if not is_master(event.get_user_id()):
        return
    
    args = event.get("text", "").split()
    if len(args) < 2:
        await event.reply("用法: /addmaster <使用者ID>")
        return
    
    new_master = args[0]
    MASTERS.append(new_master)
    await event.reply(f"已新增框架主人: {new_master}")
```

### 群組權限

```python
@command("groupinfo", help="檢視群組資訊")
async def groupinfo_handler(event):
    if not event.is_group_message():
        await event.reply("此命令僅限群聊使用")
        return
    
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    
    await event.reply(f"群組 ID: {group_id}, 你的 ID: {user_id}")
```

## 訊息統計

### 訊息計數

> **注意**：以下範例使用 `sdk.storage.get/set` 進行簡單計數。在高並發場景下，建議使用 `sdk.storage.transaction()` 保證原子性。

```python
@message.on_message()
async def count_handler(event):
    # 取得統計
    stats = sdk.storage.get("message_stats", {
        "total": 0,
        "by_user": {},
        "by_day": {}
    })
    
    # 更新統計
    stats["total"] += 1
    
    user_id = event.get_user_id()
    stats["by_user"][user_id] = stats["by_user"].get(user_id, 0) + 1
    
    # 儲存
    sdk.storage.set("message_stats", stats)

@command("stats", help="檢視訊息統計")
async def stats_handler(event):
    stats = sdk.storage.get("message_stats", {
        "total": 0,
        "by_user": {},
        "by_day": {}
    })
    
    top_users = sorted(
        stats["by_user"].items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]
    
    top_text = "\n".join(
        f"{uid}: {count} 條訊息" for uid, count in top_users
    )
    
    await event.reply(f"總訊息數: {stats['total']}\n\n活躍使用者:\n{top_text}")
```

## 搜尋功能

### 簡單搜尋

> **注意**：以下範例使用記憶體列表儲存訊息歷史，**程式重新啟動後資料會遺失**。生產環境建議使用 `sdk.storage` 或 SQLite 表進行持久化儲存。

```python
from ErisPulse.Core.Event import command, message

# 儲存訊息歷史
message_history = []

@message.on_message()
async def store_handler(event):
    """儲存訊息用於搜尋"""
    user_id = event.get_user_id()
    text = event.get_text()
    
    message_history.append({
        "user_id": user_id,
        "text": text,
        "time": event.get_time()
    })
    
    # 限制歷史記錄數量
    if len(message_history) > 1000:
        message_history.pop(0)

@command("search", help="搜尋訊息")
async def search_handler(event):
    args = event.get_command_args()
    
    if not args:
        await event.reply("請輸入搜尋關鍵字")
        return
    
    keyword = " ".join(args)
    results = []
    
    # 搜尋歷史記錄
    for msg in message_history:
        if keyword in msg["text"]:
            results.append(msg)
    
    if not results:
        await event.reply("未找到符合的訊息")
        return
    
    # 顯示結果
    result_text = f"找到 {len(results)} 條符合訊息:\n\n"
    for i, msg in enumerate(results[:10], 1):  # 最多顯示 10 條
        result_text += f"{i}. {msg['text']}\n"
    
    await event.reply(result_text)
```

## 圖片處理

### 圖片下載和儲存

```python
from ErisPulse.Core import client

@message.on_message()
async def image_handler(event):
    """處理圖片訊息"""
    message_segments = event.get_message()
    
    for segment in message_segments:
        if segment.get("type") == "image":
            file_url = segment.get("data", {}).get("file")
            
            if file_url:
                # 建議使用 SDK 內建用戶端下載圖片
                resp = await client.get(file_url)
                if resp.status == 200:
                    image_data = await resp.read()
                    
                    # 儲存到檔案
                    filename = f"images/{event.get_time()}.jpg"
                    with open(filename, "wb") as f:
                        f.write(image_data)
                    
                    sdk.logger.info(f"圖片已儲存: {filename}")
                    await event.reply("圖片已儲存")
```

### 圖片識別範例

> **注意**：以下範例使用佔位 API 位址，實際使用時請替換為您自己的圖片識別服務。

```python
from ErisPulse.Core import client

@command("identify", help="識別圖片")
async def identify_handler(event):
    """識別訊息中的圖片"""
    message_segments = event.get_message()
    
    for segment in message_segments:
        if segment.get("type") == "image":
            file_url = segment.get("data", {}).get("file")
            
            # 呼叫圖片識別 API
            result = await _identify_image(file_url)
            
            await event.reply(f"識別結果: {result}")
            return
    
    await event.reply("未找到圖片")

async def _identify_image(url):
    """呼叫圖片識別 API（範例）- 使用 SDK 內建用戶端"""
    resp = await client.post(
        "https://api.example.com/identify",
        json={"url": url}
    )
    data = await resp.json()
    return data.get("description", "識別失敗")
```

## 下一個步驟

- [使用者使用指南](../user-guide/) - 了解設定和模組管理
- [開發者指南](../developer-guide/) - 學習開發模組和適配器
- [進階主題](../advanced/) - 深入了解框架特性