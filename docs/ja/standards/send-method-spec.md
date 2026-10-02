# ErisPulse 送信メソッド規格

このドキュメントでは、ErisPulseアダプタのSendクラスにおける送信メソッドの命名規則、引数規則、および逆変換要件を定義します。

## 0. キーワードの定義

本文書における**必須（MUST）**、**推奨（SHOULD）**、**可選（MAY）**は、RFC 2119に従い以下の意味で解釈されます：

| キーワード | 意味 | 違反時の影響 |
|--------|------|---------|
| **必須** | 強制的な要件、フレームワークの動作やプラットフォーム間の一貫性に依存 | アダプタは規格に準拠していないと見なされ、モジュールコードが動作しない可能性がある |
| **推奨** | 強く推奨するが、正当な理由がない限り遵守すべき | 違反する場合は、アダプタのドキュメントに理由と代替動作を明記する必要がある |
| **可選** | オプションで、プラットフォームの能力に応じて自由に決定できる | 無し |

## 1. 標準メソッド命名

すべての送信メソッドは**大文字キャメルケース（PascalCase）**を使用し、先頭文字は大文字とする。

### 1.1 標準送信メソッド

| メソッド名 | 説明 | 引数型 | 実装要件 |
|-------|------|---------|---------|
| `Text` | テキストメッセージを送信 | `str` | 必須 |
| `Image` | 画像を送信 | `str` \| `bytes` | 必須（基底クラスに既に実装済み、§6.4参照） |
| `Voice` | 音声を送信 | `str` \| `bytes` | 必須（基底クラスに既に実装済み；プラットフォームが音声をサポートしない場合は§2.1.5に従って降格） |
| `Video` | 動画を送信 | `str` \| `bytes` | 必須（基底クラスに既に実装済み；プラットフォームが動画をサポートしない場合は§2.1.5に従って降格） |
| `File` | ファイルを送信 | `str` \| `bytes`、`filename: str \| None = None` | 必須（基底クラスに既に実装済み） |
| `At` | ユーザー/グループを@する | `str` (user_id) | 修飾メソッド、必要に応じて使用 |
| `Face` | 表情を送信 | `str` (emoji) | 可能 |
| `Reply` | メッセージに返信する | `str` (message_id) | 修飾メソッド、必要に応じて使用 |
| `Forward` | メッセージを転送する | `str` (message_id) | 可能 |
| `Markdown` | Markdown形式のメッセージを送信 | `str` | 可能 |
| `HTML` | HTML形式のメッセージを送信 | `str` | 可能 |
| `Card` | カード形式のメッセージを送信 | `dict` | 可能 |

> 標準メソッド（`Text`/`Image`/`Voice`/`Video`/`File`）は基底クラス `SendDSL` に内蔵されており、`Raw_ob12` にデフォルトで委譲される。アダプタはこれらのメソッドを再実装せずにタイプ署名を得ることができる。プラットフォームに特別なロジックが必要な場合にのみ、個々のメソッドをオーバーライドする（§6.4参照）。

### 1.2 チェーン修飾メソッド

| メソッド名 | 説明 | 引数型 |
|-------|------|---------|
| `At` | ユーザーを@する（複数回呼び出し可） | `str` (user_id) |
| `AtAll` | 全メンバーを@する | 無し |
| `Reply` | メッセージに返信する | `str` (message_id) |

### 1.3 プロトコルメソッド

| メソッド名 | 説明 | 必須か |
|-------|------|---------|
| `Raw_ob12` | OneBot12形式のメッセージセグメントを送信 | 必須 |

**`Raw_ob12` は必須実装のメソッド**。これはアダプタの主要な責任の一つであり、OneBot12標準メッセージセグメントを受信してそれをプラットフォーム固有のAPI呼び出しに変換する。`Raw_ob12` はOneBot12 → プラットフォームへの逆変換（OneBot12 → プラットフォーム）の統一エントリーポイントであり、モジュールがプラットフォーム固有のメソッドに依存することなく、標準メッセージセグメントを使用してメッセージを送信できるようにする。

**`Raw_ob12` をオーバーライドしない場合の動作**：基底クラスのデフォルト実装は **errorレベル**のログを記録し、標準エラーレスポンス形式（`status: "failed"`, `retcode: 10002`）を返し、アダプタ開発者がこのメソッドを実装する必要があることを示す。

### 1.4 推奨される拡張命名規則

アダプタがOneBot12形式以外の生データ（プラットフォーム固有のJSON、XMLなど）を送信する必要がある場合、以下の命名規則を推奨する：

| 推奨メソッド名 | 説明 |
|-----------|------|
| `Raw_json` | 任意のJSONデータを送信 |
| `Raw_xml` | 任意のXMLデータを送信 |

**注意**：これらのメソッドは**基底クラスが提供するデフォルトメソッドではなく、強制的に実装する必要もない**。これらは命名規則としてのみ、アダプタが必要に応じて独自に定義できる。もしアダプタがこれらの形式をサポートしていない場合は、定義する必要はない。

**メッセージビルダ（MessageBuilder）**：ErisPulseは`MessageBuilder`ツールクラスを提供しており、OneBot12メッセージセグメントリストを容易に構築し、`Raw_ob12`と併用できる。詳細は[メッセージビルダ](#11-メッセージビルダ-messagebuilder)章節を参照。

## 2. 引数規則の詳細

### 2.1 メディア送信プロトコル（`Image` / `Voice` / `Video` / `File`）

本節はメディア送信の**統一プロトコル標準**である。モジュールは同じコードで4つのメディアメソッドを呼び出し、アダプタは`file`引数のさまざまな形態をプラットフォーム固有のアップロード/送信動作に変換する。

#### 2.1.1 `file`引数の合法な形態

| 形態 | 例 | アダプタの要件 |
|------|------|-----------|
| HTTP(S) URL | `https://example.com/image.jpg` | **必須**受ける |
| 本地ファイルパス | `/path/to/file.jpg`、`C:\path\to\file.jpg` | **必須**受ける |
| 二進データ | `b"\x89PNG..."` | **必須**受ける |
| `file://` URI | `file:///path/to/file.jpg` | **推奨**受ける（ローカルパスに転送して処理） |
| Base64文字列 / Data URI | `iVBORw0KGgo=...`、`data:image/png;base64,...` | **推奨**受ける（OneBot12エコシステムとの互換性に配慮） |

> アダプタは**必須の3つの形態**で動作を一貫させる必要がある。モジュールがURL、パス、またはbytesを渡しても、受信されるのは同じメッセージになる。プラットフォームが外部URLを直接使用できない場合（URLを参照またはダウンロードしてアップロード）、**要求を変更して再試行する必要はない**。

#### 2.1.2 形態判定順序

アダプタがメディア引数を処理する際、**判定順序は以下の通り**とする。

1. `bytes`型 → 直接アップロード
2. 文字列が`http://` / `https://`で始まる → URLとして処理（プラットフォームの能力に応じてURLを参照またはダウンロードしてアップロード）
3. 文字列が`file://`で始まる → プレフィックスを剥がしてローカルパスとして処理
4. その他の文字列 → ローカルパスとして処理（存在すれば読み込んでアップロード、存在しない場合は標準エラーレスポンスを返す）

```python
def _resolve_media(self, file: "str | bytes") -> bytes:
    """形態判定と正規化（例）"""
    if isinstance(file, (bytes, bytearray)):
        return bytes(file)
    if file.startswith(("http://", "https://")):
        return self._download(file)          # プラットフォームがURLを参照できない場合はダウンロード
    if file.startswith("file://"):
        file = file[len("file://"):]
    with open(file, "rb") as f:              # 本地ファイル
        return f.read()
```

#### 2.1.3 `File`のファイル名の意味

`File`メソッドの署名：`File(file, filename=None)`（`filename`はオプション引数、基底クラスに既に実装済み）。

ファイル名**推導順序**（アダプタが明示的に`filename`を提供しない場合にこの順序で生成）：

1. 明示的な`filename`引数（最高優先）
2. URLのbasename（例：`https://host/a/b/report.pdf` → `report.pdf`、クエリ文字列は剥がす）
3. 本地ファイルパスのbasename（例：`/tmp/data/backup.zip` → `backup.zip`）
4. プラットフォームが生成するデフォルト名（例：`file_{timestamp}`；**拡張子を保持する**。拡張子はプラットフォーム側の種類識別とプレビュー動作に影響する）

> `Image` / `Voice` / `Video`も**`filename`を受けることができる**（メッセージセグメント`data.filename`を通じて渡される）、ただし`File`のファイル名だけが跨プラットフォームの意味保証がある。

#### 2.1.4 プラットフォーム制限の宣言義務

各プラットフォームはメディアのサイズ上限、形式（MIME）、音声/動画の長さなどの制約が異なる。アダプタは**宣言する義務**がある：

- アダプタドキュメントにサポートするメディア形式と制限範囲を宣言する
- 制限を超えるか、サポートしない入力は**標準エラーレスポンス**を返す（`status: "failed"`；`retcode`は`10002`またはプラットフォームの意味化されたエラーコードを使用、`message`は原因を説明）、**例外をスローしてモジュールのロジックを中断してはならない**

#### 2.1.5 機能降格の段階

プラットフォームがメディアの**特定のタイプ**をサポートしない場合、以下の段階で降格する（総則「機能降格はエラーを出さない」を遵守）：

| 状況 | 降格動作 |
|------|---------|
| `Voice`が音声メッセージをサポートしない場合 | **推奨** `File`（またはプラットフォームに近縁な形態）で送信；表現できない場合は`retcode=10002`を返す |
| `Video`が動画メッセージをサポートしない場合 | 同上 |
| メディアタイプが完全にサポートされていない場合（ファイル機能がない） | `retcode=10002`を返し、`message`にサポートしていないデータタイプを明記する |
| 形態がサポートされていない場合（例：Base64を処理できない） | `retcode=10002`を返す、**`message`にモジュールにURL/bytesに変更するよう提示できる** |

**禁止される動作**：静かに破棄（返さない）、例外をスローする、モジュールにプラットフォーム分岐処理を書かせる。

### 2.2 @ユーザー引数の規則

**メソッド**：`At`（修飾メソッド）

**引数**：`user_id` (`str`)

**要件**：
- `user_id`は文字列型のユーザー識別子であるべき
- 各プラットフォームの`user_id`形式は異なる可能性がある（数値、UUID、文字列など）
- アダプタは`user_id`をプラットフォーム固有の形式に変換する責任がある
- 実際の送信メソッドの呼び出しは最後の位置に置くこと

**例**：
```python
# 単一の@ユーザー
Send.To("group", "g123").At("123456").Text("你好")

# 複数の@ユーザー（チェーン呼び出し）
send.To("group", "g123").At("123456").At("789012").Text("大家好")
```

### 2.3 メッセージ返信引数の規則

**メソッド**：`Reply`（修飾メソッド）

**引数**：`message_id` (`str`)

**要件**：
- `message_id`は文字列型のメッセージ識別子であるべき
- 以前に受信したメッセージのIDであるべき
- 一部のプラットフォームは返信機能をサポートしていない可能性があり、アダプタは優雅に降格するべき

**例**：
```python
send.To("group", "g123").Reply("msg_123456").Text("收到")
```

## 3. プラットフォーム固有メソッドの命名

Sendクラスに直接プラットフォームプレフィックス付きのメソッドを追加することは**推奨されない**。汎用メソッド名または`Raw_{プロトコル}`メソッドを使用することを推奨する。

**推奨されない**：
```python
def YunhuForm(self, form_id: str):  # ❌ 推奨されない
    pass

def TelegramSticker(self, sticker_id: str):  # ❌ 推奨されない
    pass
```

**推奨される**：
```python
def Form(self, form_id: str):  # ✅ 汎用メソッド名
    pass

def Sticker(self, sticker_id: str):  # ✅ 汎用メソッド名
    pass

def Raw_ob12(self, message):  # ✅ OneBot12形式を送信
    pass
```

**拡張メソッドの要件**：
- メソッド名はPascalCaseを使用し、プラットフォームプレフィックスを付けない
- `asyncio.Task`オブジェクトを返す必要がある
- 完全な型注釈とドキュメント文字列を提供する必要がある
- 引数設計は標準メソッドのスタイルにできるだけ一致させる

## 4. 引数名の規則

| 引数名 | 説明 | 型 |
|-------|------|------|
| `text` | テキスト内容 | `str` |
| `file` | メディア内容（URL / パス / 二進数、§2.1.1参照） | `str` / `bytes` |
| `filename` | ファイル名（`File`のオプション、§2.1.3参照） | `str` / `None` |
| `user_id` | ユーザーID | `str` / `int` |
| `group_id` | グループID | `str` / `int` |
| `message_id` | メッセージID | `str` |
| `data` | データオブジェクト（例：カードデータ） | `dict` |

## 5. 戻り値の規則

- **送信メソッド**（例：`Text`, `Image`）：`asyncio.Task`オブジェクトを返す必要がある
- **修飾メソッド**（例：`At`, `Reply`, `AtAll`）：`self`を返してチェーン呼び出しを可能にする必要がある

---

## 6. 逆変換規則（OneBot12 → プラットフォーム）

アダプタは、プラットフォーム固有のイベントをOneBot12形式に変換する（正変換）だけでなく、**OneBot12メッセージセグメントをプラットフォーム固有のAPI呼び出しに変換する**能力（逆変換）も提供しなければならない。逆変換の統一エントリーポイントは`Raw_ob12`メソッドである。

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
OneBot12標準イベント（含{platform}_raw）             プラットフォーム固有API呼び出し
（含{platform}_raw）                     （標準レスポンス形式を返す）
```

**コアの対称性**：正変換では元のデータを`{platform}_raw`に保持し、逆変換ではOneBot12標準形式を受け取り、プラットフォーム呼び出しに還元する。

### 6.2 `Raw_ob12`の実装規則

`Raw_ob12`はOneBot12標準メッセージセグメントリストを受け取り、それをプラットフォーム固有のAPI呼び出しに変換する。

**メソッド署名**：

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
    :return: asyncio.Task、await後に標準レスポンス形式を返す
    """
```

**実装要件**：

1. **すべての標準メッセージセグメントタイプを処理する必要がある**：少なくとも`text`、`image`、`audio`、`video`、`file`、`mention`、`reply`をサポートする
2. **プラットフォーム拡張メッセージセグメントを処理する必要がある**：`{platform}_xxx`形式のメッセージセグメントは、プラットフォームに対応する固有の呼び出しに変換する
3. **標準レスポンス形式を返す必要がある**：[APIレスポンス規格](api-response.md)に従う
4. **サポートしないメッセージセグメントは警告を記録してスキップし、例外をスローしてメッセージ全体の送信を失敗させるべきではない**

### 6.3 メッセージセグメント変換ルール

#### 6.3.1 標準メッセージセグメント変換

アダプタは以下の標準メッセージセグメントの変換を実装する必要がある：

| OneBot12メッセージセグメント | 変換要件 |
|----------------|---------|
| `text` | `data.text`をそのまま使用 |
| `image` | `data.file`を§2.1のメディアプロトコルに従って処理（3つの必須形態 + 判定順序） |
| `audio` | `image`の処理ロジックと同じ |
| `video` | `image`の処理ロジックと同じ |
| `file` | `image`の処理ロジックと同じ；ファイル名は§2.1.3の推導順序に従って`data.filename`を処理 |
| `mention` | プラットフォームの@ユーザー機能に変換（例：Telegramの`entities`、雲湖の`at_uid`） |
| `reply` | プラットフォームの返信引用機能に変換 |
| `face` | プラットフォームの絵文字送信機能に変換、サポートしない場合はスキップ |
| `location` | プラットフォームの位置送信機能に変換、サポートしない場合はスキップ |

#### 6.3.2 プラットフォーム拡張メッセージセグメント変換

プラットフォームプレフィックス付きのメッセージセグメントは、アダプタが認識して変換する：

```python
def _convert_ob12_segments(self, segments: List[Dict]) -> Any:
    """OneBot12メッセージセグメントをプラットフォーム固有形式に変換"""
    platform_prefix = f"{self._platform_name}_"
    
    for segment in segments:
        seg_type = segment["type"]
        seg_data = segment["data"]
        
        if seg_type.startswith(platform_prefix):
            # プラットフォーム拡張メッセージセグメント → プラットフォーム固有の呼び出し
            self._handle_platform_segment(seg_type, seg_data)
        elif seg_type in self._standard_segment_handlers:
            # 標準メッセージセグメント → プラットフォーム等価操作
            self._standard_segment_handlers[seg_type](seg_data)
        else:
            # 未知のメッセージセグメント → 警告を記録してスキップ
            logger.warning(f"サポートしないメッセージセグメント: {seg_type}")
```

#### 6.3.3 複合メッセージセグメント処理

1つのメッセージは複数のメッセージセグメントを含む可能性があり、アダプタは複合メッセージを正しく処理する：

```python
# モジュールがテキスト+画像+@ユーザーを含むメッセージを送信
await send.Raw_ob12([
    {"type": "mention", "data": {"user_id": "123"}},
    {"type": "text", "data": {"text": "你好"}},
    {"type": "image", "data": {"file": "https://example.com/img.jpg"}}
])
```

**処理戦略**：
- **優先して結合**：プラットフォームがテキスト、画像、@などを1つのメッセージに同時に含めることが可能であれば、結合して送信する
- **次善として分割**：プラットフォームが結合をサポートしない場合は、順番に複数のメッセージに分割して送信する
- **順序を保持**：メッセージセグメントの送信順序はリストの順序と一致する

### 6.4 `Raw_ob12`と標準メソッドの関係

アダプタの標準送信メソッド（`Text`、`Image`等）は**`SendDSL`基底クラスに既に実装され、デフォルトで`Raw_ob12`に委譲されている**。アダプタのサブクラスは再実装する必要はない：

```python
class Send(SendDSL):
    def Raw_ob12(self, message_segments: List[Dict]) -> asyncio.Task:
        """コア実装：OneBot12メッセージセグメント → プラットフォームAPI（必須実装）"""
        return asyncio.create_task(self._send_ob12(message_segments))

    # Text/Image/Voice/Video/Fileは基底クラスから継承され、自動的にRaw_ob12に委譲される
    # プラットフォーム固有のロジックが必要な場合は、個々のメソッドをオーバーライドできる：
    # def Text(self, text: str) -> asyncio.Task:
    #     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

**メリット**：
- 変換ロジックは`Raw_ob12`の1か所に集中し、重複コードを減らす
- 標準メソッドと`Raw_ob12`の動作は完全に一致する
- モジュールは`Text()`または`Raw_ob12()`を使用しても同じ結果を得られる
- 基底クラスがタイプ署名を提供し、IDEが標準メソッドを補完できる

### 6.5 実装例

```python
class YunhuSend(SendDSL):
    """雲湖プラットフォーム用Send実装"""
    
    def Raw_ob12(self, message_segments: list) -> asyncio.Task:
        """OneBot12メッセージセグメント → 雲湖API呼び出し"""
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
                logger.warning(f"雲湖がサポートしないメッセージセグメント: {seg_type}")
        
        # 3. 雲湖APIを呼び出す
        response = await self._call_yunhu_api(yunhu_elements, at_users, reply_to, at_all)
        
        # 4. 標準レスポンス形式を返す
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

モジュール開発者は、適切な送信メソッドを発見するためにAPIを使用できる（**プラットフォーム固有のメソッドリストをモジュールにハードコードしてはならない**—各アダプタの拡張メソッドはバージョンの進化に伴い変化するため、実行時の発見をベースとする）：

```python
from ErisPulse import adapter

# すべての送信メソッドをリストアップ
methods = adapter.list_sends("myplatform")
# ["Batch", "Form", "Image", "Recall", "Sticker", "Text", ...]

# メソッド詳細を取得
info = adapter.send_info("myplatform", "Form")
# {
#     "name": "Form",
#     "parameters": [{"name": "form_id", "type": "str", ...}],
#     "return_type": "Awaitable[Any]",
#     "docstring": "雲湖フォームを送信"
# }
```

---

## 9. アダプタ開発の注意点

`BaseAdapter`、`Send`、`Request`の`__init__`を正しくオーバーライドする方法については、[アダプタ開発入門 - `__init__`の注意点](../developer-guide/adapters/getting-started.md#init-の注意点)を参照。

---

---

## 10. アダプタ実装チェックリスト

### 送信メソッド
- [ ] 標準メソッド（`Text`, `Image`等）が実装されている
- [ ] 戻り値はすべて`asyncio.Task`である
- [ ] 修飾メソッド（`At`, `Reply`, `AtAll`）は`self`を返す
- [ ] プラットフォーム拡張メソッドはPascalCaseを使用し、プラットフォームプレフィックスを付けない
- [ ] すべてのメソッドに完全な型注釈とドキュメント文字列がある

### メディア送信プロトコル
- [ ] `file`引数の**必須形態**（HTTP(S) URL / 本地ファイルパス / `bytes`、§2.1.1参照）がすべてサポートされている
- [ ] 形態判定順序は§2.1.2（bytes → URL → `file://` → ファイルパス）に従っている
- [ ] `File`のファイル名推導順序は§2.1.3（明示的な`filename` > URLのbasename > ファイルパスのbasename > プラットフォームデフォルト）に従っている
- [ ] プラットフォームのメディア制限（サイズ / MIME / 時長）がアダプタドキュメントに宣言されている（§2.1.4）
- [ ] 不支持のメディアタイプは§2.1.5の降格段階に従って処理されている：近縁タイプに降格するか`retcode=10002`を返す、例外をスローしたり、静かに破棄したりしない

### 逆変換
- [ ] `Raw_ob12`が**実装されている**（必須、スキップ不可）
- [ ] `Raw_ob12`はすべての標準メッセージセグメント（`text`, `image`, `audio`, `video`, `file`, `mention`, `reply`）を処理できる
- [ ] `Raw_ob12`はプラットフォーム拡張メッセージセグメント（`{platform}_xxx`形式）を処理できる
- [ ] 標準送信メソッド（`Text`, `Image`等）は内部で`Raw_ob12`に委譲しており、個別の変換ロジックを実装していない
- [ ] 不支持のメッセージセグメントは警告を記録してスキップし、例外をスローしない
- [ ] 複合メッセージセグメントは正しく処理されている（結合または順序に従って分割）

---

## 11. メッセージビルダ（MessageBuilder）

`MessageBuilder`はErisPulseが提供するメッセージセグメント構築ツールで、`Raw_ob12`と併用することでOneBot12メッセージセグメントの構築プロセスを簡素化する。

### 11.1 導入

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
# 単一メッセージセグメントを高速に構築（Raw_ob12に直接渡せるlist[dict]を返す）
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
        .text("あなたのメッセージを受け取りました")
        .build()
    )
```

### 11.5 支持するメッセージセグメントメソッド

| メソッド | 説明 | dataフィールド |
|------|------|----------|
| `text(text)` | テキスト | `text` |
| `image(file)` | 画像 | `file` |
| `audio(file)` | 音声 | `file` |
| `video(file)` | 動画 | `file` |
| `file(file, filename=None)` | ファイル | `file`, `filename`(オプション) |
| `mention(user_id, user_name=None)` | @ユーザー | `user_id`, `user_name`(オプション) |
| `at(user_id, user_name=None)` | @ユーザー（`mention`の別名） | `mention`と同じ |
| `reply(message_id)` | 返信 | `message_id` |
| `at_all()` | 全員@ | `{}` |
| `custom(type, data)` | 自定義/プラットフォーム拡張 | 自定義 |

### 11.6 ユーティリティメソッド

```python
builder = MessageBuilder().text("基本内容")

# コピー（ディープコピー）
msg1 = builder.copy().image("img1").build()
msg2 = builder.copy().image("img2").build()

# クリア
builder.clear().text("新しい内容").build()

# 空かどうか判定
if builder:
    print(f"メッセージセグメントが {len(builder)} 個含まれています")
```

---

## 12. 関連ドキュメント

- [イベント変換標準](event-conversion.md) - 完全なイベント変換規則、拡張命名、メッセージセグメント標準
- [APIレスポンス標準](api-response.md) - アダプタAPIレスポンス形式の標準
- [セッションタイプ標準](session-types.md) - セッションタイプの定義とマッピング
- [リクエスト操作規則](request-action-spec.md) - リクエストイベントのフィールド要件、HandleRequest DSL、およびアダプタ実装要件