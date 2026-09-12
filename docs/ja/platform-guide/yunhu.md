# 雲湖プラットフォームの機能ドキュメント

YunhuAdapter は、雲湖プロトコルに基づいて構築されたアダプタであり、すべての雲湖機能モジュールを統合し、一貫したイベント処理とメッセージ操作のインターフェースを提供します。

---

## ドキュメント情報

- 対応モジュールバージョン: 4.4.0
- メンテナー: ErisPulse

## 基本情報

- プラットフォーム概要：雲湖（Yunhu）はエンタープライズ向けリアルタイムメッセージングプラットフォームです。
- アダプタ名：YunhuAdapter
- 複数アカウント対応：bot_id で識別し、複数の雲湖ロボットアカウントを設定できます。
- チェーン修飾子対応：`.Reply()` などのチェーン修飾子メソッドをサポートしています。
- OneBot12互換：OneBot12形式のメッセージ送信をサポートしています。

## v5 フレームワーク更新（4.4.0）

このアダプタは v5 フレームワークへの対応を完了しました（段階的アップグレード、API 互換性を保持）：

- **公式サーバーサイド API 全集**（Api DSL 拡張メソッド）：メッセージ編集、一括送信、メッセージ一覧、ユーザー/グローバルダッシュボード、グループメンバーのミュート、グループメンバーの削除、グループメッセージタイプ制限、グループタグの CRUD、ユーザーへのタグ付与
- **標準 keyboard 段**（クロスプラットフォーム対応のインタラクティブコンポーネント）：{"type": "keyboard", "data": {"rows": [[{"label", "type": "callback|link", "data"}]]}} 段は自動的に Yunhu の buttons に変換されます。.Buttons(rows) / .Keyboard(rows) 修飾子は汎用構造を受け付けます（ネイティブ構造は後方互換性を保持）
- **インタラクティブコールバックの標準フィールド**：ボタンクリック/A2UI イベントには interaction_id / button_data という標準フィールドが含まれます
- **spawn_background によるタスクの所属**：WS 接続タスクは runtime.spawn_background を使用します
- **フレームワークのソフト依存性**：ErisPulse>=2.7.1 を実行時に検出し、警告を出力します。起動時にバージョンログを出力します

### プラットフォーム拡張アクション（call / Api メソッド）

```python
from ErisPulse import sdk
yunhu = sdk.adapter.get("yunhu")

# Api メソッド（公式サーバーサイド API）
await yunhu.Api.edit_message(msg_id, recv_id, "group", "text", {"text": "新内容"})
await yunhu.Api.batch_send(["userId1", "userId2"], "text", {"text": "公告"})
await yunhu.Api.get_message_list(group_id, "group", before=10)
await yunhu.Api.set_user_board(chat_id, "group", "看板内容", expire_time=3600)
await yunhu.Api.dismiss_global_board()
await yunhu.Api.gag_group_member(group_id, user_id, 600)      # 600秒間ミュート、0=解除
await yunhu.Api.remove_group_member(group_id, user_id)
await yunhu.Api.set_group_msg_type_limit(group_id, "text,image")
await yunhu.Api.create_group_tag(group_id, "VIP", color="#FF5733")
await yunhu.Api.add_user_tag(group_id, user_id, "VIP")

# ボタンクリックコールバック（標準フィールド）
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_button(event):
    if event.get("platform") == "yunhu" and event.get("button_data"):
        data = event["button_data"]     # クロスプラットフォームで統一された値の取得
        interaction_id = event["interaction_id"]
```

> 詳細な標準仕様は [クロスプラットフォーム対応インタラクティブコンポーネント標準](../../standards/standardization-guide.md) を参照してください。

## 支援されるメッセージ送信タイプ

すべての送信メソッドは、チェーン式の構文を用いて実装されています。たとえば：

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

await yunhu.Send.To("user", user_id).Text("Hello World!")
```

サポートされる送信タイプは以下の通りです：

- `.Text(text: str)`：純粋なテキストメッセージを送信します。
- `.Html(html: str)`：HTML形式のメッセージを送信します。
- `.Markdown(markdown: str)`：Markdown形式のメッセージを送信します。
- `.A2UI(text: str)`：A2UI形式のメッセージを送信します。
- `.Image(file: bytes, stream: bool = False, filename: str = None)`：画像メッセージを送信します。ストリームアップロードとカスタムファイル名をサポートします。
- `.Video(file: bytes, stream: bool = False, filename: str = None)`：動画メッセージを送信します。ストリームアップロードとカスタムファイル名をサポートします。
- `.File(file: bytes, stream: bool = False, filename: str = None)`：ファイルメッセージを送信します。ストリームアップロードとカスタムファイル名をサポートします。
- `.Batch(target_ids: List[str], message: str, content_type: str = "text", **kwargs)`：一括メッセージ送信を行います。
- `.Edit(msg_id: str, text: str, content_type: str = "text", buttons: List = None)`：既存のメッセージを編集します。
- `.Recall(msg_id: str)`：メッセージを撤回します。
- `.Board(content: str, content_type: str = "text")`：公告看板を送信します。`To()` によって作用域が推論されます（対象を指定した場合はローカル看板、未指定の場合はグローバル看板）。チェーン式修飾：`.Expire(duration)` 相対的な有効期限（秒）、`.ExpireAt(timestamp)` 絶対的な有効期限（秒単位のタイムスタンプ）、`.ForMember(member_id)` 群メンバー用看板；**内容が空の場合は自動的に看板の撤回になります**。従来の `Board("local", "公告")` という明示的なスコープの書き方も引き続きサポートされています。
- `.DismissBoard()`：公告看板を撤回します。作用域は `To()` によって推論され、`.ForMember(member_id)` もサポートされています；従来の `DismissBoard("local")` の書き方も引き続きサポートされています。
- `.Stream(content_type: str, content_generator: AsyncGenerator, **kwargs)`：ストリーム形式のメッセージを送信します。

### グループ管理メソッド

すべてのグループ管理メソッドは、チェーン式の構文でグループを指定する必要があります。たとえば：

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

await yunhu.Send.To("group", group_id).Kick(user_id)
```

- `.Kick(user_id: str)`：グループメンバーを削除します。ロボットには「グループメンバーの削除を許可」の権限が必要です。
- `.Ban(user_id: str, duration: int = 600)`：ユーザーをミュートします。`duration` はミュートの期間（秒）で、0は解除、-1は永久ミュートを意味します。ロボットには「ユーザーのミュートを許可」の権限が必要です。
- `.CreateTag(tag: str, color: str = None, desc: str = None, sort: int = None)`：グループタグを作成します。`color` は #RRGGBB 形式で、`sort` が小さいほどリストの上位に表示されます。ロボットには「タググループの管理を許可」の権限が必要です。
- `.EditTag(tag: str, new_tag: str = None, color: str = None, desc: str = None, sort: int = None)`：グループタグを編集します。各パラメータはオプションで、指定しない場合は変更されません。ロボットには「タググループの管理を許可」の権限が必要です。
- `.DeleteTag(tag: str)`：グループタグを削除します。ロボットには「タググループの管理を許可」の権限が必要です。
- `.GetTagList()`：グループタグリストを取得します。`list` 配列を含むレスポンスデータを返します。
- `.AddUserTag(user_id: str, tag: str)`：ユーザーにタグを追加します。ロボットには「タググループの管理を許可」の権限が必要です。
- `.RemoveUserTag(user_id: str, tag: str)`：ユーザーからタグを削除します。ロボットには「タググループの管理を許可」の権限が必要です。
- `.SetMsgTypeLimit(types: str)`：グループ内のメッセージタイプを制限します。`types` はメッセージタイプの名前で、複数の場合はカンマで区切ります（例：`"text,image,video"`）、空文字列は制限なしを意味します。ロボットには「グループ情報の変更を許可」の権限が必要です。

### メッセージ照会メソッド

指定された会話（ユーザー/グループ）の履歴メッセージリストを取得するには、チェーン式の構文で対象を指定する必要があります。たとえば：

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

result = await yunhu.Send.To("group", group_id).GetMessages(before=10)
```

- `.GetMessages(message_id: str = None, before: int = None, after: int = None)`：会話の履歴メッセージを取得します。`list` 配列と `total` の合計数を含むレスポンスデータを返します。
  - `message_id`：メッセージID（オプション）。指定しない場合は `before` を併用して最近のN件を返します。
  - `before`：指定したメッセージIDの前のN件を返します。
  - `after`：指定したメッセージIDの後のN件を返します。
  - > **注意：** `before` と `after` の少なくとも1つは0より大きく指定する必要があります。さもなければ、サーバーはメッセージを返しません。

Boardの作用域は `To()` によって自動的に推論されます：
- `To(target_type, target_id)` を指定した場合 → ローカル看板（指定されたユーザー/グループ）
- `To()` を指定しない場合 → グローバル看板

```python
# ローカル看板（60秒後に相対的に期限切れ）
await yunhu.Send.To("group", group_id).Expire(60).Board("公告", content_type="markdown")

# グループメンバー用看板（指定されたメンバーのみが表示可能）
await yunhu.Send.To("group", group_id).ForMember(user_id).Board("あなたにのみ表示")

# 絶対時間の期限切れ
await yunhu.Send.To("group", group_id).ExpireAt(1785208268).Board("指定された時間で期限切れ")

# グローバル看板
await yunhu.Send.Board("グローバル公告")

# ローカル看板のクリア（内容が空の場合は自動的に撤回）
await yunhu.Send.To("group", group_id).Board("")
```

### ボタンパラメータの説明

`buttons` パラメータは、ボタンのレイアウトと機能を示すネストされたリストです。各ボタンオブジェクトには以下のフィールドが含まれます：

| フィールド         | 型   | 必須 | 説明                                                                 |
|--------------|--------|----------|----------------------------------------------------------------------|
| `text`       | string | 是       | ボタンに表示されるテキスト                                                         |
| `actionType` | int    | 是       | アクションの種類：<br>`1`: URLに移動<br>`2`: コピー<br>`3`: 投稿イベントを送信            |
| `url`        | string | 否       | `actionType=1` の場合、移動先のURLを指定します                         |
| `value`      | string | 否       | `actionType=2` の場合、この値がクリップボードにコピーされます<br>`actionType=3` の場合、この値がサブスクライバに送信されます |

例：
```python
buttons = [
    [
        {"text": "コピー", "actionType": 2, "value": "xxxx"},
        {"text": "クリックして移動", "actionType": 1, "url": "http://www.baidu.com"},
        {"text": "イベントを報告", "actionType": 3, "value": "xxxxx"}
    ]
]
await yunhu.Send.To("user", user_id).Buttons(buttons).Text("ボタン付きのメッセージ")
```
> **注意：**
> - 「イベントを報告」ボタンをクリックした場合にのみ、プッシュ通知を受け取ります。「コピー」や「URLに移動」は、プッシュ通知を受け取ることはできません。

### チェーン式修飾メソッド（複数使用可能）

チェーン式修飾メソッドは `self` を返し、チェーンで呼び出すことができます。最終的な送信メソッドの前に呼び出す必要があります：

- `.Reply(message_id: str)`：指定したメッセージに返信します。
- `.At(user_id: str)`：指定したユーザーを@します。
- `.AtAll()`：全員を@します。
- `.Buttons(buttons: List)`：ボタンを追加します。

### チェーン式呼び出しの例

```python
# 基本的な送信
await yunhu.Send.To("user", user_id).Text("Hello")

# メッセージへの返信
await yunhu.Send.To("group", group_id).Reply(msg_id).Text("返信メッセージ")

# 返信 + ボタン
await yunhu.Send.To("group", group_id).Reply(msg_id).Buttons(buttons).Text("返信とボタン付きのメッセージ")
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

# メッセージタイプの制限
await yunhu.Send.To("group", group_id).SetMsgTypeLimit("text,image,video")

# メッセージタイプの制限を解除
await yunhu.Send.To("group", group_id).SetMsgTypeLimit("")
```

### メッセージ照会の例

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# グループの最新10件のメッセージを取得（合計10件を返す）
result = await yunhu.Send.To("group", group_id).GetMessages(before=10)

# グループ内の指定されたメッセージIDの前の10件を取得（合計11件を返す）
result = await yunhu.Send.To("group", group_id).GetMessages(message_id="msg_xxx", before=10)

# グループ内の指定されたメッセージIDの前後各10件を取得（合計21件を返す）
result = await yunhu.Send.To("group", group_id).GetMessages(message_id="msg_xxx", before=10, after=10)

# ユーザー会話の履歴メッセージを取得
result = await yunhu.Send.To("user", user_id).GetMessages(message_id="msg_xxx", before=10)
```

### OneBot12メッセージのサポート

アダプターはOneBot12形式のメッセージ送信をサポートしており、プラットフォーム間のメッセージ互換性を確保します：

- `.Raw_ob12(message: List[Dict], **kwargs)`：OneBot12形式のメッセージを送信します。

```python
# OneBot12形式のメッセージを送信
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await yunhu.Send.To("user", user_id).Raw_ob12(ob12_msg)

# チェーン式修飾と併用
ob12_msg = [{"type": "text", "data": {"text": "返信メッセージ"}}]
await yunhu.Send.To("group", group_id).Reply(msg_id).Raw_ob12(ob12_msg)
```

## 標準 API 動作（ApiDSL）

> [!NOTE]  
> この機能は ErisPulse **2.7.0+** および YunhuAdapter **4.3.0+** が必要です。

`Send` のチェーン送信に加え、アダプタは OneBot12 標準 API 動作と Yunhu プラットフォーム拡張動作を公開する `Api` 内部クラスを提供します。すべてのメソッドは標準レスポンス形式を返します。

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# 情報取得（公開 Web API を通じて、認証不要）
result = await yunhu.Api.get_self_info()              # ロボット自身の情報
result = await yunhu.Api.get_user_info("7058262")     # 任意のユーザー情報
result = await yunhu.Api.get_group_info("635409929")  # グループ情報

# ファイル操作
result = await yunhu.Api.upload_file(type="path", name="a.png", path="./a.png")
result = await yunhu.Api.get_file("https://chat-file.jwznb.com/xxx")

# メッセージの撤回（chat_id + chat_type の追加提供が必要）
await yunhu.Api.delete_message("msg_id", chat_id="123", chat_type="group")

# 複数アカウント：Bot アカウントを指定
info = await yunhu.Api.Using("bot1").get_self_info()
```

### 対応する標準動作

| メソッド | 説明 | データソース |
|--------|------|-------------|
| `get_self_info()` | ロボット自身の情報 | 公開 Web API（bot-info） |
| `get_user_info(user_id)` | ユーザー情報（任意のユーザーが取得可能） | 公開 Web API（user/homepage） |
| `get_group_info(group_id)` | グループ情報 | 公開 Web API（group-info） |
| `upload_file(*, type, name, ...)` | ファイルのアップロード（image/video/file を自動判定） | Bot 開放 API |
| `get_file(file_id)` | ファイル取得（file_id は URL） | — |
| `delete_message(message_id, *, chat_id, chat_type)` | メッセージの撤回 | Bot 開放 API（/bot/recall） |

> **注意**：`get_self_info` / `get_user_info` / `get_group_info` は**非公式公開 Web API**（chat-web-go.jwzhd.com）を用いて実装されており、これらのインターフェースは認証不要ですが公式ドキュメントがなく、プラットフォームの更新に伴い変更される可能性があります。失敗した場合は標準エラーレスポンスが返されます。

### 対応していない標準動作

以下の標準動作は Yunhu には対応 API がなく、呼び出すと `retcode=10002`（サポートされていない操作）が返されます：
- `get_friend_list`（Bot 開放 API の「ロボットユーザー一覧」は現在リリース予定）
- `get_group_list` / `get_group_member_info` / `get_group_member_list`
- `set_group_name` / `leave_group`

### プラットフォーム拡張動作

`Api.call("yunhu.xxx", **params)` を用いて Yunhu 特有の動作を呼び出します（パラメータは OB12 風命名を採用し、アダプタが自動的に Yunhu フィールドに変換します）：

| 拡張動作 | 説明 | 対応 Send メソッド |
|---------|------|------------------|
| `yunhu.recall` | メッセージの撤回（msg_id, chat_id, chat_type） | `Send.To(...).Recall(msg_id)` |
| `yunhu.kick` | グループメンバーの排除（group_id, user_id） | `Send.To("group", g).Kick(uid)` |
| `yunhu.ban` | 禁言（group_id, user_id, duration） | `Send.To("group", g).Ban(uid, duration)` |
| `yunhu.unban` | 禁言解除（group_id, user_id） | `Send.To("group", g).Ban(uid, duration=0)` |
| `yunhu.tag.create/edit/delete/list` | グループタグの CRUD（group_id, ...） | `Send.To("group", g).CreateTag(...)` など |
| `yunhu.tag.relate` / `yunhu.tag.relate_cancel` | ユーザーにタグを追加/削除 | `Send.To("group", g).AddUserTag(...)` など |
| `yunhu.set_member_title` / `yunhu.unset_member_title` | **メンバーの頭衔の別名**（タグ ≈ 頭衔、内部で tag.relate にマッピング） | — |
| `yunhu.msg_type_limit` | グループメッセージタイプ制限（group_id, type） | `Send.To("group", g).SetMsgTypeLimit(...)` |
| `yunhu.get_messages` | 歴史メッセージ取得（chat_id, chat_type, message_id?, before?, after?） | `Send.To(...).GetMessages(...)` |
| `yunhu.bot_info` | 公開 bot-info クエリ（bot_id） | — |
| `yunhu.user_homepage` | 公開ユーザーのホームページクエリ（user_id） | — |

```python
# プラットフォーム拡展示例
await yunhu.Api.call("yunhu.kick", group_id="123", user_id="456")
await yunhu.Api.call("yunhu.set_member_title", group_id="123", user_id="456", title="VIP")
result = await yunhu.Api.call("yunhu.get_messages", chat_id="123", chat_type="group", before=10)
```

> **タグと頭衔**：Yunhu の「タグ」は OneBot12 群メンバーの `title` と同等の意味を持ちます。`yunhu.set_member_title` は `yunhu.tag.relate` の原生的な別名であり、内部では同一エンドポイントにマッピングされます。群メッセージイベントで送信者の役割は `senderUserLevel` から標準 `role` フィールド（owner/admin/member）にマッピングされます。

## 送信メソッドの戻り値

すべての送信メソッドは Task オブジェクトを返し、直接 await を使用して送信結果を取得できます。返り値は ErisPulse アダプタの標準化された返り値規格に準拠しています：

```python
{
    "status": "ok",           // 実行ステータス
    "retcode": 0,             // 戻りコード
    "data": {...},            // 応答データ
    "self": {...},            // 自身の情報（bot_id を含む）
    "message_id": "123456",   // メッセージID
    "message": "",            // エラーメッセージ
    "yunhu_raw": {...}        // 元の応答データ
}
```

## 特有イベントタイプ

プラットフォームが "yunhu" であることを確認してから、このプラットフォームの機能を使用してください。

### 核心的な違い

1. 特有のイベントタイプ：
    - フォーム（フォームコマンドなど）：yunhu_form
    - 表情パック/ステッカーメッセージセグメント：yunhu_expression
    - ボタンクリック：yunhu_button_click
    - A2UIボタンクリック：yunhu_a2ui_button
    - ロボット設定：yunhu_bot_setting
    - ショートカットメニュー：yunhu_shortcut_menu
2. 標準フィールドの拡張（4.3.0以降）：
    - メッセージイベントに標準の `role` フィールドが追加されました（雲湖の `senderUserLevel` から `owner`/`admin`/`member` にマッピング）
    - `user_avatar` フィールドが追加されました（送信者のアバターURL）
3. 拡張フィールド：
    - すべての特有のフィールドは `yunhu_` で始まるプレフィックスで識別されます
    - 元のデータは `yunhu_raw` フィールドに保持されます
    - プライベートチャットでは `self.user_id` はロボットのIDを表します

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

# ボタンクリックイベント
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

# A2UIボタンクリックイベント
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
    """雲湖通知イベントを処理する

    すべての通知イベントを処理するために一般的な on_notice() デコレータを使用します。
    その後、detail_type で通知の種類を区別します。
    event.reply() は自動的に雲湖プラットフォームを介して返信されます。
    """

# ボタンクリックイベントかどうかを確認する
    if event.get("detail_type") == "yunhu_button_click":
        user_id = event.get_user_id()
        user_nickname = event.get_user_nickname()
        button_value = event.get("yunhu_button", {}).get("value", "")

        print(f"ユーザー {user_nickname}({user_id}) がボタンをクリックしました: {button_value}")

# 使用 event.reply() 自動返信（プラットフォームに応じて正しい送信方法が自動選択されます）
        if button_value == "confirm":
            await event.reply("あなたは確認ボタンをクリックしました！")
        elif button_value == "cancel":
            await event.reply("操作はキャンセルされました")
        else:
            await event.reply(f"選択を受け取りました: {button_value}")

# ショートカットメニューイベントの処理
    elif event.get("detail_type") == "yunhu_shortcut_menu":
        menu_id = event.get("yunhu_menu", {}).get("id", "")
        await event.reply(f"ショートカットメニューがトリガーされました: {menu_id}")

# ロボット設定の処理
    elif event.get("detail_type") == "yunhu_bot_setting":
        settings = event.get("yunhu_setting", {})
        await event.reply(f"設定が更新されました: {settings}")

# A2UIボタンイベントの処理
    elif event.get("detail_type") == "yunhu_a2ui_button":
        a2ui = event.get("yunhu_a2ui", {})
        action_name = a2ui.get("action_name", "")
        form_context = a2ui.get("form_context", {})
        await event.reply(f"A2UI操作: {action_name}, 表单数据: {form_context}")
```

### チェーン呼び出しを使用したボタン付きメッセージの送信

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
await yunhu.Send.To("user", "789").Buttons(buttons).Text("お好みの設定を選択してください。")  

### A2UI メッセージの送信  

```python  
from ErisPulse import sdk  

yunhu = sdk.adapter.get("yunhu")  
```

# A2UIメッセージの送信  
await yunhu.Send.To("user", user_id).A2UI("A2UIインタラクティブカードの内容")  

```

# ロボット設定  
{
  "type": "notice",
  "detail_type": "yunhu_bot_setting",
  "group_id": "グループID（空の可能性あり）",
  "user_nickname": "ユーザー名",
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
  "user_nickname": "ユーザー名",
  "group_id": "グループID（グループチャットの場合）",
  "yunhu_menu": {
    "id": "メニューID",
    "type": "メニューのタイプ(整数)",
    "action": "メニューのアクション(整数)"
  }
}
```

## Event Mixin 拡張メソッド

アダプターは、`platform == "yunhu"` の場合にのみ利用可能な以下のプラットフォーム固有メソッドを登録しています。

| メソッド | 戻り値の型 | 説明 |
|------|----------|------|
| `get_raw_event()` | `dict` | 雲湖の元のイベントデータを取得します（`yunhu_raw`） |
| `get_sender_level()` | `str` | 送信者の雲湖固有のレベル（owner/administrator/member/unknown） |
| `get_sender_role()` | `str` | 送信者の OneBot12 標準 role（owner/admin/member） |
| `get_sender_title()` | `str` | 送信者の肩書（標準 `title` フィールドのアクセサ、予約済み） |
| `get_sender_avatar()` | `str` | 送信者のアバター URL |
| `get_command()` | `dict` | コマンドデータ（コマンドメッセージイベントのみ、`yunhu_command`） |
| `get_button_value()` | `str` | ボタンクリックイベントの value（`yunhu_button.value`） |
| `get_a2ui_action()` | `str` | A2UI ボタンイベントの actionName |
| `get_a2ui_form_context()` | `dict` | A2UI ボタンイベントのフォームコンテキスト |
| `get_menu_id()` | `str` | ショートカットメニューイベントの ID（`yunhu_menu.id`） |
| `get_setting()` | `dict` | ロボット設定イベントの設定データ（`yunhu_setting`） |
| `is_command_message()` | `bool` | コマンドメッセージかどうか |
| `is_button_click()` | `bool` | ボタンクリックイベントかどうか |
| `is_a2ui_button()` | `bool` | A2UI ボタンイベントかどうか |

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_yunhu_notice(event):
    if event.get("platform") != "yunhu":
        return

    if event.is_button_click():
        value = event.get_button_value()
        await event.reply(f"あなたはボタン: {value} をクリックしました。")

    if event.get("detail_type") == "yunhu_shortcut_menu":
        menu_id = event.get_menu_id()
```

## 拡張フィールドの説明

- すべての独自フィールドは `yunhu_` という接頭辞で識別され、標準フィールドとの衝突を避ける
- 云湖プラットフォームの完全な元データにアクセスできるように、元データは `yunhu_raw` フィールドに保持される
- `self.user_id` は、設定の bot_id から取得されるロボットIDを表す
- フォームコマンドは `yunhu_command` フィールドで構造化されたデータとして提供される
- ボタンクリックイベントは `yunhu_button` フィールドでボタンに関する情報を提供する
- A2UIボタンイベントは `yunhu_a2ui` フィールドでA2UIのインタラクションに関する情報を提供する
- ロボットの設定変更は `yunhu_setting` フィールドで設定項目のデータを提供する
- ショートカットメニュー操作は `yunhu_menu` フィールドでメニューに関する情報を提供する
- 表情パック/ステッカーのメッセージは `yunhu_expression` メッセージセグメントでステッカーのデータ（sticker_id、ステッカーパックID、画像サイズなど）を提供する

### 表情パック/ステッカーのメッセージセグメント (yunhu_expression)

ユーザーが表情パックまたはステッカーを送信した場合、メッセージセグメントの型は `yunhu_expression` となる：

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
| `sticker_id` | string | ステッカーの唯一の識別子 |
| `sticker_pack_id` | string | ステッカーのパックID |
| `expression_id` | string | 表情のID |
| `image_name` | string | 表情の画像ファイルのパス |
| `width` | int | 画像の幅（オプション） |
| `height` | int | 画像の高さ（オプション） |

使用例：
```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event.get_platform() == "yunhu":
        for segment in event.get("message", []):
            if segment.get("type") == "yunhu_expression":
                data = segment["data"]
                print(f"表情パックを受信: sticker_id={data['sticker_id']}, パックID={data['sticker_pack_id']}")
```

## 多Bot設定

### 設定説明

Yunhuアダプタは、複数のYunhuロボットアカウントを同時に設定および実行することをサポートしています。

```toml
# config.toml
[Yunhu_Adapter.accounts.bot1]
token = "your_bot1_token"  # ロボットのトークン（必須）
mode = "ws"  # 受信モード（オプション、既定値は"ws"、"ws"または"webhook"のいずれか）
webhook_path = "/webhook/bot1"  # Webhookのパス（オプション、既定値は"/webhook"）
enabled = true  # 有効化するかどうか（オプション、既定値はtrue）

[Yunhu_Adapter.accounts.bot2]
token = "your_bot2_token"  # 2番目のロボットのトークン
webhook_path = "/webhook/bot2"  # 独自のwebhookパス
enabled = true
```

**設定項目の説明：**
- `token`：Yunhuプラットフォームから提供されるAPIトークン（必須）
- `mode`：受信モード（オプション、既定値は `"ws"`、"ws"または"webhook"のいずれか）
- `webhook_path`：Yunhuイベントを受信するHTTPパス（オプション、既定値は"/webhook"、webhookモードでのみ使用）
- `enabled`：アカウントを有効化するかどうか（オプション、既定値はtrue）

**重要な注意事項：**
1. YunhuプラットフォームのロボットIDは**実行時に自動的に検出**されます。設定ファイルに指定する必要はありません。
2. webhookモードでは、各botに独立した`webhook_path`が必要です。これにより、個々のwebhookイベントを受信できます。
3. Yunhuプラットフォームでwebhookを設定する際には、各botに対応するURLを設定してください。たとえば：
   - Bot1: `https://your-domain.com/webhook/bot1`
   - Bot2: `https://your-domain.com/webhook/bot2`

### Send DSLを使用してBotを指定

`Using()`メソッドを使用して、どのbotでメッセージを送信するかを指定できます。このメソッドは2種類のパラメータをサポートします：
- **アカウント名**：設定ファイル中のbot名（例：`bot1`, `bot2`）
- **bot_id**：設定ファイル中の`bot_id`値

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# アカウント名を使用してメッセージを送信
await yunhu.Send.Using("bot1").To("user", "user123").Text("Hello from bot1!")

# bot_idを使用してメッセージを送信（対応するアカウントを自動的に検索）
await yunhu.Send.Using("30535459").To("group", "group456").Text("Hello from bot!")

# 指定しない場合は、最初に有効化されたbotを使用
await yunhu.Send.To("user", "user123").Text("Hello from default bot!")
```

> **ヒント：** `bot_id`を使用する場合、システムは設定ファイル中の一致するアカウントを自動的に検索します。イベントの返信処理では、`event["self"]["user_id"]`を使用して、同じアカウントに返信するのが特に便利です。

### イベント内のBot識別子

受信したイベントには、対応する`bot_id`情報が自動的に含まれます：

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "yunhu":
        # イベントをトリガーしたロボットIDを取得
        bot_id = event["self"]["user_id"]
        print(f"メッセージはBot: {bot_id} から来ています")
        
        # 同じbotを使用してメッセージを返信
        yunhu = adapter.get("yunhu")
        await yunhu.Send.Using(bot_id).To(
            event["detail_type"],
            event["user_id"] if event["detail_type"] == "private" else event["group_id"]
        ).Text("返信メッセージ")
```

### ログ情報

アダプタは、ログに`bot_id`情報を自動的に含めるため、デバッグや追跡が容易になります：

```
[INFO] [yunhu] [bot:30535459] ユーザー user123からのプライベートメッセージを受信
[INFO] [yunhu] [bot:12345678] メッセージ送信成功、message_id: abc123
```

### 管理インターフェース

```python
# すべてのアカウント情報を取得
bots = yunhu.bots

# アカウントが有効かどうかを確認
bot_status = {
    bot_name: bot_config.enabled
    for bot_name, bot_config in yunhu.bots.items()
}

# 動的にアカウントを有効化/無効化（アダプタの再起動が必要）
yunhu.bots["bot1"].enabled = False
```

### 旧設定の互換性

旧バージョンの`[Yunhu_Adapter.bots.*]`設定（`bot_id`フィールドを含む）は、`accounts`形式に自動的に移行されます（`bot_id`は実行時に自動的に検出されるため、設定ファイル中の値は無視されます）。新しい形式への移行を推奨します。