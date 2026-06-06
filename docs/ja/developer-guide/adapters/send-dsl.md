# SendDSL 詳解

SendDSL は、ErisPulse アダプターが提供するメソッドチェーンスタイルのメッセージ送信インターフェースです。

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

| メソッド名 | 説明 | 戻り値 |
|--------|------|---------|
| `Text(text: str)` | テキストメッセージを送信 | `asyncio.Task` |
| `Image(file: bytes \| str)` | 画像を送信 | `asyncio.Task` |
| `Voice(file: bytes \| str)` | 音声を送信 | `asyncio.Task` |
| `Video(file: bytes \| str)` | 動画を送信 | `asyncio.Task` |
| `File(file: bytes \| str)` | ファイルを送信 | `asyncio.Task` |

### プロトコルメソッド

| メソッド名 | 説明 | 戻り値 | 必須 |
|--------|------|---------|---------|
| `Raw_ob12(message)` | OneBot12 形式のメッセージを送信 | `asyncio.Task` | **実装必須** |

> **重要**：`Raw_ob12` はアダプターのコアメソッドであり、**実装が必須**です。これはリバース変換（OneBot12 → プラットフォーム）の統一エントリポイントです。未実装の場合、基底クラスは error ログを記録し、標準エラーレスポンス（`status: "failed"`, `retcode: 10002`）を返します。標準メソッド（`Text`、`Image` など）は内部で `Raw_ob12` に委譲する必要があります。

## 修飾メソッド

修飾メソッドはメソッドチェーンをサポートするために `self` を返します。

### At メソッド

```python
# 単一ユーザーをメンション
await adapter.Send.To("group", "123").At("456").Text("你好")

# 複数ユーザーをメンション
await adapter.Send.To("group", "123").At("456").At("789").Text("你们好")
```

### AtAll メソッド

```python
# 全員をメンション
await adapter.Send.To("group", "123").AtAll().Text("大家好")
```

### Reply メソッド

```python
# メッセージに返信
await adapter.Send.To("group", "123").Reply("msg_id").Text("回复内容")
```

### 組み合わせ修飾

```python
await adapter.Send.To("group", "123").At("456").Reply("msg_id").Text("回复@的消息")
```

## アカウント管理

### Using メソッド

```python
# アカウント名を使用
await adapter.Send.Using("account1").To("user", "123").Text("Hello")

# アカウントIDを使用
await adapter.Send.Using("bot_id").To("user", "123").Text("Hello")
```

### Account メソッド

`Account` メソッドは `Using` と同等です：

```python
await adapter.Send.Account("account1").To("user", "123").Text("Hello")
```

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
# 直接 await して結果を取得します
result = await adapter.Send.To("user", "123").Text("Hello")
print(f"送信結果: {result}")

# まず Task を保存し、後で待機します
task = adapter.Send.To("user", "123").Text("Hello")
# ... 他の操作 ...
result = await task
```

## 命名規則

### PascalCase 命名

すべての送信メソッドはアッパーキャメルケース（PascalCase）を使用します：

```python
# ✅ 正しい
def Text(self, text: str):
    pass

def Image(self, file: bytes):
    pass

# ❌ 間違い
def text(self, text: str):
    pass

def send_image(self, file: bytes):
    pass
```

### プラットフォーム固有のメソッド

プラットフォームのプレフィックスを付けたメソッドの追加は推奨されません：

```python
# ✅ 推奨
def Sticker(self, sticker_id: str):
    pass

# ❌ 非推奨
def TelegramSticker(self, sticker_id: str):
    pass
```

代わりに `Raw` メソッドを使用します：

```python
# ✅ 推奨
await adapter.Send.Raw_ob12([{"type": "sticker", ...}])

# ❌ 非推奨
def TelegramSticker(self, ...):
    pass
```

## 戻り値

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

`call_api` は標準化されたレスポンスを返す必要があります。`make_response()` / `make_error()` メソッドの使用が推奨されます：

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

手動構築もサポートしています（旧版方式も互換性があります）：

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

### メソッドチェーン

```python
# ユーザーをメンション + 返信
await my_adapter.Send.To("group", "456").At("789").Reply("msg123").Text("回复@的消息")

# 全員をメンション + 複数の修飾
await my_adapter.Send.Using("bot1").To("group", "456").AtAll().Text("公告消息")
```

### 生メッセージとメッセージ構築

`Raw_ob12` はリバース変換のコアエントリポイント（OB12 メッセージセグメントの受信 → プラットフォーム API 呼び出し）であり、`MessageBuilder` はそれと組み合わせて使用されるメソッドチェーン式のメッセージセグメント構築ツールです。

> 完全な `Raw_ob12` の実装仕様、`MessageBuilder` の使用法、およびコード例については以下を参照してください：
> - [送信メソッド仕様 §6 リバース変換仕様](../../standards/send-method-spec.md#6-反向转换规范onebot12--平台)
> - [送信メソッド仕様 §11 メッセージビルダー](../../standards/send-method-spec.md#11-消息构建器-messagebuilder)

## 関連ドキュメント

- [アダプター開発入門](getting-started.md) - アダプターの作成
- [アダプターのコア概念](core-concepts.md) - アダプターのアーキテクチャを理解する
- [アダプターのベストプラクティス](best-practices.md) - 高品質なアダプターの開発
- [送信メソッド仕様](../../standards/send-method-spec.md) - 送信メソッドの完全な仕様