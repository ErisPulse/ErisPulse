# 企業微信（WeCom）プラットフォームの特徴ドキュメント

WeComAdapter は、企業微信の自建アプリ API を基に構築されたアダプターです。コールバックを介してメッセージを受信し、アプリメッセージインターフェースを用いて送信を行い、連絡先およびメッセージカード機能を提供します。

---

## ドキュメント情報

- 対応モジュールバージョン: 0.1.0
- 維持管理者: ErisPulse

## 基本情報

- プラットフォーム紹介：企業向けWeChatの自作アプリケーション・ロボット。社内通知、インテリジェントな質問応答、オフィス自動化などの場面に適しています。
- アダプター名：WeComAdapter
- 複数アカウント対応：複数の企業を同時に設定可能（各アカウントは1つのcorpid + アプリに対応）
- 接続方法：HTTPコールバックによる受信（企業向けWeChatのバックエンドでメッセージ受信URLを設定）+ 主動APIによる送信
- 認証方式：corpid + secretからaccess_tokenを取得（自動的に更新）
- コールバックの暗号化/復号化：Token + EncodingAESKey（企業向けWeChat公式の暗号化プロトコル）
- チェーン修飾子サポート：`.Reply()`などのチェーン修飾子メソッドをサポート
- OneBot12互換性：OneBot12標準メッセージセグメントの送信をサポート

## 設定の説明

```toml
# config.toml
[WeComAdapter.accounts.default]
corpid = "YOUR_CORP_ID"        # 企業 ID（必須、企業微信管理画面-私の企業）
secret = "YOUR_APP_SECRET"     # アプリの Secret（必須、自作アプリの詳細ページ）
agentid = 1000002              # アプリ AgentId（必須、自作アプリの詳細ページ）
callback_enabled = true        # コールバック受信の有効化（デフォルト true；無効化後は送信のみ可能）
token = "YOUR_CALLBACK_TOKEN"  # コールバック検証用トークン（企業微信管理画面-メッセージ受信設定）
encoding_aes_key = "YOUR_AES_KEY_43CHARS"  # コールバックの暗号化/復号化キー（43 文字）
callback_path = "/wecom/{account}"         # コールバックパス、{account} プレースホルダに対応
enabled = true
```

**各アカウントの設定項目の説明：**

- `corpid` / `secret` / `agentid`：[企業微信管理画面](https://work.weixin.qq.com)の自作アプリページから取得（最初の2つは必須）
- `callback_enabled`：コールバック受信のスイッチ（デフォルトで有効）。**無効化するとアダプタはコールバックルートの登録をスキップし、送信のみの機能に制限される**；管理画面のコールバック関連のフィールドも非表示になる
- `token` / `encoding_aes_key`：コールバックメッセージの検証と暗号化/復号化、企業微信管理画面の「メッセージ受信」設定と一致させる
- `callback_path`：コールバック受信パス（デフォルト `/wecom/{アカウント名}`）、企業微信管理画面では完全な URL を設定する必要がある：`http(s)://あなたのアドレス:ポート/wecom/<アカウント名>`

**メッセージ受信の前提条件**：企業微信管理画面 → 自作アプリ → 「メッセージ受信」の API 受信設定、URL には上記の完全なコールバックアドレスを記入し、Token と EncodingAESKey は設定と一致させる。**注意**：企業微信ではコールバック URL が外部ネットワークからアクセス可能である必要がある（リバースプロキシの併用が推奨）。

**API 環境**：
- API 基本アドレス：`https://qyapi.weixin.qq.com/cgi-bin`
- access_token は自動的に取得・キャッシュされ、手動での管理は不要

## メッセージ送信

```python
from ErisPulse import sdk
wecom = sdk.adapter.get("wecom")

# 基本メッセージ（target_type: "user"=ユーザー "group"=アプリグループチャット）
await wecom.Send.To("user", "zhangsan").Text("こんにちは")
await wecom.Send.To("group", "group_chat_id").Markdown("**太字**通知")

# メディア（ローカルパス / bytes / URL；自動で一時素材をアップロードして送信）
await wecom.Send.To("user", "zhangsan").Image("banner.png")
await wecom.Send.To("user", "zhangsan").Voice("voice.amr")
await wecom.Send.To("user", "zhangsan").Video("demo.mp4")
await wecom.Send.To("user", "zhangsan").File("report.pdf")

# ニュースとカード
await wecom.Send.To("user", "zhangsan").News([
    {"title": "タイトル", "description": "要約", "url": "https://...", "picurl": "https://.../img.png"},
])  # 最大 8 件まで

await wecom.Send.To("user", "zhangsan").TextCard(
    title="承認リマインダー",
    description="承認待ちの書類があります",
    url="https://oa.example.com/approval/1",
    btntxt="処理する",
)

await wecom.Send.To("user", "zhangsan").TemplateCard(
    card_type="text_notice",  # 企業微信カードの種類、その他のパラメータは公式カードの JSON をそのまま渡す
    source={"icon_url": "...", "desc": "OA"},
    main_title={"title": "会議リマインダー"},
)

# パッシブな返信：メッセージを受け取った event.reply() で直接元のユーザーに返信
```

## 標準 API アクション

```python
info = await wecom.Api.get_self_info()          # アプリ情報（corpid/agentid）
status = await wecom.Api.get_status()           # 実行状態
ver = await wecom.Api.get_version()             # アダプタバージョン

# 連絡先（2.1.0 追加、自動的に access_token が注入されます）
user = await wecom.Api.get_user_info("zhangsan")            # メンバーの詳細情報（名前/部門/役職/アイコン）
depts = await wecom.Api.get_department_list(0)              # 部門リスト（0=ルート部門）
members = await wecom.Api.get_department_users(2)           # 部門のメンバー一覧
uid = await wecom.Api.get_user_by_mobile("13800000000")     # 電話番号から userid を検索
openid = await wecom.Api.userid_to_openid("zhangsan")       # userid → openid（赤包/外部支払い）
userid = await wecom.Api.openid_to_userid("oXXXX")          # openid → userid

# 複数アカウント
result = await wecom.Api.Using("corp2").get_user_info("lisi")

# 任意の企業微信 API 直接呼び出し（endpoint は cgi-bin からの相対パス、自動的に access_token が付与されます）
result = await wecom.Api.call("message/send", touser="zhangsan", msgtype="text", agentid=1000002, text={"content": "hi"})
```

## 事件の説明

- メッセージイベント：`detail_type` が `private`（メンバーがメッセージを送信）/ `group`（アプリのグループチャットメッセージ）；`user_id` はメンバーの userid
- イベントオブジェクトは `get_raw_xml()`（元のコールバック XML）などの拡張読み取りメソッドを提供
- イベントの報告（サブスクリプション/メニュークリックなど）は `request` / `notice` クラスのイベントに変換される

## 注意事項

1. **コールバック URL はインターネットからアクセス可能でなければなりません**：ローカル開発では内向的トンネルを使用できます。本番環境では Nginx を使って ErisPulse router のポートにリバースプロキシすることを推奨します。
2. **アクティブな送信頻度**：企業微信アプリのメッセージインターフェース制限（各アプリの毎日の送信量は企業の規模に関連）により、一斉送信の場合は `TaskCard`/`TemplateCard` とタグを組み合わせてください。
3. **access_token の有効性**：アダプターが自動的に更新します。同一の corpid+secret を複数のインスタンスでデプロイする場合は、公式のトークンの相互排除制限に注意してください（中央で1つのインスタンスが送受信を行うのが望ましいです）。
4. **メディアファイル**：Voice は AMR 形式でなければなりません（企業微信の制限による）；大容量のファイルは一時素材インターフェースを使用してください（アダプターが自動的に処理します）。