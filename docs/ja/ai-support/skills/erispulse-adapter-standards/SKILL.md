---
name: erispulse-adapter-standards
description: "适用于：实现/评审适配器时需要对照的硬性技术规范。覆盖场景：**このドキュメントを読むタイミング**：新しいアダプターを開発するとき、または特定のプラットフォームに新機能を追加する際、"標準に追加するか、`{platform}_` 拡張を用いるか"、命名規則、プラットフォーム間の差異をどのように処理するかを決める必要があるときは、まず本文を読んでください。特定の分野の詳細な規格を調べるだけであれば、§2の標準マップに対応するドキュメントに直接移動してください。**このドキュメントを読むべきケース**：アダプターでプラットフォームのネイティブセッションを標準タイプ（private/group/channel/guild/thread）にマッピングする場合や、モジュールで `Send.To()` にどのターゲットタイプを渡せばよいかわからない場合、`event.reply()` の自動変換を把握したい場合に本ドキュメントを参照してください。不要な場合はスキップしてください。**この文書を読むべきとき**：アダプターでプラットフォームネイティブイベントを OneBot12 標準イベントに変換する際——必須フィールド、メッセージセグメント構造、拡張フィールド命名（`{platform}_` プレフィックス）、セッションタイプ推定を確認するときに、この文書を参照してください。不要な場合は読み飛ばしてください。**このドキュメントを読むべきタイミング**: 送信メソッドの実装を行う際、命名規則、メディアパラメータ（URL/パス/bytes）のサポート、`Raw_ob12` への逆変換、メッセージの転送機能など、本文書を参照してください。必要ない場合はスキップしてください。**このドキュメントを読むべきケース**：アダプタに Api DSL の標準アクション（get_user_info / delete_message など）を実装する場合や、モジュールからこれらの標準アクションをクロスプラットフォームで呼び出す際にパラメータや data フィールドを確認する必要がある場合に、本文を参照してください。必要なければ読み飛ばして構いません。**この記事を読むタイミング**：アダプター内で `call_api` / Send / Request の返り値を実装する際に、返却値の構造と返却コードが ErisPulse の標準に準..."
---

# ErisPulse 适配器技术标准

This skill is auto-built from the ErisPulse documentation.
Repository: https://github.com/ErisPulse/ErisPulse
Source paths are annotated per section; see docs/ in the repository for the latest content.

## 内容大纲

AI 按需读取：只读需要的章节即可，不必全文加载。

- 标准化总纲: 89-98 行
- 1. 標準化原則: 100-107 行
- 2. 標準マップ: 109-119 行
- 3. 標準化ワークフロー（新規機能が標準に取り込まれる方法）: 121-158 行
- 4. 差異処理モード（アダプタ層）: 160-171 行
- 5. 交互コンポーネント標準: 173-283 行
- 6. 今後の候補（Roadmap）: 285-298 行
- 7. 新しいアダプター開発者の標準チェックリスト: 300-318 行
- 8. 関連ドキュメント: 320-323 行
- 会话类型: 325-334 行
- 1. 基本概念: 336-362 行
- 2. 標準セッションタイプ: 364-410 行
- 3. プラットフォームタイプマッピング: 412-451 行
- 4. カスタムタイプの拡張: 453-495 行
- 5. 自動タイプ推論: 497-532 行
- 6. API 使用例: 534-573 行
- 7. コア API リファレンス: 575-623 行
- 8. ユーティリティメソッド: 625-647 行
- 9. ベストプラクティス: 649-669 行
- 10. よくある質問: 671-691 行
- 11. 関連ドキュメント: 693-701 行
- 事件转换: 703-710 行
- 1. コア原則: 712-717 行
- 2. 標準フィールド要件: 719-765 行
- 3. イベント形式の例: 767-842 行
- 4. メッセージセグメント標準: 844-945 行
- 5. 不明なイベントの処理: 947-963 行
- 6. 拡張命名規約: 965-1058 行
- 7. セッションタイプの拡張: 1060-1094 行
- 8. モジュール開発者ガイド: 1096-1209 行
- 9. notice / request イベントのセッションタイプ推定: 1211-1276 行
- 10. 関連ドキュメント: 1278-1289 行
- 发送方法规范: 1291-1300 行
- 0. キーワードの定義: 1302-1310 行
- 1. 標準メソッド命名: 1312-1364 行
- 2. パラメータ規格の詳細: 1366-1534 行
- 3. プラットフォーム固有メソッド命名: 1536-1565 行
- 4. パラメータ名命名規格: 1567-1577 行
- 5. 戻り値規格: 1579-1584 行
- 6. 逆変換規格（OneBot12 → プラットフォーム）: 1586-1768 行
- 7. メソッドの発見: 1770-1791 行
- 9. アダプター開発の注意点: 1793-1799 行
- 10. アダプター実装チェックリスト: 1801-1831 行
- 11. メッセージビルダー（MessageBuilder）—アダプター側の注意点: 1833-1841 行
- 12. 関連ドキュメント: 1843-1851 行
- API 动作规范: 1853-1868 行
- 1. 設計背景: 1870-1882 行
- 2. 三層 DSL 並列構造: 1884-1899 行
- 3. 標準アクション一覧: 1901-2027 行
- 4. 使用方法: 2029-2082 行
- 5. アダプタの実装: 2084-2158 行
- 6. レスポンス形式: 2160-2175 行
- 7. SendDSL / RequestDSL との関係: 2177-2185 行
- 8. アダプタ実装チェックリスト: 2187-2200 行
- 9. 関連ドキュメント: 2202-2212 行
- API 响应规范: 2214-2221 行
- 1. 説明: 2223-2230 行
- 2. 基礎レスポンス構造: 2232-2247 行
- 3. 完全なフィールド仕様: 2249-2318 行
- 4. 実装要件: 2320-2324 行
- 5. 拡張仕様: 2326-2399 行
- 6. 注意事項: 2401-2407 行
- 次のステップ: 2409-2412 行
- 请求动作规范: 2414-2423 行
- 1. 概要: 2425-2458 行
- 2. リクエストイベントのフィールド要件: 2460-2504 行
- 3. Request DSL: 2506-2571 行
- 4. Event の便利メソッド: 2573-2607 行
- 5. アダプター実装要件: 2609-2755 行
- 6. アダプター実装チェックリスト: 2757-2774 行
- 7. エラーコードの拡張: 2776-2791 行
- 8. 関連ドキュメント: 2793-2802 行

## 标准化总纲

> 来源: `docs/ja/standards/standardization-guide.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/ja/standards/standardization-guide.md）

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

## 会话类型

> 来源: `docs/ja/standards/session-types.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/ja/standards/session-types.md）

# ErisPulse セッションタイプ標準

> [!TIP]
> **このドキュメントを読むべきケース**：アダプターでプラットフォームのネイティブセッションを標準タイプ（private/group/channel/guild/thread）にマッピングする場合や、モジュールで `Send.To()` にどのターゲットタイプを渡せばよいかわからない場合、`event.reply()` の自動変換を把握したい場合に本ドキュメントを参照してください。不要な場合はスキップしてください。

このドキュメントでは、受信イベントタイプと送信ターゲットタイプを含む、ErisPulse がサポートするセッションタイプの標準を定義します。

## 1. 基本概念

### 1.1 受信タイプ && 送信タイプ

ErisPulse は2種類のセッションタイプを区別します：

- **受信タイプ（Receive Type）**：受信するイベントの `detail_type` フィールド
- **送信タイプ（Send Type）**：メッセージ送信時に `Send.To()` メソッドへ渡すターゲットタイプ

### 1.2 タイプマッピング関係

```
受信タイプ (detail_type)     送信タイプ (Send.To)
─────────────────        ────────────────
private                 →        user
group                   →        group
channel                 →        channel
guild                   →        guild
thread                  →        thread
user                    →        user
```

**重要なポイント**：
- `private` は受信時のタイプであり、送信時の標準タイプは `user` です
- `group`、`channel`、`guild`、`thread` は受信時と送信時でタイプが同じです
- **推奨パス**：`event.reply()` を直接使用する——タイプ変換とターゲット推論が自動的に行われ、手動処理は不要です（`private` → `user` の自動変換はここで行われます）
- **手動送信時**：送信タイプを直接渡してください（例：`Send.To("user", ...)`）。手動で `Send.To("private", ...)` のように受信タイプを渡しても自動変換されますが、推奨されません（§6.1 参照）

## 2. 標準セッションタイプ

### 2.1 OneBot12 標準タイプ

#### private
- **受信タイプ**：`private`
- **送信タイプ**：`user`
- **説明**：一対一のプライベートチャットメッセージ
- **ID フィールド**：`user_id`
- **対応プラットフォーム**：プライベートチャットをサポートするすべてのプラットフォーム

#### group
- **受信タイプ**：`group`
- **送信タイプ**：`group`
- **説明**：グループチャットメッセージ。各種形式のグループ（Telegram の supergroup など）を含みます
- **ID フィールド**：`group_id`
- **対応プラットフォーム**：グループチャットをサポートするすべてのプラットフォーム

#### user
- **受信タイプ**：`user`
- **送信タイプ**：`user`
- **説明**：ユーザータイプ。一部のプラットフォーム（Telegram など）では、プライベートチャットを private ではなく user として表現します
- **ID フィールド**：`user_id`
- **対応プラットフォーム**：Telegram などのプラットフォーム

### 2.2 ErisPulse 拡張タイプ

#### channel
- **受信タイプ**：`channel`
- **送信タイプ**：`channel`
- **説明**：チャンネルメッセージ。複数ユーザーへのブロードキャスト形式のメッセージをサポートします
- **ID フィールド**：`channel_id`
- **対応プラットフォーム**：Discord、Telegram、Line など

#### guild
- **受信タイプ**：`guild`
- **送信タイプ**：`guild`
- **説明**：サーバー/コミュニティメッセージ。通常、Discord の Guild レベルのイベントに使用されます
- **ID フィールド**：`guild_id`
- **対応プラットフォーム**：Discord など

#### thread
- **受信タイプ**：`thread`
- **送信タイプ**：`thread`
- **説明**：トピック/サブチャンネルメッセージ。コミュニティ内のサブディスカッションに使用されます
- **ID フィールド**：`thread_id`
- **対応プラットフォーム**：Discord Threads、Telegram Topics など

## 3. プラットフォームタイプマッピング

### 3.1 マッピングの原則

アダプターは、プラットフォームのネイティブタイプを ErisPulse 標準タイプにマッピングする役割を担います：

```
プラットフォームネイティブタイプ → ErisPulse 標準タイプ → 送信タイプ
```

### 3.2 一般的なプラットフォームのマッピング例

#### Telegram
```
Telegram タイプ         ErisPulse 受信タイプ   送信タイプ
─────────────────      ────────────────       ───────────
private                private                 user
group                  group                   group
supergroup             group                   group  # group にマッピング
channel                channel                 channel
```

#### Discord
```
Discord タイプ         ErisPulse 受信タイプ   送信タイプ
─────────────────      ────────────────       ───────────
Direct Message         private                user
Text Channel           channel                channel
Guild                  guild                  guild
Thread                 thread                 thread
```

#### OneBot11
```
OneBot11 タイプ       ErisPulse 受信タイプ   送信タイプ
─────────────────      ────────────────       ───────────
private                private                user
group                  group                  group
discuss                group                  group  # group にマッピング
```

## 4. カスタムタイプの拡張

### 4.1 カスタムタイプの登録

アダプターはカスタムセッションタイプを登録できます：

```python
from ErisPulse.Core.Event import register_custom_type

# カスタムタイプの登録
register_custom_type(
    receive_type="my_custom_type",
    send_type="custom",
    id_field="custom_id",
    platform="MyPlatform"
)
```

### 4.2 カスタムタイプの使用

登録後、システムは自動的にこのタイプの変換と推論を処理します：

```python
# 自動推論
receive_type = infer_receive_type(event, platform="MyPlatform")
# 戻り値: "my_custom_type"

# 送信タイプへの変換
send_type = convert_to_send_type(receive_type, platform="MyPlatform")
# 戻り値: "custom"

# 対応する ID の取得
target_id = get_target_id(event, platform="MyPlatform")
# 戻り値: event["custom_id"]
```

### 4.3 カスタムタイプの登録解除

```python
from ErisPulse.Core.Event import unregister_custom_type

unregister_custom_type("my_custom_type", platform="MyPlatform")
```

## 5. 自動タイプ推論

イベントに明示的な `detail_type` フィールドがない場合、システムは存在する ID フィールドに基づいてタイプを自動推論します：

> [!NOTE]
> **2.7.0+ での動作変更**：`detail_type` は、**既知のセッションタイプ**（標準またはカスタム）である場合にのみ直接採用されます。notice/request イベントの `detail_type`（`group_member_increase`、`friend_increase` など）は**セマンティックサブタイプ**でありセッションタイプではないため、代わりに ID フィールドに基づいて正しいセッションタイプが推論されます。

### 5.1 推論の優先順位

```
優先順位（高い順）：
1. group_id     → group
2. channel_id   → channel
3. guild_id     → guild
4. thread_id    → thread
5. user_id      → private
```

### 5.2 使用例

```python
# イベントに group_id のみがある場合
event = {"group_id": "123", "user_id": "456"}
receive_type = infer_receive_type(event)
# 戻り値: "group"（group_id を優先使用）

# イベントに user_id のみがある場合
event = {"user_id": "123"}
receive_type = infer_receive_type(event)
# 戻り値: "private"

# notice イベントの detail_type はセマンティックサブタイプであり、2.7.0+ では ID フィールドから推論されます
event = {"type": "notice", "detail_type": "group_member_increase", "group_id": "123"}
receive_type = infer_receive_type(event)
# 戻り値: "group"（"group_member_increase" ではなく）
```

## 6. API 使用例

### 6.1 メッセージ送信

```python
from ErisPulse import adapter

# ユーザーに送信
await adapter.myplatform.Send.To("user", "123").Text("Hello")

# グループに送信
await adapter.myplatform.Send.To("group", "456").Text("Hello")

# 自動変換 private → user：受信タイプを手動で渡すのは非推奨の書き方です（互換性の問題が生じる可能性があります）
await adapter.myplatform.Send.To("private", "789").Text("Hello")
# 内部で自動変換されます: Send.To("user", "789")
# 推奨される方法：手動送信時は送信タイプ user を直接使用するか、event.reply() で自動変換を利用してください（6.2 参照）
```

### 6.2 イベントへの返信

```python
from ErisPulse.Core.Event import Event

# Event.reply() は自動的にタイプ変換を処理します（推奨パス）
await event.reply("返信内容")
# 内部で正しい送信タイプが自動的に使用されます（private → user などの変換はここで自動的に行われます）
```

### 6.3 コマンド処理

```python
from ErisPulse.Core.Event import command

@command(name="test")
async def handle_test(event):
    # システムが自動的にセッションタイプを処理します
    # group_id か user_id かを手動で判断する必要はありません
    await event.reply("コマンドが正常に実行されました")
```

## 7. コア API リファレンス

### 7.1 タイプ変換

```python
from ErisPulse.Core.Event import convert_to_send_type, convert_to_receive_type

# 受信タイプ → 送信タイプ
convert_to_send_type("private")  # → "user"
convert_to_send_type("group")    # → "group"

# 送信タイプ → 受信タイプ
convert_to_receive_type("user")   # → "private"
convert_to_receive_type("group")  # → "group"
```

### 7.2 ID フィールドの照会

```python
from ErisPulse.Core.Event import get_id_field, get_receive_type

get_id_field("group")    # → "group_id"
get_id_field("private")  # → "user_id"

get_receive_type("group_id")  # → "group"
get_receive_type("user_id")   # → "private"
```

### 7.3 ワンステップで送信情報を取得

```python
from ErisPulse.Core.Event import get_send_type_and_target_id

event = {"detail_type": "private", "user_id": "123"}
send_type, target_id = get_send_type_and_target_id(event)
# send_type = "user", target_id = "123"

# Send.To() に直接使用
await adapter.Send.To(send_type, target_id).Text("Hello")
```

### 7.4 ターゲット ID の取得

```python
from ErisPulse.Core.Event import get_target_id

event = {"detail_type": "group", "group_id": "456"}
get_target_id(event)  # → "456"
```

## 8. ユーティリティメソッド

```python
from ErisPulse.Core.Event import (
    is_standard_type,
    is_valid_send_type,
    get_standard_types,
    get_send_types,
    clear_custom_types,
)

is_standard_type("private")     # True
is_standard_type("custom_type") # False

is_valid_send_type("user")      # True
is_valid_send_type("invalid")   # False

get_standard_types()  # {"private", "group", "channel", "guild", "thread", "user"}
get_send_types()      # {"user", "group", "channel", "guild", "thread"}

clear_custom_types()                # すべてクリア
clear_custom_types(platform="discord")  # 指定したプラットフォームのみクリア
```

## 9. ベストプラクティス

### 7.1 アダプター開発者

1. **標準マッピングを使用**：新しいタイプを作成するのではなく、可能な限り標準タイプにマッピングしてください
2. **正しい変換**：受信タイプと送信タイプのマッピング関係が正しいことを確認してください
3. **元データの保持**：`{platform}_raw` に元のイベントタイプを保持してください
4. **ドキュメントでの説明**：アダプターのドキュメントでタイプマッピング関係を説明してください

### 7.2 モジュール開発者

1. **ユーティリティメソッドを使用**：`get_send_type_and_target_id()` などのユーティリティメソッドを使用してください
2. **ハードコーディングを避ける**：`if group_id else "private"` のようなコードを書かないでください
3. **すべてのタイプを考慮**：コードは private/group だけでなく、すべての標準タイプをサポートする必要があります
4. **柔軟な設計**：フィールドに直接アクセスするのではなく、イベントラッパーのメソッドを使用してください

### 7.3 タイプ推論

- **detail_type を優先使用**：明示的なフィールドがある場合は推論を行いません
- **推論の適切な使用**：明示的なタイプがない場合にのみ使用してください
- **優先順位に注意**：推論の優先順位を理解し、予期しない結果を避けてください

## 10. よくある質問

### Q1: 送信時に private を user に変換するのはなぜですか？

A: これは OneBot12 標準の要件です。`private` は受信時の概念であり、送信時には `user` を使用する方がセマンティクスに適しています。

### Q2: 新しいセッションタイプをサポートするには？

A: `register_custom_type()` でカスタムタイプを登録するか、標準タイプの `channel`、`guild` などを直接使用してください。

### Q3: イベントに detail_type がない場合は？

A: システムは存在する ID フィールドに基づいて自動的に推論します。優先順位は group > channel > guild > thread > user です。

### Q4: アダプターは Telegram の supergroup をどのようにマッピングしますか？

A: アダプターの変換ロジックで、`supergroup` を標準の `group` タイプにマッピングしてください。

### Q5: メールなどの特殊なプラットフォームはどのように処理しますか？

A: 汎用性のないタイプやプラットフォーム固有のタイプについては、`{platform}_raw` と `{platform}_raw_type` を使用して元データを保持し、アダプター側で処理してください。

## 11. 関連ドキュメント

**アダプター向け（マッピングと変換）**：
- [イベント変換標準](event-conversion.md) - 完全なイベント変換仕様
- [送信メソッド仕様](send-method-spec.md) - Send クラスのメソッド命名とパラメータ仕様
- [アダプター開発ガイド](../developer-guide/adapters/) - アダプター開発の完全ガイド

**モジュール向け（タイプ変換を手動で処理したくない場合）**：
- `event.reply()` を使用するだけで、タイプ変換とターゲット推論が自動的に行われます。詳細は [Event ラッパークラス解説](../developer-guide/modules/event-wrapper.md) を参照してください

## 事件转换

> 来源: `docs/ja/standards/event-conversion.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/ja/standards/event-conversion.md）

# アダプター標準化変換仕様

> [!TIP]
> **この文書を読むべきとき**：アダプターでプラットフォームネイティブイベントを OneBot12 標準イベントに変換する際——必須フィールド、メッセージセグメント構造、拡張フィールド命名（`{platform}_` プレフィックス）、セッションタイプ推定を確認するときに、この文書を参照してください。不要な場合は読み飛ばしてください。

## 1. コア原則
1. 厳格な互換性：すべての標準フィールドは OneBot12 仕様に完全に準拠しなければならない
2. 明確な拡張：プラットフォーム固有機能には {platform}_ プレフィックスを追加しなければならない（例：yunhu_form）
3. データの完全性：元のイベントデータは {platform}_raw フィールドに保持しなければならず、元のイベントタイプは {platform}_raw_type フィールドに保持しなければならない
4. 時間の統一：すべてのタイムスタンプは 10 桁の Unix タイムスタンプ（秒単位）に変換しなければならない
5. プラットフォームの統一：platform 項目の命名は、ErisPulse に登録した名前/別名と一致しなければならない

## 2. 標準フィールド要件

### 2.1 必須フィールド
| フィールド | 型 | 説明 |
|------|------|------|
| id | string | イベントの一意識別子 |
| time | integer | Unix タイムスタンプ（秒単位） |
| type | string | イベントタイプ |
| detail_type | string | イベントの詳細タイプ（詳細は[セッションタイプ標準](session-types.md)を参照） |
| platform | string | プラットフォーム名 |
| self | object | ボット自身の情報 |
| self.platform | string | プラットフォーム名 |
| self.user_id | string | ボットのユーザー ID |

**detail_type 仕様**：
- ErisPulse 標準セッションタイプを使用しなければならない（詳細は [セッションタイプ標準](session-types.md) を参照）
- サポートされるタイプ：`private`、`group`、`user`、`channel`、`guild`、`thread`
- アダプターは、プラットフォームネイティブタイプを標準タイプへマッピングする責任を負う

### 2.2 メッセージイベントフィールド
| フィールド | 型 | 説明 |
|------|------|------|
| message | array | メッセージセグメント配列 |
| alt_message | string | メッセージセグメントの代替テキスト |
| user_id | string | ユーザー ID |
| user_nickname | string | ユーザーニックネーム（任意） |

### 2.3 通知イベントフィールド
| フィールド | 型 | 説明 |
|------|------|------|
| user_id | string | ユーザー ID |
| user_nickname | string | ユーザーニックネーム（任意） |
| operator_id | string | 操作者 ID（任意） |

### 2.4 リクエストイベントフィールド
| フィールド | 型 | 説明 |
|------|------|------|
| user_id | string | ユーザー ID |
| user_nickname | string | ユーザーニックネーム（任意） |
| comment | string | リクエストの添えメッセージ（任意） |
| request_id | string | リクエスト識別子（**強く推奨**、リクエストの承認/拒否操作に使用） |

**`request_id` フィールドの説明**：
- `request_id` はリクエストイベントの一意の操作識別子であり、`HandleRequest` DSL による承認/拒否操作の実行に使用される
- アダプターはリクエストイベントの変換時に、プラットフォームネイティブのリクエスト識別子をこのフィールドにマッピングすべきである
- プラットフォーム自体にリクエスト ID がない場合、アダプターは一意の識別子を生成すべきである（例：タイムスタンプ＋ユーザー ID に基づくハッシュ）
- `request_id` が欠落している場合、`event.approve()` / `event.reject()` は `ValueError` をスローする

## 3. イベント形式の例

### 3.1 メッセージイベント (message)
```json
{
  "id": "1234567890",
  "time": 1752241223,
  "type": "message",
  "detail_type": "group",
  "platform": "yunhu",
  "self": {
    "platform": "yunhu",
    "user_id": "bot_123"
  },
  "message": [
    {
      "type": "text",
      "data": {
        "text": "抽選 スーパー大賞"
      }
    }
  ],
  "alt_message": "抽選 スーパー大賞",
  "user_id": "user_456",
  "user_nickname": "YingXinche",
  "group_id": "group_789",
  "yunhu_raw": {...},
  "yunhu_raw_type": "message.receive.normal",
  "yunhu_command": {
    "name": "抽選",
    "args": "スーパー大賞"
  }
}
```

### 3.2 通知イベント (notice)
```json
{
  "id": "1234567891",
  "time": 1752241224,
  "type": "notice",
  "detail_type": "group_member_increase",
  "platform": "yunhu",
  "self": {
    "platform": "yunhu",
    "user_id": "bot_123"
  },
  "user_id": "user_456",
  "user_nickname": "YingXinche",
  "group_id": "group_789",
  "operator_id": "",
  "yunhu_raw": {...},
  "yunhu_raw_type": "bot.followed"
}
```

### 3.3 リクエストイベント (request)
```json
{
  "id": "1234567892",
  "time": 1752241225,
  "type": "request",
  "detail_type": "friend",
  "platform": "onebot11",
  "self": {
    "platform": "onebot11",
    "user_id": "bot_123"
  },
  "user_id": "user_456",
  "user_nickname": "YingXinche",
  "comment": "フレンド申請をお願いします",
  "request_id": "req_abc123",
  "onebot11_raw": {...},
  "onebot11_raw_type": "request"
}
```

## 4. メッセージセグメント標準

### 4.1 標準メッセージセグメント

標準メッセージセグメントにプラットフォームプレフィックスは**不要**です。

| タイプ | 説明 | data フィールド |
|------|------|----------|
| `text` | プレーンテキスト | `text: str` |
| `image` | 画像 | `file`, `url: str` |
| `audio` | 音声 | `file`, `url: str` |
| `video` | 動画 | `file`, `url: str` |
| `file` | ファイル | `file`, `url: str`, `filename: str` |
| `mention` | @ユーザー | `user_id: str`, `user_name: str` |
| `reply` | 返信 | `message_id: str` |
| `face` | 絵文字 | `id: str` |
| `location` | 位置情報 | `latitude: float`, `longitude: float` |
| `keyboard` | ボタン/インラインキーボード | `rows: list[list[button]]`（4.1.1 を参照） |

**メディアセグメントの `file` フィールド形式**（送信方向、`image` / `audio` / `video` / `file` 共通）：

| 形態 | 例 | アダプター要件 |
|------|------|-----------|
| HTTP(S) URL | `https://example.com/a.png` | **必須**で受け付ける |
| ローカルファイルパス | `/tmp/a.png`、`C:\tmp\a.png` | **必須**で受け付ける |
| バイナリデータ | `bytes` | **必須**で受け付ける |
| `file://` URI / Base64 / Data URI | `file:///tmp/a.png`、`data:image/png;base64,...` | **推奨**で受け付ける |

> メディア送信プロトコルの全体（形態判定順序、ファイル名導出、能力ダウングレードの段階）については
> [送信メソッド仕様 §2.1](send-method-spec.md#21-媒体消息发送协议image--voice--video--file) を参照してください。

**フィールドの方向セマンティクス**：

- `file`：**送信方向**のコンテンツソース（上述の形態）；**受信方向**では、アダプターがプラットフォームから取得可能な形態を記入する
  （通常はダウンロード可能な URL、または `get_file` 系アクションで利用可能なリソース識別子）
- `url`：受信方向のプラットフォーム返却リンク（アダプターはプラットフォームイベントの変換時に可能な限り記入し、モジュールが直接利用できるようにする）；送信方向では省略可能
- `filename`：`file` セグメントのファイル名（送信方向では任意、省略時はアダプターが
  [送信メソッド仕様 §2.1.3](send-method-spec.md) の導出順序に従って生成；受信方向ではプラットフォームの元のファイル名を記入することが**推奨**される）

```json
{
  "type": "text",
  "data": {
    "text": "Hello World"
  }
}
```

### 4.1.1 keyboard ボタン/インラインキーボードセグメント（クロスプラットフォーム共通）

ボタン/インラインキーボードは複数のプラットフォーム（Telegram / 云湖 / QQBot / Kook / Discord など）に対応機能が存在し、**クロスプラットフォーム共通の概念**であるため、標準メッセージセグメント（プラットフォームプレフィックスなし）として扱われます。アダプターは標準セグメントをプラットフォームネイティブ構造に変換してください。プラットフォームネイティブの拡張セグメント（例：`telegram_inline_keyboard`）は引き続きそのまま透過します。

```json
{
  "type": "keyboard",
  "data": {
    "rows": [
      [
        {"label": "選択肢A", "type": "callback", "data": "vote:A"},
        {"label": "公式サイト",   "type": "link",     "data": "https://example.com"}
      ]
    ]
  }
}
```

**フィールドの説明：**

| フィールド | 型 | 必須 | 説明 |
|------|------|------|------|
| `rows` | 二次元配列 | はい | 各サブ配列が 1 行のボタンに対応 |
| `rows[][].label` | str | はい | ボタンの表示テキスト |
| `rows[][].type` | str | はい | `callback`（クリックでデータを返送）/ `link`（URL へジャンプ） |
| `rows[][].data` | str | はい | コールバックデータ（type=callback）またはジャンプ先アドレス（type=link） |
| `rows[][].*` | Any | いいえ | プラットフォーム固有の任意フィールド（例：`web_app`、`menus`）。アダプターは能力に応じてマッピングまたは無視する |

**アダプター変換リファレンス**（完全なマッピングとインタラクションコールバックイベント標準については [クロスプラットフォームインタラクションコンポーネント標準](standardization-guide.md) を参照）：

| プラットフォーム | 標準セグメント → プラットフォームネイティブ |
|------|------------------|
| Telegram | `inline_keyboard`：`[{text, callback_data \| url}]` |
| 云湖 | `buttons`：`[{label, action_type: 2=コールバック \| 1=ジャンプ, ...}]` |
| QQBot | `keyboard.content.rows`：`[{label, type: 2=コールバック \| 0=ジャンプ, data}]`（markdown タイプのメッセージが必要） |
| Kook | カードの action-group モジュール |
| Discord | components：`action_row` + `buttons`（custom_id/url） |

### 4.2 プラットフォーム拡張メッセージセグメント

プラットフォーム固有のメッセージセグメントにはプラットフォームプレフィックスを追加する必要があります：

```json
// 云湖 - フォーム
{"type": "yunhu_form", "data": {"form_id": "123456", "form_name": "申込フォーム"}}

// Telegram - スタンプ
{"type": "telegram_sticker", "data": {"file_id": "CAACAgIAAxkBAA...", "emoji": "😂"}}
```

**拡張メッセージセグメントの要件**：
1. **data 内部のフィールドにはプレフィックスを付けない**：`{"type": "yunhu_form", "data": {"form_id": "..."}}` とするべきであり、`{"type": "yunhu_form", "data": {"yunhu_form_id": "..."}}` としてはならない
2. **フォールバック手段を提供する**：モジュールは拡張メッセージセグメントを認識できない可能性があるため、アダプターは `alt_message` にテキストによる代替を提供すべきである
3. **ドキュメントの完備**：各拡張メッセージセグメントについて、`type`、`data` の構造および使用シーンをアダプターのドキュメントで説明しなければならない

## 5. 不明なイベントの処理

識別できないイベントタイプについては、警告イベントを生成すべきです：
```json
{
  "id": "1234567893",
  "time": 1752241223,
  "type": "unknown",
  "platform": "yunhu",
  "yunhu_raw": {...},
  "yunhu_raw_type": "unknown",
  "warning": "Unsupported event type: special_event",
  "alt_message": "This event type is not supported by this system."
}
```

---

## 6. 拡張命名規約

### 6.1 フィールド命名

**ルール**：`{platform}_{field_name}`

```
プラットフォームプレフィックス   フィールド名         完全なフィールド名
──────────                   ───────            ──────────
yunhu       command           yunhu_command
telegram    sticker_file_id   telegram_sticker_file_id
onebot11    anonymous         onebot11_anonymous
email       subject           email_subject
```

**要件**：
- `platform` はアダプター登録時のプラットフォーム名と完全に一致しなければならない（大文字小文字を区別）
- `field_name` は `snake_case` 命名を使用する
- ダブルアンダースコア `__` で始まる名前は禁止（Python の予約）
- 標準フィールドと同名にすることは禁止（例：`type`、`time`、`message` など）

### 6.2 メッセージセグメントタイプ命名

**ルール**：`{platform}_{segment_type}`

標準メッセージセグメントタイプ（`text`、`image`、`audio`、`video`、`mention`、`reply` など）にプラットフォームプレフィックスを追加しては**なりません**。プラットフォーム固有のメッセージセグメントタイプのみがプレフィックスを追加する必要があります。

### 6.3 生データフィールド命名

以下のフィールド名は**予約フィールド**であり、すべてのアダプターが従わなければなりません：

| 予約フィールド | 型 | 説明 |
|---------|------|------|
| `{platform}_raw` | `any` | プラットフォーム元イベントデータの完全なコピー |
| `{platform}_raw_type` | `string` | プラットフォーム元イベントタイプの識別子 |

**要件**：
- `{platform}_raw` は元データのディープコピーでなければならず、参照であってはならない
- `{platform}_raw_type` は文字列でなければならず、プラットフォームが数値型を使用している場合でも文字列に変換すること
- これら 2 つのフィールドはすべてのイベントに**存在しなければならない**（取得できない場合は `null` と空文字列 `""`）

### 6.4 プラットフォーム固有フィールドの例

```json
{
  "yunhu_command": {
    "name": "抽選",
    "args": "スーパー大賞"
  },
  "yunhu_form": {
    "form_id": "123456"
  },
  "telegram_sticker": {
    "file_id": "CAACAgIAAxkBAA..."
  }
}
```

### 6.5 ネストした拡張フィールド

拡張フィールドは単純な値でも、ネストしたオブジェクトでもかまいません：

```json
{
  "telegram_chat": {
    "id": 123456,
    "type": "supergroup",
    "title": "My Group"
  },
  "telegram_forward_from": {
    "user_id": "789",
    "user_name": "ForwardUser"
  }
}
```

**ネストフィールドの要件**：
- トップレベルのキーにはプラットフォームプレフィックスを付けなければならない
- ネストした内部フィールドにはプラットフォームプレフィックスを**追加しない**
- ネストの深さは 3 層を超えないことを推奨

### 6.6 `self` フィールドの拡張

`self` オブジェクトの標準必須フィールド（`platform`、`user_id`）は §2.1 を参照してください。以下は ErisPulse が拡張した任意フィールドです：

| フィールド | 型 | 説明 |
|------|------|------|
| `self.user_name` | `string` | ボットのニックネーム |
| `self.avatar` | `string` | ボットのアバター URL |
| `self.account_id` | `string` | マルチアカウントモードにおけるアカウント識別子 |

> **Bot 状態トラッキング**：アダプターは `type: "meta"` イベントを送信することで、フレームワークに Bot の接続状態を通知します。サポートされる `detail_type`：`connect`（オンライン）、`heartbeat`（ハートビート）、`disconnect`（オフライン）。システムはそこから `self` フィールドの Bot メタ情報を自動的に抽出し、状態をトラッキングします。また、通常のイベント内の `self` フィールドからも Bot が自動的に検出されます。詳細は [アダプターシステム API - Bot 状態管理](../api-reference/adapter-system.md) を参照してください。

---

## 7. セッションタイプの拡張

ErisPulse は OneBot12 標準の `private`、`group` をベースに、以下のセッションタイプを拡張しました：

| タイプ | OneBot12 標準 | ErisPulse 拡張 | 説明 |
|------|:-----------:|:------------:|------|
| `private` | ✅ | — | 1対1のプライベートチャット |
| `group` | ✅ | — | グループチャット |
| `user` | — | ✅ | ユーザータイプ（Telegram など） |
| `channel` | — | ✅ | チャンネル（ブロードキャスト型） |
| `guild` | — | ✅ | サーバー/コミュニティ |
| `thread` | — | ✅ | トピック/サブチャンネル |

**アダプターのカスタムタイプ拡張**：

```python
from ErisPulse.Core.Event.session_type import register_custom_type

# アダプター起動時に登録する
register_custom_type(
    receive_type="email",      # 受信イベントにおける detail_type
    send_type="email",         # 送信時のターゲットタイプ
    id_field="email_id",       # 対応する ID フィールド名
    platform="email"           # プラットフォーム識別子
)
```

**カスタムタイプの要件**：
- アダプターの `start()` 時に登録し、`shutdown()` 時に登録解除しなければならない
- `receive_type` は標準タイプと同名にすべきではない
- `id_field` は `{ターゲット}_id` の命名パターンに従うべきである

> セッションタイプの完全な定義とマッピング関係については [セッションタイプ標準](session-types.md) を参照してください。

---

## 8. モジュール開発者ガイド

### 8.1 拡張フィールドへのアクセス

```python
from ErisPulse.Core.Event import message

@message()
async def handle_message(event):
    # 標準フィールドへのアクセス
    text = event.get_text()
    user_id = event.get_user_id()

    # プラットフォーム拡張フィールドへのアクセス - 方法1：直接 get
    yunhu_command = event.get("yunhu_command")

    # プラットフォーム拡張フィールドへのアクセス - 方法2：ドットアクセス（Event ラッパークラス）
    # event.yunhu_command

    # 生データへのアクセス
    raw_data = event.get("yunhu_raw")
    raw_type = event.get_raw_type()

    # プラットフォームの判定
    platform = event.get_platform()
    if platform == "yunhu":
        pass
    elif platform == "telegram":
        pass
```

### 8.2 拡張メッセージセグメントの処理

```python
@message()
async def handle_message(event):
    message_segments = event.get("message", [])

    for segment in message_segments:
        seg_type = segment.get("type")
        seg_data = segment.get("data", {})

        if seg_type == "text":
            text = seg_data["text"]
        elif seg_type.startswith("yunhu_"):
            if seg_type == "yunhu_form":
                form_id = seg_data["form_id"]
        elif seg_type.startswith("telegram_"):
            if seg_type == "telegram_sticker":
                file_id = seg_data["file_id"]
```

### 8.3 ベストプラクティス

1. **標準フィールドを優先して使用する**：拡張フィールドが必ず存在すると仮定しないこと
2. **プラットフォーム判定**：`event.get_platform()` によってプラットフォームを判定し、拡張フィールドの存在有無から推測しないこと
3. **グレースフルデグラデーション**：拡張メッセージセグメントを処理できない場合は、`alt_message` をフォールバックとして使用すること
4. **プレフィックスをハードコードしない**：`platform` 変数を使って動的に連結すること

```python
# ✅ 推奨
platform = event.get_platform()
raw_data = event.get(f"{platform}_raw")

# ❌ 非推奨
raw_data = event.get("yunhu_raw")
```

### 8.4 リクエストイベントの処理

モジュール開発者は `event.approve()` および `event.reject()` を通じてリクエストイベントに対する操作を行うことができます：

```python
from ErisPulse.Core.Event import request

# フレンドリクエスト：自動承認
@request.on_friend_request()
async def handle_friend_request(event):
    user_name = event.get_user_nickname() or event.get_user_id()
    comment = event.get_comment()
    
    # リクエストを承認
    result = await event.approve()
    if result.get("status") == "ok":
        print(f"{user_name} のフレンドリクエストを承認しました")
    else:
        print(f"フレンドリクエストの承認に失敗しました: {result.get('message')}")

# グループ招待：条件に応じて判断
@request.on_group_request()
async def handle_group_request(event):
    comment = event.get_comment()
    
    # リクエストを拒否
    result = await event.reject(comment="当分の間、新しいグループに参加しません")
```

**アダプターを通じた直接操作**（イベントハンドラー以外のシーンに適用）：

```python
from ErisPulse import adapter

# request_id による直接操作
await adapter.myplatform.Request("req_abc123").accept()
await adapter.myplatform.Request("req_abc123").reject()

# Bot アカウントを指定して操作
await adapter.myplatform.Request("req_abc123").Using("bot1").accept()

# 備考を添える
await adapter.myplatform.Request("req_abc123").accept(comment="ようこそ")
```

---

## 9. notice / request イベントのセッションタイプ推定

### 9.1 問題の背景

notice イベントと request イベントの `detail_type` は**セマンティックサブタイプ**（例：`group_member_increase`、`friend_increase`）であり、セッションタイプ（例：`group`、`private`）ではありません。

```
type        detail_type                  意味                セッションタイプ
────        ───────────                  ────                ────────
message     group                        グループメッセージ     group（detail_type がそのままセッションタイプ）
message     private                      プライベートメッセージ  private（detail_type がそのままセッションタイプ）
notice      group_member_increase        グループメンバー増加   group（group_id からの推定が必要）
notice      friend_increase              フレンド増加          private（user_id からの推定が必要）
request     friend                       フレンドリクエスト     private（user_id からの推定が必要）
request     group                        グループリクエスト     group（detail_type がそのままセッションタイプ）
```

### 9.2 推定ルール

`infer_receive_type()` の推定順序：

1. `detail_type` が既知のセッションタイプ（`private`/`group`/`channel`/`guild`/`thread`/`user`）である場合は、そのまま使用する
2. `detail_type` がカスタムセッションタイプである場合は、そのまま使用する
3. それ以外の場合（notice/request のセマンティックサブタイプ）、ID フィールドに基づいて推定する：
   - `group_id` がある → `"group"`
   - `channel_id` がある → `"channel"`
   - `guild_id` がある → `"guild"`
   - `thread_id` がある → `"thread"`
   - `user_id` がある → `"private"`

### 9.3 `event.reply()` のターゲット推定

notice/request イベントにおける `event.reply()` の送信ターゲットは、セッションタイプの推定によって決まります：

- グループ通知イベント（`group_id` を含む）→ **グループ**に返信
- フレンド通知イベント（`user_id` のみを含む）→ **ユーザーのプライベートチャット**に返信

```python
from ErisPulse.Core.Event import notice

@notice.on_group_increase()
async def handle_welcome(event):
    group_id = event.get("group_id")    # "group_789"
    user_id = event.get("user_id")      # "user_456"

    # event.reply() はグループに送信（group/group_789）
    await event.reply("グループへようこそ！")

    # 管理者に通知する場合（プライベートチャット）、ターゲットを明示的に指定：
    await adapter.Send.To("user", "admin_id").Text(f"新しいメンバー {user_id} が {group_id} に参加しました")
```

### 9.4 アダプター開発の推奨事項

notice/request イベントに正しい ID フィールドが含まれるようにしてください：

| detail_type | 含まれるべき ID フィールド | 推定されるセッションタイプ |
|-------------|-------------------|---------------|
| `group_member_increase` | `group_id` + `user_id` | `group` |
| `group_member_decrease` | `group_id` + `user_id` | `group` |
| `friend_increase` | `user_id` | `private` |
| `friend_decrease` | `user_id` | `private` |
| `friend`（リクエスト） | `user_id` | `private` |
| `group`（リクエスト） | `group_id` | `group` |

---

## 10. 関連ドキュメント

**コンバーター実装時に併せて参照**：
- [セッションタイプ標準](session-types.md) - セッションタイプの定義とマッピング関係
- [API レスポンス標準](api-response.md) - アダプター API レスポンス形式の標準

**同一アダプターの送信側**：
- [送信メソッド仕様](send-method-spec.md) - Send クラスのメソッド命名、パラメータ仕様および逆変換の要件
- [API アクション標準](api-action-spec.md) - OneBot12 標準 API アクションの統一インターフェース

**各プラットフォームの既知の拡張イベントとメッセージセグメントの確認**：
- [各プラットフォーム特性ドキュメント](../platform-guide/README.md) - このドキュメントにアクセスすることで、各プラットフォームの特性や既知の拡張イベント、メッセージセグメントなどを知ることができます。

## 发送方法规范

> 来源: `docs/ja/standards/send-method-spec.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/ja/standards/send-method-spec.md）

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

## API 动作规范

> 来源: `docs/ja/standards/api-action-spec.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/ja/standards/api-action-spec.md）

# ErisPulse API アクション標準

> [!TIP]
> **このドキュメントを読むべきケース**：アダプタに Api DSL の標準アクション（get_user_info / delete_message など）を実装する場合や、モジュールからこれらの標準アクションをクロスプラットフォームで呼び出す際にパラメータや data フィールドを確認する必要がある場合に、本文を参照してください。必要なければ読み飛ばして構いません。

このドキュメントは、ErisPulse アダプタにおける **OneBot12 標準 API アクション**の統一インターフェース仕様を定義するものであり、モジュール開発者が標準インターフェースに向けてプログラミングできるようにし、プラットフォームネイティブ API へのマッピングはアダプタが担います。

> **カバー範囲**：OneBot12 標準アクションのうち、`ApiDSL` はユーザー / グループ / ギルド（Guild）/
> メッセージ管理 / メタ（Meta）の通常インターフェースに対する強い型付けのメソッドを提供します（`send_message` は
> `SendDSL.Raw_ob12` が担当）。ファイルリソースアクション（`upload_file` / `get_file` / チャンク転送）は
> フォールバック用の透過転送としてのみ保持されており、§3.5 の説明を参照してください。プラットフォーム拡張アクションは `Api.call("prefix.action", ...)`
> というエスケープハッチで呼び出します。アクションのパラメータと返却構造は OneBot12 仕様（リポジトリ内 `onebot/specs/interface/`）に準拠します。

## 1. 設計背景

ErisPulse では、メッセージセグメント（メッセージの送受信）とイベント形式はすでに完全に OneBot12 標準に準拠していますが、**API アクション呼び出し**（ユーザー情報の取得、グループリストの取得、メッセージの取り消しなど）はこれまで統一されておらず、モジュール開発者はプラットフォームごとに異なる `call_api` 呼び出しを書く必要がありました。

`ApiDSL` は、強い型付けの標準アクションメソッドを提供することでこの問題を解決します：

```
モジュールコード（クロスプラットフォーム統一）      アダプタ実装（プラットフォーム固有）
─────────────────              ──────────────────
adapter.Api.get_user_info("123")  →  アダプタ call_api / オーバーライド
adapter.Api.get_group_list()      →  アダプタ call_api / オーバーライド
adapter.Api.delete_message("id")  →  アダプタ call_api / オーバーライド
```

## 2. 三層 DSL 並列構造

ErisPulse アダプタには、それぞれの役割を持つ 3 つの並列な DSL 内部クラスがあります：

```
BaseAdapter
├── Send(SendDSL)       ← メッセージ送信（Text/Image/Raw_ob12）
├── Request(RequestDSL)  ← リクエスト操作（accept/reject）
└── Api(ApiDSL)          ← 標準 API アクション（ユーザー/グループ/ギルド/メッセージ管理/ファイル/メタ）★
```

| DSL | 責務 | メソッドスタイル | 戻り値 |
|-----|------|---------|--------|
| `Send` | メッセージ送信 | チェーン + `asyncio.Task` | 標準レスポンス |
| `Request` | リクエストイベントの処理 | `asyncio.Task` | 標準レスポンス |
| `Api` | クエリ/管理操作 | `async` メソッド | 標準レスポンス |

## 3. 標準アクション一覧

### 3.1 ユーザー関連

| メソッド | OB12 アクション | パラメータ | data の戻り値 |
|------|----------|------|----------|
| `get_self_info()` | `get_self_info` | なし | `user_id`, `user_name`, `user_displayname` |
| `get_user_info(user_id)` | `get_user_info` | `user_id: str` | `user_id`, `user_name`, `user_displayname`, `user_remark` |
| `get_friend_list()` | `get_friend_list` | なし | `list[get_user_info レスポンス]` |

### 3.2 グループ関連

| メソッド | OB12 アクション | パラメータ | data の戻り値 |
|------|----------|------|----------|
| `get_group_info(group_id)` | `get_group_info` | `group_id: str` | `group_id`, `group_name` |
| `get_group_list()` | `get_group_list` | なし | `list[get_group_info レスポンス]` |
| `get_group_member_info(group_id, user_id)` | `get_group_member_info` | `group_id: str`, `user_id: str` | `user_id`, `user_name`, `user_displayname` |
| `get_group_member_list(group_id)` | `get_group_member_list` | `group_id: str` | `list[get_group_member_info レスポンス]` |
| `set_group_name(group_id, group_name)` | `set_group_name` | `group_id: str`, `group_name: str` | なし |
| `leave_group(group_id)` | `leave_group` | `group_id: str` | なし |

### 3.3 メッセージ管理

| メソッド | OB12 アクション | パラメータ | 説明 |
|------|----------|------|------|
| `delete_message(message_id)` | `delete_message` | `message_id: str` | メッセージの取り消し/削除 |

> **メッセージ送信**（`send_message`）は `SendDSL` の `Raw_ob12` が処理するため、`ApiDSL` では重複して提供しません。

### 3.4 ギルド（Guild）関連

OneBot12 のギルド体系は 2 つの階層に分かれています：**ギルド（guild）** と **サブチャンネル（channel）**。

| メソッド | OB12 アクション | パラメータ | data の戻り値 |
|------|----------|------|----------|
| `get_guild_info(guild_id)` | `get_guild_info` | `guild_id: str` | `guild_id`, `guild_name` |
| `get_guild_list()` | `get_guild_list` | なし | `list[get_guild_info レスポンス]` |
| `set_guild_name(guild_id, guild_name)` | `set_guild_name` | `guild_id: str`, `guild_name: str` | なし |
| `get_guild_member_info(guild_id, user_id)` | `get_guild_member_info` | `guild_id: str`, `user_id: str` | `user_id`, `user_name`, `user_displayname` |
| `get_guild_member_list(guild_id)` | `get_guild_member_list` | `guild_id: str` | `list[get_guild_member_info レスポンス]` |
| `leave_guild(guild_id)` | `leave_guild` | `guild_id: str` | なし |
| `get_channel_info(guild_id, channel_id)` | `get_channel_info` | `guild_id: str`, `channel_id: str` | `channel_id`, `channel_name` |
| `get_channel_list(guild_id, *, joined_only)` | `get_channel_list` | `guild_id: str`, `joined_only: bool=false` | `list[get_channel_info レスポンス]` |
| `set_channel_name(guild_id, channel_id, channel_name)` | `set_channel_name` | `guild_id`, `channel_id`, `channel_name` | なし |
| `get_channel_member_info(guild_id, channel_id, user_id)` | `get_channel_member_info` | `guild_id`, `channel_id`, `user_id` | `user_id`, `user_name`, `user_displayname` |
| `get_channel_member_list(guild_id, channel_id)` | `get_channel_member_list` | `guild_id`, `channel_id` | `list[get_channel_member_info レスポンス]` |
| `leave_channel(guild_id, channel_id)` | `leave_channel` | `guild_id`, `channel_id` | なし |

> ギルド体系とグループ（group）は互いに独立しています：Discord / QQ ギルド / Kook などのプラットフォームはギルドインターフェースを実装し、
> 従来の QQ / WeChat はグループインターフェースを実装します。両方が同時に存在する場合もあれば、どちらか一方のみの場合もあります。

### 3.5 ファイルリソース操作

> [!WARNING]
> **ファイルリソースモデル（file_id 二段階方式）は ErisPulse では「フォールバック対応」に位置付けられます**：
> ErisPulse のファイル送受信は「先にアップロードして file_id を取得してから参照する」モデルを採用していません。モジュールがファイルを送信するには
> `SendDSL.File(file, filename)` を使用します（URL / パス / バイトを**送信時に直接送信**、
> [送信メソッド仕様](send-method-spec.md) を参照）。
> 本節の `upload_file` / `get_file` / チャンク転送アクションはプラットフォーム固有の `file_id` ファイルリソース
> 機能に依存しており、**汎用性が不十分**です。アダプタのバックエンドが元々この機能を備えている場合にのみ透過転送が可能で、フレームワーク内蔵の
> アダプタでは**実装せず、実装も推奨しません**。呼び出した場合は通常 `retcode=10002` が返されます。
> モジュールがクロスプラットフォームでファイルを送信する必要がある場合は、`SendDSL.File` を使用し、file_id に依存しないでください。
>
> **展望**：`file_id` リソースモデルのフレームワーク層への標準化は今後の方向性ですが、現行バージョンでは提供されません。

一括転送（小ファイル）：

| メソッド | OB12 アクション | パラメータ | data の戻り値 |
|------|----------|------|----------|
| `upload_file(*, type, name, ...)` | `upload_file` | `type`, `name`, `url`/`path`/`data`, `headers?`, `sha256?` | `file_id` |
| `get_file(file_id, type)` | `get_file` | `file_id: str`, `type: str` | `name`, `url`/`path`/`data` |

`upload_file` の `type` パラメータ：
- `"url"`：URL 経由でアップロード（`url` の指定が必要）
- `"path"`：ローカルパス経由でアップロード（`path` の指定が必要）
- `"data"`：バイナリデータ経由でアップロード（`data` の指定が必要）

#### 3.5.1 チャンク転送（大きなファイル、上記のフォールバック範囲に該当）

OneBot12 のチャンクアクションは `stage` でフェーズを区別します。`ApiDSL` は同一アクションの 3 段階/2 段階を独立したメソッドに分割します
（`offset` はバイトオフセット、`data` は JSON 内では Base64）。以下の表は参照用に保持しているだけで、
アダプタが実装する必要はなく、強制的に実装すべきでもありません：

**チャンクアップロードの 3 ステップ**：`prepare` → `transfer`（チャンクごとにループ）→ `finish`

| メソッド | 対応 stage | パラメータ | data の戻り値 |
|------|-----------|------|----------|
| `upload_file_fragmented_prepare(name, total_size)` | `prepare` | `name: str`, `total_size: int` | `file_id`（転送中に使用） |
| `upload_file_fragmented_transfer(file_id, offset, data)` | `transfer` | `file_id`, `offset: int`, `data: bytes` | なし |
| `upload_file_fragmented_finish(file_id, sha256)` | `finish` | `file_id`, `sha256: str`（ファイル全体の検証） | `file_id` |

```python
total = os.path.getsize(path)
r = await adapter.Api.upload_file_fragmented_prepare(os.path.basename(path), total)
fid = r["data"]["file_id"]
offset = 0
with open(path, "rb") as f:
    while chunk := f.read(65536):
        await adapter.Api.upload_file_fragmented_transfer(fid, offset, chunk)
        offset += len(chunk)
sha256 = hashlib.sha256(open(path, "rb").read()).hexdigest()
await adapter.Api.upload_file_fragmented_finish(fid, sha256)
```

**チャンクダウンロードの 2 ステップ**：`prepare` → `transfer`（ループでチャンクを取得）

| メソッド | 対応 stage | パラメータ | data の戻り値 |
|------|-----------|------|----------|
| `get_file_fragmented_prepare(file_id)` | `prepare` | `file_id` | `name`, `total_size`, `sha256` |
| `get_file_fragmented_transfer(file_id, offset, size)` | `transfer` | `file_id`, `offset: int`, `size: int` | `data`（今回のチャンクのバイト） |

### 3.6 メタ（Meta）アクション

メタアクションは特定のアカウントを対象としないため、`Using()` で Bot を指定する必要はありません。

| メソッド | OB12 アクション | パラメータ | data の戻り値 |
|------|----------|------|----------|
| `get_latest_events(limit, timeout)` | `get_latest_events` | `limit: int=0`, `timeout: int=0` | イベントオブジェクトの配列（メタイベントを除く） |
| `get_supported_actions()` | `get_supported_actions` | なし | `list[str]` サポート対象のアクション名 |
| `get_status()` | `get_status` | なし | `good: bool`, `bots: list[{self, online, ...}]` |
| `get_version()` | `get_version` | なし | `impl`, `version`, `onebot_version` |

### 3.7 汎用拡張アクション

| メソッド | 説明 |
|------|------|
| `call(action, **params)` | プラットフォーム拡張アクションのエスケープハッチ。OB12 拡張命名規則 `{prefix}.{action}` に従う |

## 4. 使用方法

### 4.1 基本的な呼び出し

```python
from ErisPulse import adapter

# ユーザー情報の取得（クロスプラットフォーム統一）
result = await adapter.myplatform.Api.get_user_info("123456")
if result["status"] == "ok":
    user_name = result["data"]["user_name"]
    print(f"ユーザー名: {user_name}")

# グループリストの取得
result = await adapter.myplatform.Api.get_group_list()
groups = result["data"]

# メッセージの取り消し
await adapter.myplatform.Api.delete_message("msg_123456")
```

### 4.2 Bot アカウントの指定（マルチアカウントモード）

```python
# 指定した Bot アカウントで操作を実行
info = await adapter.myplatform.Api.Using("bot1").get_self_info()
```

### 4.3 プラットフォーム拡張アクション

```python
# プラットフォーム固有の拡張アクションを呼び出し（{prefix}.{action} の命名を推奨）
result = await adapter.telegram.Api.call(
    "telegram.send_sticker",
    sticker_id="CAACAgIAAxkBAA...",
)
```

### 4.4 イベントハンドラでの使用

```python
from ErisPulse.Core.Event import message

@message()
async def handle(event):
    # 送信者の詳細情報を取得
    user_id = event.get_user_id()
    platform = event.get_platform()

    result = await getattr(adapter, platform).Api.get_user_info(user_id)
    if result["status"] == "ok":
        user_name = result["data"]["user_name"]
        await event.reply(f"こんにちは、{user_name}さん！")
```

## 5. アダプタの実装

### 5.1 デフォルト動作（設定不要）

`ApiDSL` のデフォルト実装は、標準アクション名を `endpoint` としてそのまま `adapter.call_api()` に渡します：

```python
# ApiDSL のデフォルト実装は以下と等価：
async def get_user_info(self, user_id: str) -> dict:
    return await self._adapter.call_api("get_user_info", user_id=user_id, account_id=self._account_id)
```

**適用シーン**：アダプタの基盤となるバックエンド自体が OneBot12 標準アクションプロトコルに準拠している場合、
`call_api` は標準アクション名をそのままサポートします（同プロトコルに準拠したサーバーに直接接続する場合など）。

### 5.2 標準メソッドのオーバーライド（プラットフォームネイティブ API へのマッピング）

アダプタは個々の標準メソッドをオーバーライドし、プラットフォームネイティブ API にマッピングできます：

```python
class MyAdapter(BaseAdapter):

    class Api(BaseAdapter.Api):
        """MyPlatform 標準 API アクション実装"""

        async def get_user_info(self, user_id: str) -> dict:
            # プラットフォームネイティブ API にマッピング
            raw = await self._adapter._request("GET", f"/users/{user_id}")
            if raw.get("code") != 0:
                # プラットフォーム側エラー：341xx～345xx の下 3 桁をカスタムで使用（346xx はフレームワーク予約のため使用禁止）
                return self._adapter.make_error(retcode=34400, message="ユーザーが存在しません")

            user = raw["data"]
            return self._adapter.make_response(
                data={
                    "user_id": str(user["id"]),
                    "user_name": user.get("nick", ""),
                    "user_displayname": user.get("display_name", ""),
                    "user_remark": user.get("remark", ""),
                },
                raw=raw,
            )

        async def get_friend_list(self) -> dict:
            raw = await self._adapter._request("GET", "/friends")
            friends = [
                {
                    "user_id": str(u["id"]),
                    "user_name": u.get("nick", ""),
                    "user_displayname": u.get("display_name", ""),
                    "user_remark": u.get("remark", ""),
                }
                for u in raw.get("data", [])
            ]
            return self._adapter.make_response(data=friends, raw=raw)
```

### 5.3 未対応のアクション

アダプタがオーバーライドしていない標準メソッドはデフォルト実装（`call_api` への委譲）になります。`call_api` もそのアクションをサポートしていない場合は、標準エラーレスポンスを返すべきです：

```python
async def call_api(self, endpoint: str, **params):
    if endpoint not in self._supported_endpoints:
        return self.make_error(retcode=10002, message=f"未対応のアクション: {endpoint}")
    # ... プラットフォーム API 呼び出し
```

モジュール開発者は戻り値の `retcode` でサポートされているかどうかを判断できます：

```python
result = await adapter.myplatform.Api.get_friend_list()
if result["retcode"] == 10002:
    print("このプラットフォームはフレンドリストの取得に対応していません")
```

## 6. レスポンス形式

すべての `ApiDSL` メソッドは標準 API レスポンス形式を返します（詳細は [API レスポンス標準](api-response.md) を参照）：

```json
{
    "status": "ok",
    "retcode": 0,
    "data": { ... },
    "message_id": "",
    "message": "",
    "myplatform_raw": { ... }
}
```

> **注意**：情報照会系アクションの `message_id` は空文字列です（メッセージ送信系アクションのみが `message_id` を持ちます）。

## 7. SendDSL / RequestDSL との関係

| シナリオ | 使用する DSL | 例 |
|------|---------|------|
| メッセージ送信 | `Send` | `adapter.Send.To("group", "123").Text("hi")` |
| リクエストの承認/拒否 | `Request` | `adapter.Request("req_id").accept()` |
| ユーザー/グループ情報の取得 | `Api` | `adapter.Api.get_user_info("123")` |
| メッセージの取り消し | `Api` | `adapter.Api.delete_message("msg_id")` |
| グループ退出 | `Api` | `adapter.Api.leave_group("group_id")` |

## 8. アダプタ実装チェックリスト

### 標準アクション
- [ ] `call_api` が標準アクション名を処理できること（または対応する `ApiDSL` メソッドをオーバーライド）
- [ ] 未対応のアクションは `retcode=10002` を返すこと
- [ ] 戻り値が標準 API レスポンス形式に準拠していること
- [ ] `data` フィールドに OB12 標準定義のフィールドが含まれていること
- [ ] ギルドプラットフォームは `get_guild_*` / `get_channel_*` / `leave_guild` / `leave_channel` を実装すること
- [ ] メタアクション（`get_status` / `get_version` / `get_supported_actions`）の実装を推奨
- [ ] **ファイルの送受信は `SendDSL.File`（直接送信）を使用**。ファイルリソースアクション（upload_file/get_file/チャンク転送）は**実装必須ではない**。バックエンドが `file_id` リソース機能を備える場合にのみ透過転送が必要

### 拡張アクション
- [ ] プラットフォーム拡張アクションは `{prefix}.{action}` の命名を使用
- [ ] 拡張アクションのパラメータとレスポンスも OB12 アクションのリクエスト/レスポンス構造に準拠

## 9. 関連ドキュメント

**Api DSL の戻り値実装時に併せて参照**：
- [API レスポンス標準](api-response.md) - アダプタ API レスポンス形式標準

**同一アダプタのその他の DSL**：
- [送信メソッド仕様](send-method-spec.md) - Send クラスのメソッド命名とパラメータ仕様
- [リクエスト操作仕様](request-action-spec.md) - Request DSL の使用方法

**イベント側の関連資料**：
- [イベント変換標準](event-conversion.md) - イベント形式とメッセージセグメント標準

## API 响应规范

> 来源: `docs/ja/standards/api-response.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/ja/standards/api-response.md）

# ErisPulse アダプターの標準化された返却値仕様

> [!TIP]
> **この記事を読むタイミング**：アダプター内で `call_api` / Send / Request の返り値を実装する際に、返却値の構造と返却コードが ErisPulse の標準に準拠しているか確認する必要がある場合、または特定の `retcode` の意味を確認したい場合に、本記事を参照してください。必要がない場合は飛ばしてください。

## 1. 説明  
なぜこの規格があるのでしょうか？

各プラットフォームの送信インターフェースが一貫性とOneBot12との互換性を確保するため、ErisPulseアダプターはAPIレスポンス形式においてOneBot12が定義するメッセージ送信返却構造の標準を採用しています。

ただしErisPulseのプロトコルにはいくつかの特殊な定義があります:
- 1. 基本フィールドにおいて、message_idは必須ですが、OneBot12の標準にはこのフィールドはありません。
- 2. 返却内容には、{platform_name}_raw フィールドを追加する必要があります。このフィールドには、元のレスポンスデータを格納します。

## 2. 基礎レスポンス構造
すべてのアクションレスポンスには、以下の基本フィールドを含める必要があります。

| フィールド名 | データ型 | 必須 | 説明 |
|-------|---------|------|------|
| status | string | はい | 実行ステータス。"ok"または"failed"のいずれかに設定する必要があります |
| retcode | int64 | はい | 戻り値コード。OneBot12の戻り値コード規則に従います |
| data | any | はい | レスポンスデータ。成功時はリクエスト結果を含み、失敗時はnull |
| message_id | string | はい | メッセージID。メッセージを識別するためのもので、存在しない場合は空文字列 |
| message | string | はい | エラーメッセージ。成功時は空文字列 |
| {platform_name}_raw | any | いいえ | 元のレスポンスデータ |

オプションフィールド：
| フィールド名 | データ型 | 必須 | 説明 |
|-------|---------|------|------|
| echo | string | いいえ | リクエストにechoフィールドが含まれている場合、その値をそのまま返します |

## 3. 完全なフィールド仕様

### 3.1 一般的なフィールド

#### 成功時のレスポンス例
```json
{
    "status": "ok",
    "retcode": 0,
    "data": {
        "message_id": "1234",
        "time": 1632847927.599013
    },
    "message_id": "1234",
    "message": "",
    "echo": "1234",
    "telegram_raw": {...}
}
```

#### 失敗時のレスポンス例
```json
{
    "status": "failed",
    "retcode": 10003,
    "data": null,
    "message_id": "",
    "message": "必要なパラメータが不足しています: user_id",
    "echo": "1234",
    "telegram_raw": {...}
}
```

### 3.2 戻り値コードの仕様

#### 0 成功（OK）
- 0: 成功（OK）

#### 1xxxx 動作リクエストエラー（Request Error）
| エラーコード | エラー名 | 説明 |
|-------|-------|------|
| 10001 | Bad Request | 無効な動作リクエスト |
| 10002 | Unsupported Action | 対応していない動作リクエスト |
| 10003 | Bad Param | 無効な動作リクエストパラメータ |
| 10004 | Unsupported Param | 対応していない動作リクエストパラメータ |
| 10005 | Unsupported Segment | 対応していないメッセージセグメントの種類 |
| 10006 | Bad Segment Data | 無効なメッセージセグメントパラメータ |
| 10007 | Unsupported Segment Data | 対応していないメッセージセグメントパラメータ |
| 10101 | Who Am I | ロボットアカウントが指定されていません |
| 10102 | Unknown Self | 知らないロボットアカウント |

#### 2xxxx 動作ハンドラーエラー（Handler Error）
| エラーコード | エラー名 | 説明 |
|-------|-------|------|
| 20001 | Bad Handler | 動作ハンドラーの実装エラー |
| 20002 | Internal Handler Error | 動作ハンドラーが実行中に例外をスローしました |

#### 3xxxx 動作実行エラー（Execution Error）
| エラーコード範囲 | エラー種別 | 説明 |
|-----------|---------|------|
| 31xxx | Database Error | データベースエラー |
| 32xxx | Filesystem Error | ファイルシステムエラー |
| 33xxx | Network Error | ネットワークエラー |
| 34xxx | Platform Error | ロボットプラットフォームエラー |
| 35xxx | Logic Error | 動作ロジックエラー |
| 36xxx | I Am Tired | 実装が作業を中止することを決定しました |

#### 保留エラーセグメント
- 4xxxx、5xxxx: 保留セグメント、使用しないでください
- 6xxxx～9xxxx: 他のエラーセグメント、実装が独自に使用するためのものです

## 4. 実装要件
1. すべてのレスポンスには status、retcode、data、message フィールドが含まれている必要があります。
2. リクエストに非空の echo フィールドが含まれている場合、レスポンスには同じ値の echo フィールドが含まれている必要があります。
3. 戻り値コードは OneBot12 規格に厳密に従う必要があります。
4. エラーメッセージ(message)は人間に読みやすい説明文である必要があります。

## 5. 拡張仕様

ErisPulse は OneBot12 標準の返却構造に以下の拡張を加えています。

### 5.1 `message_id` 必須フィールド

OneBot12 標準では `message_id` は `data` オブジェクト内にあり、必須ではありません。ErisPulse ではこれをトップレベルの**必須**フィールドに昇格させています：

- `message_id` を取得できない場合は、空文字列 `""` を設定する
- `message_id` が常に存在することを保証し、モジュールは null チェックを行う必要がない

### 5.2 `{platform}_raw` 原始レスポンスフィールド

返却値には、プラットフォームの原始レスポンスデータの完全なコピーを保持する `{platform}_raw` フィールドを含める必要があります：

```json
{
    "status": "ok",
    "retcode": 0,
    "data": {"message_id": "1234", "time": 1632847927},
    "message_id": "1234",
    "message": "",
    "telegram_raw": {
        "ok": true,
        "result": {"message_id": 1234, "date": 1632847927, ...}
    }
}
```

**要件**：
- `{platform}_raw` は原始レスポンスのディープコピーである必要があり、参照ではありません
- `platform` はアダプター登録時のプラットフォーム名と完全に一致する必要があります（大文字小文字を区別）
- エラーメッセージも保持し、デバッグに役立つようにする

### 5.3 フレームワーク拡張返却コード（34xxx プラットフォームエラーセグメントの下3桁をカスタム）

OneBot12 規格では、実装が `3xxxx` の下3桁をカスタムに使用することが許可されています。`34xxx` の意味は **Platform Error**（ロボットプラットフォームエラー、プラットフォーム制限による失敗など）です。`34xxx` 内部では役割ごとに分層して使用されます：

| 下3桁セグメント | 所属 | 用途 |
|---------|------|------|
| `340xx` | アダプター実装 | リクエスト操作族（Request Not Found / Already Handled / Not Supported / Permission Denied、request-action-spec §7 参照） |
| `341xx`～`345xx` | アダプター実装 | プラットフォーム側の権限 / リスク管理 / アカウント制限などのエラー（実装者が下3桁をカスタム、元のエラーは `{platform}_raw` に格納） |
| `346xx` | **ErisPulse フレームワーク（予約済み）** | フレームワーク自身のブロックと一般的な失敗、アダプターやモジュールは使用しない |
| `347xx`～`349xx` | アダプター実装 | その他のプラットフォーム実行エラー |

ErisPulse フレームワークで現在使用している `346xx` コード：

| エラーコード | エラー名 | 説明 |
|-------|-------|------|
| 34600 | SDK Failure | フレームワークの一般的な失敗（`make_error()` のデフォルト返却コード） |
| 34601 | Action Denied | 出力アクションがスコープによって禁止された（`scope.actions`）、呼び出しは行われず、直接このレスポンスを返す |

> 役割の区別：`34601` は**フレームワークが呼び出し前にブロック**（モジュールはそもそもアクションを発行する資格がない）です。
> `34004` / `34xxx` プラットフォームコードは**アクションは発行されたがプラットフォームが拒否**（Bot に権限がない、リスク管理対象など）です。
> モジュールは権限の問題を判断する際に、これら2つを同時にチェックする必要があります：まず `34601`（自分のモジュールが scope によって禁止されているか）を確認し、次に `34xxx`（プラットフォーム側の制限）を確認します。

返却構造は §2 の標準失敗レスポンスに従います：

```json
{
    "status": "failed",
    "retcode": 34601,
    "data": null,
    "message_id": "",
    "message": "action 'send' denied by scope.actions"
}
```

### 5.4 アダプター実装チェックリスト

- [ ] `status`, `retcode`, `data`, `message_id`, `message` フィールドを含む
- [ ] 返却コードは OneBot12 規格に従う（§3.2 参照）
- [ ] `message_id` が常に存在する（取得できない場合は空文字列）
- [ ] `{platform}_raw` にプラットフォームの原始レスポンスデータを含む

## 6. 注意事項
- 3xxxxエラーコードについては、下位3桁は実装側で独自に定義可能
- 予約エラーセグメント（4xxxx、5xxxx）の使用を避けること
- **`34600` / `34601` は ErisPulse フレームワークが予約するコード**（§5.3参照）であり、アダプタ/モジュールは使用しないこと
- エラーメッセージは簡潔かつ明瞭にし、デバッグに役立つようにすること

---

## 次のステップ

- **各DSLの戻り値に対応する照会**：[APIアクション標準](api-action-spec.md)（標準アクションのdataフィールド）、[リクエスト操作規格](request-action-spec.md)（リクエスト操作の34001-34004拡張）、[送信メソッド規格](send-method-spec.md)（送信失敗時の降格意味）
- **権限関連の失敗のトラブルシューティング**：まず`34601`（モジュールがscopeによって禁止されている、フレームワークが呼び出し前にブロックする、§5.3を参照）、次に`34xxx`（アクションは発行されたが、プラットフォーム側で拒否された）を確認する

## 请求动作规范

> 来源: `docs/ja/standards/request-action-spec.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/ja/standards/request-action-spec.md）

# ErisPulse リクエスト操作仕様

> [!TIP]
> **このドキュメントを読むべきケース**：アダプターで友達リクエスト/グループ招待を処理する必要がある場合（リクエストイベントの変換や `accept`/`reject` の実装）、またはモジュールで `event.approve()` / `event.reject()` を使ってリクエストを承認する場合に、本文を参照してください。該当しない場合は読み飛ばしてください。

本ドキュメントは、ErisPulse アダプターにおけるリクエストイベント操作の標準化された仕様を定義します。リクエストイベントのフィールド要件、Request DSL の使用方法、およびアダプターの実装要件が含まれます。

## 1. 概要

リクエストイベント（`type: "request"`）は、OneBot12 標準で定義された特殊なイベントタイプであり、Bot が意思決定を行う必要のあるリクエスト（友達リクエスト、グループ招待など）を表します。

メッセージイベントとは異なり、リクエストイベントは**双方向のやり取り**が必要です：
1. **受信**：アダプターがプラットフォームのネイティブリクエストを標準リクエストイベントに変換する
2. **応答**：モジュールが `Request` DSL または `Event.approve()`/`Event.reject()` を通じて操作を実行する

```
プラットフォームのネイティブリクエストイベント
    │
    ▼
Converter.convert()        ← アダプター実装（正方向の変換）
    │
    ▼
標準リクエストイベント (request_id を含む)
    │
    ├─→ モジュールハンドラー @request.on_friend_request()
    │       │
    │       ├─→ event.approve()     ← リクエストを承認
    │       └─→ event.reject()      ← リクエストを拒否
    │               │
    │               ▼
    │       adapter.Request(request_id).accept()
    │               │
    │               ▼
    │       BaseAdapter.Request.accept()  ← アダプターでオーバーライド
    │               │
    │               ▼
    │       プラットフォーム API 呼び出し
    │
    └─→ またはアダプター経由で直接操作
            await adapter.Request("req_id").accept()
```

## 2. リクエストイベントのフィールド要件

### 2.1 標準フィールド

リクエストイベントは、OneBot12 の標準フィールドに加えて、以下のフィールドを含む必要があります：

| フィールド | 型 | 必須 | 説明 |
|------|------|------|------|
| `request_id` | string | **強く推奨** | リクエスト識別子。承認/拒否操作に使用 |
| `user_id` | string | はい | リクエスト送信者の ID |
| `user_nickname` | string | いいえ | リクエスト送信者のニックネーム |
| `comment` | string | いいえ | リクエストの添付メッセージ |

### 2.2 `request_id` フィールド

`request_id` はリクエスト操作の中核となる識別子です：

- **用途**：操作対象のリクエストを識別し、`Request` DSL から使用される
- **生成ルール**：
  - プラットフォームのネイティブなリクエスト識別子を優先的に使用する（OneBot11 の `flag` フィールド、Telegram の `chat_invite_link` など）
  - プラットフォームにネイティブなリクエスト ID がない場合、アダプターは一意の識別子を生成する必要がある（推奨形式：`{platform}_{timestamp}_{user_id}`）
- **一意性**：同一プラットフォームの範囲内で一意であること
- **欠落時の動作**：`request_id` が欠落している場合、`event.approve()` / `event.reject()` は `ValueError` をスローする

### 2.3 リクエストイベントの例

```json
{
  "id": "evt_123456",
  "time": 1752241225,
  "type": "request",
  "detail_type": "friend",
  "platform": "onebot11",
  "self": {
    "platform": "onebot11",
    "user_id": "bot_123"
  },
  "user_id": "user_456",
  "user_nickname": "YingXinche",
  "comment": "友達リクエストをお願いします",
  "request_id": "flag_abc123",
  "onebot11_raw": {...},
  "onebot11_raw_type": "request"
}
```

## 3. Request DSL

### 3.1 メソッドチェーン

`Request` は `Send` と同じスタイルのメソッドチェーンインターフェースを提供します：

```python
# 基本的な使い方
await adapter.Request("req_id").accept()
await adapter.Request("req_id").reject()

# Bot アカウントを指定
await adapter.Request("req_id").Using("bot1").accept()

# 備考を付ける（kwargs 経由）
await adapter.Request("req_id").accept(comment="ようこそ")
await adapter.Request("req_id").reject(comment="今は追加しません")

# 組み合わせて使用
await adapter.Request("req_id").Using("bot1").accept(comment="ようこそ")
```

### 3.2 メソッド一覧

| メソッド | 説明 | 戻り値 |
|------|------|--------|
| `Using(account_id)` | 操作を実行する Bot アカウントを指定 | `RequestDSL`（メソッドチェーン対応） |
| `accept(**kwargs)` | リクエストを承認 | `asyncio.Task`（await 後に標準レスポンスを返す） |
| `reject(**kwargs)` | リクエストを拒否 | `asyncio.Task`（await 後に標準レスポンスを返す） |

### 3.3 戻り値の形式

操作は標準 API レスポンス形式を返します：

**成功**：
```json
{
    "status": "ok",
    "retcode": 0,
    "data": null,
    "message_id": "",
    "message": ""
}
```

**失敗**：
```json
{
    "status": "failed",
    "retcode": 34001,
    "data": null,
    "message_id": "",
    "message": "リクエストが存在しないか、期限切れです"
}
```

**未実装**（アダプターが `accept`/`reject` をオーバーライドしていない場合）：
```json
{
    "status": "failed",
    "retcode": 10002,
    "data": null,
    "message_id": "",
    "message": "プラットフォーム MyAdapter はリクエスト操作 (accept) を実装していません"
}
```

## 4. Event の便利メソッド

`Event` ラップクラスは、リクエストイベントハンドラーでの使用に適した便利メソッドを提供します：

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    # リクエスト ID を確認
    request_id = event.get_request_id()
    if not request_id:
        print("警告：リクエストイベントに request_id がありません")
        return
    
    # リクエストを承認
    result = await event.approve()
    
    # またはリクエストを拒否
    # result = await event.reject(comment="今は友達追加しません")
    
    # 結果を確認
    if result.get("status") == "ok":
        print("操作に成功しました")
    else:
        print(f"操作に失敗しました: {result.get('message')}")
```

### 4.1 Event メソッド一覧

| メソッド | 説明 | 戻り値 |
|------|------|--------|
| `get_request_id()` | リクエスト ID を取得 | `str` |
| `approve(comment=None)` | 現在のリクエストイベントを承認 | 標準レスポンス形式 |
| `reject(comment=None)` | 現在のリクエストイベントを拒否 | 標準レスポンス形式 |

## 5. アダプター実装要件

### 5.1 コンバーターの要件

アダプターのコンバーターは、リクエストイベントを変換する際に、`request_id` フィールドを正しく設定し**なければなりません**：

```python
def convert_request_event(self, raw_event: dict) -> dict:
    """プラットフォームのネイティブリクエストイベントを変換する"""
    return {
        "id": self._generate_event_id(raw_event),
        "time": int(time.time()),
        "type": "request",
        "detail_type": self._map_request_type(raw_event),  # "friend" または "group"
        "platform": self._platform_name,
        "self": {
            "platform": self._platform_name,
            "user_id": str(self._bot_id),
        },
        "user_id": str(raw_event.get("user_id", "")),
        "user_nickname": raw_event.get("nickname", ""),
        "comment": raw_event.get("message", ""),
        "request_id": self._extract_request_id(raw_event),  # ← 重要なフィールド
        f"{self._platform_name}_raw": raw_event,
        f"{self._platform_name}_raw_type": raw_event.get("type", ""),
    }

def _extract_request_id(self, raw_event: dict) -> str:
    """
    プラットフォームのネイティブイベントからリクエスト ID を抽出する
    
    プラットフォームのネイティブなリクエスト識別子を優先的に使用し、
    存在しない場合は一意の ID を生成する
    """
    # プラットフォームのネイティブ ID を優先的に使用
    if flag := raw_event.get("flag"):
        return str(flag)
    if request_key := raw_event.get("request_key"):
        return str(request_key)
    
    # フォールバック：一意の ID を生成
    import hashlib
    raw = f"{self._platform_name}_{raw_event.get('user_id')}_{raw_event.get('timestamp')}"
    return hashlib.md5(raw.encode()).hexdigest()
```

### 5.2 Request 内部クラスの実装

アダプターは、`Request` 内部クラスで `accept` と `reject` をオーバーライドするだけです：

```python
from ErisPulse.Core import BaseAdapter, RequestDSL

class MyAdapter(BaseAdapter):
    
    class Request(RequestDSL):
        """MyPlatform のリクエスト操作実装"""
        
        def accept(self, **kwargs):
            """
            リクエストを承認する
            
            :param kwargs: 拡張パラメータ。例：comment="備考"
            :return: asyncio.Task
            """
            async def _do():
                try:
                    result = await self._adapter.call_api(
                        endpoint="/set_request",
                        request_id=self._request_id,
                        approve=True,
                        **kwargs,
                    )
                    return {
                        "status": "ok" if result.get("code") == 0 else "failed",
                        "retcode": result.get("code", 0),
                        "data": None,
                        "message_id": "",
                        "message": result.get("message", ""),
                    }
                except Exception as e:
                    return {
                        "status": "failed",
                        "retcode": 34001,
                        "data": None,
                        "message_id": "",
                        "message": f"リクエスト操作に失敗しました: {e}",
                    }
            
            return self._create_task(_do())
        
        def reject(self, **kwargs):
            """リクエストを拒否する"""
            async def _do():
                try:
                    result = await self._adapter.call_api(
                        endpoint="/set_request",
                        request_id=self._request_id,
                        approve=False,
                        **kwargs,
                    )
                    return {
                        "status": "ok" if result.get("code") == 0 else "failed",
                        "retcode": result.get("code", 0),
                        "data": None,
                        "message_id": "",
                        "message": result.get("message", ""),
                    }
                except Exception as e:
                    return {
                        "status": "failed",
                        "retcode": 34001,
                        "data": None,
                        "message_id": "",
                        "message": f"リクエスト操作に失敗しました: {e}",
                    }
            
            return self._create_task(_do())
```

### 5.3 プラットフォームがリクエスト操作をサポートしていない場合

プラットフォーム自体が友達リクエスト/グループ招待操作をサポートしていない場合（一部のプラットフォームではリクエストが自動処理されるなど）、アダプターは以下の対応が可能です：

1. **`Request` 内部クラスをオーバーライドしない**：基底クラスのデフォルト実装を使用すると、`accept()`/`reject()` の呼び出し時に `retcode=10002` が返される
2. **変換時に `request_id` をスキップする**：`request_id` を生成せず、`event.approve()` に `ValueError` をスローさせる
3. **ログを記録する**：`accept`/`reject` 内で警告を記録し、適切なエラーコードを返す

### 5.4 まとめ：Send と Request の並列構成

アダプターには 2 つの並列した DSL 内部クラスがあり、それぞれが役割を担っています：

```
BaseAdapter
├── Send(SendDSL)     ← メッセージ送信
│   ├── Raw_ob12()    ← 必須実装
│   ├── Text()        ← 推奨実装
│   └── Image()       ← 必要に応じて実装
│
└── Request(RequestDSL) ← リクエスト操作
    ├── accept()        ← 必要に応じて実装
    └── reject()        ← 必要に応じて実装
```

### 5.5 アダプターの `__init__` に関する注意事項

`Request` 内部クラスの `__init__` をオーバーライドする場合は、パラメータを透過的に渡し、`super().__init__()` を呼び出す必要があります。詳細は [アダプター開発入門 - `__init__` の注意事項](../developer-guide/adapters/getting-started.md#init-注意事項) を参照してください（`Request` も同様で、パラメータは `adapter, request_id, account_id` です）。

## 6. アダプター実装チェックリスト

### 基本要件
- [ ] `__init__` をオーバーライドした場合は `super().__init__()` を呼び出していること（Send / Request ファクトリの初期化を確保）

### リクエストイベントの変換
- [ ] リクエストイベントに `request_id` フィールドが含まれている（強く推奨）
- [ ] `detail_type` が `"friend"` または `"group"` に正しくマッピングされている
- [ ] プラットフォームの生データが `{platform}_raw` フィールドに保持されている
- [ ] `request_id` の生成ルールがドキュメントに記載されている

### リクエスト操作
- [ ] `Request` 内部クラスが実装されている（プラットフォームがリクエスト操作をサポートする場合）
- [ ] `accept()` メソッドが実装されている
- [ ] `reject()` メソッドが実装されている
- [ ] 操作が標準 API レスポンス形式を返している
- [ ] サポートされていない操作は `retcode=10002` を返す
- [ ] ネットワークエラーは `retcode=33xxx` を返す（API レスポンス標準に従う）

## 7. エラーコードの拡張

リクエスト操作に関連する**アダプター実装層**の推奨エラーコード（[API レスポンス標準](api-response.md) §3.2 に従い、
`34xxx` プラットフォームエラーセグメントの下 3 桁をカスタム定義）：

| エラーコード | エラー名 | 説明 |
|-------|-------|------|
| 34001 | Request Not Found | リクエストが存在しないか、期限切れです |
| 34002 | Request Already Handled | リクエストはすでに処理されています |
| 34003 | Request Not Supported | プラットフォームはこのタイプのリクエスト操作をサポートしていません |
| 34004 | Permission Denied | Bot にはこのリクエストを処理する権限がありません（プラットフォームから返却） |

> **フレームワークコードとの境界**：上記の `340xx` は**プラットフォーム/アダプター**が返すリクエスト処理の失敗です。
> ErisPulse フレームワークは、`scope.actions` で特定のモジュールの request アクションが無効化されている場合、**アダプターを呼び出す前に**
> 直接 `34601`（Action Denied、[API レスポンス標準 §5.3](api-response.md#53-フレームワーク拡張リターンコード34xxx-プラットフォームエラーセグメントの下3桁カスタム) を参照）を返します。
> 両者は互いに代替するものではありません。まず `34601` のフレームワークゲートを通過し、その後プラットフォーム層の `340xx` エラーに到達します。

## 8. 関連ドキュメント

**リクエスト操作を実装する際に併せて参照**：
- [イベント変換標準](event-conversion.md) - 完全なイベント変換仕様（`request_id` フィールド要件を含む）
- [API レスポンス標準](api-response.md) - アダプターの API レスポンス形式標準（操作の戻り値とエラーコード）

**同一アダプターのその他の DSL**：
- [送信メソッド仕様](send-method-spec.md) - Send クラスのメソッド命名およびパラメータ仕様
- [セッションタイプ標準](session-types.md) - セッションタイプの定義とマッピング関係
