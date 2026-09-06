<img src=".github/assets/mascot-hero.png" align="right" width="300" alt="ErisPulse" style="margin-left: 24px; margin-bottom: 16px; border-radius: 12px;" />

[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | **日本語** | [Русский](README.ru.md)

# ErisPulse

**一次编写，部署到 QQ / Telegram / Kook / Yunhu / 微信公众号 / OneBot12 / ... 多个平台。**

イベント駆動型のマルチプラットフォームチャットボット開発フレームワーク。

OneBot12標準インターフェースに基づき、一度の開発で複数のプラットフォームに展開可能。柔軟なプラグインシステム、ホットリロードのサポート、そして完全な開発者ツールチェーンにより、シンプルなチャットボットから複雑な自動化システムまで、あらゆるシーンに対応します。

<p>
  <a href="https://pypi.org/project/ErisPulse/"><img src="https://img.shields.io/pypi/v/ErisPulse?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI"></a>
  <a href="https://pypi.org/project/ErisPulse/"><img src="https://img.shields.io/badge/Python-3.10+-FFD43B?style=for-the-badge&logo=python&logoColor=blue" alt="Python"></a>
  <a href="https://hub.docker.com/r/erispulse/erispulse"><img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker"></a>
  <a href="https://github.com/ErisPulse/ErisPulse/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="License"></a>
  <a href="https://github.com/ErisPulse/ErisPulse"><img src="https://img.shields.io/github/stars/ErisPulse/ErisPulse?style=for-the-badge&logo=github&color=brightgreen" alt="Stars"></a>
  <a href="https://pepy.tech/project/ErisPulse"><img src="https://img.shields.io/pepy/dt/ErisPulse?style=for-the-badge&color=blue" alt="Downloads"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json&style=for-the-badge" alt="Ruff"></a>
  <a href="https://socket.dev/pypi/package/erispulse"><img src="https://img.shields.io/badge/Socket-Secure-2ea043?style=for-the-badge&logo=socket&logoColor=white" alt="Socket"></a>
  <a href="https://www.erisdev.com"><img src="https://img.shields.io/badge/文档-erisdev.com-FF6B9D?style=for-the-badge&logo=bookstack&logoColor=white" alt="文档"></a>
  <a href="https://deepwiki.com/ErisPulse/ErisPulse"><img src="https://img.shields.io/badge/DeepWiki-ErisPulse-8A2BE2?style=for-the-badge&logo=readthedocs&logoColor=white" alt="DeepWiki"></a>
  <a href="https://www.erisdev.com/#market"><img src="https://img.shields.io/badge/模块市场-erisdev.com-C724B1?style=for-the-badge&logo=webpack&logoColor=white" alt="模块市场"></a>
  <a href="https://github.com/ErisPulse/ErisPulse/discussions"><img src="https://img.shields.io/badge/GitHub-Discussions-181717?style=for-the-badge&logo=github" alt="讨论"></a>
</p>

<br clear="both">

---

<div align="center">

### 核心特性

</div>

<table>
<tr>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_event_driven.png.png" width="50" alt="イベント駆動アーキテクチャ" />

### イベント駆動アーキテクチャ

OneBot12標準に基づく統一イベントモデル——各プラットフォームごとにif/elif文でメッセージタイプを判断する必要がなくなり、1つのハンドラで全てのアダプタに自動的に適応します

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_cross_platform.png.png" width="50" alt="マルチプラットフォーム対応" />

### マルチプラットフォーム対応

同一の業務コードを全てのプラットフォームで実行可能——1度の開発でQQ / Telegram / Kook / Yunhu / 微信公众号等15以上のプラットフォームに対応し、重複開発が不要です

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_modular.png" width="50" alt="モジュラーアーキテクチャ" />

### モジュラーアーキテクチャ

柔軟なプラグインシステムによる実行時ホットプラグイン機能——モジュールのインストール/アンインストール/有効化/無効化はプロセスの再起動なしで可能。スコープシステムと連携して、プラットフォーム / Bot / セッションごとにモジュールの有効性を正確に制御し、ブロックのようにボット機能を組み立てることができます

</td>
</tr>
<tr>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_hot_reload.png" width="50" alt="ホットリロード" />

### ホットリロード

ローカルプラグインのファイル保存で即時有効化（0.5秒程度）、任意のモジュール（PyPIインストールパッケージ含む）`sdk.reload_module()` で1行でホットリロード可能。開発デバッグ体験はインタプリタ言語に近いです

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_ai_assist.png" width="50" alt="AI補助機能" />

### AI補助機能

自然言語で要望を記述して即座に実用可能なモジュールを生成——アダプタの書き方が分からない？AIに接続したいプラットフォームを伝えれば、自動でコードを生成します

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_lightweight.png" width="50" alt="シンプルでエレガント" />

### シンプルでエレガント

直感的なチェーン式API設計——@ユーザー、返信、リトライ、タイムアウト、コールバック等の複雑なロジックを1行で実現。コードは羽毛のように軽やかで読みやすいです

</td>
</tr>
</table>

---

## スコープ（Scope）——3次元の権限制御

モジュールのコードを変更することなく、設定で「どの範囲で有効か」を一括宣言できます：

```toml
[ErisPulse.scope.platforms.onebot11]
modules = ["Chat", "Tool*"]           # ① モジュール次元：このプラットフォームではこれらのモジュールのみ有効（glob / 正規表現）

[ErisPulse.scope.identity.users.onebot11]
deny = ["u_bad", "spam_*"]            # ② 身元次元：ブラックリストユーザーのイベントは直接破棄

[ErisPulse.scope.actions.MyModule]
send = { allow = ["Text"] }           # ③ 出力次元：このモジュールはテキストのみ送信可能
api = { deny = ["set_*", "leave_*"] } #    管理系APIは禁止
```

```python
# 実行時でも呼び出し可能で即座に有効（ドット区切りパスの辞書式読み書きが可能）
sdk.scope.set_action("MyModule", "api", deny=["set_*"])
```

> 詳しくは [スコープ（Scope）](docs/ja/advanced/scope.md) を参照してください

---

## イベントのオーバーライド——モジュールのコードを変更することなく、任意のイベントタイプの挙動を上書き

```toml
# メッセージハンドラのトリガ条件を上書き（コード内の条件とANDで評価、meta/message/notice/request/command全タイプ対応）
[ErisPulse.event.overrides.message.ChatModule]
pattern = "闲聊*"

# コマンド実装のパラメータを上書き（master / hidden / aliases / prefix等、ユーザー優先）
[ErisPulse.event.overrides.command.MyModule.restart]
master = true
```

> 詳しくは [イベントのオーバーライド](docs/ja/getting-started/event-handling.md) を参照してください

---

## 動作原理

ErisPulseはアダプタ層によってプラットフォームの差異を抽象化し、業務コードはイベントそのものにのみ注目します：

```mermaid
graph LR
    subgraph Platforms[プラットフォーム]
        QQ["QQ"]
        TG["Telegram"]
        Kook["Kook"]
        YH["云湖"]
        WX["微信公众号"]
    end

    subgraph Adapters[アダプタ層]
        A1["QQ 适配器"]
        A2["Telegram 适配器"]
        A3["Kook 适配器"]
        A4["云湖 适配器"]
        A5["微信 适配器"]
    end

    Event["Event 事件总线<br/>中间件 → 分发 command/message/notice/request/meta"]

    subgraph Modules[业务模块]
        M1["命令处理器<br/>@command"]
        M2["消息处理器<br/>@message"]
        M3["你的模块"]
    end

    QQ --> A1
    TG --> A2
    Kook --> A3
    YH --> A4
    WX --> A5

    A1 -->|"OB12 事件"| Event
    A2 -->|"OB12 事件"| Event
    A3 -->|"OB12 事件"| Event
    A4 -->|"OB12 事件"| Event
    A5 -->|"OB12 事件"| Event

    Event -->|"分发"| M1
    Event -->|"分发"| M2
    Event -->|"分发"| M3

    M1 -.->|"event.reply()<br/>SendDSL"| Event
    Event -.->|"发送"| A1
```

- **アダプタ層**は各プラットフォームのネイティブプロトコルをOneBot12標準イベントに変換し、業務モジュールはプラットフォームの差異を認識しません
- **Event バス**はまずミドルウェアチェーンを実行し、イベントタイプに応じて5種類のハンドラにイベントを分類します
- **あなたのコード**はデコレータでイベントをサブスクライブし、`event.reply()`またはSendDSLで返信します——返信メッセージは同じ経路を逆流してプラットフォームに送信されます

モジュールの構成、初期化フロー、ライフサイクルイベントなどの設計詳細は、[アーキテクチャ概要](docs/ja/architecture.md)を参照してください。

---

## 速習

### 1ステップインストールスクリプト（推奨）

インストールスクリプトは、環境（Docker、Python、uv）を自動検出し、最適なインストール方法をガイドします。多言語対応（中国語/English/日本語/Русский/繁體中文）。

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

Docker Hubがアクセスできない場合、GitHub Container Registryを使用できます：

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
# docker-compose.ymlをダウンロード
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# Dashboardログイントークンを設定して起動
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

起動後、`http://<host>:8000/Dashboard`にアクセスし、設定したトークンでDashboard管理パネルにログインします。

> イメージにはErisPulseフレームワークとDashboard管理パネルが内蔵されており、`linux/amd64`と`linux/arm64`アーキテクチャをサポートします。
>
> **永続化**：設定ファイルとインストールされたモジュール/アダプタはホストにマウントされたボリュームを通じて永続化され、コンテナの再起動後も失われません。フレームワーク自体の更新はDashboardのホットアップデートで完了します。

</details>

<details>
<summary>Docker環境変数</summary>

| 変数 | デフォルト値 | 説明 |
|------|--------|------|
| `ERISPULSE_DASHBOARD_TOKEN` | 空 | Dashboardログイントークン（設定すると自動的に設定ファイルに書き込まれます）|
| `ERISPULSE_PORT` | `8000` | Dashboardポートのマッピング |
| `ERISPULSE_TAG` | `latest` | イメージタグ、`dev`に設定するとプレリリースイメージを使用します |
| `ERISPULSE_BUILD_TARGET` | `production` | ビルドターゲット：`production`（安定版）または `dev`（プレリリース版）|
| `CONTAINER_NAME` | `erispulse` | コンテナ名 |
| `TZ` | `Asia/Shanghai` | コンテナのタイムゾーン |
| `LANG` | `en_US.UTF-8` | システム言語、起動時の言語を自動検出します |
| `ERISPULSE_LANG` | 空 | 起動時の言語を強制設定：`zh` / `zh_TW` / `en` / `ja` / `ru`（`LANG`を上書きします）|

</details>

### 1Panelアプリストア

[1Panel](https://1panel.cn)アプリストアからErisPulseを1ステップでインストールできます。詳しくは[ErisPulse-1Panel](https://github.com/ErisPulse/ErisPulse-1Panel)をご覧ください。

```bash
bash <(curl -sL https://get-1panel.erisdev.com/install.sh)
```

ErisPulseは1Panelのサードパーティアプリストアに登録されており、[okxlin/appstore](https://github.com/okxlin/appstore)サードパーティリポジトリを使用してインストールできます。

### pipを使用する

```bash
pip install ErisPulse
```

> 上記の1ステップインストールスクリプトを使用することもでき、環境を自動検出して設定をガイドします。

### プロジェクトの初期化

```bash
# インタラクティブな初期化
epsdk init

# 速攻初期化（プロジェクト名を指定）
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

@command("hello", help="送信する挨拶メッセージ")
async def hello_handler(event):
    user_name = event.get_user_nickname() or "朋友"
    await event.reply(f"你好，{user_name}！")

@command("ping", help="テスト用のコマンドで、ボットがオンラインか確認します")
async def ping_handler(event):
    await event.reply("Pong！ボットが正常に動作しています。")

if __name__ == "__main__":
    import asyncio
    asyncio.run(sdk.run(keep_running=True))
```

</td>
<td width="50%" valign="top">

**動作説明**

`/hello`を送信

ボットは`你好，{ユーザー名}！`と返信します

---

`/ping`を送信

ボットは`Pong！ボットが正常に動作しています。`と返信します

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

詳細な説明は以下のドキュメントをご覧ください：
- [速習ガイド](docs/ja/quick-start.md)
- [入門ガイド](docs/ja/getting-started/)

---

## 同じコード。複数のプラットフォーム。

*まったく同じコマンドハンドラ。異なるプラットフォーム。業務ロジックを一切変更する必要はありません。*

<table>
<tr>
<td align="center" width="33%">

**Kook**

<img src=".github/assets/demo-kook.png" alt="Kook 演示" />

</td>
<td align="center" width="33%">

**QQ**

<img src=".github/assets/demo-qq.png" alt="QQ 演示" />

</td>
<td align="center" width="33%">

**云湖**

<img src=".github/assets/demo-yunhu.png" alt="云湖 演示" />

</td>
</tr>
</table>

---

## チェーン式送信DSL

1つのチェーン呼び出しで、@ユーザー、返信、リトライ、タイムアウト、コールバックなどの送信ロジックをすべて1行で実行できます：

```python
yunhu = sdk.adapter.get("yunhu")

# 単発送信：@ユーザー + 返信 + リトライ + 成功コールバック
await (yunhu.Send.To("group", "123")
       .At("456").Reply("msg_789")
       .Retry(3).Timeout(10)
       .Hook(lambda r: print("送信成功！"))
       .Text("你好"))

# バッチ送信：1つのチェーンで複数のメッセージを送信
results = await (yunhu.Send.To("user", "123")
                .Build()
                .Text("通知一")
                .Image("pic.jpg")
                .Retry(2)
                .send_all())
```

> Hook（成功コールバック）、Retry（失敗リトライ）、Timeout（タイムアウトキャンセル）、OnProgress（進捗監視）、Defer（遅延送信）、Build（バッチ構築）などのチェーンメソッドがサポートされています。詳細は[SendDSLドキュメント](docs/ja/developer-guide/adapters/send-dsl.md)をご覧ください。

---

## マルチホップ対話例

ErisPulseには強力なマルチホップ対話エンジンが内蔵されており、誘導式操作や情報収集などのインタラクティブなシーンを簡単に実現できます：

```python
from ErisPulse.Core.Event import command, request

@command("register")
async def register_handler(event):
    conv = event.conversation(timeout=60)
    
    await conv.say("ようこそ登録！")
    
    # 複数ステップでユーザー情報を収集し、自動で検証
    data = await conv.collect([
        {"key": "name", "prompt": "名前を入力してください"},
        {"key": "age", "prompt": "年齢を入力してください",
         "validator": lambda e: e.get_text().strip().isdigit(),
         "retry_prompt": "年齢は数字でなければなりません。再度入力してください"},
    ])
    
    if data and await conv.confirm(f"登録を確認しますか？名前: {data['name']}, 年齢: {data['age']}"):
        # SendDSLを使って通知を送信
        await sdk.adapter.get(event.get_platform()).Send.To(
            "user", event.get_user_id()
        ).Text(f"登録成功！{data['name']}さん、ようこそ")
        # または await event.reply("登録成功！")

# フレンドリクエストを自動処理
@request.on_friend_request()
async def handle_friend_request(event):
    user_name = event.get_user_nickname() or event.get_user_id()
    
    # リクエストを承認
    result = await event.approve()
    if result.get("status") == "ok":
        await event.reply(f"フレンドリクエストを自動的に承認しました。ようこそ {user_name}")
```

<details>
<summary>Conversation APIの詳細（分岐/選択/永続化）</summary>

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
        await conv.say("時間切れです。また挑戦してください！")
    else:
        await conv.say("不正解です。正解はGuido van Rossumです。")

@command("menu")
async def menu_handler(event):
    conv = event.conversation(timeout=60)
    
    # 分岐遷移、複雑なインタラクティブフローを構築
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

[Conversationマルチホップ対話](docs/ja/advanced/conversation.md)をご覧ください。

</details>

---

## コアモジュール

ErisPulseは、完全なマルチプラットフォームボット開発ツールチェーンを提供し、コアモジュールはそれぞれ独自の役割を果たします：

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
    SDK --> Logger["Logger<br/>ログシステム"]
    SDK --> Client["HttpClient<br/>HTTPクライアント"]
```

| モジュール | 説明 |
|------|------|
| **Event** | イベントシステム、command / message / notice / request / meta 5種類のイベントとConversationマルチホップ対話 |
| **Adapter** | アダプタ管理、BaseAdapter基底クラスによる統一イベント変換とSendDSL送信、QQ / Telegram / Kook / 云湖 / 微信公众号等15以上のプラットフォームをサポート |
| **Module** | モジュール管理、BaseModule基底クラス + 依存宣言とトポロジカルソートによるロード |
| **SendDSL** | チェーン式送信、@/返信/リトライ/タイムアウト/バッチ送信などの複雑なロジックを1行で実現 |
| **Router** | HTTP/WebSocketルーティングシステム（FastAPI + Uvicorn）|
| **Storage** | SQLiteをベースとしたキーバリューストレージ + 一般的なSQLチェーン式クエリ |
| **Config** | TOML形式の設定管理 |
| **Lifecycle** | ライフサイクルイベントフック（core.init / adapter.* / module.*）|
| **Logger** | モジュール化されたログシステム、サブロガーをサポート |
| **HttpClient** | 統一HTTP/WSクライアント（aiohttpベース）、リトライとErisPulse独自の例外体系を内蔵 |

初期化フロー、ライフサイクルイベント、モジュールロード戦略などの設計詳細は、[アーキテクチャ概要](docs/ja/architecture.md)をご覧ください。

---

## エコシステム

ErisPulseはフレームワークにとどまりません。すぐに使えるように装備されており、ゼロから車輪を作成する必要はありません。

<table>
<tr>
<td align="center" width="25%">

**フレームワーク**

コアランタイム

統一イベント & メッセージモデル

</td>
<td align="center" width="25%">

**Dashboard**

ビジュアル管理

プラグイン · ログ · 設定

[オンラインデモ →](https://dashdemo.erisdev.com/)

</td>
<td align="center" width="25%">

**AI Builder**

自然言語 → 実用可能なモジュール

[体験する →](https://builder.erisdev.com)

</td>
<td align="center" width="25%">

**モジュール市場**

即座に使えるプラグイン

[モジュールを見る →](https://www.erisdev.com/#market)

</td>
</tr>
<tr>
<td align="center" width="25%">

**アダプタ**

15+のプラットフォーム接続

</td>
<td align="center" width="25%">

**ErisPulse-App**

公式マルチデバイスクライアント

スマホで直接実行 · デスクトップトレイ常駐

[ダウンロード →](https://github.com/ErisPulse/ErisPulse-App/releases)

</td>
<td align="center" width="25%">

**Docker**

多アーキテクチャ対応

`erispulse/erispulse`

</td>
<td align="center" width="25%">

**ドキュメント & CLI**

[erisdev.com](https://www.erisdev.com)

`epsdk` フッターツール

</td>
</tr>
</table>

---

## 対応プラットフォーム

アダプタの貢献を歓迎します！どこから始めればいいか分からない？[貢献ガイド](docs/ja/contributing/README.md)をご覧ください。

| アダプタ | 説明 |
|--------|------|
| <img src=".github/assets/adapter_logo/kook.svg" height="20" alt="Kook" /> [Kook](https://github.com/shanfishapp/ErisPulse-KookAdapter) | Kook（开黑啦）即時通信プラットフォーム |
| <img src=".github/assets/adapter_logo/matrix.svg" height="20" alt="Matrix" /> [Matrix](https://github.com/ErisPulse/ErisPulse-MatrixAdapter) | Matrix分散型通信プロトコル |
| <img src=".github/assets/adapter_logo/onebot.png" height="20" alt="OneBot" /> [OneBot11](https://github.com/ErisPulse/ErisPulse-OneBot11Adapter) | OneBot v11 通用ロボットプロトコル |
| <img src=".github/assets/adapter_logo/onebot.png" height="20" alt="OneBot" /> [OneBot12](https://github.com/ErisPulse/ErisPulse-OneBot12Adapter) | OneBot v12 標準プロトコル |
| <img src=".github/assets/adapter_logo/qqbot.svg" height="20" alt="QQ" /> [QQ](https://github.com/ErisPulse/ErisPulse-QQBotAdapter) | QQ公式ロボットプラットフォーム |
| <img src=".github/assets/adapter_logo/sandbox.png" height="20" alt="Sandbox" /> [沙箱](https://github.com/ErisPulse/ErisPulse-SandboxAdapter) | ウェブ端のデバッグ、実際のプラットフォームに接続する必要なし |
| <img src=".github/assets/adapter_logo/terminal.svg" height="20" alt="Terminal" /> [终端](https://github.com/ErisPulse/ErisPulse-TerminalAdapter) | コマンドライン即チャット、ゼロ設定で開発・デバッグ |
| <img src=".github/assets/adapter_logo/telegram.svg" height="20" alt="Telegram" /> [Telegram](https://github.com/ErisPulse/ErisPulse-TelegramAdapter) | 全球的な即時通信プラットフォーム |
| <img src=".github/assets/adapter_logo/email.svg" height="20" alt="Email" /> [邮件](https://github.com/ErisPulse/ErisPulse-EmailAdapter) | メールプロトコル送受信アダプタ |
| <img src=".github/assets/adapter_logo/yunhu.png" height="20" alt="Yunhu" /> [云湖](https://github.com/ErisPulse/ErisPulse-YunhuAdapter) | 企業向け即時通信プラットフォーム（ロボット接続） |
| <img src=".github/assets/adapter_logo/yunhu.png" height="20" alt="Yunhu" /> [云湖用户](https://github.com/wsu2059q/ErisPulse-YunhuUserAdapter) | 云湖ユーザープロトコルに基づく接続アダプタ |
| [花枫咖啡馆](https://github.com/ErisPulse/ErisPulse-Ideaura/) | Allons! \(・ω・) / |
| <img src=".github/assets/adapter_logo/discord.svg" height="20" alt="Discord" /> [Discord](https://github.com/ErisPulse/ErisPulse-DiscordAdapter) | 全球的なコミュニティ通信プラットフォーム、サーバー、チャンネル、プライベートメッセージをサポート |
| <img src=".github/assets/adapter_logo/webhook.svg" height="20" alt="Webhook" /> [Webhook](https://github.com/ErisPulse/ErisPulse-WebhookAdapter) | 一般的なHTTPブリッジアダプタ、任意のシステムに接続 |
| <img src=".github/assets/adapter_logo/wechatmp.svg" height="20" alt="WechatMp" /> [微信公众号](https://github.com/ErisPulse/ErisPulse-WechatMpAdapter) | 微信公式公众号プラットフォーム |

アダプタの詳細は[プラットフォームガイド](docs/ja/platform-guide/README.md)をご覧ください。

---

## コミュニティ

私たちと交流しましょう：

- Telegram：<https://t.me/ErisPulse>
- QQ 群：<https://qm.qq.com/q/TOwnCmypcy>
- 云湖群：<https://yhfx.jwznb.com/share?key=VWJL4fTWXepa&ts=1781889199>

---

### 貢献ガイド

ErisPulseプロジェクトの健全性はあなたの貢献によります！あらゆる形式の貢献を歓迎します：

1. **問題報告** — [GitHub Issues](https://github.com/ErisPulse/ErisPulse/issues) でバグ報告を投稿
2. **機能リクエスト** — [コミュニティディスカッション](https://github.com/ErisPulse/ErisPulse/discussions) で新しいアイデアを提案
3. **コード貢献** — PRを提出する前に[コードスタイル](docs/ja/styleguide/)と[貢献ガイド](CONTRIBUTING.md)を読む
4. **ドキュメント改善** — ドキュメントとサンプルコードを改善する

**初めての貢献？** ここから始めましょう 👉 [初めての貢献実践](docs/ja/contributing/first-contribution.md)

[コミュニティディスカッションに参加](https://github.com/ErisPulse/ErisPulse/discussions)

---

<div align="center">

### 謝辞

<img src=".github/assets/thanks.png" width="200" alt="感谢" />

本プロジェクトの一部のコードは [sdkFrame](https://github.com/runoneall/sdkFrame) に基づいています。

コアアダプタの標準化層は [OneBot12規格](https://12.onebot.dev/) を参考にしており、その恩恵を受けています。

特に云湖生態系とコミュニティに感謝します。

ErisPulseの初期探索と成長は云湖開発者コミュニティの支援により実現しました。
多くのアイデア、アダプタ、実践的な経験がここから生まれました。

また、ErisPulse、OneBotエコシステム、およびオープンソースコミュニティに貢献したすべての開発者とプロジェクト作者に感謝します。

</div>