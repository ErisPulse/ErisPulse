# SendDSL の詳細

SendDSL は、ErisPulse アダプターによって提供されるチェーン呼び出しスタイルのメッセージ送信インターフェースです。

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

すべての送信メソッドは `asyncio.Task` オブジェクトを返す必要があります。

### 基本メソッド

| メソッド名 | 説明 | 返り値 |
|--------|------|---------|
| `Text(text: str)` | テキストメッセージを送信 | `asyncio.Task` |
| `Image(file: bytes \| str)` | 画像を送信 | `asyncio.Task` |
| `Voice(file: bytes \| str)` | 音声を送信 | `asyncio.Task` |
| `Video(file: bytes \| str)` | ビデオを送信 | `asyncio.Task` |
| `File(file: bytes \| str)` | ファイルを送信 | `asyncio.Task` |

### プロトコルメソッド

| メソッド名 | 説明 | 返り値 | 必須 |
|--------|------|---------|---------|
| `Raw_ob12(message)` | OneBot12 形式メッセージを送信 | `asyncio.Task` | **実装必須** |

> **重要**：`Raw_ob12` はアダプターの核心的なメソッドであり、**実装必須**です。これはリバース変換（OneBot12 → プラットフォーム）の統一されたエントリポイントです。実装されていない場合、ベースクラスは error ログを記録し、標準的なエラーレスポンス（`status: "failed"`, `retcode: 10002`）を返します。標準メソッド（`Text`、`Image` など）の内部では、`Raw_ob12` に委譲する必要があります。

## 修飾メソッド

修飾メソッドはチェーン呼び出しをサポートするために `self` を返します。

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
await adapter.Send.To("group", "123").At("456").Reply("msg_id").Text("返信したメッセージ")
```

## アカウント管理

### Using メソッド

`Using()` はメッセージを送信するアカウントを指定するために使用します。渡された識別子は以下の優先順位で `_resolve_account()` を通じて照合されます。

1. **アカウント名** — 設定内のキー名（例: `"default"`、`"bot1"`）
2. **実行時注入された bot_id** — イベント変換時に自動的に注入される識別子
3. **任意の str フィールド** — 設定内の他の文字列フィールド
4. **フォールバック** — 有効になっている最初のアカウント

```python
# アカウント名を使用
await adapter.Send.Using("account1").To("user", "123").Text("Hello")

# bot_id を使用（つまりイベント内の self.user_id）
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

# 他の操作を継続
# ...
```

### 結果を待つ

```python
# 直接 await して結果を取得
result = await adapter.Send.To("user", "123").Text("Hello")
print(f"送信結果: {result}")

# 先に Task を保存し、後で待つ
task = adapter.Send.To("user", "123").Text("Hello")
# ... 他の操作 ...
result = await task
```

## 送信ルールシステム

SendDSL は組み込みの送信ルールデコレーターを備えており、チェーンメソッドを通じてルールを追加し、最終的な送信時に一括して適用します。ルールは一般的なプロダクションシナリオをカバーしています：タイムアウト制御、失敗リトライ、成功時のコールバック、遅延送信、優先度順スキップ、進捗監視。

ルールメソッドは**`self` を返す**（At/AtAll/Reply と同様）、かつ送信メソッド（Text/Image など）の前に呼び出す必要があります。ルールは `To`/`Using`/`Account` で作成された新しいインスタンスに伝播します。

### ルールメソッド一覧

| メソッド | 説明 |
|--------|------|
| `.Hook(callback)` | 送信成功後に実行されるコールバック（複数回呼び出可能、順次実行） |
| `.Retry(times=1)` | 失敗時に自動的に N 回リトライ（初回を含む合計 N+1 回） |
| `.Timeout(seconds)` | 送信タイムアウト、タイムアウト時に現在の試行をキャンセル（Retry と組み合わせ可能） |
| `.Defer(seconds=1.0)` | 遅延送信（プロセス内でのタイマー、永続化なし） |
| `.Priority(level, drop_if_busy=False)` | 優先度を設定；積圧時にドロップ可能 |
| `.OnProgress(callback)` | 各段階の進捗コールバック（`SendContext` を受け取る） |
| `.OnError(callback)` | 最終的な失敗時のエラーコールバック（一度のみトリガー） |

### 送信成功時の実行ロジック（Hook）

```python
# 同期コールバック
await (adapter.Send.To("user", "123")
       .Hook(lambda r: print(f"送信成功、メッセージID: {r['message_id']}"))
       .Text("こんにちは"))

# 非同期コールバック
async def deduct_points(result):
    await db.update(user_id="123", points=-1)

await adapter.Send.To("user", "123").Hook(deduct_points).Text("ポイントを消費")
```

Hook は送信が最終的に成功した場合（リトライ成功含む）にのみ実行されます；失敗、タイムアウト、キャンセルではトリガーされません。

### 自動リトライ（Retry）

```python
# 初回失敗後に 2 回リトライ、合計 3 回の試行
result = await adapter.Send.To("user", "123").Retry(2).Text("リトライあり")
```

リトライのトリガー条件：送信時に例外がスローされる、送信タイムアウト、送信で `status == "failed"` のレスポンスが返される。

### タイムアウトによる自動キャンセル（Timeout）

```python
# 送信が 10 秒を超えたらキャンセル
await adapter.Send.To("user", "123").Timeout(10).Text("タイムアウトあり")

# タイムアウト + リトライ：各試行 10 秒、最大 3 回
await adapter.Send.To("user", "123").Timeout(10).Retry(2).Text("タイムアウトリトライ")
```

### 進捗監視（OnProgress / OnError）

```python
def on_progress(ctx):
    print(f"段階: {ctx.stage}, 試行: {ctx.attempt + 1}/{ctx.max_attempts}, 所要時間: {ctx.elapsed:.2f}s")
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

`stage` の可能な値：`pending`、`sending`、`retrying`、`success`、`failed`、`timeout`、`cancelled`、`dropped`。

### 遅延送信（Defer）

```python
# 5 秒後に送信
await adapter.Send.To("user", "123").Defer(5).Text("遅延メッセージ")
```

> 注意：遅延はプロセス内でのタイマーであり、プロセス再起動で失われます、永続化は提供されません。

### 優先度と積圧でのドロップ（Priority）

```python
# 低優先度メッセージ、キューが積圧している場合は自動的にドロップ
result = await (adapter.Send.To("user", "123")
               .Priority(-1, drop_if_busy=True)
               .Text("ドロップ可能な通知"))
# ドロップされた場合、result["status"] == "failed"
```

`drop_if_busy` を有効にすると、送信中のタスク数が閾値を超えた（デフォルト 64）場合、今回の送信を直接放棄します。グローバルな閾値は `.PriorityThreshold(n)` で調整できます。

### ルールの組み合わせとバックグラウンド実行

```python
# メインフローをブロックせず、ルールは有効にする
task = (adapter.Send.To("user", "123")
        .Hook(lambda r: print("送信成功！"))
        .Retry(3)
        .Timeout(10)
        .OnProgress(on_progress)
        .Text("こんにちは"))

# 他の操作を継続
await handle_next_action()
```

### ルールの伝播

ルールは `To`/`Using`/`Account` で作成された新しいインスタンスに伝播し、チェーン呼び出し内でルールが失われることを防ぎます：

```python
# ルールを To の前に設定すると、To が作成したインスタンスにも伝播
builder = adapter.Send.Retry(3).Timeout(10)
send = builder.To("user", "123")  # send はまだ Retry(3) と Timeout(10) を保持
await send.Text("hi")
```

複数のインスタンスのルールは相互に独立しています（hooks リストはディープコピー）。

## バッチ構築モード（Build）

単発モッドのほかに、SendDSL はバッチ構築モードもサポートしています：1つのチェーンで複数の送信メソッドを書き、最後にまとめて実行します。「一気に複数メッセージを送信する」シナリオに適しています。

### バッチ構築モードに入る

送信メソッドの前に `.Build()` を呼び出し、`SendBuilder` を返します。その後の送信メソッド（Text/Image など）は即時実行されず、送信の意図として蓄積されます：

```python
results = await (adapter.Send.To("user", "123")
                 .Build()                    # バッチ構築モードに入る
                 .Text("第一句")
                 .Image("pic.jpg")
                 .Text("第二句")
                 .send_all())                 # 一括実行
# results = [Text結果, Image結果, Text結果]
```

`.send_all()` は `asyncio.Task` を返し、await すると結果のリスト（意図の順序通り）が得られます。

### 並列と直列

デフォルトで**並列**実行されます（並行送信、合計所要時間は最も遅いものにほぼ等しくなります）。メッセージの到着順序を保証する必要がある場合は `.Sequential()` を呼び出します：

```python
# 直列：順次に送信
await (adapter.Send.To("group", "456")
       .Build()
       .Sequential()
       .Text("まずこれ").Text("次にこれ")
       .send_all())

# 並列（デフォルト、明示的に呼び出しても可）
await (adapter.Send.To("group", "456")
       .Build()
       .Parallel()
       .Text("並列1").Text("並列2")
       .send_all())
```

### 失敗時の継続とリトライ

バッチ実行では**失敗時の継続**戦略を採用しています：特定のメッセージの失敗は他のメッセージの送信を中断しません。`.Retry()` と組み合わせると、失敗した項目は自動的にリトライされます（リトライは個別の項目に対して適用され、バッチ全体に対しては適用されません）：

```python
await (adapter.Send.To("user", "123")
       .Build()
       .Retry(2)                       # 各項目が個別に 2 回リトライ
       .Text("失敗する可能性あり").Image("失敗する可能性あり")
       .send_all())
```

### バッチ全体のルールとコールバック

ルールはバッチ全体に統一して適用されます：

| メソッド | 説明 |
|--------|------|
| `.Timeout(seconds)` | 各メッセージ送信のタイムアウト |
| `.Retry(times)` | 各メッセージ送信が個別にリトライ（失敗時の継続） |
| `.Defer(seconds)` | バッチ全体を遅延送信 |
| `.Hook(callback)` | バッチ全体が成功した後にトリガー、`results` リストを受け取る |
| `.OnError(callback)` | バッチ内で失敗が存在した場合にトリガー、`BatchContext` を受け取る |
| `.OnProgress(callback)` | 各項目が完了した時にトリガー、`BatchContext` を受け取る |

```python
def on_progress(ctx):
    print(f"進捗: {ctx.completed}/{ctx.total}, 成功 {ctx.succeeded}, 失敗 {ctx.failed}")

async def on_error(ctx):
    print(f"バッチで {ctx.failed} 件失敗")

results = await (adapter.Send.To("user", "123")
               .Build()
               .Retry(2).Timeout(10)
               .OnProgress(on_progress)
               .OnError(on_error)
               .Hook(lambda rs: print("バッチ完了"))
               .Text("a").Text("b").Text("c")
               .send_all())
```

`BatchContext` が含む：`task_id`、`total`、`completed`、`succeeded`、`failed`、`stage`、`results`、`errors`、`elapsed`、`extra`。

`stage` の可能な値：`pending`、`sending`、`success`（すべて成功）、`partial`（一部成功）、`failed`（すべて失敗）。

### デコレーターとルールの継承

`.Build()` の前の At/AtAll/Reply デコレーターとルールはバッチ全体に継承され、各メッセージに適用されます：

```python
await (adapter.Send.To("group", "456")
       .At("789")                        # 継承：すべてのメッセージが @789
       .Build()
       .Retry(2)                         # 継承 + 追加：各項目が個別にリトライ
       .Text("@あなたへの通知")
       .Image("お知らせ画像")
       .send_all())
```

Build 入り後もデコレーター（バッチ全体に適用）を追加できます：

```python
await (adapter.Send.To("group", "456")
       .Build()
       .At("111").At("222")             # 追加 @、バッチ全体に適用
       .Text("@複数人")
       .send_all())
```

### バックグラウンド実行

単発と同様、`.send_all()` は Task を返し、await せずにバックグラウンドで実行させることができます：

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

すべての送信メソッドはキャメルケース（PascalCase）を使用します：

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

プラットフォームプレフィックスのメソッドを追加することは推奨されません：

```python
# ✅ 推奨
def Sticker(self, sticker_id: str):
    pass

# ❌ 推奨しない
def TelegramSticker(self, sticker_id: str):
    pass
```

`Raw` メソッドを使用します：

```python
# ✅ 推奨
await adapter.Send.Raw_ob12([{"type": "sticker", ...}])

# ❌ 推奨しない
def TelegramSticker(self, ...):
    pass
```

## 返り値

### Task オブジェクト

すべての送信メソッドは `asyncio.Task` を返します：

```python
import asyncio

def Text(self, text: str):
    return asyncio.create_task(
        self._adapter.call_api(
            endpoint="/send",
            content=text,
            recvId=self._target_id,
            recvType=self._target_type
        )
    )
```

### 標準化されたレスポンス

`call_api` は標準化されたレスポンスを返す必要があります。`make_response()` / `make_error()` メソッドの使用を推奨します：

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

手動構築もサポートされています（古い方式も依然として互換性があります）：

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
await my_adapter.Send.To("group", "456").At("789").Reply("msg123").Text("返信したメッセージ")

# @全員 + 複数の修飾
await my_adapter.Send.Using("bot1").To("group", "456").AtAll().Text("お知らせメッセージ")
```

### 生のメッセージとメッセージ構築

`Raw_ob12` はリバース変換の核心的なエントリポイント（OB12 メッセージセグメントを受け取る → プラットフォーム API の呼び出し）、`MessageBuilder` はそれに合わせて使用されるチェーンメッセージセグメント構築ツールです。

> 完全な `Raw_ob12` 実装仕様、`MessageBuilder` の使用方法およびコード例については以下を参照してください：
> - [送信メソッド仕様 §6 リバース変換仕様](../../standards/send-method-spec.md#6-リバース変換仕様onebot12--プラットフォーム)
> - [送信メソッド仕様 §11 メッセージビルダー](../../standards/send-method-spec.md#11-メッセージビルダー-messagebuilder)

## 関連ドキュメント

- [アダプター開発入門](getting-started.md) - アダプターの作成
- [アダプターの核心概念](core-concepts.md) - アダプターのアーキテクチャを理解する
- [アダプターのベストプラクティス](best-practices.md) - 高品質なアダプターの開発
- [送信メソッド仕様](../../standards/send-method-spec.md) - 送信メソッドの完全な仕様