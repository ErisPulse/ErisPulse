# アダプターのコア概念

ErisPulseアダプターのコア概念を理解することは、アダプター開発の基礎となります。

## アダプターアーキテクチャ

### コンポーネントの関係

```
順方向変換（受信方向）                           逆方向変換（送信方向）
─────────────────                           ─────────────────
                                             
┌──────────────────┐                        ┌──────────────────┐
│ プラットフォーム  │                        │ モジュールによる   │
│ ネイティブイベント│                        │ メッセージ構築     │
└────────┬─────────┘                        └────────┬─────────┘
         │                                           │
         ↓                                           ↓
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│                  │   │ アダプター        │   │                  │
│  Converter       │   │ (MyAdapter)      │   │ Send.Raw_ob12()  │
│  (イベント       │──→│ ┌──────────────┐ │   │ (逆方向変換      │
│   コンバーター)  │   │ │              │ │   │  エントリ)       │
│                  │   │ │              │ │   │                  │
└──────────────────┘   │ └──────────────┘ │   └────────┬─────────┘
                       └──────────────────┘            │
                                │                      ↓
                                ↓              ┌──────────────────┐
                       ┌──────────────────┐    │ プラットフォーム  │
                       │ OneBot12         │    │ API 呼び出し     │
                       │ 標準イベント     │    └────────┬─────────┘
                       └────────┬─────────┘             │
                                │                      ↓
                                ↓              ┌──────────────────┐
                       ┌──────────────────┐    │ 標準レスポンス   │
                       │ イベントシステム │    └──────────────────┘
                       └────────┬─────────┘
                                │
                                ↓
                       ┌──────────────────┐
                       │ モジュール        │
                       │ (イベント処理)   │
                       └──────────────────┘
```

**コアの対称性**：
- **順方向変換**（Converter）：プラットフォームネイティブイベント → OneBot12 標準イベント、元のデータは `{platform}_raw` に保持されます
- **逆方向変換**（Raw_ob12）：OneBot12 メッセージセグメント → プラットフォーム API 呼び出し、標準のレスポンス形式を返します

## AdapterManager アダプター管理マネージャー

`AdapterManager` は、ErisPulseアダプターシステムのコアコンポーネントであり、すべてのプラットフォームアダプターの登録、起動、終了、およびイベントのディスパッチを管理します。

### コア機能

- **アダプター登録**：複数のプラットフォームアダプターを登録および管理します
- **ライフサイクル管理**：アダプターの起動と終了を制御します
- **イベントディスパッチ**：OneBot12 標準イベントとプラットフォームネイティブイベントをディスパッチします
- **設定管理**：アダプターの有効/無効状態を管理します
- **ミドルウェアサポート**：OneBot12 イベントミドルウェアをサポートします

### 基本的な使用方法

```python
from ErisPulse import sdk

# アダプターの登録（通常はLoaderにより自動的に完了します）
sdk.adapter.register("myplatform", MyPlatformAdapter)

# すべてのアダプターを起動
await sdk.adapter.startup()

# 指定したアダプターを起動
await sdk.adapter.startup(["myplatform"])
# すべてのアダプターを起動
await sdk.adapter.startup()

# アダプターインスタンスの取得
my_adapter = sdk.adapter.get("myplatform")
# またはプロパティ経由でアクセス
my_adapter = sdk.adapter.myplatform

# すべてのアダプターを終了
await sdk.adapter.shutdown()
```

### 起動と終了

#### アダプターの起動

```python
# 登録済みのすべてのアダプターを起動
await sdk.adapter.startup()

# 指定したプラットフォームを起動
await sdk.adapter.startup(["platform1", "platform2"])
```

**起動フロー：**

1. `adapter.start` ライフサイクルイベントを送信します
2. `adapter.status.change` イベントを送信します（starting）
3. 各アダプターを並行して起動します
4. 起動失敗時、自動リトライ（指数バックオフ戦略）
5. 起動成功後、`adapter.status.change` イベントを送信します（started）

**リトライメカニズム：**

- 最初の4回のリトライ：60秒、10分、30分、60分
- 5回目以降：3時間の固定間隔

#### アダプターの終了

```python
# すべてのアダプターを終了
await sdk.adapter.shutdown()
```

**終了フロー：**

1. `adapter.stop` ライフサイクルイベントを送信します
2. すべてのアダプターの `shutdown()` メソッドを呼び出します
3. ルーティングサーバーを閉じます
4. イベントプロセッサをクリアします
5. `adapter.stopped` ライフサイクルイベントを送信します

### 設定管理

#### プラットフォーム状態の確認

```python
# プラットフォームが登録されているか確認
exists = sdk.adapter.exists("myplatform")

# プラットフォームが有効か確認
enabled = sdk.adapter.is_enabled("myplatform")

# in 演算子を使用
if "myplatform" in sdk.adapter:
    print("プラットフォームは存在し、有効です")
```

#### プラットフォームの一覧

```python
# 登録済みのすべてのプラットフォームを一覧表示
platforms = sdk.adapter.list_registered()

# すべてのプラットフォームとその状態を一覧表示
status_dict = sdk.adapter.list_items()
# 返り値: {"platform1": true, "platform2": false, ...}

# 有効なプラットフォームのリストを取得
enabled_platforms = [p for p, enabled in status_dict.items() if enabled]
```

### イベントリスニング

#### OneBot12 標準イベント

```python
from ErisPulse import sdk

# すべてのプラットフォームの標準メッセージイベントをリッスン
@sdk.adapter.on("message")
async def handle_message(data):
    print(f"OneBot12メッセージを受信: {data}")

# 特定のプラットフォームの標準メッセージイベントをリッスン
@sdk.adapter.on("message", platform="myplatform")
async def handle_platform_message(data):
    print(f"myplatform メッセージを受信: {data}")

#