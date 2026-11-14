# Minecraftプラットフォーム特徴ドキュメント

MinecraftAdapterは、RCONプロトコルに基づくMinecraft Java Editionサーバーアダプターです。コマンドの実行、メッセージの送信、ログイベントの監視が可能です。

---

## ドキュメント情報

- 対応モジュールバージョン: 0.1.2
- メンテナー: ErisPulse
- 最終更新日: 2026-11-10

## 基本情報

- プラットフォーム概要: Minecraft Java Editionサーバーボット（RCONリモートコンソール経由）
- アダプター名: MinecraftAdapter
- 複数サーバー対応: 対応（1アカウントにつき1台のサーバー、切断時に自動再接続）
- 接続方法: RCON TCP長時間接続（保活 + 指数バックオフによる再接続）
- 認証方法: RCONパスワード（server.propertiesのrcon.password）
- イベント監視: ログtail（オプション、チャット/加入/退出）
- チェーン修飾子サポート: .At()等のチェーン修飾子メソッドをサポート
- OneBot12互換性: テキストセグメントのみ（RCONではメディアを送信できない）

## サーバー事前設定

`server.properties`:

```properties
enable-rcon=true
rcon.port=25575
rcon.password=your_rcon_password
```

## 設定説明

```toml
[MinecraftAdapter.accounts.default]
host = "127.0.0.1"             # RCONサーバーのアドレス
port = 25575                   # RCONポート
password = "your_rcon_password"
bot_id = ""                    # 空欄の場合はアカウント名がデフォルト
enable_log_tail = false        # ログ監視の有効化（チャット/加入/退出イベント）
log_path = "logs/latest.log"   # ログファイルのパス
poll_interval = 1.0            # ログのスキャン間隔（秒）
enabled = true
```

**各アカウントの設定項目説明:**

- `host` / `port` / `password`: RCONエンドポイント（必須）
- `bot_id`: イベントにおけるボットの識別子（デフォルトはアカウント名）、全サーバー放送時の`group_id`として使用
- `enable_log_tail`: ログイベントの有効/無効（デフォルトは無効）。無効の場合、アダプターは純粋なコマンドモード（送信のみ、イベントは発生しない）
- `log_path`: ログファイルのパス。アダプターとサーバーが**同じホストで実行**されているか、ログディレクトリがマウントされている必要があります。ログローテーションに対応（latest.logがローテートされた後、自動的に読み取り位置をリセット）
- `poll_interval`: ログのスキャン間隔（秒、最小0.2）

## 標準化の一致

本節では、ErisPulseの標準化規格との一致する動作について説明します。規格の詳細はSDKドキュメント「APIレスポンス規格」（`docs/ja/standards/api-response.md`）を参照してください。

### Api.Using()アカウントルーティングの修正（0.1.2）

`Api` DSLの各メソッドは、以前は`Using()`で指定したアカウントを正しく消費していませんでした。現在は修正済みです: 明示的に`Using()`で渡された`_account_id`とイベントチェーンの`api_context`（イベントの発生元アカウント）は、対応するサーバーのランタイムに正しくルーティングされます。省略時は最初のアカウントに回帰します。

### メッセージイベントにメッセージIDの追加

メッセージイベントに上位の`message_id`フィールドを追加しました（UUID；tellraw/sayには実際のメッセージIDがなく、生成されたメッセージ識別子を使用）。

### 加入/退出イベントのdetail_typeの標準化（0.1.2）

プレイヤーの加入/退出イベントの`detail_type`は、`server_joined` / `server_left`から`group_member_increase` / `group_member_decrease`に標準化され、元のタイプは`sub_type`に保持されます：

| 元のタイプ | 標準化されたdetail_type | sub_type |
|----------|-------------------|----------|
| server_joined | `group_member_increase` | `server_joined` |
| server_left | `group_member_decrease` | `server_left` |

### 拡張アクションの標準化（0.1.2）

拡張アクションは、プラットフォームプレフィックス付きの呼び出し形式を提供し、旧メソッド名も互換性を保ちます：

- `Api.call("minecraft.get_player_list")` / `call_api("minecraft.get_player_list")`（旧`get_player_list`は保持）
- `Api.call("minecraft.exec", command="...")` / `call_api("minecraft.exec", ...)`（旧`exec`は保持）

### 元アクションの標準化

- `get_self_info`の`data`には標準フィールドが含まれます：`user_id` / `user_name` / `user_displayname` および `host`
- `get_version`は`{"impl": "ErisPulse-MinecraftAdapter", "version": "...", "onebot_version": "12"}`を返します
- `get_supported_actions`はサポートされるアクション名のリストを返します

### その他

- `call_api`は標準フィールド`account_id`と旧フィールド名`_account_id`の両方を受け付けます（標準名が優先）；フレームワークApiDSLは自動的に適応します

## メッセージ送信

すべての送信メソッドはTaskを返し、await後に標準レスポンスを得られます（「返却値形式」を参照）。

### 基本送信

```python
from ErisPulse import sdk
mc = sdk.adapter.get("minecraft")

# 単人メッセージ（tellraw 純文本）
await mc.Send.To("user", "Steve").Text("Hello Steve")

# 全体放送（say）
await mc.Send.To("server", "myserver").Text("サーバー全体放送")
```

### チェーン修飾子メソッド

```python
# @プレイヤー（tellraw内でプレイヤー名としてインラインにレンダリング）
await mc.Send.To("server", "myserver").At("Steve").Text(" これを見てください")
```

### 複数サーバー送信

```python
await mc.Send.Using("server2").To("server", "s2").Text("第二台のサーバーから")
```

### 支持/非サポートのメッセージセグメント

| セグメント | 支持 | 説明 |
|----|------|------|
| `text` | 支持 | 目標タイプに応じてtellraw / sayに変換 |
| `mention` | 支持 | プレイヤー名としてインラインにレンダリング |
| `reply` | 部分サポート | 受け入れるがMinecraftでは引用表示は行わない |
| `image` / `audio` / `video` / `file` | 非サポート | `retcode=10002`を返し、セグメントタイプをリストアップ |

### 目標タイプ

| target_type | 行動 |
|-------------|------|
| `user` | `tellraw <プレイヤー名> {"text":"..."}` 1人だけが見える |
| `server` / `group` | `say <内容>` 全体放送（group_idはbot_id） |

## 標準APIアクション（Api）

```python
from ErisPulse import sdk
mc = sdk.adapter.get("minecraft")

# オンラインプレイヤーリスト（listコマンドの出力を解析）
result = await mc.Api.get_player_list()       # {"players": ["Steve", "Alex"], "raw": "..."}
# プレフィックス付きの拡張アクション形式でも使用可能
result = await mc.Api.call("minecraft.get_player_list")

# 接続状態
result = await mc.Api.get_status()            # {"status": "ok", "connected": true}

# サーバーのアイデンティティ
result = await mc.Api.get_self_info()         # {user_id, user_name, host}

# バージョン
result = await mc.Api.get_version()

# 複数サーバー
result = await mc.Api.Using("server2").get_player_list()
```

### 標準アクションのサポート

| メソッド | 説明 | データソース |
|------|------|---------|
| `get_status()` | RCON接続状態 | ローカル |
| `get_self_info()` | サーバーのアイデンティティ（bot_id/アカウント名/host:port） | ローカル |
| `get_player_list()` | オンラインプレイヤーリスト（`list`コマンドの出力を解析；拡張名`minecraft.get_player_list`） | RCON |
| `get_version()` | アダプターのバージョン（impl/version/onebot_version） | ローカル |
| `get_supported_actions()` | サポートされるアクション名のリスト | ローカル |

### プラットフォーム拡張アクション

`Api.exec(cmd)`で任意のRCONコマンドを実行できます（`call_api("minecraft.exec", command=...)`と同等、旧名`exec`は互換性を保持）：

```python
# ホワイトリスト管理
await mc.Api.exec("whitelist add Alex")
await mc.Api.exec("whitelist remove Alex")

# サーバー管理
await mc.Api.exec("time set day")
await mc.Api.exec("weather clear")
await mc.Api.exec("op Alex")
await mc.Api.exec("kick Steve")

# データとスコアボード
await mc.Api.exec("scoreboard objectives add kills deathCount")
```

> **セキュリティ注意**：`Api.exec`はサーバーコンソールの完全な権限を持ちます（stop/deopなど）、信頼できない呼び出し元に未認証のエントリを公開しないでください。

### 標準アクションの非サポート

以下の標準アクションはRCONには対応しておらず、呼び出しは`retcode=10002`または`33001`（未接続）を返します：

- `delete_message`（Minecraftにはメッセージの撤回機能がない）
- `get_friend_list` / `get_group_list`（`get_player_list`で代用）

### 一般的なアクションエントリ

```python
# send_message：Sendチェーンと同等
result = await mc.call_api(
    "send_message",
    account_id="default",
    target_type="user", target_id="Steve",
    message=[{"type": "text", "data": {"text": "hi"}}],
)
```

## 送信メソッドの返却値

```python
{
    "status": "ok",                  # ok / failed
    "retcode": 0,                    # 0成功；33001未接続/実行失敗；10002非サポート
    "data": {"command_output": "..."},  # RCONコマンドの返信
    "self": {"platform": "minecraft", "user_id": "mc1"},
    "message_id": "uuid",            # 生成されたメッセージ識別子（tellraw/sayには実際のメッセージIDがない）
    "message": "",
    "minecraft_raw": {"output": "..."}
}
```

## イベントタイプ（enable_log_tail = true）

プラットフォームが`"minecraft"`であることを検証してから、このプラットフォームの特徴を使用してください。**RCONプロトコルはチャットイベントを受信できません**（純粋なリクエスト-レスポンスプロトコル）、イベント面はログ監視に依存します。

### イベントマッピング

| サーバーログ行 | Adapterイベント | 説明 |
|--------------|--------------|------|
| `[12:34:56] [...]: <Steve> 你好` | message（`detail_type: server`） | プレイヤーのチャット |
| `[12:35:00] [...]: Alex joined the game` | notice（`detail_type: group_member_increase`、`sub_type: server_joined`） | プレイヤーの加入 |
| `[12:36:00] [...]: Alex left the game` | notice（`detail_type: group_member_decrease`、`sub_type: server_left`） | プレイヤーの退出 |

### イベントフィールドの例

```python
# チャット
{
  "id": "uuid",
  "time": 1793277000,
  "type": "message",
  "detail_type": "server",
  "platform": "minecraft",
  "self": {"platform": "minecraft", "user_id": "mc1", "user_name": "mc1", "account_id": "default"},
  "user_id": "Steve",                      # プレイヤー名
  "message": [{"type": "text", "data": {"text": "你好世界"}}],
  "alt_message": "你好世界",
  "group_id": "mc1",                       # bot_id
  "minecraft_raw": {"line": "[12:34:56] [Server thread/INFO]: <Steve> 你好世界"},
  "minecraft_raw_type": "log_line"
}

# 加入（notice）
{
  "type": "notice",
  "detail_type": "group_member_increase",  # 退出はgroup_member_decrease
  "sub_type": "server_joined",             # 元のタイプはsub_typeに保持（退出はserver_left）
  "user_id": "Alex",
  "operator_id": "Alex",
  "group_id": "mc1",
  "minecraft_raw": {"line": "..."},
  "minecraft_raw_type": "log_line"
}
```

### ループ抑制

`say` / `tellraw`コマンドの返信もログに書き込まれます。アダプターは送信時に内容のフィンガープリントを記録（30秒ウィンドウ）、ログに同じ内容が出現した場合は発行をスキップし、botが送信したメッセージがイベントとしてループされることを防ぎます。

## 注意事項

1. **RCONはチャットイベントを受信できない**：プロトコルの制限（純粋なリクエスト-レスポンス）、イベント面はログ監視を有効にする必要がある
2. **ログパスの到達可能性**：アダプターとサーバーは同じホストで実行するか、ログディレクトリをマウントする（コンテナ環境では`logs/`をマウント）
3. **ログフォーマット**：vanilla / 主流サーバー（Paper、Fabricなど）のデフォルトフォーマットに依存。ログフォーマットを変更したプラグイン（独自チャットプラグインなど）は解析できない可能性がある
4. **RCONの並行処理制限**：Minecraft RCONは単一接続でシーケンシャル処理。アダプターは内部ロックと保活（30秒の空コマンド）を備えている
5. **ループ抑制のウィンドウ**：30秒以内に同じ内容は1回のみ発行
6. **セキュリティ**：`Api.exec`はコンソールレベルの権限を持つため、信頼できない呼び出し元に公開しないでください