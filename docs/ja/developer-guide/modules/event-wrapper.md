# Event ラッパークラス詳解

> [!NOTE]
> **L1 コア必読**——トップページの「読書パス」にある5つのコアドキュメントの1つで、モジュール開発に必須です。


ハンドラー内の `event` パラメーターが `.get_text()` / `.reply()` / `.wait_reply()` を直接呼び出せるのは、Event ラッパークラスのおかげです。本ドキュメントはその完全なメソッド一覧です——イベントハンドラーを作成する際に必要に応じて参照し、メソッドのシグネチャと動作はすべてここに記載の内容を基準としてください。

## event パラメーターへの型アノテーション追加

イベントハンドラーの `event` パラメーターは **Event ラッパークラス**（dict のサブクラス）です。`Event` の型アノテーションを追加することを**強く推奨**します（実行時はアノテーションがなくても動作しますが、アノテーションは IDE 補完と静的チェックに役立ちます）：

```python
from ErisPulse.Core.Event import Event

@message.on_private_message()
async def handler(event: Event):
    text = event.get_text()   # IDE がすべての便利メソッドを自動補完
    await event.reply(text)   # スペルミスは静的チェック時に検出できます
```

アノテーションを付けない場合、IDE は Event 上のメソッドを認識できず（`get_text()` / `reply()` / `wait_reply()` / プラットフォーム拡張メソッドのいずれも補完されず）、記憶を頼りに入力するしかありません。

> **区別に注意**：イベントハンドラーコールバックの `event` は **Event ラッパークラス**（`Event` でアノテーション）ですが、モジュールライフサイクルメソッド `on_load` / `on_unload` の `event` は通常の **dict**（`dict` でアノテーション）です。両者を混同しないでください。

## コア特性

- **辞書と完全互換**：Event は dict を継承
- **便利メソッド**：多数の便利メソッドを提供
- **ドットアクセス**：ドットによるイベントフィールドへのアクセスをサポート
- **後方互換**：すべてのメソッドは任意

## コアフィールドメソッド

```python
from ErisPulse.Core.Event import command, Event

@command("info")
async def info_command(event: Event):
    event_id = event.get_id()
    platform = event.get_platform()
    time = event.get_time()
    print(f"ID: {event_id}, プラットフォーム: {platform}, 時刻: {time}")
```

## メッセージイベントメソッド

```python
from ErisPulse.Core.Event import message, Event

@message.on_private_message()
async def private_handler(event: Event):
    text = event.get_text()
    user_id = event.get_user_id()
    nickname = event.get_user_nickname()
    await event.reply(f"こんにちは、{nickname}さん！")
```

## メッセージタイプ判定

```python
from ErisPulse.Core.Event import message, Event

@message.on_group_message()
async def group_handler(event: Event):
    is_private = event.is_private_message()
    is_group = event.is_group_message()
    is_at = event.is_at_message()
    await event.reply(f"タイプ: {'個人チャット' if is_private else 'グループチャット'}")
```

## 返信機能

```python
from ErisPulse.Core.Event import command, Event

@command("ask")
async def ask_command(event: Event):
    await event.reply("あなたの名前を入力してください:")
    reply = await event.wait_reply(timeout=30)
    if reply:
        name = reply.get_text()
        await event.reply(f"こんにちは、{name}さん！")

@command("price")
async def price_command(event: Event):
    await event.reply("金額を入力してください（例：5元）:")
    # 返信は正規表現に一致する必要があり、一致しない場合はタイムアウトまで待ち続けます
    reply = await event.wait_reply(timeout=30, regex=r"\d+\s*元")
    if reply:
        await event.reply(f"金額を受け付けました：{reply.get_text()}")
```

#### reply 以外：send_chain

`reply()` では対応できないシナリオ——プラットフォーム固有の修飾メソッド（Expire/Board など）、連続する複数の修飾、
内容パラメーターを持たないアクション型の送信——には `event.send_chain` でターゲットと送信アカウントが設定済みの送信チェーンを取得し、
自由に修飾を追加してから送信してください：

```python
await event.send_chain.At(event.user_id).Text("内容")     # チェーン修飾 + 送信
```

修飾メソッドの一覧は [送信メソッド仕様](../../standards/send-method-spec.md) を参照してください。

## インタラクティブセッションの応用

> [!NOTE]
> このセクションの機能には ErisPulse **2.8.0+** が必要です。

```python
# セッションのタイマーリマインダー：5分間返信がない場合はリマインドし、ユーザーの返信後に自動キャンセル
reminder = event.remind(300, "まだいますか？会話を終えたい場合は「終了」と返信してください")
reminder.cancel()  # 手動でのキャンセルも可能

# タイムアウトエスカレーション：指定時刻に必ず発火（返信ではキャンセルされない）、長時間未処理の場合にオーナーへ通知するなど
event.escalate(1800, lambda e: notify_master("チケットタイムアウト"))

# マルチパス待機：「同意」と「拒否」を同時に待ち、先着順で取得
which, reply = await event.select(
    event.expect(pattern="同意*", user="10001"),
    event.expect(pattern="拒否*", user="10002"),
    timeout=60,
)
if which is None:
    await event.reply("タイムアウト：承認を受信しませんでした")

# セッションレベル待機：同じグループの誰の返信でもマッチ可能（グループ協働）
reply = await event.wait_reply(session=True, prompt="どなたか回答をお願いします！")

# セッション受信箱：現在のセッションの直近20件のメッセージ（ボットを含む、AI コンテキスト / 重複防止の基盤）
messages = await event.history(20)

# メッセージトランザクション：例外発生時にトランザクション内で送信済みのメッセージを自動取り消し
async with event.message_tx():
    await event.reply("処理中です。お待ちください...")
    result = await do_something()
    await event.reply(f"完了：{result}")
```

## コマンド情報の取得

```python
from ErisPulse.Core.Event import command, Event

@command("cmdinfo")
async def cmdinfo_command(event: Event):
    cmd_name = event.get_command_name()
    cmd_args = event.get_command_args()
    await event.reply(f"コマンド: {cmd_name}, 引数: {cmd_args}")
```

## 通知イベントメソッド

```python
from ErisPulse.Core.Event import notice, Event

@notice.on_friend_add()
async def friend_add_handler(event: Event):
    await event.reply("友達登録ありがとうございます！")
```

## メソッド早見表

### コアメソッド

#### イベント基本情報
- `get_id()` - イベントID を取得
- `get_time()` - イベントのタイムスタンプを取得（Unix 秒単位）
- `get_type()` - イベントタイプを取得（message/notice/request/meta）
- `get_detail_type()` - イベントの詳細タイプを取得（private/group/friend など）
- `get_platform()` - プラットフォーム名を取得

#### ボット情報
- `get_self_platform()` - ボットのプラットフォーム名を取得
- `get_self_user_id()` - ボットのユーザーID を取得
- `get_self_account_id()` - ボットのアカウントID を取得（マルチ Bot モード）
- `get_self_info()` - ボットの完全情報辞書を取得

#### セッション識別子
- `get_target_id()` - 統一ターゲット ID を取得（グループチャットは `group_id`、チャンネルは `channel_id`、個人チャットは `user_id` を返し、group → channel → guild → thread → user の順で最初の非空値を採用）
- `get_session_id()` - セッションの一意識別子を取得、形式は `{platform}:{detail_type}:{target_id}`

### メッセージイベントメソッド

#### メッセージ内容
- `get_message()` - メッセージセグメント配列を取得（OneBot12 形式）
- `get_alt_message()` - メッセージの代替テキストを取得
- `get_text()` - プレーンテキスト内容を取得（`get_alt_message()` のエイリアス）
- `get_message_text()` - プレーンテキスト内容を取得（`get_alt_message()` のエイリアス）

#### 送信者情報
- `get_user_id()` - 送信者のユーザーID を取得
- `get_user_nickname()` - 送信者のニックネームを取得
- `get_sender()` - 送信者の完全情報辞書を取得

#### グループ/チャンネル情報
- `get_group_id()` - グループID を取得（グループチャットメッセージ）
- `get_channel_id()` - チャンネルID を取得（チャンネルメッセージ）
- `get_guild_id()` - サーバーID を取得（サーバーメッセージ）
- `get_thread_id()` - トピック/サブチャンネルID を取得（トピックメッセージ）

#### @メッセージ関連
- `has_mention()` - @ボットを含むかどうか
- `get_mentions()` - @されたすべてのユーザーID のリストを取得

### メッセージタイプ判定

#### 基本判定
- `is_message()` - メッセージイベントかどうか
- `is_private_message()` - 個人チャットメッセージかどうか
- `is_group_message()` - グループチャットメッセージかどうか
- `is_at_message()` - @メッセージかどうか（`has_mention()` のエイリアス）

### 通知イベントメソッド

#### 通知操作者
- `get_operator_id()` - 操作者の ID を取得
- `get_operator_nickname()` - 操作者のニックネームを取得

#### 通知タイプ判定
- `is_notice()` - 通知イベントかどうか
- `is_group_member_increase()` - グループメンバー増加イベント
- `is_group_member_decrease()` - グループメンバー減少イベント
- `is_friend_add()` - 友達追加イベント（`detail_type == "friend_increase"` に一致）
- `is_friend_delete()` - 友達削除イベント（`detail_type == "friend_decrease"` に一致）

### リクエストイベントメソッド

#### リクエスト情報
- `get_comment()` - リクエストの添付メッセージを取得

#### リクエストタイプ判定
- `is_request()` - リクエストイベントかどうか
- `is_friend_request()` - 友達リクエストかどうか
- `is_group_request()` - グループリクエストかどうか

#### リクエスト承認（approve / reject）

リクエストハンドラーを登録し、リクエストに対する判断を行います：

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend(event):
    request_id = event.get_request_id()   # リクエスト識別子（欠落時は approve/reject が ValueError を送出）
    if event.get_comment() == "合言葉":
        result = await event.approve()    # 承認（備考付き可：approve(comment="ようこそ")）
    else:
        result = await event.reject()     # 拒否
    if result.get("status") != "ok":
        # 標準レスポンス形式、失敗時は message で理由が説明されます（例：34001 リクエストは期限切れ）
        pass

@request.on_group_request()               # グループ申請 / グループ招待
async def handle_group(event):
    await event.approve()
```

> 承認アクションはアダプターの `Request` DSL を通じて実行されます。戻り値、エラーコード、アダプター実装要件については
> [リクエスト操作仕様](../../standards/request-action-spec.md) を参照してください。汎用レジストラー
> `request.on_request()`（タイプを区別しない）も同様に利用できます。

#### チェーン制御（done / is_processed / is_stopped）

- `done(claim=True)` - 取り込み（デフォルト）または後続の低優先度ハンドラーのブロックのみ
- `is_processed()` - 現在のイベントが取り込み済みかどうか
- `is_stopped()` - 現在のイベント処理チェーンがブロックされているかどうか

取り込みとブロックの完全なセマンティクス（優先度の相互作用、コマンドの取り込み）については、
[イベント処理入門 · チェーン制御：取り込みとブロック](../../getting-started/event-handling.md#チェーン制御取り込みとブロック) を参照してください。

### 返信機能

#### 基本返信
- `reply(content, method="Text", at_sender=False, quote=False, at_users=None, reply_to=None, at_all=False, via=None, **kwargs)` - 汎用返信メソッド
  - `content`: 送信内容（テキスト、URL など）
  - `method`: 送信メソッド、デフォルトは "Text"、"Image"/"Voice"/"Video"/"File" などを選択可
  - `at_sender`: 送信者をメンションするかどうか（user_id を自動抽出）
  - `quote`: 現在のメッセージを引用返信するかどうか（message_id を自動抽出）
  - `at_users`: メンションするユーザーのリスト、例：`["user1", "user2"]`
  - `reply_to`: 返信対象のメッセージ ID を手動指定
  - `at_all`: 全メンバーをメンションするかどうか
  - `**kwargs`: 追加パラメーター（例：Mention メソッドの user_id）

- `reply_ob12(message)` - OneBot12 メッセージセグメントを使用して返信
  - `message`: OneBot12 メッセージセグメントのリストまたは辞書、MessageBuilder と組み合わせて構築可能

#### プラットフォーム機能照会
- `supports(method)` - 現在のプラットフォームが特定の送信メソッド（例：`"Image"`、`"Voice"`）をサポートするか確認、`bool` を返します
- `available_methods()` - 現在のプラットフォームで利用可能なすべての送信メソッドを一覧表示、メソッド名のリストを返します

#### 転送機能

> **注意**：転送機能はアダプターの Send DSL を通じて実装する必要があり、Event ラッパークラス自体は直接的な転送メソッドを提供しません。

```python
# メッセージをグループへ転送
adapter = sdk.adapter.get(event.get_platform())
target_id = event.get_group_id()  # または他のグループIDを指定
await adapter.Send.To("group", target_id).Text(event.get_text())
```

> **マルチアカウントデプロイ**：イベント処理チェーン内での送信は**アカウントの明示的な指定が不要**です——フレームワークはイベントディスパッチのエントリポイントで、イベントをトリガーしたアカウント識別子を呼び出しコンテキストに注入します。`Send` / `Api` / `Request` チェーンで明示的に指定されていない場合、自動的にトリガーイベントのアカウントにバインドされます（明示的な `Using()` が常に優先。タイマーなどのイベントコンテキストがないシナリオではデフォルトアカウントを使用します）。つまり、上の例の転送は「このイベントを受信したアカウント」から送信され、追加のコードは不要です。

#### クロスアカウント重複受信

マルチアカウントが同じグループに在籍している場合、同一の物理メッセージが複数のアカウント経由で1回ずつ受信されることがあります。フレームワークは `ErisPulse.framework.cross_account_policy` に従って処理します（デフォルトは `off` で関連付けなし）：

- `mark`：後続のコピーは通常どおりディスパッチされますが、イベントのトップレベルに `multi_receipt` フィールドが注入されます（`{"event_id": 最初に受信したイベントのid, "self_id": 最初に受信したアカウント}`）——モジュールはこのフィールドを読み取り、応答をスキップするかどうかを自ら判断します
- `drop`：コピーはディスパッチのエントリポイントで直接破棄され、モジュールは感知しません

### 返信待機機能

- `wait_reply(prompt=None, timeout=60.0, callback=None, validator=None, method="Text", pattern=None, regex=None)` - ユーザーの返信を待機
  - `prompt`: プロンプトメッセージ。指定した場合はユーザーに送信されます
  - `timeout`: 待機タイムアウト時間（秒）、デフォルトは60秒
  - `callback`: コールバック関数。返信を受信した際に実行されます
  - `validator`: 検証関数。返信が有効かどうかの検証に使用します
  - `method`: プロンプトメッセージの送信メソッド、デフォルトは "Text"
  - `pattern`: glob ワイルドカード（`*` / `?` / `[seq]`）。返信テキストは一致する必要があり、一致しない場合は待機を続けます
  - `regex`: 正規表現。返信テキストは一致する必要があります（`pattern` と `regex` はどちらか一方）。一致しない場合は待機を続けます
  - ユーザーの返信である Event オブジェクトを返し、タイムアウト時は None を返します

#### インタラクションメソッド

- `confirm(prompt=None, timeout=60.0, yes_words=None, no_words=None, method="Text", hint=False)` - 確認対話
  - `True`（確認）/ `False`（否定）/ `None`（タイムアウト）を返します
  - 中国語・英語の確認語の自動認識を内蔵し、語彙セットのカスタマイズも可能
  - `method`: 送信メソッド、デフォルトは "Text"；"Image"/"Markdown" などの非テキスト方式でのプロンプト送信をサポート
  - `hint`: プロンプトの末尾に確認語ヒント（例：「（はい/いいえ）」）を自動追加するかどうか、デフォルトは False

- `choose(prompt, options, timeout=60.0, method="Text", options_format="auto", merge_prompt=False, placeholder="{options}")` - 選択メニュー
  - `options`: 選択肢テキストのリスト
  - 選択肢のインデックス（0 ベース）を返し、タイムアウト時は `None` を返します
  - `method`: 送信メソッド、デフォルトは "Text"；テキスト系メソッド（Text/Markdown/md/Html/h5）はデフォルトで選択肢を末尾にマージします
  - `options_format`: 選択肢の形式（デフォルト： "auto"、method に応じて内蔵スタイルを自動選択）
    - `"auto"`：Markdown→番号なしリスト（`- 1.選択肢`）、Html→番号付きリスト（`<ol>`）、その他→プレーンテキストリスト
    - `"list"`：1行に1つ、例：``1. 選択肢A\n2. 選択肢B``
    - `"inline"`：1行で表示、例：``1.A | 2.B``
    - `"md"`：Markdown 番号なしリスト
    - `"html"`：Html 番号付きリスト
    - `callable`：カスタム関数。``list[str]`` を受け取り ``str`` を返します
  - `merge_prompt`: 1つのメッセージに強制マージして送信するかどうか、デフォルトは False
    - `False`（デフォルト）：テキスト系メソッドは自動マージ；非テキストメソッドは prompt を先に送信し、その後 Text で選択肢を送信します
    - `True`：method が何であれ 1つのメッセージにマージし、ユーザーが指定した method で送信します
  - `placeholder`: 選択肢を挿入するプレースホルダー、デフォルトは `{options}`；prompt 内でこのマーカーが現れる位置が選択肢テキストに置き換えられ、空文字列に設定した場合は常に末尾に追加されます

- `collect(fields, timeout_per_field=60.0)` - フォーム収集
  - `fields`: フィールドのリスト。各項目は `key`、`prompt`、オプションの `validator`、オプションの `method` を含みます
  - `{key: value}` の辞書を返し、いずれかのフィールドがタイムアウトした場合は `None` を返します
  - 各 field は `method` キーで送信メソッドを指定できます。例えば画像を収集する場合は `{"key": "avatar", "prompt": "アイコンを送信してください", "method": "Image"}` を使用します
  - 各 field はオプションで `options` キー（リスト）をサポートし、指定するとそのフィールドは選択問題になります（choose ロジックを自動呼び出し）
  - 各 field はオプションで `options_format`、`merge_prompt`、`placeholder` キーをサポートし、選択肢の形式、メッセージマージ動作、プレースホルダーを制御します

- `wait_for(event_type="message", condition=None, timeout=60.0)` - 任意のイベントを待機
  - `condition`: フィルター関数。`True` を返した場合にマッチします
  - マッチした Event オブジェクトを返し、タイムアウト時は `None` を返します

- `conversation(timeout=60.0)` - マルチターン対話コンテキストを作成
  - `Conversation` オブジェクトを返し、`say()`/`wait()`/`confirm()`/`choose()`/`collect()`/`stop()` をサポートします
  - `is_active` プロパティは対話がアクティブかどうかを示します

#### インタラクションメソッドの例

**confirm() - 確認対話：**

```python
from ErisPulse.Core.Event import Event
@command("delete", help="データを削除")
async def delete_handler(event: Event):
    if await event.confirm("すべてのデータを削除してもよろしいですか？"):
        sdk.storage.delete("all_data")
        await event.reply("データを削除しました")
    else:
        await event.reply("キャンセルしました")
```

**confirm() - ヒント付き：**

```python
# hint=True を指定するとプロンプトの末尾に「（はい/いいえ）」が追加されます
if await event.confirm("続行しますか？", hint=True):
    await event.reply("続行しました")
# ユーザーに表示される内容：続行しますか？（はい/いいえ）
```

**choose() - 選択メニュー：**

```python
from ErisPulse.Core.Event import Event
@command("color", help="色を選択")
async def color_handler(event: Event):
    choice = await event.choose("色を選択してください：", ["赤", "緑", "青"])
    if choice is not None:
        colors = ["赤", "緑", "青"]
        await event.reply(f"選択した色：{colors[choice]}")
```

**choose() - 選択肢のフォーマットとメッセージマージ：**

```python
# inline 形式：選択肢を同じ行に表示
choice = await event.choose("選択してください：", ["A", "B", "C"], options_format="inline")
# 出力：1.A | 2.B | 3.C

# カスタム形式
choice = await event.choose("選択してください：", ["猫", "犬"],
    options_format=lambda opts: " / ".join(opts))
# 出力：猫 / 犬

# options_format="auto"（デフォルト）：method に応じて内蔵スタイルを自動選択
# Markdown → 番号なしリスト
choice = await event.choose(
    "## 選択してください", ["猫", "犬"],
    method="Markdown",  # auto は自動的に md リストと認識
)
# 出力：
# ## 選択してください
# - 1. 猫
# - 2. 犬

# Html → 番号付きリスト
choice = await event.choose(
    "<h2>選択してください</h2>", ["猫", "犬"],
    method="Html", merge_prompt=True,  # auto は自動的に html リストと認識
)
# 出力：
# <h2>選択してください</h2>
# <ol><li>1. 猫</li><li>2. 犬</li></ol>

# マージモード + プレースホルダー
choice = await event.choose(
    "## 選択してください\n{options}\n番号で返信してください",
    ["猫", "犬"],
    method="Markdown", merge_prompt=True,
)

# カスタムプレースホルダー
choice = await event.choose(
    "選択してください: [choices]",
    ["猫", "犬"],
    placeholder="[choices]",
)
```

**collect() - フォーム収集：**

```python
from ErisPulse.Core.Event import Event
@command("register", help="登録")
async def register_handler(event: Event):
    data = await event.collect([
        {"key": "name", "prompt": "名前を入力してください："},
        {"key": "age", "prompt": "年齢を入力してください：",
         "validator": lambda e: e.get_text().isdigit()},
    ])
    if data:
        await event.reply(f"登録が完了しました！{data['name']}さん、{data['age']}歳")
```

**Text 以外のメソッドでの reply：**

```python
await event.reply("http://example.com/img.jpg", method="Image")
await event.reply("http://example.com/audio.mp3", method="Voice")

from ErisPulse.Core.Event import MessageBuilder
segments = MessageBuilder.text("この画像を見てください：").image("http://example.com/img.jpg").build()
await event.reply_ob12(segments)
```

> Conversation マルチターン対話の完全な使い方は [Conversation マルチターン対話](../../advanced/conversation.md) を参照してください。

### コマンド情報

#### コマンド基本
- `get_command_name()` - コマンド名を取得
- `get_command_args()` - コマンド引数のリストを取得
- `get_command_raw()` - コマンドの元テキストを取得
- `get_command_info()` - 完全なコマンド情報辞書を取得
- `is_command()` - コマンドかどうか

### 生データ

- `get_raw()` - プラットフォームの元イベントデータを取得
- `get_raw_type()` - プラットフォームの元イベントタイプを取得

### プラットフォーム拡張メソッド

アダプターは Event ラッパークラスにプラットフォーム固有のメソッドを登録できます。メソッドは対応するプラットフォームの Event インスタンスでのみ使用可能で、他のプラットフォームからアクセスした場合は `AttributeError` が送出されます。

プラットフォームメソッドは `Event.__getattribute__` を通じて内蔵メソッドより優先して適用されるため、`confirm`、`choose`、`collect`、`wait_reply` などの内蔵インタラクションメソッドをオーバーライドして、プラットフォーム独自の実装（ボタン、カードなど）を提供できます。内蔵実装は `_builtin_*` 関数としてエクスポートされ、オーバーライド側から呼び出せます。

```python
# メールイベント - メールメソッドのみ
event = Event({"platform": "email", "email_raw": {"subject": "Hello"}})
event.get_subject()      # ✅ "Hello" を返す
event.get_chat_type()    # ❌ AttributeError

# Telegram イベント - Telegram メソッドのみ
event = Event({"platform": "telegram", "telegram_raw": {"chat": {"type": "private"}}})
event.get_chat_type()    # ✅ "private" を返す
event.get_subject()      # ❌ AttributeError

# 内蔵メソッドは常に利用可能
event.get_text()         # ✅ どのプラットフォームでも
event.reply("hi")        # ✅ どのプラットフォームでも
```

### 登録済みメソッドの照会

```python
from ErisPulse.Core.Event import get_platform_event_methods

methods = get_platform_event_methods("email")
# ["get_subject", "get_from", ...]
```

### `hasattr` と `dir` のサポート

```python
hasattr(event, "get_subject")   # platform="email" の場合のみ True を返す
"get_subject" in dir(event)     # 同上
```

### クロスプラットフォーム拡張（ワイルドカード）

`register_event_method` と `register_event_mixin` はプラットフォーム名として `"*"` を渡すことをサポートしており、登録されたメソッドは**すべてのプラットフォーム**の Event インスタンスで使用可能になります。AI 対話、コンテキスト管理など、クロスプラットフォームでの再利用が必要な機能に適しています。

```python
from ErisPulse.Core.Event.wrapper import register_event_method

@register_event_method("*")
async def ai_chat(self, prompt: str):
    # self は Event インスタンスで、イベントデータと内蔵メソッドにアクセス可能
    await self.reply(f"AI: {prompt}")
```

登録後、どのプラットフォームのイベントハンドラーからでも `event.ai_chat(...)` を呼び出せます。

メソッド解決の優先順位（高い順）：プラットフォーム固有メソッド → ワイルドカードメソッド → 内蔵メソッド → 辞書キーアクセス。

> アダプター開発者が拡張メソッドを登録する方法については、[イベントシステム API - クロスプラットフォーム拡張](../../api-reference/event-system.md#クロスプラットフォーム拡張ワイルドカード) を参照してください。

## 関連ドキュメント

### モジュール開発を続ける

- [モジュール開発入門](getting-started.md) - 最初のモジュールを作成
- [モジュールベストプラクティス](best-practices.md) - 高品質なモジュールを開発

### インタラクション機能の深掘り

- [Conversation マルチターン対話](../../advanced/conversation.md) - `wait_reply` の上に位置する完全なセッションエンジン（収集、検証、分岐ジャンプ）