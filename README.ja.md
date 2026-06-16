<table>
<tr>
<td width="35%" valign="middle" align="center">

<img src=".github/assets/mascot-hero.png" width="320" alt="ErisPulse" />

</td>
<td valign="middle">

> [English](README.en.md) | [简体中文](README.md) | [繁體中文](README.zh-TW.md) | **日本語** | [Русский](README.ru.md)

> 🎉 **v2.5.0-dev.1 は多言語をサポートしました！** フレームワークのコアと CLI インターフェースには、中国語（簡体/繁体）、英語、日本語、ロシア語が内蔵されており、システム言語を自動検出して切り替えます！

# ErisPulse

**イベント駆動型マルチプラットフォームロボット開発フレームワーク**

OneBot12標準インターフェースに基づき、一度のコード作成で複数プラットフォームに展開可能。柔軟なプラグインシステム、ホットリロードサポート、完全な開発者ツールチェーンを備え、シンプルなチャットボットから複雑な自動化システムまで、あらゆるシナリオに対応。

> Vibe Codingワークフローをサポートし、AIが直接使用可能なモジュールを生成します — [詳細](docs/ja/quick-start.md)

[![PyPI](https://img.shields.io/pypi/v/ErisPulse?style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/ErisPulse/)
[![Python](https://img.shields.io/badge/Python-3.10+-FFD43B?style=for-the-badge&logo=python&logoColor=blue)](https://pypi.org/project/ErisPulse/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://hub.docker.com/r/erispulse/erispulse)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](https://github.com/ErisPulse/ErisPulse/blob/main/LICENSE)
[![Stars](https://img.shields.io/github/stars/ErisPulse/ErisPulse?style=for-the-badge&logo=github&color=brightgreen)](https://github.com/ErisPulse/ErisPulse)
[![Downloads](https://img.shields.io/pepy/dt/ErisPulse?style=for-the-badge&color=blue)](https://pypi.org/project/ErisPulse/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json&style=for-the-badge)](https://github.com/astral-sh/ruff)
[![Socket](https://img.shields.io/badge/Socket-Secure-2ea043?style=for-the-badge&logo=socket&logoColor=white)](https://socket.dev/pypi/package/erispulse)

[![文档](https://img.shields.io/badge/文档-erisdev.com-FF6B9D?style=for-the-badge&logo=bookstack&logoColor=white)](https://www.erisdev.com)
[![模块市场](https://img.shields.io/badge/模块市场-erisdev.com-C724B1?style=for-the-badge&logo=webpack&logoColor=white)](https://www.erisdev.com/#market)
[![讨论](https://img.shields.io/badge/GitHub-Discussions-181717?style=for-the-badge&logo=github)](https://github.com/ErisPulse/ErisPulse/discussions)

</td>
</tr>
</table>

---

<div align="center">

### 核心特性

</div>

<table>
<tr>
<td width="50%" align="center" valign="top">
<br/>

### ⚡ イベント駆動アーキテクチャ

OneBot12標準に基づく明確なイベントモデルにより、メッセージ処理のロジックを直感的かつ効率的に実現します

</td>
<td width="50%" align="center" valign="top">
<br/>

### 🌐 プラットフォーム間互換性

プラグインモジュールを一度作成すれば、すべてのプラットフォームで使用可能。異なるプラットフォームごとの開発を繰り返す必要がありません

</td>
</tr>
<tr>
<td width="50%" align="center" valign="top">
<br/>

### 🧩 モジュール化設計

柔軟なプラグインシステムにより、拡張や統合が容易で、ホットプラグイン管理が可能です

</td>
<td width="50%" align="center" valign="top">
<br/>

### 🔄 ホットリロードサポート

開発時に再起動せずにコードを再読み込みできるため、開発の反復効率が大幅に向上します

</td>
</tr>
</table>

---

### 快速开始

#### 一键安装脚本（推荐）

インストールスクリプトは、環境（Docker、Python、uv）を自動検出し、最も適したインストール方法を選択します。多言語（中国語/English/日本語/Русский/繁體中文）に対応しています。

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

**Docker 安装演示**

<video src="https://github.com/user-attachments/assets/a367a466-4678-46a9-b101-073a86388ede" controls width="100%"></video>

</td>
<td align="center" width="50%">

**pip 安装演示**

<video src="https://github.com/user-attachments/assets/a2df4009-dba6-411e-b79d-4454a168d063" controls width="100%"></video>

</td>
</tr>
</table>

#### 使用 Docker (推荐)

```bash
docker pull erispulse/erispulse:latest
```

<details>
<summary>Docker Hub不可用？</summary>

Docker Hubにアクセスできない場合、GitHub Container Registryを使用できます：

```bash
docker pull ghcr.io/erispulse/erispulse:latest
```

ghcr.ioのイメージを使用する場合は、`docker-compose.yml`のimageを変更する必要があります：
```yaml
image: ghcr.io/erispulse/erispulse:latest
```

</details>

<details>
<summary>快速启动</summary>

```bash
# docker-compose.ymlをダウンロード
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# Dashboardログイントークンを設定して起動
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

> イメージにはErisPulseフレームワークとDashboard管理パネルが内蔵されており、`linux/amd64`および`linux/arm64`アーキテクチャをサポートしています。

起動後、`http://<host>:<port>/Dashboard`にアクセスし、設定したトークンをパスワードとして使用してDashboard管理パネルにログインします。

</details>

<details>
<summary>使用预发布版本 (Dev)</summary>

`ERISPULSE_CHANNEL=dev`を設定することで、予備リリース版を使用できます：

```bash
# 環境変数を使用する方法（推奨）
ERISPULSE_CHANNEL=dev ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d

# Devイメージを構築する方法
ERISPULSE_BUILD_TARGET=dev docker compose up -d --build
```

最新バージョンへの自動更新を起動時に有効にするには、`ERISPULSE_UPDATE_ON_START=true`を明示的に設定します：

```bash
ERISPULSE_CHANNEL=dev ERISPULSE_UPDATE_ON_START=true docker compose up -d
```

また、事前ビルドされたDevイメージを取得することも可能です：

```bash
docker pull erispulse/erispulse:dev
```

</details>

<details>
<summary>Docker 環境变量</summary>

| 変数 | デフォルト値 | 説明 |
|------|--------|------|
| `ERISPULSE_CHANNEL` | `stable` | バージョンチャンネル：`stable`（安定版）または `dev`（予備リリース版） |
| `ERISPULSE_UPDATE_ON_START` | `false` | コンテナ起動時に最新バージョンへの自動更新を有効にする |
| `ERISPULSE_DASHBOARD_TOKEN` | 空 | Dashboardログイントークン |
| `ERISPULSE_PORT` | `8000` | Dashboardポートマッピング |
| `TZ` | `Asia/Shanghai` | コンテナのタイムゾーン |

> `ERISPULSE_UPDATE_ON_START=true`を有効にすることで、イメージが古くても、コンテナ起動時に最新バージョンを自動的に取得できます。

</details>

#### 1Panel 应用商店

[1Panel](https://1panel.cn)アプリストアからErisPulseをワンクリックでインストールできます。詳しくは[ErisPulse-1Panel](https://github.com/ErisPulse/ErisPulse-1Panel)をご覧ください。

```bash
bash <(curl -sL https://get-1panel.erisdev.com/install.sh)
```

#### 使用 pip 安装

```bash
pip install ErisPulse
```

> 上記のワンクリックインストールスクリプトを使用することもでき、環境を自動検出し、設定のガイドを提供します。

#### 运行效果

##### 仪表盘：

<table>
<tr>
<td width="50%">

<img src=".github/assets/docs/dashboard.png" alt="Dashboard 演示" />

</td>
<td width="50%">

<video src="https://github.com/user-attachments/assets/157191c4-9a84-433c-b311-0c57e3a21151" controls width="100%"></video>

</td>
</tr>
</table>

##### 同一端代码，多个平台响应：

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

#### 初始化项目

```bash
# 対話式初期化
epsdk init

# 簡易初期化（プロジェクト名を指定）
epsdk init -q -n my_bot
```

#### 创建第一个机器人

`main.py`ファイルを作成します：

<table>
<tr>
<td width="50%" valign="top">

**命令处理器**

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command

@command("hello", help="挨拶メッセージを送信")
async def hello_handler(event):
    user_name = event.get_user_nickname() or "友達"
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

**效果说明**

`/hello`を送信

ロボットの返信：`こんにちは、{ユーザー名}！`

---

`/ping`を送信

ロボットの返信：`Pong！ロボットは正常に動作しています。`

---

**运行方式**

```bash
epsdk run main.py
# または開発モード
epsdk run main.py --reload
```

</td>
</tr>
</table>

詳細な説明は以下をご覧ください：
- [快速开始指南](docs/ja/quick-start.md)
- [入门指南](docs/ja/getting-started/)

#### 多轮对话示例

ErisPulseには強力な多段対話エンジンが内蔵されており、誘導操作や情報収集などのインタラクティブなシナリオを簡単に実現できます：

```python
from ErisPulse.Core.Event import command, request

@command("register")
async def register_handler(event):
    conv = event.conversation(timeout=60)
    
    await conv.say("ようこそ登録！")
    
    # 複数ステップでユーザー情報を収集し、自動検証
    data = await conv.collect([
        {"key": "name", "prompt": "名前を入力してください"},
        {"key": "age", "prompt": "年齢を入力してください",
         "validator": lambda e: e.get_text().strip().isdigit(),
         "retry_prompt": "年齢は数字でなければなりません。再度入力してください"},
    ])
    
    if data and await conv.confirm(f"登録を確認しますか？名前: {data['name']}, 年齢: {data['age']}"):
        # SendDSLを使用して通知を送信
        await sdk.adapter.get(event.get_platform()).Send.To(
            "user", event.get_user_id()
        ).Text(f"登録成功しました！{data['name']}さん、ようこそ")
        # または await event.reply("登録成功しました！")

# フレンドリクエストの自動処理
@request.on_friend_request()
async def handle_friend_request(event):
    user_name = event.get_user_nickname() or event.get_user_id()
    
    # リクエストを承認
    result = await event.approve()
    if result.get("status") == "ok":
        await event.reply(f"自動でフレンドリクエストを承認しました。{user_name}さん、ようこそ")
```

<details>
<summary>Conversation APIの詳細（分岐/選択/永続化）</summary>

```python
@command("quiz")
async def quiz_handler(event):
    conv = event.conversation(timeout=30)
    
    # 選択式クイズ
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
        await conv.say("不正解です。正解はGuido van Rossumです")

@command("menu")
async def menu_handler(event):
    conv = event.conversation(timeout=60)
    
    # 分岐処理で複雑なインタラクションフローを構築
    @conv.branch("main")
    async def main_menu():
        await conv.say("=== メインメニュー ===\n1. プロフィール\n2. 設定\n3. 終了")
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

[Conversation 多輪対話](docs/ja/advanced/conversation.md)を参照してください。

</details>

---

### 支持的适配器

アダプタの貢献をお待ちしています！

| アダプタ | 説明 |
|--------|------|
| <img src=".github/assets/adapter_logo/kook.svg" height="20" alt="Kook" /> [Kook](https://github.com/shanfishapp/ErisPulse-KookAdapter) | Kook（開黒啦）即時メッセージングプラットフォーム |
| <img src=".github/assets/adapter_logo/matrix.svg" height="20" alt="Matrix" /> [Matrix](https://github.com/ErisPulse/ErisPulse-MatrixAdapter) | Matrix分散型メッセージングプロトコル |
| <img src=".github/assets/adapter_logo/onebot.png" height="20" alt="OneBot" /> [OneBot11](https://github.com/ErisPulse/ErisPulse-OneBot11Adapter) | OneBot v11汎用ロボットプロトコル |
| <img src=".github/assets/adapter_logo/onebot.png" height="20" alt="OneBot" /> [OneBot12](https://github.com/ErisPulse/ErisPulse-OneBot12Adapter) | OneBot v12標準プロトコル |
| <img src=".github/assets/adapter_logo/qqbot.svg" height="20" alt="QQ" /> [QQ](https://github.com/ErisPulse/ErisPulse-QQBotAdapter) | QQ公式ロボットプラットフォーム |
| <img src=".github/assets/adapter_logo/sandbox.png" height="20" alt="Sandbox" /> [沙箱](https://github.com/ErisPulse/ErisPulse-SandboxAdapter) | ウェブ端でのデバッグ、実際のプラットフォーム接入なし |
| <img src=".github/assets/adapter_logo/telegram.svg" height="20" alt="Telegram" /> [Telegram](https://github.com/ErisPulse/ErisPulse-TelegramAdapter) | グローバルな即時メッセージングプラットフォーム |
| <img src=".github/assets/adapter_logo/email.svg" height="20" alt="Email" /> [邮件](https://github.com/ErisPulse/ErisPulse-EmailAdapter) | メールプロトコル受発信アダプタ |
| <img src=".github/assets/adapter_logo/yunhu.png" height="20" alt="Yunhu" /> [云湖](https://github.com/ErisPulse/ErisPulse-YunhuAdapter) | 企業向け即時メッセージングプラットフォーム（ロボット接入） |
| [云湖用户](https://github.com/wsu2059q/ErisPulse-YunhuUserAdapter) | 雲湖ユーザー協定に基づく接入アダプタ |
| [花枫咖啡馆](https://github.com/ErisPulse/ErisPulse-Ideaura/) | Allons! \(・ω・) / |

アダプタの詳細については、[アダプタ詳細紹介](docs/ja/platform-guide/README.md)をご覧ください。

---

### 应用场景

<div align="center">

| 多平台机器人 | 聊天助手 | 自动化工具 | 消息转发 |
|:---:|:---:|:---:|:---:|
| 複数プラットフォームに同じ機能のロボットを展開 | AIチャットモジュールを接続し、エンターテインメントとインタラクションを実現 | メッセージ通知、タスク管理、データ収集 | 複数プラットフォーム間のメッセージ同期と転送 |

</div>

---

### 贡献指南

ErisPulseプロジェクトの健全性には、皆様のご協力が必要です！あらゆる形態の貢献を歓迎します：

1. **問題報告** — [GitHub Issues](https://github.com/ErisPulse/ErisPulse/issues)にバグ報告を投稿
2. **機能リクエスト** — [コミュニティ議論](https://github.com/ErisPulse/ErisPulse/discussions)で新アイデアを提案
3. **コード貢献** — PRを提出する前に[コードスタイル](docs/ja/styleguide/)および[貢献ガイド](CONTRIBUTING.md)を確認してください
4. **ドキュメント改善** — ドキュメントやサンプルコードの改善を手伝ってください

[コミュニティ議論に参加](https://github.com/ErisPulse/ErisPulse/discussions)

---

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=ErisPulse/ErisPulse&type=Date)](https://star-history.com/#ErisPulse/ErisPulse&Date)

---

<div align="center">

### 致谢

<img src=".github/assets/thanks.png" width="200" alt="感谢" />

本プロジェクトの一部のコードは [sdkFrame](https://github.com/runoneall/sdkFrame) に基づいています。コアアダプタの標準化層は [OneBot12規格](https://12.onebot.dev/) に基づいています。オープンソースコミュニティに貢献してくださったすべての開発者と著作者に感謝します。

</div>