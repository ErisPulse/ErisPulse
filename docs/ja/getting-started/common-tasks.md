# 一般的タスクの例

> [!TIP]
> **このページを読むタイミング**：ロボットに特定の機能を追加したいときは、節ごとに参照してください。永続化、定期タスク、メッセージフィルタリング、権限制御、一括送信など、各節はそのままコピーできる完全な例です。イベント処理の書き方を体系的に学びたい場合は [イベント処理入門](event-handling.md) を先に見てください。必要なければ飛ばしてください。

## 目次

1. データの永続化
2. 定期タスク
3. メッセージのフィルタリング
4. プラットフォームの多様性対応
5. メッセージ送信の高度な機能（再試行/タイムアウト/一括送信）
6. 権限制御
7. メッセージ統計
8. 検索機能
9. 画像処理

## データの永続化

### 簡単なカウンター

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command

@command("count", help="コマンドの呼び出し回数を表示")
async def count_handler(event):
    # カウントを取得
    count = await sdk.storage.aget("command_count", 0)
    
    # カウントを増加
    count += 1
    await sdk.storage.aset("command_count", count)
    
    await event.reply(f"これは {count} 回目のコマンド呼び出しです")
```

### ユーザーのデータ保存

```python
@command("profile", help="プロフィールを表示")
async def profile_handler(event):
    user_id = event.get_user_id()
    
    # ユーザーのデータを取得
    user_data = await sdk.storage.aget(f"user:{user_id}", {
        "nickname": "",
        "join_date": None,
        "message_count": 0
    })
    
    profile_text = f"""
ニックネーム: {user_data['nickname']}
加入日: {user_data['join_date']}
メッセージ数: {user_data['message_count']}
    """
    
    await event.reply(profile_text.strip())

@command("setnick", help="ニックネームを設定")
async def setnick_handler(event):
    user_id = event.get_user_id()
    args = event.get_command_args()
    
    if not args:
        await event.reply("ニックネームを入力してください")
        return
    
    # ユーザーのデータを更新
    user_data = await sdk.storage.aget(f"user:{user_id}", {})
    user_data["nickname"] = " ".join(args)
    await sdk.storage.aset(f"user:{user_id}", user_data)
    
    await event.reply(f"ニックネームを{' '.join(args)}に設定しました")
```

## 定期タスク

### 簡単なタイマー

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command
import asyncio

class TimerModule:
    def __init__(self):
        self.sdk = sdk
        self._tasks = []
    
    async def on_load(self, event):
        """モジュールがロードされたときに定期タスクを開始"""
        self._start_timers()
        
        @command("timer", help="タイマー管理")
        async def timer_handler(event):
            await event.reply("タイマーが実行中です...")
    
    def _start_timers(self):
        """定期タスクを開始"""
        # 60秒ごとに実行
        task = asyncio.create_task(self._every_minute())
        self._tasks.append(task)
        
        # 毎日午前0時に実行
        task = asyncio.create_task(self._daily_task())
        self._tasks.append(task)
    
    async def _every_minute(self):
        """毎分実行されるタスク"""
        self.sdk.logger.info("毎分タスクが実行されました")
        # あなたのロジック...
    
    async def _daily_task(self):
        """毎日午前0時に実行されるタスク（注：UTC時間で計算されます。ローカル時間が必要な場合は、自分で調整してください）"""
        import time
        
        while True:
            # 午前0時までの時間を計算
            now = time.time()
            midnight = now + (86400 - now % 86400)
            
            await asyncio.sleep(midnight - now)
            
            # タスクを実行
            self.sdk.logger.info("毎日タスクが実行されました")
            # あなたのロジック...
```

### ライフサイクルイベントを使用

```python
@sdk.lifecycle.on("core.init.complete")
async def init_complete_handler(event_data):
    """SDKの初期化が完了した後に定期タスクを開始"""
    import asyncio
    
    async def daily_reminder():
        """毎日のリマインダー"""
        await asyncio.sleep(86400)  # 24時間
        sdk.logger.info("毎日タスクを実行")
    
    # バックグラウンドタスクを開始
    asyncio.create_task(daily_reminder())
```

## メッセージのフィルタリング

### キーワードフィルタリング

```python
from ErisPulse.Core.Event import message

blocked_words = ["スパム", "広告", "フィッシング"]

@message.on_message()
async def filter_handler(event):
    text = event.get_text()
    
    # 敏感語を含むかチェック
    for word in blocked_words:
        if word in text:
            sdk.logger.warning(f"スパムメッセージをブロック: {word}")
            return  # このメッセージを処理しない
    
    # 通常のメッセージを処理
    await event.reply(f"受信: {text}")
```

### ブラックリストフィルタリング

```python
# 設定ファイルやストレージからブラックリストをロード
blacklist = await sdk.storage.aget("user_blacklist", [])

@message.on_message()
async def blacklist_handler(event):
    user_id = event.get_user_id()
    
    if user_id in blacklist:
        sdk.logger.info(f"ブラックリストユーザー: {user_id}")
        return  # このメッセージを処理しない
    
    # 通常のメッセージを処理
    await event.reply(f"こんにちは、{user_id}")
```

## プラットフォームの多様性対応

### プラットフォーム固有の応答

```python
@command("help", help="ヘルプを表示")
async def help_handler(event):
    platform = event.get_platform()
    
    if platform == "yunhu":
        await event.reply("雲湖プラットフォームのヘルプ...")
    elif platform == "telegram":
        await event.reply("Telegram platform help...")
    elif platform == "onebot11":
        await event.reply("OneBot11 help...")
    else:
        await event.reply("一般的なヘルプ情報")
```

### プラットフォームの機能検出

```python
@command("rich", help="富文本メッセージを送信")
async def rich_handler(event):
    platform = event.get_platform()
    
    if platform == "yunhu":
        # 雲湖はHTMLをサポート
        yunhu = sdk.adapter.get("yunhu")
        await yunhu.Send.To("user", event.get_user_id()).Html(
            "<b>太字テキスト</b><i>斜体テキスト</i>"
        )
    elif platform == "telegram":
        # TelegramはMarkdownをサポート
        telegram = sdk.adapter.get("telegram")
        await telegram.Send.To("user", event.get_user_id()).Markdown(
            "**太字テキスト** *斜体テキスト*"
        )
    else:
        # 他のプラットフォームはプレーンテキストを使用
        await event.reply("太字テキスト 斜体テキスト")
```

## メッセージ送信の高度な機能（再試行/タイムアウト/一括送信）

`event.reply()` だけでなく、アダプタの Send DSL を使用して、失敗時の自動再試行、タイムアウト、成功後の処理、一括送信などのより複雑な送信シナリオを実現できます。

> 以下の例では、`event.get_detail_type()` と `event.get_target_id()` を使用して、イベントからターゲットの種類とIDを取得しています（グループチャットは自動的に group_id、プライベートチャットは user_id を取得）。ハードコードを避けるためです。

### 送信成功後に処理を実行

```python
@command("pay", help="支払いをシミュレート")
async def pay_handler(event):
    yunhu = sdk.adapter.get(event.get_platform())
    user_id = event.get_user_id()
    # 送信成功後にポイントを減算
    send_result = await (yunhu.Send.To(event.get_detail_type(), event.get_target_id())
                         .Text("支払い成功、10ポイントを減算しました"))
    if send_result:
        await sdk.storage.aset(f"points:{user_id}", -10)
```

### 失敗時の再試行 + タイムアウト

```python
@command("notice", help="重要な通知を送信")
async def notice_handler(event):
    adapter_inst = sdk.adapter.get(event.get_platform())
    # 最大3回再試行、各試行のタイムアウトは10秒
    task = (adapter_inst.Send.To(event.get_detail_type(), event.get_target_id())
            .Retry(3)
            .Timeout(10)
            .OnError(lambda ctx: sdk.logger.error(f"通知の送信に失敗しました: {ctx.error}"))
            .Text("これは重要な通知です"))
    # 待たずにバックグラウンドで送信
```

### 一括送信

一連のメッセージを送信し、一括で処理します：

```python
@command("announce", help="お知らせを送信")
async def announce_handler(event):
    adapter_inst = sdk.adapter.get(event.get_platform())
    # 複数のメッセージを作成し、一括で送信（デフォルトでは並列実行）
    results = await (adapter_inst.Send.To(event.get_detail_type(), event.get_target_id())
                    .Build()
                    .Text("📋 今日のお知らせ")
                    .Image("https://example.com/banner.jpg")
                    .Text("詳細は上記の画像をご覧ください")
                    .Retry(2)            # 失敗した項目は個別に再試行
                    .send_all())
    sdk.logger.info(f"一括送信完了、合計 {len(results)} 件")
```

> より詳細なルールと一括送信の説明は [プラットフォームの特性ガイド](../platform-guide/README.md#送信ルールデコレータ) を参照してください。

## 権限制御

### 管理者チェック

```python
# マスターユーザーのリストを設定
MASTERS = ["user123", "user456"]

def is_master(user_id):
    """フレームワークのマスターかチェック"""
    return user_id in MASTERS

@command("master", help="フレームワークマスター用のコマンド")
async def master_handler(event):
    user_id = event.get_user_id()
    
    if not is_master(user_id):
        await event.reply("権限がありません、このコマンドはフレームワークマスターのみ使用できます")
        return
    
    await event.reply("フレームワークマスター用のコマンドが正常に実行されました")

@command("addmaster", help="フレームワークマスターを追加")
async def addmaster_handler(event):
    if not is_master(event.get_user_id()):
        return
    
    args = event.get("text", "").split()
    if len(args) < 2:
        await event.reply("使い方: /addmaster <ユーザーID>")
        return
    
    new_master = args[0]
    MASTERS.append(new_master)
    await event.reply(f"フレームワークマスターを追加しました: {new_master}")
```

### グループの権限

```python
@command("groupinfo", help="グループ情報を表示")
async def groupinfo_handler(event):
    if not event.is_group_message():
        await event.reply("このコマンドはグループチャットでのみ使用できます")
        return
    
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    
    await event.reply(f"グループID: {group_id}, あなたのID: {user_id}")
```

## メッセージの統計

### メッセージのカウント

> **注意**：以下の例では `sdk.storage.get/set` を使用して単純なカウントを行っています。高負荷の状況では、`sdk.storage.transaction()` を使用して原子性を保証することをお勧めします。

```python
@message.on_message()
async def count_handler(event):
    # 統計を取得
    stats = await sdk.storage.aget("message_stats", {
        "total": 0,
        "by_user": {},
        "by_day": {}
    })
    
    # 統計を更新
    stats["total"] += 1
    
    user_id = event.get_user_id()
    stats["by_user"][user_id] = stats["by_user"].get(user_id, 0) + 1
    
    # 保存
    await sdk.storage.aset("message_stats", stats)

@command("stats", help="メッセージの統計を表示")
async def stats_handler(event):
    stats = await sdk.storage.aget("message_stats", {
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

> **注意**：以下の例ではメッセージ履歴をメモリ内のリストに保存しています。**アプリケーション再起動後はデータが失われます**。本番環境では、`sdk.storage` または SQLite テーブルを使用して永続化することをお勧めします。

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
    
    # 履歴の件数を制限
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
        await event.reply("一致するメッセージは見つかりませんでした")
        return
    
    # 結果を表示
    result_text = f"{len(results)} 件の一致するメッセージが見つかりました:\n\n"
    for i, msg in enumerate(results[:10], 1):  # 最大10件表示
        result_text += f"{i}. {msg['text']}\n"
    
    await event.reply(result_text)
```

## 画像処理

### 画像のダウンロードと保存

```python
from ErisPulse.Core import client

@message.on_message()
async def image_handler(event):
    """画像メッセージを処理"""
    message_segments = event.get_message()
    
    for segment in message_segments:
        if segment.get("type") == "image":
            file_url = segment.get("data", {}).get("file")
            
            if file_url:
                # SDKの内蔵クライアントを使用して画像をダウンロードすることを推奨
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

> **注意**：以下の例では、プレースホルダのAPIアドレスを使用しています。実際の使用では、独自の画像認識サービスに置き換えてください。

```python
from ErisPulse.Core import client

@command("identify", help="画像を認識")
async def identify_handler(event):
    """メッセージ内の画像を認識"""
    message_segments = event.get_message()
    
    for segment in message_segments:
        if segment.get("type") == "image":
            file_url = segment.get("data", {}).get("file")
            
            # 画像認識APIを呼び出す
            result = await _identify_image(file_url)
            
            await event.reply(f"認識結果: {result}")
            return
    
    await event.reply("画像が見つかりませんでした")

async def _identify_image(url):
    """画像認識APIを呼び出す（例）- SDKの内蔵クライアントを使用"""
    resp = await client.post(
        "https://api.example.com/identify",
        json={"url": url}
    )
    data = await resp.json()
    return data.get("description", "認識に失敗しました")
```

## 次のステップ

- **機能を実装した後、長期間実行したい**：[デプロイガイド](../user-guide/deployment.md) を参照し、Docker / systemd による守護プロセスとバックアップ・アップグレードについて確認してください。
- **実装した機能を他の人に配布したい**：[モジュール開発入門](../developer-guide/modules/getting-started.md) から始め、スクリプトをインストール可能なモジュールにアップグレードしてください。
- **設定を調整したり、「モジュールが反応しない」問題をトラブルシューティングしたい**：[設定ファイルの説明](../user-guide/configuration.md) と [スコープ](../advanced/scope.md) を確認してください。