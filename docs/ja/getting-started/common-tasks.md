# よくあるタスクの例

このガイドは、一般的な機能の実装例を提供し、一般的な機能を素早く実装するのに役立ちます。

## 内容リスト

1. データ永続化
2. 定期タスク
3. メッセージフィルタリング
4. マルチプラットフォーム対応
5. メッセージ送信（リトライ/タイムアウト/一括）
6. 権限管理
7. メッセージ統計
8. 検索機能
9. 画像処理

## データ永続化

### シンプルなカウンター

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command

@command("count", help="コマンド呼び出し回数を表示")
async def count_handler(event):
    # カウントを取得
    count = sdk.storage.get("command_count", 0)
    
    # カウントを増やす
    count += 1
    sdk.storage.set("command_count", count)
    
    await event.reply(f"これは {count} 回目のコマンド呼び出しです")
```

### ユーザーデータの保存

```python
@command("profile", help="プロフィールを表示")
async def profile_handler(event):
    user_id = event.get_user_id()
    
    # ユーザーデータを取得
    user_data = sdk.storage.get(f"user:{user_id}", {
        "nickname": "",
        "join_date": None,
        "message_count": 0
    })
    
    profile_text = f"""
ニックネーム: {user_data['nickname']}
参加日: {user_data['join_date']}
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
    
    # ユーザーデータを更新
    user_data = sdk.storage.get(f"user:{user_id}", {})
    user_data["nickname"] = " ".join(args)
    sdk.storage.set(f"user:{user_id}", user_data)
    
    await event.reply(f"ニックネームが設定されました: {' '.join(args)}")
```

## 定期タスク

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
        """モジュール読み込み時にタイマータスクを開始"""
        self._start_timers()
        
        @command("timer", help="タイマー管理")
        async def timer_handler(event):
            await event.reply("タイマーは実行中です...")
    
    def _start_timers(self):
        """定期タスクを開始"""
        # 60 秒ごとに実行
        task = asyncio.create_task(self._every_minute())
        self._tasks.append(task)
        
        # 毎日午前中に実行
        task = asyncio.create_task(self._daily_task())
        self._tasks.append(task)
    
    async def _every_minute(self):
        """1 分ごとに実行するタスク"""
        self.sdk.logger.info("1 分ごとのタスク実行")
        # あなたのロジック...
    
    async def _daily_task(self):
        """毎日午前中に実行するタスク（注：UTC 時間ベースで計算されます。ローカル時間を使用する場合は調整してください）"""
        import time
        
        while True:
            # 午前中までの時間を計算
            now = time.time()
            midnight = now + (86400 - now % 86400)
            
            await asyncio.sleep(midnight - now)
            
            # タスクを実行
            self.sdk.logger.info("毎日のタスク実行")
            # あなたのロジック...
```

### ライフサイクルイベントの使用

```python
@sdk.lifecycle.on("core.init.complete")
async def init_complete_handler(event_data):
    """SDK 初期化完了後にタイマータスクを開始"""
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
    
    # 敏感単語が含まれているかチェック
    for word in blocked_words:
        if word in text:
            sdk.logger.warning(f"機密メッセージをブロックしました: {word}")
            return  # このメッセージを処理しない
    
    # メッセージを通常処理
    await event.reply(f"受信しました: {text}")
```

### ブラックリストフィルタリング

```python
# 設定またはストレージからブラックリストを読み込む
blacklist = sdk.storage.get("user_blacklist", [])

@message.on_message()
async def blacklist_handler(event):
    user_id = event.get_user_id()
    
    if user_id in blacklist:
        sdk.logger.info(f"ブラックリストユーザー: {user_id}")
        return  # 処理しない
    
    # 通常処理
    await event.reply(f"こんにちは、{user_id}")
```

## マルチプラットフォーム対応

### プラットフォーム固有の応答

```python
@command("help", help="ヘルプを表示")
async def help_handler(event):
    platform = event.get_platform()
    
    if platform == "yunhu":
        await event.reply("Yunhu プラットフォームヘルプ...")
    elif platform == "telegram":
        await event.reply("Telegram platform help...")
    elif platform == "onebot11":
        await event.reply("OneBot11 help...")
    else:
        await event.reply("一般的なヘルプ情報")
```

### プラットフォーム機能の検出

```python
@command("rich", help="リッチテキストメッセージを送信")
async def rich_handler(event):
    platform = event.get_platform()
    
    if platform == "yunhu":
        # Yunhu は HTML をサポート
        yunhu = sdk.adapter.get("yunhu")
        await yunhu.Send.To("user", event.get_user_id()).Html(
            "<b>太字テキスト</b><i>斜体テキスト</i>"
        )
    elif platform == "telegram":
        # Telegram は Markdown をサポート
        telegram = sdk.adapter.get("telegram")
        await telegram.Send.To("user", event.get_user_id()).Markdown(
            "**太字テキスト** *斜体テキスト*"
        )
    else:
        # 他のプラットフォームはプレーンテキストを使用
        await event.reply("太字テキスト 斜体テキスト")
```

## メッセージ送信（リトライ/タイムアウト/一括）

単純な `event.reply()` に加えて、アダプタの Send DSL を使用して、より複雑な送信シナリオ（失敗時の自動リトライ、タイムアウトによるキャンセル、成功後のロジック実行、複数メッセージの一括送信）を実装できます。

> 以下の例では、`event.get_detail_type()` と `event.get_target_id()` を使用してイベントからターゲットタイプと ID を取得します（グループチャットの場合は `group_id`、プライベートチャットの場合は `user_id` を自動的に取得し、ハードコーディングを回避します）。

### 送信成功後にロジックを実行

```python
@command("pay", help="シミュレーション支払い")
async def pay_handler(event):
    yunhu = sdk.adapter.get(event.get_platform())
    user_id = event.get_user_id()
    # 送信成功後にのみポイントを減らす
    await (yunhu.Send.To(event.get_detail_type(), event.get_target_id())
           .Hook(lambda r: sdk.storage.set(f"points:{user_id}", -10))
           .Text("支払い成功、10 ポイントを差し引きました"))
```

### 失敗時のリトライ + タイムアウトキャンセル

```python
@command("notice", help="重要な通知を送信")
async def notice_handler(event):
    adapter_inst = sdk.adapter.get(event.get_platform())
    # 最大 3 回リトライ、各回 10 秒タイムアウト
    task = (adapter_inst.Send.To(event.get_detail_type(), event.get_target_id())
            .Retry(3)
            .Timeout(10)
            .OnError(lambda ctx: sdk.logger.error(f"通知送信失敗: {ctx.error}"))
            .Text("これは重要な通知です"))
    # 待たず、バックグラウンドで送信
```

### 複数メッセージの一括送信

1 つのチェーンで複数メッセージを送信し、一括で実行します：

```python
@command("announce", help="お知らせを送信")
async def announce_handler(event):
    adapter_inst = sdk.adapter.get(event.get_platform())
    # 複数メッセージを構築し、一括で送信（デフォルトで並列実行）
    results = await (adapter_inst.Send.To(event.get_detail_type(), event.get_target_id())
                    .Build()
                    .Text("📋 本日のお知らせ")
                    .Image("https://example.com/banner.jpg")
                    .Text("詳細は上の画像をご覧ください")
                    .Retry(2)            # 失敗した項目ごとにリトライ
                    .send_all())
    sdk.logger.info(f"一括送信完了、合計 {len(results)} 件")
```

> より詳細なルールと一括送信の説明については、[プラットフォーム機能ガイド](../platform-guide/README.md#送信ルールデコレータ) を参照してください。

## 権限管理

### 管理者チェック

```python
# 管理者リストを設定
ADMINS = ["user123", "user456"]

def is_admin(user_id):
    """管理者かどうかをチェック"""
    return user_id in ADMINS

@command("admin", help="管理者コマンド")
async def admin_handler(event):
    user_id = event.get_user_id()
    
    if not is_admin(user_id):
        await event.reply("権限が不十分です。このコマンドは管理者のみ使用可能です")
        return
    
    await event.reply("管理者コマンドが正常に実行されました")

@command("addadmin", help="管理者を追加")
async def addadmin_handler(event):
    if not is_admin(event.get_user_id()):
        return
    
    args = event.get_command_args()
    if not args:
        await event.reply("追加する管理者 ID を入力してください")
        return
    
    new_admin = args[0]
    ADMINS.append(new_admin)
    await event.reply(f"管理者を追加しました: {new_admin}")
```

### グループ権限

```python
@command("groupinfo", help="グループ情報を表示")
async def groupinfo_handler(event):
    if not event.is_group_message():
        await event.reply("このコマンドはグループチャットでのみ使用できます")
        return
    
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    
    await event.reply(f"グループ ID: {group_id}, 自分の ID: {user_id}")
```

## メッセージ統計

### メッセージカウント

> **注意**: 以下の例は、`sdk.storage.get/set` を使用して単純なカウントを行っています。高並列シナリオでは、`sdk.storage.transaction()` を使用して原子性を保証することを推奨します。

```python
@message.on_message()
async def count_handler(event):
    # 統計を取得
    stats = sdk.storage.get("message_stats", {
        "total": 0,
        "by_user": {},
        "by_day": {}
    })
    
    # 統計を更新
    stats["total"] += 1
    
    user_id = event.get_user_id()
    stats["by_user"][user_id] = stats["by_user"].get(user_id, 0) + 1
    
    # 保存
    sdk.storage.set("message_stats", stats)

@command("stats", help="メッセージ統計を表示")
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
        f"{uid}: {count} 通のメッセージ" for uid, count in top_users
    )
    
    await event.reply(f"総メッセージ数: {stats['total']}\n\nアクティブユーザー:\n{top_text}")
```

## 検索機能

### シンプルな検索

> **注意**: 以下の例では、メッセージ履歴をメモリリストで保存しています。**プログラムの再起動後にデータが失われます**。本番環境では、`sdk.storage` または SQLite テーブルを使用して永続化ストレージすることを推奨します。

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
    
    # 履歴の数を制限
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
    """画像メッセージを処理"""
    message_segments = event.get_message()
    
    for segment in message_segments:
        if segment.get("type") == "image":
            file_url = segment.get("data", {}).get("file")
            
            if file_url:
                # SDK 内蔵クライアントを使用した画像ダウンロードを推奨
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

### 画像識別の例

> **注意**: 以下の例ではプレースホルダ API アドレスを使用しています。実際の使用時は、自分の画像識別サービスに置き換えてください。

```python
from ErisPulse.Core import client

@command("identify", help="画像を識別")
async def identify_handler(event):
    """メッセージ内の画像を識別"""
    message_segments = event.get_message()
    
    for segment in message_segments:
        if segment.get("type") == "image":
            file_url = segment.get("data", {}).get("file")
            
            # 画像識別 API を呼び出す
            result = await _identify_image(file_url)
            
            await event.reply(f"識別結果: {result}")
            return
    
    await event.reply("画像が見つかりません")

async def _identify_image(url):
    """画像識別 API を呼び出す（例）- SDK 内蔵クライアントを使用"""
    resp = await client.post(
        "https://api.example.com/identify",
        json={"url": url}
    )
    data = await resp.json()
    return data.get("description", "識別に失敗しました")
```

## 次のステップ

- [ユーザーガイド](../user-guide/) - 設定とモジュール管理を理解する
- [開発者ガイド](../developer-guide/) - モジュールとアダプタの開発を学ぶ
- [高度なトピック](../advanced/) - フレームワークの機能について詳しく学ぶ