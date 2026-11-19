# アダプター標準化ガイド（総綱）

> [!TIP]
> **この文書をいつ読むべきか**：新しいアダプターを開発する場合や、あるプラットフォーム向けに新しい機能を追加して「標準に取り込むか `{platform}_` 拡張とするか」の判断、命名の付け方、プラットフォーム差異の処理方法を決める必要があるときは、まず本文をお読みください。特定分野の具体的な仕様を調べたいだけであれば、§2 標準マップの該当ドキュメントへ直接ジャンプできます。

このドキュメントは ErisPulse アダプター標準化の**総綱**です：クロスプラットフォーム標準化の原則、標準マップ、差異処理パターン、新機能が標準に入るフローを確立し、**インタラクティブコンポーネント標準**（ボタン/キーボード、ドロップダウン選択など）と**インタラクションコールバックイベント**の完全な定義を示します。アダプター開発者は新機能を実装する際に**標準定義を優先採用**し、モジュール開発者が同一コードで任意のプラットフォームにおいて一貫した体験——命名の一貫性、パラメータの一貫性、戻り値の一貫性——を得られるようにします。

---

## 1. 標準化原則

1. **命名の一貫性**：同一概念はすべてのプラットフォームで同一の命名を使用する（例：取り消しは `delete_message` に統一、ボタンセグメントは `keyboard` に統一）、プラットフォームによって異ならない
2. **パラメータの一貫性**：標準アクション/セグメント/メソッドのパラメータ構造はすべてのプラットフォームで一貫させる。プラットフォーム固有パラメータは**オプションの拡張パラメータ**または**拡張フィールド**として提供し、標準シグネチャを汚染しない
3. **戻り値の一貫性**：すべての API/送信呼び出しは標準レスポンス構造（`status/retcode/data/message_id/message`）を返す。`data` 内の標準フィールド（例：`user_id/user_name`）のセマンティクスは一貫している。プラットフォームの生データは `{platform}_raw` に格納する
4. **拡張は根拠付き**：プラットフォーム固有機能は `{platform}_` 接頭辞で命名する（セグメント：`yunhu_form`、アクション：`yunhu.board`、イベントフィールド：`qqbot_button_id`）、非クロスプラットフォームであることを明確に識別する
5. **差異はアダプター層で吸収**：モジュールコードは標準に向けたプログラミングを行い、プラットフォーム差異はアダプターが変換する（パラメータマッピング、フィールド標準化、機能縮退）。モジュールにプラットフォーム分岐の記述を要求しない
6. **機能縮退でもエラーを出さない**：プラットフォームが標準機能をサポートしていない場合、優雅に縮退する（`retcode=10002` を返す、コンポーネントをテキスト化して `alt_message` に格納する）。例外をスローしてモジュールロジックを中断しない

## 2. 標準マップ

| 分野 | 標準ドキュメント | カバー内容 |
|------|---------|---------|
| イベント変換 | [イベント変換標準](event-conversion.md) | イベント構造、標準メッセージセグメント（text/image/mention/reply/keyboard など）、プラットフォーム拡張セグメント仕様 |
| インタラクティブコンポーネント | **本ドキュメント §5** | ボタン/キーボード、ドロップダウン選択、カード、インタラクションコールバックイベント標準フィールド、デコレーター規約、各プラットフォームマッピング |
| API アクション | [API アクション標準](api-action-spec.md) | OneBot12 標準アクション（ユーザー/グループ/チャンネル/メッセージ管理/メタアクション）の統一インターフェースと `ApiDSL` |
| リクエスト操作 | [リクエスト操作仕様](request-action-spec.md) | リクエストイベントフィールド（request_id）、Request DSL（approve/reject）とリクエストタイプのコンテキスト保持 |
| 送信メソッド | [送信メソッド仕様](send-method-spec.md) | Send クラスメソッドの命名、パラメータ、デコレーター、逆変換（OB12→プラットフォーム） |
| セッションタイプ | [セッションタイプ標準](session-types.md) | user/group/channel/guild/dms などのセッションタイプ定義とマッピング |
| API レスポンス | [API レスポンス標準](api-response.md) | 標準レスポンス構造と retcode 規約 |

## 3. 標準化ワークフロー（新機能がどのように標準に入るか）

```
プラットフォーム固有機能（{platform}_ 接頭辞）
        │  ≥2 のプラットフォームで同種の機能が出現
        ▼
共通性の識別（汎用概念とパラメータサブセットの抽出）
        │
        ▼
標準ドラフト（命名 + パラメータ + 戻り値 + 各プラットフォームマッピング表）
        │  レビュー
        ▼
本総綱/各分野の標準ドキュメントに記載 + フレームワーク基底クラス/アダプターによる互換レイヤー実装
        │
        ▼
標準セグメント/アクション（接頭辞なし）——モジュールはクロスプラットフォームで使用可能
```

**例**：ボタンは当初各プラットフォームで独立実装（`telegram_inline_keyboard` / 云湖 buttons / QQBot keyboard）→ ≥3 のプラットフォームで出現 → 汎用構造を抽出（`label/type/data` + rows）→ 標準 `keyboard` セグメントを公開 → 各アダプターが互換レイヤーを実装（デコレーターが汎用構造を受け入れる + 標準セグメント変換 + ネイティブセグメントの透過）。

### 3.1 命名規則

| 対象 | 規則 | 例 |
|------|------|------|
| 標準メッセージセグメント | 小文字、汎用概念は接頭辞なし | `keyboard`、`select`、`mention` |
| プラットフォーム拡張セグメント | `{platform}_` 接頭辞 | `telegram_sticker`、`yunhu_form` |
| 標準 API アクション | OB12 標準名（snake_case） | `get_group_info`、`delete_message` |
| プラットフォーム拡張アクション | `{platform}.` 接頭辞またはプロトコル汎用名 | `yunhu.board`、`send_poke`（OB11 拡張） |
| デコレーター | PascalCase、汎用機能はフレームワーク基底クラスへ | `.Keyboard(rows)`、`.At(uid)` |
| イベント標準フィールド | 汎用概念は接頭辞なし | `interaction_id`、`button_data`、`request_id` |
| イベントプラットフォームフィールド | `{platform}_` 接頭辞 | `qqbot_event_id`、`telegram_chat_id` |

### 3.2 パラメータと戻り値の規則

- 標準パラメータはすべてのプラットフォームで**同名同義**。単位/フォーマットは標準ドキュメントで明確化する（例：秒単位のタイムスタンプ、文字列 ID）
- 必須パラメータは各プラットフォーム機能の**共通サブセット**を採る。プラットフォーム拡張機能はオプションパラメータとする
- プラットフォームの強い制約（例：QQBot のリッチメディアは event_id と混在送信できない）はアダプターが自動処理/縮退し、モジュールに露出させない
- 戻り値 `data` の標準フィールドは全プラットフォームで一貫。プラットフォームの追加情報は `data` 内のプラットフォーム命名フィールドまたは `{platform}_raw` に格納する

## 4. 差異処理パターン（アダプター層）

| パターン | 説明 | 例 |
|------|------|------|
| **パラメータマッピング** | 標準パラメータ → プラットフォームネイティブパラメータ | `delete_message(message_id)` → TG `deleteMessage(chat_id, message_id)`（登録テーブルで chat_id を補完） |
| **構造変換** | 標準セグメント → プラットフォームネイティブ構造 | `keyboard` セグメント → `inline_keyboard` / buttons / QQBot keyboard |
| **アクションマッピング** | 標準アクション名 → プラットフォームアクション名 | `get_self_info` → `get_login_info`（OB11） |
| **フィールド標準化** | プラットフォームレスポンス → 標準フィールド | `getMe()` → `{user_id, user_name, user_displayname}` |
| **合成識別子** | プラットフォームにネイティブ識別子がない場合に決定論的 ID を生成 | TG join request に ID なし → `tjr_{chat}_{user}_{date}` |
| **機能縮退** | 非対応時はテキスト化/10002 を返す | Kook に keyboard なし → alt_message でテキスト化。`get_friend_list` → 10002 |
| **正規化** | プラットフォームの不整形データ → 標準フォーマット | QQBot @マーカーの openid → bot_id（名称の正規化） |
| **デュアルトラック互換** | 標準構造とプラットフォームネイティブ構造の両方を受け入れる | `.Keyboard()` は汎用 rows またはネイティブ構造を受け入れる |

---

## 5. インタラクティブコンポーネント標準

### 5.1 コンポーネント一覧と状態

| コンポーネント | 標準セグメント type | 状態 | サポート済みプラットフォーム |
|------|------------|------|-----------|
| ボタン/キーボード（keyboard） | `keyboard` | ✅ 標準化済み | Telegram / 云湖 / QQBot |
| ドロップダウン選択（select） | `select` | 📋 予約（構造は §5.4 参照） | Discord / Telegram(bot) |
| カード（card） | `card` | 📋 予約（§5.5 参照） | Kook / 云湖 |
| モーダル（modal） | `modal` | 📋 予約 | Discord |

> デコレーターの階層規約：汎用インタラクティブコンポーネントの Send デコレーターは**アダプターの Send クラスで実装**する（フレームワーク基底クラスには組み込まない）。命名は §5.2 の規約に従い、パラメータは本ドキュメントの標準構造に従う。

### 5.2 keyboard ボタン/インラインキーボード

#### メッセージセグメント構造（送信方向）

標準 `keyboard` セグメント = `rows` の二次元配列。各ボタンは
`{"label": "表示テキスト", "type": "callback" | "link", "data": "コールバックデータまたはリンク先"}`。
プラットフォーム固有のオプションフィールドも許可される（アダプターは能力に応じてマッピングまたは無視する）。

> **構造定義の一次ソース**：完全なメッセージセグメント JSON、フィールド表とフィールドのセマンティクスは
> [イベント変換標準 §4.1.1 keyboard ボタン/インラインキーボードセグメント](event-conversion.md#411-keyboard-ボタンインラインキーボードセグメントクロスプラットフォーム共通) を参照。
> 本節では繰り返し記載しない。

#### 各プラットフォームマッピング対照

| プラットフォーム | 標準セグメント → ネイティブ構造 | ネイティブ構造リファレンス |
|------|------------------|-------------|
| Telegram | `reply_markup.inline_keyboard`：`[{text, callback_data \| url}]` | callback→`callback_data`（≤64 バイト）、link→`url` |
| 云湖 | `content.buttons`：`[{label, action_type}]` | callback→`action_type:2` + `action` + `value`、link→`action_type:1` + `url` |
| QQBot | `keyboard.content.rows`：`[{label, type, data}]` | callback→`type:2` + `data`、link→`type:0` + `data`（メッセージは markdown タイプである必要あり） |
| Kook | カード `action-group` モジュール：`[{type, text, value, click}]` | callback→`click:return` + `value`、link→`click:link` + `url` |
| Discord | `components[].components`：`[{label, style, custom_id \| url}]` | callback→`style:1` + `custom_id`、link→`style:5` + `url` |

#### Send デコレーター（各アダプターの Send クラスが実装）

汎用デコレーターは**各アダプターが自分の Send クラス内で実装**する（フレームワーク基底クラスは変更しない）：

- `.Keyboard(rows)`：標準命名。§5.2 の汎用 rows 構造を受け入れ、内部的に標準 `keyboard`
  メッセージセグメントを生成する（またはプラットフォームネイティブ構造に直接変換）。`Raw_ob12` が統一的に処理する
- `.Buttons(rows)`：オプションのセマンティックエイリアス。動作は同一
- **後方互換**：プラットフォームネイティブ構造を検出した場合はそのまま透過（エラーなし、変換なし）
- プラットフォームネイティブ拡張セグメント（例：`telegram_inline_keyboard`）は引き続き透過され、影響を受けない

```python
# 同じコードで任意のプラットフォーム（各アダプターがデコレーターと変換を提供）
rows = [[{"label": "いいね", "type": "callback", "data": "like:1"},
         {"label": "ホーム", "type": "link", "data": "https://example.com"}]]
await adapter.Send.To("group", gid).Keyboard(rows).Text("選択してください")
```

> アダプター互換リスト：QQBot / Telegram / 云湖 は実装済み（デコレーター + 標準セグメント変換）。
> 新しいアダプターは本ドキュメントに従って実装すればよい（§7 Checklist 参照）。

### 5.3 インタラクションコールバックイベント（ボタンクリック後）

ユーザーがボタンをクリックした後、プラットフォームがプッシュするイベントは以下の標準フィールドを**必ず**提供しなければならない（detail_type はプラットフォーム命名を保持可能）：

| 標準フィールド | 型 | 必須 | 説明 |
|---------|------|------|------|
| `interaction_id` | str | はい | 今回のインタラクションの ID（応答に使用可能、例：ローディング表示/トースト） |
| `button_data` | str | はい | ボタンの返送データ（§5.2 の `data` に相当） |
| `button_label` | str | いいえ | ボタンの表示テキスト |
| `user_id` | str | はい | クリックしたユーザー |
| `message_id` | str | いいえ | ボタンがあるメッセージ |
| `group_id` / `channel_id` | str | いいえ | 送信元セッション |

**detail_type の規約**：各プラットフォームの既存命名を保持する（`qqbot_interaction` / `telegram_callback_query` /
`yunhu_a2ui_button` など）が、**標準フィールドは必ず揃えておくこと**——モジュールは `event.get("button_data")` でクロスプラットフォームに値を取得できる。

**Event 拡張メソッドの提案**（アダプターの EventMixin が提供）：

```python
def get_button_data(self) -> str: ...     # button_data
def get_interaction_id(self) -> str: ...  # interaction_id
```

**インタラクションへの応答**（プラットフォームの機能に応じて）：`adapter.reply_interaction(interaction_id, code=0)`（QQBot）/
`answerCallbackQuery`（Telegram）など。命名はプラットフォームのメソッド群に従い、統一は強制しない。

#### 各プラットフォームのコールバックイベントマッピング

| プラットフォーム | ネイティブイベント | detail_type | interaction_id の取得元 | button_data の取得元 |
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
      {"label": "オプションA", "data": "opt:A"},
      {"label": "オプションB", "data": "opt:B"}
    ],
    "min_values": 1,
    "max_values": 1
  }
}
```

コールバックイベントは §5.3 のフィールドを再利用する（`button_data` = 選択された `data`、複数選択時は JSON 配列）。
最初の実装プラットフォーム：Discord（select menu）、Telegram（keyboard 切り替え）。未実装プラットフォームがこのセグメントを
受け取った場合は `alt_message` 内でテキストリストに縮退させるべきである。

### 5.5 card カード（予約、標準化は当面保留）

カードの構造は差異が極めて大きく（Kook のフル機能カードモジュール vs 云湖 html vs QQ markdown+keyboard）、
当面は強い標準化を行わない。推奨事項：

- リッチテキストカードは `text` + `keyboard` の組み合わせで表現する（ほとんどのシナリオで十分）
- プラットフォームのフル機能カードは引き続き `{platform}_card` 拡張セグメントを使用する（例：`kook_card`）
- ≥2 のプラットフォームで同種構造のカード機能が出現した時点でレビューして昇格を検討する

---

## 6. 将来の候補（Roadmap）

以下の機能はすでに ≥2 のプラットフォームで出現しているか、出現が見込まれるものであり、優先度に応じて標準化を推進する：

| 候補 | 関連プラットフォーム | 優先度 | 備考 |
|------|---------|--------|------|
| select ドロップダウン選択 | Discord / Telegram | 高 | 構造ドラフトは §5.4 参照 |
| リアクション/絵文字リアクション（reactions） | QQBot / Telegram / Discord / Kook | 高 | アクション + イベントの両側を標準化 |
| グループ管理アクション（ミュート/キック/承認） | QQBot / 云湖 / OB11 | 高 | 多くはすでにプラットフォームアクションとして実装済み、標準シグネチャの抽出待ち |
| アナウンス/掲示板 | 云湖 / Telegram / Discord | 中 | `set_announcement` 系アクション |
| ファイルリソースモデル（file_id 二段式） | 各プラットフォーム | 低（一時保留） | 送信は `SendDSL.File(file, filename)` による直送がすでに標準パス（URL/パス/bytes の直送、[送信メソッド仕様 §2.1](send-method-spec.md) 参照）。file_id モデルはバックエンドが本来備えている場合にのみ透過、[API アクション標準 §3.5](api-action-spec.md) 参照 |
| カード card | Kook / 云湖 | 低 | 構造差異が大きい、§5.5 参照 |
| フォーム form | 云湖 | 低 | プラットフォーム固有、`{platform}_` 接頭辞を保持 |
| メディアのトランスコード/サイズ検出 | 各プラットフォーム | 低 | アダプター内部実装、対外的な標準化はしない |

## 7. 新規アダプター開発者向け標準 Checklist

新しいアダプターを開発する際は、このチェックリストに従って実装する（★ は必須、その他は推奨）：

- [ ] ★ イベントを OneBot12 標準構造に変換、`BaseConverter` を継承
- [ ] ★ 標準メッセージセグメントの送受信サポート（text/image/mention/reply/keyboard…。メディアセグメントは
      [送信メソッド仕様 §2.1](send-method-spec.md) の形態等級分類と縮退ステップに従って処理）
- [ ] ★ `Raw_ob12` を実装（標準セグメント → プラットフォーム構造変換を含む。標準 `keyboard` セグメントは必須）
- [ ] ★ 標準レスポンス構造を返す（`make_response`/`make_error`）
- [ ] ★ マルチアカウント：`AccountConfigClass(BotAccountConfig)` + アカウント解決（アカウント名 / `bot_id` マッチング）
- [ ] ★ Send クラスは `BaseAdapter.Send` を継承し、`_apply_modifiers`/`send_context` を使用
- [ ] ☆ Api DSL：標準アクションをプラットフォーム API にマッピング（API アクション標準参照）
- [ ] ☆ Request DSL：リクエストイベントに `request_id` + `accept/reject` を含む（異種エンドポイントプラットフォームはリクエストタイプのコンテキスト保持を含む）
- [ ] ☆ インタラクティブコンポーネント：`keyboard` セグメント変換 + インタラクションコールバック標準フィールド + `.Keyboard()`/`.Buttons()` デコレーター（アダプターの Send クラスが実装）
- [ ] ☆ EventMixin：`get_raw_event()` / `get_button_data()` などのプラットフォーム拡張メソッド
- [ ] ☆ ライフサイクルタスクは `runtime.spawn_background` を使用
- [ ] ☆ 設定の読み取りは `self.cfg` を使用
- [ ] ☆ フレームワークのソフト依存：ErisPulse のハード依存を宣言しない + 実行時バージョン検出
- [ ] ☆ i18n：設定フィールドとログの多言語化
- [ ] ☆ platform-guide プラットフォームドキュメント + アダプターリポジトリの platform-features.md

## 8. 関連ドキュメント

- 各分野の標準は §2 標準マップを参照
- フレームワーク内蔵アダプターはリファレンス実装として参照可能：QQBot（v5 パラダイム全体）、OneBot11（Api DSL マッピング）、云湖（BaseConverter + Web API 拡張）