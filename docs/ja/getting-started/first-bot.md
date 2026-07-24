# 最初のボットを作成する

このガイドでは、単純な ErisPulse ボットをゼロから作成する方法を説明します。

## ステップ1：プロジェクトの作成

CLI ツールを使用してプロジェクトを初期化します：

```bash
# 対話形式で初期化
epsdk init

# またはクイック初期化
epsdk init -q -n my_first_bot
```

プロンプトに従って設定を完了してください。以下を推奨します：
- プロジェクト名：my_first_bot
- ログレベル：INFO
- サーバー：デフォルト設定
- アダプター：必要なプラットフォームを選択（例: Yunhu）

## ステップ2：プロジェクト構造の確認

初期化後のプロジェクト構造：

```
my_first_bot/
├── config/
│   └── config.toml
├── main.py
└── requirements.txt
```

## ステップ3：最初のコマンドを作成する

`main.py` を開き、簡単なコマンドハンドラーを作成します：

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command

@command("hello", help="挨拶メッセージを送信")
async def hello_handler(event):
    """hello コマンドを処理"""
    user_name = event.get_user_nickname() or "友達"
    await event.reply(f"こんにちは、{user_name}！私はErisPulseボットです。")

@command("ping", help="ボットがオンラインかテスト")
async def ping_handler(event):
    """ping コマンドを処理"""
    await event.reply("Pong！ボットは正常に動作しています。")

async def main():
    """メインエントリ関数"""
    print("ErisPulseを起動中...")
    
    # keep_running=True（デフォルト）：フレームワークは実行中のブロックを維持し、終了シグナル（例: Ctrl+C）が受信されるまで待機します
    await sdk.run(keep_running=True)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### `keep_running` パラメータ

`sdk.run(keep_running)` は、フレームワークが実行中のブロックを維持するかどうかを制御します：

- **`keep_running=True`（デフォルト）**：`run()` は常にブロックされ、終了シグナル（例: Ctrl+C）が受信されるまで待機します。純粋な bot アプリケーションに適しています。
- **`keep_running=False`**：`run()` は初期化が完了するとすぐに返されます。**フレームワークはアンインストールされません** – 既に起動したアダプタ/モジュールはバックグラウンドタスクとして引き続きメッセージイベントを処理し、独自のロジックを続行できます。イベントループが終了し、フレームワークが閉じられるまでです。例えば：

```python
async def main():
    await sdk.run(keep_running=False)   # 初期化後にすぐに返る
    # フレームワークはバックグラウンドで実行中なので、ここで他の作業ができます
    while True:
        await asyncio.sleep(3600)
        print("毎時チェック")
```

> `run()` の2つのモッドの他に、`init()`/`uninit()` によるライフサイクルのマニュアル制御や、アダプタ/ルーター単体の起動停止など、より細かい制御方法があります。詳しくは [起動プロセスとマニュアル制御](../advanced/startup.md) をご覧ください。

## ステップ4：ボットを実行する

```bash
# 通常実行
epsdk run main.py

# 開発モード（ホットリロード対応）
epsdk run main.py --reload
```

## ステップ5：ボットをテストする

チャットプラットフォームでコマンドを送信します：

```
/hello
```

ボットの返信が表示されます。

## コードの説明

### コマンドデコレーター

```python
@command("hello", help="挨拶メッセージを送信")
```

- `hello`：コマンド名。ユーザーは `/hello` で呼び出します。
- `help`：コマンドヘルプ説明。`/help` コマンドに表示されます。

### イベントパラメータ

```python
async def hello_handler(event):
```

`event` パラメータは Event オブジェクトで、以下を含みます：
- メッセージ内容：`event.get_text()`
- 送信者情報：`event.get_user_id()`、`event.get_user_nickname()`
- プラットフォーム情報：`event.get_platform()`
- グループ情報：`event.get_group_id()`
- 原始データ：`event.get_raw()`

> Event オブジェクトのメソッドの詳細については、[Eventラッパークラス詳細](../developer-guide/modules/event-wrapper.md) を参照してください。

### 返信の送信

```python
await event.reply("返信内容")
```

`event.reply()` は、送信者にメッセージを送信する便利なメソッドです。

## 拡張：追加機能の追加

ErisPulse は豊富なイベント処理とデータ処理機能を提供します：

- **メッセージ監視**：`@message.on_message()` を使用して各種メッセージを監視 → [イベント処理の入門](event-handling.md)
- **通知監視**：`@notice.on_friend_add()` などを使用してシステム通知を監視 → [イベント処理の入門](event-handling.md)
- **データ保存**：`sdk.storage.get/set` を使用してデータを永続化 → [共通タスク例](common-tasks.md)

## よくある質問

### コマンドが応答しない？

1. アダプターが正しく設定されているか確認し、`config/config.toml` のアダプターの `status` が `true` であることを確認してください。
2. 端末のログ出力を確認し、エラーメッセージがないか（特に `ERROR` レベルのログ）確認してください。
3. コマンドプレフィックスが正しいか確認してください（デフォルトは `/`）。設定ファイルの `[ErisPulse.event.command]` セクションで確認できます。
4. コマンド名のスペルが正しいか、大文字と小文字の感度設定を確認してください。

### コマンドプレフィックスを変更するには？

`config.toml` に以下を追加します：

```toml
[ErisPulse.event.command]
prefix = "!"
case_sensitive = false
```

### マルチプラットフォームをサポートするには？

ErisPulse は OneBot12 標準を使用して、異なるプラットフォームのイベント形式を統一しています。`@command` および `@message` に登録されたハンドラーは、自動的にすべてのプラットフォームのイベントを受け取ります。`event.get_platform()` を使用して送信元プラットフォームを区別できます：

```python
@command("hello")
async def hello_handler(event):
    platform = event.get_platform()
    
    if platform == "yunhu":
        await event.reply("こんにちは！雲湖からです")
    elif platform == "telegram":
        await event.reply("Hello! From Telegram")
    else:
        await event.reply("こんにちは！")
```

> マルチプラットフォームアダプションのヒントについては、[共通タスク例](common-tasks.md#マルチプラットフォームアダプティブ) を参照してください。

## 次のステップ

- [基本概念](basic-concepts.md) - ErisPulseのコア概念について深く理解する
- [イベント処理の入門](event-handling.md) - 各種イベントの処理を学ぶ
- [共通タスク例](common-tasks.md) - 実用的な機能をマスターする