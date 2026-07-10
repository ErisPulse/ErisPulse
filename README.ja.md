<img src=".github/assets/mascot-hero.png" align="right" width="300" alt="ErisPulse" style="margin-left: 24px; margin-bottom: 16px; border-radius: 12px;" />

[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | **日本語** | [Русский](README.ru.md)

# ErisPulse

**一次書き込み、複数プラットフォームへのデプロイ。**

イベント駆動型のマルチプラットフォームチャットボット開発フレームワーク。

OneBot12標準インターフェースに基づき、一度書き込めば複数プラットフォームにデプロイ可能。柔軟なプラグインシステム、ホットリロードサポート、および完全な開発者ツールチェーンにより、シンプルなチャットボットから複雑な自動化システムまで、あらゆるシナリオに対応。

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

### 主な特徴

</div>

<table>
<tr>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_event_driven.png.png" width="50" alt="イベント駆動アーキテクチャ" />

### イベント駆動アーキテクチャ

OneBot12標準に基づく明確なイベントモデルにより、メッセージ処理ロジックをより直感的かつ効率的に実現

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_cross_platform.png.png" width="50" alt="マルチプラットフォーム互換性" />

### マルチプラットフォーム互換性

プラグインモジュールを一度書けば、すべてのプラットフォームで使用可能。異なるプラットフォームごとに再開発する必要がない

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_modular.png" width="50" alt="モジュール化設計" />

### モジュール化設計

柔軟なプラグインシステム。拡張や統合が容易。ホットプラグイン管理が可能

</td>
</tr>
<tr>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_hot_reload.png" width="50" alt="ホットリロード" />

### ホットリロード

開発時に再起動せずにコードを再読み込み可能

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_ai_assist.png" width="50" alt="AI支援" />

### AI支援

AIによる開発支援により、要望を即座に利用可能なモジュールへと変換

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_lightweight.png" width="50" alt="シンプルで優雅" />

### シンプルで優雅

直感的なAPI設計により、コードが羽毛のように軽く読みやすい

</td>
</tr>
</table>

### 鏈式送信DSL

1つのチェーン呼び出しで、メンション、返信、再試行、タイムアウト、コールバックなど、すべての送信ロジックを完了：

```python
yunhu = sdk.adapter.get("yunhu")

# 単発送信：ユーザーをメンション + 返信 + 再試行 + 成功コールバック
await (yunhu.Send.To("group", "123")
       .At("456").Reply("msg_789")
       .Retry(3).Timeout(10)
       .Hook(lambda r: print("送信成功！"))
       .Text("你好"))

# 一括送信：1つのチェーンで複数のメッセージを送信
results = await (yunhu.Send.To("user", "123")
                .Build()
                .Text("通知一")
                .Image("pic.jpg")
                .Retry(2)
                .send_all())
```

> Hook（成功コールバック）、Retry（失敗再試行）、Timeout（タイムアウトキャンセル）、OnProgress（進行状況監視）、Defer（遅延送信）、Build（一括構築）などのチェーンメソッドがサポートされています。詳細は[SendDSLドキュメント](docs/ja/developer-guide/adapters/send-dsl.md)をご覧ください。

---

## 同じコード。複数のプラットフォーム。

*まったく同じコマンドハンドラ。異なるプラットフォーム。ビジネスロジックを一切変更する必要がない。*

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

## エコシステム

ErisPulseはフレームワークにとどまらない。インストールしてすぐに始められる。ゼロから車輪を作り直す必要はない。

<table>
<tr>
<td align="center" width="25%">

**フレームワーク**

コアランタイム

統一されたイベント&メッセージモデル

</td>
<td align="center" width="25%">

**ダッシュボード**

可視化管理

プラグイン・ログ・設定

[オンラインデモ →](https://dashdemo.erisdev.com/)

</td>
<td align="center" width="25%">

**AI Builder**

自然言語 → 利用可能なモジュール

[体験する →](https://www.erisdev.com/#builder)

</td>
<td align="center" width="25%">

**モジュールマーケット**

すぐに使えるプラグイン

[モジュールを閲覧 →](https://www.erisdev.com/#market)

</td>
</tr>
<tr>
<td align="center" width="25%">

**アダプター**

15以上のプラットフォーム接続

</td>
<td align="center" width="25%">

**ドキュメント**

[erisdev.com](https://www.erisdev.com)

</td>
<td align="center" width="25%">

**Docker**

マルチアーキテクチャ対応

`erispulse/erispulse`

</td>
<td align="center" width="25%">

**CLI**

`epsdk` フッターツール

</td>
</tr>
</table>

---

## プロジェクトの起源

ErisPulseは、フレームワークになるために生まれたわけではありません。

それは、**Amer** というプロジェクトから始まりました。これは、異なるプラットフォーム間のメッセージの相互接続と同期を目的としたプロジェクトでした。

接続するプラットフォームが増えるにつれ、**ryunhusdk2の非同期バージョン**を維持し、統一されたイベントモデルとアダプター体系を段階的に抽象化していきました。

これらの実践が、今日のErisPulseに発展しました。

ErisPulseの目標は、常に変わっていません：

**開発者がプラットフォームの違いではなく、ビジネスに集中できるようにすること。**

---

### すぐに始める

#### 1クリックインストールスクリプト（推奨）

インストールスクリプトは、環境（Docker、Python、uv）を自動的に検出し、最も適したインストール方法を案内します。多言語（中国語/English/日本語/Русский/繁體中文）をサポートしています。

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

#### Dockerを使用する（推奨）

```bash
docker pull erispulse/erispulse:latest
```

<details>
<summary>Docker Hubが使用できない場合</summary>

Docker Hubにアクセスできない場合は、GitHub Container Registryを使用できます：

```bash
docker pull ghcr.io/erispulse/erispulse:latest
```

ghcr.ioのイメージを使用する場合、`docker-compose.yml`のimageを変更する必要があります：
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

> イメージにはErisPulseフレームワークとDashboard管理パネルが含まれており、`linux/amd64`と`linux/arm64`アーキテクチャをサポートしています。

起動後、`http://<host>:<port>/Dashboard`にアクセスし、設定したトークンをパスワードとして使用してDashboard管理パネルにログインします。

</details>

<details>
<summary>開発版（Dev）を使用する</summary>

`ERISPULSE_CHANNEL=dev`を設定することで開発版を使用できます：

```bash
# 方法1：環境変数を使用（推奨）
ERISPULSE_CHANNEL=dev ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d

# 方法2：devイメージをビルド
ERISPULSE_BUILD_TARGET=dev docker compose up -d --build
```

最新バージョンに自動更新したい場合は、`ERISPULSE_UPDATE_ON_START=true`を明示的に設定します：

```bash
ERISPULSE_CHANNEL=dev ERISPULSE_UPDATE_ON_START=true docker compose up -d
```

また、事前構築されたdevイメージを取得することもできます：

```bash
docker pull erispulse/erispulse:dev
```

</details>

<details>
<summary>Docker環境変数</summary>

| 変数 | デフォルト値 | 説明 |
|------|--------|------|
| `ERISPULSE_CHANNEL` | `stable` | バージョンチャネル：`stable`（安定版）または `dev`（開発版） |
| `ERISPULSE_UPDATE_ON_START` | `false` | コンテナ起動時に自動的に最新バージョンに更新するかどうか（明示的に有効にする必要あり） |
| `ERISPULSE_DASHBOARD_TOKEN` | 空 | Dashboardログイントークン |
| `ERISPULSE_PORT` | `8000` | Dashboardポートマッピング |
| `TZ` | `Asia/Shanghai` | コンテナのタイムゾーン |

> `ERISPULSE_UPDATE_ON_START=true`を設定することで、イメージが古くてもコンテナが起動時に最新バージョンを自動的に取得できるようになります。

</details>

#### 1Panelアプリストア

[1Panel](https://1panel.cn)アプリストアからErisPulseをワンクリックでインストールできます。詳細は[ErisPulse-1Panel](https://github.com/ErisPulse/ErisPulse-1Panel)をご覧ください。

```bash
bash <(curl -sL https://get-1panel.erisdev.com/install.sh)
```

ErisPulseは1Panelのサードパーティアプリストアに登録されており、[okxlin/appstore](https://github.com/okxlin/appstore)サードパーティリポジトリを使用してインストールできます。

#### pipを使用してインストール

```bash
pip install ErisPulse
```

> 上記のワンクリックインストールスクリプトを使用して、環境を自動的に検出し、設定をガイドすることもできます。

#### プロジェクトの初期化

```bash
# 対話形式で初期化
epsdk init

# プロジェクト名を指定して迅速初期化
epsdk init -q -n my_bot
```

#### 最初のボットを作成する

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
    user_name = event.get_user_nickname() or "朋友"
    await event.reply(f"你好，{user_name}！")

@command("ping", help="ロボットがオンラインかどうかをテスト")
async def ping_handler(event):
    await event.reply("Pong！ロボットは正常に動作しています。")

if __name__ == "__main__":
    import asyncio
    asyncio.run(sdk.run(keep_running=True))
```

</td>
<td width="50%" valign="top">

**動作説明**

`/hello`を送信

ロボットが返信：`你好，{ユーザー名}！`

---

`/ping`を送信

ロボットが返信：`Pong！ロボットは正常に動作しています。`

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
- [クイックスタートガイド](docs/ja/quick-start.md)
- [入門ガイド](docs/ja/getting-started/)

#### マルチホップ対話例

ErisPulseには強力なマルチホップ対話エンジンが内蔵されており、誘導操作、情報収集などのインタラクティブなシナリオを簡単に実現できます：

```python
from ErisPulse.Core.Event import command, request

@command("register")
async def register_handler(event):
    conv = event.conversation(timeout=60)
    
    await conv.say("ようこそ登録へ！")
    
    # 複数ステップでユーザー情報を収集し、自動的に検証
    data = await conv.collect([
        {"key": "name", "prompt": "名前を入力してください"},
        {"key": "age", "prompt": "年齢を入力してください",
         "validator": lambda e: e.get_text().strip().isdigit(),
         "retry_prompt": "年齢は数字でなければなりません。もう一度入力してください。"},
    ])
    
    if data and await conv.confirm(f"登録を確認しますか？名前: {data['name']}, 年齢: {data['age']}"):
        # SendDSLを使用して通知を送信
        await sdk.adapter.get(event.get_platform()).Send.To(
            "user", event.get_user_id()
        ).Text(f"登録成功！{data['name']}さん、ようこそ！")
        # または await event.reply("登録成功！")

# フレンドリクエストの自動処理
@request.on_friend_request()
async def handle_friend_request(event):
    user_name = event.get_user_nickname() or event.get_user_id()
    
    # リクエストを承認
    result = await event.approve()
    if result.get("status") == "ok":
        await event.reply(f"自動でフレンドリクエストを承認しました。{user_name}さん、ようこそ！")
```

<details>
<summary>Conversation APIの詳細（分岐/選択/永続化）をもっと見る</summary>

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
        await conv.say("タイムアウトしました。またお越しください！")
    else:
        await conv.say("不正解です。正解はGuido van Rossumです。")

@command("menu")
async def menu_handler(event):
    conv = event.conversation(timeout=60)
    
    # 分岐遷移。複雑なインタラクティブフローを構築
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

## 対応プラットフォーム

アダプターの貢献をお待ちしています！

| アダプター | 説明 |
|--------|------|
| <img src=".github/assets/adapter_logo/kook.svg" height="20" alt="Kook" /> [Kook](https://github.com/shanfishapp/ErisPulse-KookAdapter) | Kook（开黑啦）インスタントメッセージプラットフォーム |
| <img src=".github/assets/adapter_logo/matrix.svg" height="20" alt="Matrix" /> [Matrix](https://github.com/ErisPulse/ErisPulse-MatrixAdapter) | Matrix分散型通信プロトコル |
| <img src=".github/assets/adapter_logo/onebot.png" height="20" alt="OneBot" /> [OneBot11](https://github.com/ErisPulse/ErisPulse-OneBot11Adapter) | OneBot v11 一般的なロボットプロトコル |
| <img src=".github/assets/adapter_logo/onebot.png" height="20" alt="OneBot" /> [OneBot12](https://github.com/ErisPulse/ErisPulse-OneBot12Adapter) | OneBot v12 標準プロトコル |
| <img src=".github/assets/adapter_logo/qqbot.svg" height="20" alt="QQ" /> [QQ](https://github.com/ErisPulse/ErisPulse-QQBotAdapter) | QQ公式ロボットプラットフォーム |
| <img src=".github/assets/adapter_logo/sandbox.png" height="20" alt="Sandbox" /> [Sandbox](https://github.com/ErisPulse/ErisPulse-SandboxAdapter) | ウェブ端末のデバッグ。実際のプラットフォームに接続する必要なし |
| <img src=".github/assets/adapter_logo/telegram.svg" height="20" alt="Telegram" /> [Telegram](https://github.com/ErisPulse/ErisPulse-TelegramAdapter) | 世界的なインスタントメッセージプラットフォーム |
| <img src=".github/assets/adapter_logo/email.svg" height="20" alt="Email" /> [Email](https://github.com/ErisPulse/ErisPulse-EmailAdapter) | メールプロトコル送受信アダプター |
| <img src=".github/assets/adapter_logo/yunhu.png" height="20" alt="Yunhu" /> [云湖](https://github.com/ErisPulse/ErisPulse-YunhuAdapter) | 企業向けインスタントメッセージプラットフォーム（ロボット接続） |
| <img src=".github/assets/adapter_logo/yunhu.png" height="20" alt="Yunhu" /> [云湖ユーザー](https://github.com/wsu2059q/ErisPulse-YunhuUserAdapter) | 云湖ユーザープロトコルに基づく接続アダプター |
| [花枫咖啡馆](https://github.com/ErisPulse/ErisPulse-Ideaura/) | Allons! \(・ω・) / |
| <img src=".github/assets/adapter_logo/discord.svg" height="20" alt="Discord" /> [Discord](https://github.com/ErisPulse/ErisPulse-DiscordAdapter) | 世界的なコミュニティコミュニケーションプラットフォーム。サーバー、チャンネル、プライベートメッセージをサポート |
| <img src=".github/assets/adapter_logo/webhook.svg" height="20" alt="Webhook" /> [Webhook](https://github.com/ErisPulse/ErisPulse-WebhookAdapter) | 一般的なHTTPブリッジアダプター。任意のシステムに接続可能 |
| <img src=".github/assets/adapter_logo/wechatmp.svg" height="20" alt="WechatMp" /> [微信公众号](https://github.com/ErisPulse/ErisPulse-WechatMpAdapter) | 微信公式公众号プラットフォーム |

アダプターの詳細は[アダプター紹介](docs/ja/platform-guide/README.md)をご覧ください。

---

### 応用シーン

<div align="center">

| マルチプラットフォームロボット | チャットアシスタント | 自動化ツール | メッセージ転送 |
|:---:|:---:|:---:|:---:|
| 複数のプラットフォームに<br>同じ機能のロボットを展開 | AIチャットモジュールを接続<br>エンターテイメントやインタラクションを実現 | メッセージ通知、タスク管理<br>データ収集 | 複数プラットフォーム間のメッセージ<br>同期と転送 |

</div>

---

## コミュニティ

ErisPulseコミュニティに参加して、開発者と共同でエコシステムを構築しましょう。

### 云湖

グループID: `635409929`

グループチャットに参加:

https://yhfx.jwznb.com/share?key=VWJL4fTWXepa&ts=1781889199

### QQグループ

https://qm.qq.com/q/TOwnCmypcy

### Telegram

https://t.me/ErisPulse

---

### 貢献ガイド

ErisPulseプロジェクトの健全性には、皆様の力が必要です！さまざまな形での貢献を歓迎します：

1. **問題報告** — [GitHub Issues](https://github.com/ErisPulse/ErisPulse/issues) でバグ報告を提出
2. **機能リクエスト** — [コミュニティディスカッション](https://github.com/ErisPulse/ErisPulse/discussions) で新しいアイデアを提案
3. **コード貢献** — PRを提出する前に[コードスタイル](docs/ja/styleguide/)と[貢献ガイド](CONTRIBUTING.md)を読んでください
4. **ドキュメント改善** — ドキュメントとサンプルコードを改善するのを手伝ってください

[コミュニティディスカッションに参加](https://github.com/ErisPulse/ErisPulse/discussions)

---

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=ErisPulse/ErisPulse&type=Date)](https://star-history.com/#ErisPulse/ErisPulse&Date)

---

<div align="center">

### 謝辞

<img src=".github/assets/thanks.png" width="200" alt="感謝" />

本プロジェクトの一部のコードは[sdkFrame](https://github.com/runoneall/sdkFrame)に基づいています。

コアアダプターの標準化層は[OneBot12規格](https://12.onebot.dev/)を参考にしており、その恩恵を受けています。

特に云湖エコシステムとコミュニティに感謝します。

ErisPulseの初期探索と成長は、云湖開発者コミュニティのサポートに大きく依存しています。多くのアイデア、アダプター、実践的な経験がここから生まれました。

また、ErisPulse、OneBotエコシステム、オープンソースコミュニティに貢献したすべての開発者とプロジェクト作者に感謝します。

</div>