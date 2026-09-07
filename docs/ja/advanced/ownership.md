# 所有者（owner）システム

所有権は、モジュールの「プラグインアンドプレイ」の基盤です。モジュールが読み込まれる際に登録されるフレームワークリソースはすべて自動的に所有者に記名され、モジュールのアンロード/無効化時に所有者に基づいて一括で回収されます。モジュールの作者はリソースを宣言するだけで、手動でクリーンアップロジックを書く必要はありません。

> **関連システム**：スコープはイベント配信時に「リソースが有効かどうか」を決定し、所有権はライフサイクル中に「リソースが誰に属するか、誰がアンロード時に回収されるか」を決定します。  
> スコープの詳細は[統一制御面（scope）](scope.md)を参照してください。バックグラウンドタスクの詳細は[ライフサイクル管理](lifecycle.md#バックグラウンドタスクの所有と自動キャンセル)を参照してください。

{!--< tips >!--}
1. 所有権は**登録の瞬間**に `current_owner` に基づいて自動的に記録され、モジュールのコードに変更は一切不要です。
2. アンロード/無効化は同じクリーンアップチェーン（`_cleanup_module_registrations`）を使用し、各ステップで失敗しても警告のみで中断はしません。
3. ユーザー設定のリソース（永続化オーバーライド / スコープルール / コマンドACL）は、モジュールのアンロード時にクリーンアップされません。
{!--< /tips >!--}

## owner コンテキストメカニズム

owner は、コンテキスト変数 `current_owner` を介して `ErisPulse.runtime.context` に渡されます：

```python
from ErisPulse.runtime import owner_scope, get_current_owner

with owner_scope("MyModule"):
    # このスコープ内に登録されたすべてのリソースは自動的に MyModule に属します
    assert get_current_owner() == "MyModule"
```

フレームワークは、以下のタイミングで自動的に owner を注入します（モジュールやアダプターのコードで手動でラップする必要はありません）：

| 時点 | owner 値 | 位置 |
|------|----------|------|
| モジュール `load()` | モジュール名 | インスタンス化 + `on_load` 全体 |
| アダプター `start()` / `restart()` | プラットフォーム名 | アダプター起動全体 |
| `activate_on` ラグジュアリスタブ登録 | モジュール名 | 占位コマンド/ハンドラの登録 |
| イベントハンドラ実行中 | ハンドラ所属モジュール名 | handler / コマンドエントリポイントの再注入 |

実行中の再注入とは、モジュールが `on_load` で宣言したコマンドハンドラが**実行中**に登録型 API（例：`sdk.adapter.on()`、`overrides.*.set(persist=False)`）を呼び出す場合、それらも自動的にこのモジュールに属することを意味します。

## リソースの所有関係

モジュールは、ロードコンテキスト内で以下のリソースを登録し、所有関係を記録します。アンロードまたは無効化時に、自動的にリソースを回収します。

| リソース | 登録方法 | クリーンアップ呼び出し |
|------|----------|----------|
| コマンド | `@command()` / コマンド dict 宣言 | `command.unregister_by_owner()` |
| イベントハンドラ | `@message` / `@notice` / `@request` / `@meta` | `handler.unregister_by_owner()` |
| アダプタイベントリスナー | `sdk.adapter.on()` / `raw=True` | `adapter.unregister_handlers_by_owner()` |
| アダプタミドルウェア | `@sdk.adapter.middleware` | 同上 |
| ルーティング（HTTP/WS/SSE） | `router.http()` / `websocket()` / `sse()` | 名前空間 + owner による二重保証 |
| ルーティングミドルウェア | `@router.middleware()` / `add_middleware()` | `router.unregister_all_by_owner()` |
| Dashboard トップページエントリ | `router.register_home_entry()` | `unregister_home_entries_by_owner()` |
| 自定义会话类型 | `register_custom_type()` | `unregister_custom_types_by_owner()` |
| バックグラウンドタスク | `self.spawn()` | `cancel_owner_tasks()` |
| ライフサイクルフック | `lifecycle.register()` | `lifecycle.unregister_by_owner()` |
| 主人身源 provider | `master.provider` | `master.unregister_by_owner()` |
| i18n 翻訳キー | `I18nClass` 宣言（domain=モジュール名） | `i18n.unregister_domain()` |
| イベントオーバーライド（実行時） | `overrides.*.set(persist=False)` | `overrides.unregister_by_owner()` |
| コンテキストデータ | `runtime/context` は owner ごとに記録 | モジュールごとの正確なクリーンアップ |

アダプタ側の対応するリソース（プラットフォーム名を owner として）は、アダプタの `shutdown()` / `restart()` 時に `_cleanup_adapter_resources` によって回収されます。以下も含まれます：

| リソース | クリーンアップ呼び出し |
|------|----------|
| アダプタ独自の `on()` ハンドラとミドルウェア | `adapter.unregister_handlers_by_owner(platform)` |
| プラットフォームイベントメソッド拡張（`EventMixin`） | `unregister_platform_event_methods(platform)` |
| 自定义会话类型 | `unregister_custom_types_by_owner(platform)` |
| i18n 翻訳ドメイン（domain=設定キー） | `i18n.unregister_domain(設定キー)` |
| 細かい粒度の名前空間ルーティング | `router.unregister_all_by_owner(platform)` |

## 卸載/無効化のクリーンアップシーケンス

`unload()` および `disable()` は、同じクリーンアップチェーンを使用します（各ステップで個別に try/except を使用し、失敗してもログに記録され、**後続のクリーンアップを中断しません**）：

```mermaid
flowchart TD
    A["unload / disable"] --> B["on_unload()（タイムアウト保護）"]
    B --> C["バックグラウンドタスクのキャンセル（cancel_owner_tasks）"]
    C --> D["_cleanup_module_registrations"]
    D --> D1["i18n 翻訳ドメイン"]
    D1 --> D2["ルーティング：名前空間 + owner のデフォルト処理<br/>（ミドルウェア / ホームページエントリを含む）"]
    D2 --> D3["アダプタイベントハンドラ / ミドルウェア"]
    D3 --> D4["コマンド + イベントハンドラ"]
    D4 --> D5["カスタムセッションタイプ"]
    D5 --> D6["実行時イベントのオーバーライド（persist=False）"]
    D6 --> D7["所有者プロバイダ"]
    D7 --> D8["ライフサイクルフック"]
    D8 --> E["SDK属性の削除 + ラグジュアリプロキシ"]
```

`sdk.uninit()` で終了する際には、以下のグローバルなデフォルト処理が追加されます：すべてのアダプタのシャットダウン → すべてのモジュールの unload → `router.stop()`（ルーティング/ミドルウェア/ホームページエントリのクリア）→ `cancel_all_background_tasks()` → イベントハンドラおよびフックのクリア。

## 設計の境界：アンインストール時にクリーンアップされないリソース

所有権は**モジュールコードが登録したランタイムリソース**のみを回収します。以下のリソースは**ユーザーの設定の意味**（制御権はユーザーにあり、意図的に設定している可能性がある）に属し、モジュールのアンインストール後も設定に従って永続的に保持されます：

| リソース | 意味 | 説明 |
|------|------|------|
| `overrides.*.set(persist=True)` | 永続化されたオーバーライド | 設定ファイルに書き込まれ、再起動後に有効。モジュールのアンインストール時に削除されない（ユーザーが明示的に設定） |
| `scope.set_action()` などのスコープルール | 権限制御面 | ユーザー/Dashboard によって管理され、モジュールのアンインストール時にルールは回収されない |
| `overrides.acl.set(persist=True)` | コマンド ACL | 上記と同じ |
| Conversation `save()` による永続化 | 複数回の対話の保存 | データ資産はクリーンアップされない |

ランタイムに一時的に書き込まれたもの（`persist=False`）は、所有者に従って回収されます。**永続化の有無が「ユーザーの資産」と「モジュールのランタイム状態」の境界線です**。

## モジュール開発者ガイド

### 推奨される書き方

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command
from ErisPulse.runtime import owner_scope, spawn_background

class MyModule(BaseModule):
    async def on_load(self, event):
        # フレームワークリソース：自動帰属、手動クリーンアップ不要
        self.task = self.spawn(self.polling())      # バックグラウンドタスク
        sdk.router.register_home_entry("私のモジュール", "/my")  # ホームページエントリ

        # モジュール独自リソース：owner_scope に包むことで帰属体系に組み込む
        with owner_scope("MyModule"):
            self.client.on_event(self._handle)      # 仮想のカスタム登録

    async def on_unload(self, event):
        # フレームワークリソースは自動回収済み、owner_scope がカバーしない独自リソースのみクリーンアップ
        await self.client.close()
```

### 注意事項

- **import 時の登録は帰属対象外**：モジュールの最上層（import 時）に登録されたフック/ハンドラーは
  `owner_scope` より前に行われ、フレームワークレベルのリソース（owner=None）として扱われ、**クリーンアップされません**。
  すべて `on_load()` 内で登録してください。
- **カスタム domain の i18n 登録**：`i18n.register(domain=...)` の domain がモジュール名と異なる場合、自動回収されません。domain=モジュール名を維持してください。
- **バックグラウンドタスクは必ず self.spawn() を使用**：裸の `asyncio.create_task` はモジュールに帰属せず、アンロード時にキャンセルされません（詳細は[ライフサイクル管理](lifecycle.md#バックグラウンドタスクの帰属と自動キャンセル)を参照）。
- クリーンアップの「失敗は警告のみ」：1ステップのクリーンアップで異常が発生しても、他のリソースの回収は妨げられません。デバッグ/警告レベルのログで確認でき、トラブルシューティング時には TRACE を有効にしてください。