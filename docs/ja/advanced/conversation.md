# Conversation 多層会話

`Conversation` クラスは、同じセッション内での多層対話に便利なメソッドを提供し、導入型操作、情報収集、対話形式の質問応答などのシナリオの実装に適しています。

## 会話の作成

`Event` オブジェクトの `conversation()` メソッドを通じて作成します：

```python
from ErisPulse.Core.Event import command

@command("quiz")
async def quiz_handler(event):
    conv = event.conversation(timeout=30)

    await conv.say("🎮 知識クイズにご参加ください！")

    answer = await conv.choose("最初の質問：Pythonの作成者は誰ですか？", [
        "Guido van Rossum",
        "James Gosling",
        "Dennis Ritchie",
    ])

    if answer is None:
        await conv.say("タイムアウトしました。またしましょう！")
        return

    if answer == 0:
        await conv.say("正解です！")
    else:
        await conv.say("不正解です。正解は Guido van Rossum です")

    conv.stop()
```

## コア API

### say(content, **kwargs)

メッセージを送信し、`self` を返してチェーンメソッド呼び出しをサポートします：

```python
await conv.say("1行目").say("2行目").say("3行目")
```

送信メソッドを指定することもできます：

```python
await conv.say("https://example.com/image.jpg", method="Image")
```

### wait(prompt=None, timeout=None)

ユーザーの返信を待ち、`Event` オブジェクトまたは `None`（タイムアウト）を返します：

```python
# 簡単に待つ
resp = await conv.wait()
if resp:
    text = resp.get_text()

# プロンプトを送信して待つ
resp = await conv.wait(prompt="お名前を入力してください：")

# カスタムタイムアウトを使用（会話のデフォルトを上書き）
resp = await conv.wait(prompt="10秒以内に返信してください：", timeout=10)
```

### confirm(prompt=None, **kwargs)

ユーザーの確認（はい/いいえ）を待ち、`True` / `False` / `None`（タイムアウト）を返します：

```python
result = await conv.confirm("すべてのデータを削除してもよろしいですか？")
if result is True:
    await conv.say("削除しました")
elif result is False:
    await conv.say("キャンセルしました")
else:
    await conv.say("タイムアウトで返信がありません")
```

組み込みで認識される確認用語：`是/yes/y/确认/确定/好/ok/true/对/嗯/行/同意/没问题/可以/当然...`

組み込みで認識される否定用語：`否/no/n/取消/不/不要/不行/cancel/false/错/不对/别/拒绝...`

### choose(prompt, options, **kwargs)

ユーザーがオプションから選択するのを待ち、オプションのインデックス（0から始まる）または `None` を返します：

```python
choice = await conv.choose("色を選択してください：", ["赤", "緑", "青"])
if choice is not None:
    colors = ["赤", "緑", "青"]
    await conv.say(f"あなたは {colors[choice]} を選びました")
```

ユーザーは番号（`1`/`2`/`3`）またはオプションのテキスト（`赤`）で選択できます。

### collect(fields, **kwargs)

複数ステップで情報を収集し、データディクショナリまたは `None` を返します：

```python
data = await conv.collect([
    {"key": "name", "prompt": "お名前を入力してください"},
    {"key": "age", "prompt": "年齢を入力してください",
     "validator": lambda e: e.get("alt_message", "").strip().isdigit(),
     "retry_prompt": "年齢は数値である必要があります。再入力してください"},
    {"key": "city", "prompt": "都市を入力してください"},
])

if data:
    await conv.say(f"登録成功！\n名前: {data['name']}\n年齢: {data['age']}\n都市: {data['city']}")
else:
    await conv.say("登録処理が中断されました")
```

フィールド設定：

| パラメータ | 説明 | デフォルト値 |
|------|------|--------|
| `key` | フィールドキー名（必須） | - |
| `prompt` | プロンプトメッセージ | `"請输入 {key}"` |
| `validator` | バリデーション関数（Event を受け取り、bool を返す） | なし |
| `retry_prompt` | バリデーション失敗時の再試行プロンプト | `"输入无效，请重新输入"` |
| `max_retries` | 最大再試行回数 | 3 |
| `condition` | 条件関数（既に収集されたデータ dict を受け取り、bool を返す） | なし |

**条件フィールド**：`condition` を使用すると動的なフォームを実現でき、条件が満たされた場合にのみそのフィールドを収集します：

```python
data = await conv.collect([
    {"key": "has_car", "prompt": "車を持っていますか？（はい/いいえ）"},
    {"key": "car_brand", "prompt": "車の型式を入力してください",
     "condition": lambda d: d.get("has_car", "").lower() in ("是", "yes", "y")},
])
```

### stop()

手動で会話を終了し、`is_active` を `False` に設定します：

```python
conv.stop()
```

### is_active

会話がアクティブ状態にあるかどうか：

```python
if conv.is_active:
    await conv.say("会話はまだ進行中です")
```

## アクティブ状態の管理

会話は以下の場合、自動的に非アクティブ状態になります：

1. `stop()` メソッドが呼び出された場合
2. `wait()` がタイムアウトして `None` を返した場合
3. `collect()` がいずれかのステップでタイムアウトまたは再試行回数が尽き、`None` を返した場合

非アクティブ状態になった後、すべての対話メソッド（`wait`/`confirm`/`choose`/`collect`）は `None` を即座に返し、ユーザー入力の待機を継続しません。

## 分岐と移動

### @conv.branch(name) デコレータ

`branch()` で会話の分岐を登録し、`goto()` で分岐間を移動します：

```python
@command("menu")
async def menu_handler(event):
    conv = event.conversation(timeout=60)

    @conv.branch("main")
    async def main_menu():
        await conv.say("=== メインメニュー ===\n1. 個人情報\n2. 設定\n3. 退出")
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
        await conv.say("=== 個人情報 ===\n名前: Alice\n0. 戻る")
        resp = await conv.wait()
        if resp and resp.get_text().strip() == "0":
            await conv.goto("main")

    @conv.branch("settings")
    async def settings():
        await conv.say("=== 設定 ===\n1. 通知のON/OFF\n0. 戻る")
        resp = await conv.wait()
        if resp and resp.get_text().strip() == "0":
            await conv.goto("main")

    await conv.start()  # 最初に登録された分岐から開始
```

### conv.start(name=None)

会話を開始し、デフォルトでは最初に登録された分岐から始まります：

```python
await conv.start()          # 最初の分岐から開始
await conv.start("settings") # 指定した分岐から開始
```

## コンテキストと永続化

### conv.context

各会話インスタンスは組み込みの `context` 辞書を持ち、分岐間で状態を共有するために使用します：

```python
@conv.branch("step1")
async def step1():
    conv.context["username"] = resp.get_text().strip()
    await conv.goto("step2")

@conv.branch("step2")
async def step2():
    name = conv.context.get("username", "不明")
    await conv.say(f"こんにちは、{name}！")
```

### save() / resume() / clear_saved()

会話は永続化をサポートしており、タイムアウトや中断後に復元できます：

```python
# 会話状態を保存
conv_id = conv.save()
# conv_id = "user_123_group_456"  # ユーザーとグループに基づいて自動生成

# ... 後で同じセッションで復元 ...
conv2 = event.conversation()
if conv2.resume():
    await conv2.say("おかえりなさい！前の会話を続けます")
else:
    await conv2.say("以前の会話が見つかりませんでした")

# 保存された会話をクリア
conv.clear_saved()
```

## 典型的なワークフロー

### 導入型登録

```python
@command("register")
async def register_handler(event):
    conv = event.conversation(timeout=60)

    await conv.say("登録へようこそ！")

    data = await conv.collect([
        {"key": "username", "prompt": "ユーザー名を入力してください（3-20文字）",
         "validator": lambda e: 3 <= len(e.get_text().strip()) <= 20},
        {"key": "email", "prompt": "メールアドレスを入力してください",
         "validator": lambda e: "@" in e.get_text() and "." in e.get_text(),
         "retry_prompt": "メールアドレスの形式が正しくありません。再入力してください"},
    ])

    if not data:
        await event.reply("登録がキャンセルされました")
        return

    confirmed = await conv.confirm(
        f"登録情報を確認しますか？\nユーザー名: {data['username']}\nメール: {data['email']}"
    )

    if confirmed:
        await conv.say("✅ 登録成功！")
    else:
        await conv.say("❌ 登録がキャンセルされました")
```

### ループ対話

```python
@command("chat")
async def chat_handler(event):
    conv = event.conversation(timeout=120)
    await conv.say("対話モードに入ります。「退出」で終了")

    while conv.is_active:
        resp = await conv.wait()
        if resp is None:
            await conv.say("タイムアウト、対話を終了")
            break

        text = resp.get_text().strip()

        if text == "退出":
            await conv.say("さようなら！")
            conv.stop()
        elif text == "帮助":
            await conv.say("使用可能なコマンド：退出、帮助、状态")
        elif text == "状态":
            await conv.say("対話はアクティブです")
        else:
            await conv.say(f"あなたは「{text}」と言いました")
```

## 関連ドキュメント

- [Event 包装クラス](../developer-guide/modules/event-wrapper.md) - Event オブジェクトのすべてのメソッド
- [イベント処理入門](../getting-started/event-handling.md) - イベント処理の基礎