# ErisPulse 送信メソッド規格

本文書では、ErisPulse アダプタの Send クラスにおける送信メソッドの命名規格、パラメータ規格および逆変換要件を定義します。

## 1. 標準メソッド命名

送信メソッドはすべて **PascalCase（大文字キャメルケース）** を使用し、先頭文字は大文字です。

### 1.1 標準送信メソッド

| メソッド名 | 説明 | パラメータ型 |
|-------|------|---------|
| `Text` | テキストメッセージを送信 | `str` |
| `Image` | 画像を送信 | `bytes` \| `str` (URL/パス) |
| `Voice` | 音声を送信 | `bytes` \| `str` (URL/パス) |
| `Video` | 動画を送信 | `bytes` \| `str` (URL/パス) |
| `File` | ファイルを送信 | `bytes` \| `str` (URL/パス) |
| `At` | ユーザー/グループを@する | `str` (user_id) |
| `Face` | 表情を送信 | `str` (emoji) |
| `Reply` | メッセージに返信する | `str` (message_id) |
| `Forward` | メッセージを転送する | `str` (message_id) |
| `Markdown` | Markdownメッセージを送信 | `str` |
| `HTML` | HTMLメッセージを送信 | `str` |
| `Card` | カードメッセージを送信 | `dict` |

### 1.2 チェーン修飾メソッド

| メソッド名 | 説明 | パラメータ型 |
|-------|------|---------|
| `At` | ユーザーを@する（複数回呼び出し可能） | `str` (user_id) |
| `AtAll` | 全員を@する | 無し |
| `Reply` | メッセージに返信する | `str` (message_id) |

### 1.3 プロトコルメソッド

| メソッド名 | 説明 | 必須か |
|-------|------|---------|
| `Raw_ob12` | OneBot12形式のメッセージセグメントを送信 | 必須 |

**`Raw_ob12` は実装が必要なメソッドです**。これはアダプタの中心的な役割の一つであり、OneBot12標準メッセージセグメントを受け取り、それをプラットフォーム固有のAPI呼び出しに変換することです。`Raw_ob12` はOneBot12からプラットフォームへの一元的な変換エントリポイントであり、モジュールがプラットフォーム固有のメソッドに依存せずに、標準メッセージセグメントを使ってメッセージを送信できるようにします。

**`Raw_ob12` をオーバーライドしない場合の動作**：基底クラスのデフォルト実装では、**errorレベル**のログを記録し、標準エラー応答形式（`status: "failed"`, `retcode: 10002`）を返し、アダプタ開発者がこのメソッドを実装する必要があることを示します。

### 1.4 推奨される拡張命名規約

アダプタがOneBot12形式以外の生データ（プラットフォーム固有のJSON、XMLなど）を送信する機能をサポートする場合、以下の命名規約を推奨します：

| 推奨メソッド名 | 説明 |
|-----------|------|
| `Raw_json` | 任意のJSONデータを送信 |
| `Raw_xml` | 任意のXMLデータを送信 |

**注意**：これらのメソッドは**基底クラスに提供されているものではなく、実装が必須というわけではありません**。これらは単なる命名規約であり、アダプタは必要に応じて独自に定義できます。アダプタがこれらの形式をサポートしていない場合は、定義する必要はありません。

**メッセージビルダー（MessageBuilder）**：ErisPulseは`MessageBuilder`というツールクラスを提供しており、OneBot12メッセージセグメントリストを簡単に構築するのに使用できます。`Raw_ob12`と併用してください。詳しくは[メッセージビルダー](#11-メッセージビルダー-messagebuilder)章をご覧ください。

## 2. パラメータ規格の詳細説明

### 2.1 メディアメッセージのパラメータ規格

メディアメッセージ（`Image`、`Voice`、`Video`、`File`）は、2種類のパラメータタイプをサポートしています。

#### 2.1.1 文字列パラメータ（URL またはファイルパス）

**形式：** `str`

**サポート対象：**
- **URL**：ネットワークリソースのアドレス（例：`https://example.com/image.jpg`）
- **ファイルパス**：ローカルファイルのパス（例：`/path/to/file.jpg` または `C:\\path\\to\\file.jpg`）

**使用シーン：**
- ファイルが既にネットワーク上にある場合、URLを直接送信する
- ローカルディスクにファイルがある場合、ファイルパスを送信する
- アダプタがファイルのアップロードを自動的に処理することを希望する

**推奨：** URLを使用することを優先し、URLが利用できない場合はローカルファイルパスを使用する

**例：**
```python
# URLを使用する
send.Image("https://example.com/image.jpg")

# ローカルファイルパスを使用する
send.Image("/path/to/local/image.jpg")
send.Image("C:\\path\\to\\local\\image.jpg")
```

#### 2.1.2 2進数データパラメータ

**形式：** `bytes`

**使用シーン：**
- ファイルが既にメモリ内にある場合（例：ネットワークからダウンロード、他のソースから読み込む）
- ファイルを処理した後に送信する必要がある場合（例：画像の圧縮、フォーマットの変換）
- ファイルを繰り返し読み取ることを避ける

**注意事項：**
- 大きなファイルのアップロードは多くのメモリを消費する可能性がある
- 妥当なファイルサイズ制限を設定することを推奨する

**例：**
```python
# ネットワークから読み取って送信する
import requests
image_data = requests.get("https://example.com/image.jpg").content
send.Image(image_data)

# ファイルから読み取って送信する
with open("/path/to/local/image.jpg", "rb") as f:
    image_data = f.read()
send.Image(image_data)
```

#### 2.1.3 パラメータ処理の優先順位

アダプタがメディアメッセージのパラメータを受け取った場合、以下の順序で処理する必要があります：

1. **URLパラメータ**：URLを直接使用して送信する（一部のプラットフォームアダプタでは、URLのダウンロード後にアップロードを行う場合がある）
2. **ファイルパス**：ローカルパスであるかを検証し、ローカルパスであればファイルをアップロードする
3. **2進数データ**：2進数データを直接アップロードする

**アダプタ実装の推奨：**
```python
def Image(self, image: Union[bytes, str]):
    if isinstance(image, str):
        # URLかローカルパスかを判断する
        if image.startswith(("http://", "https://")):
            # URLを直接送信する
            return self._send_image_by_url(image)
        else:
            # ローカルパスの場合、ファイルを読み込んでアップロードする
            with open(image, "rb") as f:
                return self._upload_image(f.read())
    elif isinstance(image, bytes):
        # 2進数データの場合、直接アップロードする
        return self._upload_image(image)
```

### 2.2 @ユーザーのパラメータ規格

**メソッド：** `At`（修飾メソッド）

**パラメータ：** `user_id` (`str`)

**要件：**
- `user_id` は文字列型のユーザー識別子である必要がある
- 各プラットフォームの `user_id` の形式は異なる可能性がある（数字、UUID、文字列など）
- アダプタは `user_id` をプラットフォーム固有の形式に変換する責任がある
- 実際の送信メソッドの呼び出しを最後に配置することに注意する

**例：**
```python
# 単一の@ユーザー
Send.To("group", "g123").At("123456").Text("你好")

# 複数の@ユーザー（チェーン呼び出し）
send.To("group", "g123").At("123456").At("789012").Text("大家好")
```

### 2.3 メッセージへの返信のパラメータ規格

**メソッド：** `Reply`（修飾メソッド）

**パラメータ：** `message_id` (`str`)

**要件：**
- `message_id` は文字列型のメッセージ識別子である必要がある
- 以前に受信したメッセージのIDである必要がある
- 一部のプラットフォームでは返信機能がサポートされていない可能性があるため、アダプタは優雅な降格処理を行うべきである

**例：**
```python
send.To("group", "g123").Reply("msg_123456").Text("收到")
```

## 3. 平台特有メソッドの命名

Send クラスに直接プラットフォームのプレフィックスを付けてメソッドを追加することは**推奨されません**。代わりに、一般的なメソッド名または `Raw_{プロトコル}` メソッドを使用することを推奨します。

**推奨されない例：**
```python
def YunhuForm(self, form_id: str):  # ❌ 推奨されません
    pass

def TelegramSticker(self, sticker_id: str):  # ❌ 推奨されません
    pass
```

**推奨される例：**
```python
def Form(self, form_id: str):  # ✅ 一般的なメソッド名
    pass

def Sticker(self, sticker_id: str):  # ✅ 一般的なメソッド名
    pass

def Raw_ob12(self, message):  # ✅ OneBot12 形式を送信
    pass
```

**拡張メソッドの要件：**
- メソッド名は PascalCase を使用し、プラットフォームのプレフィックスを付けない
- 必ず `asyncio.Task` オブジェクトを返す
- 完全な型注釈とドキュメント文字列を提供する
- パラメータの設計は、標準メソッドのスタイルとできるだけ一致させる

## 4. パラメータ命名規則

| パラメータ名 | 説明 | 型 |
|-------|------|------|
| `text` | テキスト内容 | `str` |
| `url` / `file` | ファイルの URL またはバイナリデータ | `str` / `bytes` |
| `user_id` | ユーザー ID | `str` / `int` |
| `group_id` | グループ ID | `str` / `int` |
| `message_id` | メッセージ ID | `str` |
| `data` | データオブジェクト（例：カードデータ） | `dict` |

## 5. 戻り値の規格

- **送信メソッド**（例: `Text`, `Image`）：必ず `asyncio.Task` オブジェクトを返す必要があります
- **修飾メソッド**（例: `At`, `Reply`, `AtAll`）：チェーン呼び出しをサポートするため、必ず `self` を返す必要があります

---

## 6. 反転変換規格（OneBot12 → プラットフォーム）

アダプターは、プラットフォームのネイティブイベントを OneBot12 形式に変換する（正方向変換）だけでなく、**必ず** OneBot12 メッセージセグメントをプラットフォームのネイティブ API 呼び出しに変換する機能（反転変換）を提供する必要があります。反転変換の統一エントリーポイントは `Raw_ob12` メソッドです。

### 6.1 変換モデル

```
正方向変換（受信方向）                反転変換（送信方向）
─────────────────                ─────────────────
プラットフォームのネイティブイベント                       OneBot12 メッセージセグメントリスト
    │                                  │
    ▼                                  ▼
Converter.convert()               Send.Raw_ob12()
    │                                  │
    ▼                                  ▼
OneBot12 標準イベント                  プラットフォームのネイティブ API 呼び出し
（含 {platform}_raw）             （標準レスポンス形式を返す）
```

**コアの対称性**：正方向変換では、元のデータは `{platform}_raw` に保持され、反転変換では OneBot12 標準形式を受け取り、プラットフォームの呼び出しに復元されます。

### 6.2 `Raw_ob12` 実装規格

`Raw_ob12` は、OneBot12 標準メッセージセグメントリストを受け取り、それをプラットフォームのネイティブ API 呼び出しに変換する必要があります。

**メソッド署名**：

```python
def Raw_ob12(self, message_segments: List[Dict]) -> asyncio.Task:
    """
    OneBot12 標準メッセージセグメントの送信

    :param message_segments: OneBot12 メッセージセグメントリスト
        [
            {"type": "text", "data": {"text": "Hello"}},
            {"type": "image", "data": {"file": "https://..."}},
            {"type": "mention", "data": {"user_id": "123"}},
        ]
    :return: asyncio.Task。await 後に標準レスポンス形式を返す
    """
```

**実装要件**：

1. **すべての標準メッセージセグメントタイプを処理する必要がある**：少なくとも `text`、`image`、`audio`、`video`、`file`、`mention`、`reply` をサポートする
2. **プラットフォーム拡張メッセージセグメントを処理する必要がある**：`{platform}_xxx` タイプのメッセージセグメントについては、プラットフォームに対応するネイティブ呼び出しに変換する
3. **標準レスポンス形式を返す必要がある**：[API レスポンス標準](api-response.md)に従う
4. **サポートされていないメッセージセグメントは警告を記録してスキップする**。エラーをスローしてメッセージ全体の送信を失敗させるべきではない

### 6.3 メッセージセグメント変換ルール

#### 6.3.1 標準メッセージセグメント変換

アダプターは以下の標準メッセージセグメントの変換を実装する必要があります：

| OneBot12 メッセージセグメント | 変換要件 |
|----------------|---------|
| `text` | `data.text` を直接使用する |
| `image` | `data.file` のタイプに応じて処理する：URL は直接使用し、bytes はアップロードし、ローカルパスは読み込んでからアップロードする |
| `audio` | `image` と同じ処理ロジック |
| `video` | `image` と同じ処理ロジック |
| `file` | `image` と同じ処理ロジック。`data.filename` に注意する |
| `mention` | プラットフォームの @ユーザー 機制に変換する（例：Telegram の `entities`、云湖の `at_uid`） |
| `reply` | プラットフォームの返信引用機制に変換する |
| `face` | プラットフォームの絵文字送信機制に変換する。サポートされていない場合はスキップする |
| `location` | プラットフォームの位置送信機制に変換する。サポートされていない場合はスキップする |

#### 6.3.2 プラットフォーム拡張メッセージセグメント変換

プラットフォームのプレフィックスを持つメッセージセグメントについては、アダプターは識別して変換する必要があります：

```python
def _convert_ob12_segments(self, segments: List[Dict]) -> Any:
    """OneBot12 メッセージセグメントをプラットフォームのネイティブ形式に変換する"""
    platform_prefix = f"{self._platform_name}_"
    
    for segment in segments:
        seg_type = segment["type"]
        seg_data = segment["data"]
        
        if seg_type.startswith(platform_prefix):
            # プラットフォーム拡張メッセージセグメント → プラットフォームのネイティブ呼び出し
            self._handle_platform_segment(seg_type, seg_data)
        elif seg_type in self._standard_segment_handlers:
            # 標準メッセージセグメント → プラットフォームの同等操作
            self._standard_segment_handlers[seg_type](seg_data)
        else:
            # 未知のメッセージセグメント → 警告を記録してスキップする
            logger.warning(f"サポートされていないメッセージセグメントタイプ: {seg_type}")
```

#### 6.3.3 複合メッセージセグメントの処理

1 つのメッセージには複数のメッセージセグメントが含まれる可能性があり、アダプターは複合メッセージを正しく処理する必要があります：

```python
# モジュールがテキスト+画像+@ユーザー を含むメッセージを送信
await send.Raw_ob12([
    {"type": "mention", "data": {"user_id": "123"}},
    {"type": "text", "data": {"text": "你好"}},
    {"type": "image", "data": {"file": "https://example.com/img.jpg"}}
])
```

**処理戦略**：
- **優先的に結合する**：プラットフォームが 1 つのメッセージにテキスト、画像、@などを同時に含むことをサポートしている場合は、結合して送信する
- **次善の策として分割する**：プラットフォームが結合をサポートしていない場合は、順番に分割して複数のメッセージとして送信する
- **順序を保持する**：メッセージセグメントの送信順序は、リストの順序と一致するようにする

### 6.4 `Raw_ob12` と標準メソッドの関係

アダプターの標準送信メソッド（`Text`、`Image` など）は、**`SendDSL` 基底クラスに既に実装されており、`Raw_ob12` にデフォルトで委譲されている**。アダプターのサブクラスでは、これらのメソッドを再実装する必要はありません：

```python
class Send(SendDSL):
    def Raw_ob12(self, message_segments: List[Dict]) -> asyncio.Task:
        """コア実装：OneBot12 メッセージセグメント → プラットフォーム API（必ず実装する）"""
        return asyncio.create_task(self._send_ob12(message_segments))

    # Text/Image/Voice/Video/File は基底クラスから継承され、自動的に Raw_ob12 に委譲される
    # プラットフォーム固有のロジックが必要な場合は、個別のメソッドをオーバーライドする：
    # def Text(self, text: str) -> asyncio.Task:
    #     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

**メリット**：
- 変換ロジックは `Raw_ob12` に集中し、重複コードを減らす
- 標準メソッドと `Raw_ob12` の動作は完全に一致する
- モジュールは `Text()` または `Raw_ob12()` を使用しても同じ結果を得られる
- 基底クラスが型署名を提供し、IDE は標準メソッドを補完できる

### 6.5 実装例

```python
class YunhuSend(SendDSL):
    """云湖プラットフォームの Send 実装"""
    
    def Raw_ob12(self, message_segments: list) -> asyncio.Task:
        """OneBot12 メッセージセグメント → 云湖 API 呼び出し"""
        return asyncio.create_task(self._do_send(message_segments))
    
    async def _do_send(self, segments: list) -> dict:
        """実際の送信ロジック"""
        # 1. 修飾子の状態を解析する
        at_users = self._at_users or []
        reply_to = self._reply_to
        at_all = self._at_all
        
        # 2. メッセージセグメントを変換する
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
        
        # 3. 云湖 API を呼び出す
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

## 7. メソッド発見

モジュール開発者は、API を使用してアダプターがサポートする送信メソッドを照会することができます。

```python
from ErisPulse import adapter

# すべての送信メソッドをリスト化
methods = adapter.list_sends("myplatform")
# ["Batch", "Form", "Image", "Recall", "Sticker", "Text", ...]

# メソッドの詳細を確認
info = adapter.send_info("myplatform", "Form")
# {
#     "name": "Form",
#     "parameters": [{"name": "form_id", "type": "str", ...}],
#     "return_type": "Awaitable[Any]",
#     "docstring": "雲湖フォームの送信"
# }
```

---

## 8. 登録済みの送信メソッド拡張

| プラットフォーム | メソッド名 | 説明 |
|------|--------|------|
| onebot12 | `Mention` | ユーザーをメンションする（OneBot12スタイル） |
| onebot12 | `Sticker` | ステッカーを送信する |
| onebot12 | `Location` | 位置情報を送信する |
| onebot12 | `Recall` | メッセージを撤回する |
| onebot12 | `Edit` | メッセージを編集する |
| onebot12 | `Batch` | バッチ送信する |

> **注意**: 送信メソッドにはプラットフォームのプレフィックスを付けないでください。異なるプラットフォームの同名メソッドは異なる実装を持つことができます。

## 9. アダプター開発の注意点

`BaseAdapter`、`Send`、`Request` の `__init__` を正しくオーバーライドする方法については、[アダプター開発入門 - `__init__` の注意点](../developer-guide/adapters/getting-started.md#init-の注意点) を参照してください。

## 10. アダプタ実装チェックリスト

### 送信メソッド
- [ ] 標準メソッド（`Text`, `Image` など）が実装されている
- [ ] 戻り値はすべて `asyncio.Task` である
- [ ] 修飾メソッド（`At`, `Reply`, `AtAll`）は `self` を返す
- [ ] プラットフォーム拡張メソッドは PascalCase を使用し、プラットフォームのプレフィックスは付与しない
- [ ] すべてのメソッドに完全な型注釈とドキュメント文字列がある

### 逆変換
- [ ] `Raw_ob12` **が実装されている**（必須、スキップ不可）
- [ ] `Raw_ob12` はすべての標準メッセージセグメント（`text`, `image`, `audio`, `video`, `file`, `mention`, `reply`）を処理できる
- [ ] `Raw_ob12` はプラットフォーム拡張メッセージセグメント（`{platform}_xxx` 型）を処理できる
- [ ] 標準送信メソッド（`Text`, `Image` など）は内部で `Raw_ob12` に委譲し、独立した変換ロジックを実装しない
- [ ] 対応していないメッセージセグメントは警告を記録してスキップし、例外を送出しない
- [ ] 複合メッセージセグメントは正しく処理される（結合または順序通りに分割）

## 11. メッセージビルダー（MessageBuilder）

`MessageBuilder` は、ErisPulse が提供するメッセージセグメント構築ツールであり、`Raw_ob12` と併用することで、OneBot12 のメッセージセグメント構築プロセスを簡素化します。

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
# 単一メッセージセグメントを高速に構築（Raw_ob12 に直接渡せる list[dict] を返す）
await adapter.Send.To("user", "123").Raw_ob12(MessageBuilder.text("Hello"))
await adapter.Send.To("group", "456").Raw_ob12(MessageBuilder.image("https://..."))
await adapter.Send.To("group", "456").Raw_ob12(MessageBuilder.mention("123"))
await adapter.Send.To("group", "456").Raw_ob12(MessageBuilder.reply("msg_id"))
await adapter.Send.To("group", "456").Raw_ob12(MessageBuilder.at_all())
```

### 11.4 Event.reply_ob12 との併用

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

### 11.5 対応するメッセージセグメントメソッド

| メソッド | 説明 | data フィールド |
|------|------|----------|
| `text(text)` | テキスト | `text` |
| `image(file)` | 画像 | `file` |
| `audio(file)` | 音声 | `file` |
| `video(file)` | 動画 | `file` |
| `file(file, filename=None)` | ファイル | `file`, `filename`（オプション） |
| `mention(user_id, user_name=None)` | @ユーザー | `user_id`, `user_name`（オプション） |
| `at(user_id, user_name=None)` | @ユーザー（`mention` の別名） | `mention` と同じ |
| `reply(message_id)` | メッセージへの返信 | `message_id` |
| `at_all()` | 全員にメンション | `{}` |
| `custom(type, data)` | 自定義/プラットフォーム拡張 | 自定義 |

### 11.6 ユーティリティメソッド

```python
builder = MessageBuilder().text("基礎内容")

# コピー（ディープコピー）
msg1 = builder.copy().image("img1").build()
msg2 = builder.copy().image("img2").build()

# クリア
builder.clear().text("新内容").build()

# 空かどうかの判定
if builder:
    print(f"メッセージセグメントが {len(builder)} 個含まれています")
```

## 12. 関連ドキュメント

- [イベント変換標準](event-conversion.md) - 完全なイベント変換の仕様、拡張名およびメッセージセグメントの標準
- [APIレスポンス標準](api-response.md) - アダプタAPIレスポンス形式の標準
- [セッション型標準](session-types.md) - セッション型の定義とマッピング関係
- [リクエスト操作規範](request-action-spec.md) - リクエストイベントのフィールド要件、HandleRequest DSLおよびアダプタ実装要件