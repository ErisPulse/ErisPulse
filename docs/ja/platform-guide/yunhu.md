# 雲湖プラットフォームの特徴ドキュメント

YunhuAdapterは、雲湖プロトコルに基づいて構築されたアダプターであり、雲湖のすべての機能モジュールを統合し、一貫したイベント処理とメッセージ操作のインターフェースを提供します。

---

## ドキュメント情報

- 対応モジュールバージョン: 4.3.0
- メンテナー: ErisPulse

## 基本情報

- プラットフォーム概要: 雲湖（Yunhu）は、企業向けのリアルタイムコミュニケーションプラットフォームです。
- アダプター名: YunhuAdapter
- 複数アカウント対応: bot_id で識別・設定可能な複数の雲湖ロボットアカウントをサポート
- 鏈式修飾対応: .Reply() などのチェーン修飾メソッドをサポート
- OneBot12互換: OneBot12形式のメッセージ送信をサポート

## 送信可能なメッセージタイプ

すべての送信メソッドはチェーン構文で実装されています。例:
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

await yunhu.Send.To("user", user_id).Text("Hello World!")
```

サポートされる送信タイプは以下の通りです:
- `.Text(text: str)`: 純粋なテキストメッセージを送信。
- `.Html(html: str)`: HTML形式のメッセージを送信。
- `.Markdown(markdown: str)`: Markdown形式のメッセージを送信。
- `.A2UI(text: str)`: A2UI形式のメッセージを送信。
- `.Image(file: bytes, stream: bool = False, filename: str = None)`: 画像メッセージを送信。ストリームアップロードとカスタムファイル名をサポート。
- `.Video(file: bytes, stream: bool = False, filename: str = None)`: 動画メッセージを送信。ストリームアップロードとカスタムファイル名をサポート。
- `.File(file: bytes, stream: bool = False, filename: str = None)`: ファイルメッセージを送信。ストリームアップロードとカスタムファイル名をサポート。
- `.Batch(target_ids: List[str], message: str, content_type: str = "text", **kwargs)`: バッチ送信。
- `.Edit(msg_id: str, text: str, content_type: str = "text", buttons: List = None)`: 既存メッセージを編集。
- `.Recall(msg_id: str)`: メッセージを撤回。
- `.Board(content: str, content_type: str = "text")`: 公告ボードを送信。`To()` で推論されるスコープ（指定対象=ローカルボード、未指定=グローバルボード）。チェーン修飾: `.Expire(duration)` 相対期限（秒）、`.ExpireAt(timestamp)` 絶対期限（秒単位のタイムスタンプ）、`.ForMember(member_id)` 群メンバー用ボード；**内容が空の場合は自動的にボードの撤回に変換**。旧式の `Board("local", "公告")` 明示的なスコープ指定も引き続きサポート。
- `.DismissBoard()`：公告ボードを撤回。`To()` で推論されるスコープをサポートし、`.ForMember(member_id)` もサポート。旧式の `DismissBoard("local")` 指定も引き続きサポート。
- `.Stream(content_type: str, content_generator: AsyncGenerator, **kwargs)`: ストリームメッセージを送信。

### 群管理メソッド

すべての群管理メソッドは、チェーン構文で群を指定する必要があります。例:
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

await yunhu.Send.To("group", group_id).Kick(user_id)
```

- `.Kick(user_id: str)`: 群メンバーを削除。ロボットは「群メンバーの削除を許可」権限が必要。
- `.Ban(user_id: str, duration: int = 600)`: ユーザーを禁止。`duration` は禁止時間（秒）、0は解除、-1は永久禁止。ロボットは「ユーザーの禁止を許可」権限が必要。
- `.CreateTag(tag: str, color: str = None, desc: str = None, sort: int = None)`: 群タグを作成。`color` は #RRGGBB 形式、`sort` は小さいほど上に表示。ロボットは「タググループの制御を許可」権限が必要。
- `.EditTag(tag: str, new_tag: str = None, color: str = None, desc: str = None, sort: int = None)`: 群タグを編集。各パラメータはオプションで、送信しない場合は変更しない。ロボットは「タググループの制御を許可」権限が必要。
- `.DeleteTag(tag: str)`: 群タグを削除。ロボットは「タググループの制御を許可」権限が必要。
- `.GetTagList()`: 群タグリストを取得。`list` 配列を含むレスポンスデータを返す。
- `.AddUserTag(user_id: str, tag: str)`: ユーザーにタグを追加。ロボットは「タググループの制御を許可」権限が必要。
- `.RemoveUserTag(user_id: str, tag: str)`: ユーザーからタグを削除。ロボットは「タググループの制御を許可」権限が必要。
- `.SetMsgTypeLimit(types: str)`: 群内のメッセージタイプを制限。`types` はメッセージタイプ名、複数はカンマ区切り（例: `"text,image,video"`）、空文字列は制限なし。ロボットは「群情報の変更を許可」権限が必要。

### メッセージ取得メソッド

指定された会話（ユーザー/群）の履歴メッセージリストを取得するには、チェーン構文で対象を指定する必要があります。例:
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

result = await yunhu.Send.To("group", group_id).GetMessages(before=10)
```

- `.GetMessages(message_id: str = None, before: int = None, after: int = None)`: 会話の履歴メッセージを取得。`list` 配列と `total` 総数を含むレスポンスデータを返す。
  - `message_id`: メッセージID（オプション）。指定しない場合、`before` と組み合わせて最近のN件を返す。
  - `before`: 指定メッセージIDの前のN件を返す。
  - `after`: 指定メッセージIDの後のN件を返す。
  - > **注意:** `before` と `after` は少なくとも1つ指定し、0より大きく、さもなければサーバーはメッセージを返しません。

Boardのスコープは `To()` で自動的に推論されます:
- `To(target_type, target_id)` を指定 → ローカルボード（対象ユーザー/群）
- `To()` を指定しない → グローバルボード

```python
# ローカルボード（60秒後に相対的に期限切れ）
await yunhu.Send.To("group", group_id).Expire(60).Board("公告", content_type="markdown")

# 群メンバー用ボード（特定メンバーのみ表示）
await yunhu.Send.To("group", group_id).ForMember(user_id).Board("あなた専用")

# 絶対時間での期限切れ
await yunhu.Send.To("group", group_id).ExpireAt(1785208268).Board("指定時間で期限切れ")

# グローバルボード
await yunhu.Send.Board("グローバル公告")

# ローカルボードをクリア（内容が空 → 自動的に撤回）
await yunhu.Send.To("group", group_id).Board("")
```

### ボタンパラメータの説明

`buttons` パラメータは、ボタンのレイアウトと機能を示すネストされたリストです。各ボタンオブジェクトには以下のフィールドが含まれます:

| フィールド         | 型   | 必須 | 説明                                                                 |
|--------------|--------|----------|----------------------------------------------------------------------|
| `text`       | string | 是       | ボタンのテキスト                                                         |
| `actionType` | int    | 是       | アクションタイプ：<br>`1`: URLに移動<br>`2`: コピー<br>`3`: クリック報告            |
| `url`        | string | 否       | `actionType=1` の場合、移動先のURLを使用                              |
| `value`      | string | 否       | `actionType=2` の場合、この値がクリップボードにコピーされる<br>`actionType=3` の場合、この値がサブスクライバーに送信される |

例:
```python
buttons = [
    [
        {"text": "コピー", "actionType": 2, "value": "xxxx"},
        {"text": "クリックで移動", "actionType": 1, "url": "http://www.baidu.com"},
        {"text": "イベントを報告", "actionType": 3, "value": "xxxxx"}
    ]
]
await yunhu.Send.To("user", user_id).Buttons(buttons).Text("ボタン付きメッセージ")
```
> **注意:**
> - 「イベントを報告」ボタンをクリックしたユーザーのみが通知を受け取ります。コピーとURL移動は通知を受け取れません。

### チェーン修飾メソッド（複数使用可能）

チェーン修飾メソッドは `self` を返し、チェーン呼び出しをサポートします。最終的な送信メソッドの前に呼び出す必要があります:

- `.Reply(message_id: str)`: 指定したメッセージに返信。
- `.At(user_id: str)`: 指定ユーザーを@する。
- `.AtAll()`: 全員を@する。
- `.Buttons(buttons: List)`：ボタンを追加する。

### チェーン呼び出しの例

```python
# 基本的な送信
await yunhu.Send.To("user", user_id).Text("Hello")

# メッセージに返信
await yunhu.Send.To("group", group_id).Reply(msg_id).Text("返信メッセージ")

# 返信 + ボタン
await yunhu.Send.To("group", group_id).Reply(msg_id).Buttons(buttons).Text("返信とボタン付きメッセージ")
```

### 群管理の例

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# 群メンバーを削除
await yunhu.Send.To("group", group_id).Kick(user_id)

# ユーザーを禁止（10分間）
await yunhu.Send.To("group", group_id).Ban(user_id, duration=600)

# 禁止を解除
await yunhu.Send.To("group", group_id).Ban(user_id, duration=0)

# 永久禁止
await yunhu.Send.To("group", group_id).Ban(user_id, duration=-1)

# 群タグを作成
await yunhu.Send.To("group", group_id).CreateTag("VIPユーザー", color="#FF5733", desc="VIP会員")

# 群タグを編集
await yunhu.Send.To("group", group_id).EditTag("VIPユーザー", new_tag="SVIPユーザー", color="#33C4FF")

# 群タグを削除
await yunhu.Send.To("group", group_id).DeleteTag("VIPユーザー")

# 群タグリストを取得
result = await yunhu.Send.To("group", group_id).GetTagList()

# ユーザーにタグを追加
await yunhu.Send.To("group", group_id).AddUserTag(user_id, "VIPユーザー")

# ユーザーからタグを削除
await yunhu.Send.To("group", group_id).RemoveUserTag(user_id, "VIPユーザー")

# メッセージタイプ制限を設定
await yunhu.Send.To("group", group_id).SetMsgTypeLimit("text,image,video")

# メッセージタイプ制限を解除
await yunhu.Send.To("group", group_id).SetMsgTypeLimit("")
```

### メッセージ取得の例

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# 群の最新10件のメッセージを取得（合計10件）
result = await yunhu.Send.To("group", group_id).GetMessages(before=10)

# 指定メッセージIDの前の10件を取得（合計11件）
result = await yunhu.Send.To("group", group_id).GetMessages(message_id="msg_xxx", before=10)

# 指定メッセージIDの前後各10件を取得（合計21件）
result = await yunhu.Send.To("group", group_id).GetMessages(message_id="msg_xxx", before=10, after=10)

# ユーザー会話の履歴メッセージを取得
result = await yunhu.Send.To("user", user_id).GetMessages(message_id="msg_xxx", before=10)
```

### OneBot12メッセージサポート

アダプターはOneBot12形式のメッセージ送信をサポートし、プラットフォーム間のメッセージ互換性を確保します:

- `.Raw_ob12(message: List[Dict], **kwargs)`: OneBot12形式のメッセージを送信。

```python
# OneBot12形式のメッセージを送信
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await yunhu.Send.To("user", user_id).Raw_ob12(ob12_msg)

# チェーン修飾と組み合わせる
ob12_msg = [{"type": "text", "data": {"text": "返信メッセージ"}}]
await yunhu.Send.To("group", group_id).Reply(msg_id).Raw_ob12(ob12_msg)
```

## 標準APIアクション（ApiDSL）

> [!NOTE]
> この機能はErisPulse **2.7.0+** およびYunhuAdapter **4.3.0+** が必要です。

`Send`チェーン送信に加えて、アダプターは`Api`内部クラスを提供し、OneBot12標準APIアクションと雲湖プラットフォーム拡張アクションを公開します。すべてのメソッドは標準レスポンス形式を返します。

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# 情報取得（公開Web APIを使用、認証不要）
result = await yunhu.Api.get_self_info()              # ロボット自身の情報
result = await yunhu.Api.get_user_info("7058262")     # 任意のユーザー情報
result = await yunhu.Api.get_group_info("635409929")  # グループ情報

# ファイル操作
result = await yunhu.Api.upload_file(type="path", name="a.png", path="./a.png")
result = await yunhu.Api.get_file("https://chat-file.jwznb.com/xxx")

# メッセージ撤回（追加でchat_idとchat_typeが必要）
await yunhu.Api.delete_message("msg_id", chat_id="123", chat_type="group")

# 複数アカウント: 指定されたBotアカウント
info = await yunhu.Api.Using("bot1").get_self_info()
```

### 支持される標準アクション

| メソッド | 説明 | データソース |
|------|------|---------|
| `get_self_info()` | ロボット自身の情報 | 公開Web API（bot-info） |
| `get_user_info(user_id)` | ユーザー情報（任意のユーザーも取得可能） | 公開Web API（user/homepage） |
| `get_group_info(group_id)` | グループ情報 | 公開Web API（group-info） |
| `upload_file(*, type, name, ...)` | ファイルをアップロード（image/video/fileを自動判定） | Bot公開API |
| `get_file(file_id)` | ファイルを取得（file_idはURL） | — |
| `delete_message(message_id, *, chat_id, chat_type)` | メッセージを撤回 | Bot公開API（/bot/recall） |

> **注意**: `get_self_info` / `get_user_info` / `get_group_info` は**非公式の公開Web API**（chat-web-go.jwzhd.com）で実現され、これらのインターフェースは認証不要ですが、公式ドキュメントではなく、プラットフォームの更新に伴い変更される可能性があります。失敗した場合は標準エラー応答を返します。

### 不支持の標準アクション

以下の標準アクションは雲湖には対応していないため、呼び出すと `retcode=10002`（サポートされていない操作）が返されます:
- `get_friend_list`（Bot公開APIの「ロボットユーザー一覧」は、現在リリース待ちの状態）
- `get_group_list` / `get_group_member_info` / `get_group_member_list`
- `set_group_name` / `leave_group`

### プラットフォーム拡張アクション

`Api.call("yunhu.xxx", **params)` を使用して雲湖特有のアクションを呼び出します（パラメータはOB12スタイルの命名を使用し、アダプターが自動的に雲湖のフィールドに翻訳します）:

| 拡張アクション | 説明 | 対応するSendメソッド |
|---------|------|---------------|
| `yunhu.recall` | メッセージを撤回（msg_id, chat_id, chat_type） | `Send.To(...).Recall(msg_id)` |
| `yunhu.kick` | 群メンバーを削除（group_id, user_id） | `Send.To("group", g).Kick(uid)` |
| `yunhu.ban` | ユーザーを禁止（group_id, user_id, duration） | `Send.To("group", g).Ban(uid, duration)` |
| `yunhu.unban` | 禁止を解除（group_id, user_id） | `Send.To("group", g).Ban(uid, duration=0)` |
| `yunhu.tag.create/edit/delete/list` | 群タグのCRUD（group_id, ...） | `Send.To("group", g).CreateTag(...)` など |
| `yunhu.tag.relate` / `yunhu.tag.relate_cancel` | ユーザーにタグを追加/削除 | `Send.To("group", g).AddUserTag(...)` など |
| `yunhu.set_member_title` / `yunhu.unset_member_title` | **メンバーの肩書きの別名**（タグ ≈ 肩書き、内部的にtag.relateにマッピング） | — |
| `yunhu.msg_type_limit` | 群のメッセージタイプ制限（group_id, type） | `Send.To("group", g).SetMsgTypeLimit(...)` |
| `yunhu.get_messages` | メッセージの履歴を取得（chat_id, chat_type, message_id?, before?, after?） | `Send.To(...).GetMessages(...)` |
| `yunhu.bot_info` | 公開bot-infoの照会（bot_id） | — |
| `yunhu.user_homepage` | 公開ユーザーのホームページ照会（user_id） | — |

```python
# プラットフォーム拡張の例
await yunhu.Api.call("yunhu.kick", group_id="123", user_id="456")
await yunhu.Api.call("yunhu.set_member_title", group_id="123", user_id="456", title="VIP")
result = await yunhu.Api.call("yunhu.get_messages", chat_id="123", chat_type="group", before=10)
```

> **タグと肩書き**: 雲湖の「タグ」はOneBot12の群メンバー `title` と同等です。`yunhu.set_member_title` は `yunhu.tag.relate` の標準的な別名であり、内部的には同じエンドポイントにマッピングされます。群メッセージイベントで送信者の役割は `senderUserLevel` から標準の `role` フィールドにマッピングされます（owner/admin/member）。

## 送信メソッドの返り値

すべての送信メソッドはTaskオブジェクトを返し、awaitで送信結果を取得できます。返り値はErisPulseアダプターの標準化された返り値規格に従います:

```python
{
    "status": "ok",           // 実行ステータス
    "retcode": 0,             // 返り値コード
    "data": {...},            // 応答データ
    "self": {...},            // 自身の情報（bot_idを含む）
    "message_id": "123456",   // メッセージID
    "message": "",            // エラーメッセージ
    "yunhu_raw": {...}        // 元の応答データ
}
```

## 特有のイベントタイプ

platform=="yunhu" であることを検証してから、このプラットフォームの特有の機能を使用する必要があります。

### 核心的な違い点

1. 特有のイベントタイプ:
    - フォーム（フォームコマンドなど）: yunhu_form
    - エモジコン/ステッカー: yunhu_expression
    - ボタンクリック: yunhu_button_click
    - A2UIボタンクリック: yunhu_a2ui_button
    - ロボットの設定: yunhu_bot_setting
    - ショートカットメニュー: yunhu_shortcut_menu
2. 標準フィールドの拡張（4.3.0+）:
    - メッセージイベントに標準 `role` フィールドが追加（雲湖 `senderUserLevel` から `owner`/`admin`/`member` にマッピング）
    - 新たな `user_avatar` フィールドが追加（送信者のアバターURL）
3. 拡張フィールド:
    - 特有のフィールドはすべて `yunhu_` で始まるプレフィックスが付けられます
    - 元のデータは `yunhu_raw` フィールドに保持されます
    - プライベートチャットでは `self.user_id` はロボットIDを示します

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
  "user_nickname": "ユーザー名",
  "message_id": "メッセージID",
  "yunhu_button": {
    "id": "ボタンID（空の場合あり）",
    "value": "ボタン値"
  }
}

# A2UIボタンクリックイベント
{
  "type": "notice",
  "detail_type": "yunhu_a2ui_button",
  "user_id": "操作したユーザーID",
  "user_nickname": "ユーザー名",
  "message_id": "メッセージID",
  "yunhu_a2ui": {
    "recv_id": "受信者ID",
    "recv_type": "受信者タイプ",
    "action_name": "操作名",
    "source_component_id": "元のコンポーネントID",
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

    一般的な on_notice() デコレータを使用してすべての通知イベントを処理し、
    detail_type で異なるタイプの通知を区別する
    event.reply() は自動的に雲湖プラットフォームを通じて返信する
    """
    # ボタンクリックイベントかどうかを確認
    if event.get("detail_type") == "yunhu_button_click":
        user_id = event.get_user_id()
        user_nickname = event.get_user_nickname()
        button_value = event.get("yunhu_button", {}).get("value", "")

        print(f"ユーザー {user_nickname}({user_id}) がボタンをクリックしました: {button_value}")

        # event.reply() を使用して自動返信（プラットフォームに応じて正しい送信方法を選択）
        if button_value == "confirm":
            await event.reply("確認ボタンをクリックしました！")
        elif button_value == "cancel":
            await event.reply("操作はキャンセルされました")
        else:
            await event.reply(f"選択を受け取りました: {button_value}")

    # ショートカットメニューイベントを処理
    elif event.get("detail_type") == "yunhu_shortcut_menu":
        menu_id = event.get("yunhu_menu", {}).get("id", "")
        await event.reply(f"ショートカットメニューがトリガーされました: {menu_id}")

    # ロボットの設定変更を処理
    elif event.get("detail_type") == "yunhu_bot_setting":
        settings = event.get("yunhu_setting", {})
        await event.reply(f"設定が更新されました: {settings}")

    # A2UIボタンイベントを処理
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
await yunhu.Send.To("user", "789").Buttons(buttons).Text("あなたの好み設定を選択してください")
```

### A2UIメッセージの送信

```python
from ErisPulse import sdk

yunhu = sdk.adapter.get("yunhu")

# A2UIメッセージを送信
await yunhu.Send.To("user", user_id).A2UI("A2UIインタラクションカードの内容")
```

# ロボットの設定
{
  "type": "notice",
  "detail_type": "yunhu_bot_setting",
  "group_id": "グループID（空の場合あり）",
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
    "type": "メニューのタイプ（整数）",
    "action": "メニューのアクション（整数）"
  }
}
```

## Event Mixin 拡張メソッド

アダプターは以下のプラットフォーム固有のメソッドを登録しており、`platform == "yunhu"` の場合にのみ利用可能です:

| メソッド | 戻り値型 | 説明 |
|------|----------|------|
| `get_raw_event()` | `dict` | 雲湖の元のイベントデータ（`yunhu_raw`）を取得 |
| `get_sender_level()` | `str` | 送信者の雲湖の元のレベル（owner/administrator/member/unknown） |
| `get_sender_role()` | `str` | 送信者のOneBot12標準のrole（owner/admin/member） |
| `get_sender_title()` | `str` | 送信者の肩書き（標準 `title` フィールドのアクセス用、予約） |
| `get_sender_avatar()` | `str` | 送信者のアバターURL |
| `get_command()` | `dict` | コマンドデータ（コマンドメッセージイベントのみ、`yunhu_command`） |
| `get_button_value()` | `str` | ボタンクリックイベントのvalue（`yunhu_button.value`） |
| `get_a2ui_action()` | `str` | A2UIボタンクリックイベントのactionName |
| `get_a2ui_form_context()` | `dict` | A2UIボタンクリックイベントのフォームコンテキスト |
| `get_menu_id()` | `str` | ショートカットメニューイベントのID（`yunhu_menu.id`） |
| `get_setting()` | `dict` | ロボットの設定イベントの設定データ（`yunhu_setting`） |
| `is_command_message()` | `bool` | コマンドメッセージかどうか |
| `is_button_click()` | `bool` | ボタンクリックイベントかどうか |
| `is_a2ui_button()` | `bool` | A2UIボタンクリックイベントかどうか |

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

- 特有のフィールドはすべて `yunhu_` で始まるプレフィックスが付けられ、標準のフィールドとの衝突を避ける
- 元のデータは `yunhu_raw` フィールドに保持され、雲湖プラットフォームの完全な元のデータにアクセスできる
- `self.user_id` はロボットIDを示す（設定の bot_id から取得）
- フォームコマンドは `yunhu_command` フィールドを通じて構造化されたデータを提供
- ボタンクリックイベントは `yunhu_button` フィールドを通じてボタンの情報を提供
- A2UIボタンクリックイベントは `yunhu_a2ui` フィールドを通じてA2UIインタラクションの情報を提供
- ロボットの設定変更は `yunhu_setting` フィールドを通じて設定項目のデータを提供
- ショートカットメニュー操作は `yunhu_menu` フィールドを通じてメニューの情報を提供
- エモジコン/ステッカーのメッセージセグメントは `yunhu_expression` でステッカーのデータを提供（sticker_id、ステッカーのパックID、画像のサイズなど）

### エモジコン/ステッカーのメッセージセグメント (yunhu_expression)

ユーザーがエモジコンまたはステッカーを送信した場合、メッセージセグメントのタイプは `yunhu_expression` になります:

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
| `sticker_id` | string | ステッカーの一意な識別子 |
| `sticker_pack_id` | string | ステッカーのパックID |
| `expression_id` | string | エモジコンID |
| `image_name` | string | エモジコンの画像ファイルのパス |
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
                print(f"ステッカーを受け取りました: sticker_id={data['sticker_id']}, パックID={data['sticker_pack_id']}")
```

---

## 複数Botの設定

### 設定の説明

雲湖アダプターは、複数の雲湖ロボットアカウントを同時に設定および実行することができます。

```toml
# config.toml
[Yunhu_Adapter.accounts.bot1]
token = "your_bot1_token"  # ロボットのtoken（必須）
mode = "ws"  # 受信モード（オプション、既定値は"ws"、"ws"または"webhook"が選択可能）
webhook_path = "/webhook/bot1"  # Webhookのパス（オプション、既定値は"/webhook"、webhookモードのみ使用）
enabled = true  # 有効かどうか（オプション、既定値はtrue）

[Yunhu_Adapter.accounts.bot2]
token = "your_bot2_token"  # 2番目のロボットのtoken
webhook_path = "/webhook/bot2"  # 独立したwebhookのパス
enabled = true
```

**設定項目の説明:**
- `token`: 雲湖プラットフォームから提供されたAPI token（必須）
- `mode`: 受信モード（オプション、既定値は"ws"、"ws"または"webhook"が選択可能）
- `webhook_path`: 雲湖イベントを受け取るHTTPパス（オプション、既定値は"/webhook"、webhookモードのみ使用）
- `enabled`: そのアカウントを有効にするかどうか（オプション、既定値はtrue）

**重要な注意点:**
1. 雲湖プラットフォームのロボットIDは**実行時に自動検出**され、設定ファイルに指定する必要はありません
2. webhookモードでは、各botには独立した`webhook_path`が必要で、独自のwebhookイベントを受け取ることができます
3. 雲湖プラットフォームでwebhookを設定する際には、各botに対応するURLを設定する必要があります。たとえば:
   - Bot1: `https://your-domain.com/webhook/bot1`
   - Bot2: `https://your-domain.com/webhook/bot2`

### Send DSLを使用してBotを指定

`Using()`メソッドを使用して、どのbotを使ってメッセージを送信するかを指定できます。このメソッドは2つのパラメータを受け付けます:
- **アカウント名**: 設定ファイルのbot名（例: `bot1`, `bot2`）
- **bot_id**: 設定ファイルの`bot_id`値

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

> **ヒント:** `bot_id`を使用する場合、システムは自動的に該当するアカウントにマッチします。これはイベントの返信処理時に特に便利で、`event["self"]["user_id"]`を使用して同じアカウントで返信できます。

### イベント内のBot識別子

受け取ったイベントには、自動的に対応する`bot_id`情報が含まれます:

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "yunhu":
        # トリガーしたイベントのロボットIDを取得
        bot_id = event["self"]["user_id"]
        print(f"メッセージはBot: {bot_id} から来ました")
        
        # 同じbotで返信メッセージを送信
        yunhu = adapter.get("yunhu")
        await yunhu.Send.Using(bot_id).To(
            event["detail_type"],
            event["user_id"] if event["detail_type"] == "private" else event["group_id"]
        ).Text("返信メッセージ")
```

### ログ情報

アダプターは自動的に`bot_id`情報をログに含め、デバッグやトラッキングに便利です:

```
[INFO] [yunhu] [bot:30535459] ユーザー user123 からのプライベートチャットメッセージを受け取りました
[INFO] [yunhu] [bot:12345678] メッセージの送信に成功しました、message_id: abc123
```

### 管理インターフェース

```python
# すべてのアカウント情報を取得
bots = yunhu.bots

# アカウントの有効状態をチェック
bot_status = {
    bot_name: bot_config.enabled
    for bot_name, bot_config in yunhu.bots.items()
}

# 動的にアカウントの有効/無効を切り替え（アダプターの再起動が必要）
yunhu.bots["bot1"].enabled = False
```

### 旧配置の互換性

旧バージョンの `[Yunhu_Adapter.bots.*]` 配置（bot_idフィールド付き）は、`accounts`形式に自動的に移行されます（bot_idは実行時に自動検出され、配置の値は無視されます）。新しい形式への移行を推奨します。