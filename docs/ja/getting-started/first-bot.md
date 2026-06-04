# 最初のボットを作成する

このガイドでは、ゼロから簡単な ErisPulse ボットを作成する方法について解説します。

## ステップ1：プロジェクトを作成

CLI ツールを使用してプロジェクトを初期化します：

```bash
# 対話形式での初期化
epsdk init

# またはクイック初期化
epsdk init -q -n my_first_bot
```

プロンプトに従って設定を完了し、以下を選択することを推奨します：
- プロジェクト名：my_first_bot
- ログレベル：INFO
- サーバー：デフォルト設定
- アダプタ：必要なプラットフォームを選択してください（例：Yunhu）

## ステップ2：プロジェクト構造を確認する

初期化後のプロジェクト構造：

```
my_first_bot/
├── config/
│   └── config.toml
├── main.py
└── requirements.txt
```

## ステップ3：最初のコマンドを記述する

`main.py` を開き、単純なコマンドハンドラーを記述します：

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command

@command("hello", help="发送问候消息")
async def hello_handler(event):
    """hello コマンドを処理します"""
    user_name = event.get_user_nickname() or "朋友"
    await event.reply(f"こんにちは、{user_name}！私は ErisPulse ボットです。")

@command("ping", help="测试机器人是否在线")
async def ping_handler(event):
    """ping コマンドを処理します"""
    await event.reply("Pong！ボットは正常に動作しています。")

async def main():
    """メインのエントリーポイント関数"""
    print("ErisPulse を初期化しています...")
    # SDK を実行し、実行し続けます
    await sdk.run(keep_running=True)

    # または
    # await sdk.run(keep_running=False)
    # ...Do Something
    # 想いのまま何でもできます
    # `sdk.run(keep_running=False)` と等価です

    print("ErisPulse 初期化完了！")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

## ステップ4：ボットを実行する

```bash
# 通常実行
epsdk run main.py

# 開発モード（ホットリロードをサポート）
epsdk run main.py --reload
```

## ステップ5：ボットをテストする

チャットプラットフォームでコマンドを送信します：

```
/hello
```

ボットからの返信を受け取るはずです。

## コードの説明

### コマンドデコレータ

```python
@command("hello", help="发送问候消息")
```

- `hello`：コマンド名。ユーザーは `/hello` で呼び出します
- `help`：コマンドのヘルプ説明。`/help` コマンド内で表示されます

### イベントパラメータ

```python
async def hello_handler(event):
```

`event` パラメータは Event オブジェクトであり、以下を含みます：
- メッセージ内容
- 送信者情報
- プラットフォーム情報
- など...

### 返信を送信する

```python
await event.reply("回复内容")
```

`event.reply()` は送信者にメッセージを送るための便利なメソッドです。

## 拡張機能の追加

### メッセージリスナーの追加

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def message_handler(event):
    """すべてのメッセージを監聴します"""
    text = event.get_text()
    if "你好" in text:
        await event.reply("こんにちは！")
```

### 通知リスナーの追加

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event):
    """フレンド追加イベントを監視します"""
    user_id = event.get_user_id()
    await event.reply(f"フレンドとして追加していただきありがとうございます！あなたのIDは {user_id} です")
```

### ストレージシステムを使用する

```python
# カウンターを取得
count = sdk.storage.get("hello_count", 0)

# カウンターを増やす
count += 1
sdk.storage.set("hello_count", count)

await event.reply(f"{count} 回目の hello コマンドの実行です。")
```

## よくある質問

### コマンドに応答がありませんか？

1. アダプタが正しく設定されているか確認します
2. ログ出力を確認し、エラーがないかチェックします
3. コマンドのプレフィックスが正しいか確認します（デフォルトは `/`）

### コマンドのプレフィックスを変更する方法？

`config.toml` に追加します：

```toml
[ErisPulse.event.command]
prefix = "!"
case_sensitive = false
```

### マルチプラットフォームをサポートする方法？

コードは、すべての読み込まれたプラットフォームアダプタを自動的に適合させます。ロジックが互換性を持つように確認するだけです：

```python
@command("hello")
async def hello_handler(event):
    platform = event.get_platform()
    
    if platform == "yunhu":
        await event.reply("こんにちは！Yunhuよりおかえりなさい")
    elif platform == "telegram":
        await event.reply("Hello! From Telegram")
```

## 次のステップ

- [基本概念](basic-concepts.md) - ErisPulse のコア概念を詳しく理解する
- [基本概念](basic-concepts.md) - ErisPulse のコア概念を詳しく理解する
- [イベント処理入門](event-handling.md) - 各種イベントの処理を学ぶ
- [一般的なタスクの例](common-tasks.md) - より実用的な機能をマスターする