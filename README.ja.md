<table>
<tr>
<td width="35%" valign="middle" align="center">

<img src=".github/assets/mascot-hero.png" width="320" alt="ErisPulse" />

</td>
<td valign="middle">

[English](README.en.md) | [简体中文](README.md) | [繁體中文](README.zh-TW.md) | **日本語** | [Русский](README.ru.md)

# ErisPulse

**イベント駆動型マルチプラットフォームボット開発フレームワーク**

OneBot12 標準インターフェースに基づき、一度記述すれば複数のプラットフォームにデプロイできます。柔軟なプラグインシステム、ホットリロードサポート、完全な開発者ツールチェーンを提供します。

> Vibe Coding ワークフローをサポート — AI が直接使用可能なモジュールを生成 — [詳細](docs/ja/ai-support/README.md)

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

### コア機能

</div>

<table>
<tr>
<td width="50%" align="center" valign="top">
<br/>

### ⚡ イベント駆動アーキテクチャ

OneBot12 標準に基づく明確なイベントモデルにより、メッセージ処理ロジックをより直感的かつ効率的にします。

</td>
<td width="50%" align="center" valign="top">
<br/>

### 🌐 クロスプラットフォーム対応

プラグインモジュールは1度記述すればすべてのプラットフォームで使用可能です。異なるプラットフォームごとの再開発は不要です。

</td>
</tr>
<tr>
<td width="50%" align="center" valign="top">
<br/>

### 🧩 モジュラー設計

柔軟なプラグインシステムで、拡張と統合が容易。ホットプラグ可能なモジュール管理をサポートします。

</td>
<td width="50%" align="center" valign="top">
<br/>

### 🔄 ホットリロード対応

開発時にコードを再読み込みするために再起動する必要がなく、開発の反復効率を大幅に向上させます。

</td>
</tr>
</table>

---

### クイックスタート

#### インストールスクリプト（推奨）

インストールスクリプトは環境（Docker、Python、uv）を自動的に検出し、最適なインストール方法をガイドし、多言語（中国語/English/日本語/Русский/繁體中文）をサポートします。

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

**Docker インストールのデモ**

<video src="https://github.com/user-attachments/assets/a367a466-4678-46a9-b101-073a86388ede" controls width="100%"></video>

</td>
<td align="center" width="50%">

**pip インストールのデモ**

<video src="https://github.com/user-attachments/assets/a2df4009-dba6-411e-b79d-4454a168d063" controls width="100%"></video>

</td>
</tr>
</table>

#### Docker の使用（推奨）

```bash
docker pull erispulse/erispulse:latest
```

<details>
<summary>Docker Hub にアクセスできない場合？</summary>

Docker Hub にアクセスできない場合、GitHub Container Registry を使用できます：

```bash
docker pull ghcr.io/erispulse/erispulse:latest
```

ghcr.io イメージを使用する場合、`docker-compose.yml` の image を以下のように変更する必要があります：
```yaml
image: ghcr.io/erispulse/erispulse:latest
```

</details>

<details>
<summary>クイックスタート</summary>

```bash
# docker-compose.yml をダウンロード
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# Dashboard ログイントークンを設定して起動
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

> 鏡像には ErisPulse フレームワークと Dashboard 管理パネルが内蔵されており、`linux/amd64` および `linux/arm64` アーキテクチャをサポートしています。

起動後、`http://<host>:<port>/Dashboard` にアクセスし、設定したトークンをパスワードとして使用して Dashboard 管理パネルにログインします。

</details>

<details>
<summary>プレリリース版（Dev）の使用</summary>

`ERISPULSE_CHANNEL=dev` を設定することでプレリリース版を使用できます：

```bash
# 方法1：環境変数を使用する（推奨）
ERISPULSE_CHANNEL=dev ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d

# 方法2：dev イメージをビルド
ERISPULSE_BUILD_TARGET=dev docker compose up -d --build
```

起動時に最新バージョン（stable または dev のどちらでも）に自動的に更新する場合は、`ERISPULSE_UPDATE_ON_START=true` を明示的に設定します：

```bash
ERISPULSE_CHANNEL=dev ERISPULSE_UPDATE_ON_START=true docker compose up -d
```

プレビルドされた dev イメージをプルすることもできます：

```bash
docker pull erispulse/erispulse:dev
```

</details>

<details>
<summary>Docker 環境変数</summary>

| 変数 | デフォルト値 | 説明 |
|------|--------|------|
| `ERISPULSE_CHANNEL` | `stable` | バージョンチャネル：`stable`（安定版）または `dev`（プレリリース版） |
| `ERISPULSE_UPDATE_ON_START` | `false` | コンテナ起動時に最新バージョンに自動的に更新するかどうか（明示的に有効にする必要があります） |
| `ERISPULSE_DASHBOARD_TOKEN` | 空 | Dashboard ログイントークン |
| `ERISPULSE_PORT` | `8000` | Dashboard ポートマッピング |
| `TZ` | `Asia/Shanghai` | コンテナのタイムゾーン |

> `ERISPULSE_UPDATE_ON_START=true` を有効にすると、ミラーが古い場合でも、コンテナは起動時に最新バージョンを自動的に取得できるようになります。

</details>

#### 1Panel アプリストア

[1Panel](https://1panel.cn) アプリストア経由で ErisPulse を1クリックでインストールします。詳細は [ErisPulse-1Panel](https://github.com/ErisPulse/ErisPulse-1Panel) を参照してください。

```bash
bash <(curl -sL https://get-1panel.erisdev.com/install.sh)
```

#### pip の使用

```bash
pip install ErisPulse
```

> 上記のインストールスクリプトを使用して、環境を自動的に検出し、設定をガイドすることもできます。

#### 実行結果


##### ダッシュボード：

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


##### 1つのコードで複数のプラットフォームに対応：

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

#### プロジェクトの初期化

```bash
# インタラクティブ初期化
epsdk init

# クイック初期化（プロジェクト名を指定）
epsdk init -q -n my_bot
```

#### 最初のボットの作成

`main.py` ファイルを作成します：

<table>
<tr>
<td width="50%" valign="top">

**コマンドハンドラー**

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command

@command("hello", help="送信ハローメッセージ")
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

**動作の説明**

`/hello` を送信

ボットの応答：`こんにちは、{ユーザー名}！`

---

`/ping` を送信

ボットの応答：`Pong！ボットは正常に動作しています。`

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

詳細な説明については、以下を参照してください：
- [クイックスタートガイド](docs/ja/quick-start.md)
- [入門ガイド](docs/ja/getting-started/)

#### マルチラウンド会話の例

ErisPulse は強力なマルチラウンド会話エンジンを内蔵しており、誘導型操作、情報収集などのインタラクションシナリオを簡単に実現できます：

```python
from ErisPulse.Core.Event import command, request

@command("register")
async def register_handler(event):
    conv = event.conversation(timeout=60)
    
    await conv.say("登録へようこそ！")
    
    # 複数ステップでユーザー情報を収集し、自動的に検証
    data = await conv.collect([
        {"key": "name", "prompt": "名前を入力してください"},
        {"key": "age", "prompt": "年齢を入力してください",
         "validator": lambda e: e.get_text().strip().isdigit(),
         "retry_prompt": "年齢は数字である必要があります。もう一度入力してください"},
    ])
    
    if data and await conv.confirm(f"登録しますか？ 名前: {data['name']}, 年齢: {data['age']}"):
        # SendDSL を使用して主にプッシュ通知を送信
        await sdk.adapter.get(event.get_platform()).Send.To(
            "user", event.get_user_id()
        ).Text(f"登録成功！ {data['name']}さん、ようこそ")
        # または await event.reply("登録成功！")

# フレンドリクエストを自動的に処理
@request.on_friend_request()
async def handle_friend_request(event):
    user_name = event.get_user_nickname() or event.get_user_id()
    
    # リクエストを承認
    result = await event.approve()
    if result.get("status") == "ok":
        await event.reply(f"{user_name}さんへのフレンドリクエストを自動的に承認しました。ようこそ")
```

<details>
<summary>Conversation API の詳細を見る（分岐ジャンプ / 選択 / 永続化）</summary>

```python
@command("quiz")
async def quiz_handler(event):
    conv = event.conversation(timeout=30)
    
    # 選択式のクイズ
    answer = await conv.choose("Python