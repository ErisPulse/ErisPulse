# 常見任務範例

本指南提供常見功能的實作範例，協助您快速實作常用功能。

## 內容列表

1. 資料持久化
2. 定時任務
3. 訊息過濾
4. 多平台適配
5. 權限控制
6. 訊息統計
7. 搜尋功能
8. 圖片處理

## 資料持久化

### 簡單計數器

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command

@command("count", help="查看指令呼叫次數")
async def count_handler(event):
    # 取得計數
    count = sdk.storage.get("command_count", 0)
    
    # 增加計數
    count += 1
    sdk.storage.set("command_count", count)
    
    await event.reply(f"這是第 {count} 次呼叫此指令")
```

### 使用者資料儲存

```python
@command("profile", help="查看個人資料")
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
            await event.reply("定時器正在運作中...")
    
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
        # 您的邏輯...
    
    async def _daily_task(self):
        """每天凌晨執行的任務"""
        import time
        
        while True:
            # 計算到凌晨的時間
            now = time.time()
            midnight = now + (86400 - now % 86400)
            
            await asyncio.sleep(midnight - now)
            
            # 執行任務
            self.sdk.logger.info("每日任務執行")
            # 您的邏輯...
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
        self.sdk.logger.info("執行每日任務")
    
    # 啟動背景任務
    asyncio.create_task(daily_reminder())
```

## 訊息過濾

### 關鍵詞過濾

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
    await event.reply(f"您好，{user_id}")
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
        await event.reply("通用說明資訊")
```

### 平台特性檢測

```python
@command("rich", help="傳送富文本訊息")
async def rich_handler(event):
    platform = event.get_platform()
    
    if platform == "yunhu":
        # 雲湖支援 HTML
        yunhu = sdk.adapter.get("yunhu")
        await yunhu.Send.To("user", event.get_user_id()).Html(
            "<b>粗體文字</b><i>斜體文字</i>"
        )
    elif platform == "telegram":
        # Telegram 支援 Markdown
        telegram = sdk.adapter.get("telegram")
        await telegram.Send.To("user", event.get_user_id()).Markdown(
            "**粗體文字** *斜體文字*"
        )
    else:
        # 其他平台使用純文字
        await event.reply("粗體文字 斜體文字")
```

## 權限控制

### 管理員檢查

```python
# 設定管理員清單
ADMINS = ["user123", "user456"]

def is_admin(user_id):
    """檢查是否為管理員"""
    return user_id in ADMINS

@command("admin", help="管理員指令")
async def admin_handler(event):
    user_id = event.get_user_id()
    
    if not is_admin(user_id):
        await event.reply("權限不足，此指令僅限管理員使用")
        return
    
    await event.reply("管理員指令執行成功")

@command("addadmin", help="新增管理員")
async def addadmin_handler(event):
    if not is_admin(event.get_user_id()):
        return
    
    args = event.get_command_args()
    if not args:
        await event.reply("請輸入要新增的管理員 ID")
        return
    
    new_admin = args[0]
    ADMINS.append(new_admin)
    await event.reply(f"已新增管理員: {new_admin}")
```

### 群組權限

```python
@command("groupinfo", help="檢視群組資訊")
async def groupinfo_handler(event):
    if not event.is_group_message():
        await event.reply("此指令僅限群組使用")
        return
    
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    
    await event.reply(f"群組 ID: {group_id}, 您的 ID: {user_id}")
```

## 訊息統計

### 訊息計數

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
        f"{uid}: {count} 則訊息" for uid, count in top_users
    )
    
    await event.reply(f"總訊息數: {stats['total']}\n\n活躍使用者:\n{top_text}")
```

## 搜尋功能

### 簡單搜尋

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
        await event.reply("請輸入搜尋關鍵詞")
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
    result_text = f"找到 {len(results)} 則符合訊息:\n\n"
    for i, msg in enumerate(results[:10], 1):  # 最多顯示 10 則
        result_text += f"{i}. {msg['text']}\n"
    
    await event.reply(result_text)
```

## 圖片處理

### 圖片下載與儲存

```python
@message.on_message()
async def image_handler(event):
    """處理圖片訊息"""
    message_segments = event.get_message()
    
    for segment in message_segments:
        if segment.get("type") == "image":
            file_url = segment.get("data", {}).get("file")
            
            if file_url:
                # 下載圖片
                import aiohttp
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(file_url) as response:
                        if response.status == 200:
                            image_data = await response.read()
                            
                            # 儲存至檔案
                            filename = f"images/{event.get_time()}.jpg"
                            with open(filename, "wb") as f:
                                f.write(image_data)
                            
                            sdk.logger.info(f"圖片已儲存: {filename}")
                            await event.reply("圖片已儲存")
```

### 圖片辨識範例

```python
@command("identify", help="辨識圖片")
async def identify_handler(event):
    """辨識訊息中的圖片"""
    message_segments = event.get_message()
    
    for segment in message_segments:
        if segment.get("type") == "image":
            file_url = segment.get("data", {}).get("file")
            
            # 呼叫圖片辨識 API
            result = await _identify_image(file_url)
            
            await event.reply(f"辨識結果: {result}")
            return
    
    await event.reply("未找到圖片")

async def _identify_image(url):
    """呼叫圖片辨識 API（範例）"""
    import aiohttp
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.example.com/identify",
            json={"url": url}
        ) as response:
            data = await response.json()
            return data.get("description", "辨識失敗")
```

## 下一步

- [使用者使用指南](../user-guide/) - 了解設定與模組管理
- [開發者指南](../developer-guide/) - 學習開發模組與介面卡
- [進階主題](../advanced/) - 深入了解框架特性