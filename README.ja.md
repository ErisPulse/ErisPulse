<img src=".github/assets/mascot-hero.png" align="right" width="300" alt="ErisPulse" style="margin-left: 24px; margin-bottom: 16px; border-radius: 12px;" />

[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | **日本語** | [Русский](README.ru.md)

# ErisPulse

**イベント駆動型マルチプラットフォームロボット開発フレームワーク**

OneBot12標準インターフェースを基に、1回の記述で複数プラットフォームに展開可能。柔軟なプラグインシステム、ホットリロードサポート、開発者向けの完全なツールチェーンを備え、単純なチャットボットから複雑な自動化システムまで、あらゆる場面に対応します。

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
  <a href="https://www.erisdev.com/#market"><img src="https://img.shields.io/badge/模块市场-erisdev.com-C724B1?style=for-the-badge&logo=webpack&logoColor=white" alt="模块市场"></a>
  <a href="https://github.com/ErisPulse/ErisPulse/discussions"><img src="https://img.shields.io/badge/GitHub-Discussions-181717?style=for-the-badge&logo=github" alt="讨论"></a>
</p>

<br clear="both">

---

<div align="center">

### 核心特性 · AI モジュールビルダー

</div>

> 👉 **自然言語で要望を記述し、AIが公式ドキュメントを参照してモジュール/アダプターのコードを生成し、ダウンロードできる**  
> [**今すぐ体験 → `https://www.erisdev.com/#builder`**](https://www.erisdev.com/#builder)
>
> 生成可能なモジュール: アダプター、機能モジュール、プラグインテンプレート
>
> Vibe Coding ワークフローもサポート — AIが生成した素材をダウンロードして、AIに送信するだけで使用可能 [詳細](docs/ja/quick-start.md)

<table>
<tr>
<td width="50%" align="center" valign="top">
<br/>

### ⚡ イベント駆動アーキテクチャ

OneBot12標準に基づく明確なイベントモデルにより、メッセージ処理がより直感的かつ効率的になります

</td>
<td width="50%" align="center" valign="top">
<br/>

### 🌐 プラットフォーム間互換性

プラグインモジュールは1回の記述で全てのプラットフォームで使用可能。異なるプラットフォーム用に再開発する必要はありません

</td>
</tr>
<tr>
<td width="50%" align="center" valign="top">
<br/>

### 🧩 モジュール設計

柔軟なプラグインシステムにより、拡張や統合が容易で、ホットプラグイン管理が可能

</td>
<td width="50%" align="center" valign="top">
<br/>

### 🔄 ホットリロード + AI補助

開発中は再起動せずにコードを再読み込み可能。AI補助開発により要望を直接使えるモジュールに変換

</td>
</tr>
</table>

---

### 速習

#### 1クリックインストールスクリプト（推奨）

インストールスクリプトは環境（Docker、Python、uv）を自動検出し、最適なインストール方法を案内します。多言語対応（中国語/English/日本語/Русский/繁体中国語）。

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
# docker-compose.ymlをダウンロード
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# Dashboardログイントークンを設定して起動
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

> イメージにはErisPulseフレームワークとDashboard管理パネルが含まれており、`linux/amd64`および`linux/arm64`アーキテクチャをサポートしています。

起動後、`http://<host>:<port>/Dashboard`にアクセスし、設定したトークンをパスワードとして使用してDashboard管理パネルにログインします。

</details>

<details>
<summary>開発用バージョンの使用 (Dev)</summary>

`ERISPULSE_CHANNEL=dev`を設定することで、開発用バージョンを使用できます：

```bash
# 方式一：環境変数を使用（推奨）
ERISPULSE_CHANNEL=dev ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d

# 方式二：devイメージをビルド
ERISPULSE_BUILD_TARGET=dev docker compose up -d --build
```

最新バージョンに自動的に更新したい場合は、`ERISPULSE_UPDATE_ON_START=true`を明示的に設定します：

```bash
ERISPULSE_CHANNEL=dev ERISPULSE_UPDATE_ON_START=true docker compose up -d
```

また、事前ビルドされたdevイメージを取得することも可能です：

```bash
docker pull erispulse/erispulse:dev
```

</details>

<details>
<summary>Docker環境変数</summary>

| 変数 | デフォルト値 | 説明 |
|------|--------|------|
| `ERISPULSE_CHANNEL` | `stable` | バージョンチャンネル：`stable`（安定版）または `dev`（開発版） |
| `ERISPULSE_UPDATE_ON_START` | `false` | コンテナ起動時に最新バージョンに自動更新するかどうか（明示的に有効化する必要があります） |
| `ERISPULSE_DASHBOARD_TOKEN` | 空 | Dashboardログイントークン |
| `ERISPULSE_PORT` | `8000` | Dashboardポートマッピング |
| `TZ` | `Asia/Shanghai` | コンテナのタイムゾーン |

> `ERISPULSE_UPDATE_ON_START=true`を有効にすることで、イメージが古くてもコンテナ起動時に最新バージョンを自動的に取得できます。

</details>

#### 1Panelアプリストア

[1Panel](https://1panel.cn)アプリストアからErisPulseを1クリックでインストールできます。詳細は[ErisPulse-1Panel](https://github.com/ErisPulse/ErisPulse-1Panel)をご覧ください。

```bash
bash <(curl -sL https://get-1panel.erisdev.com/install.sh)
```

#### pipを使用する

```bash
pip install ErisPulse
```

> 上記の1クリックインストールスクリプトを使用することもでき、環境を自動検出し、設定を案内します。

#### 実行効果

##### ダッシュボード:

[![オンラインデモ](https://img.shields.io/badge/オンラインデモ-Dashboard-FF6B9D?style=for-the-badge&logo=github&logoColor=white)](https://dashdemo.erisdev.com/)

> 💡 オンラインデモダッシュボードを体験: [DashDemo](https://dashdemo.erisdev.com/)

<table>
<tr>
<td width="50%">

<img src=".github/assets/docs/dashboard.png" alt="Dashboardデモ" />

</td>
<td width="50%">

<video src="https://github.com/user-attachments/assets/157191c4-9a84-433c-b311-0c57e3a21151" controls width="100%"></video>

</td>
</tr>
</table>


##### 同じコードで、複数のプラットフォームに反応:

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

#### プロジェクトの初期化

```bash
# インタラクティブ初期化
epsdk init

# 速攻初期化（プロジェクト名を指定）
epsdk init -q -n my_bot
```

#### 最初のロボットを作成する

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

**効果説明**

`/hello`を送信

ロボットの返信: `你好，{用户名}！`

---

`/ping`を送信

ロボットの返信: `Pong！ロボットは正常に動作しています。`

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

#### マルチホップ対話の例

ErisPulseには強力なマルチホップ対話エンジンが内蔵されており、誘導操作、情報収集などのインタラクティブなシーンを簡単に実現できます：

```python
from ErisPulse.Core.Event import command, request

@command("register")
async def register_handler(event):
    conv = event.conversation(timeout=60)
    
    await conv.say("ようこそ登録！")
    
    # 複数ステップでユーザー情報を収集し、自動検証
    data = await conv.collect([
        {"key": "name", "prompt": "お名前を入力してください"},
        {"key": "age", "prompt": "年齢を入力してください",
         "validator": lambda e: e.get_text().strip().isdigit(),
         "retry_prompt": "年齢は数字でなければなりません。もう一度入力してください"},
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
        await event.reply(f"自動でフレンドリクエストを承認しました。ようこそ {user_name}")
```

<details>
<summary>Conversation APIの詳細（分岐/選択/永続化）</summary>

```python
@command("quiz")
async def quiz_handler(event):
    conv = event.conversation(timeout=30)
    
    # 選択肢付きの質問
    answer = await conv.choose("Pythonの作成者は誰ですか？", [
        "Guido van Rossum",
        "James Gosling", 
        "Dennis Ritchie",
    ])
    
    if answer == 0:
        await conv.say("正解です！")
    elif answer is None:
        await conv.say("時間切れです。また来てください！")
    else:
        await conv.say("不正解です。正解はGuido van Rossumです")

@command("menu")
async def menu_handler(event):
    conv = event.conversation(timeout=60)
    
    # 分岐処理、複雑な対話フローを構築
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

### 対応するアダプター

アダプターの貢献をお待ちしています！

| アダプター | 説明 |
|--------|------|
| <img src=".github/assets/adapter_logo/kook.svg" height="20" alt="Kook" /> [Kook](https://github.com/shanfishapp/ErisPulse-KookAdapter) | Kook（开黑啦）インスタントメッセージプラットフォーム |
| <img src=".github/assets/adapter_logo/matrix.svg" height="20" alt="Matrix" /> [Matrix](https://github.com/ErisPulse/ErisPulse-MatrixAdapter) | Matrix分散型通信プロトコル |
| <img src=".github/assets/adapter_logo/onebot.png" height="20" alt="OneBot" /> [OneBot11](https://github.com/ErisPulse/ErisPulse-OneBot11Adapter) | OneBot v11 一般的なロボットプロトコル |
| <img src=".github/assets/adapter_logo/onebot.png" height="20" alt="OneBot" /> [OneBot12](https://github.com/ErisPulse/ErisPulse-OneBot12Adapter) | OneBot v12 標準プロトコル |
| <img src=".github/assets/adapter_logo/qqbot.svg" height="20" alt="QQ" /> [QQ](https://github.com/ErisPulse/ErisPulse-QQBotAdapter) | QQ公式ロボットプラットフォーム |
| <img src=".github/assets/adapter_logo/sandbox.png" height="20" alt="Sandbox" /> [Sandbox](https://github.com/ErisPulse/ErisPulse-SandboxAdapter) | ウェブ端末のデバッグ、実際のプラットフォームに接続する必要なし |
| <img src=".github/assets/adapter_logo/telegram.svg" height="20" alt="Telegram" /> [Telegram](https://github.com/ErisPulse/ErisPulse-TelegramAdapter) | グローバルなインスタントメッセージプラットフォーム |
| <img src=".github/assets/adapter_logo/email.svg" height="20" alt="Email" /> [Email](https://github.com/ErisPulse/ErisPulse-EmailAdapter) | 電子メールプロトコルの送受信アダプター |
| <img src=".github/assets/adapter_logo/yunhu.png" height="20" alt="Yunhu" /> [云湖](https://github.com/ErisPulse/ErisPulse-YunhuAdapter) | 企業向けインスタントメッセージプラットフォーム（ロボット接続） |
| <img src=".github/assets/adapter_logo/yunhu.png" height="20" alt="Yunhu" /> [云湖用户](https://github.com/wsu2059q/ErisPulse-YunhuUserAdapter) | 雲湖ユーザー協定に基づく接続アダプター |
| [花枫咖啡馆](https://github.com/ErisPulse/ErisPulse-Ideaura/) | Allons! \(・ω・) / |
| <img src=".github/assets/adapter_logo/discord.svg" height="20" alt="Discord" /> [Discord](https://github.com/ErisPulse/ErisPulse-DiscordAdapter) | グローバルなコミュニティコミュニケーションプラットフォーム、サーバー、チャンネル、プライベートメッセージをサポート |
| <img src=".github/assets/adapter_logo/webhook.svg" height="20" alt="Webhook" /> [Webhook](https://github.com/ErisPulse/ErisPulse-WebhookAdapter) | 一般的なHTTPブリッジアダプター、任意のシステムに接続 |
| <img src=".github/assets/adapter_logo/wechatmp.svg" height="20" alt="WechatMp" /> [微信公众号](https://github.com/ErisPulse/ErisPulse-WechatMpAdapter) | 微信公式公众号プラットフォーム |

アダプターの詳細は[アダプター紹介](docs/ja/platform-guide/README.md)をご覧ください。

---

### 応用例

<div align="center">

| マルチプラットフォームロボット | チャットアシスタント | 自動化ツール | メッセージ転送 |
|:---:|:---:|:---:|:---:|
| 複数プラットフォームに<br>同じ機能のロボットを展開 | AIチャットモジュールを接続<br>エンターテインメントとインタラクションを実現 | メッセージ通知、タスク管理<br>データ収集 | 複数プラットフォーム間のメッセージ<br>同期と転送 |

</div>

---

### 貢献ガイド

ErisPulseプロジェクトの健全性には、皆様の貢献が必要です！あらゆる形態の貢献を歓迎します：

1. **問題報告** — [GitHub Issues](https://github.com/ErisPulse/ErisPulse/issues)でバグ報告を送信
2. **機能リクエスト** — [コミュニティ議論](https://github.com/ErisPulse/ErisPulse/discussions)で新アイデアを提案
3. **コード貢献** — PRを送信する前に[コードスタイル](docs/ja/styleguide/)と[貢献ガイド](CONTRIBUTING.md)を読む
4. **ドキュメント改善** — ドキュメントとサンプルコードを改善する

[コミュニティ議論に参加](https://github.com/ErisPulse/ErisPulse/discussions)

---

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=ErisPulse/ErisPulse&type=Date)](https://star-history.com/#ErisPulse/ErisPulse&Date)

---

<div align="center">

### 致謝

<img src=".github/assets/thanks.png" width="200" alt="感謝" />

本プロジェクトの一部のコードは[sdkFrame](https://github.com/runoneall/sdkFrame)に基づいています。コアアダプターの標準化層は[OneBot12規格](https://12.onebot.dev/)に基づいています。オープンソースコミュニティに貢献してくださったすべての開発者と著者に感謝します。

</div>