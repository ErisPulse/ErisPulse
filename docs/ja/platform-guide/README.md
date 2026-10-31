# ErisPulse PlatformFeatures ドキュメント

> 基準プロトコル：[OneBot12](https://12.onebot.dev/) 
> 
> 本ドキュメントは**プラットフォーム固有機能ガイド**であり、以下の内容を含みます：
> - 各アダプターが対応するSendメソッドの連鎖呼び出し（チェーン呼び出し）例
> - プラットフォーム固有のイベント/メッセージ形式の説明
> 
> 一般的な使用方法については以下を参照してください：
> - [基本概念](../getting-started/basic-concepts.md)
> - [イベント変換標準](../standards/event-conversion.md)  
> - [APIレスポンス仕様](../standards/api-response.md)

---

## プラットフォーム固有機能

このセクションは各アダプター開発者によって保守されており、そのアダプターとOneBot12標準との差分および拡張機能について説明するものです。以下の各プラットフォームの詳細ドキュメントを参照してください：

- [メンテナンスガイド](maintain-notes.md)

- [Yunhuプラットフォーム特性](yunhu.md)
- [Yunhuユーザープラットフォーム特性](yunhu_user.md)
- [Telegramプラットフォーム特性](telegram.md)
- [OneBot11プラットフォーム特性](onebot11.md)
- [OneBot12プラットフォーム特性](onebot12.md)
- [SnowLumaプラットフォーム特性](snowluma.md)
- [メールプラットフォーム特性](email.md)
- [Kookプラットフォーム特性](kook.md)
- [Matrixプラットフォーム特性](matrix.md)
- [WeCom（企業向けWeChat）プラットフォーム特性](wecom.md)
- [Bilibili プラットフォーム特性](bilibili.md)
- [Minecraft プラットフォーム特性](minecraft.md)
- [QQ公式ボットプラットフォーム特性](qqbot.md)
- [花楓珈琲館](ideaura.md)
- [Discord](discord.md)
- [Webhookプロトコルブリッジ](webhook.md)
- [WeChat公式アカウント](wechatmp.md)

> また `sandbox` アダプターもありますが、このアダプターにはプラットフォーム特性ドキュメントの保守は不要です

---

## 共通インターフェース

### Send 連鎖呼び出し
すべてのアダプターが以下の標準的な呼び出し方法に対応しています：

> **注意：** ドキュメント内の `{AdapterName}` は実際のアダプター名（例： `yunhu`、`telegram`、`onebot11`、`email` など）に置き換えてください。

1. タイプとIDを指定： `To(type,id).Func()`
   ```python
   # アダプターインスタンスの取得
   my_adapter = adapter.get("{AdapterName}")
   
   # メッセージの送信
   await my_adapter.Send.To("user", "U1001").Text("Hello")
   
   # 例：
   yunhu = adapter.get("yunhu")
   await yunhu.Send.To("user", "U1001").Text("Hello")
   ```
2. IDのみ指定： `To(id).Func()`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.To("U1001").Text("Hello")
   
   # 例：
   telegram = adapter.get("telegram")
   await telegram.Send.To("U1001").Text("Hello")
   ```
3. 送信アカウントを指定： `Using(account_id)`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.Using("bot1").To("U1001").Text("Hello")
   
   # 例：
   onebot11 = adapter.get("onebot11")
   await onebot11.Send.Using("bot1").To("U1001").Text("Hello")
   ```
4. 直接呼び出し： `Func()`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.Text("Broadcast message")
   
   # 例：
   email = adapter.get("email")
   await email.Send.Text("Broadcast message")
   ```

#### 非同期送信と結果処理

Send DSLのメソッドは `asyncio.Task` オブジェクトを返します。つまり、結果をすぐに待つかどうかを選択できます：

```python
# アダプターインスタンスの取得
my_adapter = adapter.get("{AdapterName}")

# 結果を待たずに、メッセージをバックグラウンドで送信
task = my_adapter.Send.To("user", "123").Text("Hello")

# 送信結果を取得する必要がある場合は、後から待機できます
result = await task
```

#### 送信ルールデコレーター

実際の開発では、送信成功後に後続のロジックを実行する、失敗時に自動リトライ、タイムアウト取消、送信進捗の監視などが必要になることがよくあります。Send DSLには送信ルールデコレーターが組み込まれており、連鎖メソッドを通じてルールを追加できます：

| メソッド | 説明 |
|--------|------|
| `.Hook(callback)` | 送信成功後に実行されるコールバック（複数回呼び出し可能） |
| `.Retry(times=1)` | 失敗時に自動でN回リトライ（初回を含め計N+1回） |
| `.Timeout(seconds)` | 単回送信のタイムアウト、超過で取消（Retryと併用可） |
| `.Defer(seconds)` | 送信を遅延（プロセス内タイマー、永続化なし） |
| `.OnProgress(callback)` | 各段階の進捗コールバック、SendContextを渡す |
| `.OnError(callback)` | 最終失敗時のエラーコールバック（一度のみ発火） |

```python
yunhu = adapter.get("yunhu")

# 送信成功後にポイントを減算
await (yunhu.Send.To("user", "123")
       .Hook(lambda r: deduct_points("123"))
       .Text("消費が完了しました"))

# 失敗時リトライ + タイムアウト取消 + 進捗監視
def on_progress(ctx):
    print(f"段階: {ctx.stage}, 試行: {ctx.attempt + 1}/{ctx.max_attempts}")

task = (yunhu.Send.To("user", "123")
        .Retry(3)              # 最大3回リトライ
        .Timeout(10)           # 毎回10秒でタイムアウト
        .OnProgress(on_progress)
        .OnError(lambda ctx: notify_admin(ctx.error))
        .Text("重要なお知らせ"))
```

ルールメソッドは `self` を返すため、送信メソッド（Text/Imageなど）の前に呼び出す必要があります。`SendContext` には `stage`（pending/sending/retrying/success/failed/timeout）、`attempt`、`elapsed`、`error`、`result` などのフィールドが含まれ、監視に便利です。

#### 一括構築モード（Build）

1つのチェーン内で複数の送信メソッドを構築し、最後に一括実行します。「一度に複数のメッセージを送る」シナリオに適しています：

```python
yunhu = adapter.get("yunhu")

# 複数のメッセージを構築し、一括送信
results = await (yunhu.Send.To("user", "123")
                .Build()                     # ビルドモードに入る
                .Text("通知1")
                .Image("pic.jpg")
                .Text("通知2")
                .send_all())                 # 一括実行
# results = [Text結果, Image結果, Text結果]
```

`.send_all()` はデフォルトで**並列**実行されます（同時送信で効率が高い）。メッセージの到着順序を保証する必要がある場合は、`.Sequential()` を呼び出して逐次実行します：

```python
# 逐次実行（順序保証）+ 失敗時リトライ
await (yunhu.Send.To("group", "456")
       .Build()
       .Sequential()                # 順番に送信
       .Retry(2)                     # 失敗した項目はそれぞれリトライ
       .Text("1つ目のメッセージ").Text("2つ目のメッセージ")
       .send_all())
```

一括実行は**失敗継続**ポリシーを採用しています：ある項目が失敗しても他の項目は中断されず、失敗した項目は自動的にリトライされます。一括実行でもバッチ全体の `Hook`（全成功後に発火）、`OnError`（失敗があると発火）、`OnProgress`（進捗コールバック）に対応しています。

> より詳細なルールと一括構築の説明については、[SendDSL 詳解](../developer-guide/adapters/send-dsl.md) を参照してください。

### イベントリスニング
イベントのリスニング方法は3種類あります：

1. プラットフォームネイティブイベントのリスニング：
   ```python
   from ErisPulse.Core import adapter, logger
   
   @adapter.on("event_type", raw=True, platform="{AdapterName}")
   async def handler(data):
       logger.info(f"{AdapterName}のネイティブイベントを受信: {data}")
   ```

2. OneBot12標準イベントのリスニング：
   ```python
   from ErisPulse.Core import adapter, logger

   # OneBot12標準イベントをリッスン
   @adapter.on("event_type")
   async def handler(data):
       logger.info(f"標準イベントを受信: {data}")

   # 特定プラットフォームの標準イベントをリッスン
   @adapter.on("event_type", platform="{AdapterName}")
   async def handler(data):
       logger.info(f"{AdapterName}の標準イベントを受信: {data}")
   ```

3. Eventモジュールによるリスニング：
    `Event`のイベントは `adapter.on()` 関数をベースとしているため、`Event`が提供するイベント形式はOneBot12標準イベントです

    ```python
    from ErisPulse.Core.Event import message, notice, request, command

    message.on_message()(message_handler)
    notice.on_notice()(notice_handler)
    request.on_request()(request_handler)
    command("hello", help="挨拶メッセージを送信", usage="hello")(command_handler)

    async def message_handler(event):
        logger.info(f"メッセージを受信: {event}")
    async def notice_handler(event):
        logger.info(f"通知を受信: {event}")
    async def request_handler(event):
        logger.info(f"リクエストを受信: {event}")
    async def command_handler(event):
        logger.info(f"コマンドを受信: {event}")
    ```

中でも最も推奨されるのは `Event` モジュールを使用したイベント処理です。`Event` モジュールは豊富なイベントタイプと豊富なイベント処理メソッドを提供しているためです。

---

## 標準形式
参考用として、ここでは簡単なイベント形式を示します。詳細情報が必要な場合は、上記のリンクを参照してください。

> **注意：** 以下の形式は基本的なOneBot12標準形式であり、各アダプターはこのベースに拡張フィールドを追加している場合があります。詳細は各アダプターの固有機能説明を参照してください。

### 標準イベント形式
すべてのアダプターが実装しなければならないイベント変換形式：
```json
{
  "id": "event_123",
  "time": 1752241220,
  "type": "message",
  "detail_type": "group",
  "platform": "example_platform",
  "self": {"platform": "example_platform", "user_id": "bot_123"},
  "message_id": "msg_abc",
  "message": [
    {"type": "text", "data": {"text": "こんにちは"}}
  ],
  "alt_message": "こんにちは",
  "user_id": "user_456",
  "user_nickname": "ExampleUser",
  "group_id": "group_789"
}
```

### 標準レスポンス形式
#### メッセージ送信成功
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
  "{platform}_raw": {...}
}
```

#### メッセージ送信失敗
```json
{
  "status": "failed",
  "retcode": 10003,
  "data": null,
  "message_id": "",
  "message": "必要なパラメータが不足しています",
  "echo": "1234",
  "{platform}_raw": {...}
}
```

---

## 参考リンク
ErisPulse プロジェクト：
- [メインリポジトリ](https://github.com/ErisPulse/ErisPulse/)
- [Yunhu アダプターリポジトリ](https://github.com/ErisPulse/ErisPulse-YunhuAdapter)
- [Telegram アダプターリポジトリ](https://github.com/ErisPulse/ErisPulse-TelegramAdapter)
- [OneBot アダプターリポジトリ](https://github.com/ErisPulse/ErisPulse-OneBotAdapter)

関連公式ドキュメント：
- [OneBot V11 プロトコルドキュメント](https://github.com/botuniverse/onebot-11)
- [Telegram Bot API 公式ドキュメント](https://core.telegram.org/bots/api)
- [Yunhu公式ドキュメント](https://www.yhchat.com/document/1-3)

## コントリビューション

より多くの開発者にアダプタードキュメントの執筆と保守への参加をご案内しています！以下の手順に従ってコントリビューションを提出してください：
1. [ErisPuls](https://github.com/ErisPulse/ErisPulse) リポジトリをForkします。
2. `docs/platform-features/` ディレクトリにMarkdownファイルを作成し、`<プラットフォーム名>.md` の形式で命名します。
3. この `README.md` ファイルに、ご自身が貢献したアダプターへのリンクおよび関連公式ドキュメントを追加します。
4. Pull Request を提出します。

ご支援ありがとうございます！