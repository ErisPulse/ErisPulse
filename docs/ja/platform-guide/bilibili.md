# Bilibili プラットフォーム特性ドキュメント

BilibiliAdapter は bilibili-api-python をベースにした Bilibili ダイレクトメッセージ（DM）アダプターで、Cookie / QRコードによるデュアルログインとイベント駆動型の DM 送受信をサポートします。

---

## ドキュメント情報

- 対応モジュールバージョン: 0.1.0
- メンテナー: ErisPulse

## 基本情報

- プラットフォーム概要：Bilibili DM ボット（公式の個人向け Bot API は存在せず、模擬ログインにより Web DM インターフェースを利用）
- アダプター名：BilibiliAdapter
- マルチアカウント対応：対応（アカウントごとに 1 つの Bilibili アカウント、独立したセッション監視）
- 接続方式：イベント駆動型セッション監視（bilibili-api `Session`）
- 認証方式：Cookie（SESSDATA / bili_jct / buvid3 / dedeuserid）またはパネルでの QRコードログイン
- チェーン修飾対応：`.Reply()` などのチェーン修飾メソッドに対応
- OneBot12 互換：標準メッセージセグメント（text / image）に対応

## 設定説明

```toml
[BilibiliAdapter.accounts.default]
login_mode = "cookie"          # cookie=認証情報の手動入力 / qrcode=パネルでQRコードスキャン（推奨）
sessdata = "YOUR_SESSDATA"     # cookie モードでは必須
bili_jct = "YOUR_BILI_JCT"     # cookie モードでは必須
buvid3 = "YOUR_BUVID3"         # 任意、リスク制御に引っかかる確率を低減
dedeuserid = "YOUR_UID"        # 任意、アカウントの UID
bot_id = ""                    # 空欄の場合はログイン後に自動取得
enabled = true
```

**設定項目の説明（各アカウント）：**

- `login_mode`：ログイン方式。`cookie` は認証情報の手動入力、`qrcode` はパネルでの QRコードスキャン（推奨）。どちらのモードでも認証情報は最終的に sessdata/bili_jct などのフィールドに保存されます
- `sessdata` / `bili_jct`：ログイン状態の Cookie（cookie モードでは必須。パネルではパスワード形式で表示）
- `buvid3`：デバイスフィンガープリント Cookie（任意）。付与するとリスク制御に引っかかる確率を大幅に低減できます
- `dedeuserid`：アカウントの UID（任意）。`bot_id` のデフォルトソースも兼ねます
- `bot_id`：アカウントの UID。空欄にするとログイン後に `get_self_info` で自動取得されます

**QRコードログインの流れ**：`login_mode = "qrcode"` を保存した後、Dashboard → コンポーネント設定 → アカウント追加ウィザードで「QRコードでBilibiliにログイン」を選択 → Bilibili アプリで QRコードをスキャン → スマホで確認 → アダプターがログイン状態をポーリング（scan → confirm → done）し、認証情報は自動的にそのアカウントの設定に書き込まれて有効になります。

> アダプターは同時に `POST /bilibili/qr/start`（QRコードの取得、画像 URL + セッショントークンを返す）と `POST /bilibili/qr/poll`（ログイン状態のポーリング）のエンドポイントも登録しており、サードパーティのフロントエンドからも直接利用できます。ポーリングリクエストには start が返した `poll_token` を付与する必要があり、不正なポーリングを防止します。

## メッセージ送信

すべての送信メソッドは Task を返し、await すると標準レスポンスが得られます（「戻り値フォーマット」を参照）。

### 基本送信

```python
from ErisPulse import sdk
bili = sdk.adapter.get("bilibili")

# テキスト DM（target は相手の UID）
await bili.Send.To("user", "123456789").Text("Hello Bilibili!")

# 画像 DM（URL またはローカルパス、Bilibili DM 用画像に変換）
await bili.Send.To("user", "123456789").Image("https://example.com/pic.jpg")
await bili.Send.To("user", "123456789").Image("./local.png")
```

### チェーン修飾メソッド

```python
# 指定メッセージに返信（msg_key は受信メッセージの message_id）
await bili.Send.To("user", "123456789").Reply("msg_key").Text("了解しました！")
```

### OneBot12 標準セグメント送信

```python
message = [
    {"type": "text", "data": {"text": "1行目"}},
    {"type": "image", "data": {"file": "https://example.com/img.jpg"}},
]
await bili.Send.To("user", "123456789").Raw_ob12(message)
```

### マルチアカウント送信

```python
await bili.Send.Using("account2").To("user", "123456789").Text("2つ目のアカウントからの送信")
```

### 対応・非対応のメッセージセグメント

| セグメント | 対応 | 説明 |
|----|------|------|
| `text` | 対応 | 連結してから `send_msg`（TEXT）で送信 |
| `image` | 対応 | `file` は URL / ローカルパス、`send_msg`（PICTURE）で送信 |
| `reply` | 部分対応 | 修飾子として受け付けますが、Bilibili DM には引用表示がないため送信コンテキストとしてのみ機能 |
| `mention` / `face` / `voice` / `video` / `file` など | 非対応 | `retcode=10002` を返し、受信したセグメントタイプを列挙 |

## 標準 API アクション（Api）

```python
from ErisPulse import sdk
bili = sdk.adapter.get("bilibili")

# 自身の情報（ニックネーム/アバター/UID）
result = await bili.Api.get_self_info()

# ユーザーの公開情報（任意のユーザー、ニックネーム/アバター）
result = await bili.Api.get_user_info("123456789")

# 指定セッションの履歴メッセージを取得（begin_seqno はページ送りに使用）
result = await bili.Api.get_session_msgs("123456789", begin_seqno=0)

# ステータスとバージョン
result = await bili.Api.get_status()
result = await bili.Api.get_version()

# マルチアカウント
result = await bili.Api.Using("account2").get_self_info()
```

### 対応している標準アクション

| メソッド | 説明 | データソース |
|------|------|---------|
| `get_self_info()` | 自身の情報（mid/name/face） | Web API（スペース情報） |
| `get_user_info(user_id)` | ユーザーの公開情報（ニックネーム/アバター） | Web API（ユーザー情報カード） |
| `get_session_msgs(talker_id, begin_seqno)` | セッションの履歴メッセージ | Web DM インターフェース（session_msgs） |
| `get_status()` | アダプターの実行状態 | ローカル |
| `get_version()` | アダプターのバージョン | ローカル |

### 非対応の標準アクション

以下の標準アクションは Bilibili DM に対応する機能がなく、呼び出すと `retcode=10002` が返されます：

- `get_friend_list` / `get_group_list` / `get_group_member_info`
- `delete_message`（Bilibili DM では相手側のみが自分のメッセージを取り消せます）
- `set_group_name` / `leave_group` などのグループ管理系

### 汎用アクションエントリ

```python
# send_message：テキストと画像セグメントの組み合わせ送信（Send チェーンと同等）
result = await bili.call_api(
    "send_message",
    _account_id="default",
    target_id="123456789",
    message=[{"type": "text", "data": {"text": "hi"}}],
)
```

## 戻り値フォーマット

すべての送信および API メソッドは ErisPulse アダプターの標準化戻り値規範に従います：

```python
{
    "status": "ok",              # ok / failed
    "retcode": 0,                # 0 成功；10002 非対応；10003 パラメータ/ターゲットエラー；33100 Bilibili インターフェースエラー
    "data": {...},               # レスポンスデータ（send_msg の生の戻り値）
    "self": {"platform": "bilibili", "user_id": "..."},
    "message_id": "123456",      # Bilibili の msg_key
    "message": "",               # エラーメッセージ
    "bilibili_raw": {...}        # 生のレスポンス
}
```

## イベントタイプ

本プラットフォームの特性を使用する前に、`platform == "bilibili"` の判定が必要です。

### イベントマッピング

| Bilibili DM イベント | Adapter イベント | 説明 |
|--------------|--------------|------|
| TEXT（テキストメッセージ） | message（text セグメント） | 通常の個人チャットテキスト |
| PICTURE（画像メッセージ） | message（image セグメント） | content.pictures → image セグメント（URL） |
| WITHDRAW（取り消し） | ログ記録のみ | 相手によるメッセージの取り消し |

### イベントフィールドの例

```python
{
  "id": "uuid",
  "time": 1793277000,
  "type": "message",
  "detail_type": "private",
  "platform": "bilibili",
  "self": {"platform": "bilibili", "user_id": "10000", "user_name": "Botニックネーム", "account_id": "default"},
  "user_id": "123456789",                  # 相手の UID（sender_uid）
  "user_nickname": "シャオワン",                  # content.sender_name（欠落する場合があります）
  "message": [{"type": "text", "data": {"text": "こんにちは"}}],
  "alt_message": "こんにちは",
  "bilibili_raw": {...},                   # Bilibili の生の DM データ
  "bilibili_raw_type": "text"              # text / picture
}
```

### 拡張フィールドの説明

- すべての固有フィールドには `bilibili_` プレフィックスが付けられます（`bilibili_raw` / `bilibili_raw_type`）
- 受信した画像は image セグメントとして、`data.file` は Bilibili の画像ホスティング URL です
- `user_nickname` はメッセージ content の `sender_name` から取得され、一部のメッセージタイプでは欠落する場合があります

## 注意事項

1. **Bilibili には公式の個人向け Bot API が存在しない**：本アダプターは模擬ログインにより Web DM インターフェースを利用しており、非公式な使用方法です。インターフェースは Bilibili のアップデートに伴って変更される可能性があります
2. **リスク制御**：高頻度/大量の DM はリスク制御を非常に引き起こしやすいです（アカウントの DM 機能が一時的に使用禁止になります）。モジュール側でのスロットリングを必ず実装してください。`buvid3` を付与すると確率を低減できます
3. **ログイン状態の失効**：Cookie の有効期限が切れるとアダプターはエラーログを記録します。QRコードの再スキャンまたは Cookie の更新を行ってください。認証情報はパネルではパスワード形式で表示されます
4. 個人チャットの制限：1対1の DM のみ対応。ファングループチャットは現在サポートされていません
5. コンプライアンス：嫌がらせ、マーケティングの一括送信などの違反行為への使用は避け、Bilibili のコミュニティルールを遵守してください