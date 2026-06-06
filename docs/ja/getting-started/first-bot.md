# 最初のボットを作成する

このガイドでは、ゼロから簡単な ErisPulse ボットを作成する方法について解説します。

## ステップ1：プロジェクトを作成

CLI ツールを使用してプロジェクトを初期化します：

```bash
# 交互式初始化
epsdk init

# または快速初始化
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
    """处理 hello 命令"""
    user_name = event.get_user_nickname() or "朋友"
    await event.reply(f"你好，{user_name}！我是 ErisPulse 机器人。")

@command("ping", help="测试机器人是否在线")
async def ping_handler(event):
    """处理 ping 命令"""
    await event.reply("Pong！机器人运行正常。")

async def main():
    """主入口函数"""
    print("正在初始化 ErisPulse...")
    # 运行 SDK 并且维持运行
    await sdk.run(keep_running=True)

    # 或者
    # await sdk.run(keep_running=False)
    # ...Do Something
    # 可以做你想做的任何事
    # 使用 await sdk.init() 等价于 `sdk.run(keep_running=False)`

    print("ErisPulse 初始化完成！")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

## ステップ4：ボットを実行する

```bash
# 普通运行
epsdk run main.py

# 开发模式（支持热重载）
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
- メッセージ内容：`event.get_text()`
- 送信者情報：`event.get_user_id()`、`event.get_user_nickname()`
- プラットフォーム情報：`event.get_platform()`
- グループ情報：`event.get_group_id()`
- 原始データ：`event.get_raw()`

> 完整な Event オブジェクトメソッドについては [Event 包装クラスの詳細](../developer-guide/modules/event-wrapper.md) を参照してください。

### 返信を送信する

```python
await event.reply("回复内容")
```

`event.reply()` は送信者にメッセージを送るための便利なメソッドです。

## 拡張機能：追加機能の追加

ErisPulse は豊富なイベント処理とデータ処理機能を提供します：

- **メッセージリスナー**：`@message.on_message()` を使用して各種メッセージを監視 → [イベント処理入門](event-handling.md)
- **通知リスナー**：`@notice.on_friend_add()` などの使用でシステム通知を監視 → [イベント処理入門](event-handling.md)
- **データストレージ**：`sdk.storage.get/set` を使用してデータを永続化 → [一般的なタスクの例](common-tasks.md)

## よくある質問

### コマンドに応答がありませんか？

1. アダプタが正しく設定されているか確認します（`config/config.toml` 内でアダプタの `status` が `true` であることを確認してください）
2. 端末のログ出力を確認し、エラーメッセージがないかチェックします（特に `ERROR` レベルのログ）
3. コマンドのプレフィックスが正しいか確認します（デフォルトは `/`）、設定ファイルの `[ErisPulse.event.command]` セクションを確認できます
4. コマンド名のスペルミスがないか確認し、大文字と小文字の区別設定に注意してください

### コマンドのプレフィックスを変更する方法？

`config.toml` に追加します：

```toml
[ErisPulse.event.command]
prefix = "!"
case_sensitive = false
```

### マルチプラットフォームをサポートする方法？

ErisPulse は OneBot12 標準を使用し、異なるプラットフォームのイベント形式を統一しました。`@command` と `@message` で登録されたハンドラーは、すべてのプラットフォームのイベントを受け取ります。`event.get_platform()` を使用してソースプラットフォームを区別できます：

```python
@command("hello")
async def hello_handler(event):
    platform = event.get_platform()
    
    if platform == "yunhu":
        await event.reply("你好！来自云湖")
    elif platform == "telegram":
        await event.reply("Hello! From Telegram")
    else:
        await event.reply("你好！")
```

> マルチプラットフォームアダプティングのテクニックについては、[一般的なタスクの例](common-tasks.md#多平台适配) を参照してください。

## 次のステップ

- [基本概念](basic-concepts.md) - ErisPulse のコア概念を詳しく理解する
- [イベント処理入門](event-handling.md) - 各種イベントの処理を学ぶ
- [一般的なタスクの例](common-tasks.md) - より実用的な機能をマスターする