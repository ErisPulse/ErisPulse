# Minecraft プラットフォーム機能ドキュメント

MinecraftAdapter は、RCON プロトコルに基づく Minecraft Java 版サーバー向けアダプターで、コマンドの実行、メッセージの送信、ログイベントのリスニングをサポートします。

---

## ドキュメント情報

- 対応モジュールバージョン: 0.1.0
- メンテナー: ErisPulse

## 基本情報

- プラットフォーム概要：Minecraft Java版サーバーボット（RCON リモートコンソール経由）
- アダプター名：MinecraftAdapter
- 複数サーバー対応：対応（アカウントごとに 1 サーバー、切断時に自動再接続）
- 接続方式：RCON TCP 常時接続（キープアライブ + 指数バックオフによる再接続）
- 認証方式：RCON パスワード（server.properties の rcon.password）
- イベント監視：ログ tail（オプション、チャット/参加/退出）
- メソッドチェーン対応：対応（`.At()` などのチェーン修飾メソッド）
- OneBot12 互換：text セグメントのみ（RCON ではメディア送信不可）

## サーバーの事前設定

`server.properties`：

```properties
enable-rcon=true
rcon.port=25575
rcon.password=your_rcon_password
```

## 設定の説明

```toml
[MinecraftAdapter.accounts.default]
host = "127.0.0.1"             # RCON サーバーアドレス
port = 25575                   # RCON ポート
password = "your_rcon_password"
bot_id = ""                    # 空欄の場合はアカウント名がデフォルト
enable_log_tail = false        # ログ監視の有効化（チャット/参加/退出イベント）
log_path = "logs/latest.log"   # ログファイルのパス
poll_interval = 1.0            # ログスキャン間隔（秒）
enabled = true
```

**設定項目の説明（各アカウント）：**

- `host` / `port` / `password`：RCON エンドポイント（必須）
- `bot_id`：イベントにおけるボットの識別子（デフォルトはアカウント名）、全サーバーブロードキャストの `group_id` としても使用されます
- `enable_log_tail`：ログイベントのスイッチ（デフォルトはオフ）。オフの場合、アダプターは純粋なコマンドモードになります（送信のみ、イベントは発生しない）
- `log_path`：ログファイルのパス。アダプターとサーバーが**同一マシン上で実行**されているか、ログディレクトリがマウントされている必要があります。ログローテーションに対応（latest.log のローテーション後、読み取り位置を自動的にリセット）
- `poll_interval`：ログスキャン間隔（秒、最小 0.2）

## メッセージ送信

すべての送信メソッドは Task を返し、await 後に標準レスポンスが得られます（「戻り値フォーマット」を参照）。

### 基本送信

```python
from ErisPulse import sdk
mc = sdk.adapter.get("minecraft")

# 単一ユーザーへのメッセージ（tellraw プレーンテキスト）
await mc.Send.To("user", "Steve").Text("Hello Steve")

# 全サーバーへのブロードキャスト（say）
await mc.Send.To("server", "myserver").Text("サーバー全体へのブロードキャスト")
```

### チェーン修飾メソッド

```python
# @プレイヤー（tellraw 内でインライン表示としてプレイヤー名をレンダリング）
await mc.Send.To("server", "myserver").At("Steve").Text(" これを見て")
```

### 複数サーバーへの送信

```python
await mc.Send.Using("server2").To("server", "s2").Text("2台目のサーバーから")
```

### サポート対象と非対応のメッセージセグメント

| セグメント | 対応状況 | 説明 |
|----|------|------|
| `text` | 対応 | 連結後、ターゲットタイプに応じて tellraw / say に変換 |
| `mention` | 対応 | プレイヤー名としてインライン表示 |
| `reply` | 部分対応 | 受け付けるが Minecraft には引用表示なし |
| `image` / `audio` / `video` / `file` | 非対応 | `retcode=10002` を返し、セグメントタイプを列挙 |

### ターゲットタイプ

| target_type | 動作 |
|-------------|------|
| `user` | `tellraw <プレイヤー名> {"text":"..."}` 該当プレイヤーのみに表示 |
| `server` / `group` | `say <内容>` 全サーバーへのブロードキャスト（group_id は bot_id） |

## 標準 API アクション（Api）

```python
from ErisPulse import sdk
mc = sdk.adapter.get("minecraft")

# オンラインプレイヤーリスト（list コマンドの出力を解析）
result = await mc.Api.get_player_list()       # {"players": ["Steve", "Alex"], "raw": "..."}

# 接続状態
result = await mc.Api.get_status()            # {"status": "ok", "connected": true}

# サーバー識別情報
result = await mc.Api.get_self_info()         # {user_id, user_name, host}

# バージョン
result = await mc.Api.get_version()

# 複数サーバー
result = await mc.Api.Using("server2").get_player_list()
```

### サポートされている標準アクション

| メソッド | 説明 | データソース |
|------|------|---------|
| `get_status()` | RCON 接続状態 | ローカル |
| `get_self_info()` | サーバー識別情報（bot_id/アカウント名/host:port） | ローカル |
| `get_player_list()` | オンラインプレイヤーリスト（`list` コマンドの出力を解析） | RCON |
| `get_version()` | アダプターバージョン | ローカル |

### プラットフォーム拡張アクション

`Api.exec(cmd)` により任意の RCON コマンドを実行できます（`call_api("exec", command=...)` と同等）：

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

> **セキュリティに関する注意**：`Api.exec` はサーバーコンソールの完全な権限（stop/deop などを含む）を持っています。認証されていないエントリポイントを信頼できない呼び出し元に公開しないでください。

### サポートされていない標準アクション

以下の標準アクションには RCON に対応する機能がなく、呼び出すと `retcode=10002` または `33001`（未接続）が返されます：

- `delete_message`（Minecraft にはメッセージの取り消し機能がありません）
- `get_friend_list` / `get_group_list`（`get_player_list` で代用してください）

### 汎用アクションエントリポイント

```python
# send_message：Send チェーンと同等
result = await mc.call_api(
    "send_message",
    _account_id="default",
    target_type="user", target_id="Steve",
    message=[{"type": "text", "data": {"text": "hi"}}],
)
```

## 送信メソッドの戻り値

```python
{
    "status": "ok",                  # ok / failed
    "retcode": 0,                    # 0 成功；33001 未接続/実行失敗；10002 非対応
    "data": {"command_output": "..."},  # RCON コマンドの応答出力
    "self": {"platform": "minecraft", "user_id": "mc1"},
    "message_id": "uuid",            # 生成されたメッセージ識別子（tellraw/say には実際のメッセージ ID なし）
    "message": "",
    "minecraft_raw": {"output": "..."}
}
```

## イベントタイプ（enable_log_tail = true）

本プラットフォームの機能を使用するには、`platform == "minecraft"` の判定が必要です。**RCON プロトコルではチャットイベントを受信できません**（純粋なリクエスト・レスポンスプロトコルのため）、イベント機能はログ監視に依存します。

### イベントマッピング

| サーバーログ行 | Adapter イベント | 説明 |
|--------------|--------------|------|
| `[12:34:56] [...]: <Steve> こんにちは` | message（`detail_type: server`） | プレイヤーのチャット |
| `[12:35:00] [...]: Alex joined the game` | notice（`detail_type: server_joined`） | プレイヤーの参加 |
| `[12:36:00] [...]: Alex left the game` | notice（`detail_type: server_left`） | プレイヤーの退出 |

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
  "message": [{"type": "text", "data": {"text": "こんにちは世界"}}],
  "alt_message": "こんにちは世界",
  "group_id": "mc1",                       # bot_id
  "minecraft_raw": {"line": "[12:34:56] [Server thread/INFO]: <Steve> こんにちは世界"},
  "minecraft_raw_type": "log_line"
}

# 参加（notice）
{
  "type": "notice",
  "detail_type": "server_joined",          # または server_left
  "user_id": "Alex",
  "operator_id": "Alex",
  "group_id": "mc1",
  "minecraft_raw": {"line": "..."},
  "minecraft_raw_type": "log_line"
}
```

### ループバックの重複排除

`say` / `tellraw` コマンドのエコーも同様にログへ書き込まれます。アダプターは送信時に内容のフィンガープリントを記録し（30 秒のウィンドウ）、ログに同じ内容が現れた場合は送信をスキップすることで、bot が送信したメッセージが受信イベントとしてループバックされるのを防ぎます。

## 注意事項

1. **RCON ではチャットイベントを受信できない**：プロトコル自体の制限（純粋なリクエスト・レスポンス型）のため、イベント機能にはログ監視の有効化が必須
2. **ログパスの到達可能性**：アダプターはサーバーと同一マシンで実行するか、ログディレクトリがマウントされている必要がある（コンテナ環境では `logs/` をマウント）
3. **ログフォーマット**：vanilla / 主要サーバー（Paper、Fabric など）のデフォルトフォーマットに依存；ログフォーマットを変更したプラグイン（カスタム chat プラグインなど）は解析できない場合がある
4. **RCON の同時実行制限**：Minecraft RCON は単一接続での逐次処理；アダプターにはロックとキープアライブ（30秒ごとの空コマンド）が組み込まれている
5. **ループバック重複排除ウィンドウ**：30秒以内の同一内容は 1 回のみ発火
6. **セキュリティ**：`Api.exec` はコンソールレベルの権限を持つため、信頼できない呼び出し元に公開しないこと