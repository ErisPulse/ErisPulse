# Sandbox プラットフォーム機能ドキュメント

SandboxAdapter は ErisPulse に組み込まれたサンドボックスアダプターで、ローカル開発とモジュールのデバッグに使用されます——実際のプラットフォームがなくてもメッセージの送受信をシミュレートできます。

---

## ドキュメント情報

- 対応モジュールバージョン: 4.2.3
- メンテナー: ErisPulse
- 最終更新: 2026-11-10

## 基本情報

- プラットフォーム概要：ローカルサンドボックス環境。仮想ユーザー/グループ、Web デバッグパネル、メッセージ永続化を提供
- アダプター名：SandboxAdapter
- プラットフォーム識別子：`sandbox`
- 単一アカウント設計（ローカルデバッグ用途）
- フレームワーク要件：ソフト依存 `ErisPulse>=2.7.1`（実行時に検出して通知、強制ではない）

## v5 パラダイム更新（4.1.0）

- **Api DSL 最小セット**：`get_self_info` / `get_status` / `get_version` / `get_supported_actions`
- **spawn_background タスク帰属**：ハートビートタスクは `runtime.spawn_background` を使用するように変更
- **フレームワークのソフト依存**：実行時に `ErisPulse>=2.7.1` を検出し、通知
- インポートパスを `Core.Bases`（BaseConfig）に更新

## 標準化への準拠（4.2.3）

レスポンス構造とエラーコードは [API レスポンス規範](../standards/api-response.md) に従います。

### HTML 送信メソッド

- `.Html(html: str)`：HTML メッセージを送信します（html チャネル経由で Web パネルにレンダリング）
- `.HTML(html: str)`：`.Html()` のエイリアス（標準 Send メソッドの命名と一貫性を保持）

### メタアクション（標準化済み）

標準メタアクションは標準レスポンスを返します：

| アクション | data の内容 |
|------|----------|
| `get_self_info` | `user_id`（設定された `self_id`）/ `user_name`（`sandbox`） |
| `get_status` | `good`（実行状態）/ `bots`（アカウントリスト） |
| `get_version` | `impl`（ErisPulse-SandboxAdapter）/ `version` / `onebot_version` |
| `get_supported_actions` | サポートされているアクション名のリスト |

```python
from ErisPulse import sdk
sandbox = sdk.adapter.get("sandbox")

result = await sandbox.Api.get_self_info()   # サンドボックスボットの識別情報
result = await sandbox.Api.get_status()
result = await sandbox.Api.get_version()
result = await sandbox.Api.get_supported_actions()
```

### リクエストイベント処理（Request stub）

サンドボックスは `type="request"` イベント（友人申請/グループ参加申請、`request_id` はシミュレートイベントから透過）を合成し、モジュールは標準的な方法で承認できます（完全な規範は [リクエスト操作規範](../standards/request-action-spec.md) を参照）：

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    await event.approve()   # または event.reject()
```

アダプター側の Request DSL は**シミュレーションスタブ**です：`accept()` / `reject()` は `request_id` を検証し（欠落時はリクエスト操作系エラーコードである標準エラー `retcode=34001` を返します）、検証通過後は承認成功をシミュレートして標準の成功レスポンスを返します。これにより、下流での `approve()` / `reject()` フローの結合テストが容易になります。

### エラーコード規範

| retcode | 意味 | 説明 |
|---------|------|------|
| 0 | 成功 | — |
| 10002 | 未サポート | プラットフォームに対応機能がない |
| 10003 | パラメーターエラー | パラメーターの欠落または無効 |
| 10006 | 無効なメッセージセグメントデータ | `MergeForward` ノードに有効なテキスト内容がない |
| 34001 | リクエストが存在しない | `Request.accept()/reject()` に `request_id` が欠落（リクエスト操作系） |

## 設定説明

```toml
[Sandbox]
self_id = "sandbox_bot"  # サンドボックスボットID
enable = true            # 有効にするかどうか
```

## 使用説明

- サンドボックスは仮想ユーザーとグループを提供し、モジュールは実際のプラットフォームと同様にメッセージの送受信が可能
- Web デバッグパネルからメッセージを手動で送信し、モジュールの処理ロジックをトリガーできる
- メッセージデータは永続化ストレージ（`sdk.storage`）に保存され、再起動後も復元可能

## サポートされるメッセージ送信タイプ

すべての送信メソッドはチェーン構文で実装されています。例：

```python
from ErisPulse import sdk
sandbox = sdk.adapter.get("sandbox")

await sandbox.Send.To("private", "user1").Text("Hello")
await sandbox.Send.To("group", "group1").Markdown("**太字**")
```

サポートされる送信タイプは以下の通りです：

| メソッド | 説明 |
|------|------|
| `.Text(text)` | テキストメッセージを送信 |
| `.Image(file, summary=None)` | 画像を送信 |
| `.Face(face_id)` | 表情を送信 |
| `.Record(file, magic=False)` | 音声を送信 |
| `.Voice(file)` | 音声を送信（audio チャンネル） |
| `.Video(file)` | 動画を送信 |
| `.File(file, filename=None)` | ファイルを送信 |
| `.Html(html)` / `.HTML(html)` | HTML メッセージを送信（後者はエイリアス） |
| `.Markdown(markdown)` | Markdown メッセージを送信 |
| `.Json(json_data)` | JSON カードメッセージを送信 |
| `.Xml(xml_data)` | XML カードメッセージを送信 |
| `.Music(platform, id, title=None)` | 音楽メッセージを送信 |
| `.Share(url, title, content=None, image=None)` | リンク共有を送信 |
| `.Location(lat, lon, title=None, content=None)` | 位置情報メッセージを送信 |
| `.Dice()` | サイコロを送信 |
| `.Rps()` | じゃんけんを送信 |
| `.Poke(user_id, type="poke")` | つつき（Poke） |
| `.Recall(message_id)` | メッセージの取り消しをシミュレート |
| `.MergeForward(nodes, title="チャット履歴を統合")` | 統合転送メッセージを送信（`<details>` 折りたたみ HTML カードとしてレンダリングされ、html チャンネルで送信されます）。モジュールの統合転送ロジックの検証に使用されます |
| `.Raw_ob12(message)` | OneBot12 の生のメッセージセグメントを送信（純粋な node リストは自動的に統合転送へルーティングされ、混合リストの node セグメントはプレーンテキストにダウングレードされます） |

`At` / `AtAll` / `Reply` 修飾子は、フレームワークの SendDSL 基底クラスによって提供されます。