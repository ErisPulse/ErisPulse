# よくあるタスクの例

このガイドでは、一般的な機能の実装例を提供し、一般的な機能を迅速に実装するのに役立ちます。

## 内容一覧

1. データの永続化
2. タイマージョブ
3. メッセージのフィルタリング
4. マルチプラットフォーム対応
5. メッセージ送信の応用（再試行/タイムアウト/バッチ）
6. アクセス制御
7. メッセージ統計
8. 検索機能
9. 画像処理

## データの永続化

### シンプルなカウンタ

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command

@command("count", help="コマンド呼び出し回数を表示")
async def count_handler(event):
    # カウントを取得
    count = sdk.storage.get("command_count", 0)
    
    # カウントを増加
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

## タイマージョブ

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
        """モジュールのロード時にタイマージョブを開始"""
        self._start_timers()
        
        @command("timer", help="タイマー管理")
        async def timer_handler(event):
            await event.reply("タイマーが稼働中...")
    
    def _start_timers(self):
        """タイマージョブを開始"""
        # 60秒ごとに実行
        task = asyncio.create_task(self._every_minute())
        self._tasks.append(task)
        
        # 毎日深夜に実行
        task = asyncio.create_task(self._daily_task())
        self._tasks.append(task)
    
    async def _every_minute(self):
        """毎分実行するジョブ"""
        self.sdk.logger.info("毎分ジョブ実行")
        # あなたのロジック...
    
    async def _daily_task(self):
        """毎日深夜に実行するジョブ（注：UTC時間ベースで計算されます。ローカル時間が必要な場合は独自に調整してください）"""
        import time
        
        while True:
            # 深夜までの時間を計算
            now = time.time()
            midnight = now + (86400 - now % 86400)
            
            await asyncio.sleep(midnight - now)
            
            # ジョブを実行
            self.sdk.logger.info("毎日ジョブ実行")
            # あなたのロジック...
```

### ライフサイクルイベントの使用

```python
@sdk.lifecycle.on("core.init.complete")
async def init_complete_handler(event_data):
    """SDKの初期化完了後にタイマージョブを開始"""
    import asyncio
    
    async def daily_reminder():
        """毎日のリマインダー"""
        await asyncio.sleep(86400)  # 24時間
        sdk.logger.info("毎日のジョブを実行")
    
    # バックグラウンドジョブを開始
    asyncio.create_task(daily_reminder())
```

## メッセージのフィルタリング

### キーワードフィルタリング

```python
from ErisPulse.Core.Event import message

blocked_words = ["ゴミ", "広告", "フィッシング"]

@message.on_message()
async def filter_handler(event):
    text = event.get_text()
    
    # 敏感ワードが含まれているかチェック
    for word in blocked_words:
        if word in text:
            sdk.logger.warning(f"敏感メッセージをブロック: {word}")
            return  # このメッセージを処理しない
    
    # メッセージを通常通り処理
    await event.reply(f"受信: {text}")
```

### ブラックリストフィルタリング

```python
# 設定またはストレージからブラックリストをロード
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
        await event.reply("Yunhuプラットフォームのヘルプ...")
    elif platform == "telegram":
        await event.reply("Telegram platform help...")
    elif platform == "onebot11":
        await event.reply("OneBot11 help...")
    else:
        await event.reply("共通のヘルプ情報")
```

### プラットフォーム機能の検出

```python
@command("rich", help="リッチテキストメッセージを送信")
async def rich_handler(event):
    platform = event.get_platform()
    
    if platform == "yunhu":
        # YunhuはHTMLをサポート
        yunhu = sdk.adapter.get("yunhu")
        await yunhu.Send.To("user", event.get_user_id()).Html(
            "<b>太字</b><i>斜体</i>"
        )
    elif platform == "telegram":
        # TelegramはMarkdownをサポート
        telegram = sdk.adapter.get("telegram")
        await telegram.Send.To("user", event.get_user_id()).Markdown(
            "**太字** *斜体*"
        )
    else:
        # 他のプラットフォームはプレーンテキストを使用
        await event.reply("太字 斜体")
```

## メッセージ送信の応用（再試行/タイムアウト/バッチ）

シンプルな `event.reply()` 以外に、アダプタの Send DSL を通じてより複雑な送信シナリオを実装できます：失敗時の自動再試行、タイムアウトによるキャンセル、成功時のロジック実行、複数メッセージのバッチ送信。

> 以下の例では、`event.get_detail_type()` と `event.get_target_id()` を使用してイベントからターゲットのタイプとIDを取得（グループチャットでは自動的に group_id を取得、DMでは自動的に user_id を取得）、ハードコーディングを回避しています。

### 送信成功後のロジック実行

```python
@command("pay", help="シミュレーション決済")
async def pay_handler(event):
    yunhu = sdk.adapter.get(event.get_platform())
    user_id = event.get_user_id()
    # 送信成功後にのみポイントを減らす
    await (yunhu.Send.To(event.get_detail_type(), event.get_target_id())
           .Hook(lambda r: sdk.storage.set(f"points:{user_id}", -10))
           .Text("決済完了しました。10ポイントを差し引きました"))
```

### 失敗再試行 + タイムアウトキャンセル

```python
@command("notice", help="重要な通知を送信")
async def notice_handler(event):
    adapter_inst = sdk.adapter.get(event.get_platform())
    # 最大3回再試行、それぞれのタイムアウトは10秒
    task = (adapter_inst.Send.To(event.get_detail_type(), event.get_target_id())
            .Retry(3)
            .Timeout(10)
            .OnError(lambda ctx: sdk.logger.error(f"通知送信失敗: {ctx.error}"))
            .Text("これは重要な通知です"))
    # 待機しない、バックグラウンドで送信
```

### 複数メッセージのバッチ送信

一つのチェーンで複数のメッセージを送信し、統一して実行します：

```python
@command("announce", help="告知を送信")
async def announce_handler(event):
    adapter_inst = sdk.adapter.get(event.get_platform())
    # 複数のメッセージを構築し、一括で送信（デフォルトで並列実行）
    results = await (adapter_inst.Send.To(event.get_detail_type(), event.get_target_id())
                    .Build()
                    .Text("📋 今日の告知")
                    .Image("https://example.com/banner.jpg")
                    .Text("詳細内容は画像を参照してください")
                    .Retry(2)            # 失敗した項目は個別に再試行
                    .send_all())
    sdk.logger.info(f"バッチ送信完了、合計 {len(results)} 件")
```

> より完全なルールとバッチの説明については [プラットフォーム機能ガイド](../platform-guide/README.md#送信ルールデコレータ) を参照してください。

## アクセス制御

### 管理者チェック

```python
# マスターのリストを設定
MASTERS = ["user123", "user456"]

def is_master(user_id):
    """フレームワークのマスターかどうかを確認"""
    return user_id in MASTERS

@command("master", help="フレームワークマスターのコマンド")
async def master_handler(event):
    user_id = event.get_user_id()
    
    if not is_master(user_id):
        await event.reply("権限が不十分です。このコマンドはフレームワークマスターのみ使用可能です")
        return
    
    await event.reply("フレームワークマスターのコマンドが正常に実行されました")

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

### グループ権限

```python
@command("groupinfo", help="グループ情報を表示")
async def groupinfo_handler(event):
    if not event.is_group_message():
        await event.reply("このコマンドはグループチャットでのみ使用できます")
        return
    
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    
    await event.reply(f"グループID: {group_id}, 自分のID: {user_id}")
```

## メッセージ統計

### メッセージカウント

> **注意**: 以下の例では `sdk.storage.get/set` を使用して単純なカウントを行っています。高並列なシナリオでは、一貫性を保つために `sdk.storage.transaction()` を使用することを推奨します。

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
        f"{uid}: {count} 件のメッセージ" for uid, count in top_users
    )
    
    await event.reply(f"総メッセージ数: {stats['total']}\n\nアクティブユーザー:\n{top_text}")
```

## 検索機能

### シンプルな検索

> **注意**: 以下の例はメモリ上のリストを使用してメッセージ履歴を保存しており、**プログラム再起動後はデータが失われます**。本番環境では `sdk.storage` または SQLite テーブルを使用して永続化ストレージすることを推奨します。

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
        await event.reply("一致するメッセージが見つかりません")
        return
    
    # 結果を表示
    result_text = f"{len(results)} 件の一致するメッセージが見つかりました:\n\n"
    for i, msg in enumerate(results[:10], 1):  # 最大10件まで表示
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
                # SDKの組み込みクライアントを使用して画像をダウンロードすることを推奨します
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

> **注意**: 以下の例ではプレースホルダAPIアドレスを使用しています。実際に使用する際は、ご自身の画像認識サービスに置き換えてください。

```python
from ErisPulse.Core import client

@command("identify", help="画像を識別")
async def identify_handler(event):
    """メッセージ内の画像を識別"""
    message_segments = event.get_message()
    
    for segment in message_segments:
        if segment.get("type") == "image":
            file_url = segment.get("data", {}).get("file")
            
            # 画像認識APIを呼び出し
            result = await _identify_image(file_url)
            
            await event.reply(f"識別結果: {result}")
            return
    
    await event.reply("画像が見つかりません")

async def _identify_image(url):
    """画像認識APIを呼び出す（例） - SDKの組み込みクライアントを使用"""
    resp = await client.post(
        "https://api.example.com/identify",
        json={"url": url}
    )
    data = await resp.json()
    return data.get("description", "識別に失敗しました")
```

## 次のステップ

- [ユーザーガイド](../user-guide/) - 設定とモジュール管理について
- [開発者ガイド](../developer-guide/) - モジュールとアダプターの開発について
- [高度なトピック](../advanced/) - フレームワークの機能について詳しく
