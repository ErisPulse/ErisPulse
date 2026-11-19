# ErisPulse 送信メソッド規格

> [!TIP]
> **このドキュメントを読むべきタイミング**：アダプターで Send クラスを実装する際、メソッド命名、メディアパラメータ（URL/パス/bytes）のサポート形態、`Raw_ob12` の逆変換、転送メッセージのマージ機能を本文と照らし合わせてください。不要であれば飛ばしてください。

本文は、ErisPulse アダプターにおける Send クラスの送信メソッドの命名規則、パラメータ規則、逆変換要件を定義します。

## 0. キーワードの約束

本文の **必須（MUST）**、**推奨（SHOULD）**、**任意（MAY）** は、RFC 2119 に従い以下の意味で解釈されます：

| キーワード | 意味 | 違反時の影響 |
|--------|------|---------|
| **必須** | 強制要件。フレームワークの動作やクロスプラットフォームの一貫性に依存 | アダプターは規格に準拠していないと見なし、モジュールコードが動作しない可能性がある |
| **推奨** | 強く推奨。十分な理由がない限り、遵守すべき | 違背する場合は、アダプターのドキュメントに理由と代替動作を明記する |
| **任意** | オプション。プラットフォームの能力に応じて決定 | 無 |

## 1. 標準メソッド命名

すべての送信メソッドは **大文字キャメルケース（PascalCase）** を使用し、先頭文字は大文字です。

### 1.1 標準送信メソッド

| メソッド名 | 説明 | パラメータ型 | 実装要件 |
|-------|------|---------|---------|
| `Text` | テキストメッセージを送信 | `str` | 必須 |
| `Image` | 画像を送信 | `str` \| `bytes` | 必須（基底クラスに既に実装済み、§6.4参照） |
| `Voice` | 音声を送信 | `str` \| `bytes` | 必須（基底クラスに既に実装済み；プラットフォームが音声をサポートしない場合は§2.1.5に従い降格） |
| `Video` | 動画を送信 | `str` \| `bytes` | 必須（基底クラスに既に実装済み；プラットフォームが動画をサポートしない場合は§2.1.5に従い降格） |
| `File` | ファイルを送信 | `str` \| `bytes`、`filename: str \| None = None` | 必須（基底クラスに既に実装済み） |
| `Location` | 位置情報を送信 | `float` (latitude/longitude)、`title: str = ""`、`content: str = ""` | 必須（基底クラスに既に実装済み） |
| `At` | ユーザー/グループを@する | `str` (user_id) | 修飾メソッド、必要に応じて |
| `Face` | 表情を送信 | `str` (emoji) | 任意 |
| `Reply` | メッセージに返信する | `str` (message_id) | 修飾メソッド、必要に応じて |
| `Forward` | メッセージを転送する | `str` (message_id) | 任意 |
| `Markdown` | Markdownメッセージを送信 | `str` | 任意 |
| `HTML` | HTMLメッセージを送信 | `str` | 任意 |
| `Card` | カードメッセージを送信 | `dict` | 任意 |

> 標準メソッド（`Text`/`Image`/`Voice`/`Video`/`File`/`Location`）は、基底クラス `SendDSL` に内蔵されており、デフォルトで `Raw_ob12` に委譲されるため、アダプターはこれらのメソッドを再実装しなくても型シグネチャを獲得できる。プラットフォームに特別なロジックが必要な場合にのみ、個々のメソッドをオーバーライドする（§6.4参照）。

### 1.2 チェーン修飾メソッド

| メソッド名 | 説明 | パラメータ型 |
|-------|------|---------|
| `At` | ユーザーを@する（複数回呼び出し可） | `str` (user_id) |
| `AtAll` | 全員を@する | 無 |
| `Reply` | メッセージに返信する | `str` (message_id) |

### 1.3 プロトコルメソッド

| メソッド名 | 説明 | 必須か |
|-------|------|---------|
| `Raw_ob12` | OneBot12形式のメッセージセグメントを送信 | 必須 |

**`Raw_ob12` は必須実装のメソッド**です。これはアダプターの主要な責任の一つであり、OneBot12標準メッセージセグメントを受け取り、それをプラットフォームのネイティブAPI呼び出しに変換する必要があります。`Raw_ob12` はOneBot12 → プラットフォームの逆変換（统一入口）であり、モジュールがプラットフォーム固有のメソッドに依存せず、標準メッセージセグメントを使って直接メッセージを送信できるようにします。

**`Raw_ob12` をオーバーライドしない場合の動作**：基底クラスのデフォルト実装は **errorレベル**のログを記録し、標準エラー応答形式（`status: "failed"`, `retcode: 10002`）を返し、アダプター開発者がこのメソッドを実装する必要があることを示します。

### 1.4 推奨の拡張命名規約

アダプターがOneBot12形式以外の生データ（プラットフォーム固有のJSON、XMLなど）を送信する必要がある場合、以下の命名規約を推奨します：

| 推奨メソッド名 | 説明 |
|-----------|------|
| `Raw_json` | 任意のJSONデータを送信 |
| `Raw_xml` | 任意のXMLデータを送信 |

**注意**：これらのメソッドは**基底クラスに提供されたデフォルトメソッドではなく、強制実装も要求されていない**。これらは命名規約としてのみ提供され、アダプターは必要に応じて独自に定義する。これらの形式をサポートしない場合は定義する必要がない。

**メッセージビルダー（MessageBuilder）**：ErisPulseは`MessageBuilder`というツールクラスを提供し、OneBot12メッセージセグメントリストを簡単に構築できるようにし、`Raw_ob12`と併用できる。詳しくは[MessageBuilder 詳解](../advanced/message-builder.md)を参照してください。

## 2. パラメータ規格詳細

### 2.1 メディア送信プロトコル（`Image` / `Voice` / `Video` / `File`）

本節はメディア送信の**統一プロトコル標準**です：モジュールは同一のコードで4つのメディアメソッドを呼び出し、アダプターは`file`パラメータの各種形態をプラットフォームのネイティブアップロード/送信動作に変換する必要があります。

#### 2.1.1 `file` パラメータの合法な形態

| 形態 | 例 | アダプターの要件 |
|------|------|-----------|
| HTTP(S) URL | `https://example.com/image.jpg` | **必須**で受け入れる |
| 本地ファイルパス | `/path/to/file.jpg`、`C:\path\to\file.jpg` | **必須**で受け入れる |
| 二進データ | `b"\x89PNG..."` | **必須**で受け入れる |
| `file://` URI | `file:///path/to/file.jpg` | **推奨**で受け入れる（ローカルパスに転送して処理） |
| Base64文字列 / Data URI | `iVBORw0KGgo=...`、`data:image/png;base64,...` | **推奨**で受け入れる（OneBot12エコシステムの慣例に準拠） |

> アダプターは**3つの必須形態**で一貫した動作をしなければならない—モジュールがURL、パス、またはbytesを渡しても、受け取るメッセージは同一である。プラットフォームが外部URLを直接使用できない場合（プラットフォームのAPIが外部URLをサポートしない）、アダプターがダウンロード/読み取り後にアップロードする。**モジュールに再試行の形態変更を要求してはならない**。

#### 2.1.2 形態判定順序

アダプターがメディアパラメータの処理を実装する際、**推奨される判定順序**は以下の通りです：

1. `bytes`型 → 直接アップロード
2. 文字列が `http://` / `https://` で始まる → URLとして処理（直接参照またはダウンロード後にアップロード、プラットフォームの能力に応じて）
3. 文字列が `file://` で始まる → プレフィックスを剥がしてローカルパスとして処理
4. その他の文字列 → ローカルパスとして処理（存在すれば読み取りアップロード；存在しない場合は標準エラー応答を返す）

```python
def _resolve_media(self, file: "str | bytes") -> bytes:
    """形態判定と正規化（例）"""
    if isinstance(file, (bytes, bytearray)):
        return bytes(file)
    if file.startswith(("http://", "https://")):
        return self._download(file)          # プラットフォームがURLを参照できない場合にダウンロード
    if file.startswith("file://"):
        file = file[len("file://"):]
    with open(file, "rb") as f:              # 本地パス
        return f.read()
```

#### 2.1.3 `File`のファイル名の意味

`File`メソッドのシグネチャ：`File(file, filename=None)`（`filename`はオプションパラメータ、基底クラスに既に実装済み）。

ファイル名の**推定順序**（アダプターが明示的な`filename`を提供しない場合にこの順序で生成）：

1. 明示的な`filename`パラメータ（最高優先）
2. URLのbasename（例：`https://host/a/b/report.pdf` → `report.pdf`、クエリ文字列を剥がす）
3. 本地パスのbasename（例：`/tmp/data/backup.zip` → `backup.zip`）
4. プラットフォームがデフォルトで生成（例：`file_{timestamp}`；**推奨**は実際の拡張子を保持する—拡張子はプラットフォーム側のタイプ識別とプレビュー動作に影響する）

> `Image` / `Voice` / `Video`も**`filename`を受け入れる**（メッセージセグメント`data.filename`を通じて渡される）が、`File`のファイル名だけがクロスプラットフォームの意味保証がある。

#### 2.1.4 プラットフォーム制限の声明義務

各プラットフォームは、メディアのサイズ上限、形式（MIME）、時長（音声/動画）などの制約が異なる。アダプターは**推奨**：

- アダプターのドキュメントにサポートするメディア形式と制限範囲を声明する
- 超限または非サポートの入力を標準エラー応答（`status: "failed"`；`retcode`は`10002`またはプラットフォーム固有のエラーコード、`message`で原因を説明）を返す。**例外をスローしてモジュールのロジックを中断してはならない**

#### 2.1.5 機能降格の段階

プラットフォームがメディア**形式**をサポートしない場合、以下の段階で降格する（総則「機能降格はエラーを出さない」に従う）：

| 情報 | 降格動作 |
|------|---------|
| `Voice`が音声メッセージをサポートしない | **推奨**は`File`（またはプラットフォームに近縁な形態）で送信；表現できない場合は`retcode=10002`を返す |
| `Video`が動画メッセージをサポートしない | 同上 |
| メディア形式が完全にサポートされていない（ファイル機能がない） | `retcode=10002`を返し、`message`に非サポートのデータ形式を明記する |
| 形態がサポートされていない（例：base64を処理できない） | `retcode=10002`を返し、`message`にモジュールにURL/bytesを使用するよう提示する可能性がある |

**禁止される動作**：静かに破棄（返却なし）、例外をスロー、モジュールにプラットフォーム分岐処理を書かせる。

### 2.2 @ユーザーのパラメータ規格

**メソッド：** `At`（修飾メソッド）

**パラメータ：** `user_id` (`str`)

**要件：**
- `user_id` は文字列型のユーザー識別子であるべき
- 各プラットフォームの `user_id` 形式は異なる可能性がある（数字、UUID、文字列など）
- アダプターは `user_id` をプラットフォーム固有の形式に変換する責任がある
- 実際の送信メソッドの呼び出しは最後の位置に置くこと

**例：**
```python
# 単一の@ユーザー
Send.To("group", "g123").At("123456").Text("你好")

# 複数の@ユーザー（チェーン呼び出し）
send.To("group", "g123").At("123456").At("789012").Text("大家好")
```

### 2.3 返信メッセージのパラメータ規格

**メソッド：** `Reply`（修飾メソッド）

**パラメータ：** `message_id` (`str`)

**要件：**
- `message_id` は文字列型のメッセージ識別子であるべき
- 以前に受信したメッセージのIDであるべき
- 一部のプラットフォームは返信機能をサポートしない可能性があるため、適切に降格する

**例：**
```python
send.To("group", "g123").Reply("msg_123456").Text("收到")
```

### 2.4 合併転送機能（`MergeForward`、オプション）

`MergeForward(nodes)` は**オプションの機能メソッド**です：複数の内容を「合併転送 / フルテキスト折りたたみ」形式で送信し、アダプターはプラットフォームの能力に応じて最適な表示方法を決定します。§1.1の`Forward(from_chat_id, message_id)`（既存メッセージの転送）とは意味が異なり、両者は併存します。

> **標準の背景**：OneBot12のコア標準にはnodeメッセージセグメントも、合併転送APIもありません。"メッセージノード"はOneBot v11エコシステム（go-cqhttp拡張）の実装層の概念であり、v12ではこの種のプラットフォーム固有能力を拡張メカニズムに委ねました。ErisPulseの実装方法は拡張メカニズムの同等物です：**標準メッセージセグメントを追加せず、オプション機能メソッド + `list_sends`ランタイム検出**—`MergeForward`を実装したアダプターは自動的に機能を獲得し、実装していない場合は呼び出し元が普通のテキストに自動的に降格し、モジュールは変更なしです。

**メソッドのシグネチャ：**

```python
def MergeForward(self, nodes: List[Dict]) -> asyncio.Task:
    """
    合併転送 / フルテキスト折りたたみメッセージを送信する

    :param nodes: 合併転送ノードの配列（go-cqhttp拡張のOneBot v11ノード形式）：
        [
            {
                "type": "node",
                "data": {
                    "user_id": "10000",     # 表示用の送信者ID
                    "nickname": "MyBot",     # 表示用の送信者ニックネーム
                    "content": [            # メッセージセグメントの配列、現在はtextセグメント
                        {"type": "text", "data": {"text": "【1/3】タイトル\n本文…"}}
                    ],
                },
            },
        ]
    :return: asyncio.Task、await後に標準応答形式を返す
    """
```

**実装要件：**

1. **プラットフォームに原生の合併転送がある**（OneBot11系）：**必須**でプロトコル専用エンドポイント（`send_group_forward_msg` / `send_private_forward_msg`）を呼び出す—NapCatなどの実装は`send_msg`に含まれるnodeセグメントを拒否する（retcode 1400）；専用エンドポイントが失敗した場合は**`send_msg`にnodeセグメントを直接転送して回復する**。
2. **プラットフォームに原生の転送機能はないが、富文本がある**（云湖 / Telegram / Kook / Discord / Matrixなど）：**推奨**でノードをプラットフォームの富文本折りたたみ形態（HTML折りたたみカード / Card / Embed / blockquoteリスト）にレンダリングする。スタイルの参考と各アダプターのタスクリストは`SDK/Adapter/ADAPTER_FORWARD_GUIDE.md`を参照。
3. **両方ない**：**実装しない**（node辞書を純粋なテキストとして発信してはならない）—実装していない場合は`list_sends`に`MergeForward`が含まれず、呼び出し元は自動的に普通のテキストに降格する。
4. **失敗の意味**：標準エラー応答（`status: "failed"`）を返すか、例外をスローしても構わない。呼び出し元は普通のテキスト送信に回復し、内容は失われない。
5. **`MergeForward`内で`Raw_ob12`を再び呼び出して同じnodesを送信してはならない**（OneBot11の`Raw_ob12`はnodeセグメントの自動ルーティングを内蔵しており、循環する）。
6. **出力nodeセグメントの解析**（全アダプターの約束）：各アダプターの`Raw_ob12`のセグメント配分は`node`セグメントを登録するべき—純粋なnodeリストは自動的に本アダプターの合併転送表示にルーティングされる（`MergeForward`があるプラットフォームでは直接呼び出すのと同等；`MergeForward`がないプラットフォームでは各ノードのテキストを「ニックネーム: 本文」として1行ずつ**原文出力**）。混合リスト中のnodeセグメントのテキストは本文に統合される。どのアダプターもnodeセグメントを静かに破棄してはならない。

**プラットフォーム実装形態**（`SDK/Adapter/ADAPTER_FORWARD_GUIDE.md`を参照）：

- 原生エンドポイント：OneBot11、SnowLuma（3段階の降格：`send_group/private_forward_msg`専用エンドポイント → `upload_forward_msg`からresidを取得してforwardセグメントを送信 → nodeセグメントを直接送信；SnowLuma APIはNapCatと完全に互換性があり、アダプターはNapCatバックエンドに直接接続できる）
- 折りたたみHTML `<details>` カード：云湖（bot/ユーザー協定）、Email、Sandbox、Allons(Ideaura)
- ホワイトリストHTML / 引用ブロック：Telegram（`<b>`+`<blockquote>`）、Matrix（blockquoteバリエーション、whitelistでdetails/インラインスタイルを除去）
- プラットフォームカード：Kook（Card header+section）、Discord（Embed fields）
- 公式Markdown引用リスト：QQBot（公式mdに折りたたみ構文がないため、サーバ側で無効なタグを拒否する40034011）
- 実装しない（nodeセグメントを原文出力して降格）：OneBot12（標準にnodeセグメントがない）、WeCom、Terminal、Webhook、WechatMp

**呼び出し元の検出例：**

```python
sends = adapter.list_sends(platform)
if "MergeForward" in sends:
    await adapter.Send.To("group", "123").MergeForward(nodes)
else:
    await adapter.Send.To("group", "123").Text(plain_text)
```

> 参考実装：`ErisPulse-OneBot11Adapter`（専用エンドポイント → `send_msg`の降格）；レンダリングテンプレートと各アダプターのタスクリストは`SDK/Adapter/ADAPTER_FORWARD_GUIDE.md`を参照。

## 3. プラットフォーム固有メソッド命名

Sendクラスに直接プラットフォームプレフィックスメソッドを追加することは**推奨されない**。一般的なメソッド名または`Raw_{プロトコル}`メソッドを使用することを推奨。

**推奨されない：**
```python
def YunhuForm(self, form_id: str):  # ❌ 推奨されない
    pass

def TelegramSticker(self, sticker_id: str):  # ❌ 推奨されない
    pass
```

**推奨：**
```python
def Form(self, form_id: str):  # ✅ 一般的なメソッド名
    pass

def Sticker(self, sticker_id: str):  # ✅ 一般的なメソッド名
    pass

def Raw_ob12(self, message):  # ✅ OneBot12形式を送信
    pass
```

**拡張メソッド要件**：
- メソッド名はPascalCaseを使用し、プラットフォームプレフィックスを付けない
- 必須で`asyncio.Task`オブジェクトを返す
- 完全な型注釈とドキュメント文字列を提供する
- パラメータ設計は標準メソッドのスタイルとできるだけ一致させる

## 4. パラメータ命名規格

| パラメータ名 | 説明 | 型 |
|-------|------|------|
| `text` | テキスト内容 | `str` |
| `file` | メディア内容（URL / パス / 二進、§2.1.1参照） | `str` / `bytes` |
| `filename` | ファイル名（`File`はオプション、§2.1.3参照） | `str` / `None` |
| `user_id` | ユーザーID | `str` / `int` |
| `group_id` | グループID | `str` / `int` |
| `message_id` | メッセージID | `str` |
| `data` | データオブジェクト（例：カードデータ） | `dict` |

## 5. 戻り値規格

- **送信メソッド**（例：`Text`, `Image`）：**必須**で`asyncio.Task`オブジェクトを返す
- **修飾メソッド**（例：`At`, `Reply`, `AtAll`）：**必須**で`self`を返してチェーン呼び出しを可能にする

---

## 6. 逆変換規格（OneBot12 → プラットフォーム）

アダプターは、プラットフォームのネイティブイベントをOneBot12形式に変換する（正変換）だけでなく、**OneBot12メッセージセグメントをプラットフォームのネイティブAPI呼び出しに変換する**（逆変換）能力も**必須**です。逆変換の統一入口は`Raw_ob12`メソッドです。

### 6.1 変換モデル

```
正変換（受信方向）                逆変換（送信方向）
─────────────────                ─────────────────
プラットフォームネイティブイベント                       OneBot12メッセージセグメントリスト
    │                                  │
    ▼                                  ▼
Converter.convert()               Send.Raw_ob12()
    │                                  │
    ▼                                  ▼
OneBot12標準イベント（含{platform}_raw）             プラットフォームネイティブAPI呼び出し
（返却は標準応答形式）
```

**コアの対称性**：正変換は原始データを`{platform}_raw`に保持し、逆変換はOneBot12標準形式を受け取り、プラットフォーム呼び出しに還元する。

### 6.2 `Raw_ob12`実装規格

`Raw_ob12`はOneBot12標準メッセージセグメントリストを受け取り、それをプラットフォームのネイティブAPI呼び出しに変換しなければならない。

**メソッドのシグネチャ：**

```python
def Raw_ob12(self, message_segments: List[Dict]) -> asyncio.Task:
    """
    OneBot12標準メッセージセグメントを送信する

    :param message_segments: OneBot12メッセージセグメントリスト
        [
            {"type": "text", "data": {"text": "Hello"}},
            {"type": "image", "data": {"file": "https://..."}},
            {"type": "mention", "data": {"user_id": "123"}},
        ]
    :return: asyncio.Task、await後に標準応答形式を返す
    """
```

**実装要件：**

1. **すべての標準メッセージセグメントタイプを処理しなければならない**：少なくとも`text`、`image`、`audio`、`video`、`file`、`mention`、`reply`をサポートする
2. **プラットフォーム拡張メッセージセグメントを処理しなければならない**：`{platform}_xxx`形式のメッセージセグメントは、プラットフォームに対応するネイティブ呼び出しに変換する
3. **標準応答形式を返さなければならない**：[API応答標準](api-response.md)に従う
4. **サポートしないメッセージセグメントは警告を記録してスキップし、例外をスローしてメッセージ全体の送信失敗を起こしてはならない**

### 6.3 メッセージセグメント変換ルール

#### 6.3.1 標準メッセージセグメント変換

アダプターは以下の標準メッセージセグメントの変換を実装しなければならない：

| OneBot12メッセージセグメント | 変換要件 |
|----------------|---------|
| `text` | `data.text`をそのまま使用 |
| `image` | `data.file`を§2.1メディアプロトコルに従って処理（3つの必須形態 + 判定順序） |
| `audio` | `image`と同じ処理ロジック |
| `video` | `image`と同じ処理ロジック |
| `file` | `image`と同じ処理ロジック；ファイル名は§2.1.3の推定順序に従って`data.filename`を処理 |
| `mention` | プラットフォームの@ユーザー機構に変換する（例：Telegramの`entities`、云湖の`at_uid`） |
| `reply` | プラットフォームの返信引用機構に変換する |
| `face` | プラットフォームの表情送信機構に変換する、サポートしない場合はスキップ |
| `location` | プラットフォームの位置送信機構に変換する、サポートしない場合はスキップ |

#### 6.3.2 プラットフォーム拡張メッセージセグメント変換

プラットフォームプレフィックス付きのメッセージセグメントは、アダプターが認識して変換するべきです：

```python
def _convert_ob12_segments(self, segments: List[Dict]) -> Any:
    """OneBot12メッセージセグメントをプラットフォームネイティブ形式に変換する"""
    platform_prefix = f"{self._platform_name}_"
    
    for segment in segments:
        seg_type = segment["type"]
        seg_data = segment["data"]
        
        if seg_type.startswith(platform_prefix):
            # プラットフォーム拡張メッセージセグメント → プラットフォームネイティブ呼び出し
            self._handle_platform_segment(seg_type, seg_data)
        elif seg_type in self._standard_segment_handlers:
            # 標準メッセージセグメント → プラットフォーム同等操作
            self._standard_segment_handlers[seg_type](seg_data)
        else:
            # 未知のメッセージセグメント → 警告を記録してスキップ
            logger.warning(f"サポートしないメッセージセグメントタイプ: {seg_type}")
```

#### 6.3.3 複合メッセージセグメント処理

1つのメッセージには複数のメッセージセグメントが含まれる可能性があり、アダプターは複合メッセージを正しく処理する必要があります：

```python
# モジュールがテキスト+画像+@ユーザーのメッセージを送信
await send.Raw_ob12([
    {"type": "mention", "data": {"user_id": "123"}},
    {"type": "text", "data": {"text": "你好"}},
    {"type": "image", "data": {"file": "https://example.com/img.jpg"}}
])
```

**処理戦略**：
- **優先して結合**：プラットフォームが1つのメッセージにテキスト、画像、@などを同時に含められる場合、結合して送信する
- **次善として分割**：プラットフォームが結合をサポートしない場合、順序に従って複数のメッセージに分割して送信する
- **順序の保持**：メッセージセグメントの送信順序はリストの順序と一致する

### 6.4 `Raw_ob12` と標準メソッドの関係

アダプターの標準送信メソッド（`Text`、`Image`など）は**`SendDSL`基底クラスに既に実装されており、デフォルトで`Raw_ob12`に委譲される**ため、アダプターのサブクラスは再実装する必要はない：

```python
class Send(SendDSL):
    def Raw_ob12(self, message_segments: List[Dict]) -> asyncio.Task:
        """コア実装：OneBot12メッセージセグメント → プラットフォームAPI（必須実装）"""
        return asyncio.create_task(self._send_ob12(message_segments))

    # Text/Image/Voice/Video/File/Locationは基底クラスから継承され、Raw_ob12に自動的に委譲される
    # プラットフォーム固有のロジックが必要な場合、メソッドをオーバーライドする：
    # def Text(self, text: str) -> asyncio.Task:
    #     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

**利点**：
- 変換ロジックは`Raw_ob12`の1か所に集中し、重複コードを減らす
- 標準メソッドと`Raw_ob12`の動作は完全に一致する
- モジュールが`Text()`を使うか`Raw_ob12()`を使うかに関わらず、同じ結果を得られる
- 基底クラスが型シグネチャを提供し、IDEは標準メソッドの補完ができる

### 6.5 実装例

```python
class YunhuSend(SendDSL):
    """云湖プラットフォームのSend実装"""
    
    def Raw_ob12(self, message_segments: list) -> asyncio.Task:
        """OneBot12メッセージセグメント → 云湖API呼び出し"""
        return asyncio.create_task(self._do_send(message_segments))
    
    async def _do_send(self, segments: list) -> dict:
        """実際の送信ロジック"""
        # 1. 修飾子の状態を解析
        at_users = self._at_users or []
        reply_to = self._reply_to
        at_all = self._at_all
        
        # 2. メッセージセグメントを変換
        yunhu_elements = []
        for seg in segments:
            seg_type = seg["type"]
            seg_data = seg["data"]
            
            if seg_type == "text":
                yunhu_elements.append({"type": "text", "content": seg_data["text"]})
            elif seg_type == "image":
                yunhu_elements.append({"type": "image", "url": seg_data["file"]})
            elif seg_type == "mention":
                at_users.append(seg_data["user_id"])
            elif seg_type == "reply":
                reply_to = seg_data["message_id"]
            elif seg_type == "yunhu_form":
                # プラットフォーム拡張メッセージセグメント
                yunhu_elements.append({"type": "form", "form_id": seg_data["form_id"]})
            else:
                logger.warning(f"云湖でサポートしていないメッセージセグメント: {seg_type}")
        
        # 3. 云湖APIを呼び出す
        response = await self._call_yunhu_api(yunhu_elements, at_users, reply_to, at_all)
        
        # 4. 標準応答形式を返す
        return {
            "status": "ok" if response["code"] == 0 else "failed",
            "retcode": response["code"],
            "data": {"message_id": response.get("msg_id", ""), "time": int(time.time())},
            "message_id": response.get("msg_id", ""),
            "message": "",
            "yunhu_raw": response
        }
```

---

## 7. メソッド発見

モジュール開発者は、アダプターがサポートする送信メソッドをAPIで照会できる（**モジュールにプラットフォームのメソッドリストをハードコーディングしてはならない**—各アダプターの拡張メソッドはバージョンの進化に伴い変化するため、ランタイムでの発見が基準となる）：

```python
from ErisPulse import adapter

# すべての送信メソッドをリストアップ
methods = adapter.list_sends("myplatform")
# ["Batch", "Form", "Image", "Recall", "Sticker", "Text", ...]

# メソッドの詳細を照会
info = adapter.send_info("myplatform", "Form")
# {
#     "name": "Form",
#     "parameters": [{"name": "form_id", "type": "str", ...}],
#     "return_type": "Awaitable[Any]",
#     "docstring": "云湖フォームを送信"
# }
```

---

## 9. アダプター開発の注意事項

`BaseAdapter`、`Send`、`Request`の`__init__`を正しくオーバーライドする方法については、[アダプター開発入門 - `__init__`の注意事項](../developer-guide/adapters/getting-started.md#init-注意事项)を参照してください。

---

---

## 10. アダプター実装チェックリスト

### 送信メソッド
- [ ] 標準メソッド（`Text`, `Image`など）は実装済み
- [ ] 戻り値はすべて`asyncio.Task`
- [ ] 修飾メソッド（`At`, `Reply`, `AtAll`）は`self`を返す
- [ ] プラットフォーム拡張メソッドはPascalCaseを使用し、プラットフォームプレフィックスを付けない
- [ ] すべてのメソッドは完全な型注釈とドキュメント文字列を備えている

### メディア送信プロトコル
- [ ] `file`パラメータの**必須形態**（HTTP(S) URL / 本地パス / `bytes`、§2.1.1参照）はすべてサポート
- [ ] 形態判定順序は§2.1.2（bytes → URL → `file://` → パス）に従っている
- [ ] `File`のファイル名推定順序は§2.1.3（明示的な`filename` > URLのbasename > パスのbasename > プラットフォームデフォルト）に従っている
- [ ] プラットフォームのメディア制限（サイズ / MIME / 時長）はアダプターのドキュメントに声明されている（§2.1.4）
- [ ] メディア形式がサポートされていない場合は、§2.1.5の降格段階に従って処理する（近縁な形式に降格するか、`retcode=10002`を返す）、例外をスローしたり、静かに破棄したりしない

### 合併転送（オプション、§2.4参照）
- [ ] プラットフォームに原生の合併転送がある場合、`MergeForward`はプロトコル専用エンドポイントを経由し、失敗した場合は`send_msg`に回復する（OneBot11系）
- [ ] プラットフォームに原生の転送機能はないが、富文本がある場合、`MergeForward`はプラットフォームの折りたたみ形態（HTMLカード / Card / Embed / blockquote）にレンダリングする
- [ ] 両方ない場合は**`MergeForward`を実装しない**、node辞書を純粋なテキストとして発信してはならない
- [ ] `MergeForward`の中で`Raw_ob12`を再呼び出さない（OneBot11の`Raw_ob12`はnodeセグメントの自動ルーティングを内蔵しており、循環する）

### 逆変換
- [ ] `Raw_ob12`は**実装済み**（必須、スキップしてはならない）
- [ ] `Raw_ob12`はすべての標準メッセージセグメント（`text`, `image`, `audio`, `video`, `file`, `mention`, `reply`）を処理できる
- [ ] `Raw_ob12`はプラットフォーム拡張メッセージセグメント（`{platform}_xxx`形式）を処理できる
- [ ] 標準送信メソッド（`Text`, `Image`など）は`Raw_ob12`に委譲しており、個別の変換ロジックを独立して実装していない
- [ ] サポートしていないメッセージセグメントは警告を記録してスキップし、例外をスローしてはならない
- [ ] 複合メッセージセグメントは正しく処理する（結合するか、順序に従って分割する）

---

## 11. メッセージビルダー（MessageBuilder）—アダプター側の注意事項

`MessageBuilder`はErisPulseが提供するOneBot12メッセージセグメント構築ツールであり、**モジュール側**がメッセージを構築するために使用する：チェーン呼び出し（または静的高速構築）により、最終的にOneBot12メッセージセグメントリスト`[{"type": ..., "data": ...}]`を生成し、`Raw_ob12`に直接渡される。

**アダプター側はこれを知るだけでよい**：`Raw_ob12`が受け取るのはこの生成物—`MessageBuilder`かリテラルかに関わらず、`Raw_ob12`は§6.2のセグメント分離ロジックに従って処理するだけで、`MessageBuilder`か手書きかを意識する必要はない。

> 完全な使い方（二重モードメカニズム、すべてのメッセージセグメントメソッド、`copy()` / `clear()`ツールメソッドと例）は[MessageBuilder 詳解](../advanced/message-builder.md)を参照してください。本文では繰り返しません。

---

## 12. 関連ドキュメント

**送信戻り値を実装する際の対応**：
- [API応答標準](api-response.md) - アダプターAPIの応答形式標準

**同一アダプターの他の側面**：
- [イベント変換標準](event-conversion.md) - 完全なイベント変換規格、拡張命名とメッセージセグメント標準
- [セッションタイプ標準](session-types.md) - セッションタイプの定義とマッピング関係
- [リクエスト操作規格](request-action-spec.md) - リクエストイベントのフィールド要件、Request DSL（approve/reject）とアダプター実装要件