# Sandbox プラットフォームの機能ドキュメント

SandboxAdapter は ErisPulse に内蔵されたサンドボックスアダプタで、ローカル開発およびモジュールのデバッグに使用されます。本物のプラットフォームを必要とせず、メッセージの送受信をシミュレートできます。

---

## ドキュメント情報

- 対応モジュールバージョン: 4.1.0
- メンテナー: ErisPulse

## 基本情報

- プラットフォーム概要：ローカルサンドボックス環境。仮想ユーザー/グループ、Web デバッグパネル、メッセージの永続化を提供
- アダプタ名：SandboxAdapter
- プラットフォーム識別子：`sandbox`
- 単一アカウント設計（ローカルデバッグ用）
- フレームワーク要件：ソフト依存 `ErisPulse>=2.7.1`（実行時検出による警告、強制ではない）

## v5 フレームワークの更新（4.1.0）

- **Api DSL 最小化**：`get_self_info` / `get_status` / `get_version` / `get_supported_actions`
- **spawn_background によるタスクの割り当て**：ハートビートタスクは `runtime.spawn_background` を使用
- **フレームワークのソフト依存**：`ErisPulse>=2.7.1` の実行時検出と警告
- インポートパスを `Core.Bases` に更新（BaseConfig）

## 標準 API アクションの例

```python
from ErisPulse import sdk
sandbox = sdk.adapter.get("sandbox")

result = await sandbox.Api.get_self_info()   # サンドボックスボットのアイデンティティ
result = await sandbox.Api.get_status()
result = await sandbox.Api.get_supported_actions()
```

## 使用方法

- サンドボックスは仮想ユーザーとグループを提供し、モジュールは本物のプラットフォームのようにメッセージの送受信が可能です。
- Web デバッグパネルを使用して、手動でメッセージを送信してモジュールの処理ロジックをトリガーできます。
- メッセージデータは永続的に保存され、再起動後も復元可能です。