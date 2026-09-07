# 常見任務範例

本指南提供常見功能的實現範例，幫助你快速實現常用功能。

## 內容清單

1. 數據持久化  
2. 定時任務  
3. 消息過濾  
4. 多平台適配  
5. 消息發送進階（重試/超時/批量）  
6. 權限控制  
7. 消息統計  
8. 搜索功能  
9. 圖片處理

## 數據持久化

### 簡單計數器

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command

@command("count", help="查看命令呼叫次數")
async def count_handler(event):
    # 獲取計數
    count = sdk.storage.get("command_count", 0)
    
    # 增加計數
    count += 1
    sdk.storage.set("command_count", count)
    
    await event.reply(f"這是第 {count} 次呼叫此命令")
```

### 用戶數據存儲

```python
@command("profile", help="查看個人資料")
async def profile_handler(event):
    user_id = event.get_user_id()
    
    # 獲取用戶數據
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
    
    # 更新用戶數據
    user_data = sdk.storage.get(f"user:{user_id}", {})
    user_data["nickname"] = " ".join(args)
    sdk.storage.set(f"user:{user_id}", user_data)
    
    await event.reply(f"暱稱已設定為: {' '.join(args)}")
```

## 定時任務

### 簡單定時器

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
        
        @command("timer", help="定時器管理")
        async def timer_handler(event):
            await event.reply("定時器正在運行中...")
    
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
    
    # 啟動後台任務
    asyncio.create_task(daily_reminder())
```

## 消息過濾

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
# 從配置或儲存加載黑名單
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
@command("help", help="顯示幫助")
async def help_handler(event):
    platform = event.get_platform()
    
    if platform == "yunhu":
        await event.reply("雲湖平台幫助...")
    elif platform == "telegram":
        await event.reply("Telegram platform help...")
    elif platform == "onebot11":
        await event.reply("OneBot11 help...")
    else:
        await event.reply("通用幫助資訊")
```

### 平台特性檢測

```python
@command("rich", help="發送富文本訊息")
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

## 消息發送進階（重試/超時/批量）

除了簡單的 `event.reply()`，你還可以透過適配器的 Send DSL 實現更複雜的發送場景：失敗自動重試、超時取消、成功後執行邏輯、批量發送多條消息。

> 下面的示例用 `event.get_detail_type()` 和 `event.get_target_id()` 從事件中獲取目標類型和 ID（群聊自動取 group_id，私聊自動取 user_id），避免硬編碼。

### 發送成功後執行邏輯

```python
@command("pay", help="模擬支付")
async def pay_handler(event):
    yunhu = sdk.adapter.get(event.get_platform())
    user_id = event.get_user_id()
    # 發送成功後才扣積分
    await (yunhu.Send.To(event.get_detail_type(), event.get_target_id())
           .Hook(lambda r: sdk.storage.set(f"points:{user_id}", -10))
           .Text("支付成功，已扣除 10 積分"))
```

### 失敗重試 + 超時取消

```python
@command("notice", help="發送重要通知")
async def notice_handler(event):
    adapter_inst = sdk.adapter.get(event.get_platform())
    # 最多重試 3 次，每次超時 10 秒
    task = (adapter_inst.Send.To(event.get_detail_type(), event.get_target_id())
            .Retry(3)
            .Timeout(10)
            .OnError(lambda ctx: sdk.logger.error(f"通知發送失敗: {ctx.error}"))
            .Text("這是一條重要通知"))
    # 不等待，後台發送
```

### 批量發送多條消息

一條鏈路發多條消息，統一執行：

```python
@command("announce", help="發送公告")
async def announce_handler(event):
    adapter_inst = sdk.adapter.get(event.get_platform())
    # 建構多條消息，統一發送（預設並行）
    results = await (adapter_inst.Send.To(event.get_detail_type(), event.get_target_id())
                    .Build()
                    .Text("📋 今日公告")
                    .Image("https://example.com/banner.jpg")
                    .Text("詳細內容見上方圖片")
                    .Retry(2)            # 失敗的條目各自重試
                    .send_all())
    sdk.logger.info(f"批量發送完成，共 {len(results)} 條")
```

> 更完整的規則與批量說明請參考 [平台特性指南](../platform-guide/README.md#發送規則裝飾器)。

## 權限控制

### 管理員檢查

```python
# 配置主人列表
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
        await event.reply("用法: /addmaster <用戶ID>")
        return
    
    new_master = args[0]
    MASTERS.append(new_master)
    await event.reply(f"已新增框架主人: {new_master}")
```

### 群組權限

```python
@command("groupinfo", help="查看群組資訊")
async def groupinfo_handler(event):
    if not event.is_group_message():
        await event.reply("此命令僅限群聊使用")
        return
    
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    
    await event.reply(f"群組 ID: {group_id}, 你的 ID: {user_id}")
```

## 消息統計

### 消息計數

> **注意**：以下示例使用 `sdk.storage.get/set` 進行簡單計數。在高併發場景下，建議使用 `sdk.storage.transaction()` 以保證原子性。

```python
@message.on_message()
async def count_handler(event):
    # 獲取統計
    stats = sdk.storage.get("message_stats", {
        "total": 0,
        "by_user": {},
        "by_day": {}
    })
    
    # 更新統計
    stats["total"] += 1
    
    user_id = event.get_user_id()
    stats["by_user"][user_id] = stats["by_user"].get(user_id, 0) + 1
    
    # 保存
    sdk.storage.set("message_stats", stats)

@command("stats", help="查看消息統計")
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
        f"{uid}: {count} 條消息" for uid, count in top_users
    )
    
    await event.reply(f"總消息數: {stats['total']}\n\n活躍用戶:\n{top_text}")
```

## 搜尋功能

### 簡單搜尋

> **注意**：以下示例使用記憶體列表儲存訊息歷史，**程式重啟後資料會遺失**。生產環境建議使用 `sdk.storage` 或 SQLite 表進行持久化儲存。

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
        await event.reply("未找到匹配的訊息")
        return
    
    # 顯示結果
    result_text = f"找到 {len(results)} 條匹配訊息:\n\n"
    for i, msg in enumerate(results[:10], 1):  # 最多顯示 10 條
        result_text += f"{i}. {msg['text']}\n"
    
    await event.reply(result_text)
```

## 圖片處理

### 圖片下載和存儲

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
                # 推薦使用 SDK 內建客戶端下載圖片
                resp = await client.get(file_url)
                if resp.status == 200:
                    image_data = await resp.read()
                    
                    # 存儲到檔案
                    filename = f"images/{event.get_time()}.jpg"
                    with open(filename, "wb") as f:
                        f.write(image_data)
                    
                    sdk.logger.info(f"圖片已儲存: {filename}")
                    await event.reply("圖片已儲存")
```

### 圖片識別範例

> **注意**：以下範例使用佔位 API 地址，實際使用時請替換為你自己的圖片識別服務。

```python
from ErisPulse.Core import client

@command("identify", help="識別圖片")
async def identify_handler(event):
    """識別訊息中的圖片"""
    message_segments = event.get_message()
    
    for segment in message_segments:
        if segment.get("type") == "image":
            file_url = segment.get("data", {}).get("file")
            
            # 調用圖片識別 API
            result = await _identify_image(file_url)
            
            await event.reply(f"識別結果: {result}")
            return
    
    await event.reply("未找到圖片")

async def _identify_image(url):
    """調用圖片識別 API（範例）- 使用 SDK 內建客戶端"""
    resp = await client.post(
        "https://api.example.com/identify",
        json={"url": url}
    )
    data = await resp.json()
    return data.get("description", "識別失敗")
```

## 下一步

- [使用者指南](../user-guide/) - 了解設定和模組管理
- [開發者指南](../developer-guide/) - 學習開發模組和適配器
- [進階主題](../advanced/) - 深入了解框架特性