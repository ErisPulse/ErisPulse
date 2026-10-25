# モジュールテスト（ErisPulse-Testing）

> [!TIP]  
> **この記事を読むタイミング**：独自のモジュールに自動テストを書く場合。必要なければスキップし、他の機能の使用に影響はありません。

[ErisPulse-Testing](https://github.com/ErisPulse/ErisPulse-Testing) は公式のテストツールキットです。  
`TestBot`、テスト用イベントファクトリー、出力メッセージのキャプチャとアサーション機能を提供し、モジュールのテストを普通の pytest のように簡単にできます。

```bash
pip install ErisPulse-Testing
```

> フレームワークの開発期にのみ使用する依存関係、実行時には介入しません。実際のアダプタープラットフォームのスモークテストは、フレームワークリポジトリの `tests/devs/test_adapter.py` を使用してください。

## 速習

```python
import pytest
from ErisPulse.Core.Event.command import command
from ErisPulse_Testing import TestBot, create_command_event

async def test_daily(make_testbot):
    async with make_testbot(prefix="/") as bot:
        @command("daily", cooldown="1d", cooldown_reply="今日已签到")
        async def daily(event):
            await event.reply("签到成功！")

        await bot.dispatch(create_command_event("daily", user_id="123"))
        assert bot.last_reply.text == "签到成功！"

        await bot.dispatch(create_command_event("daily", user_id="123"))
        bot.assert_reply_contains("今天已签到")   # 第二次命中冷却
```

`TestBot` は `async with` で使用することを推奨します：起動時に MockAdapter を登録（すべての出力メッセージをキャプチャ）、イベントの重複除去を無効化、設定の上書きを適用します。終了時にはフレームワークのグローバル状態を自動的にクリーンアップし、テストケース間の汚染を防ぎます。

pytest fixtures として利用可能（インストール後自動的に利用可能）：

- `testbot`：function レベルの標準 TestBot（platform=`test`、前缀 `/`）
- `make_testbot(**kwargs)`：カスタムパラメータのファクトリー（`prefix` / `config` / `platform` / `bot_id` ...）

テストプロジェクトの設定に `asyncio_mode = "auto"`（`[tool.pytest.ini_options]`）を追加することを推奨します。  
または、テストケースに `@pytest.mark.asyncio` を付与してください。

## イベントファクトリー

| 関数 | 説明 |
|------|------|
| `create_message_event(text, user_id=..., group_id=None, ...)` | メッセージイベント；`group_id` が空の場合はプライベートチャット |
| `create_command_event("roll 3", prefix="/")` | コマンドメッセージ（自動的に前缀を追加、既に前缀がある場合は重複しない） |
| `create_notice_event(type, ...)` | 通知イベント（例：`friend_add`） |
| `create_request_event(type, ...)` | 要求イベント（例：友達申請） |
| `create_meta_event("connect", ...)` | meta イベント（`connect` で Bot をオンラインにできる） |

すべてのイベントは uuid を使用して一意の `id` を持つため、フレームワークのイベント重複除去を回避できます。

注意：合成されたイベントには**プラットフォームの元の報文は含まれません**（`event.get_raw()` は空の dict を返します）。グループチャット / プライベートチャットなどの状況を判断するには、`event.is_group_message()` / `event.get_detail_type()` / `event.get_group_id()` などのアクセサを使用してください。raw データを直接読み取らないでください。

## TestBot API

### ディスパッチ

```python
trace = await bot.dispatch(event)          # ディスパッチし、ハンドラが実行されるのを待機して、結果を返す
await bot.dispatch(event, drain=False)     # 交互作用の最初のメッセージ：待機しない（wait_reply ハンドラは長く待機）
await bot.send_message("你好")             # メッセージを送信するショートカット
await bot.reply_as("18", user_id="u1")     # wait_reply ユーザーの返信をシミュレート（自動的に waiter の準備を待つ）
```

`dispatch()` は emit 後にすべての処理中の Task を gather し、返却時に処理が完了します。**テストでは sleep を必要としません**。

### 出力メッセージのアサーション

```python
bot.replies                # 全ての出力メッセージ（SentMessage のリスト）
bot.last_reply.text        # 最後の返信のテキスト
bot.replies_to("123")      # 目標でフィルタリング
bot.clear_replies()        # テスト間の隔離
bot.assert_replied()                       # 出力メッセージが存在する
bot.assert_replied(contains="签到", to="123")
bot.assert_not_replied()                   # 出力メッセージが存在しない
bot.assert_reply_contains("签到成功")       # 指定されたテキストを含む出力メッセージが存在する
await bot.wait_for_reply(timeout=2)        # 異なる返信が現れるのを待つ
```

`SentMessage` のフィールド：`text`（テキストの最初の部分）、`segments`（完全なメッセージセグメント）、  
`target_type` / `target_id` / `bot_id`（送信のコンテキスト）、`has_modifier("at")` など。

### モジュールのロード

```python
await bot.load_module("MyModule")   # 既に登録されたモジュール名（entry-point の発見が完了したフレームワーク sdk.init() が必要）
await bot.load_module(MyModule)     # または BaseModule のサブクラス（自動的に register + load、推奨）
await bot.unload_module("MyModule")
```

`on_load` で登録されたコマンド / イベントハンドラはモジュールに属し、アンロード時に自動的にクリーンアップされます。これにより「アンロード後にコマンドが無効になる」ことを直接アサーションできます。  
注意：文字列形式では**entry-point のスキャンは行われません**（TestBot はフレームワークの発見プロセスを初期化しません）。ソフト依存モジュールをテストする場合は、クラスオブジェクトを直接渡すか、`module.register` した後に名前を渡してください。

### 依存の置換（EP>=2.9.0-dev が必要）

```python
with bot.patch_dependency(get_session, fake_session) as mock:
    await bot.dispatch(create_command_event("query"))
    assert mock.called
```

置換されるのは、コマンド登録表で `Depends(get_session)` で宣言された関数です。`with` の終了時に自動的に元に戻ります。

### 設定の上書き

```python
bot = TestBot(prefix="//", config={
    "ErisPulse.event.command.case_sensitive": False,
    "MyModule.api_key": "test-key",     # モジュールの設定（self.cfg から読み取れる）
})
```

設定はメモリ層に注入され、コマンドの前缀などは即座に更新されます。2点注意：

1. **永続化**：上書きはフレームワークの遅延書き込み戦略（デフォルトで約5秒）に従って cwd の `config/config.toml` に落とされます。テスト対象のプロジェクトリポジトリでは、`config/` を `.gitignore` に追加してください。
2. **モジュール実行時の設定書き戻しとの競合（既知の制限）**：テスト対象のモジュールが `self.cfg = ...`（例：サブスクライブリスト）のように設定を一括で書き戻す場合、この点分の上書きと並存すると、ConfigManager の読み書きの一貫性の問題が発生します。モジュールが一括で読み取る場合、上書きされた値が見えない可能性があります。また、上書きされた値も書き戻し時に一括書き戻しによって上書きされる可能性があります（ErisPulse 2.9.0-dev.2 で修正済み、2.8.x では影響あり）。「実行時に設定を書き戻す」用例では、2.8.x では fixture で一括書き戻し方式で関連設定をリセットすることを推奨します。

## ディスパッチの判定チェーン（「コマンドがなぜ実行されなかったか」を調査する場合；EP>=2.9.0-dev が必要）

`dispatch()` は `DispatchTrace` を返します。これは、今回のディスパッチで経過した各判定ポイントの因果チェーンです：

```python
trace = await bot.dispatch(create_command_event("dailyx", user_id="123"))

trace.verdict        # executed / rejected / dropped / failed / no_match / passed
trace.explain()      # 因果の1行ずつ説明（現在の言語）
trace.command        # 命中のコマンド名（未命中の場合は None）
trace.steps("cooldown")  # フェーズごとに判定記録をフィルタ

trace.assert_executed("daily")  # 実行されたことをアサーション（失敗時は因果チェーンを含む）
trace.assert_rejected()         # 権限系の判定で拒否されたことをアサーション
trace.assert_dropped()          # クールダウンなどで静かにドロップされたことをアサーション
trace.assert_no_match()         # コマンドが一致しなかったことをアサーション
```

判定のカバー範囲：コマンドのテキスト判定、コマンドの一致判定（一致しなかった場合は類似語の提案）、作用域、ユーザー ACL、オーナーのチェック、権限関数、クールダウンによるドロップ、パラメータの解析、実行結果、ミドルウェアによる拒否。

本番環境でも、フレームワーク内に `ErisPulse.Core.Event.trace`（`start_dispatch_trace()` / `format_dispatch_trace()`）が用意されており、判定チェーンの収集とレンダリングが可能です。

## 次のステップ

### テストで「コマンドが実行されなかった」問題が発生した場合

### テストが通って、配信の準備が整った場合

- [モジュールの基本概念](modules/core-concepts.md) — モジュールのアーキテクチャと設定宣言の詳細を補完
- [配布とモジュールストアのガイド](publishing.md) — PyPI とモジュールストアへの配布の完全なプロセス