# 雲湖プラットフォームの特徴ドキュメント

YunhuAdapterは、雲湖プロトコルに基づいて構築されたアダプタであり、すべての雲湖機能モジュールを統合し、一貫したイベント処理とメッセージ操作インターフェースを提供します。

---

## ドキュメント情報

- 対応モジュールバージョン: 4.5.0
- 維持者: ErisPulse

## 基本情報

- プラットフォーム概要: 雲湖（Yunhu）はエンタープライズ向けのリアルタイム通信プラットフォームです。
- アダプタ名: YunhuAdapter
- マルチアカウント対応: bot_id で識別可能な複数の雲湖ロボットアカウントをサポート
- チェーン修飾子対応: .Reply() などのチェーン修飾子メソッドをサポート
- OneBot12互換: OneBot12形式のメッセージ送信をサポート

## v5 フレームワークアップデート (4.4.0)

本アダプタは v5 フレームワークにアップデートを完了しました（累積アップグレード、API互換性を保証）：

- **公式サービスAPI全集**（Api DSL 拡張メソッド）: 編集メッセージ、一括送信、メッセージリスト、ユーザー/グローバルボード、グループメンバーのミュート、グループメンバーの削除、グループメッセージの種類制限、グループタグの CRUD、ユーザーにタグを付ける
- **標準 keyboard 段**（跨プラットフォームのインタラクションコンポーネント標準）: {"type": "keyboard", "data": {"rows": [[{"label", "type": "callback|link", "data"}]]}} 段は自動的に雲湖の buttons に変換されます。.Buttons(rows) / .Keyboard(rows) 修飾子は汎用構造を受け入れます（元の構造は後方互換性を保証）
- **インタラクションコールバック標準フィールド**: ボタンクリック/A2UI イベントには interaction_id / button_data という標準フィールドが含まれます
- **spawn_background タスクの所属**: WS 接続タスクは runtime.spawn_background を使用
- **フレームワークのソフト依存**: ErisPulse>=2.7.1 を実行時に検出し、警告を表示します。起動時にバージョンログを出力します

### プラットフォーム拡張アクション（call / Api メソッド）

```python
from ErisPulse import sdk
yunhu = sdk.adapter.get("yunhu")

# Api メソッド（公式サービスAPI）
await yunhu.Api.edit_message(msg_id, recv_id, "group", "text", {"text": "新内容"})
await yunhu.Api.batch_send(["userId1", "userId2"], "text", {"text": "公告"})
await yunhu.Api.get_message_list(group_id, "group", before=10)
await yunhu.Api.set_user_board(chat_id, "group", "看板内容", expire_time=3600)
await yunhu.Api.dismiss_global_board()
await yunhu.Api.gag_group_member(group_id, user_id, 600)      # 禁言600秒、0=解除
await yunhu.Api.remove_group_member(group_id, user_id)
await yunhu.Api.set_group_msg_type_limit(group_id, "text,image")
await yunhu.Api.create_group_tag(group_id, "VIP", color="#FF5733")
await yunhu.Api.add_user_tag(group_id, user_id, "VIP")

# ボタンクリックコールバック（標準フィールド）
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_button(event):
    if event.get("platform") == "yunhu" and event.get("button_data"):
        data = event["button_data"]     # 跨プラットフォーム統一取値
        interaction_id = event["interaction_id"]
```

> 完全な標準説明は [跨プラットフォームインタラクションコンポーネント標準](../standards/standardization-guide.md) を参照してください。

---
## 支援するメッセージ送信タイプ

すべての送信メソッドはチェーン構文で実現されます。例えば:

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

await yunhu.Send.To("user", user_id).Text("Hello World!")
```

サポートする送信タイプは以下の通りです:

- `.Text(text: str)`：テキストメッセージを送信します。
- `.Html(html: str)`：HTML形式のメッセージを送信します。
- `.Markdown(markdown: str)`：Markdown形式のメッセージを送信します。
- `.MergeForward(nodes, title="合併チャット記録")`：合併転送メッセージを送信します（`<details>`折りたたみHTMLカードとしてレンダリングされ、htmlチャネルを介して送信されます）。
- `.A2UI(text: str)`：A2UI形式のメッセージを送信します。
- `.Image(file: bytes, stream: bool = False, filename: str = None)`：画像メッセージを送信します。ストリームアップロードとカスタムファイル名をサポートします。
- `.Video(file: bytes, stream: bool = False, filename: str = None)`：動画メッセージを送信します。ストリームアップロードとカスタムファイル名をサポートします。
- `.File(file: bytes, stream: bool = False, filename: str = None)`：ファイルメッセージを送信します。ストリームアップロードとカスタムファイル名をサポートします。
- `.Batch(target_ids: List[str], message: str, content_type: str = "text", **kwargs)`：一括メッセージ送信。
- `.Edit(msg_id: str, text: str, content_type: str = "text", buttons: List = None)`：既存のメッセージを編集します。
- `.Recall(msg_id: str)`：メッセージを撤回します。
- `.Board(content: str, content_type: str = "text")`：公告ボードを送信します。`To()` で推論される作用域（指定されたターゲット=ローカルボード、未指定=グローバルボード）。チェーン修飾子：`.Expire(duration)` 相対的な有効期限（秒）、`.ExpireAt(timestamp)` 絶対的な有効期限（秒単位のタイムスタンプ）、`.ForMember(member_id)` グループメンバーのボード；**コンテンツが空の場合は自動的にボードの撤回に変換されます**。旧式の `Board("local", "公告")` 明示的な scope 書き方もまだ互換性があります。
- `.DismissBoard()`：公告ボードを撤回します。作用域は `To()` で推論され、`.ForMember(member_id)` もサポートします；旧式の `DismissBoard("local")` 書き方もまだ互換性があります。
- `.Stream(content_type: str, content_generator: AsyncGenerator, **kwargs)`：ストリームメッセージを送信します。

### グループ管理メソッド

すべてのグループ管理メソッドは、チェーン構文でグループを指定する必要があります。例えば:

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

await yunhu.Send.To("group", group_id).Kick(user_id)
```

- `.Kick(user_id: str)`：グループメンバーを削除します。ロボットには「グループメンバーの削除を許可」権限が必要です。
- `.Ban(user_id: str, duration: int = 600)`：ユーザーをミュートします。`duration` はミュート期間（秒）、0 は解除、-1 は永久ミュートです。ロボットには「ユーザーのミュートを許可」権限が必要です。
- `.CreateTag(tag: str, color: str = None, desc: str = None, sort: int = None)`：グループタグを作成します。`color` は #RRGGBB 形式、`sort` は小さいほど上に表示されます。ロボットには「タググループの制御を許可」権限が必要です。
- `.EditTag(tag: str, new_tag: str = None, color: str = None, desc: str = None, sort: int = None)`：グループタグを編集します。各パラメータはオプションで、指定しない場合は変更されません。ロボットには「タググループの制御を許可」権限が必要です。
- `.DeleteTag(tag: str)`：グループタグを削除します。ロボットには「タググループの制御を許可」権限が必要です。
- `.GetTagList()`：グループタグリストを取得します。`list` 配列を含むレスポンスデータを返します。
- `.AddUserTag(user_id: str, tag: str)`：ユーザーにタグを追加します。ロボットには「タググループの制御を許可」権限が必要です。
- `.RemoveUserTag(user_id: str, tag: str)`：ユーザーからタグを削除します。ロボットには「タググループの制御を許可」権限が必要です。
- `.SetMsgTypeLimit(types: str)`：グループ内のメッセージの種類を制限します。`types` はメッセージ種類名、複数指定はカンマ区切り（例: "text,image,video"）、空文字列は制限なしを意味します。ロボットには「グループ情報の変更を許可」権限が必要です。

### メッセージ検索メソッド

指定された会話（ユーザー/グループ）の履歴メッセージリストを取得するには、チェーン構文でターゲットを指定する必要があります。例えば:

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

result = await yunhu.Send.To("group", group_id).GetMessages(before=10)
```

- `.GetMessages(message_id: str = None, before: int = None, after: int = None)`：会話の履歴メッセージを取得します。`list` 配列と `total` 総数を含むレスポンスデータを返します。
  - `message_id`：メッセージID（オプション）。指定しない場合、`before` と組み合わせて最近のN件を返します。
  - `before`：指定したメッセージIDの前のN件を返します。
  - `after`：指定したメッセージIDの後のN件を返します。
  - > **注意:** `before` と `after` の少なくとも1つは0より大きく指定する必要があります。そうでない場合、サーバーはメッセージを返しません。

Board 作用域は `To()` によって自動的に推論されます：
- `To(target_type, target_id)` を指定した場合 → ローカルボード（指定されたユーザー/グループ）
- `To()` を指定していない場合 → グローバルボード

```python
# ローカルボード（60秒後に相対的に期限切れ）
await yunhu.Send.To("group", group_id).Expire(60).Board("公告", content_type="markdown")

# グループメンバーのボード（特定のメンバーのみが見える）
await yunhu.Send.To("group", group_id).ForMember(user_id).Board("あなただけが見える")

# 絶対時間スタンプで期限切れ
await yunhu.Send.To("group", group_id).ExpireAt(1785208268).Board("指定された時間に期限切れ")

# グローバルボード
await yunhu.Send.Board("グローバル公告")

# ローカルボードのクリア（コンテンツが空の場合は自動的にボードの撤回）
await yunhu.Send.To("group", group_id).Board("")
```

### ボタンパラメータの説明

`buttons` パラメータは、ボタンのレイアウトと機能を示すネストされたリストです。各ボタンオブジェクトには以下のフィールドが含まれます：

| フィールド         | 型   | 必須 | 説明                                                                 |
|--------------|--------|----------|----------------------------------------------------------------------|
| `text`       | string | 是       | ボタン上の文字                                                         |
| `actionType` | int    | 是       | アクションタイプ：<br>`1`: URLにジャンプ<br>`2`: コピー<br>`3`: 投稿イベント |
| `url`        | string | 否       | `actionType=1` の場合使用され、ジャンプ先のURLを示します                         |
| `value`      | string | 否       | `actionType=2` の場合、この値がクリップボードにコピーされます<br>`actionType=3` の場合、この値がサブスクライバーに送信されます |

例:
```python
buttons = [
    [
        {"text": "コピー", "actionType": 2, "value": "xxxx"},
        {"text": "クリックしてジャンプ", "actionType": 1, "url": "http://www.baidu.com"},
        {"text": "イベントを報告", "actionType": 3, "value": "xxxxx"}
    ]
]
await yunhu.Send.To("user", user_id).Buttons(buttons).Text("ボタン付きメッセージ")
```
> **注意:**
> - ユーザーが**イベントを報告するボタン**をクリックした場合のみ、プッシュを受け取れます。**コピー**と**URLジャンプ**はプッシュを受け取ることができません。

### チェーン修飾子メソッド（複数使用可能）

チェーン修飾子メソッドは `self` を返し、チェーン呼び出しをサポートします。最終的な送信メソッドの前に呼び出す必要があります：

- `.Reply(message_id: str)`：指定されたメッセージに返信します。
- `.At(user_id: str)`：指定されたユーザーを@します。
- `.AtAll()`：全員を@します。
- `.Buttons(buttons: List)`：ボタンを追加します。

### チェーン呼び出しの例

```python
# 基本的な送信
await yunhu.Send.To("user", user_id).Text("Hello")

# メッセージに返信
await yunhu.Send.To("group", group_id).Reply(msg_id).Text("返信メッセージ")

# 返信 + ボタン
await yunhu.Send.To("group", group_id).Reply(msg_id).Buttons(buttons).Text("返信とボタン付きメッセージ")
```

### グループ管理の例

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# グループメンバーの削除
await yunhu.Send.To("group", group_id).Kick(user_id)

# ユーザーのミュート（10分間）
await yunhu.Send.To("group", group_id).Ban(user_id, duration=600)

# ミュートの解除
await yunhu.Send.To("group", group_id).Ban(user_id, duration=0)

# 永久ミュート
await yunhu.Send.To("group", group_id).Ban(user_id, duration=-1)

# グループタグの作成
await yunhu.Send.To("group", group_id).CreateTag("VIPユーザー", color="#FF5733", desc="VIP会員")

# グループタグの編集
await yunhu.Send.To("group", group_id).EditTag("VIPユーザー", new_tag="SVIPユーザー", color="#33C4FF")

# グループタグの削除
await yunhu.Send.To("group", group_id).DeleteTag("VIPユーザー")

# グループタグリストの取得
result = await yunhu.Send.To("group", group_id).GetTagList()

# ユーザーにタグを追加
await yunhu.Send.To("group", group_id).AddUserTag(user_id, "VIPユーザー")

# ユーザーからタグを削除
await yunhu.Send.To("group", group_id).RemoveUserTag(user_id, "VIPユーザー")

# メッセージの種類制限
await yunhu.Send.To("group", group_id).SetMsgTypeLimit("text,image,video")

# メッセージの種類制限の解除
await yunhu.Send.To("group", group_id).SetMsgTypeLimit("")
```

### メッセージ検索の例

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# グループの最近10件のメッセージを取得（合計10件返される）
result = await yunhu.Send.To("group", group_id).GetMessages(before=10)

# グループで指定されたメッセージIDの前の10件を取得（合計11件返される）
result = await yunhu.Send.To("group", group_id).GetMessages(message_id="msg_xxx", before=10)

# グループで指定されたメッセージIDの前後各10件を取得（合計21件返される）
result = await yunhu.Send.To("group", group_id).GetMessages(message_id="msg_xxx", before=10, after=10)

# ユーザー会話の履歴メッセージを取得
result = await yunhu.Send.To("user", user_id).GetMessages(message_id="msg_xxx", before=10)
```

### OneBot12メッセージのサポート

このアダプタはOneBot12形式のメッセージ送信をサポートし、プラットフォーム間のメッセージ互換性を確保します：

- `.Raw_ob12(message: List[Dict], **kwargs)`：OneBot12形式のメッセージを送信します。

```python
# OneBot12形式のメッセージを送信
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await yunhu.Send.To("user", user_id).Raw_ob12(ob12_msg)

# チェーン修飾子と組み合わせる
ob12_msg = [{"type": "text", "data": {"text": "返信メッセージ"}}]
await yunhu.Send.To("group", group_id).Reply(msg_id).Raw_ob12(ob12_msg)
```

## 標準APIアクション（ApiDSL）

> [!NOTE]
> この機能は ErisPulse **2.7.0+** および YunhuAdapter **4.3.0+** が必要です。

`Send` チェーン送信に加えて、アダプタは `Api` 内部クラスを提供し、OneBot12標準APIアクションと雲湖プラットフォームの拡張アクションを公開します。すべてのメソッドは標準レスポンス形式を返します。

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# 情報取得（公開Web APIを介して、認証不要）
result = await yunhu.Api.get_self_info()              # ロボット自身の情報
result = await yunhu.Api.get_user_info("7058262")     # 任意のユーザー情報
result = await yunhu.Api.get_group_info("635409929")  # グループ情報

# ファイル操作
result = await yunhu.Api.upload_file(type="path", name="a.png", path="./a.png")
result = await yunhu.Api.get_file("https://chat-file.jwznb.com/xxx")

# メッセージの撤回（chat_id + chat_type の追加が必要）
await yunhu.Api.delete_message("msg_id", chat_id="123", chat_type="group")

# 多アカウント：特定のBotアカウントを指定
info = await yunhu.Api.Using("bot1").get_self_info()
```

### 対応する標準アクション

| メソッド | 説明 | データソース |
|------|------|---------|
| `get_self_info()` | ロボット自身の情報 | 公開Web API（bot-info） |
| `get_user_info(user_id)` | ユーザー情報（任意のユーザーが取得可能） | 公開Web API（user/homepage） |
| `get_group_info(group_id)` | グループ情報 | 公開Web API（group-info） |
| `upload_file(*, type, name, ...)` | ファイルのアップロード（image/video/fileを自動判定） | Bot公開API |
| `get_file(file_id)` | ファイルの取得（file_id はURL） | — |
| `delete_message(message_id, *, chat_id, chat_type)` | メッセージの撤回 | Bot公開API（/bot/recall） |

> **注意:** `get_self_info` / `get_user_info` / `get_group_info` は**非公式な公開Web API**（chat-web-go.jwzhd.com）を介して実装されます。これらのAPIは認証不要ですが、公式ドキュメントではなく、プラットフォームの更新に伴い変更される可能性があります。失敗した場合は標準のエラーレスポンスを返します。

### 対応しない標準アクション

以下のような標準アクションは雲湖には対応するAPIがなく、呼び出した場合は `retcode=10002`（対応していない操作）を返します：
- `get_friend_list`（Bot公開APIの「ロボットユーザー一覧」はまだリリース予定）
- `get_group_list` / `get_group_member_info` / `get_group_member_list`
- `set_group_name` / `leave_group`

### プラットフォーム拡張アクション

`Api.call("yunhu.xxx", **params)` を使用して雲湖特有のアクションを呼び出します（パラメータはOB12スタイルの命名を使用し、アダプタが自動的に雲湖のフィールドに変換します）：

| 拡張アクション | 説明 | 等価Sendメソッド |
|---------|------|---------------|
| `yunhu.recall` | メッセージの撤回（msg_id, chat_id, chat_type） | `Send.To(...).Recall(msg_id)` |
| `yunhu.kick` | グループメンバーの削除（group_id, user_id） | `Send.To("group", g).Kick(uid)` |
| `yunhu.ban` | ユーザーのミュート（group_id, user_id, duration） | `Send.To("group", g).Ban(uid, duration)` |
| `yunhu.unban` | ユーザーのミュート解除（group_id, user_id） | `Send.To("group", g).Ban(uid, duration=0)` |
| `yunhu.tag.create/edit/delete/list` | グループタグのCRUD（group_id, ...） | `Send.To("group", g).CreateTag(...)` など |
| `yunhu.tag.relate` / `yunhu.tag.relate_cancel` | ユーザーにタグを追加/削除 | `Send.To("group", g).AddUserTag(...)` など |
| `yunhu.set_member_title` / `yunhu.unset_member_title` | **メンバーの肩書の別名**（タグ ≈ 肩書、内部でtag.relateにマッピング） | — |
| `yunhu.msg_type_limit` | グループのメッセージの種類制限（group_id, type） | `Send.To("group", g).SetMsgTypeLimit(...)` |
| `yunhu.get_messages` | 歴史メッセージの取得（chat_id, chat_type, message_id?, before?, after?） | `Send.To(...).GetMessages(...)` |
| `yunhu.bot_info` | 公開bot-infoの取得（bot_id） | — |
| `yunhu.user_homepage` | 公開ユーザーのホームの取得（user_id） | — |

```python
# プラットフォーム拡展示例
await yunhu.Api.call("yunhu.kick", group_id="123", user_id="456")
await yunhu.Api.call("yunhu.set_member_title", group_id="123", user_id="456", title="VIP")
result = await yunhu.Api.call("yunhu.get_messages", chat_id="123", chat_type="group", before=10)
```

> **タグと肩書**：雲湖の「タグ」の意味はOneBot12のグループメンバーの`title`に等しいです。`yunhu.set_member_title`は`yunhu.tag.relate`の元の意味の別名であり、内部で同一のエンドポイントにマッピングされます。グループメッセージイベントで送信者の役割は`senderUserLevel`から標準の`role`フィールドにマッピングされます（owner/admin/member）。

## 送信メソッドの戻り値

すべての送信メソッドはTaskオブジェクトを返し、awaitで送信結果を取得できます。返り値はErisPulseアダプタの標準化された返り値規格に従います：

```python
{
    "status": "ok",           // 実行ステータス
    "retcode": 0,             // 返り値コード
    "data": {...},            // レスポンスデータ
    "self": {...},            // 自身の情報（bot_idを含む）
    "message_id": "123456",   // メッセージID
    "message": "",            // エラーメッセージ
    "yunhu_raw": {...}        // 元のレスポンスデータ
}
```

## 特有のイベントタイプ

platform=="yunhu"を検証してから、このプラットフォームの特有の機能を使用する必要があります。

### 核心的な違い

1. 特有のイベントタイプ：
    - フォーム（フォームコマンドなど）：yunhu_form
    - 表情パック/ステッカーのメッセージセグメント：yunhu_expression
    - ボタンクリック：yunhu_button_click
    - A2UIボタンクリック：yunhu_a2ui_button
    - ロボットの設定：yunhu_bot_setting
    - ショートカットメニュー：yunhu_shortcut_menu
2. 標準フィールドの拡張（4.3.0+）：
    - メッセージイベントに標準の`role`フィールドが追加されました（雲湖の`senderUserLevel`から`owner`/`admin`/`member`にマッピング）
    - `user_avatar`フィールドが追加されました（送信者のアバターURL）
3. 拡張フィールド：
    - 特有のフィールドはすべて`yunhu_`で始まるプレフィックスが付いています
    - 元のデータは`yunhu_raw`フィールドに保存されています
    - プライベートチャットでは`self.user_id`はロボットのIDを示します

### 特殊フィールドの例

```python
# フォームコマンド
{
  "type": "message",
  "detail_type": "private",
  "yunhu_command": {
    "name": "フォームコマンド名",
    "id": "コマンドID",
    "form": {
      "フィールドID1": {
        "id": "フィールドID1",
        "type": "input/textarea/select/radio/checkbox/switch",
        "label": "フィールドラベル",
        "value": "フィールド値"
      }
    }
  }
}

# ボタンイベント
{
  "type": "notice",
  "detail_type": "yunhu_button_click",
  "user_id": "ボタンをクリックしたユーザーID",
  "user_nickname": "ユーザーのニックネーム",
  "message_id": "メッセージID",
  "yunhu_button": {
    "id": "ボタンID（空の場合あり）",
    "value": "ボタンの値"
  }
}

# A2UIボタンイベント
{
  "type": "notice",
  "detail_type": "yunhu_a2ui_button",
  "user_id": "操作したユーザーID",
  "user_nickname": "ユーザーのニックネーム",
  "message_id": "メッセージID",
  "yunhu_a2ui": {
    "recv_id": "受信者のID",
    "recv_type": "受信者のタイプ",
    "action_name": "操作名",
    "source_component_id": "ソースコンポーネントID",
    "form_context": {},
    "interaction_json": "インタラクションデータのJSON文字列"
  }
}

### ボタンクリックイベントの処理例

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_yunhu_notice(event):
    """雲湖の通知イベントを処理する

    一般的な on_notice() デコレータを使用して、すべての通知イベントを処理し、
    detail_type で異なるタイプの通知を区別する
    event.reply() は自動的に雲湖プラットフォームを介して返信する
    """
    # ボタンクリックイベントかどうかを確認
    if event.get("detail_type") == "yunhu_button_click":
        user_id = event.get_user_id()
        user_nickname = event.get_user_nickname()
        button_value = event.get("yunhu_button", {}).get("value", "")

        print(f"ユーザー {user_nickname}({user_id}) がボタンをクリックしました: {button_value}")

        # event.reply() を使用して返信（プラットフォームに応じて正しい送信方法を選択）
        if button_value == "confirm":
            await event.reply("確認ボタンをクリックしました！")
        elif button_value == "cancel":
            await event.reply("操作がキャンセルされました")
        else:
            await event.reply(f"選択を受け取りました: {button_value}")

    # ショートカットメニューイベントの処理
    elif event.get("detail_type") == "yunhu_shortcut_menu":
        menu_id = event.get("yunhu_menu", {}).get("id", "")
        await event.reply(f"ショートカットメニューが起動されました: {menu_id}")

    # ロボットの設定変更
    elif event.get("detail_type") == "yunhu_bot_setting":
        settings = event.get("yunhu_setting", {})
        await event.reply(f"設定が更新されました: {settings}")

    # A2UIボタンイベントの処理
    elif event.get("detail_type") == "yunhu_a2ui_button":
        a2ui = event.get("yunhu_a2ui", {})
        action_name = a2ui.get("action_name", "")
        form_context = a2ui.get("form_context", {})
        await event.reply(f"A2UI操作: {action_name}, フォームデータ: {form_context}")
```

### チェーン呼び出しを使用してボタン付きメッセージを送信

```python
from ErisPulse import sdk

yunhu = sdk.adapter.get("yunhu")

buttons = [
    [
        {"text": "確認", "actionType": 3, "value": "confirm"},
        {"text": "キャンセル", "actionType": 3, "value": "cancel"},
        {"text": "詳細を表示", "actionType": 1, "url": "http://example.com/detail"}
    ]
]

# グループにボタン付きメッセージを送信
await yunhu.Send.To("group", "123456").Buttons(buttons).Text("以下の操作を確認してください")

# ユーザーのプライベートチャットにボタン付きメッセージを送信
await yunhu.Send.To("user", "789").Buttons(buttons).Text("あなたの好みの設定を選択してください")
```

### A2UIメッセージの送信

```python
from ErisPulse import sdk

yunhu = sdk.adapter.get("yunhu")

# A2UIメッセージを送信
await yunhu.Send.To("user", user_id).A2UI("A2UIインタラクティブカードの内容")
```

# ロボットの設定
{
  "type": "notice",
  "detail_type": "yunhu_bot_setting",
  "group_id": "グループID（空の場合あり）",
  "user_nickname": "ユーザーのニックネーム",
  "yunhu_setting": {
    "設定項目ID": {
      "id": "設定項目ID",
      "type": "input/radio/checkbox/select/switch",
      "value": "設定値"
    }
  }
}

# ショートカットメニュー
{
  "type": "notice",
  "detail_type": "yunhu_shortcut_menu",
  "user_id": "メニューをトリガーしたユーザーID",
  "user_nickname": "ユーザーのニックネーム",
  "group_id": "グループID（プライベートチャットの場合）",
  "yunhu_menu": {
    "id": "メニューID",
    "type": "メニューのタイプ(整数)",
    "action": "メニューのアクション(整数)"
  }
}
```

## Event Mixin 拡張メソッド

アダプタは以下のプラットフォーム固有のメソッドを登録しています。`platform == "yunhu"` の場合にのみ利用可能です：

| メソッド | 戻り値の型 | 説明 |
|------|----------|------|
| `get_raw_event()` | `dict` | 雲湖の元のイベントデータを取得（`yunhu_raw`） |
| `get_sender_level()` | `str` | 送信者の雲湖の元のレベル（owner/administrator/member/unknown） |
| `get_sender_role()` | `str` | 送信者のOneBot12標準のrole（owner/admin/member） |
| `get_sender_title()` | `str` | 送信者の肩書（標準の `title` フィールドのアクセス用、予約） |
| `get_sender_avatar()` | `str` | 送信者のアバターURL |
| `get_command()` | `dict` | コマンドデータ（コマンドメッセージイベントのみ、`yunhu_command`） |
| `get_button_value()` | `str` | ボタンクリックイベントの value（`yunhu_button.value`） |
| `get_a2ui_action()` | `str` | A2UIボタンイベントの actionName |
| `get_a2ui_form_context()` | `dict` | A2UIボタンイベントのフォームコンテキスト |
| `get_menu_id()` | `str` | ショートカットメニューイベントのID（`yunhu_menu.id`） |
| `get_setting()` | `dict` | ロボットの設定イベントの設定データ（`yunhu_setting`） |
| `is_command_message()` | `bool` | コマンドメッセージかどうか |
| `is_button_click()` | `bool` | ボタンクリックイベントかどうか |
| `is_a2ui_button()` | `bool` | A2UIボタンイベントかどうか |

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_yunhu_notice(event):
    if event.get("platform") != "yunhu":
        return

    if event.is_button_click():
        value = event.get_button_value()
        await event.reply(f"ボタンをクリックしました: {value}")

    if event.get("detail_type") == "yunhu_shortcut_menu":
        menu_id = event.get_menu_id()
```

## 拡張フィールドの説明

- すべての特有のフィールドは `yunhu_` で始まるプレフィックスで識別され、標準のフィールドと混同されないようにします。
- 元のデータは `yunhu_raw` フィールドに保持され、雲湖プラットフォームの完全な元のデータにアクセスできます。
- `self.user_id` はロボットのIDを示します（設定の bot_id から取得）。
- フォームコマンドは `yunhu_command` フィールドを通じて構造化されたデータを提供します。
- ボタンクリックイベントは `yunhu_button` フィールドを通じてボタンに関する情報を提供します。
- A2UIボタンイベントは `yunhu_a2ui` フィールドを通じてA2UIインタラクションに関する情報を提供します。
- ロボットの設定変更は `yunhu_setting` フィールドを通じて設定項目のデータを提供します。
- ショートカットメニュー操作は `yunhu_menu` フィールドを通じてメニューに関する情報を提供します。
- 表情パック/ステッカーのメッセージセグメントは `yunhu_expression` メッセージセグメントを通じてステッカーのデータ（sticker_id、ステッカーのパックID、画像のサイズなど）を提供します。

### 表情パック/ステッカーのメッセージセグメント (yunhu_expression)

ユーザーが表情パックまたはステッカーを送信した場合、メッセージセグメントのタイプは `yunhu_expression` になります：

```json
{
  "type": "yunhu_expression",
  "data": {
    "sticker_id": "35154",
    "sticker_pack_id": "1670",
    "expression_id": "0",
    "image_name": "sticker/fabb9077f2ba302402ea871cab3686ad7a3fc52c.gif",
    "width": 500,
    "height": 500
  }
}
```

| フィールド | 型 | 説明 |
|------|------|------|
| `sticker_id` | string | ステッカーのユニークな識別子 |
| `sticker_pack_id` | string | ステッカーのパックID |
| `expression_id` | string | 表情のID |
| `image_name` | string | 表情画像のファイルパス |
| `width` | int | 画像の幅（オプション） |
| `height` | int | 画像の高さ（オプション） |

使用例:
```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event.get_platform() == "yunhu":
        for segment in event.get("message", []):
            if segment.get("type") == "yunhu_expression":
                data = segment["data"]
                print(f"表情パックを受け取りました: sticker_id={data['sticker_id']}, パックID={data['sticker_pack_id']}")
```

---

## マルチBot設定

### 設定の説明

雲湖アダプタは複数の雲湖ロボットアカウントを同時に設定および実行することをサポートしています。

```toml
# config.toml
[Yunhu_Adapter.accounts.bot1]
token = "your_bot1_token"  # ロボットのトークン（必須）
mode = "ws"  # 受信モード（オプション、デフォルトは"ws"、"ws"または"webhook"が選択可能）
webhook_path = "/webhook/bot1"  # Webhookのパス（オプション、デフォルトは"/webhook"、webhookモードのみ使用）
enabled = true  # 有効にするかどうか（オプション、デフォルトはtrue）

[Yunhu_Adapter.accounts.bot2]
token = "your_bot2_token"  # 2番目のロボットのトークン
webhook_path = "/webhook/bot2"  # 独自のwebhookパス
enabled = true
```

**設定項目の説明:**
- `token`: 雲湖プラットフォームが提供するAPIトークン（必須）
- `mode`: 受信モード（オプション、デフォルトは `"ws"`、`"ws"`、`"webhook"` が選択可能）
- `webhook_path`: 雲湖イベントを受信するHTTPパス（オプション、デフォルトは`"/webhook"`、webhookモードのみ使用）
- `enabled`: そのアカウントを有効にするかどうか（オプション、デフォルトはtrue）

**重要な注意:**
1. 雲湖プラットフォームのロボットIDは**実行時に自動検出**され、設定ファイルに指定する必要はありません。
2. webhookモードでは、各botには独自の`webhook_path`が必要で、それぞれのwebhookイベントを受信できるようにします。
3. 雲湖プラットフォームでwebhookを設定する際には、各botにそれぞれのURLを設定する必要があります。例えば:
   - Bot1: `https://your-domain.com/webhook/bot1`
   - Bot2: `https://your-domain.com/webhook/bot2`

### Send DSLを使用してBotを指定

`Using()`メソッドを使用して、どのbotを使ってメッセージを送信するかを指定できます。このメソッドは2種類のパラメータをサポートします:
- **アカウント名**: 設定ファイル中のbot名（例: `bot1`, `bot2`）
- **bot_id**: 設定ファイル中の `bot_id` 値

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# アカウント名を使用してメッセージを送信
await yunhu.Send.Using("bot1").To("user", "user123").Text("Hello from bot1!")

# bot_idを使用してメッセージを送信（自動的に該当するアカウントにマッチ）
await yunhu.Send.Using("30535459").To("group", "group456").Text("Hello from bot!")

# 指定しない場合は最初に有効なbotを使用
await yunhu.Send.To("user", "user123").Text("Hello from default bot!")
```

> **ヒント:** `bot_id`を使用する場合、システムは自動的に該当するアカウントを検索します。これはイベントの返信時に特に便利で、`event["self"]["user_id"]`を使用して同じアカウントで返信できます。

### イベント中のBot識別子

受信したイベントには、自動的に対応する`bot_id`情報が含まれます:

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "yunhu":
        # トリガーされたイベントのロボットIDを取得
        bot_id = event["self"]["user_id"]
        print(f"メッセージはBot: {bot_id} から来ました")
        
        # 同じbotでメッセージを返信
        yunhu = adapter.get("yunhu")
        await yunhu.Send.Using(bot_id).To(
            event["detail_type"],
            event["user_id"] if event["detail_type"] == "private" else event["group_id"]
        ).Text("返信メッセージ")
```

### ログ情報

アダプタは自動的に `bot_id` 情報を含むログを出力し、デバッグや追跡に便利です:

```
[INFO] [yunhu] [bot:30535459] ユーザー user123 からのプライベートメッセージを受信しました
[INFO] [yunhu] [bot:12345678] メッセージ送信成功、message_id: abc123
```

### 管理インターフェース

```python
# すべてのアカウント情報を取得
bots = yunhu.bots

# アカウントの有効化状態を確認
bot_status = {
    bot_name: bot_config.enabled
    for bot_name, bot_config in yunhu.bots.items()
}

# 動的にアカウントの有効化/無効化（アダプタの再起動が必要）
yunhu.bots["bot1"].enabled = False
```

### 旧配置の互換性

旧版の `[Yunhu_Adapter.bots.*]` 配置（`bot_id` フィールドを含む）は、`accounts` 形式に自動的に移行されます（`bot_id` は実行時に自動検出されるため、配置ファイル中の値は無視されます）。新しい形式への移行を推奨します。