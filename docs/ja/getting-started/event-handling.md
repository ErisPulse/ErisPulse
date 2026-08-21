# イベント処理の基礎

このガイドでは、ErisPulse 内の各種イベントを処理する方法について説明します。

## イベントタイプの概要

ErisPulse は、以下のイベントタイプをサポートしています。

| イベントタイプ | 説明 | 適用シーン |
|---------|------|---------|
| メッセージイベント | ユーザーから送信されたすべてのメッセージ | チャットボット、コンテンツフィルタリング |
| コマンドイベント | コマンドプレフィックスで始まるメッセージ | コマンド処理、機能への入り口 |
| 通知イベント | システム通知（友達追加、メンバーの変更など） | ウェルカムメッセージ、ステータス通知 |
| リクエストイベント | ユーザーリクエスト（友達リクエスト、グループ招待） | リクエストの自動処理 |
| メタイベント | システムレベルのイベント（接続、ハートビート） | 接続監視、ステータスチェック |

## メッセージイベント処理

> **ヒント**: イベントハンドラーでは `Event` 型アノテーションの使用を推奨します。これにより IDE の自動補完および型チェックのサポートが利用できます。

```python
from ErisPulse.Core.Event import Event  # アノテーション用にイベント型をインポートします
```

### 全メッセージを監听する

```python
from ErisPulse.Core.Event import message, Event

@message.on_message()
async def message_handler(event: Event):
    text = event.get_text()
    user_id = event.get_user_id()
    sdk.logger.info(f"受信した {user_id} のメッセージ: {text}")
```

### プライベートメッセージを監听する

```python
@message.on_private_message()
async def private_handler(event: Event):
    user_id = event.get_user_id()
    await event.reply(f"こんにちは、{user_id}！これはプライベートメッセージです。")
```

### グループメッセージを監听する

```python
@message.on_group_message()
async def group_handler(event: Event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    sdk.logger.info(f"グループ {group_id} の {user_id} からメッセージが送信されました")
```

### @メッセージを監听する

```python
@message.on_at_message()
async def at_handler(event: Event):
    # @されたユーザーリストを取得
    mentions = event.get_mentions()
    await event.reply(f"@したユーザー: {mentions}")

## コマンドイベント処理

### 基本コマンド

```python
from ErisPulse.Core.Event import command

@command("help", help="ヘルプ情報を表示します")
async def help_handler(event):
    help_text = """
利用可能なコマンド：
/help - ヘルプを表示
/ping - 接続をテスト
/info - 情報を表示
    """
    await event.reply(help_text)
```

### コマンド別名

```python
@command(["help", "h"], aliases=["help", "h"], help="ヘルプ情報を表示します")
async def help_handler(event):
    await event.reply("ヘルプ情報...")
```

ユーザーは以下のいずれかの方法で呼び出すことができます：
- `/help`
- `/h`
- `/help`

### コマンド引数

```python
@command("echo", help="メッセージをエコーします")
async def echo_handler(event):
    # コマンド引数を取得
    args = event.get_command_args()
    
    if not args:
        await event.reply("エコーするメッセージを入力してください")
    else:
        await event.reply(f"あなたが言った: {' '.join(args)}")
```

### コマンドグループ

```python
@command("admin.reload", group="admin", help="モジュールを再読み込みします")
async def reload_handler(event):
    await event.reply("モジュールを再読み込みしました")

@command("admin.stop", group="admin", help="ロボットを停止します")
async def stop_handler(event):
    await event.reply("ロボットを停止しました")
```

### コマンド権限

```python
def is_master(event):
    """ユーザーがフレームワークの所有者かをチェックします"""
    master_list = ["user123", "user456"]
    return event.get_user_id() in master_list

@command("master", permission=is_master, help="フレームワーク所有者用コマンド")
async def master_handler(event):
    await event.reply("これはフレームワーク所有者用のコマンドです")
```

### コマンド優先度

```python
# 優先度の数値が大きいほど、実行が早くなります
@message.on_message(priority=10)
async def high_priority_handler(event):
    await event.reply("高優先度のハンドラ")

@message.on_message(priority=1)
async def low_priority_handler(event):
    await event.reply("低優先度のハンドラ")
```

### 並列イベント処理

ErisPulse のイベントシステムは**同優先度では並列、異なる優先度では直列**のスケジューリングモデルを採用しています：

```
イベント到着
    ↓
priority=10 組: [ハンドラC || ハンドラD] 並列 → 結果をマージ
    ↓ (中断されない場合)
priority=0 組: [ハンドラA || ハンドラB] 並列 → 結果をマージ
    ↓
...
```

- **同優先度並列**：優先度が同じ複数のハンドラは同時に実行され、スループットが向上します
- **跨優先度直列**：異なる優先度のグループは順番に実行されます（数値が大きいほど先に実行）、高優先度ハンドラが先に実行されることを保証します
- **Copy-On-Write**：ハンドラが変更を行わない場合、コピーを作成せず、オーバーヘッドをゼロにします
- **競合処理**：同優先度の複数ハンドラが同じフィールドを変更した場合、最後に変更された値が使用され、警告ログが記録されます
- **中断メカニズム**：任意のハンドラが `event.done()`（デフォルト）または `event.done(claim=False)` を呼び出した後、以降の低優先度グループはスキップされます。認領とブロッキングの違いは下記の[「リンク制御：認領とブロッキング」](docs/ja/event-handling.md#リンク制御認領とブロッキング)を参照してください。

```python
# 例：同優先度ハンドラの並列実行
@message.on_message(priority=0)
async def handler_a(event):
    # タスクAを処理
    event['result_a'] = process_a()

@message.on_message(priority=0)
async def handler_b(event):
    # handler_a と並列に実行
    event['result_b'] = process_b()

# 異なる優先度の直列実行
@message.on_message(priority=10)
async def handler_c(event):
    # 最も優先度が高い、最初に実行されます
    pass
```

> **並列上限**：一致するハンドラのすべての Task は**即座に作成**されますが、**同時に実行される数**を制限するための信号量によって制御され、デフォルトの上限は **64**（`ErisPulse.framework.handler_max_concurrency`、ホットアップデート対応）です。上限を超えた Task は信号量上でキューイングされ、前の処理が完了した後に実行されます。イベントのピーク時には、これが「圧力調整弁」となります。
>
> **遅延ログ**：個々のハンドラが **1 秒**以上処理にかかった場合、フレームワークは WARNING ログを出力します（`handler_slow`）。`wait_reply` の待機時間は処理時間から除外され、「返信を待つ」ことで誤って遅延と判定されることはありません。

## スコープフィルタリング：なぜ私のモジュールはメッセージを受け取らないのか

イベントの配信は、**ハンドラ Task の作成前に**スコープフィルタリングが行われます。これは、モジュールの所有者に基づいて `scope.is_allowed` を判定（セッションレベル > Bot レベル > プラットフォームレベル）し、**通過しない場合は静かにスキップ**され、エラーもレスポンスも出ません。

```python
# 仮に config.toml で MyModule を特定のグループにブロックしている場合：
[ErisPulse.scope]
block = { yunhu = { group_123 = ["MyModule"] } }
```

この場合、そのグループのメッセージが到着しても、`MyModule` のコマンドやイベントハンドラは**いずれもスケジュールされません**。これはバグではなく、スコープメカニズムによるものです。モジュールが反応しない問題を調査する際には、まずスコープのバインディングを確認してください。

- 3段階のフィルタリングポイント：アダプターバスレベル（Task の作成前）、Event モジュールレベル（各優先度グループ内）、コマンドレベル（権限チェック前）
- フィルタリングのログは **TRACE** レベルでのみ表示されます（`core.scope.denied`）。デフォルトの INFO レベルでは、何も表示されません。
- フレームワークレベルのハンドラ（例：コマンドディスパッチャー `scope_exempt=True`）は、スコープの影響を受けません。

> スコープの3段階バインディング、ホワイトリスト/ブラックリスト、優先度のオーバーライド、および「default_allow」による暗黙の拒否の意味については、[スコープシステム](../../advanced/scope.md)を参照してください。

## リンク制御：認領とブロック

> [!NOTE]  
> `event.done()` / `event.mark_processed()` の `claim=` / `stop=` パラメータは、この機能には ErisPulse **2.7.1+** が必要です。

ErisPulse では、「認領」と「ブロック」の 2 つの正交的な意味を分離し、`event.done()` で一元的に制御することで、コマンド処理の周囲にログ、監査、権限などの観察層を重ねることが容易になります。

**2 つの概念の正確な定義：**

- **認領（claim）**：イベントがこのプロセッサによって処理されたことをマークします（`_processed` に書き込み）。コマンドディスパッチャは、認領済みのイベントを**スキップ**します——同じメッセージが複数のコマンドプロセッサによって繰り返し処理されるのを防ぎます。典型的なシナリオ：コマンドが正常にマッチした後に認領し、コマンドディスパッチャが再び介入しないようにします。
- **ブロック（stop）**：イベントが**より低い優先度**のプロセッサに伝播するのを阻止します（`_propagation_stopped` に書き込み）。低い優先度のプロセッサ（例：`on_message`）は、このイベントを見なくなります。典型的なシナリオ：高い優先度のプロセッサがイベントを完全に処理したため、低い優先度のプロセッサが再度実行されないようにする。

| `event.done(...)` | 認領 | ブロック | 場面 |
|-------------------|------|------|------|
| `event.done()` | ✔ | ✔ | コマンド / プロセッサが処理完了した際の標準的な方法 |
| `event.done(stop=False)` | ✔ | ✘ | 認領のみ：低い優先度の観察者（ログ / 統計）は引き続きイベントを見ることができます |
| `event.done(claim=False)` | ✘ | ✔ | ブロックのみ（例：ファイアウォール / 限流）：認領は行わず、低い優先度の処理は実行されません |

`event.done(claim=, stop=)` は `event.mark_processed(claim=, stop=)` のエイリアスであり、両者はパラメータと動作が完全に等価です。

```python
@command("help")
async def help_cmd(event):
    event.done()            # 認領 + ブロック（コマンド処理完了の標準的な方法）

@message.on_message(priority=50)
async def observer(event):
    event.done(stop=False)  # 認領のみ：低い優先度の処理が引き続き実行されます（ログ / 統計）

@message.on_message(priority=100)
async def firewall(event):
    if denied(event):
        event.done(claim=False)  # ブロックのみ：低い優先度の処理は実行されず、認領も行いません
```

### コマンドと返信の block 設定

コマンドがマッチした後、または `wait_reply` が返信をマッチした後、デフォルトではイベントの伝播がブロックされます（後方互換性のため）。この設定を変更することで、低い優先度のプロセッサ（ログ / 監査 / 権限）がこれらのメッセージを観察できるようにすることができます。

```toml
[ErisPulse.event.command]
block = false   # コマンドメッセージは低い優先度のプロセッサに引き続き伝播します

[ErisPulse.event.wait_reply]
block = false   # wait_reply によって消費された返信は、低い優先度のプロセッサに引き続き伝播します

## 通知イベント処理

### 親友追加

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event):
    user_id = event.get_user_id()
    nickname = event.get_user_nickname() or "新しい友達"
    await event.reply(f"{nickname}さん、私の友人として追加していただきありがとうございます！")
```

### グループメンバー増加

```python
@notice.on_group_increase()
async def member_increase_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"{user_id}さんがグループ {group_id} に参加しました。")
```

### グループメンバー減少

```python
@notice.on_group_decrease()
async def member_decrease_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"{user_id}さんがグループ {group_id} を退出しました。")

## リクエストイベントの処理

### フレンドリクエスト

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def friend_request_handler(event):
    user_id = event.get_user_id()
    comment = event.get_comment()
    
    sdk.logger.info(f"フレンドリクエストを受信: {user_id}, コメント: {comment}")
    
    # アダプター API を使用してリクエストを処理できます
    # 詳細な実装については各アダプターのドキュメントをご参照ください
```

### グループ招待リクエスト

```python
@request.on_group_request()
async def group_request_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    
    await event.reply(f"グループ {group_id} の招待を受信しました。送信者: {user_id}")

## メタイベント処理

### 接続イベント

```python
from ErisPulse.Core.Event import meta

@meta.on_connect()
async def connect_handler(event):
    platform = event.get_platform()
    sdk.logger.info(f"{platform} プラットフォームに接続しました")

@meta.on_disconnect()
async def disconnect_handler(event):
    platform = event.get_platform()
    sdk.logger.warning(f"{platform} プラットフォームとの接続が切断されました")
```

### ハートビートイベント

```python
@meta.on_heartbeat()
async def heartbeat_handler(event):
    platform = event.get_platform()
    sdk.logger.debug(f"{platform} ハートビート検出")
```

### Bot ステータス照会

アダプタがメタイベントを送信した後、フレームワークは自動的に Bot のステータスを追跡します。いつでも照会できます。

```python
from ErisPulse import sdk

# 特定の Bot がオンラインかどうかをチェック
if sdk.adapter.is_bot_online("telegram", "123456"):
    telegram = sdk.adapter.get("telegram")
    await telegram.Send.To("user", "123456").Text("Bot はオンラインです")

# 現在すべてのオンライン Bot を一覧表示
bots = sdk.adapter.list_bots()
for platform, bot_list in bots.items():
    for bot_id, info in bot_list.items():
        print(f"{platform}/{bot_id}: {info['status']}")

# 完全なステータスサマリーを取得
summary = sdk.adapter.get_status_summary()

## インタラクティブ処理

### `reply` メソッドを使用した返信の送信

`event.reply()` メソッドは、@ 指定や返信などの機能を含むメッセージを送信するために、様々な修飾パラメータをサポートします：

```python
# シンプルな返信
await event.reply("こんにちは")

# 異なるタイプのメッセージを送信
await event.reply("http://example.com/image.jpg", method="Image")  # 画像
await event.reply("http://example.com/voice.mp3", method="Voice")  # 音声

# 個別のユーザーに @ 指定
await event.reply("こんにちは", at_users=["user123"])

# 複数のユーザーに @ 指定
await event.reply("皆さんこんにちは", at_users=["user1", "user2", "user3"])

# メッセージへの返信
await event.reply("返信内容", reply_to="msg_id")

# 全体メンバーに @ 指定
await event.reply("告知", at_all=True)

# 組み合わせ: ユーザーへの @ 指定 + メッセージへの返信
await event.reply("内容", at_users=["user1"], reply_to="msg_id")
```

### ユーザーの返信を待つ

```python
@command("ask", help="ユーザーに問い合わせる")
async def ask_handler(event):
    await event.reply("名前を入力してください：")
    
    # ユーザーの返信を待つ（タイムアウト時間 30 秒）
    reply = await event.wait_reply(timeout=30)
    
    if reply:
        name = reply.get_text()
        await event.reply(f"こんにちは、{name}！")
    else:
        await event.reply("タイムアウトしました。もう一度入力してください。")
```

### 検証付きの返信待機

```python
@command("age", help="年齢を尋ねる")
async def age_handler(event):
    def validate_age(event_data):
        """年齢が有効かどうかを検証"""
        try:
            age = int(event_data.get_text())
            return 0 <= age <= 150
        except ValueError:
            return False
    
    await event.reply("年齢を入力してください (0-150)：")
    
    reply = await event.wait_reply(
        timeout=60,
        validator=validate_age
    )
    
    if reply:
        age = int(reply.get_text())
        await event.reply(f"あなたの年齢は {age} 歳です")
    else:
        await event.reply("入力が無効か、タイムアウトしました")
```

### コールバック付きの返信待機

```python
@command("confirm", help="操作を確認")
async def confirm_handler(event):
    async def handle_confirmation(reply_event):
        text = reply_event.get_text().lower()
        
        if text in ["はい", "yes", "y"]:
            await event.reply("操作が確認されました！")
        else:
            await event.reply("操作がキャンセルされました。")
    
    await event.reply("この操作を実行しますか？(はい/いいえ)")
    
    await event.wait_reply(
        timeout=30,
        callback=handle_confirmation
    )
```

### 確認会話 (confirm)

ユーザーの確認または否定を待ち、組み込みの中国語/英語の確認語を自動的に識別します：

```python
@command("confirm", help="操作を確認")
async def confirm_handler(event):
    if await event.confirm("この操作を実行してもよろしいですか？"):
        await event.reply("確認しました。実行中...")
    else:
        await event.reply("キャンセルされました")

# カスタム確認語
if await event.confirm("続けますか？", yes_words={"go", "続ける"}, no_words={"stop", "停止"}):
    pass
```

### 選択メニュー (choose)

ユーザーはオプション番号またはオプションのテキストで返信できます：

```python
@command("choose", help="選択")
async def choose_handler(event):
    choice = await event.choose(
        "色を選んでください：",
        ["赤色", "緑色", "青色"]
    )
    
    if choice is not None:
        colors = ["赤色", "緑色", "青色"]
        await event.reply(f"あなたが選んだのは：{colors[choice]}")
    else:
        await event.reply("タイムアウトのため選択されませんでした")
```

**マージモード**: `merge_prompt=True` の場合、オプションがプロンプトメッセージに連結され、ユーザーが指定した `method` を使用して1つのメッセージで送信されます：

```python
# マージされたプロンプトとオプションを Markdown で送信
choice = await event.choose(
    "## 色を選んでください\n{options}\n番号を返信してください",
    ["赤色", "緑色", "青色"],
    method="Markdown",
    merge_prompt=True,
)
```

> `{options}` プレースホルダーはオプションの挿入位置を制御します。書かない場合はプロンプトの末尾に追加されます。
> `placeholder` パラメータを使用してプレースホルダーをカスタマイズできます（例：`placeholder="[choices]"`）。
> `options_format="auto"`（デフォルト）は、method に応じてスタイルを自動的に選択します：Markdown → 箇条書き、Html → 番号付きリスト、その他 → 純粋なテキストリスト。
> テキストメソッド（Text/Markdown/Html など）はデフォルトでオプションを末尾にマージします。テキスト以外のメソッド（Image など）はデフォルトで2つのメッセージに分割されます。

### フォーム収集 (collect)

複数ステップでユーザー入力を収集します：

```python
@command("register", help="登録")
async def register_handler(event):
    data = await event.collect([
        {"key": "name", "prompt": "名前を入力してください："},
        {"key": "age", "prompt": "年齢を入力してください：", 
         "validator": lambda e: e.get_text().isdigit()},
        {"key": "email", "prompt": "メールアドレスを入力してください："}
    ])
    
    if data:
        await event.reply(f"登録成功！\n名前：{data['name']}\n年齢：{data['age']}\nメール：{data['email']}")
    else:
        await event.reply("登録のタイムアウトか入力が無効です")
```

### 任意のイベントを待つ (wait_for)

条件を満たす任意のイベント（同一ユーザーに限定されない）を待ちます：

```python
@command("wait_member", help="新しいメンバーを待つ")
async def wait_member_handler(event):
    await event.reply("グループメンバーの参加を待っています...")
    
    evt = await event.wait_for(
        event_type="notice",
        condition=lambda e: e.get_detail_type() == "group_member_increase",
        timeout=120
    )
    
    if evt:
        await event.reply(f"新メンバーへの歓迎：{evt.get_user_id()}")
    else:
        await event.reply("タイムアウトしました")
```

### 多回対話 (conversation)

インタラクティブな多回対話コンテキストを作成します：

```python
@command("survey", help="アンケート調査")
async def survey_handler(event):
    conv = event.conversation(timeout=60)
    
    await conv.say("アンケート調査へのご参加ありがとうございます！")
    
    while conv.is_active:
        reply = await conv.wait()
        
        if reply is None:
            await conv.say("対話がタイムアウトしました、さようなら！")
            break
        
        text = reply.get_text()
        
        if text == "退出":
            await conv.say("さようなら！")
            break
        
        await conv.say(f"あなたは「{text}」と言いました。続けて入力するか、「退出」と入力して終了してください")
```

### 組み込みの確認語

ErisPulse には中国語と英語の確認語のコレクションが組み込まれています：

- **確認語** (`CONFIRM_YES_WORDS`): はい、yes、y、確認、確定、よし、良い、ok、true、はい、うん、行く、同意、問題ありません...
- **否定語** (`CONFIRM_NO_WORDS`): いいえ、no、n、キャンセル、いいえ、しない、できない、cancel、false、間違い、拒否、できません...

## イベントデータへのアクセス

### Event オブジェクトの一般的なメソッド

```python
@command("info")
async def info_handler(event):
    # 基本情報
    event_id = event.get_id()
    event_time = event.get_time()
    event_type = event.get_type()
    detail_type = event.get_detail_type()
    
    # 送信者情報
    user_id = event.get_user_id()
    nickname = event.get_user_nickname()
    
    # メッセージ内容
    message_segments = event.get_message()
    alt_message = event.get_alt_message()
    text = event.get_text()
    
    # グループ情報
    group_id = event.get_group_id()
    
    # ボット情報
    self_id = event.get_self_user_id()
    self_platform = event.get_self_platform()
    
    # 生データ
    raw_data = event.get_raw()
    raw_type = event.get_raw_type()
    
    # プラットフォーム情報
    platform = event.get_platform()
    
    # メッセージタイプの判断
    is_private = event.is_private_message()
    is_group = event.is_group_message()
    is_at = event.is_at_message()
    
    # コマンド情報
    if event.is_command():
        cmd_name = event.get_command_name()
        cmd_args = event.get_command_args()
        cmd_raw = event.get_command_raw()
```

### プラットフォーム拡張メソッド

組み込みメソッドに加え、各プラットフォームアダプターはプラットフォーム固有のメソッドも登録します。これにより、プラットフォーム特有のデータにアクセスするのが容易になります。

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    platform = event.get_platform()

    # プラットフォームに応じて固有メソッドを呼び出す
    if platform == "telegram":
        chat_type = event.get_chat_type()      # Telegram 固有メソッド
    elif platform == "email":
        subject = event.get_subject()           # メール固有メソッド
```

プラットフォームでどのメソッドが登録されているか不明な場合は、登録されているメソッドを確認できます。

```python
from ErisPulse.Core.Event import get_platform_event_methods

methods = get_platform_event_methods("telegram")
# ["get_chat_type", "is_bot_message", ...]
```

> 各プラットフォームで登録されている固有メソッドについては、対応する[プラットフォームドキュメント](../platform-guide/)を参照してください。

## イベント処理のベストプラクティス

### 1. 例外処理

```python
@command("process")
async def process_handler(event):
    try:
        # 業務ロジック
        result = await do_some_work()
        await event.reply(f"結果: {result}")
    except ValueError as e:
        # 予期されるビジネスエラー
        await event.reply(f"パラメータエラー: {e}")
    except Exception as e:
        # 予期しないエラー
        sdk.logger.error(f"処理失敗: {e}")
        await event.reply("処理に失敗しました。しばらく待ってから再試行してください")
```

### 2. ログ記録

```python
@message.on_message()
async def message_handler(event):
    user_id = event.get_user_id()
    text = event.get_text()
    
    sdk.logger.info(f"メッセージを処理中: {user_id} - {text}")
    
    # モジュールの独自ロガーを使用
    from ErisPulse import sdk
    logger = sdk.logger.get_child("MyHandler")
    logger.debug(f"詳細デバッグ情報")
```

### 3. 条件処理

```python
@message.on_message(priority=0)
async def conditional_handler(event):
    """条件処理 - ハンドラー内で判断"""
    # 特定のユーザーからのメッセージのみ処理
    if event.get_user_id() in ["bot1", "bot2"]:
        return
    
    # 特定のキーワードを含むメッセージのみ処理
    if "キーワード" not in event.get_text():
        return
    
    await event.reply("条件を満たしました、メッセージを処理します")

## 次のステップ

- [一般的なタスクの例](common-tasks.md) - 基本機能の実装を学ぶ（メッセージ送信の高度な機能：リトライ/タイムアウト/バッチを含む）
- [プラットフォームの機能ガイド](../platform-guide/README.md) - Send DSL のチェーン送信、送信ルール、バッチ構築の完全な説明
- [Event ラッパークラスの詳細](../developer-guide/modules/event-wrapper.md) - Event オブジェクトについて深く理解する
- [ユーザーガイド](../user-guide/) - 設定とモジュール管理について理解する