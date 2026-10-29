<img src=".github/assets/mascot-hero.png" align="right" width="300" alt="ErisPulse" style="margin-left: 24px; margin-bottom: 16px; border-radius: 12px;" />

[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | **日本語** | [Русский](README.ru.md)

# ErisPulse

**一次書き込み、QQ / Telegram / Kook / 云湖 / 微信公众号 / OneBot12 / ... など複数のプラットフォームに展開。**

OneBot12 標準インターフェースに基づき、イベント駆動型のモジュラーアシンクロニスロボットフレームワーク。ビジネスコードは1回だけ記述し、アダプタが各プラットフォームの差異を抽象化。プラグインシステム、ホットリロード、完全な開発者ツールチェーンが即座に利用可能。

<p>
  <a href="https://pypi.org/project/ErisPulse/"><img src="https://img.shields.io/pypi/v/ErisPulse?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI"></a>
  <a href="https://pypi.org/project/ErisPulse/"><img src="https://img.shields.io/badge/Python-3.10+-FFD43B?style=for-the-badge&logo=python&logoColor=blue" alt="Python"></a>
  <a href="https://github.com/botuniverse/onebot-11"><img src="https://img.shields.io/badge/OneBot-11-black?style=for-the-badge" alt="OneBot 11"></a>
  <a href="https://12.onebot.dev/"><img src="https://img.shields.io/badge/OneBot-12-black?style=for-the-badge" alt="OneBot 12"></a>
  <a href="https://hub.docker.com/r/erispulse/erispulse"><img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker"></a>
  <a href="https://github.com/ErisPulse/ErisPulse/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="License"></a>
  <a href="https://pepy.tech/project/ErisPulse"><img src="https://img.shields.io/pepy/dt/ErisPulse?style=for-the-badge&color=blue" alt="Downloads"></a>
  <a href="https://github.com/ErisPulse/ErisPulse/stargazers"><img src="https://img.shields.io/github/stars/ErisPulse/ErisPulse?style=for-the-badge&logo=github&color=yellow" alt="Stars"></a>
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

OneBot12 の統一イベントモデルに基づき、1つのハンドラで全てのアダプタに対応

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_cross_platform.png.png" width="50" alt="クロスプラットフォーム互換性" />

### クロスプラットフォーム互換性

QQ / Telegram / Kook / 云湖 など 15+ プラットフォーム、ビジネスコードは変更なし

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_modular.png" width="50" alt="モジュール設計" />

### モジュール設計

プラグインのホットプラグイン / ホットリロード、プラットフォーム / Bot / セッションごとのスコープ制御

</td>
</tr>
<tr>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_hot_reload.png" width="50" alt="ホットリロード" />

### ホットリロード

保存即有効、軽量で無感覚なホットリロード

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_ai_assist.png" width="50" alt="AI支援" />

### AI支援

自然言語で要件を記述し、即座に使用可能なモジュールを生成

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_lightweight.png" width="50" alt="簡潔でエレガント" />

### 簡潔でエレガント

チェーン式API：@ユーザー、返信、再試行、一括送信を1行で完了

</td>
</tr>
</table>

---

## 作業原理

ErisPulse はアダプタ層でプラットフォームの差異を抽象化し、ビジネスコードはイベント自体のみを意識するようにします：

```mermaid
graph LR
    P["15+ プラットフォーム<br/>QQ · Telegram · Kook · 云湖 · 微信公众号 · 郵便 · Webhook ..."]
    A["アダプタ層<br/>各プロトコル → OneBot12 標準イベント"]
    Event["Event イベントバス<br/>ミドルウェア → 分類 command/message/notice/request/meta"]
    M["ビジネスモジュール<br/>@command / @message ハンドラ・あなたのモジュール"]
    P --> A --> Event --> M
    M -.->|"event.reply() / SendDSL"| Event
```

- **アダプタ層**は各プラットフォームのプロトコルを OneBot12 標準イベントに変換し、ビジネスモジュールはプラットフォームの差異を意識しない
- **Event バス**はミドルウェアチェーンを実行した後、イベントタイプに応じて5種類のハンドラに分類する
- **あなたのコード**はデコレータでイベントをサブスクライブし、`event.reply()` または SendDSL で返信する。返信メッセージは同じ経路を逆流してプラットフォームに送信される

モジュールの構成、初期化プロセス、ライフサイクルイベントなどの設計詳細は、[アーキテクチャ概要](docs/ja/architecture.md)をご覧ください。

---

## 速習

### 1クリックインストールスクリプト（推奨）

インストールスクリプトは、Docker、Python、uv などの環境を自動検出し、最適なインストール方法を案内します。多言語（日本語/English/日本語/Русский/繁體中文）に対応しています。

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

**Docker インストールデモ**

<video src="https://github.com/user-attachments/assets/a367a466-4678-46a9-b101-073a86388ede" controls width="100%"></video>

</td>
<td align="center" width="50%">

**pip インストールデモ**

<video src="https://github.com/user-attachments/assets/a2df4009-dba6-411e-b79d-4454a168d063" controls width="100%"></video>

</td>
</tr>
</table>

### Docker を使用する（推奨）

```bash
docker pull erispulse/erispulse:latest
```

<details>
<summary>Docker Hub が利用できない？</summary>

Docker Hub にアクセスできない場合は、GitHub Container Registry を使用できます：

```bash
docker pull ghcr.io/erispulse/erispulse:latest
```

ghcr.io レジストリを使用する場合、`docker-compose.yml` の image を変更する必要があります：
```yaml
image: ghcr.io/erispulse/erispulse:latest
```

</details>

<details>
<summary>クイック起動</summary>

```bash
# docker-compose.yml をダウンロード
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# Dashboard ログイントークンを設定して起動
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

起動後、`http://<host>:8000/Dashboard` にアクセスし、設定したトークンで Dashboard 管理パネルにログインします。

> イメージには ErisPulse フレームワークと Dashboard 管理パネルが内蔵されており、`linux/amd64` および `linux/arm64` アーキテクチャをサポートします。
>
> **永続化**：設定ファイルとインストールされたモジュール/アダプタはボリュームマウントによりホストに永続化され、コンテナの再起動後も失われません。フレームワーク自体の更新は Dashboard でホットアップデートされます。

</details>

<details>
<summary>Docker 環境変数</summary>

| 変数 | デフォルト値 | 説明 |
|------|--------|------|
| `ERISPULSE_DASHBOARD_TOKEN` | 空 | Dashboard ログイントークン（設定すると自動的に設定ファイルに書き込まれます）|
| `ERISPULSE_PORT` | `8000` | Dashboard ポートマッピング |
| `ERISPULSE_TAG` | `latest` | イメージタグ、`dev` に設定するとプレリリースイメージを使用します |
| `CONTAINER_NAME` | `erispulse` | コンテナ名 |
| `TZ` | `Asia/Shanghai` | コンテナのタイムゾーン |
| `LANG` | `en_US.UTF-8` | システム言語、起動時のインターフェース言語を自動検出します |
| `ERISPULSE_LANG` | 空 | 起動時のインターフェース言語を強制指定：`zh` / `zh_TW` / `en` / `ja` / `ru`（`LANG` を上書きします）|

</details>

### 1Panel アプリストア

[1Panel](https://1panel.cn) アプリストアから ErisPulse をワンクリックでインストールできます。詳しくは [ErisPulse-1Panel](https://github.com/ErisPulse/ErisPulse-1Panel) をご覧ください。

```bash
bash <(curl -sL https://get-1panel.erisdev.com/install.sh)
```

ErisPulse は 1Panel 第三者アプリストアに登録されており、[okxlin/appstore](https://github.com/okxlin/appstore) 第三者リポジトリを使用してインストールできます。

### pip を使用する

```bash
pip install ErisPulse
```

`epsdk` をグローバルコマンドとして使用したい場合、`uv tool install` を推奨します：

```bash
uv tool install ErisPulse
```

> 上記の 1クリックインストールスクリプトを使用して、環境を自動検出し設定を誘導することもできます（スクリプトメニューには「グローバル CLI インストール（uv tool）」のオプションも用意されています）。

### プロジェクトの初期化

```bash
# インタラクティブな初期化
epsdk init

# ファスト初期化（プロジェクト名を指定）
epsdk init -q -n my_bot
```

### 最初のロボットを作成する

`main.py` ファイルを作成します：

<table>
<tr>
<td width="50%" valign="top">

**コマンドハンドラ**

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command

@command("hello", help="挨拶メッセージを送信")
async def hello_handler(event):
    user_name = event.get_user_nickname() or "友人"
    await event.reply(f"こんにちは、{user_name}！")

@command("ping", help="ロボットがオンラインかテスト")
async def ping_handler(event):
    await event.reply("Pong！ロボットは正常に動作しています。")

if __name__ == "__main__":
    import asyncio
    asyncio.run(sdk.run(keep_running=True))
```

</td>
<td width="50%" valign="top">

**動作説明**

`/hello` を送信

ロボットは `こんにちは、{ユーザー名}！` と返信

---

`/ping` を送信

ロボットは `Pong！ロボットは正常に動作しています。` と返信

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

詳細な説明は、以下のドキュメントをご覧ください：
- [速習ガイド](docs/ja/quick-start.md)
- [入門ガイド](docs/ja/getting-started/)

---

## 同じコード。複数のプラットフォーム。

*全く同じコマンドハンドラ。異なるプラットフォーム。ビジネスロジックを一切変更せずに利用可能。*

<table>
<tr>
<td align="center" width="33%">

**Kook**

<img src=".github/assets/demo-kook.png" alt="Kook デモ" />

</td>
<td align="center" width="33%">

**QQ**

<img src=".github/assets/demo-qq.png" alt="QQ デモ" />

</td>
<td align="center" width="33%">

**云湖**

<img src=".github/assets/demo-yunhu.png" alt="云湖 デモ" />

</td>
</tr>
</table>

---

## チェーン式送信 DSL

ユーザーへの @、返信、再試行、タイムアウト、成功コールバック——複雑な送信ロジックを1行のチェーンで記述可能：

```python
yunhu = sdk.adapter.get("yunhu")

# 単発：@ユーザー + 返信 + 再試行 + 成功コールバック
await (yunhu.Send.To("group", "123").At("456").Reply("msg_789")
       .Retry(3).Timeout(10)
       .Hook(lambda r: print("送信成功！")).Text("こんにちは"))

# 一括：1つのチェーンで複数メッセージを送信
results = await (yunhu.Send.To("user", "123").Build()
                 .Text("通知1").Image("pic.jpg").Retry(2).send_all())
```

> Hook / Retry / Timeout / OnProgress / Defer / Build などのチェーン式メソッドは、[SendDSL ドキュメント](docs/ja/developer-guide/adapters/send-dsl.md)をご覧ください。

---

## 複数回対話の例

情報を収集、入力の検証、送信の確認、対話のステータス管理は一切不要：

```python
from ErisPulse.Core.Event import command

@command("register")
async def register_handler(event):
    conv = event.conversation(timeout=60)
    await conv.say("ようこそ登録へ！")
    data = await conv.collect([
        {"key": "name", "prompt": "お名前を入力してください"},
        {"key": "age", "prompt": "年齢を入力してください",
         "validator": lambda e: e.get_text().strip().isdigit(),
         "retry_prompt": "年齢は数字でなければなりません。再度入力してください"},
    ])
    if data and await conv.confirm(f"登録を確認しますか？名前: {data['name']}, 年齢: {data['age']}"):
        await event.reply(f"登録完了！ようこそ {data['name']} さん")
```

> 選択肢付き質問（choose）、分岐移動（branch / goto）、永続化などの完全な機能は、[Conversation 複数回対話](docs/ja/advanced/conversation.md)をご覧ください。

---

## コアモジュール

1つの `sdk` エントリーポイントで、すべてのコア機能を統合します：

```mermaid
graph LR
    SDK["sdk 統一エントリーポイント"] --> Event & Adapter & Module & Router & Storage
    SDK --> Config & Lifecycle & Logger & HttpClient
```

| モジュール | 説明 |
|------|------|
| **Event** | イベントシステム、command / message / notice / request / meta 5種類のイベントと Conversation 複数回対話 |
| **Adapter** | アダプタ管理、BaseAdapter 基底クラスでイベント変換と SendDSL 送信を統一、QQ / Telegram / Kook / 云湖 / 微信公众号 など 15+ プラットフォームをサポート |
| **Module** | モジュール管理、BaseModule 基底クラス + 依存関係の宣言とトポロジカルソートによるロード |
| **SendDSL** | チェーン式送信、@/返信/再試行/タイムアウト/一括送信などの複雑なロジックを1行で完了 |
| **Router** | HTTP/WebSocket ルーティングシステム（FastAPI + Uvicorn）|
| **Storage** | SQLite をベースとしたキーバリュー格納 + 一般的なSQLチェーン式クエリ |
| **Config** | TOML 設定管理 |
| **Lifecycle** | ライフサイクルイベントフック（core.init / adapter.* / module.*）|
| **Logger** | モジュール化されたロガー、サブロガーをサポート |
| **HttpClient** | 統一された HTTP/WS クライアント（aiohttp をベース）、再試行と ErisPulse 例外体系を内蔵 |

初期化プロセス、ライフサイクルイベント、モジュールロード戦略などの設計詳細は、[アーキテクチャ概要](docs/ja/architecture.md)をご覧ください。

---

## スコープ（Scope）——3次元の権限制御

モジュールコードを一切変更せずに、設定で「どの範囲で有効か」を一括宣言可能：

```toml
[ErisPulse.scope.platforms.onebot11]
modules = ["Chat", "Tool*"]           # ① モジュール次元：このプラットフォームではこれらのモジュールのみを開放（glob / 正規表現）

[ErisPulse.scope.identity.users.onebot11]
deny = ["u_bad", "spam_*"]            # ② アイデンティティ次元：ブラックリストのユーザーのイベントは直接破棄

[ErisPulse.scope.actions.MyModule]
send = { allow = ["Text"] }           # ③ 出力次元：このモジュールはテキストのみを送信可能
api = { deny = ["set_*", "leave_*"] } #    管理系APIは禁止
```

```python
# 実行時にも呼び出し可能、即時有効（ドット区切りのパスによる辞書式読み書きがサポート）
sdk.scope.set_action("MyModule", "api", deny=["set_*"])
```

> 詳細は [スコープ（scope）](docs/ja/advanced/scope.md) をご覧ください。

---

## イベント上書き——モジュールコードを変更せずに、任意のイベントタイプの動作を上書き

トリガー語を変更したり、コマンドに管理者制限を追加したり、モジュールソースコードを変更せずに、設定で即時有効：

```toml
# メッセージハンドラのトリガー条件を上書き（コード内の条件とAND；meta/message/notice/request/command 全タイプ対応）
[ErisPulse.event.overrides.message.ChatModule]
pattern = "雑談*"

# コマンド実装のパラメータを上書き（master / hidden / aliases / prefix など、ユーザー優先）
[ErisPulse.event.overrides.command.MyModule.restart]
master = true
```

> 詳細は [イベント上書き](docs/ja/getting-started/event-handling.md) をご覧ください。

---

## エコシステム

ErisPulse は単なるフレームワークにとどまらず、すぐに使えるようになっています。ゼロからホイールを作り直す必要はありません。

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

自然言語 → 使用可能なモジュール

[体験する →](https://builder.erisdev.com)

</td>
<td align="center" width="25%">

**モジュール市場**

すぐに使えるプラグイン

[モジュールを見る →](https://www.erisdev.com/#market)

</td>
</tr>
<tr>
<td align="center" width="25%">

**アダプタ**

15+ プラットフォーム接続

</td>
<td align="center" width="25%">

**ErisPulse-App**

公式マルチデバイスクライアント

スマホで直接実行 · デスクトップトレイ常駐

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

`epsdk` フッターツール

</td>
</tr>
</table>

---

## 対応プラットフォーム

アダプタの貢献を歓迎します！どこから始めたらよいか分からない？[貢献ガイド](docs/ja/contributing/README.md)をご覧ください。

| アダプタ | 説明 |
|--------|------|
| <img src=".github/assets/adapter_logo/kook.svg" height="20" alt="Kook" /> [Kook](https://github.com/shanfishapp/ErisPulse-KookAdapter) | Kook（開黑啦）即時通信プラットフォーム |
| <img src=".github/assets/adapter_logo/matrix.svg" height="20" alt="Matrix" /> [Matrix](https://github.com/ErisPulse/ErisPulse-MatrixAdapter) | Matrix 分散型通信プロトコル |
| <img src=".github/assets/adapter_logo/onebot.png" height="20" alt="OneBot" /> [OneBot11](https://github.com/ErisPulse/ErisPulse-OneBot11Adapter) | OneBot v11 一般ロボットプロトコル |
| <img src=".github/assets/adapter_logo/onebot.png" height="20" alt="OneBot" /> [OneBot12](https://github.com/ErisPulse/ErisPulse-OneBot12Adapter) | OneBot v12 標準プロトコル |
| <img src=".github/assets/adapter_logo/qqbot.svg" height="20" alt="QQ" /> [QQ](https://github.com/ErisPulse/ErisPulse-QQBotAdapter) | QQ 公式ロボットプラットフォーム |
| <img src=".github/assets/adapter_logo/sandbox.png" height="20" alt="Sandbox" /> [Sandbox](https://github.com/ErisPulse/ErisPulse-SandboxAdapter) | ウェブ端のデバッグ、本番プラットフォーム接入不要 |
| <img src=".github/assets/adapter_logo/terminal.svg" height="20" alt="Terminal" /> [Terminal](https://github.com/ErisPulse/ErisPulse-TerminalAdapter) | コマンドラインでチャット、設定ゼロで開発・デバッグ |
| <img src=".github/assets/adapter_logo/telegram.svg" height="20" alt="Telegram" /> [Telegram](https://github.com/ErisPulse/ErisPulse-TelegramAdapter) | グローバルな即時通信プラットフォーム |
| <img src=".github/assets/adapter_logo/email.svg" height="20" alt="Email" /> [メール](https://github.com/ErisPulse/ErisPulse-EmailAdapter) | メールプロトコル受発信アダプタ |
| <img src=".github/assets/adapter_logo/yunhu.png" height="20" alt="Yunhu" /> [云湖](https://github.com/ErisPulse/ErisPulse-YunhuAdapter) | 企業向け即時通信プラットフォーム（ロボット接続） |
| <img src=".github/assets/adapter_logo/yunhu.png" height="20" alt="Yunhu" /> [云湖ユーザー](https://github.com/wsu2059q/ErisPulse-YunhuUserAdapter) | 云湖ユーザープロトコルに基づく接続アダプタ |
| [花枫咖啡馆](https://github.com/ErisPulse/ErisPulse-Ideaura/) | Allons! \(・ω・) / |
| <img src=".github/assets/adapter_logo/discord.svg" height="20" alt="Discord" /> [Discord](https://github.com/ErisPulse/ErisPulse-DiscordAdapter) | グローバルなコミュニティ通信プラットフォーム、サーバー、チャンネル、プライベートメッセージに対応 |
| <img src=".github/assets/adapter_logo/webhook.svg" height="20" alt="Webhook" /> [Webhook](https://github.com/ErisPulse/ErisPulse-WebhookAdapter) | 一般的な HTTP ブリッジアダプタ、任意のシステムに接続可能 |
| <img src=".github/assets/adapter_logo/wechatmp.svg" height="20" alt="WechatMp" /> [微信公众号](https://github.com/ErisPulse/ErisPulse-WechatMpAdapter) | 微信公式公众号プラットフォーム |

アダプタの詳細は [プラットフォームガイド](docs/ja/platform-guide/README.md) をご覧ください。

---

## コミュニティ

私たちと交流しましょう：

- Telegram：<https://t.me/ErisPulse>
- QQ グループ：<https://qm.qq.com/q/TOwnCmypcy>
- 云湖グループ：<https://yhfx.jwznb.com/share?key=VWJL4fTWXepa&ts=1781889199>

このプロジェクトが役立ったと感じたら、ぜひ [爱发电](https://ifdian.net/a/YingXinche) で継続的な開発を支援してください！

---

## Star History

ErisPulse が役立ったなら、ぜひ Star ⭐ を押してください——これは他の開発者がプロジェクトを知る最も直接的な方法です。

[![Star History Chart](https://api.star-history.com/svg?repos=ErisPulse/ErisPulse&type=Date)](https://star-history.com/#ErisPulse/ErisPulse&Date)

---

### 貢献ガイド

ErisPulse プロジェクトの健全性は、皆様の貢献によって支えられています！あらゆる形態での貢献を歓迎します：

1. **問題報告** — [GitHub Issues](https://github.com/ErisPulse/ErisPulse/issues) でバグ報告を送信
2. **機能リクエスト** — [コミュニティ議論](https://github.com/ErisPulse/ErisPulse/discussions) で新しいアイデアを提案
3. **コード貢献** — PR を送信する前に [コードスタイル](docs/ja/styleguide/) と [貢献ガイド](CONTRIBUTING.md) をご確認ください
4. **ドキュメント改善** — ドキュメントとサンプルコードの改善を支援

**初めての貢献？** ここから始めましょう 👉 [初めての貢献実践](docs/ja/contributing/first-contribution.md)

[コミュニティ議論に参加する](https://github.com/ErisPulse/ErisPulse/discussions)

---

<div align="center">

### 謝辞

<img src=".github/assets/thanks.png" width="200" alt="感謝" />

本プロジェクトの一部のコードは [sdkFrame](https://github.com/runoneall/sdkFrame) を基にしています。コアアダプタの標準化層は [OneBot12 規格](https://12.onebot.dev/) を参考にしており、その恩恵を受けています。

ErisPulse の初期探索と成長は、云湖開発者コミュニティのサポートに大きく依存しています。多くのアイデア、アダプタ、実践的な経験はここから生まれました。

また、ErisPulse、OneBot エコシステム、およびオープンソースコミュニティに貢献したすべての開発者やプロジェクト作者に感謝します。

</div>