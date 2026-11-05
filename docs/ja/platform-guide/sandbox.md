# Sandboxプラットフォームの特徴ドキュメント

SandboxAdapterは、ErisPulseに内蔵されたサンドボックスアダプターで、ローカル開発とモジュールのデバッグに使用されます。本物のプラットフォームを必要とせず、メッセージの送受信をシミュレートします。

---

## ドキュメント情報

- 対応するモジュールのバージョン: 4.2.0
- 維持管理者: ErisPulse

## 基本情報

- プラットフォームの概要：ローカルサンドボックス環境で、仮想ユーザー/グループ、Webデバッグパネル、メッセージの永続化を提供します。
- アダプター名: SandboxAdapter
- プラットフォーム識別子: `sandbox`
- 単一アカウント設計（ローカルデバッグ環境）
- フレームワークの要件：ソフト依存 `ErisPulse>=2.7.1`（実行時検出による警告、強制ではありません）

## v5 フレームワークの更新（4.2.0）

- **Api DSL最小集合**：`get_self_info` / `get_status` / `get_version` / `get_supported_actions`
- **spawn_background タスクの所属**：ハートビートタスクは `runtime.spawn_background` を使用
- **フレームワークのソフト依存**：実行時に `ErisPulse>=2.7.1` を検出し、警告を表示
- インポートパスを `Core.Bases`（BaseConfig）に更新

## 標準Apiの動作例

```python
from ErisPulse import sdk
sandbox = sdk.adapter.get("sandbox")

result = await sandbox.Api.get_self_info()   # サンドボックス上のロボットのアイデンティティ
result = await sandbox.Api.get_status()
result = await sandbox.Api.get_supported_actions()
```

## 使用方法

- サンドボックスは仮想ユーザーとグループを提供し、モジュールは本物のプラットフォームのようにメッセージを送受信できます。
- Webデバッグパネルは手動でメッセージを送信し、モジュールの処理ロジックをトリガーできます。
- メッセージデータは永続化され、再起動後も復元できます。
- `.MergeForward(nodes, title="合并聊天记录")`：メッセージの結合転送を送信します（HTMLの`<details>`折りたたみカードとしてレンダリングされ、htmlチャンネルから発信されます）。これは、モジュールの結合転送ロジックを検証するために使用されます。