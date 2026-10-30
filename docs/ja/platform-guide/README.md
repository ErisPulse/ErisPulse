# ErisPulse PlatformFeatures ドキュメント

> 基準プロトコル: [OneBot12](https://12.onebot.dev/)  
> 本文書は**プラットフォーム固有の機能ガイド**であり、以下を含む：
> - 各アダプタがサポートするSendメソッドの連鎖呼び出し例
> - プラットフォーム固有のイベント/メッセージフォーマットの説明
> 
> 一般的な使用方法は以下のドキュメントを参照してください：
> - [基本概念](../getting-started/basic-concepts.md)
> - [イベント変換基準](../standards/event-conversion.md)  
> - [APIレスポンス規格](../standards/api-response.md)

---

## プラットフォーム固有機能

このセクションは各アダプター開発者によって管理されており、そのアダプターと OneBot12 標準との差異および拡張機能について説明します。各プラットフォームの詳細なドキュメントは以下をご参照ください：

- [メンテナンスガイド](maintain-notes.md)

- [雲湖プラットフォーム特性](yunhu.md)
- [雲湖ユーザープラットフォーム特性](yunhu_user.md)
- [Telegramプラットフォーム特性](telegram.md)
- [OneBot11プラットフォーム特性](onebot11.md)
- [OneBot12プラットフォーム特性](onebot12.md)
- [SnowLumaプラットフォーム特性](snowluma.md)
- [メールプラットフォーム特性](email.md)
- [Kook(开黑啦)プラットフォーム特性](kook.md)
- [Matrixプラットフォーム特性](matrix.md)
- [企業微信（WeCom）プラットフォーム特性](wecom.md)
- [QQ公式ボットプラットフォーム特性](qqbot.md)
- [花楓カフェ](ideaura.md)
- [Discord](discord.md)
- [Webhookプロトコルブリッジ](webhook.md)
- [WeChat公式アカウント](wechatmp.md)

> また、`sandbox` アダプターもありますが、このアダプターについてはプラットフォーム特性ドキュメントの管理は不要です

---

## 一般的なインターフェース

### Send 鏈式呼び出し

すべてのアダプタは以下の標準的な呼び出し方法をサポートしています：

> **注意:** ドキュメント内の `{AdapterName}` は実際のアダプタ名（例: `yunhu`、`telegram`、`onebot11`、`email` など）に置き換える必要があります。

1. タイプとIDを指定: `To(type,id).Func()`
   ```python
   # アダプタインスタンスを取得
   my_adapter = adapter.get("{AdapterName}")
   
   # メッセージを送信
   await my_adapter.Send.To("user", "U1001").Text("Hello")
   
   # 例:
   yunhu = adapter.get("yunhu")
   await yunhu.Send.To("user", "U1001").Text("Hello")
   ```
2. IDのみを指定: `To(id).Func()`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.To("U1001").Text("Hello")
   
   # 例:
   telegram = adapter.get("telegram")
   await telegram.Send.To("U1001").Text("Hello")
   ```
3. 送信アカウントを指定: `Using(account_id)`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.Using("bot1").To("U1001").Text("Hello")
   
   # 例:
   onebot11 = adapter.get("onebot11")
   await onebot11.Send.Using("bot1").To("U1001").Text("Hello")
   ```
4. 直接呼び出し: `Func()`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.Text("Broadcast message")
   
   # 例:
   email = adapter.get("email")
   await email.Send.Text("Broadcast message")
   ```

#### 非同期送信と結果処理

Send DSLのメソッドは`asyncio.Task`オブジェクトを返すため、結果を即座に待つか、後で待つかを選択できます：

```python
# アダプタインスタンスを取得
my_adapter = adapter.get("{AdapterName}")

# 結果を待たずにバックグラウンドでメッセージを送信
task = my_adapter.Send.To("user", "123").Text("Hello")

# 送信結果が必要な場合は、後で待つ
result = await task
```

#### 送信ルールデコレータ

実際の開発では、送信が成功した後に後続の処理を実行したい、失敗時に自動でリトライしたい、タイムアウトでキャンセルしたい、送信の進行状況を監視したいなどの要望があります。Send DSLには、これらの要望に応えるための送信ルールデコレータが組み込まれており、送信メソッドの前にチェーンでルールを追加できます：

| メソッド | 説明 |
|--------|------|
| `.Hook(callback)` | 送信が成功した後に実行されるコールバック（複数回呼び出せる） |
| `.Retry(times=1)` | 失敗時にリトライをN回（初回含む、合計N+1回） |
| `.Timeout(seconds)` | 単回送信のタイムアウト、タイムアウトでキャンセル（Retryと組み合わせ可） |
| `.Defer(seconds)` | 送信を遅延（プロセス内での単純な遅延、永続化はしない） |
| `.OnProgress(callback)` | 各段階の進行状況をコールバック、SendContextを渡す |
| `.OnError(callback)` | 最終的に失敗した際のエラーコールバック（1回のみ発動） |

```python
yunhu = adapter.get("yunhu")

# 送信成功後にポイントを減らす
await (yunhu.Send.To("user", "123")
       .Hook(lambda r: deduct_points("123"))
       .Text("消費成功"))

# 失敗リトライ + タイムアウトキャンセル + 進行状況の監視
def on_progress(ctx):
    print(f"段階: {ctx.stage}, 試行: {ctx.attempt + 1}/{ctx.max_attempts}")

task = (yunhu.Send.To("user", "123")
        .Retry(3)              # 最大3回リトライ
        .Timeout(10)           # 10秒でタイムアウト
        .OnProgress(on_progress)
        .OnError(lambda ctx: notify_admin(ctx.error))
        .Text("重要通知"))
```

ルールメソッドは`self`を返すため、送信メソッド（Text/Imageなど）の前に呼び出す必要があります。`SendContext`には`stage`（pending/sending/retrying/success/failed/timeout）、`attempt`、`elapsed`、`error`、`result`などのフィールドが含まれ、モニタリングに便利です。

#### バッチ構築モード（Build）

1つのチェーンで複数の送信メソッドを構築し、最後にまとめて実行します。これは「一気に複数のメッセージを送信する」ような場面に適しています：

```python
yunhu = adapter.get("yunhu")

# 複数のメッセージを構築し、まとめて送信
results = await (yunhu.Send.To("user", "123")
                .Build()                     # 構築モードに入る
                .Text("通知一")
                .Image("pic.jpg")
                .Text("通知二")
                .send_all())                 # まとめて実行
# results = [Textの結果, Imageの結果, Textの結果]
```

`.send_all()`はデフォルトで**並列**実行（並行送信、効率的）です。順序を保証したい場合は`.Sequential()`で**直列**実行します：

```python
# 直列実行（順序を保証）+ 失敗リトライ
await (yunhu.Send.To("group", "456")
       .Build()
       .Sequential()                # 送信順序を保証
       .Retry(2)                     # 失敗した項目はそれぞれリトライ
       .Text("第一条").Text("第二条")
       .send_all())
```

バッチ実行では**失敗継続**戦略を採用しています：1つのメッセージが失敗しても他のメッセージは中断されず、失敗したメッセージは自動でリトライされます。バッチ実行では、全メッセージが成功した後に発動する`Hook`、失敗した場合に発動する`OnError`、進行状況を監視する`OnProgress`もサポートしています。

> さらに詳細なルールとバッチ構築の説明は [SendDSL 詳解](../developer-guide/adapters/send-dsl.md) を参照してください。

### イベント監視

3種類のイベント監視方法があります：

1. プラットフォーム固有のイベント監視：
   ```python
   from ErisPulse.Core import adapter, logger
   
   @adapter.on("event_type", raw=True, platform="{AdapterName}")
   async def handler(data):
       logger.info(f"受信した{AdapterName}プラットフォームのイベント: {data}")
   ```

2. OneBot12標準イベント監視：
   ```python
   from ErisPulse.Core import adapter, logger

   # OneBot12標準イベントを監視
   @adapter.on("event_type")
   async def handler(data):
       logger.info(f"受信した標準イベント: {data}")

   # 特定プラットフォームの標準イベントを監視
   @adapter.on("event_type", platform="{AdapterName}")
   async def handler(data):
       logger.info(f"受信した{AdapterName}プラットフォームの標準イベント: {data}")
   ```

3. Eventモジュールによるイベント監視：
    `Event`のイベントは`adapter.on()`関数に基づいているため、`Event`が提供するイベントフォーマットはOneBot12標準イベントです。

    ```python
    from ErisPulse.Core.Event import message, notice, request, command

    message.on_message()(message_handler)
    notice.on_notice()(notice_handler)
    request.on_request()(request_handler)
    command("hello", help="挨拶メッセージを送信", usage="hello")(command_handler)

    async def message_handler(event):
        logger.info(f"受信したメッセージ: {event}")
    async def notice_handler(event):
        logger.info(f"受信した通知: {event})
    async def request_handler(event):
        logger.info(f"受信したリクエスト: {event})
    async def command_handler(event):
        logger.info(f"受信したコマンド: {event})
    ```

この中で、最も推奨されるのは`Event`モジュールによるイベント処理です。`Event`モジュールは豊富なイベントタイプとイベント処理メソッドを提供しているためです。

---

## 標準フォーマット
参考のため、ここにイベントフォーマットの簡単な例を示します。詳細情報が必要な場合は、上記のリンクを参照してください。

> **注意:** 以下のフォーマットは基本的なOneBot12標準フォーマットであり、各アダプタはこの上に拡張フィールドを追加する可能性があります。具体的な内容は、各アダプタの特定機能の説明を参照してください。

### 標準イベントフォーマット
すべてのアダプタが実装するイベント変換フォーマット：
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
    {"type": "text", "data": {"text": "你好"}}
  ],
  "alt_message": "你好",
  "user_id": "user_456",
  "user_nickname": "ExampleUser",
  "group_id": "group_789"
}
```

### 標準レスポンスフォーマット
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
ErisPulseプロジェクト：
- [主リポジトリ](https://github.com/ErisPulse/ErisPulse/)
- [Yunhuアダプタリポジトリ](https://github.com/ErisPulse/ErisPulse-YunhuAdapter)
- [Telegramアダプタリポジトリ](https://github.com/ErisPulse/ErisPulse-TelegramAdapter)
- [OneBotアダプタリポジトリ](https://github.com/ErisPulse/ErisPulse-OneBotAdapter)

関連公式ドキュメント：
- [OneBot V11プロトコルドキュメント](https://github.com/botuniverse/onebot-11)
- [Telegram Bot API公式ドキュメント](https://core.telegram.org/bots/api)
- [雲湖公式ドキュメント](https://www.yhchat.com/document/1-3)

## 貢献の参加

開発者の方々からのさらなる貢献を歓迎します！以下の手順に従って、貢献を提出してください：
1. [ErisPulse](https://github.com/ErisPulse/ErisPulse) リポジトリをForkします。
2. `docs/platform-features/` ディレクトリにMarkdownファイルを作成し、`<プラットフォーム名>.md`という形式で命名します。
3. 本`README.md`ファイルに、ご自身が貢献したアダプタへのリンクと、関連する公式ドキュメントを追加します。
4. Pull Requestを提出します。

ご支援ありがとうございます！