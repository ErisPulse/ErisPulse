# 微信公众号（WechatMp）アダプター - プラットフォーム特性ドキュメント

## 基本情報
- モジュール名: `ErisPulse-WechatMpAdapter`
- プラットフォーム識別子: `mp`（別名: `wechat_mp`）
- モジュールバージョン: 4.3.2
- 維持管理者: ErisPulse
- 最終更新: 2026-11-10
- 依存: `cryptography`

## v5 ファンタジーの更新（4.2.0）

- **BaseConverter の継承**：コンバーターの共通フィールドはフレームワークの build_base_event によって構築されます。
- **Api DSL の最小セット**：get_self_info（appid）/get_status/get_version/get_supported_actions
- **フレームワークのソフト依存**：ErisPulse>=2.7.1 を実行時に検出し、警告を表示します。起動時にバージョンのログを出力します。

## 標準化の整列 (4.3.2)

レスポンス構造とエラーコードは、[API レスポンス規格](../standards/api-response.md)に従います。

### メッセージイベントの補完 message_id

メッセージイベントの最上層に標準の `message_id` フィールドを追加します（WeChat の MsgId を取得し、不足している場合は空文字列で補完）。モジュールは `mp_msg_id` から読み取る必要はありません。

### 標準レスポンス

すべての `call_api` / Send 呼び出しは、標準レスポンスを返します：`status` / `retcode` / `data` / `message_id` / `message` + 最上層の `mp_raw`。**パッシブリプライが成功した場合、`message` は空文字列です**（`data.passive_reply=true` はパッシブリプライとしてブロックされたことを示します）。

### エラーコード規格

| retcode | 含意 | 説明 |
|---------|------|------|
| 0 | 成功 | — |
| 34100 | プラットフォームの失敗 | WeChat API が errcode != 0 を返した場合；**元の errcode は `mp_raw` に保持されます**。token の取得失敗もこのコードに属します |
| 10003 | パラメータのエラー / 未認証 | 認証されていないアカウント（`verified=false`）がパッシブリプライのコンテキスト外でカスタマーメッセージを呼び出した場合 |

### アカウントと複数アカウント

- `call_api` は、標準名の `account_id` と旧名の `_account_id` の両方のアカウントフィールドをサポートします。フレームワーク ApiDSL（`Api.Using(...)`）が自動的に適応します
- `Send` は `send_context`（イベントアカウントをデフォルトとして）を読み取ります
- `get_self_info` は、標準フィールドを補完します：`user_id`（WeChat 公衆号 AppID）/ `user_name` / `user_displayname`（`wechatmp:{アカウント名}`）

---

### 既に接続済みのプラットフォーム機能

- **受信**：WeChat 公衆号のコールバックメッセージと、フォロー/アンフォローなどのイベント（明文/セキュリティモード）、署名検証
- **送信**：カスタマーメッセージ（Text/Image など、Send DSL を経由）
- **API**：アカウント情報（appid）と実行状態（最小限のセット）

## 支援するメッセージ送信タイプ

| 方法 | 説明 | WeChat API |
|------|------|---------|
| `Text(text)` | テキストを送信 | カスタマーサービスメッセージ `message/custom/send` |
| `Image(file)` | 画像を送信（media_id の自動アップロード） | カスタマーサービスメッセージ + `media/upload` |
| `Voice(file)` | 音声を送信（media_id の自動アップロード） | カスタマーサービスメッセージ + `media/upload` |
| `Video(file, title, description)` | 動画を送信（media_id の自動アップロード） | カスタマーサービスメッセージ + `media/upload` |
| `Music(url, title, description, ...)` | 音楽を送信 | カスタマーサービスメッセージ |
| `News(articles)` | 画像付きテキストメッセージを送信 | カスタマーサービスメッセージ |
| `Template(template_id, data, url)` | テンプレートメッセージを送信 | `message/template/send` |
| `Menu(head_content, list, tail_content)` | メニューメッセージを送信 | カスタマーサービスメッセージ `msgmenu` |
| `Raw_ob12(message)` | OneBot12 標準メッセージセグメントを送信 | - |

### メディアファイルの説明
- 3 種類のパラメータタイプをサポート：
  - `str` URL（`http://` / `https://` で始まる）：自動的にダウンロードしてアップロード
  - `str` ローカルファイルパス：自動的に読み取ってアップロード
  - `bytes` バイナリデータ：直接アップロード
  - `str` media_id：`media:` というプレフィックスを付けることで、既にアップロードされた media_id を再利用可能
- アップロード後に有効期限 3 日の臨時素材 `media_id` が取得できる

### 重要な制限事項
- カスタマーサービスメッセージは、ユーザーと公式アカウントが対話した後 **48 時間以内** にのみ送信可能
- 48 時間を超える場合は、テンプレートメッセージを使用する必要がある（ユーザーの許可が必要）
- 認証されていないサービスアカウント（`verified=false`）は、自動送信ができない。受動的な返信のみ可能（上記の「認証済みサービスアカウントと受動的な返信」を参照）

## イベントの種類

### メッセージイベント (message)
すべてのユーザーのメッセージは `detail_type: private`（公式アカウントの1対1の場面）です。

| 微信 MsgType | メッセージセグメントの種類 | 説明 |
|-------------|-----------|------|
| `text` | `text` | テキストメッセージ |
| `image` | `image` | 画像メッセージ |
| `voice` | `voice` | 音声メッセージ（音声認識結果を含む） |
| `video` | `video` | ビデオメッセージ |
| `shortvideo` | `video` | 小型ビデオ（`mp_shortvideo`をマーク） |
| `location` | `location` | 地理位置メッセージ |
| `link` | `text` | リンクメッセージ（テキストに変換） |

### 通知イベント (notice)
イベントは `mp_event` フィールドで具体的な種類を識別します。

| 微信 Event | `mp_event` | 説明 |
|-----------|-----------|------|
| `subscribe` | `subscribe` | 公式アカウントをフォロー |
| `unsubscribe` | `unsubscribe` | フォローを解除 |
| `SCAN` | `scan` | パラメータ付きQRコードをスキャン |
| `LOCATION` | `location_report` | 地理位置を報告 |
| `CLICK` | `menu_click` | 自定義メニューをクリック |
| `VIEW` | `menu_view` | メニューのリンクに遷移 |
| `TEMPLATESENDJOBFINISH` | `template_send_finish` | テンプレートメッセージ送信結果 |
| `MASSSENDJOBFINISH` | `mass_send_finish` | 一斉送信メッセージ送信結果 |

## プラットフォーム拡張フィールド

イベントオブジェクト内の微信特有のフィールド（`mp_` で始まる）：

| フィールド | 型 | 説明 |
|------|------|------|
| `mp_raw` | str | 元の XML データ |
| `mp_raw_type` | str | 元のメッセージ/イベントの型 |
| `mp_msg_id` | str | 微信メッセージ ID |
| `mp_event` | str | イベントの型（イベント通知のみ） |
| `mp_event_key` | str | イベントのキー（メニューのクリック/スキャンなど） |
| `mp_to_user` | str | 受信者の微信号（公式アカウントの元のID） |
| `mp_from_user` | str | 送信者の OpenID |
| `mp_data` | dict | 解析後の XML ディクショナリデータ |

## イベント拡張メソッド

`register_event_mixin("mp", ...)` で登録すると、イベントオブジェクト上で直接以下のメソッドを呼び出すことができます。

| メソッド | 戻り値 | 説明 |
|------|--------|------|
| `get_openid()` | str | 送信者の OpenID |
| `get_msg_type()` | str | 微信の元のメッセージタイプ |
| `get_event()` | str | イベントタイプ（イベント通知のみ） |
| `get_content()` | str | メッセージの純粋なテキスト内容 |
| `get_raw_xml()` | str | 元の XML データ |

## 配置オプション

### 複数アカウントの設定

各アカウントは1つのWeChat公式アカウントに対応します：

```toml
[WechatMpAdapter.accounts.main]
appid = "wx1234567890abcdef"
appsecret = "your_app_secret_here"
token = "your_callback_token"
encoding_aes_key = ""                    # セキュリティモード/互換モードが必要な場合（43文字）
callback_path = "/mp/main"               # コールバックパス
verified = true                          # 認証済みサービスアカウントかどうか（アクティブ送信能力に影響）
enable = true

[WechatMpAdapter.accounts.secondary]
appid = "wx0987654321fedcba"
appsecret = "another_app_secret"
token = "another_callback_token"
callback_path = "/mp/secondary"
enable = true
```

### 設定フィールドの説明

| フィールド | 必須 | 説明 |
|------|------|------|
| `appid` | はい | 公式アカウントの AppID |
| `appsecret` | はい | 公式アカウントの AppSecret（secret） |
| `token` | いいえ | コールバック検証トークン（署名検証を有効にするために推奨） |
| `encoding_aes_key` | いいえ | メッセージの暗号化/復号化キー（43文字、セキュリティモードが必要） |
| `callback_path` | いいえ | コールバックパステンプレート、デフォルトは `/mp/{account}`、`{account}` はアカウント名に置換されます |
| `verified` | いいえ | 認証済み**サービスアカウント**かどうか、デフォルトは `true`（下記を参照） |
| `enable` | いいえ | 有効化するかどうか、デフォルトは true |

### 認証済みサービスアカウントと受動応答（verified）

- `verified = true`（デフォルト、認証済みサービスアカウント）：**カスタマーメッセージ**のアクティブ送信（48時間ウィンドウ内）とテンプレートメッセージを使用可能
- `verified = false`（未認証のサブスクリプションアカウント）：
  - カスタマーメッセージ / テンプレートメッセージは**webhook受動応答のコンテキスト内でのみ送信可能**（ユーザーからのメッセージを受信した後15秒以内、1回の応答のみ）——アダプターは送信を受動応答として自動的に捕捉します
  - アクティブ送信（例：定時タスク）は `retcode=10003` エラー（未認証）を返します

## 暗号化モードの説明

WeChat 公開アカウントは、3 つのメッセージの暗号化/復号化モードを提供しています。

| モード | 説明 | encoding_aes_key | 验証フィールド |
|------|------|-----------------|---------|
| 明文モード | XML を明文で送信 | 不要 | `signature` |
| 兼容モード | 明文と暗号文が同時に存在 | 選択 | `signature` / `msg_signature` |
| 安全モード | 全てを暗号化 | 必須 | `msg_signature` |

このアダプタは自動的に処理します：
- 明文モード：`signature` を検証し、XML を直接解析
- 安全/兼容モード：`Encrypt` フィールドを検出し、`msg_signature` を検証し、AES-256-CBC を使用して復号
- 復号には `cryptography` ライブラリが必要（dependencies に宣言済み）

## コールバックルート

アダプターは、有効なアカウントごとに2つのルート（GET + POST）を登録します。

- **GET**：WeChatサーバーの接続検証。署名を検証した後に `echostr` を返します。
- **POST**：ユーザーのメッセージとイベントを受け取ります。署名を検証→必要に応じて復号化→変換→emit

実際のアクセスパスには、モジュールのプレフィックスが自動的に追加されます。たとえば、ルートを `/mp/main` に登録した場合、実際のアクセスパスは `/mp_{account}_verify/mp/main` および `/mp_{account}_message/mp/main` になります。

## API レスポンス

すべての `call_api` 呼び出しは、標準化されたレスポンスを返します：

- 成功: `status: "ok"`, `retcode: 0`
- 失敗: `status: "failed"`, `retcode: 34100`（プラットフォームのエラー；**元の errcode は `mp_raw` に保持されます**）または `10003`（パラメータエラー / 認証されていない）
- 常に `mp_raw`（元のレスポンス）と、ルートレベルの `message_id`（存在しない場合は空文字列）が含まれます。