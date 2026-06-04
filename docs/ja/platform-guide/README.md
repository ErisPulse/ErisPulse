# ErisPulse PlatformFeatures ドキュメント

> 基本プロトコル：[OneBot12](https://12.onebot.dev/) 
> 
> 本ドキュメントは**プラットフォーム固有機能ガイド**であり、以下を含みます：
> - 各アダプタがサポートするSendメソッドチェーン（連鎖呼び出し）の例
> - プラットフォーム固有のイベント/メッセージフォーマットの説明
> 
> 一般的な使用方法については以下を参照してください：
> - [基本概念](../getting-started/basic-concepts.md)
> - [イベント変換標準](../standards/event-conversion.md)  
> - [APIレスポンス仕様](../standards/api-response.md)

---

## プラットフォーム固有機能

このセクションは各アダプタ開発者がメンテナンスを行っており、そのアダプタがOneBot12標準との差異と拡張機能を説明するために使用されます。以下の各プラットフォームの詳細なドキュメントを参照してください：

- [メンテナンス説明](maintain-notes.md)

- [雲湖プラットフォーム固有機能](yunhu.md)
- [雲湖ユーザープラットフォーム固有機能](yunhu_user.md)
- [Telegramプラットフォーム固有機能](telegram.md)
- [OneBot11プラットフォーム固有機能](onebot11.md)
- [OneBot12プラットフォーム固有機能](onebot12.md)
- [メールプラットフォーム固有機能](email.md)
- [Kook(開黑啦)プラットフォーム固有機能](kook.md)
- [Matrixプラットフォーム固有機能](matrix.md)
- [QQ公式ボットプラットフォーム固有機能](qqbot.md)
- [花枫カフェ](ideaura.md)

> その他にも `sandbox` アダプタがありますが、このアダプタにはプラットフォーム固有機能のドキュメントメンテナンスは不要です。

---

## 汎用インターフェース

### Send メソッドチェーン
すべてのアダプタは以下の標準的な呼び出し方式をサポートしています：

> **注意：** ドキュメント内の `{AdapterName}` は実際のアダプタ名に置き換えてください（例：`yunhu`、`telegram`、`onebot11`、`email` など）。

1. 型とIDを指定: `To(type,id).Func()`
   ```python
   # アダプタインスタンスの取得
   my_adapter = adapter.get("{AdapterName}")
   
   # メッセージを送信
   await my_adapter.Send.To("user", "U1001").Text("Hello")
   
   # 例：
   yunhu = adapter.get("yunhu")
   await yunhu.Send.To("user", "U1001").Text("Hello")
   ```
2. IDのみを指定: `To(id).Func()`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.To("U1001").Text("Hello")
   
   # 例：
   telegram = adapter.get("telegram")
   await telegram.Send.To("U1001").Text("Hello")
   ```
3. 送信アカウントを指定: `Using(account_id)`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.Using("bot1").To("U1001").Text("Hello")
   
   # 例：
   onebot11 = adapter.get("onebot11")
   await onebot11.Send.Using("bot1").To("U1001").Text("Hello")
   ```
4. 直接呼び出し: `Func()`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.Text("Broadcast message")
   
   # 例：
   email = adapter.get("email")
   await email.Send.Text("Broadcast message")
   ```

#### 非同期送信と結果処理

Send DSLのメソッドは `asyncio.Task` オブジェクトを返します。これは、結果を即座に待機するかどうかを選択できることを意味します：

```python
# アダプタインスタンスの取得
my_adapter = adapter.get("{AdapterName}")

# 結果を待たず、メッセージをバックグラウンドで送信
task = my_adapter.Send.To("user", "123").Text("Hello")

# 送信結果が必要な場合は、後で待機可能です
result = await task
```

### イベント監視
イベント監視方法は3種類あります：

1. プラットフォームネイティブなイベント監視：
   ```python
   from ErisPulse.Core import adapter, logger
   
   @adapter.on("event_type", raw=True, platform="{AdapterName}")
   async def handler(data):
       logger.info(f"收到{AdapterName}原生事件: {data}")
   ```

2. OneBot12標準イベント監視：
   ```python
   from ErisPulse.Core import adapter, logger

   # OneBot12標準イベントを監視
   @adapter.on("event_type")
   async def handler(data):
       logger.info(f"收到标准事件: {data}")

   # 特定プラットフォームの標準イベントを監視
   @adapter.on("event_type", platform="{AdapterName}")
   async def handler(data):
       logger.info(f"收到{AdapterName}标准事件: {data}")
   ```

3. Eventモジュール監視：
    `Event`のイベントは `adapter.on()` 関数に基づいているため、`Event`が提供するイベントフォーマットはOneBot12標準イベントとなります。

    ```python
    from ErisPulse.Core.Event import message, notice, request, command

    message.on_message()(message_handler)
    notice.on_notice()(notice_handler)
    request.on_request()(request_handler)
    command("hello", help="发送问候消息", usage="hello")(command_handler)

    async def message_handler(event):
        logger.info(f"收到消息: {event}")
    async def notice_handler(event):
        logger.info(f"收到通知: {event}")
    async def request_handler(event):
        logger.info(f"收到请求: {event}")
    async def command_handler(event):
        logger.info(f"收到命令: {event}")
    ```

中でも最も推奨されるのは `Event` モジュールを使用したイベント処理です。これは `Event` モジュールが豊富なイベントタイプと豊富なイベント処理メソッドを提供するためです。

---

## 標準フォーマット
参照しやすいよう、ここでは簡単なイベントフォーマットを示します。詳細が必要な場合は、上のリンクを参照してください。

> **注意：** 以下のフォーマットは基本的なOneBot12標準フォーマットです。各アダプタはこれをベースに拡張フィールドを持っている場合があります。詳細は各アダプタの固有機能の説明を参照してください。

### 標準イベントフォーマット
すべてのアダプタが実装しなければならないイベント変換フォーマット：
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
  "message": "缺少必要参数",
  "echo": "1234",
  "{platform}_raw": {...}
}
```

---

## 参考リンク
ErisPulse プロジェクト：
- [メインリポジトリ](https://github.com/ErisPulse/ErisPulse/)
- [Yunhu アダプタライブラリ](https://github.com/ErisPulse/ErisPulse-YunhuAdapter)
- [Telegram アダプタライブラリ](https://github.com/ErisPulse/ErisPulse-TelegramAdapter)
- [OneBot アダプタライブラリ](https://github.com/ErisPulse/ErisPulse-OneBotAdapter)

関連する公式ドキュメント：
- [OneBot V11 プロトコルドキュメント](https://github.com/botuniverse/onebot-11)
- [Telegram Bot API 公式ドキュメント](https://core.telegram.org/bots/api)
- [雲湖公式ドキュメント](https://www.yhchat.com/document/1-3)

## 貢献の招待

私たちはより多くの開発者がアダプタドキュメントの作成とメンテナンスに参加することを歓迎します！以下の手順に従って貢献を提出してください：
1. [ErisPuls](https://github.com/ErisPulse/ErisPulse) リポジトリを Fork してください。
2. `docs/platform-features/` ディレクトリ下に Markdown ファイルを作成し、命名形式を `<プラットフォーム名>.md` としてください。
3. 本 `README.md` ファイルに、あなたが貢献したアダプタへのリンクおよび関連する公式ドキュメントを追加してください。
4. Pull Request を提出してください。

ご支援ありがとうございます！