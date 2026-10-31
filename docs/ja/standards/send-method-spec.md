# ErisPulse 送信メソッド規格

> [!TIP]
> **このドキュメントを読むべきタイミング**: 送信メソッドの実装を行う際、命名規則、メディアパラメータ（URL/パス/bytes）のサポート、`Raw_ob12` への逆変換、メッセージの転送機能など、本文書を参照してください。必要ない場合はスキップしてください。

本文書では、ErisPulseアダプターにおける `Send` クラスの送信メソッドの命名規則、パラメータ規格、逆変換要件を定義します。

## 0. キーワードの定義

本文書内の **必須（MUST）**、**推奨（SHOULD）**、**可能（MAY）** は、RFC 2119に準拠した意味で解釈されます：

| キーワード | 意味 | 違反時の影響 |
|--------|------|---------|
| **必須** | 強制的要件、フレームワークの動作やプラットフォーム間の一貫性に依存 | アダプターは標準に準拠していないと見なし、モジュールコードが正常に動作しない |
| **推奨** | 強く推奨される；正当な理由がない限り、遵守する | 違反する場合は、アダプターのドキュメントに理由と代替動作を明記する |
| **可能** | オプション、プラットフォームの能力に応じて決定 | 無 |

## 1. 標準メソッド命名

すべての送信メソッドは **大文字キャメルケース（PascalCase）** を使用します。先頭文字は大文字です。

### 1.1 標準送信メソッド

| メソッド名 | 説明 | パラメータ型 | 実装要件 |
|-------|------|---------|---------|
| `Text` | テキストメッセージを送信 | `str` | 必須 |
| `Image` | 画像を送信 | `str` \| `bytes` | 必須（基底クラスに既に実装済み、§6.4参照） |
| `Voice` | 音声を送信 | `str` \| `bytes` | 必須（基底クラスに既に実装済み；プラットフォームが音声をサポートしない場合は、§2.1.5に従って降格） |
| `Video` | 動画を送信 | `str` \| `bytes` | 必須（基底クラスに既に実装済み；プラットフォームが動画をサポートしない場合は、§2.1.5に従って降格） |
| `File` | ファイルを送信 | `str` \| `bytes`、`filename: str \| None = None` | 必須（基底クラスに既に実装済み） |
| `At` | ユーザー/グループを@する | `str` (user_id) | 修飾メソッド、必要に応じて |
| `Face` | 表情を送信 | `str` (emoji) | 可能 |
| `Reply` | メッセージに返信する | `str` (message_id) | 修飾メソッド、必要に応じて |
| `Forward` | メッセージを転送する | `str` (message_id) | 可能 |
| `Markdown` | Markdownメッセージを送信 | `str` | 可能 |
| `HTML` | HTMLメッセージを送信 | `str` | 可能 |
| `Card` | カードメッセージを送信 | `dict` | 可能 |

> 標準メソッド（`Text`/`Image`/`Voice`/`Video`/`File`）は、基底クラス `SendDSL` に内臓されており、デフォルトで `Raw_ob12` に委譲されます。アダプターは、単一の型署名を獲得するため、これらのメソッドを再実装する必要はありません。ただし、プラットフォームに特別なロジックが必要な場合は、個別のメソッドをオーバーライドしてください（§6.4参照）。

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

**`Raw_ob12` は必須実装のメソッドです**。これはアダプターの主要な責任の一つです：OneBot12標準メッセージセグメントを受け取り、それをプラットフォームのネイティブAPI呼び出しに変換します。`Raw_ob12` は、OneBot12 → プラットフォームへの逆変換の統一エントリーポイントであり、モジュールがプラットフォーム固有のメソッドに依存することなく、標準メッセージセグメントを使ってメッセージを送信できるようにします。

**`Raw_ob12` をオーバーライドしない場合の動作**：基底クラスのデフォルト実装は、**errorレベル**のログを記録し、標準エラー応答形式（`status: "failed"`, `retcode: 10002`）を返し、アダプター開発者がこのメソッドを実装する必要があることを示します。

### 1.4 推奨される拡張命名規則

アダプターがOneBot12形式以外の生データ（プラットフォーム固有のJSON、XMLなど）を送信する必要がある場合、以下の命名規則を推奨します：

| 推奨メソッド名 | 説明 |
|-----------|------|
| `Raw_json` | 任意のJSONデータを送信 |
| `Raw_xml` | 任意のXMLデータを送信 |

**注意**：これらのメソッドは**基底クラスに提供されたデフォルトメソッドではなく、強制実装も要求されていません**。これらは命名規則としてのみ、アダプターが必要に応じて独自に定義できます。アダプターがこれらの形式をサポートしていない場合は、定義する必要はありません。

**メッセージビルダー（MessageBuilder）**：ErisPulseは、OneBot12メッセージセグメントリストを簡単に構築するための `MessageBuilder` ツールクラスを提供しており、`Raw_ob12` と併用できます。詳細は [MessageBuilder 详解](../advanced/message-builder.md) を参照してください。

## 2. パラメータ規格の詳細

### 2.1 メディアメッセージ送信プロトコル（`Image` / `Voice` / `Video` / `File`）

本節はメディア送信の**統一プロトコル標準**です：モジュールは同一のコードで4つのメディアメソッドを呼び出し、アダプターは`file`パラメータの様々な形態をプラットフォームのネイティブアップロード/送信動作に変換します。

#### 2.1.1 `file` パラメータの合法な形態

| 形態 | 例 | アダプターの要件 |
|------|------|-----------|
| HTTP(S) URL | `https://example.com/image.jpg` | **必須** |
| 本地ファイルパス | `/path/to/file.jpg`、`C:\path\to\file.jpg` | **必須** |
| 二進データ | `b"\x89PNG..."` | **必須** |
| `file://` URI | `file:///path/to/file.jpg` | **推奨**（ローカルパスに転送して処理） |
| Base64文字列 / Data URI | `iVBORw0KGgo=...`、`data:image/png;base64,...` | **推奨**（OneBot12エコシステムの慣例に準拠） |

> アダプターは、3つの必須形態（URL、パス、bytes）において、モジュールがURL、パス、bytesを渡しても、同じメッセージになるように動作しなければなりません。プラットフォームが外部URLを直接使用できない場合（URLを参照できない場合）、アダプターはダウンロード/読み取り後にアップロードする必要があります。**モジュールに再試行する形態を変更するよう要求してはなりません**。

#### 2.1.2 形態判定順序

アダプターがメディアパラメータを処理する際、**判定順序は以下の通り**に従う必要があります：

1. `bytes`型 → 直接アップロード
2. 文字列が `http://` / `https://` で始まる → URLとして処理（直接参照またはダウンロード後アップロード、プラットフォームの能力に応じて）
3. 文字列が `file://` で始まる → プレフィックスを剥がしてローカルパスとして処理
4. その他の文字列 → ローカルパスとして処理（存在する場合は読み込みアップロード；存在しない場合は標準エラー応答を返す）

```python
def _resolve_media(self, file: "str | bytes") -> bytes:
    """形態判定と正規化（例）"""
    if isinstance(file, (bytes, bytearray)):
        return bytes(file)
    if file.startswith(("http://", "https://")):
        return self._download(file)          # プラットフォームがURLを参照できない場合、ダウンロード
    if file.startswith("file://"):
        file = file[len("file://"):]
    with open(file, "rb") as f:              # 本地ファイルパス
        return f.read()
```

#### 2.1.3 `File` のファイル名の意味

`File` メソッドの署名：`File(file, filename=None)`（`filename` はオプション、基底クラスに既に実装済み）。

ファイル名**推導順序**（アダプターが明示的に `filename` を提供しない場合にこの順序で生成）：

1. 明示的な `filename` パラメータ（最優先）
2. URLのbasename（例：`https://host/a/b/report.pdf` → `report.pdf`、クエリ文字列を剥がす）
3. 本地ファイルパスのbasename（例：`/tmp/data/backup.zip` → `backup.zip`）
4. プラットフォームが生成するデフォルト名（例：`file_{timestamp}`；**拡張子は保持する**—拡張子はプラットフォーム側のタイプ識別とプレビューに影響する）

> `Image` / `Voice` / `Video` は `filename` を**受け入れる**可能性があります（メッセージセグメント `data.filename` から渡される）が、`File` のみが跨プラットフォームの意味保証を持つファイル名です。

#### 2.1.4 プラットフォーム制限の明示義務

各プラットフォームは、メディアのサイズ制限、フォーマット（MIME）、時長（音声/動画）などの制約が異なります。アダプターは**推奨**されます：

- アダプターのドキュメントにサポートするメディアの種類と制限範囲を明示する
- 超限または非対応の入力に対しては**標準エラー応答**を返す（`status: "failed"`；`retcode` は `10002` またはプラットフォーム固有のエラーコードを使用、`message` に原因を説明）、**例外を投げたりモジュールのロジックを中断させたりしない**

#### 2.1.5 機能降格の段階

プラットフォームが特定のメディア**タイプ**をサポートしない場合、以下の段階に従って降格します（「機能降格はエラーを出さない」原則に従う）：

| 情報 | 降格動作 |
|------|---------|
| `Voice` が音声メッセージをサポートしない | **推奨** `File`（またはプラットフォームに近い形態）で送信する；表現できない場合は `retcode=10002` を返す |
| `Video` が動画メッセージをサポートしない | 同上 |
| メディアタイプが完全にサポートされていない（ファイル機能がない） | `retcode=10002` を返し、不サポートのデータタイプを `message` に記述する |
| 形態がサポートされていない（Base64を処理できない） | `retcode=10002` を返し、`message` にモジュールがURL/bytesを使用するよう提示する可能性がある |

**禁止される動作**：静かに破棄（返却なし）、例外の投げ出し、モジュールにプラットフォーム分岐処理を書かせる。

### 2.2 @ユーザー パラメータ規格

**メソッド:** `At`（修飾メソッド）

**パラメータ:** `user_id` (`str`)

**要件:**
- `user_id` は文字列型のユーザー識別子であるべき
- 各プラットフォームの `user_id` 形式は異なる可能性がある（数字、UUID、文字列など）
- アダプターは `user_id` をプラットフォーム固有の形式に変換する責任がある
- 実際の送信メソッドの呼び出しは、最後の位置に置くべき

**例:**
```python
# 単一の@ユーザー
Send.To("group", "g123").At("123456").Text("你好")

# 複数の@ユーザー（チェーン呼び出し）
send.To("group", "g123").At("123456").At("789012").Text("大家好")
```

### 2.3 返信メッセージ パラメータ規格

**メソッド:** `Reply`（修飾メソッド）

**パラメータ:** `message_id` (`str`)

**要件:**
- `message_id` は文字列型のメッセージ識別子であるべき
- 以前に受信したメッセージのIDであるべき
- 一部のプラットフォームは返信機能をサポートしない可能性があるため、アダプターは優雅に降格するべき

**例:**
```python
send.To("group", "g123").Reply("msg_123456").Text("收到")
```

### 2.4 メッセージの結合転送機能（`MergeForward`、オプション）

`MergeForward(nodes)` は**オプションの機能メソッド**です：複数の内容を「結合転送 / フルテキスト折りたたみ」形式で送信し、アダプターはプラットフォームの能力に応じて最適な表示方法を決定します。`Forward(from_chat_id, message_id)`（既存のメッセージを転送する）とは異なる意味を持ち、両者は併存します。

> **標準背景**：OneBot12のコア標準にはnodeメッセージセグメントも、結合転送APIもありません。"メッセージノード"はOneBot v11エコシステム（go-cqhttp拡張）の実装層の概念であり、v12ではこれらのプラットフォーム固有能力を拡張メカニズムに委譲しました。ErisPulseの実装方法は、**標準メッセージセグメントを追加せず、オプション能力メソッド + `list_sends`の実行時検出**です—`MergeForward`を実装したアダプターは自動的に能力を得るため、実装していない場合は普通のテキストに自動的に降格し、モジュールは変更なしです。

**メソッド署名:**

```python
def MergeForward(self, nodes: List[Dict]) -> asyncio.Task:
    """
    結合転送 / フルテキスト折りたたみメッセージを送信する

    :param nodes: 合併転送ノードの配列（go-cqhttp拡張のOneBot v11ノード形式）：
        [
            {
                "type": "node",
                "data": {
                    "user_id": "10000",     # 表示用の送信者ID
                    "nickname": "MyBot",     # 表示用の送信者名
                    "content": [            # メッセージセグメントの配列、現在はtextセグメントのみ
                        {"type": "text", "data": {"text": "【1/3】タイトル\n本文…"}}
                    ],
                },
            },
        ]
    :return: asyncio.Task、await後に標準応答形式を返す
    """
```

**実装要件:**

1. **プラットフォームに原生の結合転送機能がある**（OneBot11系）：**必須**でプロトコル専用エンドポイント（`send_group_forward_msg` / `send_private_forward_msg`）を呼び出すこと。NapCatなどの実装は`send_msg`に含まれるnodeセグメントを拒否する（retcode 1400）ため、専用エンドポイントを失敗した場合は`send_msg`に回退してnodeセグメントを直接送信すること。
2. **プラットフォームに原生の転送機能はないが、富文本機能がある**（云湖 / Telegram / Kook / Discord / Matrixなど）：**推奨**でノードをプラットフォームの富文本折りたたみ形態（HTML折りたたみカード / Card / Embed / blockquoteリスト）にレンダリングすること。スタイルと各アダプターのタスクリストは `SDK/Adapter/ADAPTER_FORWARD_GUIDE.md` を参照。
3. **両方ない**：**実装しない**（node辞書を純粋なテキストとして送信してはならない）—実装しない場合、`list_sends`に`MergeForward`が含まれず、呼び出し元は自動的に普通のテキストに降格する。
4. **失敗の意味**：標準エラー応答（`status: "failed"`）を返すか、例外を投げることも可能。呼び出し元はテキスト送信に回退し、内容は失われない。
5. **`MergeForward`内で`Raw_ob12`を再利用して同じnodesを送信しない**（OneBot11の`Raw_ob12`は純nodeセグメントを自動ルーティングするため、ループになる）。
6. **出力nodeセグメントの解析**（全アダプターの合意）：各アダプターの`Raw_ob12`のセグメント配分は`node`セグメントを登録するべき—純nodeリストは自動的に本アダプターの結合転送表示にルーティングされる（`MergeForward`があるプラットフォームは直接呼び出すのと同等；`MergeForward`がないプラットフォームは各ノードのテキストを「ニックネーム: 本文」の形式で逐行**原文出力**）。混合リスト中のnodeセグメントのテキストは本文に統合される。どのアダプターがnodeセグメントを受け取っても、静かに破棄してはならない。

**プラットフォームの実装形態**（`SDK/Adapter/ADAPTER_FORWARD_GUIDE.md`を参照）：

- 原生エンドポイント：OneBot11、SnowLuma（3段階降格：`send_group/private_forward_msg`専用エンドポイント → `upload_forward_msg`からresidを取得してforwardセグメントを送信 → nodeセグメントを直接送信；SnowLuma APIはNapCatと向かって対応しており、アダプターはNapCatバックエンドに直接接続できる）
- 折りたたみHTML `<details>`カード：云湖（bot/ユーザー協定）、Email、Sandbox、Allons(Ideaura)
- ホワイトリストHTML / 引用ブロック：Telegram（`<b>`+`<blockquote>`）、Matrix（blockquoteバリエーション、ホワイトリストでdetails/インラインスタイルを剥がす）
- プラットフォームカード：Kook（Card header+section）、Discord（Embed fields）
- 官方Markdown引用リスト：QQBot（公式mdには折りたたみ構文がないため、サーバ側で無効なタグを拒否 40034011）
- 実装しない（nodeセグメントを原文出力して降格）：OneBot12（標準にnodeセグメントがない）、WeCom、Terminal、Webhook、WechatMp

**呼び出し元の検出例:**

```python
sends = adapter.list_sends(platform)
if "MergeForward" in sends:
    await adapter.Send.To("group", "123").MergeForward(nodes)
else:
    await adapter.Send.To("group", "123").Text(plain_text)
```

> 参考実装：`ErisPulse-OneBot11Adapter`（専用エンドポイント → `send_msg`回退）；レンダリングテンプレートと各アダプターのタスクリストは `SDK/Adapter/ADAPTER_FORWARD_GUIDE.md` を参照。

## 3. プラットフォーム固有メソッド命名

`Send`クラスに直接プラットフォームプレフィックスを付けるメソッドを追加することは**推奨されません**。代わりに、汎用メソッド名や`Raw_{プロトコル}`メソッドを使用することを推奨します。

**推奨されない:**
```python
def YunhuForm(self, form_id: str):  # ❌ 推奨されない
    pass

def TelegramSticker(self, sticker_id: str):  # ❌ 推奨されない
    pass
```

**推奨:**
```python
def Form(self, form_id: str):  # ✅ 汎用メソッド名
    pass

def Sticker(self, sticker_id: str):  # ✅ 汎用メソッド名
    pass

def Raw_ob12(self, message):  # ✅ OneBot12形式を送信
    pass
```

**拡張メソッドの要件:**
- メソッド名はPascalCaseを使用し、プラットフォームプレフィックスを付けない
- 必須で`asyncio.Task`オブジェクトを返す
- 完全な型注釈とドキュメント文字列を提供する
- パラメータ設計は、標準メソッドのスタイルとできるだけ一致させる

## 4. パラメータ名命名規格

| パラメータ名 | 説明 | 型 |
|-------|------|------|
| `text` | テキスト内容 | `str` |
| `file` | メディア内容（URL / パス / 2進、§2.1.1参照） | `str` / `bytes` |
| `filename` | ファイル名（`File`はオプション、§2.1.3参照） | `str` / `None` |
| `user_id` | ユーザーID | `str` / `int` |
| `group_id` | グループID | `str` / `int` |
| `message_id` | メッセージID | `str` |
| `data` | データオブジェクト（例：カードデータ） | `dict` |

## 5. 戻り値規格

- **送信メソッド**（`Text`, `Image`など）：`asyncio.Task`オブジェクトを返す必要がある
- **修飾メソッド**（`At`, `Reply`, `AtAll`）：`self`を返して、チェーン呼び出しを可能にする必要がある

---

## 6. 逆変換規格（OneBot12 → プラットフォーム）

アダプターは、プラットフォームのネイティブイベントをOneBot12形式に変換する（正変換）だけでなく、**OneBot12メッセージセグメントをプラットフォームのネイティブAPI呼び出しに変換する**（逆変換）能力も**必須**です。逆変換の統一エントリーポイントは`Raw_ob12`メソッドです。

### 6.1 変換モデル

```
正変換（受信方向）                逆変換（送信方向）
─────────────────                ─────────────────
プラットフォームのネイティブイベント                       OneBot12メッセージセグメントリスト
    │                                  │
    ▼                                  ▼
Converter.convert()               Send.Raw_ob12()
    │                                  │
    ▼                                  ▼
OneBot12標準イベント（{platform}_rawを含む）             プラットフォームのネイティブAPI呼び出し
（標準応答形式を返す）
```

**コアの対称性**：正変換は`{platform}_raw`に元のデータを保持し、逆変換はOneBot12標準形式を受け取り、プラットフォームの呼び出しに還元する。

### 6.2 `Raw_ob12`の実装規格

`Raw_ob12`はOneBot12標準メッセージセグメントリストを受け取り、それをプラットフォームのネイティブAPI呼び出しに変換する必要があります。

**メソッド署名:**

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

**実装要件:**

1. **すべての標準メッセージセグメントタイプを処理する必要がある**：少なくとも`text`、`image`、`audio`、`video`、`file`、`mention`、`reply`をサポートする
2. **プラットフォーム拡張メッセージセグメントを処理する必要がある**：`{platform}_xxx`形式のメッセージセグメントは、プラットフォームに対応するネイティブ呼び出しに変換する
3. **標準応答形式を返す必要がある**：[API応答標準](api-response.md)に従う
4. **サポートしないメッセージセグメントは警告を記録してスキップする**、例外を投げてメッセージ全体の送信失敗を引き起こしてはならない

### 6.3 メッセージセグメント変換ルール

#### 6.3.1 標準メッセージセグメント変換

アダプターは以下の標準メッセージセグメントの変換を実装する必要があります：

| OneBot12メッセージセグメント | 変換要件 |
|----------------|---------|
| `text` | `data.text`をそのまま使用 |
| `image` | `data.file`を§2.1媒体プロトコルに従って処理（3つの必須形態 + 判定順序） |
| `audio` | `image`と同様の処理ロジック |
| `video` | `image`と同様の処理ロジック |
| `file` | `image`と同様の処理ロジック；ファイル名は§2.1.3の推導順序に従って`data.filename`を処理 |
| `mention` | プラットフォームの@ユーザー機能に変換（例：Telegramの`entities`、云湖の`at_uid`） |
| `reply` | プラットフォームの返信引用機能に変換 |
| `face` | プラットフォームの表情送信機能に変換、不サポートの場合はスキップ |
| `location` | プラットフォームの位置送信機能に変換、不サポートの場合はスキップ |

#### 6.3.2 プラットフォーム拡張メッセージセグメント変換

プラットフォームプレフィックス付きのメッセージセグメントは、アダプターが認識して変換する必要があります：

```python
def _convert_ob12_segments(self, segments: List[Dict]) -> Any:
    """OneBot12メッセージセグメントをプラットフォームのネイティブ形式に変換する"""
    platform_prefix = f"{self._platform_name}_"
    
    for segment in segments:
        seg_type = segment["type"]
        seg_data = segment["data"]
        
        if seg_type.startswith(platform_prefix):
            # プラットフォーム拡張メッセージセグメント → プラットフォームのネイティブ呼び出し
            self._handle_platform_segment(seg_type, seg_data)
        elif seg_type in self._standard_segment_handlers:
            # 標準メッセージセグメント → プラットフォームの等価操作
            self._standard_segment_handlers[seg_type](seg_data)
        else:
            # 未知のメッセージセグメント → 警告を記録してスキップ
            logger.warning(f"サポートしないメッセージセグメントタイプ: {seg_type}")
```

#### 6.3.3 複合メッセージセグメント処理

1つのメッセージには複数のメッセージセグメントが含まれる可能性があり、アダプターは正しく処理する必要があります：

```python
# モジュールがテキスト+画像+@ユーザーのメッセージを送信
await send.Raw_ob12([
    {"type": "mention", "data": {"user_id": "123"}},
    {"type": "text", "data": {"text": "你好"}},
    {"type": "image", "data": {"file": "https://example.com/img.jpg"}}
])
```

**処理戦略**：
- **優先的に結合**：プラットフォームが1つのメッセージにテキスト、画像、@などを同時に含められる場合、結合して送信する
- **退而的に分割**：プラットフォームが結合をサポートしない場合、順番に複数のメッセージに分割して送信する
- **順序を保持**：メッセージセグメントの送信順序はリストの順序と一致する

### 6.4 `Raw_ob12` と標準メソッドの関係

アダプターの標準送信メソッド（`Text`、`Image`など）は**`SendDSL`基底クラスに既に実装され、デフォルトで`Raw_ob12`に委譲されている**ため、アダプターのサブクラスでは再実装する必要はありません：

```python
class Send(SendDSL):
    def Raw_ob12(self, message_segments: List[Dict]) -> asyncio.Task:
        """コア実装：OneBot12メッセージセグメント → プラットフォームAPI（必須実装）"""
        return asyncio.create_task(self._send_ob12(message_segments))

    # Text/Image/Voice/Video/Fileは基底クラスから継承され、自動的にRaw_ob12に委譲される
    # プラットフォーム固有のロジックが必要な場合は、単一メソッドをオーバーライドする：
    # def Text(self, text: str) -> asyncio.Task:
    #     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

**利点**：
- 変換ロジックは`Raw_ob12`に1か所に集中し、重複コードを減らす
- 標準メソッドと`Raw_ob12`の動作は完全に一致する
- モジュールは`Text()`でも`Raw_ob12()`でも同じ結果を得られる
- 基底クラスが型署名を提供し、IDEが標準メソッドを補完できる

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
                logger.warning(f"云湖がサポートしないメッセージセグメント: {seg_type}")
        
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

モジュール開発者は、アダプターがサポートする送信メソッドをAPIで照会することができます（**モジュール内でプラットフォームのメソッドリストをハードコーディングしないでください**—各アダプターの拡張メソッドはバージョンの進化に伴い変化するため、実行時の発見が基準です）：

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
#     "docstring": "云湖表单を送信"
# }
```

---

## 9. アダプター開発の注意点

`BaseAdapter`、`Send`、`Request` の `__init__` を正しくオーバーライドする方法については、[アダプター開発入門 - `__init__` 注意事項](../developer-guide/adapters/getting-started.md#init-注意事项)を参照してください。

---

---

## 10. アダプター実装チェックリスト

### 送信メソッド
- [ ] 標準メソッド（`Text`, `Image` 等）は実装済み
- [ ] 戻り値はすべて `asyncio.Task`
- [ ] 修飾メソッド（`At`, `Reply`, `AtAll`）は `self` を返す
- [ ] プラットフォーム拡張メソッドはPascalCase、プラットフォームプレフィックスなし
- [ ] すべてのメソッドに完全な型注釈とドキュメント文字列がある

### メディア送信プロトコル
- [ ] `file` パラメータの**必須形態**はすべてサポート：HTTP(S) URL / 本地パス / `bytes`（§2.1.1参照）
- [ ] 形態判定順序は§2.1.2に従う（bytes → URL → `file://` → パス）
- [ ] `File` のファイル名の推導順序は§2.1.3に従う（明示的`filename` > URL basename > パス basename > プラットフォームデフォルト）
- [ ] プラットフォームのメディア制限（サイズ / MIME / 時長）はアダプターのドキュメントに明示されている
- [ ] 不サポートのメディアタイプは§2.1.5の降格段階に従って処理：近縁タイプに降格するか、`retcode=10002`を返す、例外を投げたり静かに破棄したりしない

### 合併転送（オプション、§2.4参照）
- [ ] プラットフォームに原生の合併転送がある場合、`MergeForward`はプロトコル専用エンドポイントを経由し、失敗した場合は`send_msg`に回退する（OneBot11系）
- [ ] プラットフォームに原生の転送機能はないが、富文本機能がある場合、`MergeForward`はプラットフォームの折りたたみ形態（HTMLカード / Card / Embed / blockquote）にレンダリングする
- [ ] 両方ない場合、`MergeForward`を実装しない、node辞書を純テキストとして成功したように返すことはしない
- [ ] `MergeForward`内部で`Raw_ob12`を再利用して同じnodesを送信しない

### 逆変換
- [ ] `Raw_ob12` **は実装済み**（必須、スキップ不可）
- [ ] `Raw_ob12`はすべての標準メッセージセグメント（`text`, `image`, `audio`, `video`, `file`, `mention`, `reply`）を処理できる
- [ ] `Raw_ob12`はプラットフォーム拡張メッセージセグメント（`{platform}_xxx`形式）を処理できる
- [ ] 標準送信メソッド（`Text`, `Image` 等）は内部で`Raw_ob12`に委譲しており、個別の変換ロジックを実装していない
- [ ] 不サポートのメッセージセグメントは警告を記録してスキップし、例外を投げない
- [ ] 複合メッセージセグメントは正しく処理される（結合または順序に従って分割）

---

## 11. メッセージビルダー（MessageBuilder）—アダプター側の注意点

`MessageBuilder`はErisPulseが提供するOneBot12メッセージセグメントのビルダーで、**モジュール側**がメッセージを構築するために使用されます。チェーン呼び出し（または静的高速構築）により、最終的にOneBot12メッセージセグメントリスト`[{"type": ..., "data": ...}]`を生成し、`Raw_ob12`に直接渡されます。

**アダプター側は、以下を知るだけでよい**：`Raw_ob12`が受け取るのはこの生成物であり、`MessageBuilder`かリテラルかに関わらず、`段分発`ロジックに従って処理される。`段分発`ロジックに従って処理される。

> 完全な使い方（二つのモード、すべてのメッセージセグメントメソッド、`copy()` / `clear()`ツールメソッドと例）は [MessageBuilder 详解](../advanced/message-builder.md) を参照し、本文書では繰り返さない。

---

## 12. 関連ドキュメント

**送信の戻り値を実装する際の対応**：
- [API応答標準](api-response.md) - アダプターAPIの応答形式の標準

**同一アダプターの他の側面**：
- [イベント変換標準](event-conversion.md) - 完全なイベント変換の規格、拡張命名とメッセージセグメントの標準
- [セッション型の標準](session-types.md) - セッション型の定義とマッピング
- [リクエスト操作の規格](request-action-spec.md) - リクエストイベントのフィールド要件、HandleRequest DSLとアダプターの実装要件