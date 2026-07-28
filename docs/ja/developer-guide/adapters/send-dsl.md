# SendDSL 詳解

SendDSL は、ErisPulse アダプターが提供するチェーンメソッドスタイルのメッセージ送信インターフェースです。

## 基本の呼び出し方

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

### 4. 組み合わせ使用

```python
await adapter.Send.Using("bot1").To("group", "123").Text("Hello")
```

## メソッドチェーン

```
Using/Account() → To() → [修飾メソッド] → [送信メソッド]
```

## 送信メソッド

すべての送信メソッドは `asyncio.Task` オブジェクトを返します。

### 基本メソッド（基底クラスに実装済み）

以下の標準メソッドは `SendDSL` 基底クラスに実装されています。**デフォルトでは `Raw_ob12` に委譲されます**。アダプターのサブクラスは実装を繰り返す必要がなく、直接使用でき、IDE で補完できます。

| メソッド名 | 説明 | 戻り値 |
|--------|------|---------|
| `Text(text: str)` | テキストメッセージを送信 | `asyncio.Task` |
| `Image(file: bytes \| str)` | 画像を送信 | `asyncio.Task` |
| `Voice(file: bytes \| str)` | 音声を送信（OneBot12 `audio` セグメント） | `asyncio.Task` |
| `Video(file: bytes \| str)` | 動画を送信 | `asyncio.Task` |
| `File(file: bytes \| str, filename: str = None)` | ファイルを送信 | `asyncio.Task` |

アダプターは単一の標準メソッドを上書きして、プラットフォーム固有のロジックを提供できます。

```python
class Send(SendDSL):
    def Raw_ob12(self, message, **kwargs):
        # 必須実装
        ...

    # オプション：Text を上書きしてプラットフォーム固有のロジックを提供
    # def Text(self, text: str):
    #     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

### プロトコルメソッド

| メソッド名 | 説明 | 戻り値 | 必須 |
|--------|------|---------|---------|
| `Raw_ob12(message)` | OneBot12 形式のメッセージを送信 | `asyncio.Task` | **必須実装** |

> **重要**：`Raw_ob12` はアダプターの核心的なメソッドであり、**必須実装**です。これは「OneBot12 → プラットフォーム」への逆変換の統一されたエントリポイントです。実装されていない場合、基底クラスは error ログを出力し、標準エラー応答（`status: "failed"`, `retcode: 10002`）を返します。標準メソッド（`Text`、`Image` など）はデフォルトで `Raw_ob12` に委譲されます。

### プラットフォーム固有メソッド

アダプターは `Send` サブクラスでプラットフォーム固有の送信メソッドを追加できます（`event.supports()` / `event.available_methods()` によって認識されます）：

```python
class Send(SendDSL):
    def Raw_ob12(self, message, **kwargs): ...

    # プラットフォーム固有メソッド
    def Sticker(self, sticker_id: str):
        return self.Raw_ob12([{"type": "sticker", "data": {"id": sticker_id}}])
```

## 修飾メソッド

修飾メソッドは `self` を返してチェーンメソッドをサポートします。

### At メソッド

```python
# @単一のユーザー
await adapter.Send.To("group", "123").At("456").Text("こんにちは")

# @複数のユーザー
await adapter.Send.To("group", "123").At("456").At("789").Text("皆さんこんにちは")
```

### AtAll メソッド

```python
# @全員
await adapter.Send.To("group", "123").AtAll().Text("皆さんこんにちは")
```

### Reply メソッド

```python
# メッセージへの返信
await adapter.Send.To("group", "123").Reply("msg_id").Text("返信内容")
```

### 組み合わせ修飾

```python
await adapter.Send.To("group", "123").At("456").Reply("msg_id").Text("@への返信")
```

### プラットフォーム固有の修飾メソッド

組み込みの `At`/`AtAll`/`Reply` のほかに、アダプターは**プラットフォーム固有の修飾メソッド**を定義できます。この種のメソッドは**`self` を返すだけでよく**、何もデコレータは必要ありません。フレームワークが自動的に認識します。

- `self` を返す（SendDSL インスタンス）→ 修飾メソッド。送信ラッパー/ライフサイクルイベントはトリガーされず、チェーンは続行します
- `Task`/`Awaitable` を返す → 送信メソッド

```python
class Send(SendDSL):
    def Raw_ob12(self, message, **kwargs): ...

    # 修飾メソッド：self を返し、送信しません
    def Expire(self, seconds: int):
        self._expire = seconds
        return self

    def ForMember(self, user_id: str):
        self._member = user_id
        return self

    # 送信メソッド：Task を返し、修飾メソッドで設定された状態に依存します
    def Board(self, content: str, **kwargs):
        return self.Raw_ob12([{"type": "board", "data": {"text": content}}])
```

使用例：

```python
# 修飾メソッドは連続してチェーンを積み重ねることができます
await adapter.Send.To("group", "big").Expire(3600).ForMember("114").Board("看板内容")
```

## Event ラッパークラスでの修飾メソッドの使用

`event.reply()` はデフォルトで `at_sender`/`at_users`/`at_all`/`quote` などの組み込み修飾パラメータのみを公開しています。プラットフォーム固有の修飾メソッドを使用するには、2つの方法があります。

### 方法1：reply() の via パラメータ

少量、既知の修飾メソッドに適しています：

```python
await event.reply("看板内容", method="Board",
                  via=[("Expire", 3600), ("ForMember", "114514")])
```

`via` はリストです。各要素は以下の形式を取ることができます：

| 形式 | 等価なチェーン呼び出し |
|------|-------------|
| `"Name"` | `.Name()` |
| `("Name", arg1, arg2)` | `.Name(arg1, arg2)` |
| `("Name", (arg1,), {kw: val})` | `.Name(arg1, kw=val)` |

### 方法2：event.send_chain()

**連続した複数の修飾メソッド**や、**内容パラメータを持たないアクション型メソッド**（撤回、削除など）に適しています。`send_chain()` は `To`/`Using` が設定された送信チェーンを返し、任意の修飾メソッドと送信メソッドを自由に追加できます：

```python
# プラットフォーム固有の修飾メソッド + 看板の送信
await event.send_chain().Expire(3600).Board("1時間後に期限切れ")

# 連続した複数の修飾メソッド
await (event.send_chain()
       .Expire(3600)
       .ForMember("114514")
       .Board("看板内容", content_type="markdown"))

# 組み込みの修飾メソッドも利用可能です
await event.send_chain().At("123").Reply("msg_id").Text("hi")

# 内容パラメータを持たないアクション型メソッド
await event.send_chain().DismissBoard()
```

## アカウント管理

### Using メソッド

`Using()` はメッセージを送信するアカウントを指定するために使用します。渡された識別子は `_resolve_account()` を通じて、以下の優先順位で照合されます。

1. **アカウント名** — 設定のキー名（例：`"default"`、`"bot1"`）
2. **実行時に注入された bot_id** — イベント変換時に自動注入された識別子
3. **任意の str フィールド** — 設定の他の文字列フィールド
4. **フォールバック** — 最初に有効なアカウント

```python
# アカウント名を使用
await adapter.Send.Using("account1").To("user", "123").Text("Hello")

# bot_id を使用（イベント内の self.user_id に相当）
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
# メッセージはバックグラウンドで送信されます
task = adapter.Send.To("user", "123").Text("Hello")

# 他の操作を続行
# ...
```

### 結果を待つ

```python
# 直接 await して結果を取得
result = await adapter.Send.To("user", "123").Text("Hello")
print(f"送信結果: {result}")

# 先に Task を保存して、後で待つ
task = adapter.Send.To("user", "123").Text("Hello")
# ... 他の操作 ...
result = await task
```

## 送信ルールシステム

SendDSL には、チェーンメソッドでルールを追加し、最終送信時に一括して適用する送信ルールデコレータが組み込まれています。ルールは一般的なプロダクションシナリオをカバーします：タイムアウト制御、失敗リトライ、成功コールバック、遅延送信、優先度廃棄、進捗監視。

ルールメソッドは**`self` を返します**（At/AtAll/Reply と同様）、送信メソッド（Text/Image など）の前に呼び出す必要があります。ルールは `To`/`Using`/`Account` が作成する新しいインスタンスに伝播します。

### ルールメソッド一覧

| メソッド | 説明 |
|--------|------|
| `.Hook(callback)` | 送信成功後に実行されるコールバック（複数回呼び出し可能、順序通り実行） |
| `.Retry(times=1)` | 失敗時に自動的に N 回リトライ（最初の 1 回を含む合計 N+1 回） |
| `.Timeout(seconds)` | 1回の送信タイムアウト。タイムアウトで現在の試行をキャンセル（Retry と組み合わせ可能） |
| `.Defer(seconds=1.0)` | 遅延送信（プロセス内タイマー、永続化なし） |
| `.Priority(level, drop_if_busy=False)` | 優先度を設定。バックログ時は廃棄可能 |
| `.OnProgress(callback)` | 各段階の進捗コールバック（`SendContext` を渡します） |
| `.OnError(callback)` | 最終的な失敗時のエラーコールバック（1回のみトリガー） |

### 送信成功後に実行されるロジック（Hook）

```python
# 同期コールバック
await (adapter.Send.To("user", "123")
       .Hook(lambda r: print(f"送信成功、メッセージID: {r['message_id']}"))
       .Text("こんにちは"))

# 非同期コールバック
async def deduct_points(result):
    await db.update(user_id="123", points=-1)

await adapter.Send.To("user", "123").Hook(deduct_points).Text("ポイント減算")
```

Hook は送信が最終的に成功したとき（リトライ成功を含む）にのみ実行されます。失敗、タイムアウト、キャンセルはトリガーされません。

### 失敗時の自動リトライ（Retry）

```python
# 最初の失敗後に 2 回リトライ、合計 3 回の試行
result = await adapter.Send.To("user", "123").Retry(2).Text("リトライ付き")
```

リトライのトリガー条件：送信が例外を投げる、送信がタイムアウトする、送信が `status == "failed"` のレスポンスを返す。

### タイムアウトによる自動キャンセル（Timeout）

```python
# 1回の送信が 10 秒を超えるとキャンセル
await adapter.Send.To("user", "123").Timeout(10).Text("タイムアウト付き")

# タイムアウト + リトライ：各試行 10 秒、最大 3 回
await adapter.Send.To("user", "123").Timeout(10).Retry(2).Text("タイムアウトリトライ")
```

### 進捗監視（OnProgress / OnError）

```python
def on_progress(ctx):
    print(f"段階: {ctx.stage}, 試行: {ctx.attempt + 1}/{ctx.max_attempts}, 耗時: {ctx.elapsed:.2f}s")
    if ctx.stage == "failed":
        print(f"  エラー: {ctx.error!r}")

async def on_error(ctx):
    await notify_admin(f"{ctx.target_id} への送信に失敗: {ctx.error!r}")

await (adapter.Send.To("user", "123")
       .Retry(3).Timeout(10)
       .OnProgress(on_progress)
       .OnError(on_error)
       .Text("監視"))
```

`SendContext` が含むフィールド：`task_id`、`platform`、`method`、`target_type`、`target_id`、`bot_id`、`stage`、`attempt`、`max_attempts`、`started_at`、`finished_at`、`elapsed`、`error`、`result`、`extra`。

`stage` の可能性のある値：`pending`、`sending`、`retrying`、`success`、`failed`、`timeout`、`cancelled`、`dropped`。

### 遅延送信（Defer）

```python
# 5 秒後に送信
await adapter.Send.To("user", "123").Defer(5).Text("遅延メッセージ")
```

> 注意：遅延はプロセス内タイマーです。プロセスの再起動で失われ、永続化は提供されません。

### 優先度とバックログ廃棄（Priority）

```python
# 低優先度メッセージ、バックログ時に自動的に廃棄
result = await (adapter.Send.To("user", "123")
               .Priority(-1, drop_if_busy=True)
               .Text("廃棄可能な通知"))
# 廃棄された場合、result["status"] == "failed"
```

`drop_if_busy` を有効にすると、進行中の送信タスク数がしきい値（デフォルト 64）を超えたとき、今回の送信を直接放棄します。`.PriorityThreshold(n)` でグローバルなしきい値を調整できます。

### ルールの組み合わせとバックグラウンド実行

```python
# メインフローをブロックせず、ルールは依然として有効です
task = (adapter.Send.To("user", "123")
        .Hook(lambda r: print("送信成功！"))
        .Retry(3)
        .Timeout(10)
        .OnProgress(on_progress)
        .Text("こんにちは"))

# 他の操作を続行
await handle_next_action()
```

### ルールの伝播

ルールは `To`/`Using`/`Account` が作成する新しいインスタンスに伝播し、チェーン呼び出し中のルールの紛失を防ぎます：

```python
# To の前にルールを設定すると、To が作成するインスタンスにも伝播します
builder = adapter.Send.Retry(3).Timeout(10)
send = builder.To("user", "123")  # send は依然として Retry(3) と Timeout(10) を保持しています
await send.Text("hi")
```

複数のインスタンスのルールは相互に独立しています（フックリストのディープコピー）。

## バッチビルドモード（Build）

単発モードのほかに、SendDSL はバッチビルドモードもサポートしています：1つのチェーン内で複数の送信メソッドを記述し、最後に一括実行します。「まとめて複数のメッセージを一気に送信」するシナリオに適しています。

### ビルドモードに入る

送信メソッドの前に `.Build()` を呼び出すと、`SendBuilder` を返します。その後、送信メソッド（Text/Image など）は即座に実行されず、送信意図として蓄積されます：

```python
results = await (adapter.Send.To("user", "123")
                 .Build()                    # ビルドモードに入る
                 .Text("第一句")
                 .Image("pic.jpg")
                 .Text("第二句")
                 .send_all())                 # 一括実行
# results = [Text結果, Image結果, Text結果]
```

`.send_all()` は `asyncio.Task` を返し、await すると結果のリスト（意図の順序）を取得できます。

### 並列と順列

デフォルトでは**並列**実行です（並行送信、合計所要時間は最も遅いものとほぼ等価）。メッセージの到着順序を保証する必要がある場合は、`.Sequential()` を呼び出します：

```python
# 順列：順番に送信
await (adapter.Send.To("group", "456")
       .Build()
       .Sequential()
       .Text("先にこれ").Text("次にこれ")
       .send_all())

# 並列（デフォルト、明示的に呼び出しても可）
await (adapter.Send.To("group", "456")
       .Build()
       .Parallel()
       .Text("並列1").Text("並列2")
       .send_all())
```

### 失敗時の継続とリトライ

バッチ実行では**失敗時の継続**戦略を採用しています：1つでも失敗すると他の項目の送信が中断されません。`.Retry()` を組み合わせると、失敗した項目は自動的にリトライされます（リトライは1つの項目に作用し、バッチ全体には作用しません）：

```python
await (adapter.Send.To("user", "123")
       .Build()
       .Retry(2)                       # 各項目が各自 2 回リトライ
       .Text("失敗する可能性あり").Image("こちらも失敗する可能性あり")
       .send_all())
```

### 整体のルールとコールバック

ルールは全体に一律に作用します：

| メソッド | 説明 |
|--------|------|
| `.Timeout(seconds)` | 各送信の1回のタイムアウト |
| `.Retry(times)` | 各送信の各自のリトライ（失敗時の継続） |
| `.Defer(seconds)` | 整体の遅延送信 |
| `.Hook(callback)` | 全体が成功した後にトリガー、`results` リストを受け取ります |
| `.OnError(callback)` | バッチに失敗が存在する場合にトリガー、`BatchContext` を受け取ります |
| `.OnProgress(callback)` | 各項目の完了時にトリガー、`BatchContext` を受け取ります |

```python
def on_progress(ctx):
    print(f"進捗: {ctx.completed}/{ctx.total}, 成功 {ctx.succeeded}, 失敗 {ctx.failed}")

async def on_error(ctx):
    print(f"バッチに {ctx.failed} 件の失敗があります")

results = await (adapter.Send.To("user", "123")
               .Build()
               .Retry(2).Timeout(10)
               .OnProgress(on_progress)
               .OnError(on_error)
               .Hook(lambda rs: print("全体完了"))
               .Text("a").Text("b").Text("c")
               .send_all())
```

`BatchContext` が含むもの：`task_id`、`total`、`completed`、`succeeded`、`failed`、`stage`、`results`、`errors`、`elapsed`、`extra`。

`stage` の可能性のある値：`pending`、`sending`、`success`（全成功）、`partial`（一部成功）、`failed`（全失敗）。

### デコレータとルールの継承

`.Build()` 以前の At/AtAll/Reply デコレータとルールは全体に継承され、各メッセージに作用します：

```python
await (adapter.Send.To("group", "456")
       .At("789")                        # 継承：すべてのメッセージが @789
       .Build()
       .Retry(2)                         # 継承 + 追加：各項目がそれぞれリトライ
       .Text("@あなたへの通知")
       .Image("告知画像")
       .send_all())
```

Build に入った後もデコレータを追加できます（全体に作用します）：

```python
await (adapter.Send.To("group", "456")
       .Build()
       .At("111").At("222")             # 追加 @、全体に作用
       .Text("@複数人")
       .send_all())
```

### バックグラウンド実行

単発と同様、`.send_all()` は Task を返し、await しなければバックグラウンドで実行できます：

```python
task = (adapter.Send.To("user", "123")
        .Build()
        .Hook(lambda rs: print("バッチ送信完了"))
        .Text("a").Text("b")
        .send_all())

# メインフローをブロックしない
await do_something_else()
```

## 命名規則

### PascalCase 命名

すべての送信メソッドはパスカルケースを使用します：

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

プラットフォームプレフィックスのメソッドの追加は推奨されません：

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
```

## 戻り値

### Task オブジェクト

すべての送信メソッドは `asyncio.Task` を返します。アダプターは `Raw_ob12` のみを実装し、標準メソッド（Text/Image など）はデフォルトでそれに委譲します：

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

# Text/Image/Voice/File は基底クラスから継承し、自動的に Raw_ob12 に委譲されます
# 標準メソッドを上書きする必要がある場合は、asyncio.Task を返すだけです：
# def Text(self, text: str):
#     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

### 標準化された応答

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

手動構築もサポートされています（旧方式も互換性があります）：

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
await my_adapter.Send.To("group", "456").At("789").Reply("msg123").Text("返信@メッセージ")

# @全員 + 複数の修飾
await my_adapter.Send.Using("bot1").To("group", "456").AtAll().Text("告知メッセージ")
```

### 生のメッセージとメッセージビルド

`Raw_ob12` は「OneBot12 メッセージセグメント → プラットフォーム API 呼び出し」への逆変換の核心的なエントリポイントであり、`MessageBuilder` はそれと組み合わせて使用されるチェーンメソッドベースのメッセージセグメントビルドツールです。

> 完全な `Raw_ob12` 実装仕様、`MessageBuilder` の使用法およびコード例については、以下を参照してください：
> - [送信メソッド仕様 §6 逆変換仕様](../../standards/send-method-spec.md#6-逆変換仕様onebot12--プラットフォーム)
> - [送信メソッド仕様 §11 メッセージビルダー](../../standards/send-method-spec.md#11-メッセージビルダー-messagebuilder)

## 関連ドキュメント

- [アダプター開発入門](getting-started.md) - アダプターの作成
- [アダプターのコア概念](core-concepts.md) - アダプターのアーキテクチャを理解する
- [アダプターのベストプラクティス](best-practices.md) - 高品質なアダプターの開発
- [送信メソッド仕様](../../standards/send-method-spec.md) - 送信メソッドの完全な仕様