# Matrixプラットフォーム特性ドキュメント

MatrixAdapter は [Matrixプロトコル](https://spec.matrix.org/) をベースに構築されたアダプターで、Matrixプロトコルのすべてのコア機能モジュールを統合し、統一されたイベント処理とメッセージ操作インターフェースを提供します。

---

## ドキュメント情報

- 対応モジュールバージョン: 4.6.1
- メンテナー: ErisPulse
- 最終更新: 2026-11-10

## 基本情報

- プラットフォーム概要：Matrixはオープンな分散型通信プロトコルで、プライベートチャットやグループなど複数のシナリオに対応します
- アダプター名：MatrixAdapter
- マルチアカウント対応：複数の Matrix アカウントの同時設定に対応
- 接続方式：Long Polling（Matrix Sync API `/sync` 経由）
- 認証方式：access_token、または user_id + password ログインによる token 取得
- チェーン修飾対応：`.Reply()`、`.At()`、`.AtAll()` などのチェーン修飾メソッドに対応
- OneBot12互換：OneBot12 形式メッセージの送信に対応

## 設定説明

MatrixAdapter はマルチアカウント設定をサポートしており、各アカウントごとに homeserver と認証情報を個別に設定します。

```toml
# config.toml
# アカウント1
[Matrix_Adapter.accounts.default]
homeserver = "https://matrix.org"          # Matrixサーバーアドレス（必須）
access_token = "YOUR_ACCESS_TOKEN"          # アクセストークン（user_id+password のいずれか一方を選択）
user_id = ""                                # MatrixユーザーID（例：@bot:matrix.org）
password = ""                               # Matrixユーザーパスワード
auto_accept_invites = true                  # ルーム招待を自動承認するか（任意、デフォルトtrue）
enabled = true                              # 有効にするか（任意、デフォルトtrue）

# アカウント2
[Matrix_Adapter.accounts.bot2]
homeserver = "https://matrix.example.com"
access_token = "ANOTHER_TOKEN"
enabled = true
```

> 旧設定との互換性：旧式の単一アカウント `[Matrix_Adapter]` 設定（access_token を含む）が検出された場合、自動的に `accounts.default` へ移行されます。

**設定項目の説明（各アカウント）：**
- `homeserver`：Matrixサーバーアドレス（必須）、デフォルトは `https://matrix.org`
- `access_token`：アクセストークン、Matrixクライアントから取得できます。既に token をお持ちの場合はそのまま記入してください
- `user_id`：MatrixユーザーID（例：`@bot:matrix.org`）、`password` と併用してログインします
- `password`：Matrixユーザーパスワード、自動ログインして access_token を取得するために使用します
- `auto_accept_invites`：ルーム招待を自動承認するかどうか、デフォルトは `true`
- `enabled`：このアカウントを有効にするか（任意、デフォルトtrue）
- `encryption_enabled`：エンドツーエンド暗号化を有効にするかどうか、デフォルトは `false`
- `trust_all_devices`：未検証デバイスを自動信頼するかどうか（E2EE）、デフォルトは `true`
- `device_id`：デバイス ID（E2EE、通常は自動取得されるため記入不要）
- `store_path`：暗号化セッション保存ディレクトリ（E2EE）、デフォルトは `data/matrix/<アカウント名>`

**認証方式：**
- 方法1（推奨）：`access_token` を直接指定
- 方法2：`user_id` と `password` を指定すると、アダプターが自動的にログインAPIを呼び出して token を取得します

## v5 パラダイム更新（4.2.0）

- **BaseConverter 継承**：コンバーターの共通フィールドはフレームワークの build_base_event によって構築されます
- **Api DSL**：get_self_info/get_user_info/get_group_info/get_group_list/get_group_member_list/leave_group/delete_message(redact) + メタアクション
- **メッセージイベントへの message_id 追加**（event_id）；メッセージレジストリが delete_message をサポート
- **spawn_background タスク帰属**：同期/ハートビートタスクは runtime.spawn_background を使用するように変更
- **フレームワークのソフト依存**：実行時に ErisPulse>=2.7.1 を検出して通知；起動時にバージョンログを出力
- Matrix にはネイティブのボタン機能がないため、標準 keyboard セグメントは警告なしに無視されます（エラーにはなりません）

## エンドツーエンド暗号化（4.3.0）

4.3.0 から、アダプターは暗号化ルームのエンドツーエンド暗号化（matrix-nio[e2e] / vodozemac ベース）をネイティブサポートします：

```toml
[Matrix_Adapter.accounts.default]
user_id = "@bot:matrix.org"
password = "YOUR_PASSWORD"
encryption_enabled = true       # 有効化（デフォルトは false、既存デプロイへの影響なし）
trust_all_devices = true        # 未検証デバイスを自動信頼（デフォルト；false は厳格モード）
```

- 暗号化ルームでのメッセージ送受信は自動的に復号/暗号化、メディアはエンドツーエンド暗号化（`m.file.encrypted`）
- `device_id` は自動解析・永続化されます；セッションは `store_path`（デフォルト `data/matrix/<アカウント名>`）に保存されます。**削除しないでください**、削除すると過去のメッセージを復号できなくなります
- イベント Mixin に `event.is_encrypted()` を追加；メディアセグメントには `matrix_encrypted_file`（JWK）が付与され、`MatrixAdapter.decrypt_media()` で復号できます
- クロス署名とサーバー側キーバックアップには非対応；Python >= 3.10 が必要です
- 無効または matrix-nio 未インストールの場合は、自動的に平文モードへフォールバックします

詳細は後述の[エンドツーエンド暗号化（E2EE）](#エンドツーエンド暗号化e2ee)セクションおよび[アダプター README](https://github.com/ErisPulse/ErisPulse-MatrixAdapter) を参照してください。

## 標準化アラインメント

このセクションでは、アダプターと ErisPulse 標準化仕様の整合動作について説明します。仕様の詳細は SDK ドキュメント『API レスポンス仕様』（`docs/ja/standards/api-response.md`）および『送信メソッド仕様』（`docs/ja/standards/send-method-spec.md`）を参照してください。

### マルチアカウント受理（4.6.1 以降）

- すべてのイベントに `self.account_id`（送信元アカウント名）が注入されます；access_token ログインのアカウントも、`user_id` が空の場合でもマルチアカウント受理とイベントルーティングを正しく完了できます

### エラーコード標準化（4.6.x）

- **メディアアップロード/ダウンロード失敗とリクエストタイムアウトは一律 33001**（ネットワークエラー）
- **プラットフォーム API 失敗は一律 34100**（プラットフォームエラー）、Matrix errcode は `message` と `matrix_raw` フィールドに保持されます
- **取り消しコンテキスト欠落 10003**：`delete_message` がメッセージの帰属コンテキストを見つけられない場合、パラメータエラーを返します

| retcode | 説明 |
|---------|------|
| 0 | 成功 |
| 10002 | サポートされていないアクション（例：get_friend_list、Matrix には友人の概念がない） |
| 10003 | 送信先が無効（Matrix ルームとして解析できない）、取り消しコンテキストの欠落 |
| 33001 | ネットワークエラー（メディアアップロード/ダウンロード失敗、リクエストタイムアウト） |
| 34100 | プラットフォーム API 失敗（Matrix errcode は message と matrix_raw に保持） |

### Send 仕様

- Send 全メソッドは `send_context` を読み取ります：イベントチェーン内では自動的に現在のイベント送信元アカウントを使用し、明示的に `Using()` で指定されたアカウントが優先されます
- HTML メソッド：`.Html(html, fallback)` でリッチテキストメッセージを送信；`HTML` は仕様上のスペル別名です（`Html` は既存モジュールとの互換性のため保持）
- `get_group_list` の戻り値の各項目に `group_name` フィールドを補完します（`get_group_info` と一致）

### 標準Apiアクション例

```python
from ErisPulse import sdk
matrix = sdk.adapter.get("matrix")
result = await matrix.Api.get_self_info()            # /account/whoami
result = await matrix.Api.get_group_info(room_id)    # m.room.name
result = await matrix.Api.get_group_list()           # /joined_rooms（各項目に group_name を含む）
await matrix.Api.delete_message(event_id)            # redact（レジストリが room_id を補完）
```

---

### 対応済みプラットフォーム機能

- **イベント**：メッセージ（m.room.message：テキスト/画像/ファイル/音声動画/返信/編集）、メンバー増減（m.room.member）、ルーム名変更などの状態イベント
- **セッション**：プライベートチャット（DM ルーム自動検出）/ グループ（ルーム）；送信は Text/Image/File/Voice/Video/Markdown/Raw_ob12 に対応
- **API**：whoami/profile/joined_rooms/ルーム状態/メンバーリスト/leave/redact（上記の Api DSL を参照）

---

## サポートされるメッセージ送信タイプ

すべての送信メソッドはチェーン構文で実装されています。例：
```python
from ErisPulse.Core import adapter
matrix = adapter.get("matrix")

await matrix.Send.To("group", room_id).Text("Hello World!")
```

サポートされる送信タイプ：
- `.Text(text: str)`：プレーンテキストメッセージを送信します。
- `.Image(file: bytes | str)`：画像メッセージを送信します。ファイルパス、URL、MXC URI、バイナリデータに対応します。
- `.Voice(file: bytes | str)`：ボイスメッセージを送信します。ファイルパス、URL、MXC URI、バイナリデータに対応します。
- `.Video(file: bytes | str)`：動画メッセージを送信します。ファイルパス、URL、MXC URI、バイナリデータに対応します。
- `.File(file: bytes | str, filename: str = "")`：ファイルメッセージを送信します。ファイルパス、URL、MXC URI、バイナリデータに対応します。
- `.Notice(text: str)`：通知メッセージを送信します（Matrix の m.notice タイプ）。
- `.Html(html: str, fallback: str = "")`：HTML形式のメッセージを送信します。リッチテキストコンテンツに対応します（`HTML` は仕様上のスペル別名）。
- `.MergeForward(nodes, title="チャット履歴の結合")`：結合転送メッセージを送信します（formatted_body blockquote 引用ブロック形式；ホワイトリストにより details/インラインスタイルが剥離されます）。
- `.Raw_ob12(message: List[Dict], **kwargs)`：OneBot12 形式のメッセージを送信します。

### チェーン修飾メソッド（組み合わせ使用可能）

チェーン修飾メソッドは `self` を返し、チェーン呼び出しに対応しています。最終的な送信メソッドの前に呼び出す必要があります：

- `.Reply(message_id: str)`：指定したメッセージに返信します（Matrix `m.in_reply_to` 関係を使用）。
- `.At(user_id: str)`：指定したユーザーをメンションします（Matrix `m.mentions` フィールドで実装）。
- `.AtAll()`：ルーム内の全員をメンションします（Matrix `@room` メンションで実装）。

### チェーン呼び出し例

```python
# 基本送信（"user" ターゲットはユーザーID（@user:server、DMルームを自動逆引き）またはルームID（!room:server）をサポート）
await matrix.Send.To("user", "@alice:matrix.org").Text("Hello")

# メッセージに返信
await matrix.Send.To("group", room_id).Reply("$event_id").Text("返信メッセージ")

# ユーザーをメンション
await matrix.Send.To("group", room_id).At("@user:matrix.org").Text("こんにちは")

# 全員をメンション
await matrix.Send.To("group", room_id).AtAll().Text("お知らせ通知")

# 組み合わせ使用：返信 + メンション
await matrix.Send.To("group", room_id).Reply("$event_id").At("@user:matrix.org").Text("複合メッセージ")

# HTMLメッセージの送信
await matrix.Send.To("group", room_id).Html("<h1>タイトル</h1><p>内容</p>", fallback="タイトル\n内容")

# 通知メッセージの送信
await matrix.Send.To("group", room_id).Notice("システム通知")
```

### OneBot12メッセージサポート

アダプターは OneBot12 形式のメッセージ送信をサポートし、クロスプラットフォームのメッセージ互換を実現します：

```python
# OneBot12 形式メッセージの送信
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await matrix.Send.To("user", dm_room_id).Raw_ob12(ob12_msg)

# チェーン修飾との併用
ob12_msg = [{"type": "text", "data": {"text": "返信メッセージ"}}]
await matrix.Send.To("group", room_id).Reply("$event_id").Raw_ob12(ob12_msg)

# 複雑なメッセージ
ob12_msg = [
    {"type": "text", "data": {"text": "この画像を見てください："}},
    {"type": "image", "data": {"file": "https://example.com/image.png"}},
    {"type": "text", "data": {"text": "悪くないでしょう？"}}
]
await matrix.Send.To("group", room_id).Raw_ob12(ob12_msg)

# 位置情報メッセージ（標準 location セグメント → Matrix m.location；テキストと共存する場合は独立したイベントに分割）
ob12_msg = [
    {"type": "text", "data": {"text": "私はここにいます"}},
    {"type": "location", "data": {"latitude": 39.9, "longitude": 116.4, "title": "北京市"}}
]
await matrix.Send.To("group", room_id).Raw_ob12(ob12_msg)
```

## 送信メソッドの戻り値

すべての送信メソッドは Task オブジェクトを返し、await で直接送信結果を取得できます。戻り結果は ErisPulse アダプター標準化戻り値仕様に従います：

```python
{
    "status": "ok",           // 実行状態: "ok" または "failed"
    "retcode": 0,             // 戻りコード
    "data": {...},            // レスポンスデータ
    "message_id": "$event_id", // MatrixイベントID
    "message": "",            // エラーメッセージ
    "matrix_raw": {...}       // 生のレスポンスデータ
}
```

エラーコードの仕様については、前述の[標準化アラインメント](#標準化アラインメント)セクションを参照してください。

## 固有イベントタイプ

本プラットフォームの特性機能を使用するには、`platform=="matrix"` による判定が必要です

### コア差分ポイント

1. **分散型アーキテクチャ**：Matrix は分散型通信プロトコルで、ユーザーIDの形式は `@user:server.domain`、ルームIDの形式は `!room_id:server.domain` です
2. **ルーム概念**：Matrix はグループチャットとプライベートチャットを区別せず、すべてのセッションは「ルーム」です。アダプターは DM（Direct Message）アカウントデータによりプライベートチャットルームを自動識別します
3. **Long Polling 同期**：WebSocket ではなく `/sync` API によるロングポーリングで新イベントを取得します
4. **MXC URI**：メディアファイルは `mxc://server.domain/media_id` 形式で参照されます
5. **HTML リッチテキスト**：`formatted_body` による HTML 形式メッセージの送信に対応します
6. **絵文字リアクション**：メッセージレベルの絵文字リアクション（Reaction）に対応し、従来の返信メッセージとは異なります
7. **メッセージ編集**：`m.replace` 関係による送信済みメッセージの編集に対応します
8. **メッセージ取り消し**：`m.room.redaction` によるメッセージの取り消し/削除に対応します

### 拡張フィールド

- すべての固有フィールドは `matrix_` プレフィックスで識別されます
- 生データは `matrix_raw` フィールドに保持されます
- `matrix_raw_type` は元のMatrixイベントタイプを識別します（例：`m.room.message`、`m.room.member`）

### 特殊フィールド例

```python
# グループメッセージ
{
  "type": "message",
  "detail_type": "group",
  "user_id": "@user:matrix.org",
  "group_id": "!room_id:matrix.org",
  "matrix_room_id": "!room_id:matrix.org"
}

# プライベートチャットメッセージ
{
  "type": "message",
  "detail_type": "private",
  "user_id": "@user:matrix.org",
  "matrix_room_id": "!dm_room_id:matrix.org"
}

# 絵文字リアクション
{
  "type": "notice",
  "detail_type": "matrix_reaction",
  "matrix_reaction_event_id": "$reacted_msg_id",
  "matrix_reaction_key": "👍"
}

# メッセージ取り消し
{
  "type": "notice",
  "detail_type": "matrix_redaction",
  "matrix_redacted_event_id": "$deleted_msg_id"
}

# メッセージ編集
{
  "type": "message",
  "detail_type": "group",
  "matrix_edit": true,
  "matrix_original_event_id": "$original_event_id"
}

# スレッドメッセージ
{
  "type": "message",
  "detail_type": "group",
  "thread_id": "$thread_root_id"
}
```

### メッセージセグメントタイプ

Matrixメッセージは `msgtype` に基づいて自動的に対応するメッセージセグメントへ変換されます：

| msgtype | 変換タイプ | 説明 |
|---|---|---|
| m.text | `text` | テキストメッセージ |
| m.notice | `text` | 通知メッセージ |
| m.emote | `text` | アクションメッセージ |
| m.image | `image` | 画像メッセージ |
| m.audio | `audio` | オーディオメッセージ（標準メッセージセグメント名は `audio`；`voice` は送信メソッド名であり、セグメント名ではありません） |
| m.video | `video` | 動画メッセージ |
| m.file | `file` | ファイルメッセージ |
| m.location | `location` | 位置情報メッセージ（latitude/longitude は geo URI から解析） |

> メンション（mention）：メッセージ content 内の `m.mentions`（Matrix v1.11+ 仕様）は標準 `mention` セグメントに変換されます——
> `m.mentions.user_ids` → `mention(user_id=...)`、`m.mentions.room` → `mention(user_id="all")`。

メッセージセグメント構造例：

```json
// テキストメッセージ（HTML付き）
{
  "type": "text",
  "data": {
    "text": "プレーンテキスト内容",
    "html": "<b>HTMLコンテンツ</b>"
  }
}

// 画像メッセージ
{
  "type": "image",
  "data": {
    "url": "mxc://matrix.org/abc123",
    "filename": "photo.png",
    "matrix_mxc": "mxc://matrix.org/abc123",
    "info": {
      "mimetype": "image/png",
      "w": 800,
      "h": 600,
      "size": 123456
    }
  }
}

// 位置情報メッセージ（latitude/longitude は geo URI から解析）
{
  "type": "location",
  "data": {
    "latitude": 39.9,
    "longitude": 116.4,
    "matrix_geo_uri": "geo:39.9,116.4",
    "text": "北京市"
  }
}
```

### Event Mixin メソッド

MatrixAdapter は以下のイベント Mixin メソッドを登録しており、イベント処理内で直接呼び出せます：

| メソッド | 戻り値の型 | 説明 |
|------|----------|------|
| `get_room_id()` | `str` | ルームIDを取得 |
| `get_matrix_event_type()` | `str` | 元のMatrixイベントタイプを取得 |
| `get_matrix_sender()` | `str` | 元の送信者IDを取得 |
| `get_reaction_key()` | `str` | リアクションの絵文字を取得 |
| `is_edited()` | `bool` | メッセージが編集メッセージかどうかを判定 |
| `is_notice()` | `bool` | メッセージが m.notice タイプかどうかを判定 |

```python
@message.on_message()
async def handle_message(event):
    if event.get("platform") != "matrix":
        return

    room_id = event.get_room_id()
    event_type = event.get_matrix_event_type()
    sender = event.get_matrix_sender()
    is_edited = event.is_edited()
    is_notice = event.is_notice()
```

## Sync API 接続

### 同期フロー

1. access_token または user_id + password で認証します
2. `/_matrix/client/v3/account/whoami` を呼び出して bot_user_id を取得します
3. connect メタイベントを発行します
4. 初期同期（`/_matrix/client/v3/sync?timeout=0`）を実行して `next_batch` token を取得します
5. DM ルームを検出します（`/_matrix/client/v3/user/{user_id}/account_data/m.direct`）
6. Long Polling 同期ループを開始します（`/_matrix/client/v3/sync?since={next_batch}&timeout=30000`）
7. 各同期で返された新イベントを処理し、変換して発行します

### ハートビートメカニズム

- アダプターは 30 秒ごとに `heartbeat` メタイベントを発行します
- 接続成功時に `connect` メタイベントを発行します
- 切断時に `disconnect` メタイベントを発行します

### ルーム招待

- ルーム招待（`invite` 状態のルーム）を受信した際、`auto_accept_invites` が `true`（デフォルト）に設定されている場合、アダプターは自動的にルームへ参加します
- ルームへの参加には `/_matrix/client/v3/join/{room_id}` API を呼び出します

## エンドツーエンド暗号化（E2EE）

アダプターは 4.3.0 から、暗号化ルームのエンドツーエンド暗号化（matrix-nio[e2e] / vodozemac ベース）をネイティブサポートし、`encryption_enabled = true` で有効化できます。

### 動作メカニズム

- **同期**：有効化後、同期は nio E2EE セッションを経由し、デバイスキーのアップロード、ワンタイムキーの補充、to-device メッセージ（Olm/Megolm セッションキー配布）はすべて自動処理されます；timeline 内の `m.room.encrypted` イベントは自動的に平文イベントへ復号され、その後統一変換が行われます
- **送信**：ターゲットルームが暗号化ルームの場合、自動的に Megolm セッションを共有してペイロードを暗号化します；復号に失敗したイベントはスキップされ、警告が記録されます
- **メディア**：暗号化ルームでのメディアアップロードはエンドツーエンド暗号化（`m.file.encrypted`）です；受信側のメディアセグメントには `matrix_encrypted_file`（JWK、url/key/iv/hashes を含む）が付与され、暗号文をダウンロードした後、`MatrixAdapter.decrypt_media(ciphertext, key, iv, sha256)` で復号できます
- **デバイス**：`device_id` は自動解析（ログインレスポンス → `/whoami` → ローカル永続化）され、パスワードでの再ログイン時は同一デバイスを再利用します；`trust_all_devices = true`（デフォルト）は未検証デバイスを自動信頼（bot シナリオでの慣例）、`false` は厳格モードです
- **フォールバック**：E2EE が無効または matrix-nio が未インストールの場合、自動的に平文 REST パスへフォールバックし、動作は旧版と完全に一致します

### モジュール側インターフェース

- イベント Mixin：`event.is_encrypted()` でメッセージが暗号化ルームからのものかを判定
- メディアセグメントフラグ：`encrypted: true` と `matrix_encrypted_file`（JWK）
- 復号ヘルパー：`MatrixAdapter.decrypt_media(file_bytes, key, iv, hash_value) -> bytes`

### 既知の制限

- クロス署名（cross-signing）とサーバー側キーバックアップ（room key backup）には対応していません
- ローカルセッション保存ディレクトリ（`store_path`、デフォルト `data/matrix/<アカウント名>`）を削除すると、過去のメッセージを復号できなくなります
- 対話式 SAS（絵文字）検証は現時点で未対応で、今後のバージョンで提供予定です

## 使用例

### グループメッセージの処理

```python
from ErisPulse.Core.Event import message
from ErisPulse import sdk

matrix = sdk.adapter.get("matrix")

@message.on_message()
async def handle_group_msg(event):
    if event.get("platform") != "matrix":
        return
    if event.get("detail_type") != "group":
        return

    text = event.get_text()
    room_id = event.get("group_id")

    if text == "hello":
        await matrix.Send.To("group", room_id).Reply(
            event.get("message_id")
        ).Text("Hello!")
```

### 絵文字リアクションの処理

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_reaction(event):
    if event.get("platform") != "matrix":
        return

    if event.get("detail_type") == "matrix_reaction":
        reaction_key = event.get("matrix_reaction_key")
        reacted_event_id = event.get("matrix_reaction_event_id")
        room_id = event.get_room_id()
        # 絵文字リアクションを処理...
```

### メディアメッセージの送信

```python
# 画像の送信（URL）
await matrix.Send.To("group", room_id).Image("https://example.com/image.png")

# 画像の送信（MXC URI）
await matrix.Send.To("group", room_id).Image("mxc://matrix.org/abc123")

# 画像の送信（バイナリデータ）
with open("image.png", "rb") as f:
    image_bytes = f.read()
await matrix.Send.To("group", room_id).Image(image_bytes)

# 画像の送信（ローカルファイルパス）
await matrix.Send.To("group", room_id).Image("/path/to/image.png")

# ファイルの送信（ファイル名付き）
await matrix.Send.To("group", room_id).File("/path/to/document.pdf", filename="ドキュメント.pdf")
```

### メッセージ編集の処理

```python
@message.on_message()
async def handle_edited_message(event):
    if event.get("platform") != "matrix":
        return

    if event.is_edited():
        original_id = event.get("matrix_original_event_id")
        # 編集メッセージを処理...
```

### メンバー変更の監視

```python
@notice.on_notice()
async def handle_member_change(event):
    if event.get("platform") != "matrix":
        return

    detail_type = event.get("detail_type")

    if detail_type == "group_member_increase":
        user_id = event.get("user_id")
        nickname = event.get("user_nickname")
        print(f"ユーザー {nickname} ({user_id}) がルームに参加しました")

    elif detail_type == "group_member_decrease":
        user_id = event.get("user_id")
        operator_id = event.get("operator_id")
        print(f"ユーザー {user_id} が削除されました、操作者: {operator_id}")
```