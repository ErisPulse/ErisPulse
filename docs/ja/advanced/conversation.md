# Conversation 多輪対話

`Conversation` クラスは、同一セッション内で複数回の対話を行うための便利なメソッドを提供し、誘導型操作、情報収集、対話型の質問応答などのシナリオに適しています。

## 対話の作成

`Event` オブジェクトの `conversation()` メソッドを使用して作成します：

```python
from ErisPulse.Core.Event import command

@command("quiz")
async def quiz_handler(event):
    conv = event.conversation(timeout=30)

    await conv.say("🎮 知識クイズへようこそ！")

    answer = await conv.choose("第一問：Python の生みの親は誰ですか？", [
        "Guido van Rossum",
        "James Gosling",
        "Dennis Ritchie",
    ])

    if answer is None:
        await conv.say("タイムアウトしました。また次回お試しください！")
        return

    if answer == 0:
        await conv.say("正解です！")
    else:
        await conv.say("不正解です。正解は Guido van Rossum です。")

    conv.stop()
```

## コア API

### say(content, **kwargs)

メッセージを送信し、`self` を返してメソッドチェーンを可能にします：

```python
await conv.say("第一行").say("第二行").say("第三行")
```

送信方法を指定することもできます：

```python
await conv.say("https://example.com/image.jpg", method="Image")
```

### wait(prompt=None, timeout=None)

ユーザーからの返信を待ち、`Event` オブジェクトまたは `None`（タイムアウト）を返します：

```python
# 単純に待機
resp = await conv.wait()
if resp:
    text = resp.get_text()

# プロンプトを送信して待機
resp = await conv.wait(prompt="あなたの名前を入力してください：")

# カスタムタイムアウトを使用（対話のデフォルトタイムアウトを上書き）
resp = await conv.wait(prompt="10秒以内に返信してください：", timeout=10)
```

### confirm(prompt=None, **kwargs)

ユーザーの確認（はい/いいえ）を待ち、`True` / `False` / `None`（タイムアウト）を返します：

```python
result = await conv.confirm("すべてのデータを削除してもよろしいですか？")
if result is True:
    await conv.say("削除しました。")
elif result is False:
    await conv.say("キャンセルしました。")
else:
    await conv.say("タイムアウトしました。")
```

認識される確認用語：`はい/yes/y/確認/確定/好/ok/true/対/うん/行/同意/問題ない/可能/当然...`

認識される否定用語：`否/no/n/キャンセル/不/不要/行かない/cancel/false/間違った/違った/別/拒否...`

### choose(prompt, options, **kwargs)

ユーザーが選択肢から選択するのを待ち、選択肢のインデックス（0ベース）または `None` を返します：

```python
choice = await conv.choose("色を選択してください：", ["赤", "緑", "青"])
if choice is not None:
    colors = ["赤", "緑", "青"]
    await conv.say(f"選択した色は {colors[choice]} です。")
```

ユーザーは番号（`1`/`2`/`3`）または選択肢のテキスト（`赤`）を入力して選択できます。

`options_format="auto"`（デフォルト）は、method に応じて自動的に組み込みのスタイルを選択します：Markdown→箇条書き、Html→番号付きリスト、その他→プレーンテキストリスト。
`"list"`、`"inline"`、`"md"`、`"html"`、またはカスタム関数もサポートされています。

`merge_prompt=True` を使用して、プロンプトと選択肢を1つのメッセージに統合し、プレースホルダで選択肢の挿入位置を制御できます（デフォルトは `{options}`、`placeholder` でカスタマイズ可能）：

```python
choice = await conv.choose(
    "## 選択してください\n{options}",
    ["選択肢A", "選択肢B"],
    method="Markdown",
    merge_prompt=True,
)

# カスタムプレースホルダ
choice = await conv.choose(
    "選択してください: [choices]",
    ["選択肢A", "選択肢B"],
    placeholder="[choices]",
)
```

### collect(fields, **kwargs)

複数ステップで情報を収集し、データ辞書または `None` を返します：

```python
data = await conv.collect([
    {"key": "name", "prompt": "名前を入力してください"},
    {"key": "age", "prompt": "年齢を入力してください",
     "validator": lambda e: e.get("alt_message", "").strip().isdigit(),
     "retry_prompt": "年齢は数字で入力してください。"},
    {"key": "city", "prompt": "都市を入力してください"},
])

if data:
    await conv.say(f"登録完了！\n名前: {data['name']}\n年齢: {data['age']}\n都市: {data['city']}")
else:
    await conv.say("登録が中断されました。")
```

フィールドの設定：

| パラメータ | 説明 | デフォルト値 |
|------|------|--------|
| `key` | フィールドのキー名（必須） | - |
| `prompt` | プロンプトメッセージ | `"{key} を入力してください"` |
| `validator` | 関数を受け取り、bool を返す検証関数 | 無し |
| `retry_prompt` | 検証失敗時の再入力プロンプト | `"入力が無効です。再度入力してください。"` |
| `max_retries` | 最大再試行回数 | 3 |
| `condition` | 条件関数、既に収集されたデータの辞書を受け取り、bool を返す | 無し |

**条件付きフィールド**：`condition` を使用して、条件が満たされた場合にのみフィールドを収集する動的フォームを作成できます：

```python
data = await conv.collect([
    {"key": "has_car", "prompt": "車をお持ちですか？（はい/いいえ）"},
    {"key": "car_brand", "prompt": "車のブランドを入力してください。",
     "condition": lambda d: d.get("has_car", "").lower() in ("はい", "yes", "y")},
])
```

### stop()

手動で対話を終了し、`is_active` を `False` に設定します：

```python
conv.stop()
```

### is_active

対話がアクティブかどうかを返します：

```python
if conv.is_active:
    await conv.say("対話はまだ進行中です。")
```

## アクティブ状態の管理

```mermaid
stateDiagram-v2
    state "アクティブ" as active
    state "非アクティブ" as inactive
    [*] --> active: event.conversation()
    active --> active: say / wait / confirm / choose / collect
    active --> inactive: stop()
    active --> inactive: wait() タイムアウト
    active --> inactive: collect() タイムアウトまたは再試行回数超過
    inactive --> [*]
```

以下の状況で対話は自動的に非アクティブになります：

1. `stop()` メソッドを呼び出した場合
2. `wait()` がタイムアウトして `None` を返した場合
3. `collect()` が何らかのステップでタイムアウトまたは再試行回数を超過した場合

非アクティブになった後、`wait`/`confirm`/`choose`/`collect` のすべてのインタラクションメソッドは即座に `None` を返し、ユーザーからの入力を待続しません。

## 分岐とジャンプ

### @conv.branch(name) デコレータ

`branch()` を使用して対話の分岐を登録し、`goto()` で分岐間をジャンプできます：

```python
@command("menu")
async def menu_handler(event):
    conv = event.conversation(timeout=60)

    @conv.branch("main")
    async def main_menu():
        await conv.say("=== メインメニュー ===\n1. 本人情報\n2. 設定\n3. 終了")
        resp = await conv.wait()
        if resp is None:
            return
        text = resp.get_text().strip()
        if text == "1":
            await conv.goto("profile")
        elif text == "2":
            await conv.goto("settings")
        elif text == "3":
            await conv.say("さようなら！")
            conv.stop()

    @conv.branch("profile")
    async def profile():
        await conv.say("=== 本人情報 ===\n名前: Alice\n0. 戻る")
        resp = await conv.wait()
        if resp and resp.get_text().strip() == "0":
            await conv.goto("main")

    @conv.branch("settings")
    async def settings():
        await conv.say("=== 設定 ===\n1. 通知のオン/オフ\n0. 戻る")
        resp = await conv.wait()
        if resp and resp.get_text().strip() == "0":
            await conv.goto("main")

    await conv.start()  # 最初に登録された分岐から開始
```

### conv.start(name=None)

対話を開始します。デフォルトでは最初に登録された分岐から開始します：

```python
await conv.start()          # 最初の分岐から開始
await conv.start("settings") # 指定された分岐から開始
```

## コンテキストと永続化

### conv.context

各対話インスタンスには `context` 辞書が内蔵されており、分岐間で状態を共有するために使用できます：

```python
@conv.branch("step1")
async def step1():
    conv.context["username"] = resp.get_text().strip()
    await conv.goto("step2")

@conv.branch("step2")
async def step2():
    name = conv.context.get("username", "不明")
    await conv.say(f"こんにちは、{name} さん！")
```

### save() / resume() / clear_saved()

対話は永続化が可能で、タイムアウトや中断後に再開できます：

```python
# 対話の状態を保存（通常は手動で呼び出す必要はありません。下記の「自動チェックポイント」を参照）
await conv.save()

# ... その後、同じセッションで再開 ...
conv2 = event.conversation()
if await conv2.resume():
    await conv2.say("戻ってきました！以前の対話を再開します。")
else:
    await conv2.say("以前の対話は見つかりませんでした。")

# 保存された対話を削除
await conv.clear_saved()
```

ストレージのキーにはターゲットの次元が含まれます（`conversation:{platform}:{user_id}:{target_id}`）。同じユーザーが異なるセッションで対話しても、互いに上書きされることはありません。`resume()` 時に、`target` を含まない旧形式のアーカイブは自動的に移行されます。

## 自動チェックポイントと再起動後の復元

### 自動アーカイブ

フレームワークは以下のタイミングでチェックポイントを自動的に維持します。通常、`save()` を手動で呼び出す必要はありません：

| タイミング | 行動 |
|------|------|
| `goto()` / `start()` で分岐をジャンプしたとき | 自動的に保存（現在の分岐 + context） |
| `stop()` / `wait()` タイムアウト / `collect()` 失敗したとき | 自動的にクリア（対話の終端状態） |

### チェックポイントのTTL

アーカイブにはタイムスタンプが付いており、`ErisPulse.interaction.checkpoint_ttl`（デフォルト 24 時間）を超えるアーカイブは、復元時に自動的に破棄されます：

```toml
[ErisPulse.interaction]
checkpoint_ttl = 86400  # 秒
```

### 再起動後の自動復元

フレームワークが再起動した後、進行中の対話（メモリ中の待機コルーチン）は失われますが、チェックポイントは残っています。`register_resume_handler` を使用して**復元工場**を登録することで、フレームワークは再起動後にそのセッションの最初のメッセージを受け取ったときに自動的に対話を継続します：

```python
from ErisPulse.Core.Event.wrapper import Conversation

@Conversation.register_resume_handler()  # platform="onebot11" を渡してプラットフォームを限定することも可能
def make_conversation(event) -> Conversation:
    # 工場の役割：対話を再構築し、すべての分岐を再登録する
    conv = event.conversation(timeout=60)

    @conv.branch("menu")
    async def menu(conv, event):
        ...

    return conv
```

登録後、再起動前に `menu` 分岐にいたユーザーが最初のメッセージを送信すると、フレームワークは自動的に：context を復元 → そのメッセージを認証 → 保存された分岐から対話を継続します。工場を登録していない場合、このメカニズムはゼロコストです。

### 復元は即座に制御を引き継ぐ

`resume()` が成功した場合、フレームワークは自動的に以下の2つのことを行います：

1. **セッションの制御権の獲得**：自動的にこのセッションの排他リースを取得します。他のモジュールは `sdk.interaction.get_owner_of(event)` を使用して「このユーザーが対話中にいる」ことを感知できます。セッションが他のモジュールによって占有されている場合、復元は失敗し（`False` を返します）、2つの対話が競合することを防ぎます。
2. **履歴の持ち込み**：会話の受信箱から最近の10件のメッセージを `conv.recent_history` に取得します（AI モジュールが復元された後、LLM のコンテキストが途切れません）。`resume(with_history=0)` を使用してこの機能を無効にできます。

```python
if await conv.resume(with_history=20):
    for m in conv.recent_history:
        print(m["role"], ":", m["text"])
```

### 手動での復元（自動メカニズムを使わない場合）

```python
@command("continue")
async def continue_handler(event):
    conv = event.conversation()
    # ... 分岐の登録 ...
    if await conv.resume():
        conv.goto(conv.get_current_branch())
```

## 一般的なフロー・パターン

### 誘導型登録

```python
@command("register")
async def register_handler(event):
    conv = event.conversation(timeout=60)

    await conv.say("ようこそ登録へ！")

    data = await conv.collect([
        {"key": "username", "prompt": "ユーザー名を入力してください（3〜20文字）",
         "validator": lambda e: 3 <= len(e.get_text().strip()) <= 20},
        {"key": "email", "prompt": "メールアドレスを入力してください",
         "validator": lambda e: "@" in e.get_text() and "." in e.get_text(),
         "retry_prompt": "メールアドレスの形式が正しくありません。再度入力してください。"},
    ])

    if not data:
        await event.reply("登録がキャンセルされました。")
        return

    confirmed = await conv.confirm(
        f"登録情報を確認しますか？\nユーザー名: {data['username']}\nメールアドレス: {data['email']}"
    )

    if confirmed:
        await conv.say("✅ 登録完了！")
    else:
        await conv.say("❌ 登録がキャンセルされました。")
```

### ループ対話

```python
@command("chat")
async def chat_handler(event):
    conv = event.conversation(timeout=120)
    await conv.say("対話モードに入りました。メッセージ「終了」で終了します。")

    while conv.is_active:
        resp = await conv.wait()
        if resp is None:
            await conv.say("タイムアウトしました。対話が終了します。")
            break

        text = resp.get_text().strip()

        if text == "終了":
            await conv.say("さようなら！")
            conv.stop()
        elif text == "ヘルプ":
            await conv.say("利用可能なコマンド：終了、ヘルプ、状態")
        elif text == "状態":
            await conv.say("対話はアクティブです。")
        else:
            await conv.say(f"入力内容：{text}")
```

## 関連文書

- [Event 包装クラス](../developer-guide/modules/event-wrapper.md) - Event オブジェクトのすべてのメソッド
- [イベント処理の入門](../getting-started/event-handling.md) - イベント処理の基礎