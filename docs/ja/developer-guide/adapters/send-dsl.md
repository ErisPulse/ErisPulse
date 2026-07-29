# SendDSL 詳解

SendDSL は ErisPulse アダプターが提供するチェーン呼び出しスタイルのメッセージ送信インターフェースです。

## 基本的な呼び出し方

### 1. タイプとIDを指定する

```python
await adapter.Send.To("group", "123").Text("Hello")
```

### 2. IDのみを指定する

```python
await adapter.Send.To("123").Text("Hello")
```

### 3. 送信アカウントを指定する

```python
await adapter.Send.Using("bot1").Text("Hello")
```

### 4. 組み合わせて使用する

```python
await adapter.Send.Using("bot1").To("group", "123").Text("Hello")
```

## メソッドチェーン

```
Using/Account() → To() → [修飾メソッド] → [送信メソッド]
```

## 送信メソッド

すべての送信メソッドは `asyncio.Task` オブジェクトを返します。

### 基本メソッド（基底クラスに組み込み済み）

以下の標準メソッドは `SendDSL` 基底クラスに組み込み実装されており、**デフォルトでは `Raw_ob12` に委譲されます**。アダプターのサブクラスで重複して実装しなくても直接使用でき、IDE の補完も効きます：

| メソッド名 | 説明 | 返り値 |
|--------|------|---------|
| `Text(text: str)` | テキストメッセージを送信 | `asyncio.Task` |
| `Image(file: bytes \| str)` | 画像を送信 | `asyncio.Task` |
| `Voice(file: bytes \| str)` | 音声を送信（OneBot12 `audio` セグメント） | `asyncio.Task` |
| `Video(file: bytes \| str)` | ビデオを送信 | `asyncio.Task` |
| `File(file: bytes \| str, filename: str = None)` | ファイルを送信 | `asyncio.Task` |

アダプターは単一の標準メソッドをオーバーライドして、プラットフォーム固有のロジックを提供できます：

```python
class Send(SendDSL):
    def Raw_ob12(self, message, **kwargs):
        # 実装必須
        ...

    # オプション: Text をオーバーライドしてプラットフォーム固有のロジックを提供
    # def Text(self, text: str):
    #     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

### プロトコルメソッド

| メソッド名 | 説明 | 返り値 | 必須 |
|--------|------|---------|---------|
| `Raw_ob12(message)` | OneBot12 形式メッセージを送信 | `asyncio.Task` | **実装必須** |

> **重要**：`Raw_ob12` はアダプターの核心となるメソッドであり、**実装必須**です。これは逆変換（OneBot12 → プラットフォーム）の統一エントリポイントです。未実装の場合、基底クラスはエラーログを記録し、標準エラーレスポンス（`status: "failed"`, `retcode: 10002`）を返します。標準メソッド（`Text`、`Image` など）はデフォルトで `Raw_ob12` に委譲されます。

### プラットフォーム固有のメソッド

アダプターは `Send` サブクラスにプラットフォーム固有の送信メソッドを追加できます（`event.supports()` / `event.available_methods()` によって認識されます）：

```python
class Send(SendDSL):
    def Raw_ob12(self, message, **kwargs): ...

    # プラットフォーム固有のメソッド
    def Sticker(self, sticker_id: str):
        return self.Raw_ob12([{"type": "sticker", "data": {"id": sticker_id}}])
```

## 修飾メソッド

修飾メソッドは `self` を返してチェーン呼び出しをサポートします。

### At メソッド

```python
# @単一ユーザー
await adapter.Send.To("group", "123").At("456").Text("你好")

# @複数ユーザー
await adapter.Send.To("group", "123").At("456").At("789").Text("你们好")
```

### AtAll メソッド

```python
# @全員
await adapter.Send.To("group", "123").AtAll().Text("大家好")
```

### Reply メソッド

```python
# メッセージを返信
await adapter.Send.To("group", "123").Reply("msg_id").Text("回复内容")
```

### 組み合わせ修飾

```python
await adapter.Send.To("group", "123").At("456").Reply("msg_id").Text("回复@的消息")
```

### プラットフォーム固有の修飾メソッド

組み込みの `At`/`AtAll`/`Reply` に加え、アダプターは**プラットフォーム固有の修飾メソッド**を定義できます。これらのメソッドは**`self` を返すだけでよく**、何も装飾子（デコレータ）は必要ありません——フレームワークが自動的に認識します：

- `self` を返す（SendDSL インスタンス）→ 修飾メソッド。送信ラッパー/ライフサイクルイベントはトリガーせず、チェーン継続
- `Task`/`Awaitable` を返す → 送信メソッド

```python
class Send(SendDSL):
    def Raw_ob12(self, message, **kwargs): ...

    # 修飾メソッド: self を返し、送信しない
    def Expire(self, seconds: int):
        self._expire = seconds
        return self

    def ForMember(self, user_id: str):
        self._member = user_id
        return self

    # 送信メソッド: Task を返し、修飾メソッドで設定された状態に依存
    def Board(self, content: str, **kwargs):
        return self.Raw_ob12([{"type": "board", "data": {"text": content}}])
```

使用例：

```python
# 修飾メソッドは連続してチェーンで積み上げられる
await adapter.Send.To("group", "big").Expire(3600).ForMember("114").Board("看板内容")
```

## イベントラッパークラスでの修飾メソッドの使用

`event.reply()` はデフォルトで `at_sender`/`at_users`/`at_all`/`quote` 等の組み込み修飾パラメータのみを公開しています。プラットフォーム固有の修飾メソッドを使用するには、2つの方法があります。

### 方法1: reply() の via パラメータ

少量、既知の修飾メソッドに適しています：

```python
await event.reply("看板内容", method="Board",
                  via=[("Expire", 3600), ("ForMember", "114514")])
```

`via` はリスト形式で、各要素は以下の形式を取れます：

| 形式 | 等価なチェーン呼び出し |
|------|-------------|
| `"Name"` | `.Name()` |
| `("Name", arg1, arg2)` | `.Name(arg1, arg2)` |
| `("Name", (arg1,), {kw: val})` | `.Name(arg1, kw=val)` |

### 方法2: event.send_chain()

**複数の修飾メソッドを連続して**、または**内容パラメータを持たないアクション型メソッド**（例：撤回、削除）に適しています。`send_chain()` は設定済みの `To`/`Using` を持つ送信チェーンを返し、任意の修飾メソッドや送信メソッドを自由に追加できます：

```python
# プラットフォーム固有の修飾メソッド + 看板の送信
await event.send_chain().Expire(3600).Board("一小时后过期")

# 複数の修飾メソッドを連続して
await (event.send_chain()
       .Expire(3600)
       .ForMember("114514")
       .Board("看板内容", content_type="markdown"))

# 組み込みの修飾メソッドも同様に使用可能
await event.send_chain().At("123").Reply("msg_id").Text("hi")

# 内容パラメータを持たないアクション型メソッド
await event.send_chain().DismissBoard()
```

> `send_chain()` は完全な SendDSL インスタンスを返すため、**すべてのチェーン機能が使用可能**です——修飾メソッドだけでなく、送信ルールやバッチ構築も含まれます：

```python
# 送信ルール: リトライ + タイムアウト + 成功時コールバック
await (event.send_chain()
       .Retry(3).Timeout(10)
       .Hook(lambda r: print("发送成功"))
       .Text("可靠发送"))

# 遅延送信 + プラットフォーム修飾 + 看板
await event.send_chain().Defer(5).Expire(3600).Board("延迟看板")

# バッチ構築モード
results = await (event.send_chain()
                 .Build()
                 .Text("第一句").Image("pic.jpg").Text("第二句")
                 .send_all())
```

## アカウント管理

### Using メソッド

`Using()` はメッセージを送信するアカウントを指定するために使用します。渡された識別子は以下の優先順位で `_resolve_account()` によって照合されます：

1. **アカウント名** — 設定のキー名（例：`"default"`、`"bot1"`）
2. **ランタイムで注入された bot_id** — イベント変換時に自動注入される識別子
3. **任意の str フィールド** — 設定内のその他の文字列フィールド
4. **フォールバック** — 最初に有効なアカウント

```python
# アカウント名を使用
await adapter.Send.Using("account1").To("user", "123").Text("Hello")

# bot_idを使用（イベント内の self.user_id に相当）
await adapter.Send.Using("bot_123").To("user", "123").Text("Hello")
```

### Account メソッド

`Account` メソッドは `Using` と等価です：

```python
await adapter.Send.Account("account1").To("user", "123").Text("Hello")
```

## 非同期処理

### 結果を待たない

```python
# メッセージはバックグラウンドで送信
task = adapter.Send.To("user", "123").Text("Hello")

# 他の操作を続行
# ...
```

### 結果を待つ

```python
# 直接 await して結果を取得
result = await adapter.Send.To("user", "123").Text("Hello")
print(f"发送结果: {result}")

# 先に Task を保存し、後で待機
task = adapter.Send.To("user", "123").Text("Hello")
# ... 他の操作 ...
result = await task
```

## 送信ルールシステム

SendDSL はチェーンメソッドでルールを追加し、最終的な送信時に一括して適用する送信ルールデコレータを内蔵しています。ルールは一般的な運用シナリオをカバーしています：タイムアウト制御、失敗時リトライ、成功時コールバック、遅延送信、優先度による廃棄、進捗監視。

ルールメソッドは**`self` を返します**（At/AtAll/Reply と同様）、送信メソッド（Text/Image など）の前に呼び出す必要があります。ルールは `To`/`Using`/`Account` によって作成された新しいインスタンスに伝播します。

### ルールメソッド一覧

| メソッド | 説明 |
|--------|------|
| `.Hook(callback)` | 送信成功後に実行されるコールバック（複数回呼び出せ、順次実行） |
| `.Retry(times=1)` | 失敗時に自動リトライ N 回（最初の試行を含む合計 N+1 回） |
| `.Timeout(seconds)` | 送信ごとのタイムアウト、タイムアウトで現在の試行をキャンセル（Retry と組み合わせ可能） |
| `.Defer(seconds=1.0)` | 遅延送信（プロセス内のタイマー、永続化なし） |
| `.Priority(level, drop_if_busy=False)` | 優先度を設定；キューが滞った際は廃棄可能 |
| `.OnProgress(callback)` | 各段階の進捗コールバック（`SendContext` を受け取る） |
| `.OnError(callback)` | 最終的な失敗時のエラーコールバック（一度のみトリガー） |

### 送信成功後の実行ロジック（Hook）

```python
# 同期コールバック
await (adapter.Send.To("user", "123")
       .Hook(lambda r: print(f"发送成功，消息ID: {r['message_id']}"))
       .Text("你好"))

# 非同期コールバック
async def deduct_points(result):
    await db.update(user_id="123", points=-1)

await adapter.Send.To("user", "123").Hook(deduct_points).Text("扣积分")
```

Hook は送信が最終的に成功（リトライを含む）した場合にのみ実行されます；失敗、タイムアウト、キャンセルではトリガーされません。

### 失敗時の自動リトライ（Retry）

```python
# 最初の失敗後にリトライ 2 回、合計 3 回の試行
result = await adapter.Send.To("user", "123").Retry(2).Text("带重试")
```

リトライのトリガー条件：送信が例外をスローした場合、送信タイムアウト、送信から `status == "failed"` のレスポンスが返された場合。

### タイムアウト時の自動キャンセル（Timeout）

```python
# 送信ごとに 10 秒を超えるとキャンセル
await adapter.Send.To("user", "123").Timeout(10).Text("带超时")

# タイムアウト + リトライ：各試行 10 秒、最大 3 回
await adapter.Send.To("user", "123").Timeout(10).Retry(2).Text("超时重试")
```

### 進捗監視（OnProgress / OnError）

```python
def on_progress(ctx):
    print(f"阶段: {ctx.stage}, 尝试: {ctx.attempt + 1}/{ctx.max_attempts}, 耗时: {ctx.elapsed:.2f}s")
    if ctx.stage == "failed":
        print(f"  错误: {ctx.error!r}")

async def on_error(ctx):
    await notify_admin(f"发送给 {ctx.target_id} 失败: {ctx.error!r}")

await (adapter.Send.To("user", "123")
       .Retry(3).Timeout(10)
       .OnProgress(on_progress)
       .OnError(on_error)
       .Text("监控"))
```

`SendContext` が含むフィールド：`task_id`、`platform`、`method`、`target_type`、`target_id`、`bot_id`、`stage`、`attempt`、`max_attempts`、`started_at`、`finished_at`、`elapsed`、`error`、`result`、`extra`。

`stage` の可能な値：`pending`、`sending`、`retrying`、`success`、`failed`、`timeout`、`cancelled`、`dropped`。

### 遅延送信（Defer）

```python
# 5 秒後に送信
await adapter.Send.To("user", "123").Defer(5).Text("迟到消息")
```

> 注意：遅延はプロセス内のタイマーであり、プロセス再起動で失われます。永続化は提供されません。

### 優先度とキューの廃棄（Priority）

```python
# 低優先度メッセージ、キューが滞った際は自動的に廃棄
result = await (adapter.Send.To("user", "123")
               .Priority(-1, drop_if_busy=True)
               .Text("可放弃的通知"))
# 廃棄された場合、result["status"] == "failed"
```

`drop_if_busy` を有効にすると、送信中のタスク数が閾値を超えたとき（デフォルト 64）に今回の送信を即座に放棄します。グローバルな閾値は `.PriorityThreshold(n)` で調整できます。

### ルールの組み合わせとバックグラウンド実行

```python
# メインプロセスをブロックせず、ルールは正常に適用される
task = (adapter.Send.To("user", "123")
        .Hook(lambda r: print("发送成功！"))
        .Retry(3)
        .Timeout(10)
        .OnProgress(on_progress)
        .Text("你好"))

# 他の操作を続行
await handle_next_action()
```

### ルールの伝播

ルールは `To`/`Using`/`Account` によって作成された新しいインスタンスに伝播し、チェーン呼び出し中でのルールの紛失を防ぎます：

```python
# ルールは To の前に設定されており、To が作成したインスタンスにも伝播する
builder = adapter.Send.Retry(3).Timeout(10)
send = builder.To("user", "123")  # send はまだ Retry(3) と Timeout(10) を持っている
await send.Text("hi")
```

複数のインスタンスのルールは相互に独立です（フックリストはディープコピーされます）。

## バッチ構築モード（Build）

単発モッドに加え、SendDSL はバッチ構築モードもサポートしています：一つのチェーン内で複数の送信メソッドを記述し、最後に一括して実行します。「一度に複数のメッセージを送信する」というシナリオに適しています。

### 構築モードへの移行

送信メソッドの前に `.Build()` を呼び出して、`SendBuilder` を返します。以降、送信メソッド（Text/Image など）は即座に実行されず、送信意図として蓄積されます：

```python
results = await (adapter.Send.To("user", "123")
                 .Build()                    # 構築モードへ移行
                 .Text("第一句")
                 .Image("pic.jpg")
                 .Text("第二句")
                 .send_all())                 # 一括実行
# results = [Text結果, Image結果, Text結果]
```

`.send_all()` は `asyncio.Task` を返し、await 後に結果リスト（意図の順序）を取得できます。

### 並列と直列

デフォルトでは**並列**実行（同時送信、全体の所要時間は最も遅いものに等しくなります）。メッセージの到着順序を保証する必要がある場合は `.Sequential()` を呼び出します：

```python
# 直列：順番に送信
await (adapter.Send.To("group", "456")
       .Build()
       .Sequential()
       .Text("先发这个").Text("再发这个")
       .send_all())

# 並列（デフォルト、明示的に呼び出しても可）
await (adapter.Send.To("group", "456")
       .Build()
       .Parallel()
       .Text("并发1").Text("并发2")
       .send_all())
```

### 失敗時の継続とリトライ

バッチ実行では**失敗時の継続**戦略を採用しています：1つの失敗が他の送信の中断を引き起こさません。`.Retry()` を組み合わせる場合、失敗したエントリは自動的にリトライされます（リトライは個々のエントリに適用され、バッチ全体には適用されません）：

```python
await (adapter.Send.To("user", "123")
       .Build()
       .Retry(2)                       # 各エントリが個別に 2 回リトライ
       .Text("可能失败的").Image("也可能失败的")
       .send_all())
```

### バッチ全体のルールとコールバック

ルールはバッチ全体に統一的に適用されます：

| メソッド | 説明 |
|--------|------|
| `.Timeout(seconds)` | 各送信の単一タイムアウト |
| `.Retry(times)` | 各送信の個別リトライ（失敗時の継続） |
| `.Defer(seconds)` | バッチ全体の遅延送信 |
| `.Hook(callback)` | バッチ全体が成功した後でトリガー、`results` リストを受け取る |
| `.OnError(callback)` | バッチに失敗がある場合トリガー、`BatchContext` を受け取る |
| `.OnProgress(callback)` | 各完了時トリガー、`BatchContext` を受け取る |

```python
def on_progress(ctx):
    print(f"进度: {ctx.completed}/{ctx.total}, 成功 {ctx.succeeded}, 失败 {ctx.failed}")

async def on_error(ctx):
    print(f"批次有 {ctx.failed} 条失败")

results = await (adapter.Send.To("user", "123")
               .Build()
               .Retry(2).Timeout(10)
               .OnProgress(on_progress)
               .OnError(on_error)
               .Hook(lambda rs: print("整批完成"))
               .Text("a").Text("b").Text("c")
               .send_all())
```

`BatchContext` が含むもの：`task_id`、`total`、`completed`、`succeeded`、`failed`、`stage`、`results`、`errors`、`elapsed`、`extra`。

`stage` の可能な値：`pending`、`sending`、`success`（全成功）、`partial`（一部成功）、`failed`（全失敗）。

### 修飾子とルールの継承

`.Build()` 之前の At/AtAll/Reply 修飾子とルールはバッチ全体に継承され、各メッセージに適用されます：

```python
await (adapter.Send.To("group", "456")
       .At("789")                        # 継承：すべてのメッセージが @789
       .Build()
       .Retry(2)                         # 継承 + 追加：各メッセージが個別にリトライ
       .Text("@你的通知")
       .Image("公告图")
       .send_all())
```

Build へ移行した後でも修飾子を追加できます（バッチ全体に適用）：

```python
await (adapter.Send.To("group", "456")
       .Build()
       .At("111").At("222")             # 追加 @、バッチ全体に適用
       .Text("@多人")
       .send_all())
```

### バックグラウンド実行

単発モッドと同様、`.send_all()` は Task を返し、await せずにバックグラウンドで実行させることができます：

```python
task = (adapter.Send.To("user", "123")
        .Build()
        .Hook(lambda rs: print("批量发送完成"))
        .Text("a").Text("b")
        .send_all())

# メインプロセスをブロックしない
await do_something_else()
```

## 命名規則

### PascalCase 命名

すべての送信メソッドは大文字小文字区別のキャメルケース（PascalCase）を使用します：

```python
# ✅ 正しい
def Text(self, text: str):
    pass

def Image(self, file: bytes):
    pass

# ❌ 間違った
def text(self, text: str):
    pass

def send_image(self, file: bytes):
    pass
```

### プラットフォーム固有のメソッド

プラットフォームプレフィックスを持つメソッドの追加は推奨しません：

```python
# ✅ 推奨
def Sticker(self, sticker_id: str):
    pass

# ❌ 推奨しない
def TelegramSticker(self, sticker_id: str):
    pass
```

`Raw` メソッドを使用して置換してください：

```python
# ✅ 推奨
await adapter.Send.Raw_ob12([{"type": "sticker", ...}])

# ❌ 推奨しない
def TelegramSticker(self, ...):
    pass
```

## 返り値

### Task オブジェクト

すべての送信メソッドは `asyncio.Task` を返します。アダプターは `Raw_ob12` のみを実装すればよく、標準メソッド（Text/Image など）はデフォルトで委譲されます：

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

# Text/Image/Voice/File は基底クラスから継承済み、自動的に Raw_ob12 に委譲
# 標準メソッドをオーバーライドする場合は、asyncio.Task を返せばよい：
# def Text(self, text: str):
#     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

### 標準化されたレスポンス

`call_api` は標準化されたレスポンスを返すべきです。`make_response()` / `make_error()` メソッドの使用を推奨します：

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

手動構築（古い方式も互換性としてサポート）も可能です：

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

## 完全な例

### 基本的な使用

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
# @ユーザー + 返信
await my_adapter.Send.To("group", "456").At("789").Reply("msg123").Text("回复@的消息")

# @全員 + 複数の修飾
await my_adapter.Send.Using("bot1").To("group", "456").AtAll().Text("公告消息")
```

### 原始メッセージとメッセージ構築

`Raw_ob12` は逆変換の核心的なエントリポイント（OB12 メッセージセグメントを受け取り → プラットフォーム API の呼び出し）、`MessageBuilder` はそれを補助するチェーン式メッセージセグメント構築ツールです。

> 完全な `Raw_ob12` 実装仕様、`MessageBuilder` の使い方、コード例については以下を参照してください：
> - [送信メソッド仕様 §6 逆変換仕様](../../standards/send-method-spec.md#6-逆変換仕様onebot12--プラットフォーム)
> - [送信メソッド仕様 §11 メッセージビルダー](../../standards/send-method-spec.md#11-メッセージビルダー-messagebuilder)

## 関連ドキュメント

- [アダプター開発入門](getting-started.md) - アダプターの作成
- [アダプターのコア概念](core-concepts.md) - アダプターのアーキテクチャを理解する
- [アダプターのベストプラクティス](best-practices.md) - 高品質なアダプターの開発
- [送信メソッド仕様](../../standards/send-method-spec.md) - 送信メソッドの完全な仕様