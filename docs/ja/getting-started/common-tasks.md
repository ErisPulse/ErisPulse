# 一般的タスクの例

このガイドでは、一般的な機能の実装例を提供し、一般的な機能を迅速に実装できるようにします。

## 内容リスト

1. データの永続化
2. 定期タスク
3. メッセージフィルタリング
4. 多プラットフォーム対応
5. メッセージ送信の高度機能（再試行/タイムアウト/一括送信）
6. 権限制御
7. メッセージ統計
8. 検索機能
9. 画像処理

## データ永続化

### シンプルなカウンター

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command

@command("count", help="コマンドの呼び出し回数を表示")
async def count_handler(event):
    # カウントを取得
    count = sdk.storage.get("command_count", 0)
    
    # カウントを増加
    count += 1
    sdk.storage.set("command_count", count)
    
    await event.reply(f"このコマンドは {count} 回目の呼び出しです")
```

### ユーザーデータの保存

```python
@command("profile", help="個人情報の表示")
async def profile_handler(event):
    user_id = event.get_user_id()
    
    # ユーザーデータを取得
    user_data = sdk.storage.get(f"user:{user_id}", {
        "nickname": "",
        "join_date": None,
        "message_count": 0
    })
    
    profile_text = f"""
名前: {user_data['nickname']}
加入日: {user_data['join_date']}
メッセージ数: {user_data['message_count']}
    """
    
    await event.reply(profile_text.strip())

@command("setnick", help="名前を設定")
async def setnick_handler(event):
    user_id = event.get_user_id()
    args = event.get_command_args()
    
    if not args:
        await event.reply("名前を入力してください")
        return
    
    # ユーザーデータを更新
    user_data = sdk.storage.get(f"user:{user_id}", {})
    user_data["nickname"] = " ".join(args)
    sdk.storage.set(f"user:{user_id}", user_data)
    
    await event.reply(f"名前を {' '.join(args)} に設定しました")
```

## タイマー

### シンプルなタイマー

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command
import asyncio

class TimerModule:
    def __init__(self):
        self.sdk = sdk
        self._tasks = []
    
    async def on_load(self, event):
        """モジュールのロード時にタイマーを開始"""
        self._start_timers()
        
        @command("timer", help="タイマー管理")
        async def timer_handler(event):
            await event.reply("タイマーが実行中です...")
    
    def _start_timers(self):
        """タイマーを開始"""
        # 60秒ごとに実行
        task = asyncio.create_task(self._every_minute())
        self._tasks.append(task)
        
        # 毎日午前0時に実行
        task = asyncio.create_task(self._daily_task())
        self._tasks.append(task)
    
    async def _every_minute(self):
        """1分ごとに実行されるタスク"""
        self.sdk.logger.info("1分ごとのタスクを実行")
        # ここに処理を記述してください...
    
    async def _daily_task(self):
        """毎日午前0時に実行されるタスク（注：UTC時間に基づいて計算されます。ローカル時間が必要な場合は、独自に調整してください）"""
        import time
        
        while True:
            # 午前0時までの時間を計算
            now = time.time()
            midnight = now + (86400 - now % 86400)
            
            await asyncio.sleep(midnight - now)
            
            # タスクを実行
            self.sdk.logger.info("毎日のタスクを実行")
            # ここに処理を記述してください...
```

### ライフサイクルイベントの使用

```python
@sdk.lifecycle.on("core.init.complete")
async def init_complete_handler(event_data):
    """SDKの初期化完了後にタイマーを開始"""
    import asyncio
    
    async def daily_reminder():
        """毎日のリマインダー"""
        await asyncio.sleep(86400)  # 24時間
        sdk.logger.info("毎日のタスクを実行")
    
    # バックグラウンドタスクを開始
    asyncio.create_task(daily_reminder())
```

## メッセージフィルタリング

### キーワードフィルタリング

```python
from ErisPulse.Core.Event import message

blocked_words = ["ゴミ", "広告", "フィッシング"]

@message.on_message()
async def filter_handler(event):
    text = event.get_text()
    
    # 敏感語を含むかチェック
    for word in blocked_words:
        if word in text:
            sdk.logger.warning(f"フィルタリングされたメッセージ: {word}")
            return  # このメッセージは処理しない
    
    # 通常のメッセージ処理
    await event.reply(f"受信: {text}")
```

### ブラックリストフィルタリング

```python
# 設定ファイルやストレージからブラックリストを読み込む
blacklist = sdk.storage.get("user_blacklist", [])

@message.on_message()
async def blacklist_handler(event):
    user_id = event.get_user_id()
    
    if user_id in blacklist:
        sdk.logger.info(f"ブラックリストユーザー: {user_id}")
        return  # 処理しない
    
    # 通常の処理
    await event.reply(f"こんにちは、{user_id}")
```

## 多プラットフォーム対応

### プラットフォーム固有の応答

```python
@command("help", help="ヘルプを表示します")
async def help_handler(event):
    platform = event.get_platform()
    
    if platform == "yunhu":
        await event.reply("雲湖プラットフォームのヘルプ...")
    elif platform == "telegram":
        await event.reply("Telegram プラットフォームのヘルプ...")
    elif platform == "onebot11":
        await event.reply("OneBot11 のヘルプ...")
    else:
        await event.reply("一般的なヘルプ情報")
```

### プラットフォームの機能検出

```python
@command("rich", help="富文本メッセージを送信します")
async def rich_handler(event):
    platform = event.get_platform()
    
    if platform == "yunhu":
        # 雲湖は HTML をサポート
        yunhu = sdk.adapter.get("yunhu")
        await yunhu.Send.To("user", event.get_user_id()).Html(
            "<b>太字のテキスト</b><i>斜体のテキスト</i>"
        )
    elif platform == "telegram":
        # Telegram は Markdown をサポート
        telegram = sdk.adapter.get("telegram")
        await telegram.Send.To("user", event.get_user_id()).Markdown(
            "**太字のテキスト** *斜体のテキスト*"
        )
    else:
        # 他のプラットフォームはプレーンテキストを使用
        await event.reply("太字のテキスト 斜体のテキスト")
```

## メッセージ送信の高度な機能（再試行/タイムアウト/一括送信）

単純な `event.reply()` に加えて、アダプターの Send DSL を使って、より複雑な送信シナリオを実現できます。例えば、送信失敗時の自動再試行、タイムアウトによるキャンセル、送信成功後に実行するロジック、複数メッセージの一括送信などです。

> 以下の例では、`event.get_detail_type()` と `event.get_target_id()` を使用して、イベントから送信先のタイプと ID を取得しています（グループチャットでは `group_id`、プライベートチャットでは `user_id` が自動的に取得されます）。これにより、送信先をハードコーディングする必要がありません。

### 送信成功後に実行するロジック

```python
@command("pay", help="支払いをシミュレート")
async def pay_handler(event):
    yunhu = sdk.adapter.get(event.get_platform())
    user_id = event.get_user_id()
    # 送信が成功した後にのみポイントを減算
    await (yunhu.Send.To(event.get_detail_type(), event.get_target_id())
           .Hook(lambda r: sdk.storage.set(f"points:{user_id}", -10))
           .Text("支払い成功。10ポイントを減算しました。"))
```

### 失敗時の再試行 + タイムアウトによるキャンセル

```python
@command("notice", help="重要な通知を送信")
async def notice_handler(event):
    adapter_inst = sdk.adapter.get(event.get_platform())
    # 最大3回再試行、各試行のタイムアウトは10秒
    task = (adapter_inst.Send.To(event.get_detail_type(), event.get_target_id())
            .Retry(3)
            .Timeout(10)
            .OnError(lambda ctx: sdk.logger.error(f"通知送信失敗: {ctx.error}"))
            .Text("これは重要な通知です。"))
    # 送信結果を待たずにバックグラウンドで送信
```

### 複数メッセージの一括送信

1つのチェーンで複数のメッセージを送信し、統一して処理できます。

```python
@command("announce", help="公告を送信")
async def announce_handler(event):
    adapter_inst = sdk.adapter.get(event.get_platform())
    # 複数のメッセージを構築し、一括で送信（デフォルトでは並行実行）
    results = await (adapter_inst.Send.To(event.get_detail_type(), event.get_target_id())
                    .Build()
                    .Text("📋 今日の公告")
                    .Image("https://example.com/banner.jpg")
                    .Text("詳細は上記画像をご覧ください。")
                    .Retry(2)            # 失敗したメッセージは個別に再試行
                    .send_all())
    sdk.logger.info(f"一括送信完了。合計 {len(results)} 件のメッセージを送信しました。")
```

> 送信ルールの詳細と一括送信に関する説明については、[プラットフォームの特徴ガイド](../platform-guide/README.md#送信ルールデコレーター)をご覧ください。

## 権限制御

### 管理者チェック

```python
# 管理者リストの設定
MASTERS = ["user123", "user456"]

def is_master(user_id):
    """フレームワークの管理者かどうかをチェック"""
    return user_id in MASTERS

@command("master", help="フレームワーク管理者用コマンド")
async def master_handler(event):
    user_id = event.get_user_id()
    
    if not is_master(user_id):
        await event.reply("権限がありません。このコマンドはフレームワーク管理者のみ使用可能です。")
        return
    
    await event.reply("フレームワーク管理者用コマンドが正常に実行されました。")

@command("addmaster", help="フレームワーク管理者を追加")
async def addmaster_handler(event):
    if not is_master(event.get_user_id()):
        return
    
    args = event.get("text", "").split()
    if len(args) < 2:
        await event.reply("使用方法: /addmaster <ユーザーID>")
        return
    
    new_master = args[0]
    MASTERS.append(new_master)
    await event.reply(f"フレームワーク管理者として追加しました: {new_master}")
```

### グループ権限

```python
@command("groupinfo", help="グループ情報を表示")
async def groupinfo_handler(event):
    if not event.is_group_message():
        await event.reply("このコマンドはグループチャットでのみ使用可能です。")
        return
    
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    
    await event.reply(f"グループ ID: {group_id}, あなたの ID: {user_id}")
```

## メッセージ統計

### メッセージ数のカウント

> **注意**: 以下の例では、`sdk.storage.get/set` を使用して簡単なカウントを行っています。高並行なシナリオでは、原子性を保証するために `sdk.storage.transaction()` を使用することを推奨します。

```python
@message.on_message()
async def count_handler(event):
    # 統計の取得
    stats = sdk.storage.get("message_stats", {
        "total": 0,
        "by_user": {},
        "by_day": {}
    })
    
    # 統計の更新
    stats["total"] += 1
    
    user_id = event.get_user_id()
    stats["by_user"][user_id] = stats["by_user"].get(user_id, 0) + 1
    
    # 保存
    sdk.storage.set("message_stats", stats)

@command("stats", help="メッセージの統計を表示")
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
        f"{uid}: {count} 件のメッセージ" for uid, count in top_users
    )
    
    await event.reply(f"総メッセージ数: {stats['total']}\n\n活発なユーザー:\n{top_text}")
```

## 検索機能

### 簡単な検索

> **注意**：以下の例では、メッセージ履歴をメモリ内のリストに保存しています。**アプリケーションを再起動するとデータは失われます**。本番環境では、`sdk.storage` または SQLite テーブルを使用して永続化を推奨します。

```python
from ErisPulse.Core.Event import command, message

# メッセージ履歴を保存
message_history = []

@message.on_message()
async def store_handler(event):
    """検索用にメッセージを保存"""
    user_id = event.get_user_id()
    text = event.get_text()
    
    message_history.append({
        "user_id": user_id,
        "text": text,
        "time": event.get_time()
    })
    
    # 履歴記録数を制限
    if len(message_history) > 1000:
        message_history.pop(0)

@command("search", help="メッセージを検索")
async def search_handler(event):
    args = event.get_command_args()
    
    if not args:
        await event.reply("検索キーワードを入力してください")
        return
    
    keyword = " ".join(args)
    results = []
    
    # 履歴を検索
    for msg in message_history:
        if keyword in msg["text"]:
            results.append(msg)
    
    if not results:
        await event.reply("一致するメッセージが見つかりませんでした")
        return
    
    # 結果を表示
    result_text = f"{len(results)} 件の一致するメッセージが見つかりました:\n\n"
    for i, msg in enumerate(results[:10], 1):  # 最大 10 件表示
        result_text += f"{i}. {msg['text']}\n"
    
    await event.reply(result_text)
```

## 画像処理

### 画像のダウンロードと保存

```python
from ErisPulse.Core import client

@message.on_message()
async def image_handler(event):
    """画像メッセージを処理する"""
    message_segments = event.get_message()
    
    for segment in message_segments:
        if segment.get("type") == "image":
            file_url = segment.get("data", {}).get("file")
            
            if file_url:
                # SDK 内のクライアントを使用して画像をダウンロードすることを推奨します
                resp = await client.get(file_url)
                if resp.status == 200:
                    image_data = await resp.read()
                    
                    # ファイルに保存
                    filename = f"images/{event.get_time()}.jpg"
                    with open(filename, "wb") as f:
                        f.write(image_data)
                    
                    sdk.logger.info(f"画像を保存しました: {filename}")
                    await event.reply("画像を保存しました")
```

### 画像認識の例

> **注意**: 以下の例では占め API アドレスを使用しています。実際の使用時には、自分の画像認識サービスに置き換えてください。

```python
from ErisPulse.Core import client

@command("identify", help="画像を識別する")
async def identify_handler(event):
    """メッセージ中の画像を識別する"""
    message_segments = event.get_message()
    
    for segment in message_segments:
        if segment.get("type") == "image":
            file_url = segment.get("data", {}).get("file")
            
            # 画像認識 API を呼び出す
            result = await _identify_image(file_url)
            
            await event.reply(f"識別結果: {result}")
            return
    
    await event.reply("画像が見つかりません")

async def _identify_image(url):
    """画像認識 API を呼び出す（例）- SDK 内のクライアントを使用"""
    resp = await client.post(
        "https://api.example.com/identify",
        json={"url": url}
    )
    data = await resp.json()
    return data.get("description", "識別に失敗しました")
```

## 次のステップ

- [ユーザー使用ガイド](../user-guide/) - 設定とモジュール管理の方法を学ぶ
- [開発者ガイド](../developer-guide/) - モジュールやアダプターの開発方法を学ぶ
- [高度なトピック](../advanced/) - フレームワークの機能をさらに詳しく理解する