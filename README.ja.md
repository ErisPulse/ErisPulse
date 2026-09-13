<img src=".github/assets/mascot-hero.png" align="right" width="300" alt="ErisPulse" style="margin-left: 24px; margin-bottom: 16px; border-radius: 12px;" />

[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | **日本語** | [Русский](README.ru.md)

# ErisPulse

**一次書き込み、QQ / Telegram / Kook / Yunhu / 微信公式アカウント / OneBot12 / ... など複数プラットフォームに展開。**

イベント駆動型の多プラットフォームチャットボット開発フレームワーク。

OneBot12標準インターフェースをベースに、一度のコードで複数プラットフォームに展開可能。柔軟なプラグインシステム、ホットリロード対応、そして包括的な開発者ツールチェーンにより、シンプルなチャットボットから複雑な自動化システムまで、あらゆるシナリオに対応。

<p>
  <a href="https://pypi.org/project/ErisPulse/"><img src="https://img.shields.io/pypi/v/ErisPulse?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI"></a>
  <a href="https://pypi.org/project/ErisPulse/"><img src="https://img.shields.io/badge/Python-3.10+-FFD43B?style=for-the-badge&logo=python&logoColor=blue" alt="Python"></a>
  <a href="https://github.com/botuniverse/onebot-11"><img src="https://img.shields.io/badge/OneBot-11-black?style=for-the-badge" alt="OneBot 11"></a>
  <a href="https://12.onebot.dev/"><img src="https://img.shields.io/badge/OneBot-12-black?style=for-the-badge" alt="OneBot 12"></a>
  <a href="https://hub.docker.com/r/erispulse/erispulse"><img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker"></a>
  <a href="https://github.com/ErisPulse/ErisPulse/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="License"></a>
  <a href="https://pepy.tech/project/ErisPulse"><img src="https://img.shields.io/pepy/dt/ErisPulse?style=for-the-badge&color=blue" alt="Downloads"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json&style=for-the-badge" alt="Ruff"></a>
  <a href="https://socket.dev/pypi/package/erispulse"><img src="https://img.shields.io/badge/Socket-Secure-2ea043?style=for-the-badge&logo=socket&logoColor=white" alt="Socket"></a>
  <a href="https://www.erisdev.com"><img src="https://img.shields.io/badge/ドキュメント-erisdev.com-FF6B9D?style=for-the-badge&logo=bookstack&logoColor=white" alt="ドキュメント"></a>
  <a href="https://deepwiki.com/ErisPulse/ErisPulse"><img src="https://img.shields.io/badge/DeepWiki-ErisPulse-8A2BE2?style=for-the-badge&logo=readthedocs&logoColor=white" alt="DeepWiki"></a>
  <a href="https://www.erisdev.com/#market"><img src="https://img.shields.io/badge/モジュール市場-erisdev.com-C724B1?style=for-the-badge&logo=webpack&logoColor=white" alt="モジュール市場"></a>
  <a href="https://github.com/ErisPulse/ErisPulse/discussions"><img src="https://img.shields.io/badge/GitHub-ディスカッション-181717?style=for-the-badge&logo=github" alt="ディスカッション"></a>
</p>

<br clear="both">

---

<div align="center">

### 主な特徴

</div>

<table>
<tr>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_event_driven.png.png" width="50" alt="イベント駆動アーキテクチャ" />

### イベント駆動アーキテクチャ

OneBot12の統一イベントモデルに基づき、一つのハンドラで全てのアダプタに対応

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_cross_platform.png.png" width="50" alt="クロスプラットフォーム互換性" />

### クロスプラットフォーム互換性

QQ / Telegram / Kook / 云湖 等15以上のプラットフォーム、業務コードを変更せずに利用可能

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_modular.png" width="50" alt="モジュラーデザイン" />

### モジュラーデザイン

プラグインのホットプラグイン / ホットリロード、プラットフォーム / Bot / セッションごとのスコープ管理

</td>
</tr>
<tr>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_hot_reload.png" width="50" alt="ホットリロード" />

### ホットリロード

保存するだけで有効、軽量で感覚のないホットリロード

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_ai_assist.png" width="50" alt="AIアシスタント" />

### AIアシスタント

自然言語で要望を記述し、直接利用可能なモジュールを生成

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_lightweight.png" width="50" alt="シンプルでエレガント" />

### シンプルでエレガント

チェーン式API：@ユーザー、返信、再試行、バッチ送信を一行で完了

</td>
</tr>
</table>

---

## 動作原理

ErisPulseはアダプタ層を介してプラットフォームの差異を抽象化し、業務コードはイベント自体にのみ関心を持ちます：

```mermaid
graph LR
    subgraph Platforms[プラットフォーム]
        QQ["QQ"]
        TG["Telegram"]
        Kook["Kook"]
        YH["云湖"]
        WX["微信公式アカウント"]
    end

    subgraph Adapters[アダプタ層]
        A1["QQアダプタ"]
        A2["Telegramアダプタ"]
        A3["Kookアダプタ"]
        A4["云湖アダプタ"]
        A5["微信アダプタ"]
    end

    Event["Eventイベントバス<br/>ミドルウェア → コマンド/メッセージ/通知/リクエスト/メタの配信"]

    subgraph Modules[業務モジュール]
        M1["コマンドハンドラ<br/>@command"]
        M2["メッセージハンドラ<br/>@message"]
        M3["あなたのモジュール"]
    end

    QQ --> A1
    TG --> A2
    Kook --> A3
    YH --> A4
    WX --> A5

    A1 -->|"OB12イベント"| Event
    A2 -->|"OB12イベント"| Event
    A3 -->|"OB12イベント"| Event
    A4 -->|"OB12イベント"| Event
    A5 -->|"OB12イベント"| Event

    Event -->|"配信"| M1
    Event -->|"配信"| M2
    Event -->|"配信"| M3

    M1 -.->|"event.reply()<br/>SendDSL"| Event
    Event -.->|"送信"| A1
```

- **アダプタ層**は各プラットフォームの独自プロトコルをOneBot12標準イベントに変換し、業務モジュールはプラットフォームの差異を意識しません。
- **Eventイベントバス**はまずミドルウェアチェーンを実行し、イベントタイプごとに5種類のハンドラに配信します。
- **あなたのコード**はデコレータでイベントをサブスクライブし、`event.reply()`またはSendDSLで返信します。返信メッセージは同じ経路を逆流してプラットフォームに送信されます。

モジュールの構成、初期化プロセス、ライフサイクルイベントなどの設計詳細は、[アーキテクチャ概要](docs/ja/architecture.md)を参照してください。

---

## 速習

### インストールスクリプト（推奨）

インストールスクリプトは環境（Docker、Python、uv）を自動検出し、最適なインストール方法を誘導します。多言語（中国語/English/日本語/Русский/繁體中文）もサポートしています。

Windows (PowerShell):
```powershell
irm https://get.erisdev.com/install.ps1 -OutFile install.ps1; powershell -ExecutionPolicy Bypass -File install.ps1
```

macOS / Linux:
```bash
curl -fsSL https://get.erisdev.com/install.sh -o install.sh && chmod +x install.sh && ./install.sh
```

<table>
<tr>
<td align="center" width="50%">

**Dockerインストールデモ**

<video src="https://github.com/user-attachments/assets/a367a466-4678-46a9-b101-073a86388ede" controls width="100%"></video>

</td>
<td align="center" width="50%">

**pipインストールデモ**

<video src="https://github.com/user-attachments/assets/a2df4009-dba6-411e-b79d-4454a168d063" controls width="100%"></video>

</td>
</tr>
</table>

### Dockerを使用する（推奨）

```bash
docker pull erispulse/erispulse:latest
```

<details>
<summary>Docker Hubが利用できない場合</summary>

Docker Hubにアクセスできない場合は、GitHub Container Registryを使用できます：

```bash
docker pull ghcr.io/erispulse/erispulse:latest
```

ghcr.ioのイメージを使用する場合は、`docker-compose.yml`のimageを変更する必要があります：
```yaml
image: ghcr.io/erispulse/erispulse:latest
```

</details>

<details>
<summary>クイックスタート</summary>

```bash
# docker-compose.ymlのダウンロード
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# Dashboardのログイントークンを設定して起動
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

起動後、`http://<ホスト>:8000/Dashboard`にアクセスし、設定したトークンでDashboard管理パネルにログインします。

> イメージにはErisPulseフレームワークとDashboard管理パネルが内蔵されており、`linux/amd64`と`linux/arm64`アーキテクチャをサポートします。
>
> **永続化**：設定ファイルとインストールされたモジュール/アダプタはボリュームマウントによりホストに永続化され、コンテナの再起動後も失われません。フレームワーク自体の更新はDashboardのホットアップデートで完了します。

</details>

<details>
<summary>Docker環境変数</summary>

| 変数 | デフォルト値 | 説明 |
|------|--------|------|
| `ERISPULSE_DASHBOARD_TOKEN` | 空 | Dashboardのログイントークン（設定すると自動的に設定ファイルに書き込まれます）|
| `ERISPULSE_PORT` | `8000` | Dashboardのポートマッピング |
| `ERISPULSE_TAG` | `latest` | イメージタグ、`dev`に設定するとプレリリースイメージを使用します |
| `ERISPULSE_BUILD_TARGET` | `production` | ビルドターゲット：`production`（安定版）または `dev`（プレリリース版）|
| `CONTAINER_NAME` | `erispulse` | コンテナ名 |
| `TZ` | `Asia/Shanghai` | コンテナのタイムゾーン |
| `LANG` | `en_US.UTF-8` | システム言語、起動時のインターフェース言語を自動検出します |
| `ERISPULSE_LANG` | 空 | 起動時のインターフェース言語を強制設定：`zh` / `zh_TW` / `en` / `ja` / `ru`（`LANG`を上書きします）|

</details>

### 1Panelアプリストア

[1Panel](https://1panel.cn)アプリストアからErisPulseをワンクリックでインストールできます。詳細は[ErisPulse-1Panel](https://github.com/ErisPulse/ErisPulse-1Panel)を参照してください。

```bash
bash <(curl -sL https://get-1panel.erisdev.com/install.sh)
```

ErisPulseは1Panelのサードパーティアプリストアに登録されており、[okxlin/appstore](https://github.com/okxlin/appstore)サードパーティリポジトリを使用してインストールできます。

### pipを使用する

```bash
pip install ErisPulse
```

> 上記のワンクリックインストールスクリプトを使用して、環境を自動検出し、設定を誘導することもできます。

### プロジェクトの初期化

```bash
# インタラクティブな初期化
epsdk init

# 速やかな初期化（プロジェクト名を指定）
epsdk init -q -n my_bot
```

### 最初のボットを作成する

`main.py`ファイルを作成します：

<table>
<tr>
<td width="50%" valign="top">

**コマンドハンドラ**

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command

@command("hello", help="挨拶メッセージを送信")
async def hello_handler(event):
    user_name = event.get_user_nickname() or "友達"
    await event.reply(f"こんにちは、{user_name}！")

@command("ping", help="ボットがオンラインかどうかをテスト")
async def ping_handler(event):
    await event.reply("Pong！ボットは正常に動作しています。")

if __name__ == "__main__":
    import asyncio
    asyncio.run(sdk.run(keep_running=True))
```

</td>
<td width="50%" valign="top">

**効果の説明**

`/hello`を送信

ボットの返信：`こんにちは、{ユーザー名}！`

---

`/ping`を送信

ボットの返信：`Pong！ボットは正常に動作しています。`

---

**実行方法**

```bash
epsdk run main.py
# または開発モード
epsdk run main.py --reload
```

</td>
</tr>
</table>

詳細な説明は以下のドキュメントを参照してください：
- [速習ガイド](docs/ja/quick-start.md)
- [入門ガイド](docs/ja/getting-started/)

---

## 同じコードで複数のプラットフォーム

*完全に同じコマンドハンドラ。異なるプラットフォーム。業務ロジックを一切変更せずに対応。*

<table>
<tr>
<td align="center" width="33%">

**Kook**

<img src=".github/assets/demo-kook.png" alt="Kookデモ" />

</td>
<td align="center" width="33%">

**QQ**

<img src=".github/assets/demo-qq.png" alt="QQデモ" />

</td>
<td align="center" width="33%">

**云湖**

<img src=".github/assets/demo-yunhu.png" alt="云湖デモ" />

</td>
</tr>
</table>

---

## チェーン式送信DSL

`@ユーザー`、返信、再試行、タイムアウト、コールバックなど、すべての送信ロジックを1つのチェーンで完了できます：

```python
yunhu = sdk.adapter.get("yunhu")

# 単発送信：@ユーザー + 返信 + 再試行 + 成功コールバック
await (yunhu.Send.To("group", "123")
       .At("456").Reply("msg_789")
       .Retry(3).Timeout(10)
       .Hook(lambda r: print("送信成功！"))
       .Text("こんにちは"))

# バッチ送信：1つのチェーンで複数のメッセージを送信
results = await (yunhu.Send.To("user", "123")
                .Build()
                .Text("通知1")
                .Image("pic.jpg")
                .Retry(2)
                .send_all())
```

> Hook（成功コールバック）、Retry（失敗再試行）、Timeout（タイムアウトキャンセル）、OnProgress（進行状況監視）、Defer（遅延送信）、Build（バッチ構築）などのチェーンメソッドがサポートされています。詳細は[SendDSLドキュメント](docs/ja/developer-guide/adapters/send-dsl.md)を参照してください。

---

## マルチホップ対話例

ErisPulseには強力なマルチホップ対話エンジンが内蔵されており、誘導操作や情報収集などのインタラクティブなシナリオを簡単に実現できます：

```python
from ErisPulse.Core.Event import command, request

@command("register")
async def register_handler(event):
    conv = event.conversation(timeout=60)
    
    await conv.say("ようこそ登録！")
    
    # 複数ステップでユーザー情報を収集し、自動的に検証
    data = await conv.collect([
        {"key": "name", "prompt": "名前を入力してください"},
        {"key": "age", "prompt": "年齢を入力してください",
         "validator": lambda e: e.get_text().strip().isdigit(),
         "retry_prompt": "年齢は数字でなければなりません、再入力してください"},
    ])
    
    if data and await conv.confirm(f"登録を確認しますか？名前: {data['name']}, 年齢: {data['age']}"):
        # SendDSLを使用して通知を送信
        await sdk.adapter.get(event.get_platform()).Send.To(
            "user", event.get_user_id()
        ).Text(f"登録成功！ようこそ {data['name']}")
        # または await event.reply("登録成功！")

# フレンドリクエストを自動処理
@request.on_friend_request()
async def handle_friend_request(event):
    user_name = event.get_user_nickname() or event.get_user_id()
    
    # リクエストを承認
    result = await event.approve()
    if result.get("status") == "ok":
        await event.reply(f"自動でフレンドリクエストを承認しました、ようこそ {user_name}")
```

<details>
<summary>Conversation APIの詳細（ブランチジャンプ / 選択 / 永続化）</summary>

```python
@command("quiz")
async def quiz_handler(event):
    conv = event.conversation(timeout=30)
    
    # 選択式の質問
    answer = await conv.choose("Pythonの作成者は誰ですか？", [
        "Guido van Rossum",
        "James Gosling", 
        "Dennis Ritchie",
    ])
    
    if answer == 0:
        await conv.say("正解です！")
    elif answer is None:
        await conv.say("タイムアウトしました、次回また来てください！")
    else:
        await conv.say("間違っています、正解はGuido van Rossumです")

@command("menu")
async def menu_handler(event):
    conv = event.conversation(timeout=60)
    
    # ブランチジャンプで複雑なインタラクティブフローを構築
    @conv.branch("main")
    async def main_menu():
        await conv.say("=== メインメニュー ===\n1. 本人情報\n2. 設定\n3. 終了")
        resp = await conv.wait()
        if resp and resp.get_text().strip() == "1":
            await conv.goto("profile")
    
    @conv.branch("profile")
    async def profile():
        await conv.say("名前: Alice\n0. 戻る")
        resp = await conv.wait()
        if resp and resp.get_text().strip() == "0":
            await conv.goto("main")
    
    await conv.start()
```

[Conversationマルチホップ対話](docs/ja/advanced/conversation.md)を参照してください。

</details>

---

## 核心モジュール

ErisPulseは包括的な多プラットフォームチャットボット開発ツールチェーンを提供し、各モジュールがそれぞれの役割を果たします：

```mermaid
graph TB
    SDK["sdk<br/>統一エントリーポイント"]

    SDK --> Event["Event<br/>イベントシステム"]
    SDK --> AdapterMgr["Adapter<br/>アダプタ管理"]
    SDK --> ModuleMgr["Module<br/>モジュール管理"]
    SDK --> Router["Router<br/>HTTP/WSルーティング"]
    SDK --> Storage["Storage<br/>SQLiteストレージ"]
    SDK --> Config["Config<br/>設定管理"]
    SDK --> Lifecycle["Lifecycle<br/>ライフサイクル"]
    SDK --> Logger["Logger<br/>ロギングシステム"]
    SDK --> Client["HttpClient<br/>HTTPクライアント"]
```

| モジュール | 説明 |
|------|------|
| **Event** | イベントシステム、command / message / notice / request / meta 5種類のイベントとConversationマルチホップ対話 |
| **Adapter** | アダプタ管理、BaseAdapter基底クラスによる統一イベント変換とSendDSL送信、QQ / Telegram / Kook / 云湖 / 微信公式アカウントなど15以上のプラットフォームをサポート |
| **Module** | モジュール管理、BaseModule基底クラス + 依存関係宣言とトポロジカルソートによるロード |
| **SendDSL** | チェーン式送信、@/返信/再試行/タイムアウト/バッチなどの複雑なロジックを1行で完了 |
| **Router** | HTTP/WebSocketルーティングシステム（FastAPI + Uvicorn）|
| **Storage** | SQLiteをベースとしたキーバリュー型ストレージ + 一般的なSQLチェーン式クエリ |
| **Config** | TOML形式の設定管理 |
| **Lifecycle** | ライフサイクルイベントフック（core.init / adapter.* / module.*）|
| **Logger** | モジュール化されたロギングシステム、サブロガーをサポート |
| **HttpClient** | 統一HTTP/WSクライアント（aiohttpベース）、リトライとErisPulse例外体系を内蔵 |

初期化プロセス、ライフサイクルイベント、モジュールロード戦略などの詳細設計は、[アーキテクチャ概要](docs/ja/architecture.md)を参照してください。

---

## スコープ（Scope）——3次元の権限制御

モジュールコードを一切変更することなく、設定で「どの範囲で有効か」を一括宣言できます：

```toml
[ErisPulse.scope.platforms.onebot11]
modules = ["Chat", "Tool*"]           # ① モジュール次元：このプラットフォームではこれらのモジュールのみを開放（glob / 正規表現）

[ErisPulse.scope.identity.users.onebot11]
deny = ["u_bad", "spam_*"]            # ② 身元次元：ブラックリストのユーザーのイベントは直接破棄

[ErisPulse.scope.actions.MyModule]
send = { allow = ["Text"] }           # ③ 出力次元：このモジュールはテキストのみを送信可能
api = { deny = ["set_*", "leave_*"] } #    管理系APIを禁止
```

```python
# 実行時でも呼び出し可能、直ちに有効（点分パス形式の辞書読み書きが可能）
sdk.scope.set_action("MyModule", "api", deny=["set_*"])
```

> [スコープ（scope）](docs/ja/advanced/scope.md)を参照してください。

---

## イベント上書き——モジュールコードを変更せず、任意のイベントタイプの動作を上書き

```toml
# メッセージハンドラのトリガ条件を上書き（コード内の条件とAND；meta/message/notice/request/command全タイプに対応）
[ErisPulse.event.overrides.message.ChatModule]
pattern = "雑談*"

# コマンド実装のパラメータを上書き（master / hidden / aliases / prefixなど、ユーザー優先）
[ErisPulse.event.overrides.command.MyModule.restart]
master = true
```

> [イベント上書き](docs/ja/getting-started/event-handling.md)を参照してください。

---

## エコシステム

ErisPulseはフレームワークにとどまらず、インストール後すぐに利用可能で、ゼロから車輪を作り直す必要はありません。

<table>
<tr>
<td align="center" width="25%">

**フレームワーク**

コアランタイム

統一イベント＆メッセージモデル

</td>
<td align="center" width="25%">

**Dashboard**

ビジュアル管理

プラグイン・ログ・設定

[オンラインデモ →](https://dashdemo.erisdev.com/)

</td>
<td align="center" width="25%">

**AI Builder**

自然言語 → 利用可能なモジュール

[体験する →](https://builder.erisdev.com)

</td>
<td align="center" width="25%">

**モジュール市場**

即座に使えるプラグイン

[モジュールを閲覧 →](https://www.erisdev.com/#market)

</td>
</tr>
<tr>
<td align="center" width="25%">

**アダプタ**

15以上のプラットフォーム接続

</td>
<td align="center" width="25%">

**ErisPulse-App**

公式マルチデバイスクライアント

スマホで直接実行・デスクトップトレイ常駐

[ダウンロード・インストール →](https://github.com/ErisPulse/ErisPulse-App/releases)

</td>
<td align="center" width="25%">

**Docker**

多アーキテクチャ対応

`erispulse/erispulse`

</td>
<td align="center" width="25%">

**ドキュメント & CLI**

[erisdev.com](https://www.erisdev.com)

`epsdk`フットスタックツール

</td>
</tr>
</table>

---

## 対応プラットフォーム

プラットフォームのアダプタを貢献していただけると幸いです！どこから始めればよいか分からない場合は、[貢献ガイド](docs/ja/contributing/README.md)をご覧ください。

| アダプタ | 説明 |
|--------|------|
| <img src=".github/assets/adapter_logo/kook.svg" height="20" alt="Kook" /> [Kook](https://github.com/shanfishapp/ErisPulse-KookAdapter) | Kook（開黑啦）即時通信プラットフォーム |
| <img src=".github/assets/adapter_logo/matrix.svg" height="20" alt="Matrix" /> [Matrix](https://github.com/ErisPulse/ErisPulse-MatrixAdapter) | Matrix分散型通信プロトコル |
| <img src=".github/assets/adapter_logo/onebot.png" height="20" alt="OneBot" /> [OneBot11](https://github.com/ErisPulse/ErisPulse-OneBot11Adapter) | OneBot v11 一般ロボットプロトコル |
| <img src=".github/assets/adapter_logo/onebot.png" height="20" alt="OneBot" /> [OneBot12](https://github.com/ErisPulse/ErisPulse-OneBot12Adapter) | OneBot v12 標準プロトコル |
| <img src=".github/assets/adapter_logo/qqbot.svg" height="20" alt="QQ" /> [QQ](https://github.com/ErisPulse/ErisPulse-QQBotAdapter) | QQ公式ロボットプラットフォーム |
| <img src=".github/assets/adapter_logo/sandbox.png" height="20" alt="Sandbox" /> [Sandbox](https://github.com/ErisPulse/ErisPulse-SandboxAdapter) | ウェブ端末デバッグ、実際のプラットフォームに接続せずに |
| <img src=".github/assets/adapter_logo/terminal.svg" height="20" alt="Terminal" /> [Terminal](https://github.com/ErisPulse/ErisPulse-TerminalAdapter) | コマンドライン即チャット、設定不要の開発・デバッグ |
| <img src=".github/assets/adapter_logo/telegram.svg" height="20" alt="Telegram" /> [Telegram](https://github.com/ErisPulse/ErisPulse-TelegramAdapter) | グローバルな即時通信プラットフォーム |
| <img src=".github/assets/adapter_logo/email.svg" height="20" alt="Email" /> [メール](https://github.com/ErisPulse/ErisPulse-EmailAdapter) | メールプロトコル送受信アダプタ |
| <img src=".github/assets/adapter_logo/yunhu.png" height="20" alt="Yunhu" /> [云湖](https://github.com/ErisPulse/ErisPulse-YunhuAdapter) | 企業向け即時通信プラットフォーム（ロボット接続） |
| <img src=".github/assets/adapter_logo/yunhu.png" height="20" alt="Yunhu" /> [云湖ユーザー](https://github.com/wsu2059q/ErisPulse-YunhuUserAdapter) | 云湖ユーザープロトコルに基づく接続アダプタ |
| [花枫咖啡馆](https://github.com/ErisPulse/ErisPulse-Ideaura/) | Allons! \(・ω・) / |
| <img src=".github/assets/adapter_logo/discord.svg" height="20" alt="Discord" /> [Discord](https://github.com/ErisPulse/ErisPulse-DiscordAdapter) | グローバルなコミュニティ通信プラットフォーム、サーバー、チャンネル、プライベートメッセージに対応 |
| <img src=".github/assets/adapter_logo/webhook.svg" height="20" alt="Webhook" /> [Webhook](https://github.com/ErisPulse/ErisPulse-WebhookAdapter) | 一般的なHTTPブリッジアダプタ、任意のシステムに接続 |
| <img src=".github/assets/adapter_logo/wechatmp.svg" height="20" alt="WechatMp" /> [微信公式アカウント](https://github.com/ErisPulse/ErisPulse-WechatMpAdapter) | 微信公式アカウントプラットフォーム |

アダプタの詳細は[プラットフォームガイド](docs/ja/platform-guide/README.md)をご覧ください。

---

## コミュニティ

私たちと交流しましょう：

- Telegram: <https://t.me/ErisPulse>
- QQグループ: <https://qm.qq.com/q/TOwnCmypcy>
- 云湖グループ: <https://yhfx.jwznb.com/share?key=VWJL4fTWXepa&ts=1781889199>

---

### 貢献ガイド

ErisPulseプロジェクトの健全性はあなたの貢献にも依存します！あらゆる形態の貢献を歓迎します：

1. **問題報告** — [GitHub Issues](https://github.com/ErisPulse/ErisPulse/issues)にバグレポートを提出
2. **機能リクエスト** — [コミュニティディスカッション](https://github.com/ErisPulse/ErisPulse/discussions)で新アイデアを提案
3. **コード貢献** — PRを提出する前に[コードスタイル](docs/ja/styleguide/)と[貢献ガイド](CONTRIBUTING.md)を読んでください
4. **ドキュメント改善** — ドキュメントやサンプルコードを改善する

**初めての貢献？** ここから始めましょう 👉 [初めての貢献実践](docs/ja/contributing/first-contribution.md)

[コミュニティディスカッションに参加](https://github.com/ErisPulse/ErisPulse/discussions)

---

<div align="center">

### 感謝

<img src=".github/assets/thanks.png" width="200" alt="感謝" />

本プロジェクトの一部のコードは[sdkFrame](https://github.com/runoneall/sdkFrame)に基づいています。

コアアダプタの標準化層は[OneBot12規格](https://12.onebot.dev/)を参考にしており、その恩恵を受けています。

特に云湖エコシステムとコミュニティに感謝します。

ErisPulseの初期の探求と成長は云湖開発者コミュニティのサポートに欠かせません。多くのアイデア、アダプタ、実践的な経験がここで生まれました。

また、ErisPulse、OneBotエコシステム、およびオープンソースコミュニティに貢献したすべての開発者やプロジェクト作者に感謝します。

</div>