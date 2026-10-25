# モジュールテスト（ErisPulse-Testing）

> [!TIP]  
> **この記事を読むタイミング**：独自のモジュールに自動テストを書くとき。不要であれば飛ばしても、他の機能に影響はありません。

[ErisPulse-Testing](https://github.com/ErisPulse/ErisPulse-Testing) は公式のテストツールキットです。  
`TestBot`、テストイベントファクトリー、出力メッセージのキャプチャとアサーション機能を提供し、モジュールのテストを通常の pytest と同じように簡単に実現します。

```bash
pip install ErisPulse-Testing
```

> フレームワークの開発期にのみ使用するツールであり、実行時には一切介入しません。実際のアダプタープラットフォームでの冒煙テストは、フレームワークリポジトリの `tests/devs/test_adapter.py` を使用してください。

## 快速开始

```python
import pytest
from ErisPulse.Core.Event.command import command
from ErisPulse_Testing import TestBot, create_command_event

async def test_daily(make_testbot):
    async with make_testbot(prefix="/") as bot:
        @command("daily", cooldown="1d", cooldown_reply="今天已签到")
        async def daily(event):
            await event.reply("签到成功！")

        await bot.dispatch(create_command_event("daily", user_id="123"))
        assert bot.last_reply.text == "签到成功！"

        await bot.dispatch(create_command_event("daily", user_id="123"))
        bot.assert_reply_contains("今天已签到")   # 第二次命中冷却
```

`TestBot` は `async with` を推奨して使用してください：起動時に MockAdapter を登録し、すべての出力メッセージをキャプチャし、イベントの重複防止を無効化し、設定の上書きを適用します。終了時にはフレームワークのグローバル状態を自動的にクリーンアップし、テストケース間の相互汚染を防ぎます。

pytest fixtures として自動的に利用可能です（インストール後）：

- `testbot`：function レベルの標準 TestBot（platform=`test`、接頭辞 `/`）
- `make_testbot(**kwargs)`：カスタムパラメータのファクトリー（`prefix` / `config` / `platform` / `bot_id` ...）

テストプロジェクトの設定で `asyncio_mode = "auto"`（`[tool.pytest.ini_options]`）を推奨します。  
または、テストケースに `@pytest.mark.asyncio` を追加してください。

## 事件工厂

| 関数 | 説明 |
|------|------|
| `create_message_event(text, user_id=..., group_id=None, ...)` | メッセージイベント；`group_id` が空の場合はプライベートチャット |
| `create_command_event("roll 3", prefix="/")` | コマンドメッセージ（自動的に接頭辞を追加、既に接頭辞が付いている場合は重複しない） |
| `create_notice_event(type, ...)` | 通知イベント（例：`friend_add`） |
| `create_request_event(type, ...)` | 要求イベント（例：友達申請） |
| `create_meta_event("connect", ...)` | meta イベント（`connect` で Bot をオンラインにできる） |

すべてのイベントは uuid を用いた一意の `id` を持つため、フレームワークのイベント重複防止を自然に回避します。

注意：合成イベントには**プラットフォームの元の報文は含まれません**（`event.get_raw()` は空の dict を返します）。グループチャット / プライベートチャットなどの状況を判断するには、`event.is_group_message()` / `event.get_detail_type()` / `event.get_group_id()` などのアクセサを使用してください。raw を直接読んではいけません。

## TestBot API

### 分发

```python
trace = await bot.dispatch(event)          # ディスパッチし、ハンドラが実行されるまで待機し、返り値は処理の決定チェーン
await bot.dispatch(event, drain=False)     # 交互作用の最初のメッセージ：待機しない（wait_reply ハンドラは長時間待機）
await bot.send_message("你好")             # メッセージのディスパッチのショートカット
await bot.reply_as("18", user_id="u1")     # wait_reply ユーザーの返信をシミュレート（自動で waiter が準備されるまで待機）
```

`dispatch()` は emit 後、すべての処理中の Task を gather し、返り値が返る時点で処理が完了します。**テストでは sleep は不要です**。

### 出站断言

```python
bot.replies                # 全ての出力メッセージ（SentMessage のリスト）
bot.last_reply.text        # 最後の返信のテキスト
bot.replies_to("123")      # 目標でフィルタリング
bot.clear_replies()        # テスト間の出力メッセージを隔離
bot.assert_replied()                       # 出力メッセージが存在する
bot.assert_replied(contains="签到", to="123")
bot.assert_not_replied()                   # 何も出力メッセージがない
bot.assert_reply_contains("签到成功")       # 指定テキストを含む出力メッセージが存在する
await bot.wait_for_reply(timeout=2)        # 異步返信の出現を待つ
```

`SentMessage` のフィールド：`text`（最初のテキストセグメント）、`segments`（完全なメッセージセグメント）、`target_type` / `target_id` / `bot_id`（送信のコンテキスト）、`has_modifier("at")` など。

### 模块加载

```python
await bot.load_module("MyModule")   # 登録済みのモジュール名（`sdk.init()` で entry-point 発見が完了している必要がある）
await bot.load_module(MyModule)     # または BaseModule のサブクラス（自動 register + load、推奨）
await bot.unload_module("MyModule")
```

`on_load` で登録されたコマンド / イベントハンドラはモジュールに属し、アンロード時に自動的にクリーンアップされます。これにより、"アンロード後にコマンドが無効になる"ことを直接アサーションできます。  
注意：文字列形式では**entry-point スキャンは行われません**（TestBot はフレームワークの発見プロセスを初期化しません）。依存モジュールをテストする場合は、直接クラスオブジェクトを渡すか、`module.register` した後に名前を渡してください。

### 依赖替换（EP>=2.9.0-dev 以降）

```python
with bot.patch_dependency(get_session, fake_session) as mock:
    await bot.dispatch(create_command_event("query"))
    assert mock.called
```

コマンド登録表の `Depends(get_session)` で宣言された関数を置換します。`with` が終了すると自動的に元に戻ります。

### 配置覆写

```python
bot = TestBot(prefix="//", config={
    "ErisPulse.event.command.case_sensitive": False,
    "MyModule.api_key": "test-key",     # モジュールの設定（self.cfg で読める）
})
```

設定はメモリ層に注入され、コマンド接頭辞などは即座に更新されます。2点注意があります：

1. **ファイルへの書き込み**：覆写はフレームワークの遅延書き込み戦略（デフォルトで約5秒）に従って cwd の `config/config.toml` に書き込まれます。テスト対象のプロジェクトリポジトリでは、`config/` を `.gitignore` に追加してください。
2. **モジュール実行時の設定書き戻しとの競合（既知の制限）**：テスト対象のモジュールが設定を節単位で書き戻す（`self.cfg = ...`、例：購読リスト）場合、この点分覆写と並存すると、ConfigManager の読み書きの一貫性の問題が発生します。モジュールが節単位で設定を読み取る場合、覆写値が見えない可能性があります。また、覆写値が節単位の書き戻しによって上書きされる可能性もあります（ErisPulse 2.9.0-dev.2 で修正済み、2.8.x では影響を受けます）。"実行時の設定書き戻し"を含むテストケースでは、2.8.x では fixture で節単位の書き戻しで設定をリセットすることを推奨します。

## 分发决策链（"コマンドがなぜ実行されなかったか"を調査する場合；EP>=2.9.0-dev 以降）

`dispatch()` は `DispatchTrace` を返します。これは、今回のディスパッチが経過した各判定ポイントの因果チェーンです。

```python
trace = await bot.dispatch(create_command_event("dailyx", user_id="123"))

trace.verdict        # executed / rejected / dropped / failed / no_match / passed
trace.explain()      # 逐行の因果説明（現在の言語）
trace.command        # 命中したコマンド名（未命中の場合は None）
trace.steps("cooldown")  # 階段ごとに判定記録をフィルタリング

trace.assert_executed("daily")  # 実行されたことをアサーション（失敗時は因果チェーンを含む）
trace.assert_rejected()         # 権限系判定で拒否されたことをアサーション
trace.assert_dropped()          # クールダウンなどで静かにドロップされたことをアサーション
trace.assert_no_match()         # コマンドが命中しなかったことをアサーション
```

判定のカバレッジ：コマンドテキスト判定、コマンド命中（未命中の場合はスペル補正を含む）、作用域、ユーザー ACL、オーナーチェック、権限関数、クールダウンによる静かなドロップ、パラメータ解析、実行結果、ミドルウェアによる否決。

本番環境でも、フレームワーク内蔵の `ErisPulse.Core.Event.trace`（`start_dispatch_trace()` / `format_dispatch_trace()`）を使用して、決定チェーンの収集とレンダリングが可能です。

## 下一步

### テストで「コマンドが実行されなかった」問題が発見された場合

### テストが通って、配布準備中

- [モジュールの基本概念](modules/core-concepts.md) — モジュールのアーキテクチャと設定宣言の詳細を補完する
- [配布とモジュールストアガイド](publishing.md) — PyPI とモジュールストアへの配布の完全なプロセス