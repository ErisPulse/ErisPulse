你是一个 ErisPulse 适配器开发专家，精通以下领域：

- 异步网络编程 (asyncio, aiohttp)
- WebSocket 和 WebHook 连接管理
- OneBot12 事件转换标准
- 平台 API 集成和适配
- SendDSL 链式消息发送系统
- 事件转换器 (Converter) 设计
- API 响应标准化

你擅长：
- 将平台原生事件转换为 OneBot12 标准格式
- 实现可靠的网络连接和重试机制
- 设计优雅的链式调用 API
- 遵循 ErisPulse 适配器开发规范
- 处理多账户和配置管理

**使用以下文档作为知识库，回答问题时请优先参考文档内容。**



---



=================
ErisPulse 适配器开发指南
=================




====
快速开始
====

# 入門指南

歡迎來到 ErisPulse 入門指南。如果你是第一次使用 ErisPulse，這裡將帶你從零開始，逐步了解框架的核心概念和基本用法。

## 學習路徑

本指南按以下順序組織，建議依次閱讀：

1. **建立第一個機器人** - 了解完整的專案初始化流程
2. **基礎概念** - 理解 ErisPulse 的核心架構
3. **事件處理入門** - 學習如何處理各類事件
4. **常見任務範例** - 掌握常用功能的實作

## 開發方式選擇

ErisPulse 支援兩種開發方式，你可以根據需求選擇：

### 嵌入式開發（適合快速原型）

直接在專案中使用 ErisPulse，無需建立獨立模組。

```python
# main.py
import asyncio
from ErisPulse import sdk
from ErisPulse.Core.Event import command

@command("hello")
async def hello(event):
    await event.reply("你好！")

# 執行 SDK 並且維持運作 | 需要在非同步環境中運作
asyncio.run(sdk.run(keep_running=True))
```

**優點：**
- 快速上手，無需額外配置
- 適合專案內部專用功能
- 便於除錯和測試

**缺點：**
- 不便於程式碼複用和分發
- 難以獨立管理依賴

### 模組開發（推薦用於生產）

建立獨立的模組套件，透過套件管理員安裝使用。

**優點：**
- 便於分發和共享
- 獨立的依賴管理
- 清晰的版本控制

**缺點：**
- 需要額外的專案結構
- 初期設定相對複雜

## ErisPulse 核心概念

### 架構概覽

```
┌─────────────────────────────────────────────────────┐
│                ErisPulse 框架                 │
├─────────────────────────────────────────────────────┤
│                                             │
│  ┌──────────────┐      ┌──────────────┐    │
│  │  適配器系統  │◄────►│  事件系統    │    │
│  │             │      │              │    │
│  │  Yunhu      │      │  Message     │    │
│  │  Telegram   │      │  Command     │    │
│  │  OneBot11   │      │  Notice      │    │
│  │  Email      │      │  Request     │    │
│  └──────────────┘      │  Meta        │    │
│         │              └──────────────┘    │
│         ▼                   │              │
│  ┌──────────────┐           ▼              │
│  │  模組系統    │◄──────────────┐       │
│  │             │               │       │
│  │  模組 A     │               │       │
│  │  模組 B     │               │       │
│  │  ...        │               │       │
│  └──────────────┘               │       │
│                               │       │
│  ┌──────────────┐              │       │
│  │  核心模組    │◄─────────────┘       │
│  │  Storage    │                      │
│  │  Config     │                      │
│  │  Logger     │                      │
│  │  Router     │                      │
│  └──────────────┘                      │
└─────────────────────────────────────────────┘
         │                    │
         ▼                    ▼
    ┌────────┐          ┌────────┐
    │  平台   │          │ 使用者  │
    │  API    │          │ 程式碼  │
    └────────┘          └────────┘
```

### 核心元件說明

#### 1. 適配器系統

適配器負責與特定平台通訊，將平台特定的事件轉換為統一的 OneBot12 標準格式。

**範例：**
- Yunhu 適配器：與雲湖平台通訊
- Telegram 適配器：與 Telegram Bot API 通訊
- OneBot11 適配器：與 OneBot11 相容的應用程式通訊

#### 2. 事件系統

事件系統負責處理各類事件，包括：
- **訊息事件**：使用者發送的訊息
- **指令事件**：使用者輸入的指令（如 `/hello`）
- **通知事件**：系統通知（如好友新增、群組成員變化）
- **請求事件**：使用者請求（如好友請求、群組邀請）
- **元事件**：系統層級事件（如連線、心跳）

#### 3. 模組系統

模組是功能擴充的主要方式，用於：
- 註冊事件處理器
- 實作業務邏輯
- 提供指令介面
- 呼叫適配器發送訊息

#### 4. 核心模組

提供基礎功能的模組：
- **Storage**：基於 SQLite 的鍵值儲存
- **Config**：TOML 格式的設定管理
- **Logger**：模組化日誌系統
- **Router**：HTTP 和 WebSocket 路由管理

## 開始學習

準備好了嗎？讓我們開始建立你的第一個機器人。

- [建立第一個機器人](first-bot.md)



====
基础概念
====

# 基礎概念

本指南介紹 ErisPulse 的核心概念，幫助你理解框架的設計思想和基本架構。

## 事件驅動架構

ErisPulse 採用事件驅動架構，所有的交互都通過事件來傳遞和處理。

### 事件流程

```
用戶發送訊息
      │
      ▼
平台接收
      │
      ▼
適配器接收平台原生事件
      │
      ▼
轉換為 OneBot12 標準事件
      │
      ▼
提交到事件系統
      │
      ▼
分發給已註冊的處理器
      │
      ▼
模組處理事件
      │
      ▼
通過適配器發送響應
      │
      ▼
平台顯示給用戶
```

### OneBot12 標準

ErisPulse 使用 OneBot12 作為核心事件標準。OneBot12 是一個通用的聊天機器人應用介面標準，定義了統一的事件格式。

所有適配器都將平台特定的事件轉換為 OneBot12 格式，確保代碼的一致性。

## 核心組件

### 1. SDK 對象

SDK 是所有功能的統一入口點，提供對核心組件的訪問。

```python
from ErisPulse import sdk

# 訪問核心模組
sdk.storage    # 存儲系統
sdk.config     # 配置系統
sdk.logger     # 日



======
事件处理入门
======

# 事件處理入門

本指南介紹如何處理 ErisPulse 中的各類事件。

## 事件類型概覽

ErisPulse 支援以下事件類型：

| 事件類型 | 說明 | 適用場景 |
|---------|------|---------|
| 訊息事件 | 使用者發送的任何訊息 | 聊天機器人、內容過濾 |
| 命令事件 | 以命令前綴開頭的訊息 | 命令處理、功能入口 |
| 通知事件 | 系統通知（好友新增、群組成員變化等） | 歡迎訊息、狀態通知 |
| 請求事件 | 使用者請求（好友請求、群組邀請） | 自動處理請求 |
| 元事件 | 系統級事件（連線、心跳） | 連線監控、狀態檢查 |

## 訊息事件處理

### 監聽所有訊息

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def message_handler(event):
    text = event.get_text()
    user_id = event.get_user_id()
    sdk.logger.info(f"收到 {user_id} 的訊息: {text}")
```

### 監聽私聊訊息

```python
@message.on_private_message()
async def private_handler(event):
    user_id = event.get_user_id()
    await event.reply(f"你好，{user_id}！這是私聊訊息。")
```

### 監聽群聊訊息

```python
@message.on_group_message()
async def group_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    sdk.logger.info(f"群組 {group_id} 中 {user_id} 發送了訊息")
```

### 監聽@訊息

```python
@message.on_at_message()
async def at_handler(event):
    # 取得被@的使用者列表
    mentions = event.get_mentions()
    await event.reply(f"你@了這些使用者: {mentions}")
```

## 命令事件處理

### 基本命令

```python
from ErisPulse.Core.Event import command

@command("help", help="顯示幫助資訊")
async def help_handler(event):
    help_text = """
可用命令：
/help - 顯示幫助
/ping - 測試連線
/info - 查看資訊
    """
    await event.reply(help_text)
```

### 命令別名

```python
@command(["help", "h"], aliases=["幫助"], help="顯示幫助資訊")
async def help_handler(event):
    await event.reply("幫助資訊...")
```

使用者可以使用以下任何方式呼叫：
- `/help`
- `/h`
- `/幫助`

### 命令參數

```python
@command("echo", help="回顯訊息")
async def echo_handler(event):
    # 取得命令參數
    args = event.get_command_args()
    
    if not args:
        await event.reply("請輸入要回顯的訊息")
    else:
        await event.reply(f"你說了: {' '.join(args)}")
```

### 命令組

```python
@command("admin.reload", group="admin", help="重新載入模組")
async def reload_handler(event):
    await event.reply("模組已重新載入")

@command("admin.stop", group="admin", help="停止機器人")
async def stop_handler(event):
    await event.reply("機器人已停止")
```

### 命令權限

```python
def is_admin(event):
    """檢查使用者是否為管理員"""
    admin_list = ["user123", "user456"]
    return event.get_user_id() in admin_list

@command("admin", permission=is_admin, help="管理員命令")
async def admin_handler(event):
    await event.reply("這是管理員命令")
```

### 命令優先級

```python
# 優先級數值越小，執行越早
@message.on_message(priority=10)
async def high_priority_handler(event):
    await event.reply("高優先級處理器")

@message.on_message(priority=1)
async def low_priority_handler(event):
    await event.reply("低優先級處理器")
```

## 通知事件處理

### 好友新增

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event):
    user_id = event.get_user_id()
    nickname = event.get_user_nickname() or "新朋友"
    await event.reply(f"歡迎新增我為好友，{nickname}！")
```

### 群組成員增加

```python
@notice.on_group_increase()
async def member_increase_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"歡迎新成員 {user_id} 加入群組 {group_id}")
```

### 群組成員減少

```python
@notice.on_group_decrease()
async def member_decrease_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"成員 {user_id} 離開了群組 {group_id}")
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
    # 具體實作請參考各適配器文件
```

### 群組邀請請求

```python
@request.on_group_request()
async def group_request_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    
    await event.reply(f"收到群組 {group_id} 的邀請，來自 {user_id}")
```

## 元事件處理

### 連線事件

```python
from ErisPulse.Core.Event import meta

@meta.on_connect()
async def connect_handler(event):
    platform = event.get_platform()
    sdk.logger.info(f"{platform} 平台已連線")

@meta.on_disconnect()
async def disconnect_handler(event):
    platform = event.get_platform()
    sdk.logger.warning(f"{platform} 平台已斷線")
```

### 心跳事件

```python
@meta.on_heartbeat()
async def heartbeat_handler(event):
    platform = event.get_platform()
    sdk.logger.debug(f"{platform} 心跳檢測")
```

## 互動式處理

### 使用 reply 方法發送回覆

`event.reply()` 方法支援多種修飾參數，方便發送帶有 @、回覆等功能的訊息：

```python
# 簡單回覆
await event.reply("你好")

# 發送不同類型的訊息
await event.reply("http://example.com/image.jpg", method="Image")  # 圖片
await event.reply("http://example.com/voice.mp3", method="Voice")  # 語音

# @單個使用者
await event.reply("你好", at_users=["user123"])

# @多個使用者
await event.reply("大家好", at_users=["user1", "user2", "user3"])

# 回覆訊息
await event.reply("回覆內容", reply_to="msg_id")

# @全體成員
await event.reply("公告", at_all=True)

# 組合使用：@使用者 + 回覆訊息
await event.reply("內容", at_users=["user1"], reply_to="msg_id")
```

### 等待使用者回覆

```python
@command("ask", help="詢問使用者")
async def ask_handler(event):
    await event.reply("請輸入你的名字:")
    
    # 等待使用者回覆，逾時時間 30 秒
    reply = await event.wait_reply(timeout=30)
    
    if reply:
        name = reply.get_text()
        await event.reply(f"你好，{name}！")
    else:
        await event.reply("等待逾時，請重新輸入。")
```

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
        await event.reply("輸入無效或逾時")
```

### 帶回呼的等待回覆

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

## 事件資料存取

### Event 物件常用方法

```python
@command("info")
async def info_handler(event):
    # 基礎資訊
    event_id = event.get_id()
    event_time = event.get_time()
    event_type = event.get_type()
    detail_type = event.get_detail_type()
    
    # 發送者資訊
    user_id = event.get_user_id()
    nickname = event.get_user_nickname()
    
    # 訊息內容
    message_segments = event.get_message()
    alt_message = event.get_alt_message()
    text = event.get_text()
    
    # 群組資訊
    group_id = event.get_group_id()
    
    # 機器人資訊
    self_id = event.get_self_user_id()
    self_platform = event.get_self_platform()
    
    # 原始資料
    raw_data = event.get_raw()
    raw_type = event.get_raw_type()
    
    # 平台資訊
    platform = event.get_platform()
    
    # 訊息類型判斷
    is_private = event.is_private_message()
    is_group = event.is_group_message()
    is_at = event.is_at_message()
    
    # 命令資訊
    if event.is_command():
        cmd_name = event.get_command_name()
        cmd_args = event.get_command_args()
        cmd_raw = event.get_command_raw()
```

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
    logger.debug(f"詳細除錯資訊")
```

### 3. 條件處理

```python
def should_handle(event):
    """判斷是否應該處理此事件"""
    # 只處理特定使用者的訊息
    if event.get_user_id() in ["bot1", "bot2"]:
        return False
    
    # 只處理包含特定關鍵字的訊息
    if "關鍵字" not in event.get_text():
        return False
    
    return True

@message.on_message(condition=should_handle)
async def conditional_handler(event):
    await event.reply("條件滿足，處理訊息")
```

## 下一步

- [常見任務範例](common-tasks.md) - 學習常用功能的實作
- [Event 包裝類詳解](../developer-guide/modules/event-wrapper.md) - 深入了解 Event 物件
- [使用者使用指南](../user-guide/) - 了解配置和模組管理



=====
适配器开发
=====


### 适配器开发入门

# 適配器開發入門

本指南協助您開始開發 ErisPulse 適配器，以連接新的訊息平台。

## 適配器簡介

### 什麼是適配器

適配器是 ErisPulse 與各個訊息平台之間的橋樑，負責：

1. 接收平台事件並轉換為 OneBot12 標準格式
2. 將 OneBot12 標準回應轉換為平台特定格式
3. 管理與平台的連線
4. 提供統一的 SendDSL 訊息發送介面

### 適配器架構

```
平台事件
    ↓
轉換器 (Converter)
    ↓
OneBot12 標準事件
    ↓
事件系統
    ↓
模組處理
    ↓
SendDSL 訊息發送
    ↓
平台 API 呼叫
```

## 目錄結構

標準的適配器套件結構：

```
MyAdapter/
├── pyproject.toml          # 專案配置
├── README.md               # 專案說明
├── LICENSE                 # 許可證
└── MyAdapter/
    ├── __init__.py          # 套件入口
    ├── Core.py               # 適配器主類別
    └── Converter.py          # 事件轉換器
```

## 快速開始

### 1. 建立專案

```bash
mkdir MyAdapter && cd MyAdapter
```

### 2. 建立 pyproject.toml

```toml
[project]
name = "ErisPulse-MyAdapter"
version = "1.0.0"
description = "MyAdapter平台適配器"
readme = "README.md"
requires-python = ">=3.9"
license = { file = "LICENSE" }
authors = [ { name = "yourname", email = "your@mail.com" } ]

dependencies = [
    "aiohttp>=3.8.0"
]

[project.urls]
"homepage" = "https://github.com/yourname/MyAdapter"

[project.entry-points."erispulse.adapter"]
"MyAdapter" = "MyAdapter:MyAdapter"
```

### 3. 建立適配器主類別

```python
# MyAdapter/Core.py
from ErisPulse import sdk
from ErisPulse.Core import BaseAdapter
from ErisPulse.Core import router, logger, config as config_manager, adapter

class MyAdapter(BaseAdapter):
    def __init__(self, sdk):
        self.sdk = sdk
        self.logger = logger.get_child("MyAdapter")
        self.config_manager = config_manager
        self.adapter = adapter
        
        self.config = self._get_config()
        self.converter = self._setup_converter()
        self.convert = self.converter.convert
        
        self.logger.info("MyAdapter 初始化完成")
    
    def _setup_converter(self):
        from .Converter import MyPlatformConverter
        return MyPlatformConverter()
    
    def _get_config(self):
        config = self.config_manager.getConfig("MyAdapter", {})
        if config is None:
            default_config = {
                "api_endpoint": "https://api.example.com",
                "timeout": 30
            }
            self.config_manager.setConfig("MyAdapter", default_config)
            return default_config
        return config
```

### 4. 實作必要方法

```python
class MyAdapter(BaseAdapter):
    # ... __init__ 程式碼 ...
    
    async def start(self):
        """啟動適配器（必須實作）"""
        # 註冊 WebSocket 或 WebHook 路由
        router.register_websocket(
            module_name="myplatform",
            path="/ws",
            handler=self._ws_handler
        )
        self.logger.info("適配器已啟動")
    
    async def shutdown(self):
        """關閉適配器（必須實作）"""
        router.unregister_websocket(
            module_name="myplatform",
            path="/ws"
        )
        # 清理連線和資源
        self.logger.info("適配器已關閉")
    
    async def call_api(self, endpoint: str, **params):
        """呼叫平台 API（必須實作）"""
        raise NotImplementedError("需要實作 call_api")
```

### 5. 實作 Send 類別

```python
import asyncio

class MyAdapter(BaseAdapter):
    # ... 其他程式碼 ...
    
    class Send(BaseAdapter.Send):
        # 方法名稱映射表（小寫 -> 實際方法名稱）
        _METHOD_MAP = {
            "text": "Text",
            "image": "Image",
            "video": "Video",
            # ... 其他方法
        }
        
        def __getattr__(self, name):
            """
            支援大小寫不敏感呼叫，未定義方法返回文字提示
            """
            name_lower = name.lower()
            if name_lower in self._METHOD_MAP:
                return getattr(self, self._METHOD_MAP[name_lower])
            
            def unsupported(*args, **kwargs):
                return self.Text(f"[不支援的發送類型] {name}")
            return unsupported
        
        def Text(self, text: str):
            """發送文字訊息"""
            return asyncio.create_task(
                self._adapter.call_api(
                    endpoint="/send",
                    content=text,
                    recvId=self._target_id,
                    recvType=self._target_type
                )
            )
        
        def Image(self, file):
            """發送圖片訊息"""
            # 實作見下方說明
            pass
        
        def Raw_ob12(self, message, **kwargs):
            """
            發送 OneBot12 格式訊息
            """
            if isinstance(message, dict):
                message = [message]
            
            async def _send():
                for segment in message:
                    seg_type = segment.get("type", "")
                    seg_data = segment.get("data", {})
                    
                    if seg_type == "text":
                        await self.Text(seg_data.get("text", ""))
                    elif seg_type == "image":
                        await self.Image(seg_data.get("file") or seg_data.get("url", ""))
                    # ... 處理其他訊息類型
            
            return asyncio.create_task(_send())
```

**媒體類發送方法實作要點：**

- `file` 參數應同時支援 `bytes` 二進位資料和 `str` URL 兩種類型
- 當傳入 URL 時，需先下載檔案再上傳到平台
- 平台通常需要先呼叫上傳介面取得檔案識別碼，再呼叫發送介面

**`__getattr__` 魔術方法：**

- 實作方法名稱大小寫不敏感（`Text`、`text`、`TEXT` 都能呼叫）
- 未定義的方法應返回提示資訊而非報錯

**`Raw_ob12` 方法：**

- 將 OneBot12 標準訊息格式轉換為平台格式發送
- 處理訊息段陣列，根據 `type` 欄位分發到對應的發送方法

### 6. 實作轉換器

```python
# MyAdapter/Converter.py
import time
import uuid

class MyPlatformConverter:
    def convert(self, raw_event):
        """將平台原生事件轉換為 OneBot12 標準格式"""
        if not isinstance(raw_event, dict):
            return None
        
        onebot_event = {
            "id": str(raw_event.get("event_id", uuid.uuid4())),
            "time": int(time.time()),
            "type": self._convert_event_type(raw_event.get("type")),
            "detail_type": self._convert_detail_type(raw_event),
            "platform": "myplatform",
            "self": {
                "platform": "myplatform",
                "user_id": str(raw_event.get("bot_id", ""))
            },
            "myplatform_raw": raw_event,
            "myplatform_raw_type": raw_event.get("type", "")
        }
        
        return onebot_event
    
    def _convert_event_type(self, event_type):
        """轉換事件類型"""
        type_map = {
            "message": "message",
            "notice": "notice"
        }
        return type_map.get(event_type, "unknown")
    
    def _convert_detail_type(self, raw_event):
        """轉換詳細類型"""
        return "private"  # 簡化範例
```

### 7. 建立套件入口

```python
# MyAdapter/__init__.py
from .Core import MyAdapter
```

## 下一步

- [適配器核心概念](core-concepts.md) - 了解適配器架構
- [SendDSL 詳解](send-dsl.md) - 學習訊息發送
- [轉換器實作](converter.md) - 了解事件轉換
- [適配器最佳實踐](best-practices.md) - 開發高品質適配器



### 适配器核心概念

# 介接器核心概念

了解 ErisPulse 介接器的核心概念是開發介接器的基礎。

## 介接器架構

### 組件關係

```
┌─────────────────────────────────────────┐
│         平台 API                │
└────────────┬────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────┐
│      介接器           │
│  ┌────────────────────────────┐    │
│  │ Send 類 (訊息發送 DSL)    │    │
│  └────────────────────────────┘    │
│  ┌────────────────────────────┐    │
│  │ Converter (事件轉換器)     │    │
│  └────────────────────────────┘    │
└────────────┬────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────┐
│     OneBot12 標準事件           │
└────────────┬────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────┐
│      事件系統                   │
└────────────┬────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────┐
│      模組 (處理事件)            │
└─────────────────────────────────────────┘
```

## AdapterManager 介接器管理器

`AdapterManager` 是 ErisPulse 介接器系統的核心組件，負責管理所有平台介接器的註冊、啟動、關閉和事件分發。

### 核心功能

- **介接器註冊**：註冊和管理多個平台介接器
- **生命週期管理**：控制介接器的啟動和關閉
- **事件分發**：分發 OneBot12 標準事件和平台原生事件
- **設定管理**：管理介接器的啟用/停用狀態
- **中介軟體支援**：支援 OneBot12 事件中介軟體

### 基本使用

```python
from ErisPulse import sdk

# 註冊介接器（通常由 Loader 自動完成）
sdk.adapter.register("myplatform", MyPlatformAdapter)

# 啟動所有介接器
await sdk.adapter.startup()

# 啟動指定介接器
await sdk.adapter.startup(["myplatform"])
# 啟動全部介接器
await sdk.adapter.startup()

# 取得介接器實例
my_adapter = sdk.adapter.get("myplatform")
# 或透過屬性存取
my_adapter = sdk.adapter.myplatform

# 關閉所有介接器
await sdk.adapter.shutdown()
```

### 啟動和關閉

#### 啟動介接器

```python
# 啟動所有已註冊的介接器
await sdk.adapter.startup()

# 啟動指定平台
await sdk.adapter.startup(["platform1", "platform2"])
```

**啟動流程：**

1. 提交 `adapter.start` 生命週期事件
2. 提交 `adapter.status.change` 事件（starting）
3. 並行啟動各個介接器
4. 如果啟動失敗，自動重試（指數退避策略）
5. 啟動成功後提交 `adapter.status.change` 事件（started）

**重試機制：**

- 前 4 次重試：60秒、10分鐘、30分鐘、60分鐘
- 第 5 次及以後：3 小時固定間隔

#### 關閉介接器

```python
# 關閉所有介接器
await sdk.adapter.shutdown()
```

**關閉流程：**

1. 提交 `adapter.stop` 生命週期事件
2. 呼叫所有介接器的 `shutdown()` 方法
3. 關閉路由伺服器
4. 清空事件處理器
5. 提交 `adapter.stopped` 生命週期事件

### 設定管理

#### 檢查平台狀態

```python
# 檢查平台是否已註冊
exists = sdk.adapter.exists("myplatform")

# 檢查平台是否啟用
enabled = sdk.adapter.is_enabled("myplatform")

# 使用 in 運算子
if "myplatform" in sdk.adapter:
    print("平台存在且已啟用")
```

#### 列出平台

```python
# 列出所有已註冊的平台
platforms = sdk.adapter.list_registered()

# 列出所有平台及其狀態
status_dict = sdk.adapter.list_items()
# 傳回: {"platform1": true, "platform2": false, ...}

# 取得已啟用的平台列表
enabled_platforms = [p for p, enabled in status_dict.items() if enabled]
```

### 事件監聽

#### OneBot12 標準事件

```python
from ErisPulse import sdk

# 監聽所有平台的標準訊息事件
@sdk.adapter.on("message")
async def handle_message(data):
    print(f"收到 OneBot12 訊息: {data}")

# 監聽特定平台的標準訊息事件
@sdk.adapter.on("message", platform="myplatform")
async def handle_platform_message(data):
    print(f"收到 myplatform 訊息: {data}")

# 監聽所有事件
@sdk.adapter.on("*")
async def handle_any_event(data):
    print(f"收到事件: {data.get('type')}")
```

#### 平台原生事件

```python
# 監聽特定平台的原生事件
@sdk.adapter.on("raw_event_type", raw=True, platform="myplatform")
async def handle_raw_event(data):
    print(f"收到原生事件: {data}")

# 監聽所有平台的原生事件（萬用字元）
@sdk.adapter.on("*", raw=True)
async def handle_all_raw_events(data):
    print(f"收到原生事件: {data}")
```

#### 事件分發機制

當呼叫 `adapter.emit(event_data)` 時：

1. **中介軟體處理**：先執行所有 OneBot12 中介軟體
2. **標準事件分發**：分發到匹配的 OneBot12 事件處理器
3. **原生事件分發**：如果存在原始資料，分發到原生事件處理器

**匹配規則：**

- 精確匹配：`@sdk.adapter.on("message")` 只匹配 `message` 事件
- 萬用字元：`@sdk.adapter.on("*")` 匹配所有事件
- 平台過濾：`platform="myplatform"` 只分發指定平台的事件

### 中介軟體

#### 新增中介軟體

```python
@sdk.adapter.middleware
async def logging_middleware(data):
    """日誌記錄中介軟體"""
    print(f"處理事件: {data.get('type')}")
    return data  # 必須傳回資料

@sdk.adapter.middleware
async def filter_middleware(data):
    """事件過濾中介軟體"""
    # 過濾不需要的事件
    if data.get("type") == "notice":
        return None  # 傳回 None 會阻止事件繼續分發
    return data
```

#### 中介軟體執行順序

中介軟體按照註冊順序執行，後註冊的中介軟體先執行。

```python
# 註冊順序
sdk.adapter.middleware(middleware1)  # 最後執行
sdk.adapter.middleware(middleware2)  # 中間執行
sdk.adapter.middleware(middleware3)  # 最先執行

# 執行順序：middleware3 -> middleware2 -> middleware1
```

### 取得介接器實例

#### get() 方法

```python
adapter = sdk.adapter.get("myplatform")
if adapter:
    await adapter.Send.To("user", "123").Text("Hello")
```

#### 屬性存取

```python
# 透過屬性名稱存取（不區分大小寫）
adapter = sdk.adapter.myplatform
await adapter.Send.To("user", "123").Text("Hello")
```

## BaseAdapter 基類

### 基本結構

```python
from ErisPulse.Core import BaseAdapter

class MyAdapter(BaseAdapter):
    def __init__(self, sdk):
        # 初始化介接器
        pass
    
    async def start(self):
        """啟動介接器（必須實作）"""
        pass
    
    async def shutdown(self):
        """關閉介接器（必須實作）"""
        pass
    
    async def call_api(self, endpoint: str, **params):
        """呼叫平台 API（必須實作）"""
        pass
```

### 初始化過程

```python
class MyAdapter(BaseAdapter):
    def __init__(self, sdk):
        # 取得 SDK 引用
        self.sdk = sdk
        
        # 取得核心模組
        self.logger = logger.get_child("MyAdapter")
        self.config_manager = config_manager
        self.adapter = adapter
        
        # 載入設定
        self.config = self._get_config()
        
        # 設定轉換器
        self.converter = self._setup_converter()
        self.convert = self.converter.convert
```

## Send 訊息發送 DSL

### 繼承關係

```python
class MyAdapter(BaseAdapter):
    class Send(BaseAdapter.Send):
        """Send 巢狀類別，繼承自 BaseAdapter.Send"""
        pass
```

### 可用屬性

`Send` 類別在呼叫時會自動設定以下屬性：

| 屬性 | 說明 | 設定方式 |
|-----|------|---------|
| `_target_id` | 目標ID | `To(id)` 或 `To(type, id)` |
| `_target_type` | 目標類型 | `To(type, id)` |
| `_target_to` | 簡化目標ID | `To(id)` |
| `_account_id` | 發送帳號ID | `Using(account_id)` |
| `_adapter` | 介接器實例 | 自動設定 |

### 基本方法

```python
class Send(BaseAdapter.Send):
    def Text(self, text: str):
        """發送文字訊息（必須傳回 Task）"""
        import asyncio
        return asyncio.create_task(
            self._adapter.call_api(
                endpoint="/send",
                content=text,
                recvId=self._target_id,
                recvType=self._target_type
            )
        )
```

### 鏈式修飾方法

```python
class Send(BaseAdapter.Send):
    def __init__(self, adapter, target_type=None, target_id=None, account_id=None):
        super().__init__(adapter, target_type, target_id, account_id)
        self._at_user_ids = []
        self._reply_message_id = None
        self._at_all = False
    
    def At(self, user_id: str) -> 'Send':
        """@使用者（可多次呼叫）"""
        self._at_user_ids.append(user_id)
        return self
    
    def AtAll(self) -> 'Send':
        """@全體成員"""
        self._at_all = True
        return self
    
    def Reply(self, message_id: str) -> 'Send':
        """回覆訊息"""
        self._reply_message_id = message_id
        return self
```

## 事件轉換器

### 轉換流程

```
平台原始事件
    ↓
Converter.convert()
    ↓
OneBot12 標準事件
```

### 必要欄位

所有轉換後的事件必須包含：

```python
{
    "id": "事件唯一識別碼",
    "time": 1234567890,           # 10位 Unix 時間戳記
    "type": "message/notice/request/meta",
    "detail_type": "事件詳細類型",
    "platform": "平台名稱",
    "self": {
        "platform": "平台名稱",
        "user_id": "機器人 ID"
    },
    "{platform}_raw": {...},       # 原始資料（必須）
    "{platform}_raw_type": "..."    # 原始類型（必須）
}
```

### 轉換器範例

```python
class MyPlatformConverter:
    def convert(self, raw_event):
        """將平台原生事件轉換為 OneBot12 標準格式"""
        if not isinstance(raw_event, dict):
            return None
        
        # 產生事件 ID
        event_id = raw_event.get("event_id") or str(uuid.uuid4())
        
        # 轉換時間戳記
        timestamp = raw_event.get("timestamp")
        if timestamp and timestamp > 10**12:
            timestamp = int(timestamp / 1000)
        else:
            timestamp = int(timestamp) if timestamp else int(time.time())
        
        # 轉換事件類型
        event_type = self._convert_type(raw_event.get("type"))
        detail_type = self._convert_detail_type(raw_event)
        
        # 建構標準事件
        onebot_event = {
            "id": str(event_id),
            "time": timestamp,
            "type": event_type,
            "detail_type": detail_type,
            "platform": "myplatform",
            "self": {
                "platform": "myplatform",
                "user_id": str(raw_event.get("bot_id", ""))
            },
            "myplatform_raw": raw_event,
            "myplatform_raw_type": raw_event.get("type", "")
        }
        
        return onebot_event
```

## 連線管理

### WebSocket 連線

```python
from fastapi import WebSocket

class MyAdapter(BaseAdapter):
    async def start(self):
        """註冊 WebSocket 路由"""
        router.register_websocket(
            module_name="myplatform",
            path="/ws",
            handler=self._ws_handler,
            auth_handler=self._auth_handler
        )
    
    async def _ws_handler(self, websocket: WebSocket):
        """WebSocket 連線處理器"""
        self.connection = websocket
        
        try:
            while True:
                data = await websocket.receive_text()
                onebot_event = self.convert(data)
                if onebot_event:
                    await self.adapter.emit(onebot_event)
        except WebSocketDisconnect:
            self.logger.info("連線已中斷")
        finally:
            self.connection = None
    
    async def _auth_handler(self, websocket: WebSocket) -> bool:
        """WebSocket 認證"""
        token = websocket.query_params.get("token")
        return token == "valid_token"
```

### WebHook 連線

```python
from fastapi import Request

class MyAdapter(BaseAdapter):
    async def start(self):
        """註冊 WebHook 路由"""



### SendDSL 详解

# SendDSL 詳解

SendDSL 是 ErisPulse 介接器提供的鏈式調用風格的訊息發送介面。

## 基本調用方式

### 1. 指定類型和 ID

```python
await adapter.Send.To("group", "123").Text("Hello")
```

### 2. 僅指定 ID

```python
await adapter.Send.To("123").Text("Hello")
```

### 3. 指定發送帳號

```python
await adapter.Send.Using("bot1").Text("Hello")
```

### 4. 組合使用

```python
await adapter.Send.Using("bot1").To("group", "123").Text("Hello")
```

## 方法鏈

```
Using/Account() → To() → [修飾方法] → [發送方法]
```

## 發送方法

所有發送方法必須返回 `asyncio.Task` 物件。

### 基本方法

| 方法名 | 說明 | 返回值 |
|--------|------|---------|
| `Text(text: str)` | 發送文字訊息 | `asyncio.Task` |
| `Image(file: bytes \| str)` | 發送圖片 | `asyncio.Task` |
| `Voice(file: bytes \| str)` | 發送語音 | `asyncio.Task` |
| `Video(file: bytes \| str)` | 發送影片 | `asyncio.Task` |
| `File(file: bytes \| str)` | 發送檔案 | `asyncio.Task` |

### 原始方法

| 方法名 | 說明 | 返回值 |
|--------|------|---------|
| `Raw_ob12(message)` | 發送 OneBot12 格式訊息 | `asyncio.Task` |
| `Raw_json(json_str)` | 發送原始 JSON 訊息 | `asyncio.Task` |

## 修飾方法

修飾方法返回 `self` 以支援鏈式調用。

### At 方法

```python
# @單個使用者
await adapter.Send.To("group", "123").At("456").Text("你好")

# @多個使用者
await adapter.Send.To("group", "123").At("456").At("789").Text("你們好")
```

### AtAll 方法

```python
# @全體成員
await adapter.Send.To("group", "123").AtAll().Text("大家好")
```

### Reply 方法

```python
# 回覆訊息
await adapter.Send.To("group", "123").Reply("msg_id").Text("回覆內容")
```

### 組合修飾

```python
await adapter.Send.To("group", "123").At("456").Reply("msg_id").Text("回覆@的訊息")
```

## 帳號管理

### Using 方法

```python
# 使用帳號名
await adapter.Send.Using("account1").To("user", "123").Text("Hello")

# 使用帳號 ID
await adapter.Send.Using("bot_id").To("user", "123").Text("Hello")
```

### Account 方法

`Account` 方法與 `Using` 等價：

```python
await adapter.Send.Account("account1").To("user", "123").Text("Hello")
```

## 非同步處理

### 不等待結果

```python
# 訊息在後台發送
task = adapter.Send.To("user", "123").Text("Hello")

# 繼續執行其他操作
# ...
```

### 等待結果

```python
# 直接 await 取得結果
result = await adapter.Send.To("user", "123").Text("Hello")
print(f"發送結果: {result}")

# 先儲存 Task，稍後等待
task = adapter.Send.To("user", "123").Text("Hello")
# ... 其他操作 ...
result = await task
```

## 命名規範

### PascalCase 命名

所有發送方法使用大駝峰命名法：

```python
# ✅ 正確
def Text(self, text: str):
    pass

def Image(self, file: bytes):
    pass

# ❌ 錯誤
def text(self, text: str):
    pass

def send_image(self, file: bytes):
    pass
```

### 平台特有方法

不推薦添加平台前綴方法：

```python
# ✅ 推薦
def Sticker(self, sticker_id: str):
    pass

# ❌ 不推薦
def TelegramSticker(self, sticker_id: str):
    pass
```

使用 `Raw` 方法替代：

```python
# ✅ 推薦
await adapter.Send.Raw_ob12([{"type": "sticker", ...}])

# ❌ 不推薦
def TelegramSticker(self, ...):
    pass
```

## 返回值

### Task 物件

所有發送方法返回 `asyncio.Task`：

```python
import asyncio

def Text(self, text: str):
    return asyncio.create_task(
        self._adapter.call_api(
            endpoint="/send",
            content=text,
            recvId=self._target_id,
            recvType=self._target_type
        )
    )
```

### 標準化回應

`call_api` 應返回標準化回應：

```python
async def call_api(self, endpoint: str, **params):
    return {
        "status": "ok" or "failed",
        "retcode": 0 or error_code,
        "data": {...},
        "message_id": "msg_id" or "",
        "message": "",
        "{platform}_raw": raw_response
    }
```

## 完整範例

### 基本使用

```python
from ErisPulse.Core import adapter

my_adapter = adapter.get("myplatform")

# 發送文字
await my_adapter.Send.To("user", "123").Text("Hello World!")

# 發送圖片
await my_adapter.Send.To("group", "456").Image("https://example.com/image.jpg")

# 發送檔案
with open("document.pdf", "rb") as f:
    await my_adapter.Send.To("user", "123").File(f.read())
```

### 鏈式調用

```python
# @使用者 + 回覆
await my_adapter.Send.To("group", "456").At("789").Reply("msg123").Text("回覆@的訊息")

# @全體 + 多個修飾
await my_adapter.Send.Using("bot1").To("group", "456").AtAll().Text("公告訊息")
```

### 原始訊息

```python
# 發送 OneBot12 格式訊息
ob12_msg = [
    {"type": "text", "data": {"text": "Hello"}},
    {"type": "image", "data": {"file": "https://example.com/image.jpg"}}
]
await my_adapter.Send.To("group", "456").Raw_ob12(ob12_msg)
```

## 相關文件

- [介接器開發入門](getting-started.md) - 建立介接器
- [介接器核心概念](core-concepts.md) - 了解介接器架構
- [介接器最佳實踐](best-practices.md) - 開發高品質介接器
- [發送方法命名規範](../../standards/send-type-naming.md) - 命名規範



### 适配器开发最佳实践

# 配接器開發最佳實踐

本文件提供了 ErisPulse 配接器開發的最佳實踐建議。

## 連線管理

### 1. 實作連線重試

```python
import asyncio

class MyAdapter(BaseAdapter):
    async def start(self):
        retry_count = 0
        max_retries = 5
        
        while retry_count < max_retries:
            try:
                await self._connect_to_platform()
                self.logger.info("連線成功")
                break
            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    # 指數退避策略
                    wait_time = min(60 * (2 ** retry_count), 600)
                    self.logger.warning(
                        f"連線失敗，{wait_time}秒後重試 ({retry_count}/{max_retries}): {e}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error("連線失敗，已達到最大重試次數")
                    raise
```

### 2. 連線狀態管理

```python
class MyAdapter(BaseAdapter):
    def __init__(self, sdk):
        super().__init__()
        self.connection = None
        self._connected = False
    
    async def _ws_handler(self, websocket: WebSocket):
        self.connection = websocket
        self._connected = True
        self.logger.info("連線已建立")
        
        try:
            while True:
                data = await websocket.receive_text()
                await self._process_event(data)
        except WebSocketDisconnect:
            self.logger.info("連線已斷線")
        finally:
            self.connection = None
            self._connected = False
```

### 3. 心跳保活

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        self.connection = await self._connect_to_platform()
        # 啟動心跳任務
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
    
    async def _heartbeat_loop(self):
        """心跳保活"""
        while self.connection:
            try:
                await self.connection.send_json({"type": "ping"})
                await asyncio.sleep(30)  # 每30秒一次心跳
            except Exception as e:
                self.logger.error(f"心跳失敗: {e}")
                break
```

## 事件轉換

### 1. 嚴格遵循 OneBot12 標準

```python
class MyPlatformConverter:
    def convert(self, raw_event):
        """轉換事件"""
        onebot_event = {
            "id": str(raw_event.get("event_id", uuid.uuid4())),
            "time": int(time.time()),
            "type": self._convert_type(raw_event.get("type")),
            "detail_type": self._convert_detail_type(raw_event),
            "platform": "myplatform",
            "self": {
                "platform": "myplatform",
                "user_id": str(raw_event.get("bot_id", ""))
            },
            "myplatform_raw": raw_event,  # 保留原始資料（必須）
            "myplatform_raw_type": raw_event.get("type", "")  # 原始類型（必須）
        }
        return onebot_event
```

### 2. 時間戳標準化

```python
def _convert_timestamp(self, timestamp):
    """轉換為 10 位秒級時間戳"""
    if not timestamp:
        return int(time.time())
    
    # 如果是毫秒級時間戳
    if timestamp > 10**12:
        return int(timestamp / 1000)
    
    # 如果是秒級時間戳
    return int(timestamp)
```

### 3. 事件 ID 生成

```python
import uuid

def _generate_event_id(self, raw_event):
    """生成事件 ID"""
    event_id = raw_event.get("event_id")
    if event_id:
        return str(event_id)
    # 如果平台沒有提供 ID，生成 UUID
    return str(uuid.uuid4())
```

## SendDSL 實作

### 1. 必須返回 Task 物件

```python
class Send(BaseAdapter.Send):
    def Text(self, text: str):
        """發送文字訊息"""
        import asyncio
        return asyncio.create_task(
            self._adapter.call_api(
                endpoint="/send",
                content=text,
                recvId=self._target_id,
                recvType=self._target_type
            )
        )
```

### 2. 鏈式修飾方法返回 self

```python
class Send(BaseAdapter.Send):
    def At(self, user_id: str) -> 'Send':
        """@使用者"""
        if not hasattr(self, '_at_user_ids'):
            self._at_user_ids = []
        self._at_user_ids.append(user_id)
        return self  # 必須返回 self
    
    def Reply(self, message_id: str) -> 'Send':
        """回覆訊息"""
        self._reply_message_id = message_id
        return self  # 必須返回 self
```

### 3. 支援平台特有方法

```python
class Send(BaseAdapter.Send):
    def Sticker(self, sticker_id: str):
        """發送貼圖"""
        import asyncio
        return asyncio.create_task(
            self._adapter.call_api(
                endpoint="/send_sticker",
                sticker_id=sticker_id,
                recvId=self._target_id,
                recvType=self._target_type
            )
        )
    
    def Card(self, card_data: dict):
        """發送卡片訊息"""
        import asyncio
        return asyncio.create_task(
            self._adapter.call_api(
                endpoint="/send_card",
                card=card_data,
                recvId=self._target_id,
                recvType=self._target_type
            )
        )
```

## API 回應

### 1. 標準化回應格式

```python
async def call_api(self, endpoint: str, **params):
    try:
        raw_response = await self._platform_api_call(endpoint, **params)
        
        return {
            "status": "ok" if raw_response.get("success") else "failed",
            "retcode": 0 if raw_response.get("success") else raw_response.get("code", 10001),
            "data": raw_response.get("data"),
            "message_id": raw_response.get("data", {}).get("message_id", ""),
            "message": "",
            "myplatform_raw": raw_response
        }
    except Exception as e:
        return {
            "status": "failed",
            "retcode": 34000,
            "data": None,
            "message_id": "",
            "message": str(e),
            "myplatform_raw": None
        }
```

### 2. 錯誤碼規範

遵循 OneBot12 標準錯誤碼：

```python
# 1xxxx - 動作請求錯誤
10001: Bad Request
10002: Unsupported Action
10003: Bad Param

# 2xxxx - 動作處理器錯誤
20001: Bad Handler
20002: Internal Handler Error

# 3xxxx - 動作執行錯誤
31000: Database Error
32000: Filesystem Error
33000: Network Error
34000: Platform Error
35000: Logic Error
```

## 多帳號支援

### 1. 帳號設定驗證

```python
def _get_config(self):
    """驗證設定"""
    config = self.config_manager.getConfig("MyAdapter", {})
    accounts = config.get("accounts", {})
    
    if not accounts:
        # 建立預設帳號
        default_account = {
            "token": "",
            "enabled": False
        }
        config["accounts"] = {"default": default_account}
        self.config_manager.setConfig("MyAdapter", config)
    
    return config
```

### 2. 帳號選擇機制

```python
async def _get_account_for_message(self, event):
    """根據事件選擇發送帳號"""
    bot_id = event.get("self", {}).get("user_id")
    
    # 尋找匹配的帳號
    for account_name, account_config in self.accounts.items():
        if account_config.get("bot_id") == bot_id:
            return account_name
    
    # 如果沒有找到，使用第一個啟用的帳號
    for account_name, account_config in self.accounts.items():
        if account_config.get("enabled", True):
            return account_name
    
    return None
```

## 錯誤處理

### 1. 分類異常處理

```python
async def call_api(self, endpoint: str, **params):
    try:
        response = await self._platform_api_call(endpoint, **params)
        return self._standardize_response(response)
    except aiohttp.ClientError as e:
        # 網路錯誤
        self.logger.error(f"網路錯誤: {e}")
        return self._error_response("網路請求失敗", 33000)
    except asyncio.TimeoutError:
        # 逾時錯誤
        self.logger.error(f"請求逾時: {endpoint}")
        return self._error_response("請求逾時", 32000)
    except json.JSONDecodeError:
        # JSON 解析錯誤
        self.logger.error("JSON 解析失敗")
        return self._error_response("回應格式錯誤", 10006)
    except Exception as e:
        # 未知錯誤
        self.logger.error(f"未知錯誤: {e}", exc_info=True)
        return self._error_response(str(e), 34000)
```

### 2. 日誌記錄

```python
class MyAdapter(BaseAdapter):
    def __init__(self, sdk=None):
        super().__init__(sdk)
        self.logger = logger.get_child("MyAdapter")
    
    async def start(self):
        self.logger.info("配接器啟動中...")
        # ...
        self.logger.info("配接器啟動完成")
    
    async def shutdown(self):
        self.logger.info("配接器關閉中...")
        # ...
        self.logger.info("配接器關閉完成")
```

## 測試

### 1. 單元測試

```python
import pytest
from ErisPulse.Core.Bases import BaseAdapter

class TestMyAdapter:
    def test_converter(self):
        """測試轉換器"""
        converter = MyPlatformConverter()
        raw_event = {"type": "message", "content": "Hello"}
        result = converter.convert(raw_event)
        assert result is not None
        assert result["platform"] == "myplatform"
        assert "myplatform_raw" in result
    
    def test_api_response(self):
        """測試 API 回應格式"""
        adapter = MyAdapter()
        response = adapter.call_api("/test", param="value")
        assert "status" in response
        assert "retcode" in response
```

### 2. 整合測試

```python
@pytest.mark.asyncio
async def test_adapter_start():
    """測試配接器啟動"""
    adapter = MyAdapter()
    await adapter.start()
    assert adapter._connected is True

@pytest.mark.asyncio
async def test_send_message():
    """測試發送訊息"""
    adapter = MyAdapter()
    await adapter.start()
    
    result = await adapter.Send.To("user", "123").Text("Hello")
    assert result is not None
```

## 文件維護

### 1. 維護平台特性文件

在 `docs-new/platform-guide/` 下建立 `{platform}.md` 文件：

```markdown
# 平台名稱配接器文件

## 基本資訊
- 對應模組版本: 1.0.0
- 維護者: Your Name

## 支援的訊息發送類型
...

## 特有事件類型
...

## 設定選項
...
```

### 2. 更新版本資訊

發布新版本時，更新文件中的版本資訊：

```toml
[project]
version = "2.0.0"  # 更新版本號
```

## 相關文件

- [配接器開發入門](getting-started.md) - 建立第一個配接器
- [配接器核心概念](core-concepts.md) - 了解配接器架構
- [SendDSL 詳解](send-dsl.md) - 學習訊息發送



====
技术标准
====


### 会话类型标准

# ErisPulse 會話類型標準

本文文件定義了 ErisPulse 支援的會話類型標準，包括接收事件類型與發送目標類型。

## 1. 核心概念

### 1.1 接收類型 && 發送類型

ErisPulse 區分兩種會話類型：

- **接收類型**：用於接收的事件的 `detail_type` 欄位
- **發送類型**：用於發送訊息時 `Send.To()` 方法的目的類型

### 1.2 類型對應關係

```
接收類型 (detail_type)     發送類型 (Send.To)
─────────────────        ────────────────
private                 →        user
group                   →        group
channel                 →        channel
guild                   →        guild
thread                  →        thread
user                    →        user
```

**關鍵點**：
- `private` 是接收時的類型，發送時必須使用 `user`
- `group`、`channel`、`guild`、`thread` 在接收和發送時類型相同
- 系統會自動進行類型轉換，無需手動處理（這代表著你可以直接使用獲得的接收類型進行發送），但實際上，你無需考慮這些。由於 Event 的包裝類的存在，你可以直接使用 `event.reply()` 方法，而無需考慮類型轉換。

## 2. 標準會話類型

### 2.1 OneBot12 標準類型

#### private
- **接收類型**：`private`
- **發送類型**：`user`
- **說明**：一對一私聊訊息
- **ID 欄位**：`user_id`
- **適用平台**：所有支援私聊的平台

#### group
- **接收類型**：`group`
- **發送類型**：`group`
- **說明**：群組聊天訊息，包括各種形式的群組（如 Telegram supergroup）
- **ID 欄位**：`group_id`
- **適用平台**：所有支援群組聊天的平台

#### user
- **接收類型**：`user`
- **發送類型**：`user`
- **說明**：使用者類型，某些平台（如 Telegram）將私聊表示為 user 而非 private
- **ID 欄位**：`user_id`
- **適用平台**：Telegram 等平台

### 2.2 ErisPulse 擴展類型

#### channel
- **接收類型**：`channel`
- **發送類型**：`channel`
- **說明**：頻道訊息，支援多個使用者的廣播式訊息
- **ID 欄位**：`channel_id`
- **適用平台**：Discord, Telegram, Line 等

#### guild
- **接收類型**：`guild`
- **發送類型**：`guild`
- **說明**：伺服器/社群訊息，通常用於 Discord Guild 級別的事件
- **ID 欄位**：`guild_id`
- **適用平台**：Discord 等

#### thread
- **接收類型**：`thread`
- **發送類型**：`thread`
- **說明**：話題/子頻道訊息，用於社群中的子討論區
- **ID 欄位**：`thread_id`
- **適用平台**：Discord Threads, Telegram Topics 等

## 3. 平台類型對應

### 3.1 對應原則

介面卡負責將平台的原生類型對應到 ErisPulse 標準類型：

```
平台原生類型 → ErisPulse 標準類型 → 發送類型
```

### 3.2 常見平台對應範例

#### Telegram
```
Telegram 類型          ErisPulse 接收類型    發送類型
─────────────────      ────────────────       ───────────
private                private                 user
group                  group                   group  # 對應到 group
channel                channel                 channel
```

#### Discord
```
Discord 類型          ErisPulse 接收類型    發送類型
─────────────────      ────────────────       ───────────
Direct Message         private                user
Text Channel           channel                channel
Guild                  guild                  guild
Thread                 thread                 thread
```

#### OneBot11
```
OneBot11 類型        ErisPulse 接收類型    發送類型
─────────────────      ────────────────       ───────────
private                private                user
group                  group                  group
discuss                group                  group  # 對應到 group
```

## 4. 自訂類型擴展

### 4.1 註冊自訂類型

介面卡可以註冊自訂會話類型：

```python
from ErisPulse.Core.Event import register_custom_type

# 註冊自訂類型
register_custom_type(
    receive_type="my_custom_type",
    send_type="custom",
    id_field="custom_id",
    platform="MyPlatform"
)
```

### 4.2 使用自訂類型

註冊後，系統會自動處理該類型的轉換與推斷：

```python
# 自動推斷
receive_type = infer_receive_type(event, platform="MyPlatform")
# 返回: "my_custom_type"

# 轉換為發送類型
send_type = convert_to_send_type(receive_type, platform="MyPlatform")
# 返回: "custom"

# 取得對應 ID
target_id = get_target_id(event, platform="MyPlatform")
# 返回: event["custom_id"]
```

### 4.3 取消註冊自訂類型

```python
from ErisPulse.Core.Event import unregister_custom_type

unregister_custom_type("my_custom_type", platform="MyPlatform")
```

## 5. 自動類型推斷

當事件沒有明確的 `detail_type` 欄位時，系統會根據存在的 ID 欄位自動推斷類型：

### 5.1 推斷優先順序

```
優先順序（由高到低）：
1. group_id     → group
2. channel_id   → channel
3. guild_id     → guild
4. thread_id    → thread
5. user_id      → private
```

### 5.2 使用範例

```python
# 事件只有 group_id
event = {"group_id": "123", "user_id": "456"}
receive_type = infer_receive_type(event)
# 返回: "group"（優先使用 group_id）

# 事件只有 user_id
event = {"user_id": "123"}
receive_type = infer_receive_type(event)
# 返回: "private"
```

## 6. API 使用範例

### 6.1 發送訊息

```python
from ErisPulse import adapter

# 發送給使用者
await adapter.myplatform.Send.To("user", "123").Text("Hello")

# 發送給群組
await adapter.myplatform.Send.To("group", "456").Text("Hello")

# 自動轉換 private → user（不推薦，可能有相容性問題）
await adapter.myplatform.Send.To("private", "789").Text("Hello")
# 內部自動轉換為: Send.To("user", "789") # 直接使用 user 作為會話類型是更優的選擇
```

### 6.2 事件回覆

```python
from ErisPulse.Core.Event import Event

# Event.reply() 自動處理類型轉換
await event.reply("回覆內容")
# 內部自動使用正確的發送類型
```

### 6.3 命令處理

```python
from ErisPulse.Core.Event import command

@command(name="test")
async def handle_test(event):
    # 系統自動處理會話類型
    # 無需手動判斷 group_id 還是 user_id
    await event.reply("命令執行成功")
```

## 7. 最佳實務

### 7.1 介面卡開發者

1. **使用標準對應**：盡可能對應到標準類型，而非建立新類型
2. **正確轉換**：確保接收類型和發送類型的對應關係正確
3. **保留原始資料**：在 `{platform}_raw` 中保留原始事件類型
4. **文件說明**：在介面卡文件中說明類型對應關係

### 7.2 模組開發者

1. **使用工具方法**：使用 `get_send_type_and_target_id()` 等工具方法
2. **避免硬編碼**：不要寫 `if group_id else "private"` 這樣的程式碼
3. **考慮所有類型**：程式碼要支援所有標準類型，不只是 private/group
4. **靈活設計**：使用事件包裝器的方法，而非直接存取欄位

### 7.3 類型推斷

- **優先使用 detail_type**：如果有明確欄位，不進行推斷
- **合理使用推斷**：只在沒有明確類型時使用
- **注意優先順序**：了解推斷優先順序，避免意外結果

## 8. 常見問題

### Q1: 為什麼發送時 private 要轉換為 user？

A: 這是 OneBot12 標準的要求。`private` 是接收時的概念，發送時使用 `user` 更符合語意。

### Q2: 如何支援新的會話類型？

A: 透過 `register_custom_type()` 註冊自訂類型，或直接使用標準類型中的 `channel`、`guild` 等。

### Q3: 事件沒有 detail_type 怎麼辦？

A: 系統會根據存在的 ID 欄位自動推斷。優先順序為：group > channel > guild > thread > user。

### Q4: 介面卡如何對應 Telegram supergroup？

A: 在介面卡的轉換邏輯中，將 `supergroup` 對應到標準的 `group` 類型。

### Q5: 郵件等特殊平台如何處理？

A: 針對不通用或平台特有的類型，使用 `{platform}_raw` 和 `{platform}_raw_type` 保留原始資料，介面卡自行處理。

## 9. 相關文件

- [事件轉換標準](event-conversion.md) - 完整的事件轉換規範
- [發送方法規範](send-method-spec.md) - Send 類別的方法命名和參數規範
- [介面卡開發指南](../developer-guide/adapters/) - 介面卡開發完整指南

請直接返回翻譯後的完整 Markdown 內容，不要包含任何其他文字。



### 事件转换标准

# 適配器標準化轉換規範

## 1. 核心原則
1. 嚴格相容：所有標準欄位必須完全遵循 OneBot12 規範
2. 明確擴展：平台特有功能必須添加 {platform}_ 前綴（如 yunhu_form）
3. 資料完整：原始事件資料必須保留在 {platform}_raw 欄位中，原始事件類型必須保留在 {platform}_raw_type 欄位中
4. 時間統一：所有時間戳記必須轉換為 10 位 Unix 時間戳記（秒級）
5. 平台統一：platform 項命名必須與你在 ErisPulse 中註冊的名稱/別稱一致

## 2. 標準欄位要求

### 2.1 必要欄位
| 欄位 | 類型 | 說明 |
|------|------|------|
| id | string | 事件唯一識別碼 |
| time | integer | Unix 時間戳記（秒級） |
| type | string | 事件類型 |
| detail_type | string | 事件詳細類型（詳見[會話類型標準](session-types.md)） |
| platform | string | 平台名稱 |
| self | object | 機器人自身資訊 |
| self.platform | string | 平台名稱 |
| self.user_id | string | 機器人使用者 ID |

**detail_type 規範**：
- 必須使用 ErisPulse 標準會話類型（詳見 [會話類型標準](session-types.md)）
- 支援的類型：`private`, `group`, `user`, `channel`, `guild`, `thread`
- 適配器負責將平台原生類型對應到標準類型

### 2.2 訊息事件欄位
| 欄位 | 類型 | 說明 |
|------|------|------|
| message | array | 訊息段陣列 |
| alt_message | string | 訊息段備用文字 |
| user_id | string | 使用者 ID |
| user_nickname | string | 使用者暱稱（選填） |

### 2.3 通知事件欄位
| 欄位 | 類型 | 說明 |
|------|------|------|
| user_id | string | 使用者 ID |
| user_nickname | string | 使用者暱稱（選填） |
| operator_id | string | 操作者 ID（選填） |

### 2.4 請求事件欄位
| 欄位 | 類型 | 說明 |
|------|------|------|
| user_id | string | 使用者 ID |
| user_nickname | string | 使用者暱稱（選填） |
| comment | string | 請求附言（選填） |

## 3. 事件格式範例

### 3.1 訊息事件 (message)
```json
{
  "id": "1234567890",
  "time": 1752241223,
  "type": "message",
  "detail_type": "group",
  "platform": "yunhu",
  "self": {
    "platform": "yunhu",
    "user_id": "bot_123"
  },
  "message": [
    {
      "type": "text",
      "data": {
        "text": "抽獎 超級大獎"
      }
    }
  ],
  "alt_message": "抽獎 超級大獎",
  "user_id": "user_456",
  "user_nickname": "YingXinche",
  "group_id": "group_789",
  "yunhu_raw": {...},
  "yunhu_raw_type": "message.receive.normal",
  "yunhu_command": {
    "name": "抽獎",
    "args": "超級大獎"
  }
}
```

### 3.2 通知事件 (notice)
```json
{
  "id": "1234567891",
  "time": 1752241224,
  "type": "notice",
  "detail_type": "group_member_increase",
  "platform": "yunhu",
  "self": {
    "platform": "yunhu",
    "user_id": "bot_123"
  },
  "user_id": "user_456",
  "user_nickname": "YingXinche",
  "group_id": "group_789",
  "operator_id": "",
  "yunhu_raw": {...},
  "yunhu_raw_type": "bot.followed"
}
```

### 3.3 請求事件 (request)
```json
{
  "id": "1234567892",
  "time": 1752241225,
  "type": "request",
  "detail_type": "friend",
  "platform": "onebot11",
  "self": {
    "platform": "onebot11",
    "user_id": "bot_123"
  },
  "user_id": "user_456",
  "user_nickname": "YingXinche",
  "comment": "請加好友",
  "onebot11_raw": {...},
  "onebot11_raw_type": "request"  // onebot11 原始事件類型就是 `request`
}
```

## 4. 訊息段標準

### 4.1 通用訊息段
```json
{
  "type": "text",
  "data": {
    "text": "Hello World"
  }
}
```

### 4.2 特殊訊息段
平台特有的訊息段需要添加平台前綴：
```json
{
  "type": "yunhu_form",
  "data": {
    "form_id": "123456"
  }
}
```

## 5. 未知事件處理

對於無法識別的事件類型，應產生警告事件：
```json
{
  "id": "1234567893",
  "time": 1752241223,
  "type": "unknown",
  "platform": "yunhu",
  "yunhu_raw": {...},
  "yunhu_raw_type": "unknown",
  "warning": "不支援的事件類型：special_event",
  "alt_message": "This event type is not supported by this system."
}
```

## 6. 平台特性欄位

所有平台特有欄位必須以平台名稱作為前綴

比如:
- 雲湖平台：`yunhu_`
- Telegram 平台：`telegram_`
- OneBot11 平台：`onebot11_`

### 6.1 特有欄位範例
```json
{
  "yunhu_command": {
    "name": "抽獎",
    "args": "超級大獎"
  },
  "yunhu_form": {
    "form_id": "123456"
  },
  "telegram_sticker": {
    "file_id": "CAACAgIAAxkBAA..."
  }
}
```

## 7. 適配器實作檢查清單
- [ ] 所有標準欄位已正確對應
- [ ] 平台特有欄位已添加前綴
- [ ] 時間戳記已轉換為 10 位秒級
- [ ] 原始資料保存在 {platform}_raw，原始事件類型已儲存到 {platform}_raw_type
- [ ] 訊息段的 alt_message 已產生
- [ ] 所有事件類型已通過單元測試
- [ ] 文件包含完整範例和說明



### API 响应标准

# ErisPulse 適配器標準化回傳規範

## 1. 說明
為什麼會有這個規範？

為了確保各平台發送介面回傳統一性與 OneBot12 相容性，ErisPulse 適配器在 API 回應格式上採用了 OneBot12 定義的訊息發送回傳結構標準。

但 ErisPulse 的協議有一些特殊定義：
- 1. 基礎欄位中，message_id 是必須的，但 OneBot12 標準中無此欄位
- 2. 回傳內容中需要新增 {platform_name}_raw 欄位，用於存放原始回應資料

## 2. 基礎回傳結構
所有動作回應必須包含以下基礎欄位：

| 欄位名 | 資料類型 | 必選 | 說明 |
|-------|---------|------|------|
| status | string | 是 | 執行狀態，必須是 "ok" 或 "failed" |
| retcode | int64 | 是 | 回傳碼，遵循 OneBot12 回傳碼規則 |
| data | any | 是 | 回應資料，成功時包含請求結果，失敗時為 null |
| message_id | string | 是 | 訊息 ID，用於識別訊息，沒有則為空字串 |
| message | string | 是 | 錯誤資訊，成功時為空字串 |
| {platform_name}_raw | any | 否 | 原始回應資料 |

可選欄位：
| 欄位名 | 資料類型 | 必選 | 說明 |
|-------|---------|------|------|
| echo | string | 否 | 當請求中包含 echo 欄位時，原樣回傳 |

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

#### 0 成功
- 0: 成功

#### 1xxxx 動作請求錯誤
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

#### 2xxxx 動作處理器錯誤
| 錯誤碼 | 錯誤名 | 說明 |
|-------|-------|------|
| 20001 | Bad Handler | 動作處理器實作錯誤 |
| 20002 | Internal Handler Error | 動作處理器執行時拋出異常 |

#### 3xxxx 動作執行錯誤
| 錯誤碼範圍 | 錯誤類型 | 說明 |
|-----------|---------|------|
| 31xxx | Database Error | 資料庫錯誤 |
| 32xxx | Filesystem Error | 檔案系統錯誤 |
| 33xxx | Network Error | 網路錯誤 |
| 34xxx | Platform Error | 機器人平台錯誤 |
| 35xxx | Logic Error | 動作邏輯錯誤 |
| 36xxx | I Am Tired | 實作決定罷工 |

#### 保留錯誤段
- 4xxxx、5xxxx: 保留段，不應使用
- 6xxxx～9xxxx: 其他錯誤段，供實作自定義使用

## 4. 實作要求
1. 所有回應必須包含 status、retcode、data 和 message 欄位
2. 當請求中包含非空 echo 欄位時，回應必須包含相同值的 echo 欄位
3. 回傳碼必須嚴格遵循 OneBot12 規範
4. 錯誤資訊應當是人類可讀的描述

## 5. 注意事項
- 關於 3xxxx 錯誤碼，低三位可由實作自行定義
- 避免使用保留錯誤段 (4xxxx、5xxxx)
- 錯誤資訊應當簡潔明瞭，便於除錯



### 发送方法规范

# ErisPulse 發送方法規範

本文件定義了 ErisPulse 适配器中 `Send` 類別發送方法的命名規範和參數規範。

## 1. 標準方法命名

所有發送方法使用 **大駝峰命名法**，首字母大寫。

### 1.1 標準發送方法

| 方法名 | 說明 | 參數類型 |
|-------|------|---------|
| `Text` | 傳送文字訊息 | `str` |
| `Image` | 傳送圖片 | `bytes` \| `str` (URL/路徑) |
| `Voice` | 傳送語音 | `bytes` \| `str` (URL/路徑) |
| `Video` | 傳送視頻 | `bytes` \| `str` (URL/路徑) |
| `File` | 傳送檔案 | `bytes` \| `str` (URL/路徑) |
| `At` | @用戶/群組 | `str` (user_id) |
| `Face` | 傳送表情 | `str` (emoji) |
| `Reply` | 回覆訊息 | `str` (message_id) |
| `Forward` | 轉發訊息 | `str` (message_id) |
| `Markdown` | 傳送 Markdown 訊息 | `str` |
| `HTML` | 傳送 HTML 訊息 | `str` |
| `Card` | 傳送卡片訊息 | `dict` |

### 1.2 鏈式修飾方法

| 方法名 | 說明 | 參數類型 |
|-------|------|---------|
| `At` | @用戶（可多次調用） | `str` (user_id) |
| `AtAll` | @全體成員 | 無 |
| `Reply` | 回覆訊息 | `str` (message_id) |

### 1.3 協議方法

| 方法名 | 說明 |
|-------|------|
| `Raw_ob12` | 傳送原始 OneBot12 格式訊息 |
| `Raw_json` | 傳送原始 JSON 格式訊息 |
| `Raw_xml` | 傳送原始 XML 格式訊息 |

## 2. 參數規範詳解

### 2.1 媒體訊息參數規範

媒體訊息（`Image`、`Voice`、`Video`、`File`）支援兩種參數類型：

#### 2.1.1 字串參數（URL 或檔案路徑）

**格式：** `str`

**支援類型：**
- **URL**：網路資源位址（如 `https://example.com/image.jpg`）
- **檔案路徑**：本機檔案路徑（如 `/path/to/file.jpg` 或 `C:\\path\\to\\file.jpg`）

**使用場景：**
- 檔案已在網路上，直接發送 URL
- 檔案在本機磁碟，發送檔案路徑
- 希望適配器自動處理檔案上傳

**推薦：** 優先使用 URL，如果 URL 不可用則使用本機檔案路徑

**範例：**
```python
# 使用 URL
send.Image("https://example.com/image.jpg")

# 使用本地文件路径
send.Image("/path/to/local/image.jpg")
send.Image("C:\\path\\to\\local\\image.jpg")
```

#### 2.1.2 二進位數據參數

**格式：** `bytes`

**使用場景：**
- 檔案已在記憶體中（如從網路下載、從其他來源讀取）
- 需要處理後再發送（如圖片壓縮、格式轉換）
- 避免重複讀取檔案

**注意事項：**
- 大檔案上傳可能消耗較多記憶體
- 建議設定合理的檔案大小限制

**範例：**
```python
# 從網路讀取後發送
import requests
image_data = requests.get("https://example.com/image.jpg").content
send.Image(image_data)

# 從檔案讀取後發送
with open("/path/to/local/image.jpg", "rb") as f:
    image_data = f.read()
send.Image(image_data)
```

#### 2.1.3 參數處理優先順序

當適配器接收到媒體訊息參數時，應按以下順序處理：

1. **URL 參數**：直接使用 URL 發送(部分平台适配器可能存在URL下载后再上传的操作)
2. **檔案路徑**：檢測是否為本地路徑，若是則上傳檔案
3. **二進位數據**：直接上傳二進位數據

**適配器實作建議：**
```python
def Image(self, image: Union[bytes, str]):
    if isinstance(image, str):
        # 判斷是 URL 還是本地路徑
        if image.startswith(("http://", "https://")):
            # URL 直接發送
            return self._send_image_by_url(image)
        else:
            # 本地路徑，讀取後上傳
            with open(image, "rb") as f:
                return self._upload_image(f.read())
    elif isinstance(image, bytes):
        # 二進位數據，直接上傳
        return self._upload_image(image)
```

### 2.2 文字訊息參數規範

**方法：** `Text`

**參數：** `text` (`str`)

**要求：**
- 支援純文字內容
- 不進行格式化處理（如 Markdown、HTML）
- 建議限制文字長度（如 2000-5000 字元）
- 超長文字應提示使用者截斷或分段發送

**範例：**
```python
# 簡單文字
send.Text("你好，世界！")

# 長文字（建議分段）
long_text = "很長的文字內容..."
if len(long_text) > 2000:
    # 分段發送
    for i in range(0, len(long_text), 2000):
        send.Text(long_text[i:i+2000])
else:
    send.Text(long_text)
```

### 2.3 @用戶參數規範

**方法：** `At`（修飾方法）

**參數：** `user_id` (`str`)

**要求：**
- `user_id` 應為字串類型的使用者識別符
- 不同平台的 `user_id` 格式可能不同（數字、UUID、字串等）
- 適配器負責將 `user_id` 轉換為平台特定的格式

**範例：**
```python
# 單個 @ 用戶
send.Text("你好").At("123456")

# 多個 @ 用戶（鏈式調用）
send.Text("大家好").At("123456").At("789012")
```

### 2.4 回覆訊息參數規範

**方法：** `Reply`（修飾方法）

**參數：** `message_id` (`str`)

**要求：**
- `message_id` 應為字串類型的訊息識別符
- 應為之前收到的訊息的 ID
- 某些平台可能不支援回覆功能，適配器應優雅降級

**範例：**
```python
# 回覆一條訊息
send.Text("收到").Reply("msg_123456")
```

### 2.5 卡片訊息參數規範

**方法：** `Card`

**參數：** `data` (`dict`)

**要求：**
- `data` 應為字典類型的卡片數據
- 具體格式取決於平台（如 Telegram 的 InlineKeyboard、OneBot12 的 card）
- 適配器應驗證數據格式並轉換為平台特定格式
- 不支援卡片的平台應降級為文字訊息

**範例：**
```python
# 發送卡片數據
card_data = {
    "type": "image",
    "title": "卡片標題",
    "content": "卡片內容",
    "image": "https://example.com/image.jpg"
}
send.Card(card_data)
```

### 2.6 參數驗證和錯誤處理

**通用要求：**
1. **類型檢查**：驗證參數類型是否正確
2. **範圍檢查**：驗證參數值是否在合理範圍內
3. **存在性檢查**：驗證必要參數是否存在
4. **格式檢查**：驗證 URL、檔案路徑等格式是否正確

**錯誤處理建議：**
```python
def Image(self, image: Union[bytes, str]):
    # 類型檢查
    if not isinstance(image, (bytes, str)):
        raise TypeError("參數必須是 bytes 或 str 類型")
    
    # URL 格式檢查
    if isinstance(image, str) and not image.startswith(("http://", "https://")):
        # 檢查是否為本地檔案路徑
        if not os.path.exists(image):
            raise FileNotFoundError(f"檔案不存在: {image}")
    
    # 檔案大小檢查
    if isinstance(image, bytes) and len(image) > 10 * 1024 * 1024:  # 10MB
        raise ValueError("檔案大小超過限制（10MB）")
    
    # 發送訊息
    return self._send_image(image)
```

## 3. 平台特有方法命名

**不推薦**在 `Send` 類別中直接新增平台前綴方法。建議使用通用方法名或 `Raw_{協議}` 方法。

**不推薦：**
```python
def YunhuForm(self, form_id: str):  # ❌ 不推薦
    pass

def TelegramSticker(self, sticker_id: str):  # ❌ 不推薦
    pass
```

**推薦：**
```python
def Form(self, form_id: str):  # ✅ 通用方法名
    pass

def Sticker(self, sticker_id: str):  # ✅ 通用方法名
    pass

# 或使用 Raw 方法
def Raw_ob12(self, message):  # ✅ 發送 OneBot12 格式
    pass
```

## 4. 參數命名規範

| 參數名 | 說明 | 類型 |
|-------|------|------|
| `text` | 文字內容 | `str` |
| `url` / `file` | 檔案 URL 或二進位數據 | `str` / `bytes` |
| `user_id` | 用戶 ID | `str` / `int` |
| `group_id` | 群組 ID | `str` / `int` |
| `message_id` | 訊息 ID | `str` |
| `data` | 數據對象（如卡片數據） | `dict` |

## 5. 返回值規範

- **發送方法**（如 `Text`, `Image`）：必須返回 `asyncio.Task` 物件
- **修飾方法**（如 `At`, `Reply`, `AtAll`）：必須返回 `self` 以支援鏈式調用

## 6. 相關文檔

- [适配器系统 - SendDSL 详解](../core/adapters.md) - 查看調用方法和使用範例
- [适配器开发指南](../development/adapter.md) - 查看适配器實作要求
- [模块开发指南](../development/module.md) - 查看模組中的發送訊息範例

