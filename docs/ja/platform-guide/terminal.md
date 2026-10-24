# Terminal プラットフォーム機能ドキュメント

TerminalAdapter はコマンドラインターミナルのアダプターです。ターミナルはチャットセッションとして機能し、ローカルでのモジュールロジックの迅速なデバッグに使用されます。

---

## ドキュメント情報

- 対応モジュールバージョン: 1.1.0
- メンテナー: ErisPulse

## 基本情報

- プラットフォーム概要：ローカルのコマンドラインをチャットセッションとして扱い、stdin からの入力はメッセージとして扱い、モジュールからの返信はターミナルに直接出力される
- アダプタ名：TerminalAdapter
- プラットフォーム識別子：`terminal`
- 単一アカウント設計（ローカルデバッグ用）
- フレームワーク要件：ソフト依存 `ErisPulse>=2.7.1`（実行時に検出して警告を表示するが、強制ではない）

## 設定説明

```toml
[Terminal]
bot_id = "terminal_bot"   # サンドボックス用のロボットID
bot_name = "Terminal"     # 表示名
```

## v5 フレームワークの更新 (1.1.0)

- **spawn_background によるタスクの割り当て**：stdin 読み取りループを `runtime.spawn_background` に変更
- **フレームワークのソフト依存**：`ErisPulse>=2.7.1` の実行時検出と警告メッセージの表示；起動時にバージョンログを出力

## 使用方法

```python
# モジュールは通常通りメッセージをリッスンします
from ErisPulse.Core.Event import message

@message.on_message()
async def handle(event):
    if event.get("platform") == "terminal":
        await event.reply("受信：" + event.get_text())
```

- ターミナルに入力されたテキストはユーザーのメッセージとなり、複数行に対応します（空行で終了）
- 開発段階でモジュールのロジックを迅速に検証する場合に適しており、実際のプラットフォームに接続する必要はありません