# WeChatMpアダプタ - プラットフォーム特徴ドキュメント

各言語の切り替え行（各言語名は `` | `` で区切られた行）がドキュメントに含まれている場合、上記の第8条のフォーマット要件を厳密に遵守し、``[**Label**](file)`` というような誤ったフォーマットを出力しないようにしてください。

## 基本情報
- モジュール名: `ErisPulse-WechatMpAdapter`
- プラットフォーム識別子: `mp`（別名: `wechat_mp`）
- モジュールバージョン: 4.1.0
- 維持者: ErisPulse
- 依存: `cryptography`

[**English**](docs/ja/quick-start.md)

## 支持するメッセージ送信タイプ

| 方法 | 説明 | WeChat API |
|------|------|---------|
| `Text(text)` | テキストを送信 | カスタマーサービスメッセージ `message/custom/send` |
| `Image(file)` | 画像を送信（media_id の自動取得） | カスタマーサービスメッセージ + `media/upload` |
| `Voice(file)` | 音声を送信（media_id の自動取得） | カスタマーサービスメッセージ + `media/upload` |
| `Video(file, title, description)` | 動画を送信（media_id の自動取得） | カスタマーサービスメッセージ + `media/upload` |
| `Music(url, title, description, ...)` | 音楽を送信 | カスタマーサービスメッセージ |
| `News(articles)` | 画像付きテキストメッセージを送信 | カスタマーサービスメッセージ |
| `Template(template_id, data, url)` | テンプレートメッセージを送信 | `message/template/send` |
| `Menu(head_content, list, tail_content)` | メニューメッセージを送信 | カスタマーサービスメッセージ `msgmenu` |
| `Raw_ob12(message)` | OneBot12 標準メッセージセグメントを送信 | - |

### メディアファイルの説明
- 3 種類のパラメータ型をサポート：
  - `str` URL（`http://` / `https://` で始まる）：自動的にダウンロードしてアップロード
  - `str` ローカルファイルパス：自動的に読み込んでアップロード
  - `bytes` バイナリデータ：直接アップロード
  - `str` media_id：`media:` という接頭辞を使用して、既にアップロードされた media_id を再利用可能
- アップロード後に有効期限 3 日間の有効な一時素材 `media_id` が取得できる

### 重要な制限
- カスタマーサービスメッセージは、ユーザーが公式アカウントと対話した後 **48 時間以内** にのみ、自動的に送信可能
- 48 時間を過ぎた場合は、テンプレートメッセージを使用する必要がある（ユーザーの許可が必要な場面が必要）
- 認証されていないサービスアカウント（`verified=false`）は、自動的に送信できず、受動的に返信するのみ（上記の「認証済みサービスアカウントと受動的返信」を参照）

docs/ja/quick-start.md

## イベントタイプ

### メッセージイベント (message)
すべてのユーザーからのメッセージは `detail_type: private`（公式アカウント 1v1 シナリオ）です。

| 微信 MsgType | メッセージセグメントタイプ | 説明 |
|-------------|-----------|------|
| `text` | `text` | テキストメッセージ |
| `image` | `image` | 画像メッセージ |
| `voice` | `voice` | 音声メッセージ（音声認識結果を含む） |
| `video` | `video` | ビデオメッセージ |
| `shortvideo` | `video` | 小型ビデオ（`mp_shortvideo` でマーク） |
| `location` | `location` | 地理位置メッセージ |
| `link` | `text` | リンクメッセージ（テキストに変換） |

### 通知イベント (notice)
イベントは `mp_event` フィールドによって具体的なタイプが区別されます。

| 微信 Event | `mp_event` | 説明 |
|-----------|-----------|------|
| `subscribe` | `subscribe` | 公式アカウントをフォロー |
| `unsubscribe` | `unsubscribe` | フォロー解除 |
| `SCAN` | `scan` | パラメータ付きQRコードをスキャン |
| `LOCATION` | `location_report` | 地理位置を報告 |
| `CLICK` | `menu_click` | 自作メニューをクリック |
| `VIEW` | `menu_view` | メニューのリンクに移動 |
| `TEMPLATESENDJOBFINISH` | `template_send_finish` | テンプレートメッセージ送信結果 |
| `MASSSENDJOBFINISH` | `mass_send_finish` | 群送信メッセージ送信結果 |

[**English**](docs/en/quick-start.md) | [**日本語**](docs/ja/quick-start.md) | [**简体中文**](docs/ja/quick-start.md)

## プラットフォーム拡張フィールド

イベントオブジェクト内の微信特有のフィールド（`mp_` で始まるフィールド）：

| フィールド | 型 | 説明 |
|------|------|------|
| `mp_raw` | str | 元の XML データ |
| `mp_raw_type` | str | 元のメッセージ/イベントの種類 |
| `mp_msg_id` | str | 微信メッセージ ID |
| `mp_event` | str | イベントの種類（イベント通知の場合のみ） |
| `mp_event_key` | str | イベントの Key（メニューのクリック/スキャン等） |
| `mp_to_user` | str | 受信者の微信号（公式アカウントの元の ID） |
| `mp_from_user` | str | 送信者の OpenID |
| `mp_data` | dict | 解析された XML の辞書データ |

[バックトゥトップ](#)

## イベント拡張メソッド

`register_event_mixin("mp", ...)` で登録すると、イベントオブジェクト上で直接以下のメソッドを呼び出せます。

| メソッド | 戻り値 | 説明 |
|------|--------|------|
| `get_openid()` | str | 送信者の OpenID |
| `get_msg_type()` | str | 微信の元のメッセージタイプ |
| `get_event()` | str | イベントの種類（イベント通知のみ） |
| `get_content()` | str | メッセージの純粋なテキスト内容 |
| `get_raw_xml()` | str | 元の XML データ |

各言語のナビゲーションリンクを含む行がある場合、上記のルールに従ってパスを変更してください。

## 設定オプション

### 複数アカウントの設定

各アカウントは1つの公式アカウントに対応します：

```toml
[WechatMpAdapter.accounts.main]
appid = "wx1234567890abcdef"
appsecret = "your_app_secret_here"
token = "your_callback_token"
encoding_aes_key = ""                    # セキュリティモード/互換モードが必要な場合（43文字）
callback_path = "/mp/main"               # コールバックパス
verified = true                          # 認証済みサービスアカウントかどうか（プッシュ送信能力に影響）
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
| `token` | いいえ | コールバック認証用のトークン（署名検証を有効にするために推奨） |
| `encoding_aes_key` | いいえ | メッセージの暗号化/復号化キー（43文字、セキュリティモードで必須） |
| `callback_path` | いいえ | コールバックパスのテンプレート、デフォルトは `/mp/{account}`、`{account}` はアカウント名に置換されます |
| `verified` | いいえ | 認証済み**サービスアカウント**かどうか、デフォルトは `true`（下記を参照） |
| `enable` | いいえ | 有効化するかどうか、デフォルトは true |

### 認証済みサービスアカウントと受動応答（verified）

- `verified = true`（デフォルト、認証済みサービスアカウント）：**カスタマーメッセージ**をいつでもプッシュ送信（48時間ウィンドウ内）とテンプレートメッセージを使用可能
- `verified = false`（未認証のサブスクリプションアカウント）：
  - カスタマーメッセージ / テンプレートメッセージは**webhookの受動応答コンテキスト内でのみ送信可能**（ユーザーからのメッセージを受信後15秒以内、1回のみ）——アダプタは送信を受動応答に自動的に変換します
  - 主動的なプッシュ（例：スケジュールタスク）は `retcode=34003` エラーを返します

[**English**](docs/en/quick-start.md) | [**日本語**](docs/ja/quick-start.md) | [**简体中文**](docs/ja/quick-start.md)

## 暗号化モードの説明

WeChat 公開アカウントは、3 種類のメッセージ暗号化/復号化モードを提供しています：

| モード | 説明 | encoding_aes_key | 検証フィールド |
|------|------|-----------------|---------|
| 明文モード | XML を明文で送信 | 必要なし | `signature` |
| 互換モード | 明文と暗号文が同時に存在 | オプション | `signature` / `msg_signature` |
| 安全モード | 全て暗号化 | 必須 | `msg_signature` |

このアダプタは自動的に以下を処理します：
- 明文モード：`signature` を検証し、XML を直接解析
- 安全/互換モード：`Encrypt` フィールドを検出し、`msg_signature` を検証し、AES-256-CBC を使用して復号
- 復号には `cryptography` ライブラリが必要（dependencies に宣言済み）

言語切り替え行がある場合（各言語名を `` | `` で区切る行）、上記のルール 8 に厳密に従い、``[**Label**](file)`` のような誤った形式を出力しないように注意してください。

## コールバックルート

アダプターは、有効化された各アカウントに対して 2 つのルート（GET + POST）を登録します：

- **GET**：WeChat サーバーへの接続検証。署名を検証した後、`echostr` を返します
- **POST**：ユーザーからのメッセージとイベントを受信。署名を検証→（必要に応じて）復号化→変換→emit

実際のアクセスパスには、モジュールのプレフィックスが自動的に追加されます。たとえば、登録パスが `/mp/main` の場合、実際のアクセスパスは `/mp_{account}_verify/mp/main` および `/mp_{account}_message/mp/main` になります。

[**English**](docs/en/quick-start.md) | [**日本語**](docs/ja/quick-start.md) | [**简体中文**](docs/ja/quick-start.md)

## API のレスポンス

すべての `call_api` 呼び出しは、標準化されたレスポンスを返します：

- 成功：`status: "ok"`, `retcode: 0`
- 失敗：`status: "failed"`, `retcode: 34000+errcode`
- いずれの場合も `mp_raw`（元のレスポンス）、`message_id` を含みます

7. **重要：パスの置換ルール**
   - ドキュメントリンク内の `docs/ja/` を `docs/ja/` に置換する
   - 例：`docs/ja/quick-start.md` は `docs/ja/quick-start.md` に変更する
   - 非現在言語版ファイルを指すリンク（例：`README.xx.md` 形式のリンク）は、変更しないでそのままにする
   - これにより、リンクが正しい言語のドキュメントバージョンを指すようになる