# 雲湖プラットフォーム特性ドキュメント

YunhuAdapterは、雲湖プロトコルに基づいて構築されたアダプターであり、全ての雲湖機能モジュールを統合し、統一されたイベント処理とメッセージ操作インターフェースを提供します。

---

## ドキュメント情報

- 対応モジュールバージョン: 3.10.1
- メンテナ: ErisPulse

## 基本情報

- プラットフォーム概要：雲湖（Yunhu）はエンタープライズレベルのIMプラットフォームです
- アダプター名：YunhuAdapter
- マルチアカウント対応：bot_id を通じて複数の雲湖ボットアカウントを識別・設定できることをサポート
- チェーン修飾子対応：`.Reply()` などのチェーン修飾子メソッドをサポート
- OneBot12互換：OneBot12形式メッセージの送信をサポート

## サポートされるメッセージ送信タイプ

全ての送信メソッドはチェーン構文（メソッドチェーン）で実装されています。例：

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

await yunhu.Send.To("user", user_id).Text("Hello World!")
```

サポートされている送信タイプは以下の通りです：

- `.Text(text: str)`：プレーンテキストメッセージを送信します。
- `.Html(html: str)`：HTML形式メッセージを送信します。
- `.Markdown(markdown: str)`：Markdown形式メッセージを送信します。
- `.A2UI(text: str)`：A2UI形式メッセージを送信します。
- `.Image(file: bytes, stream: bool = False, filename: str = None)`：画像メッセージを送信します。ストリーミングアップロードとカスタムファイル名に対応しています。
- `.Video(file: bytes, stream: bool = False, filename: str = None)`：動画メッセージを送信します。ストリーミングアップロードとカスタムファイル名に対応しています。
- `.File(file: bytes, stream: bool = False, filename: str = None)`：ファイルメッセージを送信します。ストリーミングアップロードとカスタムファイル名に対応しています。
- `.Batch(target_ids: List[str], message: str, content_type: str = "text", **kwargs)`：メッセージを一括送信します。
- `.Edit(msg_id: str, text: str, content_type: str = "text", buttons: List = None)`：既存のメッセージを編集します。
- `.Recall(msg_id: str)`：メッセージを取り消します（撤回）。
- `.Board(scope: str, content: str, **kwargs)`：掲示板を公告します。scope は `local` と `global` をサポートします。
- `.DismissBoard(scope: str, **kwargs)`：公告掲示板を取り消します。
- `.Stream(content_type: str, content_generator: AsyncGenerator, **kwargs)`：ストリーミングメッセージを送信します。

Board の board_type は以下のタイプをサポートします：

- `local`：ユーザー専用の掲示板
- `global`：グローバル掲示板

### ボタンパラメータの説明

`buttons` パラメータは、ボタンのレイアウトと機能を表すネストされたリストです。各ボタンオブジェクトには以下のフィールドが含まれています：

| フィールド         | タイプ   | 必須 | 説明                                                                 |
|--------------|--------|----------|----------------------------------------------------------------------|
| `text`       | string | 是       | ボタン上のテキスト                                                         |
| `actionType` | int    | 是       | アクションタイプ：<br>`1`: URLへジャンプ<br>`2`: コピー<br>`3`: レポート |
| `url`        | string | 否       | `actionType=1` の場合に使用、ジャンプ先の URL を示します                 |
| `value`      | string | 否       | `actionType=2` の場合、その値がクリップボードにコピーされます<br>`actionType=3` の場合、その値がサブスクライブ先に送信されます |

例：

```python
buttons = [
    [
        {"text": "复制", "actionType": 2, "value": "xxxx"},
        {"text": "点击跳转", "actionType": 1, "url": "http://www.baidu.com"},
        {"text": "汇报事件", "actionType": 3, "value": "xxxxx"}
    ]
]
await yunhu.Send.To("user", user_id).Buttons(buttons).Text("ボタン付きメッセージ")
```

> **注意：**
> - ユーザーが**ボタンレポート（Report）イベント**のボタンをクリックした場合にのみ、プッシュ通知を受け取ります。**コピー**と**URLジャンプ**ではプッシュ通知を受け取れません。

### チェーン修飾子メソッド（組み合わせて使用可能）

チェーン修飾子メソッドは `self` を返すため、チェーン呼び出しが可能です。最終的な送信メソッドの前に呼び出す必要があります。

- `.Reply(message_id: str)`：指定されたメッセージに返信します。
- `.At(user_id: str)`：指定されたユーザーにメンションします。
- `.AtAll()`：全員にメンションします。
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

### OneBot12メッセージサポート

アダプターは OneBot12 形式のメッセージ送信をサポートしており、クロスプラットフォームのメッセージ互換性を容易にします。

- `.Raw_ob12(message: List[Dict], **kwargs)`：OneBot12 形式メッセージを送信します。

```python
# OneBot12 形式のメッセージを送信
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await yunhu.Send.To("user", user_id).Raw_ob12(ob12_msg)

# チェーン修飾子と組み合わせる
ob12_msg = [{"type": "text", "data": {"text": "返信メッセージ"}}]
await yunhu.Send.To("group", group_id).Reply(msg_id).Raw_ob12(ob12_msg)
```

## 送信メソッドの戻り値

全ての送信メソッドは `Task` オブジェクトを返し、`await` を直接使用して送信結果を取得できます。返却結果は ErisPulse アダプターの標準化された戻り値仕様に従います。

```python
{
    "status": "ok",           // 実行ステータス
    "retcode": 0,             // 返り値コード
    "data": {...},            // レスポンスデータ
    "self": {...},            // 自身情報（bot_id を含む）
    "message_id": "123456",   // メッセージID
    "message": "",            // エラーメッセージ
    "yunhu_raw": {...}        // 原始レスポンスデータ
}
```

## 固有イベントタイプ

このプラットフォームの特性を使用するには、`platform=="yunhu"` を検出する必要があります

### 核心の差異点

1. 固有イベントタイプ：
    - フォーム（フォームコマンドを含む）：yunhu_form
    - スタンプ/絵文字メッセージセグメント：yunhu_expression
    - ボタンクリック：yunhu_button_click
    - A2UIボタンクリック：yunhu_a2ui_button
    - ボット設定：yunhu_bot_setting
    - ショートカットメニュー：yunhu_shortcut_menu
2. 拡張フィールド：
    - 全ての固有フィールドは yunhu_ プレフィックスで識別されます
    - 原始データは yunhu_raw フィールドに保持されます
    - チャットプライベート (`private`) 中の self.user_id はボットIDを表します

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
  "user_id": "操作ユーザーID",
  "user_nickname": "ユーザーのニックネーム",
  "message_id": "メッセージID",
  "yunhu_a2ui": {
    "recv_id": "受信者ID",
    "recv_type": "受信者タイプ",
    "action_name": "操作名",
    "source_component_id": "ソースコンポーネントID",
    "form_context": {},
    "interaction_json": "インタラクションデータJSON文字列"
  }
}

### ボタンクリックイベントの処理例

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_yunhu_notice(event):
    """Yunhu通知イベントを処理します

    すべての通知イベントを処理するために汎用の on_notice() デコレーターを使用し、
    detail_type を通じて異なる種類の通知を区別します
    event.reply() は自動的に Yunhu プラットフォーム経由で返信されます
    """
    # ボタンクリックイベントか確認
    if event.get("detail_type") == "yunhu_button_click":
        user_id = event.get_user_id()
        user_nickname = event.get_user_nickname()
        button_value = event.get("yunhu_button", {}).get("value", "")

        print(f"ユーザー {user_nickname}({user_id}) がボタンをクリックしました: {button_value}")

        # event.reply() を使用して自動返信します（プラットフォームに応じて正しい送信方法を選択します）
        if button_value == "confirm":
            await event.reply("確認ボタンをクリックしました！")
        elif button_value == "cancel":
            await event.reply("操作がキャンセルされました")
        else:
            await event.reply(f"選択を受け取りました: {button_value}")

    # ショートカットメニューイベントを処理
    elif event.get("detail_type") == "yunhu_shortcut_menu":
        menu_id = event.get("yunhu_menu", {}).get("id", "")
        await event.reply(f"ショートカットメニューがトリガーされました: {menu_id}")

    # ボット設定の変更を処理
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

### ボタン付きメッセージをチェーン呼び出しで送信

```python
from ErisPulse import sdk

yunhu = sdk.adapter.get("yunhu")

buttons = [
    [
        {"text": "確認", "actionType": 3, "value": "confirm"},
        {"text": "キャンセル", "actionType": 3, "value": "cancel"},
        {"text": "詳細を見る", "actionType": 1, "url": "http://example.com/detail"}
    ]
]

# ボタン付きメッセージをグループに送信
await yunhu.Send.To("group", "123456").Buttons(buttons).Text("以下の操作を確認してください")

# ボタン付きメッセージをユーザーのプライベートチャットに送信
await yunhu.Send.To("user", "789").Buttons(buttons).Text("選好設定を選択してください")
```

### A2UIメッセージの送信

```python
from ErisPulse import sdk

yunhu = sdk.adapter.get("yunhu")

# A2UIメッセージを送信
await yunhu.Send.To("user", user_id).A2UI("A2UIインタラクションカードの内容")
```

# ボット設定
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
  "group_id": "グループID（グループチャットの場合）",
  "yunhu_menu": {
    "id": "メニューID",
    "type": "メニュータイプ(整数)",
    "action": "メニューアクション(整数)"
  }
}
```

## 拡張フィールドの説明

- 全ての固有フィールドは `yunhu_` プレフィックスで識別され、標準フィールドとの競合を避けます
- 原始データは `yunhu_raw` フィールドに保持され、雲湖プラットフォームの完全な原始データにアクセスするのに便利です
- `self.user_id` はボットIDを表します（設定の bot_id から取得）
- フォームコマンドは `yunhu_command` フィールドを通じて構造化データを提供します
- ボタンクリックイベントは `yunhu_button` フィールドを通じてボタンに関する情報を提供します
- A2UIボタンイベントは `yunhu_a2ui` フィールドを通じて A2UI インタラクションに関する情報を提供します
- ボット設定の変更は `yunhu_setting` フィールドを通じて設定項目データを提供します
- ショートカットメニュー操作は `yunhu_menu` フィールドを通じてメニューに関する情報を提供します
- スタンプ/絵文字メッセージは `yunhu_expression` メッセージセグメントを通じてスタンプデータ（sticker_id、パッケージID、画像サイズなど）を提供します

### スタンプ/絵文字メッセージセグメント (yunhu_expression)

ユーザーがスタンプまたは絵文字を送信すると、メッセージセグメントのタイプは `yunhu_expression` になります：

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
| `sticker_id` | string | スタンプの固有識別子 |
| `sticker_pack_id` | string | スタンプパッケージID |
| `expression_id` | string | 絵文字ID |
| `image_name` | string | 絵文字画像ファイルパス |
| `width` | int | 画像の幅（任意） |
| `height` | int | 画像の高さ（任意） |

使用例：

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event.get_platform() == "yunhu":
        for segment in event.get("message", []):
            if segment.get("type") == "yunhu_expression":
                data = segment["data"]
                print(f"スタンプを受け取りました: sticker_id={data['sticker_id']}, パックID={data['sticker_pack_id']}")
```

---

## マルチBot設定

### 設定の説明

Yunhu アダプターは、同時に複数の雲湖ボットアカウントを設定・実行することをサポートしています。

```toml
# config.toml
[Yunhu_Adapter.bots.bot1]
bot_id = "30535459"  # ボットID（必須）
token = "your_bot1_token"  # ボットトークン（必須）
webhook_path = "/webhook/bot1"  # Webhookパス（任意、デフォルトは"/webhook"）
enabled = true  # 有効にするかどうか（任意、デフォルトはtrue）

[Yunhu_Adapter.bots.bot2]
bot_id = "12345678"  # 2番目のボットのID
token = "your_bot2_token"  # 2番目のボットのトークン
webhook_path = "/webhook/bot2"  # 独立したwebhookパス
enabled = true
```

**設定項目の説明：**
- `bot_id`：ボットの固有識別子ID（必須）。どのボットによってトリガーされたイベントかを識別するために使用されます
- `token`：雲湖プラットフォームが提供するAPIトークン（必須）
- `webhook_path`：雲湖イベントを受信するHTTPパス（任意、デフォルトは"/webhook"）
- `enabled`：このbotを有効にするかどうか（任意、デフォルトはtrue）

**重要なヒント：**
1. 雲湖プラットフォームのイベントにはボットIDが含まれていないため、設定で明示的に `bot_id` を指定する必要があります
2. 各botには独自の `webhook_path` を持たせる必要があり、それぞれのwebhookイベントを受信できるようにするためです
3. 雲湖プラットフォームでwebhookを設定する際は、各botに対応するURLを設定してください。例：
   - Bot1: `https://your-domain.com/webhook/bot1`
   - Bot2: `https://your-domain.com/webhook/bot2`

### Send DSLを使用したBotの指定

`Using()` メソッドを使用して、どのbotを使用してメッセージを送信するかを指定できます。このメソッドは2つのパラメータをサポートします：
- **アカウント名**：設定の bot 名（例: `bot1`, `bot2`）
- **bot_id**：設定の `bot_id` 値

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# アカウント名を使用してメッセージを送信
await yunhu.Send.Using("bot1").To("user", "user123").Text("bot1からのメッセージです！")

# bot_id を使用してメッセージを送信（対応するアカウントを自動的に照合）
await yunhu.Send.Using("30535459").To("group", "group456").Text("botからのメッセージです！")

# 指定がない場合、最初に有効になったbotが使用されます
await yunhu.Send.To("user", "user123").Text("デフォルトbotからのメッセージです！")
```

> **ヒント：** `bot_id` を使用する場合、システムは設定内の一致するアカウントを自動的に検索します。イベントへの返信を処理する際に特に便利です。`event["self"]["user_id"]` を直接使用して、同じアカウントから返信できます。

### イベント内のBot識別子

受信したイベントには、対応する `bot_id` 情報が自動的に含まれます。

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "yunhu":
        # イベントをトリガーしたボットIDを取得
        bot_id = event["self"]["user_id"]
        print(f"メッセージは Bot: {bot_id} から来ました")
        
        # 同じbotで返信メッセージを送信
        yunhu = adapter.get("yunhu")
        await yunhu.Send.Using(bot_id).To(
            event["detail_type"],
            event["user_id"] if event["detail_type"] == "private" else event["group_id"]
        ).Text("返信メッセージ")
```

### ログ情報

アダプターはログに自動的に `bot_id` 情報を含めます。デバッグと追跡を容易にします：

```
[INFO] [yunhu] [bot:30535459] プライベートメッセージを受信 (送信者: user123)
[INFO] [yunhu] [bot:12345678] メッセージ送信成功、message_id: abc123
```

### 管理インターフェース

```python
# 全アカウント情報の取得
bots = yunhu.bots

# アカウントが有効か確認
bot_status = {
    bot_name: bot_config.enabled
    for bot_name, bot_config in yunhu.bots.items()
}

# アカウントの動的有効化/無効化（アダプターの再起動が必要）
yunhu.bots["bot1"].enabled = False
```

### 旧形式の設定との互換性

システムは旧形式の設定を自動的に互換性を持たせますが、より良いマルチbotサポートを得るために、新形式の設定に移行することをお勧めします。

請直接返回翻译后的完整Markdown内容，不要包含任何其他文字。