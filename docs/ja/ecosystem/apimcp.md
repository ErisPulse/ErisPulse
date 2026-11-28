# ErisPulse-ApiMCP — AI クライアントでボットを操作する

> [!TIP]
> **このドキュメントが必要な場面**：Claude Desktop などの MCP 対応 AI クライアントに、ボットの直接操作——メッセージの送信、メッセージの確認、モジュールの呼び出し、アダプターの管理、イベントストリームの観測——をさせたいときに読んでください。不要であれば読み飛ばして構いません。

[ErisPulse-ApiMCP](https://github.com/wsu2059q/ErisPulse-ApiMCP) は、ボットのランタイム機能を **MCP（Model Context Protocol）** 経由で AI クライアントに公開します。インストールすると、Claude Desktop に 17 個のツールが追加され、AI があなたに代わってメッセージの送受信、モジュールのトラブルシューティング、グループチャットイベントの購読、フレームワークドキュメントの検索を行えるようになります——ボットは「あなたが管理するプログラム」から「AI の手と目」へと変わります。

> [!IMPORTANT]
> ApiMCP は別途インストールが必要で、**トークンを明示的に設定して初めて**ブリッジが有効になります：
>
> ```bash
> epsdk install ErisPulse-ApiMCP
> ```
>
> `config.toml` の `[ApiMCP]` セクションに `token = "長いランダム文字列"` を設定してください（または環境変数 `ERISPULSE_APIMCP_TOKEN`）。未設定の場合は、死活監視以外のすべてのエンドポイントが 503 を返し、トークンのサイレントリークを防ぎます。

## 仕組み

2層構造となっており、ボット本体には AI への依存を一切導入していません：

- **ボットプロセス内**：ApiMCP モジュールがフレームワーク内蔵の HTTP サーバー上に REST ブリッジをマウントします（`/apimcp/*`、トークン認証、デフォルトのレート制限は 30 リクエスト/分）
- **独立プロセス**：`erispulse-apimcp` コマンドが公式の `mcp` SDK を使用して stdio サーバーを起動し、MCP ツール呼び出しをボットの HTTP ブリッジへ転送します

```
Claude Desktop ──MCP(stdio)──► erispulse-apimcp ──HTTP──► ボットプロセス REST ブリッジ ──► sdk.*
```

ボットがオフラインの場合やブリッジが未設定の場合、ツールは読みやすいエラーメッセージとトラブルシューティングのガイドを返し、スタックトレースはスローしません。

## Claude Desktop 接続

`claude_desktop_config.json` を編集します（Windows: `%APPDATA%\Claude\`、macOS: `~/Library/Application Support/Claude/`）：

```json
{
  "mcpServers": {
    "erispulse": {
      "command": "erispulse-apimcp",
      "env": {
        "ERISPULSE_APIMCP_URL": "http://127.0.0.1:8000",
        "ERISPULSE_APIMCP_TOKEN": "あなたのトークン"
      }
    }
  }
}
```

保存後、Claude Desktop を完全に再起動し、ツールリストに `erispulse` サーバーが表示されれば接続成功です。MCP stdio server をサポートする任意のクライアント（Claude Code、Cursor など）でも、同じ方法で接続できます。

## 17個のツール一覧

| カテゴリ | ツール | 説明 |
|---|---|---|
| モジュール | `list_modules` / `get_module_info` / `call_module` / `reload_module` | インストール済みモジュールの公開サービスの閲覧と呼び出し、ホットリロードの実行 |
| アダプター | `list_adapters` / `get_adapter_status` / `reload_adapter` | プラットフォームのオンライン状態。アダプターのリロードはデフォルトで無効 |
| メッセージ | `send_message` / `recent_messages` | 任意のプラットフォームへテキスト/画像/音声/動画/ファイルを送信。複数botデプロイでは `account` で送信アカウントを指定可能。[transcript](../advanced/transcript.md) で最近のメッセージを遡って確認 |
| イベント | `subscribe_events` / `unsubscribe` / `poll_events` | メッセージ/通知などのイベントを購読。リングバッファ（デフォルト 1000 件）、差分ポーリング |
| ドキュメント | `search_erispulse_docs` / `read_erispulse_doc` / `refresh_erispulse_docs` | ErisPulse フレームワークドキュメントの検索と閲覧。独立したドキュメントエンジンにより、フレームワークのバージョンに応じてダウンロード・キャッシュされ、他のモジュールに依存しない |
| ランタイム | `get_topology` / `sdk_health` | ランタイムトポロジー（マスキング済み）とヘルスサマリー |

典型的な使用例：AI がまず `subscribe_events(["message"])` を行い、その後定期的に `poll_events` でグループチャット内の話題を観察し、`send_message` で割り込むべきか、あるいは `call_module` で特定のモジュールの機能を呼び出すべきかを判断します。フレームワークの機能の使い方が分からない場合は、AI がまず `search_erispulse_docs` でドキュメントを調べてから実行することもできます。

## セキュリティ上の要点

- **トークンは完全な制御権限**：メッセージの読み取り、送信、ホワイトリスト内モジュールメソッドの呼び出しが可能になります。リポジトリへのコミットや公開チャンネルへの貼り付けは絶対にしないでください。マルチテナント環境では複数のボットインスタンスに分割してください
- **最小権限の付与**：`module_call_whitelist` で呼び出し可能なモジュールを絞り込み（`モジュール.メソッド` 形式による精密な許可に対応）、`send_target_whitelist` で送信先を絞り込み（例：特定のグループへの送信のみ許可）、`allow_adapter_reload` はデフォルトの無効状態を維持してください
- **ローカルホストのみでリッスン**：ローカル環境でのみ使用する場合は、フレームワークの HTTP サーバーを `server.host = "127.0.0.1"` に設定してください。マシンをまたぐ場合は、内部ネットワーク + リバースプロキシによる TLS が必須です
- 出力はキー名レベルでサニタイズされます（キー/パス系のキーはキーごと破棄）。深いレベルのサニタイズはモジュール自身の責任であり、機密性の高いセッションではサブスクリプションを開放しないでください

完全な設定項目（バッファ容量、ルックバックウィンドウ、イベントタイプのホワイトリストなど）と REST エンドポイントの詳細については、[プロジェクトの README](https://github.com/wsu2059q/ErisPulse-ApiMCP) を参照してください。

---

## 次のステップ

- **AIを単に操作される存在ではなく、グループ内で「生き」させたい**：QvQChatは正方向——エージェントが能動的にチャットや作業を行う。詳細は [QvQChat 汎用エージェント](qvqchat.md) を参照。ApiMCPは逆方向——外部AIがボットを操作する。両方を同時にインストール可能
- **最近のメッセージのデータがどこから来るのか知りたい**：[会話受信トレイ transcript](../advanced/transcript.md)
- **ボットのHTTP serverについて知りたい**：[ルーティングシステム](../advanced/router.md)