# プラットフォームの特徴説明 — Webhook 一般ブリッジアダプタ

このドキュメントは、Webhookアダプタの双方向ブリッジプロトコル、フィールドマッピング、実装の特徴について詳しく説明します。

## 概要

Webhookアダプタは**プロトコルレベルのブリッジ**であり、特定のプラットフォームに縛られていません。HTTP経由でメッセージを送受信することで、HTTPリクエストを発行可能な任意のシステムをErisPulseに接続できます。

```
インバウンド方向                                オットバウンド方向
────────                                ────────
外部システム                                ErisPulse モジュール
   │                                       │
   │ POST JSON                             │ Send.Text(...)
   ▼                                       ▼
┌──────────────────────────────────────────────────┐
│              WebhookAdapter                       │
│  ┌──────────────────┐   ┌──────────────────┐    │
│  │ 入力ルーティング  │   │ 出力フォワード    │    │
│  │ GET  (ヘルスチェック)   │   │ client.post()    │    │
│  │ POST (イベント受信)   │   │ → outgoing_url   │    │
│  └────────┬─────────┘   └────────▲─────────┘    │
│           │                      │               │
│           ▼                      │               │
│  ┌──────────────────┐   ┌──────────────────┐    │
│  │ WebhookConverter │   │ Send クラス        │    │
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

各アカウントは独立したブリッジ設定であり、互いに影響しません。

| アカウント | bot_id | callback_path | outgoing_url | secret |
|------|--------|---------------|--------------|--------|
| `default` | `webhook_bot` | `/webhook/default` | `https://a.com/recv` | `key1` |
| `discord` | `discord_bot` | `/webhook/discord` | `https://b.com/send` | `key2` |

各アカウントは起動時に独立したルーティングを登録し、独立して emit connect を行います。

## 入力プロトコル

### 1. ヘルスチェック（GET）

- **パス**: `{callback_path}`
- **メソッド**: `GET`
- **認証**: なし
- **レスポンス**:

```json
{"status": "ok", "account": "default"}
```

### 2. イベント受信（POST）

- **パス**: `{callback_path}`
- **メソッド**: `POST`
- **Content-Type**: `application/json`
- **認証**（secretを設定した場合）: ヘッダー `X-Webhook-Secret` またはクエリ `?secret=`

#### リクエストボディ

```json
{
  "user_id": "u123",
  "user_nickname": "ユーザー名",
  "group_id": "グループID（グループ会話のみ）",
  "detail_type": "private",
  "message": [
    {"type": "text", "data": {"text": "メッセージ内容"}}
  ],
  "raw": {}
}
```

| フィールド | 必須 | 説明 |
|------|------|------|
| `user_id` | はい | 送信者ID |
| `user_nickname` | いいえ | 送信者ニックネーム |
| `group_id` | いいえ | グループ/チャンネルID（グループ会話時に提供） |
| `detail_type` | いいえ | 会話タイプ（`private`/`group`）、未指定時はアカウントのデフォルト値を使用 |
| `message` | はい | OneBot12 メッセージセグメント配列 |
| `raw` | いいえ | 送信元データ、`webhook_raw` にそのまま格納 |

#### レスポンス

```json
{"status": "ok"}
```

エラーの場合はHTTPステータスコードを含みます：

| ステータスコード | 意味 |
|--------|------|
| 400 | 不正なJSON / bodyがオブジェクトでない |
| 401 | 認証失敗 |
| 404 | 未知のアカウント |
| 500 | イベントの配信失敗 |

### 3. フィールドマッピング（入力JSON → OneBot12 イベント）

| 入力JSON | OneBot12 イベントフィールド | 説明 |
|-----------|-------------------|------|
| — | `id` | 自動生成 |
| — | `time` | 現在のUnixタイムスタンプ（秒） |
| — | `type` | 固定 `message` |
| `detail_type` | `detail_type` | 未指定時はアカウントのデフォルト値を使用 |
| — | `platform` | 固定 `webhook` |
| — | `self.platform` | 固定 `webhook` |
| — | `self.user_id` | アカウント `bot_id` |
| `user_id` | `user_id` | そのまま透過 |
| `user_nickname` | `user_nickname` | そのまま透過（オプション） |
| `group_id` | `group_id` | そのまま透過（オプション） |
| `message` | `message` | そのまま透過 |
| 完全なbody | `webhook_raw` | 元のリクエスト |
| アカウント名 | `webhook_account` | イベントを生成したアカウント名 |
| `type` または `message` | `webhook_raw_type` | 元のイベントタイプ |

## 出力プロトコル

### 1. メッセージ送信

モジュールが `Send.To(...).Text(...)` などのメソッドを呼び出すと、アダプタは `outgoing_url` にPOSTリクエストを送信します：

- **メソッド**: `POST`
- **Content-Type**: `application/json`
- **認証ヘッダー**（secretを設定した場合）: `X-Webhook-Secret: {secret}`

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
| `target_type` | 目標タイプ（`Send.To(type, id)` から取得）、未指定時はアカウントのデフォルト値を使用 |
| `target_id` | 目標ID（`Send.To` から取得） |
| `account` | 送信アカウント名 |
| `message` | OneBot12 メッセージセグメント配列 |
| `timestamp` | 送信タイムスタンプ（秒） |

### 2. レスポンスの標準化

アダプタは出力先が返すレスポンスをErisPulseの標準レスポンス形式に標準化します：

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

出力先のレスポンスJSONの `message_id` フィールドからメッセージIDを抽出します。出力先が `message_id` を返さない場合は空文字列です。

リクエストが失敗した場合はエラーレスポンスを返します（`status: "failed"`, `retcode: 33001`）。

## Send メソッド

| メソッド | 説明 |
|------|------|
| `Text(text)` | テキストを送信し、`[{"type":"text","data":{"text":text}}]` にラップ |
| `Image(file)` | 画像を送信し、`[{"type":"image","data":{"file":file}}]` にラップ |
| `Raw_ob12(message)` | OneBot12の元のメッセージセグメントを送信 |
| `Json(data)` | 元のJSONを透過し、`[{"type":"json","data":{"raw":data}}]` にラップ |

`At` / `AtAll` / `Reply` 修飾子はフレームワークの基底クラスが提供し、`_apply_modifiers` でメッセージセグメントにマージされます。

## イベント拡張メソッド（WebhookEventMixin）

| メソッド | 説明 |
|------|------|
| `get_raw_data()` | 元のリクエストbody（`webhook_raw`）を取得 |
| `get_detail_type()` | 会話タイプを取得 |
| `get_webhook_account()` | このイベントを生成したアカウント名を取得 |

## 特性マトリクス

| 特性 | 対応状況 |
|------|----------|
| 複数アカウント | ✅ 各アカウントが独立したブリッジを提供 |
| 入力認証 | ✅ ヘッダー / クエリの両モード |
| ヘルスチェック | ✅ GETでステータスを返す |
| 出力認証 | ✅ ヘッダーにsecretを含む |
| OneBot12標準イベント | ✅ 完全な標準フィールド |
| Metaイベント | ✅ connect / disconnect |
| ルーティング発見 | ✅ `webhook`名前空間に登録 |
| WebSocket | ❌ HTTPのみ |
| メディアアップロード | ❌ URLを透過するのみ、バイナリデータの代行送信は行わない |

## 注意事項

1. **単方向出力**: `outgoing_url` が空の場合は、このアカウントは入力受信のみを行い、送信操作はエラーを返します。
2. **秘密鍵のセキュリティ**: `secret` は設定で暗号化された形式で保存され（metadata secret）、転送にはHTTPSの使用を推奨します。
3. **パスのユニーク性**: 複数のアカウントの `callback_path` は互いに異なる必要があります。ルーティングの競合を避けるためです。
4. **冪等性**: アダプタは入力イベントの重複除去を保証しません。外部システムはリトライ処理を独自に行う必要があります。
5. **タイムアウト**: 出力リクエストはErisPulseの組み込み `client` を使用し、グローバルのタイムアウト設定を継承します。