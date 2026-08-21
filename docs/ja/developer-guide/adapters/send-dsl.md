# SendDSL 詳解

SendDSL は、ErisPulse アダプターが提供する、チェーン呼び出しスタイルのメッセージ送信インターフェースです。

各言語間の切り替え行（各言語名が `` | `` で区切られた行）が含まれる場合、上記の第8条のフォーマット要件を厳密に遵守し、``[**Label**](file)`` といった誤った形式を出力しないようにしてください。

## 基本的な呼び出し方法

### 1. 型とIDを指定

```python
await adapter.Send.To("group", "123").Text("Hello")
```

### 2. IDのみ指定

```python
await adapter.Send.To("123").Text("Hello")
```

### 3. 送信アカウントを指定

```python
await adapter.Send.Using("bot1").Text("Hello")
```

### 4. 組み合わせて使用

```python
await adapter.Send.Using("bot1").To("group", "123").Text("Hello")
```

[**English**](docs/ja/quick-start.md) | [**简体中文**](docs/ja/quick-start.md)

## メソッドチェーン

```mermaid
flowchart LR
    A["Using / Account<br/>（送信するアカウントを指定、オプション）"] --> B["To<br/>（送信先のタイプとIDを指定）"]
    B --> C["修飾メソッド<br/>At / Reply / Expire / ForMember など"]
    C --> D["送信メソッド<br/>Text / Image / Voice / Raw_ob12"]
    D --> E["返り値 asyncio.Task"]
```

[**English**](docs/en/quick-start.md) | [**中文**](docs/ja/quick-start.md) | [**日本語**](docs/ja/quick-start.md)

## 送信方法

すべての送信メソッドは `asyncio.Task` オブジェクトを返します。

### 基本メソッド（基底クラスに内蔵）

以下の標準メソッドは `SendDSL` 基底クラスに内蔵されており、**デフォルトで `Raw_ob12` に委譲**されます。アダプタのサブクラスは、再実装する必要がなく、直接使用できます。また、IDE が補完できます。

| メソッド名 | 説明 | 戻り値 |
|--------|------|---------|
| `Text(text: str)` | テキストメッセージを送信 | `asyncio.Task` |
| `Image(file: bytes \| str)` | 画像を送信 | `asyncio.Task` |
| `Voice(file: bytes \| str)` | 音声を送信（OneBot12 `audio` セグメント） | `asyncio.Task` |
| `Video(file: bytes \| str)` | 動画を送信 | `asyncio.Task` |
| `File(file: bytes \| str, filename: str = None)` | ファイルを送信 | `asyncio.Task` |

アダプタは、個々の標準メソッドをオーバーライドして、プラットフォーム固有のロジックを提供できます：

```python
class Send(SendDSL):
    def Raw_ob12(self, message, **kwargs):
        # 必須実装
        ...

    # オプション：Text をオーバーライドして、プラットフォーム固有のロジックを提供
    # def Text(self, text: str):
    #     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

### プロトコルメソッド

| メソッド名 | 説明 | 戻り値 | 必須か |
|--------|------|---------|---------|
| `Raw_ob12(message)` | OneBot12 形式のメッセージを送信 | `asyncio.Task` | **必須実装** |

> **重要**：`Raw_ob12` はアダプタのコアメソッドであり、**必須実装**です。これは OneBot12 → プラットフォームへの逆変換の統一エントリーポイントです。実装しない場合、基底クラスは error ログを記録し、標準のエラー応答（`status: "failed"`, `retcode: 10002`）を返します。標準メソッド（`Text`、`Image` など）は、デフォルトで `Raw_ob12` に委譲されます。

### プラットフォーム固有のメソッド

アダプタは `Send` サブクラスに、プラットフォーム固有の送信メソッドを追加できます（`event.supports()` / `event.available_methods()` で認識されます）：

```python
class Send(SendDSL):
    def Raw_ob12(self, message, **kwargs): ...

    # プラットフォーム固有のメソッド
    def Sticker(self, sticker_id: str):
        return self.Raw_ob12([{"type": "sticker", "data": {"id": sticker_id}}])

## 修飾メソッド

修飾メソッドは `self` を返すことで、メソッドチェーンをサポートします。

### At メソッド

```python
# @特定のユーザー
await adapter.Send.To("group", "123").At("456").Text("こんにちは")

# @複数のユーザー
await adapter.Send.To("group", "123").At("456").At("789").Text("皆さんこんにちは")
```

### AtAll メソッド

```python
# @全員メンション
await adapter.Send.To("group", "123").AtAll().Text("皆さんこんにちは")
```

### Reply メソッド

```python
# メッセージへの返信
await adapter.Send.To("group", "123").Reply("msg_id").Text("返信内容")
```

### 修飾の組み合わせ

```python
await adapter.Send.To("group", "123").At("456").Reply("msg_id").Text("@を含む返信")
```

### プラットフォーム固有の修飾メソッド

組み込みの `At`/`AtAll`/`Reply` に加えて、アダプタは**プラットフォーム固有の修飾メソッド**を定義できます。この種のメソッドは**`self` を返すだけで**、デコレータは不要です。フレームワークが自動的に識別します：

- `self`（SendDSL インスタンス）を返す → 修飾メソッド、送信パッケージやライフサイクルイベントはトリガーせず、メソッドチェーンを継続
- `Task`/`Awaitable` を返す → 送信メソッド

```python
class Send(SendDSL):
    def Raw_ob12(self, message, **kwargs): ...

    # 修飾メソッド：self を返す、送信は行わない
    def Expire(self, seconds: int):
        self._expire = seconds
        return self

    def ForMember(self, user_id: str):
        self._member = user_id
        return self

    # 送信メソッド：Task を返す、修飾メソッドで設定されたステートに依存
    def Board(self, content: str, **kwargs):
        return self.Raw_ob12([{"type": "board", "data": {"text": content}}])
```

使用例：

```python
# 修飾メソッドは連続してメソッドチェーンで使用可能
await adapter.Send.To("group", "big").Expire(3600).ForMember("114").Board("ボードの内容")

## Event 包装类中的修飾メソッドの使用

> [!NOTE]
> `reply(via=)` と `event.send_chain()` は ErisPulse **2.7.0+** が必要です。

`event.reply()` はデフォルトで `at_sender`/`at_users`/`at_all`/`quote` などの組み込み修飾パラメータのみを公開します。プラットフォーム固有の修飾メソッドを使用するには、2 つの方法があります：

### 方法 1: reply() の via パラメータ

少量で既知の修飾メソッドに適しています：

```python
await event.reply("看板内容", method="Board",
                  via=[("Expire", 3600), ("ForMember", "114514")])
```

`via` はリストであり、各要素は以下の形式のいずれかです：

| 形式 | 等価な連鎖呼び出し |
|------|-------------|
| `"Name"` | `.Name()` |
| `("Name", arg1, arg2)` | `.Name(arg1, arg2)` |
| `("Name", (arg1,), {kw: val})` | `.Name(arg1, kw=val)` |

### 方法 2: event.send_chain()

**複数の修飾メソッド**や**内容パラメータのないアクション型メソッド**（例：取り消し、削除）に適しています。`send_chain()` は `To`/`Using` が設定された送信チェーンを返し、任意の修飾メソッドと送信メソッドを自由に追加できます：

```python
# プラットフォーム固有の修飾メソッド + 看板送信
await event.send_chain().Expire(3600).Board("一時間後に期限切れ")

# 複数の連続修飾メソッド
await (event.send_chain()
       .Expire(3600)
       .ForMember("114514")
       .Board("看板内容", content_type="markdown"))

# 組み込み修飾メソッドも使用可能
await event.send_chain().At("123").Reply("msg_id").Text("hi")

# 内容パラメータのないアクション型メソッド
await event.send_chain().DismissBoard()
```

> `send_chain()` は完全な SendDSL インスタンスを返すため、**すべての連鎖特性が使用可能**です — 修飾メソッドだけでなく、送信ルールや一括構築も含まれます：

```python
# 送信ルール：リトライ + タイムアウト + 成功コールバック
await (event.send_chain()
       .Retry(3).Timeout(10)
       .Hook(lambda r: print("送信成功"))
       .Text("信頼性の高い送信"))

# 遅延送信 + プラットフォーム修飾 + 看板
await event.send_chain().Defer(5).Expire(3600).Board("遅延看板")

# 一括構築モード
results = await (event.send_chain()
                 .Build()
                 .Text("第一句").Image("pic.jpg").Text("第二句")
                 .send_all())

## アカウント管理

### Using メソッド

`Using()` は、メッセージを送信するアカウントを指定するために使用します。渡された識別子は、`_resolve_account()` によって以下の優先順位でマッチされます：

1. **アカウント名** — 設定ファイルのキー名（例: `"default"`、`"bot1"`）
2. **実行時に注入された bot_id** — イベント変換時に自動的に注入される識別子
3. **任意の str フィールド** — 設定ファイル内の他の文字列フィールド
4. **デフォルト** — 最初に有効化されたアカウント

```python
# アカウント名を使用
await adapter.Send.Using("account1").To("user", "123").Text("Hello")

# bot_id を使用（イベント内の self.user_id に相当）
await adapter.Send.Using("bot_123").To("user", "123").Text("Hello")
```

### Account メソッド

`Account` メソッドは `Using` と同等です：

```python
await adapter.Send.Account("account1").To("user", "123").Text("Hello")
```

[**English**](docs/en/quick-start.md) | [**日本語**](docs/ja/quick-start.md)

## 非同期処理

### 結果を待たない

```python
# メッセージはバックグラウンドで送信されます
task = adapter.Send.To("user", "123").Text("Hello")

# 他の操作を続行します
# ...
```

### 結果を待つ

```python
# await を直接使用して結果を取得します
result = await adapter.Send.To("user", "123").Text("Hello")
print(f"送信結果: {result}")

# まず Task を保存し、後で待機します
task = adapter.Send.To("user", "123").Text("Hello")
# ... 他の操作 ...
result = await task
```

[**English**](docs/en/async-processing.md) | [**中文**](docs/ja/async-processing.md) | [**日本語**](docs/ja/async-processing.md)

## 送信ルールシステム

SendDSL には、ルールデコレータをチェーン形式で追加し、最終的な送信時に一括適用できるルールシステムが内蔵されています。ルールは一般的なプロダクションシナリオをカバーしています：タイムアウト制御、失敗時のリトライ、成功時のコールバック、遅延送信、優先度による破棄、進行状況の監視。

ルールメソッドは**selfを返す**（At/AtAll/Replyと同じ）ため、送信メソッド（Text/Imageなど）の前に呼び出す必要があります。ルールは `To`/`Using`/`Account` で作成された新しいインスタンスに伝播します。

### ルールメソッド一覧

| メソッド | 説明 |
|--------|------|
| `.Hook(callback)` | 送信が成功した後に実行されるコールバック（複数回呼び出すことができ、順番に実行されます） |
| `.Retry(times=1)` | 失敗した場合に自動的にN回リトライ（最初の送信を含めて合計N+1回） |
| `.Timeout(seconds)` | 単回送信のタイムアウト、タイムアウト時に現在の試行をキャンセル（Retryと重ねて使用可能） |
| `.Defer(seconds=1.0)` | 送信を遅延（プロセス内でのタイマー、永続化はされません） |
| `.Priority(level, drop_if_busy=False)` | 送信の優先度を設定；送信キューが混雑した場合に破棄可 |
| `.OnProgress(callback)` | 各段階の進行状況コールバック（SendContextを引数に渡す） |
| `.OnError(callback)` | 最終的に失敗した際のエラーコールバック（1回のみ呼び出されます） |

### 送信成功後に実行されるロジック（Hook）

```python
# 同期コールバック
await (adapter.Send.To("user", "123")
       .Hook(lambda r: print(f"送信成功、メッセージID: {r['message_id']}"))
       .Text("你好"))

# 異同步コールバック
async def deduct_points(result):
    await db.update(user_id="123", points=-1)

await adapter.Send.To("user", "123").Hook(deduct_points).Text("扣积分")
```

Hookは送信が最終的に成功した場合（リトライ成功を含む）にのみ実行されます。失敗、タイムアウト、キャンセルの場合はトリガーされません。

### 失敗時の自動リトライ（Retry）

```python
# 初回失敗後に2回リトライし、合計3回の試行
result = await adapter.Send.To("user", "123").Retry(2).Text("带重试")
```

リトライのトリガー条件：送信時に例外が発生した場合、送信がタイムアウトした場合、送信が `status == "failed"` のレスポンスを返した場合。

### タイムアウトによる自動キャンセル（Timeout）

```python
# 単回送信が10秒を超えるとキャンセル
await adapter.Send.To("user", "123").Timeout(10).Text("带超时")

# タイムアウト + リトライ：各試行10秒、最大3回
await adapter.Send.To("user", "123").Timeout(10).Retry(2).Text("超时重试")
```

### 進行状況の監視（OnProgress / OnError）

```python
def on_progress(ctx):
    print(f"段階: {ctx.stage}, 試行: {ctx.attempt + 1}/{ctx.max_attempts}, 耗時: {ctx.elapsed:.2f}s")
    if ctx.stage == "failed":
        print(f"  エラー: {ctx.error!r}")

async def on_error(ctx):
    await notify_admin(f"送信先 {ctx.target_id} に送信失敗: {ctx.error!r}")

await (adapter.Send.To("user", "123")
       .Retry(3).Timeout(10)
       .OnProgress(on_progress)
       .OnError(on_error)
       .Text("监控"))
```

`SendContext` に含まれるフィールド：`task_id`、`platform`、`method`、`target_type`、`target_id`、`bot_id`、`stage`、`attempt`、`max_attempts`、`started_at`、`finished_at`、`elapsed`、`error`、`result`、`extra`。

`stage` の可能な値：`pending`、`sending`、`retrying`、`success`、`failed`、`timeout`、`cancelled`、`dropped`。

### 遅延送信（Defer）

```python
# 5秒後に送信
await adapter.Send.To("user", "123").Defer(5).Text("迟到消息")
```

> 注意：遅延はプロセス内でのタイマーであり、プロセスの再起動で失われるため、永続化は提供されません。

### 優先度と送信キューの混雑による破棄（Priority）

```python
# 低優先度のメッセージ、送信キューが混雑した場合に自動的に破棄
result = await (adapter.Send.To("user", "123")
               .Priority(-1, drop_if_busy=True)
               .Text("可放弃的通知"))
# 破棄された場合、result["status"] == "failed"
```

`drop_if_busy` を有効にすると、送信中のタスク数が閾値（デフォルトは64）を超えた場合、その送信は直ちに破棄されます。`.PriorityThreshold(n)` でグローバルな閾値を調整できます。

### ルールの組み合わせとバックグラウンド実行

```python
# メインプロセスをブロックせず、ルールは正常に有効
task = (adapter.Send.To("user", "123")
        .Hook(lambda r: print("送信成功！"))
        .Retry(3)
        .Timeout(10)
        .OnProgress(on_progress)
        .Text("你好"))

# 他の操作を継続
await handle_next_action()
```

### ルールの伝播

ルールは `To`/`Using`/`Account` で作成された新しいインスタンスに伝播し、チェーン呼び出し中にルールが失われることを防ぎます：

```python
# Toの前にルールを設定しても、Toで作成されたインスタンスに伝播します
builder = adapter.Send.Retry(3).Timeout(10)
send = builder.To("user", "123")  # sendはRetry(3)とTimeout(10)を引き継ぎます
await send.Text("hi")
```

複数のインスタンスのルールは独立しています（hooksリストは深くコピーされます）。

## バッチ構築モード（Build）

SendDSL は、シングルショットモードに加えて、バッチ構築モードもサポートしています。1つのチェーンに複数の送信メソッドを記述し、最後に一括して実行します。これは「一気に複数のメッセージを送信する」シナリオに適しています。

### 構築モードの開始

送信メソッドの前に `.Build()` を呼び出すと、`SendBuilder` が返されます。その後、送信メソッド（Text/Image など）は即座に実行されず、送信意図として蓄積されます：

```python
results = await (adapter.Send.To("user", "123")
                 .Build()                    # 構築モードに移行
                 .Text("第一句")
                 .Image("pic.jpg")
                 .Text("第二句")
                 .send_all())                 # 一括実行
# results = [Text結果, Image結果, Text結果]
```

`.send_all()` は `asyncio.Task` を返し、await 後に意図の順序に従った結果リストが得られます。

### 並列と直列

デフォルトでは**並列**実行（並行送信、総所要時間は最遅の1件に等しい）されます。メッセージの到着順序を保証する必要がある場合は `.Sequential()` を呼び出します：

```python
# 直列：順番に送信
await (adapter.Send.To("group", "456")
       .Build()
       .Sequential()
       .Text("先発这个").Text("再发这个")
       .send_all())

# 並列（デフォルト、明示的に呼び出すことも可能）
await (adapter.Send.To("group", "456")
       .Build()
       .Parallel()
       .Text("并发1").Text("并发2")
       .send_all())
```

### 失敗時の継続とリトライ

バッチ実行では**失敗時の継続**戦略を採用しています。1件の失敗は他の件の送信を中断しません。`.Retry()` と併用すると、失敗した件は自動的にリトライされます（リトライは個々の件に作用し、バッチ全体をリトライするものではありません）：

```python
await (adapter.Send.To("user", "123")
       .Build()
       .Retry(2)                       # 各件ごとに2回リトライ
       .Text("可能失败的").Image("也可能失败的")
       .send_all())
```

### バッチ全体のルールとコールバック

ルールはバッチ全体に適用されます：

| メソッド | 説明 |
|--------|------|
| `.Timeout(seconds)` | 各件の送信の単回タイムアウト |
| `.Retry(times)` | 各件の送信を個別にリトライ（失敗時の継続） |
| `.Defer(seconds)` | バッチ全体の送信を遅延 |
| `.Hook(callback)` | バッチ全体が成功した後にトリガーされ、`results` リストを受け取る |
| `.OnError(callback)` | バッチに失敗がある場合にトリガーされ、`BatchContext` を受け取る |
| `.OnProgress(callback)` | 各件が完了するたびにトリガーされ、`BatchContext` を受け取る |

```python
def on_progress(ctx):
    print(f"進捗: {ctx.completed}/{ctx.total}, 成功 {ctx.succeeded}, 失敗 {ctx.failed}")

async def on_error(ctx):
    print(f"バッチに {ctx.failed} 件失敗")

results = await (adapter.Send.To("user", "123")
               .Build()
               .Retry(2).Timeout(10)
               .OnProgress(on_progress)
               .OnError(on_error)
               .Hook(lambda rs: print("バッチ全体完了"))
               .Text("a").Text("b").Text("c")
               .send_all())
```

`BatchContext` には以下のフィールドが含まれます：`task_id`、`total`、`completed`、`succeeded`、`failed`、`stage`、`results`、`errors`、`elapsed`、`extra`。

`stage` の値は次のいずれかです：`pending`、`sending`、`success`（すべて成功）、`partial`（一部成功）、`failed`（すべて失敗）。

### 修飾子とルールの継承

`.Build()` 以前の At/AtAll/Reply 修飾子とルールはバッチ全体に継承され、各件に適用されます：

```python
await (adapter.Send.To("group", "456")
       .At("789")                        # 継承：各件に @789 が適用される
       .Build()
       .Retry(2)                         # 継承 + 追加：各件ごとにリトライ
       .Text("@你的通知")
       .Image("公告图")
       .send_all())
```

Build 後でも修飾子を追加できます（バッチ全体に適用されます）：

```python
await (adapter.Send.To("group", "456")
       .Build()
       .At("111").At("222")             # 追加 @、バッチ全体に適用
       .Text("@多人")
       .send_all())
```

### バックグラウンド実行

シングルショットと同じく、`.send_all()` は Task を返し、await せずにバックグラウンドで実行させることもできます：

```python
task = (adapter.Send.To("user", "123")
        .Build()
        .Hook(lambda rs: print("バッチ送信完了"))
        .Text("a").Text("b")
        .send_all())

# メインフローをブロックしない
await do_something_else()

## 命名規則

### PascalCase 命名

送信メソッドはすべて大文字キャメルケース命名法を使用します：

```python
# ✅ 正しい
def Text(self, text: str):
    pass

def Image(self, file: bytes):
    pass

# ❌ 間違っている
def text(self, text: str):
    pass

def send_image(self, file: bytes):
    pass
```

### プラットフォーム固有メソッド

プラットフォームプレフィックス付きメソッドの追加は推奨されません：

```python
# ✅ 推奨
def Sticker(self, sticker_id: str):
    pass

# ❌ 推奨されない
def TelegramSticker(self, sticker_id: str):
    pass
```

`Raw` メソッドを使用して置き換えます：

```python
# ✅ 推奨
await adapter.Send.Raw_ob12([{"type": "sticker", ...}])

# ❌ 推奨されない
def TelegramSticker(self, ...):
    pass

## 送信リンクの内部分解

`await adapter.Send.To("group", "123").Text("x")` を実行すると、フレームワークは以下の処理をすべて自動的に行います。

```mermaid
flowchart TD
    A["adapter.Send.To(...).Text(...)"] --> B["To/Using チェーンメソッド<br/>毎回不変の新規インスタンスを返す（順序は関係ない）"]
    B --> C["__getattribute__ による送信メソッドのインターセプト<br/>ルールラッパーを1層包む"]
    C --> D["送信メソッド（Textなど）の呼び出し<br/>内部では Raw_ob12 に委譲"]
    D --> E["Raw_ob12 は asyncio.create_task(...) を返す"]
    E --> F["[Send] ログを記録"]
    F --> G["emit message.sending（fire-and-forget）を発火"]
    G --> H{"送信ルールを宣言しているか？"}
    H -->|"いいえ"| I["Task done_callback → emit message.sent"]
    H -->|"はい"| J["apply_send_rules で外層 Task にラップ<br/>リトライ/タイムアウト/遅延/優先度"]
    J --> I
    I --> K["await により標準的なレスポンス dict を得る"]
```

**フレームワークが各ステップで行ったこと:**

| 階段 | フレームワークが行ったこと |
|------|-------------|
| チェーンのマージ | `To`/`Using`/`Account` の各呼び出しは**不変の新規インスタンス**を作成し、既に設定されたフィールドを継承するため、`To(...).Using(...)` と `Using(...).To(...)` は**等価**、順序は関係ない |
| メソッドのラッピング | 送信メソッド（`Text`など）は `__getattribute__` によってラップされ、修飾メソッド（`To`/`Using`/`At`/`Retry`など）は**ラップされない**。`Raw_ob12` のネストされた呼び出しは `_in_rule_wrap` によるマーキングで重複ラップを防ぐ |
| Task の作成 | `Raw_ob12` 内部の `asyncio.create_task()` が Task の実際の作成点であり、`Text()` は Task を同期的に返すだけで、**ブロックはしない** |
| 送信ログ | `[Send] platform/method -> target` のイベントログを記録（`exclude_levels=["EVENT"]` で抑制可能） |
| `message.sending` | 送信メソッドが呼び出された際に**即座に** fire-and-forget でトリガーされる（ハンドラが存在する場合にのみ、`has_handlers` による短絡評価が先に実行される） |
| `message.sent` | Task の `done_callback` にバインドされる——**ルールがある場合は、リトライプロセス全体の最終結果を上書きする**、ルールがない場合は元の Task の完了を意味する |

### アカウント解決のフォールバックチェーン

アダプタ内部で `_resolve_account(account_id)` を呼び出した場合、以下の順序で具体的なアカウントに解決されます：

1. 単一アカウントアダプタ（`AccountConfigClass` なし）→ 直接返す
2. アカウント名が `account_id` に正確に一致
3. 各アカウントの `bot_id` フィールドが一致
4. 各アカウントの `str` 型フィールド値が一致（`enabled`/`name` を除く）
5. 最後に有効な最初のアカウントを返す
6. すべて失敗 → `ValueError` を投げる

> あなたが渡した `account_id` は、`Using()` で明示的に指定されたもの > イベントの `self` フィールド（`account_id` は `user_id` より優先、`event.reply()` で自動的に注入される）> 指定なし（アダプタが最初の有効なアカウントをデフォルトで返す）。

### 送信ルールエンジン（リトライ/タイムアウト/遅延）

ルールは `Raw_ob12` が Task を返した**後**に外側の Task としてラップされ、メインの処理には影響しない。重要な事実:

| ルール | 説明 |
|------|------|
| `Retry(n)` | 合計 `n+1` 回の試行を行う；**失敗後は即時再送信、指数バックオフはなし** |
| `Timeout(s)` | 単回送信のタイムアウト取消（`asyncio.wait_for`）、期限切れでなければリトライ |
| `Defer(s)` | 送信前に `sleep` による遅延 |
| `Priority(level, drop_if_busy)` | 積み重ねが閾値を超えた場合、直ちに `{status:"failed", retcode:10002, message:"dropped_low_priority"}` を返す |
| `Hook(fn)` | 最終的に成功した場合のみ順序通りに実行 |
| `on_progress` / `on_error` | 各段階 / 最終的な失敗時のコールバック |

> **注意**: リトライは「即時再送信」であり、指数バックオフは行われない。プラットフォームのリクエスト制限によるバックオフが必要な場合は、`on_error` コールバック内で `sleep` してから手動で再送信を行う必要がある。ルールの成功判定は、返却される dict の `status == "ok"` に基づく（`retcode == 0`）。

> 標準的なレスポンス形式と `retcode` の完全な意味については [API レスポンス規格](../../standards/api-response.md) を参照してください。

## 戻り値

### Task オブジェクト

すべての送信メソッドは `asyncio.Task` を返します。アダプタは `Raw_ob12` のみ実装すればよく、標準メソッド（Text/Image など）はデフォルトでそれらを委譲します：

```python
import asyncio

def Raw_ob12(self, message, **kwargs):
    async def _do_send():
        segments = self._apply_modifiers(message)
        return await self._adapter.call_api(
            endpoint="/send_message",
            message=segments,
            **self.send_context,
            **kwargs,
        )
    return asyncio.create_task(_do_send())

# Text/Image/Voice/Video/File は基底クラスから継承され、自動的に Raw_ob12 に委譲されます
# 標準メソッドをオーバーライドする場合は、asyncio.Task を返すだけです：
# def Text(self, text: str):
#     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

### 応答の標準化

`call_api` は標準化された応答を返す必要があります。`make_response()` / `make_error()` メソッドの使用が推奨されます：

```python
async def call_api(self, endpoint: str, **params):
    try:
        result = await self._do_api_call(endpoint, **params)
        return self.make_response(
            data=result.get("data"),
            message_id=result.get("message_id", ""),
            raw=result,
        )
    except Exception as e:
        return self.make_error(message=str(e))
```

また、手動で構築することも可能です（旧バージョンの方式も互換性があります）：

```python
async def call_api(self, endpoint: str, **params):
    return {
        "status": "ok" または "failed",
        "retcode": 0 またはエラーコード,
        "data": {...},
        "message_id": "msg_id" または "",
        "message": "",
        "{platform}_raw": raw_response
    }
```

直接翻訳後の完全なMarkdown内容を返してください。

## 完全例

### 基本的な使用方法

```python
from ErisPulse.Core import adapter

my_adapter = adapter.get("myplatform")

# テキストを送信
await my_adapter.Send.To("user", "123").Text("Hello World!")

# 画像を送信
await my_adapter.Send.To("group", "456").Image("https://example.com/image.jpg")

# ファイルを送信
with open("document.pdf", "rb") as f:
    await my_adapter.Send.To("user", "123").File(f.read())
```

### チェーン呼び出し

```python
# @ユーザー + メッセージの返信
await my_adapter.Send.To("group", "456").At("789").Reply("msg123").Text("返信メッセージ")

# @全員 + 複数の修飾
await my_adapter.Send.Using("bot1").To("group", "456").AtAll().Text("お知らせメッセージ")
```

### ロウメッセージとメッセージビルダー

`Raw_ob12` は逆変換の中心となるエントリーポイントです（OB12 メッセージセグメント → プラットフォーム API 呼び出し）。`MessageBuilder` はそれに伴って使用されるチェーン式のメッセージセグメント構築ツールです。

> 完全な `Raw_ob12` 実装の規格、`MessageBuilder` の使用方法およびコード例については、以下のドキュメントを参照してください：
> - [送信メソッド規格 §6 逆変換規格 (OneBot12 → プラットフォーム)](../../standards/send-method-spec.md#6-反向変換規格onebot12--プラットフォーム)
> - [送信メソッド規格 §11 メッセージビルダー](../../standards/send-method-spec.md#11-メッセージビルダー-messagebuilder)

## 関連ドキュメント

- [アダプタ開発の入門](getting-started.md) - アダプタの作成
- [アダプタのコアコンセプト](core-concepts.md) - アダプタアーキテクチャの理解
- [アダプタのベストプラクティス](best-practices.md) - 高品質なアダプタの開発
- [送信メソッドの仕様](../../standards/send-method-spec.md) - 送信メソッドの完全な仕様