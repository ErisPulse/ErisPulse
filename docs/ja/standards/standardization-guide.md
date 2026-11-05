# アダプター標準化ガイド（概要）

> [!TIP]
> **このドキュメントを読むタイミング**：新しいアダプターを開発するとき、または特定のプラットフォームに新機能を追加する際、"標準に追加するか、`{platform}_` 拡張を用いるか"、命名規則、プラットフォーム間の差異をどのように処理するかを決める必要があるときは、まず本文を読んでください。特定の分野の詳細な規格を調べるだけであれば、§2の標準マップに対応するドキュメントに直接移動してください。

本文は、ErisPulse アダプターの標準化に関する**概要**です。ここでは、多様なプラットフォーム間で標準化を実現するための原則、標準マップ、差異処理のモード、新機能を標準に追加するプロセス、さらに**インタラクティブコンポーネントの標準**（ボタン/キーボード、ドロップダウン選択など）と**インタラクティブコールバックイベント**の完全な定義を示します。アダプター開発者は、新しい機能を実装する際には**まず標準定義を採用**し、モジュール開発者が同一のコードで任意のプラットフォームで一貫した体験を得られるようにすることが求められます。つまり、命名、パラメータ、返り値がすべて一貫している必要があります。

## 1. 標準化原則

1. **命名の一貫性**：同一概念はすべてのプラットフォームで同一の命名を使用する（例：撤回は `delete_message`、ボタンセグメントは `keyboard` など）。プラットフォームごとに異なる命名は使用しない。
2. **パラメータの一貫性**：標準アクション/セグメント/メソッドのパラメータ構造はすべてのプラットフォームで一貫している。プラットフォーム固有のパラメータは**オプション拡張パラメータ**または**拡張フィールド**として提供され、標準のシグネチャを汚染しない。
3. **返却値の一貫性**：すべての API/送信呼び出しは標準レスポンス構造（`status/retcode/data/message_id/message`）を返す。`data` 内の標準フィールド（例：`user_id/user_name`）の意味は一貫している。プラットフォーム固有のデータは `{platform}_raw` に格納する。
4. **拡張の根拠**：プラットフォーム固有の機能は `{platform}_` という接頭辞で命名する（セグメント：`yunhu_form`、アクション：`yunhu.board`、イベントフィールド：`qqbot_button_id`）。これにより、非クロスプラットフォームであることが明確に示される。
5. **差異はアダプタ層で吸収**：モジュールコードは標準プログラミングを対象とし、プラットフォームの差異はアダプタによって変換される（パラメータのマッピング、フィールドの標準化、機能のロールバック）。モジュールはプラットフォームの分岐を書く必要はない。
6. **機能ロールバック時にエラーを発生させない**：プラットフォームが標準機能をサポートしていない場合、エラーを発生させずにロールバックする（`retcode=10002` を返す、コンポーネントのテキスト化を `alt_message` に含める）。モジュールのロジックを中断しない。

## 2. 標準マップ

| ドメイン | 標準ドキュメント | 覆蓋内容 |
|------|---------|---------|
| イベント変換 | [イベント変換標準](event-conversion.md) | イベント構造、標準メッセージセグメント（text/image/mention/reply/keyboard など）、プラットフォーム拡張セグメントの規格 |
| 交互コンポーネント | **本文書 §5** | ボタン/キーボード、ドロップダウン選択、カード、交互コールバックイベントの標準フィールド、修飾子の約束事、各プラットフォームへのマッピング |
| API アクション | [API アクション標準](api-action-spec.md) | OneBot12 標準アクション（ユーザー/グループ/チャンネル/メッセージ管理/メタアクション）の統一インターフェースと `ApiDSL` |
| 要求操作 | [要求操作規格](request-action-spec.md) | 要求イベントフィールド（request_id）と Request DSL（approve/reject） |
| 送信メソッド | [送信メソッド規格](send-method-spec.md) | Send クラスメソッドの命名、パラメータ、修飾子、逆変換（OB12→プラットフォーム） |
| 会話タイプ | [会話タイプ標準](session-types.md) | user/group/channel/guild/dms などの会話タイプの定義とマッピング |
| API 応答 | [API 応答標準](api-response.md) | 標準応答構造と retcode の約束事 |

## 3. 標準化ワークフロー（新規機能が標準に取り込まれる方法）

```
プラットフォーム固有の機能（{platform}_ 前綴）
        │  2 つ以上のプラットフォームで同様の機能が出現
        ▼
共通性の識別（共通概念とパラメータのサブセットの抽出）
        │
        ▼
標準草案（命名 + パラメータ + 戻り値 + 各プラットフォームのマッピング表）
        │  審査
        ▼
本ガイドライン/各分野の標準文書に記載 + フレームワークの基底クラス/アダプタによる互換性層の実装
        │
        ▼
標準セグメント/アクション（前綴なし）——モジュールがプラットフォーム間で再利用可能
```

**例**：ボタンは当初、各プラットフォームで独立して実装されていた（`telegram_inline_keyboard` / 雲湖 buttons / QQBot keyboard）→ 3 つ以上のプラットフォームで登場 → 共通構造（`label/type/data` + rows）を抽出 → 標準 `keyboard` セグメントを発行 → 各アダプタが互換性層を実装（修飾子が共通構造を受け入れ、標準セグメントを変換し、ネイティブセグメントを透過する）。

### 3.1 命名規則

| 対象 | 規則 | 例 |
|------|------|------|
| 標準メッセージセグメント | 小文字、共通概念には前綴なし | `keyboard`、`select`、`mention` |
| プラットフォーム拡張セグメント | `{platform}_` 前綴 | `telegram_sticker`、`yunhu_form` |
| 標準APIアクション | OB12 標準名（snake_case） | `get_group_info`、`delete_message` |
| プラットフォーム拡張アクション | `{platform}.` 前綴またはプロトコル共通名 | `yunhu.board`、`send_poke`（OB11 拡張） |
| 修飾子 | PascalCase、共通機能はフレームワークの基底クラスに進む | `.Keyboard(rows)`、`.At(uid)` |
| イベント標準フィールド | 共通概念には前綴なし | `interaction_id`、`button_data`、`request_id` |
| イベントプラットフォームフィールド | `{platform}_` 前綴 | `qqbot_event_id`、`telegram_chat_id` |

### 3.2 パラメータと戻り値の規則

- 標準パラメータはすべてのプラットフォームで**同名同義**である。単位/フォーマットは標準文書で明確に定義（例：秒単位のタイムスタンプ、文字列ID）
- 必須パラメータは各プラットフォームの機能の**共通部分**を取る。プラットフォームの強化機能はオプションパラメータとする
- プラットフォームの強制制約（例：QQBot の富媒体は event_id と混ぜて送信できない）はアダプタが自動的に処理/降格し、モジュールには公開しない
- 戻り値 `data` の標準フィールドは全プラットフォームで一貫している。プラットフォームの追加情報は `data` 内のプラットフォーム名前空間フィールドまたは `{platform}_raw` に格納する

## 4. 差異処理モード（アダプタ層）

| モード | 説明 | 例 |
|------|------|------|
| **パラメータマッピング** | 標準パラメータ → プラットフォーム固有パラメータ | `delete_message(message_id)` → TG `deleteMessage(chat_id, message_id)`（chat_idの登録表による補完） |
| **構造変換** | 標準セグメント → プラットフォーム固有構造 | `keyboard` セグメント → `inline_keyboard` / buttons / QQBot keyboard |
| **アクションマッピング** | 標準アクション名 → プラットフォームアクション名 | `get_self_info` → `get_login_info`（OB11） |
| **フィールド標準化** | プラットフォームのレスポンス → 標準フィールド | `getMe()` → `{user_id, user_name, user_displayname}` |
| **合成識別子** | プラットフォームに固有識別子がない場合、一意なIDを生成 | TG join request にIDがない → `tjr_{chat}_{user}_{date}` |
| **機能の降格** | 対応していない場合、テキスト化/返却値10002 | Kook に keyboard がない → alt_message でテキスト化；`get_friend_list` → 10002 |
| **正規化** | プラットフォームの不純なデータ → 標準フォーマット | QQBot @マーク openid → bot_id（名前の正規化） |
| **二重軌道互換** | 標準構造とプラットフォーム固有構造の両方を受け入れる | `.Keyboard()` は一般的な rows またはプラットフォーム固有構造を受け入れる |

## 5. 交互コンポーネント標準

### 5.1 コンポーネント一覧とステータス

| コンポーネント | 標準段 type | 状態 | 対応プラットフォーム |
|------|------------|------|-----------|
| ボタン/キーボード（keyboard） | `keyboard` | ✅ 標準化済み | Telegram / 云湖 / QQBot |
| ドロップダウン選択（select） | `select` | 📋 予約済み（構造は§5.4参照） | Discord / Telegram(bot) |
| カード（card） | `card` | 📋 予約済み（§5.5参照） | Kook / 云湖(html) |
| モーダル（modal） | `modal` | 📋 予約済み | Discord |

> 修飾子の階層規約：汎用的なインタラクティブコンポーネントの Send 修飾子は**アダプタの Send クラスが実装**する（フレームワークの基底クラスには内蔵しない）。命名は §5.2 の規約に従い、引数は本文書の標準構造に従う。

### 5.2 keyboard ボタン/インラインキーボード

#### メッセージ段構造（送信方向）

標準 `keyboard` 段 = `rows` 二次元配列。各ボタンは `{"label": "表示テキスト", "type": "callback" | "link", "data": "コールバックデータまたは遷移先アドレス"}`。プラットフォーム固有のオプションフィールドも許容（アダプタは機能に応じてマッピングまたは無視する）。

> **構造定義の権威**：完全なメッセージ段の JSON、フィールド表、およびフィールドの意味は [イベント変換標準 §4.1.1 keyboard ボタン/インラインキーボード段](event-conversion.md#411-keyboard-ボタン内联键盘段跨平台通用) を参照。本節では繰り返さない。

#### 各プラットフォームのマッピング対照

| プラットフォーム | 標準段 → ネイティブ構造 | ネイティブ構造の参考 |
|------|------------------|-------------|
| Telegram | `reply_markup.inline_keyboard`：`[{text, callback_data \| url}]` | callback→`callback_data`（≤64バイト）、link→`url` |
| 云湖 | `content.buttons`：`[{label, action_type}]` | callback→`action_type:2` + `action` + `value`、link→`action_type:1` + `url` |
| QQBot | `keyboard.content.rows`：`[{label, type, data}]` | callback→`type:2` + `data`、link→`type:0` + `data`（メッセージは markdown 型でなければならない） |
| Kook | カード `action-group` モジュール：`[{type, text, value, click}]` | callback→`click:return` + `value`、link→`click:link` + `url` |
| Discord | `components[].components`：`[{label, style, custom_id \| url}]` | callback→`style:1` + `custom_id`、link→`style:5` + `url` |

#### Send 修飾子（各アダプタの Send クラスで実装）

汎用的な修飾子は**各アダプタが自分の Send クラスで実装**する（フレームワークの基底クラスは変更しない）：

- `.Keyboard(rows)`：標準命名。§5.2 の汎用 rows 構造を受ける。内部で標準 `keyboard` メッセージ段（または直接プラットフォームのネイティブ構造に変換）を生成し、`Raw_ob12` で統一処理する。
- `.Buttons(rows)`：オプションの別名。動作は同一。
- **後方互換性**：プラットフォームのネイティブ構造を検出した場合は直接透過する（エラーを発生させず、変換しない）。
- プラットフォームのネイティブ拡張段（例：`telegram_inline_keyboard`）は透過し、影響を受けない。

```python
# 同じコード、任意のプラットフォーム（各アダプタが修飾子と変換を提供）
rows = [[{"label": "いいね", "type": "callback", "data": "like:1"},
         {"label": "ホーム", "type": "link", "data": "https://example.com"}]]
await adapter.Send.To("group", gid).Keyboard(rows).Text("選択してください")
```

> アダプタの互換性リスト：QQBot / Telegram / 云湖 は実装済み（修飾子 + 標準段変換）；新規アダプタは本文書に従って実装すればよい（§7 Checklist参照）。

### 5.3 インタラクティブコールバックイベント（ボタンクリック後）

ユーザーがボタンをクリックした後、プラットフォームが送信するイベントは**必ず**以下の標準フィールドを提供する必要がある（detail_type はプラットフォームの命名を保持する）：

| 標準フィールド | 型 | 必須 | 説明 |
|---------|------|------|------|
| `interaction_id` | str | はい | 今回のインタラクションのID（応答に使用可能、例：回転/通知） |
| `button_data` | str | はい | ボタンが返すデータ（§5.2 の `data`） |
| `button_label` | str | いいえ | ボタンの表示テキスト |
| `user_id` | str | はい | クリックしたユーザー |
| `message_id` | str | いいえ | ボタンが含まれるメッセージ |
| `group_id` / `channel_id` | str | いいえ | ソース会話 |

**detail_type 約定**：各プラットフォームの既存命名を保持する（`qqbot_interaction` / `telegram_callback_query` / `yunhu_a2ui_button` など）。ただし**標準フィールドは必須**であるため、モジュールは `event.get("button_data")` で跨プラットフォームに渡って値を取得できる。

**Event 拡張メソッドの提案**（アダプタの EventMixin が提供）：

```python
def get_button_data(self) -> str: ...     # button_data
def get_interaction_id(self) -> str: ...  # interaction_id
```

**インタラクションへの応答**（プラットフォームの能力に応じて）：`adapter.reply_interaction(interaction_id, code=0)`（QQBot）/ `answerCallbackQuery`（Telegram）など、プラットフォームのメソッド族に従い、統一は強制しない。

#### 各プラットフォームのコールバックイベントマッピング

| プラットフォーム | ネイティブイベント | detail_type | interaction_id のソース | button_data のソース |
|------|---------|-------------|--------------------|-----------------|
| Telegram | `callback_query` | `telegram_callback_query`（notice） | `callback_query.id` | `callback_query.data` |
| 云湖 | ボタンクリックイベント | `yunhu_button_click` / `yunhu_a2ui_button` | `buttonId` / `sourceComponentId` | `value` / `actionName` |
| QQBot | `INTERACTION_CREATE` | `qqbot_interaction` | `interaction.id` | `data.resolved.button_data` |
| Kook | ボタンクリックイベント | `kook_button_click` | `msg_id`+`value` | `value` |
| Discord | `INTERACTION_CREATE` | `discord_interaction` | `interaction.id` | `data.custom_id` |

### 5.4 select ドロップダウン選択（予約）

```json
{
  "type": "select",
  "data": {
    "placeholder": "選択してください",
    "options": [
      {"label": "選択肢A", "data": "opt:A"},
      {"label": "選択肢B", "data": "opt:B"}
    ],
    "min_values": 1,
    "max_values": 1
  }
}
```

コールバックイベントは §5.3 のフィールドを再利用する（`button_data` = 選択された `data`、複数選択時は JSON 配列）。最初に実装するプラットフォーム：Discord（select menu）、Telegram（keyboard 切り替え）。実装していないプラットフォームは、この段を `alt_message` に降格してテキストリストとして表示する。

### 5.5 card カード（予約、標準化を保留）

カードの構造は非常に多様（Kook の全機能カードモジュール vs 云湖 html vs QQ markdown+keyboard）、強制的な標準化は保留。提案：

- フルテキストのカードは `text` + `keyboard` の組み合わせで表現する（多くの場面で十分）
- プラットフォームの全機能カードは `{platform}_card` 拡張段（例：`kook_card`）を使用し続ける
- 2つ以上のプラットフォームで同構造のカード機能が登場した際に、再評価して標準化を検討

---

## 6. 今後の候補（Roadmap）

以下の機能は、2 つ以上のプラットフォームで既に存在するか、または予定されており、優先順位に従って標準化を進めています。

| 候補 | 涉及プラットフォーム | 優先度 | 備考 |
|------|---------|--------|------|
| select ドロップダウン選択 | Discord / Telegram | 高 | 構造の草案は §5.4 を参照 |
| 意見表明/絵文字応答（reactions） | QQBot / Telegram / Discord / Kook | 高 | 動作とイベントの両側の標準化 |
| 群管理操作（ミュート/キック/承認） | QQBot / 云湖 / OB11 | 高 | 多数はプラットフォームの操作として実装済み、標準的な署名の抽出を待つ |
| 公告/看板 | 云湖 / Telegram / Discord | 中 | `set_announcement` 類の操作 |
| ファイルリソースモデル（file_id 二段式） | 各プラットフォーム | 低（保留） | 送信直送 `SendDSL.File(file, filename)` は既に標準的な経路（URL/パス/バイト直送、[送信メソッド規格 §2.1](send-method-spec.md) 参照）；file_id モデルは後端が天然に備えている場合にのみ透過的に使用、[API 動作標準 §3.5](api-action-spec.md) 参照 |
| カード card | Kook / 云湖 | 低 | 構造の差が大きい、§5.5 を参照 |
| フォーム form | 云湖 | 低 | プラットフォーム固有、`{platform}_` プレフィックスを保持 |
| メディア変換/サイズ検出 | 各プラットフォーム | 低 | アダプタ内部での実装、外部には標準化しない |

## 7. 新しいアダプター開発者の標準チェックリスト

新しいアダプターを開発する際は、以下のチェックリストを確認して実装してください（★ は必須、その他の項目は推奨）：

- [ ] ★ イベントを OneBot12 標準構造に変換し、`BaseConverter` を継承する
- [ ] ★ 標準メッセージセグメントの送受信をサポート（text/image/mention/reply/keyboard…；メディアセグメントは [送信方法規格 §2.1](send-method-spec.md) の形態分類と階層処理に従う）
- [ ] ★ `Raw_ob12` を実装する（標準セグメント → プラットフォーム構造の変換；標準 `keyboard` セグメントは必ず実装）
- [ ] ★ 標準レスポンス構造を返す（`make_response`/`make_error`）
- [ ] ★ 複数アカウント対応：`AccountConfigClass(BotAccountConfig)` + `_resolve_account`
- [ ] ★ Send クラスは `BaseAdapter.Send` を継承し、`_apply_modifiers`/`send_context` を使用する
- [ ] ☆ Api DSL：標準アクションをプラットフォームAPIにマッピングする（API 動作標準を参照）
- [ ] ☆ Request DSL：リクエストイベントには `request_id` と `accept/reject` を含める
- [ ] ☆ インタラクティブコンポーネント：`keyboard` セグメントの変換 + インタラクティブコールバックの標準フィールド + `.Keyboard()`/.Buttons()` 修飾子（アダプターの Send クラスで実装）
- [ ] ☆ EventMixin：`get_raw_event()` / `get_button_data()` などのプラットフォーム拡張メソッド
- [ ] ☆ ライフサイクルタスクは `runtime.spawn_background` を使用する
- [ ] ☆ 設定読み込みは `self.cfg` を使用する
- [ ] ☆ フレームワークのソフト依存：ErisPulse のハード依存を宣言せず、ランタイムでのバージョン検証を行う
- [ ] ☆ i18n：設定フィールドとログの多言語対応
- [ ] ☆ platform-guide プラットフォームドキュメント + アダプターリポジトリの platform-features.md

## 8. 関連ドキュメント

- 各分野の標準については §2 標準マップを参照してください。
- フレームワークに内蔵されているアダプターは、参考実装としてご利用いただけます：QQBot（v5 パターンの全量）、OneBot11（Api DSL マッピング）、雲湖（BaseConverter + Web API 拡張）。