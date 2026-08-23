# 雲湖プラットフォームの特徴ドキュメント

YunhuAdapter は、雲湖プロトコルに基づいて構築されたアダプタであり、すべての雲湖機能モジュールを統合し、統一されたイベント処理およびメッセージ操作インターフェースを提供します。

---

[**English**](docs/en/quick-start.md) | [**日本語**](docs/ja/quick-start.md) | [**한국어**](docs/ko/quick-start.md) | [**简体中文**](docs/ja/quick-start.md)

## ドキュメント情報

- 対応モジュールバージョン: 4.3.0
- 維持管理者: ErisPulse

7. **重要: パスの置換ルール**
   - ドキュメントのリンク内の `docs/ja/` を `docs/ja/` に置換する
   - 例: `docs/ja/quick-start.md` は `docs/ja/quick-start.md` に変更する
   - 非現在言語版ファイルを指すリンク（例: `README.xx.md` 形式のリンク）は、変更しないで元のままにする
   - これにより、リンクが正しい言語のドキュメント版を指すようになる

## 基本情報

- プラットフォーム紹介：雲湖（Yunhu）はエンタープライズ向けのリアルタイムメッセージングプラットフォームです。
- アダプタ名：YunhuAdapter
- マルチアカウントサポート：bot_id で識別し、複数の雲湖ロボットアカウントを設定することができます。
- チェーン修飾サポート：`.Reply()` などのチェーン修飾メソッドをサポートしています。
- OneBot12互換：OneBot12形式のメッセージを送信することができます。

[**English**](docs/en/quick-start.md) | [**日本語**](docs/ja/quick-start.md) | [**简体中文**](docs/ja/quick-start.md) | [**繁體中文**](docs/zh-TW/quick-start.md) | [**한국어**](docs/ko/quick-start.md)

## 支持するメッセージ送信タイプ

すべての送信メソッドは、チェーン式の構文で実装されています。たとえば：

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
- `.Batch(target_ids: List[str], message: str, content_type: str = "text", **kwargs)`：一括送信メッセージ。
- `.Edit(msg_id: str, text: str, content_type: str = "text", buttons: List = None)`：既存メッセージを編集します。
- `.Recall(msg_id: str)`：メッセージを撤回します。
- `.Board(content: str, content_type: str = "text")`：公告看板を送信します。スコープは `To()` から推論されます（対象を指定する場合はローカル看板、未指定の場合はグローバル看板）。チェーン修飾子：`.Expire(duration)` 相対的な期限切れ（秒）、`.ExpireAt(timestamp)` 絶対的な期限切れ（秒単位のタイムスタンプ）、`.ForMember(member_id)` 群メンバー看板；**内容が空の場合、自動的に看板の撤回になります**。旧式の `Board("local", "公告")` による明示的なスコープ指定も引き続きサポートされます。
- `.DismissBoard()`：公告看板を撤回します。スコープは `To()` から推論され、`.ForMember(member_id)` もサポートされます；旧式の `DismissBoard("local")` の書き方も引き続きサポートされます。
- `.Stream(content_type: str, content_generator: AsyncGenerator, **kwargs)`：ストリーム形式のメッセージを送信します。

### グループ管理メソッド

すべてのグループ管理メソッドは、チェーン式の構文でグループを指定する必要があります。たとえば：

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

await yunhu.Send.To("group", group_id).Kick(user_id)
```

- `.Kick(user_id: str)`：グループメンバーを削除します。ロボットには「グループメンバーの削除を許可」の権限が必要です。
- `.Ban(user_id: str, duration: int = 600)`：ユーザーの発言禁止。`duration`は発言禁止の期間（秒）で、0は発言禁止解除、-1は永久発言禁止です。ロボットには「ユーザーの発言禁止を許可」の権限が必要です。
- `.CreateTag(tag: str, color: str = None, desc: str = None, sort: int = None)`：グループタグを作成します。`color`の形式は#RRGGBBで、`sort`は小さいほど上に表示されます。ロボットには「タググループの制御を許可」の権限が必要です。
- `.EditTag(tag: str, new_tag: str = None, color: str = None, desc: str = None, sort: int = None)`：グループタグを編集します。各パラメータはオプションで、指定しない場合は変更されません。ロボットには「タググループの制御を許可」の権限が必要です。
- `.DeleteTag(tag: str)`：グループタグを削除します。ロボットには「タググループの制御を許可」の権限が必要です。
- `.GetTagList()`：グループタグリストを取得します。`list`配列を含むレスポンスデータを返します。
- `.AddUserTag(user_id: str, tag: str)`：ユーザーにタグを追加します。ロボットには「タググループの制御を許可」の権限が必要です。
- `.RemoveUserTag(user_id: str, tag: str)`：ユーザーからタグを削除します。ロボットには「タググループの制御を許可」の権限が必要です。
- `.SetMsgTypeLimit(types: str)`：グループ内のメッセージタイプを制限します。`types`はメッセージタイプ名で、複数指定する場合はカンマで区切ります（例："text,image,video"）。空文字列は制限なしを意味します。ロボットには「グループ情報の変更を許可」の権限が必要です。

### メッセージ取得メソッド

指定された会話（ユーザー/グループ）の履歴メッセージリストを取得するには、チェーン式の構文で対象を指定する必要があります。たとえば：

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

result = await yunhu.Send.To("group", group_id).GetMessages(before=10)
```

- `.GetMessages(message_id: str = None, before: int = None, after: int = None)`：会話の履歴メッセージを取得します。`list`配列と`total`総数を含むレスポンスデータを返します。
  - `message_id`：メッセージID（オプション）。指定しない場合、`before`と組み合わせて最近のN件のメッセージを返します。
  - `before`：指定したメッセージIDの前N件を返します。
  - `after`：指定したメッセージIDの後N件を返します。
  - > **注意：** `before` と `after` の少なくとも1つは0より大きく指定する必要があります。それ以外の場合はサーバーはメッセージを返しません。

Boardのスコープは `To()` によって自動的に推論されます：
- `To(target_type, target_id)` を指定 → ローカル看板（指定されたユーザー/グループ）
- `To()` を指定しない → グローバル看板

```python
# ローカル看板（60秒後に相対的に期限切れ）
await yunhu.Send.To("group", group_id).Expire(60).Board("公告", content_type="markdown")

# 群メンバー看板（特定メンバーのみ表示）
await yunhu.Send.To("group", group_id).ForMember(user_id).Board("あなたにのみ表示")

# 絶対時間の期限切れ
await yunhu.Send.To("group", group_id).ExpireAt(1785208268).Board("指定時間で期限切れ")

# グローバル看板
await yunhu.Send.Board("グローバル公告")

# ローカル看板をクリア（内容が空 → 自動的に看板を撤回）
await yunhu.Send.To("group", group_id).Board("")
```

### ボタンパラメータの説明

`buttons` パラメータは、ボタンのレイアウトと機能を表すネストされたリストです。各ボタンオブジェクトには以下のフィールドが含まれます：

| フィールド         | タイプ   | 必須 | 説明                                                                 |
|--------------|--------|----------|----------------------------------------------------------------------|
| `text`       | string | はい       | ボタン上の文字                                                         |
| `actionType` | int    | はい       | 動作タイプ：<br>`1`: URLにジャンプ<br>`2`: コピー<br>`3`: 投稿イベントを送信            |
| `url`        | string | いいえ       | `actionType=1` の場合、ジャンプ先のURLを示します                         |
| `value`      | string | いいえ       | `actionType=2` の場合、この値がクリップボードにコピーされます<br>`actionType=3` の場合、この値がサブスクライバーに送信されます |

例：
```python
buttons = [
    [
        {"text": "コピー", "actionType": 2, "value": "xxxx"},
        {"text": "クリックしてジャンプ", "actionType": 1, "url": "http://www.baidu.com"},
        {"text": "イベントを報告", "actionType": 3, "value": "xxxxx"}
    ]
]
await yunhu.Send.To("user", user_id).Buttons(buttons).Text("ボタン付きのメッセージ")
```
> **注意：**
> - ユーザーが**イベント報告ボタン**をクリックした場合にのみ通知が送信されます。**コピー**や**URLジャンプ**は通知を受け取ることはできません。

### チェーン修飾メソッド（組み合わせて使用可能）

チェーン修飾メソッドは `self` を返し、チェーン呼び出しをサポートします。最終的な送信メソッドの前に呼び出す必要があります：

- `.Reply(message_id: str)`：指定されたメッセージに返信します。
- `.At(user_id: str)`：指定されたユーザーを@します。
- `.AtAll()`：全員を@します。
- `.Buttons(buttons: List)`：ボタンを追加します。

### チェーン呼び出しの例

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

# ユーザーの発言禁止（10分間）
await yunhu.Send.To("group", group_id).Ban(user_id, duration=600)

# 発言禁止の解除
await yunhu.Send.To("group", group_id).Ban(user_id, duration=0)

# 永久発言禁止
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

# メッセージタイプの制限を設定
await yunhu.Send.To("group", group_id).SetMsgTypeLimit("text,image,video")

# メッセージタイプの制限を解除
await yunhu.Send.To("group", group_id).SetMsgTypeLimit("")
```

### メッセージ取得の例

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# グループの最新10件のメッセージを取得（合計10件）
result = await yunhu.Send.To("group", group_id).GetMessages(before=10)

# グループ内の指定されたメッセージIDの前10件を取得（合計11件）
result = await yunhu.Send.To("group", group_id).GetMessages(message_id="msg_xxx", before=10)

# グループ内の指定されたメッセージIDの前後各10件を取得（合計21件）
result = await yunhu.Send.To("group", group_id).GetMessages(message_id="msg_xxx", before=10, after=10)

# ユーザー会話の履歴メッセージを取得
result = await yunhu.Send.To("user", user_id).GetMessages(message_id="msg_xxx", before=10)
```

### OneBot12メッセージのサポート

アダプターはOneBot12形式のメッセージの送信をサポートしており、プラットフォーム間のメッセージ互換性を確保します：

- `.Raw_ob12(message: List[Dict], **kwargs)`：OneBot12形式のメッセージを送信します。

```python
# OneBot12形式のメッセージを送信
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await yunhu.Send.To("user", user_id).Raw_ob12(ob12_msg)

# チェーン修飾子と組み合わせて使用
ob12_msg = [{"type": "text", "data": {"text": "返信メッセージ"}}]
await yunhu.Send.To("group", group_id).Reply(msg_id).Raw_ob12(ob12_msg)

## 標準 API 動作（ApiDSL）

> [!NOTE]
> この機能は ErisPulse **2.7.0+** および YunhuAdapter **4.3.0+** が必要です。

`Send` のチェーン送信に加えて、アダプターは OneBot12 標準 API 動作と Yunhu プラットフォーム拡張動作を公開する `Api` 内部クラスを提供します。すべてのメソッドは標準的なレスポンス形式を返します。

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# 情報照会（公開 Web API を通じて、認証不要）
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

### 標準動作のサポート状況

| メソッド | 説明 | データソース |
|------|------|---------|
| `get_self_info()` | ロボット自身の情報 | 公開 Web API（bot-info） |
| `get_user_info(user_id)` | ユーザー情報（任意のユーザーが照会可能） | 公開 Web API（user/homepage） |
| `get_group_info(group_id)` | グループ情報 | 公開 Web API（group-info） |
| `upload_file(*, type, name, ...)` | ファイルのアップロード（image/video/file を自動判定） | Bot 開放 API |
| `get_file(file_id)` | ファイルの取得（file_id は URL） | — |
| `delete_message(message_id, *, chat_id, chat_type)` | メッセージの撤回 | Bot 開放 API（/bot/recall） |

> **注意**：`get_self_info` / `get_user_info` / `get_group_info` は**非公式公開 Web API**（chat-web-go.jwzhd.com）を通じて実装されています。これらのインターフェースは認証を必要としませんが、公式ドキュメントではなく、プラットフォームの更新に伴い変更される可能性があります。失敗した場合は標準的なエラーレスポンスが返されます。

### 標準動作のサポート外

以下の標準動作は Yunhu には対応する API がなく、呼び出した場合 `retcode=10002`（サポートされていない操作）が返されます：
- `get_friend_list`（Bot 開放 API の「ロボットユーザー一覧」は現在リリース待ち）
- `get_group_list` / `get_group_member_info` / `get_group_member_list`
- `set_group_name` / `leave_group`

### プラットフォーム拡張動作

`Api.call("yunhu.xxx", **params)` を使用して Yunhu 特有の動作を呼び出します（パラメータは OB12 風の命名を使用し、アダプターが自動的に Yunhu フィールドに変換します）：

| 拡張動作 | 説明 | 等価 Send 方法 |
|---------|------|---------------|
| `yunhu.recall` | メッセージの撤回（msg_id, chat_id, chat_type） | `Send.To(...).Recall(msg_id)` |
| `yunhu.kick` | グループメンバーの排除（group_id, user_id） | `Send.To("group", g).Kick(uid)` |
| `yunhu.ban` | 静音（group_id, user_id, duration） | `Send.To("group", g).Ban(uid, duration)` |
| `yunhu.unban` | 静音解除（group_id, user_id） | `Send.To("group", g).Ban(uid, duration=0)` |
| `yunhu.tag.create/edit/delete/list` | グループタグの CRUD（group_id, ...） | `Send.To("group", g).CreateTag(...)` など |
| `yunhu.tag.relate` / `yunhu.tag.relate_cancel` | ユーザーにタグを追加/削除 | `Send.To("group", g).AddUserTag(...)` など |
| `yunhu.set_member_title` / `yunhu.unset_member_title` | **メンバーの頭銜の別名**（タグ＝頭銜、内部的に tag.relate にマッピング） | — |
| `yunhu.msg_type_limit` | グループメッセージの種類制限（group_id, type） | `Send.To("group", g).SetMsgTypeLimit(...)` |
| `yunhu.get_messages` | 歴史メッセージの取得（chat_id, chat_type, message_id?, before?, after?） | `Send.To(...).GetMessages(...)` |
| `yunhu.bot_info` | 公開 bot-info 照会（bot_id） | — |
| `yunhu.user_homepage` | 公開ユーザーのホームページ照会（user_id） | — |

```python
# プラットフォーム拡展示例
await yunhu.Api.call("yunhu.kick", group_id="123", user_id="456")
await yunhu.Api.call("yunhu.set_member_title", group_id="123", user_id="456", title="VIP")
result = await yunhu.Api.call("yunhu.get_messages", chat_id="123", chat_type="group", before=10)
```

> **タグと頭銜**：Yunhu の「タグ」の意味は OneBot12 グループメンバーの `title` と等価です。`yunhu.set_member_title` は `yunhu.tag.relate` の本質的な別名であり、内部的には同じエンドポイントにマッピングされます。グループメッセージイベントにおける送信者の役割は `senderUserLevel` から標準の `role` フィールド（owner/admin/member）にマッピングされます。

## 送信メソッドの戻り値

すべての送信メソッドは Task オブジェクトを返し、これに直接 await を使用して送信結果を取得できます。返り値は ErisPulse アダプターの標準化された返り値規格に従います：

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

## 特有イベントタイプ

このプラットフォームの機能を使用するには、`platform=="yunhu"` の検証が必要です。

### 核心的な差異点

1. 特有イベントタイプ：
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
    - すべての特有フィールドは `yunhu_` で始まるプレフィックスで識別されます
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
    "id": "ボタンID（空の可能性あり）",
    "value": "ボタン値"
  }
}

# A2UIボタンクリックイベント
{
  "type": "notice",
  "detail_type": "yunhu_a2ui_button",
  "user_id": "操作ユーザーID",
  "user_nickname": "ユーザーのニックネーム",
  "message_id": "メッセージID",
  "yunhu_a2ui": {
    "recv_id": "受信者ID",
    "recv_type": "受信者タイプ",
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

    すべての通知イベントを処理するために一般的な on_notice() デコレーターを使用し、
    detail_type で通知の種類を区別します。
    event.reply() は自動的に雲湖プラットフォームを通じて返信されます。
    """

# ボタンクリックイベントかどうかをチェックする  
    if event.get("detail_type") == "yunhu_button_click":  
        user_id = event.get_user_id()  
        user_nickname = event.get_user_nickname()  
        button_value = event.get("yunhu_button", {}).get("value", "")  

        print(f"ユーザー {user_nickname}({user_id}) がボタンをクリックしました: {button_value}")

# 使用 event.reply() 自動返信（プラットフォームに応じて正しい送信方法が自動的に選択されます）  
        if button_value == "confirm":
            await event.reply("あなたは確認ボタンをクリックしました！")
        elif button_value == "cancel":
            await event.reply("操作はキャンセルされました")
        else:
            await event.reply(f"あなたの選択を受け取りました: {button_value}")

# ショートカットメニューイベントの処理
    elif event.get("detail_type") == "yunhu_shortcut_menu":
        menu_id = event.get("yunhu_menu", {}).get("id", "")
        await event.reply(f"ショートカットメニューがトリガーされました: {menu_id}")

[**English**](docs/en/quick-start.md) | [**日本語**](docs/ja/quick-start.md)

# ロボット設定の変更を処理

    elif event.get("detail_type") == "yunhu_bot_setting":
        settings = event.get("yunhu_setting", {})
        await event.reply(f"設定が更新されました: {settings}")

# A2UIボタンイベントの処理
    elif event.get("detail_type") == "yunhu_a2ui_button":
        a2ui = event.get("yunhu_a2ui", {})
        action_name = a2ui.get("action_name", "")
        form_context = a2ui.get("form_context", {})
        await event.reply(f"A2UI操作: {action_name}, 表示データ: {form_context}")
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

# 送信ボタン付きメッセージをグループに送信  
await yunhu.Send.To("group", "123456").Buttons(buttons).Text("以下の操作を確認してください")

# ユーザーのプライベートチャットにボタン付きメッセージを送信  
await yunhu.Send.To("user", "789").Buttons(buttons).Text("お好みの設定を選択してください")

```markdown
### A2UI メッセージの送信

```python
from ErisPulse import sdk

yunhu = sdk.adapter.get("yunhu")
```

[**English**](docs/en/quick-start.md) | [**日本語**](docs/ja/quick-start.md) | [**中文**](docs/ja/quick-start.md)

# A2UIメッセージの送信
await yunhu.Send.To("user", user_id).A2UI("A2UIインタラクティブカードの内容")

```
# ロボット設定
{
  "type": "notice",
  "detail_type": "yunhu_bot_setting",
  "group_id": "グループID（空である可能性あり）",
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
  "group_id": "グループID（グループチャットの場合）",
  "yunhu_menu": {
    "id": "メニューID",
    "type": "メニューのタイプ(整数)",
    "action": "メニューのアクション(整数)"
  }
}

## Event Mixin 拡張メソッド

アダプターは以下のプラットフォーム固有メソッドを登録しており、`platform == "yunhu"` の場合にのみ利用可能です：

| メソッド | 戻り値の型 | 説明 |
|------|----------|------|
| `get_raw_event()` | `dict` | 雲湖の元のイベントデータを取得します（`yunhu_raw`） |
| `get_sender_level()` | `str` | 送信者の雲湖の元のレベル（owner/administrator/member/unknown） |
| `get_sender_role()` | `str` | 送信者の OneBot12 標準 role（owner/admin/member） |
| `get_sender_title()` | `str` | 送信者の肩書き（標準 `title` フィールドのアクセサ、予約済み） |
| `get_sender_avatar()` | `str` | 送信者のアイコン URL |
| `get_command()` | `dict` | コマンドデータ（コマンドメッセージイベントのみ、`yunhu_command`） |
| `get_button_value()` | `str` | ボタンクリックイベントの value（`yunhu_button.value`） |
| `get_a2ui_action()` | `str` | A2UI ボタンイベントの actionName |
| `get_a2ui_form_context()` | `dict` | A2UI ボタンイベントのフォームコンテキスト |
| `get_menu_id()` | `str` | ショートカットメニューイベント ID（`yunhu_menu.id`） |
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
        await event.reply(f"あなたはボタン: {value} をクリックしました")

    if event.get("detail_type") == "yunhu_shortcut_menu":
        menu_id = event.get_menu_id()

## 拡張フィールドの説明

- すべての独自フィールドは `yunhu_` という接頭辞で識別され、標準フィールドとの衝突を避ける
- `yunhu_raw` フィールドに元のデータを保持し、クラウド湖プラットフォームの完全な元のデータに簡単にアクセスできるようにする
- `self.user_id` は、設定の bot_id から取得されるロボットIDを表す
- フォームコマンドは `yunhu_command` フィールドを通じて構造化されたデータを提供する
- ボタンのクリックイベントは `yunhu_button` フィールドを通じてボタンに関する情報を提供する
- A2UIボタンイベントは `yunhu_a2ui` フィールドを通じてA2UIのインタラクションに関する情報を提供する
- ロボットの設定変更は `yunhu_setting` フィールドを通じて設定項目のデータを提供する
- ショートカットメニュー操作は `yunhu_menu` フィールドを通じてメニューに関する情報を提供する
- エモジーパック/ステッカーのメッセージは `yunhu_expression` メッセージセグメントを通じてステッカーのデータ（sticker_id、ステッカーのパックID、画像のサイズなど）を提供する

### エモジーパック/ステッカーのメッセージセグメント (yunhu_expression)

ユーザーがエモジーパックまたはステッカーを送信した場合、メッセージセグメントのタイプは `yunhu_expression` となる：

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

| フィールド | タイプ | 説明 |
|------|------|------|
| `sticker_id` | string | ステッカーの一意な識別子 |
| `sticker_pack_id` | string | ステッカーのパックID |
| `expression_id` | string | エモジーパックのID |
| `image_name` | string | エモジーパックの画像ファイルのパス |
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
                print(f"エモジーパックを受け取りました: sticker_id={data['sticker_id']}, パックID={data['sticker_pack_id']}")

## 多Bot配置

### 設定説明

Yunhuアダプタは、複数のYunhuロボットアカウントを同時に設定および実行することをサポートしています。

```toml
# config.toml
[Yunhu_Adapter.accounts.bot1]
token = "your_bot1_token"  # ロボットのトークン（必須）
mode = "ws"  # 受信モード（オプション、デフォルトは"ws"、"ws"または"webhook"）
webhook_path = "/webhook/bot1"  # Webhookのパス（オプション、デフォルトは"/webhook"）
enabled = true  # 有効化するかどうか（オプション、デフォルトはtrue）

[Yunhu_Adapter.accounts.bot2]
token = "your_bot2_token"  # 2番目のロボットのトークン
webhook_path = "/webhook/bot2"  # 独自のwebhookパス
enabled = true
```

**設定項目の説明:**
- `token`：Yunhuプラットフォームから提供されるAPIトークン（必須）
- `mode`：受信モード（オプション、デフォルトは `"ws"`、"ws"または"webhook"）
- `webhook_path`：Yunhuイベントを受信するHTTPパス（オプション、デフォルトは"/webhook"、webhookモードでのみ使用）
- `enabled`：このアカウントを有効化するかどうか（オプション、デフォルトはtrue）

**重要な注意事項:**
1. YunhuプラットフォームのロボットIDは**実行時に自動検出**され、設定ファイルに指定する必要はありません
2. webhookモードでは、各botに独立した`webhook_path`を設定する必要があります。これにより、それぞれのbotが独自のwebhookイベントを受信できます
3. Yunhuプラットフォームでwebhookを設定する際は、各botに対応するURLを設定してください。たとえば:
   - Bot1: `https://your-domain.com/webhook/bot1`
   - Bot2: `https://your-domain.com/webhook/bot2`

### Send DSLを使用してBotを指定

`Using()`メソッドを使用して、どのbotを使ってメッセージを送信するかを指定できます。このメソッドは2種類のパラメータを受け付けます:
- **アカウント名**：設定ファイル中のbot名（例: `bot1`, `bot2`）
- **bot_id**：設定ファイル中の `bot_id` 値

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# アカウント名を使用してメッセージを送信
await yunhu.Send.Using("bot1").To("user", "user123").Text("Hello from bot1!")

# bot_idを使用してメッセージを送信（対応するアカウントに自動マッチング）
await yunhu.Send.Using("30535459").To("group", "group456").Text("Hello from bot!")

# 指定しない場合は、最初に有効化されたbotを使用
await yunhu.Send.To("user", "user123").Text("Hello from default bot!")
```

> **ヒント:** `bot_id`を使用する場合、システムは設定ファイルにマッチするアカウントを自動的に検索します。これは、イベントの返信処理時に特に便利で、`event["self"]["user_id"]`を使用して、同じアカウントに返信することができます。

### イベントにおけるBot識別

受信したイベントには、対応する`bot_id`情報が自動的に含まれます:

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "yunhu":
        # イベントをトリガーしたロボットIDを取得
        bot_id = event["self"]["user_id"]
        print(f"メッセージはBot: {bot_id} から送信されました")
        
        # 同じbotを使用して返信
        yunhu = adapter.get("yunhu")
        await yunhu.Send.Using(bot_id).To(
            event["detail_type"],
            event["user_id"] if event["detail_type"] == "private" else event["group_id"]
        ).Text("返信メッセージ")
```

### ログ情報

アダプタはログに自動的に `bot_id` 情報を含め、デバッグや追跡に便利です:

```
[INFO] [yunhu] [bot:30535459] ユーザー user123 からのプライベートメッセージを受信
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

### 旧設定の互換性

旧バージョンの `[Yunhu_Adapter.bots.*]` 設定（`bot_id`フィールドを含む）は、`accounts`形式に自動的に移行されます（`bot_id`は実行時に自動検出されるため、設定ファイル中の値は無視されます）。新しい形式への移行を早急にお勧めします。