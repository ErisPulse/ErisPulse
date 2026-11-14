# 企業微信（WeCom）プラットフォームの特徴ドキュメント

WeComAdapter は、企業微信の自建アプリ API を基に構築されたアダプターであり、コールバックによるメッセージ受信、アプリメッセージのインターフェースを介した送信、および連絡先とメッセージカード機能を提供します。

---

## ドキュメント情報

- 対応モジュールバージョン: 0.1.2
- 維持管理者: ErisPulse
- 最終更新日: 2026-11-10

## 基本情報

- プラットフォーム概要：企業向けWeChatの自作アプリケーションロボット。社内通知、インテリジェントな質問応答、オフィスの自動化などの場面に適しています。
- アダプター名：WeComAdapter
- プラットフォーム登録名：`wecom`（別名 `wxwork`）
- 多アカウント対応：複数の企業を同時に設定可能（各アカウントは1つの corpid + アプリに対応）
- 接続方法：HTTPコールバックによる受信（企業向けWeChatのバックエンドでメッセージURLを設定）+ プッシュAPIによる送信
- 認証方式：corpid + secret から access_token を取得（自動的に更新）
- コールバックの暗号化/復号化：Token + EncodingAESKey（企業向けWeChatの公式暗号化プロトコル）
- 会話タイプのマッピング：アプリケーションメッセージ → `private`（メンバーのプライベートメッセージ）、アプリケーショングループチャット → `group`
- 鏈式修飾子のサポート：`.Reply()` などの修飾子メソッドをチェーンで使用可能
- OneBot12互換性：OneBot12標準のメッセージセグメントを送信可能

## 標準化対応（0.1.2）

このバージョンではアダプタの標準化対応を完了し、レスポンス構造とエラーコードは [API レスポンス規格](../standards/api-response.md)に準拠しています。

### アカウントと複数アカウント

- `call_api` は、アカウントフィールドを `account_id`（標準名）/ `_account_id`（旧名）の両方でサポートし、フレームワーク ApiDSL（`Api.Using(...)`）が自動的に適応します。
- **`get_user_info` など 6 つのアドレス帳 Api メソッド（`get_user_info` / `get_department_list` / `get_department_users` / `get_user_by_mobile` / `userid_to_openid` / `openid_to_userid`）は `Using()` のバックアップを修正しました**：アカウントが省略された場合、`Api.Using(...)` で指定されたアカウントに自動的に切り替わり、無視されなくなりました。
- `Send` は `send_context`（イベントアカウントのバックアップ）を読み取ります：イベントコンテキストから `Send` を呼び出す場合、デフォルトで元のアカウントに切り替わります。

### 標準フィールド

- **メッセージイベントにトップレベルの `message_id` を補完**（企業微信の MsgId を取得し、不足している場合は uuid でバックアップ）
- **`get_user_info` などのクエリ結果に標準化されたフィールドを追加**：`user_id` / `user_name` / `user_displayname`、元のデータは `wecom_raw` に保持されます。
- **`get_self_info` に `user_displayname` を補完**（`user_id` は corpid、`user_name` / `user_displayname` は `wecom:{アカウント名}`）
- Converter はフレームワークの `BaseConverter` を再利用します（共通フィールド id/time/platform/self/wecom_raw は `build_base_event` で統一的に構築されます）。

### エラーコード規格

| retcode | 含意 | 説明 |
|---------|------|------|
| 0 | 成功 | — |
| 34100 | プラットフォーム失敗 | 企業微信が失敗を返した（errcode != 0）；元のレスポンスは `wecom_raw` に保持されます。|
| 10003 | パラメータエラー | パラメータが不足または無効です。|

## 設定説明

```toml
# config.toml
[WeComAdapter.accounts.default]
corpid = "YOUR_CORP_ID"        # 企業 ID（必須、企業微信管理画面-私の企業）
secret = "YOUR_APP_SECRET"     # アプリの Secret（必須、自作アプリの詳細ページ）
agentid = 1000002              # アプリ AgentId（必須、自作アプリの詳細ページ）
callback_enabled = true        # コールバック受信の有効化（デフォルト true；無効化後は送信のみ可能）
token = "YOUR_CALLBACK_TOKEN"  # コールバック検証用 Token（企業微信管理画面-メッセージ受信設定）
encoding_aes_key = "YOUR_AES_KEY_43CHARS"  # コールバックの暗号化・復号化キー（43 文字）
callback_path = "/wecom/{account}"         # コールバックパス、{account} 占位符をサポート
enabled = true
```

**各アカウントの設定項目の説明：**

| 項目 | 型 | 必須 | 説明 |
|------|------|------|------|
| `corpid` | string | 是 | 企業 ID |
| `secret` | string | 是 | アプリ Secret |
| `agentid` | int | 建議 | アプリ AgentID |
| `callback_enabled` | bool | 否 | コールバック受信スイッチ（デフォルト有効） |
| `token` | string | 否 | コールバック検証用 Token |
| `encoding_aes_key` | string | 否 | コールバックの暗号化・復号化キー（43 文字） |
| `callback_path` | string | 否 | コールバックパス、{account} 占位符をサポート |
| `enabled` | bool | 否 | 有効化するかどうか（デフォルト true） |

- `corpid` / `secret` / `agentid`：[企業微信管理画面](https://work.weixin.qq.com)の自作アプリページから取得（前2つは必須）
- `callback_enabled`：コールバック受信スイッチ（デフォルト有効）。**無効化後はアダプターがコールバックルートの登録をスキップし、送信機能のみを保持**；管理画面のコールバック関連のフィールドも非表示になる
- `token` / `encoding_aes_key`：コールバックメッセージの検証と暗号化・復号化、企業微信管理画面の「メッセージ受信」設定と一致する
- `callback_path`：コールバック受信パス（デフォルト `/wecom/{アカウント名}`）、企業微信管理画面で完全な URL を設定する必要がある：`http(s)://あなたのアドレス:ポート/wecom/<アカウント名>`

**メッセージ受信の前提条件**：企業微信管理画面 → 自作アプリ → 「メッセージ受信」設定で API 受信を有効化し、URL に上記の完全なコールバックアドレスを記入し、Token と EncodingAESKey は設定と一致するようにする。**注意**：企業微信はコールバック URL がパブリックネットワークでアクセス可能であることを要求しており、リバースプロキシの使用が推奨される。

**API 環境**：
- API 基本アドレス：`https://qyapi.weixin.qq.com/cgi-bin`
- access_token は自動的に取得・キャッシュ更新されるため、手動での管理は不要。

## 支援されるメッセージ送信タイプ

すべての送信メソッドは、チェーン式の構文で実現されています。例：

```python
from ErisPulse import sdk
wecom = sdk.adapter.get("wecom")

# 基本メッセージ（target_type: "user"=ユーザー "group"=グループチャット）
await wecom.Send.To("user", "zhangsan").Text("こんにちは")
await wecom.Send.To("group", "group_chat_id").Markdown("**太字**通知")

# メディア（ローカルパス / bytes / URL；自動的に一時素材をアップロードして送信）
await wecom.Send.To("user", "zhangsan").Image("banner.png")
await wecom.Send.To("user", "zhangsan").Voice("voice.amr")
await wecom.Send.To("user", "zhangsan").Video("demo.mp4")
await wecom.Send.To("user", "zhangsan").File("report.pdf")

# 画像とテキスト、カード
await wecom.Send.To("user", "zhangsan").News([
    {"title": "タイトル", "description": "要約", "url": "https://...", "picurl": "https://.../img.png"},
])  # 最大 8 件

await wecom.Send.To("user", "zhangsan").TextCard(
    title="承認リマインド",
    description="承認待ちの書類があります",
    url="https://oa.example.com/approval/1",
    btntxt="処理する",
)

await wecom.Send.To("user", "zhangsan").TemplateCard(
    card_type="text_notice",  # 企業微信のカードタイプ、その他のパラメータは公式のカード JSON に透かし
    source={"icon_url": "...", "desc": "OA"},
    main_title={"title": "会議リマインド"},
)

# パッシブリプライ：メッセージを受け取った event.reply() で直接元のユーザーに返信
# 多アカウント指定での送信
await wecom.Send.To("user", "UserID", account_id="app2").Text("app2 で送信")
```

### 基本的な送信メソッド

| メソッド | 説明 | パラメータ |
|------|------|------|
| `.Text(text)` | 純粋なテキストメッセージを送信 | `text: str` |
| `.Markdown(content)` | Markdown メッセージを送信（アプリメッセージがサポート） | `content: str` |

### メディア送信メソッド

メディアメソッドは `bytes`（自動アップロードして media_id を取得）と `str`（アップロード済みの media_id またはパス/URL）の 2 つの入力をサポートします：

| メソッド | 説明 |
|------|------|
| `.Image(file, filename)` | 画像を送信 |
| `.Voice(file, filename)` | 音声を送信（企業微信の制限により AMR 形式が必要） |
| `.Audio(file, filename)` | Voice の別名 |
| `.Video(file, filename)` | 動画を送信 |
| `.File(file, filename)` | ファイルを送信 |

### フルテキストカードメソッド

| メソッド | 説明 |
|------|------|
| `.News(articles)` | 画像付きテキストメッセージを送信（最大 8 件） |
| `.TextCard(title, description, url, btntxt)` | テキストカードを送信 |
| `.TextCardMiniProgram(**kwargs)` | 小プログラム通知カードを送信 |
| `.TemplateCard(card_type, **kwargs)` | テンプレートカードを送信 |

### 原始メッセージ送信

- `.Raw_ob12(message: List[Dict])`：OneBot12 標準フォーマットのメッセージを送信

### チェーン修飾メソッド

| メソッド | 説明 |
|------|------|
| `.At(user_id)` | 指定ユーザーを@する（フレームワーク SendDSL 基底クラスで実装） |
| `.AtAll()` | 全メンバーを@する（フレームワーク SendDSL 基底クラスで実装） |
| `.Reply(message_id)` | 指定メッセージに返信する（フレームワーク SendDSL 基底クラスで実装） |

### 送信対象マッピング

| OB12 target_type | 企業微信対象フィールド | API エンドポイント |
|---|---|---|
| `user` / `private` | `touser` | `message/send` |
| `group` | `chatid` | `appchat/send` |

## 標準 API アクション

```python
info = await wecom.Api.get_self_info()          # アプリケーション情報（corpid/agentid）
status = await wecom.Api.get_status()           # 実行状態
ver = await wecom.Api.get_version()             # アダプターのバージョン

# 連絡先（access_token は自動的に注入されます；0.1.2 以降 Using() がバックアップとして有効）
user = await wecom.Api.get_user_info("zhangsan")            # メンバーの詳細情報（名前/所属/役職/アイコン）
depts = await wecom.Api.get_department_list(0)              # 部門リスト（0=ルート部門）
members = await wecom.Api.get_department_users(2)           # 部門のメンバー一覧
uid = await wecom.Api.get_user_by_mobile("13800000000")     # 電話番号から userid を取得
openid = await wecom.Api.userid_to_openid("zhangsan")       # userid → openid（赤包/外部支払い）
userid = await wecom.Api.openid_to_userid("oXXXX")          # openid → userid

# 複数アカウント：特定の企業アカウントを指定
result = await wecom.Api.Using("corp2").get_user_info("lisi")

# 任意の企業微信 API の直接呼び出し（endpoint は cgi-bin からの相対パスで、自動的に access_token が付与されます）
result = await wecom.Api.call("message/send", touser="zhangsan", msgtype="text", agentid=1000002, text={"content": "hi"})
```

## 特有イベントタイプ

このプラットフォームの機能を使用するには、`platform == "wecom"` の検証が必要です。企業微信のイベントは OneBot12 標準に従って変換され、`wecom_` という接頭辞でプラットフォーム拡張を提供します。

### メッセージイベント detail_type マッピング

企業微信アプリが受け取るメッセージはすべて `private`（プライベートメッセージ）にマッピングされます：

| 企業微信メッセージ | OneBot12 type / detail_type |
|---|---|
| `text` | `message` / `private` |
| `image` | `message` / `private` |
| `voice` | `message` / `private` |
| `video` / `shortvideo` | `message` / `private` |
| `location` | `message` / `private` |
| `link` | `message` / `private` |

### 特有イベントタイプ（notice）

| detail_type | 説明 |
|---|---|
| `wecom_subscribe` | ユーザーが登録 / アプリにアクセス（subscribe / enter_agent） |
| `wecom_unsubscribe` | ユーザーが登録解除 |
| `wecom_location_report` | 位置情報の報告 |
| `wecom_menu_click` | メニューアイテムをクリックしてイベントを発生（click） |
| `wecom_menu_view` | メニューアイテムをクリックしてリンクに移動（view） |
| `wecom_scancode` | スキャンしてイベントを発生 |
| `wecom_menu_photo` | 写真撮影 / ギャラリーイベント |

> 位置情報の報告や登録、メニューアイテムのクリックなどのイベントは `request` / `notice` タイプのイベントに変換されます。

### 標準メッセージセグメントタイプ

変換後のメッセージセグメントは OneBot12 標準形式を使用します：

| メッセージセグメントタイプ | 説明 | data フィールド |
|---|------|---|
| `text` | 純粋なテキスト | `text` |
| `image` | 画像 | `file`（PicUrl または MediaId）、`url` |
| `audio` | 音声 | `file`（MediaId） |
| `video` | 動画 | `file`（MediaId）、`thumbnail` |
| `location` | 位置情報 | `latitude`, `longitude`, `title` |
| `file` | ファイル / リンク | `file`, `filename`, `url` |

### プラットフォーム拡張メッセージセグメント

`wecom_` 接頭辞で識別される拡張メッセージセグメント（送信方向）：

| メッセージセグメントタイプ | 説明 | data フィールド |
|---|---|---|
| `wecom_markdown` | Markdown メッセージ | `content` |
| `wecom_news` | 図文メッセージ | `articles`（list） |
| `wecom_textcard` | テキストカード | `title`, `description`, `url`, `btntxt` |
| `wecom_miniprogram_notice` | 小プログラム通知 | 原生フィールドを透過 |
| `wecom_template_card` | テンプレートカード | `card_type` + 原生フィールド |

### イベント例

#### テキストメッセージ

```python
{
  "id": "1234567890123456",
  "time": 1348831860,
  "type": "message",
  "detail_type": "private",
  "platform": "wecom",
  "self": {"platform": "wecom", "user_id": "Corpid"},
  "message_id": "1234567890123456",
  "user_id": "UserID",
  "user_nickname": "UserID",
  "message": [{"type": "text", "data": {"text": "メッセージ内容"}}],
  "alt_message": "メッセージ内容",
  "wecom_raw": {"MsgType": "text", "Content": "メッセージ内容", "...": "..."},
  "wecom_raw_type": "text",
  "wecom_agentid": "1000002",
  "wecom_corpid": "Corpid",
  "wecom_msg_id": "1234567890123456"
}
```

> **0.1.2 変更点**：メッセージイベントにトップレベルの `message_id` を追加しました（企業微信の MsgId を使用し、存在しない場合は uuid をバックアップとして使用）。

#### メニューアイテムクリックイベント

```python
{
  "type": "notice",
  "detail_type": "wecom_menu_click",
  "platform": "wecom",
  "user_id": "UserID",
  "wecom_event_key": "menu_key_1",
  "wecom_raw_type": "event"
}
```

## Event Mixin 拡張メソッド

アダプターは以下のプラットフォーム固有メソッドを登録しており、`platform == "wecom"` の場合にのみ使用可能です。

| メソッド | 戻り値型 | 説明 |
|------|----------|------|
| `get_user_id()` | `str` | 送信者の UserID を取得します |
| `get_msg_type()` | `str` | 企業微信メッセージのタイプ（text/image/...）を取得します |
| `get_content()` | `str` | メッセージの純粋なテキスト内容を取得します |
| `get_agentid()` | `str` | アプリの AgentID を取得します |
| `get_corpid()` | `str` | 企業の Corpid を取得します |
| `get_msg_id()` | `str` | メッセージ MsgId を取得します |
| `get_raw_xml()` | `str` | 解読後の元の XML を取得します |
| `get_raw()` | `dict` | 解析後の元のデータ辞書を取得します |
| `get_event_key()` | `str` | メニューイベントの EventKey を取得します |
| `get_media_id()` | `str` | メディアメッセージの MediaId を取得します |

### 使用例

```python
from ErisPulse.Core.Event import message, notice

@message.on_message()
async def handle_message(event):
    if event.get("platform") != "wecom":
        return

    msg_type = event.get_msg_type()
    user_id = event.get_user_id()
    content = event.get_content()

    if msg_type == "text":
        await event.reply(f"受信: {content}")

@notice.on_notice()
async def handle_notice(event):
    if event.get("platform") != "wecom":
        return

    if event.get("detail_type") == "wecom_menu_click":
        key = event.get_event_key()
        await event.reply(f"メニューをクリックしました: {key}")
```

## 拡張フィールドの説明

- すべての固有フィールドは `wecom_` で始まるプレフィックスで識別されます
- 元のデータは `wecom_raw` フィールドに保持されます（解析後の辞書）
- 解読後の元の XML は `wecom_raw_xml` フィールドに保持されます
- 元のイベントタイプは `wecom_raw_type` フィールドに保持されます
- `wecom_corpid`：企業ID
- `wecom_agentid`：アプリケーション AgentID
- `wecom_msg_id`：企業微信メッセージID

## 認証と暗号化

### access_token 管理

- 各アカウントごとに access_token を個別にキャッシュ
- 有効期限は 7200 秒、5 分前に自動的に更新
- token が無効（errcode 40014/42001）になった場合、キャッシュを自動的にクリアして再試行

### メッセージの暗号化・復号

- アルゴリズム：AES-256-CBC（PKCS7 填充）
- 鍵：`base64decode(EncodingAESKey + "=")`（32 バイト）
- IV：鍵の先頭 16 バイト
- 署名：`sha1("".join(sorted([token, timestamp, nonce, encrypt])))`
- 依存ライブラリ：`cryptography`

## 注意事項

1. **コールバック URL はインターネットからアクセス可能でなければなりません**：ローカル開発時は、内網のトンネルを使用できます。本番環境では、Nginx を使用して ErisPulse router のポートにリバースプロキシすることを推奨します。
2. **アクティブな送信頻度**：企業微信のアプリメッセージインターフェースの制限（各アプリの毎日の送信量は企業の規模に関連）のため、一斉送信の場合は `TaskCard` / `TemplateCard` をタグと組み合わせて使用してください。
3. **access_token の有効性**：アダプターは自動的にリフレッシュします。同じ corpid + secret を使用する複数のインスタンスをデプロイする場合、公式のトークンの相互排除制限（推奨：1つのインスタンスで送受信を行う）に注意してください。
4. **メディアファイル**：Voice は AMR 形式（企業微信の制限）が必要です。大容量のファイルは一時素材インターフェースを使用してください（アダプターが自動的に処理します）。