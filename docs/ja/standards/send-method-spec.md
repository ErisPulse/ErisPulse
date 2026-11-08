# ErisPulse 送信メソッド規格

> [!TIP]
> **このドキュメントを読むべきタイミング**：アダプタで Send クラスを実装する際、メソッド命名、メディアパラメータ（URL/パス/bytes）のサポート、`Raw_ob12` の逆変換、メッセージの転送機能など、本文を参照してください。必要がない場合は飛ばしてください。

本文書では、ErisPulse アダプタにおける Send クラスの送信メソッドの命名規則、引数規則、逆変換要件を定義します。

## 0. キーワードの約束

本文書における **必須（MUST）**、**推奨（SHOULD）**、**可選（MAY）** は、RFC 2119 に従い以下の意味で解釈されます：

| キーワード | 意味 | 違反時の影響 |
|--------|------|---------|
| **必須** | 強制要件。フレームワークの動作やクロスプラットフォームの一貫性に依存 | アダプタは仕様に準拠していないと見なされ、モジュールのコードが動作しない可能性がある |
| **推奨** | 強く推奨。十分な理由がない限り、遵守すべき | 違反する場合は、アダプタのドキュメントに理由と代替動作を明記する |
| **可選** | 選択肢。プラットフォームの能力に応じて決定 | 無 |

## 1. 標準メソッド命名

すべての送信メソッドは **PascalCase（大文字で始まる）** を使用します。

### 1.1 標準送信メソッド

| メソッド名 | 説明 | 引数の型 | 実装要件 |
|-------|------|---------|---------|
| `Text` | テキストメッセージを送信 | `str` | 必須 |
| `Image` | 画像を送信 | `str` \| `bytes` | 必須（基底クラスで既に実装済み、§6.4参照） |
| `Voice` | 音声を送信 | `str` \| `bytes` | 必須（基底クラスで既に実装済み；プラットフォームが音声をサポートしない場合は §2.1.5 に従って降格） |
| `Video` | 動画を送信 | `str` \| `bytes` | 必須（基底クラスで既に実装済み；プラットフォームが動画をサポートしない場合は §2.1.5 に従って降格） |
| `File` | ファイルを送信 | `str` \| `bytes`、`filename: str \| None = None` | 必須（基底クラスで既に実装済み） |
| `Location` | 位置メッセージを送信 | `float` (latitude/longitude)、`title: str = ""`、`content: str = ""` | 必須（基底クラスで既に実装済み） |
| `At` | ユーザー/グループを@する | `str` (user_id) | 修飾メソッド、必要に応じて |
| `Face` | 顔文字を送信 | `str` (emoji) | 可能 |
| `Reply` | メッセージに返信する | `str` (message_id) | 修飾メソッド、必要に応じて |
| `Forward` | メッセージを転送する | `str` (message_id) | 可能 |
| `Markdown` | Markdownメッセージを送信 | `str` | 可能 |
| `HTML` | HTMLメッセージを送信 | `str` | 可能 |
| `Card` | カードメッセージを送信 | `dict` | 可能 |

> 標準メソッド（`Text`/`Image`/`Voice`/`Video`/`File`/`Location`）は基底クラス `SendDSL` に内蔵されており、デフォルトで `Raw_ob12` に委譲されるため、アダプタは再実装する必要がなく、型署名が得られる。プラットフォームに特別なロジックが必要な場合のみ、個々のメソッドをオーバーライドする（§6.4参照）。

### 1.2 鏈式修飾メソッド

| メソッド名 | 説明 | 引数の型 |
|-------|------|---------|
| `At` | ユーザーを@する（複数回呼び出し可能） | `str` (user_id) |
| `AtAll` | 全員を@する | 無 |
| `Reply` | メッセージに返信する | `str` (message_id) |

### 1.3 協定メソッド

| メソッド名 | 説明 | 必須か |
|-------|------|---------|
| `Raw_ob12` | OneBot12形式のメッセージセグメントを送信 | 必須 |

**`Raw_ob12` は必須実装のメソッド**です。これはアダプタの主要な責任の一つであり、OneBot12標準メッセージセグメントを受け取り、それをプラットフォーム固有のAPI呼び出しに変換します。`Raw_ob12` はOneBot12 → プラットフォームへの逆変換の統一エントリポイントであり、モジュールがプラットフォーム固有のメソッドに依存せず、直接標準メッセージセグメントを使ってメッセージを送信できるようにします。

**`Raw_ob12` をオーバーライドしない場合の動作**：基底クラスのデフォルト実装は **errorレベル** のログを記録し、標準エラー応答形式（`status: "failed"`, `retcode: 10002`）を返し、アダプタ開発者がこのメソッドを実装する必要があることを示します。

### 1.4 推奨される拡張命名規約

アダプタがOneBot12形式以外の生データ（プラットフォーム固有のJSON、XMLなど）を送信する必要がある場合、以下の命名規約を推奨します：

| 推奨メソッド名 | 説明 |
|-----------|------|
| `Raw_json` | 任意のJSONデータを送信 |
| `Raw_xml` | 任意のXMLデータを送信 |

**注意**：これらのメソッドは**基底クラスで提供されているものではなく、強制的に実装する必要もありません**。これらは命名規約としてのみ提供され、アダプタは必要に応じて独自に定義できます。アダプタがこれらの形式をサポートしていない場合は、定義する必要はありません。

**メッセージビルダー（MessageBuilder）**：ErisPulseは、OneBot12メッセージセグメントリストを簡単に構築するための`MessageBuilder`ツールクラスを提供しており、`Raw_ob12`と併用できます。詳しくは [MessageBuilder 详解](../advanced/message-builder.md) を参照してください。

## 2. 引数規格の詳細

### 2.1 メディアメッセージ送信プロトコル（`Image` / `Voice` / `Video` / `File`）

本節はメディア送信の**統一プロトコル仕様**です：モジュールは同一のコードで4つのメディアメソッドを呼び出し、アダプタは`file`引数の様々な形態をプラットフォーム固有のアップロード/送信動作に変換します。

#### 2.1.1 `file` 引数の合法な形態

| 形態 | 例 | アダプタの要件 |
|------|------|-----------|
| HTTP(S) URL | `https://example.com/image.jpg` | **必須**で受け入れ |
| 本地ファイルパス | `/path/to/file.jpg`、`C:\path\to\file.jpg` | **必須**で受け入れ |
| 二進データ | `b"\x89PNG..."` | **必須**で受け入れ |
| `file://` URI | `file:///path/to/file.jpg` | **推奨**で受け入れ（ローカルパスに転送して処理） |
| Base64文字列 / Data URI | `iVBORw0KGgo=...`、`data:image/png;base64,...` | **推奨**で受け入れ（OneBot12エコシステムとの互換性） |

> アダプタは**3つの必須形態**で動作が一貫する必要があります。モジュールがURL、パス、bytesのいずれを渡しても、受け取るメッセージは同一になります。プラットフォームが外部URLを直接使用できない場合（APIがURLの参照をサポートしていない）、アダプタはダウンロード/読み込み後にアップロードを行い、**モジュールに再試行を要求することはありません**。

#### 2.1.2 形態判定順序

アダプタがメディア引数を処理する際には、**以下のように形態を判定する順序で判定するべきです**：

1. `bytes`型 → 直接アップロード
2. 文字列が `http://` / `https://` で始まる → URLとして処理（直接参照またはダウンロード後にアップロード、プラットフォームの能力に応じて）
3. 文字列が `file://` で始まる → プレフィックスを剥離してローカルパスとして処理
4. その他の文字列 → ローカルパスとして処理（存在すれば読み込みアップロード、存在しない場合は標準エラー応答を返す）

```python
def _resolve_media(self, file: "str | bytes") -> bytes:
    """形態判定と正規化（例）"""
    if isinstance(file, (bytes, bytearray)):
        return bytes(file)
    if file.startswith(("http://", "https://")):
        return self._download(file)          # プラットフォームがURLを参照できない場合、ダウンロード
    if file.startswith("file://"):
        file = file[len("file://"):]
    with open(file, "rb") as f:              # 本地パス
        return f.read()
```

#### 2.1.3 `File` のファイル名の意味

`File` メソッドの署名：`File(file, filename=None)`（`filename` はオプション引数、基底クラスで既に実装済み）。

ファイル名の**推定順序**（アダプタが明示的に `filename` を提供しない場合に使用）：

1. 明示的な `filename` 引数（最優先）
2. URLのbasename（例：`https://host/a/b/report.pdf` → `report.pdf`、クエリ文字列を剥離）
3. 本地パスのbasename（例：`/tmp/data/backup.zip` → `backup.zip`）
4. プラットフォームがデフォルトで生成する（例：`file_{timestamp}`；**推奨**は実際の拡張子を保持すること——拡張子はプラットフォーム側のタイプ識別とプレビュー動作に影響）

> `Image` / `Voice` / `Video` は**可能**で `filename` を受け入れる（メッセージセグメント `data.filename` で渡される）が、`File` のみが跨プラットフォームのファイル名の意味を保証する。

#### 2.1.4 プラットフォーム制限の宣言義務

各プラットフォームはメディアのサイズ上限、形式（MIME）、時長（音声/動画）などに制限があります。アダプタは**推奨**されます：

- アダプタのドキュメントにサポートするメディア形式と制限範囲を宣言する
- 超限または不支持の入力に対しては**標準エラー応答**を返す（`status: "failed"`；`retcode` は `10002` またはプラットフォーム固有のエラーコード、`message` に原因を説明する）、**例外をスローしてモジュールのロジックを中断することはない**

#### 2.1.5 機能降格の段階

プラットフォームがメディアの**型**をサポートしない場合、以下の段階で降格する（「機能降格はエラーを出さない」原則に従う）：

| 状況 | 降格動作 |
|------|---------|
| `Voice` が音声メッセージをサポートしない | **推奨**で `File`（またはプラットフォームに近縁な形態）で送信する；表現できない場合は `retcode=10002` を返す |
| `Video` が動画メッセージをサポートしない | 同上 |
| メディアの型が完全にサポートされていない（ファイル機能がない） | `retcode=10002` を返し、`message` にサポートしていないデータ型を明記する |
| 形態がサポートされていない（例：base64が処理できない） | `retcode=10002` を返し、`message` にモジュールがURL/bytesに変更するよう提示してもよい |

**禁止される動作**：静かに破棄（返却がない）、例外をスローする、モジュールにプラットフォーム固有の処理を書かせる。

### 2.2 @ユーザー引数の規格

**メソッド：** `At`（修飾メソッド）

**引数：** `user_id` (`str`)

**要件：**
- `user_id` は文字列型のユーザー識別子であるべき
- 各プラットフォームの `user_id` 形式は異なる（数字、UUID、文字列など）
- アダプタは `user_id` をプラットフォーム固有の形式に変換する責任がある
- 実際の送信メソッドの呼び出しは最後に位置させるべき

**例：**
```python
# 単一の@ユーザー
Send.To("group", "g123").At("123456").Text("你好")

# 複数の@ユーザー（連鎖呼び出し）
send.To("group", "g123").At("123456").At("789012").Text("大家好")
```

### 2.3 メッセージ返信引数の規格

**メソッド：** `Reply`（修飾メソッド）

**引数：** `message_id` (`str`)

**要件：**
- `message_id` は文字列型のメッセージ識別子であるべき
- 以前に受信したメッセージのIDであるべき
- 一部のプラットフォームは返信機能をサポートしていないため、アダプタは優雅に降格するべき

**例：**
```python
send.To("group", "g123").Reply("msg_123456").Text("收到")
```

### 2.4 メッセージの結合転送機能（`MergeForward`、オプション）

`MergeForward(nodes)` は**オプションの機能メソッド**です：複数の内容を「結合転送 / フルテキスト折りたたみ」の形式で送信するためのもので、アダプタはプラットフォームの能力に応じて最適な表示方法を決定します。§1.1の `Forward(from_chat_id, message_id)`（既存のメッセージを転送する）とは異なる意味を持ち、併存します。

> **標準の背景**：OneBot12のコア標準にはnodeメッセージセグメントも、結合転送APIもありません。"メッセージノード"はOneBot v11エコシステム（go-cqhttp拡張）の実装層の概念であり、v12ではこれらのプラットフォーム特有の機能を拡張メカニズムに委譲しました。ErisPulseの実装方法は拡張メカニズムの同等物です：**標準メッセージセグメントを追加せず、オプションの機能メソッド + `list_sends`のランタイム検出**——`MergeForward`を実装したアダプタは自動的に機能を獲得し、実装していない場合は呼び出し元が普通のテキストに自動的に降格し、モジュールは変更を必要としません。

**メソッドの署名：**

```python
def MergeForward(self, nodes: List[Dict]) -> asyncio.Task:
    """
    結合転送 / フルテキスト折りたたみメッセージを送信

    :param nodes: 結合転送ノードの配列（go-cqhttp拡張のOneBot v11ノード形式）：
        [
            {
                "type": "node",
                "data": {
                    "user_id": "10000",     # 表示用の送信者ID
                    "nickname": "MyBot",     # 表示用の送信者ニックネーム
                    "content": [            # メッセージセグメントの配列、現在はtextセグメントのみ
                        {"type": "text", "data": {"text": "【1/3】タイトル\n本文…"}}
                    ],
                },
            },
        ]
    :return: asyncio.Task、await後に標準応答形式を返す
    """
```

**実装要件：**

1. **プラットフォームに原生の結合転送がある**（OneBot11系）：**必須**でプロトコル専用エンドポイント（`send_group_forward_msg` / `send_private_forward_msg`）を呼び出すべきです。NapCatなどは`send_msg`に含まれるnodeセグメントを拒否します（retcode 1400）；専用エンドポイントが失敗した場合は`send_msg`でnodeセグメントを直接送信することも可能です。
2. **プラットフォームに原生の転送機能がないが、富テキスト機能がある**（云湖 / Telegram / Kook / Discord / Matrixなど）：**推奨**でノードをプラットフォームの富テキスト折りたたみ形態（HTML折りたたみカード / Card / Embed / blockquoteリスト）にレンダリングするべきです。参考スタイルと各アダプタのタスクリストは`SDK/Adapter/ADAPTER_FORWARD_GUIDE.md`を参照してください。
3. **両方がない**：**実装しないでください**（node辞書を純粋なテキストとして発信してはいけません）——実装していない場合、`list_sends`に`MergeForward`が含まれず、呼び出し元は自動的に普通のテキストに降格します。
4. **失敗の意味**：標準エラー応答（`status: "failed"`）を返すか、例外をスローしても構いません。呼び出し元は普通のテキスト送信に降格し、内容は失われません。
5. **`MergeForward`内で`Raw_ob12`を再利用して同じnodesを送信しないでください**（OneBot11の`Raw_ob12`はnodeセグメントの自動ルーティングを既に内蔵しており、ループになります）。
6. **出力nodeセグメントの解析**（全アダプタの約束）：各アダプタの`Raw_ob12`セグメント配信は`node`セグメントを登録するべきです。純粋なnodeリストは自動的に本アダプタの結合転送表示にルーティングされます（`MergeForward`があるプラットフォームは直接呼び出すのと同等です；このメソッドがないプラットフォームは各ノードのテキストを「ニックネーム: 本文」として1行ずつ**原文出力**します）；混合リスト中のnodeセグメントのテキストは本文に統合されます。どのアダプタもnodeセグメントを静かに破棄してはいけません。

**プラットフォーム実装形態**（`SDK/Adapter/ADAPTER_FORWARD_GUIDE.md`を参照）：

- 原生エンドポイント：OneBot11、SnowLuma（3段階の降格：`send_group/private_forward_msg`専用エンドポイント → `upload_forward_msg`でresidを取得してforwardセグメントを送信 → nodeセグメントを直接送信；SnowLuma APIはNapCatと向かい合っており、アダプタはNapCatバックエンドに直接接続できます）
- 折りたたみHTML `<details>` カード：云湖（bot/ユーザー協定）、Email、Sandbox、Allons(Ideaura)
- ホワイトリストHTML / 引用ブロック：Telegram（`<b>`+`<blockquote>`）、Matrix（blockquoteのバリエーション、details/インラインスタイルをホワイトリストで除去）
- プラットフォームカード：Kook（Card header+section）、Discord（Embed fields）
- 公式Markdown引用リスト：QQBot（公式mdは折りたたみ構文がなく、サーバーサイドで無効なタグを40034011で拒否）
- 実装しない（nodeセグメントを原文出力して降格）：OneBot12（標準にはnodeセグメントがない）、WeCom、Terminal、Webhook、WechatMp

**呼び出し元の検出例：**

```python
sends = adapter.list_sends(platform)
if "MergeForward" in sends:
    await adapter.Send.To("group", "123").MergeForward(nodes)
else:
    await adapter.Send.To("group", "123").Text(plain_text)
```

> 参考実装：`ErisPulse-OneBot11Adapter`（専用エンドポイント → `send_msg`の降格）；レンダリングテンプレートと各アダプタのタスクリストは`SDK/Adapter/ADAPTER_FORWARD_GUIDE.md`を参照してください。

## 3. プラットフォーム固有メソッドの命名

Sendクラスに直接プラットフォームプレフィックス付きのメソッドを追加することは**推奨されません**。代わりに、一般的なメソッド名または`Raw_{プロトコル}`メソッドを使用することを推奨します。

**推奨されない例：**
```python
def YunhuForm(self, form_id: str):  # ❌ 推奨されない
    pass

def TelegramSticker(self, sticker_id: str):  # ❌ 推奨されない
    pass
```

**推奨される例：**
```python
def Form(self, form_id: str):  # ✅ 一般的なメソッド名
    pass

def Sticker(self, sticker_id: str):  # ✅ 一般的なメソッド名
    pass

def Raw_ob12(self, message):  # ✅ OneBot12形式を送信
    pass
```

**拡張メソッドの要件**：
- メソッド名はPascalCaseを使用し、プラットフォームプレフィックスを付けない
- `asyncio.Task`オブジェクトを返す必要がある
- 完全な型注釈とドキュメント文字列を提供する必要がある
- パラメータ設計は標準メソッドのスタイルにできるだけ合わせる

## 4. パラメータ名の規格

| パラメータ名 | 説明 | 型 |
|-------|------|------|
| `text` | テキスト内容 | `str` |
| `file` | メディア内容（URL / パス / 二進数、§2.1.1参照） | `str` / `bytes` |
| `filename` | ファイル名（`File`はオプション、§2.1.3参照） | `str` / `None` |
| `user_id` | ユーザーID | `str` / `int` |
| `group_id` | グループID | `str` / `int` |
| `message_id` | メッセージID | `str` |
| `data` | データオブジェクト（例：カードデータ） | `dict` |

## 5. 戻り値の規格

- **送信メソッド**（例：`Text`, `Image`）：`asyncio.Task`オブジェクトを返す必要がある
- **修飾メソッド**（例：`At`, `Reply`, `AtAll`）：`self`を返して、メソッドチェーンを可能にする必要がある

---

## 6. 逆変換規格（OneBot12 → プラットフォーム）

アダプタは、プラットフォーム固有のイベントをOneBot12形式に変換するだけでなく、**OneBot12メッセージセグメントをプラットフォーム固有のAPI呼び出しに変換する逆変換の能力も必須**です。逆変換の統一エントリポイントは`Raw_ob12`メソッドです。

### 6.1 変換モデル

```
正方向変換（受信方向）                逆方向変換（送信方向）
─────────────────                ─────────────────
プラットフォーム固有のイベント                       OneBot12メッセージセグメントリスト
    │                                  │
    ▼                                  ▼
Converter.convert()               Send.Raw_ob12()
    │                                  │
    ▼                                  ▼
OneBot12標準イベント                  プラットフォーム固有のAPI呼び出し
（{platform}_rawを含む）             （標準応答形式を返す）
```

**コアの対称性**：正方向変換は元のデータを`{platform}_raw`に保持し、逆方向変換はOneBot12標準形式を受け取り、プラットフォームの呼び出しに還元する。

### 6.2 `Raw_ob12`の実装規格

`Raw_ob12`はOneBot12標準メッセージセグメントリストを受け取り、それをプラットフォーム固有のAPI呼び出しに変換する必要があります。

**メソッドの署名：**

```python
def Raw_ob12(self, message_segments: List[Dict]) -> asyncio.Task:
    """
    OneBot12標準メッセージセグメントを送信

    :param message_segments: OneBot12メッセージセグメントリスト
        [
            {"type": "text", "data": {"text": "Hello"}},
            {"type": "image", "data": {"file": "https://..."}},
            {"type": "mention", "data": {"user_id": "123"}},
        ]
    :return: asyncio.Task、await後に標準応答形式を返す
    """
```

**実装要件**：

1. **すべての標準メッセージセグメントタイプを処理する必要がある**：少なくとも`text`、`image`、`audio`、`video`、`file`、`mention`、`reply`をサポートする
2. **プラットフォーム拡張メッセージセグメントを処理する必要がある**：`{platform}_xxx`形式のメッセージセグメントは、プラットフォームに相当する固有の呼び出しに変換する
3. **標準応答形式を返す必要がある**：[API応答標準](api-response.md)に従う
4. **サポートしないメッセージセグメントは警告を記録してスキップする**。例外をスローしてメッセージ全体の送信を失敗させない

### 6.3 メッセージセグメント変換ルール

#### 6.3.1 標準メッセージセグメント変換

アダプタは以下の標準メッセージセグメントの変換を実装する必要があります：

| OneBot12メッセージセグメント | 変換要件 |
|----------------|---------|
| `text` | `data.text`をそのまま使用 |
| `image` | `data.file`を§2.1メディアプロトコルに従って処理（3つの必須形態 + 判定順序） |
| `audio` | `image`と同じ処理ロジック |
| `video` | `image`と同じ処理ロジック |
| `file` | `image`と同じ処理ロジック；ファイル名は§2.1.3の推定順序に従って`data.filename`を処理 |
| `mention` | プラットフォームの@ユーザー機能（例：Telegramの`entities`、云湖の`at_uid`）に変換する |
| `reply` | プラットフォームの返信引用機能に変換する |
| `face` | プラットフォームの顔文字送信機能に変換する。サポートしない場合はスキップする |
| `location` | プラットフォームの位置送信機能に変換する。サポートしない場合はスキップする |

#### 6.3.2 プラットフォーム拡張メッセージセグメント変換

プラットフォームプレフィックス付きのメッセージセグメントは、アダプタが認識して変換する必要があります：

```python
def _convert_ob12_segments(self, segments: List[Dict]) -> Any:
    """OneBot12メッセージセグメントをプラットフォーム固有の形式に変換"""
    platform_prefix = f"{self._platform_name}_"
    
    for segment in segments:
        seg_type = segment["type"]
        seg_data = segment["data"]
        
        if seg_type.startswith(platform_prefix):
            # プラットフォーム拡張メッセージセグメント → プラットフォーム固有の呼び出し
            self._handle_platform_segment(seg_type, seg_data)
        elif seg_type in self._standard_segment_handlers:
            # 標準メッセージセグメント → プラットフォーム同等の操作
            self._standard_segment_handlers[seg_type](seg_data)
        else:
            # 未知のメッセージセグメント → 警告を記録してスキップ
            logger.warning(f"サポートしないメッセージセグメント: {seg_type}")
```

#### 6.3.3 複合メッセージセグメントの処理

1つのメッセージには複数のメッセージセグメントが含まれる可能性があり、アダプタは正しく処理する必要があります：

```python
# モジュールがテキスト+画像+@ユーザーを含むメッセージを送信
await send.Raw_ob12([
    {"type": "mention", "data": {"user_id": "123"}},
    {"type": "text", "data": {"text": "你好"}},
    {"type": "image", "data": {"file": "https://example.com/img.jpg"}}
])
```

**処理戦略**：
- **優先的に結合**：プラットフォームが1つのメッセージにテキスト、画像、@などを同時に含める場合、結合して送信する
- **次に分割**：プラットフォームが結合をサポートしない場合、順番に複数のメッセージに分割して送信する
- **順序を保持**：メッセージセグメントの送信順序はリストの順序と一致する

### 6.4 `Raw_ob12` と標準メソッドの関係

アダプタの標準送信メソッド（`Text`、`Image`など）は**`SendDSL`基底クラスで既に実装され、デフォルトで`Raw_ob12`に委譲されている**ため、アダプタのサブクラスは再実装する必要はありません：

```python
class Send(SendDSL):
    def Raw_ob12(self, message_segments: List[Dict]) -> asyncio.Task:
        """コア実装：OneBot12メッセージセグメント → プラットフォームAPI（必須実装）"""
        return asyncio.create_task(self._send_ob12(message_segments))

    # Text/Image/Voice/Video/File/Locationは基底クラスから継承され、Raw_ob12に自動的に委譲される
    # プラットフォーム特有のロジックが必要な場合は、個々のメソッドをオーバーライドする：
    # def Text(self, text: str) -> asyncio.Task:
    #     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

**利点**：
- 変換ロジックは`Raw_ob12`に1か所に集中し、重複コードを減らす
- 標準メソッドと`Raw_ob12`の動作は完全に一致する
- モジュールが`Text()`を使うか`Raw_ob12()`を使うかに関わらず、同じ結果を得られる
- 基底クラスが型署名を提供し、IDEは標準メソッドを補完できる

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
                logger.warning(f"云湖でサポートしないメッセージセグメント: {seg_type}")
        
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

## 7. メソッドの発見

モジュール開発者は、アダプタがサポートする送信メソッドをAPIで照会することができます（**モジュール内でプラットフォームのメソッドリストをハードコードしないでください**——各アダプタの拡張メソッドはバージョンの進化に伴い変更されるため、ランタイムでの発見が標準です）：

```python
from ErisPulse import adapter

# すべての送信メソッドをリストアップ
methods = adapter.list_sends("myplatform")
# ["Batch", "Form", "Image", "Recall", "Sticker", "Text", ...]

# メソッドの詳細を取得
info = adapter.send_info("myplatform", "Form")
# {
#     "name": "Form",
#     "parameters": [{"name": "form_id", "type": "str", ...}],
#     "return_type": "Awaitable[Any]",
#     "docstring": "云湖フォームを送信"
# }
```

---

## 9. アダプタ開発の注意事項

`BaseAdapter`、`Send`、`Request`の`__init__`を正しくオーバーライドする方法については、[アダプタ開発入門 - `__init__` 注意事項](../developer-guide/adapters/getting-started.md#init-注意事项)を参照してください。

---

---

## 10. アダプタ実装チェックリスト

### 送信メソッド
- [ ] 標準メソッド（`Text`, `Image`等）は実装済み
- [ ] 戻り値はすべて`asyncio.Task`
- [ ] 修飾メソッド（`At`, `Reply`, `AtAll`）は`self`を返す
- [ ] プラットフォーム拡張メソッドはPascalCaseを使用し、プラットフォームプレフィックスを付けない
- [ ] すべてのメソッドには完全な型注釈とドキュメント文字列がある

### メディア送信プロトコル
- [ ] `file`引数の**必須形態**はすべてサポート：HTTP(S) URL / 本地パス / `bytes`（§2.1.1参照）
- [ ] 形態判定順序は§2.1.2に従う（bytes → URL → `file://` → パス）
- [ ] `File`のファイル名の推定順序は§2.1.3に従う（明示的な`filename` > URLのbasename > パスのbasename > プラットフォームのデフォルト）
- [ ] プラットフォームのメディア制限（サイズ / MIME / 時長）はアダプタのドキュメントに宣言されている
- [ ] プラットフォームがサポートしていないメディア形式は、§2.1.5の降格段階に従って処理する：近縁形式に降格するか、`retcode=10002`を返す；例外をスローしたり、静かに破棄したりしない

### 結合転送（オプション、§2.4参照）
- [ ] プラットフォームに原生の結合転送がある場合、`MergeForward`はプロトコルの専用エンドポイントを使用し、失敗した場合は`send_msg`に回帰する（OneBot11系）
- [ ] プラットフォームに原生の転送機能がないが、富テキスト機能がある場合、`MergeForward`はプラットフォームの折りたたみ形態（HTMLカード / Card / Embed / blockquote）にレンダリングする
- [ ] 両方ともない場合、`MergeForward`を実装しない；node辞書を純粋なテキストとして発信しない
- [ ] `MergeForward`内部で`Raw_ob12`を再利用して同じnodesを送信しない

### 逆変換
- [ ] `Raw_ob12`は**実装済み**（必須、スキップ不可）
- [ ] `Raw_ob12`はすべての標準メッセージセグメント（`text`, `image`, `audio`, `video`, `file`, `mention`, `reply`）を処理できる
- [ ] `Raw_ob12`はプラットフォーム拡張メッセージセグメント（`{platform}_xxx`形式）を処理できる
- [ ] 標準送信メソッド（`Text`, `Image`等）は`Raw_ob12`に委譲されており、個別に変換ロジックを実装していない
- [ ] サポートしないメッセージセグメントは警告を記録してスキップし、例外をスローしない
- [ ] 複合メッセージセグメントは正しく処理される（結合または順序に従って分割）

---

## 11. メッセージビルダー（MessageBuilder）——アダプタ側の注意事項

`MessageBuilder`はErisPulseが提供するOneBot12メッセージセグメントの構築ツールであり、**モジュール側**でメッセージを構築するために使用されます。メソッドチェーン（または静的高速構築）により、最終的に`Raw_ob12`に渡すOneBot12メッセージセグメントリストを生成します。

**アダプタ側は以下だけを知っていればよい**：`Raw_ob12`が受け取るのはこの生成物です——`MessageBuilder`から来たか、文字列リテラルかは関係なく、`Raw_ob12`は§6.2のセグメント配布ロジックに従って処理するだけで、`MessageBuilder`の存在を意識する必要はありません。

> 完全な使い方（両方のモード、全メッセージセグメントメソッド、`copy()` / `clear()` ユーティリティメソッドと例）は [MessageBuilder 详解](../advanced/message-builder.md) を参照してください。本文では繰り返しません。

---

## 12. 関連ドキュメント

**送信メソッドの戻り値を実装する際の併用**：
- [API応答標準](api-response.md) - アダプタAPIの応答形式の標準

**同一アダプタの他の側面**：
- [イベント変換標準](event-conversion.md) - 完全なイベント変換規格、拡張命名とメッセージセグメント標準
- [セッションタイプ標準](session-types.md) - セッションタイプの定義とマッピング関係
- [リクエスト操作規格](request-action-spec.md) - リクエストイベントのフィールド要件、HandleRequest DSLおよびアダプタ実装要件