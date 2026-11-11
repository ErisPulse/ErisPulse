# Oopz プラットフォームの特徴ドキュメント

## ドキュメント情報

| 項目 | 内容 |
|---|---|
| モジュールバージョン | 0.1.0 |
| プラットフォーム識別子 | `oopz` |
| メンテナ | ErisPulse チーム |
| 最終更新日 | 2026-11-11 |

> ⚠️ Oopz には公式のロボットプラットフォームが存在せず、このアダプターはコミュニティによる逆解析プロトコルに基づき**ユーザーのアカウントとして**接続しています。非公式のインターフェースはいつでも無効になる可能性がありますので、サブアカウントを使用してください。詳細は README のリスクに関する声明をご覧ください。

## 基本情報

- アダプタクラス: `OopzAdapter`（エントリーポイント `oopz`）
- 接続方法: WebSocket（`wss://ws.oopz.cn`）+ REST ゲートウェイ（`https://gateway.oopz.cn`）、RSA署名リクエストヘッダー + JWT
- 認証情報: 「アカウントとパスワードのどちらか」——`password`（電話番号+パスワード+クライアントの秘密鍵、自動ログイン継続）または `token`（uid/JWT/device_id/秘密鍵の4つ揃い）
- 複数アカウント: サポート（`[Oopz_Adapter.accounts.<name>]`）、イベント `self.account_id` で元のアカウントを識別
- フレームワークのソフト依存: ErisPulse ≥ 2.7.1

## 会話モデル

| ErisPulse 目標 | Oopz 概念 | 説明 |
|---|---|---|
| `Send.To("group", <チャンネルID>)` | チャンネル（channel） | ドメインはアダプターが「channel→area キャッシュ + 加入ドメインスキャン」を経て自動的に解析します |
| `Send.To("user", <相手UID>)` | プライベートチャットセッション | 自動的に `PATCH /client/v1/chat/v1/to` を実行してセッションを開始し、sessionId をキャッシュします |
| `guild_id` フィールド / guild の意味 | ドメイン（area） | ドメインレベルの操作は `get_guild_*` と `oopz.*` 管理拡張を経由します |

## 標準化の整列（0.1.0）

### エラーコードの規格

| retcode | 含意 |
|---|---|
| 0 | 成功 |
| 10002 | 対応されていないアクション/メッセージセグメントの降格（音声、動画、ファイル送信、upload_file、keyboard など） |
| 10003 | パラメータの欠落/不正（例：チャンネルが所属するドメインを特定できない） |
| 33001 | ネットワーク異常/リクエスト制限（429の場合は Retry-After を尊重し、1回リトライ） |
| 34100 | プラットフォームが失敗を返した（元の応答は `oopz_raw` に格納） |
| 34005 | アカウントが解析されていない（設定されていないか、セッションが確立されていない） |

### 応答構造

すべての応答は `status / retcode / data / message_id / message / oopz_raw` を含む。送信応答の `message_id` は、プラットフォームが返した `messageId` から取得する。`data.self_info.user_id` は `get_self_info` で戻り値として戻される。

### イベントフィールドの完全性

- すべてのイベントは `id / time / type / detail_type / sub_type / platform / self` を必須とし、`oopz_raw` と `oopz_raw_type` は常に存在する。
- メッセージイベントの最上位には `message_id` を必ず含む。タイムスタンプのマイクロ秒文字列は統一的に秒に変換する。
- イベントの `id` はアカウントドメインで重複を排除する（`<アカウント>:<タイプ>:<プラットフォームID>`）。
- 未知のイベントは `type="unknown"` + `warning` に変換され、静かに破棄されない。
- プロトコル内部フレーム（ハンドシェイク/認証/ハートビート/サブスクリプション）はプラットフォームイベントを生成しない。

### 降格の意味

- `voice/audio/video/file` 送信セグメント → `retcode=10002`（プラットフォームがサポートしているのは画像のアップロードのみ）、例外をスローしない。
- `guild` 送信先 → `retcode=10003`（チャンネルを指定してください）。
- token モードの JWT が無効 → `retcode=34100` で認証情報の更新を促す。password モードでは、自動的に再ログイン後、1回リトライする。

## 支援されるメッセージ送信タイプ

| 方法 | プラットフォーム実装 |
|---|---|
| `Text` | テキスト（text/content 両方書き込み） |
| `Image` | COS 署名票アップロード（画像のみ）、テキストプレースホルダ `![IMAGEw{w}h{h}]({fileKey})` + attachments |
| `At / AtAll / Reply` | `mentionList` / `isMentionAll` / `referenceMessageId` |
| `Important()` 修飾子 | `styleTags=["IMPORTANT"]` 公告スタイル |
| `Recall(messageId)` | `recallGim`（チャンネル）/ `recallIm`（プライベートメッセージ、自分発信のみ撤回可能） |
| `Raw_ob12` | OneBot12 段 → プラットフォーム payload（text/mention/mention_all/reply/image；その他の段は降格 10002） |
| Voice/Video/File/Keyboard | 非対応 → 10002 |

## 標準 API 動作（ApiDSL）

### 対応している標準動作

`get_self_info`、`get_user_info`、`get_friend_list`、`get_group_info`（チャンネルと所属ドメインの統合情報）、`get_group_list`（参加しているドメインのチャンネルの平準化されたリスト）、`get_guild_info`、`get_guild_list`、`get_channel_list`、`get_guild_members`、`delete_message`（`channel_id` または `user_id` のコンテキストが必要）、`get_file`（添付ファイル URL → base64）、`leave_guild`、`get_status`、`get_version`、`get_supported_actions`

### 対応していない標準動作（retcode=10002）

`send_message`（Send DSL を使用）、`upload_file`、`get_latest_events`、`set_group_name`、`set_group_admin`、`set_group_leave`、`set_group_card`、`leave_group`、`leave_channel`

### プラットフォーム拡張動作（oopz.*）

| 動作 | 必須パラメータ | 説明 |
|---|---|---|
| `oopz.create_channel` | `area_id, name` | オプション: `channel_type/group_id/secret/max_member` |
| `oopz.delete_channel` | `area_id, channel_id` | |
| `oopz.mute_member` / `oopz.unmute_member` | `area_id, user_id` | ミュート、`duration` 分数が自動的に設定（5分/1時間/1日/3日/7日） |
| `oopz.mute_mic` / `oopz.unmute_mic` | `area_id, user_id` | ミュート解除 |
| `oopz.kick_member` | `area_id, user_id` | ドメインから退出 |
| `oopz.block_user` / `oopz.unblock_user` | `area_id, user_id` | ドメインのブラックリスト |
| `oopz.get_area_members` | `area_id` | オプション: `offset_start/offset_end` |
| `oopz.get_assignable_roles` | `area_id, target_id` | 分配可能なロール |
| `oopz.assign_role` / `oopz.revoke_role` | `area_id, target_id, role_id` | 内部で全ロールを読み込んで、まとめて送信 |
| `oopz.react_message` / `oopz.unreact_message` | `message_id, channel_id, emoji` | オプション: `user_id`（プライベートメッセージ）/`area_id` |
| `oopz.get_reactions` | `message_id` | オプション: `message_ids`（≤50）/`user_id` |
| `oopz.get_reaction_persons` | `message_id, channel_id, emoji` | レイションしたユーザーのページング |
| `oopz.top_message` | `message_id, area_id, channel_id` | ピン留め/解除（`cancel=True`） |
| `oopz.get_history_messages` | `area_id, channel_id` | オプション: `size`（デフォルト 50） |
| `oopz.get_friend_requests` | — | フレンドリクエストリスト |
| `oopz.respond_friend_request` | `target, friend_request_id, agree` | 審査（通常は Request DSL を使用） |

## 友人申請の処理

- イベント: `request/friend`、`request_id` は**状態を持たない複合キー** `<target>:<friendRequestId>`
- `event.approve()` / `event.reject()` → POST `/client/v1/friendship/v1/response`
- 単一エンドポイントの同構性により、要求タイプのコンテキスト保持テーブルは不要

## 送信メソッドの戻り値

```json
{
  "status": "ok",
  "retcode": 0,
  "data": {"message_id": "14283..."},
  "message_id": "14283...",
  "message": "",
  "oopz_raw": {"messageId": "14283...", "timestamp": "..."}
}
```

## 特有イベントタイプ

- メッセージイベント拡張フィールド: `oopz_area_id`、`guild_id`（チャンネルメッセージ）；`oopz_reference_message_id`（返信）
- 通知拡張: `oopz_edited_text`、`oopz_emoji`、`oopz_reaction_type`、`oopz_persons`、`oopz_from_channel`、`oopz_channel_name`、`oopz_channel_type`、`oopz_area_name`、`oopz_role_id`、`oopz_role_name`、`oopz_ban_until`、`oopz_login_state`
- `EventMixin` 便利メソッド: `get_raw_event()`、`get_area_id()`、`get_edited_text()`、`get_emoji()`、`get_reaction_type()`、`get_voice_persons()`