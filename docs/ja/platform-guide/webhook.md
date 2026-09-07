# プラットフォームの機能説明 — Webhook 一般的なブリッジアダプター

このドキュメントでは、Webhookアダプターの双方向ブリッジプロトコル、フィールドマッピング、実装の特徴について詳しく説明します。

## 概要

Webhook アダプタは、**プロトコルレベルのブリッジ**です。特定のプラットフォームに縛られることなく、HTTP経由でメッセージを受け渡します。HTTPリクエストを発行できる任意のシステムを ErisPulse に接続できます。

```
受信方向                                送信方向
────────                                ────────
外部システム                                ErisPulse モジュール
   │                                       │
   │ POST JSON                             │ Send.Text(...)
   ▼                                       ▼
┌──────────────────────────────────────────────────┐
│              WebhookAdapter                       │
│  ┌──────────────────┐   ┌──────────────────┐    │
│  │ 受信ルート          │   │ 送信転送          │    │
│  │ GET  (健康チェック)   │   │ client.post()    │    │
│  │ POST (イベント受信)   │   │ → outgoing_url   │    │
│  └────────┬─────────┘   └────────▲─────────┘    │
│           │                      │               │
│           ▼                      │               │
│  ┌──────────────────┐   ┌──────────────────┐    │
│  │ WebhookConverter │   │ Send クラス      │    │
│  │ JSON → OneBot12  │   │ メッセージセグメント → JSON │    │
│  └────────┬─────────┘   └────────▲─────────┘    │
└───────────┼──────────────────────┼───────────────┘
            ▼                      │
     adapter.emit(event)    call_api("send_message")
            │                      │
            ▼                      │
       ErisPulse イベントシステム ◄────────┘
```

## 複数アカウントモデル

各アカウントは、互いに干渉しない独立したブリッジ設定です。

| アカウント | bot_id | callback_path | outgoing_url | secret |
|------|--------|---------------|--------------|--------|
| `default` | `webhook_bot` | `/webhook/default` | `https://a.com/recv` | `key1` |
| `discord` | `discord_bot` | `/webhook/discord` | `https://b.com/send` | `key2` |

各アカウントは、起動時に独立してルートを登録し、独立して emit connect を行います。

## 入站プロトコル

### 1. ヘルスチェック（GET）

- **パス**：`{callback_path}`
- **メソッド**：`GET`
- **認証**：なし
- **レスポンス**：

```json
{"status": "ok", "account": "default"}
```

### 2. イベントの受信（POST）

- **パス**：`{callback_path}`
- **メソッド**：`POST`
- **Content-Type**：`application/json`
- **認証**（secret設定時）：Header `X-Webhook-Secret` または Query `?secret=`

#### リクエストボディ

```json
{
  "user_id": "u123",
  "user_nickname": "用户名",
  "group_id": "群组ID（仅群组会话）",
  "detail_type": "private",
  "message": [
    {"type": "text", "data": {"text": "消息内容"}}
  ],
  "raw": {}
}
```

| フィールド | 必須 | 説明 |
|----------|------|------|
| `user_id` | はい | 送信者ID |
| `user_nickname` | いいえ | 送信者ニックネーム |
| `group_id` | いいえ | グループ/チャンネルID（グループ会話時提供） |
| `detail_type` | いいえ | 会話の種類（`private`/`group`）、省略時はアカウントのデフォルト値を使用 |
| `message` | はい | OneBot12 メッセージセグメントの配列 |
| `raw` | いいえ | 送信されたデータ、`webhook_raw` にそのまま保存 |

#### レスポンス

```json
{"status": "ok"}
```

エラーの際はHTTPステータスコードを返します：

| ステータスコード | 内容 |
|------------------|------|
| 400 | 不正なJSON / bodyがオブジェクトでない |
| 401 | 認証失敗 |
| 404 | 未知のアカウント |
| 500 | イベント配信失敗 |

### 3. フィールドマッピング（入力JSON → OneBot12イベント）

| 入力JSON | OneBot12イベントのフィールド | 説明 |
|----------|-----------------------------|------|
| — | `id` | 自動生成 |
| — | `time` | 現在のUnixタイムスタンプ（秒） |
| — | `type` | 固定値 `message` |
| `detail_type` | `detail_type` | 省略時はアカウントのデフォルト値を使用 |
| — | `platform` | 固定値 `webhook` |
| — | `self.platform` | 固定値 `webhook` |
| — | `self.user_id` | アカウントの `bot_id` |
| `user_id` | `user_id` | そのまま透過 |
| `user_nickname` | `user_nickname` | そのまま透過（オプション） |
| `group_id` | `group_id` | そのまま透過（オプション） |
| `message` | `message` | そのまま透過 |
| 完全なbody | `webhook_raw` | 元のリクエスト |
| アカウント名 | `webhook_account` | イベントを生成したアカウント名 |
| `type` または `message` | `webhook_raw_type` | 元のイベントの種類 |

## 出力プロトコル

### 1. メッセージ送信

モジュールが `Send.To(...).Text(...)` などのメソッドを呼び出した場合、アダプターは `outgoing_url` に POST リクエストを送信します。

- **メソッド**：`POST`
- **Content-Type**：`application/json`
- **認証用ヘッダー**（secret が設定されている場合）：`X-Webhook-Secret: {secret}`

#### リクエストボディ

```json
{
  "target_type": "private",
  "target_id": "target_user_id",
  "account": "default",
  "message": [
    {"type": "text", "data": {"text": "メッセージ内容"}}
  ],
  "timestamp": 1700000000
}
```

| フィールド | 説明 |
|------|------|
| `target_type` | 目標の種類（`Send.To(type, id)` から取得、省略時はアカウントのデフォルト値） |
| `target_id` | 目標の ID（`Send.To` から取得） |
| `account` | 送信するアカウント名 |
| `message` | OneBot12 メッセージセグメントの配列 |
| `timestamp` | 送信時刻のタイムスタンプ（秒） |

### 2. 応答の標準化

アダプターは出力先が返す応答を ErisPulse の標準応答形式に標準化します。

```json
{
  "status": "ok",
  "retcode": 0,
  "data": {"message_id": "...", ...},
  "message_id": "...",
  "message": "",
  "webhook_raw": {}
}
```

出力先の JSON 応答から `message_id` フィールドを抽出してメッセージ ID を取得します。出力先が `message_id` を返さない場合は、空文字列になります。

リクエストに失敗した場合はエラー応答を返します（`status: "failed"`, `retcode: 33001`）。

## Send メソッド

| メソッド | 説明 |
|------|------|
| `Text(text)` | テキストを送信し、`[{"type":"text","data":{"text":text}}]` にラップします |
| `Image(file)` | 画像を送信し、`[{"type":"image","data":{"file":file}}]` にラップします |
| `Raw_ob12(message)` | OneBot12 の生メッセージセグメントを送信します |
| `Json(data)` | 生の JSON を透過的に送信し、`[{"type":"json","data":{"raw":data}}]` にラップします |

`At` / `AtAll` / `Reply` 修飾子は、フレームワークの基底クラスによって提供され、`_apply_modifiers` によってメッセージセグメントにマージされます。

## イベント拡張メソッド (WebhookEventMixin)

| メソッド | 説明 |
|------|------|
| `get_raw_data()` | 元のリクエスト body (`webhook_raw`) を取得します |
| `get_detail_type()` | 会話の種類を取得します |
| `get_webhook_account()` | このイベントを生成したアカウント名を取得します |

## 特性マトリクス

| 特性 | 支持状況 |
|------|----------|
| 多アカウント | ✅ 各アカウントごとに独立したブリッジ |
| 入站認証 | ✅ Header / Query の両モード |
| ヘルスチェック | ✅ GET でステータスを返す |
| 出站認証 | ✅ Header に secret を含む |
| OneBot12 標準イベント | ✅ 完全な標準フィールド |
| Meta イベント | ✅ connect / disconnect |
| ルーティング発見 | ✅ `webhook` 名前空間に登録 |
| WebSocket | ❌ HTTP 場合のみ |
| メディアアップロード | ❌ URL を透過するのみ、バイナリを代行転送しない |

## 注意事項

1. **単方向出力**：`outgoing_url` が空の場合は、このアカウントは入力のみを受け付け、送信操作はエラーを返します。
2. **秘密鍵の安全性**：`secret` は設定で暗号化された形式（metadata secret）で保存され、通信には HTTPS を使用することを推奨します。
3. **パスの一意性**：複数のアカウントの `callback_path` は互いに異なる必要があります。ルーティングの競合を避けるためです。
4. **冪等性**：アダプターは入力イベントの重複排除を保証しません。外部システムがリトライ処理を独自に実行する必要があります。
5. **タイムアウト**：出力リクエストは ErisPulse の組み込み `client` を使用し、グローバルなタイムアウト設定を継承します。