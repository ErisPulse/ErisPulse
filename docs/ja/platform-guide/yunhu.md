# 云湖プラットフォームの特徴ドキュメント

YunhuAdapterは、Yunhuプロトコルに基づいて構築されたアダプターであり、Yunhuのすべての機能モジュールを統合し、一貫したイベント処理とメッセージ操作のインターフェースを提供します。

---

## ドキュメント情報

- 対応モジュールバージョン: 4.6.2
- メンテナ: ErisPulse
- 最終更新日: 2026-11-10

## 基本情報

- プラットフォーム紹介: Yunhuは、企業向けのリアルタイムコミュニケーションプラットフォームです。
- アダプタ名: YunhuAdapter
- 多アカウント対応: bot_idで識別可能な複数のYunhuロボットアカウントを構成可能
- 鏈式修飾子対応: .Reply()などの修飾子メソッドをチェーンで使用可能
- OneBot12互換: OneBot12形式のメッセージ送信に対応

## v5 ファンタジー更新（4.4.0）

本アダプターはv5ファンタジーに完全に適合し、増分アップグレードでAPIは互換性を保持しています：

- **公式サービスAPI一覧**（Api DSL拡張メソッド）: 編集メッセージ、一括送信、メッセージリスト、ユーザー/グローバルボード、グループメンバーの禁止、グループメンバーの削除、グループメッセージタイプ制限、グループタグのCRUD、ユーザーにタグを付ける
- **標準 keyboard 段**（跨プラットフォーム相互作用コンポーネント標準）: {"type": "keyboard", "data": {"rows": [[{"label", "type": "callback|link", "data"}]]}} メッセージは自動的にYunhuのbuttonsに変換される。.Buttons(rows) / .Keyboard(rows) 修飾子は汎用構造を受け入れる（元の構造は後方互換）
- **相互作用コールバック標準フィールド**: ボタンクリック/A2UIイベントには interaction_id / button_data という標準フィールドが含まれる
- **spawn_background タスクの所属**: WS接続タスクは `runtime.spawn_background` を使用
- **フレームワークのソフト依存**: ErisPulse>=2.7.1を実行時に検出し、警告を表示する。起動時にバージョンログを出力する

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

> 完全な標準説明は[跨プラットフォーム相互作用コンポーネント標準](../standards/standardization-guide.md)をご覧ください。

## 標準化対応（4.6.2）

このバージョンではアダプターの標準化が完了し、応答構造とエラーコードは[API応答規格](../standards/api-response.md)に従います。

### アカウントと多アカウントの完結

- **イベント注入 `self.account_id`**（内部アカウント名）: 受信したイベント `self` オブジェクトには、イベントを発生させたアカウント名が含まれており、`event.reply()` は自動的に**受信したアカウント**にルーティングされます。多アカウントの場面では、もう手動で `Using(bot_id)` を使用する必要はありません。
- **`call_api` 双重互換フィールド**: `account_id`（標準名）/ `_account_id`（旧名）の両方でアカウントを指定可能。フレームワークのApiDSL（`Api.Using(...)`）は自動的に適応
- **`Send` は `send_context` を読み取る**（イベントアカウントのバックアップ）: イベント処理コンテキスト内で `Send` を呼び出す場合、デフォルトでは送信元アカウントにフォールバックする

### エラーコード規格

| retcode | 含義 | 说明 |
|---------|------|------|
| 0 | 成功 | — |
| 33001 | 网络错误 | 云湖服务器失败等网络类异常 |
| 34100 | 平台失败 | 云湖返回失败；原始响应保留在 `yunhu_raw` |
| 10002 | 不支持 | 资源不存在（机器人/用户/群不存在）或平台无对应能力的标准动作 |
| 10003 | 参数错误 | 缺少或无效参数 |

> **4.6.2 変更点**: `_platform` を追加した後、`make_response` はフレームワークによって自動的に `yunhu_raw` を含む。プラットフォームの失敗はすべて `34100` を返す。"机器人/用户/群不存在" は `34001` から `10002`（リソースが存在しない）に変更された。

### 応答構造の調整

元の応答の非標準 `self` フィールドは `data.self_info`（bot_id を含む）に移動し、トップレベルには標準フィールドと `yunhu_raw` だけが残る：

```json
{
  "status": "ok",
  "retcode": 0,
  "data": {
    "self_info": {"user_id": "bot_id"},
    "messageInfo": {"msgId": "..."}
  },
  "message_id": "123456",
  "message": "",
  "yunhu_raw": {}
}
```

### 未知のイベントは静かに破棄されない

認識できないYunhuイベントは、`type="unknown"` イベント（`detail_type` は元のイベントタイプ、元のデータは `yunhu_raw` に保持）を生成し、警告ログを出力する。モジュールはこれに基づいて未対応のイベントタイプを調査できる。

### プラットフォーム拡張メソッドの約定

歴史的なプラットフォーム拡張メソッド（`edit_message` / `batch_send` / `set_user_board` / `gag_group_member` / `create_group_tag` など）は引き続き使用可能。**新しいプラットフォーム拡張はすべて `Api.call("yunhu.xxx", **params)` を通じて行う**（下記「プラットフォーム拡張アクション」を参照）。

---

## 支持するメッセージ送信タイプ

すべての送信メソッドはチェーン構文で実現可能。例えば：
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

await yunhu.Send.To("user", user_id).Text("Hello World!")
```

サポートする送信タイプは以下の通りです：
- `.Text(text: str)`：純粋なテキストメッセージを送信。
- `.Html(html: str)`：HTML形式のメッセージを送信。`.HTML(html)` は別名（標準 Send メソッドの命名と一致させる）。
- `.Markdown(markdown: str)`：Markdown形式のメッセージを送信。
- `.MergeForward(nodes, title="合并聊天记录")`：合併転送メッセージを送信（<details>折りたたみHTMLカードとしてレンダリングされ、htmlチャネルを通じて送信される）。
- `.A2UI(text: str)`：A2UI形式のメッセージを送信。
- `.Image(file: bytes, stream: bool = False, filename: str = None)`：画像メッセージを送信。ストリームアップロードとカスタムファイル名をサポート。
- `.Video(file: bytes, stream: bool = False, filename: str = None)`：動画メッセージを送信。ストリームアップロードとカスタムファイル名をサポート。
- `.File(file: bytes, stream: bool = False, filename: str = None)`：ファイルメッセージを送信。ストリームアップロードとカスタムファイル名をサポート。
- `.Batch(target_ids: List[str], message: str, content_type: str = "text", **kwargs)`：一括メッセージ送信。
- `.Edit(msg_id: str, text: str, content_type: str = "text", buttons: List = None)`：既存のメッセージを編集。
- `.Recall(msg_id: str)`：メッセージを撤回。
- `.Board(content: str, content_type: str = "text")`：公告看板を送信。作用域は `To()` から推測される（ターゲットを指定=ローカル看板、未指定=グローバル看板）。チェーン修飾：`.Expire(duration)` 相対的な期限（秒）、`.ExpireAt(timestamp)` 絶対的な期限（秒単位のタイムスタンプ）、`.ForMember(member_id)` グループメンバー看板；**内容が空の場合は自動的に看板を撤回**。旧式 `Board("local", "公告")` 明示的な scope 書き込みもまだ互換性がある。
- `.DismissBoard()`：公告看板を撤回。作用域は `To()` から推測され、`.ForMember(member_id)` もサポートする。旧式 `DismissBoard("local")` 書き込みもまだ互換性がある。
- `.Stream(content_type: str, content_generator: AsyncGenerator, **kwargs)`：ストリームメッセージを送信。

### グループ管理メソッド

すべてのグループ管理メソッドはチェーン構文でグループを指定する必要がある。例えば：
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

await yunhu.Send.To("group", group_id).Kick(user_id)
```

- `.Kick(user_id: str)`：グループメンバーを削除。ロボットは`グループメンバーを削除する権限`が必要。
- `.Ban(user_id: str, duration: int = 600)`：ユーザーを禁止。`duration`は禁止時間（秒）、0は解除、-1は永久禁止。ロボットは`ユーザーを禁止する権限`が必要。
- `.CreateTag(tag: str, color: str = None, desc: str = None, sort: int = None)`：グループタグを作成。`color`は#RRGGBB形式、`sort`が小さいほど前に表示される。ロボットは`タググループを制御する権限`が必要。
- `.EditTag(tag: str, new_tag: str = None, color: str = None, desc: str = None, sort: int = None)`：グループタグを編集。各パラメータはオプションで、指定しない場合は変更しない。ロボットは`タググループを制御する権限`が必要。
- `.DeleteTag(tag: str)`：グループタグを削除。ロボットは`タググループを制御する権限`が必要。
- `.GetTagList()`：グループタグリストを取得。返却データには`list`配列が含まれる。
- `.AddUserTag(user_id: str, tag: str)`：ユーザーにタグを追加。ロボットは`タググループを制御する権限`が必要。
- `.RemoveUserTag(user_id: str, tag: str)`：ユーザーからタグを削除。ロボットは`タググループを制御する権限`が必要。
- `.SetMsgTypeLimit(types: str)`：グループ内のメッセージタイプを制限。`types`はメッセージタイプ名で、複数ある場合はカンマで区切る（例: `"text,image,video"`）、空文字列は制限しない。ロボットは`グループ情報を変更する権限`が必要。

### メッセージ検索メソッド

指定された会話（ユーザー/グループ）の履歴メッセージリストを取得するには、チェーン構文でターゲットを指定する必要がある。例えば：
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

result = await yunhu.Send.To("group", group_id).GetMessages(before=10)
```

- `.GetMessages(message_id: str = None, before: int = None, after: int = None)`：会話の履歴メッセージを取得。返却データには`list`配列と`total`総数が含まれる。
  - `message_id`：メッセージID（オプション）。指定しない場合、`before`と組み合わせて最近のN件を返す。
  - `before`：指定したメッセージIDの前のN件を返す。
  - `after`：指定したメッセージIDの後のN件を返す。
  - > **注意：** `before` と `after` は少なくとも1つを指定する必要があり、0より大きくなければ、サーバーはメッセージを返さない。

Board 作用域は `To()` によって自動的に推測される：
- `To(target_type, target_id)` を指定 → ローカル看板（指定されたユーザー/グループ）
- `To()` を指定しない → グローバル看板

```python
# ローカル看板（60 秒後相対的な期限）
await yunhu.Send.To("group", group_id).Expire(60).Board("公告", content_type="markdown")

# グループメンバー看板（指定されたメンバーのみ表示）
await yunhu.Send.To("group", group_id).ForMember(user_id).Board("あなた専用")

# 絶対時間の期限
await yunhu.Send.To("group", group_id).ExpireAt(1785208268).Board("指定時間で期限切れ")

# グローバル看板
await yunhu.Send.Board("グローバル公告")

# ローカル看板をクリア（内容が空の場合は自動的に看板を撤回）
await yunhu.Send.To("group", group_id).Board("")
```

### ボタンパラメータの説明

`buttons` パラメータは、ボタンのレイアウトと機能を示すネストされたリストです。各ボタンオブジェクトには以下のフィールドが含まれます：

| フィールド         | タイプ   | 必須 | 説明                                                                 |
|--------------|--------|----------|----------------------------------------------------------------------|
| `text`       | string | 是       | ボタン上の文字                                                         |
| `actionType` | int    | 是       | 動作タイプ：<br>`1`: URL に移動<br>`2`: コピー<br>`3`: イベントを報告            |
| `url`        | string | 否       | `actionType=1` の場合、移動先の URL を使用する                         |
| `value`      | string | 否       | `actionType=2` の場合、この値がクリップボードにコピーされる<br>`actionType=3` の場合、この値がサブスクライバに送信される |

例：
```python
buttons = [
    [
        {"text": "コピー", "actionType": 2, "value": "xxxx"},
        {"text": "クリックして移動", "actionType": 1, "url": "http://www.baidu.com"},
        {"text": "イベントを報告", "actionType": 3, "value": "xxxxx"}
    ]
]
await yunhu.Send.To("user", user_id).Buttons(buttons).Text("ボタン付きメッセージ")
```
> **注意：**
> - ユーザーが**イベント報告ボタン**をクリックした場合にのみ、通知を受け取る。**コピー**と**URL移動**は通知を受け取れない。

### チェーン修飾メソッド（組み合わせ可能）

チェーン修飾メソッドは `self` を返し、チェーンで呼び出すことが可能。最終的な送信メソッドの前に呼び出す必要がある：

- `.Reply(message_id: str)`：指定されたメッセージに返信。
- `.At(user_id: str)`：指定されたユーザーを@する。
- `.AtAll()`：全員を@する。
- `.Buttons(buttons: List)`：ボタンを追加する。

### チェーン呼び出しの例

```python
# 基礎的な送信
await yunhu.Send.To("user", user_id).Text("Hello")

# メッセージの返信
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

# ユーザーの禁止（10分間）
await yunhu.Send.To("group", group_id).Ban(user_id, duration=600)

# 禁止の解除
await yunhu.Send.To("group", group_id).Ban(user_id, duration=0)

# 永久禁止
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

### OneBot12メッセージサポート

アダプターはOneBot12形式のメッセージを送信することをサポートし、跨プラットフォームメッセージの互換性を確保する：

- `.Raw_ob12(message: List[Dict], **kwargs)`：OneBot12形式のメッセージを送信。

```python
# OneBot12形式のメッセージを送信
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await yunhu.Send.To("user", user_id).Raw_ob12(ob12_msg)

# チェーン修飾と組み合わせて使用
ob12_msg = [{"type": "text", "data": {"text": "返信メッセージ"}}]
await yunhu.Send.To("group", group_id).Reply(msg_id).Raw_ob12(ob12_msg)
```

## 標準 API アクション（ApiDSL）

> [!NOTE]
> 本機能は ErisPulse **2.7.0+** および YunhuAdapter **4.3.0+** が必要です。

`Send` チェーン送信に加えて、アダプターは `Api` 内部クラスを提供し、OneBot12標準 API アクションと Yunhu プラットフォーム拡張アクションを公開します。すべてのメソッドは標準応答形式を返します。

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

# メッセージの撤回（chat_id + chat_type の提供が必要）
await yunhu.Api.delete_message("msg_id", chat_id="123", chat_type="group")

# 多アカウント：特定の Bot アカウントを指定
info = await yunhu.Api.Using("bot1").get_self_info()
```

### 支持する標準アクション

| メソッド | 説明 | データ来源 |
|------|------|---------|
| `get_self_info()` | ロボット自身の情報 | 公開 Web API（bot-info） |
| `get_user_info(user_id)` | ユーザー情報（任意のユーザーが照会可能） | 公開 Web API（user/homepage） |
| `get_group_info(group_id)` | グループ情報 | 公開 Web API（group-info） |
| `upload_file(*, type, name, ...)` | ファイルをアップロード（image/video/file を自動判定） | Bot 開放 API |
| `get_file(file_id)` | ファイルを取得（file_id は URL に等しい） | — |
| `delete_message(message_id, *, chat_id, chat_type)` | メッセージを撤回 | Bot 開放 API（/bot/recall） |

> **注意**：`get_self_info` / `get_user_info` / `get_group_info` は**非公式の公開 Web API**（chat-web-go.jwzhd.com）を通じて実現され、これらのインターフェースは認証不要だが、公式ドキュメントではなく、プラットフォームの更新に伴い変更される可能性がある。失敗時は標準エラーレスポンスを返す。

### 標準アクションの非対応

以下の標準アクションは Yunhu には対応する API がないため、呼び出された場合は `retcode=10002`（対応しない操作）が返される：
- `get_friend_list`（Bot 開放 API の「ロボットユーザー一覧」はまだリリース待ち）
- `get_group_list` / `get_group_member_info` / `get_group_member_list`
- `set_group_name` / `leave_group`

### プラットフォーム拡張アクション

`Api.call("yunhu.xxx", **params)` を通じて Yunhu 特有のアクションを呼び出す（パラメータは OB12 風の命名を使用し、アダプターが自動的に Yunhu フィールドに翻訳する）：

| 拡張アクション | 説明 | 等価 Send メソッド |
|---------|------|---------------|
| `yunhu.recall` | メッセージの撤回（msg_id, chat_id, chat_type） | `Send.To(...).Recall(msg_id)` |
| `yunhu.kick` | グループメンバーの削除（group_id, user_id） | `Send.To("group", g).Kick(uid)` |
| `yunhu.ban` | 禁言（group_id, user_id, duration） | `Send.To("group", g).Ban(uid, duration)` |
| `yunhu.unban` | 禁言の解除（group_id, user_id） | `Send.To("group", g).Ban(uid, duration=0)` |
| `yunhu.tag.create/edit/delete/list` | グループタグの CRUD（group_id, ...） | `Send.To("group", g).CreateTag(...)` など |
| `yunhu.tag.relate` / `yunhu.tag.relate_cancel` | ユーザーにタグを追加/削除 | `Send.To("group", g).AddUserTag(...)` など |
| `yunhu.set_member_title` / `yunhu.unset_member_title` | **メンバーの頭語の別名**（タグ ≈ 頭語、内部的に tag.relate にマッピング） | — |
| `yunhu.msg_type_limit` | グループメッセージのタイプ制限（group_id, type） | `Send.To("group", g).SetMsgTypeLimit(...)` |
| `yunhu.get_messages` | 歴史メッセージの取得（chat_id, chat_type, message_id?, before?, after?） | `Send.To(...).GetMessages(...)` |
| `yunhu.bot_info` | 公開 bot-info 検索（bot_id） | — |
| `yunhu.user_homepage` | 公開ユーザーのホーム検索（user_id） | — |

```python
# プラットフォーム拡展示例
await yunhu.Api.call("yunhu.kick", group_id="123", user_id="456")
await yunhu.Api.call("yunhu.set_member_title", group_id="123", user_id="456", title="VIP")
result = await yunhu.Api.call("yunhu.get_messages", chat_id="123", chat_type="group", before=10)
```

> **タグと頭語**：Yunhuの「タグ」の意味はOneBot12のグループメンバーの`title`と同等です。`yunhu.set_member_title`は`yunhu.tag.relate`の原生語義別名で、内部的には同一のエンドポイントにマッピングされます。グループメッセージイベントで送信者の役割は`senderUserLevel`から標準の`role`フィールドにマッピングされます（owner/admin/member）。

## 送信メソッドの返り値

すべての送信メソッドは Task オブジェクトを返し、直接 await して送信結果を取得できる。返り値は ErisPulse アダプターの標準化された返り値規格に従う：

```python
{
    "status": "ok",           // 実行状態
    "retcode": 0,             // 返り値コード
    "data": {...},            // 返り値データ（self_info は bot_id を含む、上記「返り値構造の調整」参照）
    "message_id": "123456",   // メッセージID
    "message": "",            // エラーメッセージ
    "yunhu_raw": {...}        // 元の返り値データ
}
```

> **4.6.2 変更点**：元の返り値の非標準 `self` フィールドは `data.self_info` に移動しました。bot_id を取得するには `result["data"]["self_info"]["user_id"]` を使用してください。

## 特有のイベントタイプ

`platform=="yunhu"` を検証してから本プラットフォームの特有機能を使用する必要があります。

### 核心的な違い点

1. 特有のイベントタイプ：
    - 表形式（例: 表形式のコマンド）: yunhu_form
    - 表情/ステッカー形式のメッセージ: yunhu_expression
    - ボタンクリック: yunhu_button_click
    - A2UIボタンクリック: yunhu_a2ui_button
    - ロボットの設定: yunhu_bot_setting
    - ショートカットメニュー: yunhu_shortcut_menu
2. 標準フィールドの拡張（4.3.0+）:
    - メッセージイベントに標準の `role` フィールドが追加されました（Yunhu の `senderUserLevel` から `owner`/`admin`/`member` にマッピング）
    - 新たに `user_avatar` フィールドが追加されました（送信者のアバター URL）
3. 拡張フィールド:
    - すべての特有フィールドは `yunhu_` で始まるプレフィックスが付いています
    - 元のデータは `yunhu_raw` フィールドに保持されます
    - プライベートチャットでは `self.user_id` はロボットのIDを表します

### 特殊フィールドの例

```python
# 表形式のコマンド
{
  "type": "message",
  "detail_type": "private",
  "yunhu_command": {
    "name": "表形式のコマンド名",
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
  "user_id": "操作ユーザーID",
  "user_nickname": "ユーザーのニックネーム",
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
    """Yunhu通知イベントを処理する

    すべての通知イベントを処理するには、on_notice()デコレータを使用し、
    detail_typeで異なるタイプの通知を区別する
    event.reply()は自動的にYunhuプラットフォームで返信する
    """

# ボタンクリックイベントかどうかを確認
    if event.get("detail_type") == "yunhu_button_click":
        user_id = event.get_user_id()
        user_nickname = event.get_user_nickname()
        button_value = event.get("yunhu_button", {}).get("value", "")

        print(f"ユーザー {user_nickname}({user_id}) がボタンをクリックしました: {button_value}")

# event.reply()を使用して返信（プラットフォームに応じて正しい送信方法を選択する）
        if button_value == "confirm":
            await event.reply("確認ボタンをクリックしました！")
        elif button_value == "cancel":
            await event.reply("操作がキャンセルされました")
        else:
            await event.reply(f"選択を受け付けました: {button_value}")

# ショートカットメニューイベントを処理
    elif event.get("detail_type") == "yunhu_shortcut_menu":
        menu_id = event.get("yunhu_menu", {}).get("id", "")
        await event.reply(f"ショートカットメニューが起動しました: {menu_id}")

# ロボットの設定変更
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

### チェーン呼び出しを使ってボタン付きメッセージを送信する

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
await yunhu.Send.To("user", user_id).A2UI("A2UIインタラクションカードの内容")
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
  "user_id": "メニューを起動したユーザーID",
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

アダプターは以下のプラットフォーム固有のメソッドを登録し、`platform == "yunhu"` の場合にのみ使用可能：

| メソッド | 戻り値の型 | 説明 |
|------|----------|------|
| `get_raw_event()` | `dict` | Yunhuの元のイベントデータを取得（`yunhu_raw`） |
| `get_sender_level()` | `str` | 送信者のYunhuの元のレベル（owner/administrator/member/unknown） |
| `get_sender_role()` | `str` | 送信者のOneBot12標準のrole（owner/admin/member） |
| `get_sender_title()` | `str` | 送信者の頭語（標準の`title`フィールドのアクセサ、予約） |
| `get_sender_avatar()` | `str` | 送信者のアバターURL |
| `get_command()` | `dict` | コマンドデータ（コマンドメッセージイベントのみ、`yunhu_command`） |
| `get_button_value()` | `str` | ボタンクリックイベントのvalue（`yunhu_button.value`） |
| `get_a2ui_action()` | `str` | A2UIボタンクリックイベントのactionName |
| `get_a2ui_form_context()` | `dict` | A2UIボタンクリックイベントのフォームコンテキスト |
| `get_menu_id()` | `str` | ショートカットメニューイベントのID（`yunhu_menu.id`） |
| `get_setting()` | `dict` | ロボット設定イベントの設定データ（`yunhu_setting`） |
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

- すべての特有フィールドは `yunhu_` プレフィックスで始まり、標準フィールドとの衝突を避ける
- 元のデータは `yunhu_raw` フィールドに保持され、Yunhuプラットフォームの完全な元のデータにアクセス可能
- `self.user_id` はロボットのIDを表す（設定のbot_idから取得）
- 表形式のコマンドは `yunhu_command` フィールドを通じて構造化データを提供
- ボタンクリックイベントは `yunhu_button` フィールドを通じてボタンに関する情報を提供
- A2UIボタンクリックイベントは `yunhu_a2ui` フィールドを通じてA2UIインタラクションに関する情報を提供
- ロボットの設定変更は `yunhu_setting` フィールドを通じて設定項目のデータを提供
- ショートカットメニュー操作は `yunhu_menu` フィールドを通じてメニューに関する情報を提供
- 表情/ステッカー形式のメッセージは `yunhu_expression` メッセージセグメントを通じてステッカーのデータを提供（sticker_id、ステッカーのパックID、画像のサイズなど）

### 表情/ステッカー形式のメッセージセグメント (yunhu_expression)

ユーザーが表情/ステッカーを送信すると、メッセージセグメントのタイプは `yunhu_expression` となる：

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
| `sticker_id` | string | ステッカーの唯一の識別子 |
| `sticker_pack_id` | string | ステッカーのパックID |
| `expression_id` | string | 表情のID |
| `image_name` | string | 表情の画像のファイルパス |
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
                print(f"表情パックを受け取りました: sticker_id={data['sticker_id']}, パックID={data['sticker_pack_id']}")
```

---

## 多Bot設定

### 設定の説明

Yunhuアダプターは複数のYunhuロボットアカウントを同時に設定および実行できる。

```toml
# config.toml
[Yunhu_Adapter.accounts.bot1]
token = "your_bot1_token"  # ロボットtoken（必須）
mode = "ws"  # 受信モード（オプション、デフォルトは"ws"、"ws"または"webhook"可）
webhook_path = "/webhook/bot1"  # Webhookのパス（オプション、デフォルトは"/webhook"）
enabled = true  # 有効かどうか（オプション、デフォルトはtrue）

[Yunhu_Adapter.accounts.bot2]
token = "your_bot2_token"  # 第二のロボットのtoken
webhook_path = "/webhook/bot2"  # 独自のwebhookパス
enabled = true
```

**設定項目の説明：**
- `token`：Yunhuプラットフォームが提供するAPI token（必須）
- `mode`：受信モード（オプション、デフォルトは `"ws"`、"ws"または"webhook"可）
- `webhook_path`：Yunhuイベントを受け取るHTTPパス（オプション、デフォルトは"/webhook"、webhookモードのみ使用）
- `enabled`：このアカウントを有効にするかどうか（オプション、デフォルトはtrue）

**重要な注意点：**
1. YunhuプラットフォームのロボットIDは**実行時に自動検出**され、設定に指定する必要はない
2. webhookモードでは、各botに独立した`webhook_path`が必要で、独自のwebhookイベントを受け取れる
3. Yunhuプラットフォームでwebhookを設定する際、各botに該当するURLを設定する必要があります。例えば：
   - Bot1: `https://your-domain.com/webhook/bot1`
   - Bot2: `https://your-domain.com/webhook/bot2`

### Send DSLを使用してBotを指定

`Using()`メソッドを使用して、どのbotを使ってメッセージを送信するかを指定できる。このメソッドは2つのパラメータをサポートする：
- **アカウント名**：設定中のbot名（例: `bot1`, `bot2`）
- **bot_id**：設定中の `bot_id` 値

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# アカウント名を使ってメッセージを送信
await yunhu.Send.Using("bot1").To("user", "user123").Text("Hello from bot1!")

# bot_idを使ってメッセージを送信（自動的に対応するアカウントにマッチ）
await yunhu.Send.Using("30535459").To("group", "group456").Text("Hello from bot!")

# 指定しない場合は最初に有効なbotを使用
await yunhu.Send.To("user", "user123").Text("Hello from default bot!")
```

> **ヒント:** `bot_id` を使用する場合、システムは設定の中で一致するアカウントを自動的に検索します。これはイベントの返信時に特に便利で、`event["self"]["user_id"]` を使用して同じアカウントに返信することができます。

### イベント内のBot識別子

受信したイベントには、対応する`bot_id`情報が自動的に含まれます（4.6.2以降、内部アカウント名 `self.account_id` も注入）：

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "yunhu":
        # 送信元のロボットIDを取得
        bot_id = event["self"]["user_id"]
        account_id = event["self"].get("account_id", "")  # 内部アカウント名（例: bot1）
        print(f"メッセージはBot: {bot_id}（アカウント: {account_id}）から来ました")

        # 4.6.2以降、event.reply()は受理アカウントに自動的にルーティングされるので、直接返信できます
        await event.reply("返信メッセージ")

        # まだ明示的にアカウントを指定して送信することもできます
        yunhu = adapter.get("yunhu")
        await yunhu.Send.Using(bot_id).To(
            event["detail_type"],
            event["user_id"] if event["detail_type"] == "private" else event["group_id"]
        ).Text("返信メッセージ")
```

> **ヒント**: `call_api` は、`account_id`（標準名）と `_account_id`（旧名）の両方のアカウントフィールドをサポートしており、フレームワークの ApiDSL の `Using()` とイベントアカウントのバックアップ（`send_context`）は自動的に適応されます。

### ログ情報

アダプターはログに自動的に `bot_id` 情報を含め、デバッグや追跡に便利です。

```
[INFO] [yunhu] [bot:30535459] ユーザー user123 からのプライベートチャットメッセージを受け取りました
[INFO] [yunhu] [bot:12345678] メッセージ送信成功、message_id: abc123
```

### 管理インターフェース

```python
# すべてのアカウント情報を取得
bots = yunhu.bots

# アカウントの有効状態を確認
bot_status = {
    bot_name: bot_config.enabled
    for bot_name, bot_config in yunhu.bots.items()
}

# アカウントの有効/無効を動的に変更（アダプターの再起動が必要）
yunhu.bots["bot1"].enabled = False
```

### 旧設定の互換性

旧版の `[Yunhu_Adapter.bots.*]` 設定（bot_idフィールドを含む）は `accounts` 形式に自動的に移行されます（bot_idは実行時に自動検出され、設定の値は無視されます）。新しい形式への移行を推奨します。