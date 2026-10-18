# ErisPulse 送信メソッド規格

本文書は、ErisPulseアダプタのSendクラスにおける送信メソッドの命名規則、パラメータ規則、および逆変換要件を定義します。

## 0. キーワードの約束

本文書内の **必須（MUST）**、**推奨（SHOULD）**、**可能（MAY）** は、RFC 2119に従い以下の意味で解釈されます：

| キーワード | 意味 | 違反時の影響 |
|--------|------|---------|
| **必須** | 強制要件。フレームワークの動作/クロスプラットフォームの一貫性はこれに依存 | アダプタは規格に準拠していないと見なされ、モジュールコードが動作しない可能性がある |
| **推奨** | 強く推奨。十分な理由がない限り、遵守すべき | 違反する場合は、アダプタのドキュメントに理由と代替動作を明記する必要がある |
| **可能** | オプション。プラットフォームの能力に応じて決定 | 無 |

## 1. 標準メソッド命名

送信メソッドは **大キャメルケース（PascalCase）** を使用し、先頭文字は大文字とする。

### 1.1 標準送信メソッド

| メソッド名 | 説明 | パラメータ型 | 実装要件 |
|-------|------|---------|---------|
| `Text` | テキストメッセージを送信 | `str` | 必須 |
| `Image` | 画像を送信 | `str` \| `bytes` | 必須（基底クラスに既に実装済み、§6.4参照） |
| `Voice` | 音声を送信 | `str` \| `bytes` | 必須（基底クラスに既に実装済み；プラットフォームが音声をサポートしない場合は§2.1.5に従い降格） |
| `Video` | 動画を送信 | `str` \| `bytes` | 必須（基底クラスに既に実装済み；プラットフォームが動画をサポートしない場合は§2.1.5に従い降格） |
| `File` | ファイルを送信 | `str` \| `bytes`、`filename: str \| None = None` | 必須（基底クラスに既に実装済み） |
| `At` | ユーザー/グループを@する | `str` (user_id) | 修飾メソッド、必要に応じて |
| `Face` | 表情を送信 | `str` (emoji) | 可能 |
| `Reply` | メッセージに返信 | `str` (message_id) | 修飾メソッド、必要に応じて |
| `Forward` | メッセージを転送 | `str` (message_id) | 可能 |
| `Markdown` | Markdownメッセージを送信 | `str` | 可能 |
| `HTML` | HTMLメッセージを送信 | `str` | 可能 |
| `Card` | カードメッセージを送信 | `dict` | 可能 |

> 標準メソッド（`Text`/`Image`/`Voice`/`Video`/`File`）は基底クラス `SendDSL` に内蔵され、デフォルトで `Raw_ob12` に委譲されるため、アダプタは再実装する必要がない。プラットフォームに特殊なロジックが必要な場合のみ、個々のメソッドをオーバーライドする（§6.4参照）。

### 1.2 チェーン修飾メソッド

| メソッド名 | 説明 | パラメータ型 |
|-------|------|---------|
| `At` | ユーザーを@する（複数回呼び出し可） | `str` (user_id) |
| `AtAll` | 全員を@する | 無 |
| `Reply` | メッセージに返信 | `str` (message_id) |

### 1.3 プロトコルメソッド

| メソッド名 | 説明 | 必須か |
|-------|------|---------|
| `Raw_ob12` | OneBot12形式のメッセージセグメントを送信 | 必須 |

**`Raw_ob12` は必須実装メソッド**。これはアダプタの主要な責任の一つであり、OneBot12標準メッセージセグメントを受信して、プラットフォーム固有のAPI呼び出しに変換する。`Raw_ob12` は逆変換（OneBot12 → プラットフォーム）の統一エントリーポイントであり、モジュールがプラットフォーム固有のメソッドに依存せず、標準メッセージセグメントを使用してメッセージを送信できるようにする。

**`Raw_ob12` をオーバーライドしない場合の動作**：基底クラスのデフォルト実装は **errorレベル** のログを記録し、エラー応答形式（`status: "failed"`, `retcode: 10002`）を返し、アダプタ開発者がこのメソッドを実装する必要があることを示す。

### 1.4 推奨される拡張命名規約

アダプタがOneBot12形式以外のデータ（プラットフォーム固有のJSON、XMLなど）を送信する必要がある場合、以下の命名規約を推奨する：

| 推奨メソッド名 | 説明 |
|-----------|------|
| `Raw_json` | 任意のJSONデータを送信 |
| `Raw_xml` | 任意のXMLデータを送信 |

**注意**：これらのメソッドは**基底クラスに提供されているものではなく、強制的に実装する必要もない**。これらは単なる命名規約であり、アダプタは必要に応じて独自に定義する。これらの形式をサポートしない場合は、定義する必要はない。

**メッセージビルダー（MessageBuilder）**：ErisPulseは`MessageBuilder`ツールクラスを提供し、OneBot12メッセージセグメントリストを簡単に構築できる。`Raw_ob12`と併用する。[メッセージビルダー](#11-メッセージビルダー-messagebuilder)章節を参照。

## 2. パラメータ規則の詳細

### 2.1 メディア送信プロトコル（`Image` / `Voice` / `Video` / `File`）

本節はメディア送信の**統一プロトコル標準**である。モジュールは同一のコードで4つのメディアメソッドを呼び出し、アダプタは`file`パラメータの様々な形態をプラットフォーム固有のアップロード/送信動作に変換する。

#### 2.1.1 `file`パラメータの合法な形態

| 形態 | 例 | アダプタの要件 |
|------|------|-----------|
| HTTP(S) URL | `https://example.com/image.jpg` | **必須**受諾 |
| 本地ファイルパス | `/path/to/file.jpg`、`C:\path\to\file.jpg` | **必須**受諾 |
| 二進データ | `b"\x89PNG..."` | **必須**受諾 |
| `file://` URI | `file:///path/to/file.jpg` | **推奨**受諾（ローカルパスに変換して処理） |
| Base64文字列 / Data URI | `iVBORw0KGgo=...`、`data:image/png;base64,...` | **推奨**受諾（OneBot12エコシステムの慣例に準拠） |

> アダプタは**3つの必須形態**で動作を一貫させる必要がある。モジュールがURL、パス、またはbytesを送信しても、受信されるのは同一のメッセージである。プラットフォームが外部URLを直接使用できない場合（URLを参照できないAPI）、アダプタがダウンロード/読み取り後にアップロードする。**モジュールに再試行を要求して形態を変更させるべきではない**。

#### 2.1.2 形態判定順序

アダプタがメディアパラメータを処理する際、**判定順序は以下の通り**とする。

1. `bytes`型 → 直接アップロード
2. 文字列が`http://` / `https://`で始まる → URLとして処理（直接参照またはダウンロード後アップロード、プラットフォームの能力に応じて）
3. 文字列が`file://`で始まる → プレフィックスを剥離してローカルパスとして処理
4. それ以外の文字列 → ローカルパスとして処理（存在する場合は読み取りアップロード；存在しない場合は標準エラー応答を返す）

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

#### 2.1.3 `File`のファイル名の意味

`File`メソッドのシグネチャ：`File(file, filename=None)`（`filename`はオプション、基底クラスに既に実装済み）。

ファイル名**推導順序**（アダプタが`filename`を明示的に提供しない場合に使用）：

1. 明示的な`filename`パラメータ（最優先）
2. URLのbasename（例：`https://host/a/b/report.pdf` → `report.pdf`、クエリ文字列を剥離）
3. 本地パスのbasename（例：`/tmp/data/backup.zip` → `backup.zip`）
4. プラットフォームがデフォルトで生成（例：`file_{timestamp}`；**拡張子は保持すべき**。拡張子はプラットフォーム側のタイプ識別とプレビュー動作に影響する）

> `Image` / `Voice` / `Video`も**`filename`を受け取れる**（メッセージセグメント`data.filename`を通じて渡される）、ただし`File`のファイル名のみがクロスプラットフォームで意味が保証される。

#### 2.1.4 プラットフォーム制限の宣言義務

各プラットフォームはメディアのサイズ制限、形式（MIME）、音声/動画の長さなどの制約が異なる。アダプタは**宣言すべき**：

- アダプタドキュメントにサポートするメディア形式と制限範囲を記載
- 制限を超えるまたはサポートされない入力に対しては**標準エラー応答**を返す（`status: "failed"`；`retcode`は`10002`またはプラットフォームの意味化されたエラーコードを使用、`message`に原因を説明）、**例外を投げてモジュールの処理を中断してはならない**

#### 2.1.5 機能降格の段階

プラットフォームがメディアの**特定のタイプ**をサポートしない場合、以下の段階で降格する（総則「機能降格はエラーを出さない」に従う）：

| 情報 | 降格動作 |
|------|---------|
| `Voice`が音声メッセージをサポートしない | **推奨**`File`（またはプラットフォームの類似形態）として送信；表現できない場合は`retcode=10002`を返す |
| `Video`が動画メッセージをサポートしない | 同上 |
| メディアタイプが完全にサポートされていない（ファイル機能がない） | `retcode=10002`を返し、`message`にサポートされていないデータタイプを明記 |
| 形態がサポートされていない（Base64を処理できないなど） | `retcode=10002`を返し、`message`にモジュールにURL/bytesを使用するよう提示できる |

**禁止される動作**：静かに破棄（返却がない）、例外を投げる、モジュールにプラットフォーム分岐処理を書かせる。

### 2.2 @ユーザーのパラメータ規則

**メソッド**：`At`（修飾メソッド）

**パラメータ**：`user_id` (`str`)

**要件**：
- `user_id`は文字列型のユーザー識別子であるべき
- 各プラットフォームの`user_id`の形式は異なる可能性がある（数字、UUID、文字列など）
- アダプタは`user_id`をプラットフォーム固有の形式に変換する責任がある
- 実際の送信メソッドの呼び出しは最後に位置させる

**例**：
```python
# 単一の@ユーザー
Send.To("group", "g123").At("123456").Text("你好")

# 複数の@ユーザー（チェーン呼び出し）
send.To("group", "g123").At("123456").At("789012").Text("大家好")
```

### 2.3 返信メッセージのパラメータ規則

**メソッド**：`Reply`（修飾メソッド）

**パラメータ**：`message_id` (`str`)

**要件**：
- `message_id`は文字列型のメッセージ識別子であるべき
- 以前に受信したメッセージのIDであるべき
- プラットフォームによっては返信機能がサポートされていない可能性があり、アダプタは優雅に降格する

**例**：
```python
send.To("group", "g123").Reply("msg_123456").Text("收到")
```

### 2.4 合併転送機能（`MergeForward`、オプション）

`MergeForward(nodes)`は**オプションの機能メソッド**：複数の内容を「合併転送 / ファイバーテキスト折りたたみ」形式で送信する。アダプタはプラットフォームの能力に応じて最適な表示方法を決定する。§1.1の`Forward(from_chat_id, message_id)`（既存メッセージの転送）とは意味が異なり、両者は共存する。

> **標準の背景**：OneBot12のコア標準にはnodeメッセージセグメントも、合併転送APIも含まれていない。"メッセージノード"はOneBot v11エコシステム（go-cqhttp拡張）の実装層の概念であり、v12ではこのようなプラットフォーム固有の機能を拡張メカニズムに委譲した。ErisPulseの実装方法は拡張メカニズムと同等物：**標準メッセージセグメントを追加せず、オプション機能メソッド + `list_sends`ランタイム検出**——`MergeForward`を実装したアダプタは自動的に機能を得る。未実装の場合は呼び出し元は普通のテキストに自動的に降格し、モジュールは変更を必要としない。

**メソッドシグネチャ**：

```python
def MergeForward(self, nodes: List[Dict]) -> asyncio.Task:
    """
    合併転送 / ファイバーテキスト折りたたみメッセージを送信

    :param nodes: 合併転送ノード配列（go-cqhttp拡張のOneBot v11ノード形式）：
        [
            {
                "type": "node",
                "data": {
                    "user_id": "10000",     # 表示用送信者ID
                    "nickname": "QvQChat",  # 表示用送信者ニックネーム
                    "content": [            # メッセージセグメント配列、現在はtextセグメント
                        {"type": "text", "data": {"text": "【1/3】タイトル\n本文…"}}
                    ],
                },
            },
        ]
    :return: asyncio.Task、await後に標準応答形式を返す
    """
```

**実装要件**：

1. **プラットフォームに元生の合併転送がある**（OneBot11系）：**必須**プロトコル専用エンドポイントを呼び出す
   （`send_group_forward_msg` / `send_private_forward_msg`）——NapCat等の実装は
   `send_msg`に含まれるnodeセグメントを拒否する（retcode 1400）；専用エンドポイントが失敗した場合は**`send_msg`に回退**できる
2. **プラットフォームに元生の転送はなく、富文本がある**（云湖 / Telegram / Kook / Discord / Matrix等）：
   **推奨**ノードをプラットフォームの富文本折りたたみ形態（HTML折りたたみカード / Card / Embed / blockquoteリスト）にレンダリングする。
   スタイルと各アダプタのタスクリストは`SDK/Adapter/ADAPTER_FORWARD_GUIDE.md`を参照
3. **両者ともない**：**実装してはならない**（retcode 1400を返すだけでは不十分）——未実装の場合は`list_sends`に`MergeForward`が含まれず、呼び出し元は自動的に普通のテキストに降格
4. **失敗の意味**：標準エラー応答（`status: "failed"`）を返すか、例外を投げてもよい、呼び出し元は普通のテキスト送信に回復し、内容は失われない
5. **`MergeForward`内部で`Raw_ob12`を再呼び出して同じnodesを送信してはならない**（OneBot11の`Raw_ob12`は既に純nodeセグメントの自動ルーティングを内蔵しており、ループになる）

**呼び出し元の検出例**：

```python
sends = adapter.list_sends(platform)
if "MergeForward" in sends:
    await adapter.Send.To("group", "123").MergedForward(nodes)
else:
    await adapter.Send.To("group", "123").Text(plain_text)
```

> 参考実装：`ErisPulse-OneBot11Adapter`（専用エンドポイント → `send_msg`回退）；レンダリングテンプレートと各アダプタのタスクリストは
> `SDK/Adapter/ADAPTER_FORWARD_GUIDE.md`を参照。

## 3. プラットフォーム固有メソッドの命名

`Send`クラスに直接プラットフォームプレフィックス付きメソッドを追加することは**推奨されない**。一般的なメソッド名または`Raw_{プロトコル}`メソッドを使用することを推奨する。

**推奨されない**：
```python
def YunhuForm(self, form_id: str):  # ❌ 推奨されない
    pass

def TelegramSticker(self, sticker_id: str):  # ❌ 推奨されない
    pass
```

**推奨**：
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
- パラメータ設計は標準メソッドスタイルにできるだけ合わせる

## 4. パラメータ名の命名規則

| パラメータ名 | 説明 | 型 |
|-------|------|------|
| `text` | テキスト内容 | `str` |
| `file` | メディア内容（URL / パス / 二進、§2.1.1参照） | `str` / `bytes` |
| `filename` | ファイル名（`File`はオプション、§2.1.3参照） | `str` / `None` |
| `user_id` | ユーザーID | `str` / `int` |
| `group_id` | グループID | `str` / `int` |
| `message_id` | メッセージID | `str` |
| `data` | データオブジェクト（例：カードデータ） | `dict` |

## 5. 戻り値の規則

- **送信メソッド**（例：`Text`, `Image`）：`asyncio.Task`オブジェクトを返す必要がある
- **修飾メソッド**（例：`At`, `Reply`, `AtAll`）：`self`を返して、チェーン呼び出しを可能にする必要がある

---

## 6. 逆変換規則（OneBot12 → プラットフォーム）

アダプタは、プラットフォーム固有イベントをOneBot12形式に変換する（正変換）だけでなく、**OneBot12メッセージセグメントをプラットフォーム固有API呼び出しに変換する**（逆変換）能力も**必須**である。逆変換の統一エントリーポイントは`Raw_ob12`メソッドである。

### 6.1 変換モデル

```
正変換（受信方向）                逆変換（送信方向）
─────────────────                ─────────────────
プラットフォーム固有イベント                       OneBot12メッセージセグメントリスト
    │                                  │
    ▼                                  ▼
Converter.convert()               Send.Raw_ob12()
    │                                  │
    ▼                                  ▼
OneBot12標準イベント                  プラットフォーム固有API呼び出し
（含{platform}_raw）             （標準応答形式を返す）
```

**コアの対称性**：正変換は `{platform}_raw` に元のデータを保持し、逆変換はOneBot12標準形式を受け取り、プラットフォーム呼び出しに還元する。

### 6.2 `Raw_ob12`実装規則

`Raw_ob12`はOneBot12標準メッセージセグメントリストを受け取り、それをプラットフォーム固有API呼び出しに変換する必要がある。

**メソッドシグネチャ**：

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

1. **すべての標準メッセージセグメントタイプを処理する必要がある**：少なくとも`text`、`image`、`audio`、`video`、`file`、`mention`、`reply`をサポート
2. **プラットフォーム拡張メッセージセグメントを処理する必要がある**：`{platform}_xxx`タイプのメッセージセグメントは、プラットフォームに対応する原生呼び出しに変換する
3. **標準応答形式を返す必要がある**：[API応答規格](api-response.md)に従う
4. **サポートしないメッセージセグメントは警告を記録してスキップする**、例外を投げてメッセージ全体の送信失敗を引き起こしてはならない

### 6.3 メッセージセグメント変換ルール

#### 6.3.1 標準メッセージセグメント変換

アダプタは以下の標準メッセージセグメントの変換を実装する必要がある：

| OneBot12メッセージセグメント | 変換要件 |
|----------------|---------|
| `text` | `data.text`をそのまま使用 |
| `image` | `data.file`を§2.1メディアプロトコルに従って処理（3つの必須形態 + 判定順序） |
| `audio` | `image`と同様の処理ロジック |
| `video` | `image`と同様の処理ロジック |
| `file` | `image`と同様の処理ロジック；ファイル名は§2.1.3の推導順序に従って`data.filename`を処理 |
| `mention` | プラットフォームの@ユーザーメカニズムに変換（例：Telegramの`entities`、云湖の`at_uid`） |
| `reply` | プラットフォームの返信引用メカニズムに変換 |
| `face` | プラットフォームの表情送信メカニズムに変換、不支持の場合はスキップ |
| `location` | プラットフォームの位置送信メカニズムに変換、不支持の場合はスキップ |

#### 6.3.2 プラットフォーム拡張メッセージセグメント変換

プラットフォームプレフィックス付きメッセージセグメントについては、アダプタは認識して変換する：

```python
def _convert_ob12_segments(self, segments: List[Dict]) -> Any:
    """OneBot12メッセージセグメントをプラットフォーム原生形式に変換"""
    platform_prefix = f"{self._platform_name}_"
    
    for segment in segments:
        seg_type = segment["type"]
        seg_data = segment["data"]
        
        if seg_type.startswith(platform_prefix):
            # プラットフォーム拡張メッセージセグメント → プラットフォーム原生呼び出し
            self._handle_platform_segment(seg_type, seg_data)
        elif seg_type in self._standard_segment_handlers:
            # 標準メッセージセグメント → プラットフォーム同等操作
            self._standard_segment_handlers[seg_type](seg_data)
        else:
            # 未知のメッセージセグメント → 警告を記録してスキップ
            logger.warning(f"サポートされていないメッセージセグメントタイプ: {seg_type}")
```

#### 6.3.3 複合メッセージセグメント処理

1つのメッセージは複数のメッセージセグメントを含む可能性があり、アダプタは複合メッセージを正しく処理する必要がある：

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
- **次善として分割**：プラットフォームが結合をサポートしない場合、順序に従って複数のメッセージに分割して送信する
- **順序の保持**：メッセージセグメントの送信順序はリストの順序と一致する

### 6.4 `Raw_ob12` と標準メソッドの関係

アダプタの標準送信メソッド（`Text`、`Image`など）は**`SendDSL`基底クラスに内蔵され、デフォルトで`Raw_ob12`に委譲される**ため、アダプタのサブクラスは再実装する必要はない：

```python
class Send(SendDSL):
    def Raw_ob12(self, message_segments: List[Dict]) -> asyncio.Task:
        """コア実装：OneBot12メッセージセグメント → プラットフォームAPI（必須実装）"""
        return asyncio.create_task(self._send_ob12(message_segments))

    # Text/Image/Voice/Video/Fileは基底クラスから継承され、Raw_ob12に自動的に委譲される
    # プラットフォーム特有のロジックが必要な場合、個々のメソッドをオーバーライドする：
    # def Text(self, text: str) -> asyncio.Task:
    #     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

**メリット**：
- 変換ロジックは`Raw_ob12`に集中し、重複コードを減らす
- 標準メソッドと`Raw_ob12`の動作は完全に一致する
- モジュールは`Text()`でも`Raw_ob12()`でも同じ結果を得られる
- 基底クラスが型のシグネチャを提供し、IDEが標準メソッドの補完を提供する

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
                logger.warning(f"云湖がサポートしていないメッセージセグメント: {seg_type}")
        
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

モジュール開発者は、アダプタがサポートする送信メソッドをAPIで取得できる（**モジュールにハードコードしないでください**——各アダプタの拡張メソッドはバージョンの進化に伴い変化するため、ランタイムで検出する必要があります）：

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

`BaseAdapter`、`Send`、`Request`の`__init__`を正しくオーバーライドする方法については、[アダプタ開発入門 - `__init__`の注意事項](../developer-guide/adapters/getting-started.md#init-の注意事項)を参照してください。

---

---

## 10. アダプタ実装チェックリスト

### 送信メソッド
- [ ] 標準メソッド（`Text`, `Image`など）が実装されている
- [ ] 戻り値はすべて`asyncio.Task`
- [ ] 修飾メソッド（`At`, `Reply`, `AtAll`）は`self`を返す
- [ ] プラットフォーム拡張メソッドはPascalCaseを使用し、プラットフォームプレフィックスを付けない
- [ ] すべてのメソッドには完全な型注釈とドキュメント文字列がある

### メディア送信プロトコル
- [ ] `file`パラメータの**必須形態**すべてをサポートしている：HTTP(S) URL / 本地パス / `bytes`（§2.1.1参照）
- [ ] 形態判定順序は§2.1.2に従っている（bytes → URL → `file://` → パス）
- [ ] `File`のファイル名の推導順序は§2.1.3に従っている（明示的な`filename` > URLのbasename > パスのbasename > プラットフォームのデフォルト）
- [ ] プラットフォームのメディア制限（サイズ / MIME / 時長）はアダプタドキュメントに記載されている（§2.1.4）
- [ ] メディアタイプがサポートされていない場合は、§2.1.5の降格段階に従って処理している：近縁なタイプに降格するか、`retcode=10002`を返す。例外を投げたり、静かに破棄したりしない

### 合併転送（オプション、§2.4参照）
- [ ] プラットフォームに原生の合併転送がある場合、`MergeForward`はプロトコル専用エンドポイントを呼び出し、失敗した場合は`send_msg`に回退する（OneBot11系）
- [ ] プラットフォームに原生の転送がないが、富文本がある場合、`MergeForward`はプラットフォームの折りたたみ形態（HTMLカード / Card / Embed / blockquoteリスト）にレンダリングする。スタイルとアダプタごとのタスクリストは`SDK/Adapter/ADAPTER_FORWARD_GUIDE.md`を参照
- [ ] 両方ない場合は`MergeForward`を実装しない。`retcode=10002`を返すだけでは不十分。実装していない場合、`list_sends`に`MergeForward`が含まれず、呼び出し元は普通のテキストに自動的に降格する
- [ ] `MergeForward`内部で`Raw_ob12`を呼び出して同じnodesを送信しない（OneBot11の`Raw_ob12`は既に純nodeセグメントの自動ルーティングを内蔵しており、ループになる）

---

## 11. メッセージビルダー（MessageBuilder）

`MessageBuilder`はErisPulseが提供するメッセージセグメント構築ツールで、`Raw_ob12`と併用してOneBot12メッセージセグメントの構築を簡素化する。

### 11.1 インポート

```python
from ErisPulse.Core import MessageBuilder
# または
from ErisPulse.Core.Event import MessageBuilder
```

### 11.2 チェーン呼び出しによる構築

```python
# テキスト、画像、@ユーザーを含むメッセージを構築
segments = (
    MessageBuilder()
    .mention("123456")
    .text("你好，看看这张图")
    .image("https://example.com/img.jpg")
    .reply("msg_789")
    .build()
)

# 送信
await adapter.Send.To("group", "456").Raw_ob12(segments)
```

### 11.3 単一セグメントの高速構築

```python
# 単一メッセージセグメントを構築（list[dict]を返し、Raw_ob12に直接渡せる）
await adapter.Send.To("user", "123").Raw_ob12(MessageBuilder.text("Hello"))
await adapter.Send.To("group", "456").Raw_ob12(MessageBuilder.image("https://..."))
await adapter.Send.To("group", "456").Raw_ob12(MessageBuilder.mention("123"))
await adapter.Send.To("group", "456").Raw_ob12(MessageBuilder.reply("msg_id"))
await adapter.Send.To("group", "456").Raw_ob12(MessageBuilder.at_all())
```

### 11.4 Event.reply_ob12と併用

```python
from ErisPulse.Core import MessageBuilder

@message()
async def handle(event: Event):
    await event.reply_ob12(
        MessageBuilder()
        .mention(event.get_user_id())
        .text("收到你的消息")
        .build()
    )
```

### 11.5 支援されるメッセージセグメントメソッド

| メソッド | 説明 | dataフィールド |
|------|------|----------|
| `text(text)` | テキスト | `text` |
| `image(file)` | 画像 | `file` |
| `audio(file)` | 音声 | `file` |
| `video(file)` | 動画 | `file` |
| `file(file, filename=None)` | ファイル | `file`, `filename`(オプション) |
| `mention(user_id, user_name=None)` | @ユーザー | `user_id`, `user_name`(オプション) |
| `at(user_id, user_name=None)` | @ユーザー（`mention`の別名） | 同`mention` |
| `reply(message_id)` | 返信 | `message_id` |
| `at_all()` | @全員 | `{}` |
| `custom(type, data)` | 自定義/プラットフォーム拡張 | 自定義 |

### 11.6 ユーティリティメソッド

```python
builder = MessageBuilder().text("基礎内容")

# コピー（深コピー）
msg1 = builder.copy().image("img1").build()
msg2 = builder.copy().image("img2").build()

# クリア
builder.clear().text("新内容").build()

# 空かどうか判定
if builder:
    print(f"メッセージセグメント数: {len(builder)}")
```

---

## 12. 関連文書

- [イベント変換規格](event-conversion.md) - 完全なイベント変換規格、拡張命名とメッセージセグメント標準
- [API応答規格](api-response.md) - アダプタAPI応答形式の標準
- [セッションタイプ規格](session-types.md) - セッションタイプの定義とマッピング
- [リクエスト操作規格](request-action-spec.md) - リクエストイベントのフィールド要件、HandleRequest DSL、およびアダプタ実装要件