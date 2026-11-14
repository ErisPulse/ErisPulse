# Webhook 通用橋接アダプタープラットフォームの機能ドキュメント

WebhookAdapter はプロトコルレベルの双方向橋渡しアダプターであり、特定のプラットフォームに紐付いていません。入力側では外部システムからの POST リクエストの JSON を OneBot12 イベントに変換し、出力側ではモジュールの Send から外部システムに POST します。

---

## ドキュメント情報

- 対応モジュールバージョン: 4.3.2
- メンテナー: ErisPulse
- 最終更新日: 2026-11-10

## 基本情報

- プラットフォーム概要: HTTP リクエストを発行できる任意のシステムが、このアダプターを通じて ErisPulse に接続できます。
- アダプター名: WebhookAdapter
- プラットフォーム識別子: `webhook`
- 多アカウント対応: 各アカウントは独立した橋渡し設定 (bot_id / callback_path / outgoing_url / secret) です。
- フレームワーク要件: ソフト依存 `ErisPulse>=2.7.1`（実行時検出と警告、強制はしません）。

## 接続済みプラットフォーム機能

- **入力**: 外部システムが callback_path に POST → OneBot12 イベントに変換 (json/text セグメントを透過)
- **出力**: モジュール Send → outgoing_url に POST (双方向橋渡し)
- **API**: 橋渡し認証情報と実行状態 (最小限)

## v5 フレームワーク更新 (4.2.0)

- **Api DSL 最小集**: get_self_info/get_status/get_version/get_supported_actions
- **フレームワークソフト依存**: 実行時に ErisPulse>=2.7.1 を検出し警告を出力し、起動時にバージョンログを出力
- インポートパスを Core.Bases に更新

## 標準化対応 (4.3.2)

レスポンス構造とエラーコードは [API レスポンス規格](../standards/api-response.md)に従います。

### イベントフィールド

- **メッセージイベントの `message_id` 補完**: 入力側 body の `message_id` を優先的に透過し、不足時は uuid を補完 (下流で message_id で重複除去/返信時に空値を取得しないように)
- **イベント注入 `self.account_id`** (アカウント名): 多アカウント環境下で `event.reply()` は該当イベントを受理したアカウントに自動ルーティング
- **`alt_message` 空文字列補完**: 入力側で提供されない場合、空文字列を補完し、標準フィールドの完全性を保証
- **JSON セグメント名を `webhook_json` に変更**: プラットフォームプレフィックスなしの裸の `json` セグメントはすべて `webhook_json` に統一 (プラットフォーム拡張セグメント命名規則に従う)
- Converter はフレームワーク `BaseConverter` を再利用 (共通フィールドは `build_base_event` で統一構築)
- `get_self_info` で標準フィールドを補完: `user_id` (アカウント bot_id) / `user_name` / `user_displayname` (`webhook:{アカウント名}`)

### エラーコード規格

| retcode | 含意 | 説明 |
|---------|------|------|
| 0 | 成功 | — |
| 33001 | ネットワークエラー | 出力先 POST 目標失敗 (接続/タイムアウトなど) |
| 10003 | パラメータエラー | 出力 URL 未設定、パラメータ不足など |

### アカウントと多アカウント

- `call_api` は両対応アカウントフィールドをサポート: `account_id` (標準名) / `_account_id` (旧名), フレームワーク ApiDSL (`Api.Using(...)`) は自動的に適応
- `Send` は `send_context` (イベントアカウントのデフォルト) を読み込む: イベントコンテキストから `Send` を呼び出す際、デフォルトで元のアカウントにフォールバック

## 概要

Webhook アダプターは**プロトコルレベルの橋渡し**であり、特定のプラットフォームに紐付いていません。HTTP を通じて送受信を行い、HTTP リクエストを発行できる任意のシステムが ErisPulse に接続できます。

```
入力方向                                出力方向
────────                                ────────
外部システム                                ErisPulse モジュール
   │                                       │
   │ POST JSON                             │ Send.Text(...)
   ▼                                       ▼
┌──────────────────────────────────────────────────┐
│              WebhookAdapter                       │
│  ┌──────────────────┐   ┌──────────────────┐    │
│  │ 入力ルーティング          │   │ 出力転送          │    │
│  │ GET  (健康チェック)   │   │ client.post()    │    │
│  │ POST (イベント受信)   │   │ → outgoing_url   │    │
│  └────────┬─────────┘   └────────▲─────────┘    │
│           │                      │               │
│           ▼                      │               │
│  ┌──────────────────┐   ┌──────────────────┐    │
│  │ WebhookConverter │   │ Send クラス          │    │
│  │ JSON → OneBot12  │   │ メッセージセグメント → JSON    │    │
│  └────────┬─────────┘   └────────▲─────────┘    │
└───────────┼──────────────────────┼───────────────┘
            ▼                      │
     adapter.emit(event)    call_api("send_message")
            │                      │
            ▼                      │
       ErisPulse イベントシステム ◄────────┘
```

## 多アカウントモデル

各アカウントは独立した橋渡し設定であり、互いに干渉しません:

| アカウント | bot_id | callback_path | outgoing_url | secret |
|------|--------|---------------|--------------|--------|
| `default` | `webhook_bot` | `/webhook/default` | `https://a.com/recv` | `key1` |
| `discord` | `discord_bot` | `/webhook/discord` | `https://b.com/send` | `key2` |

各アカウントは起動時に独立してルーティングを登録し、独立して connect を emit します。

### アカウント設定フィールド

| フィールド | 必須 | 説明 |
|------|------|------|
| `bot_id` | いいえ | Bot 身元 ID (この橋渡しで表示される) |
| `callback_path` | いいえ | 入力側コールバックパス ( `{account}` プレースホルダをサポート) |
| `outgoing_url` | いいえ | 出力先 URL (モジュールがメッセージを送信する際、このアドレスに POST) |
| `secret` | いいえ | 認証キー (空欄の場合は検証を無効化; 設定画面では暗号化して保存) |

## 入力プロトコル

### 1. 健康チェック (GET)

- **パス**: `{callback_path}`
- **メソッド**: `GET`
- **認証**: なし
- **レスポンス**:

```json
{"status": "ok", "account": "default"}
```

### 2. イベント受信 (POST)

- **パス**: `{callback_path}`
- **メソッド**: `POST`
- **Content-Type**: `application/json`
- **認証** (secret 設定時): Header `X-Webhook-Secret` または Query `?secret=`

#### リクエスト Body

```json
{
  "user_id": "u123",
  "user_nickname": "ユーザー名",
  "group_id": "グループID（グループ会話のみ）",
  "detail_type": "private",
  "message_id": "オプション、イベントの message_id として透過 (不足時は uuid で補完)",
  "alt_message": "オプション、純文本文の代替",
  "message": [
    {"type": "text", "data": {"text": "メッセージ内容"}}
  ],
  "raw": {}
}
```

| フィールド | 必須 | 説明 |
|------|------|------|
| `user_id` | はい | 送信者 ID |
| `user_nickname` | いいえ | 送信者ニックネーム |
| `group_id` | いいえ | グループ/チャンネル ID (グループ会話時に提供) |
| `detail_type` | いいえ | 会話タイプ (`private`/`group`)、未指定時はアカウントのデフォルト値を使用 |
| `message_id` | いいえ | メッセージ ID、イベントのトップレベル `message_id` として透過 (不足時は uuid で補完) |
| `alt_message` | いいえ | 純文本文の代替、不足時は空文字列で補完 |
| `message` | はい | OneBot12 メッセージセグメント配列 |
| `raw` | いいえ | 元データ、`webhook_raw` にそのまま保存 |

#### レスポンス

```json
{"status": "ok"}
```

エラーの場合は HTTP ステータスコードを含むレスポンス:

| ステータスコード | 含意 |
|--------|------|
| 400 | 無効な JSON / body がオブジェクトでない |
| 401 | 認証失敗 |
| 404 | 未知のアカウント |
| 500 | イベント配信失敗 |

### 3. フィールドマッピング (入力 JSON → OneBot12 イベント)

| 入力 JSON | OneBot12 イベントフィールド | 説明 |
|-----------|-------------------|------|
| — | `id` | 自動生成 |
| — | `time` | 現在の Unix タイムスタンプ (秒) |
| — | `type` | 固定 `message` |
| `detail_type` | `detail_type` | 未指定時はアカウントのデフォルト値を使用 |
| — | `platform` | 固定 `webhook` |
| — | `self.platform` | 固定 `webhook` |
| — | `self.user_id` | アカウントの `bot_id` |
| — | `self.account_id` | アカウント名 (4.3.2 で注入、多アカウントルーティング) |
| `user_id` | `user_id` | 透過 |
| `user_nickname` | `user_nickname` | 透過 (オプション) |
| `group_id` | `group_id` | 透過 (オプション) |
| `message_id` | `message_id` | 透過、不足時は uuid で補完 (4.3.2) |
| `alt_message` | `alt_message` | 透過、不足時は空文字列で補完 (4.3.2) |
| `message` | `message` | 透過 |
| 完全な body | `webhook_raw` | 元のリクエスト |
| アカウント名 | `webhook_account` | イベントを生成したアカウント名 |
| `type` または `message` | `webhook_raw_type` | 元のイベントタイプ |

> 裸の `json` セグメント (`{"type": "json", ...}`) は、入力/出力の両側で `webhook_json` セグメントに統一されます。

## 出力プロトコル

### 1. メッセージ送信

モジュールが `Send.To(...).Text(...)` などのメソッドを呼び出すと、アダプターは `outgoing_url` に POST を送信します:

- **メソッド**: `POST`
- **Content-Type**: `application/json`
- **認証ヘッダー** (secret 設定時): `X-Webhook-Secret: {secret}`

#### リクエスト Body

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
| `target_type` | 目標タイプ (`Send.To(type, id)` から取得、未指定時はアカウントのデフォルト値を使用) |
| `target_id` | 目標 ID (`Send.To` から取得) |
| `account` | 送信アカウント名 |
| `message` | OneBot12 メッセージセグメント配列 |
| `timestamp` | 送信タイムスタンプ (秒) |

### 2. レスポンス標準化

アダプターは出力先からのレスポンスを ErisPulse の標準レスポンス形式に標準化します:

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

ターゲットレスポンス JSON の `message_id` フィールドからメッセージ ID を抽出します。ターゲットが `message_id` を返さない場合、空文字列になります。

リクエストが失敗した場合はエラーレスポンスを返します (`status: "failed"`, `retcode: 33001`)。

## Send メソッド

| メソッド | 説明 |
|------|------|
| `Text(text)` | テキストを送信し、`[{"type":"text","data":{"text":text}}]` にラップ |
| `Image(file)` | 画像を送信し、`[{"type":"image","data":{"file":file}}]` にラップ |
| `Raw_ob12(message)` | OneBot12 原始メッセージセグメントを送信 |
| `Json(data)` | 原始 JSON を透過し、`[{"type":"webhook_json","data":{"raw":data}}]` にラップ |

`At` / `AtAll` / `Reply` 修飾子はフレームワークの基底クラスから提供され、`_apply_modifiers` でメッセージセグメントにマージされます。

## イベント拡張メソッド (WebhookEventMixin)

| メソッド | 説明 |
|------|------|
| `get_raw_data()` | 元のリクエスト body (`webhook_raw`) を取得 |
| `get_detail_type()` | 会話タイプを取得 |
| `get_webhook_account()` | イベントを生成したアカウント名を取得 |

## 機能マトリックス

| 機能 | 対応状況 |
|------|----------|
| 多アカウント | ✅ 各アカウントは独立した橋渡し |
| 入力側認証 | ✅ ヘッダー / クエリの両モード |
| 健康チェック | ✅ GET でステータスを返す |
| 出力側認証 | ✅ ヘッダーに secret を含める |
| OneBot12 標準イベント | ✅ 完全な標準フィールド |
| Meta イベント | ✅ connect / disconnect |
| ルーティング発見 | ✅ `webhook` 名前空間に登録 |
| WebSocket | ❌ HTTP 限定 |
| メディアアップロード | ❌ URL 透過のみ、バイナリを代行送信しない |

## 注意事項

1. **単方向出力**: `outgoing_url` が空欄の場合、このアカウントは入力側のみの受信となり、送信操作はエラーを返します (`retcode: 10003`)
2. **秘钥セキュリティ**: `secret` は設定で暗号化して保存 (metadata secret), 通信は HTTPS を推奨
3. **パスのユニーク性**: 複数アカウントの `callback_path` は互いに異なる必要があり、ルーティングの衝突を避ける
4. **멱등性**: アダプターは入力イベントの重複除去を保証しない、外部システムはリトライ処理を独自に行う必要がある
5. **タイムアウト**: 出力リクエストは ErisPulse 内部の `client` を使用し、グローバルのタイムアウト設定を継承