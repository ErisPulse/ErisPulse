# ErisPulse-QvQChat 通用インテリジェントエージェント

> [!TIP]
> **このドキュメントを読む必要があるのは**、ロボットに AI インテリジェントエージェントの機能（ツールループ、ストリーミング対話、MCP、長期記憶）を追加したい場合、または独自のモジュールサービスをインテリジェントエージェントから呼び出せるようにしたい場合です。必要ない場合はこのドキュメントは飛ばしてください。

[ErisPulse-QvQChat](https://pypi.org/project/ErisPulse-QvQChat/) は、**汎用的なインテリジェントエージェントモジュール**です。ツールループを基盤として、メッセージの送受信、エコシステムモジュールサービスの呼び出し、コードの作成と実行、コンピュータの操作、画像や音声の生成、スケジュールタスクと長期記憶の管理など、すべてを同一のツールプロトコルで行います。

> [!IMPORTANT]
> QvQChat は個別にインストールする必要があります：
>
> ```bash
> epsdk install ErisPulse-QvQChat
> ```
>
> また、「モデルプール」に少なくとも1つの OpenAI 互換モデル（Base URL、API Key、モデル名）を追加する必要があります。

## 核心能力

| 能力 | 说明 |
|---|---|
| 工具循環 | モデルが出力したツール呼び出し → 並列実行 → 結果の埋め込み → 最終回答が出るまで推論を継続 |
| ストリーミング対話 | SSE による逐字出力、ツールのステップがリアルタイムで表示される；リフレッシュや切り替え後に戻っても、進行状況は失われない |
| コンテキスト圧縮 | token の閾値を超えると、古い対話を要約して圧縮（デフォルトは 128000 估算、カスタマイズ可能） |
| エコシステムサービス橋 | モジュールで宣言されたサービスを自動的にツールとして変換、モジュールの追加・削除で機能を増減可能 |
| MCP クライアント | stdio と Streamable HTTP、MCP ツールを同じツールセットに統合 |
| 子インテリジェントエージェント | `spawn_agent` で独立したセッションの子インテリジェントエージェントを起動し、タスクを探索、結果のみを報告 |
| プロセス内実行 | `run_python_sdk` でメインプロセス内で Python を実行し、実行時のオブジェクトに直接アクセス可能 |
| コンピュータ操作 | 3段階のセキュリティサンドボックス（strict / standard / permissive）、危険な操作は確認が必要、全プロセスを監査 |
| 視覚理解 | 画像を自動的にモデルに注入（画像をサポートしない場合、自動的に削除して再試行） |
| 附件 | ハッシュ値に基づいて任意のファイルを重複除去し、AI にパスを渡して処理させる；Ctrl+V でスクリーンショットを貼り付け可能 |
| 会話共有 | 一時的な読み取り専用リンク（有効期間とトークン予算付き）、Markdown でエクスポート可能 |
| 定時タスク | cron / 一回限り / 間隔、永続化、権限は作成者に付与 |
| 会話の引き継ぎ | 管理者はインテリジェントエージェントが特定の会話を独占できるようにできる |
| パーソナリティシステム | システムプロンプト + 初回対話 + ツールホワイトリスト、会話にバインド可能 |
| 長期記憶 | 各会話ごとのメモリ項目、類似度に基づいて検索して注入 |
| AI による自動命名 | 会話の最初の返信後に、簡潔なタイトルを自動生成 |

## モジュール拡張

ErisPulse モジュールが `services` を宣言すると、専用のインターフェースを必要とせず、QvQChat のツールとして自動的に機能します。

```python
from ErisPulse.Core.Bases import BaseModule, ModuleMeta

class Main(BaseModule):
    @staticmethod
    def get_meta() -> ModuleMeta:
        return ModuleMeta(name="Draw", services=[
            {"name": "draw", "description": "説明に基づいて画像を生成し、画像の URL を返す"},
        ])

    async def draw(self, prompt: str, size: str = "1024x1024"):
        return {"image_url": "https://..."}
```

サービスのメソッドシグネチャは自動的にツールの JSON Schema パラメータ定義にマッピングされ、ドキュメント文字列の最初の行はパラメータの説明として使用されます。

### 深度統合（オプション）

モジュールは以下の任意のサービスを追加で実装できます。各サービスは**個別に選択可能**です。つまり、人格拡張のみを行うモジュールもあれば、プロンプトの注入のみを行うモジュールもあります。

#### `qvq_prompts()` → システムプロンプトの注入

`list[str]` または `list[{"text": str, "priority": int}]` を返します。`priority` が昇順に並べ替えられ、連結されます。

```python
async def qvq_prompts(self):
    return [
        {"text": "画像を描画した後、send_message を使って画像をユーザーに送信する。", "priority": 10},
        {"text": "対応するスタイル：アニメ、写実、水彩、ピクセル。", "priority": 20},
    ]
```

#### `qvq_personas()` → 人格プリセットの登録

人格のリストを返します。`id` には自動的に `ext.<モジュール名>.` というプレフィックスが追加され、モジュールのアンロード時に自動的にクリーンアップされます。これは、感情的なサポート、翻訳担当者、コードレビュー担当者など、人格拡張専用のモジュールに適しています。

```python
async def qvq_personas(self):
    return [
        {"id": "companion", "name": "暖男", "system": "あなたは温かく思いやりのあるチャットパートナーです..."},
        {"id": "coder", "name": "コード指導者", "system": "...", "tools": ["read_file", "run_python"]},
    ]
```

`tools` は、その人格が使用できるツールのサブセットを限定することもできます。

#### `qvq_schemas()` → 明示的なパラメータ schema

`dict[サービス名, JSON Schema]` を返し、メソッドシグネチャの推論を上書きします。パラメータが複雑または厳密な検証が必要な場合に使用します。

```python
async def qvq_schemas(self):
    return {
        "draw": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "画面の説明"},
                "size": {"type": "string", "enum": ["512x512", "1024x1024"]},
            },
            "required": ["prompt"],
        },
    }
```

### リフレッシュタイミング

深度統合サービスのリフレッシュタイミングは、起動時、モジュールのロード/アンロード時、およびダッシュボードの「ツール」ページでの手動リフレッシュ時です。

## イベントのサブスクライブ

QvQChat は 2 つのライフサイクルイベントをブロードキャストします：

| イベント | 時機 | ペイロード |
|---|---|---|
| `qvq.message` | ユーザーメッセージ受信時 | `chat_key` `platform` `sender_id` `sender_name` `text` `is_group` |
| `qvq.replied` | レプリが送信された後 | `chat_key` `reply` `tools` |

```python
async def setup(self):
    sdk.lifecycle.on("qvq.message", self.on_message)
```

## サービスとして呼び出される

| サービス | シグネチャ | 説明 |
|---|---|---|
| `chat` | `(session_id, prompt, persona="")` | スマートエージェントと対話し、テキストを返す |
| `run_prompt` | `(chat_key, prompt, ...)` | プロンプトを実行し、結果をターゲットセッションに送信できる |
| `get_status` | `()` | 実行状態の概要 |

## インターフェース

`/QvQChat/view` に独立してアクセスするか、ダッシュボードのサイドバーに埋め込むことができます。

![概要](https://raw.githubusercontent.com/wsu2059q/ErisPulse-QvQChat/main/.github/assets/overview.png)

![会話](https://raw.githubusercontent.com/wsu2059q/ErisPulse-QvQChat/main/.github/assets/chat.png)

---

## 次に進む

- **自分のモジュールをエージェントツールにする**：`get_meta()` で `services` を宣言するだけで可能。フィールドの意味は [コアモジュール API - サービス契約](../api-reference/core-modules.md) を参照してください。
- **エージェントメッセージのサブスクライブで連携させる**：[ライフサイクルイベント](../advanced/lifecycle.md) を使って `qvq.message` / `qvq.replied` を監視します。
- **エージェントを使わず、ただの複数回対話フォームが欲しい場合**：内蔵の [Conversation 複数回対話](../advanced/conversation.md) がより軽量な選択です。
- **ウェブ管理**：[ErisPulse-Dashboard](dashboard.md) のサイドバーと併用してください。