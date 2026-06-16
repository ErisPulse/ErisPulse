# WeChat 公衆アカウント (WechatMp) アダプタ - プラットフォーム特性ドキュメント

## 基本情報
- モジュール名: `ErisPulse-WechatMpAdapter`
- プラットフォーム識別子: `mp`（別名: `wechat_mp`）
- モジュールバージョン: 4.0.0
- メンテナ: ErisPulse
- 依存関係: `cryptography`

## サポートされているメッセージ送信タイプ

| メソッド | 説明 | WeChat API |
|------|------|---------|
| `Text(text)` | テキスト送信 | カスタマーサービスメッセージ `message/custom/send` |
| `Image(file)` | 画像送信（自動アップロードして media_id を取得） | カスタマーサービスメッセージ + `media/upload` |
| `Voice(file)` | 音声送信（自動アップロードして media_id を取得） | カスタマーサービスメッセージ + `media/upload` |
| `Video(file, title, description)` | 動画送信（自動アップロードして media_id を取得） | カスタマーサービスメッセージ + `media/upload` |
| `Music(url, title, description, ...)` | 音楽送信 | カスタマーサービスメッセージ |
| `News(articles)` | 記事グループ送信 | カスタマーサービスメッセージ |
| `Template(template_id, data, url)` | テンプレートメッセージ送信 | `message/template/send` |
| `Menu(head_content, list, tail_content)` | メニューメッセージ送信 | カスタマーサービスメッセージ `msgmenu` |
| `Raw_ob12(message)` | OneBot12 標準メッセージセグメント送信 | - |

### メディアファイルの説明
- サポートされているパラメータタイプは3種類です：
  - `str` URL（`http://` / `https://` で始まる）：自動ダウンロード後にアップロード
  - `str` ローカルファイルパス：自動読み込み後にアップロード
  - `bytes` バイナリデータ：直接アップロード
  - `str` media_id：`media:` プレフィックスを使用して、既にアップロード済みの media_id を直接再利用可能
- アップロード後、有効期間 3 日の一時メディア `media_id` を取得します

### 重要な制限
- カスタマーサービスメッセージは、ユーザーが公衆アカウントと対話した後 **48時間以内** にのみ、主動的に送信可能です
- 48時間を超える場合、テンプレートメッセージを使用する必要があります（ユーザー承認が必要なシナリオ）

## イベントタイプ

### メッセージイベント (message)
すべてのユーザーメッセージは `detail_type: private` です（公衆アカウント 1v1 シナリオ）。

| WeChat MsgType | メッセージセグメントタイプ | 説明 |
|-------------|-----------|------|
| `text` | `text` | テキストメッセージ |
| `image` | `image` | 画像メッセージ |
| `voice` | `voice` | 音声メッセージ（音声認識結果を含む） |
| `video` | `video` | 動画メッセージ |
| `shortvideo` | `video` | ショート動画（マーク `mp_shortvideo`） |
| `location` | `location` | 場所メッセージ |
| `link` | `text` | リンクメッセージ（テキストに変換） |

### 通知イベント (notice)
イベントは `mp_event` フィールドで具体的なタイプを区別します。

| WeChat Event | `mp_event` | 説明 |
|-----------|-----------|------|
| `subscribe` | `subscribe` | 公衆アカウントフォロー |
| `unsubscribe` | `unsubscribe` | アンフォロー |
| `SCAN` | `scan` | パラメータ付きQRコードスキャン |
| `LOCATION` | `location_report` | 場所報告 |
| `CLICK` | `menu_click` | カスタムメニュークリック |
| `VIEW` | `menu_view` | メニューリンク移動 |
| `TEMPLATESENDJOBFINISH` | `template_send_finish` | テンプレートメッセージ送信結果 |
| `MASSSENDJOBFINISH` | `mass_send_finish` | グループ送信メッセージ送信結果 |

## プラットフォーム拡張フィールド

イベントオブジェクト内の WeChat 固有のフィールド（`mp_` プレフィックス）：

| フィールド | 型 | 説明 |
|------|------|------|
| `mp_raw` | str | 原始 XML データ |
| `mp_raw_type` | str | 原始メッセージ/イベントタイプ |
| `mp_msg_id` | str | WeChat メッセージ ID |
| `mp_event` | str | イベントタイプ（イベント通知のみ） |
| `mp_event_key` | str | イベントキー（メニュークリック/スキャンなど） |
| `mp_to_user` | str | 受信側 WeChat ID（公衆アカウント元ID） |
| `mp_from_user` | str | 送信側 OpenID |
| `mp_data` | dict | 解析された XML 辞書データ |

## イベント拡張メソッド

`register_event_mixin("mp", ...)` 経由で登録し、イベントオブジェクト上で直接呼び出せます：

| メソッド | 戻り値 | 説明 |
|------|--------|------|
| `get_openid()` | str | 送信者 OpenID |
| `get_msg_type()` | str | WeChat 原始メッセージタイプ |
| `get_event()` | str | イベントタイプ（イベント通知のみ） |
| `get_content()` | str | メッセージの純テキスト内容 |
| `get_raw_xml()` | str | 原始 XML データ |

## 設定オプション

### 複数アカウント設定

各アカウントは一つの公衆アカウントに対応します：

```toml
[WechatMpAdapter.accounts.main]
appid = "wx1234567890abcdef"
appsecret = "your_app_secret_here"
token = "your_callback_token"
encoding_aes_key = ""                    # セキュアモード/互換モードのみ必要（43桁）
callback_path = "/mp/main"               # コールバックパス
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
| `appid` | Yes | 公衆アカウント AppID |
| `appsecret` | Yes | 公衆アカウント AppSecret（secret） |
| `token` | No | コールバック検証 Token（署名検証を有効にするために推奨） |
| `encoding_aes_key` | No | メッセージの暗号化/復号化キー（43桁、セキュアモード必須） |
| `callback_path` | No | コールバックパステンプレート、デフォルト `/mp/{account}`、`{account}` はアカウント名で置換されます |
| `enable` | No | 有効かどうか、デフォルト true |

## 暗号化モードの説明

WeChat 公衆アカウントは3種類のメッセージ暗号化/復号化モードを提供します：

| モード | 説明 | encoding_aes_key | 検証フィールド |
|------|------|-----------------|---------|
| 明文モード | XML 明文転送 | 必要なし | `signature` |
| 互換モード | 明文+暗文が共存 | オプション | `signature` / `msg_signature` |
| セキュアモード | 完全暗号化 | 必須 | `msg_signature` |

このアダプタは自動的に処理します：
- 明文モード：`signature` を検証し、XML を直接解析
- セキュア/互換モード：`Encrypt` フィールドを検出し、`msg_signature` を検証、AES-256-CBC で復号
- 復号は `cryptography` ライブラリに依存します（依存関係に宣言済み）

## コールバックルーティング

アダプタは有効になっている各アカウントに対して2つのルート（GET + POST）を登録します：

- **GET**：WeChat サーバー接入検証、署名検証後に `echostr` を返す
- **POST**：ユーザーメッセージとイベントを受け取り、署名検証→復号（必要な場合）→変換→emit

実際のアクセスパスにはモジュールプレフィックスが自動的に追加されます。例えば、登録パス `/mp/main` の場合、
実際のアクセスパスは `/mp_{account}_verify/mp/main` と `/mp_{account}_message/mp/main` になります。

## API レスポンス

すべての `call_api` 呼び出しは標準化されたレスポンスを返します：

- 成功：`status: "ok"`, `retcode: 0`
- 失敗：`status: "failed"`, `retcode: 34000+errcode`
- 常に `mp_raw`（原始レスポンス）、`message_id` を含みます